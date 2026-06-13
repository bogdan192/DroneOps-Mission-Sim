#!/usr/bin/env python3
"""Simulation-only ATAK/CoT-style telemetry feed examples."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from integration_contracts.atak_telemetry import (  # noqa: E402
    atak_track_to_external_asset,
    normalize_atak_track,
)


def build_simulated_atak_tracks():
    raw_tracks = [
        {
            "uid": "atak.drone.scout-01",
            "callsign": "ATAK Scout Drone 1",
            "cotType": "a-f-A-UAS",
            "source": "mock-atak-feed",
            "status": "observed",
            "point": {"lat": 44.4084, "lon": 26.3106, "hae": 135},
            "speedMps": 12.5,
            "courseDeg": 96,
        },
        {
            "uid": "atak.team.alpha",
            "callsign": "Team Alpha",
            "domain": "ground",
            "kind": "personnel",
            "source": "mock-atak-feed",
            "status": "observed",
            "position": {"lat": 44.4052, "lon": 26.3050, "alt": 75},
        },
        {
            "uid": "atak.air.observer-02",
            "callsign": "Air Observer 2",
            "cotType": "a-f-A",
            "source": "mock-atak-feed",
            "status": "observed",
            "point": {"lat": 44.4102, "lon": 26.3082, "hae": 260},
            "speedMps": 28.0,
            "courseDeg": 175,
        },
    ]
    return [normalize_atak_track(item) for item in raw_tracks]


def build_simulated_atak_external_assets():
    return [atak_track_to_external_asset(track) for track in build_simulated_atak_tracks()]


def self_test():
    tracks = build_simulated_atak_tracks()
    assets = build_simulated_atak_external_assets()
    assert len(tracks) == 3
    assert any(track["kind"] == "drone" for track in tracks)
    assert any(asset["kind"] == "personnel" for asset in assets)
    assert all(asset["readOnly"] for asset in assets)
    return {"tracks": tracks, "assets": assets}


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
