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
