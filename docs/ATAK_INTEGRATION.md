# ATAK Integration Notes

The corrected direction is drone-side ATAK/TAK as a network node, not merely a
basestation UI.

## Intended Role

An Android/ATAK device or companion computer on each drone would:

- publish node status
- receive TAK/CoT or local network orders
- exchange fleet protocol messages
- host or reach a local LLM/planner
- compile validated simulation or flight-controller programs
- report assignment and telemetry status

## Current Prototype

The current onboard node is pure Python and local HTTP. It models the API and
data boundaries before moving them into Android/ATAK plugin code.

## Future Adapter

Replace local HTTP transport with:

- ATAK plugin IPC for local device communication
- CoT event mapping for fleet messages
- authenticated peer transport
- a controller bridge only after simulation and safety gates

## Do Not Shortcut

Do not connect the onboard node directly to MAVLink mission upload. Add a
separate live-flight subsystem with authentication, geofence checks, operator
approval, and audit logs.

