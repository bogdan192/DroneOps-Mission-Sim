#!/usr/bin/env python3
"""Fleet protocol message builders.

These messages are plain JSON-compatible dicts so they can later travel over
CoT, TAK plugin IPC, HTTP, MQTT, or another authenticated transport.
"""

import time


MESSAGE_TYPES = (
    "node.status",
    "order.intent",
    "mission.proposal",
    "mission.assignment",
    "mission.telemetry",
)


def node_status(node_id, position, battery_percent=100.0, role="worker", capabilities=None, state="available"):
    msg = {
        "type": "node.status",
        "schemaVersion": "0.1",
        "timestamp": timestamp(),
        "nodeId": str(node_id),
        "role": role,
        "state": state,
        "position": {
            "lat": float(position["lat"]),
            "lon": float(position["lon"]),
            "alt": float(position.get("alt", 0.0)),
        },
        "batteryPercent": float(battery_percent),
        "capabilities": capabilities or ["route", "survey", "relay"],
    }
    return validate_message(msg)


def order_intent(order_id, text, issuer="basestation", route_waypoints=None):
    msg = {
        "type": "order.intent",
        "schemaVersion": "0.1",
        "timestamp": timestamp(),
        "orderId": str(order_id),
        "issuer": str(issuer),
        "text": str(text),
        "routeWaypoints": route_waypoints or [],
    }
    return validate_message(msg)


def mission_assignment(mission_id, node_id, route_waypoints, task_type="route"):
    msg = {
        "type": "mission.assignment",
        "schemaVersion": "0.1",
        "timestamp": timestamp(),
        "missionId": str(mission_id),
        "nodeId": str(node_id),
        "taskType": task_type,
        "routeWaypoints": route_waypoints,
        "liveExecution": False,
    }
    return validate_message(msg)


def validate_message(message):
    if not isinstance(message, dict):
        raise ValueError("fleet message must be a JSON object")
    if message.get("type") not in MESSAGE_TYPES:
        raise ValueError("unsupported message type: {}".format(message.get("type")))
    if message.get("schemaVersion") != "0.1":
        raise ValueError("unsupported schemaVersion")
    return message


def timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

