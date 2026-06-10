import os, re, time, subprocess
from .config import STREAM
from .sources import load_scry, resolve_ids

STREAM_FRESH_SECS = 8.0   # trust the local capture stream only if the daemon wrote it this recently
KNOWN_FMTS = ("PremierDraft", "QuickDraft", "TradDraft", "Sealed", "TradSealed")  # real 17Lands formats

def event_from_line(line):
    """EventName from a raw DraftPack log line (escaped or plain JSON), or ''."""
    m = re.search(r'EventName\\":\\"([^\\"]*)', line or "") \
        or re.search(r'"EventName":"([^"]*)"', line or "")
    return m.group(1) if m else ""
def apply_event(cfg, event):
    """Adopt set/fmt auto-detected from a draft EventName ('QuickDraft_MKM_20260608' -> fmt, set)
    unless given explicitly. The fmt slot is adopted only when it's a real 17Lands format — special
    events (e.g. 'MWM_SOS_Cascade_BotDraft') put junk there, which would query a dataset that
    doesn't exist; the ratings proxy fallback covers whatever format we keep."""
    parts = (event or "").split("_")
    if len(parts) >= 2 and parts[1] and not cfg.get("set_explicit"):
        cfg["set"] = parts[1]
    if parts and parts[0] in KNOWN_FMTS and not cfg.get("fmt_explicit"):
        cfg["fmt"] = parts[0]

def _last_stream_line(needle, max_age=STREAM_FRESH_SECS):
    """Return the last line containing `needle` from the LOCAL capture stream — but only if the
    daemon wrote it within `max_age` seconds (so we never serve a stale pack from a wedged/idle
    follower). Returns None otherwise, so the caller falls back to a fresh live read. This lets
    SSH-mode `pull` avoid a per-pick reverse-SSH round-trip while the daemon is actively capturing
    (the stream is a local file the daemon already mirrors), with correctness preserved by the
    freshness gate + fallback."""
    try:
        if time.time() - os.path.getmtime(STREAM) > max_age:
            return None
        with open(STREAM, "rb") as f:                 # scan the last ~2MB for speed
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 2_000_000))
            data = f.read().decode("utf-8", "replace")
        hits = [ln for ln in data.splitlines() if needle in ln]
        return hits[-1] if hits else None
    except Exception:
        return None

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
    return re.findall(r"\d{5,7}", m.group(1)) if m else None
def pull_pack(cfg):
    """Return (ids, packnum, picknum, picked_ids, event) from the latest DraftPack in Player.log.
    The same log line carries PickedCards + EventName, so colors can be inferred and set/fmt
    auto-detected without a second read."""
    # SSH mode: prefer the daemon's fresh local stream (no round-trip); fall back to a live read.
    line = (_last_stream_line("DraftPack") if _read_mode(cfg) == "ssh" else None) \
        or _last_log_line(cfg, "DraftPack")
    ids = _parse_array(line, "DraftPack")
    if not ids:
        raise SystemExit("No DraftPack found in Player.log. Is a draft open?")
    pk = re.search(r'PackNumber\\?":(\d+)', line)
    pi = re.search(r'PickNumber\\?":(\d+)', line)
    picked = _parse_array(line, "PickedCards") or []
    return (ids, (int(pk.group(1)) if pk else -1), (int(pi.group(1)) if pi else -1), picked,
            event_from_line(line))
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
        for tok in re.findall(r"\{([^}]+)\}", mana):   # symbol-wise so hybrid {W/U} counts both
            for sym in "WUBRG":
                if sym in tok:
                    pips[sym] += 1
    if not pips:
        return ""
    top = [c for c, n in pips.most_common() if n > 0][:2]
    return "".join(sorted(top, key="WUBRG".index))
def pull_picked(cfg):
    """Return (picked_ids, event) from the latest PickedCards in Player.log."""
    line = (_last_stream_line("PickedCards") if _read_mode(cfg) == "ssh" else None) \
        or _last_log_line(cfg, "PickedCards")
    ids = _parse_array(line, "PickedCards")
    if ids is None:
        raise SystemExit("No PickedCards found in Player.log. Has the draft started?")
    return ids, event_from_line(line)
