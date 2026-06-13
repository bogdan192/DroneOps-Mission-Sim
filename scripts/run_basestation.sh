#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8088}"
MODEL="${MODEL:-llama3.1:8b}"

args=(tools/droneops_basestation/server.py --host "$HOST" --port "$PORT" --model "$MODEL")
if [[ "${OLLAMA:-0}" == "1" ]]; then
  args+=(--ollama)
fi

exec "$PYTHON_BIN" -B "${args[@]}"
