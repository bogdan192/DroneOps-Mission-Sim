# ATAK Integration Notes

The current basestation uses an in-process simulation state. It was designed to
mirror the shape of the ATAK DroneOps plugin prototype so the adapter can later
be swapped.

## Current Local API Shape

The simulated DroneOps API exposes:

- `GET /health`
- `GET /fleet`
- `POST /mission-intents`

The basestation currently calls equivalent in-process Python methods for speed
and reliability. To integrate with ATAK, replace that adapter with HTTP calls to
the Android plugin endpoint or another authenticated local bridge.

## Recommended Next Step

Keep this order:

1. Basestation to local simulator.
2. Basestation to Android emulator running ATAK and DroneOps.
3. Android emulator to SITL autopilot.
4. Hardware-in-loop with motors disabled or props removed.
5. Supervised real aircraft tests only after the safety gates are implemented.

## Do Not Shortcut

Do not connect `/api/simulate` directly to real MAVLink mission upload. Add an
explicit live-flight subsystem with authentication, geofence checks, operator
approval, and audit logs.

