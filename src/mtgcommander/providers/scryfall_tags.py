"""Scryfall function tags (the community's Tagger labels, searchable as `otag:ramp`) as sets of oracle ids.

Why tags: whether a card ramps, removes, draws or sweeps is the one fact Scryfall's volunteers have already
labelled for almost every card, so roles come from tags and not from guessing at rules text (roles.py keeps
text patterns only for brand-new cards). This module is a lookup, not card evidence, so it is not registered
in SIGNAL_PROVIDERS.

Source: the `oracle_tags` bulk file (~6 MB gzipped, ~4,500 tags, JSON Lines). Tags form a tree: a parent such
as `ramp` lists only the cards tagged with it directly and its children (`mana-rock`, `land-ramp`, ...) hold
the rest. Scryfall's `otag:` search includes every descendant (`otag:ramp` finds 2,287 cards, the tag itself
only 549), so `load` expands each requested tag the same way.

Only the requested tags are kept, in data/cache/commander/scryfall/tags.json, for TTL["scryfall_tags"] (30
days). If the bulk file cannot be fetched, the same sets come from paginated `otag:<slug>` searches."""
import json, os, time, urllib.parse
from .. import carddb, net
from ..config import TTL

SCHEMA = 1
SOURCE = "scryfall_tags"
INFO = {}    # about the last load(): {"fetched", "cache": "fresh" | "network" | "stale", "method", "url"}


def index_tags(objs):
    """Tag objects → (tags, names). tags = {id: {"slug", "children": [ids], "ids": [oracle ids]}};
    names maps every slug and alias to its tag id (a real slug beats someone else's alias)."""
    tags, names, aliases = {}, {}, []
    for t in objs:
        if not t.get("id"):
            continue
        tags[t["id"]] = {"slug": t.get("slug", ""), "children": list(t.get("child_ids") or []),
                         "ids": [g["oracle_id"] for g in t.get("taggings") or [] if g.get("oracle_id")]}
        names[t.get("slug", "")] = t["id"]
        aliases += [(a, t["id"]) for a in t.get("aliases") or []]
    for alias, tid in aliases:
        names.setdefault(alias, tid)
    return tags, names


def expand(tags, names, slugs):
    """{slug: set of oracle ids} for the requested slugs, each including all descendant tags. An unknown slug
    gives an empty set (roles.py's tests check that every slug it asks for exists)."""
    out = {}
    for slug in slugs:
        ids, seen, stack = set(), set(), [names[slug]] if slug in names else []
        while stack:
            tid = stack.pop()
            if tid in seen or tid not in tags:
                continue
            seen.add(tid)
            ids.update(tags[tid]["ids"])
            stack.extend(tags[tid]["children"])
        out[slug] = ids
    return out


def from_search(slugs):
    """Fallback: oracle ids per slug from paginated `otag:` searches (one request per 175 cards).
    net.request, not fetch_json: the pages are large and only the ids are kept (in tags.json)."""
    out = {}
    for slug in slugs:
        ids = set()
        url = carddb.SEARCH + "?" + urllib.parse.urlencode({"q": f"otag:{slug}", "unique": "cards"})
        while url:
            try:
                page = json.loads(net.request(url, source=SOURCE))
            except net.NotFound:                   # a tag nobody has used
                break
            except ValueError:
                raise net.FetchError(SOURCE, url, "the response was not JSON")
            ids.update(c["oracle_id"] for c in page.get("data", []) if c.get("oracle_id"))
            url = page.get("next_page") if page.get("has_more") else None
        out[slug] = ids
    return out


def _collect(slugs, refresh):
    """(sets, method, url): from the bulk file, else from searches."""
    raw = os.path.join(os.path.dirname(net.cache_file("scryfall", "tags")), "oracle_tags.jsonl.gz")
    try:
        url, _ = carddb.bulk_entry("oracle_tags", refresh=refresh)
        try:
            net.download(url, raw, source=SOURCE)
            tags, names = index_tags(carddb.iter_bulk(raw))
        except (OSError, EOFError, ValueError) as e:
            raise net.FetchError(SOURCE, url, f"the tag file was damaged: {e}")
        finally:
            carddb.discard(raw)
        return expand(tags, names, slugs), "bulk", url
    except net.FetchError:
        return from_search(slugs), "search", carddb.SEARCH


def _serve(doc, state, want):
    INFO.clear()
    INFO.update({"fetched": doc.get("fetched", ""), "cache": state, "method": doc.get("method", ""),
                 "url": doc.get("source", "")})
    return {t: set(doc["tags"].get(t, ())) for t in want}


def load(tags, *, refresh=None, offline=None):
    """{tag slug: set of oracle ids} (descendants included). Served from the cache when it is under 30 days
    old and holds every requested tag; otherwise rebuilt, keeping the tags that earlier calls asked for too.
    A failed rebuild falls back to an old cache that has the tags ("stale"); with none, FetchError."""
    refresh = net.MODE["refresh"] if refresh is None else refresh
    offline = net.MODE["offline"] if offline is None else offline
    want = list(dict.fromkeys([tags] if isinstance(tags, str) else tags))
    path = net.cache_file("scryfall", "tags")
    cached = net.read_json(path)
    ok = isinstance(cached, dict) and cached.get("schema") == SCHEMA and isinstance(cached.get("tags"), dict)
    have = ok and all(t in cached["tags"] for t in want)
    fresh = ok and time.time() - cached.get("ts", 0) < TTL[SOURCE]
    if have and (offline or (fresh and not refresh)):
        return _serve(cached, "fresh" if fresh else "stale", want)
    if offline:
        raise net.FetchError(SOURCE, carddb.BULK_LIST,
                             "offline (--offline) and no tag cache; run `warm` while online")
    keep = sorted(set(want) | (set(cached["tags"]) if ok else set()))
    try:
        sets, method, url = _collect(keep, refresh)
    except net.FetchError:
        if have:
            return _serve(cached, "stale", want)
        raise
    now = time.time()
    doc = {"schema": SCHEMA, "fetched": net.iso(now), "ts": now, "source": url, "method": method,
           "tags": {t: sorted(ids) for t, ids in sets.items()}}
    net.atomic_json(path, doc)
    return _serve(doc, "network", want)
