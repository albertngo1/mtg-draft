import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root (this file is src/mtgdraft/)
HERE = ROOT                            # kept for the relpath() display calls below
SHIM = os.path.join(ROOT, "src", "mtg-draft.py")  # entry the daemon re-spawns for the hidden `_tail` worker
REPLAY = os.path.join(ROOT, "src", "replay.py")   # coached-replay renderer (invoked to auto-write replay.md)
DATA = os.path.join(ROOT, "data")      # gitignored generated data: cache/ drafts/ logs/
CACHE = os.path.join(DATA, "cache")
GRADES = os.path.join(ROOT, "grades")  # committed external-grade files: <source>_<SET>.json
DRAFTS = os.path.join(DATA, "drafts")  # ETL output: parsed per-draft JSON (gitignored)
LOGDIR = os.path.join(DATA, "logs")  # side-car capture of the raw Player.log stream (gitignored)
STREAM = os.path.join(LOGDIR, "player_stream.log")  # everything Player.log emits, mirrored here
PIDFILE = os.path.join(LOGDIR, ".capture.pid")       # PID of the running background follower
CFGFILE = os.path.join(LOGDIR, ".capture.json")      # source/cap config the follower reads
CAP_MB_DEFAULT = float(os.environ.get("MTG_CAP_MB", "50"))
GUIDES = os.path.join(ROOT, "lords-of-limited")  # committed expert set guides: <SET>-draft-guide.md
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
SCRY_CACHE = os.path.join(CACHE, "scryfall_arena.json")
