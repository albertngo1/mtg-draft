#!/usr/bin/env python3
"""MTGA live draft coach — resolve a pack's Arena card IDs to a ranked 17Lands table.

The pipeline this automates (previously run by hand every pick):
  1. read the current pack's Arena card IDs from Player.log on the laptop (over SSH)
  2. map IDs -> card names/cost via the Scryfall Arena endpoint
  3. pull 17Lands GIH WR / IWD / ALSA for the set+format
  4. print a ranked table (highest GIH WR first)

CGB / external-grade cross-reference is NOT scripted (it's a fragile scrape) — the
coaching agent does that step with WebFetch. See AGENTS.md.

Usage:
  ./mtg-draft.sh pull                 # SSH the laptop, read the latest DraftPack, rank it
  ./mtg-draft.sh rank 102690 102462   # rank an explicit list of Arena card IDs
  ./mtg-draft.sh resolve 102690 ...   # just print name|cmc|color|type for IDs

Common flags:
  --set SOS           17Lands expansion code (default: $MTG_SET or SOS)
  --fmt QuickDraft    PremierDraft | QuickDraft | TradDraft | Sealed (default: QuickDraft)
  --colors UR         mark these colors as on-color (default: $MTG_COLORS, blank = none)
  --days 120          17Lands lookback window in days (default 120)
  --refresh           force re-fetch of the cached 17Lands dataset

Config (env or edit DEFAULTS below):
  MTG_SSH=albertngo@100.111.228.115   MTG_SSH_KEY=~/.ssh/wc3_reverse_play
  MTG_LOG="~/Library/Logs/Wizards Of The Coast/MTGA/Player.log"
"""
import sys, os, json, re, time, datetime, subprocess, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
os.makedirs(CACHE, exist_ok=True)

DEFAULTS = {
    "set": os.environ.get("MTG_SET", "SOS"),
    "fmt": os.environ.get("MTG_FMT", "QuickDraft"),
    "colors": os.environ.get("MTG_COLORS", ""),
    "days": int(os.environ.get("MTG_DAYS", "120")),
    "ssh": os.environ.get("MTG_SSH", "albertngo@100.111.228.115"),
    "ssh_key": os.path.expanduser(os.environ.get("MTG_SSH_KEY", "~/.ssh/wc3_reverse_play")),
    "log": os.environ.get("MTG_LOG", "~/Library/Logs/Wizards Of The Coast/MTGA/Player.log"),
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


def resolve_ids(ids):
    """Return {id: {name, cmc, color, type}} resolving misses via Scryfall (cached)."""
    cache = load_scry()
    out, dirty = {}, False
    for cid in ids:
        cid = str(cid)
        if cid in cache:
            out[cid] = cache[cid]
            continue
        try:
            d = json.loads(_get(f"https://api.scryfall.com/cards/arena/{cid}"))
            ci = d.get("color_identity", [])
            rec = {
                "name": (d.get("name", "?").split("//")[0].strip()),
                "full_name": d.get("name", "?"),
                "cmc": int(d.get("cmc", 0)),
                "color": "".join(ci) if ci else "C",
                "rarity": d.get("rarity", "?")[:1].upper(),
                "type": d.get("type_line", "").split("//")[0].split("—")[0].strip(),
            }
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


def index_17(data):
    """name (lowercased, front-face) -> record."""
    idx = {}
    for c in data:
        nm = c.get("name", "")
        idx[nm.lower()] = c
        idx[nm.split("//")[0].strip().lower()] = c
    return idx


def lookup_17(idx, name):
    key = name.lower()
    if key in idx:
        return idx[key]
    front = name.split("//")[0].strip().lower()
    if front in idx:
        return idx[front]
    for k, v in idx.items():  # prefix fallback for split/adventure cards
        if k.startswith(front) or front.startswith(k):
            return v
    return None


# ---------- Player.log reader (SSH) ----------
def pull_pack(cfg):
    """Return (ids, packnum, picknum, npicked) from the latest DraftPack in Player.log."""
    logpath = cfg["log"]
    if logpath.startswith("~"):
        logpath = "$HOME" + logpath[1:]
    remote = (f'tail -8000 "{logpath}" | grep -E "DraftPack" | tail -1')
    cmd = ["ssh", "-i", cfg["ssh_key"], "-o", "ConnectTimeout=8", "-o", "BatchMode=yes",
           cfg["ssh"], remote]
    line = subprocess.check_output(cmd, text=True)
    m = re.search(r'\\"DraftPack\\":\[([^\]]*)\]', line) or re.search(r'"DraftPack":\[([^\]]*)\]', line)
    if not m:
        raise SystemExit("No DraftPack found in Player.log tail. Is a draft open?")
    ids = re.findall(r"\d{5,6}", m.group(1))
    pk = re.search(r'PackNumber\\?":(\d+)', line)
    pi = re.search(r'PickNumber\\?":(\d+)', line)
    picked = re.search(r'\\"PickedCards\\":\[([^\]]*)\]', line) or re.search(r'"PickedCards":\[([^\]]*)\]', line)
    npick = len(re.findall(r"\d{5,6}", picked.group(1))) if picked else 0
    return ids, (int(pk.group(1)) if pk else -1), (int(pi.group(1)) if pi else -1), npick


# ---------- table ----------
def grade_gih(w):
    if w is None:
        return ""
    w *= 100
    return ("\U0001f525bomb" if w >= 57 else "excellent" if w >= 54 else
            "solid" if w >= 52 else "filler" if w >= 50 else "avoid")


def print_table(ids, cfg):
    cards = resolve_ids(ids)
    data = seventeen(cfg["set"], cfg["fmt"], cfg["days"], cfg["refresh"])
    idx = index_17(data)
    on = set(cfg["colors"].upper())
    rows = []
    for cid in ids:
        rec = cards[str(cid)]
        s = lookup_17(idx, rec["full_name"]) or lookup_17(idx, rec["name"])
        gih = s.get("ever_drawn_win_rate") if s else None
        iwd = s.get("drawn_improvement_win_rate") if s else None
        alsa = s.get("avg_seen") if s else None
        n = s.get("ever_drawn_game_count") if s else 0
        # on-color = every colored pip is in `on` (colorless always on)
        col = rec["color"]
        oncol = (col == "C") or (on and all(c in on for c in col if c in "WUBRG"))
        rows.append((gih or 0, oncol, rec, gih, iwd, alsa, n))
    rows.sort(key=lambda r: r[0], reverse=True)

    print(f"\n  {cfg['set']} {cfg['fmt']}  ({len(ids)} cards"
          + (f", on-color = {cfg['colors']}" if on else "") + ")\n")
    print(f"  {'':1}{'CARD':24}{'CLR':5}{'R':3}{'MV':3}{'GIHWR':8}{'IWD':7}{'ALSA':6}{'N':6} {'tier'}")
    print("  " + "-" * 72)
    for gih, oncol, rec, _, iwd, alsa, n in rows:
        mark = "▸" if (on and oncol) else " "
        g = f"{gih*100:.1f}%" if gih else "n/a"
        i = f"{iwd*100:+.1f}" if iwd is not None else "n/a"
        a = f"{alsa:.1f}" if alsa else "n/a"
        dim = "" if (not on or oncol) else "  (off)"
        print(f"  {mark}{rec['name'][:23]:24}{rec['color']:5}{rec['rarity']:3}"
              f"{rec['cmc']:<3}{g:8}{i:7}{a:6}{str(n):6} {grade_gih(gih)}{dim}")
    print()


# ---------- arg parse ----------
def main():
    args = sys.argv[1:]
    cfg = dict(DEFAULTS)
    cfg["refresh"] = False
    cmd, ids = None, []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("pull", "rank", "resolve"):
            cmd = a
        elif a == "--set":
            i += 1; cfg["set"] = args[i]
        elif a == "--fmt":
            i += 1; cfg["fmt"] = args[i]
        elif a == "--colors":
            i += 1; cfg["colors"] = args[i]
        elif a == "--days":
            i += 1; cfg["days"] = int(args[i])
        elif a == "--refresh":
            cfg["refresh"] = True
        elif a in ("-h", "--help"):
            print(__doc__); return
        elif re.fullmatch(r"\d{5,6}", a):
            ids.append(a)
        else:
            print(f"unknown arg: {a}\n"); print(__doc__); return
        i += 1

    if cmd is None and ids:
        cmd = "rank"
    if cmd == "pull":
        pack, pk, pi, npick = pull_pack(cfg)
        label = (f"Pack {pk+1} Pick {pi+1}" if pk >= 0 else "current pack")
        print(f"\n  >> {label}  ({npick} cards already taken)")
        print_table(pack, cfg)
    elif cmd == "rank":
        if not ids:
            raise SystemExit("rank: give Arena card IDs, e.g. rank 102690 102462")
        print_table(ids, cfg)
    elif cmd == "resolve":
        for cid, rec in resolve_ids(ids).items():
            print(f"{cid}|{rec['name']}|{rec['cmc']}|{rec['color']}|{rec['type']}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
