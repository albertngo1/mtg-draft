#!/usr/bin/env python3
"""Build a single Markdown card reference for an MTG set: every card as a tile in a
3-per-row HTML grid, with image, 17Lands ratings, Draftsim grade, expert-guide notes,
and an AI take.

Sources (relative to the mtg-draft repo root):
  data/cache/17lands_<SET>_PremierDraft_1200d.json   image + 17Lands ratings
  grades/draftsim_<SET>.json                         Draftsim DS grade (0-5)
  draft-guides/{lords-of-limited,numot,limited-resources}/...  expert per-card notes
  card-reference/ai_takes_<SET>.json                 pre-generated AI takes (this folder)

Usage: python3 build_card_reference.py [SET]   (default SET=SOS)
Output: card-reference/<SET>-card-reference.md
"""
import json, os, re, html, sys

SET = (sys.argv[1] if len(sys.argv) > 1 else "SOS").upper()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT  = os.path.join(HERE, f"{SET}-card-reference.md")
COLS = 3  # cards per row

# ---- load 17Lands (primary: image + ratings) --------------------------------
cards = json.load(open(f"{ROOT}/data/cache/17lands_{SET}_PremierDraft_1200d.json"))

# ---- reviewer grades: Draftsim (DS, numeric /5) or CardGameBase (CGB, letters)
def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.split("//")[0].lower())

ds, GLABEL, GDESC = {}, "", ""
for src, label, desc in (("draftsim", "DS", "Draftsim grade /5"),
                         ("cardgamebase", "CGB", "CardGameBase letter grade")):
    p = f"{ROOT}/grades/{src}_{SET}.json"
    if os.path.exists(p):
        ds = {norm(k): v for k, v in json.load(open(p)).items() if not k.startswith("_")}
        GLABEL, GDESC = label, desc
        break

# ---- AI takes (pre-generated, stored alongside this script) -----------------
ai = json.load(open(f"{HERE}/ai_takes_{SET}.json"))

# ---- guide notes ------------------------------------------------------------
BULLET = re.compile(r"^\s*-\s*\[?\*\*(.+?)\*\*\]?(?:\([^)]*\))?\s*[—–-]\s*(.+?)\s*$")
TABLE  = re.compile(r"^\s*\|\s*\[?\*\*(.+?)\*\*\]?[^|]*\|\s*(.+?)\s*\|")
def parse_guide(path):
    notes = {}
    if not os.path.exists(path):
        return notes
    insec = False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            insec = ("card tip" in line.lower()) or ("card note" in line.lower())
            continue
        if not insec:
            continue
        m = BULLET.match(line) or TABLE.match(line)
        if not m:
            continue
        raw, note = m.group(1), m.group(2).strip()
        names = [raw.split("(")[0]] + re.findall(r"\(([^)]+)\)", raw)
        if not note:
            continue
        for nm in names:
            k = norm(nm)
            if k and k not in notes:
                notes[k] = note
    return notes

lol   = parse_guide(f"{ROOT}/draft-guides/lords-of-limited/{SET}-draft-guide.md")
numot = parse_guide(f"{ROOT}/draft-guides/numot/{SET}.md")
lr    = parse_guide(f"{ROOT}/draft-guides/limited-resources/{SET}.md")

# ---- grouping / ordering ----------------------------------------------------
GROUP_KEY = {"W":"1-White","U":"2-Blue","B":"3-Black","R":"4-Red","G":"5-Green"}
GROUP_TITLE = {"1-White":"White","2-Blue":"Blue","3-Black":"Black","4-Red":"Red",
               "5-Green":"Green","6-Multicolor":"Multicolor","7-Colorless":"Colorless","8-Lands":"Lands"}
def group_of(c):
    if any("Land" in t for t in c["types"]):
        return "8-Lands"
    col = c["color"]
    if col == "":   return "7-Colorless"
    if len(col)==1: return GROUP_KEY[col]
    return "6-Multicolor"

def gih(c):  return c.get("ever_drawn_win_rate") or 0.0
def pct(x):  return f"{x*100:.1f}%" if x else "—"
def signed(x): return f"{x*100:+.1f}" if x else "—"
def ds_grade(c):
    v = ds.get(norm(c["name"])); return f"{v}" if v is not None else "—"

groups = {}
for c in cards:
    groups.setdefault(group_of(c), []).append(c)
for g in groups.values():
    g.sort(key=gih, reverse=True)

def esc(s): return html.escape(str(s))

def cell(c):
    """one card tile as an HTML <td>."""
    name, k = c["name"], norm(c["name"])
    col = c["color"] or "C"
    badge = f'{esc(col)} · {c["rarity"].capitalize()}'
    parts = [f'<td width="33%" valign="top">']
    if c.get("url"):
        parts.append(f'<img src="{c["url"]}" width="240" alt="{esc(name)}"><br>')
    parts.append(f'<b>{esc(name)}</b><br><sub>{badge}</sub><br>')
    # compact stat lines
    parts.append(f'<sub>GIH <b>{pct(gih(c))}</b> · IWD {signed(c.get("drawn_improvement_win_rate"))} '
                 f'· ALSA {c.get("avg_seen",0):.1f} · {GLABEL} {ds_grade(c)}</sub><br>')
    parts.append(f'<sub>OH {pct(c.get("opening_hand_win_rate"))} · GD {pct(c.get("drawn_win_rate"))} '
                 f'· Play {pct(c.get("play_rate"))}</sub><br>')
    # AI take
    take = ai.get(name)
    if take:
        parts.append(f'<br>🤖 <b>AI:</b> {esc(take)}<br>')
    # expert notes
    for label, src in (("📘 LoL", lol), ("🎙 Numot", numot), ("🎧 LR", lr)):
        note = src.get(k)
        if note:
            parts.append(f'<br><sub><b>{label}:</b> {esc(note)}</sub>')
    parts.append('</td>')
    return "".join(parts)

# ---- emit -------------------------------------------------------------------
total = len(cards)
L = []
L.append(f"# {SET} — Full Card Reference (Visual Grid)\n")
L.append(f"*Every draftable {SET} card ({total} total) as a tile: image, 17Lands ratings, "
         "Draftsim grade, expert-guide notes, and an AI take. "
         "Ratings: 17Lands PremierDraft (1200-day sample). Generated by `build_card_reference.py`.*\n")
L.append("**Legend** — **GIH** = Games-in-Hand WR (primary) · **IWD** = Improvement When Drawn (pp) · "
         "**ALSA** = Avg Last Seen At (lower = earlier) · **OH/GD** = Opening-Hand / Drawn WR · "
         f"**Play** = play rate · **{GLABEL}** = {GDESC}.  "
         "🤖 AI · 📘 Lords of Limited · 🎙 NumotTheNummy · 🎧 Limited Resources.\n")
CAVEAT = {
    "SOS": "> SOS is a soup/Converge format — multicolor & Converge win-rates are inflated by 4-5c "
           "pilots. The AI take and guide notes decode which deck a number came from.\n",
    "MKM": "> MKM is a grindy 2-color guild-midrange format, so GIH WR transfers honestly (little soup "
           "inflation). Ratings are 2024 MKM PremierDraft historical data. White pairs (Boros best) sit "
           "on top; black is the weakest color.\n",
}
L.append(CAVEAT.get(SET, ""))
L.append("## Contents\n")
for key in sorted(groups):
    t = GROUP_TITLE[key]
    L.append(f"- [{t}](#{t.lower()}) ({len(groups[key])})")
L.append("")

for key in sorted(groups):
    t = GROUP_TITLE[key]
    L.append(f"\n## {t}\n")
    g = groups[key]
    L.append("<table>")
    for i in range(0, len(g), COLS):
        L.append("<tr>")
        for c in g[i:i+COLS]:
            L.append(cell(c))
        L.append("</tr>")
    L.append("</table>\n")

open(OUT, "w", encoding="utf-8").write("\n".join(L))

matched = sum(1 for c in cards if any(s.get(norm(c["name"])) for s in (lol, numot, lr)))
print(f"wrote {OUT}")
print(f"cards: {total} | AI takes: {sum(1 for c in cards if c['name'] in ai)} "
      f"| >=1 guide note: {matched} | DS grades: {sum(1 for c in cards if norm(c['name']) in ds)} "
      f"| {COLS} per row")
