#!/usr/bin/env python3
"""Thin entry point for mtg-commander, the Commander (EDH) deck builder. All logic lives in the
`mtgcommander` package (src/mtgcommander/); see its modules: config, net, carddb, decklist,
providers/, roles, brackets, fantasy, score, build, validate, render, cli."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # make `mtgcommander` importable
from mtgcommander.cli import main

if __name__ == "__main__":
    main()
