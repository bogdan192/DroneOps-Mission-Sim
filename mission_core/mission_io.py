#!/usr/bin/env python3
"""Mission DSL persistence and GeoJSON route helpers."""

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mission_core import mission_schema


SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def default_mission_store_dir(root=None):
    base = Path(root) if root else Path(__file__).resolve().parents[1]
    return base / "data" / "missions"


def mission_file_name(mission_id):
    safe_id = SAFE_ID_RE.sub("-", str(mission_id or "").strip()).strip("-._")
    if not safe_id:
        raise ValueError("missionId is required")
    return "{}.json".format(safe_id)


def save_mission_dsl(mission, directory=None):
    normalized = mission_schema.validate_mission_dsl(mission)
    target_dir = Path(directory) if directory else default_mission_store_dir()
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        target_dir = Path(tempfile.gettempdir()) / "droneops-missions"
        target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / mission_file_name(normalized["missionId"])
    path.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "missionId": normalized["missionId"],
        "path": str(path),
        "bytes": path.stat().st_size,
    }


def load_mission_dsl(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return mission_schema.validate_mission_dsl(payload)


def list_mission_dsl(directory=None):
    target_dir = Path(directory) if directory else default_mission_store_dir()
    if not target_dir.exists():
        return []
    missions = []
    for path in sorted(target_dir.glob("*.json")):
        try:
            mission = load_mission_dsl(path)
        except Exception:
            continue
        missions.append({
            "missionId": mission["missionId"],
            "objective": mission.get("objective", ""),
            "source": mission.get("source", ""),
            "path": str(path),
            "waypointCount": len(mission.get("routeWaypoints", [])),
            "liveExecution": False,
        })
    return missions


def route_to_geojson(route_waypoints, properties=None):
    route = mission_schema.normalize_route(route_waypoints)
    return {
        "type": "Feature",
        "properties": {
            **(properties or {}),
            "mode": "SIMULATION_ONLY",
            "waypoints": [
                {"label": point["label"], "alt": point["alt"]}
                for point in route
            ],
        },
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [point["lon"], point["lat"], point["alt"]]
                for point in route
            ],
        },
    }


def route_from_geojson(payload):
    feature = _extract_route_feature(payload)
    geometry = feature.get("geometry") or {}
    if geometry.get("type") != "LineString":
        raise ValueError("GeoJSON route must be a LineString Feature")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise ValueError("GeoJSON route must contain at least two coordinates")
    waypoint_meta = (feature.get("properties") or {}).get("waypoints") or []
    route = []
    for index, coordinate in enumerate(coordinates):
        if not isinstance(coordinate, list) or len(coordinate) < 2:
            raise ValueError("GeoJSON coordinate {} must contain lon and lat".format(index))
        meta = waypoint_meta[index] if index < len(waypoint_meta) and isinstance(waypoint_meta[index], dict) else {}
        route.append({
            "label": meta.get("label") or ("START" if index == 0 else ("END" if index == len(coordinates) - 1 else "WP{}".format(index))),
            "lat": coordinate[1],
            "lon": coordinate[0],
            "alt": coordinate[2] if len(coordinate) > 2 else meta.get("alt", 80.0),
        })
    return mission_schema.normalize_route(route)


def _extract_route_feature(payload):
    if not isinstance(payload, dict):
        raise ValueError("GeoJSON payload must be an object")
    if payload.get("type") == "Feature":
        return payload
    if payload.get("type") == "FeatureCollection":
        for feature in payload.get("features") or []:
            if (feature.get("geometry") or {}).get("type") == "LineString":
                return feature
        raise ValueError("GeoJSON FeatureCollection does not contain a LineString")
    if payload.get("type") == "LineString":
        return {"type": "Feature", "properties": {}, "geometry": payload}
    raise ValueError("unsupported GeoJSON route type: {}".format(payload.get("type")))


def self_test():
    mission = mission_schema.build_route_mission(
        "simulate route export",
        [
            {"label": "START", "lat": 44.4057, "lon": 26.3019, "alt": 80},
            {"label": "WP1", "lat": 44.4074, "lon": 26.3078, "alt": 90},
            {"label": "END", "lat": 44.40571, "lon": 26.30191, "alt": 80},
        ],
        source="mission-io-test",
    )
    geojson = route_to_geojson(mission["routeWaypoints"], {"missionId": mission["missionId"]})
    imported = route_from_geojson(geojson)
    assert imported == mission["routeWaypoints"]
    return {"mission": mission, "geojson": geojson}


if __name__ == "__main__":
    print(json.dumps(self_test(), indent=2, sort_keys=True))
