"""Commander Spellbook: combos a decklist has, combos one card away, and the bracket each combo implies.

Why this source: Wizards' brackets limit two-card infinite combos, and finding those by hand is the job
Spellbook already does. `find-my-combos` answers "which combos does this list contain?" and "which would one
more card complete?", and tags every combo with a bracket. The second answer keeps `upgrade` from adding the
missing half of a combo the target bracket does not allow. Please credit Commander Spellbook
(https://commanderspellbook.com) wherever combos are shown; every Combo carries its page URL.

What the API does (OpenAPI schema at /schema/, version 7.1.9, read 2026-10-11):
- POST /find-my-combos {"commanders": [{"card": n}], "main": [{"card": n, "quantity": q}]} answers
  {"count", "next", "previous", "results": {"identity", "included", "almostIncluded", ...}}. A page holds up
  to 1000 variants across all buckets and `next` is the URL of the following page (POST the same body there).
  Only `included` and `almostIncluded` are used: the other buckets need a colour or a commander the deck
  does not have.
- Names match case-insensitively but otherwise exactly. A double-faced card must be written "Front // Back"
  (the Scryfall name); a front-face-only or unknown name is silently ignored, so callers pass canonical names.
- A variant (one combo) has `id` ("3000-4871"), `uses` [{card: {name}, quantity}] (the commander is one of
  them), `requires` [{template: {name}, quantity}] (a non-card need such as "any sacrifice outlet"),
  `produces` [{feature: {name}}] and `bracketTag`. `almostIncluded` is a combo with one piece missing.
- POST /estimate-bracket takes the same body and returns Spellbook's own verdict for the whole list.

The local index (read 2026-10-11): Spellbook's developer guide says to use the API for a few calls per user
action and to read everything else from the file it publishes, "fetch it on a schedule of your own and read it
locally": https://json.commanderspellbook.com/variants.json.gz (29 MB gzipped, 687 MB as text, 114,450 variants,
rebuilt daily). The file is one JSON object, {"timestamp", "version", "variants": [...], "aliases": [...]}. A
variant has the API's own shape (`id`, `uses`, `requires`, `produces`, `bracketTag`) plus `identity` (its colors:
"GWUB", or "C" for none), `status`, `spoiler` and `legalities`, and each card in `uses` carries five image links,
which is most of the size. `find_combos_local` reads the file once, keeps a compact index (about 10 MB, cached 7
days) and answers "which combos does this list have, and which are one card away" with no request at all.
`combos_for` is the one call that tries the index and falls back to the API.
"""
import collections, gzip, hashlib, json, os, re, time, zlib
from .. import carddb, net
from ..config import TTL

NAME = "spellbook"
API = "https://backend.commanderspellbook.com"
SITE = "https://commanderspellbook.com"
FIND_URL, ESTIMATE_URL = API + "/find-my-combos", API + "/estimate-bracket"
MAX_PAGES = 5  # 1000 variants a page; a list needing more is a cEDH pile, and page one has the popular combos
VARIANTS_URL = "https://json.commanderspellbook.com/variants.json.gz"
INDEX_SCHEMA = 1            # bump when the saved index changes shape; an index of another schema is rebuilt
READ_CHUNK = 1 << 20        # characters of the daily file read at a time
VARIANT_MAX = 1 << 22       # a variant is about 6 KB of text; one that outgrows this means the file is damaged

# Spellbook tags every combo with the kind of deck it belongs in. Its own words are in the site source
# (SpaceCowMedia/commander-spellbook-site, src/lib/brackets.ts: BRACKET_DESCRIPTION_MAP, BRACKET_FIT_MAP) and
# the backend (spellbook/models/variant.py: BracketTag, the Variant.bracket column, estimate_bracket), read
# 2026-10-11. `lowest` is the lowest bracket the tag can fit (the backend's own Variant.bracket numbers).
# `min_bracket` is the lowest bracket it surely fits (the site's `sure` column). They differ for the two
# borderline tags, and we take the upper end so a deck never lands a bracket too low because of a combo:
# Chatterfang + Pitiless Plunderer is tagged S, and Bracket 3 must block it. `meaning` quotes Spellbook's
# description of the tag, so `check` can say why a combo was blocked.
BRACKET_TAGS = {
    "R": {"label": "Ruthless", "min_bracket": 4, "lowest": 4,
          "meaning": "For competitive decks at brackets 4+"},
    "S": {"label": "Spicy", "min_bracket": 4, "lowest": 3,
          "meaning": "Probably 3 or 4, but hard to classify"},
    "P": {"label": "Powerful", "min_bracket": 3, "lowest": 3,
          "meaning": "For strong decks in bracket 3+"},
    "O": {"label": "Oddball", "min_bracket": 3, "lowest": 2,
          "meaning": "Probably 2 or 3, but hard to classify"},
    "C": {"label": "Core", "min_bracket": 2, "lowest": 2,
          "meaning": "For unoptimized decks in bracket 2+"},
    "E": {"label": "Exhibition", "min_bracket": 1, "lowest": 1,
          "meaning": "For any deck"},
    # Banned cards are illegal in every bracket; 5 is the top of the scale, the nearest an int gets to "never"
    "B": {"label": "Not Legal", "min_bracket": 5, "lowest": None,
          "meaning": "Not legal in any bracket"},
}

# Spellbook's classification of a combo inside a whole-list estimate: (its camelCase key, our snake_case key)
_COMBO_FLAGS = (("relevant", "relevant"), ("borderlineRelevant", "borderline_relevant"),
                ("arguablyTwoCard", "arguably_two_card"), ("definitelyTwoCard", "definitely_two_card"),
                ("speed", "speed"), ("extraTurn", "extra_turn"), ("massLandDenial", "mass_land_denial"),
                ("lock", "lock"), ("skipTurns", "skip_turns"),
                ("controlAllOpponents", "control_all_opponents"),
                ("controlSomeOpponents", "control_some_opponents"))
_CARD_FLAGS = (("banned", "banned"), ("gameChanger", "game_changers"), ("massLandDenial", "mass_land_denial"),
               ("extraTurn", "extra_turns"))


# ---------------------------------------------------------------- pure parsing
def bracket_needed(tag, two_card, infinite):
    """The lowest bracket that allows a combo with this tag. A tag we do not know (or none) falls back to the
    Wizards rule of thumb: a two-card infinite combo needs Bracket 4, anything else fits anywhere."""
    known = BRACKET_TAGS.get(tag)
    if known:
        return known["min_bracket"]
    return 4 if two_card and infinite else 1


def _combo(variant_id, cards, templates, produces, tag, pieces, missing):
    """A Combo from the parts the API's variants and the local index both hold, so the two cannot disagree on what
    counts as a two-card combo or an infinite one. `pieces` is the number of things the combo needs: every copy
    of every card, and every template (a need the deck must meet too, so "two cards + a template" is three)."""
    two_card, infinite = pieces == 2, any("infinite" in p.lower() for p in produces)
    return {"id": str(variant_id), "cards": cards, "requires": templates, "missing": missing,
            "produces": produces, "bracket_tag": tag, "min_bracket": bracket_needed(tag, two_card, infinite),
            "two_card": two_card, "infinite": infinite, "url": f"{SITE}/combo/{variant_id}/"}


def parse_combo(variant, have=None):
    """One Spellbook variant → a Combo. `have` is the casefolded set of the deck's card names; with it,
    `missing` lists the combo's cards the deck lacks (always empty for a combo that is already included)."""
    uses, requires = variant.get("uses") or [], variant.get("requires") or []
    cards = [u["card"]["name"] for u in uses if u.get("card")]
    templates = [t["template"]["name"] for t in requires if t.get("template")]
    produces = [p["feature"]["name"] for p in variant.get("produces") or [] if p.get("feature")]
    pieces = sum(u.get("quantity") or 1 for u in uses) + sum(t.get("quantity") or 1 for t in requires)
    missing = [] if have is None else [n for n in cards if n.casefold() not in have]
    return _combo(variant.get("id", ""), cards, templates, produces, variant.get("bracketTag") or None, pieces,
                  missing)


def parse_results(results, deck_names):
    """{"included": [Combo], "almost": [Combo]} from the `results` object of one find-my-combos page."""
    have = {n.casefold() for n in deck_names}
    return {"included": [parse_combo(v) for v in results.get("included") or []],
            "almost": [parse_combo(v, have) for v in results.get("almostIncluded") or []]}


def parse_estimate(payload):
    """Spellbook's verdict on a whole list: {"tag", "label", "min_bracket", "lowest", "meaning", "banned",
    "game_changers", "mass_land_denial", "extra_turns", "combos"}. Each combo is a Combo plus Spellbook's own
    classification of it (speed, relevant, definitely_two_card, lock, ...)."""
    tag = payload.get("bracketTag")
    known = BRACKET_TAGS.get(tag, {})
    out = {"tag": tag, "label": known.get("label"), "min_bracket": known.get("min_bracket"),
           "lowest": known.get("lowest"), "meaning": known.get("meaning")}
    for theirs, ours in _CARD_FLAGS:
        out[ours] = [c["card"]["name"] for c in payload.get("cards") or [] if c.get(theirs)]
    out["combos"] = []
    for classified in payload.get("combos") or []:
        combo = parse_combo(classified.get("combo") or {})
        combo.update({ours: classified.get(theirs) for theirs, ours in _COMBO_FLAGS})
        out["combos"].append(combo)
    return out


# ---------------------------------------------------------------- network
def _deck_body(commanders, cards):
    """The request body. Repeated names (basic lands) become a quantity; the order is fixed so it hashes the
    same whatever order the caller listed the cards in."""
    copies = collections.Counter(cards)
    return {"commanders": [{"card": n} for n in sorted(commanders)],
            "main": [{"card": n, "quantity": q} if q > 1 else {"card": n} for n, q in sorted(copies.items())]}


def _digest(body):
    return hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def _merge_info(infos):
    """One fetched time and cache state for a read of several pages: the oldest page, the worst state."""
    states = {i["cache"] for i in infos}
    return {"fetched": min(i["fetched"] for i in infos),
            "cache": "stale" if "stale" in states else "network" if "network" in states else "fresh"}


def find_combos(commanders, cards, *, refresh=None, offline=None):
    """Combos in this list and combos one card away:
    {"included": [Combo], "almost": [Combo], "fetched": ISO, "cache": "fresh" | "network" | "stale"}.
    `cards` are the deck's other cards by canonical name (a double-faced card as "Front // Back"). Cached
    under a hash of the sorted names; the body is too long to serve as a URL key."""
    body = _deck_body(commanders, cards)
    base, deck_names = _digest(body), list(commanders) + list(cards)
    found, infos, url = {"included": [], "almost": []}, [], FIND_URL
    for page in range(MAX_PAGES):
        payload, info = net.fetch_json(url, source=NAME, key=f"combos-{base}-{page}", data=body,
                                       refresh=refresh, offline=offline)
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, dict):
            raise net.FetchError(NAME, url, "the answer has no `results` object (the API may have changed)")
        infos.append(info)
        part = parse_results(results, deck_names)
        found["included"] += part["included"]
        found["almost"] += part["almost"]
        url = payload.get("next")
        if not url or not url.startswith(API + "/"):
            break
    found.update(_merge_info(infos))
    return found


def estimate_bracket(commanders, cards, *, refresh=None, offline=None):
    """Spellbook's own bracket estimate for the list (see parse_estimate); None if the endpoint is gone."""
    body = _deck_body(commanders, cards)
    try:
        payload, info = net.fetch_json(ESTIMATE_URL, source=NAME, key=f"estimate-{_digest(body)}", data=body,
                                       refresh=refresh, offline=offline)
    except net.NotFound:
        return None
    if not isinstance(payload, dict) or "bracketTag" not in payload:
        raise net.FetchError(NAME, ESTIMATE_URL, "the answer has no `bracketTag` (the API may have changed)")
    return dict(parse_estimate(payload), fetched=info["fetched"], cache=info["cache"])


# ---------------------------------------------------------------- the local combo index
_ARRAY_START = re.compile(r'"variants"\s*:\s*\[')
_SEPARATORS = " \t\r\n,"
_MEMO = {}      # index path -> (ComboIndex, {"fetched", "cache"}), so one process reads the saved index once


def reset():
    """Forget the loaded index (tests, and a long-running process that wants the next call to look again)."""
    _MEMO.clear()


def _open_text(path):
    """A text stream over the daily file. The server labels it `Content-Encoding: gzip`, so a saved copy is a
    gzip or, if a download tool undid the encoding, plain JSON: look at the magic number, not the file name."""
    with open(path, "rb") as f:
        gzipped = f.read(2) == b"\x1f\x8b"
    return gzip.open(path, "rt", encoding="utf-8") if gzipped else open(path, encoding="utf-8")


def _head_value(head, key):
    found = re.search(r'"%s"\s*:\s*"([^"]*)"' % key, head)
    return found.group(1) if found else ""


def open_daily_file(path, *, chunk=READ_CHUNK):
    """(info, variants) for the daily file: its own {"timestamp", "version"} and an iterator over its variants.
    json has no streaming reader, so the iterator decodes one variant, forgets it and reads on: memory holds a
    chunk of text, not the 687 MB of the whole file. A file that is cut off or damaged raises ValueError (or
    OSError, EOFError, zlib.error from the gzip) while the iterator runs."""
    f = _open_text(path)
    text = ""
    while True:
        start = _ARRAY_START.search(text)
        if start:
            break
        more = f.read(chunk)
        if not more or len(text) > VARIANT_MAX:
            f.close()
            raise ValueError("the file has no list of variants")
        text += more
    head = text[:start.start()]
    info = {"timestamp": _head_value(head, "timestamp"), "version": _head_value(head, "version")}
    return info, _each_variant(f, text, start.end(), chunk)


def _each_variant(f, text, pos, chunk):
    decoder = json.JSONDecoder()
    try:
        while True:
            while True:                          # past the commas and spaces, reading on when the text runs out
                while pos < len(text) and text[pos] in _SEPARATORS:
                    pos += 1
                if pos < len(text):
                    break
                more = f.read(chunk)
                if not more:
                    raise ValueError("the list of variants never ends")
                text, pos = more, 0
            if text[pos] == "]":
                return
            while True:
                try:
                    variant, end = decoder.raw_decode(text, pos)
                    break
                except ValueError:               # a variant cut by the end of the text so far: read more
                    more = f.read(chunk)
                    if not more or len(text) - pos > VARIANT_MAX:
                        raise ValueError("a variant could not be read")
                    text, pos = text[pos:] + more, 0
            pos = end
            yield variant
    finally:
        f.close()


def _colors(identity):
    """Spellbook's identity text ("GWUB", "C" for none) as WUBRG letters in WUBRG order ("" for none)."""
    return "".join(c for c in "WUBRG" if c in (identity or ""))


def reduce_variant(variant):
    """(record, "") with what the index keeps of one raw variant, or (None, why) for a variant no Commander deck
    can use. Left out: one that is not OK (every variant in today's file is), one that needs an unreleased card
    ("spoiler") and one that is not legal in Commander ("not legal": it needs a banned card, so it can neither be
    in a legal deck nor be completed by adding a card). The record is {"id", "cards" (a name once for each copy
    it needs), "requires" (the templates, the same way), "produces", "tag", "identity" (WUBRG letters), "leaders"
    (cards that must be the commander)}."""
    uses = variant.get("uses") or []
    if variant.get("status", "OK") != "OK":
        return None, "status"
    if variant.get("spoiler") or any((u.get("card") or {}).get("spoiler") for u in uses):
        return None, "spoiler"
    if not (variant.get("legalities") or {}).get("commander", True):
        return None, "not legal"
    cards, leaders, templates = [], [], []
    for use in uses:
        name = (use.get("card") or {}).get("name")
        if name:
            cards += [name] * (use.get("quantity") or 1)
            if use.get("mustBeCommander"):
                leaders.append(name)
    if not cards:
        return None, "no cards"
    for need in variant.get("requires") or []:
        name = (need.get("template") or {}).get("name")
        if name:
            templates += [name] * (need.get("quantity") or 1)
    produces = [p["feature"]["name"] for p in variant.get("produces") or [] if p.get("feature")]
    return {"id": variant.get("id", ""), "cards": cards, "requires": templates, "produces": produces,
            "tag": variant.get("bracketTag") or "", "identity": _colors(variant.get("identity")),
            "leaders": leaders}, ""


class _Table:
    """A table of texts: each distinct text gets the next whole number, and the index stores that number, so a
    card's name is written once however many combos use it."""

    def __init__(self):
        self.texts, self._ids = [], {}

    def number(self, text):
        found = self._ids.get(text)
        if found is None:
            found = self._ids[text] = len(self.texts)
            self.texts.append(text)
        return found


def reduce_file(path, *, chunk=READ_CHUNK):
    """The index document for the daily file at `path`: a row per usable variant,
    [id, card numbers, template numbers, result numbers, bracket tag, identity, commander-only card numbers],
    and the three tables of texts the numbers refer to (names, templates, features). `dropped` counts the variants
    left out, by reason."""
    info, variants = open_daily_file(path, chunk=chunk)
    names, templates, features = _Table(), _Table(), _Table()
    rows, dropped = [], collections.Counter()
    for variant in variants:
        kept, why = reduce_variant(variant)
        if kept is None:
            dropped[why] += 1
            continue
        rows.append([kept["id"], [names.number(n) for n in kept["cards"]],
                     [templates.number(t) for t in kept["requires"]],
                     [features.number(p) for p in kept["produces"]], kept["tag"], kept["identity"],
                     [names.number(n) for n in kept["leaders"]]])
    now = time.time()
    return {"schema": INDEX_SCHEMA, "fetched": net.iso(now), "ts": now, "source": VARIANTS_URL,
            "dump": info["timestamp"], "version": info["version"], "dropped": dict(dropped),
            "names": names.texts, "templates": templates.texts, "features": features.texts, "variants": rows}


class ComboIndex:
    """The saved index in memory, with the lookup that finds a deck's combos. The first `match` builds a list, for
    every card, of the variants that use it; a deck then touches only the variants of its own cards (a few
    thousand of the 111,000), not all of them."""

    def __init__(self, doc):
        self.names, self.templates, self.features = doc["names"], doc["templates"], doc["features"]
        self.rows = doc["variants"]
        self.dump = doc.get("dump", "")
        self._by_name = {name.casefold(): number for number, name in enumerate(self.names)}
        self._postings = self._distinct = self._alone = None

    def __len__(self):
        return len(self.rows)

    def _index_rows(self):
        self._postings = [[] for _ in self.names]
        self._distinct = []
        self._alone = []
        for n, row in enumerate(self.rows):
            different = set(row[1])
            self._distinct.append(len(different))
            if row[2]:                           # needs a template: left out of the lookup, see `match`
                continue
            if len(different) == 1:
                # a variant of a single card is one card away from a deck that lacks the card, and no card of the
                # deck leads to it, so the lookup by card never sees it
                self._alone.append(n)
            for number in different:
                self._postings[number].append(n)

    def _combo(self, n, missing):
        variant_id, card_numbers, template_numbers, feature_numbers, tag = self.rows[n][:5]
        return _combo(variant_id, [self.names[i] for i in dict.fromkeys(card_numbers)],
                      [self.templates[i] for i in dict.fromkeys(template_numbers)],
                      [self.features[i] for i in feature_numbers], tag or None,
                      len(card_numbers) + len(template_numbers), [self.names[i] for i in missing])

    def match(self, commanders, cards, identity=None):
        """{"included": [Combo], "almost": [Combo]} for a deck, in the file's order. Included: the deck holds
        every card the variant uses (all copies it needs), the commanders counted among the cards. Almost:
        exactly one card is missing. A variant that needs a card to be the commander is skipped unless that card
        is one of `commanders`, and with `identity` (the commanders' colors, as WUBRG letters) an almost combo
        whose colors do not fit is skipped, because its missing card could not go in the deck.

        A variant that also needs a template ("Persist Creature", "Any sacrifice outlet": 6,367 of the 111,378)
        is never offered. Whether a deck has a card of that class is a Scryfall search the API runs for each
        deck; checked on 2026-10-11 it counts an unmet template as a missing piece (a deck with both cards of a
        Persist Creature combo but no persist creature gets it as "almost" with no card missing, and as
        "included" once a persist creature is added). Without that search a combo like this could only be
        guessed at, so it is left out: the answer can miss a template combo the API would list, and never lists
        one the API would not. (Checked on 2026-10-11 against seven real lists, the index offered nothing the API
        did not, and the API's other combos were template combos and combos with a banned card.)"""
        if self._postings is None:
            self._index_rows()
        copies = collections.Counter(n.casefold() for n in list(commanders) + list(cards))
        leaders = {n.casefold() for n in commanders}
        held = {self._by_name[key]: have for key, have in copies.items() if key in self._by_name}
        colors = None if identity is None else set(identity)
        whole = collections.Counter()           # row -> how many of its distinct cards the deck holds in full
        for number, have in held.items():
            for n in self._postings[number]:
                if have >= self.rows[n][1].count(number):
                    whole[n] += 1
        found = {"included": [], "almost": []}
        candidates = [(n, count) for n, count in whole.items() if count >= self._distinct[n] - 1]
        candidates += [(n, 0) for n in self._alone if n not in whole]
        for n, count in sorted(candidates):
            row = self.rows[n]
            if any(self.names[i].casefold() not in leaders for i in row[6]):
                continue
            if count == self._distinct[n]:
                found["included"].append(self._combo(n, []))
            elif count == self._distinct[n] - 1 and (colors is None or set(row[5]) <= colors):
                missing = [number for number in dict.fromkeys(row[1])
                           if held.get(number, 0) < row[1].count(number)]
                found["almost"].append(self._combo(n, missing))
        return found


def build_index():
    """Download the daily file, boil it down to the index, save the index and delete the download. Returns the
    index document. The download stays gzipped (29 MB); `reduce_file` unzips it as it reads."""
    path = net.cache_file(NAME, "variants")
    raw = os.path.join(os.path.dirname(path), "variants.json.gz")
    try:
        net.download(VARIANTS_URL, raw, source=NAME, decode=False)
        doc = reduce_file(raw)
    except (OSError, EOFError, ValueError, zlib.error) as e:     # a cut-off download, bad gzip, bad JSON
        raise net.FetchError(NAME, VARIANTS_URL, f"the combo file was damaged: {e}")
    finally:
        carddb.discard(raw)
    if not doc["variants"]:
        raise net.FetchError(NAME, VARIANTS_URL, "the combo file held no combos")
    net.atomic_json(path, doc)
    return doc


def local_index(*, refresh=None, offline=None):
    """(ComboIndex, {"fetched": ISO time of the download, "cache": "fresh" | "network" | "stale"}). The saved
    index is used while it is under TTL["spellbook_variants"] (7 days) old; otherwise it is rebuilt from the daily
    file, which takes a few seconds and is the only download. A failed rebuild falls back to the old index
    ("stale"); with none, FetchError. The first call per process reads the saved file; later calls return the same
    index."""
    refresh = net.MODE["refresh"] if refresh is None else refresh
    offline = net.MODE["offline"] if offline is None else offline
    path = net.cache_file(NAME, "variants")
    memo = _MEMO.get(path)
    if memo and (not refresh or memo[1]["cache"] == "network"):
        return memo
    doc = net.read_json(path)
    have = isinstance(doc, dict) and doc.get("schema") == INDEX_SCHEMA and isinstance(doc.get("variants"), list)
    fresh = have and time.time() - doc.get("ts", 0) < TTL["spellbook_variants"]
    if have and (offline or (fresh and not refresh)):
        state = "fresh" if fresh else "stale"
    elif offline:
        raise net.FetchError(NAME, VARIANTS_URL, "offline (--offline) and no saved combo file; run `warm` (or "
                                                 "`stats`) once without --offline to save it")
    else:
        try:
            doc, state = build_index(), "network"
        except net.FetchError:
            if not have:
                raise
            state = "stale"
    _MEMO[path] = memo = (ComboIndex(doc), {"fetched": doc.get("fetched", ""), "cache": state})
    return memo


def find_combos_local(commanders, cards, *, identity=None, refresh=None, offline=None):
    """The answer of `find_combos`, from the local index instead of the API:
    {"included": [Combo], "almost": [Combo], "fetched": ISO, "cache": "fresh" | "network" | "stale"}.
    `identity` is the commanders' colors (WUBRG letters); pass it so a combo whose missing card is outside them is
    not offered. Raises FetchError when the index can be neither read nor built."""
    index, info = local_index(refresh=refresh, offline=offline)
    found = index.match(commanders, cards, identity)
    found.update(info)
    return found


def combos_for(commanders, cards, *, identity=None, refresh=None, offline=None):
    """`find_combos_local`, or `find_combos` when the index cannot be had (a failed download, or --offline with no
    saved index): the same answer, plus "via": "index" | "api" and, after a fallback, "note" saying why. If the
    API fails too, FetchError carries both reasons. `stats` calls this; `check`, `build` and `upgrade` still ask
    the API directly."""
    try:
        found = find_combos_local(commanders, cards, identity=identity, refresh=refresh, offline=offline)
    except net.FetchError as local:
        try:
            found = find_combos(commanders, cards, refresh=refresh, offline=offline)
        except net.FetchError as api:
            raise net.FetchError(NAME, api.url, f"{api.reason} (the combo file was not available either: "
                                                f"{local.reason})")
        found.update(via="api", note=f"The combo file was not available ({local.reason}), so Commander "
                                     "Spellbook's API answered.")
        return found
    found["via"] = "index"
    return found
