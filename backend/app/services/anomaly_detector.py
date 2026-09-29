from __future__ import annotations
from typing import Any
THRESHOLDS: dict[str, dict[str, Any]] = {
    "high_torque": {
        "parameter": "torque",
        "upper": 25.0,
        "severity": "high",
        "event_type": "torque_drag",
        "explanation": "Torque exceeds upper threshold. Possible stuck pipe or formation change.",
    },
    "low_flow_rate": {
        "parameter": "mud_flow_rate",
        "lower": 500.0,
        "severity": "critical",
        "event_type": "lost_circulation",
        "explanation": "Mud flow rate below minimum. Possible lost circulation or pump failure.",
    },
    "high_ecd": {
        "parameter": "ecd_kgL",
        "upper": 1.8,
        "severity": "high",
        "event_type": "pressure_anomaly",
        "explanation": "Equivalent circulating density above safe window. Fracture gradient at risk.",
    },
    "low_rop_high_wob": {
        "parameter": "rop_mhr",
        "lower": 0.5,
        "co_parameter": "wob",
        "co_lower": 100.0,
        "severity": "high",
        "event_type": "stuck_pipe",
        "explanation": "Low ROP combined with high WOB indicates possible packed-off or stuck assembly.",
    },
    "high_standpipe_pressure": {
        "parameter": "standpipe_pressure_kpa",
        "upper": 27000.0,
        "severity": "high",
        "event_type": "pressure_anomaly",
        "explanation": "Standpipe pressure above normal operating range. Possible pack-off or wellbore restriction.",
    },
    "low_rpm_high_torque": {
        "parameter": "rpm",
        "lower": 20.0,
        "co_parameter": "torque",
        "co_upper": 20.0,
        "severity": "medium",
        "event_type": "torque_drag",
        "explanation": "Low RPM with elevated torque suggests possible string engagement or formation instability.",
    },
}
def _check_simple(record: dict[str, Any], key: str, rule: dict[str, Any]) -> dict[str, Any] | None:
    parameter = rule["parameter"]
    value = record.get(parameter)
    if value is None:
        return None
    triggered = False
    if "upper" in rule and value > rule["upper"]:
        triggered = True
    if "lower" in rule and value < rule["lower"]:
        triggered = True
    if not triggered:
        return None
    return {
        "anomaly_type": key,
        "event_type": rule["event_type"],
        "severity": rule["severity"],
        "parameter": parameter,
        "value": round(value, 4),
        "threshold": rule.get("upper", rule.get("lower")),
        "depth_m": record.get("measured_depth_m"),
        "timestamp": record.get("timestamp"),
        "explanation": rule["explanation"],
    }
def _check_compound(record: dict[str, Any], key: str, rule: dict[str, Any]) -> dict[str, Any] | None:
    parameter = rule["parameter"]
    co_parameter = rule.get("co_parameter")
    value = record.get(parameter)
    co_value = record.get(co_parameter) if co_parameter else None
    if value is None:
        return None
    primary_triggered = False
    if "upper" in rule and value > rule["upper"]:
        primary_triggered = True
    if "lower" in rule and value < rule["lower"]:
        primary_triggered = True
    if not primary_triggered:
        return None
    if co_parameter and co_value is not None:
        co_triggered = False
        if "co_upper" in rule and co_value > rule["co_upper"]:
            co_triggered = True
        if "co_lower" in rule and co_value > rule["co_lower"]:
            co_triggered = True
        if not co_triggered:
            return None
    return {
        "anomaly_type": key,
        "event_type": rule["event_type"],
        "severity": rule["severity"],
        "parameter": parameter,
        "value": round(value, 4),
        "threshold": rule.get("upper", rule.get("lower")),
        "co_parameter": co_parameter,
        "co_value": round(co_value, 4) if co_value is not None else None,
        "depth_m": record.get("measured_depth_m"),
        "timestamp": record.get("timestamp"),
        "explanation": rule["explanation"],
    }
def detect_anomalies(telemetry_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    for record in telemetry_records:
        for key, rule in THRESHOLDS.items():
            result = None
            if "co_parameter" in rule:
                result = _check_compound(record, key, rule)
            else:
                result = _check_simple(record, key, rule)
            if result:
                anomalies.append(result)
    anomalies.sort(key=lambda item: ({"critical": 0, "high": 1, "medium": 2, "low": 3}.get(item["severity"], 4), item.get("depth_m") or 0))
    return anomalies
