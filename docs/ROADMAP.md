# Roadmap

## Near Term

- [x] Persist mission DSL files.
- [x] Add route import/export as GeoJSON.
- Connect basestation orders to onboard node API.
- Add peer-node simulator with multiple onboard node processes.
- Add transport authentication to fleet messages.

## Onboard Autonomy

- Add order inbox and durable mission state.
- Add leader election or deterministic assignment authority.
- Add conflict resolution for competing assignments.
- [x] Add telemetry freshness checks.
- [x] Add prompt-injection filtering for incoming orders.

## Simulation Expansion

- Add ArduPilot SITL adapter.
- Add PX4 SITL adapter.
- Add replayable mission test fixtures.
- Add deterministic simulation clock controls.

## ATAK Expansion

- [x] Map fleet protocol messages to CoT events.
- [x] Add Android/ATAK plugin bridge.
- [x] Test Android emulator plus onboard node loopback.

## Real-Flight Preconditions

Real-flight support is intentionally out of scope until safety gates exist:

- legal geo-zone checks
- authenticated mission upload
- human approval
- telemetry validation
- lost-link policy
- emergency stop
- audit logging
