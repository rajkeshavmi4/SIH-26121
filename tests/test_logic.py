from types import SimpleNamespace
from backend.app.alerts import build_alerts, interval_distance
from backend.app.scoring import distance_km, rank_offset
def test_interval_distance_and_upcoming_alert():
    incident = SimpleNamespace(top_depth_m=1200, bottom_depth_m=1300, formation="Barail", severity="high", event_type="kick", well_id="w", id="i", mitigation="review", source_document="demo.pdf", source_page=1, source_type="synthetic", is_synthetic=True)
    assert interval_distance(1000, 1200, 1300) == 200
    assert build_alerts(1000, [incident], 300)[0]["status"] == "upcoming"
    assert build_alerts(1700, [incident], 300) == []
def test_haversine_and_explainable_score():
    active = SimpleNamespace(latitude=27.4, longitude=95.3, total_depth_m=3000, formation="Barail", trajectory="deviated")
    candidate = SimpleNamespace(latitude=27.41, longitude=95.31, total_depth_m=2900, formation="Barail", trajectory=None)
    result = rank_offset(active, candidate, 3)
    assert 0 < distance_km(27.4, 95.3, 27.41, 95.31) < 2
    assert result["relevance_score"] > 50
    assert "trajectory similarity unavailable" in result["missing_fields"]
