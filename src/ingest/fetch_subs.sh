#!/usr/bin/env bash
# Shared YouTube auto-caption fetcher for ALL draft-guide source channels.
#
#   src/ingest/fetch_subs.sh <channel-slug>
#
# Channel slug must match a key in src/ingest/channels.json and a raw bucket at
# data/subs/<slug>/ holding worklist.json. For each video listed there, downloads +
# cleans the English auto-captions into data/subs/<slug>/<SET>/<id>.txt and records
# id<TAB>upload_date<TAB>title in data/subs/<slug>/meta.tsv (the single date model).
# Idempotent: skips any video whose .txt already exists; meta.tsv is upserted per fetch.
#
# Auto-captions transcribe SPEECH for the podcast channels (numot, limited-resources),
# so card/mechanic names get mangled — correct only where confident, mark (?) when distilling.
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"   # src/ingest -> repo root
SLUG="${1:?usage: fetch_subs.sh <channel-slug>}"
BUCKET="$ROOT/data/subs/$SLUG"
WORKLIST="$BUCKET/worklist.json"
META="$BUCKET/meta.tsv"
LOG="$BUCKET/fetch.log"

[ -f "$WORKLIST" ] || { echo "no worklist at $WORKLIST" >&2; exit 1; }
mkdir -p "$BUCKET"
[ -f "$META" ] || : > "$META"
echo "=== fetch start $(date) — channel $SLUG ===" >> "$LOG"

python3 - "$WORKLIST" << 'PYEOF' > /tmp/fetch_list_$SLUG.txt
import json, sys
work = json.load(open(sys.argv[1]))
for code, w in work.items():
    for v in w["videos"]:
        print(f"{code}\t{v['id']}")
PYEOF

clean_vtt() {  # $1=vtt $2=out.txt : strip cues/tags, collapse rolling-caption duplicates
  python3 - "$1" "$2" << 'PYEOF'
import re, sys
raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()
lines, out, prev = raw.splitlines(), [], None
for ln in lines:
    if "-->" in ln or ln.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or re.fullmatch(r"\d*", ln.strip()):
        continue
    ln = re.sub(r"<[^>]+>", "", ln).strip()
    if not ln or ln == prev:
        continue
    out.append(ln); prev = ln
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(out) + "\n")
PYEOF
}

n=0
while IFS=$'\t' read -r set vid; do
  mkdir -p "$BUCKET/$set"
  txt="$BUCKET/$set/$vid.txt"
  [ -s "$txt" ] && continue
  yt-dlp --skip-download --write-auto-subs --sub-langs en --sub-format vtt \
         --print-to-file "%(id)s\t%(upload_date)s\t%(title)s" "$META" \
         --sleep-requests 1 --retries 8 --retry-sleep 30 \
         -o "$BUCKET/$set/$vid" "https://www.youtube.com/watch?v=$vid" >> "$LOG" 2>&1
  vtt="$BUCKET/$set/$vid.en.vtt"
  if [ -s "$vtt" ]; then
    clean_vtt "$vtt" "$txt" && rm -f "$vtt"
    echo "OK  $set $vid $(wc -w < "$txt" | tr -d ' ')w" >> "$LOG"
  else
    echo "MISS $set $vid (no auto-subs)" >> "$LOG"
  fi
  n=$((n+1)); sleep 2
done < /tmp/fetch_list_$SLUG.txt
echo "=== fetch done $(date) — processed $n ===" >> "$LOG"
