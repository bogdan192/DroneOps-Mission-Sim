# Claude Project Instructions

## Short Summary

DroneOps Mission Sim is a simulation-only prototype for an onboard drone
autonomy-node architecture. It explores mission planning, peer coordination,
adapter boundaries, and ATAK-style visualization without controlling real
hardware.

This repository must remain unable to arm, launch, fly, land, or command a real
aircraft.

## What The Project Should Do

The intended architecture is:

1. Receive a high-level order or user-drawn route.
2. Use a deterministic planner or optional local LLM to turn that order into
   structured mission intent.
3. Validate mission intent with deterministic safety checks.
4. Coordinate work across a fleet using transport-neutral messages.
5. Compile controller-facing output through an explicit adapter boundary.
6. Simulate execution locally.
7. Display simulated telemetry in a basestation-style live view.

The future direction is adapter-based integration, not direct controller access
from the LLM or UI.

## What The Project Does Now

Implemented today:

- Mission DSL validation in `mission_core/mission_schema.py`.
- Fleet messages and assignment planning in `fleet_protocol/`.
- Onboard node orchestration in `onboard_node/node.py`.
- Controller compiler injection on `OnboardNode`.
- Local simulated controller compiler in
  `controller_adapters/simulated_controller.py`.
- Simulation-only adapters in `sim_adapters/`.
- End-to-end CLI mock mission runtime in `mock_runtime/mission_simulator.py`.
- Interactive browser mission organizer and live tracker split across
  `control_station/`.
- Legacy compatibility entrypoint in `live_web/server.py`.
- ATAK/CoT-like telemetry normalization in `atak_tracking/tracker.py`.
- Optional Ollama planner support in `tools/droneops_local_planner/`.
- Fail-closed real-integration placeholders in `real_integrations/`.

Not implemented:

- Real TAK network transport.
- Real Android device control.
- Real MAVLink, PX4, or ArduPilot mission upload.
- Real drone flight, arming, takeoff, landing, or actuator control.
- Production authentication, authorization, audit, geofence, failsafe, or
  compliance stack.

## Safety Rules

Follow these rules for every change:

- Keep all runtime behavior simulation-only.
- Keep `mode: "simulation"` and `liveExecution: false`.
- Do not add real flight-control, MAVLink, PX4, ArduPilot, actuator, radio, or
  phone-control behavior.
- Do not let LLM output become raw controller commands.
- Do not bypass `mission_schema.reject_raw_command_fields`.
- Do not make `real_integrations/` do anything except fail closed unless the
  task is explicitly to write a design document.
- Treat `sim_adapters/`, `mock_runtime/`, and `live_web/` as non-production
  simulator code.

## Real vs Mock Boundary

Reusable architecture/contracts:

- `mission_core/`
- `fleet_protocol/`
- `integration_contracts/`
- `onboard_node/`
- `atak_tracking/`

Simulation-only:

- `sim_adapters/`
- `mock_runtime/`
- `control_station/`
- `live_web/`
- `tools/droneops_sim/`
- `controller_adapters/simulated_controller.py`

Fail-closed real placeholders:

- `real_integrations/`

Production-capable code must not import simulator-only modules. Read
`docs/REAL_VS_MOCK.md` before changing this boundary.

## Repository Map

```text
README.md                         Human overview and quick start
NO_ADMIN_QUICK_START.md           Double-click launch instructions
AGENTS.md                         Codex-facing instructions
CLAUDE.md                         Claude-facing instructions
docs/REAL_VS_MOCK.md              Boundary between reusable and simulated code
docs/ARCHITECTURE.md              System architecture
docs/SAFETY.md                    Safety contract
docs/MISSION_DSL.md               Mission DSL shape
docs/FLEET_PROTOCOL.md            Fleet message protocol
docs/ONBOARD_NODE.md              Onboard node API
docs/MOCK_SIMULATION.md           Mock runtime details
docs/LIVE_WEB_TRACKING.md         Browser tracker details
mission_core/mission_schema.py    Validates mission DSL and rejects raw fields
fleet_protocol/messages.py        Builds transport-neutral messages
fleet_protocol/coordinator.py     Plans deterministic assignments
integration_contracts/runtime.py  Adapter protocols and safety gate helpers
onboard_node/node.py              Order handling and mission orchestration
controller_adapters/              Controller compiler implementations
sim_adapters/                     Simulation-only adapter implementations
mock_runtime/                     End-to-end simulator harness
control_station/                  Control station mission state, API, UI, app
live_web/                         Compatibility entrypoint
atak_tracking/                    ATAK-style tracking normalization
real_integrations/                Disabled placeholders for future adapters
scripts/                          Local checks and launch helpers
scripts/demo_launcher.py          Shared no-admin local demo launcher
tools/                            Demo servers and planner tooling
```

## Testing

Run the full local check script after code changes:

```bash
python3 -B scripts/test.py
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

Focused checks:

```powershell
python -B onboard_node\node.py --self-test
python -B mock_runtime\mission_simulator.py --self-test
python -B live_web\server.py --self-test
```

## Preferred Change Style

- Preserve the real-vs-mock separation.
- Use dependency injection for new adapters.
- Keep schemas and message shapes plain JSON-compatible dictionaries.
- Keep deterministic code responsible for validation and assignment.
- Add docs when introducing a new module or boundary.
- Keep browser demo changes inside `live_web/` unless changing shared tracking
  or schema behavior.
- Keep safety checks close to the mission DSL and integration contracts.
- Keep launch and test paths portable across Windows, macOS, and Linux.
