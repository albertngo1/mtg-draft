#!/usr/bin/env bash
# Thin wrapper around src/mtg-commander.py, the Commander deck builder (see README "Commander").
DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$DIR/src/mtg-commander.py" "$@"
