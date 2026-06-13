#!/usr/bin/env python3
"""Onboard DroneOps node prototype.

This service models what would run on a drone companion device: it receives a
high-level order, asks a local planner/model for mission intent, coordinates
with peer node status, and compiles a simulation controller program.
"""

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "droneops_local_planner"))

from controller_adapters import simulated_controller  # noqa: E402
from fleet_protocol import coordinator, messages  # noqa: E402
from mission_core import mission_schema  # noqa: E402
import droneops_planner  # noqa: E402


DEFAULT_ROUTE = [
    {"label": "START", "lat": 44.4057, "lon": 26.3019, "alt": 80},
    {"label": "NORTH", "lat": 44.4092, "lon": 26.3056, "alt": 90},
    {"label": "EAST", "lat": 44.4081, "lon": 26.3142, "alt": 88},
    {"label": "SOUTH", "lat": 44.4039, "lon": 26.3128, "alt": 86},
    {"label": "RETURN", "lat": 44.4059, "lon": 26.3022, "alt": 80},
]


class OnboardNode:
    def __init__(self, node_id, position=None, model="llama3.1:8b", use_ollama=False, controller_compiler=None):
        self.node_id = node_id
        self.position = position or {"lat": 44.4057, "lon": 26.3019, "alt": 80}
        self.model = model
        self.use_ollama = use_ollama
        self.controller_compiler = controller_compiler or simulated_controller.compile_simulation_program

    def status(self):
        return messages.node_status(
            self.node_id,
            self.position,
            battery_percent=96.0,
            role="leader-capable",
            capabilities=["route", "survey", "relay", "mission_compile"],
        )

    def handle_order(self, order_text, route_waypoints=None, fleet_status=None):
        droneops_planner.validate_order_text(order_text)
        route = route_waypoints or self._route_from_order(order_text)
        mission = mission_schema.build_route_mission(order_text, route, source=self.node_id)
        fleet = fleet_status or self.default_fleet()
        assignment_plan = coordinator.plan_assignments(mission, fleet)
        assignment = self.assignment_for_node(assignment_plan)
        controller_program = self.compile_controller_program(self.node_id, mission, assignment)
        return {
            "nodeStatus": self.status(),
            "mission": mission,
            "assignmentPlan": assignment_plan,
            "localAssignment": assignment,
            "controllerProgram": controller_program,
            "safety": {
                "liveExecution": False,
                "rawControllerCommands": False,
                "requiresHumanApproval": True,
            },
        }

    def compile_controller_program(self, node_id, mission, assignment):
        return self.controller_compiler(node_id, mission, assignment)

    def _route_from_order(self, order_text):
        if self.use_ollama:
            intent = droneops_planner.call_ollama(
                order_text,
                self.model,
                droneops_planner.DEFAULT_OLLAMA_URL,
                30.0,
            )
        else:
            intent = droneops_planner.mock_intent(order_text)
        intent = droneops_planner.validate_intent(intent)
        return intent.get("routeWaypoints") or DEFAULT_ROUTE

    def default_fleet(self):
        return [
            self.status(),
            messages.node_status("drone-peer-1", {"lat": 44.4058, "lon": 26.3020, "alt": 80}, 92),
            messages.node_status("drone-peer-2", {"lat": 44.4059, "lon": 26.3021, "alt": 80}, 88),
        ]

    def assignment_for_node(self, assignment_plan):
        for assignment in assignment_plan["assignments"]:
            if assignment["nodeId"] == self.node_id:
                return assignment
        return assignment_plan["assignments"][0]


class OnboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._json(200, {
                "service": "DroneOps Onboard Node",
                "mode": "SIMULATION_ONLY",
                "nodeStatus": self.server.node.status(),
            })
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/orders":
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = self.server.node.handle_order(
                payload.get("order", ""),
                route_waypoints=payload.get("routeWaypoints"),
                fleet_status=payload.get("fleetStatus"),
            )
            self._json(200, result)
        except Exception as exc:
            self._json(422, {"error": str(exc), "mode": "SIMULATION_ONLY"})

    def log_message(self, fmt, *args):
        print("{} - {}".format(self.address_string(), fmt % args))

    def _json(self, status, payload):
        data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class OnboardServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class, node):
        super().__init__(server_address, handler_class)
        self.node = node


def run_server(host, port, node):
    server = OnboardServer((host, port), OnboardHandler, node)
    print("DroneOps onboard node listening on http://{}:{}".format(host, port))
    print("Mission execution mode: SIMULATION_ONLY")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def self_test():
    node = OnboardNode("drone-self")
    result = node.handle_order(
        "coordinate with peers and simulate the Bucharest outskirts route",
        route_waypoints=DEFAULT_ROUTE,
    )
    assert result["controllerProgram"]["liveExecution"] is False
    assert result["assignmentPlan"]["assignmentCount"] >= 1
    assert len(DEFAULT_ROUTE) >= 5
    assert mission_schema.distance_meters(DEFAULT_ROUTE[0], DEFAULT_ROUTE[-1]) < 50
    return result


def main():
    parser = argparse.ArgumentParser(description="Run a simulation-only onboard DroneOps node.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--node-id", default="drone-self")
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--ollama", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return
    node = OnboardNode(args.node_id, model=args.model, use_ollama=args.ollama)
    run_server(args.host, args.port, node)


if __name__ == "__main__":
    main()
