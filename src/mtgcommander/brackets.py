"""Wizards' Commander Brackets as data, plus the four limits a program can check.

Wizards says a deck's bracket rests on intent, but each bracket also carries limits that can be counted:
Game Changers, mass land denial, extra turns and two-card combos. The numbers live in
commander/brackets.json with their source and date, so a rule change is a data edit; this module only
applies them.

Three things a program cannot judge, each approximated by a rule the messages label as this tool's own:
  - "chaining" extra turns (Brackets 2-3): more than one extra-turn card counts as chaining.
  - "early" versus "late" two-card combos (Bracket 3): every two-card combo Commander Spellbook rates
    above Bracket 3 is blocked. Longer combos are never over a limit: Wizards' limits name two-card combos.
  - Exhibition's theme (Bracket 1): `estimated` is only the lowest bracket whose limits the list meets,
    a floor.

Combos come from providers/spellbook.py (a Combo is a plain dict, so tests feed fixtures). Spellbook's tags
do not cover Wizards' Bracket 1-2 rule against two-card combos (a combo can be two-card, infinite and tagged
Exhibition), so at Brackets 1-2 a two-card infinite combo is over the limit whatever its tag says."""
import json, os, re
from . import config

_DATA = {}  # brackets.json and what is derived from it, read on first use


def _data():
    if not _DATA:
        with open(os.path.join(config.COMMITTED, "brackets.json"), encoding="utf-8") as f:
            raw = json.load(f)
        _DATA.update(raw=raw,
                     mld=_names(raw["mass_land_denial_cards"]),
                     mld_except=_names(raw["mass_land_denial_exceptions"]),
                     mld_rx=[re.compile(p) for p in raw["mass_land_denial_patterns"]],
                     extra=_names(raw["extra_turn_cards"]),
                     extra_rx=[re.compile(p) for p in raw["extra_turn_patterns"]])
    return _DATA


def _names(cards):
    """Each name plus its front face, so a split card matches as "A // B" or as just "A"."""
    return set(cards) | {c.split(" // ")[0] for c in cards}


def _bracket(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = 0
    if not 1 <= n <= 5:
        raise ValueError(f"bracket must be 1-5, not {value!r}")
    return n


def rules(bracket):
    """The limits of one bracket: name, wording, game_changers_max (None: any number), mass_land_denial
    (True: allowed), extra_turns, two_card_combos, plus its number."""
    n = _bracket(bracket)
    return dict(_data()["raw"]["brackets"][str(n)], bracket=n)


# ---------------------------------------------------------------- card tests
def _on_list(rec, names):
    return rec.get("name") in names or rec.get("front") in names


def _text_hit(rec, patterns):
    text = (rec.get("text") or "").lower()
    return any(p.search(text) for p in patterns)


def _mld_source(rec):
    """"list" (curated name), "text" (a text pattern matched) or None. The exceptions only veto a text
    match: a card that replaces the lands it destroys fails Wizards' "without replacing them"."""
    d = _data()
    if _on_list(rec, d["mld"]):
        return "list"
    if not _on_list(rec, d["mld_except"]) and _text_hit(rec, d["mld_rx"]):
        return "text"
    return None


def is_mass_land_denial(rec):
    return _mld_source(rec) is not None


def is_extra_turn(rec):
    d = _data()
    return _on_list(rec, d["extra"]) or _text_hit(rec, d["extra_rx"])


# ---------------------------------------------------------------- combos
def _combo_label(combo):
    cards = " + ".join(combo.get("cards") or [])
    result = ", ".join((combo.get("produces") or [])[:3])
    return f"{cards} ({result})" if result else cards


def _combo_limit(combo, bracket):
    """Why `bracket` does not allow this Commander Spellbook combo, or None when it does. Wizards' limits
    cover two-card combos only ("Game-enders, lockouts or infinites"), so a longer combo is never over the
    limit, whatever Spellbook rates it."""
    mode = rules(bracket)["two_card_combos"]
    if mode == "any" or not combo.get("two_card"):
        return None
    if mode == "none" and combo.get("infinite"):
        return f"a two-card infinite combo, which Bracket {bracket} does not allow"
    needed = combo.get("min_bracket") or 1
    if needed <= bracket:
        return None
    rated = f"Commander Spellbook rates it for Bracket {needed} or higher"
    if mode == "none":
        return f"{rated}, and Bracket {bracket} allows no two-card combos"
    return (f"{rated}; Bracket {bracket} allows two-card combos only late in the game, and this tool "
            "cannot tell early from late, so it blocks the ones Spellbook rates higher")


def _problems(bracket, facts):
    """Every limit of `bracket` the facts break, as violation dicts. `excess` is how many of `cards`
    must go (for a combo, any one of its cards)."""
    rule, out = rules(bracket), []
    gc, cap = facts["gc"], rule["game_changers_max"]
    if cap is not None and len(gc) > cap:
        s = "s" if len(gc) != 1 else ""
        allowed = "none" if cap == 0 else f"up to {cap}"
        out.append({"rule": "game_changers", "cards": list(gc), "excess": len(gc) - cap,
                    "message": f"{len(gc)} Game Changer{s} ({', '.join(gc)}); "
                               f"Bracket {bracket} allows {allowed}."})
    if facts["mld"] and not rule["mass_land_denial"]:
        names = [n for n, _ in facts["mld"]]
        guessed = [n for n, how in facts["mld"] if how == "text"]
        msg = f"Mass land denial is not allowed in Bracket {bracket}: {', '.join(names)}."
        if guessed:
            msg += (f" Found by rules text ({', '.join(guessed)}); Wizards publishes no complete list, "
                    "so check with your pod.")
        out.append({"rule": "mass_land_denial", "cards": names, "excess": len(names), "message": msg})
    extra, mode = facts["extra"], rule["extra_turns"]
    if mode == "none" and extra:
        out.append({"rule": "extra_turns", "cards": list(extra), "excess": len(extra),
                    "message": f"Bracket {bracket} allows no extra-turn cards: {', '.join(extra)}."})
    elif mode == "no-chaining" and len(extra) > 1:
        out.append({"rule": "extra_turns", "cards": list(extra), "excess": len(extra) - 1,
                    "message": f"{len(extra)} extra-turn cards ({', '.join(extra)}); Bracket {bracket} "
                               "allows extra turns only if they are not chained. This tool treats a "
                               "second extra-turn card as chaining, which is its own judgment, not a "
                               "Wizards rule."})
    for combo in facts["combos"]:
        why = _combo_limit(combo, bracket)
        if why:
            out.append({"rule": "two_card_combos", "cards": list(combo.get("cards") or []), "excess": 1,
                        "url": combo.get("url", ""), "message": f"{_combo_label(combo)}: {why}."})
    return out


# ---------------------------------------------------------------- the checks
def _inventory(commanders, cards, db):
    """The list's distinct cards as db records, commanders first: (records, commander names, unknown
    names). `cards` may hold names or (count, name) pairs; a singleton format needs no counts."""
    if isinstance(commanders, str):
        commanders = [commanders]
    recs, seen, unknown, cmdr = [], set(), [], set()
    for is_commander, group in ((True, commanders or []), (False, cards or [])):
        for item in group:
            name = item[1] if isinstance(item, (tuple, list)) else item
            rec = db.get(name)
            if rec is None:
                if name not in seen:
                    unknown.append(name)
                    seen.add(name)
            elif rec["name"] not in seen:
                seen.add(rec["name"])
                recs.append(rec)
                if is_commander:
                    cmdr.add(rec["name"])
    return recs, cmdr, unknown


def check(commanders, cards, bracket, db, *, combos=None):
    """What a program can check of the list against `bracket`. `combos` is the answer of
    providers.spellbook.find_combos ({"included": [Combo], "almost": [Combo]}); without it combos are not
    checked and `estimated` ignores them. Each violation is {"rule", "cards", "message", "excess"} (a
    combo's also has "url"): `excess` of the listed cards must go. `estimated` is the lowest bracket
    whose limits the list meets."""
    bracket = _bracket(bracket)
    rule = rules(bracket)
    recs, commander_names, unknown = _inventory(commanders, cards, db)
    facts = {"gc": [], "mld": [], "extra": [], "combos": list((combos or {}).get("included") or [])}
    for r in recs:
        how = _mld_source(r)
        if r.get("gc"):
            facts["gc"].append(r["name"])
        if how:
            facts["mld"].append((r["name"], how))
        if is_extra_turn(r):
            facts["extra"].append(r["name"])
    violations = _problems(bracket, facts)
    estimated = next((b for b in range(1, 6) if not _problems(b, facts)), 5)

    notes = []
    if unknown:
        shown = ", ".join(unknown[:5]) + (", ..." if len(unknown) > 5 else "")
        s = "s" if len(unknown) != 1 else ""
        notes.append(f"{len(unknown)} card name{s} not found in the card index and not checked: {shown}.")
    if combos is None:
        notes.append("Combos were not checked (no Commander Spellbook data), so the estimate ignores them.")
    if rule["extra_turns"] == "no-chaining" and facts["extra"]:
        notes.append(f"Extra turns: Wizards allows them in Bracket {bracket} only if they are not chained "
                     "or looped. This tool reads that as at most one extra-turn card, a judgment of its "
                     "own, not a Wizards rule.")
    if rule["game_changers_max"] is not None:
        notes += [f"{r['name']} is your commander and a Game Changer, so it counts toward the limit."
                  for r in recs if r["name"] in commander_names and r.get("gc")]
    longer = [c for c in facts["combos"] if not c.get("two_card") and (c.get("min_bracket") or 1) > bracket]
    for combo in longer[:3]:
        notes.append(f"{_combo_label(combo)}: Commander Spellbook rates it for Bracket {combo['min_bracket']} "
                     "or higher. Wizards' limits name only two-card combos, so it is allowed; your pod may "
                     "still want to know.")
    if not violations and estimated < bracket:
        notes.append(f"The list meets the checkable limits of Bracket {estimated}. Wizards says intent and "
                     "how a deck plays decide its bracket, so treat the estimate as a floor.")
    pairs = [{"cards": list(c.get("cards") or []), "produces": list(c.get("produces") or []),
              "url": c.get("url", ""), "min_bracket": c.get("min_bracket"),
              "infinite": bool(c.get("infinite"))} for c in facts["combos"] if c.get("two_card")]
    return {"bracket": bracket, "ok": not violations, "violations": violations,
            "game_changers": facts["gc"], "gc_max": rule["game_changers_max"],
            "mass_land_denial": [n for n, _ in facts["mld"]], "extra_turns": facts["extra"],
            "two_card_combos": pairs, "estimated": estimated, "notes": notes}


def blocked_adds(bracket, combos):
    """{card to add: reason} for every card that would finish a combo this bracket does not allow. Only a
    combo with exactly one card missing counts; a missing template (such as "any sacrifice outlet")
    names no card to block."""
    bracket = _bracket(bracket)
    found = {}
    for combo in (combos or {}).get("almost") or []:
        missing = combo.get("missing") or []
        why = _combo_limit(combo, bracket) if len(missing) == 1 else None
        if why:
            found.setdefault(missing[0], []).append((combo, why))
    out = {}
    for name, hits in found.items():
        combo, why = hits[0]
        partners = ", ".join(c for c in combo.get("cards") or [] if c != name)
        kind = "a two-card combo" if combo.get("two_card") else "a combo"
        result = ", ".join((combo.get("produces") or [])[:3])
        shown = f" ({result})" if result else ""
        more = f" (and {len(hits) - 1} more such combos)" if len(hits) > 1 else ""
        out[name] = f"completes {kind} with {partners}{shown}: {why}{more}"
    return out


def can_add(rec, state, bracket):
    """(True, "") when adding `rec` keeps the list within `bracket`; else (False, why). `state` counts
    what the list already holds: {"gc": n, "extra_turns": n, "mld": n}; a missing key counts as 0."""
    rule, state, name = rules(bracket), state or {}, rec.get("name", "this card")
    n, cap = rule["bracket"], rule["game_changers_max"]
    if rec.get("gc") and cap is not None and state.get("gc", 0) + 1 > cap:
        held = f", and the list already has {state.get('gc', 0)}" if cap else ""
        allowed = "none" if cap == 0 else f"up to {cap}"
        return False, f"{name} is a Game Changer; Bracket {n} allows {allowed}{held}"
    if not rule["mass_land_denial"] and is_mass_land_denial(rec):
        return False, f"{name} is mass land denial, which Bracket {n} does not allow"
    if is_extra_turn(rec):
        if rule["extra_turns"] == "none":
            return False, f"{name} is an extra-turn card; Bracket {n} allows none"
        if rule["extra_turns"] == "no-chaining" and state.get("extra_turns", 0) >= 1:
            return False, (f"{name} would be a second extra-turn card; Bracket {n} allows extra turns "
                           "only if they are not chained (this tool allows one)")
    return True, ""


# ---------------------------------------------------------------- legality
DECK_SIZE = 100            # a Commander deck is exactly this many cards, the commander(s) included
_PARTNER_WITH = "partner with "


def _front(name):
    return (name or "").split(" // ")[0].casefold()


def _name_list(names, limit=8):
    """'A, B, C' for a message; a long list ends 'and N more' (the problem's `cards` holds every name)."""
    shown = ", ".join(names[:limit])
    return shown + (f", and {len(names) - limit} more" if len(names) > limit else "")


def _can_pair(a, b):
    """Whether commander records `a` and `b` may lead one deck together. The rules are Partner (both),
    Partner with <Name> (each names the other), Friends forever (both), Partner—<restriction> such as Character
    select (both with the same restriction), Choose a Background with a Background, and a Doctor with a
    Doctor's companion. `partner` is carddb's reading of the front face's rules text."""
    pa, pb = (a.get("partner") or "").casefold(), (b.get("partner") or "").casefold()
    if not pa or not pb:
        return False
    if pa == pb and (pa in ("partner", "friends forever") or pa.startswith("partner—")):
        return True
    if pa.startswith(_PARTNER_WITH) and pb.startswith(_PARTNER_WITH):
        return (pa[len(_PARTNER_WITH):] == _front(b.get("front") or b.get("name"))
                and pb[len(_PARTNER_WITH):] == _front(a.get("front") or a.get("name")))
    return {pa, pb} in ({"choose a background", "background"}, {"doctor", "doctor's companion"})


def _commander_problems(leaders):
    """Messages about who leads the deck. `leaders` is [(name, record or None)] in the order given."""
    if not leaders:
        return ["The list has no commander."]
    if len(leaders) > 2:
        return [f"A Commander deck has one or two commanders; this list names {len(leaders)}: "
                f"{_name_list([n for n, _ in leaders])}."]
    out = []
    for name, rec in leaders:
        if rec is None:
            out.append(f"{name} was not found in the card index, so it cannot be checked as a commander.")
        elif not rec.get("commander_ok"):
            out.append(f"{name} cannot be a commander: it is not a legendary creature and does not say it can "
                       "be your commander.")
        elif len(leaders) == 1 and (rec.get("partner") or "") == "background":
            out.append(f"{name} is a Background; it needs a commander with Choose a Background beside it.")
    if not out and len(leaders) == 2:
        (na, a), (nb, b) = leaders
        if not _can_pair(a, b):
            how = "; ".join(f"{n} has {(r.get('partner') or 'no pairing ability')}" for n, r in leaders)
            out.append(f"{na} and {nb} cannot lead a deck together ({how}).")
    return out


def legality(commanders, cards, db):
    """Whether the list is a legal Commander deck: {"ok": bool, "problems": [{"kind", "cards", "message"}]}.
    `cards` are the non-commander cards as names or (count, name) pairs; `db.get(name)` gives card records.
    One problem per kind, most important first:
      commander  none, more than two, one that cannot lead, or two that cannot be paired
      count      the total, commanders included, is not DECK_SIZE (a name the index does not know still
                 counts toward the total, but nothing else is said about it; that report belongs to the caller)
      banned / not_legal   `legal` is "banned" / "not_legal" or "restricted" (commanders included)
      color      a card whose color identity is not inside the commanders' combined identity
      duplicate  more than one copy of a card that is not a basic land and does not allow any number"""
    if isinstance(commanders, str):
        commanders = [commanders]
    leaders = [(name, db.get(name)) for name in commanders or []]
    copies, unknown_copies = {}, 0       # canonical name -> copies; copies of names the index lacks
    for item in cards or []:
        n, name = item if isinstance(item, (tuple, list)) else (1, item)
        rec = db.get(name)
        if rec is None:
            unknown_copies += n
        else:
            key = rec.get("name") or name
            copies[key] = copies.get(key, 0) + n
    for name, rec in leaders:            # a commander also in the 99 is a second copy
        if rec is not None:
            key = rec.get("name") or name
            copies[key] = copies.get(key, 0) + 1
    records = {name: db.get(name) for name in copies}
    problems = []

    def add(kind, names, message):
        problems.append({"kind": kind, "cards": list(names), "message": message})

    for message in _commander_problems(leaders):
        add("commander", [n for n, _ in leaders], message)
    total = sum(copies.values()) + unknown_copies + sum(1 for _, rec in leaders if rec is None)
    if total != DECK_SIZE:
        add("count", [], f"A Commander deck has exactly {DECK_SIZE} cards, commander included; this list has "
                         f"{total}.")
    banned = [n for n, r in records.items() if r.get("legal") == "banned"]
    if banned:
        add("banned", banned, f"Banned in Commander: {_name_list(banned)}.")
    illegal = [n for n, r in records.items() if r.get("legal") in ("not_legal", "restricted")]
    if illegal:
        add("not_legal", illegal, f"Not legal in Commander: {_name_list(illegal)}.")
    known = [rec for _, rec in leaders if rec is not None]
    if known:                            # with no commander there is no identity to measure against
        identity = set("".join(rec.get("ci") or "" for rec in known))
        off = [n for n, r in records.items() if set(r.get("ci") or "") - identity]
        if off:
            shown = "".join(c for c in "WUBRG" if c in identity) or "colorless"
            add("color", off, f"{len(off)} card{'s' if len(off) != 1 else ''} outside the commander's colors "
                              f"({shown}): {_name_list(off)}.")
    repeated = [n for n, k in copies.items() if k > 1 and "Basic" not in (records[n].get("types") or [])
                and not records[n].get("any_number")]
    if repeated:
        add("duplicate", repeated, "More than one copy (only basic lands and cards that say so may repeat): "
                                   + _name_list([f"{n} x{copies[n]}" for n in repeated]) + ".")
    return {"ok": not problems, "problems": problems}
