"""Card scores: what a card is worth to this commander at this bracket, and the evidence behind the number.

Why this shape: no public source records which cards win casual Commander games. At Brackets 1-4 the honest
signal is what experienced builders chose (EDHREC, Archidekt), so a card's base score is its inclusion rate at
the target bracket, pulled toward the all-bracket rate while the bracket has few decks. Three small
corrections sit on top, each labelled with where it comes from:

  - a precon discount, because many lists for a precon's commander stay close to the box and a stock card's
    inclusion partly measures inertia rather than choice (Brackets 2-3);
  - a tournament residual (EDHTop16 win rate with the card minus without it), shrunk by sample size, capped,
    weighted by bracket, and kept to roles whose value does not depend on the rest of the deck (mana, draw,
    interaction), because a combo piece's tournament win rate belongs to the deck it was in;
  - the fantasy: how much more this commander's builders play the card in decks tagged with the chosen themes,
    and a salt penalty for cards that are miserable to play against.

`gather` fetches and canonicalizes everything once into an evidence dict; `card_scores` is pure arithmetic on
that dict, so tests (and `validate`, which holds tournament decks out) can feed it hand-made evidence. The
weights are named constants because validation re-fits them; only Bracket 5 can be fitted to results, so the
Bracket 2-4 weights are judgment calls and say so.

Evidence kinds on every score: "builder" (what deck builders chose), "tournament" (Bracket 5 play rates),
"popularity" (Scryfall's overall EDHREC rank, the no-data fallback) and "none" (not on any list)."""
import datetime, math, re
from . import config, decklist, fantasy, net, roles
from .providers import archidekt, edhrec, edhtop16

K_BASE = 200          # pseudo-decks of the all-bracket rate mixed into a bracket's inclusion rate
K_TOURN = 25          # pseudo-entries of EDHREC's cEDH-page rate mixed into the tournament play rate at Bracket 5:
                      # small, so ~150 real entries lead (validate: K_BASE here let EDHREC outweigh them)
K_THEME = 50          # same, for a theme page measured against the rate it is compared with
K_RESID = 50          # entries of shrinkage on the tournament residual
RESID_SCALE = 4.0     # win-rate gaps (+-5 points) are small next to inclusion gaps, so the gap is scaled up
RESID_CAP = 0.2
W_BRACKET = {1: 0.0, 2: 0.0, 3: 0.2, 4: 0.5, 5: 1.0}   # weight of the tournament term; only 5 is fitted
SALT_GAMMA = 0.15     # largest salt penalty, for a salt-4 card
SALT_FLOOR = 1.0      # salt below which a card costs nothing (used only when the salt list has no floor)
SALT_MAX = 4.0        # EDHREC's salt runs 0-4
THIN = 50             # a bracket with fewer decks than this borrows from its neighbours
TOURN_MIN = 30        # entries needed before tournament play rates replace the builder rate at Bracket 5
POP_WEIGHT = 0.3      # the most popular card scores this much when only Scryfall's rank is known
POP_MAX_RANK = 4000
POP_POOL = 700        # candidate pool size in popularity mode
PRECON_PERCENTILE = 0.10
PRECON_S_MAX = 0.6
THEME_SCALE = 2.5     # a theme pull is a few points of inclusion; scaled up it can matter next to the base
THEME_CAP = 0.5       # and the theme part never moves a score by more than this. Both are judgment until
                      # validation fits them (like the Bracket 2-4 tournament weights)
PLAYSTYLE_THEME_WEIGHT = 0.5   # a playstyle's themes count half as much as a theme you named
GLOBAL_SYNERGY_FACTOR = 0.5    # a theme page for all commanders is weaker evidence than this commander's own
MATCHER_PULL = 0.1             # a card whose text fits the theme, when no page says anything
ARCHIDEKT_LIMIT = 30           # decks pulled when Archidekt widens or replaces EDHREC
SHOW_PULL = 0.02               # smallest positive theme pull worth printing in the evidence text
SHOW_DRAG = -0.05              # a theme pull must fall this low to be worth printing as a drag
SHOW_RESID = 0.005             # smallest tournament adjustment worth printing
SHOW_RESID_ENTRIES = 20        # and the fewest entries a printed win-rate gap may rest on

SOURCE_NAMES = {"edhrec": "EDHREC", "archidekt": "Archidekt", "edhtop16": "EDHTop16", "scryfall": "Scryfall",
                "mtgjson": "MTGJSON", "spellbook": "Commander Spellbook"}
_MATCHERS = {}  # playstyles.json "theme_matchers", compiled on first use


# ----------------------------------------------------------------------------- small helpers
def short_name(commanders):
    """How players say the commander in a sentence: 'Hazel' for Hazel of the Rootbloom, 'Chatterfang' for
    Chatterfang, Squirrel General. A pair joins with ' & '."""
    names = [commanders] if isinstance(commanders, str) else list(commanders)
    shown = [n.split(" // ")[0].split(",")[0].split(" of the ")[0].strip() or n for n in names]
    return " & ".join(shown)


def _pct(p):
    return "<1%" if 0 < p < 0.005 else f"{p:.0%}"


def _first(found):
    return found[0] if found else None


def _guard(warnings, label, fn, *args, **kw):
    """Call a provider; a missing page gives None quietly, a failed fetch gives None and a warning that names
    the source (the run goes on with the sources that did answer)."""
    try:
        return fn(*args, **kw)
    except net.NotFound:
        return None
    except net.FetchError as e:
        line = f"{SOURCE_NAMES.get(e.source, e.source)} unavailable for {label}: {e.reason}"
        if line not in warnings:
            warnings.append(line)
        return None


def _union_ci(commanders, db):
    held = set()
    for c in commanders:
        rec = db.get(c)
        held |= set(rec["ci"]) if rec else set()
    return "".join(x for x in "WUBRG" if x in held)


def _blank_card():
    return {"all": None, "at": None, "themes": {}, "theme_global": {}, "tourn": None, "pop": None}


def _canon_cards(db, cards, skip):
    """{canonical name: stats} from a provider's {name as the source spells it: stats}. Names the card index
    does not know, basic lands and `skip` (the commanders) are left out; two spellings of one card keep the
    larger sample."""
    out = {}
    for raw, st in cards.items():
        rec = db.get(raw)
        if rec is None or "Basic" in rec["types"] or rec["name"] in skip:
            continue
        old = out.get(rec["name"])
        if old is None or _sample(st) > _sample(old):
            out[rec["name"]] = st
    return out


def _sample(st):
    return st.get("decks", st.get("entries", 0))


def _pool(parts):
    """One builder page from several: [(page decks, {name: stats})] -> ({name: stats}, total decks). A card is
    summed over the pages that list it; a page that lacks it counts as that many decks without it, because a
    card under a page's listing line (about 5%) was played in fewer than that, not unknown."""
    out = {}
    for name in set().union(*(c for _, c in parts)):
        decks = of = 0
        syn = syn_w = 0.0
        for n, cards in parts:
            st = cards.get(name)
            if st:
                decks, of = decks + st["decks"], of + st["of"]
                if st.get("synergy") is not None:
                    syn, syn_w = syn + st["synergy"] * st["of"], syn_w + st["of"]
            else:
                of += n
        out[name] = {"decks": decks, "of": of, "synergy": syn / syn_w if syn_w else None}
    return out, sum(n for n, _ in parts)


def _lowest(stats):
    """Lowest inclusion among the cards one page lists ({name: stats}): where its listing line sits."""
    rates = [st["decks"] / st["of"] for st in stats.values() if st.get("of")]
    return min(rates) if rates else 0.0


def _floor(cards, slot):
    """Lowest inclusion among the cards a page lists: where its listing line sits."""
    rates = [c[slot]["decks"] / c[slot]["of"] for c in cards.values() if c.get(slot)]
    return min(rates) if rates else 0.0


def _percentile(values, q):
    v = sorted(values)
    if not v:
        return 0.0
    pos = q * (len(v) - 1)
    lo = int(pos)
    return v[lo] + (v[min(lo + 1, len(v) - 1)] - v[lo]) * (pos - lo)


def _age_days(fetched):
    try:
        then = datetime.datetime.strptime(fetched, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None
    return round((datetime.datetime.now(datetime.timezone.utc) - then).total_seconds() / config.DAY, 1)


def _note_source(sources, sig):
    """Keep, per source, its oldest fetch and its worst cache state ("stale" > "network" > "fresh")."""
    if not sig:
        return
    old = sources.get(sig["source"])
    worst = max((old["cache"] if old else "fresh", sig.get("cache", "fresh")),
                key=("fresh", "network", "stale").index)
    sources[sig["source"]] = {"fetched": min(old["fetched"], sig["fetched"]) if old else sig["fetched"],
                              "cache": worst}


def _finish_sources(sources, warnings):
    """Add each source's age, and warn once for every source that served an expired copy."""
    for src, info in sources.items():
        info["age_days"] = _age_days(info["fetched"])
        if info["cache"] == "stale":
            age = f"{info['age_days']} days old" if info["age_days"] is not None else "out of date"
            warnings.append(f"{SOURCE_NAMES.get(src, src)} data is {age} (offline or the site failed)")


# ----------------------------------------------------------------------------- theme matchers
def _matchers():
    """playstyles.json theme_matchers: the weak last-resort signal that a card fits a theme."""
    if not _MATCHERS:
        data = net.read_json(roles.PLAYSTYLES_PATH) or {}
        for slug, m in (data.get("theme_matchers") or {}).items():
            _MATCHERS[slug] = (set(m.get("subtypes") or ()), set(m.get("types") or ()),
                               [re.compile(p) for p in m.get("text") or ()])
    return _MATCHERS


def theme_match(rec, theme):
    """True when the card's subtypes, types or rules text fit the theme's matcher (False if it has none)."""
    found = _matchers().get(theme)
    if not found or rec is None:
        return False
    subtypes, types, patterns = found
    text = rec["text"].lower()
    return bool(subtypes & set(rec["subtypes"])) or bool(types & set(rec["types"])) or any(
        p.search(text) for p in patterns)


# ----------------------------------------------------------------------------- gathering the evidence
def _playstyle_themes(spec):
    for p in fantasy.menu()["playstyles"]:
        if p["slug"] == (spec.get("playstyle") or "value"):
            return list(p["themes"])
    return []


def _theme_evidence(ev, db, commanders, bracket, spec, kw, call, skip):
    """Fill the theme parts of the evidence. Per theme, the best page that exists: this commander's decks at
    this bracket with the theme (when it has at least THIN decks), else this commander's decks with the theme
    at any bracket, else the theme across all commanders. With none, card text decides (theme_match)."""
    weights = {t: 1.0 for t in spec.get("themes") or ()}
    for t in _playstyle_themes(spec):
        weights.setdefault(t, PLAYSTYLE_THEME_WEIGHT)
    ev["theme_weights"] = weights
    for t in weights:
        ev["theme_src"][t] = None
        if "edhrec" not in ev["enabled"]:
            continue
        page = call(f"the {t} theme", edhrec.bracket_theme_signal, commanders, bracket, t, **kw)
        how = "at"
        if not page or page["n"] < THIN:
            page, how = _first(call(f"the {t} theme", edhrec.signals, commanders, None, t, **kw)), "all"
        if page:
            listed = _canon_cards(db, page["cards"], skip)
            for name, st in listed.items():
                ev["cards"].setdefault(name, _blank_card())["themes"][t] = st
            ev["n"]["themes"][t], ev["theme_src"][t] = page["n"], how
            ev["floor_themes"][t] = _lowest(listed)
            _note_source(ev["sources"], page)
            continue
        page = call(f"the {t} theme", edhrec.theme_signal, t, **kw)
        if page:
            for name, st in _canon_cards(db, page["cards"], skip).items():
                ev["cards"].setdefault(name, _blank_card())["theme_global"][t] = st
            ev["theme_src"][t] = "global"
            _note_source(ev["sources"], page)


def _builder_evidence(ev, db, commanders, bracket, sources, kw, call, skip):
    """The all-bracket page ("all") and the bracket's page ("at") from EDHREC, widened or replaced by
    Archidekt when the bracket is thin or EDHREC has nothing."""
    warnings, name = ev["warnings"], short_name(commanders)
    all_sig = at_sig = None
    if "edhrec" in sources:
        all_sig = _first(call("the all-bracket page", edhrec.signals, commanders, None, **kw))
        at_sig = _first(call(f"the Bracket {bracket} page", edhrec.signals, commanders, bracket, **kw))
        ev["meta"] = call("the commander page", edhrec.commander_meta, commanders, **kw)
    got_edhrec = bool(all_sig or at_sig)
    if not got_edhrec and "archidekt" in sources:
        at_sig = _first(call("decks", archidekt.signals, commanders, bracket, limit=ARCHIDEKT_LIMIT, **kw))
        all_sig = _first(call("decks", archidekt.signals, commanders, None, limit=ARCHIDEKT_LIMIT, **kw))
        if at_sig or all_sig:
            ev["at_label"] = f"Archidekt Bracket {bracket}"
            warnings.append("EDHREC has no data for this commander (or is off), so the Archidekt decks "
                            "are the only sample.")
    for sig in (all_sig, at_sig):
        _note_source(ev["sources"], sig)
    for sig, slot in ((all_sig, "all"), (at_sig, "at")):
        if sig:
            for card, st in _canon_cards(db, sig["cards"], skip).items():
                ev["cards"].setdefault(card, _blank_card())[slot] = st
            ev["n"][slot] = sig["n"]
    if got_edhrec and ev["n"]["at"] < THIN:
        _widen_thin_bracket(ev, db, commanders, bracket, sources, kw, call, skip, at_sig)
    elif not got_edhrec and at_sig and ev["n"]["at"] < THIN:
        warnings.append(f"Thin data: only {ev['n']['at']} Archidekt Bracket {bracket} {name} decks.")


def _widen_thin_bracket(ev, db, commanders, bracket, sources, kw, call, skip, at_sig):
    """Pool the neighbouring brackets (and Archidekt) into "at" when the bracket has under THIN decks, and say
    so with the counts."""
    name, had = short_name(commanders), ev["n"]["at"]
    parts = [(at_sig["n"], _canon_cards(db, at_sig["cards"], skip))] if at_sig else []
    used = {bracket: had}
    for b in (bracket - 1, bracket + 1):
        sig = None
        if 1 <= b <= 5:
            sig = _first(call(f"the Bracket {b} page", edhrec.signals, commanders, b, **kw))
        if sig:
            parts.append((sig["n"], _canon_cards(db, sig["cards"], skip)))
            used[b] = sig["n"]
            _note_source(ev["sources"], sig)
    deck_sig = None
    if "archidekt" in sources:
        deck_sig = _first(call("decks", archidekt.signals, commanders, bracket, limit=ARCHIDEKT_LIMIT, **kw))
        if deck_sig:
            parts.append((deck_sig["n"], _canon_cards(db, deck_sig["cards"], skip)))
            _note_source(ev["sources"], deck_sig)
    head = f"Thin data: only {had:,} Bracket {bracket} {name} decks on EDHREC (under {THIN}); "
    if len(parts) <= (1 if at_sig else 0):
        ev["warnings"].append(head + "no neighbouring bracket or Archidekt data to widen with.")
        return
    pooled, total = _pool(parts)
    for card in ev["cards"].values():
        card["at"] = None
    for card, st in pooled.items():
        ev["cards"].setdefault(card, _blank_card())["at"] = st
    ev["n"]["at"] = total
    span = sorted(b for b, n in used.items() if n)
    label = f"Brackets {span[0]}-{span[-1]}" if len(span) > 1 else f"Bracket {span[0]}" if span else ""
    ev["at_label"] = " + ".join(x for x in (label, "Archidekt" if deck_sig else "") if x) or ev["at_label"]
    detail = [f"Bracket {b} ({n:,} decks)" for b, n in sorted(used.items()) if n and b != bracket]
    detail += [f"{deck_sig['n']} Archidekt decks"] if deck_sig else []
    ev["warnings"].append(head + f"widened with {', '.join(detail)}, {total:,} decks in all.")


def _popularity_pool(db, ci, skip):
    """{name: EDHREC rank} for the most-played Commander-legal cards inside the colors (best POP_POOL)."""
    colors, found = set(ci), []
    for rec in db.values():
        rank = rec.get("rank")
        if (rank and rank <= POP_MAX_RANK and rec["legal"] == "legal" and set(rec["ci"]) <= colors
                and "Basic" not in rec["types"] and rec["name"] not in skip):
            found.append((rank, rec["name"]))
    return {n: r for r, n in sorted(found)[:POP_POOL]}


def gather(commanders, bracket, spec, db, *, sources=None, refresh=None, offline=None,
           tournament_signal=None):
    """Everything the scorer needs, fetched once and keyed by canonical card name:

    {"commanders", "ci", "bracket", "spec", "enabled", "at_label",
     "cards": {name: {"all": builder stats | None, "at": ..., "themes": {t: stats},
                      "theme_global": {t: stats}, "tourn": tournament stats | None,
                      "pop": EDHREC rank | None}},
     "n": {"all": decks, "at": decks, "themes": {t: decks}, "tourn": entries},
     "floor_all", "floor_at": lowest inclusion each page lists (a card under it was played in fewer decks),
     "tourn_totals", "meta": commander_meta | None, "salt": {name: salt}, "salt_floor",
     "theme_weights": {t: 1.0 | 0.5}, "theme_src": {t: "at" | "all" | "global" | None},
     "floor_themes": {t: lowest inclusion the page used for t lists; a card absent from it is under that},
     "precon": {"name", "cards", "s"} | None, "popularity": bool,
     "sources": {source: {"fetched", "cache", "age_days"}}, "warnings": [str]}

    `sources` names the enabled providers (default config.SOURCES). A failed or missing page costs a warning,
    never the run; with no builder data at all the pool comes from Scryfall's popularity rank."""
    sources = tuple(config.SOURCES if sources is None else sources)
    kw = {"refresh": refresh, "offline": offline}
    commanders = [db.resolve(c) or c for c in commanders]
    warnings = []
    ev = {"commanders": commanders, "ci": _union_ci(commanders, db), "bracket": bracket, "spec": spec,
          "enabled": sources, "at_label": f"Bracket {bracket}", "cards": {},
          "n": {"all": 0, "at": 0, "themes": {}, "tourn": 0}, "floor_all": 0.0, "floor_at": 0.0,
          "tourn_totals": None, "meta": None, "salt": {}, "salt_floor": None, "theme_weights": {},
          "theme_src": {}, "floor_themes": {}, "precon": None, "popularity": False, "sources": {},
          "warnings": warnings}
    skip = set(commanders)
    call = lambda label, fn, *a, **k: _guard(warnings, label, fn, *a, **k)

    _builder_evidence(ev, db, commanders, bracket, sources, kw, call, skip)
    _theme_evidence(ev, db, commanders, bracket, spec, kw, call, skip)

    if spec.get("keep_fun") and "edhrec" in sources:
        salt = call("the salt list", edhrec.salt_scores, **kw) or {}
        for raw, value in salt.items():
            rec = db.get(raw)
            if rec:
                ev["salt"][rec["name"]] = value
        ev["salt_floor"] = min(ev["salt"].values()) if ev["salt"] else None

    if W_BRACKET.get(bracket, 0) > 0:
        sig = tournament_signal
        if sig is None and "edhtop16" in sources:
            sig = _first(call("tournament results", edhtop16.signals, commanders, **kw))
        if sig:
            for card, st in _canon_cards(db, sig["cards"], skip).items():
                ev["cards"].setdefault(card, _blank_card())["tourn"] = st
            checked = (sig.get("meta") or {}).get("checked")
            if checked is not None:   # the source looked up only these cards (EDHTop16: a commander's 100 most played)
                looked_up = set(_canon_cards(db, dict.fromkeys(checked, {}), skip))
                for card, rec in ev["cards"].items():
                    if card not in looked_up:
                        rec["tourn_unchecked"] = True   # not looked at, which is not "never played": see _base
            ev["n"]["tourn"], ev["tourn_totals"] = sig["n"], sig.get("totals")
            _note_source(ev["sources"], sig)

    ev["floor_all"], ev["floor_at"] = _floor(ev["cards"], "all"), _floor(ev["cards"], "at")
    if not (ev["n"]["all"] or ev["n"]["at"]):
        _popularity_fallback(ev, db, commanders, skip)
    elif bracket in (2, 3):
        _add_precon(ev, db, commanders, kw, call, skip)
    _finish_sources(ev["sources"], warnings)
    return ev


def _popularity_fallback(ev, db, commanders, skip):
    pool = _popularity_pool(db, ev["ci"], skip)
    for name, rank in pool.items():
        ev["cards"].setdefault(name, _blank_card())["pop"] = rank
    ev["popularity"] = True
    ev["warnings"].append(
        f"No deck-builder data was available for {short_name(commanders)} (EDHREC and Archidekt are off, "
        "failed or have no page), so every card is scored by its overall EDHREC popularity rank from "
        "Scryfall. The results are generic: good-stuff staples for these colors, not what this commander's "
        "players actually run.")


def _add_precon(ev, db, commanders, kw, call, skip):
    """Brackets 2-3: remember the commander's newest precon, so its stock cards get the inertia discount."""
    found = call("precon decks", decklist.precons_for_commander, commanders[0], **kw)
    if not found:
        return
    cards = []
    for _, raw in found[0]["cards"]:
        rec = db.get(raw)
        if rec and "Basic" not in rec["types"] and rec["name"] not in skip:
            cards.append(rec["name"])
    ev["precon"] = {"name": found[0]["name"], "cards": cards}
    ev["precon"]["s"] = _precon_s(ev, db)


# ----------------------------------------------------------------------------- the base score
def _incl(ev, card):
    """(p_all, p_at): the card's inclusion rate over all brackets and at the target bracket. A card missing
    from a page that exists was played in fewer decks than that page's listing line, so it sits at or under
    the line; with no page at all, the other page stands in."""
    n = ev.get("n") or {}
    all_, at = card.get("all"), card.get("at")
    raw_all = all_["decks"] / all_["of"] if all_ else None
    raw_at = at["decks"] / at["of"] if at else None
    if raw_all is not None:
        p_all = raw_all
    elif raw_at is not None:
        p_all = min(raw_at, ev.get("floor_all", 0.0)) if n.get("all") else raw_at
    else:
        p_all = 0.0
    if raw_at is not None:
        p_at = raw_at
    elif n.get("at"):
        p_at = min(p_all, ev.get("floor_at", 0.0))
    else:
        p_at = p_all
    return p_all, p_at


def _base(ev, card, rec=None):
    """The base score before the precon discount: {"kind", "base", "n", "p_all", "p_at"}."""
    n = ev.get("n") or {}
    all_, at = card.get("all"), card.get("at")
    p_all, p_at = _incl(ev, card)
    if ev["bracket"] == 5 and n.get("tourn", 0) >= TOURN_MIN and not card.get("tourn_unchecked"):
        # cEDH: what tournament decks played, shrunk toward what cEDH builders chose (when we know that). A card
        # the tournament source did not look up keeps the builder rate below: 0 tournament entries would be a guess
        entries, nt = (card.get("tourn") or {}).get("entries", 0), n["tourn"]
        has_prior = bool(all_ or at or n.get("at") or n.get("all"))
        base = (entries + K_TOURN * p_at) / (nt + K_TOURN) if has_prior else entries / nt
        return {"kind": "tournament", "base": base, "n": nt, "p_all": p_all, "p_at": p_at}
    if at:
        base, size = (at["decks"] + K_BASE * p_all) / (at["of"] + K_BASE), at["of"]
    elif n.get("at"):
        base, size = (p_at * n["at"] + K_BASE * p_all) / (n["at"] + K_BASE), n["at"]
    else:
        base, size = p_all, (all_["of"] if all_ else n.get("all", 0))
    if all_ or at:
        return {"kind": "builder", "base": base, "n": size, "p_all": p_all, "p_at": p_at}
    pop = (card.get("pop") or (rec or {}).get("rank")) if ev.get("popularity") else None
    if pop and pop <= POP_MAX_RANK:
        base = POP_WEIGHT * (1 - math.log(pop) / math.log(POP_MAX_RANK))
        return {"kind": "popularity", "base": min(1.0, max(0.0, base)), "n": 0, "p_all": 0.0, "p_at": 0.0,
                "rank": pop}
    return {"kind": "none", "base": 0.0, "n": 0, "p_all": 0.0, "p_at": 0.0}


def _precon_s(ev, db):
    """Share of near-stock lists, read off the precon's weakest nonland cards: nobody picks those on purpose,
    so how often they still appear is how often the list was left as it came (10th percentile of base, a card
    on no list counting as 0, clamped to [0, PRECON_S_MAX])."""
    precon = ev.get("precon")
    if not precon:
        return 0.0
    bases = []
    for name in precon["cards"]:
        rec = db.get(name)
        if rec is not None and not rec["land"]:
            bases.append(_base(ev, ev["cards"].get(name) or _blank_card(), rec)["base"])
    return min(PRECON_S_MAX, max(0.0, _percentile(bases, PRECON_PERCENTILE)))


# ----------------------------------------------------------------------------- card_scores
def _clamp(x, cap):
    return max(-cap, min(cap, x))


class _Scorer:
    """The parts of a score that do not depend on the card, worked out once per card_scores call."""

    def __init__(self, ev, spec, db, role_map):
        self.ev, self.db, self.role_map = ev, db, role_map
        self.B = ev["bracket"]
        self.W = W_BRACKET.get(self.B, 0.0)
        self.weight = spec.get("weight")
        self.weight = config.DEFAULT_FANTASY_WEIGHT if self.weight is None else float(self.weight)
        self.keep_fun = bool(spec.get("keep_fun"))
        self.themes = ev.get("theme_weights") or {}
        self.who = short_name(ev["commanders"])
        self.label = ev.get("at_label") or f"Bracket {self.B}"
        precon = ev.get("precon")
        self.precon = set(precon["cards"]) if precon else set()
        self.s = 0.0
        if precon:
            self.s = precon["s"] if precon.get("s") is not None else _precon_s(ev, db)
        salt = ev.get("salt") or {}
        self.salt = salt if self.keep_fun else {}
        floor = ev.get("salt_floor")
        self.salt_floor = floor if floor is not None else (min(salt.values()) if salt else SALT_FLOOR)

    # --- one card
    def score(self, name):
        rec = self.db.get(name)
        card = {**_blank_card(), **(self.ev["cards"].get(name) or {})}   # hand-made evidence may omit slots
        base = _base(self.ev, card, rec)
        value, discounted = base["base"], False
        if name in self.precon and self.s > 0 and base["kind"] == "builder":
            value, discounted = max(0.0, (value - self.s) / (1 - self.s)), True
        resid, resid_text = self._residual(name, card)
        theme, pulls, theme_text = self._theme(card, rec)
        salt, salt_text = self._salt(name)
        parts = {"base": value, "resid": resid, "theme": theme, "salt": salt}
        extras = [t for t in (resid_text, theme_text, salt_text) if t]
        text = [self._base_text(card, base, discounted)] + extras
        return {"score": sum(parts.values()), "parts": parts, "kind": base["kind"],
                "evidence": "; ".join(text), "n": base["n"], "pulls": pulls}

    # --- parts
    def _residual(self, name, card):
        """(W_B * the shrunk, capped win-rate gap with versus without the card, text); (0, "") when the
        tournament data cannot speak: no weight at this bracket, no entries, or a role whose value depends on
        the rest of the deck (Brackets 1-4 only)."""
        tourn, totals = card.get("tourn"), self.ev.get("tourn_totals")
        if not self.W or not tourn or not totals:
            return 0.0, ""
        if self.B < 5 and not (self.role_map.get(name) or set()) & roles.CARRYOVER:
            return 0.0, ""
        games_out, wins_out = totals["games"] - tourn["games"], totals["wins"] - tourn["wins"]
        if tourn["games"] <= 0 or games_out <= 0:
            return 0.0, ""
        gap = tourn["wins"] / tourn["games"] - wins_out / games_out
        # The gap is only as sure as its thinner side: a staple in 98% of decks has a handful without it.
        n = min(tourn["entries"], totals["entries"] - tourn["entries"])
        if n <= 0:
            return 0.0, ""
        part = self.W * _clamp(RESID_SCALE * gap * n / (n + K_RESID), RESID_CAP)
        if abs(part) < SHOW_RESID or tourn["entries"] < SHOW_RESID_ENTRIES:   # too small or thin to mention
            return part, ""
        return part, (f"cEDH results: {gap * 100:+.1f} pts game win rate over "
                      f"{tourn['entries']:,} entries (weight {self.W:g})")

    def _theme(self, card, rec):
        """(clamp(fantasy weight * THEME_SCALE * weighted mean pull, +-THEME_CAP), {theme: pull}, text)."""
        if not self.themes:
            return 0.0, {}, ""
        pulls, notes = {}, []
        for t in self.themes:
            pull, how, shown = self._pull(card, rec, t)
            pulls[t] = pull
            if shown is not None and (pull >= SHOW_PULL or (how == "page" and pull <= SHOW_DRAG)):
                notes.append((abs(self.themes[t] * pull), shown))
        total_w = sum(self.themes.values())
        mean = sum(w * pulls[t] for t, w in self.themes.items()) / total_w
        top = [text for _, text in sorted(notes, reverse=True)[:2]]
        part = _clamp(self.weight * THEME_SCALE * mean, THEME_CAP)
        return part, pulls, ", ".join(top) if self.weight and top else ""

    def _pull(self, card, rec, t):
        """(pull, how, text) for one theme: the best evidence that exists, see _theme_evidence."""
        src = self.ev["theme_src"].get(t) if self.ev.get("theme_src") else None
        if src in ("at", "all"):
            p_all, p_at = _incl(self.ev, card)
            p_ref = p_at if src == "at" else p_all
            page, size = card["themes"].get(t), (self.ev["n"].get("themes") or {}).get(t, 0)
            if page:
                decks, of = page["decks"], page["of"]
            else:
                # EDHREC caps its per-type lists (creatures stop at the top 50, about 10%): a card missing
                # from a page that exists was played in fewer decks than its lowest listed card, not in none
                decks, of = min(p_ref, (self.ev.get("floor_themes") or {}).get(t, 0.0)) * size, size
            pull = (decks + K_THEME * p_ref) / (of + K_THEME) - p_ref
            return pull, "page", f"{pull:+.0%} in {t} decks"
        if src == "global":
            st = card["theme_global"].get(t)
            if st and st.get("synergy") is not None:
                return (GLOBAL_SYNERGY_FACTOR * max(0.0, st["synergy"]), "global",
                        f"{t} synergy {st['synergy']:+.0%} (all commanders)")
        if theme_match(rec, t):
            return MATCHER_PULL, "text", f"fits {t} (by card text)"
        return 0.0, "none", None

    def _salt(self, name):
        value = self.salt.get(name)
        if value is None:
            return 0.0, ""
        pen = SALT_GAMMA * max(0.0, value - self.salt_floor) / (SALT_MAX - self.salt_floor)
        return -pen, f"salt {value:.1f}" if pen > 0 else ""

    # --- text
    def _base_text(self, card, base, discounted):
        kind, who, label = base["kind"], self.who, self.label
        if kind == "popularity":
            return f"EDHREC rank #{base['rank']:,} overall (via Scryfall)"
        if kind == "tournament":
            entries, nt = (card.get("tourn") or {}).get("entries", 0), base["n"]
            text = f"in {_pct(entries / nt)} of {nt:,} cEDH tournament decks"
            return text + (f" (cEDH builders {_pct(base['p_at'])})" if base["p_at"] else "")
        all_, at = card.get("all"), card.get("at")
        if kind == "none":
            if self.ev.get("popularity"):
                return f"not among the {POP_MAX_RANK:,} most-played Commander cards (via Scryfall)"
            return "not on this commander's EDHREC lists (under ~5% of decks)"
        if at:
            extra = []
            if all_:
                extra.append(f"all brackets {_pct(all_['decks'] / all_['of'])}")
            syn = at["synergy"] if at.get("synergy") is not None else (all_ or {}).get("synergy")
            if syn is not None:
                extra.append(f"synergy {syn:+.0%}")
            text = f"in {_pct(at['decks'] / at['of'])} of {at['of']:,} {label} {who} decks"
            text += f" ({', '.join(extra)})" if extra else ""
        elif self.ev["n"].get("at"):
            text = (f"in {_pct(all_['decks'] / all_['of'])} of {all_['of']:,} {who} decks (all brackets); "
                    f"rare at {label}")
        else:
            text = f"in {_pct(all_['decks'] / all_['of'])} of {all_['of']:,} {who} decks (all brackets)"
        return text + ("; precon-adjusted" if discounted else "")


def card_scores(evidence, spec, db, role_map, names=None):
    """{name: {"score", "parts": {"base", "resid", "theme", "salt"}, "kind", "evidence", "n", "pulls"}}.

    score = base + resid + theme + salt, the parts being signed contributions (salt is <= 0):
      base   inclusion at the bracket, pulled toward the all-bracket rate: (decks_at + K_BASE*p_all) /
             (of_at + K_BASE); a precon card is rescaled to (base - s) / (1 - s) at Brackets 2-3; at Bracket 5
             the tournament play rate, shrunk toward the cEDH page with K_TOURN, replaces it when there are
             TOURN_MIN entries;
      resid  W_BRACKET[B] * clamp(RESID_SCALE * gap * n / (n + K_RESID), +-RESID_CAP), gap = game win
             rate with the card minus without it; Brackets 1-4 only for roles in roles.CARRYOVER;
      theme  clamp(spec["weight"] * THEME_SCALE * weighted mean over themes of how much more this
             commander's theme decks play the card than the decks it is compared with, +-THEME_CAP). A
             theme page is shrunk with K_THEME; a card absent from it counts as played at its listing
             floor, not never;
      salt   -SALT_GAMMA * (salt - floor) / (SALT_MAX - floor) when spec["keep_fun"].
    `pulls` holds the per-theme pulls (unweighted) for the "theme picks" report. `names=None` scores every
    card in the evidence; named cards the evidence has never heard of get base 0, kind "none"."""
    scorer = _Scorer(evidence, spec, db, role_map)
    out = {}
    for name in (list(evidence["cards"]) if names is None else names):
        canonical = db.resolve(name) or name
        out[canonical] = scorer.score(canonical)
    return out
