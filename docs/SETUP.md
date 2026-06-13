# Setup

## Requirements

- Windows PowerShell, macOS Terminal, or another POSIX-like shell.
- Python 3.10 or newer.
- Optional: Google Maps JavaScript API key.
- Optional: Ollama for local natural-language interpretation.

The current code uses only Python standard-library modules.

## No-Admin Demo Launch

Windows:

```text
Double-click Launch DroneOps Demo.cmd
```

macOS:

```text
Double-click Launch DroneOps Demo.command
```

The launcher starts the local control station, opens the browser, and keeps all
execution on `127.0.0.1`. See `NO_ADMIN_QUICK_START.md`.

## Verify The Project

macOS/Linux:

```bash
python3 -B scripts/test.py
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

## Browser UI Tests

The browser UI tests use Playwright as a development/test dependency. The helper
creates a local `.venv-ui-tests` folder, installs `requirements-dev.txt`, and
downloads Playwright Chromium without admin access.

macOS/Linux:

```bash
python3 -B scripts/run_browser_ui_tests.py
```

Windows:

```powershell
python -B scripts\run_browser_ui_tests.py
```

After the first install, rerun faster with:

```bash
python3 -B scripts/run_browser_ui_tests.py --skip-install
```

## Run The Onboard Node

macOS/Linux:

```bash
python3 -B onboard_node/node.py --self-test
python3 -B onboard_node/node.py --node-id drone-01
```

Convenience script:

```bash
bash scripts/run_onboard_node.sh
```

Windows:

```powershell
python onboard_node\node.py --self-test
python onboard_node\node.py --node-id drone-01
```

Default address:

```text
http://127.0.0.1:8091
```

## Run A Mocked Mission

macOS/Linux:

```bash
python3 -B mock_runtime/mission_simulator.py
```

Or:

```bash
NODES=4 TICKS=8 bash scripts/run_mock_mission.sh
```

Windows:

```powershell
python mock_runtime\mission_simulator.py
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_mock_mission.ps1 -Nodes 4 -Ticks 8
```

## Run The Live Web Tracker

macOS/Linux:

```bash
python3 -B -m control_station.app
```

Or:

```bash
bash scripts/run_control_station.sh
```

Windows:

```powershell
python -m control_station.app
```

Open:

```text
http://127.0.0.1:8092
```

With Google Maps:

macOS/Linux:

```bash
export GOOGLE_MAPS_API_KEY="your-key"
python3 -B -m control_station.app
```

Windows:

```powershell
$env:GOOGLE_MAPS_API_KEY="your-key"
python -m control_station.app
```

## Run The Basestation

macOS/Linux:

```bash
python3 -B tools/droneops_basestation/server.py
```

Windows:

```powershell
python tools\droneops_basestation\server.py
```

Open:

```text
http://127.0.0.1:8088
```

## Run With Google Maps

macOS/Linux:

```bash
export GOOGLE_MAPS_API_KEY="your-key"
python3 -B tools/droneops_basestation/server.py
```

Convenience script:

```bash
GOOGLE_MAPS_API_KEY="your-key" bash scripts/run_basestation.sh
```

Windows:

```powershell
$env:GOOGLE_MAPS_API_KEY="your-key"
python tools\droneops_basestation\server.py
```

Convenience script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_basestation.ps1 -GoogleMapsApiKey "your-key"
```

## Run With Ollama

macOS/Linux:

```bash
OLLAMA=1 MODEL="llama3.1:8b" bash scripts/run_onboard_node.sh
OLLAMA=1 MODEL="llama3.1:8b" bash scripts/run_basestation.sh
```

Windows:

```powershell
python onboard_node\node.py --ollama --model llama3.1:8b
python tools\droneops_basestation\server.py --ollama --model llama3.1:8b
```

The model output is validated before it can become mission DSL.
