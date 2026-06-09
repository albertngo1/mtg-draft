import sys, os, json, re, time, datetime, signal, hashlib, subprocess, urllib.request, urllib.error
from .config import HERE
from .sources import load_scry, resolve_ids, seventeen
from .grades import load_grades_any
from .logread import _last_log_line, _parse_array, _read_mode, infer_colors

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
        if a.get("themes"):
            th = "  ".join(f"{t}:{n}" for t, n in list(a["themes"].items())[:8])
            print(f"  THEMES:  {th}")
        if a.get("archetype_lean"):
            print(f"  ARCHETYPE LEAN:  {'  ·  '.join(a['archetype_lean'])}")
        if a.get("open_color_readable"):
            print(f"  OPEN COLORS (premiums still flowing to you, pick 5+):  {a['open_color_readable']}")
        last_run = next((p["running"] for p in reversed(state["picks"]) if p.get("running")), None)
        if last_run and last_run.get("premiums_passed_readable"):
            print(f"  PREMIUMS PASSED (good cards you let go, by color):  "
                  f"{last_run['premiums_passed_readable']}")
        if last_run and last_run.get("needs_readable"):
            print(f"  STILL NEEDS (prioritize next picks):  {last_run['needs_readable']}")
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
    ds, ds_label = load_grades_any(cfg["set"])   # external reviewer grades (Draftsim x/5 or CGB tier)

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

    dsh = f"{ds_label:5}" if ds else ""      # only show a grade column if that source is cached
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
