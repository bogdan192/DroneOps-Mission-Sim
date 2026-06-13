# Safety Contract

This repository is a simulation and planning prototype. It must not be wired to
real aircraft without a separate safety design, legal review, and supervised
test program.

## Current Hard Boundaries

- Mission DSL must use `mode: "simulation"`.
- `liveExecution` is forced to `false`.
- The LLM/planner may propose intent, not controller commands.
- Raw controller command fields are rejected.
- Route waypoints must contain valid latitude/longitude pairs.
- Waypoint altitude must be between `0` and `120` meters.
- Speed must be positive and at most `20 m/s`.
- The system does not generate raw MAVLink commands.
- The system does not arm, take off, land, or control actuators.
- Simulator modules live under `sim_adapters`, `mock_runtime`, and `live_web`.
  Real-capable adapters must not import from those modules.
- Real adapter placeholders under `real_integrations` fail closed.

## Required Gates Before Real Flight

- SITL tests with ArduPilot or PX4.
- Hardware-in-loop tests with props removed.
- Explicit operator approval before any mission upload.
- Geofence enforcement from authoritative UAS geographical-zone data.
- Return-to-launch and lost-link handling.
- Command authentication and audit logging.
- Per-aircraft health checks.
- Manual override and emergency stop.
- Compliance review for the operating country and airspace.

## Autonomous Fleet Threats

The architecture must account for:

- prompt injection through received orders
- compromised peer nodes
- stale or spoofed telemetry
- conflicting task assignments
- model hallucination
- loss of network consensus
- GNSS degradation
- battery reserve errors
- airspace restriction changes

The current prototype is intentionally local and simulation-only while those
controls are designed.
