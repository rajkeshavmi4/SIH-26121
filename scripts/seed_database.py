from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
from sqlalchemy import delete, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.db import Base, SessionLocal, engine
from backend.app.models import Incident, Scenario, Well, CasingData, CementingData, MudData, BHAData, TrajectoryData, FormationData, ReviewItem

DATA = ROOT / "data" / "synthetic"

def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def seed(reset: bool = False, confirm_reset_demo: bool = False) -> None:
    if reset and not confirm_reset_demo:
        raise SystemExit("Refusing reset: pass --confirm-reset-demo to delete synthetic demo rows")
    
    Base.metadata.create_all(engine)
    wells = load("wells.json")
    
    with SessionLocal() as db:
        if reset:
            demo_well_ids = [row["id"] for row in wells]
            db.execute(delete(Incident).where(Incident.is_synthetic.is_(True)))
            db.execute(delete(Scenario).where(Scenario.id.like("scenario-%")))
            db.execute(delete(Well).where(Well.id.in_(demo_well_ids)))
            db.execute(delete(CasingData))
            db.execute(delete(CementingData))
            db.execute(delete(MudData))
            db.execute(delete(BHAData))
            db.execute(delete(TrajectoryData))
            db.execute(delete(FormationData))
            db.execute(delete(ReviewItem))
            db.commit()

        for row in wells:
            if db.get(Well, row["id"]):
                continue
            
            well_obj = Well(
                id=row["id"],
                name=row["name"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                total_depth_m=row["total_depth_m"],
                formation=row["formation"],
                trajectory=row.get("trajectory"),
                status=row.get("status", "historical"),
                is_synthetic=row.get("is_synthetic", False),
                demo_label="Namowell Volve demo"
            )
            db.add(well_obj)
            db.flush()

            db.add(CasingData(well_id=row["id"], outer_diameter_in=9.625, inner_diameter_in=8.835, shoe_tvd_m=1200.0, shoe_md_m=1250.0, weight_ppf=40.0, grade="N-80", collapse_psi=4950.0, burst_psi=5750.0))
            db.add(CementingData(well_id=row["id"], slurry_density_sg=1.90, top_of_cement_m=200.0, bottom_of_cement_m=1200.0, compressive_strength_psi=3500.0, displacement_bbl=180.0))
            db.add(MudData(well_id=row["id"], depth_m=1500.0, mud_type="WBM", mud_weight_sg=1.25, pv_cp=18.0, yp_lb_100ft2=22.0, gel_10s_lb=8.0, gel_10m_lb=14.0, ecd_sg=1.31, ph=9.5, filtrate_ml=4.5))
            db.add(BHAData(well_id=row["id"], top_depth_m=1400.0, bottom_depth_m=1500.0, bit_diameter_in=8.5, bit_type="PDC", mwd_lwd_tools="Gamma-Resistivity-Sonic", motor_rss_flag="RSS", max_wob_kda=25.0, collar_od_in=6.75))

            for md in [0.0, 500.0, 1000.0, 1500.0, 2000.0, 2500.0, 3000.0]:
                inc = 0.0 if md < 500 else (md - 500) * 0.015
                azi = 45.0
                tvd = md * 0.95 if md > 500 else md
                db.add(TrajectoryData(well_id=row["id"], measured_depth_m=md, inclination_deg=inc, azimuth_deg=azi, true_vertical_depth_m=tvd, dogleg_severity_deg100ft=1.2, northing_m=md*0.1, easting_m=md*0.1))

            formations = ["Hordaland", "Grid", "Sele", "Lista", "Heimdal", "Maureen"]
            for idx, fname in enumerate(formations):
                top_m = idx * 500.0
                bot_m = (idx + 1) * 500.0
                db.add(FormationData(
                    well_id=row["id"],
                    formation_name=fname,
                    top_tvd_m=top_m * 0.95,
                    bottom_tvd_m=bot_m * 0.95,
                    top_md_m=top_m,
                    bottom_md_m=bot_m,
                    lithology="Shale/Sandstone",
                    pore_pressure_sg=1.15 + idx * 0.03,
                    frac_gradient_sg=1.65 + idx * 0.04,
                    permeability_md=45.0,
                    porosity_pct=18.5,
                    ucs_psi=6500.0
                ))

        for row in load("scenarios.json"):
            if not db.get(Scenario, row["id"]):
                db.add(Scenario(**{key: value for key, value in row.items() if key != "is_synthetic"}))

        events = load("events.json")
        for row in events:
            if db.get(Incident, row["id"]):
                continue
            
            db.add(Incident(
                id=row["id"],
                well_id=row["well_id"],
                event_type=row["event_type"],
                top_depth_m=row.get("start_depth_m", row.get("top_depth_m", 1000.0)),
                bottom_depth_m=row.get("end_depth_m", row.get("bottom_depth_m", 1050.0)),
                formation=row.get("formation", "Hordaland"),
                severity=row.get("severity", "MEDIUM"),
                mitigation=row.get("recorded_mitigation", row.get("mitigation", "Standard procedure")),
                source_document=row.get("source_document_id", "volve_ddr_01.txt"),
                source_page=row.get("source_page", 1),
                bounding_box=json.dumps([0.15, 0.05, 0.25, 0.95]),
                snippet=row.get("description", "Event snippet"),
                confidence=0.95,
                source_type="real_dataset",
                is_synthetic=row.get("is_synthetic", False),
                approval_status="APPROVED"
            ))

        if not db.get(ReviewItem, "rev-001"):
            db.add(ReviewItem(
                id="rev-001",
                entity_type="INCIDENT_EXTRACTION",
                entity_id="evt-demo-101",
                status="PENDING_REVIEW",
                payload_json=json.dumps({"event_type": "kick", "depth_m": 1820.0, "formation": "Barail", "confidence": 0.82})
            ))

        db.commit()
        print(f"Namowell demo seed complete: {len(wells)} wells, full engineering models, scenarios, incidents, and pending review item.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Delete synthetic demo rows before reseeding")
    parser.add_argument("--confirm-reset-demo", action="store_true", help="Required with --reset")
    args = parser.parse_args()
    seed(args.reset, args.confirm_reset_demo)
