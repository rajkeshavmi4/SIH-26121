import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.app.main import app
from backend.app.schemas import EventResponse
client = TestClient(app)
def test_health_reports_database():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"
def test_well_listing_is_paginated_and_typed():
    response = client.get("/api/wells?page=1&page_size=2")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) <= 2
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["page_size"] == 2
    assert "total" in payload["meta"]
def test_missing_well_is_a_clear_404():
    response = client.get("/api/wells/does-not-exist")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
def test_event_schema_rejects_invalid_depth_interval():
    with pytest.raises(ValidationError, match="depth interval"):
        EventResponse(id="e", external_id=None, well_id="w", event_type="kick", original_event_type=None, start_depth_m=500, end_depth_m=400, formation_name="Barail", severity="high", description=None, recorded_mitigation="", source_document_id=None, source_page=None, extraction_status="verified", data_origin="uploaded", is_synthetic=False, created_at="2026-01-01T00:00:00Z")
