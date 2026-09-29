from .models import Incident
def interval_distance(depth: float, top: float, bottom: float) -> float:
    if top <= depth <= bottom:
        return 0.0
    return top - depth if depth < top else depth - bottom
def build_alerts(depth: float, incidents: list[Incident], lookahead_m: float = 300.0) -> list[dict]:
    alerts = []
    for incident in incidents:
        distance = interval_distance(depth, incident.top_depth_m, incident.bottom_depth_m)
        if distance <= lookahead_m:
            status = "within interval" if distance == 0 else "upcoming"
            alerts.append({"incident": incident, "status": status, "distance_to_interval_m": distance, "relevance_factors": [f"depth interval {incident.top_depth_m:.0f}-{incident.bottom_depth_m:.0f} m", f"formation match: {incident.formation}", f"severity: {incident.severity}"], "data_completeness": ["event type", "depth interval", "formation", "mitigation", "source page"]})
    return sorted(alerts, key=lambda item: (item["distance_to_interval_m"], item["incident"].severity))
