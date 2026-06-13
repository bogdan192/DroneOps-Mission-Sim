#!/usr/bin/env python3
"""Deterministic fleet task allocation.

This module is deliberately boring and predictable. LLMs may propose intent, but
allocation and controller-program construction should be deterministic.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fleet_protocol import messages
from mission_core import mission_schema


def plan_assignments(mission, fleet_status):
    mission = mission_schema.validate_mission_dsl(mission)
    candidates = eligible_nodes(fleet_status, mission)
    if not candidates:
        raise ValueError("no eligible fleet nodes are available")

    route = mission["routeWaypoints"]
    segments = route_segments(route)
    assignments = []
    for index, node in enumerate(candidates):
        assigned_segments = [segment for segment_index, segment in enumerate(segments) if segment_index % len(candidates) == index]
        if not assigned_segments:
            assigned_segments = [segments[index % len(segments)]]
        assigned_route = prepend_common_start(route[0], stitch_segments(assigned_segments))
        assignments.append(messages.mission_assignment(
            mission["missionId"],
            node["nodeId"],
            assigned_route,
            task_type="route",
        ))
    return {
        "missionId": mission["missionId"],
        "strategy": "round_robin_route_segments",
        "assignmentCount": len(assignments),
        "assignments": assignments,
    }


def eligible_nodes(fleet_status, mission):
    min_battery = float(mission["constraints"].get("minBatteryPercent", 35.0))
    nodes = []
    for node in fleet_status:
        if node.get("type") != "node.status":
            continue
        if node.get("state") not in ("available", "simulating", "ready"):
            continue
        if float(node.get("batteryPercent", 0)) < min_battery:
            continue
        if "route" not in node.get("capabilities", []):
            continue
        nodes.append(node)
    return sorted(nodes, key=lambda item: item["nodeId"])


def route_segments(route):
    if len(route) < 2:
        raise ValueError("route must contain at least 2 points")
    return [[route[index], route[index + 1]] for index in range(len(route) - 1)]


def stitch_segments(segments):
    stitched = []
    for segment in segments:
        if not stitched:
            stitched.extend(segment)
        else:
            stitched.append(segment[-1])
    return stitched


def prepend_common_start(start_point, assigned_route):
    if not assigned_route:
        return [start_point]
    if same_position(start_point, assigned_route[0]):
        return assigned_route
    return [start_point] + assigned_route


def same_position(a, b):
    return (
        float(a["lat"]) == float(b["lat"]) and
        float(a["lon"]) == float(b["lon"]) and
        float(a.get("alt", 0)) == float(b.get("alt", 0))
    )


def self_test():
    mission = mission_schema.self_test()
    fleet = [
        messages.node_status("drone-a", {"lat": 44.4057, "lon": 26.3019, "alt": 80}, 96),
        messages.node_status("drone-b", {"lat": 44.4058, "lon": 26.3020, "alt": 80}, 92),
    ]
    plan = plan_assignments(mission, fleet)
    assert plan["assignmentCount"] == 2
    assert plan["assignments"][0]["liveExecution"] is False
    for assignment in plan["assignments"]:
        assert same_position(mission["routeWaypoints"][0], assignment["routeWaypoints"][0])
    return plan


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
