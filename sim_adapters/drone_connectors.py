#!/usr/bin/env python3
"""Simulation-only connector registry for ATAK-equipped drones."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from integration_contracts.drone_connectors import (  # noqa: E402
    normalize_atak_drone_registration,
    normalize_connector_heartbeat,
    normalize_drone_middleware_connector,
)


def build_simulated_atak_drone_registrations():
    raw = [
        {
            "nodeId": "atak-drone-01",
            "callsign": "ATAK Drone 01",
            "platform": "android-atak-companion",
            "links": [
                {"linkType": "atak-cot", "endpointRef": "cot://mock-atak/drone-01"},
                {"linkType": "mavlink-readonly", "endpointRef": "udp://mock-mavlink/drone-01"},
            ],
            "capabilities": ["telemetry", "health", "observation_report"],
            "position": {"lat": 44.4057, "lon": 26.3019, "alt": 80},
            "state": "online",
        },
        {
            "nodeId": "atak-drone-02",
            "callsign": "ATAK Drone 02",
            "platform": "android-atak-companion",
            "links": [
                {"linkType": "atak-cot", "endpointRef": "cot://mock-atak/drone-02"},
                {"linkType": "vendor-sdk-readonly", "endpointRef": "sdk://mock-vendor/drone-02"},
            ],
            "capabilities": ["telemetry", "health"],
            "position": {"lat": 44.4058, "lon": 26.3020, "alt": 80},
            "state": "registered",
        },
    ]
    return [normalize_atak_drone_registration(item) for item in raw]


def build_simulated_drone_middleware_connectors():
    raw = [
        {
            "connectorId": "mavlink-readonly-adapter",
            "name": "MAVLink Read-Only Adapter",
            "linkType": "mavlink-readonly",
            "endpointRef": "udp://readonly/not-configured",
            "state": "registered",
            "supportedInputs": ["heartbeat", "gps", "battery", "attitude"],
        },
        {
            "connectorId": "vendor-sdk-readonly-adapter",
            "name": "Vendor SDK Read-Only Adapter",
            "linkType": "vendor-sdk-readonly",
            "endpointRef": "sdk://readonly/not-configured",
            "state": "registered",
            "supportedInputs": ["health", "gps", "media_metadata"],
        },
    ]
    return [normalize_drone_middleware_connector(item) for item in raw]


def apply_simulated_heartbeat(registrations, heartbeat):
    normalized = normalize_connector_heartbeat(heartbeat)
    updated = []
    found = False
    for item in registrations:
        if item["nodeId"] != normalized["nodeId"]:
            updated.append(item)
            continue
        merged = dict(item)
        merged["state"] = normalized["state"]
        merged["lastHeartbeatIso"] = normalized["lastHeartbeatIso"]
        if normalized["position"]:
            merged["position"] = normalized["position"]
        if normalized["batteryPercent"] is not None:
            merged["batteryPercent"] = normalized["batteryPercent"]
        updated.append(merged)
        found = True
    if not found:
        updated.append(normalize_atak_drone_registration({
            "nodeId": normalized["nodeId"],
            "callsign": normalized["nodeId"],
            "state": normalized["state"],
            "position": normalized["position"] or {},
            "capabilities": ["telemetry", "health"],
        }))
    return updated


def self_test():
    registrations = build_simulated_atak_drone_registrations()
    middleware = build_simulated_drone_middleware_connectors()
    updated = apply_simulated_heartbeat(registrations, {
        "nodeId": "atak-drone-01",
        "batteryPercent": 90,
        "position": {"lat": 44.406, "lon": 26.303, "alt": 82},
    })
    assert len(registrations) == 2
    assert len(middleware) == 2
    assert updated[0]["batteryPercent"] == 90.0
    assert all(item["readOnly"] for item in registrations + middleware + updated)
    return {"registrations": updated, "middleware": middleware}


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
