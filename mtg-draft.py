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

(On macOS/Linux you can also use the ./mtg-draft.sh wrapper.)

Side-car capture: any draft command (pull/pool/watch) auto-starts a detached background
process that mirrors the ENTIRE Player.log stream to logs/player_stream.log and keeps
following it (across Arena restarts) until you run `capture stop`. It's idempotent — only
one runs at a time. This gives a durable raw record of the whole draft so questions can be
answered from the saved stream instead of re-reading the noisy live log.

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
import sys, os, json, re, time, datetime, signal, subprocess, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
GRADES = os.path.join(HERE, "grades")  # committed external-grade files: <source>_<SET>.json
LOGDIR = os.path.join(HERE, "logs")  # side-car capture of the raw Player.log stream (gitignored)
STREAM = os.path.join(LOGDIR, "player_stream.log")  # everything Player.log emits, mirrored here
PIDFILE = os.path.join(LOGDIR, ".capture.pid")       # PID of the running background tailer


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
    path = os.path.join(CACHE, f"17lands_{set_code}_{fmt}.json")
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


def tail_follow(logpath, outpath):
    """Internal worker (run via the hidden `_tail` command): follow Player.log forever and
    append every byte it writes to outpath. Pure Python so it works on Windows too, and it
    re-reads from the top when Arena rotates/recreates the log on relaunch."""
    logpath = os.path.expanduser(logpath)
    out = open(outpath, "ab")
    pos, cur = 0, None
    while True:
        try:
            st = os.stat(logpath)
        except FileNotFoundError:
            time.sleep(1.0)
            continue
        ino = (st.st_dev, st.st_ino)
        if ino != cur or st.st_size < pos:    # first open OR rotated/truncated -> start over
            cur, pos = ino, 0
        if st.st_size > pos:
            with open(logpath, "rb") as f:
                f.seek(pos)
                data = f.read()
                pos = f.tell()
            out.write(data)
            out.flush()
        time.sleep(0.5)


def ensure_capture(cfg):
    """Idempotently start the background follower mirroring Player.log -> STREAM.
    No-op if one is already running. Best-effort: never raise into the draft flow."""
    os.makedirs(LOGDIR, exist_ok=True)
    if _capture_alive():
        return False
    try:
        if _read_mode(cfg) == "local":
            cmd = [sys.executable, os.path.abspath(__file__), "_tail",
                   "--log", os.path.expanduser(cfg["log"]), "--out", STREAM]
            p = _spawn_detached(cmd)
        else:                                  # remote log: tail it over SSH into our STREAM
            if not cfg.get("ssh_key"):
                return False
            logpath = cfg["log"]
            if logpath.startswith("~"):
                logpath = "$HOME" + logpath[1:]
            cmd = ["ssh", "-i", cfg["ssh_key"], "-o", "ServerAliveInterval=15",
                   "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", cfg["ssh"],
                   f'tail -n +1 -F "{logpath}"']
            p = _spawn_detached(cmd, stdout=open(STREAM, "ab"))
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
    print(f"  stream : {STREAM}  ({sz/1e6:.1f} MB)\n")


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
        opt = {args[j]: args[j + 1] for j in range(1, len(args) - 1, 2)}
        tail_follow(opt.get("--log"), opt.get("--out"))
        return

    cfg = dict(DEFAULTS)
    cfg["refresh"] = False
    cmd, ids = None, []
    cfg["brief"] = False
    cfg["force_local"] = bool(os.environ.get("MTG_LOCAL"))  # --local / MTG_LOCAL forces local read
    cfg["poll"] = 2
    cfg["colors_explicit"] = bool(cfg["colors"])  # MTG_COLORS env counts as explicit
    cfg["capture_action"] = "start"               # for the `capture` command: start|status|stop
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("pull", "rank", "resolve", "warm", "pool", "watch", "capture"):
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
            i += 1; cfg["set"] = args[i]
        elif a == "--fmt":
            i += 1; cfg["fmt"] = args[i]
        elif a == "--colors":
            i += 1; cfg["colors"] = args[i]; cfg["colors_explicit"] = True
        elif a == "--days":
            i += 1; cfg["days"] = int(args[i])
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
    if cmd in ("pull", "pool", "watch"):
        if ensure_capture(cfg):
            print(f"  (capture started → {os.path.relpath(STREAM, HERE)})")

    if cmd == "capture":
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
