# Codex Project Instructions

## Project Identity

Name: DroneOps Mission Sim

Purpose: simulation-only prototype for an onboard drone autonomy-node
architecture. The project models how an onboard node could receive high-level
orders, use a local planner or LLM to create structured mission intent,
coordinate with peers, compile a controller program through an adapter boundary,
and expose simulated ATAK-style tracking.

This repository does not arm, launch, fly, land, or command a real aircraft.

## Current State

The project currently provides:

- A mission DSL validator that forces `mode: "simulation"` and
  `liveExecution: false`.
- Fleet protocol messages for node status, order intent, mission assignment,
  and telemetry.
- Deterministic multi-drone route assignment.
- An onboard-node API with `/health` and `/orders`.
- A local planner with deterministic mock mode and optional Ollama mode.
- Simulator adapters for fake fleet inventory, in-memory transport, and
  synthetic telemetry.
- A browser-based control station split into mission session, HTTP API, UI, and
  CLI startup modules.
- Fail-closed placeholders for future real integrations.

## Non-Negotiable Safety Rules

- Do not add code that can command a real drone, phone, flight controller,
  actuator, MAVLink endpoint, PX4 instance, ArduPilot instance, radio, or TAK
  network.
- Do not change default behavior away from simulation mode.
- Preserve `liveExecution: false` unless the user explicitly requests a
  separate, reviewed design document. Do not implement real execution.
- The LLM/planner may produce structured intent only. It must not produce raw
  controller commands.
- Raw command fields such as `mavlink`, `arm`, `takeoff`, `actuator`,
  `servo`, `velocityCommand`, and `rcOverride` must remain rejected.
- Real-capable code must not import from `mock_runtime`, `sim_adapters`,
  `live_web`, or `tools/droneops_sim`.

## Real vs Mock Boundary

Reusable contract/planning modules:

- `mission_core/`
- `fleet_protocol/`
- `integration_contracts/`
- `onboard_node/`, only with an explicitly supplied controller compiler for
  non-default use
- `atak_tracking/`, as telemetry presentation/normalization support

Simulation-only modules:

- `sim_adapters/`
- `mock_runtime/`
- `control_station/`
- `live_web/`
- `tools/droneops_sim/`
- `controller_adapters/simulated_controller.py`

Disabled real placeholders:

- `real_integrations/`

Read `docs/REAL_VS_MOCK.md` before moving code across these boundaries.

## File Organization

```text
README.md                         Project overview and quick start
NO_ADMIN_QUICK_START.md           Double-click launch instructions
AGENTS.md                         Codex instructions
CLAUDE.md                         Claude instructions
mission_core/mission_schema.py    Mission DSL validation and safety checks
fleet_protocol/messages.py        JSON-compatible fleet message builders
fleet_protocol/coordinator.py     Deterministic assignment planner
integration_contracts/runtime.py  Adapter contracts and fail-closed checks
integration_contracts/external_assets.py Read-only external asset contracts
onboard_node/node.py              Onboard node API and orchestration
controller_adapters/              Controller compilers
sim_adapters/                     Simulation-only fleet, transport, runtime
sim_adapters/external_assets.py   Mock read-only external asset feed
mock_runtime/mission_simulator.py End-to-end CLI simulation harness
control_station/                  Control station session, API, UI, app
live_web/server.py                Compatibility entrypoint to control_station
atak_tracking/tracker.py          ATAK/CoT-like telemetry normalization
real_integrations/                Disabled fail-closed placeholders
tools/droneops_local_planner/     Deterministic and Ollama-backed planner
tools/droneops_basestation/       Older basestation demo server
tools/droneops_sim/               Local simulation tooling
scripts/test.ps1                  Full local check script
scripts/test.py                   Cross-platform full local check script
scripts/demo_launcher.py          Shared no-admin local demo launcher
scripts/run_browser_ui_tests.py   Auto-installs local Playwright UI test deps
docs/                             Architecture, safety, setup, and API docs
```

## Main Data Flow

```text
Order text or route waypoints
  -> onboard_node.OnboardNode
  -> local planner or provided route
  -> mission_core mission DSL validation
  -> fleet_protocol coordinator assignment
  -> injected controller compiler
  -> simulator runtime today
  -> ATAK-style tracker and browser visualization
```

## Important Commands

Run all checks:

```bash
python3 -B scripts/test.py
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

Run browser UI checks with local no-admin dependency install:

```bash
python3 -B scripts/run_browser_ui_tests.py
```

Run onboard node self-test:

```powershell
python -B onboard_node\node.py --self-test
```

Run mocked mission:

```powershell
python -B mock_runtime\mission_simulator.py
```

Run live web simulator:

```powershell
python -B live_web\server.py
```

Preferred control-station entrypoint:

```powershell
python -B -m control_station.app
```

Optional Google Maps key for live web or basestation:

```powershell
$env:GOOGLE_MAPS_API_KEY="your-key"
```

## Development Guidance

- Keep edits small and boundary-preserving.
- Prefer adding explicit adapters over mixing real and mock code.
- Keep simulator defaults obvious in names, docs, API responses, and tests.
- Add or update docs when changing project structure.
- Add tests for safety gates, adapter boundaries, and message schemas.
- Use `python3 -B scripts/test.py` or `scripts/test.ps1` after changes.
- Use `python3 -B scripts/run_browser_ui_tests.py` for browser-level UI
  coverage. It creates `.venv-ui-tests`, installs `requirements-dev.txt`, and
  downloads Playwright Chromium locally.
- This repo is Python with Windows PowerShell and macOS/Linux Bash launchers.
  Runtime code should avoid dependencies; dev/test dependencies belong in
  `requirements-dev.txt`.

## Useful Docs

- `docs/REAL_VS_MOCK.md`
- `docs/ARCHITECTURE.md`
- `docs/SAFETY.md`
- `docs/MISSION_DSL.md`
- `docs/FLEET_PROTOCOL.md`
- `docs/ONBOARD_NODE.md`
- `docs/MOCK_SIMULATION.md`
- `docs/LIVE_WEB_TRACKING.md`
