#!/usr/bin/env python3
"""End-to-end mocked mission simulation.

This fills the currently missing pieces around the onboard node:

- a mock TAK/network message bus
- peer drone status messages
- mission assignment distribution
- simulated controller-program execution
- telemetry output over time
- automatic simulated return-to-home after the route timeline ends

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


def run_mock_mission(order, route_waypoints=None, node_count=3, ticks=8, sleep_seconds=0.0, return_home_ticks=10):
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
    route_ticks = max(2, int(ticks))
    rth_ticks = max(1, int(return_home_ticks))
    for tick in range(route_ticks):
        tick_items = []
        for runtime in runtimes:
            telemetry = runtime.telemetry_at(tick, route_ticks)
            network.publish("mission.telemetry", telemetry)
            tick_items.append(telemetry)
        timeline.append({"tick": tick, "telemetry": tick_items})
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    home = route_position(mission["routeWaypoints"][0])
    for runtime in runtimes:
        network.publish("mission.return_home", {
            "type": "mission.return_home",
            "schemaVersion": "0.1",
            "timestamp": messages.timestamp(),
            "missionId": mission["missionId"],
            "nodeId": runtime.node_id,
            "command": "auto_return_to_home",
            "reason": "mission_complete",
            "home": home,
            "liveExecution": False,
        })

    route_end_by_id = {
        runtime.node_id: runtime.telemetry_at(route_ticks - 1, route_ticks)["position"]
        for runtime in runtimes
    }
    for offset in range(rth_ticks):
        tick = route_ticks + offset
        tick_items = []
        fraction = min(1.0, offset / float(max(1, rth_ticks - 1)))
        for runtime in runtimes:
            telemetry = return_home_telemetry(runtime, route_end_by_id[runtime.node_id], home, fraction, tick)
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
        "missionTicks": route_ticks,
        "returnHomeTicks": rth_ticks,
        "totalTicks": route_ticks + rth_ticks,
        "networkEventCount": len(network.events),
        "networkTopics": sorted(set(event["topic"] for event in network.events)),
        "safety": {
            "llmDirectControllerAccess": False,
            "rawControllerCommands": False,
            "realDroneCommands": False,
        },
    }


def return_home_telemetry(runtime, route_end, home, fraction, tick):
    position = {
        "lat": round(lerp(route_end["lat"], home["lat"], fraction), 7),
        "lon": round(lerp(route_end["lon"], home["lon"], fraction), 7),
        "alt": round(lerp(route_end["alt"], home["alt"], fraction), 1),
    }
    state = "complete" if fraction >= 1.0 else "returning_home"
    runtime.battery_percent = max(20.0, 96.0 - tick * 0.4)
    return {
        "type": "mission.telemetry",
        "schemaVersion": "0.1",
        "timestamp": messages.timestamp(),
        "nodeId": runtime.node_id,
        "missionId": runtime.program["missionId"],
        "state": state,
        "position": position,
        "batteryPercent": round(runtime.battery_percent, 1),
        "liveExecution": False,
    }

def compact_summary(result):
    final_tick = result["timeline"][-1]
    return {
        "mode": result["mode"],
        "liveExecution": result["liveExecution"],
        "missionId": result["mission"]["missionId"],
        "assignmentCount": result["assignmentPlan"]["assignmentCount"],
        "networkTopics": result["networkTopics"],
        "missionTicks": result["missionTicks"],
        "returnHomeTicks": result["returnHomeTicks"],
        "totalTicks": result["totalTicks"],
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
    assert "mission.return_home" in result["networkTopics"]
    mission_start = route_position(result["mission"]["routeWaypoints"][0])
    for telemetry in result["timeline"][0]["telemetry"]:
        assert telemetry["position"] == mission_start
    returning_tick = result["timeline"][result["missionTicks"]]
    assert {item["state"] for item in returning_tick["telemetry"]} == {"returning_home"}
    for telemetry in result["timeline"][-1]["telemetry"]:
        assert telemetry["state"] == "complete"
        assert telemetry["position"] == mission_start
    return result


def main():
    parser = argparse.ArgumentParser(description="Run an end-to-end mocked DroneOps mission.")
    parser.add_argument("--order", default="coordinate with peers and simulate the Bucharest outskirts route")
    parser.add_argument("--nodes", type=int, default=4)
    parser.add_argument("--ticks", type=int, default=8)
    parser.add_argument("--return-home-ticks", type=int, default=10)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--full", action="store_true", help="Print the full simulation payload.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    result = self_test() if args.self_test else run_mock_mission(
        args.order,
        node_count=args.nodes,
        ticks=args.ticks,
        sleep_seconds=args.sleep,
        return_home_ticks=args.return_home_ticks,
    )
    payload = result if args.full else compact_summary(result)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
