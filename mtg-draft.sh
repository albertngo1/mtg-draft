#!/usr/bin/env bash
# Thin wrapper around mtg-draft.py — see AGENTS.md for the coaching workflow.
exec python3 "$(dirname "$0")/src/mtg-draft.py" "$@"
