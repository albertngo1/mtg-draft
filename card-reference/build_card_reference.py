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
import json, os, re, html, sys, time, base64, urllib.request

# Image modes (default = hotlink cards.scryfall.io, fine on GitHub where images are proxied):
#   --local-images  download each image once into data/card-images/<SET>/ and reference it by
#                   relative path; writes <SET>-card-reference.local.md.
#   --embed-images  inline every image as a base64 data: URI so the .md is ONE self-contained file
#                   (no external folder, works offline anywhere); writes <SET>-card-reference.embedded.md.
# Both exist because VS Code's markdown preview pre-loads the whole doc at once (it ignores
# loading="lazy"), bursting ~300 concurrent image requests. For a brand-new set whose images aren't
# yet warm at Scryfall's CDN edges, that burst 404s a large fraction, showing broken "?" boxes.
# Not hotlinking (local or embedded) removes every remote request, so the preview is reliable.
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
LOCAL_IMAGES = "--local-images" in sys.argv[1:]
EMBED_IMAGES = "--embed-images" in sys.argv[1:]
SET = (ARGS[0] if ARGS else "SOS").upper()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_suffix = ".embedded.md" if EMBED_IMAGES else ".local.md" if LOCAL_IMAGES else ".md"
OUT  = os.path.join(HERE, f"{SET}-card-reference{_suffix}")
IMGDIR = os.path.join(ROOT, "data", "card-images", SET)  # download cache (gitignored via data/)
COLS = 3  # cards per row

# Optional alternate image host, keyed by mtga_id. Committed as card-reference/alt_images_<SET>.json.
# Used for a brand-new set whose images are cold at Scryfall's CDN edge (so VS Code's ~300-request
# preview burst 404s half of them): ECL points at TCGplayer's CDN, which is fully warm and serves the
# burst at 100%. This keeps the default committed .md a single remote-hotlink file (no local folder,
# no 34MB embed) that loads reliably in BOTH VS Code and GitHub.
ALT_IMAGES = {}
_alt_path = os.path.join(HERE, f"alt_images_{SET}.json")
if os.path.exists(_alt_path):
    with open(_alt_path) as _f:
        ALT_IMAGES = json.load(_f)

def _local_path(c):
    return os.path.join(IMGDIR, f'{c.get("mtga_id") or norm(c["name"])}.jpg')

def _img_bytes(c):
    """Return the card image bytes, or None. Reuses data/card-images/<SET>/ as a download cache
    (so --embed-images after --local-images is instant); otherwise fetches Scryfall's `normal`
    size (~60-90KB, sharp at 240px) and caches it. Retries because a brand-new set's images can be
    cold at Scryfall's edge and 404 on first hit, succeeding once the edge fills."""
    dest = _local_path(c)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        with open(dest, "rb") as f:
            return f.read()
    url = c["url"].replace("/large/", "/normal/")
    req = urllib.request.Request(url, headers={"User-Agent": "mtg-draft-card-reference"})
    for attempt in range(6):
        try:
            data = urllib.request.urlopen(req, timeout=30).read()
            if data:
                os.makedirs(IMGDIR, exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(data)
                return data
        except Exception:
            pass
        time.sleep(0.4 * (attempt + 1))  # back off; cold-edge 404s clear once the fill completes
    return None

def predownload(cards):
    """Pre-fetch every image with a small thread pool BEFORE rendering. 6 workers stays under the
    per-host burst that makes Scryfall 404 a new set's cold images, while being ~6x faster than
    one-at-a-time. Returns the count that failed after all retries."""
    import concurrent.futures
    failed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for data in ex.map(_img_bytes, cards):
            if not data:
                failed += 1
    return failed

def img_src(c):
    """Default: remote Scryfall URL. --local-images: relative path. --embed-images: base64 data URI.
    Any per-image failure falls back to the remote URL."""
    if EMBED_IMAGES:
        data = _img_bytes(c)
        if data:
            return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")
        return c["url"]
    if LOCAL_IMAGES:
        dest = _local_path(c)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            return os.path.relpath(dest, HERE)  # relative to the .md in card-reference/
    # default remote: prefer the alternate host (TCGplayer for ECL) over Scryfall when mapped
    return ALT_IMAGES.get(str(c.get("mtga_id"))) or c["url"]

# ---- load 17Lands (primary: image + ratings) --------------------------------
cards = json.load(open(f"{ROOT}/data/cache/17lands_{SET}_PremierDraft_1200d.json"))

# ---- reviewer grades: Draftsim (DS, numeric /5) or CardGameBase (CGB, letters)
def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.split("//")[0].lower())

# A set can carry several reviewer-grade files; show every one that exists rather
# than only the first, since they differ in both coverage and authority.
GRADE_SOURCES = []          # [(label, {norm_name: grade}), ...] in display order
ds, GLABEL, GDESC = {}, "", ""
for src, label, desc in (("limitedresources", "LR", "Limited Resources letter grade"),
                         ("cardgamebase", "CGB", "CardGameBase letter grade"),
                         ("draftsim", "DS", "Draftsim grade /5")):
    path = f"{ROOT}/grades/{src}_{SET}.json"
    if os.path.exists(path):
        table = {norm(k): v for k, v in json.load(open(path)).items() if not k.startswith("_")}
        GRADE_SOURCES.append((label, table, desc))
        if not ds:                       # first one also feeds the legacy single-grade path
            ds, GLABEL, GDESC = table, label, desc

# ---- AI takes (pre-generated, stored alongside this script) -----------------
ai = json.load(open(f"{HERE}/ai_takes_{SET}.json"))

# ---- guide notes ------------------------------------------------------------
# Card name in bold, optionally linked, optionally followed by one-or-more parentheticals
# (a scryfall link AND a mana/reminder gloss — LoL's `[**Card**](url) (4WW: …) — note` form),
# then the note. The separator is optional so Numot's `**Card:** note` (colon inside the bold)
# also parses; the `:?` lets the bold swallow that trailing colon.
BULLET = re.compile(r"^\s*-\s*\[?\*\*(.+?):?\*\*\]?(?:\s*\([^)]*\))*\s*[—–:-]?\s*(.+?)\s*$")
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
def all_grades(c):
    """Every reviewer grade this set has, e.g. ' · LR B+ · CGB A-'. Sources that
    don't cover a card are skipped rather than printed as a dash."""
    out = []
    for label, table, _ in GRADE_SOURCES:
        g = table.get(norm(c["name"]))
        if g:
            out.append(f"{label} {g}")
    return (" · " + " · ".join(out)) if out else ""


def ds_grade(c):
    v = ds.get(norm(c["name"])); return f"{v}" if v is not None else "—"


def play_score(c):
    return c.get("play_rate") or 0.0


# Per-set ordering inside each colour group. Default is play rate alone.
# "alsa_play" ranks by ALSA and play rate together, which is the better signal for a
# young set: ALSA and play rate are populated from every draft, while GIH WR needs
# games *won or lost with the card in hand* and so lags badly early on.
SORT = {"HOB": "alsa_play"}


def order_group(g):
    if SORT.get(SET) != "alsa_play":
        g.sort(key=play_score, reverse=True)
        return
    # Rank-average: scale-free, so no normalisation constants to tune, and a card
    # missing one metric still sorts sensibly on the other. ALSA is "average last seen
    # at", so LOWER is better (picked earlier); play rate is higher-is-better.
    by_alsa = sorted(g, key=lambda c: (c.get("avg_seen") is None, c.get("avg_seen") or 0))
    by_play = sorted(g, key=lambda c: -(c.get("play_rate") or 0))
    r_alsa = {id(c): i for i, c in enumerate(by_alsa)}
    r_play = {id(c): i for i, c in enumerate(by_play)}
    g.sort(key=lambda c: r_alsa[id(c)] + r_play[id(c)])


groups = {}
for c in cards:
    groups.setdefault(group_of(c), []).append(c)
for g in groups.values():
    order_group(g)

def esc(s): return html.escape(str(s))

def cell(c):
    """one card tile as an HTML <td>."""
    name, k = c["name"], norm(c["name"])
    col = c["color"] or "C"
    badge = f'{esc(col)} · {c["rarity"].capitalize()}'
    parts = [f'<td width="33%" valign="top">']
    if c.get("url"):
        # loading="lazy" + decoding="async": these references hold 270-340 images; without
        # lazy-loading every <img> fires at once when the file opens, blowing past the browser's
        # per-host connection cap and Scryfall's burst throttle, so some images time out and show
        # broken. Lazy-loading requests them only as they scroll into view.
        parts.append(f'<img src="{esc(img_src(c))}" width="240" alt="{esc(name)}" '
                     f'loading="lazy" decoding="async"><br>')
    parts.append(f'<b>{esc(name)}</b><br><sub>{badge}</sub><br>')
    # compact stat lines
    parts.append(f'<sub>GIH <b>{pct(gih(c))}</b> · IWD {signed(c.get("drawn_improvement_win_rate"))} '
                 f'· ALSA {f"{c["avg_seen"]:.1f}" if c.get("avg_seen") else "—"}{all_grades(c)}</sub><br>')
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

# ---- pre-download images (under --local-images / --embed-images) -------------
if LOCAL_IMAGES or EMBED_IMAGES:
    _how = "embedding" if EMBED_IMAGES else "downloading"
    print(f"  {_how} {len(cards)} {SET} images (6 workers, normal size)...")
    _failed = predownload(cards)
    print(f"  images ready: {len(cards) - _failed}/{len(cards)}"
          + (f"  ({_failed} fell back to remote URL)" if _failed else ""))

# ---- emit -------------------------------------------------------------------
total = len(cards)
L = []
L.append(f"# {SET} — Full Card Reference (Visual Grid)\n")
# grade clause is omitted entirely for sets with no reviewer-grade file (e.g. ECL),
# otherwise the intro/legend render a stray ", ," / empty "**** = ." artifact.
_grade_intro = f"{GDESC}, " if GDESC else ""
L.append(f"*Every draftable {SET} card ({total} total) as a tile: image, 17Lands ratings, "
         f"{_grade_intro}expert-guide notes, and an AI take. "
         "Ratings: 17Lands PremierDraft (1200-day sample). Generated by `build_card_reference.py`.*\n")
# legend lists only the guides that actually contributed notes for this set
_guide_legend = " · ".join(full for _lab, full, src in GUIDE_SRCS if src)
_grade_legend = "".join(f" · **{l}** = {d}" for l, _, d in GRADE_SOURCES)
L.append("**Legend** — **GIH** = Games-in-Hand WR (primary) · **IWD** = Improvement When Drawn (pp) · "
         "**ALSA** = Avg Last Seen At (lower = earlier) · **OH/GD** = Opening-Hand / Drawn WR · "
         f"**Play** = play rate{_grade_legend}.  "
         f"🤖 AI · {_guide_legend}.\n")
CAVEAT = {
    "HOB": "> **Settled data.** HOB hit Arena on **2026-08-11**; these numbers are from **6,001,733 PremierDraft games** as of **2026-08-19**, with **179 of 188 cards** carrying a GIH WR. Evaluations have converged — the median per-card GIH WR move over the previous two days was **0.21pp** and the largest was 1.0pp, so treat this as close to final. The 9 cards without a win rate are genuinely unplayed rather than merely unmeasured. Two reviewer-grade sources render side by side: **LR** (Limited Resources 865 + 866, all 188) and **CGB** (CardGameBase, all 188).\n"
           ">\n"
           "> Removal cannot kill small creatures (no Shock, no Stab), so **two-drops are safe** and curve-out plans are rewarded. Damage-based removal caps at 5, making **6-toughness creatures near-unanswerable** at common. See the **Format brief** below for the archetype reads, gameplay rules and traps distilled from all four expert guides.\n",
    "SOS": "> SOS is a soup/Converge format — multicolor & Converge win-rates are inflated by 4-5c "
           "pilots. The AI take and guide notes decode which deck a number came from.\n",
    "MKM": "> MKM is a grindy 2-color guild-midrange format, so GIH WR transfers honestly (little soup "
           "inflation). Ratings are 2024 MKM PremierDraft historical data. White pairs (Boros best) sit "
           "on top; black is the weakest color.\n",
    "MSH": "> MSH 17Lands data is now mature (updated 2026-07-23): **285 of 334 cards** have a GIH WR off "
           "~15.2M PremierDraft games, with QuickDraft (246 cards / ~2.1M games) and Sealed (254 cards / ~1.4M "
           "games) both live. Cards still lacking WR show blank stats; lean on the **CGB letter grade** + "
           "expert notes for those. WR is now a settled signal.\n",
    "ECL": "> ECL (Lorwyn Eclipsed) is a **tribal-synergy, midrange-to-grindy** format that plays slower than "
           "it looks — two-drops get blanked by high-toughness bodies and games often start on turn three. "
           "The 17Lands GIH WR is mature and full (**273 of 288 cards** off ~22.2M PremierDraft games). Big "
           "caveats: GIH WR **underrates efficient removal** (Cinder Strike doesn't win by being drawn) and "
           "**overrates tribal/blight/Vivid payoffs** (their number comes from the built-around deck) — the AI "
           "take + guide notes decode which deck a number belongs to. No reviewer-grade file exists for ECL, so "
           "WR + notes carry the read. **Five toughness** is the magic number (dodges Blight Rot, Seer, and "
           "Cinder Strike-on-blight).\n",
    "BLB": "> BLB is a finished format (Aug-Sep 2024) — the 17Lands GIH WR is **mature and full-format**, and the "
           "expert notes are end-of-format retrospectives (LoL's '50 Takes' finale, LR's Sunset Show, Kenji's "
           "last BLB VODs), so this reference is settled, not provisional. Big caveat: it's a **typal/synergy "
           "format**, so GIH WR is archetype-conditional — a tribal 'false friend' (Carrot Cake is great in GW "
           "Rabbits, bad in RW Mice) reads average overall but swings hard by deck. The AI take + guide notes "
           "decode which tribe a number belongs to.\n",
    "DFT": "> DFT (Aetherdrift) is the vehicles set that drove **under the speed limit** — despite the racing "
           "theme it's one of the **slower** recent formats, so plan for the long game and don't overvalue vanilla "
           "two-mana 2/2s (a good two-drop wants 3 power OR 3 toughness; 4 toughness is the magic number). The "
           "17Lands GIH WR is a finished-format signal (Feb-Mar 2025) and CGB letter grades are pre-data theory — "
           "trust live WR on conflict. **Color order at common: Green ≥ Black > Red = White > Blue**, but blue's "
           "*uncommons* are elite, so blue is a strong support color. GIH WR **overrates big green fatties/payoffs** "
           "(their number comes from the ramp deck) and **underrates cheap removal** — the AI take + guide notes "
           "decode which deck a number belongs to.\n",
    "OTJ": "> OTJ (Outlaws of Thunder Junction) is a **midrange, bombs-and-removal** format that plays a hair faster "
           "than it looks — draft the best bomb you open, then prioritize clean (ideally exile) removal, since the set "
           "is bomby and recursion is everywhere. Ratings are finished-format 2024 PremierDraft data (**364 of 376 "
           "cards** have a GIH WR); CGB letter grades are pre-data theory — trust live WR on conflict. **Green is the "
           "best color and GW mounts the best deck; blue is underrated/open** (uncommons wheel to pick 6+); **red is "
           "weakest.** GIH WR **inflates** multicolor good-stuff + build-around payoffs (Railway Brawler, Marchesa, "
           "crime engines) and **underrates** efficient removal (Throw from the Saddle, Desert's Due) — the AI take + "
           "guide notes decode which deck a number belongs to. **The Big Score (OTP) bonus-sheet reprints** appear one "
           "per pack; evaluate them on raw power.\n",
    "DSK": "> DSK (Duskmourn: House of Horror) is a **graveyard-matters midrange** format that plays slower than "
           "it looks — five- and six-drop bomb uncommons are real P1P1s, and the engine pairs dominate once they "
           "\"turn on.\" The three overlapping axes are **Delirium** (4+ card types in yard), **Manifest Dread**, and "
           "**Eerie** (enchantments/rooms). The 17Lands GIH WR is a finished-format signal (Sep-Oct 2024; **272 of 281 "
           "cards** have one); CGB letter grades are pre-data theory — trust live WR on conflict. **Color order: Green > "
           "Black >> Blue > White > Red** (green is busted at common AND uncommon; blue has weak commons but elite "
           "uncommons, so late blue uncommons = open). GIH WR **overrates synergy/build-around payoffs** (delirium "
           "fatties, reanimate targets, eerie/room engines post the built-around deck's number) and **underrates cheap "
           "exile removal** (Scorching Dragonfire, Nowhere to Run, Sheltered by Ghosts) — the AI take + guide notes "
           "decode which deck a number belongs to. **Four toughness is the magic number** (dodges the two premier "
           "damage-removal spells), and **exile/tuck > kill** since feeding graveyards helps your opponents.\n",
}
L.append("> **Ordering:** cards within each colour are ranked by a combined **ALSA + play-rate** score "
         "(rank-average of the two), not by GIH WR — ALSA and play rate are populated from every draft, "
         "while GIH WR lags on a new set.\n" if SORT.get(SET) == "alsa_play" else "")
L.append(CAVEAT.get(SET, ""))

# ---- archetype map (set-specific 10 color-pair guilds) -----------------------
ARCHETYPES = {
    "HOB": "**Archetype win rates** (17Lands PremierDraft, 227,771 decks, 2026-08-01 → 08-19):\n\n"
           "| WR | Games | Pair | Plan | Signposts |\n|---|---|---|---|---|\n"
           "| **57.4%** | 67.3k | **BR** | Rakdos Goblins — amass one huge Army, sacrifice for value; best removal and the deepest colours. Also the most-played deck by a wide margin. Post-play read: it is a **kill-you deck, not a sacrifice-attrition deck** | Bolg of the North · Goblin Plate Mail · Fearsome Goblin Pair |\n"
           "| **57.3%** | 3.0k | **WB** | Orzhov — **unsupported and the best of the off-pairs.** Black's common equipment feed white's equipment/storied cards; white's tokens feed black's sac effects. Small sample, big signal | — |\n"
           "| **56.6%** | 43.9k | **BG** | Golgari Ferocious — black-shaped aggro with green bodies; power 4+ payoffs. The most explosive openers in the format. **Not** an elves/synergy deck | The Chief Warg · Large Bear · Duskwatch Hunter |\n"
           "| **55.7%** | 41.3k | **RW** | Boros Dwarves — storied + equipment; carried by white's rares, which get passed too late. **Storied turns on by itself** — stop building around it | Thorin Oakenshield · Dáin Ironfoot · Dwalin, Weaponmaster |\n"
           "| **55.4%** | 39.7k | **WU** | Azorius Recruit — draw-two payoffs and go-wide tokens. Skill-intensive; **best deck in top-player stats.** Good *against* the black decks (1/1 tokens blank menace) | Bard the Bowman · Eagle's Rescue · Patient Instructor |\n"
           "| **53.9%** | 3.0k | **UR** | Izzet — no signpost, but blue and red are deep enough to carry it | — |\n"
           "| **53.4%** | 7.0k | **UB** | Dimir — no signpost and no plan, but black's removal carries it above the other off-pairs | — |\n"
           "| **52.2%** | 2.0k | **RG** | Gruul — unsupported; playable as straight beats if both colours are open | — |\n"
           "| **51.2%** | 19.8k | **GU** | Simic Elves/Landfall — **the worst supported deck by 4.2 points**, and still the third-most-drafted. **Don't chase elves** — play the good blue and green cards | Silvan Reveler · Thranduil, Sindarin Liege · Mirkwood Nurturer |\n"
           "| **46.8%** | 0.9k | **GW** | Selesnya — **the worst pairing in the format** | — |\n\n"
           "**Mono-colour benchmark:** Mono-Black **62.3%** (n=2.2k) is the highest win rate on the board — a blunt statement of how far ahead black is. Three-colour decks post **48.6%**; Sultai is **43.6%**. Splash only for removal, and only once the fixing is already in your pool.\n\n"
           "**Removal benchmarks:** the format's defining constraint is that **removal cannot kill small creatures** — no Shock, "
           "no Stab, no cheap white damage spell — so **two-drops are safe** and curve-out plans are rewarded. **Damage-based "
           "removal caps at 5**, making 6-toughness creatures (Old Fat Spider, Wilderland Scrounger) effectively unanswerable at "
           "common. Premium commons: Pinecone Strike (3 damage + exile) and Bilbo's Deadly Slice (Murder); **Stone by Sunlight is "
           "the only efficient uncommon removal** — Troll Negotiations, Burn Burn Tree and Fern and Celebrate the Mountain-king "
           "are all four mana. White gets exactly one common removal spell. **Sweepers barely exist**, so going wide is rewarded "
           "and anthems are unusually good; **lifegain barely exists**, so there is no stabilising back. **Menace is the defining "
           "keyword** — blocking is close to illegal in many games, which is why removing *a* body matters more than removing the "
           "right one. **Traps:** synergy decks you can't assemble (this is what sank Simic), splashing off the plentiful fixing, "
           "and storied/ferocious payoffs run with too few enablers.\n",

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
    "ECL": "### The archetypes (color-pair guilds)\n\n"
           "ECL is a **tribal-synergy** format — five two-color tribes plus real Vivid, Blight, and Fairies "
           "off-ramps. Being in a supported pair unlocks gold lords, Eclipsed cards, and Commands, so more good "
           "cards flow your way — but a **contested** tribal lane makes your deck atrocious, so read the signals "
           "and be willing to pivot to Vivid/Blight. **Changelings keep you open** (they satisfy every typal "
           "payoff and count Vivid pips). Ranked by Lords of Limited's 2026-03-23 retrospective.\n\n"
           "| Tier | Pair | Tribe / plan | Key cards |\n"
           "|------|------|--------------|-----------|\n"
           "| **S** | **BG** | Elves — well-sized bodies + graveyard-as-resource; Morcan's Eyes floods 2/2 elf tokens for inevitability | Morcan's Eyes · Dawnhand Eulogist · Nameless Inversion |\n"
           "| **A** | **UW** | Merfolk — tempo/convoke, tap synergies + flash; close before turn 8 (highest floor) | Deepchannel Duelist · Merrow Skyswimmer · Unexpected Assistance |\n"
           "| **A-** | **UR** | Elementals — midrange ETB power + land-cyclers; season-long riser | Flamebraider (kill on sight) · Ashling's Command · Flaring Cinder |\n"
           "| **A-** | **2c Vivid** | Two-color base deploying off-color payoffs late; loves a board stall (NOT 5-color) | Shine Striker · Prisma Basher · Shimmer Wild's Growth |\n"
           "| **B** | **RB** | Goblins — GRINDY not aggro; win via blight-drain + triggers | Champion of the Weird · Sour Bread Auntie · Gristle Glutton |\n"
           "| **B** | **BW** | Blight — grindy counter value; high-toughness bodies absorb counters | Reaping Willow · Moonlit Mentor · Bog Slither's Embrace |\n"
           "| **B** | **UB** | Fairies/Flash — act on the opponent's turn; can trophy with no rares | Voracious Tome Skimmer · Mischievous Sneakling · Glamour Gifter |\n"
           "| **C** | **GW** | Kithkin — weenie aggro + pump lords; predicted #1, FINISHED LAST (one removal stops it) | Thought-Weft Lieutenant · Clacken Festival · Mist Meadow Council |\n"
           "| **C** | **RW** | Blight/Giants — beatdown; less refined than BW blight | Brambleback Brute · Cinder Strike |\n"
           "| **C** | **RG** | Treasure — really just a Temur Vivid base, not a pure pair | Nogggle Robber |\n\n"
           "**Removal benchmarks:** Cinder Strike (R, 1-mana deal-4 on blight — best common), Bog Slither's "
           "Embrace (B), Luminal Hold (W), Nameless Inversion / Sear / Feed the Flames (uncommons). **Format "
           "rules:** hold removal for lords/engines (don't push 2 damage); creature counts run 15–20 even in "
           "Vivid/Blight; two-drops without synergy are dead weight (curve starts on three); high flash density "
           "punishes slamming into open mana; **Blight is upside only when you build for it** (Narho Bark Elm, "
           "Spiral into Solitude are traps otherwise).\n",
    "DFT": "### The archetypes (color-pair guilds)\n\n"
           "DFT is a **slow, grindy** format wearing a racing costume — every pick is read against which pair a card "
           "serves. Pairs ranked by Lords of Limited's 2025-03-17 retrospective (the decisive source). Green plays "
           "the best raw threats at common, so **every deck needs a plan to beat big green** (Hazard of the Dunes, "
           "Migrating Ketradon, Regal Imperiosaur).\n\n"
           "| Tier | Pair | Game plan | Signposts |\n"
           "|------|------|-----------|-----------|\n"
           "| **S** | **BG** | Graveyard value + exhaust, big bodies — the best deck | Thundering Broodwagon · Wreckage Wickerfolk · Spin Out · Earthrumbler |\n"
           "| **A** | **UB** | Artifact/affinity control, thopters, Haunt the Network drain (Esper soup too) | Haunt the Network · Pactdoll Terror · Repurposing Bay · Rangers' Refueler |\n"
           "| **A** | **BR** | Start Your Engines aggro-midrange, edict into engine-start, drain | Momentum Breaker · Outpace Oblivion · Endrider Spikespitter · Magmakin Artillerist |\n"
           "| **A-** | **UR** | Cycling/discard + **Push the Limit** build-around — highest ceiling in the set | Clamorous Ironclad · Spire Mechcycle · Push the Limit · Thunderhead Gunner |\n"
           "| **B+** | **Big White** | Broad-base midrange/control with chunky vehicles — NOT aggro white | Ride's End · Broadcast Rambler · Marshals' Pathcruiser · Explosive Getaway |\n"
           "| **B** | **4c No-Green** | Esper/Mardu/Grixis good-uncommon piles on Starting Column + Night Market fixing | Starting Column · Ride's End · Haunt the Network |\n"
           "| **B** | **Green late-game** | Ramp into big green bodies + exhaust payoffs (incl. GU exhaust) | Hazard of the Dunes · Regal Imperiosaur · Boom Scholar |\n"
           "| **C+** | **RG** | Exhaust big-mana stompy, Boom Scholar cost-reduction | Boom Scholar · Rocketeer Boostbuggy · Hazard of the Dunes |\n"
           "| **C** | **WB / WU / GU / RW** | Aristocrats · artifact-vehicles · exhaust-thopters · pilot beatdown — narrower support pairs | Embalmed Ascendant · Guidelight Pathmaker · Rangers' Aetherhive · Cloudspire Coordinator |\n\n"
           "**Removal benchmarks:** Ride's End (W, premium), Spin Out (B common), Momentum Breaker (B edict/tempo), "
           "Outpace Oblivion / Lightning Strike (R), Bounce Off (U tempo), Broadside Barrage (gold), Spectacular "
           "Pileup (W cycling wrath — wheels because everyone avoids white). **Format rules:** vanilla 2-mana 2/2s "
           "are below replacement; **aggressive white is a trap** (big white only); **Push the Limit needs 9+ "
           "mounts/vehicles** — don't force it; RW Boros is hard to pilot (every win is 'two wins'); max speed "
           "(Start Your Engines) turns on when an opponent loses life on your turn, and payoffs spike hard at max.\n",
    "OTJ": "### The archetypes (color-pair guilds)\n\n"
           "OTJ is a **midrange, bombs-and-removal** format — draft the best bomb you open, then prioritize clean "
           "(ideally exile) removal to answer the opponent's, because the set is bomby and recursion is everywhere. "
           "**Green is the best color and GW mounts is the best deck; blue is underrated and open** (its uncommons "
           "wheel to pick 6+); **red is the weakest color.** Pairs ranked by Lords of Limited's 2025-01-28 "
           "retrospective; Numot's counter-lean pushes Desert-fixed **4-5c good-stuff/crime** and **RG Railway "
           "Brawler stompy** up. Crime (targeting the opponent/their stuff) is a cross-color sub-theme, and the "
           "10-desert crime-land cycle is dual-purpose fixing.\n\n"
           "| Tier | Pair | Plan | Signposts / key cards |\n"
           "|------|------|------|-----------------------|\n"
           "| **S** | **GW** | Mounts + go-wide, big green rate + white removal, Miriam recursion | Congregation Gryff · Miriam, Herd Whisperer · Throw from the Saddle · Bounding Felidar |\n"
           "| **A** | **UB** | Control / crime: card advantage + removal + Intimidation Campaign; Grindstone win-con | Slickshot Lockpicker · Vault Plunderer · Intimidation Campaign · Lazav |\n"
           "| **A** | **UW** | Control/tempo, \"didn't cast from hand\" payoffs on a control shell | Wrangler of the Damned · Mystical Tether · Canyon Crab · Lassoed by the Law |\n"
           "| **A** | **BR** | Outlaws aggro + crimes + burn (affinity-for-outlaws bodies) | Vile Smasher · Reckless Lackey · Laughing Jasper Flint · Jagged Barrens |\n"
           "| **B** | **UR** | LATE-GAME control w/ double-spell package (preferred) — Razzle-Dazzler aggro is a trap unless fully built | Kraum · Malcolm · Highway Robbery · Canyon Crab |\n"
           "| **B** | **BW** | Midrange crimes + recursion | Ruthless Lawbringer · Lively Dirge · Mourner's Surprise |\n"
           "| **B-** | **GB** | Value/midrange, Honest Rutstein recursion + green rate | Honest Rutstein · Patient Naturalist · Throw from the Saddle |\n"
           "| **C+** | **RG** | Stompy — Railway Brawler makes the team huge, Dance of the Tumbleweeds ramp (Numot's #1 mythic) | Railway Brawler · Dance of the Tumbleweeds · Colossal Rattlewurm |\n"
           "| **C+** | **RW** | Boros go-wide aggro (needs its 2-drops; red's weakness caps it) | Scalestorm Summoner · Trained Arynx · Skewer the Critics |\n"
           "| **C** | **GU / 4-5c** | GU self-mill niche · **4-5c good-stuff/crime** on Desert + Oasis Gardener fixing (Numot's favorite) | Oasis Gardener · Bandit's Haul · Villainous Wealth · Mirage Mesa |\n\n"
           "**Removal benchmarks:** Throw from the Saddle (G fight — **best common in the set**), Mystical Tether "
           "(W exile — premium), Lassoed by the Law (W), Desert's Due (B, needs a desert), Consuming Ashes (B exile), "
           "Explosive Derailment / Skewer the Critics (R), Stop Cold (U exile vs bombs). **Format rules:** 17 lands "
           "standard (18 with mana sinks); **plot is a value/late-game mechanic, NOT tempo** — don't plot over a "
           "better play; **don't hold creatures waiting to commit a crime**; take crime-deserts 2-4 deep with "
           "payoffs. **Traps:** Skulduggery, Patient Naturalist, Outlaw Stitcher, Arid Archway, Phantom Interference, "
           "Razzle-Dazzler aggro. GIH WR **inflates** multicolor soup + build-around payoffs (Railway Brawler, "
           "Marchesa) and **underrates** efficient removal.\n",
    "DSK": "### The archetypes (color-pair guilds)\n\n"
           "DSK is a **graveyard-matters midrange** format built on three overlapping axes — **Delirium** (4+ card "
           "types in yard), **Manifest Dread** (face-down 2/2s that fuel the yard + flip up), and **Eerie** "
           "(enchantment/room triggers). **Green is busted** (elite commons AND uncommons) and **black** has the "
           "premium removal + payoffs; blue is weak-commons/elite-uncommons, so late blue uncommons signal an open "
           "lane. Don't over-commit before pick 5-6 — take mono-color removal/efficient creatures while reading the "
           "seat. Ranked by Lords of Limited's settled read; Numot's counter-lean pushes **WU enchantments** ('maybe "
           "the best deck') and **BR sacrifice** up.\n\n"
           "| Tier | Pair | Theme / plan | Signposts / key cards |\n"
           "|------|------|--------------|-----------------------|\n"
           "| **S** | **BG** | Golgari Delirium value — fill the yard fast, unlock huge payoffs; splashes W/R naturally | Brood Weaver · Drag to the Roots · Wickerbough Thresher · Say Its Name |\n"
           "| **A** | **UG** | Simic Manifest Dread engine — repeat it, flip up, refill (grinding midrange) | Oblivious Bookworm (best gold uncommon) · Paranormal Analyst · Threats Around Every Corner · Under the Skin |\n"
           "| **A** | **BW** | Orzhov Reanimator — discard/mill fatties, reanimate them | Rite of the Moth · Shroudstomper · Miasma Demon · Vile Mutilator |\n"
           "| **A-** | **UB** | Dimir Eerie control — enchantments/rooms, surveil, recurring evasion | Skullcap Nuisance · Fear of Infinity (\"can't race it\") · Nowhere to Run |\n"
           "| **B+** | **RG** | Gruul Delirium stompy — fill yard, attack with big delirium bodies (Jund-splash natural) | Wildfire Wickerfolk · Beastie Beatdown · Patchwork Beastie |\n"
           "| **B** | **WU** | Azorius Eerie tempo — enchantments trigger eerie + glimmers/rooms (best deck when open) | Gremlin Tamer · Inquisitive Glimmer · Glimmerlight |\n"
           "| **B** | **BR** | Rakdos Sacrifice/Eerie — sac creatures/enchantments for value (Kenji favorite) | Disturbing Mirth · Sawblade Skinripper · Cracked Skull |\n"
           "| **B-** | **GW** | Selesnya Survival — snowball beatdown via survival triggers + counters | Shrewd Storyteller · Orphans of the Wheat · Hardened Escort |\n"
           "| **C+** | **UR** | Izzet Rooms — control/burn; signposts pull opposite ways, plays as soup (inconsistent) | Smoky Lounge // Misty Salon · Intruding Soulrager · Pyroclasm |\n"
           "| **C** | **RW** | Boros aggro — power-2-or-less tokens/gremlins, Arabella drain (shallowest, weakest lane) | Arabella, Abandoned Doll · Midnight Mayhem · Razorkin Hordecaller |\n\n"
           "**Removal benchmarks:** Scorching Dragonfire (1R: deal 3, exile) and Nowhere to Run (1B flash: −3/−3) are "
           "the premier damage removal — **four toughness is the magic number** (dodges both). Premium exile/tuck: "
           "Sheltered by Ghosts, Trapped in the Screen, Seized from Slumber (BW), Unable to Scream (U). Murder / Final "
           "Vengeance / Withering Torment are the honest black kills. **Format rules:** 16-17 lands (Terramorphic + "
           "land-cyclers + manifest dread smooth the mana); **exile/tuck > kill** since feeding graveyards helps "
           "Delirium/Reanimator opponents. **Traps:** five-drop flyers with no board impact (Fear of Falling — "
           "previewed premium, settled trap), Coordinated Clobbering, Monstrous Emergence (doesn't exile). Delirium's "
           "hardest type is **artifacts** — Terramorphic Expanse, Glimmerlight, Piggy Bank, Patchwork Beastie are the glue.\n",
}
L.append(ARCHETYPES.get(SET, ""))

# ---- per-set strategy brief -------------------------------------------------
# The format-level commentary distilled from the expert guides that isn't attached to any single
# card: draft plan, gameplay rules, deckbuilding doctrine, traps, cross-source disagreements.
# Lives here rather than in a sidecar file so the reference is built from one place — the whole
# point is that the reader never has to open a second document.
BRIEF = {
    "MSH": "## Format brief \u2014 everything that isn't a single card\n\nDistilled from the four expert guides in `draft-guides/` so you don't need a second window.\n\n**Read this first \u2014 every MSH expert source predates the data.** Each was recorded *before or during*\nrelease week: Limited Level-Ups' deepest input is a 2026-06-24 ranked draft, Lords of Limited's is a\n2026-06-23 paper early-access episode, Limited Resources only ever aired the commons/uncommons review\n(#858, 2026-06-17 \u2014 no rares/mythics review, no format overview, no sunset show), and NumotTheNummy\nhas two release-window VODs he himself drafted loosely. **Not one of them saw a single game of\n17Lands data.** This brief's main job is therefore to say *where 8.35M games proved the\nexperts wrong*. On any conflict, the data wins \u2014 that is not a tiebreak rule here, it is the whole\npoint. Read the guide notes on a card tile as theory, and the numbers on the same tile as the verdict.\n\n**Calibrate to the baseline:** MSH GIH WRs run high. Mono-color game-weighted averages sit between\n53.5% and 57.9%, so a 55% card is *average*, not good. Read the deltas, not the absolutes.\n\n### The draft plan in five lines\n\n1. **Be in blue or white. Both, ideally.** Game-weighted mono-color GIH WR: **U 57.9% \u2248 W 57.9% >\n   G 56.4% > B 55.6% > R 53.5%.** The experts unanimously called blue #1 and that held \u2014 but *white\n   is dead even with it*, not a clear #2, and **red is 4.3pp behind blue**, an enormous gap. The top\n   six commons in the set are all white or blue (Hero in Training 60.5%, Trickster's Stratagem 60.4%,\n   Murdock's Crusade 59.7%, S.H.I.E.L.D. Deployment Drone 59.5%, Web Up 59.3%, We Say Thee Nay!\n   59.3%). That is the whole color story.\n2. **Do not pair blue with black.** This is the format's biggest expert miss. LLU called UB its\n   \"de-facto best in practice,\" LoL ranked it Tier 1 co-#1, Draftsim led with it. By gold-card win\n   rate UB is **dead last of the ten pairs.** The mechanism is simple: blue is the best color, black\n   is the *fourth* color, and UB's signposts are its two worst (Kang 55.4% at ALSA 5.0 \u2014 it wheels;\n   Ghost 52.4%). Connive is genuinely good; the black half of the pair is what drags. **Pair blue\n   with white instead.**\n3. **The signpost cycle is a trap. Take the good card.** Of the twenty gold-and-hybrid signposts,\n   **six have negative IWD** and only **one \u2014 Killmonger, Scourge of Wakanda (60.3%, IWD +6.2) \u2014 is\n   worth a genuinely high pick.** LoL and Numot both called Killmonger the best gold uncommon by a\n   wide margin, and that is the one signpost call the field got right.\n4. **Removal is scarce, and all four sources independently said so.** This is the single\n   most-confirmed take across every guide \u2014 LLU (\"at a premium more so than usual\"), LR (the whole\n   #858 grading frame), LoL (\"prioritize it and hold it\"), Numot (who blamed both losing drafts on\n   being removal-light). Nothing in the data contradicts it. Dark Deed (59.4%, IWD +6.3), Punishing\n   Punch (59.7%), Web Up (59.3%), Cruel Alliance (59.1% \u2014 LR correctly called it \"likely the best\n   black common\") are the benchmarks. Do not pass cheap interaction.\n5. **Lightly-themed goodstuff midrange is a fine default.** LLU's post-draft verdict \u2014 \"the theme is\n   good cards, it's a midrange deck\u2026 something you're going to find pretty commonly in this set\" \u2014\n   is the read that survives contact with the numbers. No pair is dead, the fixing is deep, and every\n   hard-committed synergy lane below underperformed its hype.\n\n### Where the experts were wrong \u2014 judged by 8.35M games\n\nGold-card GIH WR by color pair, best to worst: **BG 58.8 \u00b7 UW 58.8 \u00b7 RW 58.5 \u00b7 WB 57.5 \u00b7 GR 57.4 \u00b7\nBR 56.7 \u00b7 GW 56.0 \u00b7 UR 55.4 \u00b7 GU 55.1 \u00b7 UB 54.1.**\n\n\u26a0 **This is a proxy, not 17Lands' archetype win rate.** It averages only the gold cards legal in each\npair, so it conflates card quality with archetype quality and rests on small per-pair samples. Trust\nthe direction and the extremes; do not treat the exact ordering as settled.\n\n- **UB \u2014 ranked #1 or co-#1 by three of four sources; finishes last.** See line 2 above. The largest\n  collective miss in the repo for this set.\n- **RW \u2014 LoL called it \"too fussy,\" \"a house made of toothpicks,\" Tier 2; it finishes #3.** And it\n  holds the best card in the set, **The Super Hero Civil War (69.3%, IWD +16.8, ALSA 1.5)**. Note the\n  shape though: *both* its signposts are negative-IWD (War Machine \u22121.1, Thor Odinson \u22120.5), so RW is\n  good **despite** its signposts, carried by white commons and that one rare.\n- **GW \u2014 LoL Tier 1, LLU's #2 archetype; finishes #7.** Both its signposts are negative-IWD too\n  (Black Panther, Vanguard \u22120.3 despite LR's B+ \"both enabler and payoff\"; Spider-Man, To the Rescue\n  \u22121.0). The hero theme turning on \"automatically\" was true and did not matter.\n- **BG #1 and UW #2 are the two calls that held.** LoL had both in Tier 1; LLU had UW at #4 and BG\n  down at #6, so LoL wins this one.\n- **GU worst-pair and UR shallowest-theme predictions both hold** (9th and 8th). LLU's \"a deck you\n  draft once in a blue moon\" and \"you won't get a true all-artifact deck\" were correct.\n- **LLU's grades beat LR's on uncommons \u2014 weight them accordingly.** LR graded the signposts in the\n  abstract before playing and systematically over-rated them: Madame Hydra B (actual 49.8%, IWD\n  \u22120.5), Beast, Erudite Aerialist B\u2212 (49.5%, IWD \u22122.6 \u2014 the worst signpost in the set), Ant-Man,\n  Colony Commander B+ \"closer to A\u2212, pushing the limits all by itself\" (53.7%, IWD +0.8), Bullseye\n  B+ \"completely justifies itself\" (54.2%). LLU had those same cards at D+, D, and D+/C\u2212. On MSH\n  uncommons, **LLU's letter beats LR's letter.**\n- **LR's own \"predicted-volatile\" watchlist resolved mostly to the pessimistic branch:** Madame Hydra\n  \u2192 bust \u00b7 Mockingbird, Ace Agent \u2192 50.3%, IWD \u22122.6, the \"trap until proven otherwise\" read was right\n  \u00b7 Speedball, New Warrior \u2192 50.3%, IWD \u22122.2, the \"could just as easily be a B+\" hope lost \u00b7 Red Hulk\n  \u2192 52.2%, the D branch of \"predicted A-or-D\". Two went the other way: **Wakandan Drone Flock** is a\n  fine playable that wheels (57.1% at ALSA 5.9 \u2014 better than the feared C\u2212), and **Panther Pounce**\n  stayed marginal (54.1%, IWD \u22120.1).\n- **Plans split; LoL's blanket \"garbage\" was too harsh.** Political Triumph is a top-ten uncommon\n  (59.2%) while Construct a Cosmic Cube is a genuine bust (48.8%). LLU's more careful \"value the\n  early chapters, they rarely reach the final one\" is the read that survives.\n- **LLU's sleeper list is the best single piece of prediction in the four guides \u2014 6 of 7 hit.**\n  Trickster's Stratagem (60.4%, the #2 common in the set), We Say Thee Nay! (59.3%), Undercover\n  Skrull (59.0%), Take Up the Shield (58.5%), H.E.R.B.I.E. Scout Unit (57.5% at ALSA 4.7),\n  Surveillance Room (56.3% at ALSA 5.8). The one miss: **A.I.M. Synthoids** \u2014 \"don't sideboard it\"\n  was wrong, it is a sideboard card (52.3%, IWD \u22120.8).\n\n### The one thing this brief cannot settle: format speed\n\nLLU and LoL converge hard on **slow and grindy** \u2014 board stalls, flying breaks them, no board wipes,\n\"Dominaria United cadence,\" missing land drop three is an auto-loss. Numot, from the other side of\nthe table, insists the loudest lesson of his two drafts was that **\"playing first and curving out is\nOP,\"** and that he lost repeatedly to clean 2\u21923\u21924 villain curves before any stall formed. Card-level\nwin rates cannot adjudicate this. Treat both as true: the format grinds when neither player is\nahead, and punishes you hard when you are the one durdling.\n\n### Deckbuilding doctrine\n\n- **The 2-drop slot is the scarce one; the 4-drop slot clogs.** LoL and Numot independently hit this.\n  Do not play bad filler two-drops \u2014 you 0-for-1 yourself \u2014 but do count land-cyclers as two-drops\n  (cycle on two, play a three on three). Typical: 3\u20135 real two-drops plus 2\u20133 cyclers, 16\u201317 lands,\n  17\u201318 creatures because so many engines are bodies.\n- **4 toughness is the magic number.** You need to attack through it and to kill it, which is why\n  deal-3 effects underperform their reputation.\n- **No board wipes exist.** Only deal-2-or-3-to-everything. Go-wide and sticky single threats are\n  unusually safe; a white bomb with no sweeper to answer it just wins.\n- **Splash freely for removal and a bomb or two \u2014 not for a pile of fatties.** Fixing is deep\n  (gain-lands in ~half of packs, an untapped rare dual cycle, land-cyclers, Ant-Man's Army 56.8%,\n  Surveillance Room 56.3%). Numot proved the failure mode himself: his 4\u20135 colour soup piles were\n  \"cool, not good,\" bomb-heavy and interaction-light, and lost to clean curves.\n- **Bait removal with your mid-curve.** LLU's post-play correction: a random 4-mana 4/4 plays *better*\n  than its grade in a slow format, because eating their removal on your medium threat protects your\n  actual bomb. The top-end no-ETB fatties still get raced \u2014 that exception holds.\n- **Don't straddle two synergy lanes.** Numot's clearest self-diagnosed error: his deck drifted\n  between +1/+1 counters and artifacts and committed to neither. Counters live in GU, artifacts in\n  UR; they do not merge.\n\n### Traps and sleepers the data settled\n\n- **Worst early picks** (taken by pick 4 on average, negative or zero IWD): Thunderbolts Conspiracy\n  (49.2%, IWD \u22121.2), War Machine, Legacy of Iron (\u22121.1), Spider-Man, To the Rescue (\u22121.0), Alien\n  Invasion (\u22121.0), Black Panther, Vanguard (\u22120.3), The Sentry, Golden Guardian (53.1% at ALSA 2.4),\n  Construct a Cosmic Cube (48.8%), Shang-Chi, Master of Kung Fu (53.0% at ALSA 2.7).\n- **Cheapest edges \u2014 strong cards that wheel** (ALSA 6+): Rapid Rescue (57.8% at ALSA **8.0** \u2014 the\n  single biggest gap in the set), Giant-Sized Flying Ant (57.6% at 6.2), S.H.I.E.L.D. Helicarrier\n  (57.4% at 6.9 \u2014 LLU's Alex defended this over co-host Mark's D+ and community pushback; **Alex was\n  right**), HYDRA Infiltration (56.4% at 7.3), Depower (56.1% at 6.6), Super Suit (55.8% at 7.0).\n- **HYDRA Troopers is not a reason to be in BG** \u2014 53.3% at ALSA 6.6, after LoL and LR both walked it\n  back from \"premium\" to \"conditional.\" They were right to walk it back, and it fell further.\n- **HULK SMASH! is fine, actually** \u2014 55.4%, IWD +2.7. LLU's \"more of a constructed card than a\n  limited card\" was too harsh; this is the one place LLU under-called rather than over-called.\n- **Take the reprints seriously.** Sword of Fire and Ice (69.2%), Path to Exile, Counterspell,\n  Massacre Girl, Extinction Event and the rest of the bonus sheet carry no expert notes at all\n  because set reviews skip known quantities. Their tiles have numbers and an AI take only \u2014 that is\n  a coverage gap, not a signal that they are unimportant.\n\n### Calibration note\n\nNumot's own warning is the right frame for this whole document: he crushed paper early access, then\nwent 0-3 on release-day Arena and cautioned that \"the early-access sample may not be a good way to\ncount my drafting in this format.\" Every guide here is written from inside that window. Where a card\ntile shows a confident letter grade next to a mediocre win rate, the win rate is what happened.\n",
    "HOB": "## Format brief — everything that isn't a single card\n\nDistilled from the four expert guides in `draft-guides/` so you don't need a second window. Sources\nin priority order: **Limited Level-Ups State of the Format** (2026-08-15, post-play, Alex had drafted\nthe format for four days and reviewed coaching logs), **NumotTheNummy** (three week-one Premier VODs,\n2026-08-14 → 08-16), **Limited Resources 865/866**, **Lords of Limited crash course** (prerelease\ntheory, weakest). On conflict: live 17Lands numbers > post-play takes > prerelease predictions.\n\n### The draft plan in five lines\n\n1. **Black is the default, not the commitment.** *\"Drafting black when it's open or semi-open is\n   almost like drafting on easy mode\"* — it has the best and deepest commons. But the single most\n   common trainwreck in Alex's coaching logs is *\"I started black, I hung on to black for dear life,\n   and it was clear a lot of other people were fighting for black.\"* Six-drafters-in-black tables are\n   real; a great W/U or R/W deck flies around when that happens.\n2. **Curve out. That is the format.** Numot: *\"curving out is overpowered\"* and *\"something you\n   really need to do in this format is have a low curve.\"* Games are won by two-drop → three-drop →\n   four-drop with no bombs involved, and lost to exactly that from red-black.\n3. **Take the cheap card at equal power.** *\"There are so many good cheap cards that you don't need\n   expensive cards as often. If your cheap cards are good in the late game, why play a six-drop\n   unless it's exceptional?\"*\n4. **Being reactive is punished.** *\"Trying to just cast a bunch of removal doesn't work very well.\n   There's a lot of recursion, a lot of token makers — you want to be on the front foot.\"*\n5. **The unsupported pairs are real.** **W/B is the best of them** (black's two common equipment feed\n   white's equipment/storied cards; white's tokens feed black's sac effects; three of nine sealed\n   pools Alex built that week were W/B). U/B is fine on black's depth alone. Numot drafted **R/G** and\n   **U/B splashing green** in week one and neither was a mistake. Don't cage yourself in the five\n   signposted pairs.\n\n### Gameplay rules that actually change results\n\n- **Attack more than you think you should.** *\"Taking a defensive stance in a format that is largely\n  about racing is consigning yourself to playing a defensive role\"* — which turns off the very cards\n  that are good. A topdecked Goblin Plate Mail matters when they're at 8, not at 16. Default: for the\n  first ~4 turns, just attack, unless your hand is specifically built around surviving to a bomb.\n- **Do the menace math explicitly.** *\"I'm almost sure I've seen a lot of folks put themselves dead\n  on board because they didn't realize how much damage I could attack back for.\"* Two blockers vs.\n  three menace creatures blocks **one** creature — and one removal spell means it blocks **none**.\n  Intuition is miscalibrated here; count it out every turn.\n- **Don't decline a lethal alpha strike over a card they might have.** Numot's one self-diagnosed\n  punt of the run: *\"I had an easy win if I attack with everything... I got too scared of what they\n  could have. Why wouldn't I just go in with 50 points of trample damage?\"*\n- **Sequencing is punishing because the games are short.** Fewer turns means each decision is a\n  larger fraction of the game — which land, which two-drop, how you double-spell on four.\n- **Every unspent mana is expensive.** In a six-turn game, a wasted mana is a much bigger share of\n  your total than in a ten-turn one. This is the real argument for one-mana adventure halves and\n  cheap equipment: they let you *fill* a turn, not just fill a deck slot.\n- **Take the big hit instead of losing two creatures.** *\"Do I double block and lose both of my\n  creatures? Do I take eight? I think taking eight's the play.\"*\n- **Don't pay optional life when the attack already works** — Desolation Prowler's activation is\n  genuinely dangerous in a deck already paying life elsewhere, and burn range comes up fast.\n- **Where the equipment sits is a play, not upkeep.** *\"Move the blade over to the 2/1, that way none\n  of their 1/1s have a good block.\"* Reassign it every combat.\n- **A fast format only feels fast when one player isn't affecting the board.** *\"Games do tend to\n  slow down if both players are coming to the table prepared — matching each other on curve, with a\n  good amount of interaction.\"* That's why a seven-mana adventure creature is still castable.\n\n### Deckbuilding doctrine\n\n- **Copy counts differ per card and Alex worked them out on air:** Goblin Plate Mail **three** (the\n  second copy plays like an aura, but three means you actually see the first on turn two) · Gollum,\n  Silent Slinker **two** (legend rule; three got punished on stream) · Crude Bent Blade **four or\n  five, no cap** · Tidings of War **one or two** · Moment of Glory **not three**.\n- **Modal cards are good in proportion to how *different* the modes are.** Reverent Howl is the case\n  study: draw-two after a mulligan and +2/+2 lifelink in a race are different games. Apply the same\n  test to Stone by Sunlight and Warg Tactics.\n- **Splash only for removal, and only if the fixing arrived first.** Fixing is plentiful (the dual\n  cycle is in ~50% of packs) but almost nothing is worth splashing — the gold rares aren't\n  splashable and the good uncommons are locked to their pair. **Celebrate the Mountain-king** is the\n  archetypal target.\n- **Ferocious wants 8–10 enablers**, counting equipment and counters, not just naturally-big\n  creatures — and eight is worse than it sounds if three of them are six-drops.\n- **Storied is not a build-around.** It turns on incidentally; in R/W it is nearly automatic. *\"I\n  just haven't seen a red-white opponent not have storied by turn five.\"* Stop holding Thorin\n  Oakenshield back to protect it.\n- **W/U recruit is skill-intensive, and the common mistake is discarding lands.** A free 1/1 is\n  frequently the better outcome — *\"ask, would I like a free 1/1 here? Is that better than the card\n  in hand that I might not have time to cast?\"*\n\n### Traps and reversals the format has already settled\n\n- **Goblin-town Flunkies** — Alex's predicted top red common; *\"has super underperformed.\"* The 1/1\n  haste half stops being a card after turn two in a format decided by creature sizing.\n- **Crude Bent Blade** — the reverse: unranked prerelease, now the best or second-best black common,\n  first-pickable, four or five copies. Read its tile.\n- **The legendary-equipment cycle** (Sting, Orcrist, My Precious, Balin, Inside Information) all go\n  pick 1–3 and all have **negative IWD**. **Sting is unplayable** — it's designed for four-player\n  games. Orcrist barely creeps into playable.\n- **The gold uncommon signposts are mostly not the reason to be in a pair.** *\"The uncommon gold\n  cards are all kind of just not anything special.\"* Exceptions: **Bard the Bowman** (his favourite)\n  and **Dáin's Company**.\n- **Simic U/G is the broken archetype** — 6+ points behind Rakdos. If you end up there, **don't\n  chase elves**: *\"a lot of the elf cards ask you to have a critical mass to be good, so to make\n  them tick you have to play bad cards.\"* Play the good blue and green cards instead. Thranduil,\n  Sindarin Liege is the one elf card that's self-fuelling.\n- **Blue commons wheel far too late for their strength** — Plunder the Trollshaws, Long Lake\n  Nuisance and Lakeshore Apothecary all post strong win rates at ALSA 6+. The cheapest edge in the\n  format.\n- **Don't first-pick fixing**, and don't play Wood Elves — a three-mana 1/1 *\"just ain't it.\"*\n\n### Cross-source disagreements, left unresolved on purpose\n\n- **Gollum, Silent Slinker** — LLU calls it a premium under-the-radar common and 17Lands agrees;\n  Numot found it *\"has underperformed for me consistently.\"* The likely explanation is the one Kenji\n  names himself: he plays from a defensive posture and this is a racing card.\n- **Dáin's Company** — Numot: *\"not very good, right?\"* LLU: strong enough to take out of most packs.\n- **Snowslope Hunter** — Numot: *\"amazing,\"* given how many equipment there are to sacrifice. LLU:\n  playable but off-plan for how he builds B/R.\n- **Wargling** — Alex likes it against the data (*\"I don't think this is a D+ two-drop\"*); it has\n  since climbed to roughly average.\n\n### Calibration note\n\nNumot went **18-18** on release day and did not trophy in his **first eight drafts** while making\nevaluations that mostly held up. Alex, by 2026-08-15: *\"I don't think there's that much more\nexploring of the format to be done.\"* Treat the week-one read as close to final — which the 17Lands\nconvergence supports — but don't rewrite your pick order off one bad weekend.\n",
}
L.append(BRIEF.get(SET, ""))

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
      f"| >=1 guide note: {matched} "
      + "".join(f"| {l} grades: {sum(1 for c in cards if norm(c['name']) in t)} "
                for l, t, _ in GRADE_SOURCES)
      + f"| {COLS} per row")
