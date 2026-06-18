import re

# GIH WR at/above which a card counts as a "premium" — the threshold used everywhere we read
# openness (premiums seen/passed late by color). Single source of truth so etl + analysis agree.
PREMIUM_GIH = 0.55
# A premium surviving to this pick (or later) means the color is underdrafted upstream — too early
# before this and a strong card showing up means nothing.
OPEN_LATE_PICK = 5

_CONVERGE_RX = re.compile(r"\bconverge\b|colou?rs? of mana spent|for each colou?r of mana", re.I)
def _inflation(meta, tags):
    """Flag (with a plain-English caveat) cards whose GIH overstates their value in a clean 2-color
    deck. Only the *mechanically verifiable* cases — Converge/colors-of-mana and {X} costs — never a
    fuzzy 'this looks like a payoff' guess, which would re-introduce over-correction."""
    text = meta.get("text", "") or ""
    mana = meta.get("mana", "") or ""
    if "converge" in tags or _CONVERGE_RX.search(text):
        return {"kind": "converge",
                "note": "GIH reflects 4–5c soup pilots (scales with colors of mana spent); in a "
                        "2-color deck this plays as X≈2 — read it well below the headline."}
    if "{X}" in mana:
        return {"kind": "x-cost",
                "note": "X-cost: GIH skews to games where X was paid large; its value tracks the "
                        "mana you have spare, not the headline number."}
    return None
_REMOVAL_RX = re.compile(
    r"destroy target|exile target (creature|permanent|artifact|enchantment|nonland|tapped)|"
    r"deals \d+ damage to (any target|target|each|it)|fight|gets [-−]\d+/[-−]\d+|"
    r"[-−]\d+/[-−]\d+ until|tap target|can't block", re.I)
def _kind(type_line):
    t = type_line or ""
    if "Land" in t:
        return "land"
    if "Creature" in t or "Vehicle" in t:
        return "creature"
    if "Instant" in t or "Sorcery" in t:
        return "spell"
    return "other"
_TAG_RX = [
    # --- generic / always-on ---
    ("life-loss",       re.compile(r"loses? \d+ life|lose life|each opponent loses|drain", re.I)),
    ("lifegain",        re.compile(r"gains? \d+ life|gain life|lifelink", re.I)),
    ("ward",            re.compile(r"\bward\b", re.I)),
    ("counters",        re.compile(r"\+1/\+1 counter", re.I)),
    ("sacrifice",       re.compile(r"sacrifice", re.I)),
    ("graveyard",       re.compile(r"graveyard", re.I)),
    ("tokens",          re.compile(r"create .*token", re.I)),
    ("exile",           re.compile(r"\bexile", re.I)),
    ("evasion",         re.compile(r"flying|menace|can't be blocked|skulk|intimidate|trample", re.I)),
    ("card-draw",       re.compile(r"draw (a|one|two|three|\d+) card", re.I)),
    # --- MKM (Murders at Karlov Manor) ---
    ("clues",           re.compile(r"investigate|\bclue", re.I)),
    ("disguise",        re.compile(r"disguise|\bcloak\b", re.I)),
    ("collect-evidence", re.compile(r"collect evidence", re.I)),
    ("suspect",         re.compile(r"\bsuspect", re.I)),
    ("cases",           re.compile(r"to solve|solved\b", re.I)),
    # --- SOS / Secrets of Strixhaven (school spellslinger · soup · the five colleges) ---
    # Verified against the cached SOS pool — these are SOS's real keywords (magecraft/learn/lesson
    # from the ORIGINAL Strixhaven do NOT appear here; this set uses prepared/converge/paradigm).
    ("spells-matter",   re.compile(r"instant or sorcery|noncreature spell|whenever you cast", re.I)),
    ("prepared",        re.compile(r"\bprepared\b", re.I)),                 # creature ⁠// spell-half copy
    ("converge",        re.compile(r"\bconverge\b", re.I)),                 # soup payoff: scales w/ colors of mana
    ("paradigm",        re.compile(r"\bparadigm\b", re.I)),                 # recast the spell from exile
    ("fractal",         re.compile(r"\bfractal\b", re.I)),                  # Quandrix 0/0 +1/+1-counter token
    ("flashback",       re.compile(r"\bflashback\b|cast .{0,30}from your graveyard", re.I)),  # Lorehold gy value
]
# --- Typal / tribal detection (set-agnostic) -----------------------------------------------------
# In MTG oracle text creature types are Capitalized when used as a type ("other Squirrels you
# control", "whenever a Bird enters"), so we capture Capitalized tokens inside genuinely typal
# phrasings and drop the non-type words a capitalized-token grab would otherwise catch.
_NOT_A_TRIBE = {"Creature", "Creatures", "Token", "Tokens", "Permanent", "Permanents", "Player",
                "Players", "Opponent", "Opponents", "Card", "Cards", "Spell", "Spells", "Land",
                "Lands", "Color", "Colors", "Counter", "Counters", "Artifact", "Enchantment",
                "This", "Whenever", "When", "Target", "Each", "Another", "Other", "Attacking",
                "Blocking", "Blocked", "Tapped", "Untapped", "Defending", "Nonland", "Nontoken",
                "Legendary", "Basic", "Snow", "Modified", "Equipped", "Enchanted", "Saddled",
                "Chosen", "Named", "Up", "All", "Any", "Until", "Their", "Your", "Damage",
                "Noncreature", "Nonland", "Sacrificed", "Attacked"}
_IRREGULAR = {"mice": "Mouse", "wolves": "Wolf", "elves": "Elf", "dwarves": "Dwarf",
              "thieves": "Thief", "leeches": "Leech", "foxes": "Fox", "sphinxes": "Sphinx"}
def _norm_tribe(s):
    """Normalize a captured payoff-tribe token to its canonical singular Capitalized form so it
    matches Scryfall subtypes ('Squirrels'->'Squirrel', 'Mice'->'Mouse'). Leaves -ss/-us singulars
    (Fungus) alone."""
    k = (s or "").strip().lower()
    if k in _IRREGULAR:
        return _IRREGULAR[k]
    if k.endswith("s") and not k.endswith(("ss", "us")) and len(k) > 3:
        k = k[:-1]
    return k.capitalize()
_CHANGELING_RX = re.compile(r"is every creature type|\bchangeling\b", re.I)
# Typal-payoff phrasings → capture the referenced creature type(s). Patchwork-Banner-style
# "of the chosen type" is a FLEX anthem (names whatever your dominant tribe is).
_PAYOFF_RXS = [
    re.compile(r"\b([A-Z][a-z]+)s?\s+(?:creatures?\s+)?you control\s+(?:get|gets|gain|gains|have|has)\b"),
    re.compile(r"whenever (?:a|an|another)\s+([A-Z][a-z]+)(?:\s+or\s+(?:a|an|another)?\s*([A-Z][a-z]+))?\b"),
    re.compile(r"for each (?:other\s+)?([A-Z][a-z]+)\b"),
    re.compile(r"\b([A-Z][a-z]+)\s+spells?\s+you cast\b"),
]
def _changeling(meta):
    return bool(_CHANGELING_RX.search(meta.get("text", "") or ""))
def _tribal_payoff(meta):
    """If the card rewards a creature type (lord/anthem/typal-ETB/count/cast payoff), return
    {tribes:[...], flex:bool, kind:str}; else None. `flex` = names "the chosen type" (Patchwork
    Banner), so it serves whatever tribe you're densest in. Set-agnostic — works off oracle text."""
    text = meta.get("text", "") or ""
    if not text:
        return None
    flex = bool(re.search(r"of the chosen type", text, re.I))
    tribes = set()
    for rx in _PAYOFF_RXS:
        for m in rx.finditer(text):
            for g in m.groups():
                if g:
                    tribes.add(g)
    tribes = {_norm_tribe(t) for t in (tribes - _NOT_A_TRIBE)}
    if not tribes and not flex:
        return None
    return {"tribes": sorted(tribes), "flex": flex, "kind": "anthem" if flex else "typal"}
def _card_tags(meta):
    """Tag a card by mechanic/theme + role so pool-wide archetype leanings can be aggregated."""
    text = meta.get("text", "") or ""
    cmc, tl = meta.get("cmc"), meta.get("type", "")
    tags = [name for name, rx in _TAG_RX if rx.search(text)]
    if _REMOVAL_RX.search(text):
        tags.append("removal")
    if _changeling(meta):
        tags.append("changeling")
    if _tribal_payoff(meta):
        tags.append("tribal-payoff")
    if _kind(tl) == "creature" and isinstance(cmc, int):
        if cmc <= 2:
            tags.append("early-creature")
        if cmc >= 5:
            tags.append("top-end")
    return tags
def _tribes(cards):
    """Count creature subtypes across a card pool to surface tribal axes (e.g. Detective is a
    real MKM axis). Only counts subtypes on creature-type cards — subtypes also exist on lands /
    artifacts / enchantments (e.g. 'Equipment', 'Aura'), which aren't tribes. Returns an ordered
    {subtype: count} dict, most-common first."""
    from collections import Counter
    c = Counter()
    for card in cards:
        if _kind(card.get("type_line") or card.get("type")) != "creature":
            continue
        for st in card.get("subtypes") or []:
            c[st] += 1
    return dict(c.most_common())
def _tribes_readable(tribes, minimum=3):
    """Plain-English top tribes worth coaching on: 'Detective 5, Human 4'. Empty when no
    subtype reaches `minimum` (a 1-of isn't a tribe)."""
    return ", ".join(f"{st} {n}" for st, n in tribes.items() if n >= minimum)
_TRIBE_LIVE = 3   # a tribe is "live" (turns on its payoffs) at this many members (incl. changelings)
_PIP_RX = re.compile(r"\{([^}]+)\}")
def _castable_in(card, colors):
    """True if `card` is playable in a deck of `colors`. HYBRID-AWARE: parses the mana cost when
    present so a hybrid pip ({W/B}, {2/R}) is castable if EITHER side is available (or it's
    generic/Phyrexian), not treated as needing both colors. Falls back to the card's color letters
    when no mana string is stored (older cache). `colors` None/empty = no filter (whole pool)."""
    if not colors:
        return True
    on = set(colors.upper())
    mana = card.get("mana")
    if mana:
        for g in _PIP_RX.findall(mana):
            parts = g.split("/")
            # a pip is satisfiable if any option is generic/X/snow/Phyrexian (non WUBRG) or on-color
            if any(p not in "WUBRG" for p in parts) or any(p in on for p in parts):
                continue
            return False                            # every option is an off-color colored pip
        return True
    return all(ch in on for ch in (card.get("color") or "") if ch in "WUBRG")
def tribal_read(cards, colors=None):
    """Tribal-COHERENCE read over a set of (enriched) cards — the axis that actually decides value in
    a typal set (BLB Squirrels/Birds, etc.), which raw color/curve metrics miss. Returns the dominant
    tribe, how many creatures FEED it (changelings count as every tribe — pure glue), the tribal
    PAYOFFS present and whether each is fed enough to turn on, and the off-tribe 'false friend' count.
    Pass `colors` to read only the cards castable in the deck's colors — without it, off-color cuts in
    the pool pollute the dominant tribe (a WU Birds deck reads as 'Mouse' off its cut red Mice). Empty
    dict when there's no tribal axis (no tribe reaches _TRIBE_LIVE and no payoff) — so non-typal
    decks/sets stay quiet and this never invents synergy that isn't there."""
    from collections import Counter
    cards = [c for c in cards if _castable_in(c, colors)]
    creatures = [c for c in cards if _kind(c.get("type_line") or c.get("type")) == "creature"]
    tribes = Counter()
    changelings = []
    for c in creatures:
        if c.get("changeling") or "changeling" in (c.get("tags") or []):
            changelings.append(c["name"])
        for st in c.get("subtypes") or []:
            tribes[st] += 1
    n_change = len(changelings)
    payoffs = [c for c in cards if c.get("tribal_payoff") or "tribal-payoff" in (c.get("tags") or [])]
    dominant, dom_count = (tribes.most_common(1)[0] if tribes else (None, 0))
    fed = dom_count + n_change
    if (fed < _TRIBE_LIVE) and not payoffs:
        return {}
    def _fed(tp):
        if not tp:
            return None
        if tp.get("flex"):
            return True
        return any((tribes.get(t, 0) + n_change) >= _TRIBE_LIVE for t in tp.get("tribes") or [])
    payoff_rows = []
    for c in payoffs:
        tp = c.get("tribal_payoff") or {"tribes": [], "flex": True, "kind": "typal"}
        payoff_rows.append({"name": c["name"], "tribes": tp.get("tribes") or [],
                            "flex": bool(tp.get("flex")), "kind": tp.get("kind"),
                            "fed": bool(_fed(tp))})
    off = [c["name"] for c in creatures
           if dominant and not (c.get("changeling") or "changeling" in (c.get("tags") or []))
           and dominant not in (c.get("subtypes") or [])]
    return {
        "dominant": dominant, "dominant_count": dom_count, "changelings": changelings,
        "fed": fed, "creatures": len(creatures),
        "concentration": round(fed / len(creatures), 2) if creatures else 0.0,
        "payoffs": payoff_rows, "payoffs_fed": sum(1 for p in payoff_rows if p["fed"]),
        "off_tribe": off,
    }
def tribal_readable(read):
    """Plain-English tribal coherence: 'Squirrel 11/16 (incl 2 changelings) · 3 payoffs fed'. ''
    when there's no tribal axis or no dominant tribe worth coaching on."""
    if not read or not read.get("dominant"):
        return ""
    parts = [f"{read['dominant']} {read['fed']}/{read['creatures']}"]
    nch = len(read.get("changelings") or [])
    if nch:
        parts[0] += f" (incl {nch} changeling{'s' if nch > 1 else ''})"
    pcount = len(read.get("payoffs") or [])
    if pcount:
        fedp = read.get("payoffs_fed", 0)
        tail = f"{pcount} payoff{'s' if pcount > 1 else ''}"
        tail += " fed" if fedp == pcount else f", {fedp}/{pcount} fed"
        parts.append(tail)
    noff = len(read.get("off_tribe") or [])
    if noff:
        parts.append(f"{noff} off-tribe")
    return " · ".join(parts)
def _archetype_lean(themes, curve, counts):
    """Rank the pool's strongest archetype signals (themes manifest, not prescribe). Aggro is a
    curve/creature read; the rest are scored by theme density and only the top couple are returned."""
    leans = []
    nonland = sum(curve.values()) or 1
    low = sum(n for mv, n in curve.items() if mv <= 2)
    if counts.get("creature", 0) >= 14 and low / nonland >= 0.45:
        leans.append("aggro / low-curve")
    scored = [
        ("aristocrats (sacrifice / life-loss)", themes.get("sacrifice", 0) + themes.get("life-loss", 0)),
        ("lifegain / lifedrain", themes.get("lifegain", 0) + themes.get("life-loss", 0)),
        ("clue / artifact value", themes.get("clues", 0)),
        ("graveyard / flashback value",
         themes.get("graveyard", 0) + themes.get("collect-evidence", 0) + themes.get("flashback", 0)),
        ("+1/+1 counters / fractals", themes.get("counters", 0) + themes.get("fractal", 0)),
        ("exile-matters", themes.get("exile", 0)),
        ("disguise / face-down tempo", themes.get("disguise", 0) + themes.get("ward", 0)),
        ("spellslinger (instants & sorceries)",
         themes.get("spells-matter", 0) + themes.get("paradigm", 0)),
        # soup is rare-but-loud: a few Converge/paradigm payoffs already signal the multicolor plan.
        ("soup / Converge (multicolor value)", themes.get("converge", 0) * 2 + themes.get("paradigm", 0)),
    ]
    strong = sorted((x for x in scored if x[1] >= 6), key=lambda x: -x[1])
    leans += [name for name, _ in strong[:2]]
    return leans
COLOR_NAMES = {"W": "white", "U": "blue", "B": "black", "R": "red", "G": "green", "C": "colorless"}
def _color_phrase(counter):
    """Spell out a {color-letter: count} map in plain English, most-passed first:
    {"G": 20, "R": 14, "U": 6} -> '20 green, 14 red, 6 blue'. Empty -> '' (caller skips it)."""
    items = sorted(counter.items(),
                   key=lambda kv: (-kv[1], "WUBRG".index(kv[0]) if kv[0] in "WUBRG" else 99))
    return ", ".join(f"{n} {COLOR_NAMES.get(ch, ch)}" for ch, n in items if n)
def _premiums_seen_by_color(offered_cards):
    """Premium cards (GIH WR >= PREMIUM_GIH) SEEN across a set of offered cards, counted by color
    pip. SEEN = taken + passed — the *unconfounded* supply reaching the seat. Reading openness off
    cards *passed* is blind to your own colors (you keep the premiums you take, so your drafted color
    never accumulates a passed count and reads as dry); counting what you SAW fixes that confound."""
    from collections import Counter
    return Counter(ch for c in offered_cards
                   if c.get("gih") and c["gih"] >= PREMIUM_GIH
                   for ch in (c.get("color") or "") if ch in "WUBRG")
def _open_color_signal(picks):
    """Open-color read: premium cards (GIH >= PREMIUM_GIH) still SEEN late (pick >= OPEN_LATE_PICK)
    by color. A premium surviving to pick 5+ means that color is underdrafted upstream WHETHER OR NOT
    you took it — so we count every offered card (taken + passed), not just the ones you let go.
    Returns (signal_list, readable_phrase) with colors at >=4 late premiums seen, most-seen first."""
    from collections import Counter
    seen = Counter()
    for p in picks:
        if p["pick"] >= OPEN_LATE_PICK:
            seen += _premiums_seen_by_color(p["offered"])
    signal = [{"color": col, "color_name": COLOR_NAMES.get(col, col), "late_premiums_seen": n}
              for col, n in seen.most_common() if n >= 4]
    readable = ", ".join(f"{s['late_premiums_seen']} {s['color_name']}" for s in signal)
    return signal, readable
def _deck_needs(n, creatures, two_drops, removal, curve):
    """What the deck still needs RIGHT NOW, scaled to how far through the draft you are — so it reads
    'low on 2-drops' as a live priority instead of screaming 'few creatures' at pick 3. Targets are
    the Be-Boring/CABS end-state (16 creatures · 6 two-drops · 3-4 removal · ≤6 at 5+ MV)."""
    frac = min(1.0, n / 42.0)                       # ~fraction of a 45-card pool drafted
    needs = []
    if two_drops < round(6 * frac):   needs.append(f"2-drops ({two_drops})")
    if removal < round(3.5 * frac):   needs.append(f"removal (~{removal})")
    if creatures < round(16 * frac):  needs.append(f"creatures ({creatures})")
    five_plus = sum(v for k, v in curve.items() if int(k) >= 5)
    if five_plus > 6:                 needs.append(f"top-heavy ({five_plus} at 5+)")
    return needs
