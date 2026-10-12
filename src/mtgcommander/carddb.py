"""Card index for the Commander builder: Scryfall's oracle_cards bulk file boiled down to one record a card.

Why a local index: every module needs rules text, color identity, legality and prices for thousands of cards,
and Scryfall asks clients to prefer bulk files over per-card requests. The raw file is ~200 MB uncompressed,
so it is streamed once, reduced to ~35k records (see `card_record`) and deleted; later runs read the index.

Name matching is the other job. Decklists spell cards every way (lower case, curly apostrophes, "Aether Vial"
for "Æther Vial", "Fire/Ice", the front face alone), so `CardDB.get` accepts any spelling that `normalize`
maps to the same key, and `suggest` offers close matches for typos. A card keeps its Scryfall `oracle_id` when
Scryfall renames it, so `by_oracle` finds a saved card by id when its name no longer matches.

Each record also keeps the links to the card's picture (the front, and the back when the faces have pictures of
their own) and to its Scryfall page, so the deck pages can show a card without asking Scryfall about it.

Prices: the index holds the default printing's price. `cheapest_prices` asks Scryfall for the cheapest
printing of the few cards a recommendation needs (`prefer:usd-low`, checked against the minimum over all
printings)."""
import difflib, gzip, json, os, re, time, unicodedata, urllib.parse
from . import net
from .config import TTL

SCHEMA = 2               # 2: records also hold the picture links, the Scryfall page link, power and toughness
BULK_LIST = "https://api.scryfall.com/bulk-data"
SEARCH = "https://api.scryfall.com/cards/search"
WUBRG = "WUBRG"
# Layouts that are never deck cards (front_card is a set's theme card). Everything else is kept even when it
# is not Commander-legal: decklists may contain such cards and `check` has to report them.
NON_CARD_LAYOUTS = {"token", "double_faced_token", "emblem", "art_series", "vanguard", "scheme", "planar",
                    "front_card"}
PRICE_QUERY_MAX = 900     # Scryfall cuts a search at 1,000 characters and then answers "unclosed parentheses"
PRICE_SCHEMA = 1
WARNINGS = []             # non-fatal problems (a price search that failed); callers print and clear them

_MEMO = {}                # index path -> CardDB, so repeated load() calls in one run read the file once
_PUNCT = str.maketrans({"’": "'", "‘": "'", "`": "'", "´": "'", "“": '"', "”": '"',
                        "–": "-", "—": "-"})


def normalize(name):
    """Comparison key for a card name: casefolded, accents stripped, one kind of apostrophe, spaces collapsed.
    'Lim-Dûl’s  Vault' and 'lim-dul's vault' agree, so do 'Æther Vial' and 'Aether Vial', and so do
    'Fire/Ice', 'Fire / Ice' and 'Fire // Ice' (MTGO writes split cards with a single slash)."""
    s = unicodedata.normalize("NFKD", (name or "").translate(_PUNCT))
    s = "".join(c for c in s if not unicodedata.combining(c)).casefold().replace("æ", "ae")
    s = re.sub(r"\s*/{1,2}\s*", " // ", s)
    return re.sub(r"\s+", " ", s).strip()


# ----------------------------------------------------------------------------- card records
_OFF_BATTLEFIELD_CREATURE = re.compile(r"isn't on the battlefield, it's an? [^.]*creature")
_PARTNER_LINE = re.compile(r"^(?:(Partner with) (.+?)|(Partner)(?:—(.+?))?|(Choose a Background)"
                           r"|(Doctor's companion)|(Friends forever))(?: \(.*)?$")
_ANY_NUMBER = re.compile(r"a deck can have (any number of|up to \w+) cards named", re.I)


def _split_types(type_line):
    """'Legendary Creature — Elf Druid' → (['Legendary', 'Creature'], ['Elf', 'Druid'])."""
    left, _, right = (type_line or "").partition("—")
    return left.split(), right.split()


def _price(prices):
    """The default printing's price: normal, else foil, else etched (some cards exist only in foil)."""
    for k in ("usd", "usd_foil", "usd_etched"):
        if (prices or {}).get(k):
            return float(prices[k])
    return None


def _partner_kind(keywords, subtypes, ftext):
    """Which pairing a commander allows (None if it has no pairing ability). Values: "partner",
    "partner with <Name>", "friends forever", "partner—<restriction>" (Character select, Survivors, ...),
    "choose a background", "background", "doctor's companion", "doctor". The details come from the front
    face's rules text; the keywords are the fallback for a card whose text Scryfall has not caught up with."""
    if "Background" in subtypes:
        return "background"
    if {"Time", "Lord", "Doctor"} <= set(subtypes):
        return "doctor"
    for line in (ftext or "").split("\n"):
        m = _PARTNER_LINE.match(line.strip())
        if not m:
            continue
        if m.group(1):                                       # Partner with <Name>
            return f"partner with {m.group(2)}"
        if m.group(3):                                       # Partner, or Partner—<restriction>
            restriction = (m.group(4) or "").lower()
            if not restriction:
                return "partner"
            return restriction if restriction == "friends forever" else "partner—" + restriction
        return (m.group(5) or m.group(6) or m.group(7)).lower()
    kw = {k.lower() for k in keywords}
    return next((k for k in ("partner", "choose a background", "doctor's companion", "friends forever")
                 if k in kw), None)


def _can_lead(types, subtypes, ftext, has_pt, meld_result):
    """May this card be (one of) the commander(s)? Mirrors Scryfall's is:commander: a Legendary Creature, a
    card that says so, a Legendary Vehicle or Spacecraft with printed power and toughness, a Background (only
    next to a "Choose a Background" commander; `partner` says so), and Grist-style cards that are creatures
    everywhere except the battlefield. The back half of a meld pair is never in a deck."""
    if meld_result:
        return False
    legendary = "Legendary" in types
    return ((legendary and "Creature" in types)
            or "can be your commander" in ftext.lower()
            or (legendary and has_pt and bool({"Vehicle", "Spacecraft"} & set(subtypes)))
            or (legendary and "Background" in subtypes)
            or (legendary and bool(_OFF_BATTLEFIELD_CREATURE.search(ftext))))


def _normal_image(obj):
    """The link to the `normal` size picture in a card's or a face's `image_uris`, or "" when it has none."""
    return ((obj or {}).get("image_uris") or {}).get("normal") or ""


def card_record(d):
    """The index record for one Scryfall card object, or None for things that are not deck cards.
    Keys are documented in the design doc; every key is always present. The picture keys are links, "" when
    Scryfall has none: `image` is the front (a split or adventure card has one picture for both halves, on the
    card itself; a transform or modal card has one per face), `image_back` the second face's own picture."""
    faces = d.get("card_faces") or []
    front = faces[0] if faces else d
    oracle_id = d.get("oracle_id") or front.get("oracle_id")   # a reversible card keeps it on its faces
    if d.get("layout") in NON_CARD_LAYOUTS or not oracle_id:
        return None
    name = d.get("name") or front.get("name", "")
    type_line = d.get("type_line") or " // ".join(f.get("type_line", "") for f in faces)
    types, subtypes = _split_types(front.get("type_line") or type_line.split(" // ")[0])
    text = d.get("oracle_text") or " // ".join(f["oracle_text"] for f in faces if f.get("oracle_text"))
    ftext = (front.get("oracle_text") if faces else d.get("oracle_text")) or ""
    ci = d.get("color_identity") or []       # Scryfall's order is not WUBRG (Fire // Ice is ["R","U"])
    meld_result = any(p.get("component") == "meld_result" and p.get("name") == name
                      for p in d.get("all_parts", []))
    is_land = "Land" in types
    return {
        "name": name,
        "front": front.get("name") or name,
        "oracle_id": oracle_id,
        "ci": "".join(c for c in WUBRG if c in ci),
        "mana_cost": (front.get("mana_cost") if faces else d.get("mana_cost")) or "",
        "cmc": float(d.get("cmc") or 0),
        "type_line": type_line,
        "types": types,
        "subtypes": subtypes,
        "text": text.replace("\n", " "),
        "keywords": list(d.get("keywords") or []),
        "legal": (d.get("legalities") or {}).get("commander", "not_legal"),
        "gc": bool(d.get("game_changer")),
        "price": _price(d.get("prices")),
        "rank": d.get("edhrec_rank"),
        "produced_mana": list(d.get("produced_mana") or []),
        "land": is_land,
        # Only modal DFCs can be played as a land from hand; a transform card's land back cannot.
        "mdfc_land": (not is_land and d.get("layout") == "modal_dfc"
                      and any("Land" in _split_types(f.get("type_line"))[0] for f in faces[1:])),
        "commander_ok": _can_lead(types, subtypes, ftext, front.get("power") is not None, meld_result),
        "partner": _partner_kind(d.get("keywords") or [], subtypes, ftext),
        # "up to seven/nine cards named" (Seven Dwarves, Nazgûl) is treated the same: not a one-copy card
        "any_number": bool(_ANY_NUMBER.search(text)),
        "layout": d.get("layout", "normal"),
        "released": d.get("released_at", ""),   # of the default printing, so only an upper bound on age
        # a creature's printed power and toughness, as Scryfall writes them ("2", "*", "1+*"); None for a card with
        # none (the front face's, like every other key)
        "power": front.get("power") if faces else d.get("power"),
        "toughness": front.get("toughness") if faces else d.get("toughness"),
        "image": _normal_image(d) or _normal_image(front),
        "image_back": _normal_image(faces[1]) if len(faces) > 1 else "",
        "scryfall_uri": d.get("scryfall_uri") or "",
    }


# ----------------------------------------------------------------------------- bulk files
def _open_text(path):
    """A text stream over a bulk file. The CDN serves `application/gzip` without Content-Encoding, so
    net.download saves the gzip bytes untouched; look at the magic number, not the file name."""
    with open(path, "rb") as f:
        gz = f.read(2) == b"\x1f\x8b"
    return gzip.open(path, "rt", encoding="utf-8") if gz else open(path, encoding="utf-8")


def iter_bulk(path):
    """Objects from a Scryfall bulk file, one at a time so 200 MB never sits in memory. Today's files are
    JSON Lines; the older layout was an array with one card per line, which the same loop handles (stray
    brackets and trailing commas are skipped). Anything else (a pretty-printed array) is read whole."""
    with _open_text(path) as f:
        n = 0
        for line in f:
            s = line.strip().rstrip(",")
            if s in ("", "[", "]"):
                continue
            try:
                obj = json.loads(s)
            except ValueError:
                if n:
                    raise
                f.seek(0)
                yield from json.load(f)
                return
            n += 1
            if isinstance(obj, list):
                yield from obj
            else:
                yield obj


def bulk_entry(kind, *, refresh=None, offline=None):
    """(download url, listing entry) for a Scryfall bulk-data type such as "oracle_cards" or "oracle_tags".
    The listing is cached for an hour only: file names carry a timestamp, so an old URL may be gone."""
    listing, _ = net.fetch_json(BULK_LIST, source="scryfall", key="bulk-data", ttl=3600, refresh=refresh,
                                offline=offline)
    entry = next((e for e in listing.get("data", []) if e.get("type") == kind), None)
    url = entry and (entry.get("jsonl_download_uri") or entry.get("download_uri"))
    if not url:
        raise net.FetchError("scryfall", BULK_LIST, f"the bulk-data list has no {kind} file (API changed?)")
    return url, entry


def discard(path):
    try:
        os.remove(path)
    except OSError:
        pass


def index_path():
    return net.cache_file("scryfall", "carddb")


def build_index(*, refresh=None, offline=None):
    """Download the bulk file, reduce it to records, save the index and delete the raw file.
    Returns the index dict."""
    url, entry = bulk_entry("oracle_cards", refresh=refresh, offline=offline)
    raw = os.path.join(os.path.dirname(index_path()), "oracle_cards.jsonl.gz")
    cards = {}
    try:
        net.download(url, raw, source="scryfall")
        for obj in iter_bulk(raw):
            rec = card_record(obj)
            old = rec and cards.get(rec["name"])
            # A few names belong to two cards (Pick Your Poison is both a real card and a playtest card);
            # the Commander-legal one is the card a decklist means.
            if rec and (not old or (rec["legal"] == "legal" and old["legal"] != "legal")):
                cards[rec["name"]] = rec
    except (OSError, EOFError, ValueError) as e:   # truncated gzip, bad JSON
        raise net.FetchError("scryfall", url, f"the card file was damaged: {e}")
    finally:
        discard(raw)
    if not cards:
        raise net.FetchError("scryfall", url, "the card file held no cards")
    now = time.time()
    idx = {"schema": SCHEMA, "fetched": net.iso(now), "ts": now, "source": url,
           "updated": (entry or {}).get("updated_at", ""), "cards": cards}
    net.atomic_json(index_path(), idx)
    return idx


# ----------------------------------------------------------------------------- the index
class CardDB:
    """All cards by canonical Scryfall name, with forgiving name lookup.
    `fetched` is the ISO time of the bulk download; `cache` is "network" (just rebuilt), "fresh" or "stale"
    (served although older than the cache lifetime because the network failed or --offline)."""

    def __init__(self, cards, fetched="", source="", cache="fresh"):
        self.cards, self.fetched, self.source, self.cache = cards, fetched, source, cache
        self._alias = None
        self._by_oracle = None

    def _aliases(self):
        """normalized spelling → canonical name. Canonical spellings win over front-face aliases; a split
        card's second half is deliberately not an alias ("Ice" is not "Fire // Ice")."""
        if self._alias is None:
            alias = {normalize(n): n for n in self.cards}
            for n, rec in self.cards.items():
                if rec["front"] != n:
                    alias.setdefault(normalize(rec["front"]), n)
            # keys first: another thread sees _alias set only once _alias_keys exists (the deck server is threaded)
            self._alias_keys = list(alias)
            self._alias = alias
        return self._alias

    def get(self, name):
        rec = self.cards.get(name)
        if rec is None:
            key = normalize(name)
            rec = self.cards.get(self._aliases().get(key))
            front, _, back = key.partition(" // ")
            if rec is None and front == back:      # MTGJSON names reversible cards "Sol Ring // Sol Ring"
                rec = self.cards.get(self._aliases().get(front))
        return rec

    def resolve(self, name):
        rec = self.get(name)
        return rec["name"] if rec else None

    def by_oracle(self, oracle_id):
        """The record with this Scryfall `oracle_id`, or None. The id is the same for every printing and survives
        a rename, which is why saved decks keep it beside each card name. The id map is built on first use."""
        if self._by_oracle is None:
            self._by_oracle = {rec["oracle_id"]: rec for rec in self.cards.values() if rec.get("oracle_id")}
        return self._by_oracle.get(oracle_id)

    def suggest(self, name, n=3):
        alias = self._aliases()
        out = []
        for k in difflib.get_close_matches(normalize(name), self._alias_keys, n=n * 2, cutoff=0.6):
            if alias[k] not in out:
                out.append(alias[k])
        return out[:n]

    def __contains__(self, name):
        return self.get(name) is not None

    def __len__(self):
        return len(self.cards)

    def values(self):
        return self.cards.values()


def load(*, refresh=None, offline=None):
    """The card index, rebuilt from Scryfall when it is older than TTL["scryfall"] or `refresh` is set.
    A failed rebuild falls back to the old index ("stale"); with nothing to fall back on it raises FetchError.
    The first call per process reads the file; later calls return the same object."""
    refresh = net.MODE["refresh"] if refresh is None else refresh
    offline = net.MODE["offline"] if offline is None else offline
    path = index_path()
    memo = _MEMO.get(path)
    if memo and (not refresh or memo.cache == "network"):
        return memo
    idx = net.read_json(path)
    have = isinstance(idx, dict) and idx.get("schema") == SCHEMA and isinstance(idx.get("cards"), dict)
    fresh = have and time.time() - idx.get("ts", 0) < TTL["scryfall"]
    if have and (offline or (fresh and not refresh)):
        state = "fresh" if fresh else "stale"
    elif offline:
        raise net.FetchError("scryfall", BULK_LIST,
                             "offline (--offline) and no card index; run `warm` while online")
    else:
        try:
            idx, state = build_index(refresh=refresh), "network"
        except net.FetchError:
            if not have:
                raise
            state = "stale"
    _MEMO[path] = db = CardDB(idx["cards"], idx.get("fetched", ""), idx.get("source", ""), state)
    return db


# ----------------------------------------------------------------------------- cheapest printing
def name_term(name):
    """A Scryfall exact-name term, or None for a name holding both kinds of quote (none exists today)."""
    if '"' not in name:
        return f'!"{name}"'
    return None if "'" in name else f"!'{name}'"


def price_queries(names, limit=PRICE_QUERY_MAX):
    """[(query, [names])] — Scryfall searches that together cover `names`, each at most `limit` characters.
    One request answers many names: `(!"Sol Ring" or !"Arcane Signet") prefer:usd-low`."""
    out, terms, chunk = [], [], []
    tail = ") prefer:usd-low"
    for name in names:
        term = name_term(name)
        if term is None:
            continue
        if terms and len("(" + " or ".join(terms + [term]) + tail) > limit:
            out.append(("(" + " or ".join(terms) + tail, chunk))
            terms, chunk = [], []
        terms.append(term)
        chunk.append(name)
    if terms:
        out.append(("(" + " or ".join(terms) + tail, chunk))
    return out


def parse_cheapest(page):
    """{card name: USD price} from one search page; a card with no USD price at all is left out."""
    out = {}
    for card in page.get("data", []):
        p = _price(card.get("prices"))
        if p is not None:
            out[card.get("name")] = p
    return out


def _search_prices(query):
    """{name: price} for one search, following pages. Uses net.request because a search page is large and the
    per-name price cache below already stores the only thing we keep."""
    url = SEARCH + "?" + urllib.parse.urlencode({"q": query, "unique": "cards"})
    out = {}
    while url:
        try:
            page = json.loads(net.request(url, source="scryfall"))
        except net.NotFound:                   # none of the names matched
            break
        except ValueError:
            raise net.FetchError("scryfall", url, "the response was not JSON")
        out.update(parse_cheapest(page))
        url = page.get("next_page") if page.get("has_more") else None
    return out


def cheapest_prices(names, *, refresh=None, offline=None):
    """{canonical name: cheapest USD printing, or None}. Searches are batched and each name's answer is cached
    for TTL["prices"] in data/cache/commander/prices/cheapest.json. A name Scryfall cannot price falls back to
    the index's default-printing price. A failed search is not an error (the fallback is used and a line is
    added to WARNINGS) because a price is an extra, not the recommendation itself."""
    refresh = net.MODE["refresh"] if refresh is None else refresh
    offline = net.MODE["offline"] if offline is None else offline
    db = load(refresh=False, offline=offline)       # --refresh means fresh prices here, not a 25 MB download
    wanted = list(dict.fromkeys(db.resolve(n) or n for n in names))
    path = net.cache_file("prices", "cheapest")
    cache = net.read_json(path)
    entries = cache["prices"] if (isinstance(cache, dict) and cache.get("schema") == PRICE_SCHEMA
                                  and isinstance(cache.get("prices"), dict)) else {}
    now, ttl = time.time(), TTL["prices"]
    todo = [] if offline else [n for n in wanted if refresh or n not in entries or now - entries[n][1] >= ttl]
    for query, chunk in price_queries(todo):
        try:
            found = _search_prices(query)
        except net.FetchError as e:
            WARNINGS.append(f"cheapest prices: {e}")
            continue
        for n in chunk:
            entries[n] = [found.get(n), now]
    if todo:
        net.atomic_json(path, {"schema": PRICE_SCHEMA, "prices": entries})
    out = {}
    for n in wanted:
        price = (entries.get(n) or [None])[0]
        out[n] = price if price is not None else (db.get(n) or {}).get("price")
    return out
