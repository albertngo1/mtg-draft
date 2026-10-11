"""EDHTop16 as card evidence: what tournament decks played, and how those decks scored.

Why this source: it is the only public place that ties whole decklists to game results (wins, losses, draws,
final standing), so it is the only place a per-card win-rate gap can be measured. It covers cEDH tournaments
only (Bracket 5), so score.py shrinks the correction hard and applies it below Bracket 5 to a few roles only.

What the GraphQL API (https://edhtop16.com/api/graphql) does, read from its introspection schema 2026-10-11:
- `commander(name:)` is an exact, case-sensitive lookup. A double-faced commander is "Front // Back"
  (Scryfall's spelling); a partner pair is both names joined by " / " in alphabetical order (all 578 pairs
  on the site follow that order). An unknown name answers HTTP 200 with `commander: null` and the error
  "Query returned no rows".
- `Commander.entries(first, after, filters: {minEventSize, timePeriod, maxStanding}, sortBy)` pages by offset
  cursor; the order is stable between calls. `Entry.maindeck` is the set of card names outside the command
  zone (99 cards, 98 for a pair); a basic land appears once however many copies the deck ran.
- Reading `maindeck` costs the server about 0.17 s per entry (an entry without it takes a few milliseconds),
  so a page holds PAGE entries and stays well inside net's 60 s timeout. A cold read of 284 entries
  (Chatterfang, one year) takes under a minute once, then comes from the one-day cache.
- An entry made the top cut when `standing <= tournament.topCut`; a tournament with topCut 0 had no cut. That
  reproduces the site's own `stats.topCuts` (68 of 284 for Chatterfang over one year).
"""
import hashlib, json, os, re, urllib.parse
from .. import net

NAME, KIND = "edhtop16", "tournament"
API = "https://edhtop16.com/api/graphql"
SITE = "https://edhtop16.com"
TIME_PERIODS = ("ALL_TIME", "ONE_MONTH", "THREE_MONTHS", "SIX_MONTHS", "ONE_YEAR", "POST_BAN")
PAGE = 100          # entries per request: about 17 s of server time, and net gives up at 60 s
MAX_ENTRIES = 1500  # signals() reads the newest this many; a play rate is then known to about +-2.5 points
NO_ROWS = "Query returned no rows"  # the API's way of saying "no such commander"

STATS_QUERY = """
query Stats($name: String!, $period: TimePeriod!) {
  commander(name: $name) { stats(filters: {timePeriod: $period}) { count topCuts conversionRate winRate } }
}"""

ENTRIES_QUERY = """
query Entries($name: String!, $first: Int!, $after: String, $period: TimePeriod!) {
  commander(name: $name) {
    entries(first: $first, after: $after, filters: {minEventSize: 0, timePeriod: $period}, sortBy: NEW) {
      pageInfo { hasNextPage endCursor }
      edges { node {
        id wins losses draws standing
        maindeck { name }
        tournament { TID name size topCut tournamentDate }
      } }
    }
  }
}"""

COMMANDERS_QUERY = """
query Commanders($first: Int!, $after: String, $minEntries: Int!, $period: TimePeriod!) {
  commanders(first: $first, after: $after, minEntries: $minEntries, sortBy: POPULARITY, timePeriod: $period) {
    pageInfo { hasNextPage endCursor }
    edges { node { name stats(filters: {timePeriod: $period}) { count conversionRate } } }
  }
}"""


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
    """{"entries", "topcuts", "conversion", "win_rate"} from a stats answer; None for an unknown commander."""
    stats = _commander_node(payload).get("stats")
    if not stats:
        return None
    return {"entries": stats.get("count") or 0, "topcuts": stats.get("topCuts") or 0,
            "conversion": stats.get("conversionRate") or 0.0, "win_rate": stats.get("winRate") or 0.0}


def parse_entry(node):
    """One entry node → an entries() record, or None when the entry has no decklist."""
    cards = list(dict.fromkeys(c["name"] for c in node.get("maindeck") or [] if c and c.get("name")))
    if not cards:
        return None
    t = node.get("tournament") or {}
    standing, cut = node.get("standing"), t.get("topCut") or 0
    return {"id": node.get("id"), "wins": node.get("wins") or 0, "losses": node.get("losses") or 0,
            "draws": node.get("draws") or 0, "standing": standing,
            "topcut": bool(standing and cut and standing <= cut),  # cut == 0: the event had no top cut
            "cards": cards,
            "tournament": {"name": t.get("name"), "date": (t.get("tournamentDate") or "")[:10],
                           "size": t.get("size") or 0, "tid": t.get("TID"), "top_cut": cut}}


def parse_entries(payload):
    """(entries, next_cursor) from one page of a commander's entries. Entries without a decklist are dropped;
    next_cursor is None on the last page."""
    conn = _commander_node(payload).get("entries") or {}
    found = [parse_entry(edge.get("node") or {}) for edge in conn.get("edges") or []]
    return [e for e in found if e], _next_cursor(conn)


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


def signals_from_entries(entries, commanders, *, time_period="ONE_YEAR", url="", fetched="", cache="network"):
    """The Signal for these entries. Pure, so validation can hold a deck out and rebuild the signal without
    it. Per card, the tournament stats are summed over the entries that ran it; `totals` is the same over all
    of them. `meta["stats"]` (the site's own totals) is left None here; signals() fills it in."""
    cards, totals = {}, _blank()
    for entry in entries:
        _add(totals, entry)
        for name in dict.fromkeys(entry["cards"]):  # once per entry, in deck order
            _add(cards.setdefault(name, _blank()), entry)
    return {"source": NAME, "kind": KIND, "commanders": list(commanders), "bracket": None, "theme": None,
            "url": url, "fetched": fetched, "cache": cache, "n": len(entries), "cards": cards,
            "totals": totals, "meta": {"stats": None, "time_period": time_period, "truncated": False}}


# ---------------------------------------------------------------- network
def _graphql_errors(payload):
    """Error messages in a GraphQL answer, leaving out 'no rows' (that one means an unknown commander)."""
    msgs = [str(e.get("message", "")) for e in payload.get("errors") or [] if isinstance(e, dict)]
    return [m for m in msgs if NO_ROWS not in m]


def _cache_key(op, variables):
    """A readable cache file name: operation, commander slug, and a hash of every variable."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(variables.get("name") or "").lower()).strip("-")[:40]
    digest = hashlib.sha1(json.dumps(variables, sort_keys=True).encode()).hexdigest()[:10]
    return "-".join(part for part in (op, slug, digest) if part)


def _query(op, query, variables, *, refresh=None, offline=None):
    """One GraphQL request through net (paced, retried, cached). Returns (payload, info).
    A server-side error raises FetchError and the answer is deleted from the cache: the API reports
    transient failures with HTTP 200, which net would otherwise keep for a day."""
    key = _cache_key(op, variables)
    payload, info = net.fetch_json(API, source=NAME, key=key, data={"query": query, "variables": variables},
                                   refresh=refresh, offline=offline)
    problems = _graphql_errors(payload) if isinstance(payload, dict) else ["the answer was not a JSON object"]
    if problems:
        try:
            os.remove(net.cache_file(NAME, key))
        except OSError:
            pass
        raise net.FetchError(NAME, API, "GraphQL error: " + "; ".join(problems)[:300])
    return payload, info


def _merge_info(infos):
    """One fetched time and cache state for a read of several pages: the oldest page, the worst state."""
    states = {i["cache"] for i in infos}
    return {"fetched": min(i["fetched"] for i in infos),
            "cache": "stale" if "stale" in states else "network" if "network" in states else "fresh"}


def _collect(commanders, time_period, limit, refresh, offline):
    """Page through the commander's entries, newest first. Returns (entries with decklists, info, truncated),
    where `truncated` says the limit stopped the read before the last entry."""
    _check_period(time_period)
    name = commander_name(commanders)
    found, seen_ids, cursors, infos, after = [], set(), set(), [], None
    while True:
        variables = {"name": name, "first": PAGE, "after": after, "period": time_period}
        payload, info = _query("entries", ENTRIES_QUERY, variables, refresh=refresh, offline=offline)
        infos.append(info)
        page, after = parse_entries(payload)
        for entry in page:  # a page boundary can shift between runs: keep each entry once
            if entry["id"] not in seen_ids:
                seen_ids.add(entry["id"])
                found.append(entry)
        if limit and len(found) >= limit:
            return found[:limit], _merge_info(infos), bool(after) or len(found) > limit
        if not after or after in cursors:  # last page, or a cursor that does not advance (never loop)
            return found, _merge_info(infos), False
        cursors.add(after)


def entries(commanders, time_period="ONE_YEAR", *, limit=None, refresh=None, offline=None):
    """Every entry with a decklist for this commander (or pair) in the period, newest first:
    [{"id", "wins", "losses", "draws", "standing", "topcut", "cards", "tournament": {"name", "date", "size",
    "tid", "top_cut"}}]. `limit` stops after that many entries (None reads them all: about 17 s per 100).
    [] when EDHTop16 has no such commander."""
    return _collect(commanders, time_period, limit, refresh, offline)[0]


def commander_stats(commanders, time_period="ONE_YEAR", *, refresh=None, offline=None):
    """The site's own totals for the commander: {"entries", "topcuts", "conversion", "win_rate"}, or None."""
    _check_period(time_period)
    variables = {"name": commander_name(commanders), "period": time_period}
    payload, _ = _query("stats", STATS_QUERY, variables, refresh=refresh, offline=offline)
    return parse_stats(payload)


def signals(commanders, bracket=None, theme=None, *, time_period="ONE_YEAR", limit=MAX_ENTRIES, refresh=None,
            offline=None):
    """The registry call (providers/__init__.py). Tournament results carry no bracket or theme tags, so a
    theme gets no signal and `bracket` is ignored: score.py decides how much weight Bracket 5 data earns.
    Reads the newest `limit` entries (None: all); meta["truncated"] says whether that cut anything."""
    if theme:
        return []
    found, info, truncated = _collect(commanders, time_period, limit, refresh, offline)
    if not found:
        return []
    sig = signals_from_entries(found, commanders, time_period=time_period, url=_page_url(commanders),
                               fetched=info["fetched"], cache=info["cache"])
    sig["meta"]["stats"] = commander_stats(commanders, time_period, refresh=refresh, offline=offline)
    sig["meta"]["truncated"] = truncated
    return [sig]


def top_commanders(min_entries=150, time_period="ONE_YEAR", *, refresh=None, offline=None):
    """Commanders with at least `min_entries` entries in the period, most played first:
    [{"name", "entries", "conversion"}]. A partner pair appears under its pair name ('A / B')."""
    _check_period(time_period)
    out, after, cursors = [], None, set()
    while True:
        variables = {"first": PAGE, "after": after, "minEntries": min_entries, "period": time_period}
        payload, _ = _query("commanders", COMMANDERS_QUERY, variables, refresh=refresh, offline=offline)
        page, after = parse_commanders(payload)
        out += page
        if not after or after in cursors:
            break
        cursors.add(after)
    return sorted(out, key=lambda c: (-c["entries"], c["name"]))
