#!/usr/bin/env python3
"""Simulation-only external ground and air asset feed."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from integration_contracts.external_assets import asset_to_cot_like, normalize_external_asset  # noqa: E402
from sim_adapters.atak_feeds import build_simulated_atak_external_assets  # noqa: E402


def build_simulated_external_assets():
    raw_assets = [
        {
            "uid": "asset.ground.observer-01",
            "callsign": "Ground Observer 1",
            "domain": "ground",
            "kind": "team",
            "source": "mock-external-assets",
            "status": "observed",
            "position": {"lat": 44.4049, "lon": 26.3049, "alt": 74},
        },
        {
            "uid": "asset.ground.relay-01",
            "callsign": "Relay Truck 1",
            "domain": "ground",
            "kind": "relay",
            "source": "mock-external-assets",
            "status": "observed",
            "position": {"lat": 44.4071, "lon": 26.3008, "alt": 76},
        },
        {
            "uid": "asset.air.observer-01",
            "callsign": "Air Observer 1",
            "domain": "air",
            "kind": "aircraft",
            "source": "mock-external-assets",
            "status": "observed",
            "position": {"lat": 44.4090, "lon": 26.3096, "alt": 220},
        },
    ]
    assets = []
    for item in raw_assets:
        asset = normalize_external_asset(item)
        asset["cotLike"] = asset_to_cot_like(asset)
        assets.append(asset)
    return assets + build_simulated_atak_external_assets()


def self_test():
    assets = build_simulated_external_assets()
    assert len(assets) == 6
    assert {asset["domain"] for asset in assets} == {"ground", "air"}
    assert any(asset["kind"] == "drone" for asset in assets)
    assert any(asset["kind"] == "personnel" for asset in assets)
    assert all(asset["readOnly"] for asset in assets)
    return assets


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
