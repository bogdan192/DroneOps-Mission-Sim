#!/usr/bin/env python3
"""Run a short live control-station ATAK/CoT simulation in-process."""

import json
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control_station.http_server import ControlStationHandler, ControlStationServer  # noqa: E402
from control_station.mission_session import ControlStationMissionSession  # noqa: E402


def request_json(method, url, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def run_live_atak_demo():
    session = ControlStationMissionSession(mission_store_dir=tempfile.mkdtemp(prefix="droneops-live-atak-"))
    server = ControlStationServer(("127.0.0.1", 0), ControlStationHandler, session, "")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = "http://{}:{}".format(host, port)
    try:
        started = request_json("POST", base + "/api/mission/start", {
            "order": "coordinate with peers and simulate the Bucharest outskirts route as a swarm member",
            "nodeCount": 4,
            "ticks": 20,
            "tickSeconds": 0.2,
            "selectedNodeIds": ["drone-01", "drone-02", "atak-drone-01"],
        })
        samples = []
        for _ in range(3):
            time.sleep(0.25)
            mission = request_json("GET", base + "/api/mission")
            cot = request_json("GET", base + "/api/atak/cot")
            samples.append({
                "tick": mission["currentTick"],
                "status": mission["status"],
                "telemetryCount": len(mission["telemetry"]),
                "cotEventCount": len(cot["events"]),
                "cotTypes": sorted(set(item["sourceMessageType"] for item in cot["events"]))[:8],
            })
        return {
            "missionId": started["mission"]["missionId"],
            "selectedNodeIds": started["selectedNodeIds"],
            "missionArtifacts": started["missionArtifacts"],
            "samples": samples,
            "liveExecution": False,
        }
    finally:
        server.shutdown()
        server.server_close()


def main():
    print(json.dumps(run_live_atak_demo(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
