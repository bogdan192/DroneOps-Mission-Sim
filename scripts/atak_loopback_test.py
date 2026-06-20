#!/usr/bin/env python3
"""Local Android/ATAK bridge loopback smoke test."""

import json
import sys
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration_contracts.atak_bridge import (  # noqa: E402
    normalize_bridge_registration,
    onboard_order_payload_from_bridge,
)
from integration_contracts.atak_cot import fleet_message_to_cot_event  # noqa: E402
from onboard_node.node import DEFAULT_ROUTE, OnboardHandler, OnboardNode, OnboardServer  # noqa: E402


def request_json(method, url, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def run_loopback():
    registration = normalize_bridge_registration({
        "bridgeId": "android-emulator-loopback-01",
        "nodeId": "headless-node-loopback",
        "callsign": "Headless Loopback",
        "appPackage": "com.droneops.headless",
        "bridgeMode": "emulator-loopback",
        "interfaces": ["http-loopback", "cot-event-feed", "android-service"],
    })
    node = OnboardNode(registration["nodeId"])
    server = OnboardServer(("127.0.0.1", 0), OnboardHandler, node)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = "http://{}:{}".format(host, port)
    try:
        health = request_json("GET", base + "/health")
        assert health["mode"] == "SIMULATION_ONLY"
        status_cot = fleet_message_to_cot_event(health["nodeStatus"], topic="node.status")
        assert status_cot["cotType"] == "a-f-A-UAS"

        order_payload = onboard_order_payload_from_bridge({
            "bridgeId": registration["bridgeId"],
            "transport": "http-loopback",
            "order": {
                "orderId": "loopback-order-01",
                "nodeId": registration["nodeId"],
                "text": "coordinate with peers and simulate the Bucharest outskirts route as a swarm member",
            },
        })
        order_payload["routeWaypoints"] = DEFAULT_ROUTE
        result = request_json("POST", base + "/orders", order_payload)
        assert result["safety"]["liveExecution"] is False
        assert result["controllerProgram"]["liveExecution"] is False
        assert result["mission"]["mode"] == "simulation"
        assignment_cot = fleet_message_to_cot_event(result["localAssignment"], topic="mission.assignment")
        assert assignment_cot["detail"]["droneops"]["nodeId"] == registration["nodeId"]
        return {
            "registration": registration,
            "health": health,
            "missionId": result["mission"]["missionId"],
            "cotEvents": [status_cot, assignment_cot],
            "liveExecution": False,
        }
    finally:
        server.shutdown()
        server.server_close()


def main():
    print(json.dumps(run_loopback(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
