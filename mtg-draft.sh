#!/usr/bin/env bash
# Thin wrapper around mtg-draft.py — see AGENTS.md for the coaching workflow.
#
# Auto-wires the SSH/log source from the capture daemon's config so live
# commands (pull/pool/watch) read Albert's laptop with ZERO flags. The capture
# daemon already stores ssh target / key / remote log path in
# data/logs/.capture.json; without this, `pull` reads the (nonexistent) local
# log and fails. Env vars set by the caller always win (we only fill blanks).
DIR="$(cd "$(dirname "$0")" && pwd)"
CAP="$DIR/data/logs/.capture.json"
if [ -f "$CAP" ]; then
  eval "$(python3 - "$CAP" <<'PY'
import json, sys, shlex
try:
    c = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)
emit = lambda k, v: print(f'export {k}={shlex.quote(str(v))}') if v else None
import os
if c.get('ssh') and not os.environ.get('MTG_SSH'):
    emit('MTG_SSH', c['ssh'])
if c.get('ssh_key') and not os.environ.get('MTG_SSH_KEY'):
    emit('MTG_SSH_KEY', c['ssh_key'])
# Remote log path lives under the laptop user; only use it in SSH mode.
if c.get('log') and c.get('ssh') and not os.environ.get('MTG_LOG'):
    emit('MTG_LOG', c['log'])
PY
)"
fi
exec python3 "$DIR/src/mtg-draft.py" "$@"
