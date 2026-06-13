#!/usr/bin/env python3
"""Simulation controller adapter.

The output is a neutral controller program for the local simulator. It is not a
MAVLink mission, not an arming request, and not a flight-control command stream.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from mission_core import mission_schema
from integration_contracts.runtime import require_simulation_payload


def compile_simulation_program(node_id, mission, assignment):
    mission = mission_schema.validate_mission_dsl(mission)
    if assignment.get("liveExecution") is not False:
        raise ValueError("assignment liveExecution must be false")
    route = mission_schema.normalize_route(assignment.get("routeWaypoints"))
    program = {
        "programVersion": "0.1",
        "target": "local-simulator",
        "nodeId": str(node_id),
        "missionId": mission["missionId"],
        "liveExecution": False,
        "preflightChecks": [
            "simulation_mode",
            "geofence_required",
            "battery_threshold",
            "lost_link_return_to_launch",
        ],
        "constraints": mission["constraints"],
        "routeWaypoints": route,
    }
    mission_schema.reject_raw_command_fields(program)
    require_simulation_payload(program, "controllerProgram")
    return program


def self_test():
    mission = mission_schema.self_test()
    assignment = {
        "liveExecution": False,
        "routeWaypoints": mission["routeWaypoints"],
    }
    program = compile_simulation_program("drone-a", mission, assignment)
    assert program["target"] == "local-simulator"
    assert program["liveExecution"] is False
    return program


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
