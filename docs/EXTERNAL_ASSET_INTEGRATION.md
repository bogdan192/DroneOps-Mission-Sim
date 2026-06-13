# External Asset Integration

This project supports a read-only integration model for external ground, air,
maritime, fixed, or relay assets in the control station.

The goal is shared situational awareness:

- receive or replay asset tracks
- consume normalized ATAK/CoT-style track inputs
- normalize them into a simple JSON shape
- expose CoT-like records for client display
- show them on the control-station map

This layer does not support:

- weapon tasking
- target designation
- fire missions
- intercept guidance
- command/control of external vehicles
- real TAK server writes
- real military network adapters

## Current Implementation

- `integration_contracts/external_assets.py` defines the read-only asset schema,
  prohibited fields, and CoT-like mapping.
- `sim_adapters/external_assets.py` provides simulated ground and air tracks for
  local demos, including normalized simulated ATAK track examples.
- `integration_contracts/atak_telemetry.py` defines the read-only ATAK/CoT-like
  track ingest scaffold.
- `sim_adapters/atak_feeds.py` provides simulated ATAK-equipped drone,
  personnel/team, and air-asset tracks.
- `control_station/mission_session.py` includes `externalAssets` in snapshots.
- `control_station/http_server.py` exposes `GET /api/assets` and
  `GET /api/atak/tracks`.
- `control_station/ui.py` shows external assets as read-only tracks.
- `real_integrations/disabled_adapters.py` includes a fail-closed real external
  asset feed placeholder.

## Asset Shape

```json
{
  "type": "external.asset",
  "schemaVersion": "0.1",
  "uid": "asset.ground.observer-01",
  "callsign": "Ground Observer 1",
  "domain": "ground",
  "kind": "team",
  "source": "mock-external-assets",
  "status": "observed",
  "position": { "lat": 44.4049, "lon": 26.3049, "alt": 74 },
  "readOnly": true,
  "liveExecution": false
}
```

Allowed domains are `ground`, `air`, `maritime`, `fixed`, and `unknown`.
Allowed kinds are `vehicle`, `aircraft`, `team`, `personnel`, `drone`, `uas`,
`sensor`, `relay`, and `unknown`.

See `docs/ATAK_TELEMETRY_INTEGRATION.md` for the inbound ATAK/CoT-style track
scaffold.

## Future Real Adapter Boundary

A future real adapter should be a separate reviewed package that converts
authorized TAK/CoT, Link, ADS-B, or other deployed control-station feeds into
the read-only asset shape. It should not import simulator modules.

Before any real deployment, add:

- authentication and authorization
- source allowlisting
- transport security
- replay/spoofing checks
- audit logs
- operator-visible source labels
- data retention rules

Keep real adapters read-only unless a separate, reviewed command authority and
safety design exists.
