"""Archidekt provider: real decklists tagged with a bracket, the second source of what builders choose.

Why it is second: EDHREC answers a whole bracket in one request, while Archidekt needs one request per deck
(about 280 KB of JSON, 60 KB on the wire). It earns its place as the fallback when EDHREC is down or has few
decks at a bracket, and as the one source with Bracket 1 decks in numbers.

How the API behaves (verified 2026-10-11):
- GET /api/decks/v3/?commanderName=<card>&edhBracket=<1-5>&formats=3&orderBy=-updatedAt&page=<n> lists deck
  summaries, 60 a page (pageSize is ignored; count stops at 1000). `commanderName` is an exact card name, and
  for a double-faced card it must be the full 'A // B' name. It matches decks that merely PLAY the card, not
  only decks it commands (a Chatterfang deck with Hazel in it is in Hazel's results), so the commander is
  checked on the full deck. Two commanderName parameters do not combine; a pair is searched by its first name.
- A summary's `size` is Archidekt's own count of main-deck cards. It lets us skip decks that are plainly not
  100 cards without downloading them (roughly one deck in six on a typical page).
- GET /api/decks/<id>/ is the deck: `categories` [{name, includedInDeck}] and `cards` [{quantity, categories
  [names], card: {oracleCard: {name}}}]. The commander is the card in the "Commander" category. A card counts
  toward the deck by its FIRST category: that rule reproduces Archidekt's `size` on every deck checked, where
  "any category excluded" does not (a card tagged ['Ramp', 'Maybeboard'] is in the deck). Maybeboard and
  "Tokens & Extras" are includedInDeck false, but Sideboard is includedInDeck TRUE, so names are checked too.
- The deck's cards carry EDHREC's salt per card (oracleCard.salt), which this module does not use.

Cards keep Archidekt's spelling: double-faced cards are 'A // B', as on Scryfall."""
import re, unicodedata, urllib.parse
from collections import Counter
from .. import net

NAME = "archidekt"
KIND = "builder"
SEARCH_SOURCE = "archidekt_search"   # which decks exist for a commander and bracket
DECK_SOURCE = "archidekt"            # one decklist
API = "https://archidekt.com/api/decks/"
SITE = "https://archidekt.com/decks/"
EDH = 3                              # Archidekt's format id for Commander
OUT_OF_DECK = ("maybeboard", "sideboard")   # category names that never count, whatever includedInDeck says
MIN_MAIN, MAX_MAIN = 98, 100         # a complete list: 100 cards counting the commanders, with a little slack
MAX_PAGES = 5                        # search pages per call, 60 decks each
DOWNLOADS_PER_DECK = 3               # downloads allowed per deck wanted (other commanders' decks are skipped)


# ---------------------------------------------------------------- parsing (pure; tests feed these dicts)
def search_url(commander, bracket=None, page=1):
    """The search page that lists decks containing `commander`, newest update first."""
    query = [("commanderName", commander)] + ([("edhBracket", bracket)] if bracket else [])
    query += [("formats", EDH), ("orderBy", "-updatedAt"), ("page", page)]
    return f"{API}v3/?{urllib.parse.urlencode(query)}"


def _iso(stamp):
    """'2026-10-11T10:40:45.399158Z' -> '2026-10-11T10:40:45Z', the format every `fetched` field uses."""
    return re.sub(r"\.\d+", "", stamp) if stamp else ""


def _card_key(name):
    """A card name reduced to what two spellings share: front face, no accents, apostrophes or case."""
    front = unicodedata.normalize("NFKD", name.split("//")[0]).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"['\u2018\u2019`]", "", front).split())


def parse_search(obj):
    """Deck summaries from one search page, newest update first: {"id", "size", "bracket", "updated"}.
    Private and unlisted decks are left out; the owner did not publish them."""
    return [{"id": r["id"], "size": r.get("size"), "bracket": r.get("edhBracket") or None,
             "updated": _iso(r.get("updatedAt"))}
            for r in obj.get("results") or [] if r.get("id") and not (r.get("private") or r.get("unlisted"))]


def _counts_toward_deck(first_category, categories):
    """Whether a card whose first category is `first_category` is in the main deck (see the top)."""
    if first_category.lower() in OUT_OF_DECK:
        return False
    return (categories.get(first_category) or {}).get("includedInDeck", True)


def parse_deck(obj):
    """One deck detail as {"id", "url", "bracket", "commanders", "cards", "updated", "size"}. `cards` holds
    the main-deck card names without the commanders, each once (basic lands too); `size` counts copies,
    commanders included, which is what the 98-100 completeness rule reads."""
    categories = {c.get("name"): c for c in obj.get("categories") or []}
    commanders, cards, size = [], [], 0
    for entry in obj.get("cards") or []:
        names = entry.get("categories") or []
        name = ((entry.get("card") or {}).get("oracleCard") or {}).get("name")
        copies = entry.get("quantity") or 0
        if not name or copies < 1 or entry.get("deletedAt") or entry.get("companion"):
            continue                      # a companion sits outside the 100
        if names and not _counts_toward_deck(names[0], categories):
            continue
        size += copies
        if any(c.lower() == "commander" for c in names):
            commanders.append(name)
        elif name not in cards:
            cards.append(name)
    return {"id": obj.get("id"), "url": f"{SITE}{obj.get('id')}", "bracket": obj.get("edhBracket") or None,
            "commanders": commanders, "cards": cards, "updated": _iso(obj.get("updatedAt")), "size": size}


# ---------------------------------------------------------------- fetching
def _expect(obj, key, info):
    """The response, or a FetchError when it lacks `key`: the API changed, and an empty answer hides that."""
    if not isinstance(obj, dict) or key not in obj:
        raise net.FetchError(NAME, info["url"],
                             f"no '{key}' in the response (Archidekt may have changed its API)")
    return obj


def _summaries(commander, bracket, infos, refresh, offline):
    """Search summaries, newest first, fetching the next page only when the caller asks for more. The info
    of every search page fetched goes into `infos`."""
    seen = set()
    for page in range(1, MAX_PAGES + 1):
        obj, info = net.fetch_json(search_url(commander, bracket, page), source=SEARCH_SOURCE,
                                   key=f"search_{commander}_{bracket or 'all'}_p{page}",
                                   refresh=refresh, offline=offline)
        infos.append(info)
        rows = parse_search(_expect(obj, "results", info))
        rows = [r for r in rows if r["id"] not in seen]       # decks added meanwhile shift the pages
        seen.update(r["id"] for r in rows)
        yield from rows
        if not obj.get("next") or not rows:
            return


def _slim_deck(obj):
    """Only the fields parse_deck reads. A full deck response is about 400 KB (every printing's prices and
    images); this keeps the cache at a few KB per deck."""
    if not isinstance(obj, dict) or "cards" not in obj:
        return obj                        # leave a changed format intact so _expect can report it
    return {"id": obj.get("id"), "edhBracket": obj.get("edhBracket"), "updatedAt": obj.get("updatedAt"),
            "categories": [{"name": c.get("name"), "includedInDeck": c.get("includedInDeck", True)}
                           for c in obj.get("categories") or []],
            "cards": [{"quantity": e.get("quantity"), "categories": e.get("categories"),
                       "deletedAt": e.get("deletedAt"), "companion": e.get("companion"),
                       "card": {"oracleCard": {"name": ((e.get("card") or {}).get("oracleCard") or {}).get("name")}}}
                      for e in obj.get("cards") or []]}


def _download(deck_id, refresh, offline):
    """(deck, info) for one deck, or (None, None) when it was deleted since the search."""
    try:
        obj, info = net.fetch_json(f"{API}{deck_id}/", source=DECK_SOURCE, key=f"deck_{deck_id}",
                                   refresh=refresh, offline=offline, keep=_slim_deck)
    except net.NotFound:
        return None, None
    return parse_deck(_expect(obj, "cards", info)), info


def _collect(commanders, bracket, limit, refresh, offline):
    """(decks, infos): up to `limit` complete decks of exactly these commanders, newest first, and the info
    of every fetch they rest on. Downloads are capped so a pair, whose first commander is searched alone,
    cannot run away; a deck already cached costs nothing and does not count."""
    if not commanders or limit < 1:
        return [], []
    wanted = {_card_key(c) for c in commanders}
    found, infos, downloads = [], [], 0
    for row in _summaries(commanders[0], bracket, infos, refresh, offline):
        if row["size"] is not None and not MIN_MAIN <= row["size"] <= MAX_MAIN:
            continue
        deck, info = _download(row["id"], refresh, offline)
        if info and info["cache"] == "network":
            downloads += 1
        if (deck and {_card_key(c) for c in deck["commanders"]} == wanted
                and MIN_MAIN <= deck["size"] <= MAX_MAIN and (not bracket or deck["bracket"] == bracket)):
            found.append(deck)
            infos.append(info)
        if len(found) >= limit or downloads >= DOWNLOADS_PER_DECK * limit:
            break                         # stop before the generator fetches another search page
    return found, infos


def decks(commanders, bracket=None, *, limit=40, refresh=None, offline=None):
    """Complete decks of exactly these commanders (98-100 main-deck cards counting them), most recently
    updated first, at most `limit`; at a bracket when one is given. Each is parse_deck's record."""
    return _collect(commanders, bracket, limit, refresh, offline)[0]


def _freshness(infos):
    states = {i["cache"] for i in infos}
    return "stale" if "stale" in states else "network" if "network" in states else "fresh"


def signals(commanders, bracket=None, theme=None, *, limit=40, refresh=None, offline=None):
    """One builder Signal from the decks above, as a list of one: `n` is the decks used and each card's stats
    are {"decks": decks that play it, "of": n, "synergy": None}. Empty when no deck qualifies, and always
    empty for a theme: Archidekt's tags are free text, so there is no theme to match."""
    if theme:
        return []
    found, infos = _collect(commanders, bracket, limit, refresh, offline)
    if not found:
        return []
    plays = Counter(name for deck in found for name in deck["cards"])
    return [{"source": NAME, "kind": KIND, "commanders": list(commanders), "bracket": bracket, "theme": None,
             "url": infos[0]["url"], "fetched": min(i["fetched"] for i in infos), "cache": _freshness(infos),
             "n": len(found), "cards": {name: {"decks": k, "of": len(found), "synergy": None}
                                        for name, k in plays.items()},
             "totals": None, "meta": {"deck_ids": [deck["id"] for deck in found]}}]
