from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

WITSML_NAMESPACE = "http://www.witsml.org/schemas/1series"
NAMESPACE = {"w": WITSML_NAMESPACE}
NULL_VALUES = {"", "-999.25", "-999.0", "-9999"}


def _number(value: str | None) -> float | None:
    if value is None or value.strip() in NULL_VALUES:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _first(values: dict[str, float | None], names: tuple[str, ...]) -> float | None:
    for name in names:
        value = values.get(name.upper())
        if value is not None:
            return value
    return None


def _to_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _convert(values: dict[str, float | None], units: dict[str, str]) -> dict[str, float | None]:
    def converted(names: tuple[str, ...], factor: float = 1.0) -> float | None:
        raw_name = next((name for name in names if values.get(name) is not None), None)
        return values[raw_name] * factor if raw_name else None

    wob_unit = units.get("WOB", "").lower()
    torque_unit = units.get("TORQUE", "").lower()
    flow_unit = units.get("FLOWIN", units.get("FLOWOUT", "")).lower()
    rop_unit = units.get("ROP_AVG", units.get("ROP", "")).lower()
    rpm_unit = units.get("SURF_RPM", units.get("BIT_RPM", "")).lower()

    wob = converted(("WOB",))
    if wob is not None and wob_unit in {"n", "newton"}:
        wob /= 1000.0
    torque = converted(("TORQUE",))
    if torque is not None and torque_unit in {"n.m", "nm", "n-m"}:
        torque /= 1000.0
    flow = converted(("FLOWIN", "FLOWOUT"))
    if flow is not None and flow_unit in {"m3/s", "m^3/s"}:
        flow *= 60000.0
    rop = converted(("ROP_AVG", "ROP"))
    if rop is not None and rop_unit in {"m/s", "m/sec"}:
        rop *= 3600.0
    rpm = converted(("SURF_RPM", "BIT_RPM"))
    if rpm is not None and rpm_unit in {"c/s", "1/s", "hz"}:
        rpm *= 60.0

    return {
        "wob": wob,
        "rpm": rpm,
        "torque": torque,
        "flow_rate_lpm": flow,
        "mud_flow_rate": flow,
        "rop_mhr": rop,
        "ecd_kgL": converted(("ECD", "ECDCS")),
        "standpipe_pressure_kpa": converted(("SPP", "STANDPIPE_PRESSURE"), 0.001),
        "mwd_inclination": converted(("INCL", "INCLINATION")),
        "mwd_azimuth": converted(("AZIM", "AZIMUTH")),
    }


def parse_witsml_file(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    root = ET.parse(path).getroot()
    log = root.find(".//w:log", NAMESPACE)
    if log is None:
        return []
    curve_names = [node.text.strip() for node in log.findall(".//w:logCurveInfo/w:mnemonic", NAMESPACE) if node.text]
    mnemonic_list = log.find(".//w:logData/w:mnemonicList", NAMESPACE)
    if mnemonic_list is not None and mnemonic_list.text:
        curve_names = [name.strip() for name in mnemonic_list.text.split(",")]
    units_node = log.find(".//w:logData/w:unitList", NAMESPACE)
    units = dict(zip(curve_names, units_node.text.split(",") if units_node is not None and units_node.text else []))
    well_name = (log.findtext("w:nameWell", default="", namespaces=NAMESPACE) or "").strip()
    rows = []
    for data_node in log.findall(".//w:logData/w:data", NAMESPACE):
        values = dict(zip(curve_names, (part.strip() for part in (data_node.text or "").split(","))))
        depth = _first({key.upper(): _number(value) for key, value in values.items()}, ("DEPTH", "MDEPTH", "BITDEP"))
        timestamp = _to_utc(values.get("Time") or values.get("TIME"))
        if depth is None or timestamp is None:
            continue
        numeric_values = {key.upper(): _number(value) for key, value in values.items()}
        converted = _convert(numeric_values, {key.upper(): value for key, value in units.items()})
        if not any(value is not None for value in converted.values()):
            continue
        rows.append({"well_name": well_name, "timestamp": timestamp, "measured_depth_m": depth, **converted, "source_file": str(path)})
    return rows


def parse_witsml_tree(root: str | Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(Path(root).rglob("*.xml")):
        rows.extend(parse_witsml_file(path))
    return rows


def write_csv(rows: list[dict[str, Any]], destination: str | Path) -> None:
    if not rows:
        raise ValueError("No telemetry rows were parsed")
    fieldnames = list(rows[0])
    with Path(destination).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
