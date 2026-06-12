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

from controller_adapters import simulated_controller  # noqa: E402
from fleet_protocol import messages  # noqa: E402
from mission_core import mission_schema  # noqa: E402
from onboard_node.node import DEFAULT_ROUTE, OnboardNode  # noqa: E402


class MockTakNetwork:
    """Tiny in-memory stand-in for TAK/CoT or drone mesh transport."""

    def __init__(self):
        self.events = []

    def publish(self, topic, payload):
        event = {
            "topic": topic,
            "timestamp": messages.timestamp(),
            "payload": payload,
        }
        self.events.append(event)
        return event

    def by_topic(self, topic):
        return [event for event in self.events if event["topic"] == topic]


class MockDroneRuntime:
    """Executes a neutral simulation controller program."""

    def __init__(self, node_id, program):
        self.node_id = node_id
        self.program = program
        self.route = mission_schema.normalize_route(program["routeWaypoints"])
        self.battery_percent = 96.0
        self.state = "assigned"

    def telemetry_at(self, tick, total_ticks):
        progress = 0.0 if total_ticks <= 1 else min(1.0, tick / float(total_ticks - 1))
        position = interpolate_route(self.route, progress)
        self.battery_percent = max(20.0, 96.0 - tick * 0.4)
        if progress >= 1.0:
            self.state = "complete"
        else:
            self.state = "simulating"
        return {
            "type": "mission.telemetry",
            "schemaVersion": "0.1",
            "timestamp": messages.timestamp(),
            "nodeId": self.node_id,
            "missionId": self.program["missionId"],
            "state": self.state,
            "position": position,
            "batteryPercent": round(self.battery_percent, 1),
            "liveExecution": False,
        }


def build_mock_fleet(node_count):
    if node_count < 1 or node_count > 12:
        raise ValueError("node_count must be between 1 and 12")
    fleet = []
    for index in range(node_count):
        fleet.append(messages.node_status(
            "drone-{:02d}".format(index + 1),
            {
                "lat": 44.4057 + index * 0.00008,
                "lon": 26.3019 + index * 0.00008,
                "alt": 80,
            },
            battery_percent=96.0 - index * 2.0,
            role="leader-capable" if index == 0 else "worker",
            capabilities=["route", "survey", "relay", "mission_compile"],
        ))
    return fleet


def run_mock_mission(order, route_waypoints=None, node_count=3, ticks=8, sleep_seconds=0.0):
    route = route_waypoints or DEFAULT_ROUTE
    network = MockTakNetwork()
    fleet_status = build_mock_fleet(node_count)
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
        program = simulated_controller.compile_simulation_program(
            assignment["nodeId"],
            mission,
            assignment,
        )
        controller_programs.append(program)
        runtimes.append(MockDroneRuntime(assignment["nodeId"], program))

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


def interpolate_route(route, progress):
    if progress <= 0:
        return route_position(route[0])
    if progress >= 1:
        return route_position(route[-1])
    segments = len(route) - 1
    scaled = progress * segments
    index = min(segments - 1, int(scaled))
    fraction = scaled - index
    start = route[index]
    end = route[index + 1]
    return {
        "lat": round(lerp(start["lat"], end["lat"], fraction), 7),
        "lon": round(lerp(start["lon"], end["lon"], fraction), 7),
        "alt": round(lerp(start["alt"], end["alt"], fraction), 1),
    }


def route_position(point):
    return {
        "lat": float(point["lat"]),
        "lon": float(point["lon"]),
        "alt": float(point.get("alt", 80)),
    }


def lerp(start, end, fraction):
    return float(start) + (float(end) - float(start)) * fraction


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

