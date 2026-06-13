#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
NODE_ID="${NODE_ID:-drone-01}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8091}"
MODEL="${MODEL:-llama3.1:8b}"

args=(onboard_node/node.py --node-id "$NODE_ID" --host "$HOST" --port "$PORT")
if [[ "${OLLAMA:-0}" == "1" ]]; then
  args+=(--ollama --model "$MODEL")
fi

exec "$PYTHON_BIN" -B "${args[@]}"
