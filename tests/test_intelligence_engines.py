from __future__ import annotations
import pytest
from backend.app.services.anomaly_detector import detect_anomalies
from backend.app.services.offset_engine import TargetInterval, distance_km, rank_offsets, ScoringConfig
def make_record(**kwargs):
    defaults = {
        "measured_depth_m": 1000.0,
        "wob": 80.0,
        "rpm": 90.0,
        "torque": 15.0,
        "mud_flow_rate": 2000.0,
        "rop_mhr": 5.0,
        "ecd_kgL": 1.45,
        "standpipe_pressure_kpa": 18000.0,
    }
    defaults.update(kwargs)
    return defaults
class TestAnomalyDetector:
    def test_no_anomalies_normal_values(self):
        records = [make_record()]
        result = detect_anomalies(records)
        assert result == []
    def test_high_torque_detected(self):
        records = [make_record(torque=28.0)]
        result = detect_anomalies(records)
        assert any(item["anomaly_type"] == "high_torque" for item in result)
        assert all(item["event_type"] in ("torque_drag", "stuck_pipe", "pressure_anomaly", "lost_circulation") for item in result)
    def test_low_flow_rate_detected(self):
        records = [make_record(mud_flow_rate=200.0)]
        result = detect_anomalies(records)
        assert any(item["anomaly_type"] == "low_flow_rate" for item in result)
        anomaly = next(item for item in result if item["anomaly_type"] == "low_flow_rate")
        assert anomaly["severity"] == "critical"
    def test_high_ecd_detected(self):
        records = [make_record(ecd_kgL=1.95)]
        result = detect_anomalies(records)
        assert any(item["anomaly_type"] == "high_ecd" for item in result)
    def test_high_standpipe_pressure(self):
        records = [make_record(standpipe_pressure_kpa=30000.0)]
        result = detect_anomalies(records)
        assert any(item["anomaly_type"] == "high_standpipe_pressure" for item in result)
    def test_missing_parameter_skipped(self):
        records = [{"measured_depth_m": 500.0}]
        result = detect_anomalies(records)
        assert result == []
    def test_multiple_anomalies_sorted_by_severity(self):
        records = [make_record(torque=28.0, mud_flow_rate=100.0, ecd_kgL=1.9)]
        result = detect_anomalies(records)
        assert len(result) >= 2
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        severities = [severity_order.get(item["severity"], 4) for item in result]
        assert severities == sorted(severities)
    def test_empty_records(self):
        assert detect_anomalies([]) == []
    def test_borderline_torque_not_triggered(self):
        records = [make_record(torque=24.9)]
        result = detect_anomalies(records)
        assert not any(item["anomaly_type"] == "high_torque" for item in result)
class TestDistanceCalculation:
    def test_same_point_is_zero(self):
        assert distance_km(26.84, 91.73, 26.84, 91.73) == pytest.approx(0.0, abs=1e-6)
    def test_known_distance_positive(self):
        d = distance_km(0, 0, 1, 0)
        assert 110 < d < 112
    def test_symmetry(self):
        d1 = distance_km(26.84, 91.73, 26.93, 91.80)
        d2 = distance_km(26.93, 91.80, 26.84, 91.73)
        assert d1 == pytest.approx(d2, rel=1e-6)
class TestOffsetRanking:
    def _make_well(self, well_id, lat, lon, formation="Barail", trajectory="vertical", depth=3000.0, incidents=None, formations=None):
        class MockWell:
            id = well_id
            latitude = lat
            longitude = lon
            total_depth_m = depth
            pass
        w = MockWell()
        w.formation = formation
        w.trajectory = trajectory
        w.total_depth_m = depth
        w.incidents = incidents or []
        w.formations = formations or []
        return w
    def test_active_well_excluded(self):
        active = self._make_well("active-1", 26.84, 91.73)
        candidates = [active, self._make_well("offset-1", 26.85, 91.74)]
        result = rank_offsets(active, candidates, 50.0, TargetInterval(1000, 2000))
        ids = [item["well_id"] for item in result["items"]]
        assert "active-1" not in ids
    def test_outside_radius_excluded(self):
        active = self._make_well("active-1", 26.84, 91.73)
        far_well = self._make_well("far-1", 50.0, 10.0)
        result = rank_offsets(active, [far_well], 50.0, TargetInterval(1000, 2000))
        assert len(result["items"]) == 0
        assert len(result["excluded"]) == 1
    def test_scores_sum_valid(self):
        active = self._make_well("active-1", 26.84, 91.73, formation="Barail")
        close_well = self._make_well("offset-1", 26.85, 91.74, formation="Barail")
        result = rank_offsets(active, [close_well], 50.0, TargetInterval(1000, 2000))
        assert len(result["items"]) == 1
        score = result["items"][0]["relevance_score"]
        assert 0 <= score <= 100
    def test_formation_match_boosts_score(self):
        active = self._make_well("active-1", 26.84, 91.73, formation="Barail")
        matching = self._make_well("match-1", 26.85, 91.74, formation="Barail")
        non_matching = self._make_well("no-match-1", 26.85, 91.74, formation="Girujan")
        result = rank_offsets(active, [matching, non_matching], 50.0, TargetInterval(1000, 2000))
        items = {item["well_id"]: item for item in result["items"]}
        assert items["match-1"]["relevance_score"] >= items["no-match-1"]["relevance_score"]
    def test_custom_weights_must_sum_to_one(self):
        with pytest.raises(ValueError):
            ScoringConfig(weights={"geographic": 0.5, "formation": 0.5, "depth": 0.1, "trajectory": 0.1, "event_relevance": 0.1})
    def test_missing_fields_reported(self):
        active = self._make_well("active-1", 26.84, 91.73, formation="Barail")
        candidate = self._make_well("offset-1", 26.85, 91.74, formation=None)
        result = rank_offsets(active, [candidate], 50.0, TargetInterval(1000, 2000))
        if result["items"]:
            assert "formation" in result["items"][0]["missing_fields"]
    def test_results_sorted_by_score_descending(self):
        active = self._make_well("active-1", 26.84, 91.73, formation="Barail")
        wells = [self._make_well(f"w-{i}", 26.84 + i * 0.01, 91.73 + i * 0.01) for i in range(1, 6)]
        result = rank_offsets(active, wells, 200.0, TargetInterval(1000, 2000))
        scores = [item["relevance_score"] for item in result["items"]]
        assert scores == sorted(scores, reverse=True)
