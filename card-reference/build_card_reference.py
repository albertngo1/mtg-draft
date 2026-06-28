#!/usr/bin/env python3
"""Build a single Markdown card reference for an MTG set: every card as a tile in a
3-per-row HTML grid, with image, 17Lands ratings, Draftsim grade, expert-guide notes,
and an AI take.

Sources (relative to the mtg-draft repo root):
  data/cache/17lands_<SET>_PremierDraft_1200d.json   image + 17Lands ratings
  grades/draftsim_<SET>.json                         Draftsim DS grade (0-5)
  draft-guides/{lords-of-limited,numot,limited-resources,limited-level-ups}/...  expert per-card notes
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
BULLET = re.compile(r"^\s*-\s*\[?\*\*(.+?)\*\*\]?(?:\([^)]*\))?\s*[—–:-]\s*(.+?)\s*$")
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

# (tile-label, full legend name, parsed-notes dict) — drives both the tiles and the legend
GUIDE_SRCS = [
    ("📘 LoL",   "📘 Lords of Limited",   parse_guide(f"{ROOT}/draft-guides/lords-of-limited/{SET}-draft-guide.md")),
    ("🎙 Numot", "🎙 NumotTheNummy",      parse_guide(f"{ROOT}/draft-guides/numot/{SET}.md")),
    ("🎧 LR",    "🎧 Limited Resources",  parse_guide(f"{ROOT}/draft-guides/limited-resources/{SET}.md")),
    ("🎓 LLU",   "🎓 Limited Level-Ups",  parse_guide(f"{ROOT}/draft-guides/limited-level-ups/{SET}.md")),
]

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


_all_alsa = [c["avg_seen"] for c in cards if c.get("avg_seen")]
_alsa_min = min(_all_alsa) if _all_alsa else 1.0
_alsa_max = max(_all_alsa) if _all_alsa else 8.0

def combined_score(c):
    play = c.get("play_rate") or 0.0
    alsa = c.get("avg_seen") or _alsa_max
    alsa_norm = 1.0 - (alsa - _alsa_min) / (_alsa_max - _alsa_min)
    return (play + alsa_norm) / 2

groups = {}
for c in cards:
    groups.setdefault(group_of(c), []).append(c)
for g in groups.values():
    g.sort(key=combined_score, reverse=True)

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
                 f'· ALSA {(c.get("avg_seen") or 0):.1f} · {GLABEL} {ds_grade(c)}</sub><br>')
    parts.append(f'<sub>OH {pct(c.get("opening_hand_win_rate"))} · GD {pct(c.get("drawn_win_rate"))} '
                 f'· Play {pct(c.get("play_rate"))}</sub><br>')
    # AI take
    take = ai.get(name)
    if take:
        parts.append(f'<br>🤖 <b>AI:</b> {esc(take)}<br>')
    # expert notes
    for label, _full, src in GUIDE_SRCS:
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
# legend lists only the guides that actually contributed notes for this set
_guide_legend = " · ".join(full for _lab, full, src in GUIDE_SRCS if src)
L.append("**Legend** — **GIH** = Games-in-Hand WR (primary) · **IWD** = Improvement When Drawn (pp) · "
         "**ALSA** = Avg Last Seen At (lower = earlier) · **OH/GD** = Opening-Hand / Drawn WR · "
         f"**Play** = play rate · **{GLABEL}** = {GDESC}.  "
         f"🤖 AI · {_guide_legend}.\n")
CAVEAT = {
    "SOS": "> SOS is a soup/Converge format — multicolor & Converge win-rates are inflated by 4-5c "
           "pilots. The AI take and guide notes decode which deck a number came from.\n",
    "MKM": "> MKM is a grindy 2-color guild-midrange format, so GIH WR transfers honestly (little soup "
           "inflation). Ratings are 2024 MKM PremierDraft historical data. White pairs (Boros best) sit "
           "on top; black is the weakest color.\n",
    "MSH": "> ⚠ EARLY DATA (updated 2026-06-27): MSH 17Lands data is filling in fast — **270 of 334 cards** "
           "now have a GIH WR off PremierDraft games, but the format is still young so numbers keep "
           "moving. Cards still lacking WR show blank stats; lean on the **CGB letter grade** + expert notes "
           "for those. Treat WR as a real-but-provisional signal, not gospel — re-pull as samples grow.\n",
    "BLB": "> BLB is a finished format (Aug-Sep 2024) — the 17Lands GIH WR is **mature and full-format**, and the "
           "expert notes are end-of-format retrospectives (LoL's '50 Takes' finale, LR's Sunset Show, Kenji's "
           "last BLB VODs), so this reference is settled, not provisional. Big caveat: it's a **typal/synergy "
           "format**, so GIH WR is archetype-conditional — a tribal 'false friend' (Carrot Cake is great in GW "
           "Rabbits, bad in RW Mice) reads average overall but swings hard by deck. The AI take + guide notes "
           "decode which tribe a number belongs to.\n",
}
L.append(CAVEAT.get(SET, ""))

# ---- archetype map (set-specific 10 color-pair guilds) -----------------------
ARCHETYPES = {
    "MSH": "### The 10 archetypes (color-pair guilds)\n\n"
           "MSH is a **slow, grindy, lightly-themed goodstuff** format — every pick below is read against the "
           "AI's read of which guild a card serves. Pairs are ranked by Limited Level-Ups' early-data read; "
           "no pair looked un-viable. The hybrid signpost is usually the higher pick.\n\n"
           "| # | Pair | Theme | Signposts |\n"
           "|---|------|-------|-----------|\n"
           "| 1 | **UB** | Connive / draw-two — smooth draws, grind card advantage (best in practice) | Kang, Temporal Tyrant · Ghost, Spectral Saboteur |\n"
           "| 2 | **GW** | Heroes-matter — go wide with ~91 heroes, low-effort payoffs | Black Panther, Vanguard · Spider-Man, To the Rescue |\n"
           "| 3 | **BR** | Villains-matter — auto-on (most black creatures are villains), push damage | Madame Hydra · Bullseye, Death Dealer |\n"
           "| 4 | **WU** | Teamwork — tap creatures to upgrade spells; wants a body-heavy build | Captain America, Living Legend · Spider-Woman, Secret Agent |\n"
           "| 5 | **RW** | Spells / prowess / tricks — the most aggressive pair | Thor Odinson · War Machine, Legacy of Iron |\n"
           "| 6 | **BG** | Graveyard — 2 creatures in yard (hit by trading); Killmonger is the linchpin | Killmonger, Scourge of Wakanda · Titania, Rugged Rumbler |\n"
           "| 7 | **RG** | Power-up / ramp — big bodies + +1/+1 mana sinks | Hulk, Gamma Goliath · Abomination, Terrifying Titan |\n"
           "| 8 | **WB** | Attack-alone — one operative, pile bonuses; small equipment sub-theme | Black Widow, Double Agent · U.S.Agent, John Walker |\n"
           "| 9 | **UR** | Artifacts — shallowest theme; evaluate each artifact on its own, don't force | Iron Man, Master of Machines · Speedball, New Warrior |\n"
           "| 10 | **GU** | +1/+1 counters — pile counters via power-up; weakest pair | Ant-Man, Colony Commander · Beast, Erudite Aerialist |\n\n"
           "**Removal benchmarks** (scarce + at a premium in this slow format): Lightning Strike (R), Dark Deed / "
           "Cruel Alliance (B), Web Up / Super Villain Lockup (W), Punishing Punch (G), Frozen in Ice (U). "
           "**Big-dummy rule:** expensive no-ETB vanilla creatures are traps; flyers break the format's board stalls.\n",
    "BLB": "### The 10 archetypes (color-pair tribes)\n\n"
           "BLB is a **typal/synergy** format — each color pair is an animal tribe with a narrow home. Think "
           "\"BG Food/Forage card,\" not \"green card.\" Ranked by Lords of Limited's end-of-format retrospective; "
           "the format **self-corrected** so all ten are draftable when open (blue pairs especially overperform "
           "for skilled drafters who read an empty lane). **Start green or black** — they branch into the most "
           "good pairs — and let pack 1 tell you the tribe.\n\n"
           "| # | Pair | Tribe / plan | Key cards |\n"
           "|---|------|--------------|-----------|\n"
           "| 1 | **BG** | Squirrels — Forage / Food / graveyard grind (deepest, highest floor) | Cache Grab · Scavenger's Talent · Vinereap Mentor |\n"
           "| 2 | **GW** | Rabbits — go-wide Offspring / Food tokens, curve out fast | Carrot Cake · Intrepid Rabbit · Treeguard Duo |\n"
           "| 3 | **GU** | Frogs — blink / bounce to re-trigger ETBs, grind value (LSV's favorite) | Pond Prophet · Sunshower Druid · Three Tree Scribe |\n"
           "| 4 | **BR** | Lizards — cheap aggressive bodies + burn / damage payoffs | Scales of Shale · Fireglass Mentor · Hired Claw |\n"
           "| 5 | **UB** | Rats — go-wide + discard / Threshold (under-drafted sleeper) | Tidecaller Mentor · Mind Drill Assailant · Mindwhisker |\n"
           "| 6 | **WB** | Bats — lifegain triggers + drain attrition (branches well) | Starscape Cleric · Moonrise Cleric · Valley Rotcaller |\n"
           "| 7 | **RG** | Raccoons — Expend / Forage / Food goodstuff (weakest, generic) | Wandertale Mentor · Bakersbane Duo · Junkblade Bruiser |\n"
           "| 8 | **RW** | Mice — Valiant / go-wide aggro (contested; Food stalls it) | Heartfire Hero · Manifold Mouse · Emberheart Challenger |\n"
           "| 9 | **UR** | Otters — spells / prowess / tempo (low floor, expert-only) | Stormcatch Mentor · Alania's Pathmaker · Stormsplitter |\n"
           "| 10 | **WU** | Birds — evasive flyers + counters (weak avg, elite ceiling when open) | Jackdaw Savior · Seedpod Squire · Plumecreed Escort |\n\n"
           "**Format principles:** medium-to-slow despite looking fast (games hit turns 10-14; whoever's buried in "
           "card advantage loses). **Food + lifegain are disproportionately strong** (buy turns for synergy to come "
           "online). Want a turn-2 play; better drafters run a U-shaped curve (lots of 1-2s + 5-6s). Removal is "
           "scarce — prioritize cheap instant-speed (Savor, Nocturnal Hunger, Sonar Strike, Scales of Shale). "
           "**Talents are the best build-arounds** — open one, jam it. The Villages (type dual lands) are a trap.\n",
}
L.append(ARCHETYPES.get(SET, ""))
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

matched = sum(1 for c in cards if any(src.get(norm(c["name"])) for _l, _f, src in GUIDE_SRCS))
print(f"wrote {OUT}")
print(f"cards: {total} | AI takes: {sum(1 for c in cards if c['name'] in ai)} "
      f"| >=1 guide note: {matched} | DS grades: {sum(1 for c in cards if norm(c['name']) in ds)} "
      f"| {COLS} per row")
