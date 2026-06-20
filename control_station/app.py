#!/usr/bin/env python3
"""Control station command-line entrypoint."""

import argparse
import json
import os
import tempfile
import time

from onboard_node.node import DEFAULT_ROUTE

from .http_server import run_server
from .mission_session import ControlStationMissionSession


HOST = "127.0.0.1"
PORT = 8092


def self_test():
    session = ControlStationMissionSession(mission_store_dir=tempfile.mkdtemp(prefix="droneops-missions-"))
    session.start(
        node_count=4,
        ticks=6,
        tick_seconds=0.1,
        selected_node_ids=["drone-01", "drone-03"],
        route_waypoints=DEFAULT_ROUTE,
    )
    first = session.snapshot()
    assert first["liveExecution"] is False
    assert len(first["atakDrones"]) >= 2
    assert first["selectedNodeIds"] == ["drone-01", "drone-03"]
    assert len(first["routeWaypoints"]) >= 5
    held = session.apply_live_order(["drone-01"], "hold")
    assert held["liveOrders"]["drone-01"]["command"] == "hold"
    resumed = session.apply_live_order(["drone-01"], "resume")
    assert "drone-01" not in resumed["liveOrders"]
    time.sleep(0.25)
    later = session.snapshot()
    assert later["currentTick"] >= first["currentTick"]
    assert session.atak_snapshot()["drones"]

    with session.lock:
        session.started_at = time.time() - (session.total_ticks * session.tick_seconds)
    returning = session.snapshot()
    assert returning["status"] == "returning_home"
    assert "mission.return_home" in returning["networkTopics"]
    assert {item["state"] for item in returning["telemetry"]} == {"returning_home"}

    with session.lock:
        session.started_at = time.time() - ((session.total_timeline_ticks_locked() - 1) * session.tick_seconds)
    complete = session.snapshot()
    assert complete["status"] == "complete"
    home = complete["routeWaypoints"][0]
    for item in complete["telemetry"]:
        assert item["state"] == "complete"
        assert abs(item["position"]["lat"] - home["lat"]) < 0.000001
        assert abs(item["position"]["lon"] - home["lon"]) < 0.000001
    return complete


def main():
    parser = argparse.ArgumentParser(description="Run the DroneOps control station web view.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(self_test(), indent=2, sort_keys=True))
        return
    session = ControlStationMissionSession(mission_store_dir=os.environ.get("DRONEOPS_MISSION_STORE_DIR"))
    run_server(args.host, args.port, session, google_maps_api_key())


def google_maps_api_key():
    value = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if value:
        return value
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_config.env")
    if not os.path.exists(config_path):
        return ""
    with open(config_path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, raw_value = stripped.split("=", 1)
            if key.strip() == "GOOGLE_MAPS_API_KEY":
                return raw_value.strip().strip('"').strip("'")
    return ""


if __name__ == "__main__":
    main()
