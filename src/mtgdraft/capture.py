import sys, os, json, time, datetime, signal, subprocess
from .config import CAP_MB_DEFAULT, CFGFILE, DEFAULTS, LOGDIR, PIDFILE, SCRY_CACHE, SHIM, STREAM
from .logread import _read_mode
from .etl import refresh_current

HEALTH_IDLE_SECS = 180   # command-path health check: no follower heartbeat this long => recycle (>3 idle ticks)
DBGLOG = os.path.join(LOGDIR, "capture-debug.log")  # always-on, capped follower diagnostics

def _dbg(msg):
    """Append a timestamped diagnostic line to capture-debug.log (front-capped ~2MB). Always on but
    event-driven (no per-poll spam), so a future wedge/lag can be diagnosed after the fact: byte
    arrival cadence (reveals MTGA's chunked/buffered flushing), truncation resets, ssh errors, idle
    gaps. Best-effort — never raises into the capture path."""
    try:
        os.makedirs(LOGDIR, exist_ok=True)
        with open(DBGLOG, "a") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}\n")
        if os.path.getsize(DBGLOG) > 2_000_000:
            with open(DBGLOG, "rb") as f:
                f.seek(-1_600_000, 2); f.readline(); keep = f.read()
            with open(DBGLOG, "wb") as f:
                f.write(keep)
    except Exception:
        pass

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
def _capture_healthy():
    """A live follower is only HEALTHY if its poll LOOP is still turning — not merely that the PID
    exists (a hung on_data/enrich network call could freeze the loop). We gate on the debug-log
    heartbeat, NOT the stream: the poller writes to capture-debug.log on every byte event AND an
    idle heartbeat every ~60s, so a healthy-but-idle follower (no new picks) still keeps it fresh,
    while a hung loop lets it go stale. This avoids the false-positive recycle churn the old
    stream-mtime check caused during normal between-pick idle. Returns the pid if healthy, else None."""
    pid = _capture_alive()
    if not pid:
        return None
    try:
        idle = time.time() - os.path.getmtime(DBGLOG)   # loop heartbeat (events + ~60s idle ticks)
    except OSError:
        return pid                                       # no debug log yet (just started) — trust PID
    return pid if idle <= HEALTH_IDLE_SECS else None
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
def _follow_local(c, on_data=None):
    """Poll a local Player.log and append new bytes to the stream (re-reads on rotation).
    `on_data(new_bytes)` fires after each append so the follower can auto-refresh current.json.
    Writes the same debug-log heartbeat as the remote follower — `_capture_healthy` gates on the
    debug log's mtime, so a follower that never touched it would read as wedged and get recycled
    (the local follower historically didn't, which made a stale debug log from an earlier SSH run
    recycle a healthy local one)."""
    logpath = os.path.expanduser(c["log"])
    pos, cur = 0, None
    _dbg(f"follow start (local): log={logpath}")
    last_beat = last_data = time.time()
    while True:
        try:
            st = os.stat(logpath)
        except FileNotFoundError:
            st = None
        if st:
            ino = (st.st_dev, st.st_ino)
            if ino != cur or st.st_size < pos:  # first open OR rotated/truncated -> start over
                if cur is not None:
                    _dbg(f"ROTATION/TRUNCATION: size {st.st_size} < offset {pos} — reset to 0")
                cur, pos = ino, 0
            if st.st_size > pos:
                with open(logpath, "rb") as f:
                    f.seek(pos)
                    data = f.read()
                    pos = f.tell()
                with open(c["out"], "ab") as out:
                    out.write(data)
                _trim(c["out"], c["cap"])
                if on_data:
                    on_data(data)
                _dbg(f"+{len(data)}B  size={st.st_size} offset={pos}  "
                     f"draftpacks_in_chunk={data.count(b'DraftPack')}")
                last_beat = last_data = time.time()
        if time.time() - last_beat >= 60:       # wall-clock heartbeat so idle ≠ wedged
            _dbg(f"idle: no new bytes for ~{int(time.time() - last_data)}s (offset={pos})")
            last_beat = time.time()
        time.sleep(0.5)
def _follow_remote(c, on_data=None, poll=1.0):
    """Mirror a remote Player.log by POLLING with byte-offset tracking. We do NOT use `ssh tail -F`:
    MTGA rewrites/truncates its own Player.log, which `tail -F` over SSH doesn't track reliably (it
    can sit alive but stop delivering new bytes — the silent-wedge bug). Instead, each tick we read
    the remote size (`wc -c`) and fetch only the bytes past our offset (`tail -c +N`); a size smaller
    than our offset means the log was truncated/rotated, so we reset to 0 and re-read. This mirrors
    what `_follow_local` does for the local case, and keeps capture self-sufficient (no dependence on
    the `pull`/AI path). `on_data(new_bytes)` fires after each append so it can refresh current.json."""
    logpath = c["log"]
    if logpath.startswith("~"):
        logpath = "$HOME" + logpath[1:]
    base = ["ssh", "-i", c["ssh_key"], "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
            "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", c["ssh"]]
    offset = 0
    idle = 0                                        # consecutive polls with no new bytes
    _dbg(f"follow start: ssh={c['ssh']} log={logpath} poll={poll}s")
    last_beat = last_data = time.time()
    while True:
        try:
            size = int((subprocess.check_output(
                base + [f'wc -c < "{logpath}"'], text=True, timeout=15).strip() or "0"))
        except Exception as e:
            _dbg(f"size probe FAILED: {type(e).__name__}: {e}")
            time.sleep(2); continue                 # host unreachable / transient — retry
        if size < offset:                           # truncated or rotated -> start over
            _dbg(f"TRUNCATION: remote size {size} < offset {offset} — reset to 0")
            offset = 0
        if size > offset:
            try:
                data = subprocess.check_output(      # bytes past our offset (tail -c is 1-indexed)
                    base + [f'tail -c +{offset + 1} "{logpath}"'], timeout=30)
            except Exception as e:
                _dbg(f"fetch FAILED at offset {offset}: {type(e).__name__}: {e}")
                time.sleep(2); continue
            if data:
                with open(c["out"], "ab") as out:
                    out.write(data)
                _trim(c["out"], c["cap"])
                if on_data:
                    on_data(data)
                offset += len(data)
                _dbg(f"+{len(data)}B  remote_size={size} offset={offset}  "
                     f"draftpacks_in_chunk={data.count(b'DraftPack')}  (after {idle} idle polls)")
                idle = 0
                last_beat = last_data = time.time()
        else:
            idle += 1
        if time.time() - last_beat >= 60:           # WALL-CLOCK heartbeat: a poll-count cadence
            _dbg(f"idle: no new bytes for ~{int(time.time() - last_data)}s "   # drifts with ssh
                 f"(remote_size={size} offset={offset})")                      # round-trip time
            last_beat = time.time()
        time.sleep(poll)
def tail_follow(cfgpath):
    """Internal worker (hidden `_tail` command). Reads its source/cap config from CFGFILE and
    follows the log forever, mirroring everything into the stream with a front-truncating cap.
    Pure Python so it works on Windows (local mode) too.

    It ALSO auto-refreshes drafts/current.json as picks stream in, so the structured draft store
    stays live with no manual `pull` — best-effort and fully isolated (an enrich error can never
    kill the byte capture, which is the durable record). Skipped if the Scryfall cache is cold
    (`warm` first) so the background process never makes surprise cold-start network calls."""
    with open(cfgpath) as f:
        c = json.load(f)
    c["cap"] = int(float(c.get("cap_mb") or 0) * 1_000_000)

    enrich_cfg = dict(DEFAULTS)                  # set/fmt auto-detect from each draft's EventName
    enrich_cfg.update({"set_explicit": False, "fmt_explicit": False,
                       "colors_explicit": False, "refresh": False})
    auto_enrich = c.get("enrich", True)
    # Re-enrich when a chunk carries a draft signal: Quick Draft emits `DraftPack`; Premier/human
    # drafts emit no DraftPack at all, so also fire on their pack (`Draft.Notify`) and pick
    # (`MakePick`) markers — otherwise current.json (the deck-state store) is never built live.
    DRAFT_MARKERS = (b"DraftPack", b"Draft.Notify", b"MakePick")
    def on_data(buf):
        if not auto_enrich or not os.path.exists(SCRY_CACHE):
            return
        if not any(m in buf for m in DRAFT_MARKERS):
            return
        try:
            refresh_current(enrich_cfg)
        except Exception:
            pass                                # capture must survive any enrich failure

    if c.get("ssh"):
        _follow_remote(c, on_data)
    else:
        _follow_local(c, on_data)
def ensure_capture(cfg):
    """Idempotently start the background follower mirroring Player.log -> STREAM (capped).
    No-op if one is already running. Best-effort: never raise into the draft flow."""
    os.makedirs(LOGDIR, exist_ok=True)
    if _capture_alive():
        if _capture_healthy():
            return False
        stop_capture()                          # alive but wedged/stale -> recycle it
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
        p = _spawn_detached([sys.executable, SHIM, "_tail", CFGFILE])
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
