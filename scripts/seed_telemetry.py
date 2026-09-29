from __future__ import annotations
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.db import Base, SessionLocal, engine
from backend.app.models import Telemetry, Well
def seed_telemetry(reset: bool = False) -> None:
    Base.metadata.create_all(engine)
    active_well_ids = ["active-demo-1", "active-demo-2", "active-demo-3"]
    rng = random.Random(42)
    with SessionLocal() as db:
        if reset:
            for well_id in active_well_ids:
                rows = db.query(Telemetry).filter(Telemetry.well_id == well_id).all()
                for row in rows:
                    db.delete(row)
            db.commit()
        for well_id in active_well_ids:
            existing = db.query(Telemetry).filter(Telemetry.well_id == well_id).count()
            if existing > 0:
                print(f"  Skipping {well_id}: {existing} records already exist")
                continue
            well = db.get(Well, well_id)
            if not well:
                print(f"  Skipping {well_id}: well not found")
                continue
            is_deviated = well.trajectory == "deviated"
            base_depth = 500.0
            num_records = 45
            step = 50.0
            base_time = datetime.now(timezone.utc) - timedelta(hours=num_records)
            records = []
            for i in range(num_records):
                depth = base_depth + i * step
                progress = i / max(num_records - 1, 1)
                wob = 70 + 60 * progress + rng.gauss(0, 5)
                rpm = 90 + 20 * math.sin(progress * math.pi) + rng.gauss(0, 4)
                torque = 12 + 8 * progress + rng.gauss(0, 1.5)
                flow_rate = 2200 + rng.gauss(0, 150)
                spp = 18000 + 4000 * progress + rng.gauss(0, 500)
                rop = max(0.5, 10 - 5 * progress + rng.gauss(0, 1.5))
                ecd = 1.4 + 0.2 * progress + rng.gauss(0, 0.02)
                inclination = (min(28, 2 * i) + rng.gauss(0, 0.5)) if is_deviated else rng.uniform(0, 2)
                azimuth = (45 + 0.5 * i + rng.gauss(0, 1)) % 360 if is_deviated else rng.uniform(0, 360)
                records.append(Telemetry(
                    well_id=well_id,
                    timestamp=base_time + timedelta(hours=i),
                    measured_depth_m=round(depth, 1),
                    wob=round(max(10, wob), 2),
                    rpm=round(max(20, rpm), 2),
                    torque=round(max(1, torque), 3),
                    flow_rate_lpm=round(max(100, flow_rate), 1),
                    pressure=round(spp * 0.145038, 2),
                    mud_flow_rate=round(max(100, flow_rate), 1),
                    rop_mhr=round(max(0.1, rop), 3),
                    ecd_kgL=round(max(1.0, ecd), 4),
                    standpipe_pressure_kpa=round(max(5000, spp), 1),
                    mwd_inclination=round(max(0, inclination), 3),
                    mwd_azimuth=round(azimuth, 3),
                    data_origin="synthetic",
                    is_synthetic=True,
                ))
            db.add_all(records)
            db.commit()
            print(f"  Seeded {len(records)} telemetry records for {well_id} ({well.name})")
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    print("Seeding telemetry data...")
    seed_telemetry(reset=args.reset)
    print("Done.")
