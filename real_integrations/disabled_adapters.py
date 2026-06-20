#!/usr/bin/env python3
"""Fail-closed placeholders for future real integrations."""

from integration_contracts.runtime import reject_real_execution


class DisabledRealTakTransport:
    def publish(self, topic, payload):
        reject_real_execution("Real TAK transport adapter")


class DisabledRealAtakTrackFeed:
    def snapshot(self):
        reject_real_execution("Real ATAK track feed")


class DisabledRealAtakPluginBridge:
    def publish_cot(self, cot_event):
        reject_real_execution("Real ATAK plugin bridge")

    def poll_orders(self):
        reject_real_execution("Real ATAK plugin bridge")


class DisabledRealAtakDroneConnectorRegistry:
    def register(self, registration):
        reject_real_execution("Real ATAK drone connector registry")

    def heartbeat(self, heartbeat):
        reject_real_execution("Real ATAK drone connector registry")


class DisabledRealDroneMiddlewareConnector:
    def snapshot(self):
        reject_real_execution("Real drone middleware connector")


class DisabledRealControllerCompiler:
    def __call__(self, node_id, mission, assignment):
        reject_real_execution("Real controller compiler")


class DisabledRealExternalAssetFeed:
    def snapshot(self):
        reject_real_execution("Real external asset feed")


class DisabledRealObservationFeed:
    def snapshot(self):
        reject_real_execution("Real observation feed")
