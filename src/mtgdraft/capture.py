import sys, os, json, re, time, datetime, signal, hashlib, subprocess, urllib.request, urllib.error
from .config import CAP_MB_DEFAULT, CFGFILE, DEFAULTS, LOGDIR, PIDFILE, SCRY_CACHE, SHIM, STREAM
from .logread import _read_mode
from .etl import refresh_current

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
def _follow_local(c, on_data=None):
    """Poll a local Player.log and append new bytes to the stream (re-reads on rotation).
    `on_data(new_bytes)` fires after each append so the follower can auto-refresh current.json."""
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
            if on_data:
                on_data(data)
        time.sleep(0.5)
def _follow_remote(c, on_data=None):
    """Stream a remote Player.log via `ssh tail -F`, appending to the stream and reconnecting
    if the SSH session drops. The capped trim runs here too (Python is in the byte path).
    `on_data(new_bytes)` fires after each append so the follower can auto-refresh current.json."""
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
                if on_data:
                    on_data(chunk)
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
    def on_data(buf):
        if not auto_enrich or b"DraftPack" not in buf or not os.path.exists(SCRY_CACHE):
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
