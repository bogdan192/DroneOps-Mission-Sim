#!/usr/bin/env python3
"""PC-side DroneOps simulation API.

This mirrors the current Android plugin API so the basestation/model pipeline can
be tested without an Android emulator or real autopilot.
"""

import argparse
import json
import math
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HOST = "127.0.0.1"
PORT = 47147
PROHIBITED_TERMS = ("attack", "strike", "weapon", "intercept", "ram")
ALLOWED_TASKS = ("observation", "survey", "mapping", "relay", "search", "report", "route")


class SimulationState:
    def __init__(self):
        self.lock = threading.Lock()
        self.started_at = time.time()
        self.mission_intents = []
        self.drones = [
            {
                "id": "sim-alpha",
                "state": "available",
                "latitude": 38.88950,
                "longitude": -77.03530,
                "altitudeMeters": 82.0,
                "batteryPercent": 94.0,
                "linkQualityPercent": 99.0,
                "assignedTask": None,
                "routeWaypoints": None,
                "routeStartedAt": None,
            },
            {
                "id": "sim-bravo",
                "state": "available",
                "latitude": 38.89030,
                "longitude": -77.03610,
                "altitudeMeters": 79.0,
                "batteryPercent": 92.0,
                "linkQualityPercent": 98.0,
                "assignedTask": None,
                "routeWaypoints": None,
                "routeStartedAt": None,
            },
            {
                "id": "sim-charlie",
                "state": "available",
                "latitude": 38.88890,
                "longitude": -77.03450,
                "altitudeMeters": 81.0,
                "batteryPercent": 96.0,
                "linkQualityPercent": 99.0,
                "assignedTask": None,
                "routeWaypoints": None,
                "routeStartedAt": None,
            },
        ]

    def configure_fleet(self, drone_count, start_point):
        count = int(drone_count)
        if count < 1 or count > 12:
            raise ValueError("droneCount must be between 1 and 12")
        lat = float(start_point["lat"])
        lon = float(start_point["lon"])
        alt = float(start_point.get("alt", 80))
        if lat < -90 or lat > 90 or lon < -180 or lon > 180:
            raise ValueError("start point contains invalid lat/lon")
        if alt < 0 or alt > 120:
            raise ValueError("start point altitude must be between 0 and 120m")

        with self.lock:
            self.drones = []
            for index in range(count):
                offset = (index - ((count - 1) / 2.0)) * 0.00008
                self.drones.append({
                    "id": "sim-{:02d}".format(index + 1),
                    "state": "available",
                    "latitude": round(lat + offset, 7),
                    "longitude": round(lon - offset, 7),
                    "altitudeMeters": alt,
                    "batteryPercent": max(70.0, 96.0 - index * 2.0),
                    "linkQualityPercent": max(85.0, 99.0 - index),
                    "assignedTask": None,
                    "routeWaypoints": None,
                    "routeStartedAt": None,
                })
            self.mission_intents = []

    def snapshot(self):
        with self.lock:
            self._advance_locked()
            return {
                "mode": "SIMULATION_ONLY",
                "liveFlightEnabled": False,
                "uptimeSeconds": round(time.time() - self.started_at, 1),
                "drones": self.drones,
                "missionIntents": self.mission_intents,
            }

    def accept_mission_intent(self, intent):
        normalized = validate_intent(intent)
        with self.lock:
            normalized["status"] = "accepted_for_simulation"
            normalized["acceptedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self.mission_intents.append(normalized)
            self._assign_tasks_locked(normalized)
            return {
                "accepted": True,
                "missionId": normalized["id"],
                "status": normalized["status"],
                "liveFlightEnabled": False,
            }

    def _assign_tasks_locked(self, intent):
        tasks = intent.get("tasks") or []
        if not tasks:
            return
        for index, drone in enumerate(self.drones):
            task = tasks[index % len(tasks)]
            drone["state"] = "simulating"
            drone["assignedTask"] = {
                "missionId": intent["id"],
                "type": task.get("type", "route"),
                "description": task.get("description", intent["objective"]),
            }
            route = intent.get("routeWaypoints")
            if route and len(route) >= 2:
                drone["routeWaypoints"] = route
                drone["routeStartedAt"] = time.time()

    def _advance_locked(self):
        elapsed = time.time() - self.started_at
        for index, drone in enumerate(self.drones):
            if drone["state"] != "simulating":
                continue
            route = drone.get("routeWaypoints")
            if route and len(route) >= 2:
                self._advance_route_locked(drone, route)
                continue
            angle = elapsed / 18.0 + index * (2 * math.pi / len(self.drones))
            drone["latitude"] = round(38.88990 + math.cos(angle) * 0.0011, 7)
            drone["longitude"] = round(-77.03510 + math.sin(angle) * 0.0011, 7)
            drone["altitudeMeters"] = round(82.0 + math.sin(angle) * 6.0, 1)
            drone["batteryPercent"] = max(20.0, round(drone["batteryPercent"] - 0.02, 2))

    def _advance_route_locked(self, drone, route):
        started_at = drone.get("routeStartedAt") or self.started_at
        segment_seconds = 5.0
        total_segments = len(route) - 1
        progress = ((time.time() - started_at) / segment_seconds) % total_segments
        segment = int(progress)
        fraction = progress - segment
        start = route[segment]
        end = route[segment + 1]
        drone["latitude"] = round(lerp(float(start["lat"]), float(end["lat"]), fraction), 7)
        drone["longitude"] = round(lerp(float(start["lon"]), float(end["lon"]), fraction), 7)
        drone["altitudeMeters"] = round(lerp(float(start.get("alt", 80)), float(end.get("alt", 80)), fraction), 1)
        drone["batteryPercent"] = max(20.0, round(drone["batteryPercent"] - 0.02, 2))


STATE = SimulationState()


def validate_intent(intent):
    if not isinstance(intent, dict):
        raise ValueError("mission intent must be a JSON object")
    if intent.get("mode") != "simulation":
        raise ValueError("mode must be simulation")
    if intent.get("liveExecution") is not False:
        raise ValueError("liveExecution must be false")

    objective = str(intent.get("objective", "")).strip()
    if len(objective) < 4:
        raise ValueError("objective is required")
    lowered = objective.lower()
    for term in PROHIBITED_TERMS:
        if term in lowered:
            raise ValueError("objective contains prohibited term: {}".format(term))

    speed = float(intent.get("maxSpeedMetersPerSecond", 0))
    if speed <= 0 or speed > 20:
        raise ValueError("maxSpeedMetersPerSecond must be >0 and <=20")

    area = intent.get("operatingArea")
    if not isinstance(area, list) or len(area) < 3:
        raise ValueError("operatingArea must contain at least 3 points")

    tasks = intent.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("tasks must be a list")
    for task in tasks:
        task_type = str(task.get("type", "")).lower()
        if task_type not in ALLOWED_TASKS:
            raise ValueError("unsupported task type: {}".format(task_type))

    route = intent.get("routeWaypoints")
    if not isinstance(route, list) or len(route) < 2:
        raise ValueError("routeWaypoints must contain at least 2 points")
    for point in route:
        lat = float(point.get("lat"))
        lon = float(point.get("lon"))
        alt = float(point.get("alt", 0))
        if lat < -90 or lat > 90 or lon < -180 or lon > 180:
            raise ValueError("routeWaypoints contains invalid lat/lon")
        if alt < 0 or alt > 120:
            raise ValueError("routeWaypoints altitude must be between 0 and 120m")

    normalized = dict(intent)
    normalized["liveExecution"] = False
    normalized["mode"] = "simulation"
    return normalized


def lerp(start, end, fraction):
    return start + (end - start) * fraction


class DroneOpsHandler(BaseHTTPRequestHandler):
    server_version = "DroneOpsSim/0.1"

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {
                "service": "DroneOps PC Simulation",
                "mode": "SIMULATION_ONLY",
                "liveFlightEnabled": False,
            })
            return
        if self.path == "/fleet":
            self._json(200, STATE.snapshot())
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/mission-intents":
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            response = STATE.accept_mission_intent(payload)
            self._json(200, response)
        except Exception as exc:
            self._json(422, {
                "accepted": False,
                "reason": str(exc),
                "mode": "SIMULATION_ONLY",
            })

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


def run_server(host, port):
    server = ThreadingHTTPServer((host, port), DroneOpsHandler)
    print("DroneOps simulation API listening on http://{}:{}".format(host, port))
    try:
        server.serve_forever()
    finally:
        server.server_close()


def request_json(method, url, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def self_test(host, port):
    server = ThreadingHTTPServer((host, port), DroneOpsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_host, actual_port = server.server_address
    base = "http://{}:{}".format(actual_host, actual_port)
    try:
        print(json.dumps(request_json("GET", base + "/health"), indent=2, sort_keys=True))
        intent = {
            "id": "self-test-survey",
            "mode": "simulation",
            "objective": "survey bounded area and report coverage",
            "liveExecution": False,
            "requiresHumanApproval": True,
            "maxSpeedMetersPerSecond": 15,
            "operatingArea": [
                {"lat": 38.889, "lon": -77.036},
                {"lat": 38.891, "lon": -77.036},
                {"lat": 38.891, "lon": -77.034},
                {"lat": 38.889, "lon": -77.034},
            ],
            "routeWaypoints": [
                {"lat": 38.889, "lon": -77.036, "alt": 80, "label": "START"},
                {"lat": 38.8902, "lon": -77.0357, "alt": 90, "label": "WP1"},
                {"lat": 38.891, "lon": -77.034, "alt": 80, "label": "END"},
            ],
            "constraints": {
                "minBatteryPercent": 35,
                "maxAltitudeMeters": 100,
                "lostLinkAction": "return_to_launch",
                "geofenceRequired": True,
            },
            "tasks": [
                {
                    "type": "route",
                    "description": "Fly simulated route and report coverage.",
                    "priority": 1,
                }
            ],
        }
        print(json.dumps(
            request_json("POST", base + "/mission-intents", intent),
            indent=2,
            sort_keys=True,
        ))
        time.sleep(0.2)
        print(json.dumps(request_json("GET", base + "/fleet"), indent=2, sort_keys=True))
    finally:
        server.shutdown()
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Run the DroneOps PC simulation API.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test(args.host, args.port)
    else:
        run_server(args.host, args.port)


if __name__ == "__main__":
    main()
