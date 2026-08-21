#!/usr/bin/env python3
"""Fetch 17Lands' real archetype (colour-pair) win rates for a set.

    python3 card-reference/fetch_archetypes.py <SET> [EVENT_TYPE] [--refresh]

Why this exists: a per-card GIH WR file cannot tell you which *archetype* wins. The obvious
workaround — averaging the win rates of the gold cards legal in each pair — is a bad proxy: it
conflates card quality with archetype quality, rests on 3-8 cards per pair, and in practice it gets
the ordering wrong. Measured against this endpoint the proxy mis-ranked pairs by up to five places
(e.g. it put BLB Simic 1st where the real data has it 5th, and MKM Golgari 6th where it is 9th).
Use this, not the proxy, for anything that claims "the best archetype is X".

17Lands serves it from /color_ratings/data. `combine_splash=true` folds a splash back into the
two-colour pair, which is what you want when asking "how good is UW" rather than "how good is
UW-splashing-red". Rows with is_summary are aggregates (Mono-color, Two-color, ...) and are skipped;
pairs under `min_games` are dropped because a pair nobody drafted has a meaningless win rate.

Output is a ranked table; the raw payload is cached at
data/cache/17lands_arch_<SET>_<EVENT_TYPE>.json (gitignored via data/). Pass --refresh to re-fetch.

The `share` column is the pair's share of all two-colour games — read it alongside the win rate.
A pair that is both the most-played and the highest-winning is a different claim from a pair that
wins a lot because only specialists draft it.
"""
import json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_GAMES = 1000

SET = (sys.argv[1] if len(sys.argv) > 1 else "SOS").upper()
args = [a for a in sys.argv[2:] if not a.startswith("--")]
EVENT = args[0] if args else "PremierDraft"
CACHE = os.path.join(ROOT, "data", "cache", f"17lands_arch_{SET}_{EVENT}.json")


def fetch(refresh=False):
    if not refresh and os.path.exists(CACHE):
        with open(CACHE) as f:
            return json.load(f)
    url = (f"https://www.17lands.com/color_ratings/data?expansion={SET}"
           f"&event_type={EVENT}&start_date=2019-01-01&end_date=2030-01-01"
           f"&combine_splash=true")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 mtg-draft"})
    data = json.loads(urllib.request.urlopen(req, timeout=60).read())
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w") as f:
        json.dump(data, f)
    return data


rows = [r for r in fetch("--refresh" in sys.argv)
        if not r.get("is_summary") and (r.get("games") or 0) >= MIN_GAMES]
for r in rows:
    r["wr"] = r["wins"] / r["games"] * 100

def group(n):
    return [r for r in rows if isinstance(r.get("short_name"), str) and len(r["short_name"]) == n]

pairs = group(2)
total = sum(r["games"] for r in pairs) or 1

print(f"{SET} {EVENT} — 17Lands archetype win rates (combine_splash, >={MIN_GAMES:,} games)\n")
print(f"  {'pair':5s} {'archetype':22s} {'win %':>7s} {'games':>10s} {'share':>7s}")
for r in sorted(pairs, key=lambda r: -r["wr"]):
    print(f"  {r['short_name']:5s} {r['color_name'][:22]:22s} {r['wr']:6.2f}% "
          f"{r['games']:>10,} {r['games']/total*100:6.1f}%")

for n, label in ((1, "MONO"), (3, "THREE-COLOUR")):
    g = group(n)
    if not g:
        continue
    print(f"\n  {label}")
    for r in sorted(g, key=lambda r: -r["wr"]):
        print(f"  {r['short_name']:5s} {r['color_name'][:22]:22s} {r['wr']:6.2f}% {r['games']:>10,}")
