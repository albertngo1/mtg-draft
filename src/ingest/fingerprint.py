#!/usr/bin/env python3
"""Fingerprint a channel's transcript scrape so incremental runs skip redundant work.

Channel-agnostic: takes a channel slug (one of the keys in src/ingest/channels.json,
e.g. lords-of-limited, numot, limited-resources) as its first argument and derives all
paths from it.

The scrape has two stages that can redo work:
  1. fetch   — src/ingest/fetch_subs.sh downloads auto-captions to
               data/subs/<slug>/<SET>/<id>.txt. Already idempotent (skips existing .txt).
  2. distill — stage-2 agents summarize every transcript into draft-guides/<slug>/<SET>.md.
               WITHOUT a manifest this re-summarizes everything each run.

This script records a content fingerprint (sha1 + word count) of every transcript
that has been distilled into draft-guides/<slug>/, in a committed manifest
(draft-guides/<slug>/manifest.json). A future run computes the same fingerprints and
only fetches/distills the videos that are NEW or whose transcript CHANGED.

Usage:
  fingerprint.py <slug> coverage    Per set: transcripts on disk vs the guide that should
                                     reflect them. ok / MISSING (no guide) / BEHIND (guide
                                     older than its newest transcript). Start here.
  fingerprint.py <slug> new         Print video IDs in worklist.json that are NOT in the
                                     manifest, or whose transcript sha1 changed — i.e. the
                                     work an incremental run actually needs to do. Grouped by set.
  fingerprint.py <slug> new --ids   Same, but print bare "<SET>\t<id>" lines
                                     (feed straight into a fetch/distill loop).
  fingerprint.py <slug> update      Rebuild draft-guides/<slug>/manifest.json from current
                                     transcripts + worklist.json. Run ONLY after a distill
                                     pass. SKIPS any set whose guide is missing or stale so
                                     it cannot certify undistilled work as done.
  fingerprint.py <slug> update --force
                                     Mark everything distilled regardless. Only for repairing
                                     a manifest you have separately verified.

ORDER MATTERS: coverage -> new -> distill -> update. Running `update` before distilling is
what caused the 2026-08-23 incident: it marked 31 videos across 5 sets as distilled when no
guide reflected them, and `new` then reported "up to date" forever. `update` now refuses.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]             # repo root (two up from src/ingest/)
CHANNELS = ROOT / "src" / "ingest" / "channels.json"


def sha1_words(txt_path):
    raw = txt_path.read_bytes()
    return hashlib.sha1(raw).hexdigest(), len(raw.split())


def scan_transcripts(subs):
    """{set: {video_id: {"sha1":..., "words":...}}} for every .txt on disk."""
    out = {}
    for txt in sorted(subs.glob("*/*.txt")):
        s, vid = txt.parent.name, txt.stem
        if s.startswith((".", "_")):
            continue
        sha1, words = sha1_words(txt)
        out.setdefault(s, {})[vid] = {"sha1": sha1, "words": words}
    return out


def load_worklist(worklist):
    return json.loads(worklist.read_text()) if worklist.exists() else {}


def guide_path(channel_meta, slug, set_code):
    """Path to the per-set guide file for a channel, per its guide_filename template."""
    tpl = channel_meta.get("guide_filename", "<SET>.md")
    gdir = channel_meta.get("guide_dir", f"draft-guides/{slug}")
    return ROOT / gdir / tpl.replace("<SET>", set_code)


def stale_sets(slug, subs, channel_meta):
    """Sets whose guide does not actually reflect the transcripts on disk.

    Returns {set: reason}. Two ways a set is stale:
      missing  — transcripts exist but no guide file was ever written
      behind   — the guide file is OLDER than the newest transcript for that set

    This exists because `update` used to mark every transcript on disk as distilled
    without checking whether any guide reflected it, which silently hid 31 undistilled
    videos across 5 sets (2026-08-23). A set-level "does a guide exist" check is NOT
    enough — a set with a stale guide passes that and still hides work.
    """
    out = {}
    for set_dir in sorted(subs.glob("*/")):
        s = set_dir.name
        if s.startswith((".", "_")):
            continue
        txts = list(set_dir.glob("*.txt"))
        if not txts:
            continue
        g = guide_path(channel_meta, slug, s)
        if not g.exists():
            out[s] = "missing"
        elif g.stat().st_mtime < max(t.stat().st_mtime for t in txts):
            out[s] = "behind"
    return out


def cmd_coverage(slug, subs, worklist, manifest_path, channel_meta):
    """Per set: transcripts on disk vs the guide and manifest that should account for them.

    TWO INDEPENDENT SIGNALS, because neither is trustworthy alone and they disagree:

      guide   mtime of the guide file vs the newest transcript. Catches "new episodes
              arrived after the guide was written". False-positives when transcripts are
              re-fetched or checked out without their content changing.
      unfp    transcripts on disk that no manifest entry mentions. Catches "fetched but
              never fingerprinted". False-positives where a manifest was backfilled and
              never listed videos that WERE distilled (lords-of-limited SOS/MKM).

    A set flagged by BOTH is very likely a real gap. One signal alone is a prompt to look,
    not a verdict — open the guide and check before spending a distill pass on it.
    """
    scanned = scan_transcripts(subs)
    stale = stale_sets(slug, subs, channel_meta)
    known = set(json.loads(manifest_path.read_text()).get("videos", {})) \
        if manifest_path.exists() else set()
    print(f"{slug}:")
    if not scanned:
        print("  (no transcripts on disk)")
        return
    flagged = []
    for s in sorted(scanned):
        g = guide_path(channel_meta, slug, s)
        gstate = {"missing": "MISSING", "behind": "BEHIND "}.get(stale.get(s), "ok     ")
        unfp = len(set(scanned[s]) - known)
        both = gstate.strip() != "ok" and unfp
        if gstate.strip() != "ok" or unfp:
            flagged.append((s, both))
        print(f"  {s:6s} guide {gstate}  unfp {unfp:2d}/{len(scanned[s]):2d}"
              f"  {'<== BOTH' if both else ''}")
    strong = [s for s, b in flagged if b]
    weak = [s for s, b in flagged if not b]
    print(f"  --> {len(scanned) - len(flagged)}/{len(scanned)} sets clean on both signals")
    if strong:
        print(f"      likely real gaps (both signals): {', '.join(strong)}")
    if weak:
        print(f"      one signal only, verify by hand: {', '.join(weak)}")


def cmd_update(slug, subs, worklist, manifest_path, channel_meta, force=False):
    work = load_worklist(worklist)
    scanned = scan_transcripts(subs)
    # Do not certify a set as distilled when no guide reflects it. Skipping keeps those
    # videos absent from the manifest, so `new` keeps reporting them instead of going quiet.
    stale = stale_sets(slug, subs, channel_meta)
    if stale and not force:
        for s, why in sorted(stale.items()):
            print(f"  SKIP {s}: guide {why} — not marking its "
                  f"{len(scanned.get(s, {}))} transcript(s) distilled")
        print(f"  ({len(stale)} set(s) skipped; distill them then re-run, or pass --force)")
        scanned = {s: v for s, v in scanned.items() if s not in stale}
    # per-set guide filename is channel-specific (e.g. <SET>-draft-guide.md for lords-of-limited,
    # <SET>.md for numot/limited-resources) — read the template from channels.json.
    fname_tpl = channel_meta.get("guide_filename", "<SET>.md")
    videos, sets = {}, {}
    for s, vids in scanned.items():
        tier = work.get(s, {}).get("tier")
        sets[s] = {"tier": tier, "file": fname_tpl.replace("<SET>", s), "video_ids": sorted(vids)}
        for vid, fp in vids.items():
            videos[vid] = {"set": s, "sha1": fp["sha1"], "words": fp["words"], "distilled": True}
    # videos in the worklist with no transcript on disk = captionless MISS — record them so
    # an incremental run doesn't keep retrying a video that simply has no auto-subs.
    miss = []
    for s, w in work.items():
        # A skipped-because-stale set must NOT land here: "no-captions" is a permanent
        # tombstone that `new` deliberately never retries, so mislabelling an undistilled
        # video as captionless hides it harder than the bug this guard exists to prevent.
        if s in stale and not force:
            continue
        for v in w.get("videos", []):
            if v["id"] not in videos:
                videos[v["id"]] = {"set": s, "sha1": None, "words": 0,
                                   "distilled": False, "reason": "no-captions"}
                miss.append(f"{s}/{v['id']}")
    manifest = {
        "channel": channel_meta.get("name", slug),
        "scope": channel_meta.get("content_type", ""),
        "note": "Fingerprint of distilled scrape. sha1 = sha1 of the cleaned transcript .txt.",
        "counts": {"sets": len(sets), "videos_distilled": sum(1 for v in videos.values() if v["distilled"]),
                   "videos_no_captions": len(miss)},
        "sets": dict(sorted(sets.items())),
        "videos": dict(sorted(videos.items())),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {manifest_path.relative_to(ROOT)} — {manifest['counts']['sets']} sets, "
          f"{manifest['counts']['videos_distilled']} distilled, "
          f"{manifest['counts']['videos_no_captions']} captionless")


def cmd_new(slug, subs, worklist, manifest_path, bare_ids=False):
    work = load_worklist(worklist)
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"videos": {}}
    known = manifest.get("videos", {})
    scanned = scan_transcripts(subs)
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


def load_channel(slug):
    channels = json.loads(CHANNELS.read_text()).get("channels", {})
    if slug not in channels:
        sys.exit(f"unknown channel slug '{slug}' — known: {', '.join(sorted(channels))}")
    return channels[slug]


def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[1] not in ("update", "new", "coverage"):
        print(__doc__)
        sys.exit(1)
    slug, cmd = args[0], args[1]
    channel_meta = load_channel(slug)
    subs = ROOT / "data" / "subs" / slug
    worklist = subs / "worklist.json"
    manifest_path = ROOT / "draft-guides" / slug / "manifest.json"
    if cmd == "update":
        cmd_update(slug, subs, worklist, manifest_path, channel_meta,
                   force="--force" in args)
    elif cmd == "coverage":
        cmd_coverage(slug, subs, worklist, manifest_path, channel_meta)
    else:
        cmd_new(slug, subs, worklist, manifest_path, bare_ids="--ids" in args)


if __name__ == "__main__":
    main()
