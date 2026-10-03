from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.witsml import parse_witsml_tree, write_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize real Volve WITSML logs to CSV")
    parser.add_argument("--source", type=Path, default=ROOT / "data" / "real" / "volve-drilling" / "witsml")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "real" / "volve_telemetry.csv")
    args = parser.parse_args()
    rows = parse_witsml_tree(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.output)
    wells = sorted({row["well_name"] for row in rows})
    print(f"Parsed {len(rows)} telemetry rows from {len(wells)} wells")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
