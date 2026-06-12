#!/usr/bin/env python3
"""Local model adapter for DroneOps mission-intent planning."""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_DRONEOPS_URL = "http://127.0.0.1:47147"
MAX_SPEED_METERS_PER_SECOND = 20.0
PROHIBITED_TERMS = (
    "attack",
    "strike",
    "weapon",
    "intercept",
    "ram",
    "target person",
    "target vehicle",
)

MISSION_INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "mode": {"type": "string", "enum": ["simulation"]},
        "objective": {"type": "string"},
        "liveExecution": {"type": "boolean"},
        "requiresHumanApproval": {"type": "boolean"},
        "maxSpeedMetersPerSecond": {"type": "number"},
        "operatingArea": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                },
                "required": ["lat", "lon"],
            },
        },
        "routeWaypoints": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                    "alt": {"type": "number"},
                    "label": {"type": "string"},
                },
                "required": ["lat", "lon", "alt", "label"],
            },
        },
        "constraints": {
            "type": "object",
            "properties": {
                "minBatteryPercent": {"type": "number"},
                "maxAltitudeMeters": {"type": "number"},
                "lostLinkAction": {"type": "string"},
                "geofenceRequired": {"type": "boolean"},
            },
            "required": [
                "minBatteryPercent",
                "maxAltitudeMeters",
                "lostLinkAction",
                "geofenceRequired",
            ],
        },
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "integer"},
                },
                "required": ["type", "description", "priority"],
            },
        },
    },
    "required": [
        "id",
        "mode",
        "objective",
        "liveExecution",
        "requiresHumanApproval",
        "maxSpeedMetersPerSecond",
        "operatingArea",
        "routeWaypoints",
        "constraints",
        "tasks",
    ],
}

SYSTEM_PROMPT = """You convert natural-language drone fleet orders into DroneOps mission-intent JSON.

Rules:
- Produce only JSON matching the schema.
- Create high-level mission intent only.
- Do not create raw MAVLink, arming, takeoff, velocity, actuator, or weapon commands.
- The output must be simulation-only: mode="simulation" and liveExecution=false.
- requiresHumanApproval must be true.
- Include a bounded operatingArea with at least 3 lat/lon points. If the order lacks coordinates, use the provided safe demo area.
- Include routeWaypoints for point-to-point flight. Extract all lat/lon coordinate pairs from the order in order. If no route coordinates exist, use the provided safe demo area as a short route.
- Use only observation, survey, mapping, relay, search, report, or route task types.
- Reject unsafe tasking by setting objective to "rejected unsafe tasking" and using an empty tasks list.
"""

SAFE_DEMO_AREA = [
    {"lat": 38.889, "lon": -77.036},
    {"lat": 38.891, "lon": -77.036},
    {"lat": 38.891, "lon": -77.034},
    {"lat": 38.889, "lon": -77.034},
]

COORD_PAIR_PATTERN = re.compile(
    r"(?P<lat>[+-]?(?:\\d+(?:\\.\\d+)?))\\s*,\\s*(?P<lon>[+-]?(?:\\d+(?:\\.\\d+)?))"
)


class PlannerError(Exception):
    pass


def post_json(url, payload, timeout_seconds):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise PlannerError("HTTP {} from {}: {}".format(exc.code, url, body))
    except urllib.error.URLError as exc:
        raise PlannerError("could not reach {}: {}".format(url, exc.reason))


def call_ollama(order, model, ollama_url, timeout_seconds):
    payload = {
        "model": model,
        "stream": False,
        "format": MISSION_INTENT_SCHEMA,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Order: {}\n\nSafe demo operatingArea if none is provided: {}"
                    .format(order, json.dumps(SAFE_DEMO_AREA))
                ),
            },
        ],
    }
    response = post_json(
        ollama_url.rstrip("/") + "/api/chat",
        payload,
        timeout_seconds,
    )
    content = response.get("message", {}).get("content")
    if not content:
        raise PlannerError("model returned no message content")
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise PlannerError("model returned invalid JSON: {}".format(exc))


def mock_intent(order):
    route = route_from_order(order)
    return {
        "id": "intent-{}".format(int(time.time())),
        "mode": "simulation",
        "objective": order.strip(),
        "liveExecution": False,
        "requiresHumanApproval": True,
        "maxSpeedMetersPerSecond": 15.0,
        "operatingArea": SAFE_DEMO_AREA,
        "routeWaypoints": route,
        "constraints": {
            "minBatteryPercent": 35.0,
            "maxAltitudeMeters": 100.0,
            "lostLinkAction": "return_to_launch",
            "geofenceRequired": True,
        },
        "tasks": [
            {
                "type": "route",
                "description": "Fly the simulated route through the supplied waypoints.",
                "priority": 1,
            }
        ],
    }


def route_from_order(order):
    points = []
    for index, match in enumerate(COORD_PAIR_PATTERN.finditer(order)):
        lat = float(match.group("lat"))
        lon = float(match.group("lon"))
        if lat < -90 or lat > 90 or lon < -180 or lon > 180:
            continue
        points.append({
            "lat": lat,
            "lon": lon,
            "alt": 80.0,
            "label": "WP{}".format(index + 1),
        })

    if len(points) >= 2:
        return points

    return [
        {"lat": 38.8890, "lon": -77.0360, "alt": 80.0, "label": "START"},
        {"lat": 38.8902, "lon": -77.0357, "alt": 90.0, "label": "WP1"},
        {"lat": 38.8910, "lon": -77.0340, "alt": 80.0, "label": "END"},
    ]


def validate_order_text(order):
    lowered = order.lower()
    for term in PROHIBITED_TERMS:
        if term in lowered:
            raise PlannerError("order contains prohibited term: {}".format(term))


def validate_intent(intent):
    if not isinstance(intent, dict):
        raise PlannerError("intent must be a JSON object")

    prohibited_fields = ("rawCommands", "mavlink", "actuator", "arm", "takeoff")
    for field in prohibited_fields:
        if field in intent:
            raise PlannerError("intent contains prohibited field: {}".format(field))

    if intent.get("mode") != "simulation":
        raise PlannerError("mode must be simulation")
    if intent.get("liveExecution") is not False:
        raise PlannerError("liveExecution must be false")
    if intent.get("requiresHumanApproval") is not True:
        raise PlannerError("requiresHumanApproval must be true")

    objective = str(intent.get("objective", "")).strip()
    if len(objective) < 4:
        raise PlannerError("objective is required")
    lowered = objective.lower()
    for term in PROHIBITED_TERMS:
        if term in lowered:
            raise PlannerError("objective contains prohibited term: {}".format(term))

    speed = float(intent.get("maxSpeedMetersPerSecond", 0))
    if speed <= 0 or speed > MAX_SPEED_METERS_PER_SECOND:
        raise PlannerError(
            "maxSpeedMetersPerSecond must be >0 and <= {}".format(
                MAX_SPEED_METERS_PER_SECOND
            )
        )

    area = intent.get("operatingArea")
    if not isinstance(area, list) or len(area) < 3:
        raise PlannerError("operatingArea must contain at least 3 points")
    for point in area:
        lat = float(point.get("lat"))
        lon = float(point.get("lon"))
        if lat < -90 or lat > 90 or lon < -180 or lon > 180:
            raise PlannerError("operatingArea contains invalid lat/lon")

    route = intent.get("routeWaypoints")
    if not isinstance(route, list) or len(route) < 2:
        raise PlannerError("routeWaypoints must contain at least 2 points")
    for index, point in enumerate(route):
        lat = float(point.get("lat"))
        lon = float(point.get("lon"))
        alt = float(point.get("alt", 0))
        if lat < -90 or lat > 90 or lon < -180 or lon > 180:
            raise PlannerError("routeWaypoints contains invalid lat/lon")
        if alt < 0 or alt > 120:
            raise PlannerError("routeWaypoints altitude must be between 0 and 120m")
        point.setdefault("label", "WP{}".format(index + 1))

    constraints = intent.get("constraints", {})
    if constraints.get("geofenceRequired") is not True:
        raise PlannerError("geofenceRequired must be true")
    if constraints.get("lostLinkAction") not in ("return_to_launch", "hold", "land"):
        raise PlannerError("lostLinkAction must be return_to_launch, hold, or land")

    tasks = intent.get("tasks")
    if not isinstance(tasks, list):
        raise PlannerError("tasks must be a list")
    for task in tasks:
        task_type = str(task.get("type", "")).lower()
        if task_type not in ("observation", "survey", "mapping", "relay", "search", "report", "route"):
            raise PlannerError("unsupported task type: {}".format(task_type))

    return intent


def submit_to_droneops(intent, droneops_url, timeout_seconds):
    return post_json(
        droneops_url.rstrip("/") + "/mission-intents",
        intent,
        timeout_seconds,
    )


def main(argv):
    parser = argparse.ArgumentParser(description="Plan DroneOps mission intent with a local model.")
    parser.add_argument("order", help="Natural-language mission order to interpret.")
    parser.add_argument("--model", default="llama3.1:8b", help="Local Ollama model name.")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--droneops-url", default=DEFAULT_DRONEOPS_URL)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--mock", action="store_true", help="Skip model call and emit a safe mock intent.")
    parser.add_argument("--submit", action="store_true", help="Submit the validated intent to DroneOps.")
    args = parser.parse_args(argv)

    try:
        validate_order_text(args.order)
        intent = mock_intent(args.order) if args.mock else call_ollama(
            args.order,
            args.model,
            args.ollama_url,
            args.timeout,
        )
        intent = validate_intent(intent)

        print(json.dumps(intent, indent=2, sort_keys=True))

        if args.submit:
            response = submit_to_droneops(intent, args.droneops_url, args.timeout)
            print(json.dumps({"droneopsResponse": response}, indent=2, sort_keys=True))
    except PlannerError as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
