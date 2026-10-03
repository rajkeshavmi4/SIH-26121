import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime

class WITSMLAdapter:
    def __init__(self):
        self.connected = False
        self.channels: Dict[str, Dict[str, Any]] = {}
        self.buffer: List[Dict[str, Any]] = []

    def connect_etp_session(self, server_url: str = "wss://etp.namowell.local/v12") -> Dict[str, Any]:
        self.connected = True
        return {
            "status": "CONNECTED",
            "server_url": server_url,
            "protocol_version": "ETP-1.2",
            "supported_protocols": ["Store", "ChannelStreaming", "Discovery"],
            "session_id": "session-namowell-etp-9912"
        }

    def subscribe_channel(self, well_id: str, log_mnemonic: str) -> Dict[str, Any]:
        channel_key = f"{well_id}:{log_mnemonic}"
        self.channels[channel_key] = {
            "well_id": well_id,
            "log_mnemonic": log_mnemonic,
            "status": "SUBSCRIBED",
            "subscribed_at": datetime.utcnow().isoformat()
        }
        return {"channel_key": channel_key, "status": "SUBSCRIBED"}

    def parse_witsml_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        records = []
        try:
            root = ET.fromstring(xml_content)
            for elem in root.findall(".//logData/data"):
                parts = elem.text.split(",") if elem.text else []
                if len(parts) >= 6:
                    records.append({
                        "measured_depth_m": float(parts[0]),
                        "wob": float(parts[1]),
                        "rpm": float(parts[2]),
                        "torque": float(parts[3]),
                        "rop_mhr": float(parts[4]),
                        "spp_kpa": float(parts[5])
                    })
        except Exception:
            lines = xml_content.splitlines()
            for line in lines:
                parts = line.split(",")
                if len(parts) >= 6:
                    try:
                        records.append({
                            "measured_depth_m": float(parts[0]),
                            "wob": float(parts[1]),
                            "rpm": float(parts[2]),
                            "torque": float(parts[3]),
                            "rop_mhr": float(parts[4]),
                            "spp_kpa": float(parts[5])
                        })
                    except ValueError:
                        continue
        return records

    def replay_log_series(self, telemetry_data: List[Dict[str, Any]], speed_multiplier: float = 1.0) -> Dict[str, Any]:
        sorted_records = sorted(telemetry_data, key=lambda x: x.get("measured_depth_m", 0.0))
        return {
            "total_records": len(sorted_records),
            "speed_multiplier": speed_multiplier,
            "start_depth_m": sorted_records[0].get("measured_depth_m", 0.0) if sorted_records else 0.0,
            "end_depth_m": sorted_records[-1].get("measured_depth_m", 0.0) if sorted_records else 0.0,
            "records": sorted_records[:100]
        }

witsml_adapter = WITSMLAdapter()
