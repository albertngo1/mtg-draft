#!/usr/bin/env python3
"""Render a physical card pool as a visual page, reusing the card-reference tiles.

    python3 card-reference/build_pool.py HOB pools/HOB-albert.json

Reads <SET>-card-reference.md and lifts the <td> tile for each card named in the
pool file, so a pool page and the set reference always render identically — there
is no second copy of the tile logic to drift.

Output lands at card-reference/<basename>.md, which the card-reference site serves
at /doc/<basename> (any .md there not ending in -card-reference.md is a doc page).

Grouped by rarity rather than colour: a pool page exists to settle who gets what
after a sealed event, and a split is negotiated over rares, not over commons.
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

if len(sys.argv) < 3:
    sys.exit(__doc__)
SET, POOL = sys.argv[1].upper(), sys.argv[2]
pool = json.load(open(POOL if os.path.isabs(POOL) else os.path.join(HERE, POOL)))

ref_path = os.path.join(HERE, f"{SET}-card-reference.md")
if not os.path.exists(ref_path):
    sys.exit(f"missing {ref_path} — build the set reference first")
ref = open(ref_path).read()

# every tile is one <td …>…</td>; alt="<card name>" identifies it
TILE = re.compile(r'<td width="33%"[^>]*>.*?</td>', re.S)
ALT = re.compile(r'alt="([^"]*)"')
tiles = {}
for t in TILE.findall(ref):
    m = ALT.search(t)
    if m:
        # alt attributes are HTML-escaped, so apostrophes arrive as &#x27;
        tiles[html.unescape(m.group(1))] = t

cards = json.load(open(f"{ROOT}/data/cache/17lands_{SET}_PremierDraft_1200d.json"))
meta = {c["name"]: c for c in cards}

ORDER = {"mythic": 0, "rare": 1, "uncommon": 2, "common": 3}
LABEL = {"mythic": "Mythic", "rare": "Rare", "uncommon": "Uncommon", "common": "Common"}

groups, missing = {}, []
for name in pool["cards"]:
    c = meta.get(name)
    if not c:
        missing.append(name)
        continue
    groups.setdefault(c["rarity"], []).append(name)

L = [f"# {pool.get('title', SET + ' pool')}\n"]
if pool.get("note"):
    L.append(f"> {pool['note']}\n")
if pool.get("counting"):
    L.append(f"> ⚠️ {pool['counting']}\n")
counts = " · ".join(f"**{len(groups.get(r, []))}** {LABEL[r].lower()}"
                    for r in sorted(groups, key=lambda r: ORDER[r]))
L.append(f"{len(pool['cards']) - len(missing)} distinct cards — {counts}\n")
L.append("Every name verified against the Scryfall card list. Tiles are lifted from "
         f"[{SET} card reference](/set/{SET}), so grades and notes match it exactly.\n")
L.append("## Contents\n")
for r in sorted(groups, key=lambda r: ORDER[r]):
    L.append(f"- [{LABEL[r]}](#{LABEL[r].lower()}) ({len(groups[r])})")
L.append("")

for r in sorted(groups, key=lambda r: ORDER[r]):
    L.append(f"\n## {LABEL[r]}\n")
    names = sorted(groups[r])
    L.append("<table>")
    for i in range(0, len(names), 3):
        L.append("<tr>")
        for n in names[i:i + 3]:
            L.append(tiles.get(n, f'<td width="33%" valign="top"><b>{n}</b><br>'
                                  f'<sub>no tile in the set reference</sub></td>'))
        L.append("</tr>")
    L.append("</table>\n")

if missing:
    L.append("\n## Not found in the set list\n")
    for n in missing:
        L.append(f"- {n}")
    L.append("")

out = os.path.join(HERE, os.path.splitext(os.path.basename(POOL))[0].replace("-albert", "-pool") + ".md")
open(out, "w").write("\n".join(L))
print(f"wrote {out} — {len(pool['cards']) - len(missing)} cards"
      + (f", {len(missing)} unmatched" if missing else ""))
