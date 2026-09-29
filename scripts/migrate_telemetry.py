from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.db import engine
from sqlalchemy import inspect, text
NEW_COLUMNS = [
    ("flow_rate_lpm", "FLOAT"),
    ("standpipe_pressure_kpa", "FLOAT"),
    ("rop_mhr", "FLOAT"),
    ("ecd_kgL", "FLOAT"),
    ("mwd_inclination", "FLOAT"),
    ("mwd_azimuth", "FLOAT"),
]
def migrate() -> None:
    inspector = inspect(engine)
    existing = {col["name"] for col in inspector.get_columns("telemetry")}
    with engine.begin() as conn:
        for col_name, col_type in NEW_COLUMNS:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE telemetry ADD COLUMN {col_name} {col_type}"))
                print(f"Added column: telemetry.{col_name}")
            else:
                print(f"Column already exists: telemetry.{col_name}")
    print("Migration complete.")
if __name__ == "__main__":
    migrate()
