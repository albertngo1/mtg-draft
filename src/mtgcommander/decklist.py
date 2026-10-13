"""Deck lists in and out: reading what players paste, matching names to real cards, and preconstructed decks.

Why a forgiving parser: lists arrive from Archidekt, Moxfield, MTG Arena, MTGO and hand-typed notes, each
with its own quantity style (`1`, `1x`, none), set/collector suffixes (`(CMM) 400`), foil marks (`*F*`),
category tags (`[Ramp]`, `[Commander{top}]`) and section headers (`Commander`, `Deck`, `Sideboard`). `parse`
accepts all of them and never fails: a line it cannot read goes to `unparsed`. `resolve` then maps each name
to the canonical Scryfall name, finds the commander, and suggests close matches for anything it does not know.

Precons come from MTGJSON: DeckList.json lists every product, deck files hold the cards. Cached 30 days
(7 for the list itself, which grows when a product is released)."""
import difflib, re, sys, urllib.parse
from . import carddb, net
from .config import DAY

MTGJSON = "https://mtgjson.com/api/v5/"
PRECON_TYPE = "Commander Deck"
SUGGEST_LIMIT = 20      # a close-match search costs ~0.1 s a name; a list in the wrong format would stall
# Header text → where the cards below it go; None means "ignore these cards" (a maybeboard is not the deck).
_SECTIONS = {"commander": "commanders", "commanders": "commanders", "deck": "cards", "main": "cards",
             "mainboard": "cards", "maindeck": "cards", "sideboard": "sideboard", "companion": "sideboard",
             "companions": "sideboard", "maybeboard": None, "considering": None, "token": None,
             "tokens": None}
_HEADER = re.compile(r"^(?://|#)?\s*(commanders?|deck|main\s*deck|main\s*board|main|side\s*board|companions?|"
                     r"maybe\s*board|considering|tokens?)\s*(?:\(\d+\))?\s*:?\s*$", re.I)
# Some exports group the deck by card type; the heading changes nothing, but must not be read as a card.
_TYPE_HEADER = re.compile(r"^(?://|#)?\s*(creatures?|instants?|sorcer(?:y|ies)|artifacts?|enchantments?|"
                          r"planeswalkers?|lands?|battles?)\s*(?:\(\d+\))?\s*:?\s*$", re.I)
_COUNT = re.compile(r"^(?:(\d+)x?\s+)?(.+?)\s*$")                 # "1 Sol Ring", "1x Sol Ring", "Sol Ring"
_CATEGORY = re.compile(r"\[([^\]]*)\]")                            # Archidekt: [Commander{top}], [Ramp]
_SET_SUFFIX = re.compile(r"\s*\([A-Za-z0-9]{2,6}\)(?:\s+[\w★†-]+)?\s*$")  # " (CMM) 400", " (cmm)"
_MARKS = re.compile(r"\s*(?:\*[A-Za-z]+\*|\^[^^]*\^)")             # *F* *E* *CMDR*  ^Tag,#color^
_SIDEBOARD_PREFIX = re.compile(r"^SB:\s*", re.I)                   # MTGO: "SB: 1 Name"
_IGNORED_CATEGORIES = {"maybeboard", "considering", "tokens"}


class UnknownPrecon(KeyError):
    """No precon has this name. `suggestions` holds the closest names."""

    def __init__(self, name, suggestions):
        super().__init__(name)
        self.name, self.suggestions = name, list(suggestions)

    def __str__(self):
        hint = "; closest: " + ", ".join(self.suggestions) if self.suggestions else ""
        return f"unknown precon {self.name!r}{hint}"


# ----------------------------------------------------------------------------- reading lists
def _categories(line):
    """Category names in [brackets], lower case, without Archidekt's {modifiers}:
    '[Commander{top}]' → ['commander']."""
    return [x.strip().lower() for c in _CATEGORY.findall(line) for x in re.sub(r"\{.*?\}", "", c).split(",")]


def parse(text):
    """Split a pasted list into {"commanders": [raw names], "cards": [(count, raw)], "sideboard": [...],
    "unparsed": [lines], "sectioned": bool, "blank_split": bool}. Names are exactly as written (set suffixes
    and marks removed); resolve() matches them to cards. `sectioned` says whether the text had
    Commander/Deck/Sideboard headers. Without headers, a blank line after the cards starts the sideboard, as
    MTGO exports do, and `blank_split` records that it was only a blank line (resolve() decides what it meant)."""
    out = {"commanders": [], "cards": [], "sideboard": [], "unparsed": [], "sectioned": False, "blank_split": False}
    section, seen_card = "cards", False
    for line in text.splitlines():
        s = line.strip()
        if not s:
            if seen_card and section == "cards" and not out["sectioned"]:
                section, out["blank_split"] = "sideboard", True
            continue
        head = _HEADER.match(s)
        if head:
            out["sectioned"] = True
            section = _SECTIONS[re.sub(r"\s+", "", head.group(1).lower())]
            continue
        if _TYPE_HEADER.match(s):
            out["sectioned"], section = True, "cards"
            continue
        if s.startswith(("#", "//")):
            continue
        where = section
        sb = _SIDEBOARD_PREFIX.match(s)
        if sb:
            s, where = s[sb.end():], "sideboard"
        categories = _categories(s)
        commander_mark = "*CMDR*" in s.upper() or "commander" in categories
        s = _MARKS.sub("", _CATEGORY.sub("", s)).strip()
        m = _COUNT.match(s)
        name = _SET_SUFFIX.sub("", m.group(2)).strip() if m else ""
        if not name:
            out["unparsed"].append(line)
            continue
        count = int(m.group(1) or 1)
        if commander_mark:
            where = "commanders"
        elif "sideboard" in categories:
            where = "sideboard"
        elif _IGNORED_CATEGORIES & set(categories):
            where = None
        if where == "commanders":
            out["commanders"].append(name)
        elif where:
            out[where].append((count, name))
        seen_card = seen_card or where == "cards"
    return out


def load(path):
    """parse() of a file; "-" reads standard input."""
    if path == "-":
        return parse(sys.stdin.read())
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return parse(f.read())


def _merge(pairs):
    """[(count, name)] with repeated names added up, in first-seen order (basics are often split by art)."""
    merged = {}
    for n, name in pairs:
        merged[name] = merged.get(name, 0) + n
    return [(n, name) for name, n in merged.items()]


def resolve(parsed, db, *, commander=None):
    """Match parsed names to cards. Returns {"commanders": [canonical], "cards": [(count, canonical)] (without
    the commanders), "unknown": [{"name": raw, "suggestions": [...]}], "warnings": [str]}.
    Where the commander comes from, in order: the `commander` argument (a name or list of names), a Commander
    section or *CMDR*/[Commander] marker, else — MTGO style — a sideboard of one or two cards that can lead a
    deck. Unknown names are reported once and left out of `cards`."""
    unknown, warnings, bad = [], [], set()

    def lookup(raw):
        rec = db.get(raw)
        if rec is None and carddb.normalize(raw) not in bad:
            bad.add(carddb.normalize(raw))
            near = db.suggest(raw) if len(unknown) < SUGGEST_LIMIT else []
            unknown.append({"name": raw, "suggestions": near})
        return rec

    raw_cmdrs = list(parsed["commanders"])
    if commander:
        given = [commander] if isinstance(commander, str) else list(commander)
        if raw_cmdrs and {carddb.normalize(c) for c in raw_cmdrs} != {carddb.normalize(c) for c in given}:
            warnings.append("the commander argument replaces the commander named in the list")
        raw_cmdrs = given
    cards = []
    for n, raw in parsed["cards"]:
        rec = lookup(raw)
        if rec:
            cards.append((n, rec["name"]))
    commanders = []
    for raw in raw_cmdrs:
        rec = lookup(raw)
        if rec and rec["name"] not in commanders:
            commanders.append(rec["name"])
    side = []
    for n, raw in parsed["sideboard"]:
        rec = db.get(raw)
        if rec:
            side.append((n, rec["name"]))
    side = _merge(side)
    if not raw_cmdrs and side and len(side) <= 2 and all(db.get(name)["commander_ok"] for _, name in side):
        commanders = [name for _, name in side]
        warnings.append("no commander was marked; using the sideboard card(s) as the commander: "
                        + ", ".join(commanders))
        side = []
    elif parsed.get("blank_split") and side:
        # Commander has no sideboard, so cards after a bare blank line are more of the deck (hand-typed lists
        # group cards with blank lines). A lone possible commander before the gap is the commander.
        lead = _merge(cards)
        if not raw_cmdrs and len(lead) == 1 and lead[0][0] == 1 and db.get(lead[0][1])["commander_ok"]:
            commanders, cards = [lead[0][1]], []
            warnings.append(f"no commander was marked; using the first card as the commander: {lead[0][1]}")
        else:
            warnings.append(f"read the {sum(n for n, _ in side)} card(s) after a blank line as part of the deck")
        cards, side = cards + side, []
    cards = _merge(cards)
    for name in commanders:           # a commander also listed among the 99 is one card, not two
        cards = [(n - 1, c) if c == name else (n, c) for n, c in cards]
    cards = [(n, c) for n, c in cards if n > 0]
    if not commanders and not raw_cmdrs:   # a named but unknown commander is already in `unknown`
        warnings.append("no commander found: mark one with a Commander section or pass it explicitly")
    if side:
        warnings.append(f"ignored {sum(n for n, _ in side)} sideboard card(s)")
    warnings += [f"could not read line: {line.strip()!r}" for line in parsed["unparsed"]]
    return {"commanders": commanders, "cards": cards, "unknown": unknown, "warnings": warnings}


def to_text(commanders, cards):
    """A list Moxfield and Archidekt both import: a Commander section, a blank line, then the Deck section,
    with lines like "1 Sol Ring". `cards` is [(count, name)]."""
    lines = ["Commander"] + [f"1 {c}" for c in commanders] + ["", "Deck"]
    return "\n".join(lines + [f"{n} {name}" for n, name in cards]) + "\n"


# ----------------------------------------------------------------------------- precons (MTGJSON)
def _entries(refresh, offline):
    """DeckList.json entries of type "Commander Deck"."""
    payload, _ = net.fetch_json(MTGJSON + "DeckList.json", source="mtgjson", key="DeckList", ttl=7 * DAY,
                                refresh=refresh, offline=offline)
    return [e for e in payload.get("data", []) if e.get("type") == PRECON_TYPE]


def precon_names(*, refresh=None, offline=None):
    """Names of all Commander precons, alphabetical."""
    return sorted({e["name"] for e in _entries(refresh, offline)}, key=str.casefold)


def pick_entry(entries, name):
    """The entry called `name`: case- and punctuation-insensitive, the newest release if the name repeats,
    else the one close spelling (typos). Raises UnknownPrecon with the closest names otherwise."""
    key = carddb.normalize(name)
    same = [e for e in entries if carddb.normalize(e["name"]) == key]
    if not same:
        keys = {carddb.normalize(e["name"]): e["name"] for e in entries}
        close = difflib.get_close_matches(key, list(keys), n=3, cutoff=0.6)
        if not close or difflib.SequenceMatcher(None, key, close[0]).ratio() < 0.85:
            raise UnknownPrecon(name, [keys[k] for k in close])
        same = [e for e in entries if carddb.normalize(e["name"]) == close[0]]
    return max(same, key=lambda e: e.get("releaseDate", ""))


def parse_deck(entry, payload, info):
    """A precon dict from a DeckList entry and its MTGJSON deck file (basics split by art are added up)."""
    data = payload.get("data") or {}
    return {"name": data.get("name") or entry["name"], "code": data.get("code") or entry["code"],
            "file": entry["fileName"], "release": data.get("releaseDate") or entry.get("releaseDate", ""),
            "commanders": [c["name"] for c in data.get("commander") or []],
            "cards": _merge((int(c.get("count", 1)), c["name"]) for c in data.get("mainBoard") or []),
            "fetched": info["fetched"], "url": info["url"]}


def _fetch_deck(entry, refresh, offline):
    payload, info = net.fetch_json(f"{MTGJSON}decks/{entry['fileName']}.json", source="mtgjson",
                                   key="deck-" + entry["fileName"], refresh=refresh, offline=offline)
    return parse_deck(entry, payload, info)


def precon(name, *, refresh=None, offline=None):
    """{"name", "code", "file", "release", "commanders": [names], "cards": [(count, name)] (the 99, without
    the commanders), "fetched", "url"}. An unknown name raises UnknownPrecon (a KeyError) with close names."""
    return _fetch_deck(pick_entry(_entries(refresh, offline), name), refresh, offline)


def _front(name):
    return carddb.normalize(name).split(" // ")[0]


def sets_printing(commander, *, refresh=None, offline=None):
    """Upper-case set codes in which Scryfall has a printing of the card (one cached search per card)."""
    term = carddb.name_term(commander)
    if term is None:
        return set()
    url = carddb.SEARCH + "?" + urllib.parse.urlencode({"q": term, "unique": "prints"})
    codes = set()
    for page_no in range(5):
        try:
            page, _ = net.fetch_json(url, source="scryfall", key=f"printings-{_front(commander)}-{page_no}",
                                     refresh=refresh, offline=offline)
        except net.NotFound:
            break
        codes |= {c["set"].upper() for c in page.get("data", []) if c.get("set")}
        url = page.get("next_page") if page.get("has_more") else None
        if not url:
            break
    return codes


def precons_for_commander(commander, *, refresh=None, offline=None):
    """Precons whose commander list holds this card, newest first. Looks up the sets the card was printed in,
    then reads only the Commander decks of those sets (a handful of cached files), not all ~200 decks."""
    codes = sets_printing(commander, refresh=refresh, offline=offline)
    decks = []
    for entry in _entries(refresh, offline):
        if entry.get("code", "").upper() in codes:
            try:
                deck = _fetch_deck(entry, refresh, offline)
            except net.NotFound:         # listed but the file is missing: skip it, do not lose the others
                continue
            if any(_front(c) == _front(commander) for c in deck["commanders"]):
                decks.append(deck)
    return sorted(decks, key=lambda d: d["release"], reverse=True)
