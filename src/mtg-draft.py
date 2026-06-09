#!/usr/bin/env python3
"""Thin entry point for mtg-draft — all logic lives in the `mtgdraft` package (src/mtgdraft/).
Kept at this path so the launchers (mtg-draft.sh/.bat) and the daemon's `_tail` self-spawn are
unchanged. See the package modules: config, sources, grades, analysis, logread, capture, etl,
render, cli."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # make `mtgdraft` importable
from mtgdraft.cli import main

if __name__ == "__main__":
    main()
