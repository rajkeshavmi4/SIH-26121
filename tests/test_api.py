import os
os.environ["DATABASE_URL"] = "sqlite:///./test_wellsage.db"
from fastapi.testclient import TestClient
from backend.app.db import Base, engine
from backend.app.main import app
from backend.app.seed import seed
Base.metadata.drop_all(engine)
seed()
client = TestClient(app)
def test_dashboard_and_simulation():
    response = client.get("/api/dashboard?scenario_id=scenario-1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["active_well"]["provenance"]["is_synthetic"] is True
    assert len(payload["offsets"]) > 0
    before = payload["scenario"]["current_depth_m"]
    after = client.post("/api/simulation/step?scenario_id=scenario-1").json()
    assert after["current_depth_m"] > before
def test_incident_filters_and_upload():
    assert client.get("/api/incidents?severity=high").status_code == 200
    response = client.post("/api/documents/upload", files={"file": ("report.txt", b"kick observed at 1200-1300 m in Barail", "text/plain")})
    assert response.status_code == 200
    assert response.json()["candidates"][0]["top_depth_m"] == 1200
