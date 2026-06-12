# Setup

## Requirements

- Windows PowerShell or a POSIX-like shell.
- Python 3.10 or newer.
- Optional: Google Maps JavaScript API key.
- Optional: Ollama for local natural-language interpretation.

The current code uses only Python standard-library modules.

## Verify The Project

```powershell
python -m py_compile tools\droneops_basestation\server.py tools\droneops_sim\sim_server.py tools\droneops_local_planner\droneops_planner.py
python tools\droneops_basestation\server.py --self-test
python tools\droneops_sim\sim_server.py --self-test
```

## Run The Basestation

```powershell
python tools\droneops_basestation\server.py
```

Then open:

```text
http://127.0.0.1:8088
```

## Run With Google Maps

```powershell
$env:GOOGLE_MAPS_API_KEY="your-key"
python tools\droneops_basestation\server.py
```

If no key is configured, the UI uses a local canvas fallback.

Convenience script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_basestation.ps1 -GoogleMapsApiKey "your-key"
```

## Run With Ollama

Start Ollama and pull a local model, then run:

```powershell
python tools\droneops_basestation\server.py --ollama --model llama3.1:8b
```

The `Interpret Order` button will use the local model. The `Simulate` button
still validates the route intent before it starts the local simulation.
