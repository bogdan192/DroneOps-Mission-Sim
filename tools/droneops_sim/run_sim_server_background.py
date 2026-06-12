#!/usr/bin/env python3
"""Background launcher for the DroneOps sim server on Windows."""

import os
import sys

import sim_server


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    stdout_path = os.path.join(here, "sim_server.out.log")
    stderr_path = os.path.join(here, "sim_server.err.log")
    sys.stdout = open(stdout_path, "w", buffering=1, encoding="utf-8")
    sys.stderr = open(stderr_path, "w", buffering=1, encoding="utf-8")
    sim_server.run_server(sim_server.HOST, sim_server.PORT)


if __name__ == "__main__":
    main()
