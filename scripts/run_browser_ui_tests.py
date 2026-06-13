#!/usr/bin/env python3
"""Install no-admin browser test dependencies and run Playwright UI checks."""

import argparse
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_VENV_DIR = ROOT / ".venv-ui-tests"
FALLBACK_VENV_DIR = Path(tempfile.gettempdir()) / "droneops-ui-tests" / ".venv-ui-tests"
REQUIREMENTS = ROOT / "requirements-dev.txt"


def venv_python(venv_dir):
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def run(command):
    subprocess.run([str(item) for item in command], cwd=ROOT, check=True)


def create_venv(venv_dir):
    python_path = venv_python(venv_dir)
    if python_path.exists():
        return python_path
    print("Creating local UI-test virtualenv at {}".format(venv_dir))
    venv.EnvBuilder(with_pip=True).create(venv_dir)
    return python_path


def ensure_venv():
    try:
        return create_venv(PROJECT_VENV_DIR)
    except OSError as exc:
        print("Project-local virtualenv could not be created: {}".format(exc))
        print("Falling back to {}".format(FALLBACK_VENV_DIR))
        return create_venv(FALLBACK_VENV_DIR)


def install_deps(python_path):
    print("Installing UI-test Python modules into the local virtualenv...")
    run([python_path, "-m", "pip", "install", "--upgrade", "pip"])
    run([python_path, "-m", "pip", "install", "-r", REQUIREMENTS])
    print("Installing Playwright Chromium browser into the local virtualenv cache...")
    run([python_path, "-m", "playwright", "install", "chromium"])


def main():
    parser = argparse.ArgumentParser(description="Run browser UI tests.")
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()

    python_path = ensure_venv()
    if not args.skip_install:
        install_deps(python_path)
    run([python_path, "-B", "scripts/browser_ui_test.py"])


if __name__ == "__main__":
    main()
