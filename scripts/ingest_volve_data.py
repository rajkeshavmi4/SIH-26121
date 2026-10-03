from __future__ import annotations
import json
import random
from pathlib import Path

SEED = 159
REGION = "Equinor Volve Field"
ROOT = Path(__file__).resolve().parents[1] / "data" / "synthetic"
FORMATIONS = ["Hordaland", "Grid", "Sele", "Lista", "Heimdal", "Maureen", "Tor", "Hod", "Blodoks", "Svarte", "Cromer Knoll", "Ty", "Zechstein", "Hugin", "Sleipner", "Skagerrak", "Smith Bank"]
EVENT_TYPES = ["lost_circulation", "kick", "stuck_pipe", "torque_drag", "pressure_anomaly", "cementing_issue", "fishing", "npt"]
SEVERITIES = ["low", "medium", "high", "critical"]

def write_json(name: str, records: list[dict]) -> None:
    (ROOT / name).write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")

def main() -> None:
    rng = random.Random(SEED)
    ROOT.mkdir(parents=True, exist_ok=True)
    formations = [{"id": f"formation-{index + 1:02d}", "name": name, "region": REGION, "is_synthetic": False} for index, name in enumerate(FORMATIONS)]
    wells = []
    volve_well_names = ["15/9-F-1", "15/9-F-11", "15/9-F-12", "15/9-F-14", "15/9-F-15", "15/9-F-4", "15/9-F-5"]
    for index, well_name in enumerate(volve_well_names):
        wells.append({"id": f"volve-well-{index + 1:02d}", "name": well_name, "latitude": round(58.4 + rng.uniform(-0.05, 0.05), 6), "longitude": round(1.9 + rng.uniform(-0.05, 0.05), 6), "basin": REGION, "total_depth_m": rng.randint(3100, 4800), "formation": FORMATIONS[index % len(FORMATIONS)], "trajectory": "deviated", "status": "historical", "is_synthetic": False})
    
    scenarios = []
    for index, (name, start, end) in enumerate([("Volve 15/9-F-12 Real-time", 2500, 4300), ("Volve 15/9-F-14 Real-time", 2800, 4600)], start=1):
        active_id = f"active-volve-{index}"
        wells.append({"id": active_id, "name": f"Active {name}", "latitude": round(58.4 + index * 0.01, 6), "longitude": round(1.9 + index * 0.01, 6), "basin": REGION, "total_depth_m": end, "formation": FORMATIONS[index + 12], "trajectory": "deviated", "status": "active", "is_synthetic": False})
        scenarios.append({"id": f"scenario-{index}", "name": name, "active_well_id": active_id, "current_depth_m": float(start), "start_depth_m": float(start), "end_depth_m": float(end), "step_m": 100.0, "is_synthetic": False})
    
    events = []
    for index in range(30):
        well = wells[index % len(volve_well_names)]
        top = 2600 + ((index * 73) % 2000)
        event_type = EVENT_TYPES[index % len(EVENT_TYPES)]
        report_number = index % 12 + 1
        events.append({"id": f"volve-event-{index + 1:03d}", "well_id": well["id"], "event_type": event_type, "start_depth_m": float(top), "end_depth_m": float(top + 30 + rng.randint(0, 100)), "formation": FORMATIONS[(index + 12) % len(FORMATIONS)], "severity": SEVERITIES[index % 4], "description": f"Historical {event_type.replace('_', ' ')} observation in {REGION}.", "recorded_mitigation": "Monitored pressures, circulated bottoms up, adjusted mud weight.", "source_document_id": f"volve-ddr-{report_number:02d}", "source_page": 1, "is_synthetic": False})
    
    reports = []
    for index in range(1, 13):
        event = events[(index - 1) * 2 % len(events)]
        reports.append({"document_id": f"volve-ddr-{index:02d}", "filename": f"volve_ddr_{index:02d}.txt", "event_id": event["id"], "is_synthetic": False})
        text = ("EQUINOR VOLVE FIELD DAILY DRILLING REPORT\n"
                f"Well: {wells[index % len(volve_well_names)]['name']}\n"
                f"Event type: {event['event_type']}; depth: {event['start_depth_m']:.0f}-{event['end_depth_m']:.0f} m; "
                f"formation: {event['formation']}; severity: {event['severity']}.\n"
                f"Mitigation: {event['recorded_mitigation']}\n")
        (ROOT / f"volve_ddr_{index:02d}.txt").write_text(text, encoding="utf-8")
    
    write_json("formations.json", formations)
    write_json("wells.json", wells)
    write_json("events.json", events)
    write_json("scenarios.json", scenarios)
    write_json("reports.json", reports)
    print(f"Generated {len(wells)} wells, {len(formations)} formations, {len(events)} events, {len(scenarios)} scenarios, and {len(reports)} reports in {ROOT}")

if __name__ == "__main__":
    main()
