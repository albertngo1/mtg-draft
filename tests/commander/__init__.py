"""Tests for the Commander builder (src/mtgcommander/). Puts src/ on sys.path so the tests import the package
the same way src/mtg-commander.py does. No test touches the network: fixtures in fixtures/ are small,
hand-written records in each source's shape, never downloaded pages."""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))
