#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8092}"

exec "$PYTHON_BIN" -B live_web/server.py --host "$HOST" --port "$PORT"
