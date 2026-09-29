from collections import defaultdict
from typing import Any, Iterable
SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
def _overlaps(first: tuple[float, float], second: tuple[float, float]) -> bool:
    return first[0] <= second[1] and second[0] <= first[1]
def _status(depth: float, top: float, bottom: float, lookahead_m: float) -> str:
    if top <= depth <= bottom:
        return "in_zone"
    if depth < top and top - depth <= lookahead_m:
        return "upcoming"
    return "passed" if depth > bottom else "outside"
def _severity(records: list[dict[str, Any]]) -> str:
    explicit = max((record.get("severity", "low") for record in records), key=lambda value: SEVERITY_ORDER.get(value, 1), default="low")
    if len(records) >= 3 and SEVERITY_ORDER.get(explicit, 1) < SEVERITY_ORDER["high"]:
        return "high"
    if len(records) >= 2 and explicit == "low":
        return "medium"
    return explicit
def evaluate_alerts(active_well_id: str, current_depth_m: float, evidence: Iterable[dict[str, Any]], lookahead_m: float = 100.0) -> list[dict[str, Any]]:
    if lookahead_m < 0:
        raise ValueError("lookahead_m must be non-negative")
    groups: list[dict[str, Any]] = []
    for record in sorted(evidence, key=lambda item: (item.get("event_type", ""), item.get("interval", [0, 0])[0], item.get("event_id", ""))):
        top, bottom = map(float, record["interval"])
        matching = next((group for group in groups if group["event_type"] == record.get("event_type") and _overlaps((group["top_depth_m"], group["bottom_depth_m"]), (top, bottom))), None)
        if matching:
            matching["top_depth_m"] = min(matching["top_depth_m"], top)
            matching["bottom_depth_m"] = max(matching["bottom_depth_m"], bottom)
            matching["evidence"].append(record)
        else:
            groups.append({"event_type": record.get("event_type", "unknown"), "top_depth_m": top, "bottom_depth_m": bottom, "evidence": [record]})
    alerts = []
    for group in groups:
        status = _status(current_depth_m, group["top_depth_m"], group["bottom_depth_m"], lookahead_m)
        if status == "outside":
            continue
        records = group["evidence"]
        offset_ids = sorted({record["offset_well_id"] for record in records if record.get("offset_well_id")})
        source_ids = sorted({record["source_document_id"] for record in records if record.get("source_document_id") is not None})
        key = f"{active_well_id}:{group['event_type']}:{group['top_depth_m']:.3f}:{group['bottom_depth_m']:.3f}"
        distance = 0.0 if status == "in_zone" else group["top_depth_m"] - current_depth_m
        alerts.append({"dedupe_key": key, "active_well_id": active_well_id, "event_type": group["event_type"], "interval_start_m": group["top_depth_m"], "interval_end_m": group["bottom_depth_m"], "current_depth_m": current_depth_m, "status": status, "distance_to_interval_m": distance, "offset_well_ids": offset_ids, "source_document_ids": source_ids, "evidence_event_ids": sorted({record["event_id"] for record in records}), "severity": _severity(records), "relevance_score": round(min(100.0, 50.0 + 10.0 * len(offset_ids)), 2), "matching_factors": ["event type", "depth interval"] + (["formation match"] if any(record.get("formation_match", True) for record in records) else []), "data_completeness": round(sum(value is not None for record in records for value in (record.get("source_document_id"), record.get("offset_well_id"), record.get("interval"))) / (3 * len(records)), 2), "explanation": "Historical offset evidence is approaching or within this measured-depth interval; it is not a prediction that an incident will occur."})
    return sorted(alerts, key=lambda item: (item["distance_to_interval_m"], item["event_type"], item["dedupe_key"]))
