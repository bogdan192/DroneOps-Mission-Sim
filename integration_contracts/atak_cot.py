#!/usr/bin/env python3
"""Simulation-safe CoT projection for DroneOps fleet messages."""

import html
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fleet_protocol import messages  # noqa: E402
from integration_contracts.runtime import require_simulation_payload  # noqa: E402


SUPPORTED_MESSAGE_TYPES = {
    "node.status",
    "order.intent",
    "mission.proposal",
    "mission.assignment",
    "mission.telemetry",
    "mission.return_home",
    "live.order",
    "connector.atak_drone.registration",
    "connector.atak_drone.heartbeat",
    "connector.node_order",
    "connector.node_order_result",
    "observation.report",
}


def fleet_message_to_cot_event(message, topic=None):
    if not isinstance(message, dict):
        raise ValueError("fleet message must be an object")
    require_simulation_payload(message, "fleetMessage")
    message_type = str(message.get("type") or topic or "").strip()
    if message_type not in SUPPORTED_MESSAGE_TYPES:
        raise ValueError("unsupported CoT projection message type: {}".format(message_type))
    point = _point_for_message(message)
    timestamp = str(message.get("timestamp") or message.get("lastSeenIso") or message.get("createdAtIso") or messages.timestamp())
    event = {
        "type": "atak.cot.event",
        "schemaVersion": "0.1",
        "sourceTopic": str(topic or message_type),
        "sourceMessageType": message_type,
        "uid": _uid_for_message(message, message_type),
        "cotType": _cot_type_for_message(message_type),
        "how": "m-g",
        "time": timestamp,
        "start": timestamp,
        "stale": timestamp,
        "point": point,
        "detail": {
            "contact": {"callsign": _callsign_for_message(message, message_type)},
            "droneops": {
                "messageType": message_type,
                "missionId": str(message.get("missionId") or ""),
                "nodeId": str(message.get("nodeId") or ""),
                "state": str(message.get("state") or message.get("status") or ""),
                "readOnly": True,
                "liveExecution": False,
            },
        },
        "readOnly": True,
        "liveExecution": False,
    }
    event["xml"] = cot_event_to_xml(event)
    return event


def network_event_to_cot_event(event):
    if not isinstance(event, dict):
        raise ValueError("network event must be an object")
    return fleet_message_to_cot_event(event.get("payload") or {}, topic=event.get("topic"))


def network_events_to_cot_events(events):
    cot_events = []
    for event in events or []:
        try:
            cot_events.append(network_event_to_cot_event(event))
        except ValueError:
            continue
    return cot_events


def cot_event_to_xml(event):
    point = event["point"]
    detail = event["detail"]["droneops"]
    return (
        '<event version="2.0" uid="{uid}" type="{cot_type}" how="{how}" time="{time}" start="{start}" stale="{stale}">'
        '<point lat="{lat}" lon="{lon}" hae="{hae}" ce="{ce}" le="{le}"/>'
        '<detail><contact callsign="{callsign}"/>'
        '<droneops messageType="{message_type}" missionId="{mission_id}" nodeId="{node_id}" state="{state}" readOnly="true" liveExecution="false"/>'
        '</detail></event>'
    ).format(
        uid=_xml(event["uid"]),
        cot_type=_xml(event["cotType"]),
        how=_xml(event["how"]),
        time=_xml(event["time"]),
        start=_xml(event["start"]),
        stale=_xml(event["stale"]),
        lat=point["lat"],
        lon=point["lon"],
        hae=point["hae"],
        ce=point["ce"],
        le=point["le"],
        callsign=_xml(event["detail"]["contact"]["callsign"]),
        message_type=_xml(detail["messageType"]),
        mission_id=_xml(detail["missionId"]),
        node_id=_xml(detail["nodeId"]),
        state=_xml(detail["state"]),
    )


def _point_for_message(message):
    position = message.get("position") or message.get("home")
    if not position and message.get("routeWaypoints"):
        position = message["routeWaypoints"][0]
    if not position:
        position = {"lat": 0.0, "lon": 0.0, "alt": 0.0}
    return {
        "lat": float(position["lat"]),
        "lon": float(position["lon"]),
        "hae": float(position.get("alt", position.get("hae", 0.0))),
        "ce": 10.0,
        "le": 10.0,
    }


def _uid_for_message(message, message_type):
    node_id = message.get("nodeId")
    if message_type == "order.intent":
        return "droneops.order.{}".format(message.get("orderId"))
    if message_type == "mission.proposal":
        return "droneops.mission.{}.proposal".format(message.get("missionId"))
    if message_type == "mission.assignment":
        return "droneops.mission.{}.assignment.{}".format(message.get("missionId"), node_id)
    if message_type == "observation.report":
        return "droneops.observation.{}".format(message.get("reportId"))
    return "droneops.{}.{}".format(message_type.replace(".", "-"), node_id or message.get("uid") or "event")


def _callsign_for_message(message, message_type):
    return str(message.get("callsign") or message.get("nodeId") or message.get("uid") or message.get("issuer") or message_type)


def _cot_type_for_message(message_type):
    if message_type in ("node.status", "mission.telemetry", "connector.atak_drone.registration", "connector.atak_drone.heartbeat"):
        return "a-f-A-UAS"
    if message_type == "observation.report":
        return "b-m-p-s-p-i"
    return "b-t-f"


def _xml(value):
    return html.escape(str(value), quote=True)


def self_test():
    status = messages.node_status("drone-01", {"lat": 44.4057, "lon": 26.3019, "alt": 80})
    event = fleet_message_to_cot_event(status)
    assert event["cotType"] == "a-f-A-UAS"
    assert event["point"]["lat"] == 44.4057
    assert "liveExecution=\"false\"" in event["xml"]
    assignment = messages.mission_assignment("mission-test", "drone-01", [status["position"]])
    assignment_event = fleet_message_to_cot_event(assignment)
    assert assignment_event["uid"] == "droneops.mission.mission-test.assignment.drone-01"
    return {"status": event, "assignment": assignment_event}


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
