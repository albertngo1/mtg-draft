"""Build a 17Lands-shaped card list for a set from Scryfall, for use BEFORE 17Lands has data.

Usage:  python3 card-reference/scryfall_cardlist.py HOB

build_card_reference.py loads its entire card list from
data/cache/17lands_<SET>_PremierDraft_1200d.json, so a set with no 17Lands
export cannot be built at all. This writes that file from Scryfall with every
stat field null, so the grid renders with blank WR columns instead of failing.
Re-run the real 17Lands fetch and rebuild once data exists; nothing else changes.

Emits data/cache/17lands_<SET>_PremierDraft_1200d.json with every stat field set to None
so build_card_reference.py renders the grid with empty WR columns rather than failing.
"""
import json, sys, time, urllib.request, pathlib

SET = sys.argv[1] if len(sys.argv) > 1 else "HOB"
ROOT = pathlib.Path(__file__).resolve().parent if "__file__" in globals() else pathlib.Path(".")
OUT = pathlib.Path.home() / ("public-src/mtg-draft/data/cache/17lands_%s_PremierDraft_1200d.json" % SET)

def get(u):
    r = urllib.request.Request(u, headers={"User-Agent": "mtg-draft/1.0", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=30))

cards, url = [], "https://api.scryfall.com/cards/search?q=set%%3A%s&unique=cards&order=set" % SET.lower()
while url:
    d = get(url); cards += d["data"]; url = d.get("next_page"); time.sleep(0.12)

STATS = ["avg_pick","avg_seen","drawn_game_count","drawn_improvement_win_rate","drawn_win_rate",
         "ever_drawn_game_count","ever_drawn_win_rate","game_count","never_drawn_game_count",
         "never_drawn_win_rate","opening_hand_game_count","opening_hand_win_rate","pick_count",
         "play_rate","pool_count","seen_count","win_rate"]

out = []
for c in cards:
    if "Basic Land" in c["type_line"]:
        continue
    faces = c.get("card_faces") or []
    img  = (c.get("image_uris") or (faces[0].get("image_uris") if faces else {}) or {}).get("large", "")
    back = (faces[1].get("image_uris", {}).get("large", "") if len(faces) > 1 else "")
    rec = {
        "name": c["name"], "rarity": c["rarity"],
        "color": "".join(c.get("color_identity") or []) or "",
        "types": [c["type_line"].split(" // ")[0]],
        "layout": c.get("layout", "standard"),
        "mtga_id": (c.get("arena_id") or c["collector_number"]),
        "url": img, "url_back": back,
    }
    rec.update({k: None for k in STATS})
    out.append(rec)



def write_by_name(SET, cards):
    """Also emit a name-keyed oracle dump for gen_ai_takes.py.

    Needed while Scryfall still reports arena_id: null for a new set — without it the
    mtga_id join in prep returns nothing and every take gets written blind."""
    import json as _json
    out = {}
    for c in cards:
        faces = c.get("card_faces") or []
        text = c.get("oracle_text")
        if text is None:
            text = " // ".join(f.get("oracle_text", "") for f in faces)
        cost = c.get("mana_cost") or " // ".join(f.get("mana_cost", "") for f in faces)
        out[c["name"]] = {
            "mana": cost, "type_line": c["type_line"], "text": text,
            "pt": (f'{c["power"]}/{c["toughness"]}' if c.get("power") else ""),
        }
    dest = pathlib.Path.home() / ("public-src/mtg-draft/data/cache/scryfall_byname_%s.json" % SET)
    _json.dump(out, open(dest, "w"), ensure_ascii=False)
    print("wrote %s — %d cards (name-keyed oracle text)" % (dest, len(out)))


# Refuse to overwrite a cache that already carries real 17Lands stats. This script exists
# only to scaffold a set BEFORE 17Lands has data; running it afterwards would silently
# replace live win rates with nulls. Pass --force to override, or --by-name-only to just
# refresh the oracle dump.
if OUT.exists() and "--force" not in sys.argv:
    import json as _j
    try:
        existing = _j.load(open(OUT))
        if any(c.get("ever_drawn_win_rate") is not None for c in existing):
            if "--by-name-only" in sys.argv:
                write_by_name(SET, cards)
                sys.exit(0)
            sys.exit("refusing to overwrite %s — it has real 17Lands stats.\n"
                     "Use --by-name-only to refresh just the oracle dump, or --force to overwrite." % OUT)
    except Exception:
        pass

OUT.parent.mkdir(parents=True, exist_ok=True)
json.dump(out, open(OUT, "w"))
write_by_name(SET, cards)
print("wrote %s — %d cards (stats null; 17Lands has no %s data yet)" % (OUT, len(out), SET))
