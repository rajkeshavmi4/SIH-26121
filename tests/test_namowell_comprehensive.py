import os
os.environ["DATABASE_URL"] = "sqlite:///./test_namowell.db"

import pytest
from fastapi.testclient import TestClient
from backend.app.db import Base, engine
from backend.app.main import app
from backend.app.services.tvd_engine import tvd_engine
from backend.app.services.ocr_service import ocr_pipeline
from backend.app.services.witsml_adapter import witsml_adapter
from backend.app.services.ml_pipeline import ml_pipeline
from scripts.seed_database import seed

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
seed(reset=True, confirm_reset_demo=True)

client = TestClient(app)

def test_tvd_minimum_curvature():
    points = [
        {"measured_depth_m": 0, "inclination_deg": 0, "azimuth_deg": 0},
        {"measured_depth_m": 500, "inclination_deg": 10, "azimuth_deg": 45},
        {"measured_depth_m": 1000, "inclination_deg": 20, "azimuth_deg": 45}
    ]
    computed = tvd_engine.compute_minimum_curvature(points)
    assert len(computed) == 3
    assert computed[-1]["true_vertical_depth_m"] > 900.0

def test_ocr_pipeline():
    text = "Page 1 report\nKick observed at 1800 m in Barail formation\nPage 2 report\nLost circulation at 2400 m"
    res = ocr_pipeline.process_text_or_file(text, "synthetic_report.txt")
    assert res["page_count"] >= 1
    assert len(res["evidence"]) >= 1

def test_witsml_adapter():
    conn = witsml_adapter.connect_etp_session()
    assert conn["status"] == "CONNECTED"
    sub = witsml_adapter.subscribe_channel("well-1", "WOB")
    assert sub["status"] == "SUBSCRIBED"

def test_ml_pipeline():
    res = ml_pipeline.train_baseline_model(synthetic_samples=100)
    assert res["accuracy"] >= 0.70
    pred = ml_pipeline.predict_hazard({"wob": 14.0, "rpm": 110.0, "torque": 22.0, "rop_mhr": 10.0, "ecd_sg": 1.35, "spp_kpa": 22000.0, "mse_mj_m3": 900.0})
    assert pred["predicted_hazard"] in ["NORMAL", "KICK_RISK", "STUCK_PIPE_RISK"]
    assert len(pred["explainability"]) > 0

def test_api_v1_endpoints():
    r1 = client.get("/api/v1/scenarios")
    assert r1.status_code == 200
    
    r2 = client.get("/api/v1/wells")
    assert r2.status_code == 200

    r3 = client.get("/api/v1/audit-trail")
    assert r3.status_code == 200

    r4 = client.post("/api/v1/benchmark/run", json={"scenario_id": "scenario-1"})
    assert r4.status_code == 200
    assert r4.json()["grade"] in ["EXCELLENT", "GOOD", "ACCEPTABLE"]
