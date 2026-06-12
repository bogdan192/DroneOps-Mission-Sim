# Roadmap

## Near Term

- Add persisted mission files.
- Add route import/export as GeoJSON.
- Add distance and estimated-time calculations.
- Add better visual separation between multiple simulated drones.
- Add authoritative UAS geographical-zone ingestion.

## Simulation Expansion

- Add ArduPilot SITL adapter.
- Add PX4 SITL adapter.
- Add replayable mission test fixtures.
- Add deterministic simulation clock controls.

## ATAK Expansion

- Replace in-process simulation adapter with a configurable DroneOps API target.
- Add Android emulator setup notes.
- Add authenticated bridge from ATAK plugin to basestation.

## Real-Flight Preconditions

Real-flight support is intentionally out of scope until safety gates exist:

- legal geo-zone checks
- authenticated mission upload
- human approval
- telemetry validation
- lost-link policy
- emergency stop
- audit logging

