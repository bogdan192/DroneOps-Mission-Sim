#!/usr/bin/env python3
"""Read-only ATAK/CoT-style telemetry ingest contracts.

This module models inbound tracks from ATAK-equipped drones, personnel/team
devices, or other air assets. It normalizes those tracks into the existing
read-only external-asset shape for display and shared situational awareness.

It intentionally does not define TAK writes, mission tasking, target
designation, route upload, or vehicle-control commands.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fleet_protocol import messages  # noqa: E402
from integration_contracts.external_assets import (  # noqa: E402
    asset_to_cot_like,
    normalize_external_asset,
)


PROHIBITED_FIELDS = {
    "target",
    "targets",
    "weapon",
    "weapons",
    "fireMission",
    "engage",
    "engagement",
    "strike",
    "attack",
    "intercept",
    "command",
    "tasking",
    "routeCommand",
    "missionUpload",
    "controllerCommand",
}


def normalize_atak_track(track):
    """Normalize an inbound ATAK/CoT-like track as read-only telemetry."""
    if not isinstance(track, dict):
        raise ValueError("ATAK track must be an object")
    reject_prohibited_fields(track)

    uid = str(track.get("uid") or track.get("id") or "").strip()
    callsign = str(track.get("callsign") or track.get("name") or uid).strip()
    if not uid:
        raise ValueError("ATAK track uid is required")
    if not callsign:
        raise ValueError("ATAK track callsign is required")

    position = extract_position(track)
    domain, kind = classify_track(track)

    normalized = {
        "type": "atak.track",
        "schemaVersion": "0.1",
        "uid": uid,
        "callsign": callsign,
        "cotType": str(track.get("cotType") or track.get("type") or "a-u"),
        "domain": domain,
        "kind": kind,
        "source": str(track.get("source", "atak-readonly-feed")),
        "status": str(track.get("status", "observed")),
        "position": position,
        "speedMps": optional_float(track.get("speedMps", track.get("speed"))),
        "courseDeg": optional_float(track.get("courseDeg", track.get("course"))),
        "lastSeenIso": str(track.get("lastSeenIso") or track.get("time") or messages.timestamp()),
        "readOnly": True,
        "liveExecution": False,
    }
    return normalized


def atak_track_to_external_asset(track):
    normalized = normalize_atak_track(track)
    asset = normalize_external_asset({
        "uid": normalized["uid"],
        "callsign": normalized["callsign"],
        "domain": normalized["domain"],
        "kind": normalized["kind"],
        "source": normalized["source"],
        "status": normalized["status"],
        "position": normalized["position"],
        "lastSeenIso": normalized["lastSeenIso"],
    })
    asset["atakTrack"] = normalized
    asset["cotLike"] = asset_to_cot_like(asset)
    return asset


def extract_position(track):
    point = track.get("point") or track.get("position") or {}
    lat = float(point.get("lat", track.get("lat")))
    lon = float(point.get("lon", point.get("lng", track.get("lon"))))
    alt = float(point.get("hae", point.get("alt", track.get("alt", 0.0))))
    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        raise ValueError("ATAK track position contains invalid lat/lon")
    return {"lat": lat, "lon": lon, "alt": alt}


def classify_track(track):
    explicit_domain = str(track.get("domain", "")).lower()
    explicit_kind = str(track.get("kind", "")).lower()
    if explicit_domain and explicit_kind:
        return explicit_domain, explicit_kind

    cot_type = str(track.get("cotType") or track.get("type") or "").lower()
    uid = str(track.get("uid") or "").lower()
    callsign = str(track.get("callsign") or "").lower()
    text = " ".join([cot_type, uid, callsign, explicit_kind])

    if any(token in text for token in ("uas", "uav", "drone", "quad")):
        return "air", "drone"
    if cot_type.startswith("a-f-a") or "air" in text or "helo" in text or "aircraft" in text:
        return "air", "aircraft"
    if any(token in text for token in ("team", "person", "troop", "infantry", "operator")):
        return "ground", "personnel"
    if cot_type.startswith("a-f-g"):
        return "ground", "vehicle"
    return explicit_domain or "unknown", explicit_kind or "unknown"


def optional_float(value):
    if value in (None, ""):
        return None
    return float(value)


def reject_prohibited_fields(value, path="atakTrack"):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in PROHIBITED_FIELDS:
                raise ValueError("{} contains prohibited operational field: {}".format(path, key))
            reject_prohibited_fields(item, "{}.{}".format(path, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_prohibited_fields(item, "{}[{}]".format(path, index))


def self_test():
    drone = normalize_atak_track({
        "uid": "atak.drone.scout-01",
        "callsign": "Scout Drone 1",
        "cotType": "a-f-A-UAS",
        "point": {"lat": 44.4082, "lon": 26.3111, "hae": 130},
    })
    assert drone["domain"] == "air"
    assert drone["kind"] == "drone"
    assert drone["readOnly"] is True

    troop_asset = atak_track_to_external_asset({
        "uid": "atak.team.alpha",
        "callsign": "Team Alpha",
        "kind": "personnel",
        "domain": "ground",
        "lat": 44.4051,
        "lon": 26.3051,
        "alt": 75,
    })
    assert troop_asset["kind"] == "personnel"
    assert troop_asset["cotLike"]["detail"]["status"]["readOnly"] is True

    try:
        normalize_atak_track({"uid": "bad", "lat": 1, "lon": 1, "missionUpload": {}})
        raise AssertionError("prohibited field accepted")
    except ValueError:
        pass
    return {"drone": drone, "troopAsset": troop_asset}


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
