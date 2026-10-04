#!/usr/bin/env python3
"""Per-colour-pair card performance from 17Lands — the synergy signal a single GIH WR hides.

    python3 card-reference/fetch_pair_synergy.py <SET> [--refresh] [--min 1000] [--z 2.5]

A card's set-wide GIH WR averages over every deck that played it. This pulls each card's stats
*inside each two-colour deck* (17Lands `colors=` filter on /api/card_data) and compares the card's
IWD in that pair against its own set-wide IWD. IWD (GIH WR minus not-drawn WR) is measured within
the same decks, so it controls for deck quality — the comparison isolates "this card is better or
worse in this shell", which is what synergy means.

Prints:
  1. cards that over/under-perform in a pair (|z| >= --z, games >= --min), z from a binomial SE
  2. colour halves: game-weighted mean shift of each colour's mono cards inside each pair
  3. per pair, the C/U cards with the highest in-pair IWD (the working engine)

Caveats: ~2,900 card x pair tests, so expect ~1% false hits at |z|>=2.5 — trust patterns (several
cards moving together), not one row. A weak deck inflates IWD of every good card in it a little.
Cache: data/cache/17lands_pairs_<SET>.json (24h).
"""
import json, math, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SET = (sys.argv[1] if len(sys.argv) > 1 else "FRA").upper()
def _opt(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default
MIN, ZCUT = _opt("--min", 1000), _opt("--z", 2.5)
PAIRS = ["WU", "UB", "BR", "RG", "WG", "WB", "UR", "BG", "WR", "UG"]
CACHE = f"{ROOT}/data/cache/17lands_pairs_{SET}.json"

def get(colors=None):
    url = (f"https://www.17lands.com/api/card_data?expansion={SET}"
           f"&event_type=PremierDraft&time_period=ALL_TIME" + (f"&colors={colors}" if colors else ""))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 mtg-draft"})
    raw = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return raw["data"] if isinstance(raw, dict) and "data" in raw else raw

def load():
    if "--refresh" not in sys.argv and os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < 86400:
        return json.load(open(CACHE))
    out = {"ALL": get()}
    for p in PAIRS:
        time.sleep(2)
        out[p] = get(p)
    json.dump(out, open(CACHE, "w"))
    return out

raw = load()
allc = {c["name"]: c for c in raw["ALL"]}
D = {p: {c["name"]: c for c in raw[p]} for p in PAIRS}
iwd = lambda c: None if c.get("drawn_improvement_win_rate") is None else c["drawn_improvement_win_rate"] * 100
def se(c):
    a, b = c.get("ever_drawn_game_count") or 0, c.get("never_drawn_game_count") or 0
    return 100 * math.sqrt(.25 / a + .25 / b) if a >= 300 and b >= 300 else None

rows = []
for n, c in allc.items():
    if iwd(c) is None:
        continue
    for p in PAIRS:
        x = D[p].get(n)
        if not x or iwd(x) is None or (x.get("ever_drawn_game_count") or 0) < MIN or not se(x):
            continue
        d = iwd(x) - iwd(c)
        rows.append((d / se(x), d, n, c["color"], c["rarity"][0].upper(), p, iwd(x), iwd(c), x["ever_drawn_game_count"]))
rows.sort(key=lambda r: -r[0])
fmt = lambda r: f"  z{r[0]:+.1f}  {r[2][:30]:30} {r[3]:3} {r[4]}  {r[5]}: IWD {r[6]:+.1f} vs {r[7]:+.1f} set-wide  n={r[8]}"
print(f"{SET} — card IWD inside a pair vs set-wide (|z|>={ZCUT}, n>={MIN})\n\nOVER-PERFORMS")
print("\n".join(fmt(r) for r in rows if r[0] >= ZCUT))
print("\nUNDER-PERFORMS")
print("\n".join(fmt(r) for r in reversed(rows) if r[0] <= -ZCUT))

print("\nCOLOUR HALVES — game-weighted mean (in-pair IWD - set-wide IWD), mono-colour cards, n>=500")
for p in PAIRS:
    parts = []
    for col in p:
        num = den = 0
        for n, c in allc.items():
            x = D[p].get(n)
            if c["color"] != col or iwd(c) is None or not x or iwd(x) is None or (x.get("ever_drawn_game_count") or 0) < 500:
                continue
            g = x["ever_drawn_game_count"]; num += g * (iwd(x) - iwd(c)); den += g
        parts.append(f"{col} {num / den:+.2f}" if den else f"{col} -")
    print(f"  {p}  " + "   ".join(parts))

print(f"\nENGINE — top in-pair IWD, commons/uncommons, n>={MIN}")
for p in PAIRS:
    rs = sorted(((iwd(x), n) for n, x in D[p].items()
                 if iwd(x) is not None and (x.get("ever_drawn_game_count") or 0) >= MIN
                 and allc[n]["rarity"] in ("common", "uncommon")), reverse=True)
    print(f"  {p}  " + "; ".join(f"{n} {v:+.1f}" for v, n in rs[:8]))
