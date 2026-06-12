#!/usr/bin/env python3
"""Run a short local DroneOps basestation simulation demo."""

import json
import os
import sys
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "droneops_local_planner"))

import droneops_planner  # noqa: E402
import sim_server  # noqa: E402


def request_json(method, path, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        "http://127.0.0.1:47147" + path,
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    order = (
        "fly from 38.8890,-77.0360 to 38.8910,-77.0340 "
        "via 38.8902,-77.0357 and report coverage"
    )
    server = ThreadingHTTPServer(("127.0.0.1", 47147), sim_server.DroneOpsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        print("DroneOps local simulation running on http://127.0.0.1:47147")
        print(json.dumps(request_json("GET", "/health"), indent=2, sort_keys=True))

        intent = droneops_planner.validate_intent(droneops_planner.mock_intent(order))
        print("Planner mission intent:")
        print(json.dumps(intent, indent=2, sort_keys=True))

        print("DroneOps response:")
        print(json.dumps(
            request_json("POST", "/mission-intents", intent),
            indent=2,
            sort_keys=True,
        ))

        for tick in range(1, 4):
            time.sleep(1)
            fleet = request_json("GET", "/fleet")
            print("Fleet tick {}:".format(tick))
            for drone in fleet["drones"]:
                print(
                    "  {id}: {state}, lat={latitude}, lon={longitude}, "
                    "alt={altitudeMeters}m, task={task}".format(
                        id=drone["id"],
                        state=drone["state"],
                        latitude=drone["latitude"],
                        longitude=drone["longitude"],
                        altitudeMeters=drone["altitudeMeters"],
                        task=drone["assignedTask"]["type"]
                        if drone["assignedTask"] else "none",
                    )
                )
    finally:
        server.shutdown()
        server.server_close()
        print("Simulation stopped cleanly.")


if __name__ == "__main__":
    main()
