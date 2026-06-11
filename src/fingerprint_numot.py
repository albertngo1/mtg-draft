#!/usr/bin/env python3
"""Fingerprint the Numot transcript scrape so incremental runs skip redundant work.

The scrape has two stages that can redo work:
  1. fetch   — fetch_subs.sh downloads auto-captions to data/numot-subs/<SET>/<id>.txt.
               Already idempotent (skips existing .txt).
  2. distill — stage-2 agents summarize every transcript into draft-guides/numot/<SET>.md.
               WITHOUT a manifest this re-summarizes everything each run.

This script records a content fingerprint (sha1 + word count) of every transcript
that has been distilled into draft-guides/numot/, in a committed manifest (draft-guides/numot/manifest.json).
A future run computes the same fingerprints and only fetches/distills the videos
that are NEW or whose transcript CHANGED.

Usage:
  fingerprint_numot.py update          Rebuild draft-guides/numot/manifest.json from current
                                        transcripts + worklist.json (run after a
                                        distill pass; marks every fetched video distilled).
  fingerprint_numot.py new             Print video IDs in worklist.json that are NOT
                                        in the manifest, or whose transcript sha1
                                        changed — i.e. the work an incremental run
                                        actually needs to do. Grouped by set.
  fingerprint_numot.py new --ids       Same, but print bare "<SET>\t<id>" lines
                                        (feed straight into a fetch/distill loop).
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # ~/src/mtg-draft
SUBS = ROOT / "data" / "numot-subs"                    # transcript tree (gitignored)
WORKLIST = SUBS / "worklist.json"
MANIFEST = ROOT / "draft-guides" / "numot" / "manifest.json"   # committed, travels with repo


def sha1_words(txt_path):
    raw = txt_path.read_bytes()
    return hashlib.sha1(raw).hexdigest(), len(raw.split())


def scan_transcripts():
    """{set: {video_id: {"sha1":..., "words":...}}} for every .txt on disk."""
    out = {}
    for txt in sorted(SUBS.glob("*/*.txt")):
        s, vid = txt.parent.name, txt.stem
        if s.startswith((".", "_")):
            continue
        sha1, words = sha1_words(txt)
        out.setdefault(s, {})[vid] = {"sha1": sha1, "words": words}
    return out


def load_worklist():
    return json.loads(WORKLIST.read_text()) if WORKLIST.exists() else {}


def cmd_update():
    work = load_worklist()
    scanned = scan_transcripts()
    videos, sets = {}, {}
    for s, vids in scanned.items():
        tier = work.get(s, {}).get("tier")
        sets[s] = {"tier": tier, "file": f"{s}.md", "video_ids": sorted(vids)}
        for vid, fp in vids.items():
            videos[vid] = {"set": s, "sha1": fp["sha1"], "words": fp["words"], "distilled": True}
    # videos in the worklist with no transcript on disk = captionless MISS — record them so
    # an incremental run doesn't keep retrying a video that simply has no auto-subs.
    miss = []
    for s, w in work.items():
        for v in w.get("videos", []):
            if v["id"] not in videos:
                videos[v["id"]] = {"set": s, "sha1": None, "words": 0,
                                   "distilled": False, "reason": "no-captions"}
                miss.append(f"{s}/{v['id']}")
    manifest = {
        "channel": "NumotTheNummy",
        "scope": "regular Arena draft VODs (cube/sealed/constructed/alchemy excluded)",
        "note": "Fingerprint of distilled scrape. sha1 = sha1 of the cleaned transcript .txt.",
        "counts": {"sets": len(sets), "videos_distilled": sum(1 for v in videos.values() if v["distilled"]),
                   "videos_no_captions": len(miss)},
        "sets": dict(sorted(sets.items())),
        "videos": dict(sorted(videos.items())),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {MANIFEST.relative_to(ROOT)} — {manifest['counts']['sets']} sets, "
          f"{manifest['counts']['videos_distilled']} distilled, "
          f"{manifest['counts']['videos_no_captions']} captionless")


def cmd_new(bare_ids=False):
    work = load_worklist()
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"videos": {}}
    known = manifest.get("videos", {})
    scanned = scan_transcripts()
    todo = {}  # set -> list of (id, why)
    for s, w in work.items():
        for v in w.get("videos", []):
            vid = v["id"]
            rec = known.get(vid)
            if rec is None:
                todo.setdefault(s, []).append((vid, "new"))
            elif rec.get("reason") == "no-captions":
                continue  # known captionless — don't retry
            else:
                # transcript present on disk but changed since fingerprinted?
                disk = scanned.get(s, {}).get(vid)
                if disk and disk["sha1"] != rec.get("sha1"):
                    todo.setdefault(s, []).append((vid, "changed"))
    if bare_ids:
        for s in sorted(todo):
            for vid, _ in todo[s]:
                print(f"{s}\t{vid}")
        return
    if not todo:
        print("up to date — no new or changed videos to fetch/distill")
        return
    total = sum(len(v) for v in todo.values())
    print(f"{total} video(s) need work across {len(todo)} set(s):")
    for s in sorted(todo):
        ids = ", ".join(f"{vid} ({why})" for vid, why in todo[s])
        print(f"  {s}: {ids}")


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("update", "new"):
        print(__doc__)
        sys.exit(1)
    if args[0] == "update":
        cmd_update()
    else:
        cmd_new(bare_ids="--ids" in args)


if __name__ == "__main__":
    main()
