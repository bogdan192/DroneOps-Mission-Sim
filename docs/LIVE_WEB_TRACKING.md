# Live Web Tracking

The live web tracker runs the mocked onboard-node mission in a browser and
streams changing drone positions through polling APIs.

It mocks ATAK drone tracking by normalizing mission telemetry into an
ATAK/CoT-like tracker model. The same API can later be fed by a real ATAK plugin
or CoT receiver.

## Run

```powershell
python live_web\server.py
```

Open:

```text
http://127.0.0.1:8092
```

With Google Maps:

```powershell
$env:GOOGLE_MAPS_API_KEY="your-key"
python live_web\server.py
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_live_web.ps1 -GoogleMapsApiKey "your-key"
```

## APIs

### `POST /api/mission/start`

Starts a mocked mission.

```json
{
  "order": "coordinate with peers and simulate the Bucharest outskirts route",
  "nodeCount": 4,
  "ticks": 36,
  "tickSeconds": 0.6
}
```

### `GET /api/mission`

Returns the mission state, assignments, controller programs, latest telemetry,
and normalized tracked drones.

### `GET /api/atak/drones`

Returns the ATAK-style tracked drone snapshot:

```json
{
  "source": "mock-atak",
  "mode": "SIMULATION_ONLY",
  "drones": []
}
```

Each drone includes a `cotLike` object with event, point, and detail fields.

## Safety

The web tracker uses mock telemetry only. It does not connect to ATAK, Android,
MAVLink, PX4, ArduPilot, or a real drone.

