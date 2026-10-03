import os
os.environ["DATABASE_URL"] = "sqlite:///./test_namowell.db"

from pathlib import Path
import fitz
from fastapi.testclient import TestClient
from backend.app.db import Base, engine
from backend.app.main import app
from scripts.seed_database import seed

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
seed(reset=True, confirm_reset_demo=True)

client = TestClient(app)

def test_txt_upload_persists_reviewable_document_and_source_view():
    response = client.post("/api/documents/upload", files={"file": ("review.txt", b"kick high at 1200-1300 m; formation: Barail; mitigation: circulate", "text/plain")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["review_status"] == "needs_review"
    assert payload["candidates"][0]["event_type"] == "kick"
    assert 0 <= payload["candidates"][0]["confidence"] <= 1
    document_id = payload["document_id"]
    assert client.get(f"/api/documents/{document_id}/viewer").text.startswith("kick")
    assert client.post(f"/api/documents/{document_id}/extract").status_code == 200

def test_invalid_and_duplicate_documents_are_rejected():
    assert client.post("/api/documents/upload", files={"file": ("report.csv", b"x", "text/csv")}).status_code == 400
    files = {"file": ("duplicate.txt", b"unique duplicate content", "text/plain")}
    assert client.post("/api/documents/upload", files=files).status_code == 200
    assert client.post("/api/documents/upload", files=files).status_code == 409

def test_pdf_extraction_and_missing_depth_remain_reviewable():
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "SYNTHETIC PDF\nformation: Barail; kick high; mitigation: review returns")
    content = pdf.tobytes()
    response = client.post("/api/documents/upload", files={"file": ("report.pdf", content, "application/pdf")})
    assert response.status_code == 200
    assert response.json()["page_count"] == 1
    assert response.json()["candidates"][0]["top_depth_m"] is None
    assert response.json()["review_status"] == "needs_review"

def test_seeded_events_retain_source_document_links():
    response = client.get("/api/events/search?event_type=kick&page_size=1")
    assert response.status_code == 200
    assert response.json()["items"][0]["source_document_id"] is not None
    assert response.json()["items"][0]["source_page"] == 1

def test_synthetic_dataset_is_labeled_and_watermarked():
    root = Path(__file__).resolve().parents[1] / "data" / "synthetic"
    wells = (root / "wells.json").read_text(encoding="utf-8")
    events = (root / "events.json").read_text(encoding="utf-8")
    report = (root / "synthetic_report_01.txt").read_text(encoding="utf-8")
    assert wells.count('"is_synthetic": true') >= 23
    assert events.count('"is_synthetic": true') >= 60
    assert "SYNTHETIC DEMO REPORT" in report
