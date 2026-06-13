#!/usr/bin/env python3
"""End-to-end mocked mission simulation.

This fills the currently missing pieces around the onboard node:

- a mock TAK/network message bus
- peer drone status messages
- mission assignment distribution
- simulated controller-program execution
- telemetry output over time

Everything remains simulation-only.
"""

import argparse
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "droneops_local_planner"))

from fleet_protocol import messages  # noqa: E402
from onboard_node.node import DEFAULT_ROUTE, OnboardNode  # noqa: E402
from sim_adapters.fleet import build_simulated_fleet  # noqa: E402
from sim_adapters.runtime import SimulatedDroneRuntime, interpolate_route, lerp, route_position  # noqa: E402
from sim_adapters.transport import InMemoryTakNetwork  # noqa: E402


MockTakNetwork = InMemoryTakNetwork
MockDroneRuntime = SimulatedDroneRuntime
build_mock_fleet = build_simulated_fleet


def run_mock_mission(order, route_waypoints=None, node_count=3, ticks=8, sleep_seconds=0.0):
    route = route_waypoints or DEFAULT_ROUTE
    network = InMemoryTakNetwork()
    fleet_status = build_simulated_fleet(node_count)
    leader = OnboardNode(fleet_status[0]["nodeId"], position=fleet_status[0]["position"])

    network.publish("order.intent", messages.order_intent("order-001", order, route_waypoints=route))
    for status in fleet_status:
        network.publish("node.status", status)

    onboard_result = leader.handle_order(order, route_waypoints=route, fleet_status=fleet_status)
    mission = onboard_result["mission"]
    assignment_plan = onboard_result["assignmentPlan"]
    network.publish("mission.proposal", {
        "type": "mission.proposal",
        "schemaVersion": "0.1",
        "timestamp": messages.timestamp(),
        "missionId": mission["missionId"],
        "source": leader.node_id,
        "liveExecution": False,
        "assignmentCount": assignment_plan["assignmentCount"],
    })

    runtimes = []
    controller_programs = []
    for assignment in assignment_plan["assignments"]:
        network.publish("mission.assignment", assignment)
        program = leader.compile_controller_program(assignment["nodeId"], mission, assignment)
        controller_programs.append(program)
        runtimes.append(SimulatedDroneRuntime(assignment["nodeId"], program))

    timeline = []
    for tick in range(ticks):
        tick_items = []
        for runtime in runtimes:
            telemetry = runtime.telemetry_at(tick, ticks)
            network.publish("mission.telemetry", telemetry)
            tick_items.append(telemetry)
        timeline.append({"tick": tick, "telemetry": tick_items})
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    return {
        "mode": "SIMULATION_ONLY",
        "liveExecution": False,
        "order": order,
        "fleet": fleet_status,
        "mission": mission,
        "assignmentPlan": assignment_plan,
        "controllerPrograms": controller_programs,
        "timeline": timeline,
        "networkEventCount": len(network.events),
        "networkTopics": sorted(set(event["topic"] for event in network.events)),
        "safety": {
            "llmDirectControllerAccess": False,
            "rawControllerCommands": False,
            "realDroneCommands": False,
        },
    }

def compact_summary(result):
    final_tick = result["timeline"][-1]
    return {
        "mode": result["mode"],
        "liveExecution": result["liveExecution"],
        "missionId": result["mission"]["missionId"],
        "assignmentCount": result["assignmentPlan"]["assignmentCount"],
        "networkTopics": result["networkTopics"],
        "finalTelemetry": final_tick["telemetry"],
        "safety": result["safety"],
    }


def self_test():
    result = run_mock_mission(
        "coordinate with peers and simulate the Bucharest outskirts route",
        node_count=4,
        ticks=6,
    )
    assert result["liveExecution"] is False
    assert result["assignmentPlan"]["assignmentCount"] == 4
    assert "mission.telemetry" in result["networkTopics"]
    mission_start = route_position(result["mission"]["routeWaypoints"][0])
    for telemetry in result["timeline"][0]["telemetry"]:
        assert telemetry["position"] == mission_start
    assert result["timeline"][-1]["telemetry"][0]["state"] == "complete"
    return result


def main():
    parser = argparse.ArgumentParser(description="Run an end-to-end mocked DroneOps mission.")
    parser.add_argument("--order", default="coordinate with peers and simulate the Bucharest outskirts route")
    parser.add_argument("--nodes", type=int, default=4)
    parser.add_argument("--ticks", type=int, default=8)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--full", action="store_true", help="Print the full simulation payload.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    result = self_test() if args.self_test else run_mock_mission(
        args.order,
        node_count=args.nodes,
        ticks=args.ticks,
        sleep_seconds=args.sleep,
    )
    payload = result if args.full else compact_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
