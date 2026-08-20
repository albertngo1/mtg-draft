#!/usr/bin/env python3
"""Build a single Markdown card reference for an MTG set: every card as a tile in a
3-per-row HTML grid, with image, 17Lands ratings, Draftsim grade, expert-guide notes,
and an AI take.

Sources (relative to the mtg-draft repo root):
  data/cache/17lands_<SET>_PremierDraft_1200d.json   image + 17Lands ratings
  grades/draftsim_<SET>.json                         Draftsim DS grade (0-5)
  draft-guides/{lords-of-limited,numot,limited-resources,limited-level-ups}/...  expert per-card notes
  card-reference/ai_takes_<SET>.json                 pre-generated AI takes (this folder)
  card-reference/briefs/<SET>.md                     REQUIRED per-set format brief (this folder)

Usage: python3 build_card_reference.py [SET]   (default SET=SOS)
Output: card-reference/<SET>-card-reference.md
"""
import json, os, re, html, sys, time, base64, difflib, urllib.request

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
NO_BRIEF = "--no-brief" in sys.argv[1:]              # build without a format brief (throwaway only)
SCAFFOLD_BRIEF = "--scaffold-brief" in sys.argv[1:]  # write briefs/<SET>.md from the template and exit
SET = (ARGS[0] if ARGS else "SOS").upper()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_suffix = ".embedded.md" if EMBED_IMAGES else ".local.md" if LOCAL_IMAGES else ".md"
OUT  = os.path.join(HERE, f"{SET}-card-reference{_suffix}")
IMGDIR = os.path.join(ROOT, "data", "card-images", SET)  # download cache (gitignored via data/)
COLS = 3  # cards per row

BRIEF_TEMPLATE = """## Format brief \u2014 everything that isn't a single card

Distilled from the expert guides in `draft-guides/` so you don't need a second window. Sources in
priority order: TODO. On conflict: live 17Lands numbers > post-play takes > prerelease predictions.

### The draft plan in five lines

1. TODO \u2014 colour/archetype hierarchy, with the game-weighted mono-colour GIH WR spread.
2. TODO \u2014 what the format rewards (curve / removal / synergy / going wide).
3. TODO \u2014 the one card or axis that defines the format.
4. TODO \u2014 the most common trainwreck the experts name.
5. TODO \u2014 whether the signposted pairs are worth committing to.

### Gameplay rules that actually change results

- TODO

### Deckbuilding doctrine

- TODO \u2014 curve shape, land count, copy counts, splash policy.

### Where the experts were wrong \u2014 judged by the data

- TODO \u2014 score each guide's headline calls against the 17Lands numbers in this same file.

### Traps and sleepers the data settled

- TODO

### Cross-source disagreements, left unresolved on purpose

- TODO

### Calibration note

TODO \u2014 how much of the format each source had actually played when they recorded.
"""

BRIEF_PATH = os.path.join(HERE, "briefs", f"{SET}.md")

if SCAFFOLD_BRIEF:
    os.makedirs(os.path.dirname(BRIEF_PATH), exist_ok=True)
    if os.path.exists(BRIEF_PATH):
        sys.exit(f"{BRIEF_PATH} already exists — refusing to overwrite.")
    open(BRIEF_PATH, "w", encoding="utf-8").write(BRIEF_TEMPLATE)
    sys.exit(f"scaffolded {BRIEF_PATH} — fill in every TODO from draft-guides/, then rebuild.")

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

CARD_KEYS = [norm(c["name"]) for c in cards]   # fuzzy-match target for garbled guide names

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
# Auto-caption transcripts mangle card names ("Cactus Durantula" for Cactarantula, "Magitech Armor"
# for Magitek Armor), so an exact-name join silently drops ~130 real expert notes across the sets.
# Anything that doesn't match exactly gets one fuzzy pass against the set's actual card list.
# FUZZ_CUT is deliberately high and near-ties are refused, so a garble that could plausibly be two
# different cards is dropped rather than attached to the wrong tile.
FUZZ_CUT = 0.78     # minimum similarity to accept a garbled name
FUZZ_MARGIN = 0.06  # best match must beat the runner-up by this much, else it's ambiguous — drop it
FUZZ_LOG = []       # (label, raw name, resolved card) for the build's summary line

def fuzzy_key(k, card_keys):
    """Resolve a garbled normalized name to a real card key, or None if unsure."""
    m = difflib.get_close_matches(k, card_keys, 3, FUZZ_CUT)
    if not m:
        return None
    best = difflib.SequenceMatcher(None, k, m[0]).ratio()
    runner = difflib.SequenceMatcher(None, k, m[1]).ratio() if len(m) > 1 else 0.0
    return m[0] if best - runner >= FUZZ_MARGIN else None

def parse_guide(path, card_keys=(), label=""):
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
            if not k or k in notes:
                continue
            if card_keys and k not in card_keys:
                fk = fuzzy_key(k, card_keys)
                if not fk or fk in notes:
                    continue
                FUZZ_LOG.append((label, nm.strip(), fk))
                k = fk
            notes[k] = note
    return notes

# (tile-label, full legend name, parsed-notes dict) — drives both the tiles and the legend
GUIDE_SRCS = [
    ("📘 LoL",   "📘 Lords of Limited",   parse_guide(f"{ROOT}/draft-guides/lords-of-limited/{SET}-draft-guide.md", CARD_KEYS, "LoL")),
    ("🎙 Numot", "🎙 NumotTheNummy",      parse_guide(f"{ROOT}/draft-guides/numot/{SET}.md", CARD_KEYS, "Numot")),
    ("🎧 LR",    "🎧 Limited Resources",  parse_guide(f"{ROOT}/draft-guides/limited-resources/{SET}.md", CARD_KEYS, "LR")),
    ("🎓 LLU",   "🎓 Limited Level-Ups",  parse_guide(f"{ROOT}/draft-guides/limited-level-ups/{SET}.md", CARD_KEYS, "LLU")),
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

# ---- per-set strategy brief (REQUIRED) --------------------------------------
# The format-level commentary distilled from the expert guides that isn't attached to any single
# card: draft plan, gameplay rules, deckbuilding doctrine, traps, cross-source disagreements.
# The point is that the reference is self-contained — the reader never opens a second document.
#
# STRUCTURAL RULE: every set MUST ship card-reference/briefs/<SET>.md. The build FAILS without it,
# so a newly scraped set cannot quietly ship a brief-less reference. Escape hatches:
#   --scaffold-brief   write briefs/<SET>.md from the house template and exit (then fill it in)
#   --no-brief         build anyway (one-off diagnostics only; never for a committed reference)


if os.path.exists(BRIEF_PATH):
    _brief = open(BRIEF_PATH, encoding="utf-8").read()
    if "TODO" in _brief and not NO_BRIEF:
        sys.exit(f"{BRIEF_PATH} still contains TODO placeholders. Finish the brief, or pass "
                 f"--no-brief for a throwaway build.")
    L.append(_brief)
elif NO_BRIEF:
    print(f"  \u26a0 no brief for {SET} (--no-brief) — the reference is NOT self-contained.")
else:
    sys.exit(
        f"missing {BRIEF_PATH}\n"
        f"Every set's card reference must carry a format brief (see briefs/HOB.md for the "
        f"blueprint).\n"
        f"  python3 build_card_reference.py {SET} --scaffold-brief   # write the template, then fill it in\n"
        f"  python3 build_card_reference.py {SET} --no-brief         # throwaway build without one"
    )

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
if FUZZ_LOG:
    print(f"  fuzzy-matched {len(FUZZ_LOG)} garbled guide names: "
          + ", ".join(f"{l}:{r}\u2192{k}" for l, r, k in FUZZ_LOG[:6])
          + (" ..." if len(FUZZ_LOG) > 6 else ""))
