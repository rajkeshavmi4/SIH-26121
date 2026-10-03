# NAMOWELL AI data dictionary

| Entity | Field | Unit / meaning |
|---|---|---|
| Well | latitude, longitude | Decimal degrees, WGS84 |
| Well | total_depth_m | Metres MD unless otherwise stated |
| Well | formation | Primary target formation |
| Incident | top_depth_m, bottom_depth_m | Inclusive measured-depth interval in metres |
| Incident | severity | low, medium, high, critical |
| Incident | event_type | kick, loss, stuck_pipe, pressure, mud_loss, casing |
| Alert | distance_to_interval_m | Positive distance from active depth to incident interval |
| Provenance | source_type | synthetic, public, uploaded, verified |
| Provenance | is_synthetic | Boolean; true for every bundled demo record |

All timestamps are ISO 8601 UTC. All bundled records carry `is_synthetic=true` and `demo_label=NWIS synthetic demo`.
