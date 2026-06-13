# Control Station Web Tracking

The control station web tracker runs the simulation-only onboard-node mission in
a browser and streams changing drone positions through polling APIs.

Implementation is split by responsibility:

- `control_station/mission_session.py` owns mission session state, selected
  drones, live-order simulation, and telemetry advancement.
- `control_station/http_server.py` owns HTTP routing and JSON responses.
- `control_station/ui.py` owns the browser HTML/CSS/JavaScript template.
- `control_station/app.py` owns CLI startup and self-test wiring.
- `live_web/server.py` is only a compatibility entrypoint.

The control station uses `sim_adapters/` for fleet inventory, transport, and
telemetry. It then normalizes simulated mission telemetry into an ATAK/CoT-like
tracker model. The tracker model is reusable; this web server is not a real
ATAK, phone, or drone integration.

Clicking or hovering over a drone map icon opens a compact drone detail popup.
The popup shows simulated onboard parameters and a Google Street View panel near
the current simulated position. If no Street View panorama is available near the
coordinates, the popup shows a clear fallback message.

## Run

```powershell
python -m control_station.app
```

macOS/Linux:

```bash
python3 -B -m control_station.app
```

Legacy entrypoint:

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
python -m control_station.app
```

macOS/Linux:

```bash
export GOOGLE_MAPS_API_KEY="your-key"
python3 -B -m control_station.app
```

Windows convenience script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_live_web.ps1 -GoogleMapsApiKey "your-key"
```

macOS/Linux convenience script:

```bash
GOOGLE_MAPS_API_KEY="your-key" bash scripts/run_control_station.sh
```

## APIs

### `POST /api/mission/start`

Starts a simulated mission.

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

## Drone Detail Popup

The popup includes:

- state
- mission id
- latitude, longitude, and altitude
- battery percentage
- tracking source
- ATAK-style UID
- live-execution flag
- last-seen timestamp
- Street View panorama when Google imagery is available

## Safety

The web tracker uses mock telemetry only. It does not connect to ATAK, Android,
MAVLink, PX4, ArduPilot, or a real drone.
