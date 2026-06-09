import sys, os, json, re, time, datetime, signal, hashlib, subprocess, urllib.request, urllib.error
from .config import DRAFTS, REPLAY, STREAM
from .sources import load_scry, resolve_ids, seventeen
from .grades import load_grades_any, load_guide_notes
from .analysis import COLOR_NAMES, _REMOVAL_RX, _archetype_lean, _card_tags, _color_phrase, _deck_needs, _inflation, _kind
from .logread import infer_colors

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
        out.append((p, ln))                            # keep the raw line for per-draft raw.log slicing
    return out
def reconstruct_drafts(text):
    """Segment the stream into drafts and reconstruct each pick (offered + what was taken).
    Returns a list of {event, picks:[{pack,pick,offered:[ids],taken:id|None}], pool:[ids]}."""
    drafts, cur = [], None
    for p, ln in _botdraft_payloads(text):
        reset = p["PackNumber"] == 0 and p["PickNumber"] == 0
        if cur is None or (reset and cur.get("_last") != (0, 0)):
            cur = {"event": p.get("EventName", ""), "entries": [], "raw": []}
            drafts.append(cur)
        cur["entries"].append(p)
        cur["raw"].append(ln)                          # this draft's slice of the rolling stream
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
        d["raw"] = "\n".join(d.get("raw", []))         # join the draft's raw stream lines
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
    ds, _ = load_grades_any(cfg["set"])
    guide = load_guide_notes(cfg["set"])
    def card(cid):
        cid = str(cid); s = by_id.get(cid); meta = scry.get(cid, {})
        name = (s["name"] if s else meta.get("name", f"<{cid}?>")).split("//")[0].strip()
        tags = _card_tags(meta)
        c = {"id": cid, "name": name,
             "color": (s.get("color") if s else meta.get("color")) or "C",
             "rarity": ((s.get("rarity") if s else meta.get("rarity")) or "?")[:1].upper(),
             "cmc": meta.get("cmc"), "type": meta.get("type", ""),
             "gih": s.get("ever_drawn_win_rate") if s else None,
             "iwd": s.get("drawn_improvement_win_rate") if s else None,
             "alsa": s.get("avg_seen") if s else None,
             "n": (s.get("ever_drawn_game_count") if s else 0) or 0,
             "ds": ds.get(name.lower()),
             "tags": tags}
        inflation = _inflation(meta, tags)
        if inflation:                              # only present when the GIH is selection-bias-inflated
            c["inflation"] = inflation
        note = guide.get(name.lower())
        if note:                                   # expert per-card note from the LoL set guide, if any
            c["guide"] = note
        return c
    return card, ratings_fmt
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
    # theme tags across the pool -> emergent archetype lean
    themes = Counter(t for c in pool for t in c.get("tags", []))
    lean = _archetype_lean(themes, curve, counts)
    # open-color read: premium cards (GIH >= 55%) still FLOWING to you late (pick >= 5) by color —
    # a color the table isn't taking shows up late. (Pick 1-4 are too early to mean much.)
    flowing = Counter()
    for p in picks:
        if p["pick"] >= 5:
            for c in p["offered"]:
                if c.get("gih") and c["gih"] >= 0.55:
                    for ch in (c.get("color") or ""):
                        if ch in "WUBRG":
                            flowing[ch] += 1
    open_signal = [{"color": col, "color_name": COLOR_NAMES.get(col, col), "late_premiums_seen": n}
                   for col, n in flowing.most_common() if n >= 4]
    open_readable = ", ".join(f"{s['late_premiums_seen']} {s['color_name']}" for s in open_signal)
    return {
        "colors": colors,
        "counts": {"creatures": counts.get("creature", 0), "spells": counts.get("spell", 0),
                   "other": counts.get("other", 0), "lands": counts.get("land", 0),
                   "nonland": len(nonland), "total": len(pool)},
        "curve": {str(mv): curve[mv] for mv in sorted(curve)},
        "two_drops": curve.get(2, 0), "five_plus": five_plus, "removal_est": removal,
        "targets": {"creatures": "15-18", "two_drops": "5-7", "removal": "3-4",
                    "lands": 17, "five_plus_cap": "~5-6"},
        "themes": dict(themes.most_common()), "archetype_lean": lean,
        "open_color_signal": open_signal, "open_color_readable": open_readable,
        "signals": signals[:12], "flags": flags,
    }
def _running_metrics(taken_cards, passed_cards, scry):
    """Compact cumulative deck state THROUGH the current pick, embedded per pick so a reader never
    has to reconstruct the pool. For the live (pending) pick this is your pool-so-far as you decide.
    `passed_cards` are the cards you saw and DIDN'T take so far — aggregated by color (and premium
    quality) to read open colors / whether premium cards were flowing to you."""
    from collections import Counter
    counts = Counter(_kind(c.get("type")) for c in taken_cards)
    nonland = [c for c in taken_cards if _kind(c.get("type")) != "land"]
    curve = Counter(int(c["cmc"]) for c in nonland if isinstance(c["cmc"], int))
    removal = sum(1 for c in taken_cards
                  if _REMOVAL_RX.search(scry.get(c["id"], {}).get("text", "") or ""))
    pips = Counter(ch for c in taken_cards for ch in (c.get("color") or "") if ch in "WUBRG")
    colors = "".join(sorted((x for x, _ in pips.most_common(2)), key="WUBRG".index))
    passed_by_color = Counter(ch for c in passed_cards
                              for ch in (c.get("color") or "") if ch in "WUBRG")
    prem_by_color = Counter(ch for c in passed_cards if c.get("gih") and c["gih"] >= 0.55
                            for ch in (c.get("color") or "") if ch in "WUBRG")
    themes = Counter(t for c in taken_cards for t in c.get("tags", []))
    curve_d = {str(mv): curve[mv] for mv in sorted(curve)}
    needs = _deck_needs(len(taken_cards), counts.get("creature", 0), curve.get(2, 0), removal, curve_d)
    return {"n": len(taken_cards), "colors": colors,
            "creatures": counts.get("creature", 0), "spells": counts.get("spell", 0),
            "other": counts.get("other", 0), "two_drops": curve.get(2, 0),
            "removal_est": removal, "curve": curve_d,
            "needs": needs, "needs_readable": ", ".join(needs) if needs else "on track",
            "passed_by_color": dict(passed_by_color),
            "passed_readable": _color_phrase(passed_by_color),
            "premiums_passed_by_color": dict(prem_by_color),
            "premiums_passed_readable": _color_phrase(prem_by_color),
            "themes": dict(themes.most_common())}
def enrich_draft(cfg, draft):
    """Resolve every id in a reconstructed draft to names+ratings; offered lists sorted by GIH WR.
    Each pick carries (a) a cumulative `running` deck-state and (b) `wheel` flags on offered cards
    that came back around (seen 8 picks earlier in the same pack). Adds a final `analysis` block."""
    pool_ids = [p["taken"] for p in draft["picks"] if p["taken"]]  # the deck = every card taken
    ids = {i for p in draft["picks"] for i in p["offered"]} | set(pool_ids)
    card, ratings_fmt = _card_enricher(cfg, ids)
    offered_ids = {(p["pack"], p["pick"]): set(p["offered"]) for p in draft["picks"]}
    scry = load_scry()
    picks, taken_sofar, passed_sofar = [], [], []
    for p in draft["picks"]:
        prev = offered_ids.get((p["pack"], p["pick"] - 8), set())   # same pack, one lap earlier
        offered = [dict(card(i), taken=(i == p["taken"]), wheel=(i in prev)) for i in p["offered"]]
        offered.sort(key=lambda c: c["gih"] or 0, reverse=True)
        tk = card(p["taken"]) if p["taken"] else None
        if tk:
            taken_sofar = taken_sofar + [tk]
        passed_sofar = passed_sofar + [c for c in offered if not c["taken"]]
        picks.append({"pack": p["pack"], "pick": p["pick"], "taken": tk,
                      "running": _running_metrics(taken_sofar, passed_sofar, scry), "offered": offered})
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
def _is_complete(picks):
    """Has this draft finished? True once the final pack has been drafted to its last pick — i.e.
    we've reached pack 3+ and its last pick equals pack 1's size (the pack length). A draft still
    in progress (the current one) has fewer picks and stays open. Derived purely from the log, so
    it works whether or not the tool was driven live."""
    if not picks:
        return False
    by_pack = {}
    for p in picks:
        by_pack.setdefault(p["pack"], []).append(p["pick"])
    pack_size = max(by_pack.get(1, [0]))
    last_pack = max(by_pack)
    return last_pack >= 3 and pack_size > 0 and max(by_pack[last_pack]) >= pack_size

def _make_replay(draft_json, out_md):
    """Best-effort: render the coached replay for a completed draft into its folder. Subprocess so a
    replay failure can never disturb the ETL/capture path. Set MTG_REPLAY_AI=1 to also add the
    model-written per-pick takes (one claude -p call) — off by default so the background daemon
    stays token-free / offline."""
    cmd = [sys.executable, REPLAY, draft_json, out_md]
    if os.environ.get("MTG_REPLAY_AI"):
        cmd.append("--ai")
    try:
        subprocess.run(cmd, check=False, capture_output=True, timeout=300)
    except Exception:
        pass

def refresh_current(cfg):
    """Parse the capture stream and persist every draft in it as a self-contained BUNDLE folder:
    drafts/<set>_<fingerprint>/ holding draft.json (the enriched cumulative store), raw.log (just
    this draft's slice of the rolling stream), and — once the draft is complete — replay.md (the
    coached audit/playback). The most recent draft is also mirrored to drafts/current.json. Older,
    already-bundled drafts are skipped (they don't change), so this stays cheap to call every pick.
    Returns (latest_state, n_drafts, current_path) or None if there's nothing to parse."""
    try:
        with open(STREAM, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except FileNotFoundError:
        return None
    drafts = reconstruct_drafts(text)
    if not drafts:
        return None
    # Arena periodically TRUNCATES its own Player.log; the follower then re-dumps a SHORT copy of a
    # draft we've already captured in full. That surfaces as a second same-fingerprint segment with
    # fewer picks. Collapse segments by fingerprint, keeping the MOST COMPLETE (max picks) instance,
    # so a truncated re-dump can never regress a draft's history. Order by first appearance so the
    # "latest" draft stays the most recent one.
    best, order = {}, []
    for d in drafts:
        fp = _draft_fingerprint(d)
        if fp not in best:
            order.append(fp); best[fp] = d
        elif len(d.get("picks") or []) > len(best[fp].get("picks") or []):
            best[fp] = d
    drafts = [best[fp] for fp in order]
    os.makedirs(DRAFTS, exist_ok=True)
    latest = None
    for idx, d in enumerate(drafts):
        is_latest = idx == len(drafts) - 1
        dcfg = _draft_cfg(cfg, d)
        fp = _draft_fingerprint(d)
        folder = os.path.join(DRAFTS, f"{dcfg['set']}_{fp}")
        draft_json = os.path.join(folder, "draft.json")
        if not is_latest and os.path.exists(draft_json):
            continue                                # older draft already bundled; won't change
        os.makedirs(folder, exist_ok=True)
        raw = d.pop("raw", "")                       # keep raw out of the enriched JSON
        state = enrich_draft(dcfg, d)
        state["draft_id"] = fp
        _write_json(draft_json, state)
        try:
            with open(os.path.join(folder, "raw.log"), "w", encoding="utf-8") as f:
                f.write(raw + "\n")
        except Exception:
            pass
        if (not is_latest) or _is_complete(state["picks"]):
            _make_replay(draft_json, os.path.join(folder, "replay.md"))
        if is_latest:
            cur_path = os.path.join(DRAFTS, "current.json")
            _write_json(cur_path, state)
            latest = (state, len(drafts), cur_path)
    return latest
