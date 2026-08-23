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

# NOTE: the brief opens straight on content. No "what this brief is" paragraph, no source
# bibliography, no pointer at the table rendered directly above it \u2014 the page already shows all
# of that, and restating it just buries the first real claim. The only thing that earns a spot
# above the first section is calibration that changes how the tiles below should be READ
# (sample-size caveats, a missing grade source, a pre-data attribution). Keep it to a blockquote.
BRIEF_TEMPLATE = """## Format brief \u2014 everything that isn't a single card

> TODO \u2014 one blockquote, only if something changes how the tiles should be read (thin sample,
> a source that grades nothing, an attribution that is pre-data). Delete this line otherwise.

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
    ("🎬 RD",    "🎬 Rough Drafts",       parse_guide(f"{ROOT}/draft-guides/rough-drafts/{SET}.md", CARD_KEYS, "RD")),
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


# Ordering inside each colour group: a rank-average of ALSA and play rate, for every set.
#
# Both metrics are populated by every single draft — ALSA by what the field passes, play
# rate by what makes the deck — so together they say where a card actually sits in the
# pick order. Play rate alone (the old default) flattened out across the whole playable
# middle of a set, and GIH WR sorts by which decks happened to draft a card, which is a
# different question from "what do I take here" and lags badly on a young set besides.
def order_group(g):
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
    "HOB": "> **Settled data.** HOB hit Arena on **2026-08-11**; these numbers are from **6,001,733 PremierDraft games** as of **2026-08-19**, with **179 of 188 cards** carrying a GIH WR. Evaluations have converged \u2014 the median per-card GIH WR move over the previous two days was **0.21pp** and the largest was 1.0pp, so treat this as close to final. The 9 cards without a win rate are genuinely unplayed rather than merely unmeasured. Two reviewer-grade sources render side by side: **LR** (Limited Resources 865 + 866, all 188) and **CGB** (CardGameBase, all 188).\n>\n> Removal cannot kill small creatures (no Shock, no Stab), so **two-drops are safe** and curve-out plans are rewarded. Damage-based removal caps at 5, making **6-toughness creatures near-unanswerable** at common. See the **Format brief** below for the archetype reads, gameplay rules and traps distilled from all four expert guides.\n",
    "SOS": "> SOS is a soup/Converge format \u2014 multicolor & Converge win-rates are inflated by 4-5c pilots. The AI take and guide notes decode which deck a number came from.\n",
    "MKM": "> MKM is a grindy 2-color guild-midrange format, so GIH WR transfers honestly (little soup inflation). Ratings are 2024 MKM PremierDraft historical data. White pairs (Boros best) sit on top; black is the weakest color.\n",
    "MSH": "> MSH 17Lands data is now mature (updated 2026-07-23): **285 of 334 cards** have a GIH WR off ~15.2M PremierDraft games, with QuickDraft (246 cards / ~2.1M games) and Sealed (254 cards / ~1.4M games) both live. Cards still lacking WR show blank stats; lean on the **CGB letter grade** + expert notes for those. WR is now a settled signal.\n",
    "ECL": "> ECL (Lorwyn Eclipsed) is a **tribal-synergy, midrange-to-grindy** format that plays slower than it looks \u2014 two-drops get blanked by high-toughness bodies and games often start on turn three. The 17Lands GIH WR is mature and full (**273 of 288 cards** off ~22.2M PremierDraft games). Big caveats: GIH WR **underrates efficient removal** (Cinder Strike doesn't win by being drawn) and **overrates tribal/blight/Vivid payoffs** (their number comes from the built-around deck) \u2014 the AI take + guide notes decode which deck a number belongs to. No reviewer-grade file exists for ECL, so WR + notes carry the read. **Five toughness** is the magic number (dodges Blight Rot, Seer, and Cinder Strike-on-blight).\n",
    "BLB": "> BLB is a finished format (Aug-Sep 2024) \u2014 the 17Lands GIH WR is **mature and full-format**, and the expert notes are end-of-format retrospectives (LoL's '50 Takes' finale, LR's Sunset Show, Kenji's last BLB VODs), so this reference is settled, not provisional. Big caveat: it's a **typal/synergy format**, so GIH WR is archetype-conditional \u2014 a tribal 'false friend' (Carrot Cake is great in GW Rabbits, bad in RW Mice) reads average overall but swings hard by deck. The AI take + guide notes decode which tribe a number belongs to.\n",
    "DFT": "> DFT (Aetherdrift) is the vehicles set that drove **under the speed limit** \u2014 despite the racing theme it's one of the **slower** recent formats, so plan for the long game and don't overvalue vanilla two-mana 2/2s (a good two-drop wants 3 power OR 3 toughness; 4 toughness is the magic number). The 17Lands GIH WR is a finished-format signal (Feb-Mar 2025) and CGB letter grades are pre-data theory \u2014 trust live WR on conflict. **Color order at common: Green \u2265 Black > Red = White > Blue**, but blue's *uncommons* are elite, so blue is a strong support color. GIH WR **overrates big green fatties/payoffs** (their number comes from the ramp deck) and **underrates cheap removal** \u2014 the AI take + guide notes decode which deck a number belongs to.\n",
    "OTJ": "> OTJ (Outlaws of Thunder Junction) is a **midrange, bombs-and-removal** format that plays a hair faster than it looks \u2014 draft the best bomb you open, then prioritize clean (ideally exile) removal, since the set is bomby and recursion is everywhere. Ratings are finished-format 2024 PremierDraft data (**364 of 376 cards** have a GIH WR); CGB letter grades are pre-data theory \u2014 trust live WR on conflict. **Green is the best color and GW mounts the best deck; blue is underrated/open** (uncommons wheel to pick 6+); **red is weakest.** GIH WR **inflates** multicolor good-stuff + build-around payoffs (Railway Brawler, Marchesa, crime engines) and **underrates** efficient removal (Throw from the Saddle, Desert's Due) \u2014 the AI take + guide notes decode which deck a number belongs to. **The Big Score (OTP) bonus-sheet reprints** appear one per pack; evaluate them on raw power.\n",
    "DSK": "> DSK (Duskmourn: House of Horror) is a **graveyard-matters midrange** format that plays slower than it looks \u2014 five- and six-drop bomb uncommons are real P1P1s, and the engine pairs dominate once they \"turn on.\" The three overlapping axes are **Delirium** (4+ card types in yard), **Manifest Dread**, and **Eerie** (enchantments/rooms). The 17Lands GIH WR is a finished-format signal (Sep-Oct 2024; **272 of 281 cards** have one); CGB letter grades are pre-data theory \u2014 trust live WR on conflict. **Color order: Green > Black >> Blue > White > Red** (green is busted at common AND uncommon; blue has weak commons but elite uncommons, so late blue uncommons = open). GIH WR **overrates synergy/build-around payoffs** (delirium fatties, reanimate targets, eerie/room engines post the built-around deck's number) and **underrates cheap exile removal** (Scorching Dragonfire, Nowhere to Run, Sheltered by Ghosts) \u2014 the AI take + guide notes decode which deck a number belongs to. **Four toughness is the magic number** (dodges the two premier damage-removal spells), and **exile/tuck > kill** since feeding graveyards helps your opponents.\n",
    "FIN": "> FIN is a **finished, very large sample** \u2014 42.1M PremierDraft games across 348 measured cards (the biggest in this reference), so the numbers here are settled. It is a **midrange, removal-heavy** format: the ground clogs with tokens and Job Select hero tokens, **four toughness is the magic number**, and **flying is what breaks through**. Pack 4-6 pieces of interaction. FIN is the one set here with **no reviewer-grade file**, so the tiles carry live win rates, guide notes and an AI take only. Bonus-sheet reprints have samples in the low thousands rather than the hundreds of thousands \u2014 read those tiles with much wider error bars.\n",
}
L.append("> **Ordering:** cards within each colour are ranked by a combined **ALSA + play-rate** score "
         "(rank-average of the two), not by GIH WR. Both are populated by every draft — where the field "
         "takes a card, and how often it makes the deck — so together they track pick priority. A win "
         "rate answers a different question: which decks drafted the card.\n")
L.append(CAVEAT.get(SET, ""))

# ---- archetype map (set-specific 10 color-pair guilds) -----------------------
ARCHETYPES = {
    "HOB": "**Archetype win rates** (17Lands PremierDraft, 227,771 decks, 2026-08-01 \u2192 08-19):\n\n| WR | Games | Pair | Plan | Signposts |\n|---|---|---|---|---|\n| **57.4%** | 67.3k | **BR** | Rakdos Goblins \u2014 amass one huge Army, sacrifice for value; best removal and the deepest colours. Also the most-played deck by a wide margin. Post-play read: it is a **kill-you deck, not a sacrifice-attrition deck** | Bolg of the North \u00b7 Goblin Plate Mail \u00b7 Fearsome Goblin Pair |\n| **57.3%** | 3.0k | **WB** | Orzhov \u2014 **unsupported and the best of the off-pairs.** Black's common equipment feed white's equipment/storied cards; white's tokens feed black's sac effects. Small sample, big signal | \u2014 |\n| **56.6%** | 43.9k | **BG** | Golgari Ferocious \u2014 black-shaped aggro with green bodies; power 4+ payoffs. The most explosive openers in the format. **Not** an elves/synergy deck | The Chief Warg \u00b7 Large Bear \u00b7 Duskwatch Hunter |\n| **55.7%** | 41.3k | **RW** | Boros Dwarves \u2014 storied + equipment; carried by white's rares, which get passed too late. **Storied turns on by itself** \u2014 stop building around it | Thorin Oakenshield \u00b7 D\u00e1in Ironfoot \u00b7 Dwalin, Weaponmaster |\n| **55.4%** | 39.7k | **WU** | Azorius Recruit \u2014 draw-two payoffs and go-wide tokens. Skill-intensive; **best deck in top-player stats.** Good *against* the black decks (1/1 tokens blank menace) | Bard the Bowman \u00b7 Eagle's Rescue \u00b7 Patient Instructor |\n| **53.9%** | 3.0k | **UR** | Izzet \u2014 no signpost, but blue and red are deep enough to carry it | \u2014 |\n| **53.4%** | 7.0k | **UB** | Dimir \u2014 no signpost and no plan, but black's removal carries it above the other off-pairs | \u2014 |\n| **52.2%** | 2.0k | **RG** | Gruul \u2014 unsupported; playable as straight beats if both colours are open | \u2014 |\n| **51.2%** | 19.8k | **GU** | Simic Elves/Landfall \u2014 **the worst supported deck by 4.2 points**, and still the third-most-drafted. **Don't chase elves** \u2014 play the good blue and green cards | Silvan Reveler \u00b7 Thranduil, Sindarin Liege \u00b7 Mirkwood Nurturer |\n| **46.8%** | 0.9k | **GW** | Selesnya \u2014 **the worst pairing in the format** | \u2014 |\n\n**Mono-colour benchmark:** Mono-Black **62.3%** (n=2.2k) is the highest win rate on the board \u2014 a blunt statement of how far ahead black is. Three-colour decks post **48.6%**; Sultai is **43.6%**. Splash only for removal, and only once the fixing is already in your pool.\n\n**Removal benchmarks:** the format's defining constraint is that **removal cannot kill small creatures** \u2014 no Shock, no Stab, no cheap white damage spell \u2014 so **two-drops are safe** and curve-out plans are rewarded. **Damage-based removal caps at 5**, making 6-toughness creatures (Old Fat Spider, Wilderland Scrounger) effectively unanswerable at common. Premium commons: Pinecone Strike (3 damage + exile) and Bilbo's Deadly Slice (Murder); **Stone by Sunlight is the only efficient uncommon removal** \u2014 Troll Negotiations, Burn Burn Tree and Fern and Celebrate the Mountain-king are all four mana. White gets exactly one common removal spell. **Sweepers barely exist**, so going wide is rewarded and anthems are unusually good; **lifegain barely exists**, so there is no stabilising back. **Menace is the defining keyword** \u2014 blocking is close to illegal in many games, which is why removing *a* body matters more than removing the right one. **Traps:** synergy decks you can't assemble (this is what sank Simic), splashing off the plentiful fixing, and storied/ferocious payoffs run with too few enablers.\n",
    "MSH": "MSH is a **slow, grindy goodstuff-midrange** format. Ranked by real 17Lands archetype win rate \u2014 note that Azorius is both the most-drafted pair *and* the highest-winning, while Simic is the second-best and the least-drafted (the open seat when white-blue is contested).\n\n**Archetype win rate** (17Lands PremierDraft, 634,709 two-colour games; share = portion of the two-colour metagame):\n\n| WR | Share | Pair | Plan | Key cards |\n|---|---|---|---|---|\n| **58.17%** | 27.2% | **WU** | Teamwork \u2014 tap creatures to upgrade spells; wants a body-heavy build | Captain America, Living Legend \u00b7 Spider-Woman, Secret Agent |\n| 56.93% | 8.5% | **UG** | +1/+1 counters \u2014 pile counters via power-up. **Under-drafted and good** | Ant-Man, Colony Commander \u00b7 Beast, Erudite Aerialist |\n| 56.36% | 13.7% | **WG** | Heroes-matter \u2014 go wide with ~91 heroes, low-effort payoffs | Black Panther, Vanguard \u00b7 Spider-Man, To the Rescue |\n| 55.72% | 6.5% | **BG** | Graveyard \u2014 2 creatures in yard (hit by trading); Killmonger is the linchpin | Killmonger, Scourge of Wakanda \u00b7 Titania, Rugged Rumbler |\n| 55.36% | 9.2% | **WB** | Attack-alone \u2014 one operative, pile bonuses; small equipment sub-theme | Black Widow, Double Agent \u00b7 U.S.Agent, John Walker |\n| 54.98% | 6.7% | **WR** | Spells / prowess / tricks \u2014 the most aggressive pair | Thor Odinson \u00b7 War Machine, Legacy of Iron |\n| 54.45% | 9.4% | **UB** | Villains/connive \u2014 the format's biggest expert over-rate; blue is fine, black drags | Kang the Conqueror \u00b7 Ghost, Elusive Specter |\n| 54.14% | 4.4% | **RG** | Power-up / ramp \u2014 big bodies + +1/+1 mana sinks | Hulk, Gamma Goliath \u00b7 Abomination, Terrifying Titan |\n| 52.96% | 7.8% | **UR** | Artifacts \u2014 shallowest theme; evaluate each artifact on its own, don't force | Iron Man, Master of Machines \u00b7 Speedball, New Warrior |\n| 51.91% | 6.6% | **BR** | Villains-matter \u2014 auto-on, push damage. Finishes last | Madame Hydra \u00b7 Bullseye, Death Dealer |\n\n**Removal benchmarks** (scarce and at a premium in this slow format): Dark Deed / Cruel Alliance (B), Punishing Punch (G), Web Up / Super Villain Lockup (W), Lightning Strike (R), Frozen in Ice (U). **Big-dummy rule:** expensive no-ETB vanilla creatures are traps; flyers break the format's board stalls.\n",
    "BLB": "BLB is a **typal/synergy** format \u2014 each color pair is an animal tribe with a narrow home. Think \"BG Food/Forage card,\" not \"green card.\" **The flattest format in this reference: the top five pairs sit inside 0.9pp**, so draft the open seat rather than a ranking. Start green or black \u2014 they branch into the most good pairs \u2014 and let pack 1 name the tribe.\n\n**Archetype win rate** (17Lands PremierDraft, 1,062,929 two-colour games; share = portion of the two-colour metagame):\n\n| WR | Share | Pair | Plan | Key cards |\n|---|---|---|---|---|\n| **55.91%** | 9.3% | **BR** | Lizards \u2014 cheap aggressive bodies + burn / damage payoffs | Scales of Shale \u00b7 Fireglass Mentor \u00b7 Hired Claw |\n| 55.64% | 15.4% | **WG** | Rabbits \u2014 go-wide Offspring / Food tokens, curve out fast | Carrot Cake \u00b7 Intrepid Rabbit \u00b7 Treeguard Duo |\n| 55.49% | 17.5% | **BG** | Squirrels \u2014 Forage / Food / graveyard grind (deepest, highest floor) | Cache Grab \u00b7 Scavenger's Talent \u00b7 Vinereap Mentor |\n| 55.38% | 12.5% | **WB** | Bats \u2014 lifegain triggers + drain attrition (branches well) | Starscape Cleric \u00b7 Moonrise Cleric \u00b7 Valley Rotcaller |\n| 55.03% | 12.7% | **UG** | Frogs \u2014 blink / bounce to re-trigger ETBs, grind value | Pond Prophet \u00b7 Sunshower Druid \u00b7 Three Tree Scribe |\n| 54.50% | 10.2% | **WR** | Mice \u2014 Valiant / go-wide aggro (contested; Food stalls it) | Heartfire Hero \u00b7 Manifold Mouse \u00b7 Emberheart Challenger |\n| 53.89% | 6.8% | **UB** | Rats \u2014 go-wide + discard / Threshold | Tidecaller Mentor \u00b7 Mind Drill Assailant \u00b7 Mindwhisker |\n| 53.82% | 7.2% | **RG** | Raccoons \u2014 Expend / Forage / Food goodstuff (generic) | Wandertale Mentor \u00b7 Bakersbane Duo \u00b7 Junkblade Bruiser |\n| 52.65% | 3.5% | **WU** | Birds \u2014 evasive flyers + counters | Jackdaw Savior \u00b7 Seedpod Squire \u00b7 Plumecreed Escort |\n| 51.61% | 4.9% | **UR** | Otters \u2014 spells / prowess / tempo. Last, and the field agrees | Stormcatch Mentor \u00b7 Alania's Pathmaker \u00b7 Stormsplitter |\n\n**Format principles:** medium-to-slow despite looking fast (games hit turns 10-14). **Food + lifegain are disproportionately strong.** Want a turn-2 play. Removal is scarce \u2014 prioritize cheap instant-speed (Savor is the best common in the set, then Nocturnal Hunger, Scales of Shale). **Innkeeper's and Hunter's Talent are format-warping; the other three Talents are ordinary.** Blue's *cards* are the cheapest late picks in the format even though blue's *pairs* finish 9th and 10th.\n",
    "ECL": "ECL is a **tribal-synergy** format \u2014 five two-color tribes plus real Vivid, Blight, and Fairies off-ramps. Being in a supported pair unlocks gold lords, Eclipsed cards, and Commands, so more good cards flow your way \u2014 but a **contested** tribal lane makes your deck atrocious, so read the signals and be willing to pivot. **Changelings keep you open** (they satisfy every typal payoff and count Vivid pips). Note the share column: five pairs take ~91% of the metagame and the other five are rounding errors, so those bottom rows rest on very small samples.\n\n**Archetype win rate** (17Lands PremierDraft, 805,893 two-colour games; share = portion of the two-colour metagame):\n\n| WR | Share | Pair | Plan | Key cards |\n|---|---|---|---|---|\n| **56.36%** | 23.8% | **BG** | Elves \u2014 well-sized bodies + graveyard-as-resource; token floods for inevitability | Morcan's Eyes \u00b7 Dawnhand Eulogist \u00b7 Nameless Inversion |\n| 55.86% | 20.6% | **WU** | Merfolk \u2014 tempo/convoke, tap synergies + flash; close before turn 8 (highest floor) | Deepchannel Duelist \u00b7 Merrow Skyswimmer \u00b7 Unexpected Assistance |\n| 55.72% | 15.7% | **WG** | Kithkin \u2014 weenie aggro + pump lords | Thought-Weft Lieutenant \u00b7 Clacken Festival \u00b7 Mist Meadow Council |\n| 55.18% | 18.0% | **UR** | Elementals \u2014 midrange ETB power + land-cyclers; season-long riser | Flamebraider (kill on sight) \u00b7 Ashling's Command \u00b7 Flaring Cinder |\n| 53.06% | 12.8% | **BR** | Goblins \u2014 GRINDY not aggro; win via blight-drain + triggers | Champion of the Weird \u00b7 Sour Bread Auntie \u00b7 Gristle Glutton |\n| 51.87% | 2.2% | **RG** | Treasure \u2014 really a Temur Vivid base, not a pure pair | Nogggle Robber |\n| 51.79% | 2.1% | **WR** | Blight/Giants \u2014 beatdown; less refined than BW blight | Brambleback Brute \u00b7 Cinder Strike |\n| 50.52% | 1.1% | **UG** | Unsupported \u2014 no tribe, no lords | \u2014 |\n| 50.37% | 2.1% | **UB** | Fairies/Flash \u2014 act on the opponent's turn; can trophy with no rares | Voracious Tome Skimmer \u00b7 Mischievous Sneakling \u00b7 Glamour Gifter |\n| 50.09% | 1.5% | **WB** | Blight \u2014 grindy counter value; high-toughness bodies absorb counters | Reaping Willow \u00b7 Moonlit Mentor \u00b7 Bog Slither's Embrace |\n\n**Removal benchmarks:** Cinder Strike (R, 1-mana deal-4 on blight \u2014 best common), Bog Slither's Embrace (B), Luminal Hold (W), Nameless Inversion / Sear / Feed the Flames (uncommons). **Format rules:** hold removal for lords/engines (don't push 2 damage); creature counts run 15-20 even in Vivid/Blight; two-drops without synergy are dead weight (the curve starts on three); high flash density punishes slamming into open mana; **Blight is upside only when you build for it.**\n",
    "DFT": "DFT is a **slow, grindy** format wearing a racing costume. **The three green pairs are the top three, separated by 0.23pp \u2014 a statistical tie** \u2014 so being in green matters more than which green pair. Green plays the best raw threats at common, so every other deck needs a plan to beat big green.\n\n**Archetype win rate** (17Lands PremierDraft, 872,036 two-colour games; share = portion of the two-colour metagame):\n\n| WR | Share | Pair | Plan | Key cards |\n|---|---|---|---|---|\n| **56.46%** | 15.0% | **UG** | Exhaust synergies + thopters; the ramp-soup base | Skyserpent Seeker \u00b7 Rangers' Aetherhive \u00b7 Hulldrifter |\n| 56.40% | 18.4% | **BG** | Graveyard value + exhaust, big bodies \u2014 most-drafted, safest default | Thundering Broodwagon \u00b7 Wreckage Wickerfolk \u00b7 Spin Out |\n| 56.23% | 8.3% | **WG** | Mounts/vehicles + green rate. **Under-drafted at 8.3%** | Veteran Beastrider \u00b7 Ride's End \u00b7 Stampeding Scurryfoot |\n| 55.62% | 5.8% | **WB** | Aristocrats \u2014 embalm/sacrifice value | Embalmed Ascendant \u00b7 Spin Out \u00b7 Ride's End |\n| 55.18% | 8.9% | **BR** | Start Your Engines aggro-midrange, edict into engine-start, drain | Momentum Breaker \u00b7 Gastal Thrillseeker \u00b7 Magmakin Artillerist |\n| 55.12% | 9.2% | **RG** | Exhaust big-mana stompy | Rocketeer Boostbuggy \u00b7 Hazard of the Dunes |\n| 54.62% | 12.2% | **UB** | Artifact/affinity control, thopters, Haunt the Network drain | Haunt the Network \u00b7 Pactdoll Terror \u00b7 Rangers' Refueler |\n| 54.24% | 7.6% | **WU** | Artifact-vehicles + Guidelight synergies | Guidelight Pathmaker \u00b7 Spikeshell Harrier \u00b7 Marshals' Pathcruiser |\n| 53.68% | 9.9% | **UR** | Cycling/discard + **Push the Limit** \u2014 high ceiling, low floor | Clamorous Ironclad \u00b7 Push the Limit \u00b7 Captain Howler |\n| 51.95% | 4.9% | **WR** | Pilot beatdown. **Worst archetype in the set by 1.7pp** | Cloudspire Coordinator \u00b7 Canyon Vaulter |\n\n**Removal benchmarks:** Ride's End (W, premium exile), Spin Out (B common), Momentum Breaker (B edict/tempo), Grim Bauble (B), Bounce Off (U tempo), Broadside Barrage (gold). **Format rules:** vanilla 2-mana 2/2s are below replacement (want 3 power OR 3 toughness); **aggressive white is a trap \u2014 big white only**; crew cost is the whole evaluation on a vehicle (crew 1 >> crew 3); exhaust is a mana sink, not a plan; Start Your Engines needs 3-4 turns to matter. Blue's uncommons are the best in the format and its commons are not.\n",
    "OTJ": "OTJ is a **midrange, bombs-and-removal** format \u2014 draft the best bomb you open, then prioritize clean (ideally exile) removal to answer the opponent's, because recursion is everywhere. **Green-White is both the best deck and the most-drafted at 23.7%** \u2014 a contested lane that wins anyway. Crime is a cross-color sub-theme, and the 10-desert crime-land cycle is dual-purpose fixing.\n\n**Archetype win rate** (17Lands PremierDraft, 1,148,129 two-colour games; share = portion of the two-colour metagame):\n\n| WR | Share | Pair | Plan | Key cards |\n|---|---|---|---|---|\n| **57.42%** | 23.7% | **WG** | Mounts + go-wide, big green rate + white removal, Miriam recursion | Congregation Gryff \u00b7 Miriam, Herd Whisperer \u00b7 Throw from the Saddle |\n| 56.10% | 8.7% | **WB** | Midrange crimes + recursion | Ruthless Lawbringer \u00b7 Lively Dirge \u00b7 Mourner's Surprise |\n| 55.77% | 16.2% | **BG** | Value/midrange, Honest Rutstein recursion + green rate | Honest Rutstein \u00b7 Patient Naturalist \u00b7 Throw from the Saddle |\n| 55.68% | 5.7% | **WR** | Boros go-wide aggro. **Under-drafted at 5.7% and better than its reputation** | Scalestorm Summoner \u00b7 Trained Arynx \u00b7 Skewer the Critics |\n| 55.28% | 9.0% | **RG** | Stompy \u2014 Railway Brawler makes the team huge, Dance of the Tumbleweeds ramp | Railway Brawler \u00b7 Dance of the Tumbleweeds \u00b7 Colossal Rattlewurm |\n| 54.34% | 6.5% | **UG** | Self-mill niche; the weaker half of the green pairs | Rise of the Varmints \u00b7 Patient Naturalist |\n| 53.89% | 11.0% | **UB** | Control / crime: card advantage + removal + Intimidation Campaign | Slickshot Lockpicker \u00b7 Vault Plunderer \u00b7 Intimidation Campaign |\n| 53.16% | 9.0% | **BR** | Outlaws aggro + crimes + burn | Vile Smasher \u00b7 Reckless Lackey \u00b7 Jagged Barrens |\n| 51.97% | 4.8% | **WU** | Control/tempo, \"didn't cast from hand\" payoffs | Wrangler of the Damned \u00b7 Mystical Tether \u00b7 Canyon Crab |\n| 50.80% | 5.3% | **UR** | Late-game control w/ double-spell package. **Worst archetype in the set** | Kraum \u00b7 Malcolm \u00b7 Highway Robbery |\n\n**Removal benchmarks:** Throw from the Saddle (G fight \u2014 **best common in the set**), Lassoed by the Law (W \u2014 the best white card outside the rares), Mystical Tether (W exile), Consuming Ashes (B exile), Shoot the Sheriff (B), Desert's Due (B, needs a desert). **Format rules:** 17 lands standard (18 with mana sinks); **plot is a value/late-game mechanic, NOT tempo**; **don't hold creatures waiting to commit a crime**; deserts are deck-fixing rather than picks. Blue's cheap *commons* are the format's biggest bargain even though both blue *pairs* finish last.\n",
    "DSK": "DSK is a **graveyard-matters midrange** format built on three overlapping axes \u2014 **Delirium** (4+ card types in yard), **Manifest Dread** (face-down 2/2s that fuel the yard + flip up), and **Eerie** (enchantment/room triggers). **But the two white tempo pairs win, and the dedicated graveyard decks don't** \u2014 Golgari finishes 6th, Orzhov 8th and Dimir 10th. The right amount of Delirium is incidental, not built-around. Don't over-commit before pick 5-6.\n\n**Archetype win rate** (17Lands PremierDraft, 1,215,147 two-colour games; share = portion of the two-colour metagame):\n\n| WR | Share | Pair | Plan | Key cards |\n|---|---|---|---|---|\n| **56.95%** | 15.6% | **WR** | Boros aggro \u2014 power-2-or-less tokens/gremlins, Arabella drain | Arabella, Abandoned Doll \u00b7 Midnight Mayhem \u00b7 Razorkin Hordecaller |\n| 56.43% | 17.3% | **WU** | Azorius Eerie tempo \u2014 enchantments trigger eerie + glimmers/rooms | Gremlin Tamer \u00b7 Inquisitive Glimmer \u00b7 Glimmerlight |\n| 55.65% | 13.7% | **UG** | Simic Manifest Dread engine \u2014 repeat it, flip up, refill | Oblivious Bookworm \u00b7 Paranormal Analyst \u00b7 Threats Around Every Corner |\n| 55.48% | 13.4% | **RG** | Gruul Delirium stompy \u2014 fill yard, attack with big delirium bodies | Wildfire Wickerfolk \u00b7 Beastie Beatdown \u00b7 Patchwork Beastie |\n| 54.99% | 9.8% | **BR** | Rakdos Sacrifice/Eerie \u2014 sac creatures/enchantments for value | Disturbing Mirth \u00b7 Sawblade Skinripper \u00b7 Cracked Skull |\n| 54.55% | 9.0% | **BG** | Golgari Delirium value \u2014 fill the yard fast, unlock payoffs | Broodspinner \u00b7 Drag to the Roots \u00b7 Say Its Name |\n| 52.74% | 5.0% | **WG** | Selesnya Survival \u2014 snowball beatdown via survival triggers | Shrewd Storyteller \u00b7 Orphans of the Wheat \u00b7 Hardened Escort |\n| 52.32% | 5.9% | **WB** | Orzhov Reanimator \u2014 discard/mill fatties, reanimate them | Rite of the Moth \u00b7 Miasma Demon \u00b7 Vile Mutilator |\n| 52.23% | 5.6% | **UR** | Izzet Rooms \u2014 control/burn; signposts pull opposite ways | Roaring Furnace // Steaming Sauna \u00b7 Intruding Soulrager |\n| 51.59% | 4.5% | **UB** | Dimir Eerie control \u2014 enchantments/rooms, surveil, recurring evasion | Fear of Infinity \u00b7 Nowhere to Run \u00b7 Skullcap Nuisance |\n\n**Removal benchmarks:** Scorching Dragonfire (1R: deal 3, exile) and Nowhere to Run (1B flash: -3/-3) are the premier damage removal \u2014 **four toughness is the magic number** (dodges both). Premium exile/tuck: Sheltered by Ghosts (the best card in the set outside rares), Trapped in the Screen, Unable to Scream. **Format rules:** 16-17 lands; **exile/tuck > kill** since feeding graveyards helps Delirium/Reanimator opponents; Delirium's hardest type is **artifacts**, so the artifact glue cards matter more than their rate. **Traps:** five-drop flyers with no board impact, Pyroclasm maindeck.\n",
    "SOS": "SOS is a **\"soup versus white-X aggro\"** format. Strixhaven has five college pairs rather than ten, plus an unwritten sixth archetype \u2014 **Converge / 5c soup** \u2014 that 17Lands structurally cannot measure, because its record is split across dozens of invisible three- and four-color builds. **The two white colleges are a tier of their own**, 2.3pp clear of third. Note Prismari: last of five *and* the second most-drafted, a quarter of the field in the worst college.\n\n**Archetype win rate** (17Lands PremierDraft, 907,949 two-colour games; share = portion of the two-colour metagame):\n\n| WR | Share | Pair | Plan | Key cards |\n|---|---|---|---|---|\n| **57.28%** | 22.1% | **WB** | Silverquill \u2014 Repartee aggro/tempo; target your own creatures to grow the board | Scolding Administrator \u00b7 Render Speechless \u00b7 Cost of Brilliance |\n| 56.89% | 25.6% | **WR** | Lorehold \u2014 \"leaves the graveyard\" value; assertive midrange rather than pure aggro | Rubble Rouser \u00b7 Molten Note \u00b7 Pursue the Past \u00b7 Ark of Hunger |\n| 54.57% | 12.1% | **UG** | Quandrix \u2014 ramp/fractals. Basically didn't exist as a 2-color deck; feeds soup | Cuboid Colony \u00b7 Snarl Song \u00b7 Environmental Scientist |\n| 54.05% | 16.1% | **BG** | Witherbloom \u2014 lifegain grind or +2/+2-menace overrun | Root Manipulation \u00b7 Grapple with Death \u00b7 Bogwater Luminary |\n| 54.00% | 23.8% | **UR** | Prismari \u2014 spell-density control; the natural soup base, and a trap as a 2-color deck | Elite Interceptor \u00b7 Tome Blast \u00b7 Stress Dream \u00b7 Sanar |\n\n**Removal benchmarks:** Unsubtle Mockery / Tome Blast (R), Last Gasp / Cost of Brilliance (B), Ajani's Response / Repel Calamity (W), Essence Scatter / Brush Off (U), Grapple with Death (BG). **Soup payoffs, and note how late two of them go:** Together as One (the best card in the set), Mathemagics, Snarl Song, **Arcane Omens (wheels to ALSA 5.5)**, **Potioner's Trove (the keystone, wheels to 4.6)**, Sundering Archaic, Divergent Equation, Wisdom of Ages. **Never force soup** \u2014 commit only once you have an over-the-top payoff; \"bad soup\" loses to everything. 17 lands standard, ~7-8 sources per main color.\n",
    "MKM": "MKM is a **grindy 2-color guild-midrange** format, so GIH WR transfers honestly \u2014 little soup inflation. **Boros is both the best and the most-drafted archetype**, and white's four pairs finish 1st, 2nd, 4th and 5th, so being predisposed to white is a real heuristic. Simic is the best non-white pair and under-drafted; the three black pairs finish 8th, 9th and 10th.\n\n**Archetype win rate** (17Lands PremierDraft, 900,623 two-colour games; share = portion of the two-colour metagame):\n\n| WR | Share | Pair | Plan | Key cards |\n|---|---|---|---|---|\n| **58.05%** | 20.1% | **WR** | Boros aggro/tempo \u2014 curve out, go wide, close fast. Carried by mono-color commons, NOT its signposts | Novice Inspector \u00b7 Dog Walker \u00b7 Case of the Gateway Express \u00b7 Lightning Helix |\n| 56.71% | 13.4% | **WG** | Selesnya \u2014 white-core go-wide disguise; you compromise the green plan, not the white one | On the Job \u00b7 Dog Walker \u00b7 Nervous Gardener \u00b7 Buried in the Garden |\n| 56.07% | 9.8% | **UG** | Simic \u2014 grindy value, Collect Evidence, surveil. **The open seat: best non-white pair at 9.8% share** | Projektor Inspector \u00b7 Out Cold \u00b7 Reasonable Doubt \u00b7 Doppelgang |\n| 55.33% | 12.3% | **WU** | Azorius \u2014 detective tempo, low curve, cheap interaction + flyers | Perimeter Enforcer \u00b7 Private Eye \u00b7 Granite Witness \u00b7 Novice Inspector |\n| 55.27% | 6.9% | **WB** | Orzhov \u2014 \"power 2 or less\" drain + go-wide aggro | Wisp-Drinker Vampire \u00b7 Inside Source \u00b7 Teysa, Opulent Oligarch |\n| 54.97% | 11.1% | **UR** | Izzet \u2014 artifacts/clues/thopters. High ceiling, low floor; third most-drafted for a below-median result | Gleaming Geardrake \u00b7 Detective's Satchel \u00b7 Maverick Thopterist |\n| 54.18% | 7.0% | **RG** | Gruul \u2014 big disguise, ramp into flip-up haymakers | Tin Street Gossip \u00b7 Tunnel Tipster \u00b7 Fanatical Strength |\n| 53.76% | 6.2% | **BR** | Rakdos \u2014 suspect aggro + sacrifice. Judith at 50.0% is the proof it didn't function | Rune-Brand Juggler \u00b7 Detective's Satchel \u00b7 Push // Pull |\n| 53.57% | 8.4% | **BG** | Golgari \u2014 graveyard build-around. **The format's biggest casualty; too slow** | Chalk Outline \u00b7 Insidious Roots \u00b7 Gravestone Strider |\n| 52.65% | 4.8% | **UB** | Dimir \u2014 clues control. Last, because everyone has Clue card advantage | Faerie Snoop \u00b7 Long Goodbye \u00b7 Deadly Cover-Up |\n\n**Removal benchmarks:** Long Goodbye (B uncommon, the best in the set), Extract a Confession (B common \u2014 better than Murder), Bite Down on Crime (G fight), Shock (R, edges Galvanize), Makeshift Binding (W). **Ward-2 disguise warps every removal evaluation** \u2014 a face-down creature is a ward-2 2/2, so cheap burn is often a 3-mana kill; fights, edicts and -X/-X sidestep the tax. **Format rules:** 17 lands (16 ultra-low curve, 18 for value/control); good two-drops are scarce and four-drops are everywhere, so play the mediocre two-drop but don't pick it early; the wheel is largely dead (Play Booster); Collect Evidence is free \u2014 don't warp picks for it; aim for zero Suspicious Detonation.\n",
    "FIN": "FIN is a **midrange, removal-heavy** format. Job Select warps removal evaluation (killing the 1/1 hero token while the equipment is attached is usually correct), tiered spells are why UR works, and the saga creatures are context cards rather than format pillars. Ranked by real 17Lands archetype win rate.\n\n**Archetype win rate** (17Lands PremierDraft, 1,375,424 two-colour games; share = portion of the two-colour metagame):\n\n| WR | Share | Pair | Plan | Key cards |\n|---|---|---|---|---|\n| **56.63%** | 16.9% | **UR** | Tiered spells into mana-value-4+ payoffs; counterburn tempo. The best deck AND the most-drafted | Shantotto, Tactician Magician \u00b7 The Emperor of Palamecia \u00b7 Sorceress's Schemes |\n| 56.52% | 9.5% | **WR** | Equipment / Job Select aggro. **Under-drafted at 9.5% and far better than its billing** | Samurai's Katana \u00b7 Dragoon's Lance \u00b7 Winota, Joiner of Forces |\n| 56.17% | 13.6% | **BG** | Graveyard value and reanimation | Cloud of Darkness \u00b7 Summon: Fenrir \u00b7 Summon: Fat Chocobo |\n| 56.10% | 10.2% | **WB** | Permanent-heavy with a legends subtheme | Rufus Shinra \u00b7 Sidequest: Hunt the Mark \u00b7 White Mage's Staff |\n| 55.88% | 6.6% | **WG** | Saga creatures + legends go-wide. Mid-table, not the trap it was called | Garnet, Princess of Alexandria \u00b7 Sazh's Chocobo \u00b7 Town Greeter |\n| 55.72% | 11.3% | **WU** | Flying tempo, artifacts and equipment | Cid, Timeless Artificer \u00b7 Dragoon's Wyvern \u00b7 Delivery Moogle |\n| 55.38% | 7.6% | **UG** | Value-ramp, almost always splashing a third colour | Ignis Scientia \u00b7 Esper Origins \u00b7 Combat Tutorial |\n| 54.90% | 12.1% | **UB** | Grindy removal pile + card advantage. **8th, despite being rated the #2 pair pre-data** | Sephiroth's Intervention \u00b7 Eject \u00b7 Resentful Revelation |\n| 54.62% | 7.9% | **BR** | Removal-heavy grind | Garland \u00b7 Choco-Comet \u00b7 Vayne's Treachery |\n| 53.37% | 4.3% | **RG** | Firmly worst. Guides and data agree \u2014 avoid | Chocobo Kick \u00b7 Call the Mountain Chocobo |\n\n**Removal benchmarks:** Sephiroth's Intervention (B common \u2014 a genuine first-pick), Choco-Comet (R uncommon, the best non-rare red card), Thunder Magic (R), Cornered by Black Mages (B), Ice Magic (U), Swallowed by Leviathan / Eject (U uncommons), Vayne's Treachery (B). Bonus sheet: Lightning Bolt and Fatal Push were the two reprints that mattered. **Format rules:** four toughness dodges the format's cheap removal, so it is a real layer of protection; flying breaks the board stalls; **do not pick Town lands early** (the payoffs work when assembled organically); every signpost uncommon is a legend, so don't legend-rule yourself; green needs to be pushed on you \u2014 one early green card is not a commitment.\n",
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
