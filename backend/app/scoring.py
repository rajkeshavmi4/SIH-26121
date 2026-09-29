from math import asin, cos, radians, sin, sqrt
from .models import Well
def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    value = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(value))
def rank_offset(active: Well, candidate: Well, incident_count: int) -> dict:
    distance = distance_km(active.latitude, active.longitude, candidate.latitude, candidate.longitude)
    proximity = max(0.0, 1.0 - min(distance / 20.0, 1.0))
    formation = 1.0 if active.formation == candidate.formation else 0.35
    depth_overlap = min(active.total_depth_m, candidate.total_depth_m) / max(active.total_depth_m, candidate.total_depth_m)
    trajectory = 1.0 if active.trajectory and candidate.trajectory and active.trajectory == candidate.trajectory else 0.5
    history = min(1.0, incident_count / 4.0)
    score = round(100 * (0.30 * proximity + 0.25 * formation + 0.20 * depth_overlap + 0.10 * trajectory + 0.15 * history), 1)
    missing = []
    if not active.trajectory or not candidate.trajectory:
        missing.append("trajectory similarity unavailable")
    return {"distance_km": round(distance, 2), "relevance_score": score, "score_factors": {"proximity": round(proximity, 2), "formation": formation, "depth_overlap": round(depth_overlap, 2), "trajectory": trajectory, "event_relevance": round(history, 2)}, "missing_fields": missing}
