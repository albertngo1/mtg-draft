"""EDHTop16 as card evidence: what tournament decks played, and how those decks scored.

Why this source: it is the only public place that ties decks to game results (wins, losses, draws, final
standing), so it is the only place a per-card win-rate gap can be measured. It covers cEDH tournaments only
(Bracket 5), so score.py shrinks the correction hard and applies it below Bracket 5 to a few roles only.

Persisted queries only (since 2026-10-19). https://edhtop16.com/api/graphql no longer takes plain-text GraphQL.
It answers every such request with HTTP 200 and {"errors": ["Only persisted queries are allowed in production.
Plain text queries are disabled."]}, where each error is a bare string, not a {"message": ...} object. (The
first version of this module read only object errors, took the refusal for an empty answer, and cached it: no
tournament evidence and no warning.) The site's own pages are a Relay app that POSTs
{"variables": {...}, "extensions": {"pastoria-id": "<id>"}} and no query text; PERSISTED below lists the ids
this module sends. An id the server does not know answers HTTP 400 (text/html, "Unable to find persisted
query: <id>"); _query turns that into a FetchError that says the ids need refreshing.

Refreshing the ids after the site redeploys: the compiled Relay operations are in the JavaScript files under
https://edhtop16.com/assets/ (the page's <script> links lead to most of them; the rest load on demand, so also
search the files a browser's network tab shows). Each operation ends with
`params:{id:`<id>`,metadata:{},name:`<operation>`,operationKind:`query`,text:null}`: copy the id of every
operation named in PERSISTED (2026-10-19: `entries-*.js` holds entries_CommanderEntriesQuery). If a field was
renamed too, the same file shows the new variables and fields.

What each query takes and returns (checked live 2026-10-19):
- stats: {commander, minEventSize, timePeriod} -> commander.stats {count, conversionRate, metaShare} and
  commander.id. There is no game win rate and no top-cut count: topcuts is rebuilt as count x conversionRate.
- entries: the first 48 entries, newest first: {commander, minEventSize, timePeriod, sortBy: NEW, maxStanding}
  -> commander.id (a node id) and commander.entries {edges [{node {id, standing, wins, losses, draws,
  decklistUrl, tournament {name, size, tournamentDate, TID}}, cursor}], pageInfo}. An entry carries NO card
  list and its tournament NO top-cut size, so an entry's `cards` is [] and its `topcut` is always False here.
- entries_more: the rest, 200 per request: the same variables with {id: the node id, count, cursor} in place of
  commander -> node.entries, the same shape.
- staples: {commander, staplesSortBy: MOST_PLAYED} -> commander.staples [{name, type, playRateLastYear}], the
  100 cards most played by the commander's decks over the LAST YEAR. The window is fixed: no time period.
- card_entries: {commander, commanderName, cardName, count, cursor, sortBy: NEW} -> commander.cardEntries
  {edges [{node {id, standing, wins, losses, draws}}], pageInfo}: every deck (ALL TIME, no date) that ran the
  card. 1000 per request; a card played in thousands of decks takes several requests.
- commanders / commanders_more: {count: 48, cursor, colorId, minEntries, minSize, sortBy: POPULARITY,
  timePeriod} -> commanders {edges [{node {name, stats {count, conversionRate, ...}}}], pageInfo}. The first
  query ignores its cursor (always the first 48); the second pages by it.

Other behavior of the API, read from its schema 2026-10-11 and re-checked 2026-10-19:
- `commander(name:)` is an exact, case-sensitive lookup. A double-faced commander is "Front // Back"
  (Scryfall's spelling); a partner pair is both names joined by " / " in alphabetical order (all 578 pairs
  on the site follow that order). An unknown name still answers HTTP 200 with `commander: null` and the error
  "Query returned no rows", on the stats, entries, staples and card_entries queries alike.
- The entry order is stable between calls and the entry ids are the same in the entries and card_entries
  queries, which is how signals() ties a card's decks back to the entries it counted.

How signals() builds the card evidence, since an entry no longer carries its cards:
1. read the commander's newest `limit` entries in the period (the "window"); `totals` are summed over them;
2. ask for the commander's 100 most played cards (staples);
3. for each of them, ask which decks ran it and sum the window's own records over those decks only. Card
   and totals share one window and one record per entry, so the win-rate gap (with the card versus without it)
   compares like with like, even though the card query itself is all-time.
Known limits: a card outside the 100 staples gets no record, and meta["checked"] says it was not looked at, so
score.py scores it at Bracket 5 from builder data instead of reading it as "no tournament play" (the old version
saw every card in every list); the staples are ranked over the last year whatever
`time_period` is (they only choose which cards to look up); and topcuts are 0 in `totals` and per card, since
no top-cut size is available.

Cost: a cold read is 1 stats + 1 staples + the entry pages (1 per 48, then 200) + 100 card requests at
1 request per second: about two minutes for a commander with a few hundred entries (Hazel of the Rootbloom:
105 requests, 106 s). A card in more than 1000 decks takes another page only while the page before it still
reached into the window, so with the window capped at MAX_ENTRIES a card needs at most two or three. Every answer then comes from
net's one-day cache.
"""
import hashlib, json, os, re, urllib.parse
from .. import net

NAME, KIND = "edhtop16", "tournament"
API = "https://edhtop16.com/api/graphql"
SITE = "https://edhtop16.com"
TIME_PERIODS = ("ALL_TIME", "ONE_MONTH", "THREE_MONTHS", "SIX_MONTHS", "ONE_YEAR", "POST_BAN")
ENTRIES_PAGE = 200  # entries per request after the first 48
CARD_PAGE = 1000    # decks per request when asking which decks ran one card (0.3 s for 317 of them)
COMMANDERS_PAGE = 48
MAX_ENTRIES = 1500  # signals() reads the newest this many; a play rate is then known to about +-2.5 points
NO_ROWS = "Query returned no rows"  # the API's way of saying "no such commander"
# why calibrate and validate, which need whole tournament decklists, find none (they quote it)
NO_DECKLISTS = ("EDHTop16 no longer gives decklists: since 2026-10-19 it answers only the persisted queries its own "
                "pages send, and none of them returns a deck's cards")

# key -> (operation name, persisted query id). The names are the Relay operations' own; the ids come from the
# site's JavaScript (see the docstring) and change when the site is redeployed.
PERSISTED = {
    "stats": ("page_CommanderStatsQuery", "365ea6c7d469ca7dc4420af2a9ac0e94"),
    "entries": ("entries_CommanderEntriesQuery", "124b6abe467f15a68b2a706f3e192fd5"),
    "entries_more": ("CommanderEntriesListQuery", "bd28e8f9faddc1eaf4590246bf2c7a25"),
    "staples": ("staples_CommanderStaplesQuery", "3979f7397ed9d69dbf496964ee5d235b"),
    "card_entries": ("stapleDetails_LazyCardEntriesQuery", "596c65975dc989fd07acc312ca6dde8e"),
    "commanders": ("page_CommandersQuery", "adb86c7711e577a33ffd053410380b2b"),
    "commanders_more": ("TopCommandersQuery", "86fac9d8c2353944c65306a21cd17574"),
}


# ---------------------------------------------------------------- names and URLs
def commander_name(commanders):
    """EDHTop16's name for a commander or partner pair: the names joined by ' / ', alphabetical."""
    if isinstance(commanders, str):
        commanders = [commanders]
    return " / ".join(sorted(commanders))


def _page_url(commanders):
    return f"{SITE}/commander/{urllib.parse.quote(commander_name(commanders), safe='')}"


def _check_period(time_period):
    if time_period not in TIME_PERIODS:
        raise ValueError(f"time_period must be one of {', '.join(TIME_PERIODS)}, not {time_period!r}")


# ---------------------------------------------------------------- pure parsing
def _commander_node(payload):
    return ((payload or {}).get("data") or {}).get("commander") or {}


def _next_cursor(connection):
    page = connection.get("pageInfo") or {}
    return page.get("endCursor") if page.get("hasNextPage") else None


def parse_stats(payload):
    """{"entries", "topcuts", "conversion", "win_rate"} from a stats answer; None for an unknown commander.
    The query has no top-cut count (topcuts is count x conversion rate, rounded) and no game win rate
    (win_rate is None; callers read only "entries" and "conversion")."""
    stats = _commander_node(payload).get("stats")
    if not stats:
        return None
    count, rate = stats.get("count") or 0, stats.get("conversionRate") or 0.0
    return {"entries": count, "topcuts": round(count * rate), "conversion": rate, "win_rate": None}


def parse_commander_id(payload):
    """The commander's node id (what the follow-up entries query is keyed by), or None for an unknown one."""
    return _commander_node(payload).get("id")


def parse_entry(node):
    """One entry node → an entries() record, or None for a node without an id (it could not be matched to a
    card's decks). The persisted queries give an entry no card list and its tournament no top-cut size, so
    `cards` is [] and `topcut` is always False; the tournament's `top_cut` is None (unknown)."""
    if not node.get("id"):
        return None
    t = node.get("tournament") or {}
    return {"id": node["id"], "wins": node.get("wins") or 0, "losses": node.get("losses") or 0,
            "draws": node.get("draws") or 0, "standing": node.get("standing"), "topcut": False, "cards": [],
            "tournament": {"name": t.get("name"), "date": (t.get("tournamentDate") or "")[:10],
                           "size": t.get("size") or 0, "tid": t.get("TID"), "top_cut": None}}


def parse_entries(payload):
    """(entries, next_cursor) from one page of a commander's entries, from either entries query (the first
    answers under `commander`, the follow-ups under `node`). next_cursor is None on the last page."""
    data = (payload or {}).get("data") or {}
    conn = (data.get("commander") or data.get("node") or {}).get("entries") or {}
    found = [parse_entry(edge.get("node") or {}) for edge in conn.get("edges") or []]
    return [e for e in found if e], _next_cursor(conn)


def parse_staples(payload):
    """The commander's most played card names, most played first ([] for an unknown commander)."""
    staples = _commander_node(payload).get("staples") or []
    return list(dict.fromkeys(s["name"] for s in staples if s and s.get("name")))


def parse_card_entries(payload):
    """(ids of the entries on this page, the id of the page's last entry, next_cursor) from one page of the
    decks that ran a card. The last id is None on an empty page."""
    conn = _commander_node(payload).get("cardEntries") or {}
    order = [(edge.get("node") or {}).get("id") for edge in conn.get("edges") or []]
    order = [i for i in order if i]
    return set(order), (order[-1] if order else None), _next_cursor(conn)


def parse_commanders(payload):
    """([{"name", "entries", "conversion"}], next_cursor) from one page of the commander list."""
    conn = ((payload or {}).get("data") or {}).get("commanders") or {}
    out = []
    for edge in conn.get("edges") or []:
        node = edge.get("node") or {}
        stats = node.get("stats") or {}
        if node.get("name"):
            out.append({"name": node["name"], "entries": stats.get("count") or 0,
                        "conversion": stats.get("conversionRate") or 0.0})
    return out, _next_cursor(conn)


def _blank():
    return {"entries": 0, "games": 0, "wins": 0, "draws": 0, "topcuts": 0}


def _add(stats, entry):
    stats["entries"] += 1
    stats["games"] += entry["wins"] + entry["losses"] + entry["draws"]
    stats["wins"] += entry["wins"]
    stats["draws"] += entry["draws"]
    stats["topcuts"] += 1 if entry["topcut"] else 0


def _signal(commanders, n, cards, totals, *, time_period, url, fetched, cache):
    """A Signal record (providers/__init__.py). `meta["stats"]` (the site's own totals) starts as None;
    signals() fills it in."""
    return {"source": NAME, "kind": KIND, "commanders": list(commanders), "bracket": None, "theme": None,
            "url": url, "fetched": fetched, "cache": cache, "n": n, "cards": cards, "totals": totals,
            "meta": {"stats": None, "time_period": time_period, "truncated": False}}


def signals_from_entries(entries, commanders, *, time_period="ONE_YEAR", url="", fetched="", cache="network"):
    """The Signal for entries that carry their own card lists (`cards`). Pure, so validation can hold a deck
    out and rebuild the signal without it. Per card, the tournament stats are summed over the entries that ran
    it; `totals` is the same over all of them. signals() cannot use this: the entries the site gives now carry
    no cards, so it works from the card queries instead."""
    cards, totals = {}, _blank()
    for entry in entries:
        _add(totals, entry)
        for name in dict.fromkeys(entry["cards"]):  # once per entry, in deck order
            _add(cards.setdefault(name, _blank()), entry)
    return _signal(commanders, len(entries), cards, totals, time_period=time_period, url=url, fetched=fetched,
                   cache=cache)


# ---------------------------------------------------------------- network
def _graphql_errors(payload):
    """Messages of every error in a GraphQL answer, leaving out 'no rows' (that one means an unknown
    commander). An error is a {"message": ...} object, or a bare string: the persisted-query gate answers
    {"errors": ["Only persisted queries are allowed ..."]}."""
    errors = payload.get("errors") or []
    if not isinstance(errors, list):
        errors = [errors]
    msgs = [str((e.get("message") or e) if isinstance(e, dict) else e).strip() for e in errors if e]
    return [m for m in msgs if m and NO_ROWS not in m]


def _cache_key(op, query_id, variables, who=""):
    """A readable cache file name: query, commander slug, and a hash of the query id and every variable (so
    a refreshed id never reads an answer cached under the old one)."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(who).lower()).strip("-")[:40]
    digest = hashlib.sha1(json.dumps([query_id, variables], sort_keys=True).encode()).hexdigest()[:10]
    return "-".join(part for part in (op, slug, digest) if part)


def _forget(key):
    try:
        os.remove(net.cache_file(NAME, key))
    except OSError:
        pass


def _fetch(key, operation, query_id, body, refresh, offline):
    """net.fetch_json for one persisted query, with the two failures that mean 'this module is out of date'
    spelled out: HTTP 400 is the answer to an id the site no longer knows, and a 404 means the API moved (net
    would keep that 404 as a cached 'no such page' and score.py would read it as nothing to report)."""
    try:
        return net.fetch_json(API, source=NAME, key=key, data=body, refresh=refresh, offline=offline)
    except net.NotFound as err:
        _forget(key)
        raise net.FetchError(NAME, API, "the API endpoint answered 404; EDHTop16 may have moved it") from err
    except net.FetchError as err:
        if err.reason.startswith("HTTP 400"):
            raise net.FetchError(
                NAME, API, f"EDHTop16 no longer recognizes its query id for {operation} ({query_id}): the ids in "
                           "PERSISTED (providers/edhtop16.py) need refreshing from the site's JavaScript, "
                           "see that file's docstring") from err
        raise


def _query(key, variables, *, who="", refresh=None, offline=None):
    """One persisted query (a PERSISTED key) through net (paced, retried, cached). Returns (payload, info).
    A server-side error raises FetchError and the answer is deleted from the cache: the API reports
    failures with HTTP 200, which net would otherwise keep for a day. `who` (the commander) only names the
    cache file."""
    operation, query_id = PERSISTED[key]
    cache_key = _cache_key(key, query_id, variables, who)
    body = {"variables": variables, "extensions": {"pastoria-id": query_id}}
    payload, info = _fetch(cache_key, operation, query_id, body, refresh, offline)
    problems = _graphql_errors(payload) if isinstance(payload, dict) else ["the answer was not a JSON object"]
    if problems:
        _forget(cache_key)
        raise net.FetchError(NAME, API, "GraphQL error: " + "; ".join(problems)[:300])
    return payload, info


def _merge_info(infos):
    """One fetched time and cache state for a read of several pages: the oldest page, the worst state."""
    states = {i["cache"] for i in infos}
    return {"fetched": min(i["fetched"] for i in infos),
            "cache": "stale" if "stale" in states else "network" if "network" in states else "fresh"}


def _collect(commanders, time_period, limit, refresh, offline):
    """Page through the commander's entries, newest first: the first query, then the follow-up query keyed by
    the commander's node id. Returns (entries, info, truncated), where `truncated` says the limit stopped the
    read before the last entry."""
    _check_period(time_period)
    name = commander_name(commanders)
    kw = {"who": name, "refresh": refresh, "offline": offline}
    filters = {"minEventSize": 0, "timePeriod": time_period, "sortBy": "NEW", "maxStanding": None}
    payload, info = _query("entries", {"commander": name, **filters}, **kw)
    commander_id = parse_commander_id(payload)
    found, seen_ids, cursors, infos = [], set(), set(), []
    while True:
        infos.append(info)
        page, after = parse_entries(payload)
        for entry in page:  # a page boundary can shift between runs: keep each entry once
            if entry["id"] not in seen_ids:
                seen_ids.add(entry["id"])
                found.append(entry)
        if limit and len(found) >= limit:
            return found[:limit], _merge_info(infos), bool(after) or len(found) > limit
        if not after or not commander_id or after in cursors:  # last page, or a cursor that does not advance
            return found, _merge_info(infos), False            # (never loop on one)
        cursors.add(after)
        more = {"id": commander_id, "count": ENTRIES_PAGE, "cursor": after, **filters}
        payload, info = _query("entries_more", more, **kw)


def entries(commanders, time_period="ONE_YEAR", *, limit=None, refresh=None, offline=None):
    """Every entry for this commander (or pair) in the period, newest first:
    [{"id", "wins", "losses", "draws", "standing", "topcut", "cards", "tournament": {"name", "date", "size",
    "tid", "top_cut"}}]. The site gives an entry no card list and no top-cut size, so `cards` is [], `topcut`
    False and `top_cut` None. `limit` stops after that many entries (None reads them all: 48, then 200 per
    request). [] when EDHTop16 has no such commander."""
    return _collect(commanders, time_period, limit, refresh, offline)[0]


def commander_stats(commanders, time_period="ONE_YEAR", *, refresh=None, offline=None):
    """The site's own totals for the commander: {"entries", "topcuts", "conversion", "win_rate"}, or None.
    win_rate is always None: the stats query has no game win rate (see parse_stats)."""
    _check_period(time_period)
    name = commander_name(commanders)
    variables = {"commander": name, "minEventSize": 0, "timePeriod": time_period}
    payload, _ = _query("stats", variables, who=name, refresh=refresh, offline=offline)
    return parse_stats(payload)


def _staples(name, refresh, offline):
    """(the commander's 100 most played card names over the last year, info)."""
    payload, info = _query("staples", {"commander": name, "staplesSortBy": "MOST_PLAYED"}, who=name,
                           refresh=refresh, offline=offline)
    return parse_staples(payload), info


def _card_entry_ids(name, card, window, refresh, offline):
    """(ids of the entries whose deck ran `card`, infos): one request, more while the answer says there are
    more pages and the last page still reached into `window` (the entry ids signals() counts). The decks come
    newest first, in the same order as the entries query (checked live 2026-10-19 on three Chatterfang cards:
    the window's entries are a prefix of each card's list, in window order), so once a page ends on a deck
    outside the window every later page is older still: reading on would only cost requests."""
    ids, cursors, infos, after = set(), set(), [], None
    while True:
        variables = {"commander": name, "commanderName": name, "cardName": card, "count": CARD_PAGE,
                     "cursor": after, "sortBy": "NEW"}
        payload, info = _query("card_entries", variables, who=name, refresh=refresh, offline=offline)
        infos.append(info)
        page, last, after = parse_card_entries(payload)
        ids |= page
        if not after or after in cursors:  # last page, or a cursor that does not advance (never loop)
            return ids, infos
        if last not in window:              # past the window's oldest entry: the rest is older
            return ids, infos
        cursors.add(after)


def signals(commanders, bracket=None, theme=None, *, time_period="ONE_YEAR", limit=MAX_ENTRIES, refresh=None,
            offline=None):
    """The registry call (providers/__init__.py). Tournament results carry no bracket or theme tags, so a
    theme gets no signal and `bracket` is ignored: score.py decides how much weight Bracket 5 data earns.
    Reads the newest `limit` entries (None: all) as the window and, for each of the commander's 100 most
    played cards, the window's entries that ran it (see the module docstring for why and what it costs).
    `n` is the window's entry count; `totals` and the per-card stats sum those same entries' own records, with
    topcuts 0 (no top-cut size is available). meta: "stats" (the site's own totals), "time_period",
    "truncated" (whether `limit` cut the window), "checked" (the card names looked up: a card outside it was
    not looked at, which is not the same as not played; score.gather marks it so) and "cards_checked" (how
    many)."""
    if theme:
        return []
    found, info, truncated = _collect(commanders, time_period, limit, refresh, offline)
    if not found:
        return []
    name = commander_name(commanders)
    # the two single requests first: if one fails, it fails before the 100 card lookups, not after them
    site_stats = commander_stats(commanders, time_period, refresh=refresh, offline=offline)
    staples, staples_info = _staples(name, refresh, offline)
    infos, window, cards = [info, staples_info], {e["id"]: e for e in found}, {}
    for card in staples:
        ids, card_infos = _card_entry_ids(name, card, window, refresh, offline)
        infos += card_infos
        played = _blank()
        for entry_id in ids.intersection(window):  # the card's decks, but only those inside the window
            _add(played, window[entry_id])
        if played["entries"]:
            cards[card] = played
    totals = _blank()
    for entry in found:
        _add(totals, entry)
    merged = _merge_info(infos)
    sig = _signal(commanders, len(found), cards, totals, time_period=time_period, url=_page_url(commanders),
                  fetched=merged["fetched"], cache=merged["cache"])
    sig["meta"].update(stats=site_stats, truncated=truncated, cards_checked=len(staples), checked=staples)
    return [sig]


def top_commanders(min_entries=150, time_period="ONE_YEAR", *, refresh=None, offline=None):
    """Commanders with at least `min_entries` entries in the period, most played first:
    [{"name", "entries", "conversion"}]. A partner pair appears under its pair name ('A / B'). Two queries:
    the first page, then the rest by cursor."""
    _check_period(time_period)
    variables = {"count": COMMANDERS_PAGE, "colorId": None, "minEntries": min_entries, "minSize": 0,
                 "sortBy": "POPULARITY", "timePeriod": time_period}
    kw = {"refresh": refresh, "offline": offline}
    out, cursors = [], set()
    payload, _ = _query("commanders", {**variables, "cursor": None}, **kw)
    while True:
        page, after = parse_commanders(payload)
        out += page
        if not after or after in cursors:  # last page, or a cursor that does not advance (never loop)
            break
        cursors.add(after)
        payload, _ = _query("commanders_more", {**variables, "cursor": after}, **kw)
    return sorted(out, key=lambda c: (-c["entries"], c["name"]))
