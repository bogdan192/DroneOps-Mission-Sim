#!/usr/bin/env python3
"""ATAK-style drone tracker.

The tracker stores normalized drone telemetry in a shape that can later be fed
by ATAK/CoT messages. Today it consumes mock mission telemetry.
"""

import time


class AtakDroneTracker:
    def __init__(self, source="mock-atak"):
        self.source = source
        self.drones = {}

    def update_from_telemetry(self, telemetry_items):
        now = time.time()
        for item in telemetry_items:
            node_id = str(item["nodeId"])
            position = item["position"]
            self.drones[node_id] = {
                "uid": "droneops.{}".format(node_id),
                "nodeId": node_id,
                "source": self.source,
                "state": item.get("state", "unknown"),
                "missionId": item.get("missionId"),
                "lat": float(position["lat"]),
                "lon": float(position["lon"]),
                "alt": float(position.get("alt", 0.0)),
                "batteryPercent": float(item.get("batteryPercent", 0.0)),
                "liveExecution": item.get("liveExecution") is True,
                "lastSeenEpoch": now,
                "lastSeenIso": item.get("timestamp"),
                "cotLike": telemetry_to_cot_like(item),
            }

    def snapshot(self):
        return {
            "source": self.source,
            "mode": "SIMULATION_ONLY",
            "drones": sorted(self.drones.values(), key=lambda item: item["nodeId"]),
        }


def telemetry_to_cot_like(item):
    position = item["position"]
    return {
        "event": {
            "version": "2.0",
            "uid": "droneops.{}".format(item["nodeId"]),
            "type": "a-f-A-M-F-Q",
            "how": "m-g",
            "time": item.get("timestamp"),
            "start": item.get("timestamp"),
            "stale": item.get("timestamp"),
        },
        "point": {
            "lat": float(position["lat"]),
            "lon": float(position["lon"]),
            "hae": float(position.get("alt", 0.0)),
            "ce": 10.0,
            "le": 10.0,
        },
        "detail": {
            "contact": {"callsign": item["nodeId"]},
            "status": {
                "state": item.get("state", "unknown"),
                "batteryPercent": item.get("batteryPercent"),
                "missionId": item.get("missionId"),
            },
        },
    }


def self_test():
    tracker = AtakDroneTracker()
    tracker.update_from_telemetry([
        {
            "nodeId": "drone-01",
            "missionId": "mission-test",
            "state": "simulating",
            "position": {"lat": 44.4057, "lon": 26.3019, "alt": 80},
            "batteryPercent": 96,
            "timestamp": "2026-06-12T00:00:00Z",
            "liveExecution": False,
        }
    ])
    snapshot = tracker.snapshot()
    assert snapshot["drones"][0]["uid"] == "droneops.drone-01"
    assert snapshot["drones"][0]["liveExecution"] is False
    return snapshot


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))

