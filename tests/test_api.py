import os
os.environ["DATABASE_URL"] = "sqlite:///./test_namowell.db"

from fastapi.testclient import TestClient
from backend.app.db import Base, engine
from backend.app.main import app
from scripts.seed_database import seed

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
seed(reset=True, confirm_reset_demo=True)

client = TestClient(app)

def test_dashboard_and_simulation():
    response = client.get("/api/dashboard?scenario_id=scenario-1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["active_well"]["provenance"]["is_synthetic"] is True
    before = payload["scenario"]["current_depth_m"]
    after = client.post("/api/simulation/step?scenario_id=scenario-1").json()
    assert after["current_depth_m"] >= before

def test_v1_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["service"] == "namowell-ai"
