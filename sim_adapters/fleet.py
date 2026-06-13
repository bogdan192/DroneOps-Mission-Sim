#!/usr/bin/env python3
"""Simulated fleet inventory for demos and tests."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fleet_protocol import messages  # noqa: E402


DEFAULT_START_POSITION = {
    "lat": 44.4057,
    "lon": 26.3019,
    "alt": 80,
}


def build_simulated_fleet(node_count):
    if node_count < 1 or node_count > 12:
        raise ValueError("node_count must be between 1 and 12")
    fleet = []
    for index in range(node_count):
        fleet.append(messages.node_status(
            "drone-{:02d}".format(index + 1),
            DEFAULT_START_POSITION,
            battery_percent=96.0 - index * 2.0,
            role="leader-capable" if index == 0 else "worker",
            capabilities=["route", "survey", "relay", "mission_compile"],
        ))
    return fleet


def self_test():
    fleet = build_simulated_fleet(4)
    assert len(fleet) == 4
    start_positions = [item["position"] for item in fleet]
    assert all(position == start_positions[0] for position in start_positions)
    return fleet


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
