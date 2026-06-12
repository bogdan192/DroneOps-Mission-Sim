#!/usr/bin/env python3
"""Simulation-only mission DSL.

The DSL is the boundary between language/model reasoning and anything that can
eventually talk to a controller adapter. It intentionally contains intent,
constraints, and waypoints only. It does not contain raw flight-controller
commands.
"""

import math
import time


PROHIBITED_TERMS = ("attack", "strike", "weapon", "intercept", "ram")
RAW_COMMAND_FIELDS = (
    "mavlink",
    "mavlinkCommand",
    "actuator",
    "servo",
    "arm",
    "takeoff",
    "velocityCommand",
    "rcOverride",
)


def build_route_mission(order_text, route_waypoints, source="onboard-node"):
    route = normalize_route(route_waypoints)
    lats = [point["lat"] for point in route]
    lons = [point["lon"] for point in route]
    pad = 0.001
    mission = {
        "missionId": "mission-{}".format(int(time.time())),
        "source": source,
        "mode": "simulation",
        "liveExecution": False,
        "requiresHumanApproval": True,
        "objective": str(order_text or "simulate route mission").strip(),
        "constraints": {
            "geofenceRequired": True,
            "lostLinkAction": "return_to_launch",
            "maxAltitudeMeters": 100.0,
            "maxSpeedMetersPerSecond": 15.0,
            "minBatteryPercent": 35.0,
            "minSeparationMeters": 25.0,
        },
        "operatingArea": [
            {"lat": min(lats) - pad, "lon": min(lons) - pad},
            {"lat": max(lats) + pad, "lon": min(lons) - pad},
            {"lat": max(lats) + pad, "lon": max(lons) + pad},
            {"lat": min(lats) - pad, "lon": max(lons) + pad},
        ],
        "routeWaypoints": route,
        "tasks": [
            {
                "taskId": "task-route-1",
                "type": "route",
                "priority": 1,
                "description": "Fly the validated simulation route.",
            }
        ],
    }
    return validate_mission_dsl(mission)


def normalize_route(route_waypoints):
    if not isinstance(route_waypoints, list) or len(route_waypoints) < 2:
        raise ValueError("routeWaypoints must contain at least 2 points")
    normalized = []
    for index, point in enumerate(route_waypoints):
        lat = float(point.get("lat"))
        lon = float(point.get("lon"))
        alt = float(point.get("alt", 80.0))
        if lat < -90 or lat > 90 or lon < -180 or lon > 180:
            raise ValueError("route waypoint contains invalid lat/lon")
        if alt < 0 or alt > 120:
            raise ValueError("route waypoint altitude must be between 0 and 120m")
        label = point.get("label")
        if not label:
            label = "START" if index == 0 else ("END" if index == len(route_waypoints) - 1 else "WP{}".format(index))
        normalized.append({
            "label": str(label),
            "lat": lat,
            "lon": lon,
            "alt": alt,
        })
    return normalized


def validate_mission_dsl(mission):
    if not isinstance(mission, dict):
        raise ValueError("mission must be a JSON object")
    reject_raw_command_fields(mission)
    if mission.get("mode") != "simulation":
        raise ValueError("mission mode must be simulation")
    if mission.get("liveExecution") is not False:
        raise ValueError("liveExecution must be false")

    objective = str(mission.get("objective", "")).strip()
    if len(objective) < 4:
        raise ValueError("objective is required")
    lowered = objective.lower()
    for term in PROHIBITED_TERMS:
        if term in lowered:
            raise ValueError("objective contains prohibited term: {}".format(term))

    constraints = mission.get("constraints")
    if not isinstance(constraints, dict):
        raise ValueError("constraints are required")
    max_speed = float(constraints.get("maxSpeedMetersPerSecond", 0))
    if max_speed <= 0 or max_speed > 20:
        raise ValueError("maxSpeedMetersPerSecond must be >0 and <=20")

    area = mission.get("operatingArea")
    if not isinstance(area, list) or len(area) < 3:
        raise ValueError("operatingArea must contain at least 3 points")
    for point in area:
        float(point["lat"])
        float(point["lon"])

    route = normalize_route(mission.get("routeWaypoints"))
    tasks = mission.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks are required")

    normalized = dict(mission)
    normalized["mode"] = "simulation"
    normalized["liveExecution"] = False
    normalized["routeWaypoints"] = route
    return normalized


def reject_raw_command_fields(value, path="mission"):
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            for raw_key in RAW_COMMAND_FIELDS:
                if raw_key.lower() == lowered:
                    raise ValueError("raw controller command field is not allowed at {}".format(path))
            reject_raw_command_fields(child, "{}.{}".format(path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_raw_command_fields(child, "{}[{}]".format(path, index))


def distance_meters(a, b):
    lat1 = math.radians(float(a["lat"]))
    lat2 = math.radians(float(b["lat"]))
    dlat = lat2 - lat1
    dlon = math.radians(float(b["lon"]) - float(a["lon"]))
    sin_lat = math.sin(dlat / 2.0)
    sin_lon = math.sin(dlon / 2.0)
    h = sin_lat * sin_lat + math.cos(lat1) * math.cos(lat2) * sin_lon * sin_lon
    return 6371000.0 * 2.0 * math.atan2(math.sqrt(h), math.sqrt(1.0 - h))


def self_test():
    mission = build_route_mission(
        "simulate cooperative route",
        [
            {"lat": 44.4057, "lon": 26.3019, "alt": 80},
            {"lat": 44.4074, "lon": 26.3078, "alt": 90},
            {"lat": 44.4102, "lon": 26.3140, "alt": 80},
        ],
    )
    assert mission["liveExecution"] is False
    assert len(mission["routeWaypoints"]) == 3
    return mission


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))

