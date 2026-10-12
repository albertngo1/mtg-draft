"""HTTP for the Commander builder: one paced, retrying client with a file cache in front of it.

Why not mtgdraft.sources._get: it has no retry or back-off, and most Commander sources (EDHREC,
EDHTop16, Archidekt, Commander Spellbook) are community sites that must not be hammered (17Lands
has banned this repo's author before). Every request goes through here, which:

1. serves a fresh cache entry without touching the network;
2. spaces requests to one host by PACE[host] seconds;
3. retries 429 and 5xx answers with exponential back-off, honoring Retry-After;
4. when the network fails, falls back to an old cache entry and reports its age.

Caches live under data/cache/commander/<source>/ (gitignored), like the repo's 17Lands cache.
`configure()` sets the run-wide --refresh / --offline mode; every fetch can still override it."""
import datetime, gzip, hashlib, json, os, re, time, urllib.error, urllib.parse, urllib.request
from .config import CACHE, DAY, TTL, UA

PACE = {                                 # minimum seconds between two requests to one host
    "api.scryfall.com": 0.5,             # 500 ms: Scryfall's limit for /cards/search, /named, /collection
    "data.scryfall.io": 0.0,             # bulk-file CDN, no request limit
    "json.edhrec.com": 1.0,
    "edhtop16.com": 1.0,
    "archidekt.com": 1.0,
    "backend.commanderspellbook.com": 1.0,
    "mtgjson.com": 0.5,
}
DEFAULT_PACE = 1.0
RETRIES = 4                              # back-off waits 1, 2, 4, 8 s (or Retry-After, capped at 60 s)
TIMEOUT = 60
RETRY_CODES = (429, 500, 502, 503, 504)
MISSING_CODES = {"json.edhrec.com": (403, 404)}  # EDHREC's file host answers 403 for a page that does not exist

MODE = {"refresh": False, "offline": os.environ.get("MTG_OFFLINE") == "1"}
_last = {}                               # host -> time.monotonic() of the last request


class FetchError(Exception):
    """A request failed and no cached copy could stand in. `source` names the missing signal."""
    def __init__(self, source, url, reason):
        super().__init__(f"{source}: {reason} ({url})")
        self.source, self.url, self.reason = source, url, reason


class NotFound(FetchError):
    """The page does not exist (HTTP 404, or 403 from EDHREC's file host) (for example a commander with no page for a
    theme). Cached like a success, so a missing page is not requested again until its cache expires."""


def configure(refresh=None, offline=None):
    """Set the run-wide mode from the command line (--refresh re-downloads; --offline never connects)."""
    if refresh is not None:
        MODE["refresh"] = bool(refresh)
    if offline is not None:
        MODE["offline"] = bool(offline)


def iso(ts):
    """Epoch seconds → '2026-10-11T12:00:00Z' (the format every `fetched` field uses)."""
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_json(path, obj):
    """Write JSON atomically; the pid-suffixed temp file keeps two concurrent runs from interleaving."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def read_json(path):
    """The parsed file, or None when it is missing or unreadable (a cache miss, never an error)."""
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def cache_file(source, key):
    """data/cache/commander/<source>/<key>.json, with the key made filesystem-safe."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", key).strip("_")[:120] or "index"
    return os.path.join(CACHE, source, safe + ".json")


def _pace(host):
    wait = _last.get(host, 0.0) + PACE.get(host, DEFAULT_PACE) - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.monotonic()


def _retry_after(err):
    try:
        return min(float(err.headers.get("Retry-After")), 60.0)
    except (AttributeError, TypeError, ValueError):
        return None


def request(url, *, data=None, headers=None, source="web", timeout=TIMEOUT):
    """GET, or POST when `data` is given (a dict or list is sent as JSON). Paced and retried.
    Returns the body as bytes, gunzipped when the server compressed it. Raises NotFound on 404 and
    FetchError once retries run out."""
    hdrs = {**UA, "Accept-Encoding": "gzip", **(headers or {})}
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
        hdrs.setdefault("Content-Type", "application/json")
    host = urllib.parse.urlsplit(url).hostname or ""
    for attempt in range(RETRIES + 1):
        _pace(host)
        try:
            req = urllib.request.Request(url, data=body, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return gzip.decompress(raw) if r.headers.get("Content-Encoding") == "gzip" else raw
        except urllib.error.HTTPError as e:  # before URLError: HTTPError is a subclass of it
            if e.code in MISSING_CODES.get(host, (404,)):
                raise NotFound(source, url, f"no such page (HTTP {e.code})")
            if e.code in RETRY_CODES and attempt < RETRIES:
                time.sleep(_retry_after(e) or 2 ** attempt)
                continue
            reason = "rate limited (429); try again later or run `warm` ahead of time" if e.code == 429 else f"HTTP {e.code}"
            raise FetchError(source, url, reason)
        except (urllib.error.URLError, OSError, EOFError) as e:  # OSError covers timeouts and resets
            if attempt < RETRIES:
                time.sleep(2 ** attempt)
                continue
            raise FetchError(source, url, f"network error: {getattr(e, 'reason', e)}")
    raise FetchError(source, url, "gave up")  # unreachable; keeps the function total


def _key(url, data):
    raw = url if data is None else url + "\n" + json.dumps(data, sort_keys=True)
    return hashlib.sha1(raw.encode()).hexdigest()[:20]


def _info(url, fetched, state):
    return {"url": url, "fetched": iso(fetched), "cache": state,
            "age_days": round((time.time() - fetched) / DAY, 1)}


def _serve(hit, state, source):
    if hit.get("status") == 404:
        raise NotFound(source, hit.get("url", ""), "no such page (cached)")
    return hit["payload"], _info(hit.get("url", ""), hit["fetched"], state)


def fetch_json(url, *, source, key=None, ttl=None, data=None, headers=None, refresh=None, offline=None,
               keep=None):
    """Cached JSON request. Returns (payload, info), where info is
    {"url", "fetched": UTC ISO time of the download, "cache": "fresh" | "network" | "stale", "age_days"}.
    "stale" means the network failed (or --offline) and an expired copy was served; callers turn it
    into a warning that names the source and its age. Raises NotFound for a 404 and FetchError when
    no usable copy exists. `key` names the cache file; by default it is a hash of url + body. `keep`, if
    given, trims a fresh download to the part worth caching (an Archidekt deck is ~400 KB, its card names a
    few KB); the trimmed payload is what both this call and later cache hits return."""
    refresh = MODE["refresh"] if refresh is None else refresh
    offline = MODE["offline"] if offline is None else offline
    ttl = TTL.get(source, 7 * DAY) if ttl is None else ttl
    path = cache_file(source, key or _key(url, data))
    hit = read_json(path)
    now = time.time()
    fresh = bool(hit) and now - hit.get("fetched", 0) < ttl
    if hit and (offline or (fresh and not refresh)):
        return _serve(hit, "fresh" if fresh else "stale", source)
    if offline:
        raise FetchError(source, url, "offline (--offline) and not cached; run `warm` while online")
    try:
        raw = request(url, data=data, headers=headers, source=source)
    except NotFound:
        atomic_json(path, {"fetched": now, "url": url, "status": 404})
        raise
    except FetchError:
        if hit:
            return _serve(hit, "stale", source)
        raise
    try:
        payload = json.loads(raw)
    except ValueError:
        if hit:
            return _serve(hit, "stale", source)
        raise FetchError(source, url, "the response was not JSON (the site may have changed its format)")
    if keep:
        payload = keep(payload)
    atomic_json(path, {"fetched": now, "url": url, "payload": payload})
    return payload, _info(url, now, "network")


def download(url, path, *, source, decode=True):
    """Stream a large file (Scryfall's bulk card data) to `path`, gunzipping on the fly, so a 150 MB
    file never sits in memory. Retried once. Returns `path`. With `decode=False` the bytes are saved as the
    server sent them: Commander Spellbook's daily file is a 29 MB gzip that the server labels
    `Content-Encoding: gzip`, so decoding it here would write 700 MB to disk for a reader that can unzip."""
    host = urllib.parse.urlsplit(url).hostname or ""
    tmp = f"{path}.{os.getpid()}.tmp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for attempt in range(2):
        _pace(host)
        try:
            req = urllib.request.Request(url, headers={**UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r, open(tmp, "wb") as out:
                gzipped = decode and r.headers.get("Content-Encoding") == "gzip"
                src = gzip.GzipFile(fileobj=r) if gzipped else r
                for chunk in iter(lambda: src.read(1 << 20), b""):
                    out.write(chunk)
            os.replace(tmp, path)
            return path
        except (urllib.error.URLError, OSError, EOFError) as e:
            if os.path.exists(tmp):
                os.remove(tmp)
            if attempt == 0:
                time.sleep(2)
                continue
            raise FetchError(source, url, f"download failed: {getattr(e, 'reason', e)}")
    return path
