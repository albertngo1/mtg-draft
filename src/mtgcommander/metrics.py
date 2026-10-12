"""Deck metrics: every number the `stats` command (and, later, the deck pages) shows about one deck, in one shape.

Why one shape: the pages must draw any metric without code of their own, so every number is an *item*

    {"id": "removal_power", "label": "Removal power", "value": 6.1, "unit": None,
     "target": {"min": 5.0, "target": 8.0, "max": 12.0} | None, "status": "short" | "inside" | "over" | None,
     "why": ["Assassin's Trophy 0.90 = instant 1.0 × any permanent 1.0 × destroy 0.9 × MV 2 1.0", ...],
     "cards": ["Assassin's Trophy", ...], "base": 7.8}          # "base" only when a base deck was given

`value` is None when the number cannot be had (no tag data, no combo data); `why` then says what is missing, and
the number is never guessed. `unit` is "%", "$" or None. `target` is the bracket's band for the number; any of
its three parts is None when the band has no such end. `status` says where `value` sits in the band.

The items sit in groups, a registry of (id, label, applies, compute) in GROUPS, so a new metric is one more item in
one function and the pages need no change:

    power         score, the bracket and its floor, Game Changers, combos, tutors
    interaction   removal power, wipe power, answers to each kind of threat, counterspells, protection
    mana          lands, ramp and draw by kind, the curve, colors, basics, lands that enter tapped
    playstyle     theme fit, how much of each playstyle the deck is, synergy with the commander
    win           finishers by kind, combos that win, hard-to-block creatures
    table         salt, the bracket's limits, price and what you own
    changes       cards added and cut against the base deck (only when a base deck is given)

`compute` is plain arithmetic on what `build.prepare` already gathered, so a call takes a few milliseconds and the
deck pages can run it after every tap. Prices, owned cards, tags and combos come in through arguments, so tests
need no network.

Removal power is this module's own measure (the design's "Metrics" section). Each removal card is worth

    speed × reach × permanence × cost, times 1.5 if it removes again and again,

with the weights below. They are judgment calls, printed in each card's `why` line so the number can be checked."""
import collections, os
from . import brackets, build, config, fantasy, net, roles, score

SCHEMA = 1

# ---------------------------------------------------------------- removal power: the weights
# speed: when the removal can be used. A repeatable ability can be used at any time, except a planeswalker's, which
# only works on your own turn like a sorcery.
SPEED_WEIGHTS = {"instant": 1.0, "repeatable ability": 1.0, "sorcery speed": 0.75}
# reach: what it can hit. "Conditional" is removal with a limit on its target (toughness, "nonblack", damage).
REACH_WEIGHTS = {"any permanent": 1.0, "creatures and planeswalkers": 0.8, "creatures only": 0.7,
                 "one kind of permanent": 0.6, "conditional": 0.6}
CONDITIONAL_TAGS = {"removal-toughness", "doom-blade", "removal-burn"}
# permanence: how well the target stays gone
PERMANENCE_WEIGHTS = {"exile": 1.0, "destroy": 0.9, "damage or -X/-X": 0.8, "bounce": 0.5}
# cost: (the highest mana value, weight); a dearer card is worth COST_DEAR
COST_WEIGHTS = ((2, 1.0), (3, 0.9), (4, 0.8))
COST_DEAR = 0.65
REPEATABLE_WEIGHT = 1.5      # removal that works again and again
ONE_SIDED_WEIGHT = 1.5       # a board wipe that spares your own side (wipe power only)

# ---------------------------------------------------------------- playstyle profile
# The playstyle profile has one entry for each playstyle in commander/playstyles.json: a sentence for what counts,
# and the signals. A signal is (kind, key, weight): ("tag", slug) is a Scryfall function tag of roles.ATTRIBUTE_TAGS,
# ("role", name) a role of roles.ROLES, ("type", name) a card type, ("cost", n) a mana value of n or more. A nonland
# card counts once, at the highest weight of the signals it matches; a playstyle's density is the weights added up
# over the nonland cards. Every line here is a judgment about which cards say "this deck plays that way".
PLAYSTYLE_SIGNALS = {
    # attack and push damage through: cards that are hard to block, extra combat phases, mass pumps
    "combat": ("cards that are hard to block, extra combat phases and mass pumps",
               (("tag", "evasion", 1.0), ("tag", "extra-combat-phase", 1.0), ("tag", "overrun", 1.0))),
    # one big protected threat: Equipment and Aura support
    "voltron": ("Equipment and Aura support",
                (("tag", "synergy-equipment", 1.0), ("tag", "synergy-aura", 1.0))),
    # many small creatures: cards that make creature tokens again and again
    "go-wide": ("cards that keep making tokens", (("tag", "repeatable-token-generator", 1.0),)),
    # sacrifice for value: outlets (a free one is better, so it counts 1.5) and death triggers
    "aristocrats": ("sacrifice outlets (a free one counts 1.5) and death triggers",
                    (("tag", "sacrifice-outlet", 1.0), ("tag", "free-sacrifice-outlet", 1.5),
                     ("tag", "death-trigger", 1.0))),
    # many instants and sorceries: the card types themselves
    "spellslinger": ("instants and sorceries", (("type", "Instant", 1.0), ("type", "Sorcery", 1.0))),
    # answer everything: the three kinds of interaction a deck can hold in numbers
    "control": ("removal, board wipes and counterspells",
                (("role", "removal", 1.0), ("role", "wipe", 1.0), ("role", "counter", 1.0))),
    # assemble a win: tutors to find the pieces, and cards that win by themselves
    "combo": ("tutors and cards that win on their own",
              (("role", "tutor", 1.0), ("tag", "alternate-win-condition", 1.0))),
    # ramp into oversized cards: the ramp role, and cards that cost 6 or more
    "big-mana": ("ramp and cards that cost 6 or more", (("role", "ramp", 1.0), ("cost", 6, 1.0))),
    # fill the graveyard and play from it: fuel, cards that count it, and recursion
    "graveyard": ("cards that fill the graveyard, count it or bring cards back",
                  (("tag", "graveyard-fuel", 1.0), ("tag", "cards-in-graveyard-matter", 1.0),
                   ("role", "recursion", 1.0))),
    # steer the table: gifts to everyone, votes, the monarch
    "politics": ("group hug, voting and monarch cards",
                 (("tag", "group-hug", 1.0), ("tag", "voting", 1.0), ("tag", "monarch-matters", 1.0))),
    # restrict opponents: taxes, lock pieces, small creatures that hinder
    "stax": ("cards that tax or lock down what opponents can do",
             (("tag", "tax", 1.0), ("tag", "lockdown", 1.0), ("tag", "hatebear", 1.0))),
    # steady advantage: card draw that keeps paying
    "value": ("card draw that keeps paying", (("tag", "draw-engine", 1.0), ("tag", "repeatable-impulsive-draw", 1.0))),
}

# ---------------------------------------------------------------- reading the data
COLOR_NAMES = {"W": "white", "U": "blue", "B": "black", "R": "red", "G": "green"}
MAX_LISTED = 10              # names or lines listed for an item that could hold hundreds (combos, cards to buy)
CURVE_TOP = 7                # the curve ends with "7 or more"
# A combo wins when one of its results ends the game for the opponents: the game is won or lost, or damage or life
# loss that never ends ("Near-infinite damage" contains "infinite damage", so it counts too). Damage to creatures
# only does not reach players, and "You can't lose the game" protects, not wins. Spellbook words its results in
# plain English; these words were checked against the 1,101 result names in its 2026-10-11 file.
WINNING_WORDS = ("win the game", "loses the game", "lose the game", "infinite damage", "infinite combat damage",
                 "infinite lifeloss")
NOT_WINNING_ENDS = (" to creatures", " to all creatures", " to some creatures", " to most creatures")
NOT_WINNING_WORDS = ("can't lose the game", "unable to lose the game")
SOURCE_WORDS = {"suggested": "suggested by the tool", "manual": "picked by hand"}
NO_TAGS = "Scryfall's function tags for card attributes are not available (offline, and no earlier run saved them)."
NO_COMBOS = "Combos were not checked: no Commander Spellbook data was available."

TARGETS_PATH = os.path.join(config.COMMITTED, "metric_targets.json")


def targets(bracket):
    """{"removal_power": {"min", "target", "max"}, "wipe_power": {...}} for a bracket, from
    commander/metric_targets.json (written by calibrate.py); {} when the file is missing or damaged, in which
    case those two items carry no band."""
    data = net.read_json(TARGETS_PATH)
    rows = data.get("brackets") if isinstance(data, dict) else None
    row = rows.get(str(min(max(int(bracket), 1), 5))) if isinstance(rows, dict) else None
    if not isinstance(row, dict):
        return {}
    return {name: {"min": v[0], "target": v[1], "max": v[2]} for name, v in row.items()
            if isinstance(v, list) and len(v) == 3}


# ---------------------------------------------------------------- removal power
def _is_instant_speed(rec):
    return "Instant" in rec["types"] or "flash" in {k.lower() for k in rec["keywords"]}


def removal_kind(rec, attrs):
    """The words for each factor of a removal card's quality: {"speed", "reach", "permanence", "cost" ("MV 2"),
    "repeatable" (bool)}. `attrs` is the card's set of roles.ATTRIBUTE_TAGS slugs."""
    attrs = frozenset(attrs)
    repeatable = "repeatable-removal" in attrs
    if _is_instant_speed(rec):
        speed = "instant"
    elif repeatable and "Planeswalker" not in rec["types"]:
        speed = "repeatable ability"
    else:
        speed = "sorcery speed"
    if "removal-permanent" in attrs or "removal-nonland" in attrs:
        reach = "any permanent"
    elif "removal-creature" in attrs and "removal-planeswalker" in attrs:
        reach = "creatures and planeswalkers"
    elif "removal-creature" in attrs:
        reach = "creatures only"
    else:
        reach = "one kind of permanent"
    if CONDITIONAL_TAGS & attrs:
        reach = "conditional"
    if "removal-exile" in attrs:
        permanence = "exile"
    elif "removal-destroy" in attrs:
        permanence = "destroy"
    elif "removal-bounce" in attrs:
        permanence = "bounce"
    else:
        permanence = "damage or -X/-X"
    return {"speed": speed, "reach": reach, "permanence": permanence, "cost": f"MV {rec['cmc']:g}",
            "repeatable": repeatable}


def _cost_weight(mana_value):
    return next((w for top, w in COST_WEIGHTS if mana_value <= top), COST_DEAR)


def removal_quality(rec, attrs):
    """(value, weights) for one removal card: value = speed × reach × permanence × cost × repeatable, and weights
    holds the five numbers it was made of. For example Assassin's Trophy, an instant that destroys any permanent
    for 2 mana, is 1.0 × 1.0 × 0.9 × 1.0 × 1.0 = 0.90. `attrs` is the card's set of roles.ATTRIBUTE_TAGS slugs."""
    kind = removal_kind(rec, attrs)
    weights = {"speed": SPEED_WEIGHTS[kind["speed"]], "reach": REACH_WEIGHTS[kind["reach"]],
               "permanence": PERMANENCE_WEIGHTS[kind["permanence"]], "cost": _cost_weight(rec["cmc"]),
               "repeatable": REPEATABLE_WEIGHT if kind["repeatable"] else 1.0}
    value = 1.0
    for w in weights.values():
        value *= w
    return value, weights


def _weight(w):
    """1.0 → '1.0', 0.65 → '0.65', 1.5 → '1.5': the weights as the design writes them."""
    text = f"{w:.2f}"
    return text[:-1] if text.endswith("0") else text


def _arithmetic(name, rec, attrs, one_sided=False):
    """(value, line): a card's removal value (times ONE_SIDED_WEIGHT for a wipe that spares your side) and the line
    that shows how it was made:
    'Assassin's Trophy 0.90 = instant 1.0 × any permanent 1.0 × destroy 0.9 × MV 2 1.0'."""
    value, weights = removal_quality(rec, attrs)
    kind = removal_kind(rec, attrs)
    parts = [f"{kind[f]} {_weight(weights[f])}" for f in ("speed", "reach", "permanence", "cost")]
    if kind["repeatable"]:
        parts.append(f"repeatable {_weight(REPEATABLE_WEIGHT)}")
    if one_sided:
        value *= ONE_SIDED_WEIGHT
        parts.append(f"one-sided {_weight(ONE_SIDED_WEIGHT)}")
    return value, f"{name} {value:.2f} = " + " × ".join(parts)


def _rate(names, role_map, attrs, db, role):
    """[(name, value, line)] for the cards of `role` ("removal" or "wipe"), strongest first."""
    rows = []
    for name in dict.fromkeys(names):
        rec = db.get(name)
        if rec is not None and role in (role_map.get(name) or role_map.get(rec["name"]) or ()):
            card_attrs = attrs.get(name) or attrs.get(rec["name"]) or frozenset()
            one_sided = role == "wipe" and "sweeper-one-sided" in card_attrs
            value, line = _arithmetic(name, rec, card_attrs, one_sided=one_sided)
            rows.append((name, value, line))
    return sorted(rows, key=lambda row: (-row[1], row[0]))


def rate_removal(names, role_map, attrs, db):
    """[(name, value, line)] for a deck's removal cards, strongest first; the sum is its removal power."""
    return _rate(names, role_map, attrs, db, "removal")


def rate_wipes(names, role_map, attrs, db):
    """The same for its board wipes (a one-sided wipe counts ONE_SIDED_WEIGHT times); the sum is its wipe power."""
    return _rate(names, role_map, attrs, db, "wipe")


# ---------------------------------------------------------------- items
def _band(low=None, target=None, high=None):
    return {"min": low, "target": target, "max": high}


def _status(value, band):
    """'short', 'inside' or 'over' for a value against a band (None when there is no value or no band)."""
    if value is None or not band:
        return None
    low, high = band.get("min"), band.get("max")
    if low is not None and value < low:
        return "short"
    if high is not None and value > high:
        return "over"
    return "inside"


def _item(id_, label, value, *, unit=None, band=None, status=None, why=(), cards=()):
    """One item, in the exact shape the pages read. A band gives the item its status, unless the caller knows
    better (the two-card combo limit is not a count)."""
    return {"id": id_, "label": label, "value": value, "unit": unit, "target": band,
            "status": status or _status(value, band), "why": list(why), "cards": list(cards)}


def _role_band(target):
    """The band of one entry of ctx["targets"]: {"min", "target", "max"}, or only a ceiling for the top end."""
    return _band(target.get("min"), target.get("target"), target.get("max"))


def _missing(id_, label, reason):
    """An item whose number cannot be had, saying why."""
    return _item(id_, label, None, why=[reason])


def _percent(part, whole):
    return round(100.0 * part / whole, 1) if whole else None


def _day(stamp):
    return (stamp or "")[:10]


# ---------------------------------------------------------------- the facts about one deck
class DeckFacts:
    """What the groups read about one deck, worked out once per `compute`: the cards with their records, the
    role counts, the deck value, the bracket report, and which of the optional inputs are present."""

    def __init__(self, ctx, db, cards, commanders, attrs, combos, owned, prices, base, changes, player):
        self.ctx, self.db, self.attrs, self.combos = ctx, db, attrs, combos
        self.base, self.changes, self.player = base, changes, player
        self.role_map, self.role_targets, self.bracket = ctx["role_map"], ctx["targets"], ctx["bracket"]
        self.owned = {db.resolve(n) or n for n in owned}
        self.prices = prices or {}
        self.commanders = [db.resolve(c) or c for c in commanders]
        self.names = []                           # canonical, one entry for each copy
        for item in cards:
            count, name = item if isinstance(item, (tuple, list)) else (1, item)
            rec = db.get(name)
            if rec is not None:
                self.names += [rec["name"]] * count
        self.distinct = list(dict.fromkeys(self.names))
        self.copies = [db.get(n) for n in self.names]
        self.nonland = [rec for rec in self.copies if not rec["land"]]
        self.lands = [rec for rec in self.copies if rec["land"]]
        self.value = build.deck_value(self.names, ctx, db)
        self.counts = self.value["roles"]
        self.report = brackets.check(self.commanders, self.names, self.bracket, db, combos=combos)

    def rec(self, name):
        return self.db.get(name)

    def attrs_of(self, name):
        return (self.attrs or {}).get(name) or frozenset()

    def with_tag(self, *slugs):
        """The distinct cards that carry any of the tag slugs."""
        wanted = set(slugs)
        return [n for n in self.distinct if wanted & self.attrs_of(n)]

    def with_role(self, role):
        return [n for n in self.distinct if role in (self.role_map.get(n) or ())]

    def price_of(self, name):
        """What `name` costs: 0 for a basic land, the caller's price or the card index's price, else None."""
        rec = self.db.get(name)
        if rec is None or "Basic" in rec["types"]:
            return 0.0
        found = self.prices.get(rec["name"], self.prices.get(name))
        return rec["price"] if found is None else found

    def is_owned(self, name):
        rec = self.db.get(name)
        return rec is None or "Basic" in rec["types"] or rec["name"] in self.owned

    def role_item(self, id_, label, role, why):
        """A role count against the bracket's band, listing the cards that fill the role."""
        return _item(id_, label, self.counts[role], band=_role_band(self.role_targets[role]), why=[why],
                     cards=self.with_role(role))

    def tag_item(self, id_, label, slugs, why):
        """A count of the cards with any of `slugs`; unavailable without tag data."""
        if self.attrs is None:
            return _missing(id_, label, NO_TAGS)
        names = self.with_tag(*slugs)
        return _item(id_, label, len(names), why=[why], cards=names)


# ---------------------------------------------------------------- group: power
def _combo_line(combo):
    result = ", ".join(combo["produces"][:3]) or "no result listed"
    bracket = f"Bracket {combo['min_bracket']} and up" if combo["min_bracket"] > 1 else "any bracket"
    return f"{' + '.join(combo['cards'])} → {result} ({bracket}; {combo['url']})"


def _power(f):
    value, report = f.value, f.report
    cap = report["gc_max"]
    chosen = f.bracket
    items = [
        _item("score", "Deck score", round(value["total"], 2),
              why=[f"Power {value['power']:.2f} plus theme {value['theme']:.2f}: the card scores, a bonus for "
                   "filling each role and the land count, less a penalty for too many cards costing 6 or more."]),
        _item("score_power", "Score from card power", round(value["power"], 2),
              why=["The deck score without the part that comes from the chosen themes."]),
        _item("score_theme", "Score from theme fit", round(value["theme"], 2),
              why=["How much more builders who chose the same themes play these cards."]),
    ] + _bracket_items(f) + [
        _item("game_changers", "Game Changers", len(report["game_changers"]), band=_band(high=cap),
              why=[f"Bracket {chosen} allows " + ("any number." if cap is None else f"up to {cap}.")],
              cards=report["game_changers"]),
    ]
    items += _combo_items(f)
    items.append(f.role_item("tutors", "Tutors", "tutor", "Cards that search the library for any card."))
    return items


def _bracket_items(f):
    """Two items. `bracket` is the bracket the player chose: "inside" while the deck keeps that bracket's limits,
    "over" with the reasons when it breaks one. `bracket_floor` is the lowest bracket whose limits the deck meets.
    It is only a floor: Brackets 1 and 2 have the same limits (what separates them is intent), so nearly every
    precon reads 1 there, which is why the headline shows the chosen bracket instead."""
    report, chosen = f.report, f.bracket
    unchecked = [n for n in report["notes"] if n.startswith("Combos were not checked")]
    broken = [v["message"] for v in report["violations"]]
    kept = [f"Within Bracket {chosen}'s limits: Game Changers, extra turns, mass land denial and two-card combos."]
    return [_item("bracket", "Bracket", chosen, band=_band(None, chosen, chosen), status="over" if broken else "inside",
                  why=(broken or kept) + unchecked),
            _item("bracket_floor", "Lowest bracket its limits allow", report["estimated"],
                  why=["The lowest bracket whose limits (Game Changers, extra turns, mass land denial, two-card "
                       "combos) the deck meets. Brackets 1 and 2 have the same limits and Wizards says intent "
                       "decides the real bracket, so this is only a floor."] + unchecked)]


def _combo_items(f):
    if f.combos is None:
        return [_missing("combos_in_deck", "Combos in the deck", NO_COMBOS),
                _missing("combos_one_away", "Combos one card away", NO_COMBOS)]
    inside, near = f.combos["included"], f.combos["almost"]
    near = sorted(near, key=lambda c: (not c["two_card"], len(c["cards"]), c["id"]))
    hidden = len(near) - MAX_LISTED
    near_why = [f"Add {' and '.join(c['missing'])} to complete {_combo_line(c)}" for c in near[:MAX_LISTED]]
    if hidden > 0:
        near_why.append(f"and {hidden} more (two-card combos are listed first)")
    wanted = list(dict.fromkeys(m for c in near[:MAX_LISTED] for m in c["missing"]))
    return [_item("combos_in_deck", "Combos in the deck", len(inside),
                  why=[_combo_line(c) for c in inside] or ["No combo from Commander Spellbook is complete here."],
                  cards=list(dict.fromkeys(n for c in inside for n in c["cards"]))),
            _item("combos_one_away", "Combos one card away", len(near), why=near_why or ["No combo is one card away."],
                  cards=wanted)]


# ---------------------------------------------------------------- group: interaction
THREATS = (("answers_creatures", "Answers to creatures", ("removal-creature", "sweeper")),
           ("answers_artifacts", "Answers to artifacts", ("removal-artifact",)),
           ("answers_enchantments", "Answers to enchantments", ("removal-enchantment",)),
           ("answers_planeswalkers", "Answers to planeswalkers", ("removal-planeswalker",)),
           ("answers_lands", "Answers to lands", ("removal-land",)),
           ("answers_graveyards", "Answers to graveyards", ("hate-graveyard",)),
           ("answers_spells", "Answers to spells", ("counterspell",)))
INTERACTION_ROLES = ("removal", "wipe", "counter", "protection")


def _power_item(id_, label, rows, band, role):
    total = round(sum(v for _, v, _ in rows), 2)
    return _item(id_, label, total, band=band, why=[line for _, _, line in rows] or [f"No {role} cards."],
                 cards=[n for n, _, _ in rows])


def _interaction(f):
    if f.attrs is None:
        items = [_missing("removal_power", "Removal power", NO_TAGS), _missing("wipe_power", "Wipe power", NO_TAGS)]
        items += [_missing(id_, label, NO_TAGS) for id_, label, _ in THREATS]
    else:
        bands = targets(f.bracket)
        items = [_power_item("removal_power", "Removal power", rate_removal(f.names, f.role_map, f.attrs, f.db),
                             bands.get("removal_power"), "removal"),
                 _power_item("wipe_power", "Wipe power", rate_wipes(f.names, f.role_map, f.attrs, f.db),
                             bands.get("wipe_power"), "wipe")]
        for id_, label, slugs in THREATS:
            names = f.with_tag(*slugs)
            items.append(_item(id_, label, len(names), band=_band(1), cards=names,
                               why=[f"{len(names)} cards can deal with it" if names else "Nothing in the deck can."]))
    items.append(f.role_item("counterspells", "Counterspells", "counter", "Cards that counter a spell."))
    items.append(f.role_item("protection", "Protection", "protection", "Cards that shield your permanents."))
    items.append(_instant_share(f))
    return items


def _instant_share(f):
    interaction = [n for n in f.distinct if set(INTERACTION_ROLES) & set(f.role_map.get(n) or ())]
    quick = [n for n in interaction if _is_instant_speed(f.rec(n))]
    if not interaction:
        return _missing("instant_share", "Interaction at instant speed", "The deck has no interaction cards.")
    return _item("instant_share", "Interaction at instant speed", _percent(len(quick), len(interaction)), unit="%",
                 why=[f"{len(quick)} of {len(interaction)} removal, wipe, counterspell and protection cards are "
                      "instants or have flash."], cards=quick)


# ---------------------------------------------------------------- group: mana and consistency
def _split_item(f, id_, label, role, slugs, why, exclude=()):
    """Cards of a role that carry one of `slugs` (and none of `exclude`): a way to split ramp or draw by kind."""
    if f.attrs is None:
        return _missing(id_, label, NO_TAGS)
    names = [n for n in f.with_role(role) if set(slugs) & f.attrs_of(n) and not set(exclude) & f.attrs_of(n)]
    return _item(id_, label, len(names), why=[why], cards=names)


def _mana(f):
    items = [
        _item("lands", "Lands", f.counts["land"], band=_role_band(f.role_targets["land"]),
              why=[f"{f.counts['land']} lands, {sum('Basic' in r['types'] for r in f.lands)} of them basic."],
              cards=[n for n in f.distinct if f.rec(n)["land"] and "Basic" not in f.rec(n)["types"]]),
        f.role_item("ramp", "Ramp", "ramp", "Mana rocks, creatures that make mana, spells that fetch lands, and "
                    "lands that make extra mana."),
        _split_item(f, "ramp_rocks", "Mana rocks", "ramp", ("mana-rock",), "Artifacts that make mana."),
        _split_item(f, "ramp_creatures", "Creatures that make mana", "ramp", ("mana-dork",),
                    "Creatures that tap for mana."),
        _split_item(f, "ramp_lands", "Land ramp", "ramp", ("land-ramp", "extra-land"),
                    "Spells that put lands onto the battlefield, and extra land drops."),
        f.role_item("draw", "Card draw", "draw", "Cards that draw cards; a cantrip that only replaces itself "
                    "does not count."),
        _split_item(f, "draw_engines", "Draw engines", "draw", ("draw-engine", "repeatable-impulsive-draw"),
                    "Cards that draw again and again."),
        _split_item(f, "draw_one_shot", "One-shot draw", "draw", ("pure-draw", "burst-draw", "impulsive-draw"),
                    "Cards that draw once; an engine is not counted here.",
                    exclude=("draw-engine", "repeatable-impulsive-draw")),
    ]
    items += _curve_items(f)
    items += _color_items(f)
    items.append(_basics_item(f))
    items += _tapped_items(f)
    items.append(_colorless_item(f))
    top = f.role_targets["topend"]["max"]
    items.append(_item("topend", "Cards costing 6 or more", f.counts["topend"], band=_band(high=top),
                       why=[f"Bracket {f.bracket} allows up to {top} nonland cards costing 6 or more."],
                       cards=[n for n in f.distinct if not f.rec(n)["land"] and f.rec(n)["cmc"] >= 6]))
    return items


def _curve_items(f):
    items = []
    for step in range(CURVE_TOP + 1):
        names = [n for n in f.distinct if not f.rec(n)["land"] and min(int(f.rec(n)["cmc"]), CURVE_TOP) == step]
        count = sum(1 for rec in f.nonland if min(int(rec["cmc"]), CURVE_TOP) == step)
        label = f"Cards with mana value {step}" + (" or more" if step == CURVE_TOP else "")
        items.append(_item(f"curve_{step}", label, count, cards=names,
                           why=["Nonland cards, counting every copy."] if step == 0 else []))
    average = sum(rec["cmc"] for rec in f.nonland) / len(f.nonland) if f.nonland else None
    items.append(_item("avg_mana_value", "Average mana value", None if average is None else round(average, 2),
                       why=["The mean mana value of the nonland cards."]))
    return items


def _color_items(f):
    items = []
    symbols = collections.Counter()
    for rec in f.nonland:
        symbols.update(build._pips(rec, f.ctx["ci"]))
    for color in (c for c in "WUBRG" if c in f.ctx["ci"]):
        sources = sum(1 for rec in f.lands if color in rec["produced_mana"])
        name = COLOR_NAMES[color]
        need = symbols[color]
        why = (f"{sources} lands make {name} mana for {need:g} {name} mana symbols in the nonland cards "
               f"({sources / need:.2f} lands for each symbol)." if need else
               f"{sources} lands make {name} mana; no nonland card needs it.")
        items.append(_item(f"sources_{name}", f"{name.title()} sources", sources, why=[why]))
    return items


def _basics_item(f):
    """Basic lands against what the deck's land searchers can take. Cultivate and Evolving Wilds find nothing when
    the deck holds no basic land, so the deck needs as many basics as its searchers can take, and at least one for
    each of its colors: the floor that build.Plan.basics_ok keeps."""
    colors = [c for c in "WUBRG" if c in f.ctx["ci"]]
    takes = {n: roles.basic_land_searches(f.rec(n)) for n in f.distinct}
    searchers = [(n, k) for n, k in takes.items() if k]
    demand = sum(takes[n] for n in f.names)
    need = max(len(colors), demand)
    have = sum(1 for rec in f.lands if "Basic" in rec["types"])
    taking = ", ".join(f"{n} {k}" for n, k in searchers) or "none"
    return _item("basics", "Basic lands", have, band=_band(need),
                 why=[f"The land searchers can take {demand} basic lands ({taking}) and the deck has "
                      f"{len(colors)} colors; it needs at least {need}."], cards=[n for n, _ in searchers])


def _tapped_items(f):
    if f.attrs is None:
        return [_missing("tapped_always", "Lands that always enter tapped", NO_TAGS),
                _missing("tapped_sometimes", "Lands that sometimes enter tapped", NO_TAGS)]
    sometimes = [n for n in f.with_tag("conditional-tapland") if f.rec(n)["land"]]
    always = [n for n in f.with_tag("tapland") if f.rec(n)["land"] and n not in sometimes]
    return [_item("tapped_always", "Lands that always enter tapped", len(always), cards=always,
                  why=["Scryfall's tag `tapland`: they always enter tapped. A land tagged both ways (The Shire) "
                       "counts as 'sometimes': one that can enter untapped is not always tapped."]),
            _item("tapped_sometimes", "Lands that sometimes enter tapped", len(sometimes), cards=sometimes,
                  why=["Scryfall's tag `conditional-tapland`: shock lands, check lands and the like enter untapped "
                       "when a condition is met."])]


def _colorless_item(f):
    """Lands that make no colored mana. A fetch land or Evolving Wilds makes none either, but it finds a land that
    does, so a land that searches the library for a land is left out."""
    names = [n for n in f.distinct if f.rec(n)["land"] and not set(f.rec(n)["produced_mana"]) & set("WUBRG")
             and not roles.searches_library_for_land(f.rec(n))]
    return _item("colorless_lands", "Lands that make only colorless mana", len(names), cards=names,
                 why=["Lands that cannot make colored mana and do not fetch a land that can."])


# ---------------------------------------------------------------- group: playstyle
def _signal_weight(f, name, rec, rules):
    """The highest weight among the playstyle signals the card matches (0 when it matches none)."""
    held = f.attrs_of(name)
    roles_held = f.role_map.get(name) or ()
    best = 0.0
    for kind, key, weight in rules:
        hit = ((kind == "tag" and key in held) or (kind == "role" and key in roles_held)
               or (kind == "type" and key in rec["types"]) or (kind == "cost" and rec["cmc"] >= key))
        best = max(best, weight if hit else 0.0)
    return best


def _profile_items(f):
    chosen = (f.ctx.get("spec") or {}).get("playstyle")
    nonland = [n for n in f.names if not f.rec(n)["land"]]
    items = []
    for slug, label in _playstyles():
        meaning, rules = PLAYSTYLE_SIGNALS[slug]
        id_ = "style_" + slug.replace("-", "_")
        if f.attrs is None and any(kind == "tag" for kind, _, _ in rules):
            items.append(_missing(id_, label, NO_TAGS))
            continue
        weights = {n: _signal_weight(f, n, f.rec(n), rules) for n in dict.fromkeys(nonland)}
        total = sum(weights[n] for n in nonland)
        names = [n for n, w in weights.items() if w]
        why = [f"Counts {meaning}: {len(names)} of the {len(set(nonland))} different nonland cards."]
        if slug == chosen:
            why.append("This is the playstyle you chose.")
        items.append(_item(id_, label, _percent(total, len(nonland)), unit="%", why=why, cards=names))
    return items


def _playstyles():
    """[(slug, label)] of every playstyle in commander/playstyles.json, in the file's order."""
    return [(p["slug"], p["label"]) for p in fantasy.menu()["playstyles"] if p["slug"] in PLAYSTYLE_SIGNALS]


def _theme_fit(f):
    themes = (f.ctx.get("evidence") or {}).get("theme_weights") or {}
    if not themes:
        return _missing("theme_fit", "Theme fit", "No theme or playstyle was chosen, so there is nothing to fit.")
    names = list(dict.fromkeys(n for n in f.names if not f.rec(n)["land"]))
    fits = [n for n in names if ((f.ctx["scores"].get(n) or {}).get("parts") or {}).get("theme", 0.0) > score.SHOW_PULL]
    return _item("theme_fit", "Theme fit", _percent(len(fits), len(names)), unit="%", cards=fits,
                 why=[f"{len(fits)} of {len(names)} nonland cards have a theme score above {score.SHOW_PULL}, "
                      f"meaning builders of {', '.join(themes)} decks play them more."])


def _synergy(f):
    cards = (f.ctx.get("evidence") or {}).get("cards") or {}
    found = {}
    for name in dict.fromkeys(n for n in f.names if not f.rec(n)["land"]):
        stats = cards.get(name) or {}
        for slot in ("at", "all"):
            value = (stats.get(slot) or {}).get("synergy")
            if value is not None:
                found[name] = value
                break
    if not found:
        return _missing("synergy", "Synergy with the commander",
                        "No card has an EDHREC synergy score (EDHREC is off, or has no page for this commander).")
    best = sorted(found.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    return _item("synergy", "Synergy with the commander", round(100.0 * sum(found.values()) / len(found), 1), unit="%",
                 why=[f"The mean of EDHREC's synergy over {len(found)} nonland cards that have one.",
                      "Highest: " + ", ".join(f"{n} {v:+.0%}" for n, v in best)], cards=[n for n, _ in best])


def _playstyle(f):
    creatures = [n for n in f.distinct if "Creature" in f.rec(n)["types"]]
    count = sum(1 for rec in f.copies if "Creature" in rec["types"])
    return ([_theme_fit(f)] + _profile_items(f)
            + [_item("creatures", "Creatures", count, why=["Cards with the type Creature, counting every copy."],
                     cards=creatures), _synergy(f)])


# ---------------------------------------------------------------- group: win plan
FINISHERS = (("finishers_overrun", "Overrun effects", ("overrun",), "Cards that pump the whole team for a big attack."),
             ("finishers_drain", "Drain and burn", ("drain-life", "burn-player-each", "opponent-loses-life"),
              "Cards that make each opponent lose life."),
             ("finishers_extra_combat", "Extra combat phases", ("extra-combat-phase",),
              "Cards that give another combat phase."),
             ("finishers_alt_win", "Alternate win conditions", ("alternate-win-condition",),
              "Cards that win the game another way."),
             ("finishers_theft", "Mass theft", ("theft-mass",), "Cards that take control of many permanents."))


def ends_the_game(combo):
    """Whether a combo wins the game by itself, by the rule WINNING_WORDS states: one of its results says the game
    is won or lost, or deals or causes damage or life loss that never ends (not damage to creatures only)."""
    for result in combo["produces"]:
        text = result.lower()
        if (any(word in text for word in WINNING_WORDS) and not text.endswith(NOT_WINNING_ENDS)
                and not any(word in text for word in NOT_WINNING_WORDS)):
            return True
    return False


def _numeric_power(rec):
    """A creature's power as a whole number; None when the card has none recorded or it varies ('*', '1+*')."""
    try:
        return int(rec.get("power"))
    except (TypeError, ValueError):
        return None


def _hard_to_block(f):
    if f.attrs is None:
        return [_missing("evasive_creatures", "Creatures that are hard to block", NO_TAGS),
                _missing("evasive_power", "Power of the hard-to-block creatures", NO_TAGS)]
    names = [n for n in f.with_tag("evasion") if "Creature" in f.rec(n)["types"]]
    items = [_item("evasive_creatures", "Creatures that are hard to block", len(names), cards=names,
                   why=["Creatures with Scryfall's tag `evasion`: flying, menace, unblockable and the like."])]
    known = {n: _numeric_power(f.rec(n)) for n in names}
    varying = [n for n, p in known.items() if p is None]
    why = [f"{n} {p}" for n, p in known.items() if p is not None]
    if varying:
        why.append("Power that varies is left out: " + ", ".join(varying) + ".")
    items.append(_item("evasive_power", "Power of the hard-to-block creatures",
                       sum(p for p in known.values() if p is not None), why=why, cards=names))
    return items


def _win(f):
    items = [f.role_item("finishers", "Finishers", "finisher", "Cards that end the game: the sum of the kinds below.")]
    items += [f.tag_item(id_, label, slugs, why) for id_, label, slugs, why in FINISHERS]
    if f.combos is None:
        items.append(_missing("combos_win", "Combos that win", NO_COMBOS))
    else:
        winners = [c for c in f.combos["included"] if ends_the_game(c)]
        items.append(_item("combos_win", "Combos that win", len(winners), why=[_combo_line(c) for c in winners] or
                           ["No complete combo ends the game by itself."],
                           cards=list(dict.fromkeys(n for c in winners for n in c["cards"]))))
    return items + _hard_to_block(f)


# ---------------------------------------------------------------- group: table and money
LIMITS = (("limit_game_changers", "Game Changers", "game_changers"),
          ("limit_extra_turns", "Extra-turn cards", "extra_turns"),
          ("limit_mass_land_denial", "Mass land denial", "mass_land_denial"))


def _limit_ceiling(rule, key):
    """The most cards of a kind a bracket allows (None: any number). Extra turns follow the tool's own reading of
    'no chaining': one is allowed."""
    if key == "game_changers":
        return rule["game_changers_max"]
    if key == "mass_land_denial":
        return None if rule["mass_land_denial"] else 0
    return {"none": 0, "no-chaining": 1}.get(rule["extra_turns"])


def _limit_items(f):
    rule, report = brackets.rules(f.bracket), f.report
    broken = {v["rule"]: v["message"] for v in report["violations"]}
    items = []
    for id_, label, key in LIMITS:
        names = report[key]
        items.append(_item(id_, label, len(names), band=_band(high=_limit_ceiling(rule, key)),
                           why=[broken.get(key) or f"Within Bracket {f.bracket}'s limit."], cards=names))
    if f.combos is None:
        items.append(_missing("limit_two_card_combos", "Two-card combos", NO_COMBOS))
    else:
        pairs = report["two_card_combos"]
        items.append(_item("limit_two_card_combos", "Two-card combos", len(pairs),
                           status="over" if "two_card_combos" in broken else "inside",
                           why=[broken.get("two_card_combos") or f"None is over Bracket {f.bracket}'s limit."],
                           cards=list(dict.fromkeys(n for p in pairs for n in p["cards"]))))
    return items


def _salt(f):
    salt = (f.ctx.get("evidence") or {}).get("salt") or {}
    if not salt:
        return _missing("salt", "Salt", "Salt scores are loaded from EDHREC only at Brackets 1-3 or with --keep-fun.")
    held = sorted(((n, salt[n]) for n in f.distinct if n in salt), key=lambda kv: (-kv[1], kv[0]))
    top = held[:3]
    return _item("salt", "Salt", round(sum(v for _, v in held), 2),
                 why=[f"{n} {v:.1f}" for n, v in top] or ["No card in the deck is on EDHREC's salt list."],
                 cards=[n for n, _ in top])


def _money(f):
    everyone = f.commanders + f.names
    priced = [(n, f.price_of(n)) for n in dict.fromkeys(everyone)]
    unknown = [n for n, p in priced if p is None]
    total = sum(f.price_of(n) or 0.0 for n in everyone)
    to_buy = [(n, p) for n, p in priced if not f.is_owned(n) and p is not None]
    cost = sum(p for n, p in to_buy)
    owned = sum(1 for n in everyone if f.is_owned(n))
    note = [f"{len(unknown)} cards have no price and count as $0: " + ", ".join(unknown[:MAX_LISTED])] if unknown else []
    dearest = sorted(to_buy, key=lambda kv: (-kv[1], kv[0]))[:MAX_LISTED]
    return [_item("price_total", "Total price", round(total, 2), unit="$",
                  why=["Every card at its price, basic lands free, owned or not."] + note),
            _item("price_to_buy", "Cost to buy", round(cost, 2), unit="$", cards=[n for n, _ in dearest],
                  why=[f"{n} ${p:.2f}" for n, p in dearest] or ["Nothing to buy."]),
            _item("owned_share", "Cards you own", _percent(owned, len(everyone)), unit="%",
                  why=[f"{owned} of {len(everyone)} cards, the commander included; basic lands count as owned."])]


def _table(f):
    return [_salt(f)] + _limit_items(f) + _money(f)


# ---------------------------------------------------------------- group: changes from the base deck
def net_changes(changes, db):
    """({card: [note, ...]} added, {card: [note, ...]} cut): the effect of a change log on the base deck, a note
    for each copy. Undone changes are skipped; a group is its items in order; a card added and then cut (or cut and
    then added) cancels out. A note is {"n", "at", "source", "group"} of the change that did it."""
    changes = changes or []
    undone = {c.get("of") for c in changes if c.get("op") == "undo"}
    added, cut = collections.OrderedDict(), collections.OrderedDict()

    def put(books, name, note):
        books.setdefault(db.resolve(name) or name, []).append(note)

    def take(books, name):
        key = db.resolve(name) or name
        if books.get(key):
            books[key].pop()
            return True
        return False

    for change in changes:
        if change.get("op") == "undo" or change.get("n") in undone:
            continue
        for item in change.get("items") or [change]:
            note = {"n": change.get("n"), "at": change.get("at"), "source": change.get("source"),
                    "group": change.get("label") if change.get("op") == "group" else None}
            if item.get("op") in ("cut", "swap") and item.get("cut") and not take(added, item["cut"]):
                put(cut, item["cut"], note)
            if item.get("op") in ("add", "swap") and item.get("add") and not take(cut, item["add"]):
                put(added, item["add"], note)
    return ({k: v for k, v in added.items() if v}, {k: v for k, v in cut.items() if v})


def _change_line(name, notes, player):
    """'Cultivate: change 13, in "Up to $25", 2026-10-11, by andy, suggested by the tool' (a card changed several
    times, like six basic lands, says '× 6' and describes the first change)."""
    first = notes[0]
    bits = [f"change {first['n']}" if first["n"] is not None else "a change"]
    if first["group"]:
        bits.append(f"in \"{first['group']}\"")
    if first["at"]:
        bits.append(_day(first["at"]))
    if player:
        bits.append(f"by {player}")
    bits.append(SOURCE_WORDS.get(first["source"], first["source"] or "no reason recorded"))
    times = f" × {len(notes)}" if len(notes) > 1 else ""
    return f"{name}{times}: " + ", ".join(bits)


def _changes(f):
    if f.changes is None:
        return [_missing(id_, label, "The change log was not given.") for id_, label in (
            ("changes_added", "Cards added"), ("changes_cut", "Cards cut"),
            ("changes_net_cost", "Net cost of the changes"))]
    added, cut = net_changes(f.changes, f.db)
    n_added, n_cut = sum(len(v) for v in added.values()), sum(len(v) for v in cut.values())

    def spent(books):
        """(dollars, cards paid for, cards without a price) over the cards you do not own."""
        pays = [f.price_of(n) for n, notes in books.items() for _ in notes if not f.is_owned(n)]
        return sum(p for p in pays if p is not None), len(pays), sum(1 for p in pays if p is None)
    paid, paid_for, unpriced = spent(added)
    refund, refund_for, unpriced_cut = spent(cut)
    why = [f"Added: ${paid:.2f} for {paid_for} of {n_added} cards (the others are owned or basic lands).",
           f"Cut: ${refund:.2f} for {refund_for} of {n_cut} cards you did not own."]
    if unpriced or unpriced_cut:
        why.append(f"{unpriced + unpriced_cut} cards have no price and count as $0.")
    return [_item("changes_added", "Cards added", n_added,
                  why=[_change_line(n, notes, f.player) for n, notes in added.items()], cards=list(added)),
            _item("changes_cut", "Cards cut", n_cut,
                  why=[_change_line(n, notes, f.player) for n, notes in cut.items()], cards=list(cut)),
            _item("changes_net_cost", "Net cost of the changes", round(paid - refund, 2), unit="$", why=why)]


# ---------------------------------------------------------------- the registry
def _always(f):
    return True


def _has_base(f):
    return f.base is not None


GROUPS = (
    ("power", "Power", _always, _power),
    ("interaction", "Interaction", _always, _interaction),
    ("mana", "Mana and consistency", _always, _mana),
    ("playstyle", "Playstyle", _always, _playstyle),
    ("win", "Win plan", _always, _win),
    ("table", "Table and money", _always, _table),
    ("changes", "Changes from the base deck", _has_base, _changes),
)


def _item_value(groups, id_):
    return next((item["value"] for g in groups for item in g["items"] if item["id"] == id_), None)


def _attach_base(groups, base):
    """Give every item the value it had in the base deck's own result (the page shows before → after). The changes
    group has no 'before'. An item the base lacks, or could not compute, gets no `base`."""
    before = {item["id"]: item["value"] for g in base["groups"] for item in g["items"]}
    for group in groups:
        if group["id"] != "changes":
            for item in group["items"]:
                if before.get(item["id"]) is not None:
                    item["base"] = before[item["id"]]


def compute(ctx, db, cards, *, commanders, attrs=None, combos=None, owned=(), prices=None, base=None, changes=None,
            player=None):
    """Every metric of one deck: {"schema": 1, "headline": {...}, "groups": [{"id", "label", "items": [...]}]}.

    `ctx` is build.prepare's context (the evidence, scores, roles and targets); `cards` the deck without its
    commanders, as names or (count, name) pairs (a name the card index lacks is skipped, as roles.counts skips it).
    `attrs` is roles.attributes(...) of those cards, or None when the tags could not be loaded: the items that need
    them then have no value and say why. `combos` is a spellbook answer ({"included", "almost"}) or None when
    combos were not checked. `owned` are card names that cost $0 to you; `prices` ({name: dollars}) replaces the
    card index's price for a name. `base` is the compute result of the deck this one started from: every item
    (except those of the changes group) then carries its `base` value, and the changes group appears, built from
    `changes`, the version's change log (who made a change is `player`, when the log does not say).

    The headline is what a page pins above everything: the score, the chosen bracket and whether the deck keeps its
    limits (`bracket_ok`), lands, removal power and the price still to pay (None where a number could not be had)."""
    facts = DeckFacts(ctx, db, cards, commanders, attrs, combos, owned, prices, base, changes, player)
    groups = [{"id": id_, "label": label, "items": make(facts)} for id_, label, applies, make in GROUPS
              if applies(facts)]
    if base is not None:
        _attach_base(groups, base)
    headline = {"score": _item_value(groups, "score"), "bracket": _item_value(groups, "bracket"),
                "bracket_ok": not facts.report["violations"], "lands": _item_value(groups, "lands"), "removal_power": _item_value(groups, "removal_power"),
                "price": _item_value(groups, "price_to_buy")}
    return {"schema": SCHEMA, "headline": headline, "groups": groups}
