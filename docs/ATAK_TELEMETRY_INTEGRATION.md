# ATAK Telemetry Integration Scaffold

This project includes read-only scaffolding for inbound ATAK/CoT-style tracks
from ATAK-equipped drones, personnel/team devices, and other air assets.

The goal is shared situational awareness:

- receive or replay ATAK/CoT-like track messages
- normalize them into a stable internal shape
- classify tracks as drone, personnel, aircraft, vehicle, or unknown
- convert tracks into the existing read-only external asset format
- expose simulated examples through the control station

This layer does not support:

- TAK server writes
- drone command/control
- route upload
- target designation
- weapon tasking
- fire missions
- intercept guidance
- raw controller commands

## Current Implementation

- `integration_contracts/atak_telemetry.py` defines the read-only track ingest
  contract and rejects operational fields.
- `sim_adapters/atak_feeds.py` provides simulated ATAK-equipped drone,
  personnel/team, and air-asset tracks.
- `sim_adapters/external_assets.py` includes those simulated tracks as
  normalized external assets for the control-station map.
- `control_station/mission_session.py` includes `atakTracks` in snapshots.
- `control_station/http_server.py` exposes `GET /api/atak/tracks`.
- `real_integrations/disabled_adapters.py` includes fail-closed placeholders
  for real TAK transport and real ATAK track feeds.

## Track Shape

```json
{
  "type": "atak.track",
  "schemaVersion": "0.1",
  "uid": "atak.drone.scout-01",
  "callsign": "ATAK Scout Drone 1",
  "cotType": "a-f-A-UAS",
  "domain": "air",
  "kind": "drone",
  "source": "mock-atak-feed",
  "status": "observed",
  "position": { "lat": 44.4084, "lon": 26.3106, "alt": 135 },
  "speedMps": 12.5,
  "courseDeg": 96,
  "readOnly": true,
  "liveExecution": false
}
```

The scaffold accepts either:

- `point.lat`, `point.lon`, `point.hae`
- `position.lat`, `position.lon`, `position.alt`
- top-level `lat`, `lon`, `alt`

## API

```text
GET /api/atak/tracks
```

The response is simulation-only:

```json
{
  "mode": "SIMULATION_ONLY",
  "source": "mock-atak-feed",
  "readOnly": true,
  "tracks": []
}
```

## Real Adapter Boundary

A future real adapter should live outside simulator modules and convert
authorized ATAK/CoT inputs into `atak.track` records. It should then pass those
records through `atak_track_to_external_asset` for display.

Before any real deployment, add:

- authenticated transport
- source allowlisting
- operator-visible source labels
- replay/spoofing checks
- audit logging
- retention rules
- explicit separation from any command authority

Keep the feed read-only unless a separate reviewed safety and authorization
design exists.
