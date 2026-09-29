# WELLSAGE AI

WELLSAGE AI is a local, decision-support prototype for Smart India Hackathon problem statement 26121: Nearby Wells Intelligence System (NWIS).

> **Safety boundary:** All bundled records are deterministic synthetic demo data. Alerts describe historical hazard proximity only; they are not failure probabilities, drilling instructions, or an operational safety system.

## Quick start

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python ..\scripts\generate_demo_data.py
python ..\scripts\seed_database.py
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend defaults to `http://localhost:8000`; set `VITE_API_URL` in `frontend/.env` to override it.

## Demo flow

1. Open the dashboard and select one of the three synthetic active-well scenarios.
2. Review the ranked offsets and expand a row to see score factors, missing fields, and provenance.
3. Use the depth stepper to cross a historical incident interval and observe the alert state change.
4. Explore incidents, filter by severity or formation, and inspect source pages.
5. Upload a PDF or TXT report. Text is extracted locally, then candidate incident lines are shown for review before insertion.

## Architecture

- `backend/app`: FastAPI routes, SQLAlchemy models, deterministic scoring, alert engine, document extraction, and seed generation.
- `frontend/src`: typed API client, responsive dashboard, Leaflet map, Recharts depth correlation, incident explorer, upload review, and simulation controls.
- `data`: data dictionary and generated demo database location.
- `tests`: backend unit and API tests.

The core API is documented at `http://localhost:8000/docs`.

## API highlights

- `GET /api/health`
- `GET /api/scenarios`
- `GET /api/dashboard?scenario_id=scenario-1`
- `GET /api/wells?scenario_id=scenario-1&radius_km=20`
- `GET /api/incidents?...filters...`
- `GET /api/correlation?scenario_id=scenario-1`
- `POST /api/simulation/{action}` where action is `start`, `pause`, `step`, or `reset`
- `POST /api/documents/upload`
- `GET /api/documents`
- `GET /api/documents/{document_id}`
- `POST /api/documents/{document_id}/extract`
- `GET /api/documents/{document_id}/viewer`
- `GET /api/search?q=kick`
- `GET /api/wells/{well_id}/offsets?radius_km=20&target_depth_m=1200-1400&formation=Barail`

## Synthetic dataset schema

`data/synthetic/` contains reproducible JSON for wells, formations, events, scenarios, and report metadata, plus watermarked TXT reports. `scripts/generate_demo_data.py` uses seed `26121` and targets the explicitly fictional **Kanchan Ridge Demo Region**. Every generated record has `is_synthetic=true`; no Oil India identifiers or real operational records are used.

Events use `event_type`, `start_depth_m`, `end_depth_m`, `severity`, `description`, `recorded_mitigation`, `formation`, `source_document_id`, and `source_page`. Supported categories are `lost_circulation`, `kick`, `stuck_pipe`, `torque_drag`, `pressure_anomaly`, `cementing_issue`, `fishing`, and `npt`.

Seeding is idempotent and preserves non-demo rows. `--reset` requires the explicit `--confirm-reset-demo` flag and only deletes rows marked synthetic or using demo IDs. Uploaded documents are hashed to reject duplicate imports. Extracted values remain `needs_review` with confidence scores; extraction is not verification.

## Offset scoring example

The offset endpoint accepts a depth range such as `target_depth_m=1200-1400`. Geographic proximity uses the documented linear decay `max(0, 1 - distance_km / radius_km)`. The prototype defaults are unvalidated demo weights: geographic `0.25`, formation `0.30`, depth `0.20`, trajectory `0.10`, and event relevance `0.15`. Missing features are removed from the denominator and the remaining weighted score is normalized to `0..100`; this is not a scientific risk or failure probability.

## Tests

```powershell
pip install -r backend/requirements.txt
pytest
```

The backend foundation is organized under `backend/app/core`, `backend/app/db`, `backend/app/models`, `backend/app/schemas`, `backend/app/api/routes`, `backend/app/services`, and `backend/app/repositories`. The current prototype uses a reliable `Base.metadata.create_all()` startup strategy for local/demo operation; replace it with Alembic revisions before production deployment. The canonical API contracts are paginated: `GET /api/wells`, `GET /api/wells/{well_id}`, `GET /api/wells/{well_id}/events`, and `GET /api/events/search`.

## Limitations

The demo uses synthetic coordinates, formations, events, and report text. Map tiles are optional: the interface still renders the well table and a coordinate plot when tiles are unavailable. SQLite FTS5 is used for local search. OCR is intentionally optional and scanned PDFs are marked `scanned_unreadable` when no text layer is available. Semantic search, Alembic migrations, and external LLMs remain outside this offline prototype.
