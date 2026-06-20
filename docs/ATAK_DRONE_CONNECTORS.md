# ATAK Drone Connector Scaffold

This scaffold models how ATAK-equipped drones can announce themselves to the
control station and report read-only connector state.

It is intentionally not a command/control adapter. It does not arm, launch,
land, return-to-home, upload missions, send MAVLink commands, or write to TAK.

## Current Implementation

- `integration_contracts/drone_connectors.py` defines:
  - ATAK drone registration records
  - ATAK drone heartbeat records
  - read-only drone middleware connector records
- `integration_contracts/atak_bridge.py` defines Android/ATAK bridge envelopes
  for local loopback and future plugin IPC.
- `integration_contracts/atak_cot.py` maps fleet protocol messages to
  simulation-safe CoT-like events.
- `sim_adapters/drone_connectors.py` provides simulated registrations,
  heartbeat updates, and read-only middleware adapters.
- `control_station/mission_session.py` includes connector snapshots.
- `control_station/http_server.py` exposes connector APIs.
- `real_integrations/disabled_adapters.py` includes fail-closed placeholders
  for real connector registries and real drone middleware connectors.

## API

```text
GET  /api/connectors
GET  /api/connectors/atak-drones
GET  /api/connectors/drone-middleware
GET  /api/atak/cot
POST /api/connectors/atak-drones/register
POST /api/connectors/atak-drones/heartbeat
```

## Registration Shape

```json
{
  "nodeId": "atak-drone-01",
  "callsign": "ATAK Drone 01",
  "platform": "android-atak-companion",
  "links": [
    { "linkType": "atak-cot", "endpointRef": "cot://readonly/drone-01" },
    { "linkType": "mavlink-readonly", "endpointRef": "udp://readonly/drone-01" }
  ],
  "capabilities": ["telemetry", "health", "observation_report"],
  "position": { "lat": 44.4057, "lon": 26.3019, "alt": 80 }
}
```

The normalized record always includes:

```json
{
  "type": "connector.atak_drone.registration",
  "schemaVersion": "0.1",
  "readOnly": true,
  "liveExecution": false
}
```

## Heartbeat Shape

```json
{
  "nodeId": "atak-drone-01",
  "state": "online",
  "batteryPercent": 91,
  "position": { "lat": 44.4060, "lon": 26.3020, "alt": 82 }
}
```

## Drone Middleware Connectors

The scaffold includes read-only placeholders for:

- `mavlink-readonly`
- `vendor-sdk-readonly`

These connectors describe telemetry inputs only. They must not expose arming,
takeoff, landing, mission upload, route commands, actuator control, RC override,
or other control surfaces.

## Safety Boundary

Connector payloads reject operational fields such as `command`, `arm`,
`takeoff`, `land`, `rtl`, `mavlink`, `missionUpload`, `actuator`, `servo`,
`rcOverride`, `target`, `tasking`, `weapon`, and `intercept`.

Future real adapters should live outside simulator modules and must include:

- authentication
- source allowlisting
- replay protection
- audit logging
- operator-visible source identity
- transport security
- explicit separation from command authority
