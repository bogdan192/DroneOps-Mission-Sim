#!/usr/bin/env python3
"""No-admin launcher for the local DroneOps demo."""

import argparse
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control_station.http_server import ControlStationHandler, ControlStationServer  # noqa: E402
from control_station.mission_session import ControlStationMissionSession  # noqa: E402


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8092
PYTHON_DOWNLOAD_URL = "https://www.python.org/downloads/"


def load_local_env():
    env_path = ROOT / "demo_config.env"
    values = {}
    if not env_path.exists():
        return values
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def pick_port(host, preferred_port, attempts=20):
    last_error = None
    for port in range(preferred_port, preferred_port + attempts):
        try:
            session = ControlStationMissionSession()
            server = ControlStationServer(
                (host, port),
                ControlStationHandler,
                session,
                google_maps_api_key=get_google_maps_api_key(),
            )
            return port, server
        except OSError as exc:
            last_error = exc
    raise RuntimeError("No local port available from {} to {}: {}".format(
        preferred_port,
        preferred_port + attempts - 1,
        last_error,
    ))


def get_google_maps_api_key(cli_value=""):
    if cli_value:
        return cli_value
    local_env = load_local_env()
    return local_env.get("GOOGLE_MAPS_API_KEY") or os.environ.get("GOOGLE_MAPS_API_KEY", "")


def print_python_help():
    print("")
    print("Python 3.10 or newer is required.")
    print("Install Python from: {}".format(PYTHON_DOWNLOAD_URL))
    print("On Windows, tick 'Add python.exe to PATH' in the installer.")
    print("On macOS, the standard python.org installer works without changing this project.")


def check_python():
    if sys.version_info >= (3, 10):
        return
    print_python_help()
    raise SystemExit(2)


def run(args):
    check_python()
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if args.google_maps_api_key:
        os.environ["GOOGLE_MAPS_API_KEY"] = args.google_maps_api_key

    port, server = pick_port(args.host, args.port)
    url = "http://{}:{}".format(args.host, port)
    if args.smoke_test:
        server.server_close()
        print("Demo launcher smoke test passed: {}".format(url))
        return

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.4)

    print("")
    print("DroneOps Mission Sim")
    print("Mode: SIMULATION_ONLY")
    print("URL: {}".format(url))
    if get_google_maps_api_key(args.google_maps_api_key):
        print("Google Maps: configured")
    else:
        print("Google Maps: no key configured; fallback map will be used")
    print("")
    print("Keep this window open while using the demo.")
    print("Press Ctrl+C in this window to stop it.")
    print("")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("")
        print("Stopping local demo...")
    finally:
        server.shutdown()
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Launch the local DroneOps demo.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--google-maps-api-key", default="")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
