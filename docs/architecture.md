# Architecture

```text
React/Vite dashboard
        |
        | typed fetch client
        v
FastAPI route layer -> domain services (scoring, alerts, ingestion)
        |
        v
SQLAlchemy 2 -> SQLite demo store
```

The route layer only translates HTTP inputs and outputs. Ranking and alert behavior lives in `backend/app/scoring.py` and `backend/app/alerts.py`, so the highest-risk behavior can be tested without a server. Ingestion extracts report text and returns reviewable candidates; it does not silently create incidents. Every bundled record has synthetic provenance.
        
For scanned PDFs, ingestion first prefers the native text layer and then attempts optional Tesseract OCR through `pytesseract`. OCR output remains `needs_review` and must be approved before it can become an operational event. A production eRTMAC connector is intentionally left as an authenticated adapter boundary; no vendor protocol is assumed by this offline prototype.
