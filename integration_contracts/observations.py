#!/usr/bin/env python3
"""Read-only observation report contracts.

Observation reports are image-and-coordinate sightings from simulated drones or
future reviewed sensor feeds. They are situational-awareness records only. This
contract does not define target designation, weapon tasking, intercept guidance,
or vehicle-control commands.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fleet_protocol import messages  # noqa: E402


ALLOWED_CATEGORIES = {
    "structure_feature",
    "vehicle",
    "terrain",
    "infrastructure",
    "unknown",
}

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


def normalize_observation_report(report):
    if not isinstance(report, dict):
        raise ValueError("observation report must be an object")
    reject_prohibited_fields(report)

    report_id = str(report.get("reportId") or report.get("id") or "").strip()
    reporting_node_id = str(report.get("reportingNodeId") or report.get("nodeId") or "").strip()
    label = str(report.get("label") or "Observation").strip()
    if not report_id:
        raise ValueError("observation reportId is required")
    if not reporting_node_id:
        raise ValueError("observation reportingNodeId is required")
    if not label:
        raise ValueError("observation label is required")

    position = report.get("position") or {}
    lat = float(position.get("lat", report.get("lat")))
    lon = float(position.get("lon", report.get("lon")))
    alt = float(position.get("alt", report.get("alt", 0.0)))
    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        raise ValueError("observation position contains invalid lat/lon")

    image_data_uri = str(report.get("imageDataUri") or "").strip()
    if image_data_uri and not image_data_uri.startswith("data:image/"):
        raise ValueError("observation imageDataUri must be a data:image URI")

    category = str(report.get("category", "unknown")).lower()
    if category not in ALLOWED_CATEGORIES:
        category = "unknown"
    confidence = float(report.get("confidence", 0.0))
    confidence = min(1.0, max(0.0, confidence))

    return {
        "type": "observation.report",
        "schemaVersion": "0.1",
        "reportId": report_id,
        "reportingNodeId": reporting_node_id,
        "missionId": str(report.get("missionId") or ""),
        "label": label,
        "category": category,
        "confidence": round(confidence, 3),
        "position": {"lat": lat, "lon": lon, "alt": alt},
        "imageDataUri": image_data_uri,
        "source": str(report.get("source", "unknown")),
        "timestamp": str(report.get("timestamp") or messages.timestamp()),
        "readOnly": True,
        "liveExecution": False,
    }


def reject_prohibited_fields(value, path="observation"):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in PROHIBITED_FIELDS:
                raise ValueError("{} contains prohibited operational field: {}".format(path, key))
            reject_prohibited_fields(item, "{}.{}".format(path, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_prohibited_fields(item, "{}[{}]".format(path, index))


def observation_to_cot_like(report):
    normalized = normalize_observation_report(report)
    position = normalized["position"]
    return {
        "event": {
            "version": "2.0",
            "uid": normalized["reportId"],
            "type": "b-m-p-s-p-i",
            "how": "m-g",
            "time": normalized["timestamp"],
            "start": normalized["timestamp"],
            "stale": normalized["timestamp"],
        },
        "point": {
            "lat": position["lat"],
            "lon": position["lon"],
            "hae": position["alt"],
            "ce": 20.0,
            "le": 20.0,
        },
        "detail": {
            "contact": {"callsign": normalized["reportingNodeId"]},
            "remarks": {
                "label": normalized["label"],
                "category": normalized["category"],
                "confidence": normalized["confidence"],
                "readOnly": True,
            },
        },
    }


def self_test():
    report = normalize_observation_report({
        "reportId": "obs.red-roof.01",
        "reportingNodeId": "drone-01",
        "label": "Red roof",
        "category": "structure_feature",
        "confidence": 0.87,
        "position": {"lat": 44.4081, "lon": 26.3142, "alt": 88},
        "imageDataUri": "data:image/svg+xml;utf8,%3Csvg%3E%3C/svg%3E",
    })
    assert report["readOnly"] is True
    assert report["liveExecution"] is False
    assert observation_to_cot_like(report)["detail"]["remarks"]["readOnly"] is True
    try:
        normalize_observation_report({"reportId": "bad", "nodeId": "drone-01", "lat": 1, "lon": 1, "tasking": "x"})
        raise AssertionError("prohibited field accepted")
    except ValueError:
        pass
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
