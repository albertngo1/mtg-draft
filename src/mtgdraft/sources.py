import os, json, time, datetime, urllib.request
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
def resolve_ids(ids):
    """Return {id: {name, cmc, color, type}} resolving misses via Scryfall (cached, 1-by-1)."""
    cache = load_scry()
    out, dirty = {}, False
    for cid in ids:
        cid = str(cid)
        if is_fresh(cache.get(cid)):  # served from cache; stale/missing entries fall through to fetch
            out[cid] = cache[cid]
            continue
        try:
            rec = _scry_rec(json.loads(_get(f"https://api.scryfall.com/cards/arena/{cid}")))
        except Exception as e:
            rec = {"name": f"<{cid}?>", "full_name": "?", "cmc": 0, "color": "?",
                   "rarity": "?", "type": f"(lookup failed: {e})"}
        cache[cid] = rec
        out[cid] = rec
        dirty = True
        time.sleep(0.06)  # be polite to Scryfall
    if dirty:
        save_scry(cache)
    return out
def set_fetch(set_code):
    """Page the whole set from Scryfall's search endpoint, caching each printing by arena_id
    (cost + oracle text + P/T). One paginated walk (~2-3 requests) instead of 1-per-card."""
    cache = load_scry()
    url = (f"https://api.scryfall.com/cards/search?q=e:{set_code.lower()}"
           f"&unique=prints&format=json")
    n = 0
    while url:
        resp = json.loads(_get(url))
        for d in resp.get("data", []):
            aid = d.get("arena_id")
            if aid is None:
                continue
            cache[str(aid)] = _scry_rec(d)
            n += 1
        url = resp.get("next_page") if resp.get("has_more") else None
        if url:
            time.sleep(0.1)
    save_scry(cache)
    return n
def warm_set(cfg):
    """Pre-cache the whole set so live drafts make ZERO per-card queries.
    17Lands gives name/color/rarity/stats keyed by mtga_id; Scryfall supplies cost + text + P/T."""
    print(f"\n  Warming {cfg['set']} from Scryfall (cost + oracle text + P/T)...")
    try:
        n = set_fetch(cfg["set"])
        print(f"  Cached {n} printings. Scryfall cache now holds {len(load_scry())} cards.")
    except Exception as e:
        print(f"  set search failed ({e}). Falling back to per-card from 17Lands ids...")
        data = seventeen(cfg["set"], cfg["fmt"], cfg["days"], cfg["refresh"])
        resolve_ids([str(c["mtga_id"]) for c in data if c.get("mtga_id")])
    print("  Done — future `pull`/`rank` for this set = 0 live queries "
          "(17Lands itself caches 24h).\n")
def seventeen(set_code, fmt, days, refresh=False):
    path = os.path.join(CACHE, f"17lands_{set_code}_{fmt}_{days}d.json")
    if not refresh and os.path.exists(path) and (time.time() - os.path.getmtime(path) < 86400):
        with open(path) as f:
            return json.load(f)
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    url = (f"https://www.17lands.com/card_ratings/data?expansion={set_code}"
           f"&format={fmt}&start_date={start}&end_date={end}")
    data = json.loads(_get(url))
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
