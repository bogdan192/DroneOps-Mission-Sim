#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
ORDER="${ORDER:-coordinate with peers and simulate the Bucharest outskirts route}"
NODES="${NODES:-4}"
TICKS="${TICKS:-8}"

args=(mock_runtime/mission_simulator.py --order "$ORDER" --nodes "$NODES" --ticks "$TICKS")
if [[ "${FULL:-0}" == "1" ]]; then
  args+=(--full)
fi

exec "$PYTHON_BIN" -B "${args[@]}"
