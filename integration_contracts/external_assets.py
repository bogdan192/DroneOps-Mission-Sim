#!/usr/bin/env python3
"""Read-only external asset tracking contracts.

External assets are ground, air, maritime, or fixed systems observed by the
control station. They are situational-awareness inputs only. This contract does
not define tasking, targeting, weapons, or vehicle-control commands.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fleet_protocol import messages  # noqa: E402


ALLOWED_DOMAINS = {"ground", "air", "maritime", "fixed", "unknown"}
ALLOWED_KINDS = {"vehicle", "aircraft", "team", "sensor", "relay", "unknown"}
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
}


def normalize_external_asset(asset):
    if not isinstance(asset, dict):
        raise ValueError("external asset must be an object")
    reject_prohibited_fields(asset)
    uid = str(asset.get("uid") or asset.get("id") or "").strip()
    callsign = str(asset.get("callsign") or uid).strip()
    if not uid:
        raise ValueError("external asset uid is required")
    if not callsign:
        raise ValueError("external asset callsign is required")

    position = asset.get("position") or {}
    lat = float(position.get("lat", asset.get("lat")))
    lon = float(position.get("lon", asset.get("lon")))
    alt = float(position.get("alt", asset.get("alt", 0.0)))
    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        raise ValueError("external asset position contains invalid lat/lon")

    domain = str(asset.get("domain", "unknown")).lower()
    kind = str(asset.get("kind", "unknown")).lower()
    if domain not in ALLOWED_DOMAINS:
        domain = "unknown"
    if kind not in ALLOWED_KINDS:
        kind = "unknown"

    return {
        "type": "external.asset",
        "schemaVersion": "0.1",
        "uid": uid,
        "callsign": callsign,
        "domain": domain,
        "kind": kind,
        "source": str(asset.get("source", "unknown")),
        "status": str(asset.get("status", "observed")),
        "position": {"lat": lat, "lon": lon, "alt": alt},
        "lastSeenIso": str(asset.get("lastSeenIso") or messages.timestamp()),
        "readOnly": True,
        "liveExecution": False,
    }


def reject_prohibited_fields(value, path="asset"):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in PROHIBITED_FIELDS:
                raise ValueError("{} contains prohibited operational field: {}".format(path, key))
            reject_prohibited_fields(item, "{}.{}".format(path, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_prohibited_fields(item, "{}[{}]".format(path, index))


def asset_to_cot_like(asset):
    normalized = normalize_external_asset(asset)
    position = normalized["position"]
    return {
        "event": {
            "version": "2.0",
            "uid": normalized["uid"],
            "type": cot_type_for_asset(normalized),
            "how": "m-g",
            "time": normalized["lastSeenIso"],
            "start": normalized["lastSeenIso"],
            "stale": normalized["lastSeenIso"],
        },
        "point": {
            "lat": position["lat"],
            "lon": position["lon"],
            "hae": position["alt"],
            "ce": 25.0,
            "le": 25.0,
        },
        "detail": {
            "contact": {"callsign": normalized["callsign"]},
            "status": {
                "domain": normalized["domain"],
                "kind": normalized["kind"],
                "status": normalized["status"],
                "readOnly": True,
            },
        },
    }


def cot_type_for_asset(asset):
    domain = asset.get("domain")
    if domain == "air":
        return "a-f-A"
    if domain == "ground":
        return "a-f-G"
    if domain == "maritime":
        return "a-f-S"
    if domain == "fixed":
        return "a-f-G-I"
    return "a-u"


def self_test():
    asset = normalize_external_asset({
        "uid": "asset.ground.01",
        "callsign": "Ground Observer 1",
        "domain": "ground",
        "kind": "team",
        "source": "mock-external-assets",
        "position": {"lat": 44.406, "lon": 26.303, "alt": 75},
    })
    assert asset["readOnly"] is True
    assert asset_to_cot_like(asset)["detail"]["status"]["readOnly"] is True
    try:
        normalize_external_asset({"uid": "bad", "lat": 1, "lon": 1, "target": "x"})
        raise AssertionError("prohibited field accepted")
    except ValueError:
        pass
    return asset


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
