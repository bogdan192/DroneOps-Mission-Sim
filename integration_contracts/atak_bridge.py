#!/usr/bin/env python3
"""Android/ATAK bridge envelopes for simulation-only loopback."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fleet_protocol import messages  # noqa: E402
from integration_contracts.drone_connectors import normalize_node_order  # noqa: E402
from integration_contracts.runtime import require_simulation_payload  # noqa: E402


ALLOWED_BRIDGE_MODES = {"headless-android", "atak-plugin", "emulator-loopback", "unknown"}
ALLOWED_INTERFACES = {"http-loopback", "tak-plugin-ipc", "cot-event-feed", "android-service"}
PROHIBITED_FIELDS = {
    "mavlink",
    "missionUpload",
    "routeCommand",
    "controllerCommand",
    "arm",
    "takeoff",
    "land",
    "rtl",
    "actuator",
    "servo",
    "rcOverride",
    "target",
    "weapon",
    "engage",
    "attack",
    "strike",
}


def normalize_bridge_registration(registration):
    if not isinstance(registration, dict):
        raise ValueError("bridge registration must be an object")
    reject_prohibited_fields(registration)
    bridge_id = str(registration.get("bridgeId") or "").strip()
    node_id = str(registration.get("nodeId") or "").strip()
    if not bridge_id:
        raise ValueError("bridgeId is required")
    if not node_id:
        raise ValueError("nodeId is required")
    mode = str(registration.get("bridgeMode") or "unknown").strip().lower()
    if mode not in ALLOWED_BRIDGE_MODES:
        mode = "unknown"
    interfaces = sorted(set(
        str(item).strip()
        for item in registration.get("interfaces", [])
        if str(item).strip() in ALLOWED_INTERFACES
    ))
    return {
        "type": "atak.bridge.registration",
        "schemaVersion": "0.1",
        "bridgeId": bridge_id,
        "nodeId": node_id,
        "callsign": str(registration.get("callsign") or node_id),
        "appPackage": str(registration.get("appPackage") or "unknown"),
        "bridgeMode": mode,
        "interfaces": interfaces,
        "createdAtIso": str(registration.get("createdAtIso") or messages.timestamp()),
        "readOnly": True,
        "liveExecution": False,
    }


def normalize_bridge_order_envelope(envelope):
    if not isinstance(envelope, dict):
        raise ValueError("bridge order envelope must be an object")
    reject_prohibited_fields(envelope)
    order = normalize_node_order(envelope.get("order") or {})
    normalized = {
        "type": "atak.bridge.order_envelope",
        "schemaVersion": "0.1",
        "bridgeId": str(envelope.get("bridgeId") or "").strip(),
        "transport": str(envelope.get("transport") or "http-loopback"),
        "order": order,
        "createdAtIso": str(envelope.get("createdAtIso") or messages.timestamp()),
        "readOnly": True,
        "liveExecution": False,
    }
    if not normalized["bridgeId"]:
        raise ValueError("bridgeId is required")
    require_simulation_payload(normalized, "bridgeOrderEnvelope")
    return normalized


def onboard_order_payload_from_bridge(envelope):
    normalized = normalize_bridge_order_envelope(envelope)
    order = normalized["order"]
    return {
        "order": order["text"],
        "sourceBridgeId": normalized["bridgeId"],
        "sourceNodeId": order["nodeId"],
        "liveExecution": False,
    }


def reject_prohibited_fields(value, path="atakBridge"):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in {field.lower() for field in PROHIBITED_FIELDS}:
                raise ValueError("{} contains prohibited operational field: {}".format(path, key))
            reject_prohibited_fields(item, "{}.{}".format(path, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_prohibited_fields(item, "{}[{}]".format(path, index))


def self_test():
    registration = normalize_bridge_registration({
        "bridgeId": "android-loopback-01",
        "nodeId": "headless-node-01",
        "bridgeMode": "emulator-loopback",
        "interfaces": ["http-loopback", "cot-event-feed"],
    })
    envelope = normalize_bridge_order_envelope({
        "bridgeId": registration["bridgeId"],
        "order": {
            "orderId": "order-loopback-01",
            "nodeId": registration["nodeId"],
            "text": "report status as a swarm member",
        },
    })
    payload = onboard_order_payload_from_bridge(envelope)
    assert payload["liveExecution"] is False
    assert payload["order"] == "report status as a swarm member"
    try:
        normalize_bridge_registration({"bridgeId": "bad", "nodeId": "n1", "mavlink": {}})
        raise AssertionError("prohibited bridge field accepted")
    except ValueError:
        pass
    return {"registration": registration, "envelope": envelope, "payload": payload}


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
