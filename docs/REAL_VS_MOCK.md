# Real vs Mock Boundary

The prototype originally kept the mock network, mock runtime, controller
compiler, and live web demo close together so the whole mission loop could be
seen quickly. That was useful for demonstration, but it made the boundary too
easy to miss. The code is now split so simulator-only behavior lives behind
explicit simulator adapters.

## Reusable Today

These parts are safe to reuse as architecture, validation, or integration
contracts:

- `mission_core/mission_schema.py` validates the current route-mission DSL.
  Today it deliberately forces `mode: "simulation"` and
  `liveExecution: false`, so it is reusable as a planning contract, not as a
  real flight-command schema.
- `fleet_protocol/messages.py` defines plain JSON-compatible node, order,
  assignment, and telemetry message shapes.
- `fleet_protocol/coordinator.py` performs deterministic assignment planning.
  It does not call a drone controller.
- `integration_contracts/runtime.py` defines adapter contracts and fail-closed
  safety checks.
- `integration_contracts/external_assets.py` defines read-only external asset
  tracking contracts and rejects operational command/tasking fields.
- `onboard_node/node.py` handles orders, planner output, mission validation,
  assignment planning, and controller compiler injection.
- `atak_tracking/tracker.py` normalizes telemetry into ATAK-style tracking
  output for a client.

## Mock or Simulation Only

These parts are not real drone integrations:

- `sim_adapters/fleet.py` creates fake drone inventory.
- `sim_adapters/transport.py` stores network events in memory instead of
  sending TAK/CoT, MQTT, radio, or mesh traffic.
- `sim_adapters/runtime.py` generates synthetic telemetry along a route.
- `sim_adapters/external_assets.py` creates fake read-only ground and air asset
  tracks.
- `controller_adapters/simulated_controller.py` compiles local simulator
  programs only.
- `mock_runtime/mission_simulator.py` wires the simulator pieces together for
  command-line demos.
- `control_station/` is a browser control-station demo backed by simulator
  adapters.
- `live_web/server.py` is a compatibility entrypoint into `control_station/`.

## Intentionally Disabled

`real_integrations/disabled_adapters.py` contains fail-closed placeholders for
future real TAK, controller, and external asset adapters. They raise an error
if called.

A real integration should be a new adapter package, not a change to the mock
runtime. It would need to implement the same contracts while adding real-world
requirements that are intentionally absent here: authentication, authorization,
transport security, geofence enforcement, failsafe handling, telemetry
verification, hardware-in-the-loop/SITL testing, and explicit human approval
before any live execution.

## Boundary Rule

Production-capable code must not import from:

- `mock_runtime`
- `sim_adapters`
- `control_station`
- `live_web`
- `tools/droneops_sim`

Production-capable code may import from:

- `mission_core`
- `fleet_protocol`
- `integration_contracts`
- `onboard_node`, only with an explicitly supplied controller compiler
- `atak_tracking`, as a telemetry presentation/normalization helper
