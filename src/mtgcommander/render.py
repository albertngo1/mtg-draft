"""Text and JSON output for the Commander builder: phone-width reports and the machine-readable result.

Why one module: the engine (score.py, build.py) returns plain result dicts and cli.py never formats anything, so
this is the only place that decides how a result reads. Three rules shape every report:
  - Lines stay within WIDTH (100) characters, so a phone terminal does not wrap a table mid-word. Long evidence
    goes on its own indented line instead of a wide column, and `_fit` wraps whatever still overflows (a long
    card name, a long warning).
  - Every number says where it came from. The footer names each source with its fetch date and says plainly
    that below Bracket 5 the numbers are what deck builders chose, not how often decks won.
  - Money prints as $12.34, gains as +0.42 and shares as 41%.
A report never fails on a missing field (results may leave optional keys out or empty); it prints less instead.

`as_json` is the other half: the same result with "schema": 1 first, so scripts can tell when the layout changes."""
import json, textwrap
from . import roles

SCHEMA = 1
WIDTH = 100                 # the longest line any report prints
TOP_EVIDENCE = 20           # cards of a build that get an evidence line when not verbose
MAX_BLOCKED = 10            # blocked cards listed before "and N more"
MAX_THEMES = 30             # themes listed before "and N more" (a commander can have hundreds of tags)
MAX_CHANGES = 12            # role-target changes listed under a calibration before "and N more"
ROLE_KEYS = ("land",) + roles.ROLES + ("topend",)
LABELS = dict(roles.LABELS, land="lands", topend="top-end")
SECTIONS = ("Creatures", "Planeswalkers", "Instants", "Sorceries", "Artifacts", "Enchantments", "Battles", "Lands")
SOURCE_ORDER = ("edhrec", "archidekt", "edhtop16", "spellbook", "scryfall", "scryfall_tags", "mtgjson")
CURVE_KEYS = ("0", "1", "2", "3", "4", "5", "6", "7+")
SOURCE_LABELS = {"edhrec": "EDHREC", "archidekt": "Archidekt", "edhtop16": "EDHTop16", "scryfall": "Scryfall",
                 "scryfall_tags": "Scryfall function tags", "prices": "Scryfall prices",
                 "spellbook": "Commander Spellbook", "mtgjson": "MTGJSON"}


# ---------------------------------------------------------------- JSON
def _jsonable(value):
    """json.dumps fallback: sets (the owned-card set in an engine context) become sorted lists."""
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    return str(value)


def as_json(result):
    """The result as JSON text, "schema": 1 first, then the result's own keys."""
    body = {"schema": SCHEMA}
    body.update((k, v) for k, v in result.items() if k != "schema")
    return json.dumps(body, indent=2, ensure_ascii=False, default=_jsonable)


# ---------------------------------------------------------------- small formatters
def _money(x):
    return "$?" if x is None else f"${x:,.2f}"


def _budget(x):
    """$75 for a whole-dollar budget, $75.50 otherwise."""
    return _money(x) if float(x) != int(x) else f"${int(x):,}"


def _pct(x):
    return "?" if x is None else f"{x * 100:.0f}%"


def _gain(x):
    return f"{x or 0:+.2f}"


def _num(n):
    return "?" if n is None else f"{n:,}"


def _day(iso):
    return (iso or "")[:10]


def _plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _ci(ci):
    return ci or "colorless"


def _wrap(text, indent=0, hang=2):
    """`text` as lines of at most WIDTH characters: the first indented `indent` spaces, the rest `hang` more."""
    return textwrap.wrap(text, WIDTH, initial_indent=" " * indent, subsequent_indent=" " * (indent + hang),
                         break_on_hyphens=False)


def _fit(lines):
    """Wrap any line still wider than WIDTH, keeping its indent (a safety net behind the layouts below)."""
    out = []
    for line in lines:
        if len(line) <= WIDTH:
            out.append(line)
        else:
            lead = len(line) - len(line.lstrip(" "))
            out += _wrap(line.strip(), indent=lead, hang=4)
    return out


def _done(lines):
    return "\n".join(_fit(lines))


def _pack(prefix, cells, hang=7, sep="  "):
    """Lines that start with `prefix` and then hold whole `cells`, never splitting inside one: a role cell such
    as 'wipes 0 (1-5) LOW' stays together even when the line has to break before it."""
    lines, cur = [], prefix
    for i, cell in enumerate(cells):
        if i == 0:
            cur += cell
        elif len(cur) + len(sep) + len(cell) > WIDTH:
            lines.append(cur)
            cur = " " * hang + cell
        else:
            cur += sep + cell
    return lines + [cur]


def _with_tail(text, tail, indent):
    """`text` wrapped at `indent`, then `tail` ('fills: ramp') on its last line if it fits, else on its own line,
    so a short tail is never cut in half."""
    lines = _wrap(text, indent=indent, hang=0) or [" " * indent]
    if len(lines[-1]) + 1 + len(tail) <= WIDTH:
        lines[-1] += " " + tail
    else:
        lines.append(" " * indent + tail)
    return lines


def _hang(head, text):
    """`head` then `text`, wrapped so the continuation lines line up under the text."""
    return textwrap.wrap(head + text, WIDTH, subsequent_indent=" " * len(head), break_on_hyphens=False) or [head]


# ---------------------------------------------------------------- shared pieces
def _bracket_no(result):
    b = result.get("bracket")
    if isinstance(b, dict):
        return b.get("bracket")
    return b if b is not None else (result.get("spec") or {}).get("bracket")


def _bn(result):
    """The result's bracket number as text ('?' when it has none, so a partial result still prints)."""
    n = _bracket_no(result)
    return "?" if n is None else str(n)


def _check_report(result):
    """The brackets.check report inside a result: "bracket_check" in check and build results ("bracket" is the
    target number, as in an upgrade result). A report stored under "bracket" itself is still read."""
    for key in ("bracket", "bracket_check", "bracket_report"):
        if isinstance(result.get(key), dict):
            return result[key]
    return {}


def _head(name, result):
    """['Squirreled Away → Bracket 3, budget $75 (spent $42.10); themes: tokens; playstyle: aristocrats'], or the
    same on two lines (the fantasy after the money) when one line would be wider than WIDTH."""
    spec = result.get("spec") or {}
    budget, spent = result.get("budget"), result.get("spent")
    cost = f"budget {_budget(budget)}" if budget is not None else "no budget"
    cost += f" (spent {_money(spent)})" if spent is not None else ""
    themes = ", ".join(spec.get("themes") or []) or "none"
    first = f"{name} → Bracket {_bn(result)}, {cost}"
    fantasy = f"themes: {themes}; playstyle: {spec.get('playstyle') or 'value'}"
    return [f"{first}; {fantasy}"] if len(first) + len(fantasy) + 2 <= WIDTH else [first, "  " + fantasy]


def _deck_line(deck):
    names = " + ".join(deck.get("commanders") or []) or "no commander"
    count = f", {deck['count']} cards" if deck.get("count") is not None else ""
    return f"{names} ({_ci(deck.get('ci'))}){count}"


def _warnings(result):
    out = []
    for w in result.get("warnings") or []:
        out += _wrap("- " + w, indent=2, hang=2)
    return ["", "Warnings:"] + out if out else []


def _sources_text(sources):
    ordered = sorted(sources, key=lambda s: (SOURCE_ORDER.index(s) if s in SOURCE_ORDER else len(SOURCE_ORDER), s))
    bits = []
    for name in ordered:
        info = sources[name] or {}
        bits.append(f"{SOURCE_LABELS.get(name, name.replace('_', ' '))} {_day(info.get('fetched'))}".strip()
                    + (" (stale)" if info.get("cache") == "stale" else ""))
    return ", ".join(bits)


def _footer(result, evidence=True):
    """Where the data came from and what kind of numbers they are. `evidence` is False for reports that only
    check rules (no builder or tournament numbers to caveat)."""
    text = _sources_text(result.get("sources") or {})
    if not text and not evidence:
        return []
    lines = [""] + _wrap(f"Sources: {text}." if text else "Sources: none recorded.", hang=2)
    bracket = _bracket_no(result)
    if evidence and isinstance(bracket, int):
        if bracket < 5:
            lines += _wrap(f"At Bracket {bracket} these numbers show what deck builders chose, not how often decks "
                           "won.")
        else:
            lines += _wrap("At Bracket 5 the numbers lean on tournament decks and results; with few entries they "
                           "fall back to what builders chose.")
    return lines


def _out_line(result):
    return [f"Wrote the new list to {result['out']}"] if result.get("out") else []


def role_status(have, target):
    """"low", "ok" or "high": a count against {"min", "target", "max"} (top-end has only a max)."""
    lo, hi = target.get("min"), target.get("max")
    if lo is not None and have < lo:
        return "low"
    return "high" if hi is not None and have > hi else "ok"


def _range(target):
    lo, hi = target.get("min"), target.get("max")
    return f"{lo}-{hi}" if lo is not None and hi is not None else f"max {hi}"


def _status_text(have, target, status):
    if status == "low":
        return f"low, {target['min'] - have} short"
    return f"high, {have - target['max']} over" if status == "high" else "ok"


def _value(v):
    """A deck value: a bare number, or build.deck_value's dict with the total (and power / theme split)."""
    if isinstance(v, dict):
        return v.get("total")
    return v


def _value_line(value):
    """'Value: 33.5 (power 29.8, theme 3.7)': a build's total, with the split when the engine gives one."""
    total = _value(value)
    if total is None:
        return []
    split = ""
    if isinstance(value, dict) and value.get("power") is not None and value.get("theme") is not None:
        split = f" (power {value['power']:.1f}, theme {value['theme']:.1f})"
    return [f"Value: {total:.1f}{split}"]


def _value_change(before, after):
    """'Value: 18.2 → 21.7 (+3.5)'."""
    b, a = _value(before), _value(after)
    return [] if b is None or a is None else [f"Value: {b:.1f} → {a:.1f} ({a - b:+.1f})"]


def _rules_summary(rep):
    """One line of what a brackets.check report found."""
    gc, cap = rep.get("game_changers") or [], rep.get("gc_max")
    bits = [f"Game Changers {len(gc)}" + (f" of {cap}" if cap is not None else "")]
    bits.append(f"extra turns {len(rep.get('extra_turns') or [])}")
    bits.append(f"mass land denial {len(rep.get('mass_land_denial') or [])}")
    bits.append(f"two-card combos {len(rep.get('two_card_combos') or [])}")
    return "; ".join(bits)


def _bracket_summary(rep, number):
    """The compact bracket verdict a build prints: one line of counts, then the problems and notes."""
    problems = rep.get("violations") or []
    verdict = "ok" if not problems else _plural(len(problems), "problem")
    lines = _wrap(f"Bracket {rep.get('bracket', number)}: {verdict}; {_rules_summary(rep)}", hang=4)
    lines += _problem_lines(problems)
    for note in rep.get("notes") or []:
        lines += _wrap("Note: " + note, indent=2, hang=6)
    return lines


def _problem_lines(problems, indent=2):
    out = []
    for p in problems:
        out += _wrap("- " + (p.get("message") or p.get("rule") or "problem"), indent=indent, hang=2)
    return out


def _blocked_lines(blocked):
    out = []
    for b in (blocked or [])[:MAX_BLOCKED]:
        out += _wrap(f"Blocked: {b.get('card')} — {b.get('reason')}", hang=4)
    if blocked and len(blocked) > MAX_BLOCKED:
        out.append(f"Blocked: and {len(blocked) - MAX_BLOCKED} more (see --json)")
    return out


def _role_cells(counts, targets):
    """['lands 36 (34-38)', 'ramp 8 (9-14) LOW', ...] for the roles both dicts know."""
    cells = []
    for key in ROLE_KEYS:
        if counts.get(key) is None:
            continue
        have, target = counts[key], targets.get(key)
        cell = f"{LABELS[key]} {have}"
        if target:
            cell += f" ({_range(target)})"
            status = role_status(have, target)
            cell += "" if status == "ok" else f" {status.upper()}"
        cells.append(cell)
    return cells


# ---------------------------------------------------------------- check
def _legality_lines(legality):
    problems = legality.get("problems") or []
    if legality.get("ok", not problems):
        return ["Legality: ok"]
    return [f"Legality: {_plural(len(problems), 'problem')}"] + _problem_lines(problems)


def _bracket_lines(rep):
    problems = rep.get("violations") or []
    n = rep.get("bracket", "?")
    out = [f"Bracket {n}: " + ("ok" if not problems else _plural(len(problems), "problem"))]
    out += _problem_lines(problems)
    gc, cap = rep.get("game_changers") or [], rep.get("gc_max")
    gc_text = f"Game Changers: {len(gc)}" + (f" of {cap}" if cap is not None else " (no limit)")
    out += _wrap(gc_text + (f" ({', '.join(gc)})" if gc else ""), indent=2, hang=4)
    for label, key in (("Mass land denial", "mass_land_denial"), ("Extra turns", "extra_turns")):
        names = rep.get(key) or []
        out += _wrap(f"{label}: " + (", ".join(names) if names else "none"), indent=2, hang=4)
    combos = rep.get("two_card_combos") or []
    out.append("  Two-card combos: " + (str(len(combos)) if combos else "none"))
    for c in combos:
        result = ", ".join((c.get("produces") or [])[:3])
        out += _wrap(" + ".join(c.get("cards") or []) + (f" ({result})" if result else ""), indent=4, hang=4)
        if c.get("url"):
            out.append("      " + c["url"])
    if rep.get("estimated") is not None:
        out += _wrap(f"Lowest bracket the list fits: {rep['estimated']} (a floor; how the deck plays decides the "
                     "real one).", indent=2, hang=2)
    for note in rep.get("notes") or []:
        out += _wrap("Note: " + note, indent=2, hang=6)
    return out


def _roles_table(counts, targets, status=None):
    out = [f"  {'ROLE':<13}{'HAVE':>4}  {'RANGE':<9}{'TARGET':>6}  STATUS"]
    for key in ROLE_KEYS:
        if counts.get(key) is None or not targets.get(key):
            continue
        have, target = counts[key], targets[key]
        state = (status or {}).get(key) or role_status(have, target)
        goal = str(target["target"]) if target.get("target") is not None else ""
        out.append(f"  {LABELS[key]:<13}{have:>4}  {_range(target):<9}{goal:>6}  {_status_text(have, target, state)}")
    return out


def _curve_line(curve):
    cells = [f"{k}:{curve[k]}" for k in CURVE_KEYS if k in curve]
    avg = f"   average {curve['avg']:.1f}" if curve.get("avg") is not None else ""
    return _wrap("Curve of nonland cards (mana value:count)  " + "  ".join(cells) + avg, hang=4)


def check_report(result, verbose=False):
    deck = result.get("deck") or {}
    lines = [f"{deck.get('name') or 'Deck'}: {_deck_line(deck)}; checked at Bracket {_bn(result)}", ""]
    lines += _legality_lines(result.get("legality") or {})
    lines += [""] + _bracket_lines(_check_report(result))
    rl = result.get("roles") or {}
    if rl.get("counts"):
        lines += ["", "Roles (the 99 cards)"] + _roles_table(rl["counts"], rl.get("targets") or {}, rl.get("status"))
    if result.get("curve"):
        lines += [""] + _curve_line(result["curve"])
    return _done(lines + _warnings(result) + _footer(result, evidence=False))


# ---------------------------------------------------------------- upgrade
def _swap_lines(rank, swap, verbose):
    forced, owned = bool(swap.get("forced")), bool(swap.get("owned"))
    tail = f"{_gain(swap.get('gain'))}  {_money(0.0 if owned else swap.get('price'))}"
    marks = [m for m, on in (("owned", owned), ("forced", forced)) if on]
    tail += f"  ({', '.join(marks)})" if marks else ""
    cut, add = swap.get("cut") or "?", swap.get("add") or "?"
    one = f"{rank:>2}  CUT {cut}  →  ADD {add}   {tail}"
    lines = [one] if len(one) <= WIDTH else [f"{rank:>2}  CUT {cut}", f"    ADD {add}   {tail}"]
    if forced and swap.get("reason"):
        lines += _wrap("forced: " + swap["reason"], indent=4, hang=8)
    text = swap.get("evidence_add") or "no deck data for this card"
    lines += _with_tail(text + ";", "fills: " + ", ".join(swap["fills"]), 4) if swap.get("fills") else \
        _wrap(text, indent=4, hang=0)
    if verbose:
        if swap.get("evidence_cut"):
            lines += _wrap("cut: " + swap["evidence_cut"], indent=4, hang=5)
        if swap.get("reason") and not forced:
            lines += _wrap("why: " + swap["reason"], indent=4, hang=5)
    return lines


def _roles_change_line(before, after):
    cells = []
    for key in ROLE_KEYS:
        b, a = before.get(key, 0), after.get(key, 0)
        if key == "land" or b != a:
            cells.append(f"{LABELS[key]} {b}→{a}")
    return _pack("Roles: ", cells)


def _still_off_target(counts, targets):
    """Roles outside their range after the change, so a swap list never hides a deck that is still short."""
    out = []
    for key in ROLE_KEYS:
        have, target = counts.get(key), targets.get(key)
        if have is None or not target or role_status(have, target) == "ok":
            continue
        out.append(f"{LABELS[key]} {have} (want {_range(target)})")
    return _pack("Still off target: ", out, hang=4) if out else []


def _rep(v):
    """A brackets.check report, or the bare number a caller may have stored instead."""
    return v if isinstance(v, dict) else {"bracket": v}


def _floor(rep):
    return rep.get("estimated") if rep.get("estimated") is not None else rep.get("bracket")


def _ok_text(rep):
    if "ok" not in rep:
        return ""
    return " (ok)" if rep["ok"] else f" ({_plural(len(rep.get('violations') or []), 'problem')})"


def _limits_state(rep):
    if "ok" not in rep:                    # a bare estimate instead of a full report
        return f"estimated {_floor(rep)}" if _floor(rep) is not None else "not checked"
    return "met" if rep["ok"] else _plural(len(rep.get("violations") or []), "problem")


def _bracket_move(result):
    """'Bracket 3 limits: met before → met after; Game Changers 0 → 1 of 3'. The estimated bracket is only a
    floor (Wizards weighs intent too), so it is mentioned as such rather than printed as the deck's bracket."""
    before, after, target = _rep(result.get("bracket_before")), _rep(result.get("bracket_after")), _bn(result)
    line = f"Bracket {target} limits: {_limits_state(before)} before → {_limits_state(after)} after"
    if "game_changers" in before or "game_changers" in after:
        cap = after.get("gc_max", before.get("gc_max"))
        line += (f"; Game Changers {len(before.get('game_changers') or [])} → "
                 f"{len(after.get('game_changers') or [])}" + (f" of {cap}" if cap is not None else ""))
    floor = _floor(after)
    if after.get("ok") and isinstance(floor, int) and isinstance(target, int) and floor < target:
        line += f" (the new list also meets Bracket {floor}'s limits)"
    lines = _wrap(line, hang=4)
    if after.get("violations"):
        lines += ["  Still over the limit:"] + _problem_lines(after["violations"], indent=4)
    return lines


def upgrade_report(result, verbose=False):
    deck = result.get("deck") or {}
    lines = _head(deck.get("name") or "Deck", result) + [_deck_line(deck)]
    swaps = result.get("swaps") or []
    if swaps:
        lines.append("")
        for i, swap in enumerate(swaps, 1):
            lines += _swap_lines(swap.get("rank") or i, swap, verbose)
    else:
        lines += ["", f"No swaps: nothing available improves this deck within the budget and the Bracket "
                      f"{_bn(result)} rules."]
    blocked = _blocked_lines(result.get("blocked"))
    lines += [""] + blocked if blocked else []
    cheap = result.get("cheap_adds") or []
    if cheap:
        lines += ["", "Cheapest useful adds:"]
        lines += [f"  {c.get('card')}  {_gain(c.get('gain'))}  {_money(c.get('price'))}" for c in cheap]
    before, after = result.get("roles_before"), result.get("roles_after")
    if before and after:
        lines += [""] + _roles_change_line(before, after)
        lines += _still_off_target(after, result.get("targets") or {})
    if result.get("value_before") is not None:
        lines += _value_change(result["value_before"], result.get("value_after"))
    if result.get("bracket_before") is not None or result.get("bracket_after") is not None:
        lines += _bracket_move(result)
    lines += _out_line(result)
    return _done(lines + _footer(result) + _warnings(result))


# ---------------------------------------------------------------- build
def _card_row(card):
    name = card.get("name") or "?"
    score = f"{card['score']:>5.2f}" if card.get("score") is not None else " " * 5
    price = _money(0.0 if card.get("owned") else card.get("price"))
    tail = ", ".join((["owned"] if card.get("owned") else []) + list(card.get("roles") or []))
    return f"  {name:<{max(44, len(name) + 2)}}{score}{price:>9}" + (f"  {tail}" if tail else "")


def _percent(p):
    """A percent number (5.9) as text: '6%', or '<1%' for a sliver that would round to nothing."""
    return "?" if p is None else "<1%" if 0 < p < 0.5 else f"{p:.0f}%"


def _fantasy_cost_lines(cost):
    if not cost:
        return []
    gap, top = cost.get("gap") or 0, cost.get("power_max")
    share = cost.get("gap_pct")                   # percent of the strongest deck's card quality, as a number
    if share is None and top:
        share = 100.0 * gap / top
    if gap <= 0:
        lines = ["Fantasy cost: the theme costs nothing; the themed build is as strong as the pure-power build."]
    else:
        lines = [f"Fantasy cost: The theme costs {gap:.1f} points of strength ({_percent(share)})."]
        if cost.get("power_with_theme") is not None and top is not None:
            lines.append(f"  Strength {cost['power_with_theme']:.1f} with the theme, {top:.1f} without it.")
    left = cost.get("left_out") or []
    if left:
        shown = ", ".join(f"{c.get('name')} ({c.get('score') or 0:.2f})" for c in left[:6])
        lines += _wrap(f"Left out: {shown}.", indent=2, hang=4)
    picks = cost.get("theme_picks") or []
    if picks:
        shown = ", ".join(f"{p.get('name')} ({p.get('theme')})" for p in picks[:8])
        lines += _wrap(f"Theme picks: {shown}.", indent=2, hang=4)
    return lines


def build_report(result, verbose=False):
    commanders = result.get("commanders") or []
    cards = [c for c in result.get("cards") or [] if c.get("name") not in commanders]
    basics = {k: v for k, v in (result.get("basics") or {}).items() if v}
    owned = sum(1 for c in cards if c.get("owned"))
    name = f"{' + '.join(commanders) or 'Deck'} ({_ci(result.get('ci'))})"
    lines = _head(name, result) + [f"{len(cards) + sum(basics.values())} cards plus the commander"
                                   f"{'s' if len(commanders) > 1 else ''}"]
    top = {id(c) for c in sorted(cards, key=lambda c: -(c.get("score") or 0))[:TOP_EVIDENCE]}
    groups = {}
    for c in cards:
        groups.setdefault(c.get("section") or "Other", []).append(c)
    unknown = sorted(set(groups) - set(SECTIONS))           # a section this module does not know still prints
    for section in [s for s in SECTIONS if s in groups or (s == "Lands" and basics)] + unknown:
        group = groups.get(section, [])                     # the engine's order: strongest first
        extra = sum(basics.values()) if section == "Lands" else 0
        lines += ["", f"{section} ({len(group) + extra})"]
        for c in group:
            lines.append(_card_row(c))
            if c.get("evidence") and (verbose or id(c) in top):
                lines += _wrap(c["evidence"], indent=4, hang=0)
        if section == "Lands" and basics:
            ordered = sorted(basics.items(), key=lambda kv: (-kv[1], kv[0]))
            lines += _wrap("Basics: " + ", ".join(f"{k} {v}" for k, v in ordered), indent=2, hang=4)
    if result.get("roles"):
        lines += [""] + _pack("Roles: ", _role_cells(result["roles"], result.get("targets") or {}))
    spent = f"Spent {_money(result.get('spent'))}" if result.get("spent") is not None else ""
    if spent:
        spent += f" of {_budget(result['budget'])}" if result.get("budget") is not None else ""
        spent += f"; {owned} of the cards are ones you own" if owned else ""
        lines += [spent]
    lines += _value_line(result["value"]) if result.get("value") is not None else []
    cost = _fantasy_cost_lines(result.get("fantasy_cost"))
    lines += [""] + cost if cost else []
    report = _check_report(result)
    if report:
        lines += [""] + _bracket_summary(report, _bn(result))
    blocked = _blocked_lines(result.get("blocked"))
    lines += [""] + blocked if blocked else []
    lines += _out_line(result)
    return _done(lines + _footer(result) + _warnings(result))


# ---------------------------------------------------------------- suggest
def _suggest_facts(c):
    """Evidence lines built from the structured fields, for a result whose commander has no `evidence` strings."""
    out = []
    for theme, share in (c.get("theme_share") or {}).items():
        decks, of = share.get("decks"), share.get("of")
        out.append(f"{theme}: {_num(decks)} of {_num(of)} decks ({_pct(share.get('share'))})")
    if c.get("bracket_decks") is not None:
        out.append(f"{_num(c['bracket_decks'])} decks at this bracket")
    if c.get("salt") is not None:
        out.append(f"salt {c['salt']:.1f} of 4")
    tour = c.get("tournament")
    if tour:
        out.append(f"{_num(tour.get('entries'))} tournament entries, {_pct(tour.get('conversion'))} reach the top cut")
    if c.get("core_cost") is not None:
        out.append(f"core cards cost about {_money(c['core_cost'])}")
    if c.get("owned_share") is not None:
        out.append(f"you own {_pct(c['owned_share'])} of them")
    return out


def suggest_report(result, verbose=False):
    spec = result.get("spec") or {}
    flt = result.get("filters") or {}
    asks = ", ".join(spec.get("themes") or []) or "any theme"
    scope = [f"Bracket {_bn(result)}"]
    if flt.get("colors"):
        scope.append(f"colors {flt['colors']}")
    if flt.get("budget") is not None:
        scope.append(f"budget {_budget(flt['budget'])}")
    lines = [f"Commanders for {asks}; playstyle: {spec.get('playstyle') or 'value'} ({', '.join(scope)})"]
    found = result.get("commanders") or []
    if not found:
        lines += ["", "No commander matched. Try fewer themes, other colors, or a larger budget."]
    for i, c in enumerate(found, 1):
        score = f"   score {c['score']:.2f}" if c.get("score") is not None else ""
        lines += ["", f"{c.get('rank') or i:>2}  {c.get('name')} ({_ci(c.get('ci'))}){score}"]
        for line in c.get("evidence") or _suggest_facts(c):
            lines += _wrap(line, indent=6, hang=0)
    return _done(lines + _footer(result) + _warnings(result))


# ---------------------------------------------------------------- themes
def themes_report(result, verbose=False):
    lines = ["Playstyles (choose one with --playstyle)"]
    for p in result.get("playstyles") or []:
        need = f" (Bracket {p['min_bracket']} and up)" if (p.get("min_bracket") or 1) > 1 else ""
        lines += _hang(f"  {p.get('slug', ''):<14}{p.get('label', ''):<14}", (p.get("description") or "") + need)
    who = result.get("commander")
    lines += ["", f"Themes for {who} (choose with --theme)" if who else
              "Common themes (choose with --theme; `themes --commander NAME` lists a commander's own)"]
    themes = result.get("themes") or []
    for t in themes[:MAX_THEMES]:
        count = f"{t['count']:>8,}" if t.get("count") is not None else ""
        lines.append(f"  {t.get('slug', ''):<28}{t.get('label', ''):<26}{count}".rstrip())
    if len(themes) > MAX_THEMES:
        lines.append(f"  and {len(themes) - MAX_THEMES} more (--json lists them all)")
    return _done(lines + _warnings(result) + _footer(result, evidence=False))


# ---------------------------------------------------------------- warm
def warm_report(result, verbose=False):
    names = " + ".join(result.get("commanders") or []) or "?"
    themes = ", ".join(result.get("themes") or [])
    lines = [f"Downloaded for {names} at Bracket {_bn(result)}" + (f"; themes: {themes}" if themes else ""), ""]
    rows = result.get("fetched") or []
    if not rows:
        return _done(lines + ["Nothing was downloaded."] + _warnings(result))
    lines.append(f"  {'SOURCE':<14}{'CACHE':<9}{'FETCHED':<12}WHAT")
    for r in rows:
        lines += _hang(f"  {r.get('source', ''):<14}{r.get('cache') or '':<9}{_day(r.get('fetched')) or '-':<12}",
                       r.get("what") or "")
    lines += [""] + _wrap("fresh = already cached and in date; network = downloaded now; stale = an old copy, "
                          "because the site could not be reached; ok = in the cache, with no date to show.")
    return _done(lines + _warnings(result))


# ---------------------------------------------------------------- validate
def _scalar(v):
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.3g}"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, (list, tuple)):
        return ", ".join(_scalar(x) for x in v)
    return str(v)


def _table(rows, indent):
    """A plain table of dicts that share keys (at most six columns), numbers right-aligned."""
    keys = list(rows[0])[:6]
    cells = [[_scalar(r.get(k)) for k in keys] for r in rows]
    widths = [max(len(k), *(len(row[i]) for row in cells)) for i, k in enumerate(keys)]
    pad = " " * indent
    numeric = [all(isinstance(r.get(k), (int, float)) for r in rows) for k in keys]
    head = "  ".join(k.upper().rjust(w) if n else k.upper().ljust(w) for k, w, n in zip(keys, widths, numeric))
    body = ["  ".join(c.rjust(w) if n else c.ljust(w) for c, w, n in zip(row, widths, numeric)) for row in cells]
    return [pad + head.rstrip()] + [pad + row.rstrip() for row in body]


def _plain(value, indent=2):
    """Lines for a free-form value (the sweep and calibration blocks of `validate` have no fixed layout)."""
    pad = " " * indent
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            if isinstance(v, (dict, list)) and v and not (isinstance(v, list) and not isinstance(v[0], dict)):
                out += [f"{pad}{k}:"] + _plain(v, indent + 2)
            else:
                out.append(f"{pad}{k}: {_scalar(v)}")
        return out
    if isinstance(value, list) and value and all(isinstance(x, dict) for x in value):
        return _table(value, indent)
    return [f"{pad}{_scalar(value)}"]


def _pct1(x):
    """41.3% (one decimal: the weights of a sweep differ by less than a point)."""
    return "?" if x is None else f"{x * 100:.1f}%"


def _sweep_lines(rows):
    """The Bracket 5 weight sweep as a table of mean overlap per pair of weights; any other layout of rows is
    printed as the free-form block it is."""
    if not all("w_bracket" in r and "k_resid" in r for r in rows):
        return ["", "Weight sweep:"] + _plain(rows)
    lines = ["", "Weight sweep (mean overlap for each W_BRACKET[5] and K_RESID):",
             f"  {'W_BRACKET':>9}{'K_RESID':>9}{'OVERLAP':>9}{'DECKS':>7}"]
    return lines + [f"  {_scalar(r['w_bracket']):>9}{_scalar(r['k_resid']):>9}{_pct1(r.get('overlap')):>9}"
                    f"{_num(r.get('decks')):>7}" for r in rows]


def _calibration_lines(report):
    """A calibrate.run report in a few lines: how each bracket's numbers came about, which numbers moved, and
    where the file went. Anything else under "calibration" is printed as the free-form block it is."""
    if not (isinstance(report.get("labels"), dict) and isinstance(report.get("changes"), list)):
        return ["", "Calibration:"] + _plain(report)
    wrote = f"wrote {report['written']}" if report.get("written") else "nothing written"
    lines = ["", f"Calibration ({wrote}):"]
    for bracket, label in sorted(report["labels"].items(), key=lambda kv: int(kv[0])):
        lines += _wrap(f"Bracket {bracket}: {label}", indent=2, hang=4)
    changes = report["changes"]
    lines.append(f"  {_plural(len(changes), 'role number')} changed" + (":" if changes else "."))
    lines += [f"    {change}" for change in changes[:MAX_CHANGES]]
    if len(changes) > MAX_CHANGES:
        lines.append(f"    and {len(changes) - MAX_CHANGES} more")
    return lines


def _upgrade_check_lines(check):
    """The Bracket 3 upgrade check: how many recent precons ended nearer the role targets, and the money."""
    n = check.get("precons") or 0
    parts = [f"{check.get('closer') or 0} of {_plural(n, 'precon')} ended nearer the role targets"]
    parts += [f"{check[key]} {word}" for key, word in (("same", "unchanged"), ("farther", "farther"))
              if check.get(key)]
    spend = ("every spend stayed within the budget" if check.get("within_budget")
             else "over budget: " + ", ".join(check.get("over_budget") or []))
    budget = _budget(check["budget"]) if check.get("budget") is not None else "none"
    lines = [""] + _wrap(f"Upgrade check at Bracket {check.get('bracket', '?')} (budget {budget}): "
                         f"{', '.join(parts)}; {spend}.")
    rows = check.get("rows") or []
    if rows:
        name = min(max([len("PRECON")] + [len(r.get("precon", "")) for r in rows]), WIDTH - 37)   # the numbers take 35
        lines.append(f"  {'PRECON':<{name}}{'GAP BEFORE':>11}{'AFTER':>7}{'SPENT':>10}{'SWAPS':>7}")
        lines += [f"  {r.get('precon', ''):<{name}}{_num(r.get('gap_before')):>11}{_num(r.get('gap_after')):>7}"
                  f"{_money(r.get('spent')):>10}{_num(r.get('swaps')):>7}" for r in rows]
        lines += _wrap("Gap counts the cards short of a role's minimum or over its maximum, added up; 0 means "
                       "every role is inside its band.", indent=2, hang=0)
    return lines


def validate_report(result, verbose=False):
    lines = [f"Validation at Bracket {_bn(result)}: {result.get('method') or 'method not stated'}"]
    rows = result.get("commanders") or []
    if rows:
        name = min(max([34] + [len(r.get("name", "")) for r in rows]), WIDTH - 27)   # a partner pair is long
        lines += ["", f"  {'COMMANDER':<{name}}{'DECKS':>6}{'OVERLAP':>9}{'BASELINE':>10}"]
        lines += [f"  {r.get('name', ''):<{name}}{_num(r.get('decks')):>6}{_pct(r.get('overlap')):>9}"
                  f"{_pct(r.get('baseline')):>10}" for r in rows]
    overall = result.get("overall") or {}
    if overall and overall.get("overlap") is None:
        lines += ["", "Overall: no real deck was compared (see the warnings)."]
    elif overall:
        lines += ["", f"Overall: overlap {_pct(overall.get('overlap'))} against a baseline of "
                      f"{_pct(overall.get('baseline'))} (n = {_num(overall.get('n'))})"]
        lines += _wrap("Overlap is how much of a real list the build reproduces; the baseline is what the "
                       "most-played cards alone reproduce.", indent=2, hang=0)
    iqr = result.get("roles_in_iqr")
    if iqr is not None:
        if isinstance(iqr, dict):
            per_role = {k: _pct(v) for k, v in iqr.items()}
            lines += ["", "Role counts inside the middle half of real lists:"] + _plain(per_role)
        else:
            lines += ["", f"Role counts inside the middle half of real lists: {_pct(iqr)}"]
    if result.get("bracket_ok_rate") is not None:
        lines.append(f"Builds that follow the Bracket rules: {_pct(result['bracket_ok_rate'])}")
    if result.get("upgrade_check"):
        lines += _upgrade_check_lines(result["upgrade_check"])
    if result.get("sweep"):
        lines += _sweep_lines(result["sweep"])
    if result.get("calibration"):
        lines += _calibration_lines(result["calibration"])
    return _done(lines + _warnings(result) + _footer(result, evidence=False))


# ---------------------------------------------------------------- dispatch
REPORTS = {"check": check_report, "upgrade": upgrade_report, "build": build_report, "suggest": suggest_report,
           "themes": themes_report, "warm": warm_report, "validate": validate_report}


def text(result, verbose=None):
    """The report for a result, chosen by result["command"]. `verbose` (default: the result's own "verbose"
    key) adds evidence to every card instead of the top ones."""
    report = REPORTS.get(result.get("command"))
    if report is None:
        raise ValueError(f"no report for command {result.get('command')!r}")
    return report(result, verbose=bool(result.get("verbose") if verbose is None else verbose))
