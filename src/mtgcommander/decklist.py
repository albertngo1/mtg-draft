"""Deck lists in and out: reading what players paste, matching names to real cards, and preconstructed decks.

Why a forgiving parser: lists arrive from Archidekt, Moxfield, MTG Arena, MTGO and hand-typed notes, each
with its own quantity style (`1`, `1x`, none), set/collector suffixes (`(CMM) 400`), foil marks (`*F*`),
category tags (`[Ramp]`, `[Commander{top}]`) and section headers (`Commander`, `Deck`, `Sideboard`). `parse`
accepts all of them and never fails on text: a line it cannot read goes to `unparsed`. `resolve` then maps each
name to the canonical Scryfall name, finds the commander, and suggests close matches for anything it does not know.

A list can also be JSON (the stripped text starts with "{" or "["): a plain deck, this tool's own base deck or saved
version, or a player's collection (`JSON_SHAPES` says which shapes; `_parse_json` reads them). JSON is either right or
wrong, so unlike text it can fail: malformed JSON or a shape the tool does not know raises ListError, with the line
and column for the first. Either way `parse` returns the same dict, so nothing downstream knows which it was.

A player who owns precons owns their cards, and a card that is free because of a box should say which box
("owned, from Peace Offering"). `boxes_of` turns what each box held into {card: [box names]}, and `attach_owned_from`
puts that list on the swaps and cards of a result: the command line and the deck server both use these two, so the
rule exists once.

Precons come from MTGJSON: DeckList.json lists every product, deck files hold the cards. Cached 30 days
(7 for the list itself, which grows when a product is released)."""
import difflib, json, os, re, sys, urllib.parse
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
_BRACKET_HEADER = re.compile(r'^\[\s*[A-Za-z][^\[\]{}"]*\]$')     # "[Commander]", Forge's "[metadata]"
# What JSON a list may be, for the message that refuses any other shape
JSON_SHAPES = ('a deck, {"commanders": ["Name"], "cards": [...], "sideboard": [...]} (the sideboard is optional), '
               'where a list of cards is [[1, "Sol Ring"]], ["Sol Ring"] or [{"name": "Sol Ring", "count": 1}]; a '
               'list of cards on its own, [...]; a base deck or a version that the deck server saved; and, only as '
               'cards you own, a collection file')


class ListError(ValueError):
    """A list that cannot be read: JSON that does not parse, a JSON shape this tool does not know, or a saved version
    whose base deck is not where it should be. The message is plain text a player can act on."""


class NotADeck(ListError):
    """A collection file was given where a deck was wanted: it lists what a player owns, not one deck's cards."""


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


def looks_like_json(text):
    """Whether a list is JSON rather than text: the stripped text (a byte order mark aside) starts with { or [. A first
    line that is only a bracketed word, such as "[Commander]" or Forge's "[metadata]", is a text section header and
    never a JSON deck, so that text is still read as text."""
    s = text.lstrip("\ufeff \t\r\n")
    if s.startswith("["):
        return not _BRACKET_HEADER.match(s.split("\n", 1)[0].strip())
    return s.startswith("{")


def parse(text, *, db=None, root=None, collection_ok=False, source=None):
    """Split a pasted list into {"commanders": [raw names], "cards": [(count, raw)], "sideboard": [...],
    "unparsed": [lines], "sectioned": bool, "blank_split": bool}. Names are exactly as written (set suffixes
    and marks removed); resolve() matches them to cards. `sectioned` says whether the text had
    Commander/Deck/Sideboard headers. Without headers, a blank line after the cards starts the sideboard, as
    MTGO exports do, and `blank_split` records that it was only a blank line (resolve() decides what it meant).

    JSON is read by `_parse_json` into the same dict; the other arguments are for it. `db` is the card index (a saved
    version needs it to replay its changes), `root` the decks folder a saved version's base deck is in,
    `collection_ok` lets a collection through (for cards a player owns; then the dict also has "precons"), and
    `source` names the list in a message ("mydeck.json"; by default "The list")."""
    if looks_like_json(text):
        return _parse_json(text, db=db, root=root, collection_ok=collection_ok, source=source or "The list")
    return parse_text(text)


def parse_text(text):
    """parse() of a list that is text, never JSON: what parse() does once it knows. It never fails. (A caller that
    reads one line at a time uses this, since a line such as "[Ramp]" alone would look like JSON.)"""
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


def load(path, *, db=None, root=None, collection_ok=False):
    """parse() of a file; "-" reads standard input. A saved version read from a file belongs to the decks folder two
    levels above it (<root>/<player>/<id>.json), which is where its base deck is looked for; read from standard input
    it belongs to `root`. `db` and `collection_ok` are parse()'s."""
    if path == "-":
        return parse(sys.stdin.read(), db=db, root=root, collection_ok=collection_ok, source="Standard input")
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    folder = os.path.dirname(os.path.dirname(os.path.abspath(path)))
    return parse(text, db=db, root=folder, collection_ok=collection_ok, source=path)


# ----------------------------------------------------------------------------- reading JSON
def _json_cards(value, where, what):
    """[(count, name)] from a JSON list of cards in any of the three shapes: [[1, "Sol Ring"]], ["Sol Ring"] or
    [{"name": "Sol Ring", "count": 1}] ("quantity" is read as "count"; no count is one copy). Anything else is a
    ListError naming the entry, since a JSON list that is half understood would quietly lose cards."""
    if value is None:
        return []
    if isinstance(value, str):                         # "commanders": "Hazel of the Rootbloom", one name as is
        value = [value]
    if not isinstance(value, list):
        raise ListError(f'{where}: "{what}" must be a list of cards, not {type(value).__name__}.')
    out = []
    for i, entry in enumerate(value, 1):
        n, name = 1, None
        if isinstance(entry, str):
            name = entry
        elif isinstance(entry, list) and len(entry) == 2:
            n, name = entry
        elif isinstance(entry, dict):
            name = entry.get("name")
            n = entry.get("count", entry.get("quantity", 1))
        if not (isinstance(name, str) and name.strip() and isinstance(n, int) and not isinstance(n, bool) and n >= 1):
            raise ListError(f'{where}: entry {i} of "{what}" is not a card: {json.dumps(entry, ensure_ascii=False)}. '
                            'Write a card as [1, "Sol Ring"], "Sol Ring" or {"name": "Sol Ring", "count": 1}.')
        out.append((n, name.strip()))
    return out


def _json_names(value, where, what):
    """The names in a JSON list of cards (a commander is one card, whatever count it was written with)."""
    return [name for _, name in _json_cards(value, where, what)]


def _parsed(commanders, cards, sideboard=(), warnings=(), sectioned=True):
    """The dict parse() returns, for a list that came as JSON (`warnings` are notes resolve() passes on)."""
    out = {"commanders": list(commanders), "cards": list(cards), "sideboard": list(sideboard), "unparsed": [],
           "sectioned": sectioned, "blank_split": False}
    if warnings:
        out["warnings"] = list(warnings)
    return out


def _saved_cards(doc, kind, db, root, where):
    """The cards of a base deck or a saved version, as decks.current replays them: a version stores its changes, not
    its cards, so its cards are its base deck's with the changes replayed, and the base deck is looked for in `root`.
    Names go through the card index by name and then by the Scryfall ids the file kept, so a card Scryfall renamed
    since still reads. Without a card index, a base deck's names are taken as written."""
    from . import decks            # here, not at the top: decks imports this module
    if kind == "base":
        if db is None:
            return _parsed(_json_names(doc.get("commanders"), where, "commanders"),
                           _json_cards(doc.get("cards"), where, "cards"))
        found = decks.current(doc, {"changes": []}, db)
    else:
        if db is None or root is None:
            raise ListError(f"{where} is a saved version, which holds the changes made to a base deck, not a card "
                            "list. Read it from its own file in the decks folder (or use stats --version PLAYER/ID).")
        base_id = doc.get("base")
        if not isinstance(base_id, str) or not decks.ID_PATTERN.fullmatch(base_id):
            raise ListError(f'{where} is a saved version that does not say which base deck it changes ("base").')
        if not isinstance(doc.get("changes", []), list):
            raise ListError(f'{where} is a saved version whose "changes" is not a list.')
        try:
            base = decks.base(root, base_id)
        except decks.NotFound:
            raise ListError(f'{where} is a saved version of the base deck "{base_id}", but there is no '
                            f'{os.path.join(root, decks.BASES, base_id + ".json")}. A version holds only its changes, '
                            "so its cards cannot be worked out without its base deck.")
        except ValueError as e:                             # the base deck's file is damaged
            raise ListError(str(e))
        found = decks.current(base, doc, db)
    return _parsed(found["commanders"], [(n, name) for n, name in found["cards"]], warnings=found["warnings"])


def _parse_json(text, *, db, root, collection_ok, source):
    """parse() of a list that is JSON (see JSON_SHAPES). A collection comes back with its loose cards as the cards
    and an extra "precons" key, and only when `collection_ok`: anywhere a deck is wanted it raises NotADeck."""
    try:
        doc = json.loads(text.lstrip("\ufeff"))
    except json.JSONDecodeError as e:
        raise ListError(f"{source} starts like JSON but is not valid JSON: {e.msg} at line {e.lineno}, column "
                        f"{e.colno}.")
    except RecursionError:
        raise ListError(f"{source} is JSON nested too deeply to read.")
    if isinstance(doc, list):
        return _parsed([], _json_cards(doc, source, "cards"), sectioned=False)
    kind = doc.get("kind") if isinstance(doc, dict) else None
    if kind in ("base", "version"):
        return _saved_cards(doc, kind, db, root, source)
    if kind == "collection":
        if not collection_ok:
            raise NotADeck(f"{source} is a collection: it lists the precons and cards a player owns, and a "
                           "collection is not a deck.")
        precons = doc.get("precons") or []
        if not isinstance(precons, list) or not all(isinstance(p, str) and p.strip() for p in precons):
            raise ListError(f'{source}: "precons" must be a list of precon names.')
        out = _parsed([], _json_cards(doc.get("cards"), source, "cards"))
        out["precons"] = [p.strip() for p in precons]
        return out
    if isinstance(doc, dict) and kind is None and "cards" in doc:
        return _parsed(_json_names(doc.get("commanders"), source, "commanders"),
                       _json_cards(doc["cards"], source, "cards"),
                       _json_cards(doc.get("sideboard"), source, "sideboard"))
    raise ListError(f"{source} is JSON in a shape this tool does not know. It reads {JSON_SHAPES}.")


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
    warnings += list(parsed.get("warnings") or [])    # a saved version's changes that could not be replayed
    return {"commanders": commanders, "cards": cards, "unknown": unknown, "warnings": warnings}


def boxes_of(found, own=()):
    """{card: [the precon names it came in, sorted]} from {card: set of precon names}, leaving out the cards in `own`.
    `own` is the deck's own cards (in `upgrade`, the list being upgraded; on the server, the base deck): they are owned
    whatever box they came in, so they are not "from" one."""
    own = set(own)
    return {card: sorted(names) for card, names in found.items() if names and card not in own}


def attach_owned_from(result, owned_from):
    """Name the box each free card comes from: every swap of an `upgrade` result and every card of a `build` result
    gets "owned_from", the precons the card came in (from `boxes_of`) when it is owned, and an empty list otherwise
    (owned some other way, or not owned), so a reader of --json can rely on the key. Returns the result."""
    for swap in result.get("swaps") or []:
        swap["owned_from"] = list(owned_from.get(swap.get("add"), ())) if swap.get("owned") else []
    cards = result.get("cards")
    for card in cards if isinstance(cards, list) else ():
        card["owned_from"] = list(owned_from.get(card.get("name"), ())) if card.get("owned") else []
    return result


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
