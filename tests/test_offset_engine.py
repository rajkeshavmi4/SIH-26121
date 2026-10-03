from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.offset_engine import ScoringConfig, TargetInterval, distance_km, rank_offsets
client = TestClient(app)
def well(identifier, latitude=0.0, longitude=0.0, formation="Barail", trajectory="vertical", incidents=None, formations=None):
    return SimpleNamespace(id=identifier, name=identifier, latitude=latitude, longitude=longitude, formation=formation, trajectory=trajectory, incidents=incidents or [], formations=formations or [], total_depth_m=3000)
def event(event_type="kick", top=1000, bottom=1200):
    return SimpleNamespace(event_type=event_type, start_depth_m=top, end_depth_m=bottom)
def formation(name="Barail", top=900, base=1300):
    return SimpleNamespace(name=name, top_depth_m=top, base_depth_m=base)
def test_haversine_identical_coordinates_and_known_distance():
    assert distance_km(27.0, 95.0, 27.0, 95.0) == 0
    assert 111.0 < distance_km(0.0, 0.0, 1.0, 0.0) < 111.3
def test_radius_boundary_is_included_and_outside_is_excluded():
    active = well("active")
    boundary = well("boundary", longitude=1.0)
    result = rank_offsets(active, [boundary], 111.2, TargetInterval(1000, 1200))
    assert [item["well_id"] for item in result["items"]] == ["boundary"]
    outside = rank_offsets(active, [boundary], 111.0, TargetInterval(1000, 1200))
    assert outside["items"] == []
    assert "outside search radius" in outside["excluded"][0]["reason"]
def test_formation_mapping_matches_and_unknown_is_missing():
    active = well("active", formation="Barail Group")
    mapped = well("mapped", formation="barail")
    unknown = well("unknown", formation="Uncatalogued")
    mapped_result = rank_offsets(active, [mapped], 20, TargetInterval(1000, 1200))
    assert mapped_result["items"][0]["score_breakdown"]["formation"] == 1
    assert mapped_result["items"][0]["matching_formations"] == ["barail"]
    unknown_result = rank_offsets(active, [unknown], 20, TargetInterval(1000, 1200))
    assert "formation" in unknown_result["items"][0]["missing_fields"]
def test_missing_features_are_renormalized_and_trajectory_is_unavailable():
    active = well("active", trajectory="deviated")
    candidate = well("candidate", trajectory=None, formations=[formation()])
    result = rank_offsets(active, [candidate], 20, TargetInterval(1000, 1200))["items"][0]
    assert "trajectory" in result["missing_fields"]
    assert result["weight_total_used"] == pytest.approx(0.75)
    assert result["data_completeness"] == pytest.approx(0.6)
    assert 0 <= result["relevance_score"] <= 100
def test_perfect_features_produce_manual_expected_score_of_100():
    active = well("active")
    candidate = well("candidate", incidents=[event()], formations=[formation()])
    result = rank_offsets(active, [candidate], 20, TargetInterval(1000, 1200))["items"][0]
    assert result["relevance_score"] == 100
    assert result["relevant_event_count"] == 1
    assert result["score_breakdown"] == {"geographic": 1.0, "formation": 1.0, "depth": 1.0, "trajectory": 1.0, "event_relevance": 1.0}
def test_active_invalid_and_empty_candidates_are_explicit():
    active = well("active")
    invalid = well("invalid", latitude=91)
    result = rank_offsets(active, [active, invalid], 20, TargetInterval(1000, 1200))
    assert result["items"] == []
    reasons = {item["well_id"]: item["reason"] for item in result["excluded"]}
    assert "active well is excluded" in reasons["active"]
    assert "invalid coordinates" in reasons["invalid"]
    assert rank_offsets(active, [], 20, TargetInterval(1000, 1200))["items"] == []
def test_deterministic_ranking_and_weight_validation():
    active = well("active")
    candidates = [well("z", longitude=0.001), well("a", longitude=0.001)]
    result = rank_offsets(active, candidates, 20, TargetInterval(1000, 1200))
    assert [item["well_id"] for item in result["items"]] == ["a", "z"]
    with pytest.raises(ValueError, match="sum to 1.0"):
        ScoringConfig(weights={"geographic": 1, "formation": 0, "depth": 0, "trajectory": 0, "event_relevance": 0.1})
def test_offsets_api_returns_breakdown_and_exclusions():
    if not client.get("/api/wells?page_size=1").json()["items"]:
        pytest.skip("offset API integration requires the seeded demo database")
    response = client.get("/api/wells/active-volve-1/offsets?radius_km=50&target_depth_m=1000-1400&limit=3")
    assert response.status_code == 200
    payload = response.json()
    assert payload["weight_note"].startswith("Unvalidated")
    assert all("score_breakdown" in item and item["well_id"] != "active-volve-1" for item in payload["items"])
