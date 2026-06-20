#!/usr/bin/env python3
"""In-memory simulated TAK/mesh transport."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fleet_protocol import messages  # noqa: E402
from integration_contracts.atak_cot import fleet_message_to_cot_event  # noqa: E402
from integration_contracts.runtime import require_simulation_payload  # noqa: E402


class InMemoryTakNetwork:
    """Tiny in-memory stand-in for TAK/CoT or drone mesh transport."""

    def __init__(self):
        self.events = []
        self.cot_events = []

    def publish(self, topic, payload):
        require_simulation_payload(payload, "payload")
        event = {
            "topic": topic,
            "timestamp": messages.timestamp(),
            "payload": payload,
        }
        self.events.append(event)
        try:
            self.cot_events.append(fleet_message_to_cot_event(payload, topic))
        except ValueError:
            pass
        return event

    def by_topic(self, topic):
        return [event for event in self.events if event["topic"] == topic]

    def cot_snapshot(self):
        return list(self.cot_events)
