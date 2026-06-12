# Ollama Integration

The local planner can call Ollama to interpret natural-language orders into
mission intent JSON.

## Run

```powershell
python tools\droneops_basestation\server.py --ollama --model llama3.1:8b
```

The basestation sends orders to:

```text
http://127.0.0.1:11434/api/chat
```

## Validation

Model output is never trusted directly. The planner validates:

- required mission intent fields
- simulation-only mode
- `liveExecution: false`
- bounded operating area
- route waypoints
- speed and altitude limits
- absence of raw command fields
- prohibited terms

The model proposes mission structure. Deterministic code validates it.

