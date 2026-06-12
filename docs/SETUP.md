# Setup

## Requirements

- Windows PowerShell or a POSIX-like shell.
- Python 3.10 or newer.
- Optional: Google Maps JavaScript API key.
- Optional: Ollama for local natural-language interpretation.

The current code uses only Python standard-library modules.

## Verify The Project

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

## Run The Onboard Node

```powershell
python onboard_node\node.py --self-test
python onboard_node\node.py --node-id drone-01
```

Default address:

```text
http://127.0.0.1:8091
```

## Run A Mocked Mission

```powershell
python mock_runtime\mission_simulator.py
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_mock_mission.ps1 -Nodes 4 -Ticks 8
```

## Run The Live Web Tracker

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

## Run The Basestation

```powershell
python tools\droneops_basestation\server.py
```

Open:

```text
http://127.0.0.1:8088
```

## Run With Google Maps

```powershell
$env:GOOGLE_MAPS_API_KEY="your-key"
python tools\droneops_basestation\server.py
```

Convenience script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_basestation.ps1 -GoogleMapsApiKey "your-key"
```

## Run With Ollama

```powershell
python onboard_node\node.py --ollama --model llama3.1:8b
python tools\droneops_basestation\server.py --ollama --model llama3.1:8b
```

The model output is validated before it can become mission DSL.
