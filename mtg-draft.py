#!/usr/bin/env python3
"""MTGA live draft coach — resolve a pack's Arena card IDs to a ranked 17Lands table.

The pipeline this automates (previously run by hand every pick):
  1. read the current pack's Arena card IDs from Player.log on the laptop (over SSH)
  2. map IDs -> card names/cost via the Scryfall Arena endpoint
  3. pull 17Lands GIH WR / IWD / ALSA for the set+format
  4. print a ranked table (highest GIH WR first)

CGB / external-grade cross-reference is NOT scripted (it's a fragile scrape) — the
coaching agent does that step with WebFetch. See AGENTS.md.

Output: a table ranked by GIH WR, PLUS a "what each card does" section (oracle text +
P/T) so picks are read for fit, not just stats. Use --brief to drop the text section.

Run `warm` once per set: it pre-caches the whole set's card text + mana value, so every
later `pull`/`rank` makes ZERO live queries (17Lands itself is cached 24h). The pack→stats
join is by mtga_id, which 17Lands provides — so Scryfall is only needed for cost/text.

Usage:
  ./mtg-draft.sh warm                 # pre-cache the whole set (text+MV) — run once per set
  ./mtg-draft.sh pull                 # SSH the laptop, read the latest DraftPack, rank it
  ./mtg-draft.sh pool                 # audit your picks so far: creatures/spells/lands, curve, CABS
  ./mtg-draft.sh watch --colors UR    # stream: auto-print the table each time a new pack appears
                                      #   run in its own terminal; add --local if on the laptop
  ./mtg-draft.sh rank 102690 102462   # rank an explicit list of Arena card IDs
  ./mtg-draft.sh resolve 102690 ...   # print name|cmc|color|type for IDs

Common flags:
  --set SOS           17Lands expansion code (default: $MTG_SET or SOS)
  --fmt QuickDraft    PremierDraft | QuickDraft | TradDraft | Sealed (default: QuickDraft)
  --colors UR         mark these colors as on-color (default: $MTG_COLORS, blank = none)
  --days 120          17Lands lookback window in days (default 120)
  --brief             skip the oracle-text section (table only)
  --local             read Player.log directly (no SSH) — use when running on the laptop itself
  --poll N            watch poll interval in seconds (default 2)
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
def _last_log_line(cfg, needle):
    """Return the last line of Player.log containing `needle` — read locally if cfg['local']
    (run on the laptop, no SSH), else tailed over SSH from the laptop."""
    if cfg.get("local"):
        path = os.path.expanduser(cfg["log"])
        with open(path, "rb") as f:               # scan the last ~3MB for speed
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 3_000_000))
            data = f.read().decode("utf-8", "replace")
        hits = [ln for ln in data.splitlines() if needle in ln]
        return hits[-1] if hits else ""
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
    """Return (ids, packnum, picknum, npicked) from the latest DraftPack in Player.log."""
    line = _last_log_line(cfg, "DraftPack")
    ids = _parse_array(line, "DraftPack")
    if not ids:
        raise SystemExit("No DraftPack found in Player.log. Is a draft open?")
    pk = re.search(r'PackNumber\\?":(\d+)', line)
    pi = re.search(r'PickNumber\\?":(\d+)', line)
    picked = _parse_array(line, "PickedCards")
    return ids, (int(pk.group(1)) if pk else -1), (int(pi.group(1)) if pi else -1), len(picked or [])


def pull_picked(cfg):
    """Return the list of Arena IDs already picked, from the latest PickedCards in Player.log."""
    ids = _parse_array(_last_log_line(cfg, "PickedCards"), "PickedCards")
    if ids is None:
        raise SystemExit("No PickedCards found in Player.log. Has the draft started?")
    return ids


def watch(cfg):
    """Poll Player.log and auto-print the ranked table each time a new pack appears.
    Standalone/blocking — run it in its own terminal (ideally on the laptop with --local).
    Ctrl-C to stop."""
    try:
        sys.stdout.reconfigure(line_buffering=True)   # stream live even when piped
    except Exception:
        pass
    where = "local log" if cfg.get("local") else f"{cfg['ssh']} over SSH"
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
                label = (f"P{int(pk.group(1))+1}P{int(pi.group(1))+1}" if pk and pi else "pack")
                print("\n" + "=" * 74 + f"\n  >> {label}")
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
        rows.append({"gih": gih or 0, "oncol": oncol, "name": name, "color": col,
                     "rarity": rarity, "cmc": meta.get("cmc", "?"), "mana": meta.get("mana", ""),
                     "pt": meta.get("pt", ""), "text": meta.get("text", ""),
                     "g": gih, "iwd": iwd, "alsa": alsa, "n": n})
    rows.sort(key=lambda r: r["gih"], reverse=True)

    print(f"\n  {cfg['set']} {cfg['fmt']}  ({len(ids)} cards"
          + (f", on-color = {cfg['colors']}" if on else "") + ")\n")
    print(f"   {'CARD':24}{'CLR':5}{'R':3}{'MV':3}{'GIHWR':8}{'IWD':7}{'ALSA':6}{'N':6} tier")
    print("  " + "-" * 72)
    for r in rows:
        mark = "▸" if (on and r["oncol"]) else " "
        g = f"{r['g']*100:.1f}%" if r["g"] else "n/a"
        i = f"{r['iwd']*100:+.1f}" if r["iwd"] is not None else "n/a"
        a = f"{r['alsa']:.1f}" if r["alsa"] else "n/a"
        dim = "" if (not on or r["oncol"]) else "  (off)"
        print(f"  {mark}{r['name'][:23]:24}{r['color']:5}{r['rarity']:3}"
              f"{str(r['cmc']):<3}{g:8}{i:7}{a:6}{str(r['n']):6} {grade_gih(r['g'])}{dim}")

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
    cfg = dict(DEFAULTS)
    cfg["refresh"] = False
    cmd, ids = None, []
    cfg["brief"] = False
    cfg["local"] = bool(os.environ.get("MTG_LOCAL"))
    cfg["poll"] = 2
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("pull", "rank", "resolve", "warm", "pool", "watch"):
            cmd = a
        elif a == "--local":
            cfg["local"] = True
        elif a == "--poll":
            i += 1; cfg["poll"] = float(args[i])
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
    if cmd == "warm":
        warm_set(cfg)
    elif cmd == "watch":
        try:
            watch(cfg)
        except KeyboardInterrupt:
            print("\n  stopped.")
    elif cmd == "pool":
        print_pool(pull_picked(cfg), cfg)
    elif cmd == "pull":
        pack, pk, pi, npick = pull_pack(cfg)
        label = (f"Pack {pk+1} Pick {pi+1}" if pk >= 0 else "current pack")
        print(f"\n  >> {label}  ({npick} cards already taken)")
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
