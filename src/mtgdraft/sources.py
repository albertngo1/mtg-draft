import os, json, time, datetime, urllib.request, urllib.parse
from .config import CACHE, SCRY_CACHE, UA

# Scryfall cache entry schema version. Bump whenever _scry_rec() starts storing new fields
# so older thin entries (cached before the change) are treated as cache misses and lazily
# re-fetched + re-enriched. v2 added type_line/types/subtypes/keywords/loyalty/color_identity.
# v3 adds image_url (front-face normal Scryfall image) so replay.md can embed card images.
SCRYFALL_SCHEMA = 3

def is_fresh(rec):
    """True if a cached Scryfall record is at the current schema and safe to serve.
    A record is fresh if it stamps the current schema (`_v` >= SCRYFALL_SCHEMA). Anything
    else is stale and re-fetches — including v2 entries that predate `image_url`, and
    failed-lookup placeholders (no `type_line`)."""
    if not isinstance(rec, dict):
        return False
    return rec.get("_v", 0) >= SCRYFALL_SCHEMA

def stale_ids(scry, ids):
    """Subset of `ids` that need a (re)fetch: absent from cache or holding a stale entry."""
    return [c for c in ids if not is_fresh(scry.get(c))]

def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()
def load_scry():
    try:
        with open(SCRY_CACHE) as f:
            return json.load(f)
    except Exception:
        return {}
def save_scry(d):
    _atomic_json(SCRY_CACHE, d)
def merge_scry(updates):
    """Reload-and-merge: re-read the on-disk cache immediately before writing and overlay only
    the freshly-fetched `updates` (id -> rec) on top, then write atomically. Avoids the lost-update
    race where the capture daemon's enrich and a concurrent CLI command each load the cache, mutate
    their own copy, and the last writer clobbers the other's new entries. We re-read late so we
    overwrite the smallest possible window; the atomic os.replace makes the write itself indivisible."""
    if not updates:
        return
    merged = load_scry()
    merged.update(updates)
    _atomic_json(SCRY_CACHE, merged)
def _atomic_json(path, obj):
    """Write JSON atomically, pid-suffixed tmp so concurrent writers (capture daemon + a CLI
    command both refreshing) can't interleave into the same tmp file."""
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)
def _parse_type_line(type_line):
    """Split a front-face type line into (full, types, subtypes).
    'Legendary Creature — Human Detective' -> ('Legendary Creature — Human Detective',
    ['Legendary','Creature'], ['Human','Detective']). Subtypes are the post-dash words
    (creature tribes, land/artifact/enchantment subtypes); types are the supertypes+card
    types before the dash. Handles either em-dash (—) or hyphen separators from Scryfall."""
    front = (type_line or "").split("//")[0].strip()
    # Scryfall uses the em-dash, but be defensive about a plain hyphen too.
    sep = "—" if "—" in front else (" - " if " - " in front else None)
    if sep:
        left, _, right = front.partition(sep)
    else:
        left, right = front, ""
    types = left.split()
    subtypes = right.split()
    return front, types, subtypes
def _scry_rec(d):
    ci = d.get("color_identity", [])
    faces = d.get("card_faces", [])
    text = d.get("oracle_text", "")
    if not text and faces:  # split / MDFC: stitch the faces
        text = " // ".join(f.get("oracle_text", "") for f in faces if f.get("oracle_text"))
    mana = d.get("mana_cost", "") or (faces[0].get("mana_cost", "") if faces else "")
    pt = ""
    if d.get("power") is not None:
        pt = f"{d.get('power')}/{d.get('toughness')}"
    elif faces and faces[0].get("power") is not None:
        pt = f"{faces[0].get('power')}/{faces[0].get('toughness')}"
    # capture the FULL front-face type line and parse it into structured fields. The top-level
    # type_line is present for normal cards; for MDFCs/split cards fall back to the first face.
    raw_tl = d.get("type_line") or (faces[0].get("type_line", "") if faces else "")
    full_tl, types, subtypes = _parse_type_line(raw_tl)
    loyalty = d.get("loyalty")
    if loyalty is None and faces:
        loyalty = next((f.get("loyalty") for f in faces if f.get("loyalty") is not None), None)
    # Front-face card image (Scryfall CDN). For split / MDFC cards the top-level image_uris
    # is absent — fall back to the first face. `normal` is ~488x680, the right size for embed.
    imgs = d.get("image_uris") or (faces[0].get("image_uris") if faces else None) or {}
    image_url = imgs.get("normal", "") or imgs.get("large", "") or imgs.get("small", "")
    return {
        "_v": SCRYFALL_SCHEMA,                      # schema stamp; stale entries lacking it re-fetch
        "name": (d.get("name", "?").split("//")[0].strip()),
        "full_name": d.get("name", "?"),
        "cmc": int(d.get("cmc", 0)),
        "mana": mana,
        "pt": pt,
        "color": "".join(ci) if ci else "C",
        "color_identity": list(ci),
        "rarity": d.get("rarity", "?")[:1].upper(),
        "type": full_tl.split("—")[0].strip(),   # back-compat: pre-dash type only ("Creature")
        "type_line": full_tl,                      # full string, e.g. "Creature — Human Detective"
        "types": types,                            # supertypes+card types, e.g. ["Legendary","Creature"]
        "subtypes": subtypes,                      # post-dash, e.g. ["Human","Detective"]
        "keywords": d.get("keywords", []),
        "loyalty": loyalty,
        "text": text.replace("\n", " "),
        "image_url": image_url,                    # front-face normal image; replay.md embeds it
    }
def _front_name(name):
    """Front-face name, the form 17Lands uses ('A // B' -> 'A'). Match key for the name fallback."""
    return (name or "").split("//")[0].strip()
def _fetch_by_name(name, set_code=None):
    """Scryfall exact-name lookup, optionally pinned to a set. The fallback path for cards whose
    arena_id Scryfall has not assigned yet (every card of a set, for ~the first weeks after its
    Arena release) — see resolve_ids/set_fetch."""
    url = f"https://api.scryfall.com/cards/named?exact={urllib.parse.quote(name)}"
    if set_code:
        url += f"&set={set_code.lower()}"
    return _scry_rec(json.loads(_get(url)))
def resolve_ids(ids, names=None, set_code=None):
    """Return {id: {name, cmc, color, type}} resolving misses via Scryfall (cached, 1-by-1).

    Scryfall keys Arena printings by `arena_id`, but it does not assign those until some weeks
    after a set hits Arena — so for a brand-new set EVERY id 404s here and the whole set comes
    back as failed placeholders (cmc 0, no mana cost, no oracle text). `names` ({id: 17Lands card
    name}) enables the fallback: on a 404, look the card up by exact name instead, then cache the
    result under the Arena id so the rest of the pipeline (which joins on id) is unchanged."""
    names = {str(k): v for k, v in (names or {}).items()}
    cache = load_scry()
    out, fetched = {}, {}
    for cid in ids:
        cid = str(cid)
        if is_fresh(cache.get(cid)):  # served from cache; stale/missing entries fall through to fetch
            out[cid] = cache[cid]
            continue
        try:
            rec = _scry_rec(json.loads(_get(f"https://api.scryfall.com/cards/arena/{cid}")))
        except Exception as e:
            rec = None
            if names.get(cid):     # arena_id not assigned yet -> fall back to an exact-name lookup
                try:
                    rec = _fetch_by_name(names[cid], set_code)
                    time.sleep(0.06)
                except Exception:
                    rec = None
            if rec is None:
                rec = {"name": names.get(cid) or f"<{cid}?>", "full_name": "?", "cmc": 0,
                       "color": "?", "rarity": "?", "type": f"(lookup failed: {e})"}
        cache[cid] = rec
        out[cid] = rec
        fetched[cid] = rec     # only the freshly-fetched entries; merged in late to avoid clobbering
        time.sleep(0.06)  # be polite to Scryfall
    merge_scry(fetched)        # reload-and-merge so a concurrent writer's new entries survive
    return out
def set_fetch(set_code, id_names=None):
    """Page the whole set from Scryfall's search endpoint, caching each printing by arena_id
    (cost + oracle text + P/T). One paginated walk (~2-3 requests) instead of 1-per-card.

    Scryfall assigns `arena_id` only some weeks after a set reaches Arena, so for a brand-new
    set this walk finds the cards but caches NOTHING (every printing has arena_id None) and the
    live table ends up with MV 0 and an empty oracle-text section. `id_names` ({mtga_id: name},
    which 17Lands supplies) closes that gap: the same printings get indexed by front-face name
    and re-keyed onto the Arena ids, so the id-joined pipeline downstream needs no changes.
    Returns (n_by_arena_id, n_by_name)."""
    url = (f"https://api.scryfall.com/cards/search?q=e:{set_code.lower()}"
           f"&unique=prints&format=json")
    fetched, by_name = {}, {}
    n = 0
    while url:
        resp = json.loads(_get(url))
        for d in resp.get("data", []):
            rec = _scry_rec(d)
            by_name.setdefault(_front_name(rec.get("name")), rec)
            aid = d.get("arena_id")
            if aid is None:
                continue
            fetched[str(aid)] = rec
            n += 1
        url = resp.get("next_page") if resp.get("has_more") else None
        if url:
            time.sleep(0.1)
    # Name-join backfill for every id the arena_id pass didn't cover.
    n_named = 0
    for cid, name in (id_names or {}).items():
        cid = str(cid)
        if cid in fetched:
            continue
        rec = by_name.get(_front_name(name))
        if rec:
            fetched[cid] = rec
            n_named += 1
    merge_scry(fetched)        # reload-and-merge so a concurrent writer's new entries survive
    return n, n_named
def warm_set(cfg):
    """Pre-cache the whole set so live drafts make ZERO per-card queries.
    17Lands gives name/color/rarity/stats keyed by mtga_id; Scryfall supplies cost + text + P/T."""
    print(f"\n  Warming {cfg['set']} from Scryfall (cost + oracle text + P/T)...")
    # 17Lands is the source of the id->name map that lets set_fetch/resolve_ids fall back to a
    # name lookup for sets Scryfall hasn't assigned arena_ids to yet.
    try:
        data = seventeen(cfg["set"], cfg["fmt"], cfg["days"], cfg["refresh"])
    except Exception:
        data = []
    id_names = {str(c["mtga_id"]): c.get("name") for c in data if c.get("mtga_id")}
    try:
        n, n_named = set_fetch(cfg["set"], id_names)
        note = f" (+{n_named} matched by name — Scryfall has no arena_id for them yet)" if n_named else ""
        print(f"  Cached {n + n_named} printings{note}. "
              f"Scryfall cache now holds {len(load_scry())} cards.")
    except Exception as e:
        print(f"  set search failed ({e}). Falling back to per-card from 17Lands ids...")
        resolve_ids(list(id_names), id_names, cfg["set"])
    print("  Done — future `pull`/`rank` for this set = 0 live queries "
          "(17Lands itself caches 24h).\n")
def _time_period(days):
    """Map a days-window to 17Lands' time_period enum (the new /api/card_data endpoint
    takes an enum, not arbitrary dates). The default 120d and the 1200d historical-proxy
    window both collapse to ALL_TIME — which is the richest sample, so that's the right
    default for an active set."""
    d = int(days)
    if d <= 1:
        return "LAST_DAY"
    if d <= 7:
        return "LAST_WEEK"
    if d <= 14:
        return "LAST_TWO_WEEKS"
    return "ALL_TIME"
def seventeen(set_code, fmt, days, refresh=False):
    path = os.path.join(CACHE, f"17lands_{set_code}_{fmt}_{days}d.json")
    if not refresh and os.path.exists(path) and (time.time() - os.path.getmtime(path) < 86400):
        with open(path) as f:
            return json.load(f)
    # 17Lands moved the live card-stats feed to /api/card_data (event_type + time_period).
    # The old /card_ratings/data endpoint still answers but now returns the card list with
    # every win-rate/seen stat nulled — so it must not be used. The new payload wraps the
    # rows in {"copyright","notes","data":[...]}; we unwrap and cache the bare list so all
    # downstream callers (and pre-existing bare-list caches) keep working unchanged.
    url = (f"https://www.17lands.com/api/card_data?expansion={set_code}"
           f"&event_type={fmt}&time_period={_time_period(days)}")
    try:
        raw = json.loads(_get(url))
        data = raw["data"] if isinstance(raw, dict) and "data" in raw else raw
    except Exception as e:
        # 17Lands outage / network error: fall back to a stale cache if we have
        # one, otherwise surface a clear error instead of an opaque URLError.
        if os.path.exists(path):
            print(f"  ⚠ 17Lands fetch failed ({e}); using stale cache "
                  f"{os.path.basename(path)}")
            with open(path) as f:
                return json.load(f)
        raise RuntimeError(
            f"17Lands unavailable and no cache for {set_code}/{fmt}: {e}"
        ) from e
    _atomic_json(path, data)
    return data
def ratings(set_code, fmt, days, refresh=False):
    """17Lands dataset with the historical fallback: if the requested format has no win-rate data
    yet (e.g. a Quick-Draft re-run early in its window, or a junk format), proxy with the set's
    original PremierDraft over a wide window. Returns (data, ratings_fmt_label)."""
    data = seventeen(set_code, fmt, days, refresh)
    if any(c.get("ever_drawn_win_rate") for c in data):
        return data, fmt
    proxy = seventeen(set_code, "PremierDraft", max(int(days), 1200), refresh)
    if any(c.get("ever_drawn_win_rate") for c in proxy):
        return proxy, "PremierDraft (historical proxy)"
    return data, fmt
