import os, re, time, subprocess
from .config import STREAM
from .sources import load_scry, resolve_ids, stale_ids

STREAM_FRESH_SECS = 8.0   # trust the local capture stream only if the daemon wrote it this recently
KNOWN_FMTS = ("PremierDraft", "QuickDraft", "TradDraft", "Sealed", "TradSealed")  # real 17Lands formats

def event_from_line(line):
    """Event name from a raw log line (escaped or plain JSON), or ''. Drafts carry `EventName`;
    the Sealed deck-build Course line carries `InternalEventName` ('MWM_SOS_Sealed_<date>')."""
    m = re.search(r'EventName\\":\\"([^\\"]*)', line or "") \
        or re.search(r'"(?:Internal)?EventName":"([^"]*)"', line or "")
    return m.group(1) if m else ""
def apply_event(cfg, event):
    """Adopt set/fmt auto-detected from an event name unless given explicitly. Draft events lead
    with the format ('QuickDraft_MKM_20260608'); Sealed events prefix it ('MWM_SOS_Sealed_<date>'),
    so we scan ALL underscore parts for a real 17Lands format rather than only the first. Junk-fmt
    special events (e.g. 'MWM_SOS_Cascade_BotDraft') match nothing here and keep the default; the
    ratings proxy fallback covers whatever format we keep. The set is the 2nd part by convention."""
    parts = (event or "").split("_")
    if len(parts) >= 2 and parts[1] and not cfg.get("set_explicit"):
        cfg["set"] = parts[1]
    if not cfg.get("fmt_explicit"):
        for p in parts:
            if p in KNOWN_FMTS:
                cfg["fmt"] = p
                break

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

# --- Premier / human-draft shapes (Quick Draft = BotDraft `DraftPack`; Premier = these) ---------
# Premier drafts log packs as `Draft.Notify` (plain JSON, `PackCards` is a CSV — NOT a `DraftPack`
# array) and picks as `MakePick` (escaped JSON `GrpIds`); neither carries a cumulative PickedCards
# array or an EventName, so the pool is rebuilt from MakePick and set/fmt come from a course line.
_PREM_NOTIFY_RX = re.compile(
    r'"draftId":"([0-9a-f-]+)","SelfPick":(\d+),"SelfPack":(\d+),"PackCards":"([0-9,]+)"')
_PREM_PICK_RX = re.compile(
    r'MakePick .*?\\"DraftId\\":\\"([0-9a-f-]+)\\",\\"GrpIds\\":\[(\d+)\],\\"Pack\\":(\d+),\\"Pick\\":(\d+)')
# Matches both the plain course line (`"InternalEventName":"PremierDraft_SOS_..."`) and the escaped
# EventJoin request (`\"EventName\":\"PremierDraft_SOS_...\"`); the `EventName` suffix covers both keys.
_PREM_EVENT_RX = re.compile(r'EventName\\?":\\?"([A-Za-z]+Draft[A-Za-z0-9_]*)')

def _local_blob(cfg, nbytes=3_000_000):
    """Recent text from the best LOCAL source, for the Premier path which needs MANY lines (every
    MakePick so far) — not the single allowlisted `tail|grep|tail -1` line the SSH reader returns.
    In SSH mode that's the capture daemon's local mirror of the remote log (STREAM); otherwise it's
    Arena's own Player.log. Reading a local file adds no new remote command shape, so the laptop's
    forced-command SSH wrapper is untouched."""
    path = STREAM if _read_mode(cfg) == "ssh" else os.path.expanduser(cfg["log"])
    try:
        with open(path, "rb") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - nbytes))
            return f.read().decode("utf-8", "replace")
    except OSError:
        return ""

def _premier_pack(text):
    """(ids, pack0, pick0, draftId) for the latest Premier pack offer in `text`, or None.
    SelfPack/SelfPick are 1-indexed in the log; returned 0-indexed to match the Quick path."""
    notes = _PREM_NOTIFY_RX.findall(text)
    if not notes:
        return None
    did, spick, spack, cards = notes[-1]
    return ([c for c in cards.split(",") if c], int(spack) - 1, int(spick) - 1, did)

def _premier_picked(text, draft_id=None):
    """Cumulative taken-card IDs (the pool) from MakePick GrpIds in pick order — the Premier analogue
    of Quick's PickedCards. Scoped to `draft_id` when given so a multi-draft stream doesn't mix pools.
    MakePick logs each pick twice (request + echo), so dedupe by (pack, pick) — one card per coord."""
    by_coord = {}
    for did, gid, pack, pk in _PREM_PICK_RX.findall(text):
        if draft_id is None or did == draft_id:
            by_coord[(int(pack), int(pk))] = gid
    return [by_coord[c] for c in sorted(by_coord)]

def _premier_event(text):
    """Last draft-style InternalEventName in `text` (e.g. 'PremierDraft_SOS_20260421'), or ''.
    Premier Draft.Notify lines carry no EventName, so set/fmt are read from the course line."""
    evs = _PREM_EVENT_RX.findall(text)
    return evs[-1] if evs else ""

def pull_pack(cfg):
    """Return (ids, packnum, picknum, picked_ids, event) for the current pack in Player.log.
    Quick Draft carries everything on one `DraftPack` line (PickedCards + EventName, so colors and
    set/fmt come free); Premier/human drafts have no DraftPack — the pack is the latest Draft.Notify,
    the pool is rebuilt from MakePick, and the event comes from the course line."""
    # SSH mode: prefer the daemon's fresh local stream (no round-trip); fall back to a live read.
    line = (_last_stream_line("DraftPack") if _read_mode(cfg) == "ssh" else None) \
        or _last_log_line(cfg, "DraftPack")
    ids = _parse_array(line, "DraftPack")
    if ids:
        pk = re.search(r'PackNumber\\?":(\d+)', line)
        pi = re.search(r'PickNumber\\?":(\d+)', line)
        picked = _parse_array(line, "PickedCards") or []
        return (ids, (int(pk.group(1)) if pk else -1), (int(pi.group(1)) if pi else -1), picked,
                event_from_line(line))
    # No DraftPack -> Premier / human draft (Draft.Notify packs, MakePick picks).
    text = _local_blob(cfg)
    pack = _premier_pack(text)
    if not pack:
        raise SystemExit("No DraftPack (Quick) or Draft.Notify pack (Premier) found in Player.log. "
                         "Is a draft open, and are Detailed Logs (Plugin Support) enabled?")
    pids, pk0, pi0, did = pack
    return (pids, pk0, pi0, _premier_picked(text, did), _premier_event(text))
def infer_colors(picked_ids, cfg):
    """Guess the player's 2 colors from their picks, by counting colored pips in mana costs.
    Returns e.g. 'UR' (in WUBRG order), or '' if there's nothing to go on yet."""
    picked_ids = [str(i) for i in picked_ids]
    if not picked_ids:
        return ""
    scry = load_scry()
    missing = stale_ids(scry, picked_ids)  # absent OR below current schema -> (re)fetch
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
    """Return (picked_ids, event) for the pool so far. Quick Draft has a cumulative PickedCards
    array; Premier has none, so the pool is rebuilt from MakePick (scoped to the current draftId)."""
    line = (_last_stream_line("PickedCards") if _read_mode(cfg) == "ssh" else None) \
        or _last_log_line(cfg, "PickedCards")
    ids = _parse_array(line, "PickedCards")
    if ids is not None:
        return ids, event_from_line(line)
    # No PickedCards array -> Premier / human draft: rebuild the pool from MakePick GrpIds.
    text = _local_blob(cfg)
    pack = _premier_pack(text)
    picked = _premier_picked(text, pack[3] if pack else None)
    if not picked:
        raise SystemExit("No PickedCards (Quick) or MakePick history (Premier) in Player.log. "
                         "Has the draft started?")
    return picked, _premier_event(text)
def _scan_file_sealed(path):
    """Stream `path` line by line and return (ids, event) for the LAST sealed deck-build pool: the
    singular deck-select Course payload (`{"Course":{...}`) carrying a top-level `"CardPool":[...]`.
    Filtering to `"Course":{` excludes the plural `{"Courses":[...]}` event-hub list (whose first
    CardPool belongs to whatever course is listed first, e.g. a ColorChallenge) and the bare
    `{"CourseId":...}` echo. Line-streamed (not slurped) so a multi-hundred-MB capture stream stays
    memory-light. Returns (None, '') if no such line exists."""
    best = (None, "")
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"Course":{' in line and '"CardPool":[' in line:
                    ids = _parse_array(line, "CardPool")
                    if ids:
                        best = (ids, event_from_line(line))   # keep the most recent match
    except OSError:
        return (None, "")
    return best

def pull_sealed(cfg):
    """Return (pool_ids, event) for a Sealed deck-build pool. Sealed has no DraftPack/Draft.Notify
    and no pick stream — the entire 6-pack pool (84 cards, with duplicates) is granted at once on the
    deck-builder's Course line as a top-level `"CardPool":[id,...]` array. That line is logged ONCE
    when the builder opens and then scrolls out of the live log tail as you play, so we read the
    capture daemon's full-history STREAM mirror first (it retains far more, and in SSH mode the daemon
    has already pulled the remote bytes locally), then the live log. Set/fmt come from the course's
    `InternalEventName` ('MWM_SOS_Sealed_<date>')."""
    paths = ([STREAM] if os.path.exists(STREAM) else []) \
        + ([os.path.expanduser(cfg["log"])] if _read_mode(cfg) == "local" else [])
    for path in paths:
        ids, event = _scan_file_sealed(path)
        if ids:
            return ids, event
    # SSH last resort: the allowlisted tail|grep|tail-1 — only finds the pool if it's still in the
    # live tail (i.e. the builder was just opened). The STREAM path above is the reliable one.
    if _read_mode(cfg) == "ssh":
        line = _last_log_line(cfg, "CardPool")
        if '"Course":{' in (line or ""):
            ids = _parse_array(line, "CardPool")
            if ids:
                return ids, event_from_line(line)
    raise SystemExit("No Sealed CardPool found in the log/capture. Open the sealed event's deck "
                     "builder in Arena (with Detailed Logs / Plugin Support enabled) so the pool is "
                     "written to the log; if reading over SSH, make sure the capture daemon is "
                     "running (it mirrors the pool even after it scrolls out of the live tail).")
