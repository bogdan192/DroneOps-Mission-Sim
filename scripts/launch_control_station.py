#!/usr/bin/env python3
"""Launch the control station as a detached local background process."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    creationflags = 0
    if os.name == "nt":
        creationflags = (
            subprocess.CREATE_NEW_PROCESS_GROUP |
            subprocess.DETACHED_PROCESS |
            subprocess.CREATE_NO_WINDOW
        )
    log_dir = Path(tempfile.gettempdir())
    out_path = log_dir / "droneops_control_station.out.log"
    err_path = log_dir / "droneops_control_station.err.log"
    with out_path.open("ab") as stdout, err_path.open("ab") as stderr:
        process = subprocess.Popen(
            [sys.executable, "-B", "-m", "control_station.app"],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            creationflags=creationflags,
            close_fds=True,
        )
        print("{} {} {}".format(process.pid, out_path, err_path))


if __name__ == "__main__":
    main()
