from typing import Any
def advance_scenario(scenario: Any, action: str) -> Any:
    if action == "start":
        scenario.running = True
    elif action == "step":
        scenario.current_depth_m = min(scenario.end_depth_m, scenario.current_depth_m + scenario.step_m)
    elif action == "reset":
        scenario.current_depth_m = scenario.start_depth_m
        scenario.running = False
    else:
        raise ValueError("action must be start, step, or reset")
    return scenario
