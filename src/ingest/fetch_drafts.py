#!/usr/bin/env python3
"""Fetch 17Lands trophy DRAFTS (packs + pool), for pick-order analysis.

Sealed gives one decision per event. A draft gives 42, and 17Lands exposes enough to
recover most of them:

  /api/trophies/    ranks:["mythic"] filters to Mythic trophies; the deck_colors sweep
                    still breaks the 100-row cap (636 unique for HOB PremierDraft).
  /data/draft       every PACK the drafter saw, 14->1 across three packs. `pick` is
                    null for non-owners — which card they took is hidden.
  /data/event_preview  the 42-card pool they ended with, plus their exact rank.

The pick is recoverable from those two: assign each pick to one pool card drawn from
its own pack such that the whole assignment is a perfect matching. Any edge present in
EVERY perfect matching is provably the real pick — 28 of 42 on the first draft tested,
including every early pick, which are the informative ones. See analyse_drafts.py.

Two requests per draft, and 17Lands blocks GETs after roughly 225 of them, so this
caches aggressively and resumes.

Usage:
  python3 src/ingest/fetch_drafts.py --set HOB --format PremierDraft --rank mythic --limit 150
"""
import argparse, itertools, json, os, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "data", "cache")
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.17lands.com/trophy_decks"}


def _get(url, data=None):
    req = urllib.request.Request(url, headers=dict(UA))
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    return json.loads(urllib.request.urlopen(req, timeout=40).read())


def enumerate_trophies(expansion, fmt, ranks, delay=0.8):
    """Unfiltered query first (the only unbiased sample), then the colour sweep."""
    base = {"expansion": expansion, "event_type": fmt, "card_names": [], "ranks": ranks}
    unbiased = [x["aggregate_id"] for x in
                _get("https://www.17lands.com/api/trophies/", dict(base, deck_colors=[]))["data"]]
    seen = {}
    combos = [[]] + [["".join(c)] for n in (1, 2, 3)
                     for c in itertools.combinations("WUBRG", n)]
    for c in combos:
        try:
            for x in _get("https://www.17lands.com/api/trophies/",
                          dict(base, deck_colors=c))["data"]:
                seen[x["aggregate_id"]] = x
        except Exception as e:
            print(f"  colour {c or 'any'}: {e}")
            time.sleep(3)
            continue
        time.sleep(delay)
    return set(unbiased), list(seen.values())


def fetch(expansion, fmt, rank, entries, limit, delay):
    d = os.path.join(CACHE, "drafts", f"{expansion}_{fmt}_{rank}")
    os.makedirs(d, exist_ok=True)
    # Some trophies have no draft log at all (404) — a private or untracked draft. That
    # is permanent, not rate limiting, so record it and never ask again. Only a 403/429
    # or a server error means back off.
    skip_path = os.path.join(d, "_no_draft.json")
    skip = set(json.load(open(skip_path))) if os.path.exists(skip_path) else set()
    got, new, backoff = 0, 0, 60
    for e in entries:
        if e["aggregate_id"] in skip:
            continue
        if limit and got >= limit:
            break
        aid, di = e["aggregate_id"], e["deck_index"]
        paths = {"draft": os.path.join(d, f"{aid}.draft.json"),
                 "deck": os.path.join(d, f"{aid}_{di}.deck.json")}
        urls = {"draft": f"https://www.17lands.com/data/draft?draft_id={aid}",
                "deck": f"https://www.17lands.com/data/event_preview"
                        f"?draft_id={aid}&deck_index={di}"}
        ok = True
        for key in ("draft", "deck"):
            if os.path.exists(paths[key]):
                continue
            try:
                json.dump(_get(urls[key]), open(paths[key], "w"))
                new += 1
                time.sleep(delay)
            except urllib.error.HTTPError as ex:
                if ex.code in (404, 410):
                    skip.add(aid)
                    json.dump(sorted(skip), open(skip_path, "w"))
                    ok = False
                    break
                print(f"  {ex} on {aid} [{key}] — backing off {backoff}s", flush=True)
                if backoff >= 900:
                    print("  still blocked; stopping. Re-run to resume.", flush=True)
                    return got
                time.sleep(backoff)
                backoff *= 4
                ok = False
                break
            except Exception as ex:
                print(f"  {ex} on {aid} [{key}] — retrying later", flush=True)
                time.sleep(5)
                ok = False
                break
        if ok and all(os.path.exists(p) for p in paths.values()):
            got += 1
            if got % 25 == 0:
                print(f"  {got} drafts complete ({new} new files)", flush=True)
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="expansion", required=True)
    ap.add_argument("--format", default="PremierDraft")
    ap.add_argument("--rank", default="mythic", help="17Lands rank filter, or 'any'")
    ap.add_argument("--limit", type=int, default=150)
    ap.add_argument("--delay", type=float, default=4.0)
    a = ap.parse_args()
    ranks = [] if a.rank == "any" else [a.rank]
    idx_path = os.path.join(CACHE, f"draft_index_{a.expansion}_{a.format}_{a.rank}.json")
    if os.path.exists(idx_path):
        idx = json.load(open(idx_path))
        unbiased, entries = set(idx["unbiased"]), idx["entries"]
        print(f"index: {len(entries)} trophies ({len(unbiased)} unbiased)")
    else:
        unbiased, entries = enumerate_trophies(a.expansion, a.format, ranks)
        json.dump({"unbiased": sorted(unbiased), "entries": entries}, open(idx_path, "w"))
        print(f"{len(entries)} unique {a.rank} trophies ({len(unbiased)} unbiased)")
    # Fetch the unbiased ones FIRST — they are the sample any frequency has to rest on.
    entries.sort(key=lambda e: e["aggregate_id"] not in unbiased)
    got = fetch(a.expansion, a.format, a.rank, entries, a.limit, a.delay)
    d = os.path.join(CACHE, "drafts", f"{a.expansion}_{a.format}_{a.rank}")
    sp = os.path.join(d, "_no_draft.json")
    n_skip = len(json.load(open(sp))) if os.path.exists(sp) else 0
    print(f"done: {got} complete drafts cached ({n_skip} trophies have no draft log)")


if __name__ == "__main__":
    main()
