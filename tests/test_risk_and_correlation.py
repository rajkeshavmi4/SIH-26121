from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.depth_correlation import distance_to_interval, interval_overlap, interval_status
from backend.app.services.risk_engine import evaluate_alerts
client = TestClient(app)
def evidence(event_id, event_type="kick", top=1000, bottom=1100, well_id="offset-1", document_id=1, severity="medium"):
    return {"event_id": event_id, "event_type": event_type, "offset_well_id": well_id, "source_document_id": document_id, "severity": severity, "interval": [top, bottom]}
def test_exact_interval_and_lookahead_boundaries():
    assert distance_to_interval(1000, 1000, 1100) == 0
    assert interval_status(1000, 1000, 1100) == "in_zone"
    assert interval_status(900, 1000, 1100, 100) == "upcoming"
    assert interval_status(899.9, 1000, 1100, 100) == "outside"
    assert interval_status(1100, 1000, 1100) == "in_zone"
    assert interval_status(1100.01, 1000, 1100) == "passed"
def test_point_overlap_and_no_historical_events():
    assert interval_overlap(1050, 1050, 1000, 1100) == 1
    assert evaluate_alerts("active", 500, [], 100) == []
def test_alert_lifecycle_approach_entry_and_exit():
    record = evidence("event-1", top=1000, bottom=1100)
    assert evaluate_alerts("active", 899, [record], 100) == []
    upcoming = evaluate_alerts("active", 900, [record], 100)[0]
    assert upcoming["status"] == "upcoming"
    assert upcoming["distance_to_interval_m"] == 100
    assert evaluate_alerts("active", 1000, [record], 100)[0]["status"] == "in_zone"
    assert evaluate_alerts("active", 1101, [record], 100)[0]["status"] == "passed"
def test_overlapping_intervals_deduplicate_and_aggregate_offset_evidence():
    alerts = evaluate_alerts("active", 1050, [evidence("e1", top=1000, bottom=1100, well_id="offset-a", document_id=2), evidence("e2", top=1050, bottom=1150, well_id="offset-b", document_id=3, severity="high")])
    assert len(alerts) == 1
    assert alerts[0]["interval_start_m"] == 1000
    assert alerts[0]["interval_end_m"] == 1150
    assert alerts[0]["offset_well_ids"] == ["offset-a", "offset-b"]
    assert alerts[0]["source_document_ids"] == [2, 3]
    assert alerts[0]["severity"] == "high"
    assert alerts[0]["evidence_event_ids"] == ["e1", "e2"]
def test_different_event_types_are_not_deduplicated():
    alerts = evaluate_alerts("active", 1050, [evidence("e1", event_type="kick"), evidence("e2", event_type="stuck_pipe")])
    assert {alert["event_type"] for alert in alerts} == {"kick", "stuck_pipe"}
def test_correlation_api_and_deterministic_simulation():
    wells = client.get("/api/wells?page_size=1").json()["items"]
    if not wells:
        pytest.skip("integration requires the seeded demo database")
    correlation = client.get("/api/wells/active-demo-1/correlation?current_depth_m=1000&lookahead_m=100")
    assert correlation.status_code == 200
    assert "event_markers" in correlation.json()
    first = client.get("/api/simulation/state?scenario_id=scenario-1").json()["current_depth_m"]
    stepped = client.post("/api/simulation/step?scenario_id=scenario-1").json()["current_depth_m"]
    assert stepped == first + 100
    reset = client.post("/api/simulation/reset?scenario_id=scenario-1").json()["current_depth_m"]
    assert reset < stepped
