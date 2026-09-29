def validate_depth_interval(start_depth_m: float, end_depth_m: float) -> None:
    if start_depth_m < 0 or end_depth_m < start_depth_m:
        raise ValueError("depth interval must satisfy 0 <= start_depth_m <= end_depth_m")
