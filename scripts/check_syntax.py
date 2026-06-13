#!/usr/bin/env python3
"""Compile Python source files without writing __pycache__ files."""

import sys


def main(paths):
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            compile(handle.read(), path, "exec")


if __name__ == "__main__":
    main(sys.argv[1:])
