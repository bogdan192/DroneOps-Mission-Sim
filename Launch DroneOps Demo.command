#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo
  echo "Python 3.10 or newer is required."
  echo "Opening the Python download page..."
  open "https://www.python.org/downloads/" || true
  echo
  echo "Install Python, then run this launcher again."
  echo
  read -r -p "Press Return to close this window."
  exit 1
fi

"$PYTHON_BIN" -B scripts/demo_launcher.py

echo
read -r -p "Press Return to close this window."
