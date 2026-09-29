from dataclasses import dataclass, field
from math import asin, cos, radians, sin, sqrt
from typing import Any, Iterable
DEFAULT_WEIGHTS = {
    "geographic": 0.25,
    "formation": 0.30,
    "depth": 0.20,
    "trajectory": 0.10,
    "event_relevance": 0.15,
}
KNOWN_FORMATION_MAPPINGS = {
    "barail": "barail",
    "barail group": "barail",
    "barail fm": "barail",
    "tikak parbat": "tikak parbat",
    "tikak parbat formation": "tikak parbat",
    "girujan": "girujan",
    "lakshmi": "lakshmi",
    "tipam": "tipam",
    "narpuh": "narpuh",
    "sylhet": "sylhet",
    "jaintia": "jaintia",
    "kopili": "kopili",
    "disang": "disang",
    "namsang": "namsang",
    "aster": "aster",
    "banyan": "banyan",
    "cedar": "cedar",
    "dahlia": "dahlia",
    "ember": "ember",
    "flint": "flint",
    "garnet": "garnet",
    "horizon": "horizon",
}
@dataclass(frozen=True)
class TargetInterval:
    top_m: float
    bottom_m: float
    def __post_init__(self):
        if self.top_m < 0 or self.bottom_m < self.top_m:
            raise ValueError("target depth interval must satisfy 0 <= top <= bottom")
@dataclass(frozen=True)
class ScoringConfig:
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    formation_mappings: dict[str, str] = field(default_factory=lambda: dict(KNOWN_FORMATION_MAPPINGS))
    def __post_init__(self):
        required = set(DEFAULT_WEIGHTS)
        if set(self.weights) != required:
            raise ValueError(f"weights must contain exactly: {', '.join(sorted(required))}")
        if any(value < 0 for value in self.weights.values()):
            raise ValueError("weights must be non-negative")
        if abs(sum(self.weights.values()) - 1.0) > 1e-9:
            raise ValueError("scoring weights must sum to 1.0")
def distance_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    radius_km = 6371.0088
    latitude_delta = radians(latitude_b - latitude_a)
    longitude_delta = radians(longitude_b - longitude_a)
    haversine = sin(latitude_delta / 2) ** 2 + cos(radians(latitude_a)) * cos(radians(latitude_b)) * sin(longitude_delta / 2) ** 2
    return 2 * radius_km * asin(sqrt(min(1.0, haversine)))
def _valid_coordinates(well: Any) -> bool:
    return (-90 <= float(well.latitude) <= 90 and -180 <= float(well.longitude) <= 180 and all(float(value) == float(value) for value in (well.latitude, well.longitude)))
def _normalize_formation(name: str | None, mappings: dict[str, str]) -> str | None:
    if not name or name.strip().lower() in {"unknown", "none", "n/a"}:
        return None
    normalized = " ".join(name.strip().lower().split())
    return mappings.get(normalized, normalized if normalized in set(mappings.values()) else None)
def _interval_overlap(first: TargetInterval, second: TargetInterval) -> float:
    overlap = max(0.0, min(first.bottom_m, second.bottom_m) - max(first.top_m, second.top_m))
    target_length = max(first.bottom_m - first.top_m, 1.0)
    return min(1.0, overlap / target_length)
def _as_interval(item: Any) -> TargetInterval | None:
    top = getattr(item, "top_depth_m", getattr(item, "start_depth_m", None))
    bottom = getattr(item, "base_depth_m", getattr(item, "end_depth_m", None))
    if top is None or bottom is None:
        return None
    try:
        return TargetInterval(float(top), float(bottom))
    except (TypeError, ValueError):
        return None
def _candidate_intervals(well: Any, events: Iterable[Any], formations: Iterable[Any]) -> list[TargetInterval]:
    intervals = [interval for item in list(events) + list(formations) if (interval := _as_interval(item)) is not None]
    return intervals
def _formation_score(target_name: str | None, candidate: Any, mappings: dict[str, str]) -> tuple[float | None, str | None]:
    target = _normalize_formation(target_name, mappings)
    candidate_names = [getattr(candidate, "formation", None), getattr(candidate, "formation_name", None)]
    candidate_names.extend(getattr(item, "name", None) for item in (getattr(candidate, "formations", []) or []))
    candidate_normalized = next((normalized for name in candidate_names if (normalized := _normalize_formation(name, mappings)) is not None), None)
    if target is None or candidate_normalized is None:
        return None, None
    return (1.0 if target == candidate_normalized else 0.0), candidate_normalized
def _event_score(events: list[Any], target: TargetInterval, event_type: str | None) -> tuple[float | None, int]:
    filtered = [event for event in events if not event_type or getattr(event, "event_type", None) == event_type]
    overlaps = [_interval_overlap(target, interval) for event in filtered if (interval := _as_interval(event)) is not None]
    if not filtered:
        return None, 0
    return min(1.0, max(overlaps, default=0.0)), sum(value > 0 for value in overlaps)
def rank_offsets(active_well: Any, candidate_wells: Iterable[Any], radius_km: float, target_interval: TargetInterval, formation: str | None = None, event_type: str | None = None, config: ScoringConfig | None = None) -> dict[str, Any]:
    if radius_km <= 0:
        raise ValueError("radius_km must be greater than 0")
    config = config or ScoringConfig()
    active_formation = formation or getattr(active_well, "formation", None)
    results: list[dict[str, Any]] = []
    exclusions: list[dict[str, str]] = []
    for candidate in candidate_wells:
        if candidate.id == active_well.id:
            exclusions.append({"well_id": candidate.id, "reason": "active well is excluded from offsets"})
            continue
        if not _valid_coordinates(candidate):
            exclusions.append({"well_id": candidate.id, "reason": "invalid coordinates; geographic distance unavailable"})
            continue
        distance = distance_km(active_well.latitude, active_well.longitude, candidate.latitude, candidate.longitude)
        if distance > radius_km:
            exclusions.append({"well_id": candidate.id, "reason": f"outside search radius ({distance:.2f} km > {radius_km:.2f} km)"})
            continue
        events = list(getattr(candidate, "incidents", []) or [])
        formations = list(getattr(candidate, "formations", []) or [])
        if event_type and not any(getattr(event, "event_type", None) == event_type for event in events):
            exclusions.append({"well_id": candidate.id, "reason": f"no matching event type: {event_type}"})
            continue
        features: dict[str, float | None] = {"geographic": max(0.0, 1.0 - distance / radius_km)}
        formation_score, matching_formation = _formation_score(active_formation, candidate, config.formation_mappings)
        features["formation"] = formation_score
        intervals = _candidate_intervals(candidate, events, formations)
        features["depth"] = max((_interval_overlap(target_interval, interval) for interval in intervals), default=None)
        active_trajectory = getattr(active_well, "trajectory", None)
        candidate_trajectory = getattr(candidate, "trajectory", None)
        features["trajectory"] = 1.0 if active_trajectory and candidate_trajectory and active_trajectory == candidate_trajectory else (0.0 if active_trajectory and candidate_trajectory else None)
        features["event_relevance"], relevant_event_count = _event_score(events, target_interval, event_type)
        available = {name: value for name, value in features.items() if value is not None}
        weight_total = sum(config.weights[name] for name in available)
        score = 100.0 * sum(config.weights[name] * value for name, value in available.items()) / weight_total if weight_total else 0.0
        missing = [name for name, value in features.items() if value is None]
        results.append({"well_id": candidate.id, "well_name": getattr(candidate, "name", candidate.id), "relevance_score": round(score, 2), "distance_km": round(distance, 3), "score_breakdown": {name: round(value, 4) for name, value in features.items() if value is not None}, "matching_formations": [matching_formation] if matching_formation and formation_score == 1 else [], "relevant_event_count": relevant_event_count, "data_completeness": round(len(available) / len(features), 2), "missing_fields": missing, "weight_total_used": round(weight_total, 4), "weights_validated": False, "weight_note": "Unvalidated demo weights; not a scientific or operational risk score."})
    results.sort(key=lambda item: (-item["relevance_score"], item["distance_km"], item["well_id"]))
    return {"items": results, "excluded": exclusions, "weights": config.weights, "weight_note": "Unvalidated demo weights; not a scientific or operational risk score."}
