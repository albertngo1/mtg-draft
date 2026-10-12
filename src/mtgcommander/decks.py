"""Saved decks: base decks and each player's versions of them, kept as JSON files in the repo.

A *base deck* is where a deck starts, a precon or a pasted list; it is written once and never changes. A *version* is
one player's copy of a base deck plus every change they made to it. Each is one file under `root` (config.DECKS, that
is commander/decks/ in the repo):

    bases/<base-id>.json          a base deck
    <player>/<version-id>.json    a version, in its player's own folder

Why a change log and not a card list. A version stores only its changes (add, cut, swap, group, undo). Its card list
is the base's cards with the changes replayed in order (`current`), so the log and the list can never disagree, "cards
added" and "cards cut" are just the difference between that list and the base's, and no history is lost. Changes are
only ever appended: an undo is a new entry that points at an older one, so a file only grows and two players'
edits to different versions never touch the same lines in git. Each change keeps the card's Scryfall `oracle_id`
beside its name, and a base keeps an `ids` map for the same reason, so a card Scryfall later renames still replays. A
file holds names and changes only, never a score, price or other number a data source supplied.

Who may change a file. `revision` counts a version's saved writes. Every change says which revision it was made on, and
a stale one is refused (`Conflict`) before anything else is checked, so a phone and a desktop tab cannot overwrite each
other. A threading lock per file covers each read, check and write. There is no lock between processes (`fcntl` does
not exist on Windows, and the repo ships `.bat` launchers), so the files assume one server process per repo. Every
write goes to a temporary file in the same folder that is then renamed over the old file, so a reader never sees half
a file.

On disk a file is `json.dumps(indent=1, ensure_ascii=False)` with a newline at the end, except that each card of a
base and each change of a version sits on one line, so a git diff shows one line per card or change. Keys come in this
order (a key the tool does not know is kept, after these):

    base      schema, kind, id, name, source, commanders, cards, created, created_by, ids
    version   schema, kind, id, player, name, base, settings, revision, created, updated, notes, changes

Every function that reads or writes files takes `root` first (tests pass a temporary folder), and the card index `db`
where it needs card facts. Mistakes raise `DeckError` or one of its subclasses; each has a `status`, the HTTP code a web
server would answer with, and a `message` a player can read. A file that cannot be read at all (a git merge conflict
left markers in it) raises `ValueError` naming the file; the listing functions skip such a file and name it in
`WARNINGS` instead."""
import contextlib, copy, json, os, re, threading, time, unicodedata
from . import carddb, decklist, net

SCHEMA = 1
BASES = "bases"                  # the folder of base decks, which is why no player can be called "bases"
ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")   # an id is a file name, so only what slug() can make is allowed
ID_MAX = 64
# Names Windows keeps for devices: a file called con.json cannot be created there (the repo ships .bat launchers)
WINDOWS_DEVICE_NAMES = {"con", "prn", "aux", "nul"} | {f"{port}{i}" for port in ("com", "lpt") for i in range(1, 10)}
MANUAL, SUGGESTED = "manual", "suggested"   # who made a change: the player, or the tool's suggestion
SOURCES = (MANUAL, SUGGESTED)
OP_CARDS = {"add": ("add",), "cut": ("cut",), "swap": ("cut", "add")}   # the card names a stored op holds
CHANGE_OPS = tuple(OP_CARDS) + ("group", "undo")   # a group holds a list of add, cut and swap items
SUGGESTIONS_SHOWN = 3            # close names offered for a card name nobody knows
NAMES_SHOWN = 8                  # names listed in one message
BASE_KEYS = ("schema", "kind", "id", "name", "source", "commanders", "cards", "created", "created_by", "ids")
VERSION_KEYS = ("schema", "kind", "id", "player", "name", "base", "settings", "revision", "created", "updated",
                "notes", "changes")
KEY_ORDER = {"base": BASE_KEYS, "version": VERSION_KEYS}
ONE_LINE_LISTS = ("cards", "changes")     # lists written with one item to a line
# The fields the code relies on, per kind of file: field -> (type, default). A hand-edited file that leaves one out
# gets the default; a default of None means the file cannot do without it.
FILE_FIELDS = {
    "base": {"name": (str, None), "commanders": (list, []), "cards": (list, []), "ids": (dict, {})},
    "version": {"name": (str, None), "base": (str, None), "settings": (dict, {}), "revision": (int, 0),
                "changes": (list, [])},
}
COLOR_WORDS = {"W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green"}

WARNINGS = []                    # non-fatal problems (a deck file that could not be read); callers print and clear them
_LOCKS = {}                      # file path -> the lock for reading, checking and writing that file
_LOCKS_GUARD = threading.Lock()


# ----------------------------------------------------------------------------- errors
class DeckError(Exception):
    """A request the deck store cannot carry out because its shape is wrong: an unknown op, a missing field, a bad id.
    `status` is the HTTP code a web server would answer with; `message` is text a player can read."""
    status = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class NotFound(DeckError):
    """No such player, base or version, or no such precon (then `suggestions` holds the closest names)."""
    status = 404

    def __init__(self, message, suggestions=()):
        super().__init__(message)
        self.suggestions = list(suggestions)


class Conflict(DeckError):
    """The deck changed since the caller read it (`revision` is the current one), or the id is already taken
    (`revision` is None)."""
    status = 409

    def __init__(self, message, revision=None):
        super().__init__(message)
        self.revision = revision


class Invalid(DeckError):
    """The request is well formed but breaks a deck rule, or a pasted list has lines that cannot be read. `details`
    lists the problems as {"text", "suggestions"} (a pasted list's also have a "line" number); it is empty when the
    message says everything."""
    status = 422

    def __init__(self, message, details=()):
        super().__init__(message)
        self.details = list(details)


# ----------------------------------------------------------------------------- small helpers
def slug(text):
    """An id made from a name: 'Squirrels go wide' -> 'squirrels-go-wide'. Accents go, apostrophes vanish, every other
    run of characters becomes one hyphen, and the result is cut to 64 characters. It is "" when the text holds no
    letter or digit (the caller then asks for an id)."""
    s = unicodedata.normalize("NFKD", str(text or ""))
    s = "".join(c for c in s if not unicodedata.combining(c)).casefold().replace("æ", "ae")
    s = re.sub(r"['‘’`´]", "", s)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:ID_MAX].rstrip("-")


def _check_id(kind, value):
    """`value` if it is a valid id, else DeckError. Ids become file and folder names, so nothing else gets through
    (fullmatch, not match: '$' would let a trailing newline in)."""
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise DeckError(f"{value!r} is not a valid {kind} id: use 1 to {ID_MAX} lowercase letters, digits and "
                        "hyphens, starting with a letter or a digit.")
    if value in WINDOWS_DEVICE_NAMES:
        raise DeckError(f'"{value}" cannot be a {kind} id: Windows keeps that name for a device, so the file could '
                        "not be saved there. Pick another name.")
    return value


def _check_player(player):
    _check_id("player", player)
    if player == BASES:
        raise DeckError(f'"{BASES}" is the folder of base decks, so it cannot be a player name.')
    return player


def _text(value, what):
    """`value` with the spaces trimmed, if it is some text; else DeckError saying `what` was wrong."""
    if not isinstance(value, str) or not value.strip():
        raise DeckError(f"{what} is missing or is not text.")
    return value.strip()


def _whole_number(value, what, least=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < least:
        raise DeckError(f"{what} must be a whole number of at least {least}.")
    return value


def _settings(value):
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise DeckError('"settings" must be an object, for example {"bracket": 3, "budget": 200}.')
    return copy.deepcopy(value)


def _stamp(now):
    """The time to record: `now` (like '2026-10-11T20:05:00Z'; tests pass it) or the current time."""
    return now or net.iso(time.time())


def _names(names):
    """'A, B, C' for a message; a long list ends 'and N more'."""
    shown = ", ".join(names[:NAMES_SHOWN])
    return shown + (f", and {len(names) - NAMES_SHOWN} more" if len(names) > NAMES_SHOWN else "")


def _color_words(letters):
    """'Black and Green' for 'BG'; 'colorless' for no colors."""
    words = [COLOR_WORDS[c] for c in "WUBRG" if c in letters]
    if not words:
        return "colorless"
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def _plural(n, noun):
    return f"{n} {noun}" + ("" if n == 1 else "s")


def _lock(path):
    """The lock that makes one file's read, check and write a single step for the threads of this process."""
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(os.path.abspath(path), threading.Lock())


# ----------------------------------------------------------------------------- reading and writing files
def _base_path(root, base_id):
    return os.path.join(root, BASES, base_id + ".json")


def _version_path(root, player, version_id):
    return os.path.join(root, player, version_id + ".json")


def _check_fields(doc, kind, path):
    """Fill in what a hand-edited file left out and refuse what it got wrong, so the code below can trust the shape."""
    for field, (wanted, default) in FILE_FIELDS[kind].items():
        value = doc[field] if field in doc else copy.deepcopy(default)
        if not isinstance(value, wanted) or (wanted is int and isinstance(value, bool)):
            raise ValueError(f"{path} has a bad or missing {field!r}.")
        doc[field] = value


def _read(path, kind):
    """The parsed deck file, or None when there is none. A file that exists but cannot be used raises ValueError
    that names it. The id (and a version's player) always come from where the file is, so a copied file cannot
    claim another deck's id."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:        # a JSON error is a ValueError; so is bad UTF-8
        raise ValueError(f"{path} could not be read: {e}")
    if not isinstance(doc, dict) or doc.get("kind") != kind or doc.get("schema") != SCHEMA:
        raise ValueError(f"{path} is not a {kind} file of schema {SCHEMA}, the only kind this version of the tool "
                         "reads.")
    _check_fields(doc, kind, path)
    doc["id"] = os.path.basename(path)[:-len(".json")]
    if kind == "version":
        doc["player"] = os.path.basename(os.path.dirname(path))
    return doc


def _line(value):
    return json.dumps(value, ensure_ascii=False)


def _render(doc):
    """The text of a deck file: the layout of json.dumps(doc, indent=1, ensure_ascii=False), with the keys in the
    documented order and each item of a list in ONE_LINE_LISTS on a single line."""
    order = KEY_ORDER[doc["kind"]]
    keys = [k for k in order if k in doc] + [k for k in doc if k not in order]
    rows = []
    for key in keys:
        value = doc[key]
        if key in ONE_LINE_LISTS and isinstance(value, list) and value:
            items = ",\n".join("  " + _line(item) for item in value)
            rows.append(f" {_line(key)}: [\n{items}\n ]")
        else:
            body = json.dumps(value, indent=1, ensure_ascii=False).replace("\n", "\n ")
            rows.append(f" {_line(key)}: {body}")
    return "{\n" + ",\n".join(rows) + "\n}\n"


def _write(path, doc):
    """Save `doc` atomically: write a temporary file in the same folder, then rename it over `path`. If anything
    fails the old file is as it was and no temporary file stays behind."""
    text = _render(doc)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())               # the new content is on disk before the name points at it
        os.replace(tmp, path)
    except BaseException:
        carddb.discard(tmp)
        raise


def _load_all(folder, kind):
    """Every readable deck file of `kind` in `folder`, in file-name order. A file that cannot be read is skipped and
    named in WARNINGS, so one damaged file does not hide the others."""
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return []
    out = []
    for name in names:
        if not name.endswith(".json") or not ID_PATTERN.fullmatch(name[:-len(".json")]):
            continue                            # a temporary file, a stray note, a folder named by hand
        try:
            doc = _read(os.path.join(folder, name), kind)
        except ValueError as e:
            WARNINGS.append(str(e))
            continue
        if doc is not None:
            out.append(doc)
    return out


# ----------------------------------------------------------------------------- listing and reading
def players(root):
    """The players: the folders under `root` except "bases" (a folder that is not a valid id is not a player)."""
    try:
        names = os.listdir(root)
    except OSError:
        return []
    return sorted(n for n in names
                  if n != BASES and ID_PATTERN.fullmatch(n) and os.path.isdir(os.path.join(root, n)))


def bases(root):
    """Every base deck, sorted by name."""
    return sorted(_load_all(os.path.join(root, BASES), "base"), key=lambda b: (b["name"].casefold(), b["id"]))


def base(root, base_id):
    """One base deck. Raises NotFound when there is none."""
    doc = _read(_base_path(root, _check_id("base", base_id)), "base")
    if doc is None:
        raise NotFound(f'There is no base deck with the id "{base_id}".')
    return doc


def versions(root, player):
    """Every version a player has, newest first (by when it was created, so editing a deck does not move it).
    Raises NotFound when the player has no folder."""
    folder = os.path.join(root, _check_player(player))
    if not os.path.isdir(folder):
        raise NotFound(f'There is no player called "{player}".')
    found = sorted(_load_all(folder, "version"), key=lambda v: v["id"])
    return sorted(found, key=lambda v: str(v.get("created", "")), reverse=True)    # a stable sort keeps ids in order


def version(root, player, version_id):
    """One version. Raises NotFound when the player or the version is missing."""
    _check_player(player)
    doc = _read(_version_path(root, player, _check_id("version", version_id)), "version")
    if doc is None:
        if not os.path.isdir(os.path.join(root, player)):
            raise NotFound(f'There is no player called "{player}".')
        raise NotFound(f'{player} has no version with the id "{version_id}".')
    return doc


def _base_of(root, doc):
    """The base deck a version was made from (NotFound if its file is gone; ValueError if the version names an
    impossible id, which only a hand edit can do)."""
    if not ID_PATTERN.fullmatch(doc["base"]):
        raise ValueError(f'The version "{doc["id"]}" names a base deck with an impossible id: {doc["base"]!r}.')
    try:
        return base(root, doc["base"])
    except NotFound:
        raise NotFound(f'The base deck "{doc["base"]}" of this version is missing; it should be in the {BASES} folder.')


# ----------------------------------------------------------------------------- making base decks
def _unknown_card(db, name):
    close = db.suggest(name, SUGGESTIONS_SHOWN)
    hint = f" Close names: {', '.join(close)}." if close else ""
    return Invalid(f'No card is called "{name}".{hint}', [{"text": name, "suggestions": close}])


def _canonical_leaders(commanders, db):
    """[(canonical name, record)] of the commanders: one or two cards, all in the card index."""
    if not isinstance(commanders, (list, tuple)) or not all(isinstance(c, str) for c in commanders):
        raise DeckError('"commanders" must be a list of card names.')
    if not commanders:
        raise Invalid("A base deck needs a commander.")
    unknown = [c for c in commanders if db.get(c) is None]
    if unknown:
        raise _unknown_names(unknown, db)
    leaders = {}
    for c in commanders:
        leaders[db.get(c)["name"]] = db.get(c)       # one entry per card, in the order given
    if len(leaders) > 2:
        raise Invalid(f"A Commander deck has one or two commanders; this one names {len(leaders)}.")
    return list(leaders.items())


def _canonical_cards(cards, db):
    """[(copies, canonical name, record)] in first-seen order, with repeated cards added up."""
    if not isinstance(cards, (list, tuple)) or not all(isinstance(e, (list, tuple)) and len(e) == 2 for e in cards):
        raise DeckError('"cards" must be a list of [copies, "Card name"] pairs.')
    pairs = [(_whole_number(n, "A card's count", 1), _text(name, "A card name")) for n, name in cards]
    unknown = [name for _, name in pairs if db.get(name) is None]
    if unknown:
        raise _unknown_names(list(dict.fromkeys(unknown)), db)
    merged = {}
    for n, name in pairs:
        rec = db.get(name)
        merged[rec["name"]] = (merged.get(rec["name"], (0, rec))[0] + n, rec)
    return [(n, name, rec) for name, (n, rec) in merged.items()]


def _unknown_names(names, db):
    """Invalid listing card names the index does not know, with close names for the first few (the search for close
    names costs a moment a name, the same limit decklist.resolve keeps)."""
    details = [{"text": name, "suggestions": db.suggest(name, SUGGESTIONS_SHOWN) if i < decklist.SUGGEST_LIMIT else []}
               for i, name in enumerate(names)]
    return Invalid(f"The card index does not know {_names(names)}.", details)


def new_base(root, *, name, commanders, cards, source, created_by, db, base_id=None, now=None):
    """Save a new base deck and return it. `cards` are [copies, name] pairs without the commanders; every name is
    stored as the card index spells it, and `ids` records each card's Scryfall id. `source` says where the deck came
    from, {"type": "precon", "name": ..., "mtgjson": <deck file name>} or {"type": "paste"}. `base_id` defaults to
    slug(name). A base is frozen once written: an id already in use raises Conflict and the file is not touched.
    Whether the deck is legal is not asked here (a base may be a precon with a card banned since); `brackets.legality`
    reports that."""
    name = _text(name, "The base deck's name")
    if not isinstance(source, dict):
        raise DeckError('"source" must say where the deck came from, for example {"type": "paste"}.')
    created_by = _check_player(created_by)
    base_id = _base_id_for(name, base_id)
    leaders = _canonical_leaders(commanders, db)
    listed = _canonical_cards(cards, db)
    ids = {leader: rec["oracle_id"] for leader, rec in leaders}
    ids.update({card: rec["oracle_id"] for _, card, rec in listed})
    doc = {"schema": SCHEMA, "kind": "base", "id": base_id, "name": name, "source": copy.deepcopy(source),
           "commanders": [leader for leader, _ in leaders], "cards": [[n, card] for n, card, _ in listed],
           "created": _stamp(now), "created_by": created_by, "ids": ids}
    path = _base_path(root, base_id)
    with _lock(path):
        if os.path.exists(path):
            raise Conflict(f'There is already a base deck with the id "{base_id}". Pick a different name.')
        _write(path, doc)
    return doc


def _base_id_for(name, given):
    """The id for a new deck: the one given, else slug(name)."""
    if given is None:
        given = slug(name)
        if not given:
            raise DeckError(f'"{name}" has no letters or digits to make an id from; give an id as well.')
    return _check_id("base", given)


def parse_list(text, db, *, commander=None):
    """Read a pasted list: {"commanders": [name], "cards": [[copies, name]], "problems": [{"line", "text",
    "suggestions"}]}. Names are the card index's spelling. A problem is a line the tool could not use, with its line
    number (the first line is 1), the line as written and close card names; a caller shows these and lets the player
    fix or drop the lines. The list itself is read by decklist.parse and decklist.resolve, so every format they
    accept works here, and `commander` names the commander when the list does not (decklist.resolve says how).
    Nothing is saved; with no problems the result goes to new_base."""
    if not isinstance(text, str):
        raise DeckError("The pasted list must be text.")
    parsed = decklist.parse(text)
    resolved = decklist.resolve(parsed, db, commander=commander)
    close = {carddb.normalize(u["name"]): u["suggestions"] for u in resolved["unknown"]}
    if parsed["blank_split"]:
        # resolve() reads the cards after a blank line as part of the deck but drops the ones it cannot match without
        # saying so; in a saved deck a typo there would vanish for good, so they are reported like any other name
        for _, raw in parsed["sideboard"]:
            if db.get(raw) is None:
                close.setdefault(carddb.normalize(raw), db.suggest(raw, SUGGESTIONS_SHOWN))
    problems, placed = [], set()
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        one = decklist.parse(line)             # on its own, a line gives the same name it gives in the whole list
        raws = one["commanders"] + [raw for _, raw in one["cards"] + one["sideboard"]]
        unmatched = [carddb.normalize(raw) for raw in raws if carddb.normalize(raw) in close]
        if one["unparsed"] or unmatched:
            problems.append({"line": number, "text": line.strip(),
                             "suggestions": close[unmatched[0]] if unmatched else []})
        placed.update(unmatched)
    for u in resolved["unknown"]:              # a name on no line: the `commander` argument itself is misspelled
        if carddb.normalize(u["name"]) not in placed:
            problems.append({"line": None, "text": u["name"], "suggestions": u["suggestions"]})
    return {"commanders": resolved["commanders"], "cards": [[n, name] for n, name in resolved["cards"]],
            "problems": problems}


def precon_base_input(name):
    """The arguments for new_base made from a precon: {"name", "commanders", "cards", "source"}. The list comes from
    decklist.precon. A name no precon has raises NotFound carrying the closest names (`suggestions`)."""
    name = _text(name, "The precon's name")
    try:
        deck = decklist.precon(name)
    except decklist.UnknownPrecon as e:
        close = f" Close names: {', '.join(e.suggestions)}." if e.suggestions else ""
        raise NotFound(f'No precon is called "{name}".{close}', e.suggestions)
    except net.NotFound:
        raise NotFound(f'MTGJSON lists a precon called "{name}" but has no deck file for it.')
    return {"name": deck["name"], "commanders": list(deck["commanders"]),
            "cards": [[n, card] for n, card in deck["cards"]],
            "source": {"type": "precon", "name": deck["name"], "mtgjson": deck["file"]}}


# ----------------------------------------------------------------------------- making versions
def new_version(root, *, player, name, base_id, settings, version_id=None, now=None):
    """Save a new version of a base deck, with no changes yet and revision 0, and return it. `player` is the folder
    name (lowercase letters, digits and hyphens; slug() makes one from a typed name). `settings` is an object holding
    the player's choices (bracket, budget, themes ...), stored as given. The version id defaults to slug(name); one
    the player already has raises Conflict. NotFound if the base deck does not exist."""
    _check_player(player)
    name = _text(name, "The version's name")
    settings = _settings(settings)
    if version_id is None:
        version_id = slug(name)
        if not version_id:
            raise DeckError(f'"{name}" has no letters or digits to make an id from; give an id as well.')
    _check_id("version", version_id)
    base(root, _check_id("base", base_id))     # the base must exist
    stamp = _stamp(now)
    doc = {"schema": SCHEMA, "kind": "version", "id": version_id, "player": player, "name": name, "base": base_id,
           "settings": settings, "revision": 0, "created": stamp, "updated": stamp, "notes": "", "changes": []}
    path = _version_path(root, player, version_id)
    with _lock(path):
        if os.path.exists(path):
            raise Conflict(f'{player} already has a version with the id "{version_id}". Pick a different name.')
        _write(path, doc)
    return doc


# ----------------------------------------------------------------------------- the card list
def _undone(changes):
    """The numbers of the changes that an undo cancels."""
    return {c["of"] for c in changes
            if isinstance(c, dict) and c.get("op") == "undo" and isinstance(c.get("of"), int)}


def _allows_many_copies(rec):
    """Basic lands and cards that say so ("a deck can have any number of cards named ...") may repeat."""
    return rec is not None and ("Basic" in rec["types"] or rec["any_number"])


def _put_copy(cards, name):
    cards[name] = cards.get(name, 0) + 1


def _take_copy(cards, name):
    if cards[name] == 1:
        del cards[name]
    else:
        cards[name] -= 1


class _Deck:
    """A version's card list while it is replayed or checked. `cards` maps each card name to its copies in list order
    (the base's cards, then added cards as they were added); `commanders` are the base's. Names are the card index's
    spelling today, found by name and then by Scryfall id, and stay as written when the index knows neither.
    `warnings` is what a reader of the file should be told. `problems` are the changes that could not be applied,
    as (change number, what it did, why not): undo compares them before and after."""

    def __init__(self, base_doc, db):
        self.db, self.warnings, self.problems = db, [], []
        ids = base_doc.get("ids")
        self.ids = ids if isinstance(ids, dict) else {}
        self.commanders, self.records, self.cards = [], [], {}
        for name in base_doc.get("commanders") or []:
            if not isinstance(name, str):
                self.warnings.append(f"Skipped a commander of the base deck that is not a card name: {name!r}.")
                continue
            shown, rec = self.find(name, self.ids.get(name))
            self.commanders.append(shown)
            self.records.append(rec)
            if rec is None:
                self.warnings.append(f"The commander {name} is not in the card index, so the deck's colors are "
                                     "unknown.")
        for entry in base_doc.get("cards") or []:
            if not (isinstance(entry, (list, tuple)) and len(entry) == 2 and isinstance(entry[0], int)
                    and entry[0] > 0 and isinstance(entry[1], str)):
                self.warnings.append(f"Skipped a card line of the base deck that is not [copies, name]: {entry!r}.")
                continue
            shown, rec = self.find(entry[1], self.ids.get(entry[1]))
            if rec is None:
                self.warnings.append(f"{entry[1]} is not in the card index; it is kept as written.")
            self.cards[shown] = self.cards.get(shown, 0) + entry[0]

    def find(self, name, oracle_id=None):
        """(the name as the card index spells it now, its record), or (name as written, None) when the index knows
        neither the name nor the id."""
        rec = self.db.get(name) if isinstance(name, str) else None
        if rec is None and oracle_id:
            rec = self.db.by_oracle(oracle_id)
        return (rec["name"] if rec else name), rec

    def colors(self):
        """The commanders' combined color identity as a set of letters, or None when a commander is not in the card
        index (the colors are unknown then, so no card is turned away for its colors)."""
        if not self.records or None in self.records:
            return None
        return set("".join(rec["ci"] for rec in self.records))

    def replay(self, changes, skip=()):
        """Apply the changes in order, leaving out the ones an undo cancels and the ones numbered in `skip`. A change
        that cannot be applied (a hand-edited or badly merged file) is skipped with a warning and never raised, so
        a broken file still opens."""
        undone = _undone(changes)
        for change in changes:
            if not isinstance(change, dict):
                self.warnings.append("Skipped an entry of the change log that is not an object.")
                continue
            n, op = change.get("n"), change.get("op")
            if op == "undo" or (isinstance(n, int) and (n in undone or n in skip)):
                continue
            items = change.get("items") if op == "group" else [change]
            if not isinstance(items, list):
                self.warnings.append(f"Skipped change {n}: its group has no list of items.")
                continue
            for item in items:
                self._replay_item(n, item)

    def _replay_item(self, n, item):
        """Apply one add, cut or swap of change `n`, or skip it with a warning."""
        if not isinstance(item, dict):
            self.warnings.append(f"Skipped change {n}: one of its entries is not an object.")
            return
        op = item.get("op")
        if op not in OP_CARDS:
            self.warnings.append(f"Skipped change {n}: {op!r} is not an add, cut or swap, the only edits this tool "
                                 "knows.")
            return
        if any(not isinstance(item.get(field), str) for field in OP_CARDS[op]):
            self.warnings.append(f"Skipped change {n}: its {op} is missing a card name.")
            return
        problem = self.apply_stored(item)
        if problem:
            what, why = problem
            self.problems.append((n, what, why))
            self.warnings.append(f"Skipped change {n}: it {what}, but {why}.")

    def apply_stored(self, item):
        """Apply one stored add, cut or swap. Returns None when it was applied, or (what it did, why it cannot be
        applied) and changes nothing."""
        op = item["op"]
        cut = self.find(item["cut"], item.get("cut_id")) if "cut" in OP_CARDS[op] else None
        add = self.find(item["add"], item.get("add_id")) if "add" in OP_CARDS[op] else None
        if cut and self.cards.get(cut[0], 0) < 1:
            return f"cut {cut[0]}", "the deck does not have it"
        if add:
            name, rec = add
            copies_left = self.cards.get(name, 0) - (1 if cut and cut[0] == name else 0)
            if name in self.commanders:
                return f"added {name}", "it is the commander"
            if copies_left > 0 and not _allows_many_copies(rec):
                return f"added {name}", "the deck already has a copy"
        if cut:
            _take_copy(self.cards, cut[0])
        if add:
            _put_copy(self.cards, add[0])
        return None


def current(base, version, db):
    """The deck a version holds now: {"commanders": [name], "cards": [[copies, name]], "warnings": [str]}.
    It is the base's cards with the version's changes replayed in order. Each name is looked up with `db.get`, then
    by the Scryfall id the file kept (`db.by_oracle`), and stays as written if both fail, so a card renamed upstream
    still resolves. Changes an undo cancels are skipped; one that cannot be applied is skipped with a warning
    (it is never an error). Order: the base's cards, then added cards in the order they were added."""
    deck = _Deck(base, db)
    deck.replay(version.get("changes") or [])
    return {"commanders": deck.commanders, "cards": [[n, name] for name, n in deck.cards.items()],
            "warnings": deck.warnings}


def diff(base_cards, cards):
    """What a version added to and cut from its base: {"added": [[copies, name]], "cut": [[copies, name]]}. Both
    arguments are lists of [copies, name]. To compare with the base as the card index knows it today, pass
    `current(base, {"changes": []}, db)["cards"]`, so a card Scryfall renamed is not shown as one cut and one add.
    A card in both with a different count is added or cut by the difference."""
    def count(pairs):
        out = {}
        for n, name in pairs:
            out[name] = out.get(name, 0) + n
        return out
    before, after = count(base_cards), count(cards)
    return {"added": [[n - before.get(name, 0), name] for name, n in after.items() if n > before.get(name, 0)],
            "cut": [[n - after.get(name, 0), name] for name, n in before.items() if n > after.get(name, 0)]}


# ----------------------------------------------------------------------------- the rules for a new change
def _request(change, inside_group=False):
    """The change as the caller sent it, checked for shape and cleaned: {"op", ...} with "card" (add, cut), "cut" and
    "add" (swap), "label" and "items" (group), "of" (undo), and "source" (everything but undo and group items).
    Raises DeckError for anything else."""
    if not isinstance(change, dict):
        raise DeckError('A change must be an object with an "op": add, cut, swap, group or undo.')
    op = change.get("op")
    allowed = tuple(OP_CARDS) if inside_group else CHANGE_OPS
    if op not in allowed:
        raise DeckError(f"{op!r} is not an op this tool accepts{' in a group' if inside_group else ''}: "
                        f"use {', '.join(allowed)}.")
    out = {"op": op}
    if op in ("add", "cut"):
        out["card"] = _text(change.get("card"), f'The "card" of a {op}')
    elif op == "swap":
        out["cut"] = _text(change.get("cut"), 'The "cut" of a swap')
        out["add"] = _text(change.get("add"), 'The "add" of a swap')
    elif op == "undo":
        out["of"] = _whole_number(change.get("of"), 'The "of" of an undo (the number of the change to undo)', 1)
    else:
        out["label"] = _text(change.get("label"), 'The "label" of a group')
        items = change.get("items")
        if not isinstance(items, list) or not items:
            raise DeckError('The "items" of a group must be a list of add, cut and swap items.')
        out["items"] = [_request(item, inside_group=True) for item in items]
    if op != "undo" and not inside_group:
        out["source"] = change.get("source", MANUAL)
        if out["source"] not in SOURCES:
            raise DeckError(f'"source" must be "{MANUAL}" or "{SUGGESTED}".')
    return out


def _sent(item):
    """A phrase for an item as it was sent: 'swap Swamp for Sol Ring'."""
    if item["op"] == "swap":
        return f"swap {item['cut']} for {item['add']}"
    return f"{item['op']} {item['card']}"


def _describe(change):
    """A phrase naming a stored change: 'add Sol Ring', 'swap Swamp for Sol Ring', 'group "Up to $25"'."""
    op = change.get("op")
    if op == "swap":
        return f"swap {change.get('cut')} for {change.get('add')}"
    if op == "group":
        return f'group "{change.get("label")}"'
    return f"{op} {change.get('add') or change.get('cut') or ''}".strip()


def _known_card(deck, name):
    rec = deck.db.get(name)
    if rec is None:
        raise _unknown_card(deck.db, name)
    return rec


def _require_playable(deck, rec):
    """Raise Invalid unless the card is legal in Commander and inside the commanders' colors."""
    name = rec["name"]
    if rec["legal"] != "legal":
        raise Invalid(f"{name} is banned in Commander." if rec["legal"] == "banned"
                      else f"{name} is not legal in Commander.")
    colors = deck.colors()
    if colors is not None and not set(rec["ci"]) <= colors:
        outside = "".join(c for c in rec["ci"] if c not in colors)
        raise Invalid(f"{name} is outside the commander's colors: it has {_color_words(outside)} in its color "
                      f"identity, and the deck is {_color_words(colors)}.")


def _applied(deck, body):
    """`body` after applying it to the deck. The rules before each call agree with `apply_stored`, so it cannot
    refuse."""
    refusal = deck.apply_stored(body)
    assert refusal is None, refusal
    return body


def _not_cuttable(deck, rec, name):
    """The Invalid for a cut of `name` (which is not in the list); `rec` is its record or None."""
    shown = rec["name"] if rec else name
    if shown in deck.commanders:
        return Invalid(f"{shown} is the commander, so it cannot be cut.")
    return Invalid(f"{shown} is not in the deck, so it cannot be cut.")


def _check_add(deck, card):
    rec = _known_card(deck, card)
    _require_playable(deck, rec)
    name = rec["name"]
    if name in deck.commanders:
        return None, f"{name} is the commander, so it is already in the deck; nothing changed."
    if name in deck.cards and not _allows_many_copies(rec):
        return None, f"{name} is already in the deck; nothing changed."
    return _applied(deck, {"op": "add", "add": name, "add_id": rec["oracle_id"]}), f"Added {name}."


def _check_cut(deck, card):
    rec = deck.db.get(card)
    name = rec["name"] if rec else card          # a card the index no longer knows can still be cut by its name
    if name not in deck.cards:
        if rec is None and name not in deck.commanders:
            raise _unknown_card(deck.db, card)
        raise _not_cuttable(deck, rec, card)
    cut_id = rec["oracle_id"] if rec else deck.ids.get(name)
    return _applied(deck, {"op": "cut", "cut": name, "cut_id": cut_id}), f"Cut {name}."


def _check_swap(deck, cut_card, add_card):
    cut_rec = deck.db.get(cut_card)
    cut_name = cut_rec["name"] if cut_rec else cut_card
    if cut_rec is None and cut_name not in deck.cards:
        raise _unknown_card(deck.db, cut_card)
    add_rec = _known_card(deck, add_card)
    _require_playable(deck, add_rec)
    add_name = add_rec["name"]
    if cut_name not in deck.cards:
        raise _not_cuttable(deck, cut_rec, cut_card)
    if cut_name == add_name:
        return None, f"Swapping {cut_name} for itself changes nothing."
    if add_name in deck.commanders:
        raise Invalid(f"{add_name} is the commander, so it is already in the deck.")
    if add_name in deck.cards and not _allows_many_copies(add_rec):
        raise Invalid(f"{add_name} is already in the deck, and only basic lands and cards that say so may have more "
                      "than one copy.")
    cut_id = cut_rec["oracle_id"] if cut_rec else deck.ids.get(cut_name)
    body = {"op": "swap", "cut": cut_name, "cut_id": cut_id, "add": add_name, "add_id": add_rec["oracle_id"]}
    return _applied(deck, body), f"Swapped {cut_name} for {add_name}."


def _check_item(deck, item):
    """Check one add, cut or swap against the list as it now stands and, if it changes the list, apply it to
    `deck`. Returns (the change as it is stored, a message), or (None, why there is nothing to do); raises Invalid
    when a rule is broken. Within an item the rules run in the order `apply` lists."""
    if item["op"] == "add":
        return _check_add(deck, item["card"])
    if item["op"] == "cut":
        return _check_cut(deck, item["card"])
    return _check_swap(deck, item["cut"], item["add"])


def _check_group(deck, request):
    """Check a group's items in order, each against the list as the ones before it left it. One broken rule rejects
    the whole group and names the item. An item that does nothing (a card already in the deck) is left out of what
    is stored; if every item is like that, the group does nothing."""
    items, stored, idle = request["items"], [], 0
    for i, item in enumerate(items, 1):
        try:
            body, _ = _check_item(deck, item)
        except Invalid as e:
            raise Invalid(f"Item {i} of {len(items)} ({_sent(item)}) breaks a rule: {e.message}", e.details)
        if body is None:
            idle += 1
        else:
            stored.append(body)
    label = request["label"]
    if not stored:
        return None, f'Nothing in "{label}" changes the deck; nothing changed.'
    note = f"; {_plural(idle, 'item')} already in place" if idle else ""
    applied = _plural(len(stored), "change")
    return {"op": "group", "label": label, "items": stored}, f'Applied "{label}": {applied}{note}.'


def _check_undo(base_doc, changes, number, db):
    """Check an undo of change `number`. The list replayed without that change must still be valid: if a later change
    depends on it (it cuts a card that change added, or adds a card that change cut) the undo is refused and the
    message names that change. Problems the log already had do not count."""
    target = next((c for c in changes if isinstance(c, dict) and c.get("n") == number), None)
    if target is None:
        raise Invalid(f"There is no change {number} to undo.")
    if target.get("op") == "undo":
        raise Invalid(f"Change {number} is itself an undo. To bring a change back, make it again.")
    if number in _undone(changes):
        return None, f"Change {number} is already undone; nothing changed."
    before, after = _Deck(base_doc, db), _Deck(base_doc, db)
    before.replay(changes)
    after.replay(changes, skip=(number,))
    had = {problem[:2] for problem in before.problems}
    broken = [problem for problem in after.problems if problem[:2] not in had]
    if broken:
        n, what, why = broken[0]
        raise Invalid(f"Change {number} ({_describe(target)}) cannot be undone yet: change {n} {what}, and with "
                      f"change {number} undone {why}. Undo change {n} first.")
    return {"op": "undo", "of": number}, f"Undid change {number} ({_describe(target)})."


def _next_number(changes):
    return max((c["n"] for c in changes if isinstance(c, dict) and isinstance(c.get("n"), int)), default=0) + 1


@contextlib.contextmanager
def _version_to_change(root, player, version_id, revision):
    """Open a version for a change and yield (its path, the version). The file's lock is held until the block ends, so
    the caller's read, check and write are one step. This is rule 1 for every change: `revision` must be the file's,
    else Conflict (carrying the current revision) before anything else is looked at."""
    _check_player(player)
    _check_id("version", version_id)
    revision = _whole_number(revision, '"revision" (the revision of the deck you are changing)')
    path = _version_path(root, player, version_id)
    with _lock(path):
        doc = version(root, player, version_id)
        if revision != doc["revision"]:
            raise Conflict(f"This deck has changed since you loaded it (you sent revision {revision}; it is now "
                           f"{doc['revision']}). Reload it and try again.", revision=doc["revision"])
        yield path, doc


def apply(root, player, version_id, change, *, revision, db, now=None):
    """Check one change against a version and, if it breaks no rule and does something, append it and save the file.
    Returns (the version, {"changed": bool, "message": str}); `message` is plain text to show the player.

    `change` is what the API sends: {"op": "add", "card": X}, {"op": "cut", "card": X}, {"op": "swap", "cut": X,
    "add": Y}, {"op": "group", "label": L, "items": [add, cut or swap items]} or {"op": "undo", "of": k}, with an
    optional "source" of "manual" (the default) or "suggested". It is stored with its number `n`, the time `at`, card
    names as the index spells them and Scryfall ids (`add_id`, `cut_id`).

    Rules, in this order (the first that applies decides):
    1. The revision. `revision` must be the file's: otherwise Conflict, carrying the current revision. Nothing else
       is checked, so a stale caller learns to reload before it hears about a card.
    2. Card rules, each an Invalid with a message a player can read: an unknown name (with up to three close names);
       a card that is not legal in Commander; one outside the commanders' colors; cutting a card that is not in
       the list; a swap whose added card is already in the list (unless it is a basic land or an "any number" card).
    3. Nothing to do, answered with changed False, no write and no new revision: adding a one-copy card that is
       already in the list; adding the commander; swapping a card for itself; undoing a change already undone.
    4. A group: its items are checked in order against the list as the earlier ones left it. One broken rule rejects the
       whole group and names the item.
    5. An undo: change k must exist and must not itself be an undo, and the list replayed without k must still be
       valid; if it is not, the undo is Invalid and names the later change that depends on k.
    6. Every write adds 1 to `revision`, sets `updated`, and is atomic (see the module docstring). Nothing limits the
       deck's size: a 101-card deck is for the caller to point out, not an error here."""
    with _version_to_change(root, player, version_id, revision) as (path, doc):
        base_doc = _base_of(root, doc)
        request = _request(change)
        if request["op"] == "undo":
            body, message = _check_undo(base_doc, doc["changes"], request["of"], db)
        else:
            deck = _Deck(base_doc, db)
            deck.replay(doc["changes"])
            check = _check_group if request["op"] == "group" else _check_item
            body, message = check(deck, request)
        if body is None:
            return doc, {"changed": False, "message": message}
        stamp = _stamp(now)
        entry = {"n": _next_number(doc["changes"]), "at": stamp, **body}
        if "source" in request:
            entry["source"] = request["source"]
        doc["changes"].append(entry)
        doc["revision"] += 1
        doc["updated"] = stamp
        _write(path, doc)
        return doc, {"changed": True, "message": message}


def update(root, player, version_id, *, revision, name=None, settings=None, now=None):
    """Change a version's name or settings and return it. `settings` holds the keys to set; the ones it leaves out keep
    their value (a null clears that setting's value). This is a write like any other: it needs the current `revision`
    (else Conflict), adds 1 to it and sets `updated`, so a phone and a desktop tab cannot overwrite each other's
    settings either. Giving the values the version already has does nothing: no write, no new revision."""
    with _version_to_change(root, player, version_id, revision) as (path, doc):
        if name is None and settings is None:
            raise DeckError('Give a new "name" or new "settings" to update.')
        new_name = doc["name"] if name is None else _text(name, "The version's name")
        new_settings = {**doc["settings"], **({} if settings is None else _settings(settings))}
        if new_name == doc["name"] and new_settings == doc["settings"]:
            return doc
        doc["name"], doc["settings"] = new_name, new_settings
        doc["revision"] += 1
        doc["updated"] = _stamp(now)
        _write(path, doc)
        return doc
