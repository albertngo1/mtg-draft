#!/usr/bin/env python3
"""MTGA live draft coach — resolve a pack's Arena card IDs to a ranked 17Lands table.

The pipeline this automates (previously run by hand every pick):
  1. read the current pack's Arena card IDs from MTGA's Player.log
  2. map IDs -> card names/cost via the Scryfall Arena endpoint
  3. pull 17Lands GIH WR / IWD / ALSA for the set+format
  4. print a ranked table (highest GIH WR first)

By default the log is read LOCALLY — run this on the same machine where MTG Arena is
installed (Windows or macOS). The log path is auto-detected per OS; override with MTG_LOG.
Reading the log from another machine over SSH is an optional advanced mode (see below).

Requires MTGA "Detailed Logs (Plugin Support)" to be enabled: in Arena, go to
Settings -> Account -> check "Detailed Logs (Plugin Support)", then restart Arena. Without
it the DraftPack entries this reads never appear in Player.log.

CGB / external-grade cross-reference is NOT scripted (it's a fragile scrape) — the
coaching agent does that step with WebFetch. See AGENTS.md.

Output: a table ranked by GIH WR, PLUS a "what each card does" section (oracle text +
P/T) so picks are read for fit, not just stats. Use --brief to drop the text section.

Run `warm` once per set: it pre-caches the whole set's card text + mana value, so every
later `pull`/`rank` makes ZERO live queries (17Lands itself is cached 24h). The pack→stats
join is by mtga_id, which 17Lands provides — so Scryfall is only needed for cost/text.

Usage (Windows: use `python mtg-draft.py ...` or `mtg-draft.bat ...`):
  python mtg-draft.py warm --set FIN     # pre-cache the whole set (text+MV) — run once per set
  python mtg-draft.py pull               # read the latest DraftPack from the local log, rank it
  python mtg-draft.py pool               # audit your picks so far: creatures/spells/lands, curve, CABS
  python mtg-draft.py watch              # stream: auto-print the table each time a new pack appears
  python mtg-draft.py rank 102690 102462 # rank an explicit list of Arena card IDs
  python mtg-draft.py resolve 102690 ... # print name|cmc|color|type for IDs
  python mtg-draft.py capture            # show/Start the background log-capture; `capture stop` to end it
  python mtg-draft.py draft              # parse the captured stream -> drafts/current.json + summary

(On macOS/Linux you can also use the ./mtg-draft.sh wrapper.)

Side-car capture: any draft command (pull/pool/watch) auto-starts a detached background
process that mirrors the ENTIRE Player.log stream to logs/player_stream.log and keeps
following it (across Arena restarts) until you run `capture stop`. It's idempotent — only
one runs at a time. This gives a durable raw record of the whole draft so questions can be
answered from the saved stream instead of re-reading the noisy live log. The stream is
bounded by a front-truncating cap (default 50MB; --cap-mb / MTG_CAP_MB) that drops the
oldest bytes first, so a draft in progress is never trimmed.

Common flags:
  --set FIN           17Lands expansion code (default: $MTG_SET or the current set you pass)
  --fmt PremierDraft  PremierDraft | QuickDraft | TradDraft | Sealed (default: PremierDraft)
  --colors UR         mark these colors as on-color (OPTIONAL — auto-detected from your picks
                      for pull/pool/watch; pass this only to override the guess)
  --days 120          17Lands lookback window in days (default 120)
  --brief             skip the oracle-text section (table only)
  --poll N            watch poll interval in seconds (default 2)
  --refresh           force re-fetch of the cached 17Lands dataset

Advanced — read the log from ANOTHER machine over SSH (e.g. Arena on a different PC):
  --ssh user@host     SSH target whose Player.log to read (or set MTG_SSH)
  --ssh-key PATH      SSH private key for that target (or set MTG_SSH_KEY)
  --local             force local read (default; kept for back-compat)
  When --ssh / MTG_SSH is set, set MTG_LOG to the log path ON THAT remote machine.

Config (env or flags):
  MTG_SET, MTG_FMT, MTG_COLORS, MTG_DAYS
  MTG_LOG    override the Player.log path (auto-detected per OS by default)
  MTG_SSH, MTG_SSH_KEY    optional remote-read target + key (leave unset for local)
"""
import sys, os, json, re, time, datetime, signal, hashlib, subprocess, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
GRADES = os.path.join(HERE, "grades")  # committed external-grade files: <source>_<SET>.json
DRAFTS = os.path.join(HERE, "drafts")  # ETL output: parsed per-draft JSON (gitignored)
LOGDIR = os.path.join(HERE, "logs")  # side-car capture of the raw Player.log stream (gitignored)
STREAM = os.path.join(LOGDIR, "player_stream.log")  # everything Player.log emits, mirrored here
PIDFILE = os.path.join(LOGDIR, ".capture.pid")       # PID of the running background follower
CFGFILE = os.path.join(LOGDIR, ".capture.json")      # source/cap config the follower reads
# Default size cap for the captured stream. Front-truncating (keeps the most RECENT bytes),
# so a draft in progress is never the thing trimmed. Right-sized from real data (2026-06-08):
# a full draft spans only ~0.25MB of the unfiltered stream, so 50MB holds ~6h of play / 200+
# draft windows before trimming — plenty, since the ETL persists each draft to its own JSON
# and the raw stream is just a rolling buffer.
CAP_MB_DEFAULT = float(os.environ.get("MTG_CAP_MB", "50"))


def load_grades(source, set_code):
    """External reviewer grades (e.g. draftsim) keyed by lowercased card name.
    Returns {} if the file doesn't exist. Files live in grades/<source>_<SET>.json."""
    try:
        with open(os.path.join(GRADES, f"{source}_{set_code}.json")) as f:
            d = json.load(f)
        return {k.lower(): v for k, v in d.items() if not k.startswith("_")}
    except Exception:
        return {}
os.makedirs(CACHE, exist_ok=True)

def default_log_path():
    """Best-guess Player.log location for the current OS (override with MTG_LOG).
    MTGA writes the log next to the game's data dir; the path differs per platform."""
    if sys.platform == "win32":
        # %USERPROFILE%\AppData\LocalLow\Wizards Of The Coast\MTGA\Player.log
        return os.path.expandvars(
            r"%USERPROFILE%\AppData\LocalLow\Wizards Of The Coast\MTGA\Player.log")
    if sys.platform == "darwin":
        return "~/Library/Logs/Wizards Of The Coast/MTGA/Player.log"
    # Linux: MTGA runs under Steam Proton — best-effort default for the Steam app id.
    return ("~/.steam/steam/steamapps/compatdata/2141910/pfx/drive_c/users/steamuser/"
            "AppData/LocalLow/Wizards Of The Coast/MTGA/Player.log")


DEFAULTS = {
    "set": os.environ.get("MTG_SET", "FIN"),
    "fmt": os.environ.get("MTG_FMT", "PremierDraft"),
    "colors": os.environ.get("MTG_COLORS", ""),
    "days": int(os.environ.get("MTG_DAYS", "120")),
    "ssh": os.environ.get("MTG_SSH", ""),            # empty = read the log locally (default)
    "ssh_key": os.path.expanduser(os.environ["MTG_SSH_KEY"]) if os.environ.get("MTG_SSH_KEY") else "",
    "log": os.environ.get("MTG_LOG", default_log_path()),
}

UA = {"User-Agent": "mtg-draft-coach/1.0", "Accept": "application/json"}


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


# ---------- Scryfall (id -> card), cached on disk ----------
SCRY_CACHE = os.path.join(CACHE, "scryfall_arena.json")


def load_scry():
    try:
        with open(SCRY_CACHE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_scry(d):
    tmp = SCRY_CACHE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f)
    os.replace(tmp, SCRY_CACHE)


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
    return {
        "name": (d.get("name", "?").split("//")[0].strip()),
        "full_name": d.get("name", "?"),
        "cmc": int(d.get("cmc", 0)),
        "mana": mana,
        "pt": pt,
        "color": "".join(ci) if ci else "C",
        "rarity": d.get("rarity", "?")[:1].upper(),
        "type": d.get("type_line", "").split("//")[0].split("—")[0].strip(),
        "text": text.replace("\n", " "),
    }


def resolve_ids(ids):
    """Return {id: {name, cmc, color, type}} resolving misses via Scryfall (cached, 1-by-1)."""
    cache = load_scry()
    out, dirty = {}, False
    for cid in ids:
        cid = str(cid)
        if cid in cache:
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


# ---------- 17Lands dataset, cached on disk (refresh daily) ----------
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
    with open(path, "w") as f:
        json.dump(data, f)
    return data


# ---------- Player.log reader (local or over SSH) ----------
def _read_mode(cfg):
    """'ssh' only when a remote target is configured and local read isn't forced; else 'local'."""
    return "ssh" if (cfg.get("ssh") and not cfg.get("force_local")) else "local"


def _last_log_line(cfg, needle):
    """Return the last line of Player.log containing `needle`. Read locally by default
    (run on the same machine as Arena); read over SSH only when --ssh / MTG_SSH is set."""
    if _read_mode(cfg) == "local":
        path = os.path.expanduser(cfg["log"])
        try:
            f = open(path, "rb")
        except FileNotFoundError:
            raise SystemExit(
                f"Player.log not found at:\n  {path}\n"
                "Set MTG_LOG to your Player.log path, and make sure MTGA 'Detailed Logs "
                "(Plugin Support)' is enabled (Settings -> Account).")
        with f:                                   # scan the last ~3MB for speed
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 3_000_000))
            data = f.read().decode("utf-8", "replace")
        hits = [ln for ln in data.splitlines() if needle in ln]
        return hits[-1] if hits else ""
    if not cfg.get("ssh_key"):
        raise SystemExit("--ssh given but no SSH key — pass --ssh-key PATH or set MTG_SSH_KEY.")
    logpath = cfg["log"]
    if logpath.startswith("~"):
        logpath = "$HOME" + logpath[1:]
    remote = f'tail -8000 "{logpath}" | grep -E "{needle}" | tail -1'
    cmd = ["ssh", "-i", cfg["ssh_key"], "-o", "ConnectTimeout=8", "-o", "BatchMode=yes",
           cfg["ssh"], remote]
    return subprocess.check_output(cmd, text=True)


def _parse_array(line, key):
    m = re.search(rf'\\"{key}\\":\[([^\]]*)\]', line) or re.search(rf'"{key}":\[([^\]]*)\]', line)
    return re.findall(r"\d{5,6}", m.group(1)) if m else None


def pull_pack(cfg):
    """Return (ids, packnum, picknum, picked_ids) from the latest DraftPack in Player.log.
    The same log line carries PickedCards, so colors can be inferred without a second read."""
    line = _last_log_line(cfg, "DraftPack")
    ids = _parse_array(line, "DraftPack")
    if not ids:
        raise SystemExit("No DraftPack found in Player.log. Is a draft open?")
    pk = re.search(r'PackNumber\\?":(\d+)', line)
    pi = re.search(r'PickNumber\\?":(\d+)', line)
    picked = _parse_array(line, "PickedCards") or []
    return ids, (int(pk.group(1)) if pk else -1), (int(pi.group(1)) if pi else -1), picked


def infer_colors(picked_ids, cfg):
    """Guess the player's 2 colors from their picks, by counting colored pips in mana costs.
    Returns e.g. 'UR' (in WUBRG order), or '' if there's nothing to go on yet."""
    picked_ids = [str(i) for i in picked_ids]
    if not picked_ids:
        return ""
    scry = load_scry()
    missing = [c for c in picked_ids if c not in scry]
    if missing:
        resolve_ids(missing)
        scry = load_scry()
    from collections import Counter
    pips = Counter()
    for cid in picked_ids:
        mana = scry.get(cid, {}).get("mana", "")
        for sym in "WUBRG":
            pips[sym] += mana.count("{" + sym + "}")
    if not pips:
        return ""
    top = [c for c, n in pips.most_common() if n > 0][:2]
    return "".join(sorted(top, key="WUBRG".index))


def pull_picked(cfg):
    """Return the list of Arena IDs already picked, from the latest PickedCards in Player.log."""
    ids = _parse_array(_last_log_line(cfg, "PickedCards"), "PickedCards")
    if ids is None:
        raise SystemExit("No PickedCards found in Player.log. Has the draft started?")
    return ids


# ---------- side-car capture: mirror the WHOLE Player.log stream to logs/ in the background ----------
# A detached follower process tails Player.log and appends everything it emits to STREAM.
# It is started automatically on a draft command (pull/pool/watch) and survives this process
# exiting, so the raw stream is always being recorded without any extra step. No filtering —
# capture everything; parsing/ETL happens later off the saved stream, not off the live log.


def _capture_alive():
    """Return the running follower's PID if it's alive, else None."""
    try:
        with open(PIDFILE) as f:
            pid = int(f.read().strip())
    except Exception:
        return None
    try:
        os.kill(pid, 0)
        return pid
    except OSError:
        return None


def _spawn_detached(cmd, stdout=None):
    """Start `cmd` fully detached so it keeps running after this CLI exits (POSIX + Windows)."""
    kw = dict(stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
              stdout=(stdout if stdout is not None else subprocess.DEVNULL))
    if os.name == "nt":
        kw["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    return subprocess.Popen(cmd, **kw)


def _trim(path, cap):
    """Front-truncate `path` to ~80% of `cap` bytes when it exceeds `cap`, keeping the most
    recent bytes (drops a partial first line). No-op if cap is 0/falsey or file is under cap."""
    if not cap:
        return
    try:
        if os.path.getsize(path) <= cap:
            return
    except OSError:
        return
    keep = int(cap * 0.8)                       # hysteresis: trim to 80% so we don't trim each cycle
    with open(path, "rb") as f:
        f.seek(-keep, os.SEEK_END)
        f.readline()                            # align to the next full line
        data = f.read()
    with open(path, "wb") as f:
        f.write(data)


def _follow_local(c):
    """Poll a local Player.log and append new bytes to the stream (re-reads on rotation)."""
    logpath = os.path.expanduser(c["log"])
    pos, cur = 0, None
    while True:
        try:
            st = os.stat(logpath)
        except FileNotFoundError:
            time.sleep(1.0)
            continue
        ino = (st.st_dev, st.st_ino)
        if ino != cur or st.st_size < pos:      # first open OR rotated/truncated -> start over
            cur, pos = ino, 0
        if st.st_size > pos:
            with open(logpath, "rb") as f:
                f.seek(pos)
                data = f.read()
                pos = f.tell()
            with open(c["out"], "ab") as out:
                out.write(data)
            _trim(c["out"], c["cap"])
        time.sleep(0.5)


def _follow_remote(c):
    """Stream a remote Player.log via `ssh tail -F`, appending to the stream and reconnecting
    if the SSH session drops. The capped trim runs here too (Python is in the byte path)."""
    logpath = c["log"]
    if logpath.startswith("~"):
        logpath = "$HOME" + logpath[1:]
    cmd = ["ssh", "-i", c["ssh_key"], "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
           "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", c["ssh"], f'tail -n +1 -F "{logpath}"']
    while True:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            for chunk in iter(lambda: p.stdout.read(65536), b""):
                with open(c["out"], "ab") as out:
                    out.write(chunk)
                _trim(c["out"], c["cap"])
        except Exception:
            pass
        finally:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(3)                           # SSH dropped — wait, then reconnect


def tail_follow(cfgpath):
    """Internal worker (hidden `_tail` command). Reads its source/cap config from CFGFILE and
    follows the log forever, mirroring everything into the stream with a front-truncating cap.
    Pure Python so it works on Windows (local mode) too."""
    with open(cfgpath) as f:
        c = json.load(f)
    c["cap"] = int(float(c.get("cap_mb") or 0) * 1_000_000)
    if c.get("ssh"):
        _follow_remote(c)
    else:
        _follow_local(c)


def ensure_capture(cfg):
    """Idempotently start the background follower mirroring Player.log -> STREAM (capped).
    No-op if one is already running. Best-effort: never raise into the draft flow."""
    os.makedirs(LOGDIR, exist_ok=True)
    if _capture_alive():
        return False
    try:
        c = {"out": STREAM, "log": cfg["log"], "cap_mb": cfg.get("cap_mb", CAP_MB_DEFAULT)}
        if _read_mode(cfg) == "ssh":
            if not cfg.get("ssh_key"):
                return False
            c["ssh"] = cfg["ssh"]
            c["ssh_key"] = cfg["ssh_key"]
        else:
            c["log"] = os.path.expanduser(cfg["log"])
        with open(CFGFILE, "w") as f:
            json.dump(c, f)
        p = _spawn_detached([sys.executable, os.path.abspath(__file__), "_tail", CFGFILE])
        with open(PIDFILE, "w") as f:
            f.write(str(p.pid))
        return True
    except Exception:
        return False


def stop_capture():
    pid = _capture_alive()
    if not pid:
        print("  capture: not running."); return
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)   # take down the worker + its ssh child
    except OSError:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    try:
        os.remove(PIDFILE)
    except OSError:
        pass
    print(f"  capture: stopped (pid {pid}).")


def capture_status(cfg):
    pid = _capture_alive()
    sz = os.path.getsize(STREAM) if os.path.exists(STREAM) else 0
    src = f"{cfg['ssh']} (SSH)" if _read_mode(cfg) == "ssh" else os.path.expanduser(cfg["log"])
    print(f"\n  capture: {'running (pid '+str(pid)+')' if pid else 'not running'}")
    print(f"  source : {src}")
    print(f"  stream : {STREAM}  ({sz/1e6:.1f} MB / {cfg.get('cap_mb', CAP_MB_DEFAULT):.0f} MB cap)\n")


# ---------- ETL: parse the captured stream into structured drafts ----------
# Each draft pick is logged as a BotDraft payload carrying PackNumber/PickNumber, the DraftPack
# (cards offered, Arena IDs) and PickedCards (cumulative picks so far). We segment the stream
# into drafts on (pack0,pick0) resets, recover the card taken at each pick by diffing the next
# entry's PickedCards, and enrich with 17Lands ratings + names + grades. Output -> drafts/current.json
# so the coach answers history questions ("what did I pass at P1P5?") from one file, not the raw log.


def _botdraft_payloads(text):
    """Pull every BotDraft DraftPack payload out of the raw stream, in log order."""
    out = []
    for ln in text.splitlines():
        if "BotDraft" not in ln or "DraftPack" not in ln:
            continue
        p = None
        m = re.search(r'"Payload":"(.*)"\}\s*$', ln)
        if m:
            try:                                   # Payload is an embedded escaped-JSON string
                p = json.loads(json.loads('"' + m.group(1) + '"'))
            except Exception:
                p = None
        if not p:                                  # fallback: regex the fields from the escaped line
            pk = re.search(r'PackNumber\\":(\d+)', ln); pi = re.search(r'PickNumber\\":(\d+)', ln)
            dp = re.search(r'DraftPack\\":\[([^\]]*)\]', ln)
            pc = re.search(r'PickedCards\\":\[([^\]]*)\]', ln)
            ev = re.search(r'EventName\\":\\"([^\\"]*)', ln)
            if not (pk and pi and dp):
                continue
            p = {"PackNumber": int(pk.group(1)), "PickNumber": int(pi.group(1)),
                 "DraftPack": re.findall(r"\d{5,6}", dp.group(1)),
                 "PickedCards": re.findall(r"\d{5,6}", pc.group(1)) if pc else [],
                 "EventName": ev.group(1) if ev else ""}
        out.append(p)
    return out


def reconstruct_drafts(text):
    """Segment the stream into drafts and reconstruct each pick (offered + what was taken).
    Returns a list of {event, picks:[{pack,pick,offered:[ids],taken:id|None}], pool:[ids]}."""
    drafts, cur = [], None
    for p in _botdraft_payloads(text):
        reset = p["PackNumber"] == 0 and p["PickNumber"] == 0
        if cur is None or (reset and cur.get("_last") != (0, 0)):
            cur = {"event": p.get("EventName", ""), "entries": []}
            drafts.append(cur)
        cur["entries"].append(p)
        cur["_last"] = (p["PackNumber"], p["PickNumber"])
    from collections import Counter
    for d in drafts:
        # sort by (pack, pick, #picked) so each pick's post-state (incl. the empty-pack closing
        # entry that shares the last pick's key) sorts AFTER it; dedupe exact repeats.
        seen, seq = set(), []
        for e in sorted(d["entries"], key=lambda e: (e["PackNumber"], e["PickNumber"],
                                                      len(e["PickedCards"]))):
            key = (e["PackNumber"], e["PickNumber"], len(e["PickedCards"]), len(e["DraftPack"]))
            if key in seen:
                continue
            seen.add(key); seq.append(e)
        picks = []
        for i, e in enumerate(seq):
            if not e["DraftPack"]:                  # empty-pack closing state — not a pick offer
                continue
            taken, base = None, Counter(e["PickedCards"])
            for nxt in seq[i + 1:]:                 # taken = first later state with one more card
                diff = Counter(nxt["PickedCards"]) - base
                if diff:
                    taken = next(iter(diff)); break
            if taken is None and len(e["DraftPack"]) == 1:
                taken = e["DraftPack"][0]            # last card of a pack is forced (no post-state needed)
            picks.append({"pack": e["PackNumber"] + 1, "pick": e["PickNumber"] + 1,
                          "offered": e["DraftPack"], "taken": taken})
        d["picks"] = picks
        d["pool"] = seq[-1]["PickedCards"] if seq else []
        d.pop("entries", None); d.pop("_last", None)
    return drafts


def _card_enricher(cfg, ids):
    """Return (fn id -> {name,color,rarity,cmc,gih,iwd,alsa,n,ds}, ratings_fmt) using 17Lands+Scryfall.
    If the live format has no win-rate data yet (e.g. a Quick-Draft re-run early in its window),
    proxy with the set's original PremierDraft over a wide historical window."""
    data = seventeen(cfg["set"], cfg["fmt"], cfg["days"], cfg["refresh"])
    ratings_fmt = cfg["fmt"]
    if not any(c.get("ever_drawn_win_rate") for c in data):
        data = seventeen(cfg["set"], "PremierDraft", max(int(cfg["days"]), 1200), cfg["refresh"])
        ratings_fmt = "PremierDraft (historical proxy)"
    by_id = {str(c["mtga_id"]): c for c in data if c.get("mtga_id")}
    scry = load_scry()
    missing = [c for c in {str(i) for i in ids} if c not in scry]
    if missing:
        resolve_ids(missing); scry = load_scry()
    ds = load_grades("draftsim", cfg["set"])
    def card(cid):
        cid = str(cid); s = by_id.get(cid); meta = scry.get(cid, {})
        name = (s["name"] if s else meta.get("name", f"<{cid}?>")).split("//")[0].strip()
        return {"id": cid, "name": name,
                "color": (s.get("color") if s else meta.get("color")) or "C",
                "rarity": ((s.get("rarity") if s else meta.get("rarity")) or "?")[:1].upper(),
                "cmc": meta.get("cmc"), "type": meta.get("type", ""),
                "gih": s.get("ever_drawn_win_rate") if s else None,
                "iwd": s.get("drawn_improvement_win_rate") if s else None,
                "alsa": s.get("avg_seen") if s else None,
                "n": (s.get("ever_drawn_game_count") if s else 0) or 0,
                "ds": ds.get(name.lower())}
    return card, ratings_fmt


_REMOVAL_RX = re.compile(
    r"destroy target|exile target (creature|permanent|artifact|enchantment|nonland|tapped)|"
    r"deals \d+ damage to (any target|target|each|it)|fight|gets [-−]\d+/[-−]\d+|"
    r"[-−]\d+/[-−]\d+ until|tap target|can't block", re.I)


def _kind(type_line):
    t = type_line or ""
    if "Land" in t:
        return "land"
    if "Creature" in t or "Vehicle" in t:
        return "creature"
    if "Instant" in t or "Sorcery" in t:
        return "spell"
    return "other"


def analyze_pool(pool, picks, colors):
    """Deckbuilding metrics over the picked pool: composition, curve, two-drops, removal estimate,
    signals (on-color premiums available late = open lane), and target-vs-actual flags."""
    from collections import Counter
    scry = load_scry()
    counts = Counter(_kind(c.get("type")) for c in pool)
    nonland = [c for c in pool if _kind(c.get("type")) != "land"]
    curve = Counter(int(c["cmc"]) for c in nonland if isinstance(c["cmc"], int))
    removal = sum(1 for c in pool
                  if _REMOVAL_RX.search((scry.get(c["id"], {}).get("text", "") or "")))
    on = set((colors or "").upper())
    signals = []                                    # premium on-color cards still seen late (pick >= 6)
    for p in picks:
        if p["pick"] >= 6:
            for c in p["offered"]:
                col = c["color"]
                oncol = col == "C" or (on and all(x in on for x in col if x in "WUBRG"))
                if c.get("gih") and c["gih"] >= 0.55 and oncol:
                    signals.append({"pack": p["pack"], "pick": p["pick"],
                                    "name": c["name"], "gih": round(c["gih"], 3)})
    five_plus = sum(n for mv, n in curve.items() if mv >= 5)
    flags = []
    if counts.get("creature", 0) < 15:
        flags.append(f"few creatures ({counts.get('creature',0)}/15-18)")
    if curve.get(2, 0) < 5:
        flags.append(f"low on 2-drops ({curve.get(2,0)}/5-7)")
    if removal < 3:
        flags.append(f"thin removal (~{removal}/3-4)")
    if five_plus > 6:
        flags.append(f"top-heavy ({five_plus} at 5+ MV, cap ~5-6)")
    return {
        "colors": colors,
        "counts": {"creatures": counts.get("creature", 0), "spells": counts.get("spell", 0),
                   "other": counts.get("other", 0), "lands": counts.get("land", 0),
                   "nonland": len(nonland), "total": len(pool)},
        "curve": {str(mv): curve[mv] for mv in sorted(curve)},
        "two_drops": curve.get(2, 0), "five_plus": five_plus, "removal_est": removal,
        "targets": {"creatures": "15-18", "two_drops": "5-7", "removal": "3-4",
                    "lands": 17, "five_plus_cap": "~5-6"},
        "signals": signals[:12], "flags": flags,
    }


def _running_metrics(taken_cards, scry):
    """Compact cumulative deck state THROUGH the current pick, embedded per pick so a reader never
    has to reconstruct the pool. For the live (pending) pick this is your pool-so-far as you decide."""
    from collections import Counter
    counts = Counter(_kind(c.get("type")) for c in taken_cards)
    nonland = [c for c in taken_cards if _kind(c.get("type")) != "land"]
    curve = Counter(int(c["cmc"]) for c in nonland if isinstance(c["cmc"], int))
    removal = sum(1 for c in taken_cards
                  if _REMOVAL_RX.search(scry.get(c["id"], {}).get("text", "") or ""))
    pips = Counter(ch for c in taken_cards for ch in (c.get("color") or "") if ch in "WUBRG")
    colors = "".join(sorted((x for x, _ in pips.most_common(2)), key="WUBRG".index))
    return {"n": len(taken_cards), "colors": colors,
            "creatures": counts.get("creature", 0), "spells": counts.get("spell", 0),
            "other": counts.get("other", 0), "two_drops": curve.get(2, 0),
            "removal_est": removal, "curve": {str(mv): curve[mv] for mv in sorted(curve)}}


def enrich_draft(cfg, draft):
    """Resolve every id in a reconstructed draft to names+ratings; offered lists sorted by GIH WR.
    Each pick carries (a) a cumulative `running` deck-state and (b) `wheel` flags on offered cards
    that came back around (seen 8 picks earlier in the same pack). Adds a final `analysis` block."""
    pool_ids = [p["taken"] for p in draft["picks"] if p["taken"]]  # the deck = every card taken
    ids = {i for p in draft["picks"] for i in p["offered"]} | set(pool_ids)
    card, ratings_fmt = _card_enricher(cfg, ids)
    offered_ids = {(p["pack"], p["pick"]): set(p["offered"]) for p in draft["picks"]}
    scry = load_scry()
    picks, taken_sofar = [], []
    for p in draft["picks"]:
        prev = offered_ids.get((p["pack"], p["pick"] - 8), set())   # same pack, one lap earlier
        offered = [dict(card(i), taken=(i == p["taken"]), wheel=(i in prev)) for i in p["offered"]]
        offered.sort(key=lambda c: c["gih"] or 0, reverse=True)
        tk = card(p["taken"]) if p["taken"] else None
        if tk:
            taken_sofar = taken_sofar + [tk]
        picks.append({"pack": p["pack"], "pick": p["pick"], "taken": tk,
                      "running": _running_metrics(taken_sofar, scry), "offered": offered})
    pool = [card(i) for i in pool_ids]
    colors = cfg["colors"] if cfg.get("colors_explicit") else infer_colors(pool_ids, cfg)
    return {"set": cfg["set"], "fmt": cfg["fmt"], "event": draft.get("event", ""),
            "ratings_fmt": ratings_fmt, "n_picks": len(picks),
            "analysis": analyze_pool(pool, picks, colors), "picks": picks, "pool": pool}


def _write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def _draft_fingerprint(draft):
    """Stable id for a draft = hash of its P1P1 pack, so re-runs overwrite the same archive file
    (no per-pick duplicates) and a different draft gets a different file."""
    first = sorted(draft["picks"][0]["offered"]) if draft["picks"] else []
    return hashlib.sha1((",".join(first)).encode()).hexdigest()[:8]


def _draft_cfg(cfg, draft):
    """Per-draft copy of cfg with set/fmt auto-detected from this draft's EventName."""
    dcfg = dict(cfg)
    parts = draft.get("event", "").split("_")       # "QuickDraft_MKM_0260608" -> fmt, set
    if len(parts) >= 2 and parts[1] and not cfg.get("set_explicit"):
        dcfg["set"] = parts[1]
    if parts and parts[0] and not cfg.get("fmt_explicit"):
        dcfg["fmt"] = parts[0]
    return dcfg


def refresh_current(cfg):
    """Parse the capture stream and persist every draft in it. Each draft -> a stable archive at
    drafts/<set>_<fingerprint>.json (idempotent — re-runs overwrite the same file), and the MOST
    RECENT draft is also written to drafts/current.json. Older, already-archived drafts are skipped
    (they don't change), so this stays cheap to call every pick. Returns (latest_state, n_drafts,
    current_path) or None if there's nothing to parse."""
    try:
        with open(STREAM, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except FileNotFoundError:
        return None
    drafts = reconstruct_drafts(text)
    if not drafts:
        return None
    os.makedirs(DRAFTS, exist_ok=True)
    latest = None
    for idx, d in enumerate(drafts):
        is_latest = idx == len(drafts) - 1
        dcfg = _draft_cfg(cfg, d)
        archive = os.path.join(DRAFTS, f"{dcfg['set']}_{_draft_fingerprint(d)}.json")
        if not is_latest and os.path.exists(archive):
            continue                                # older draft already saved; won't change
        state = enrich_draft(dcfg, d)
        state["draft_id"] = _draft_fingerprint(d)
        _write_json(archive, state)
        if is_latest:
            cur_path = os.path.join(DRAFTS, "current.json")
            _write_json(cur_path, state)
            latest = (state, len(drafts), cur_path)
    return latest


def print_draft_summary(state, n_drafts, path):
    head = state["event"] or f"{state['set']} {state['fmt']}"
    extra = f"  ({n_drafts} drafts in stream — showing most recent)" if n_drafts > 1 else ""
    print(f"\n  DRAFT — {head} — {state['n_picks']} picks{extra}")
    print(f"  ratings: {state.get('ratings_fmt', state['fmt'])}   ·   full detail: "
          f"{os.path.relpath(path, HERE)}\n")
    for p in state["picks"]:
        tk = p["taken"]
        if not tk:
            print(f"  P{p['pack']}P{p['pick']:<2} (current pack — no pick yet)")
            continue
        g = f"{tk['gih']*100:.1f}%" if tk.get("gih") else "n/a"
        line = f"  P{p['pack']}P{p['pick']:<2} {tk['name']} ({tk['color']} {g})"
        best = p["offered"][0]                      # flag a clearly-better card left in the pack
        if best["id"] != tk["id"] and best.get("gih") and tk.get("gih") \
                and best["gih"] - tk["gih"] > 0.03:
            line += f"   ⚠ passed {best['name']} ({best['gih']*100:.1f}%)"
        print(line)
    a = state.get("analysis")
    if a:
        c = a["counts"]
        print(f"\n  DECK ({a['colors'] or '—'}):  {c['creatures']} creatures · {c['spells']} spells · "
              f"{c['other']} other · {c['lands']} land   |   ~{a['removal_est']} removal · "
              f"{a['two_drops']} two-drops · {a['five_plus']} at 5+ MV")
        print("  CURVE (nonland):  " + ("  ".join(f"{mv}:{n}" for mv, n in a["curve"].items()) or "—"))
        if a["signals"]:
            sig = ", ".join(f"{s['name']} {s['gih']*100:.0f}% (P{s['pack']}P{s['pick']})"
                            for s in a["signals"][:5])
            print(f"  OPEN SIGNALS (on-color premiums seen late):  {sig}")
        if a["flags"]:
            print("  ⚠ " + "  ·  ".join(a["flags"]))
    print()


def watch(cfg):
    """Poll Player.log and auto-print the ranked table each time a new pack appears.
    Standalone/blocking — run it in its own terminal (ideally on the laptop with --local).
    Ctrl-C to stop."""
    try:
        sys.stdout.reconfigure(line_buffering=True)   # stream live even when piped
    except Exception:
        pass
    where = f"{cfg['ssh']} over SSH" if _read_mode(cfg) == "ssh" else "local log"
    print(f"\n  Watching {where} for new packs — {cfg['set']} {cfg['fmt']}"
          + (f", colors {cfg['colors']}" if cfg["colors"] else "")
          + f". Poll {cfg['poll']}s. Ctrl-C to stop.\n")
    last = None
    while True:
        try:
            line = _last_log_line(cfg, "DraftPack")
        except Exception as e:
            print(f"  (log read failed: {e} — retrying)")
            time.sleep(cfg["poll"])
            continue
        ids = _parse_array(line, "DraftPack")
        if ids:
            pk = re.search(r'PackNumber\\?":(\d+)', line)
            pi = re.search(r'PickNumber\\?":(\d+)', line)
            key = (pk.group(1) if pk else "?", pi.group(1) if pi else "?", tuple(ids))
            if key != last:
                last = key
                if not cfg["colors_explicit"]:        # re-infer as the pool clarifies
                    cfg["colors"] = infer_colors(_parse_array(line, "PickedCards") or [], cfg)
                label = (f"P{int(pk.group(1))+1}P{int(pi.group(1))+1}" if pk and pi else "pack")
                auto = "" if cfg["colors_explicit"] else f"   (colors auto: {cfg['colors'] or '—'})"
                print("\n" + "=" * 74 + f"\n  >> {label}{auto}")
                print_table(ids, cfg, show_text=not cfg["brief"])
        time.sleep(cfg["poll"])


# ---------- pool audit (agent helper: deck/curve/color check mid-draft) ----------
def print_pool(ids, cfg):
    data = seventeen(cfg["set"], cfg["fmt"], cfg["days"], cfg["refresh"])
    by_id = {str(c["mtga_id"]): c for c in data if c.get("mtga_id")}
    scry = load_scry()
    missing = [c for c in (str(i) for i in ids) if c not in scry]
    if missing:
        resolve_ids(missing)
        scry = load_scry()
    on = set(cfg["colors"].upper())

    # aggregate duplicates by id -> (count, record)
    from collections import Counter
    counts = Counter(str(i) for i in ids)
    cats = {"Creatures": [], "Spells": [], "Other": [], "Lands": []}
    off = []
    curve = {}  # mv -> count, on-color nonland only
    ncre = nspell = 0
    for cid, n in counts.items():
        s = by_id.get(cid)
        meta = scry.get(cid, {})
        name = (s["name"] if s else meta.get("name", f"<{cid}?>")).split("//")[0].strip()
        color = ((s.get("color") if s else meta.get("color", "")) or "C")
        cmc = meta.get("cmc", "?")
        types = " ".join(s.get("types", [])) if s else meta.get("type", "")
        if "Land" in types:
            cat = "Lands"
        elif "Creature" in types or "Vehicle" in types:
            cat = "Creatures"
        elif "Instant" in types or "Sorcery" in types:
            cat = "Spells"
        else:
            cat = "Other"
        oncol = (color == "C") or (on and all(c in on for c in color if c in "WUBRG"))
        label = f"{name}{(' x'+str(n)) if n > 1 else ''} ({color}{cmc})"
        if on and not oncol and cat != "Lands":
            off.append((cmc, label))
        else:
            cats[cat].append((cmc, label))
            if cat != "Lands":
                curve[cmc] = curve.get(cmc, 0) + n
                if cat == "Creatures":
                    ncre += n
                else:
                    nspell += n

    print(f"\n  YOUR POOL — {len(ids)} picks" + (f"  (on-color = {cfg['colors']})" if on else "") + "\n")
    for cat in ("Creatures", "Spells", "Other", "Lands"):
        rows = sorted(cats[cat], key=lambda r: (r[0] if isinstance(r[0], int) else 99))
        if not rows:
            continue
        tot = sum(int(x[1].split(' x')[1].split(' ')[0]) if ' x' in x[1] else 1 for x in rows)
        print(f"  {cat} ({tot}):")
        print("     " + " · ".join(r[1] for r in rows) + "\n")
    if off:
        rows = sorted(off, key=lambda r: (r[0] if isinstance(r[0], int) else 99))
        print(f"  Off-color / uncastable ({len(rows)}):")
        print("     " + " · ".join(r[1] for r in rows) + "\n")

    mvs = [m for m in curve if isinstance(m, int)]
    if mvs:
        print("  Curve (on-color nonland):")
        for mv in range(0, max(mvs) + 1):
            c = curve.get(mv, 0)
            if c:
                print(f"     {mv}: {'▮'*c} {c}")
        n5plus = sum(c for m, c in curve.items() if isinstance(m, int) and m >= 5)
        print(f"\n  CABS check: {ncre} creatures (target 15-18) · {nspell} spells · "
              f"{n5plus} cards at 5+ (cap ~5-6)\n")


# ---------- table ----------
def grade_gih(w):
    if w is None:
        return ""
    w *= 100
    return ("\U0001f525bomb" if w >= 57 else "excellent" if w >= 54 else
            "solid" if w >= 52 else "filler" if w >= 50 else "avoid")


def print_table(ids, cfg, show_text=True):
    data = seventeen(cfg["set"], cfg["fmt"], cfg["days"], cfg["refresh"])
    by_id = {str(c["mtga_id"]): c for c in data if c.get("mtga_id")}  # identity + stats
    scry = load_scry()
    # cmc + oracle text come from Scryfall; resolve any that `warm` didn't pre-cache
    missing = [c for c in (str(i) for i in ids) if c not in scry]
    if missing:
        resolve_ids(missing)
        scry = load_scry()
    on = set(cfg["colors"].upper())
    ds = load_grades("draftsim", cfg["set"])   # external reviewer grades (x/5), if cached

    rows = []
    for cid in ids:
        scid = str(cid)
        s = by_id.get(scid)                  # 17Lands record (stats + name/color/rarity)
        meta = scry.get(scid, {})            # Scryfall record (cmc/mana/pt/text)
        if s:
            name = s["name"].split("//")[0].strip()
            color = s.get("color") or "C"
            rarity = (s.get("rarity") or "?")[:1].upper()
            gih = s.get("ever_drawn_win_rate")
            iwd = s.get("drawn_improvement_win_rate")
            alsa = s.get("avg_seen")
            n = s.get("ever_drawn_game_count") or 0
        else:                                # no 17Lands data (basics / brand-new) -> Scryfall only
            name = meta.get("name", f"<{cid}?>")
            color = meta.get("color", "?")
            rarity = meta.get("rarity", "?")
            gih = iwd = alsa = None
            n = 0
        col = color if color else "C"
        oncol = (col == "C") or (on and all(c in on for c in col if c in "WUBRG"))
        nm = name.lower()
        rows.append({"gih": gih or 0, "oncol": oncol, "name": name, "color": col,
                     "rarity": rarity, "cmc": meta.get("cmc", "?"), "mana": meta.get("mana", ""),
                     "pt": meta.get("pt", ""), "text": meta.get("text", ""),
                     "g": gih, "iwd": iwd, "alsa": alsa, "n": n,
                     "ds": ds.get(nm)})
    rows.sort(key=lambda r: r["gih"], reverse=True)

    dsh = f"{'DS':5}" if ds else ""          # only show a grade column if that source is cached
    print(f"\n  {cfg['set']} {cfg['fmt']}  ({len(ids)} cards"
          + (f", on-color = {cfg['colors']}" if on else "") + ")\n")
    print(f"   {'CARD':24}{'CLR':5}{'R':3}{'MV':3}{'GIHWR':8}{'IWD':7}{'ALSA':6}{'N':6}{dsh} tier")
    print("  " + "-" * (72 + len(dsh)))
    for r in rows:
        mark = "▸" if (on and r["oncol"]) else " "
        g = f"{r['g']*100:.1f}%" if r["g"] else "n/a"
        i = f"{r['iwd']*100:+.1f}" if r["iwd"] is not None else "n/a"
        a = f"{r['alsa']:.1f}" if r["alsa"] else "n/a"
        dim = "" if (not on or r["oncol"]) else "  (off)"
        dsc = f"{(str(r['ds']) if r['ds'] is not None else '-'):5}" if ds else ""
        print(f"  {mark}{r['name'][:23]:24}{r['color']:5}{r['rarity']:3}"
              f"{str(r['cmc']):<3}{g:8}{i:7}{a:6}{str(r['n']):6}{dsc} {grade_gih(r['g'])}{dim}")

    if show_text:
        print("\n  WHAT EACH CARD DOES (read fit, not just stats):")
        for r in rows:
            mark = "▸" if (on and r["oncol"]) else " "
            hdr = f"{r['name']} {r['mana']}".strip()
            if r["pt"]:
                hdr += f"  {r['pt']}"
            print(f"\n  {mark}{hdr}  [{r['color']} {r['rarity']} · {grade_gih(r['g'])}]")
            if r["text"]:
                for line in _wrap(r["text"], 92):
                    print(f"      {line}")
    print()


def _wrap(s, width):
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > width:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


# ---------- arg parse ----------
def main():
    args = sys.argv[1:]

    # Internal: the detached background follower (started by ensure_capture). Not user-facing.
    if args and args[0] == "_tail":
        tail_follow(args[1])
        return

    cfg = dict(DEFAULTS)
    cfg["refresh"] = False
    cmd, ids = None, []
    cfg["brief"] = False
    cfg["force_local"] = bool(os.environ.get("MTG_LOCAL"))  # --local / MTG_LOCAL forces local read
    cfg["poll"] = 2
    cfg["colors_explicit"] = bool(cfg["colors"])  # MTG_COLORS env counts as explicit
    cfg["capture_action"] = "start"               # for the `capture` command: start|status|stop
    cfg["cap_mb"] = CAP_MB_DEFAULT                # captured-stream size cap (front-truncating)
    cfg["set_explicit"] = False                  # --set given? (else ETL auto-detects from EventName)
    cfg["fmt_explicit"] = False                  # --fmt given? (else ETL auto-detects from EventName)
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("pull", "rank", "resolve", "warm", "pool", "watch", "capture", "draft"):
            cmd = a
        elif a in ("stop", "status", "start") and cmd == "capture":
            cfg["capture_action"] = a
        elif a == "--local":
            cfg["force_local"] = True
        elif a == "--ssh":
            i += 1; cfg["ssh"] = args[i]
        elif a == "--ssh-key":
            i += 1; cfg["ssh_key"] = os.path.expanduser(args[i])
        elif a == "--poll":
            i += 1; cfg["poll"] = float(args[i])
        elif a == "--set":
            i += 1; cfg["set"] = args[i]; cfg["set_explicit"] = True
        elif a == "--fmt":
            i += 1; cfg["fmt"] = args[i]; cfg["fmt_explicit"] = True
        elif a == "--colors":
            i += 1; cfg["colors"] = args[i]; cfg["colors_explicit"] = True
        elif a == "--days":
            i += 1; cfg["days"] = int(args[i])
        elif a == "--cap-mb":
            i += 1; cfg["cap_mb"] = float(args[i])
        elif a == "--refresh":
            cfg["refresh"] = True
        elif a == "--brief":
            cfg["brief"] = True
        elif a in ("-h", "--help"):
            print(__doc__); return
        elif re.fullmatch(r"\d{5,6}", a):
            ids.append(a)
        else:
            print(f"unknown arg: {a}\n"); print(__doc__); return
        i += 1

    if cmd is None and ids:
        cmd = "rank"

    # Any live-draft command spins up the side-car capture (idempotent) so the full
    # Player.log stream is always being mirrored to logs/ — no extra step needed.
    if cmd in ("pull", "pool", "watch", "draft"):
        if ensure_capture(cfg):
            print(f"  (capture started → {os.path.relpath(STREAM, HERE)})")

    if cmd == "draft":
        out = refresh_current(cfg)
        if not out:
            raise SystemExit(
                "No draft found in the capture stream yet (logs/player_stream.log).\n"
                "Start/continue a draft in Arena (with Detailed Logs on) — `pull`/`capture` "
                "keep the stream recording — then run `draft` again.")
        state, n_drafts, path = out
        print_draft_summary(state, n_drafts, path)
    elif cmd == "capture":
        if cfg["capture_action"] == "stop":
            stop_capture()
        else:
            if cfg["capture_action"] != "status" and ensure_capture(cfg):
                print("  capture: started.")
            capture_status(cfg)
    elif cmd == "warm":
        warm_set(cfg)
    elif cmd == "watch":
        try:
            watch(cfg)
        except KeyboardInterrupt:
            print("\n  stopped.")
    elif cmd == "pool":
        picked = pull_picked(cfg)
        if not cfg["colors_explicit"]:
            cfg["colors"] = infer_colors(picked, cfg)
        print_pool(picked, cfg)
    elif cmd == "pull":
        pack, pk, pi, picked = pull_pack(cfg)
        if not cfg["colors_explicit"]:
            cfg["colors"] = infer_colors(picked, cfg)
        label = (f"Pack {pk+1} Pick {pi+1}" if pk >= 0 else "current pack")
        auto = "" if cfg["colors_explicit"] else f", colors auto: {cfg['colors'] or '—'}"
        print(f"\n  >> {label}  ({len(picked)} cards already taken{auto})")
        print_table(pack, cfg, show_text=not cfg["brief"])
        try:
            refresh_current(cfg)                  # keep drafts/current.json fresh, best-effort
        except Exception:
            pass
    elif cmd == "rank":
        if not ids:
            raise SystemExit("rank: give Arena card IDs, e.g. rank 102690 102462")
        print_table(ids, cfg, show_text=not cfg["brief"])
    elif cmd == "resolve":
        for cid, rec in resolve_ids(ids).items():
            print(f"{cid}|{rec['name']}|{rec['cmc']}|{rec['color']}|{rec['type']}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
