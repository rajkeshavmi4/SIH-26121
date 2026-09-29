from __future__ import annotations
import json
import random
from pathlib import Path
SEED = 26121
REGION = "Fictional Kanchan Ridge Demo Region"
ROOT = Path(__file__).resolve().parents[1] / "data" / "synthetic"
FORMATIONS = ["Aster", "Banyan", "Cedar", "Dahlia", "Ember", "Flint", "Garnet", "Horizon"]
EVENT_TYPES = ["lost_circulation", "kick", "stuck_pipe", "torque_drag", "pressure_anomaly", "cementing_issue", "fishing", "npt"]
SEVERITIES = ["low", "medium", "high", "critical"]
def write_json(name: str, records: list[dict]) -> None:
    (ROOT / name).write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
def main() -> None:
    rng = random.Random(SEED)
    ROOT.mkdir(parents=True, exist_ok=True)
    formations = [{"id": f"formation-{index + 1:02d}", "name": name, "region": REGION, "is_synthetic": True} for index, name in enumerate(FORMATIONS)]
    wells = []
    for index in range(20):
        wells.append({"id": f"demo-well-{index + 1:02d}", "name": f"Kanchan Demo Well {index + 1:02d}", "latitude": round(26.8 + rng.uniform(-0.16, 0.16), 6), "longitude": round(91.7 + rng.uniform(-0.16, 0.16), 6), "basin": REGION, "total_depth_m": rng.randint(2800, 4700), "formation": FORMATIONS[index % 8], "trajectory": "vertical" if index % 3 else "deviated", "status": "historical", "is_synthetic": True} )
    scenarios = []
    for index, (name, start, end) in enumerate([("Quartz North", 900, 3600), ("Juniper East", 1500, 4100), ("Lumen South", 700, 3300)], start=1):
        active_id = f"active-demo-{index}"
        wells.append({"id": active_id, "name": f"Active {name} Demo Well", "latitude": round(26.8 + index * 0.04, 6), "longitude": round(91.7 + index * 0.03, 6), "basin": REGION, "total_depth_m": end, "formation": FORMATIONS[index], "trajectory": "deviated", "status": "active", "is_synthetic": True})
        scenarios.append({"id": f"scenario-{index}", "name": name, "active_well_id": active_id, "current_depth_m": float(start), "start_depth_m": float(start), "end_depth_m": float(end), "step_m": 100.0, "is_synthetic": True})
    events = []
    for index in range(60):
        well = wells[index % 20]
        top = 600 + ((index * 173) % 3300)
        event_type = EVENT_TYPES[index % len(EVENT_TYPES)]
        report_number = index % 12 + 1
        events.append({"id": f"demo-event-{index + 1:03d}", "well_id": well["id"], "event_type": event_type, "start_depth_m": float(top), "end_depth_m": float(top + 60 + rng.randint(0, 180)), "formation": FORMATIONS[(index + 2) % 8], "severity": SEVERITIES[index % 4], "description": f"Fictional historical {event_type.replace('_', ' ')} observation in the demo region.", "recorded_mitigation": "Paused operations, verified returns, and reviewed offset evidence before continuing.", "source_document_id": f"demo-report-{report_number:02d}", "source_page": 1, "is_synthetic": True})
    reports = []
    for index in range(1, 13):
        event = events[(index - 1) * 5]
        reports.append({"document_id": f"demo-report-{index:02d}", "filename": f"synthetic_report_{index:02d}.txt", "event_id": event["id"], "is_synthetic": True})
        text = ("SYNTHETIC DEMO REPORT - FICTIONAL KANCHAN RIDGE DEMO REGION\n"
                "This document is invented for WELLSAGE AI testing and is not an Oil India record.\n"
                f"Event type: {event['event_type']}; depth: {event['start_depth_m']:.0f}-{event['end_depth_m']:.0f} m; "
                f"formation: {event['formation']}; severity: {event['severity']}.\n"
                f"Mitigation: {event['recorded_mitigation']}\n")
        (ROOT / f"synthetic_report_{index:02d}.txt").write_text(text, encoding="utf-8")
    write_json("formations.json", formations)
    write_json("wells.json", wells)
    write_json("events.json", events)
    write_json("scenarios.json", scenarios)
    write_json("reports.json", reports)
    print(f"Generated {len(wells)} wells, {len(formations)} formations, {len(events)} events, {len(scenarios)} scenarios, and {len(reports)} reports in {ROOT}")
if __name__ == "__main__":
    main()
