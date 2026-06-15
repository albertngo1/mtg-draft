import sys, os, json, re, hashlib, subprocess
from .config import DRAFTS, REPLAY, ROOT, STREAM
from .sources import load_scry, ratings, resolve_ids, stale_ids
from .grades import load_grades_any, load_guide_notes
from .analysis import (COLOR_NAMES, PREMIUM_GIH, _REMOVAL_RX, _archetype_lean, _card_tags,
                       _color_phrase, _deck_needs, _inflation, _kind, _open_color_signal,
                       _premiums_seen_by_color, _tribes, _tribes_readable)
from .logread import apply_event, infer_colors

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
                 "DraftPack": re.findall(r"\d{5,7}", dp.group(1)),
                 "PickedCards": re.findall(r"\d{5,7}", pc.group(1)) if pc else [],
                 "EventName": ev.group(1) if ev else ""}
        out.append((p, ln))                            # keep the raw line for per-draft raw.log slicing
    return out
_PREM_NOTIFY_RX = re.compile(
    r'"draftId":"([0-9a-f-]+)","SelfPick":(\d+),"SelfPack":(\d+),"PackCards":"([0-9,]+)"')
_PREM_PICK_RX = re.compile(
    r'MakePick .*?\\"DraftId\\":\\"([0-9a-f-]+)\\",\\"GrpIds\\":\[(\d+)\],\\"Pack\\":(\d+),\\"Pick\\":(\d+)')
# Event-join/course line: draft-style EventName (plain or escaped) + the draftId as a bare UUID.
_PREM_EVENT_RX = re.compile(r'EventName\\?":\\?"([A-Za-z]+Draft[A-Za-z0-9_]*)')
_UUID_RX = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
def _premier_segments(text):
    """Premier / human drafts log packs as `Draft.Notify` with a `PackCards` CSV (NOT the BotDraft
    `DraftPack` array), and picks as `MakePick` with `GrpIds`, both keyed by `draftId`. `SelfPack`,
    `SelfPick` and MakePick `Pick` are all 1-INDEXED and equal (SelfPick:1 == P1P1). SOS packs hold
    14 cards, so a pick at SelfPick:N has 15-N cards and a complete draft is 3*14 = 42 picks (no
    missing P1P1). Reconstruct the SAME normalized {event, picks, pool, raw} shape
    `reconstruct_drafts` emits so the rest of the pipeline (enrich/analyze/replay) is format-agnostic."""
    # Draft.Notify carries no EventName, so set/fmt come from the event-join/course line — which
    # holds the draft-style InternalEventName AND the draftId (as a UUID) on the same line. Map
    # draftId -> event so each Premier draft auto-detects its set (else it falls back to default).
    did_event = {}
    for ln in text.splitlines():
        ev = _PREM_EVENT_RX.search(ln)
        if ev:
            for u in _UUID_RX.findall(ln):
                did_event.setdefault(u, ev.group(1))
    order, offers, takes, raws = [], {}, {}, {}
    for ln in text.splitlines():
        if "Draft.Notify" in ln and "PackCards" in ln:
            for did, spick, spack, cards in _PREM_NOTIFY_RX.findall(ln):
                if did not in raws:
                    raws[did] = []; order.append(did)
                offers.setdefault(did, {})[(int(spack), int(spick))] = re.findall(r"\d{5,7}", cards)
                raws[did].append(ln)
        elif "MakePick" in ln and "GrpIds" in ln:
            for did, gid, pack, pk in _PREM_PICK_RX.findall(ln):
                if did not in raws:
                    raws[did] = []; order.append(did)
                takes.setdefault(did, {})[(int(pack), int(pk))] = gid
                raws[did].append(ln)
    drafts = []
    for did in order:
        off = offers.get(did)
        if not off:                                    # MakePick-only id with no captured packs
            continue
        tk = takes.get(did, {})
        picks = [{"pack": spack, "pick": spick, "offered": off[(spack, spick)],
                  "taken": tk.get((spack, spick))}
                 for (spack, spick) in sorted(off)]
        drafts.append({"event": did_event.get(did, ""), "picks": picks,
                       "pool": [p["taken"] for p in picks if p["taken"]],
                       "raw": "\n".join(raws.get(did, []))})
    return drafts
def reconstruct_drafts(text):
    """Segment the stream into drafts and reconstruct each pick (offered + what was taken).
    Handles BOTH the BotDraft (Quick) `DraftPack` shape and the Premier/human `Draft.Notify`
    `PackCards` shape (appended via `_premier_segments`).
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
                    # a capture gap can make diff hold 2+ new cards — prefer (deterministically)
                    # one that was actually offered in THIS pack over an arbitrary dict ordering
                    cands = [c for c in e["DraftPack"] if c in diff]
                    taken = cands[0] if cands else next(iter(diff)); break
            if taken is None and len(e["DraftPack"]) == 1:
                taken = e["DraftPack"][0]            # last card of a pack is forced (no post-state needed)
            picks.append({"pack": e["PackNumber"] + 1, "pick": e["PickNumber"] + 1,
                          "offered": e["DraftPack"], "taken": taken})
        d["picks"] = picks
        d["pool"] = seq[-1]["PickedCards"] if seq else []
        d["raw"] = "\n".join(d.get("raw", []))         # join the draft's raw stream lines
        d.pop("entries", None); d.pop("_last", None)
    return drafts + _premier_segments(text)            # Quick (BotDraft) + Premier (Draft.Notify)
def _card_enricher(cfg, ids):
    """Return (fn id -> {name,color,rarity,cmc,gih,iwd,alsa,n,ds}, ratings_fmt) using 17Lands+Scryfall.
    If the live format has no win-rate data yet (e.g. a Quick-Draft re-run early in its window),
    proxy with the set's original PremierDraft over a wide historical window."""
    data, ratings_fmt = ratings(cfg["set"], cfg["fmt"], cfg["days"], cfg["refresh"])
    by_id = {str(c["mtga_id"]): c for c in data if c.get("mtga_id")}
    scry = load_scry()
    missing = stale_ids(scry, {str(i) for i in ids})  # absent OR below current schema -> (re)fetch
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
             "type_line": meta.get("type_line", ""),
             "types": meta.get("types", []), "subtypes": meta.get("subtypes", []),
             "keywords": meta.get("keywords", []), "loyalty": meta.get("loyalty"),
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
def export_cards(cfg):
    """Lean per-card data for the WHOLE set, emitted once so the coaching agent can load it at
    draft start and resolve each pick's IDs against in-context data — no per-pick oracle-text
    streaming and no second 'let me read the card' fetch. Static during a draft (17Lands/Scryfall/
    grades/guide don't change), so it caches cleanly. Fields: id,name,color,cmc,pt,type,grade,
    gih,alsa,iwd,n,text,(guide),(inflation)."""
    data, ratings_fmt = ratings(cfg["set"], cfg["fmt"], cfg["days"], cfg["refresh"])
    ids = [str(c["mtga_id"]) for c in data if c.get("mtga_id")]
    card, _ = _card_enricher(cfg, ids)
    scry = load_scry()
    out, seen = [], set()
    for cid in ids:
        c = card(cid)
        if c["name"] in seen:                      # one row per card (drop alt-art id duplicates)
            continue
        seen.add(c["name"])
        meta = scry.get(cid, {})
        rnd = lambda v, p: round(v, p) if isinstance(v, (int, float)) else v
        rec = {"id": c["id"], "name": c["name"], "color": c["color"], "cmc": c["cmc"],
               "pt": meta.get("pt"), "type": c.get("type_line") or c.get("type", ""),
               "grade": c.get("ds"), "gih": rnd(c["gih"], 4), "alsa": rnd(c["alsa"], 2),
               "iwd": rnd(c["iwd"], 3), "n": c["n"], "text": (meta.get("text") or "").strip()}
        if c.get("guide"):
            rec["guide"] = c["guide"]
        if c.get("inflation"):
            rec["inflation"] = c["inflation"]
        out.append(rec)
    out.sort(key=lambda r: r["name"])
    return out, ratings_fmt
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
                if c.get("gih") and c["gih"] >= PREMIUM_GIH and oncol:
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
    tribes = _tribes(pool)                          # creature-subtype counts (Detective tribal etc.)
    # open-color read: premium cards (GIH >= 55%) still SEEN late (pick >= 5) by color — taken +
    # passed, NOT just passed. A premium surviving to pick 5+ means the color is underdrafted upstream
    # whether or not you took it; reading off *passed* would be blind to your own drafted colors (you
    # keep the premiums you take, so they'd never count). (Pick 1-4 are too early to mean much.)
    open_signal, open_readable = _open_color_signal(picks)
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
        "tribes": tribes, "tribes_readable": _tribes_readable(tribes),
        "open_color_signal": open_signal, "open_color_readable": open_readable,
        "signals": signals[:12], "flags": flags,
    }
def _running_metrics(taken_cards, passed_cards, seen_cards, scry):
    """Compact cumulative deck state THROUGH the current pick, embedded per pick so a reader never
    has to reconstruct the pool. For the live (pending) pick this is your pool-so-far as you decide.
    `passed_cards` are the cards you saw and DIDN'T take so far — the "signaling to my left" view.
    `seen_cards` are ALL offered cards (taken + passed) — the unconfounded openness supply: read
    open colors off `premiums_seen_by_color`, NOT off what you passed (your own drafted color never
    accumulates a passed count, so passed-by-color reads your main color as dry — the confound)."""
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
    prem_by_color = Counter(ch for c in passed_cards if c.get("gih") and c["gih"] >= PREMIUM_GIH
                            for ch in (c.get("color") or "") if ch in "WUBRG")
    # premiums SEEN (taken + passed) by color — the unconfounded openness read (includes your own
    # drafted colors, which premiums_passed_by_color structurally misses).
    seen_prem_by_color = _premiums_seen_by_color(seen_cards)
    themes = Counter(t for c in taken_cards for t in c.get("tags", []))
    tribes = _tribes(taken_cards)                   # creature-subtype counts in the pool so far
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
            "premiums_seen_by_color": dict(seen_prem_by_color),
            "premiums_seen_readable": _color_phrase(seen_prem_by_color),
            "themes": dict(themes.most_common()),
            "tribes": tribes, "tribes_readable": _tribes_readable(tribes)}
def enrich_draft(cfg, draft):
    """Resolve every id in a reconstructed draft to names+ratings; offered lists sorted by GIH WR.
    Each pick carries (a) a cumulative `running` deck-state and (b) `wheel` flags on offered cards
    that came back around (seen 8 picks earlier in the same pack). Adds a final `analysis` block."""
    pool_ids = [p["taken"] for p in draft["picks"] if p["taken"]]  # the deck = every card taken
    ids = {i for p in draft["picks"] for i in p["offered"]} | set(pool_ids)
    card, ratings_fmt = _card_enricher(cfg, ids)
    offered_ids = {(p["pack"], p["pick"]): set(p["offered"]) for p in draft["picks"]}
    scry = load_scry()
    picks, taken_sofar, passed_sofar, seen_sofar = [], [], [], []
    for p in draft["picks"]:
        prev = offered_ids.get((p["pack"], p["pick"] - 8), set())   # same pack, one lap earlier
        offered = [dict(card(i), taken=(i == p["taken"]), wheel=(i in prev)) for i in p["offered"]]
        offered.sort(key=lambda c: c["gih"] or 0, reverse=True)
        tk = card(p["taken"]) if p["taken"] else None
        if tk:                                      # only a MADE pick passes cards — the pending
            taken_sofar = taken_sofar + [tk]        # pack's cards aren't "passed" while deciding.
            # NB: wheel laps re-add the same physical cards — intended, it overweights colors the
            # table keeps passing (which is exactly the open-lane signal being read).
            passed_sofar = passed_sofar + [c for c in offered if not c["taken"]]
            seen_sofar = seen_sofar + offered       # SEEN = taken + passed: the whole offered pack,
            # including the card you took — the unconfounded supply behind premiums_seen_by_color.
        picks.append({"pack": p["pack"], "pick": p["pick"], "taken": tk,
                      "running": _running_metrics(taken_sofar, passed_sofar, seen_sofar, scry),
                      "offered": offered})
    pool = [card(i) for i in pool_ids]
    colors = cfg["colors"] if cfg.get("colors_explicit") else infer_colors(pool_ids, cfg)
    return {"set": cfg["set"], "fmt": cfg["fmt"], "event": draft.get("event", ""),
            "ratings_fmt": ratings_fmt, "n_picks": len(picks),
            "analysis": analyze_pool(pool, picks, colors), "picks": picks, "pool": pool}
def _write_json(path, obj):
    # pid-suffixed tmp: the capture daemon's on_data and a CLI `pull`/`draft` can both refresh
    # the same files concurrently — a shared tmp name would interleave their writes.
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)
def _draft_fingerprint(draft):
    """Stable id for a draft = hash of its P1P1 pack, so re-runs overwrite the same archive file
    (no per-pick duplicates) and a different draft gets a different file."""
    first = sorted(draft["picks"][0]["offered"]) if draft["picks"] else []
    return hashlib.sha1((",".join(first)).encode()).hexdigest()[:8]
def _draft_date(draft, raw_log=None):
    """Deterministic YYYY-MM-DD for a draft, used in the bundle folder name. MUST return the SAME
    string every run for the same draft so re-running `draft`/`pull` overwrites the same folder
    (the dated name is the idempotency key — so it can't be wall-clock 'now').
    Primary: parse the 8-digit YYYYMMDD suffix out of the EventName, e.g.
      'QuickDraft_MKM_20260611' -> '2026-06-11', 'MWM_SOS_Cascade_BotDraft_20260609' -> '2026-06-09'.
    Fallback (no parseable 8-digit date — e.g. a malformed '0260608'): the raw.log mtime, stable
    enough for archives. `raw_log` defaults to raw.log inside the draft's own bundle folder."""
    event = draft.get("event", "") or ""
    m = re.search(r"(\d{8})(?:\D|$)", event)
    if m:
        y, mo, da = m.group(1)[:4], m.group(1)[4:6], m.group(1)[6:8]
        if "2000" <= y <= "2099" and "01" <= mo <= "12" and "01" <= da <= "31":
            return f"{y}-{mo}-{da}"
    import datetime
    if raw_log and os.path.exists(raw_log):
        return datetime.date.fromtimestamp(os.path.getmtime(raw_log)).isoformat()
    return datetime.date.today().isoformat()
def _bundle_parts(name):
    """Split a bundle folder name into (set, date, fingerprint). The fingerprint is the LAST
    '_'-segment, the set is the FIRST, and the date (if any) is the middle. Robust to both the new
    '<SET>_<YYYY-MM-DD>_<fp>' shape and the legacy '<SET>_<fp>' shape (date=None)."""
    parts = name.split("_")
    if len(parts) < 2:
        return (name, None, None)
    return (parts[0], "_".join(parts[1:-1]) or None, parts[-1])
def _find_bundle(set_code, fp):
    """Path of an existing bundle folder for this set+fingerprint (any date), or None. Lets a re-run
    reuse the prior bundle (and its raw.log mtime) instead of minting a new dated folder."""
    try:
        names = os.listdir(DRAFTS)
    except FileNotFoundError:
        return None
    for name in names:
        s, _date, f = _bundle_parts(name)
        if s == set_code and f == fp and os.path.isdir(os.path.join(DRAFTS, name)):
            return os.path.join(DRAFTS, name)
    return None
def _draft_cfg(cfg, draft):
    """Per-draft copy of cfg with set/fmt auto-detected from this draft's EventName."""
    dcfg = dict(cfg)
    apply_event(dcfg, draft.get("event", ""))       # "QuickDraft_MKM_20260608" -> fmt, set
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

def _replay_ai_enabled():
    """Add the model-written per-pick takes? MTG_REPLAY_AI overrides explicitly (1/0); otherwise
    default ON exactly when the auth token file is present — its presence IS the opt-in, and it
    survives daemon recycles (an env flag would be lost when a flag-less CLI respawns the daemon)."""
    v = os.environ.get("MTG_REPLAY_AI")
    if v is not None:
        return v.lower() not in ("", "0", "false", "no")
    return os.path.exists(os.path.join(ROOT, "claude-token.txt"))
def _make_replay(draft_json, out_md):
    """Best-effort: render the coached replay for a completed draft into its folder. Subprocess so a
    replay failure can never disturb the ETL/capture path. With AI takes enabled this is one
    claude -p call (~2 min) — callers gate on replay.md not existing, so it runs ONCE per draft."""
    cmd = [sys.executable, REPLAY, draft_json, out_md]
    if _replay_ai_enabled():
        cmd.append("--ai")
    try:
        subprocess.run(cmd, check=False, capture_output=True, timeout=300)
    except Exception:
        pass

def refresh_current(cfg):
    """Parse the capture stream and persist every draft in it as a self-contained BUNDLE folder:
    drafts/<set>_<YYYY-MM-DD>_<fingerprint>/ holding draft.json (the enriched cumulative store), raw.log (just
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
    # Precompute each draft's deterministic bundle metadata (set/fingerprint/date). The date is
    # parsed from the EventName (raw.log mtime fallback for malformed dates), so it — NOT list
    # position — is the right key for "which draft is most recent." reconstruct_drafts returns ALL
    # Quick (BotDraft) drafts before ALL Premier segments, so an old Premier re-dump always lands
    # last; choosing latest by position would then mirror that stale draft into current.json.
    # Pick the chronologically newest instead (tiebreak: later stream position wins on equal dates).
    meta = []
    for d in drafts:
        dcfg = _draft_cfg(cfg, d)
        fp = _draft_fingerprint(d)
        existing = _find_bundle(dcfg["set"], fp)
        # Date is deterministic: REUSE the existing bundle's own folder-embedded date once written
        # (it never changes), so a reprocess can't re-date the same draft into a second folder.
        # Only compute fresh on first creation — clean 8-digit EventName date, else today() (the
        # capture-day, since live drafts are bundled the day they happen; MKM's malformed 7-digit
        # date can't be parsed). raw.log mtime is a poor key (rewritten every refresh), so it's gone.
        if existing:
            date = _bundle_parts(os.path.basename(existing))[1] or _draft_date(d)
        else:
            date = _draft_date(d)
        meta.append((dcfg, fp, date))
    latest_idx = max(range(len(drafts)), key=lambda i: (meta[i][2], i)) if drafts else -1
    latest = None
    for idx, d in enumerate(drafts):
        is_latest = idx == latest_idx
        dcfg, fp, date = meta[idx]
        # Bundle name carries the draft's date (deterministic; see _draft_date) so it sorts/reads
        # chronologically while staying the idempotency key.
        folder = os.path.join(DRAFTS, f"{dcfg['set']}_{date}_{fp}")
        draft_json = os.path.join(folder, "draft.json")
        if not is_latest and os.path.exists(draft_json):
            # Skip re-bundling an already-written draft ONLY when it can't have grown. A bundle
            # first written early (e.g. 1 pick) and later treated as "not latest" would otherwise
            # stay frozen; re-enrich it when this pass reconstructed MORE picks.
            try:
                with open(draft_json) as jf:
                    stored_n = json.load(jf).get("n_picks", 0)
            except Exception:
                stored_n = 0
            if stored_n >= len(d.get("picks") or []):
                continue                            # already bundled at full length; won't change
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
        # Render the replay ONCE, when the draft is first seen complete. Never re-render an
        # existing replay.md: the latest complete draft stays "latest" until the next draft
        # starts, and every refresh in that window would otherwise clobber it (losing AI takes,
        # and with takes enabled, burning a ~2-min claude call per refresh). To re-render after
        # a code change, run src/replay.py on the bundle by hand.
        replay_md = os.path.join(folder, "replay.md")
        if ((not is_latest) or _is_complete(state["picks"])) and not os.path.exists(replay_md):
            _make_replay(draft_json, replay_md)
        if is_latest:
            cur_path = os.path.join(DRAFTS, "current.json")
            _write_json(cur_path, state)
            latest = (state, len(drafts), cur_path)
    return latest
