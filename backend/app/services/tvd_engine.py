import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import TrajectoryData, FormationData, Well, Incident

class TVDEngine:
    @staticmethod
    def compute_minimum_curvature(points: List[Dict[str, float]]) -> List[Dict[str, float]]:
        if not points:
            return []

        sorted_pts = sorted(points, key=lambda p: p["measured_depth_m"])
        computed = []
        
        md_prev = sorted_pts[0]["measured_depth_m"]
        inc_prev = math.radians(sorted_pts[0]["inclination_deg"])
        azi_prev = math.radians(sorted_pts[0]["azimuth_deg"])
        
        tvd = md_prev * math.cos(inc_prev)
        north = md_prev * math.sin(inc_prev) * math.cos(azi_prev)
        east = md_prev * math.sin(inc_prev) * math.sin(azi_prev)
        
        computed.append({
            "measured_depth_m": md_prev,
            "inclination_deg": sorted_pts[0]["inclination_deg"],
            "azimuth_deg": sorted_pts[0]["azimuth_deg"],
            "true_vertical_depth_m": round(tvd, 2),
            "northing_m": round(north, 2),
            "easting_m": round(east, 2),
            "dogleg_severity_deg100ft": 0.0
        })

        for i in range(1, len(sorted_pts)):
            pt = sorted_pts[i]
            md_curr = pt["measured_depth_m"]
            inc_curr = math.radians(pt["inclination_deg"])
            azi_curr = math.radians(pt["azimuth_deg"])
            delta_md = md_curr - md_prev

            if delta_md <= 0:
                continue

            cos_dogleg = (math.cos(inc_curr - inc_prev) - 
                          math.sin(inc_prev) * math.sin(inc_curr) * (1 - math.cos(azi_curr - azi_prev)))
            cos_dogleg = max(-1.0, min(1.0, cos_dogleg))
            dogleg = math.acos(cos_dogleg)
            
            rf = 1.0
            if dogleg > 1e-6:
                rf = (2.0 / dogleg) * math.tan(dogleg / 2.0)

            delta_tvd = (delta_md / 2.0) * (math.cos(inc_prev) + math.cos(inc_curr)) * rf
            delta_north = (delta_md / 2.0) * (math.sin(inc_prev) * math.cos(azi_prev) + math.sin(inc_curr) * math.cos(azi_curr)) * rf
            delta_east = (delta_md / 2.0) * (math.sin(inc_prev) * math.sin(azi_prev) + math.sin(inc_curr) * math.sin(azi_curr)) * rf

            dls = math.degrees(dogleg) * (30.48 / delta_md)

            tvd += delta_tvd
            north += delta_north
            east += delta_east

            computed.append({
                "measured_depth_m": md_curr,
                "inclination_deg": pt["inclination_deg"],
                "azimuth_deg": pt["azimuth_deg"],
                "true_vertical_depth_m": round(tvd, 2),
                "northing_m": round(north, 2),
                "easting_m": round(east, 2),
                "dogleg_severity_deg100ft": round(dls, 2)
            })

            md_prev, inc_prev, azi_prev = md_curr, inc_curr, azi_curr

        return computed

    @staticmethod
    def md_to_tvd(trajectory_points: List[Dict[str, float]], md: float) -> float:
        if not trajectory_points:
            return md
        sorted_pts = sorted(trajectory_points, key=lambda p: p["measured_depth_m"])
        if md <= sorted_pts[0]["measured_depth_m"]:
            return sorted_pts[0]["true_vertical_depth_m"]
        if md >= sorted_pts[-1]["measured_depth_m"]:
            last = sorted_pts[-1]
            return last["true_vertical_depth_m"] + (md - last["measured_depth_m"]) * math.cos(math.radians(last["inclination_deg"]))
        
        for i in range(len(sorted_pts) - 1):
            p1, p2 = sorted_pts[i], sorted_pts[i+1]
            if p1["measured_depth_m"] <= md <= p2["measured_depth_m"]:
                frac = (md - p1["measured_depth_m"]) / (p2["measured_depth_m"] - p1["measured_depth_m"])
                return p1["true_vertical_depth_m"] + frac * (p2["true_vertical_depth_m"] - p1["true_vertical_depth_m"])
        return md

    @staticmethod
    def formation_aware_correlation(db: Session, active_well_id: str, active_md: float, offset_well_ids: List[str]) -> Dict[str, Any]:
        active_well = db.get(Well, active_well_id)
        if not active_well:
            return {"active_formation": "Unknown", "correlated_incidents": []}

        active_traj = [
            {"measured_depth_m": t.measured_depth_m, "inclination_deg": t.inclination_deg, "azimuth_deg": t.azimuth_deg, "true_vertical_depth_m": t.true_vertical_depth_m}
            for t in active_well.trajectories
        ]
        active_tvd = TVDEngine.md_to_tvd(active_traj, active_md)

        active_formation_obj = None
        for f in active_well.formations:
            if f.top_tvd_m <= active_tvd <= f.bottom_tvd_m:
                active_formation_obj = f
                break
        
        active_formation_name = active_formation_obj.formation_name if active_formation_obj else active_well.formation

        correlated_incidents = []
        for offset_id in offset_well_ids:
            offset_well = db.get(Well, offset_id)
            if not offset_well:
                continue
            
            offset_traj = [
                {"measured_depth_m": t.measured_depth_m, "inclination_deg": t.inclination_deg, "azimuth_deg": t.azimuth_deg, "true_vertical_depth_m": t.true_vertical_depth_m}
                for t in offset_well.trajectories
            ]
            
            for incident in offset_well.incidents:
                incident_tvd_top = TVDEngine.md_to_tvd(offset_traj, incident.top_depth_m)
                incident_tvd_bottom = TVDEngine.md_to_tvd(offset_traj, incident.bottom_depth_m)
                
                tvd_diff = abs(active_tvd - (incident_tvd_top + incident_tvd_bottom) / 2.0)
                formation_match = (incident.formation == active_formation_name)
                
                correlated_incidents.append({
                    "incident_id": incident.id,
                    "well_id": offset_well.id,
                    "well_name": offset_well.name,
                    "event_type": incident.event_type,
                    "severity": incident.severity,
                    "offset_top_md": incident.top_depth_m,
                    "offset_bottom_md": incident.bottom_depth_m,
                    "offset_top_tvd": round(incident_tvd_top, 2),
                    "offset_bottom_tvd": round(incident_tvd_bottom, 2),
                    "tvd_delta_m": round(tvd_diff, 2),
                    "formation_match": formation_match,
                    "active_formation": active_formation_name,
                    "incident_formation": incident.formation
                })

        return {
            "active_well_id": active_well_id,
            "active_md_m": active_md,
            "active_tvd_m": round(active_tvd, 2),
            "active_formation": active_formation_name,
            "correlated_incidents": sorted(correlated_incidents, key=lambda x: x["tvd_delta_m"])
        }

tvd_engine = TVDEngine()
