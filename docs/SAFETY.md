# Safety Contract

This repository is a simulation and planning prototype. It must not be wired to
real aircraft without a separate safety design, legal review, and supervised
test program.

## Current Hard Boundaries

- Mission intents must use `mode: "simulation"`.
- `liveExecution` is forced to `false`.
- The planner rejects prohibited terms such as attack, strike, weapon,
  intercept, and ram.
- Route waypoints must contain valid latitude/longitude pairs.
- Waypoint altitude must be between `0` and `120` meters.
- Speed must be positive and at most `20 m/s`.
- The system does not generate raw MAVLink commands.
- The system does not arm, take off, land, or control actuators.

## Before Any Real Flight Work

Add these gates before connecting to real hardware:

- SITL tests with ArduPilot or PX4.
- Hardware-in-loop tests with props removed.
- Explicit operator approval before any mission upload.
- Geofence enforcement from authoritative UAS geographical-zone data.
- Return-to-launch and lost-link handling.
- Command authentication and audit logging.
- Per-aircraft health checks.
- Manual override and emergency stop.
- Compliance review for the operating country and airspace.

## Bucharest Demo Note

The default route is placed on Bucharest's eastern outskirts for visualization.
The airport reference circles shown in the UI are approximate warnings, not
official restriction data. Official Romanian UAS geographical-zone data must be
checked before real flight.

