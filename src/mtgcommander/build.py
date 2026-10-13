"""Deck building: upgrade a list, build one from a commander, suggest commanders.

Why one objective: all three commands ask "what is this deck worth?" and differ only in what they may change.
A deck's value is the sum of its cards' scores (score.py) plus a bonus for having enough of each job (ramp,
draw, removal, ...) and the right number of lands, minus a penalty for too many top-end cards:

    total(D) = sum of score(c) over D's nonbasic cards + sum over roles of R_r(k_r) + L(lands)
               - TOPEND * (top-end cards above the limit)

Role value is a sum of marginal values: the i-th card of a role is worth 1.5*beta up to the bracket's minimum,
beta up to its target, then falls linearly to 0 at its maximum. So a second sweeper is worth less than a
first, and a card that fills a short role beats an equally popular one that does not. A card tagged with m
roles counts 1/sqrt(m) toward each of them (its "role mass"), so a card whose tags pile up earns about
sqrt(m)*beta between them, not m*beta, and between whole cards the role value is linear. A swap's gain is
total(D - cut + add) - total(D), and it is computed from role mass, not by re-scoring the deck, because the
search asks for it tens of thousands of times. Whole-card counts are still kept: they are what the reports,
`fills` and the bracket rules read.

`upgrade` makes forced swaps first (anything that breaks the bracket or the format), then repeats the best
affordable swap above MIN_GAIN, with no limit on how many unless the caller sets one. With a budget it does so
in steps, the price points: each step may spend up to its dollar amount and builds on the one before, so the
report shows what $50 buys on the way to $200. `build` fills the nonland slots greedily, swaps until nothing
improves, then picks lands. Both are local searches, not optima: a swap that needs two cards to change at once
is invisible to them, and each result says what it left out and why.

`upgrade` also keeps a deck's answers. The deck's value counts removal cards but not what each one can hit, so a
long upgrade could trade away the last cards that answer enchantments or planeswalkers. Once the forced swaps are
done, no swap leaves a kind of threat (creatures, artifacts, enchantments, planeswalkers, lands, graveyards, spells)
with fewer answers than a typical deck at the bracket holds (the band's target, the median of real decks), or than
the deck had if it had fewer (see `Plan.keeps_answers`; the numbers come from roles.answer_bands). The result reports
the answers before and after, and for each price point which kinds it has brought down from the starting count to
the typical count or under it: the point used up all of that kind's surplus. `build` keeps no such floor.

Lands get rules of their own, because a basic land scores 0 and so any scored nonbasic land looks like an
upgrade over it. A nonbasic land must score NONBASIC_MIN to take a basic's slot, no swap strips a color of its
lands (MANA_FLOOR), and the deck keeps as many basics as its land searchers can take (Cultivate, Evolving Wilds)
and at least as many as it has colors, split among the colors the way `build` splits basics so a searcher can
still find each one. When two basics are equally good to cut, the one whose color has the most lands per colored
mana symbol goes first.

The fantasy has a price, and `build` reports it: it builds a second deck with the theme weight at 0 and
compares the two under power-only scores.

Everything here works on canonical card names. Prices and combos come in through arguments (`prices`,
`combos_fn`) so tests need no network; the command line passes carddb.cheapest_prices' answer and
providers.spellbook.find_combos."""
import collections, math
from . import brackets, carddb, config, fantasy, net, roles, score
from .providers import edhrec, edhtop16

ROLE_BETA = 0.20          # value of a role card up to its target; 1.5x below its minimum
LAND_BETA = 1.0           # value of each land up to the target: a land is never traded for a spell lightly
MIN_GAIN = 0.02           # a swap must beat this to be worth printing
TOPEND_PENALTY = 0.10     # per nonland card with mana value 6+ above the bracket's limit
NONBASIC_MIN = 0.10       # a nonbasic land needs at least this score to take a slot from a basic
MAX_CANDIDATES = 250      # cards considered as adds, best first
MAX_LAND_CANDIDATES = 80  # nonbasic lands considered by `build`
BUILD_ITERATIONS = 300    # cap on build's swap search
COMBO_ROUNDS = 3          # how often a combo found in the finished list is repaired
MANA_FLOOR = 8            # a swap may not leave a color with fewer lands that make it (or fewer than it had)
LAND_BUDGET_SHARE = 0.10  # share of a build budget held back for nonbasic lands while the spells are chosen
PRICE_LAMBDAS = (0.0, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0)  # value per dollar
PRICE_POINTS_SHOWN = 4    # price points `upgrade` picks for a budget when the caller names none (budget included)
PRICE_POINT_MIN = 10      # dollars: no halved price point is below this (a smaller budget stands alone)
PRICE_POINT_ROUND = 5     # dollars: a halved price point is a multiple of this (the budget itself is as given)
BLOCKED_SHOWN = 5
BLOCKED_MIN_SCORE = 0.15  # a card the rules kept out is only worth naming if builders play it this often
CHEAP_ADDS = 5
THEME_SHOWN = 8           # left-out cards and theme picks listed in the fantasy cost

SUGGEST_CANDIDATES = 30   # commanders examined per suggestion
MIN_THEME_DECKS = 20      # a commander with fewer decks in the named themes has no such deck in practice
SHARE_SHRINK = 100        # decks added to a commander's count before a theme share is taken
PLAYSTYLE_WEIGHT = 0.5
BRACKET_DECKS_WEIGHT = 0.03   # per decimal digit of decks at the bracket
SALT_WEIGHT = 0.05
OWNED_WEIGHT = 0.15
TOURNAMENT_WEIGHT = 0.2
TOURNAMENT_BASELINE = 0.2     # a typical top-cut conversion rate; better than this earns a bonus
TOURNAMENT_MIN = 30           # entries before the conversion rate counts toward the score
TOURNAMENT_CONFIDENT = 100    # entries before it is shown without a "too few" caveat
CORE_INCLUSION = 0.4          # a card in this share of a commander's decks counts as one of its core cards
OWNED_TOP = 60                # owned share is taken over the commander's top nonland cards

BASIC_FOR = {"W": "Plains", "U": "Island", "B": "Swamp", "R": "Mountain", "G": "Forest"}
SECTION_TYPES = (("Creatures", "Creature"), ("Planeswalkers", "Planeswalker"), ("Instants", "Instant"),
                 ("Sorceries", "Sorcery"), ("Artifacts", "Artifact"), ("Enchantments", "Enchantment"),
                 ("Battles", "Battle"), ("Lands", "Land"))
SECTIONS = [s for s, _ in SECTION_TYPES]
STATE_ROLES = roles.ROLES + ("land", "topend")
EPS = 1e-9
LAND_TABLE = 150

# `answers` is the frozenset of threat ids (roles.THREATS) the card can answer; empty unless `upgrade` read the tags.
Facts = collections.namedtuple("Facts", "name score theme roles w land topend gc extra mld sources basic fetch answers")


def _dedupe(lines):
    return list(dict.fromkeys(lines))


def _canonical(names, db, what, warnings):
    """Canonical names for the ones the card index knows; a line of `warnings` for each it does not."""
    out = []
    for raw in names or ():
        rec = db.get(raw)
        if rec is None:
            close = db.suggest(raw)
            warnings.append(f"{what} card '{raw}' was not found" + (f"; did you mean {', '.join(close)}?"
                                                                    if close else ""))
        elif rec["name"] not in out:
            out.append(rec["name"])
    return out


def _drain(*lists):
    """Move the non-fatal lines other modules collect (roles.WARNINGS, carddb.WARNINGS) into one list."""
    out = []
    for lst in lists:
        out += lst
        del lst[:]
    return out


def section_of(rec):
    """Where a card sits in a printed list: its front face's first matching type, lands last."""
    types = set(rec["types"])
    return next((section for section, t in SECTION_TYPES if t in types), "Other")


def _inside(rec, ci):
    return set(rec["ci"]) <= set(ci)


# ----------------------------------------------------------------------------- the context
def prepare(commanders, bracket, spec, db, *, deck_cards=(), owned=(), sources=None, refresh=None,
            offline=None, tournament_signal=None):
    """Gather the evidence, tag the roles and score the cards once; upgrade, build and deck_value share it.

    ctx = {"commanders", "ci", "bracket", "spec", "evidence", "role_map", "scores", "targets", "owned": set,
           "include": [names], "exclude": {names}, "warnings", "sources"}
    `deck_cards` are the names of the list being upgraded (scored in context even when no source lists them);
    `owned` are cards that cost nothing. Scores cover the deck, everything the sources list, the owned cards
    inside the commander's colors and the spec's include list."""
    commanders = [db.resolve(c) or c for c in commanders]
    ev = score.gather(commanders, bracket, spec, db, sources=sources, refresh=refresh, offline=offline,
                      tournament_signal=tournament_signal)
    warnings = list(ev["warnings"])
    ci = ev["ci"]
    held = set(_canonical(owned, db, "owned", warnings))
    held = {n for n in held if _inside(db.get(n), ci)}
    include = _canonical(spec.get("include"), db, "include", warnings)
    exclude = set(_canonical(spec.get("exclude"), db, "exclude", warnings))
    names = [n for n in dict.fromkeys(list(deck_cards) + list(ev["cards"]) + sorted(held) + include)
             if db.get(n) is not None and "Basic" not in db.get(n)["types"]]
    role_map = roles.tag(names, db, refresh=refresh, offline=offline)
    warnings += _drain(roles.WARNINGS)
    scores = score.card_scores(ev, spec, db, role_map, names=names)
    meta = ev.get("meta") or {}
    targets = roles.targets(bracket, spec.get("playstyle") or "value",
                            avg_lands=(meta.get("avg_types") or {}).get("land"), ci=ci)
    return {"commanders": commanders, "ci": ci, "bracket": bracket, "spec": spec, "evidence": ev,
            "role_map": role_map, "scores": scores, "targets": targets, "owned": held, "include": include,
            "exclude": exclude, "warnings": _dedupe(warnings), "sources": ev["sources"]}


# ----------------------------------------------------------------------------- the value of a deck
def role_marginal(i, lo, target, hi):
    """Value of the i-th card (1-based) of a role with minimum `lo`, target and maximum `hi`."""
    if i <= lo:
        return 1.5 * ROLE_BETA
    if i <= target:
        return ROLE_BETA
    if i <= hi:
        return ROLE_BETA * (hi - i + 1) / (hi - target + 1)
    return 0.0


def land_marginal(i, target, hi):
    """Value of the i-th land: full up to the target, then fading to 0 at the maximum, then a small cost."""
    if i <= target:
        return LAND_BETA
    if i <= hi:
        return ROLE_BETA * (hi - i + 1) / (hi - target + 1)
    return -ROLE_BETA


def _cumulative(marginals):
    out = [0.0]
    for m in marginals:
        out.append(out[-1] + m)
    return out


class Model:
    """Per-card facts and the value tables of one ctx, so a swap is priced from role mass alone.

    `counts` (whole cards: roles, "land", "topend") and `mass` ({role: fractional cards}) describe a deck; the
    what-if methods take both. `scores` overrides ctx["scores"] (the fantasy cost re-prices the same decks
    under power-only scores). `answers` is {card name: frozenset of the threat ids it answers}: only `upgrade` gives
    one, from the attribute tags, and without it no card answers anything."""

    def __init__(self, ctx, db, scores=None, answers=None):
        self.db, self.ci = db, ctx["ci"]
        self.scores = ctx["scores"] if scores is None else scores
        self.answers = answers or {}
        self.role_map = ctx["role_map"]
        t = ctx["targets"]
        self.limits = {r: (t[r]["min"], t[r]["target"], t[r]["max"]) for r in roles.ROLES}
        self.role_cum = {r: _cumulative(role_marginal(i, *lim) for i in range(1, lim[2] + 2))
                         for r, lim in self.limits.items()}
        lt, lh = t["land"]["target"], t["land"]["max"]
        self.land_target = lt
        self.land_cum = _cumulative(land_marginal(i, lt, lh) for i in range(1, LAND_TABLE + 1))
        self.topend_max = t["topend"]["max"]
        self._facts = {}

    def facts(self, name):
        found = self._facts.get(name)
        if found is None:
            rec = self.db.get(name)
            if rec is None:
                found = Facts(name, 0.0, 0.0, (), 0.0, False, False, 0, 0, 0, frozenset(), False, 0, frozenset())
            else:
                basic = "Basic" in rec["types"]
                sc = None if basic else self.scores.get(rec["name"])
                lands_for = frozenset(rec["produced_mana"]) & set(self.ci) if rec["land"] else frozenset()
                held = self.role_map.get(rec["name"]) or ()
                its_roles = tuple(r for r in roles.ROLES if r in held)
                found = Facts(rec["name"], sc["score"] if sc else 0.0, sc["parts"]["theme"] if sc else 0.0,
                              its_roles, 1 / math.sqrt(len(its_roles)) if its_roles else 0.0, rec["land"],
                              not rec["land"] and rec["cmc"] >= 6, int(bool(rec["gc"])),
                              int(brackets.is_extra_turn(rec)), int(brackets.is_mass_land_denial(rec)),
                              lands_for, basic, roles.basic_land_searches(rec),
                              self.answers.get(rec["name"], frozenset()))
            self._facts[name] = found
        return found

    # --- cumulative values
    def role_value(self, role, k):
        """R(k): the value of k cards' worth of a role, k a whole number or not. Between whole cards the value
        is linear (half a card earns half of the next card's marginal); past the table it stays flat, because
        the table runs one card beyond the role's maximum, where the marginal is already 0."""
        cum = self.role_cum[role]
        top = len(cum) - 1
        if k <= 0:
            return 0.0
        if k >= top:
            return cum[top]
        whole = int(k)
        return cum[whole] + (k - whole) * (cum[whole + 1] - cum[whole])

    def role_mass(self, facts):
        """{role: mass} of a list of Facts: each card gives 1/sqrt(its roles) to every role it fills."""
        mass = dict.fromkeys(roles.ROLES, 0.0)
        for f in facts:
            for r in f.roles:
                mass[r] += f.w
        return mass

    def land_value(self, k):
        return self.land_cum[max(0, min(k, LAND_TABLE))]

    def land_marginal_at(self, i):
        return self.land_value(i) - self.land_value(i - 1)

    def penalty(self, topend):
        return TOPEND_PENALTY * max(0, topend - self.topend_max)

    def total(self, counts, mass, score_sum):
        value = score_sum + self.land_value(counts["land"]) - self.penalty(counts["topend"])
        return value + sum(self.role_value(r, mass[r]) for r in roles.ROLES)

    # --- what-if (exact: tests compare these with total() before and after)
    def add_value(self, counts, mass, f):
        """Value gained by adding card `f` to a deck holding `counts` and `mass`."""
        v = f.score + sum(self.role_value(r, mass[r] + f.w) - self.role_value(r, mass[r]) for r in f.roles)
        if f.land:
            v += self.land_marginal_at(counts["land"] + 1)
        if f.topend:
            v -= self.penalty(counts["topend"] + 1) - self.penalty(counts["topend"])
        return v

    def cut_value(self, counts, mass, f):
        """Value lost by removing card `f` from a deck holding `counts` and `mass`."""
        v = f.score + sum(self.role_value(r, mass[r]) - self.role_value(r, mass[r] - f.w) for r in f.roles)
        if f.land:
            v += self.land_marginal_at(counts["land"])
        if f.topend:
            v -= self.penalty(counts["topend"]) - self.penalty(counts["topend"] - 1)
        return v

    def overlap(self, counts, mass, cut, add):
        """What add_value - cut_value gets wrong when the two cards share a role: the role moves once, by
        add.w - cut.w, not up by add.w and down by cut.w from the same starting point."""
        v = 0.0
        for r in cut.roles:
            if r in add.roles:
                m = mass[r]
                v += (self.role_value(r, m - cut.w + add.w) - self.role_value(r, m + add.w)
                      + self.role_value(r, m) - self.role_value(r, m - cut.w))
        if cut.land and add.land:
            v += self.land_marginal_at(counts["land"]) - self.land_marginal_at(counts["land"] + 1)
        if cut.topend and add.topend:
            t = counts["topend"]
            v += self.penalty(t + 1) - 2 * self.penalty(t) + self.penalty(t - 1)
        return v

    def swap_gain(self, counts, mass, cut, add):
        return (self.add_value(counts, mass, add) - self.cut_value(counts, mass, cut)
                + self.overlap(counts, mass, cut, add))


def deck_value(cards, ctx, db, *, scores=None):
    """Value of a list of 99 (or 98) canonical names, basics repeated (commanders are not in it):
    {"total", "power" (total minus the theme part), "theme", "quality" (total minus the land term, the number
    to compare decks with the same land count), "roles": roles.counts, "land": lands}."""
    model = Model(ctx, db, scores)
    counts = roles.counts(cards, ctx["role_map"], db)
    facts = [model.facts(n) for n in cards]
    score_sum, theme = sum(f.score for f in facts), sum(f.theme for f in facts)
    land_term = model.land_value(counts["land"])
    total = model.total(counts, model.role_mass(facts), score_sum)
    return {"total": total, "power": total - theme, "theme": theme, "quality": total - land_term,
            "roles": counts, "land": counts["land"]}


# ----------------------------------------------------------------------------- a deck being edited
class Plan:
    """A deck under construction: its cards, role counts, rule state and money, plus the swap search.

    The search is the heart of both `upgrade` and `build`. For an add `a` and a cut `c` the gain is
    add_value(a) - cut_value(c) + overlap(c, a); cuts that are interchangeable (same roles, land-ness, rule
    flags, the kinds of threat they answer and, for lands, colors, basic-ness and fetching) differ only by score, so
    each such group is represented by its weakest member. That keeps a round near 250 adds x 35 groups instead of
    250 x 100."""

    def __init__(self, model, db, ci, bracket, *, prices, owned, budget=None, blocked=None):
        self.m, self.db, self.ci, self.bracket = model, db, ci, bracket
        self.colors = [c for c in "WUBRG" if c in ci]
        self.prices, self.owned, self.budget = prices, owned, budget
        self.blocked = blocked or {}
        self.cards = collections.Counter()
        self.order = []                                  # first-seen order of names, for printing
        self.counts = dict.fromkeys(STATE_ROLES, 0)      # whole cards: what reports, fills and the rules read
        self.mass = dict.fromkeys(roles.ROLES, 0.0)      # role mass: what the value reads
        self.score_sum = 0.0
        self.rules = {"gc": 0, "extra_turns": 0, "mld": 0}   # what can_add reads (commanders count)
        self.sources = collections.Counter()             # color -> lands that make it
        self.basics = 0                                  # copies of basic lands in the list
        self.basics_by_color = collections.Counter()     # color -> copies of basic lands that make it
        self.answers = collections.Counter()             # threat id -> cards in the list that answer it, once each
        self.answer_floors = {}                          # threat id -> fewest answers a swap may leave; empty: none
        self.basic_demand = 0                            # basics the list's land searchers can take, every copy
        self.pips = collections.Counter()                # color -> colored mana symbols of the nonland cards
        self.bought = {}                                 # name -> price paid in this run (refunded on a cut)
        self.spent = 0.0
        self.locked = set()                              # names that may not be cut
        self._rule_memo = {}
        self._split_memo = {}

    def clone(self):
        """An independent copy (the model, card index and price table are shared; they never change)."""
        other = Plan(self.m, self.db, self.ci, self.bracket, prices=self.prices, owned=self.owned,
                     budget=self.budget, blocked=self.blocked)
        other.cards, other.order = collections.Counter(self.cards), list(self.order)
        other.counts, other.mass, other.score_sum = dict(self.counts), dict(self.mass), self.score_sum
        other.rules, other.sources = dict(self.rules), collections.Counter(self.sources)
        other.basics, other.basic_demand, other.pips = self.basics, self.basic_demand, collections.Counter(self.pips)
        other.basics_by_color = collections.Counter(self.basics_by_color)
        other.answers, other.answer_floors = collections.Counter(self.answers), dict(self.answer_floors)
        other.bought, other.spent, other.locked = dict(self.bought), self.spent, set(self.locked)
        other._rule_memo = self._rule_memo           # depends only on (card, rule state), so it can be shared
        other._split_memo = self._split_memo         # depends only on (basics, symbols), so it can be shared
        return other

    # --- money
    def price(self, name):
        """What `name` costs you: 0 if owned or basic, None if unknown."""
        f = self.m.facts(name)
        if f.basic or f.name in self.owned:
            return 0.0
        return self.prices.get(f.name)

    def remaining(self):
        return None if self.budget is None else self.budget - self.spent

    # --- editing
    def count_commander(self, name):
        f = self.m.facts(name)
        self.rules["gc"] += f.gc
        self.rules["extra_turns"] += f.extra
        self.rules["mld"] += f.mld

    def add(self, name, buy=False):
        f = self.m.facts(name)
        if f.name not in self.cards:
            self.order.append(f.name)
            self.answers.update(f.answers)               # a card answers a threat once, however many copies it has
        self.cards[f.name] += 1
        for r in f.roles:
            self.counts[r] += 1
            self.mass[r] += f.w
        self.counts["land"] += f.land
        self.counts["topend"] += f.topend
        self.score_sum += f.score
        self.rules["gc"] += f.gc
        self.rules["extra_turns"] += f.extra
        self.rules["mld"] += f.mld
        for c in f.sources:
            self.sources[c] += 1
            self.basics_by_color[c] += f.basic
        self.basics += f.basic
        self.basic_demand += f.fetch
        for c, v in self._pips_of(f.name).items():
            self.pips[c] += v
        if buy:
            paid = self.price(f.name) or 0.0
            self.bought[f.name] = self.bought.get(f.name, 0.0) + paid
            self.spent += paid

    def remove(self, name):
        f = self.m.facts(name)
        self.cards[f.name] -= 1
        if self.cards[f.name] <= 0:
            del self.cards[f.name]
            self.order.remove(f.name)
            self.answers.subtract(f.answers)
        for r in f.roles:
            self.counts[r] -= 1
            self.mass[r] -= f.w
        self.counts["land"] -= f.land
        self.counts["topend"] -= f.topend
        self.score_sum -= f.score
        self.rules["gc"] -= f.gc
        self.rules["extra_turns"] -= f.extra
        self.rules["mld"] -= f.mld
        for c in f.sources:
            self.sources[c] -= 1
            self.basics_by_color[c] -= f.basic
        self.basics -= f.basic
        self.basic_demand -= f.fetch
        for c, v in self._pips_of(f.name).items():
            self.pips[c] -= v
        refund = self.bought.pop(f.name, 0.0)
        self.spent -= refund

    def _pips_of(self, name):
        """The colored mana symbols one copy of `name` adds to `pips`; a land has none."""
        rec = self.db.get(name)
        return {} if rec is None or rec["land"] else _pips(rec, self.ci)

    def swap(self, cut, add):
        self.remove(cut)
        self.add(add, buy=True)

    def names(self):
        """Every copy as one entry (nine Forests are nine entries)."""
        return [n for n in self.order for _ in range(self.cards[n])]

    def value(self):
        return self.m.total(self.counts, self.mass, self.score_sum)

    # --- rules
    def rule_ok(self, fa, cut=None):
        """Whether adding card `fa` keeps the Game Changer, extra-turn and mass-land-denial limits, with
        `cut` (a Facts) leaving the list first."""
        gone = cut or Facts("", 0, 0, (), 0.0, False, False, 0, 0, 0, frozenset(), False, 0, frozenset())
        state = (self.rules["gc"] - gone.gc, self.rules["extra_turns"] - gone.extra,
                 self.rules["mld"] - gone.mld)
        key = (fa.name, state)
        if key not in self._rule_memo:
            held = {"gc": state[0], "extra_turns": state[1], "mld": state[2]}
            self._rule_memo[key] = brackets.can_add(self.db.get(fa.name), held, self.bracket)
        return self._rule_memo[key]

    def mana_ok(self, cut, add):
        """A swap may not strip a color of its lands: after it each color keeps at least MANA_FLOOR sources,
        or as many as it had if it had fewer."""
        if not (cut.land or add.land):
            return True
        for c in self.colors:
            after = self.sources[c] - (c in cut.sources) + (c in add.sources)
            if after < min(self.sources[c], MANA_FLOOR):
                return False
        return True

    def basics_ok(self, cut, add):
        """A swap that cuts a basic land must leave the basics the deck still needs. Cards that search the library
        for a basic land (Cultivate, Evolving Wilds) find nothing once the last basic is gone, so after the swap
        the list keeps as many basics as its searchers can take, counting the search of the card being added, and
        at least as many as it has colors. Those basics are split among the colors the way `build` splits basics
        (one each, the rest by colored mana symbols), so a searcher can still fix either color; without the split
        the cut order alone took every Swamp from a green-heavy deck. A nonbasic land may only take a basic's slot
        if it scores NONBASIC_MIN, the same rule `build` applies. A swap that cuts anything else passes: adding a
        searcher by cutting a spell stays legal even when the deck is already short of basics."""
        if not cut.basic:
            return True
        if add.land and not add.basic and add.score < NONBASIC_MIN:
            return False
        keep = max(len(self.colors), self.basic_demand + add.fetch)
        if self.basics - 1 + add.basic < keep:
            return False
        need = self._basic_shares(keep)
        return all(self.basics_by_color[c] - 1 + (add.basic and c in add.sources) >= need.get(c, 0)
                   for c in cut.sources)

    def _tight_answers(self):
        """The kinds of threat whose answers are down to their floor or under it (and not zero): the only ones a swap
        can still thin out. Usually none, which lets `best_swap` skip `keeps_answers` for nearly every pair."""
        return {threat for threat, floor in self.answer_floors.items() if 0 < self.answers[threat] <= floor}

    def keeps_answers(self, cut, add):
        """A swap may not strip a kind of threat of its answers: after it each threat keeps at least its floor (what a
        typical deck at the bracket holds: the band's target, the median of real decks), or as many answers as it had
        if it had fewer. With 7 answers to enchantments and a floor of 4 a deck may trade down to 4 but not to 3, and
        a deck that has 2 may not lose either, though it may swap one for another. Swapping an answer to enchantments
        for an answer to planeswalkers does not help the enchantments, so each kind is judged on its own. With no
        floors (`build`, or an `upgrade` whose tags did not load) every swap passes."""
        if not self.answer_floors:
            return True
        for threat in cut.answers:
            after = self.answers[threat] - 1 + (threat in add.answers)
            if after < min(self.answers[threat], self.answer_floors.get(threat, 0)):
                return False
        return True

    def _basic_shares(self, total):
        """{color: basics} for `total` basics split like `build` splits them: one per color, the rest in
        proportion to the colored mana symbols of the nonland cards (memoized: the search asks this for every
        add it prices)."""
        key = (total, tuple(self.pips[c] for c in self.colors))
        split = self._split_memo.get(key)
        if split is None:
            split = self._split_memo[key] = _allocate(total, {c: self.pips[c] for c in self.colors})
        return split

    # --- search
    def _lands_per_symbol(self, color):
        """Lands that make `color` for each colored mana symbol of that color in the nonland cards (the +1
        keeps a color that no card uses finite). The color with the fewest gets the next basic; the one with the
        most gives up the next one."""
        return self.sources[color] / (self.pips[color] + 1)

    def _cut_order(self, f):
        """Sort key of the group `f` belongs to, for ties between equal gains: nonbasic cards first (an unscored
        utility land goes before a basic), then basic lands, the color with the most lands per symbol first. A
        basic that makes none of the deck's colors (Wastes in a colored deck) costs no color, so it leads."""
        if not f.basic:
            return 0, 0.0
        return 1, -max((self._lands_per_symbol(c) for c in f.sources), default=math.inf)

    def _groups(self, cuts):
        """Cut candidates grouped by interchangeable signature, weakest first within a group:
        [[(Facts, loss, refund), ...], ...]. The search keeps the first of several equal gains, so the order of
        the groups decides ties: see `_cut_order`."""
        groups = {}
        for name in cuts:
            f = self.m.facts(name)
            sig = (f.roles, f.land, f.topend, f.gc, f.extra, f.mld, f.sources, f.basic, f.fetch, f.answers)
            groups.setdefault(sig, []).append(f)
        out = []
        for members in groups.values():
            members.sort(key=lambda f: (f.score, f.name))
            out.append([(f, self.m.cut_value(self.counts, self.mass, f), self.bought.get(f.name, 0.0))
                        for f in members])
        out.sort(key=lambda group: self._cut_order(group[0][0]))        # stable: nonbasic groups keep their order
        return out

    def best_swap(self, cuts, adds, *, min_gain=MIN_GAIN, lam=0.0, watch=None):
        """The best (gain, cut, add) among `cuts` and `adds` that is affordable, passes the bracket's limits and the
        land and answer floors (`mana_ok`, `basics_ok`, `keeps_answers`) and beats `min_gain`, or None. With `lam` > 0
        the best is the one with the most gain minus `lam` per dollar of the add (the gain returned is still the real
        one). `watch`, if given, collects what almost happened:
        watch["blocked"][add] = (best gain, why the rules or a combo forbid it) and
        watch["costly"][add] = (best gain, price) for adds that only the budget stopped."""
        rem, best, best_key = self.remaining(), None, None
        groups = self._groups(cuts)
        tight = self._tight_answers()                  # kinds of threat a swap could still thin out
        # The members of a group answer the same kinds (that is in the signature), so one test per group says whether
        # the answers floor could refuse any of its cuts; most groups answer nothing that is down to its floor.
        at_risk = [bool(members[0][0].answers & tight) for members in groups]
        for a in adds:
            fa = self.m.facts(a)
            need = self.price(a)
            if rem is not None and need is None:
                continue
            win = self.m.add_value(self.counts, self.mass, fa)
            risky = bool(fa.gc or fa.extra or fa.mld)
            any_gain, rule_pass, hit = None, False, None
            for members, hot in zip(groups, at_risk):
                for fc, loss, refund in members:
                    if (fc.land or fa.land) and not self.mana_ok(fc, fa):
                        break
                    if fc.basic and not self.basics_ok(fc, fa):
                        break
                    if hot and not self.keeps_answers(fc, fa):
                        break
                    gain = win - loss + self.m.overlap(self.counts, self.mass, fc, fa)
                    if any_gain is None or gain > any_gain:
                        any_gain = gain
                    if risky and not self.rule_ok(fa, fc)[0]:
                        break
                    rule_pass = True
                    if rem is not None and need - refund > rem + EPS:
                        continue                         # a cut with a bigger refund may afford it
                    if hit is None or gain > hit[0]:
                        hit = (gain, fc.name)
                    break
            if any_gain is None:
                continue
            if a in self.blocked:
                self._watch(watch, "blocked", a, any_gain, self.blocked[a])
            elif risky and not rule_pass:
                why = self.rule_ok(fa)[1] or "breaks the bracket's limits"
                self._watch(watch, "blocked", a, any_gain, why)
            elif hit is None:
                self._watch(watch, "costly", a, any_gain, need)
            elif hit[0] > min_gain:
                key = hit[0] - lam * (need or 0.0)
                if best_key is None or key > best_key:
                    best, best_key = (hit[0], hit[1], a), key
        return best

    @staticmethod
    def _watch(watch, kind, add, gain, detail):
        if watch is not None:
            old = watch.setdefault(kind, {}).get(add)
            if old is None or gain > old[0]:
                watch[kind][add] = (gain, detail)

    def best_add(self, adds, lam=0.0):
        """The add with the best value (minus `lam` per dollar) that fits the budget and the bracket."""
        rem, best = self.remaining(), None
        for a in adds:
            fa = self.m.facts(a)
            p = self.price(a)
            if rem is not None and (p is None or p > rem + EPS):
                continue
            if (fa.gc or fa.extra or fa.mld) and not self.rule_ok(fa)[0]:
                continue
            v = self.m.add_value(self.counts, self.mass, fa) - lam * (p or 0.0)
            if best is None or v > best[0]:
                best = (v, a)
        return best

    def filler(self):
        """A basic land for a slot nothing else can fill: the color with the fewest lands per colored symbol."""
        if not self.colors:
            return "Wastes"
        return BASIC_FOR[min(self.colors, key=lambda c: (self._lands_per_symbol(c), c))]


def _pips(rec, ci):
    """Colored mana symbols in the front face's cost, by color inside `ci`. A hybrid symbol is split between
    its colors, and a Phyrexian one counts as its color."""
    out = collections.Counter()
    for sym in (rec["mana_cost"] or "").replace("}", "").split("{")[1:]:
        colors = [c for c in sym.split("/") if c in "WUBRG" and c in ci]
        for c in colors:
            out[c] += 1.0 / len(colors)
    return out


def _allocate(total, weights):
    """Split `total` basics among colors in proportion to `weights` by largest remainder, at least one each
    when there is room. Returns {color: n}."""
    colors = list(weights)
    if not colors or total <= 0:
        return {}
    base = {c: 1 for c in colors} if total >= len(colors) else {c: 0 for c in colors}
    spare = total - sum(base.values())
    mass = sum(weights.values())
    share = {c: (weights[c] / mass if mass else 1.0 / len(colors)) * spare for c in colors}
    for c in colors:
        base[c] += int(share[c])
    left = total - sum(base.values())
    for c in sorted(colors, key=lambda c: (-(share[c] - int(share[c])), -weights[c], c))[:left]:
        base[c] += 1
    return {c: n for c, n in base.items() if n}


# ----------------------------------------------------------------------------- shared pieces
def _candidates(ctx, db, exclude, scores=None):
    """Names that may be added: scored, Commander-legal, inside the colors, not basic, not excluded."""
    scores = ctx["scores"] if scores is None else scores
    out = []
    for name in scores:
        rec = db.get(name)
        if (rec is None or rec["legal"] != "legal" or "Basic" in rec["types"] or name in exclude
                or not _inside(rec, ctx["ci"])):
            continue
        out.append(name)
    return out


def _prune(names, model, limit):
    """The `limit` most promising names: score plus the value of the role's first card."""
    def key(name):
        f = model.facts(name)
        return (f.score + (1.5 * ROLE_BETA if f.roles else 0.0), name)
    return sorted(names, key=key, reverse=True)[:limit]


def _price_map(names, ctx, db, prices, warnings):
    """{name: price} for the names that cost money: the caller's `prices`, or Scryfall's cheapest printing."""
    if prices is not None:
        return dict(prices)
    need = [n for n in dict.fromkeys(names) if n not in ctx["owned"] and "Basic" not in db.get(n)["types"]]
    found = carddb.cheapest_prices(need) if need else {}
    warnings += _drain(carddb.WARNINGS)
    return found


def _find_combos(combos_fn, commanders, names, warnings):
    """Commander Spellbook's answer for a list, or None (with a warning) when it cannot be had."""
    if combos_fn is None:
        return None
    try:
        return combos_fn(commanders, list(names))
    except net.FetchError as e:
        warnings.append(f"Combos were not checked: {e}")
        return None


def _short_block(reason, bracket):
    """Trim brackets.blocked_adds' sentence to 'completes a two-card combo with X (needs Bracket 4)'."""
    head, _, tail = reason.partition(": ")
    if not tail:
        return reason
    need = None
    if "Bracket " in tail and "or higher" in tail:
        need = tail.split("Bracket ")[1].split(" ")[0]
    note = f"needs Bracket {need}" if need else f"not allowed at Bracket {bracket}"
    return f"{head} ({note})"


def _fills(plan, fc, fa):
    """The roles `fa` adds to that were under their target before the swap (cutting a card of the same role
    would leave its count where it was)."""
    t = plan.m.limits
    out = [r for r in fa.roles if r not in fc.roles and plan.counts[r] < t[r][1]]
    if fa.land and not fc.land and plan.counts["land"] < plan.m.land_target:
        out.append("land")
    return out


def _fill_text(plan, fills):
    target = {r: lim[1] for r, lim in plan.m.limits.items()}
    target["land"] = plan.m.land_target
    return ", ".join(f"{roles.LABELS.get(r, r)} ({plan.counts[r]} of {target[r]})" for r in fills)


# ----------------------------------------------------------------------------- upgrade
def _violating_cuts(plan, report, deck_scores, commanders, includes):
    """[(card, violation)] to cut for each bracket violation, weakest first: `excess` cards of a limit, the
    weaker non-commander piece of a combo. Cards another violation already removed count toward this one."""
    cut, out, notes = set(), [], []
    for v in report["violations"]:
        movable = [c for c in v["cards"] if c in plan.cards and c not in commanders and c not in includes]
        movable.sort(key=lambda c: (deck_scores.get(c, 0.0), c))
        if v["rule"] == "two_card_combos":
            if any(c in cut for c in v["cards"]):
                continue
            need = 1
        else:
            need = v["excess"] - sum(1 for c in v["cards"] if c in cut)
        take = [c for c in movable if c not in cut][:max(0, need)]
        if len(take) < need:
            notes.append(f"Could not fix: {v['message']} (the cards involved are your commander or "
                         "cards you asked to include)")
        for c in take:
            cut.add(c)
            out.append((c, v["message"]))
    return out, notes


def _illegal_cuts(plan, db, ci, commanders, includes, excludes):
    """[(card, reason)] for cards that cannot stay in the deck: banned, outside the colors, extra copies of a
    one-copy card, or a card the player said never to play."""
    out = []
    for name, k in plan.cards.items():
        rec = db.get(name)
        if rec is None or "Basic" in rec["types"] or name in commanders or name in includes:
            continue
        if name in excludes:
            out += [(name, f"you asked never to play {name}")] * k
        elif rec["legal"] != "legal":
            out += [(name, f"{name} is not legal in Commander ({rec['legal'].replace('_', ' ')})")] * k
        elif not _inside(rec, ci):
            out += [(name, f"{name} is outside the commander's colors")] * k
        elif k > 1 and not rec["any_number"]:
            out += [(name, f"{name} appears {k} times; Commander allows one copy")] * (k - 1)
    return out


class _Ledger:
    """Turns swaps into the result's swap records, remembering what each card costs."""

    def __init__(self, ctx, model, plan_owned, price):
        self.ctx, self.m, self.owned, self.price = ctx, model, plan_owned, price

    def cost(self, name):
        return 0.0 if name in self.owned else self.price.get(name)

    def record(self, cut, add, gain, forced, reason, fills):
        """One swap's record. "price_point" is the step of the price ladder that found it; `upgrade` fills it in
        for the optional swaps, and a forced swap belongs to no step."""
        fc = self.m.facts(cut)
        sc_add, sc_cut = self.ctx["scores"].get(add) or {}, self.ctx["scores"].get(cut) or {}
        return {"cut": cut, "add": add, "gain": gain, "price": self.cost(add), "owned": add in self.owned,
                "forced": forced, "reason": reason, "fills": fills,
                "evidence_add": sc_add.get("evidence", ""), "kind_add": sc_add.get("kind", "none"),
                "evidence_cut": "basic land" if fc.basic else sc_cut.get("evidence", "not scored"),
                "price_point": None}


def _optional_swaps(plan, ledger, pool, max_swaps, lam, watch):
    """Apply the best swaps to `plan` one at a time, at most `max_swaps` of them (None: no limit); returns their
    records, best first as they were found. With no limit it still ends: each swap locks the card it adds and
    cuts one that was not locked, and the search stops when nothing beats MIN_GAIN or the money runs out."""
    out = []
    while max_swaps is None or len(out) < max_swaps:
        choice = plan.best_swap([n for n in plan.cards if n not in plan.locked],
                                [a for a in pool if a not in plan.cards], lam=lam, watch=watch)
        if not choice:
            break
        gain, cut, add = choice
        fc, fa = plan.m.facts(cut), plan.m.facts(add)
        fills = _fills(plan, fc, fa)
        out.append(ledger.record(cut, add, gain, False, _reason(plan, fc, fa, fills), fills))
        plan.swap(cut, add)
        plan.locked.add(add)
    return out


def _budget_bound(watch):
    """True when something worth adding was refused only for its price (a price-aware run may do better)."""
    return any(g > MIN_GAIN for g, _ in (watch.get("costly") or {}).values())


def default_price_points(budget):
    """The dollar amounts an upgrade is stepped through on the way to `budget`, smallest first and the budget
    last: the budget, half of it, a quarter, and so on, at most PRICE_POINTS_SHOWN of them and no half under
    PRICE_POINT_MIN. Each halved amount is rounded half-up to a multiple of PRICE_POINT_ROUND so the steps read as
    round numbers: $200 gives 25, 50, 100 and 200; $75 gives 20, 40 and 75 (the next half, $9.38, is too small);
    a budget under $20 has no half worth a step and stands alone."""
    points, half = [float(budget)], budget / 2
    while len(points) < PRICE_POINTS_SHOWN and half >= PRICE_POINT_MIN:
        points.append(float(math.floor(half / PRICE_POINT_ROUND + 0.5) * PRICE_POINT_ROUND))
        half /= 2
    return sorted(set(points))


def _price_ladder(budget, price_points):
    """The steps one upgrade climbs, smallest first, the budget last. Without a budget there is nothing to step
    toward, so there are none. Amounts the caller names count when they are above $0 and under the budget (each
    once); with none named (None) the steps are default_price_points(budget)."""
    if budget is None:
        return []
    if price_points is None:
        return default_price_points(budget)
    return sorted({float(p) for p in price_points if 0 < p < budget}) + [float(budget)]


def _weakened(before, now, bands):
    """The kinds of threat a list answers with fewer cards than the list it started from and with no more than a
    typical deck at the bracket holds: [{"id", "label", "before", "after", "target"}] in roles.THREATS order, "label"
    being the short noun ("enchantments") and "target" the typical count (the band's target, the median of real decks).
    `before` and `now` are roles.answer_counts output, `bands` is roles.answer_bands output; a kind it has no band for
    is left out, since there is no typical count to compare with. Because the optional swaps never take a kind under
    the typical count, an entry means the list has used up all of that kind's surplus over a typical deck (7 answers
    to enchantments down to 4, where a deck usually holds 4); a kind that fell but is still above the typical count
    (7 down to 5) is not listed. One a forced swap took under the typical count is listed too."""
    return [{"id": id_, "label": roles.THREAT_NOUNS[id_], "before": before[id_], "after": now[id_],
             "target": bands[id_]["target"]}
            for id_ in roles.THREAT_IDS
            if id_ in bands and now[id_] < before[id_] and now[id_] <= bands[id_]["target"]]


def _price_point_summaries(ladder, swaps, deck_names, ctx, db, value_before, attrs=None, bands=None):
    """What each price point came to: [{"budget", "spent", "value", "swaps", "change", "answers", "weakens"}], by
    replaying the kept swaps onto the starting list in order. "swaps" and "spent" are totals so far (forced swaps
    included, since they come first), "value" is deck_value of the list at that point, and "change" is that less
    `value_before` (to 2 decimals), so a page never subtracts. "answers" is {threat id: cards that answer it} for the
    list at that point and "weakens" the kinds it has brought down from the starting count to the typical count or
    under it (see `_weakened`); `attrs` is roles.attributes output and `bands` roles.answer_bands output, and without `attrs` (the
    tags did not load) "answers" is None and "weakens" is empty. Replaying instead of remembering what the search saw
    keeps the lines true after the combo repair has undone a swap."""
    names, spent, done, out = list(deck_names), 0.0, 0, []
    start = None if attrs is None else roles.answer_counts(deck_names, attrs)
    for point in ladder:
        while done < len(swaps) and (swaps[done]["price_point"] is None or swaps[done]["price_point"] <= point):
            names.remove(swaps[done]["cut"])
            names.append(swaps[done]["add"])
            spent += swaps[done]["price"] or 0.0
            done += 1
        value = deck_value(names, ctx, db)["total"]
        now = None if attrs is None else roles.answer_counts(names, attrs)
        out.append({"budget": point, "spent": round(spent, 2), "value": value, "swaps": done,
                    "change": round(value - value_before, 2), "answers": now,
                    "weakens": [] if now is None else _weakened(start, now, bands or {})})
    return out


def _answer_tags(names, db, warnings):
    """roles.attributes for `names`, or None when the tag data could not be loaded, with a line in `warnings`. An
    upgrade cannot then tell which cards answer which kind of threat, so it keeps none of them and says so."""
    attrs = roles.attributes(names, db)
    if roles.attributes_loaded():
        return attrs
    warnings.append("Answers to each kind of threat (" + ", ".join(roles.THREAT_NOUNS.values()) + ") were not checked: "
                    "Scryfall's function tags for card attributes are not available, so a swap may have thinned them "
                    "out.")
    return None


def upgrade(ctx, deck, db, *, budget=None, max_swaps=None, price_points=None, combos_fn=None, allow_combos=False,
            prices=None):
    """Ranked cut/add swaps for `deck` ({"commanders", "cards": [(count, name)]}, names canonical) within a
    budget and the target bracket. See the module docstring for the method; the result shape is in the design
    doc ("Command line and result shapes"). The deck's own cards and `ctx["owned"]` cost nothing. `max_swaps`
    caps the optional swaps; None, the default, lets the search run until nothing beats MIN_GAIN or the money is
    gone.

    With a budget the greedy "best gain first" can spend it all on one pricey card, so the optional swaps are
    run again with a growing penalty per dollar (PRICE_LAMBDAS) and the run that ends with the most valuable
    deck wins. Every printed gain is still the real gain of that swap at the moment it was made.

    A budget is also climbed in steps, the price points (`price_points`, else default_price_points(budget); the
    budget is always the last). Each step is that whole search with the budget set to the point, starting from the
    list the step before left: money spent earlier counts toward the point, and what an earlier step bought is
    never cut. So the first swaps are what a smaller budget would do, and each later step only adds to them. A
    swap says which step found it ("price_point"; None for a forced swap), and the result's "price_points" sums up
    each step. Without a budget there are no steps.

    Answers: the optional swaps may not leave a kind of threat with fewer answers than a typical deck at the bracket
    holds (the band's target, the median of real decks), or than the list had if it had fewer
    (`Plan.keeps_answers`). The floors are set only after the forced swaps, which must happen whatever they take
    away, and only when the attribute tags loaded
    (roles.attributes_loaded); if they did not, no floor applies and a warning says that answers were not checked.
    The result carries "answers_before" and "answers_after" ({threat id: cards that answer it}, None without tags),
    and each price point carries "answers", "weakens" and "change" (see `_price_point_summaries`)."""
    warnings = list(ctx["warnings"])
    bracket, ci = ctx["bracket"], ctx["ci"]
    commanders = list(deck.get("commanders") or ctx["commanders"])
    deck_names = [n for k, n in deck["cards"] for _ in range(k)]
    includes, spec_exclude = set(ctx["include"]), set(ctx["exclude"])
    taken_names = set(deck_names) | set(commanders) | spec_exclude
    candidates = _candidates(ctx, db, taken_names)
    attrs = _answer_tags(deck_names + candidates, db, warnings)          # None: the tags did not load
    model = Model(ctx, db, answers=None if attrs is None else
                  {name: roles.threats_answered(slugs) for name, slugs in attrs.items()})

    combos = _find_combos(combos_fn, commanders, deck_names, warnings)
    if allow_combos:
        combos = {"included": [], "almost": []}
        warnings.append("Combo limits are lifted (--allow-combos); no combo is checked or blocked.")
    blocked = {} if combos is None else brackets.blocked_adds(bracket, combos)
    report_before = brackets.check(commanders, deck_names, bracket, db, combos=combos)

    pool = _prune(candidates, model, MAX_CANDIDATES)
    owned = set(ctx["owned"]) | set(deck_names)
    price = _price_map(pool, ctx, db, prices, warnings) if budget is not None else dict(prices or {})
    plan = Plan(model, db, ci, bracket, prices=price, owned=owned, budget=budget, blocked=blocked)
    for c in commanders:
        plan.count_commander(c)
    for n in deck_names:
        plan.add(n)
    plan.locked = set(includes) | set(commanders)      # a commander listed among the cards stays too
    ledger = _Ledger(ctx, model, owned, price)
    counts_before = roles.counts(deck_names, ctx["role_map"], db)
    value_before = deck_value(deck_names, ctx, db)
    for name in sorted(includes - set(deck_names) - set(commanders)):
        warnings.append(f"{name} is in your include list but not in the deck; upgrade keeps included cards "
                        "and does not add them.")
    if len(deck_names) + len(commanders) != 100:
        warnings.append(f"The list has {len(deck_names) + len(commanders)} cards; a Commander deck has 100. "
                        "Swaps keep the size the list has.")

    # --- forced swaps: what the format or the bracket does not allow
    swaps = []
    deck_scores = {n: (ctx["scores"].get(n) or {}).get("score", 0.0) for n in plan.cards}
    forced = _illegal_cuts(plan, db, ci, commanders, includes, spec_exclude)
    named = {c for c, _ in forced}
    more, notes = _violating_cuts(plan, report_before, deck_scores, set(commanders), includes)
    forced += [(c, why) for c, why in more if c not in named]
    warnings += notes
    for cut, why in forced:
        if cut not in plan.cards:
            continue
        fc = model.facts(cut)
        choice = plan.best_swap([cut], [a for a in pool if a not in plan.cards], min_gain=-math.inf)
        if choice:
            add = choice[2]
        else:                                    # nothing affordable and legal: a basic keeps the list whole
            add = plan.filler()
            why += " (no affordable replacement, so a basic land fills the slot)"
        fa = model.facts(add)
        fills, gain = _fills(plan, fc, fa), model.swap_gain(plan.counts, plan.mass, fc, fa)
        plan.swap(cut, add)
        plan.locked.add(add)
        swaps.append(ledger.record(cut, add, gain, True, why, fills))

    # --- from here on the answers are kept, down to what a typical deck holds (the band's target; the Metrics tab's
    # "short" is the band's min, a lower bar). The forced swaps above had to happen whatever they took away, so the
    # floors wait until they are done; without the tags there is nothing to keep (and the warning has been given).
    bands = {} if attrs is None else roles.answer_bands(bracket, ci)
    plan.answer_floors = {threat: band["target"] for threat, band in bands.items()}

    # --- the best swaps, one at a time. With a budget, climb the price points: each step spends up to its amount
    # on top of what the steps before spent, and tries several prices-matter settings. `watch` is the last
    # step's, so it describes the finished list.
    ladder = _price_ladder(budget, price_points)
    watch, taken = {}, []
    for point in ladder or [None]:                           # no budget: one step with no cap
        room = None if max_swaps is None else max_swaps - len(taken)
        if room is not None and room <= 0:
            break                                            # the cap counts across steps
        if point is not None:
            plan.budget = max(point, plan.spent)             # forced swaps may already have spent past a small point
        trial, step_watch = plan.clone(), {}
        got = _optional_swaps(trial, ledger, pool, room, 0.0, step_watch)
        if point is not None and _budget_bound(step_watch):
            for lam in PRICE_LAMBDAS[1:]:
                other, other_watch = plan.clone(), {}
                more = _optional_swaps(other, ledger, pool, room, lam, other_watch)
                if other.value() > trial.value() + EPS:
                    trial, got, step_watch = other, more, other_watch
        for x in got:
            x["price_point"] = point
        plan, taken, watch = trial, taken + got, step_watch
    swaps = swaps + taken

    # --- a combo that only appeared once the swaps were made
    combos_after = combos
    if combos_fn is not None and not allow_combos:
        for attempt in range(COMBO_ROUNDS + 1):
            combos_after = _find_combos(combos_fn, commanders, plan.names(), warnings)
            if combos_after is None:
                break
            report = brackets.check(commanders, plan.names(), bracket, db, combos=combos_after)
            bad = [v for v in report["violations"] if v["rule"] == "two_card_combos"]
            if not bad:
                break
            pieces = {c for v in bad for c in v["cards"]}
            undo = next((x for x in reversed(swaps) if x["add"] in pieces and not x["forced"]), None)
            if undo is None or attempt == COMBO_ROUNDS:
                warnings.append("A combo the bracket does not allow remains in the list: "
                                + "; ".join(v["message"] for v in bad))
                break
            plan.remove(undo["add"])
            plan.add(undo["cut"])
            plan.locked.discard(undo["add"])
            swaps.remove(undo)
            taken = [x for x in taken if x is not undo]
            warnings.append(f"Undid {undo['cut']} -> {undo['add']}: {undo['add']} completes a combo that "
                            f"Bracket {bracket} does not allow.")

    final_names = plan.names()
    report_after = brackets.check(commanders, final_names, bracket, db, combos=combos_after)
    if budget is None:                           # nothing depended on prices, so price only what we print
        price.update(_price_map([x["add"] for x in swaps], ctx, db, prices, warnings))
    spent = 0.0
    for rank, x in enumerate(swaps, 1):
        x["rank"], x["price"] = rank, ledger.cost(x["add"])
        spent += x["price"] or 0.0

    last_gain = taken[-1]["gain"] if taken else MIN_GAIN
    blocked_list = [{"card": c, "reason": _short_block(why, bracket), "gain": g}
                    for c, (g, why) in sorted((watch.get("blocked") or {}).items(), key=lambda kv: -kv[1][0])
                    if g > last_gain and c not in plan.cards][:BLOCKED_SHOWN]
    cheap = []
    if budget is not None and not taken:
        cheap = [{"card": c, "gain": g, "price": p}
                 for c, (g, p) in (watch.get("costly") or {}).items() if g > MIN_GAIN and p is not None]
        cheap = sorted(cheap, key=lambda r: (r["price"], -r["gain"], r["card"]))[:CHEAP_ADDS]

    value_after = deck_value(final_names, ctx, db)
    answers_before = None if attrs is None else roles.answer_counts(deck_names, attrs)
    answers_after = None if attrs is None else roles.answer_counts(final_names, attrs)
    return {"command": "upgrade",
            "deck": {"name": deck.get("name", ""), "commanders": commanders,
                     "count": len(final_names) + len(commanders), "ci": ci},
            "bracket": bracket, "budget": budget, "spent": round(spent, 2), "spec": ctx["spec"],
            "swaps": swaps,
            "price_points": _price_point_summaries(ladder, swaps, deck_names, ctx, db, value_before["total"], attrs,
                                                   bands),
            "blocked": blocked_list, "cheap_adds": cheap,
            "roles_before": counts_before, "roles_after": value_after["roles"], "targets": ctx["targets"],
            "answers_before": answers_before, "answers_after": answers_after,
            "value_before": value_before["total"], "value_after": value_after["total"],
            "bracket_before": report_before, "bracket_after": report_after,
            "deck_after": {"commanders": commanders, "cards": [[plan.cards[n], n] for n in plan.order]},
            "warnings": _dedupe(warnings), "sources": ctx["sources"]}


def _reason(plan, fc, fa, fills):
    parts = []
    if fills:
        parts.append("fills " + _fill_text(plan, fills))
    if fa.score - fc.score > 0.05:
        parts.append(f"scores {fa.score:.2f} against {fc.score:.2f}")
    return "; ".join(parts) or "slightly better fit"


# ----------------------------------------------------------------------------- build
def _usable_includes(ctx, db, warnings):
    """The spec's include cards that can be in this deck at all; the rest are named in a warning."""
    out = []
    for name in ctx["include"]:
        rec = db.get(name)
        if rec["legal"] != "legal":
            warnings.append(f"Cannot include {name}: it is not legal in Commander.")
        elif not _inside(rec, ctx["ci"]):
            warnings.append(f"Cannot include {name}: it is outside the commander's colors.")
        elif name in ctx["commanders"]:
            continue
        elif name in ctx["exclude"]:
            warnings.append(f"{name} is in both include and exclude; leaving it out.")
        else:
            out.append(name)
    return out


def _basic_split(plan, db, commanders, total):
    """{basic land: copies} for `total` slots, in proportion to the colored mana symbols of the deck's
    nonland cards and its commanders (a colorless identity gets Wastes)."""
    if total <= 0:
        return {}
    if not plan.colors:
        return {"Wastes": total}
    weight = collections.Counter({c: 0.0 for c in plan.colors})
    for name, k in plan.cards.items():
        rec = db.get(name)
        if rec and not rec["land"]:
            for c, v in _pips(rec, plan.ci).items():
                weight[c] += v * k
    for name in commanders:
        for c, v in _pips(db.get(name), plan.ci).items():
            weight[c] += v
    return {BASIC_FOR[c]: n for c, n in _allocate(total, dict(weight)).items()}


def _assemble(ctx, db, model, spells, lands, prices, owned, budget, banned, includes, commanders, blocked):
    """One deck from scratch: includes, a greedy fill of the nonland slots (with a rising price penalty when a
    budget would otherwise run out before the deck is full), a swap search, nonbasic lands, then basics.
    Returns (plan, basics); plan.short counts the nonland slots no affordable card could fill (basics took
    them)."""
    bracket, ci = ctx["bracket"], ctx["ci"]
    land_target = ctx["targets"]["land"]["target"]
    total_slots = 100 - len(commanders)
    spell_includes = [n for n in includes if not model.facts(n).land]
    spell_slots = total_slots - land_target - len(spell_includes)
    cap = None if budget is None else budget * (1 - LAND_BUDGET_SHARE)   # lands keep a share of the budget

    def fresh():
        p = Plan(model, db, ci, bracket, prices=prices, owned=owned, budget=cap, blocked=blocked)
        for c in commanders:
            p.count_commander(c)
        for n in includes:
            p.add(n, buy=True)
        p.locked = set(includes)
        return p

    usable = [n for n in spells if n not in banned and n not in includes]
    for lam in (PRICE_LAMBDAS if budget is not None else (0.0,)):
        plan, left = fresh(), spell_slots
        while left > 0:
            pick = plan.best_add([n for n in usable if n not in plan.cards], lam)
            if pick is None:
                break
            plan.add(pick[1], buy=True)
            left -= 1
        if left <= 0:
            break
    for _ in range(BUILD_ITERATIONS):
        choice = plan.best_swap([n for n in plan.cards if n not in plan.locked and not model.facts(n).land],
                                [n for n in usable if n not in plan.cards])
        if not choice:
            break
        plan.swap(choice[1], choice[2])
    plan.short, plan.slots = max(0, left), spell_slots

    # Nonbasic lands by score, leaving room for the basics the deck needs: one per color, and as many as its land
    # searchers can take (a candidate that searches adds its own demand).
    plan.budget = budget

    def lands_left(extra_demand=0):
        """Land slots still open to nonbasic lands once the basics the deck needs are set aside."""
        return land_target - max(len(plan.colors), plan.basic_demand + extra_demand) - plan.counts["land"]

    for name in sorted((n for n in lands if n not in banned and n not in plan.cards),
                       key=lambda n: (-model.facts(n).score, n)):
        f = model.facts(name)
        if lands_left() <= 0 or f.score < NONBASIC_MIN:
            break                                       # not even a land that searches for nothing fits
        if lands_left(f.fetch) <= 0:
            continue                                    # it fits only without its own search: try the next
        if plan.best_add([name]) is not None:
            plan.add(name, buy=True)
    basics = _basic_split(plan, db, commanders, total_slots - sum(plan.cards.values()))
    for name, n in basics.items():
        for _ in range(n):
            plan.add(name)
    return plan, basics


def _repair_combos(rebuild, ctx, db, commanders, combos_fn, allow_combos, warnings):
    """Run `rebuild(banned)` until the list has no combo this bracket forbids, banning the weaker piece of
    each one found (up to COMBO_ROUNDS times). Returns (plan, basics, combos, {banned card: reason})."""
    bracket, banned, why = ctx["bracket"], set(), {}
    check = combos_fn is not None and not allow_combos and brackets.rules(bracket)["two_card_combos"] != "any"
    for attempt in range(COMBO_ROUNDS + 1):
        plan, basics = rebuild(banned)
        if not check:
            return plan, basics, None, why
        combos = _find_combos(combos_fn, commanders, plan.names(), warnings)
        if combos is None:
            return plan, basics, None, why
        report = brackets.check(commanders, plan.names(), bracket, db, combos=combos)
        bad = [v for v in report["violations"] if v["rule"] == "two_card_combos"]
        if not bad:
            return plan, basics, combos, why
        if attempt == COMBO_ROUNDS:
            warnings.append("A combo the bracket does not allow remains in the list: "
                            + "; ".join(v["message"] for v in bad))
            return plan, basics, combos, why
        for v in bad:
            movable = [c for c in v["cards"]
                       if c in plan.cards and c not in commanders and c not in plan.locked]
            if movable:
                weakest = min(movable, key=lambda c: (plan.m.facts(c).score, c))
                banned.add(weakest)
                partners = ", ".join(c for c in v["cards"] if c != weakest)
                why[weakest] = f"forms a combo with {partners} that Bracket {bracket} does not allow"
    return plan, basics, None, why


def _card_rows(plan, ctx, db, cost):
    rows = []
    for name in plan.order:
        f = plan.m.facts(name)
        if f.basic:
            continue
        sc = ctx["scores"].get(name) or {}
        rows.append({"name": name, "section": section_of(db.get(name)),
                     "roles": sorted(ctx["role_map"].get(name) or ()), "score": f.score, "price": cost(name),
                     "owned": name in ctx["owned"], "evidence": sc.get("evidence", ""),
                     "kind": sc.get("kind", "none")})
    order = {s: i for i, s in enumerate(SECTIONS)}
    return sorted(rows, key=lambda r: (order.get(r["section"], len(order)), -r["score"], r["name"]))


def _blocked_cards(plan, ctx, db, pool, combos, banned_why):
    """The best cards the bracket kept out: pieces removed for a combo, cards that would complete one, and
    pool cards the Game Changer, extra-turn or mass-land-denial limits refuse: [{"card","reason","score"}]."""
    found = {c: (plan.m.facts(c).score, w) for c, w in banned_why.items()}      # taken out of the list: named
    held = brackets.blocked_adds(ctx["bracket"], combos) if combos else {}
    for name in pool:
        f = plan.m.facts(name)
        if name in plan.cards or name in found or f.score < BLOCKED_MIN_SCORE:
            continue
        ok, why = plan.rule_ok(f)
        if name in held:
            found[name] = (f.score, held[name])
        elif not ok:
            found[name] = (f.score, why)
    top = sorted(found.items(), key=lambda kv: (-kv[1][0], kv[0]))[:BLOCKED_SHOWN]
    return [{"card": c, "reason": _short_block(why, ctx["bracket"]), "score": sc} for c, (sc, why) in top]


def build(ctx, db, *, budget=None, combos_fn=None, allow_combos=False, prices=None):
    """A 100-card list around ctx's commanders: exactly the land target, role counts near the bracket's
    targets, the spec's include cards in, its exclude cards out, within `budget` and the bracket's limits.
    The fantasy cost is the same build with the theme weight at 0, compared under power-only scores."""
    warnings = list(ctx["warnings"])
    commanders, bracket, ci, spec = list(ctx["commanders"]), ctx["bracket"], ctx["ci"], ctx["spec"]
    includes = _usable_includes(ctx, db, warnings)
    themed = bool(spec.get("weight")) and bool(ctx["evidence"].get("theme_weights"))
    scores0 = None
    if themed:
        scores0 = score.card_scores(ctx["evidence"], dict(spec, weight=0.0), db, ctx["role_map"],
                                    names=list(ctx["scores"]))
    model = Model(ctx, db)
    model0 = Model(ctx, db, scores0) if themed else None

    skip = set(commanders) | set(ctx["exclude"])
    everything = _candidates(ctx, db, skip)
    spells = [n for n in everything if not db.get(n)["land"]]
    lands = [n for n in everything if db.get(n)["land"]]
    models = [model] + ([model0] if themed else [])   # the power-only deck may want cards the themed skips
    price, owned = dict(prices or {}), set(ctx["owned"])

    def make(model_):
        return lambda banned: _assemble(ctx, db, model_, pool_spells, pool_lands, price, owned, budget,
                                        banned, includes, commanders, {})

    size = MAX_CANDIDATES
    while True:
        pool_spells = sorted({n for m in models for n in _prune(spells, m, size)})
        pool_lands = sorted({n for m in models for n in _prune(lands, m, MAX_LAND_CANDIDATES)})
        pool_all = sorted(set(pool_spells) | set(pool_lands) | set(includes))
        if budget is not None:
            price.update(_price_map([n for n in pool_all if n not in price], ctx, db, prices, warnings))
        plan, basics, combos, banned_why = _repair_combos(make(model), ctx, db, commanders, combos_fn,
                                                          allow_combos, warnings)
        # A budget that the best 250 cards cannot meet may be met by cheaper ones further down the list
        if budget is None or not plan.short or size >= len(spells):
            break
        size += MAX_CANDIDATES
    if plan.short:
        warnings.append(f"Only {plan.slots - plan.short} of {plan.slots} nonland slots could be filled "
                        f"within the budget and the bracket's limits; {plan.short} more basic land(s) fill "
                        "the rest.")

    final_names = plan.names()
    report = brackets.check(commanders, final_names, bracket, db, combos=combos)
    if budget is None:
        shown = [n for n in plan.order if not plan.m.facts(n).basic]
        price.update(_price_map(shown, ctx, db, prices, warnings))
    cost = lambda n: 0.0 if n in owned else price.get(n)
    rows = _card_rows(plan, ctx, db, cost)
    spent = sum(r["price"] or 0.0 for r in rows)
    if budget is not None and spent > budget + 0.005:
        warnings.append(f"The cards you asked to include cost ${spent:.2f}, over the ${budget:.2f} budget.")

    fantasy_cost = None
    if themed:
        plan0, _, _, _ = _repair_combos(make(model0), ctx, db, commanders, combos_fn, allow_combos, [])
        fantasy_cost = _fantasy_cost(ctx, db, plan, plan0, scores0)

    value = deck_value(final_names, ctx, db)
    return {"command": "build", "commanders": commanders, "ci": ci, "bracket": bracket, "budget": budget,
            "spent": round(spent, 2), "spec": spec, "cards": rows, "basics": basics,
            "count": len(final_names) + len(commanders), "roles": value["roles"], "targets": ctx["targets"],
            "value": value["total"], "fantasy_cost": fantasy_cost, "bracket_check": report,
            "blocked": _blocked_cards(plan, ctx, db, pool_all, combos, banned_why),
            "warnings": _dedupe(warnings), "sources": ctx["sources"]}


def _fantasy_cost(ctx, db, themed_plan, plain_plan, scores0):
    """What the theme costs: the themed deck and the power-only deck, both valued with the theme weight at 0.
    The themed deck is itself a candidate for "strongest", so the gap is never negative. gap_pct is relative
    to the strongest deck's card quality (scores plus role values), not its land term."""
    ctx0 = dict(ctx, scores=scores0)
    themed, plain = deck_value(themed_plan.names(), ctx0, db), deck_value(plain_plan.names(), ctx0, db)
    best = plain if plain["total"] >= themed["total"] else themed
    gap = best["total"] - themed["total"]
    themed_in = set(themed_plan.cards)
    left_out = sorted((n for n in plain_plan.cards if n not in themed_in and not plain_plan.m.facts(n).land),
                      key=lambda n: (-plain_plan.m.facts(n).score, n))[:THEME_SHOWN]
    weights, picks = ctx["evidence"]["theme_weights"], []
    for name in themed_plan.cards:
        if themed_plan.m.facts(name).land:        # a land's pull is mostly list noise, not the fantasy
            continue
        pulls = (ctx["scores"].get(name) or {}).get("pulls") or {}
        top = max(pulls, key=lambda t: weights.get(t, 1.0) * pulls[t], default=None)
        if top and pulls[top] > 0:
            picks.append((ctx["scores"][name]["parts"]["theme"], name, top, pulls[top]))
    picks.sort(key=lambda x: (-x[0], x[1]))
    return {"power_with_theme": themed["total"], "power_max": best["total"], "gap": gap,
            "gap_pct": 100.0 * gap / best["quality"] if best["quality"] > 0 else 0.0,
            "left_out": [{"name": n, "score": plain_plan.m.facts(n).score,
                          "evidence": (scores0.get(n) or {}).get("evidence", "")} for n in left_out],
            "theme_picks": [{"name": n, "theme": t, "pull": p} for _, n, t, p in picks[:THEME_SHOWN]]}


# ----------------------------------------------------------------------------- suggest
def _playstyle_themes(spec):
    style = spec.get("playstyle") or "value"
    return next((list(p["themes"]) for p in fantasy.menu()["playstyles"] if p["slug"] == style), [])


def _rate(decks, of):
    return decks / of if of else 0.0


def suggest(spec, db, *, colors=None, budget=None, owned=(), limit=10, sources=None, refresh=None,
            offline=None):
    """Commanders that fit the themes (or the playstyle's themes) at the spec's bracket, best first, each with
    the numbers behind its rank. Candidates come from EDHREC's theme pages; the first ranking uses deck counts
    only, and the top `limit` get the slower extras: the price of their core cards, how much of their top
    cards you own, and their tournament record at Bracket 4 and up. Commanders whose core cards cost more than
    `budget` are dropped (with a warning) and the next ones take their place."""
    sources = tuple(config.SOURCES if sources is None else sources)
    kw = {"refresh": refresh, "offline": offline}
    bracket = spec["bracket"]
    warnings, info = [], {}
    want = None if not colors else set("".join(colors).upper())
    result = {"command": "suggest", "spec": spec, "bracket": bracket,
              "filters": {"colors": None if want is None else "".join(c for c in "WUBRG" if c in want),
                          "budget": budget},
              "commanders": [], "warnings": warnings, "sources": info}
    if "edhrec" not in sources:
        warnings.append("suggest needs EDHREC (its theme pages list the commanders), and EDHREC is off. "
                        "Turn it on with --sources or MTG_COMMANDER_SOURCES.")
        return result
    style_themes = _playstyle_themes(spec)
    themes = list(spec.get("themes") or []) or style_themes
    if not themes:
        warnings.append("Pick a theme (--theme) or a playstyle (--playstyle) so there is something to match.")
        return result
    failures = collections.defaultdict(list)            # (source, reason) -> what it could not read

    def guard(label, fn, *a, **k):
        try:
            return fn(*a, **k)
        except net.NotFound:
            return None
        except net.FetchError as e:
            failures[(e.source, e.reason)].append(label)
            return None

    index = {}
    for t in themes:
        for c in guard(f"the {t} theme", edhrec.theme_commanders, t, **kw) or []:
            rec = db.get(c["name"])
            if (rec is None or not rec["commander_ok"] or rec["legal"] != "legal"
                    or (want is not None and not set(rec["ci"]) <= want)):
                continue
            entry = index.setdefault(rec["name"], {"rec": rec, "listed": {}})
            entry["listed"][t] = c["decks"]
    ranked = sorted(index.values(), key=lambda e: (-sum(e["listed"].values()), e["rec"]["name"]))
    ranked = ranked[:SUGGEST_CANDIDATES]

    held = set(_canonical(owned, db, "owned", warnings))
    candidates = []
    for entry in ranked:
        name = entry["rec"]["name"]
        meta = guard(f"{name}'s page", edhrec.commander_meta, [name], **kw)
        if not meta or not meta["n_decks"]:
            continue
        n = meta["n_decks"]
        tags = {t["slug"]: t["count"] for t in meta["taglinks"]}
        shares = {t: {"decks": tags.get(t, entry["listed"].get(t, 0)), "of": n} for t in themes}
        if sum(sh["decks"] for sh in shares.values()) < MIN_THEME_DECKS:
            continue                                    # the playstyle term would otherwise carry it
        for sh in shares.values():
            sh["share"], sh["score_share"] = _rate(sh["decks"], n), sh["decks"] / (n + SHARE_SHRINK)
        style_share = sum(tags.get(t, 0) for t in style_themes) / n
        at_bracket = meta["bracket_counts"].get(bracket, 0)
        salt = meta.get("salt")
        mean_share = sum(sh["score_share"] for sh in shares.values()) / len(themes)
        base = (mean_share + PLAYSTYLE_WEIGHT * style_share
                + BRACKET_DECKS_WEIGHT * math.log10(1 + at_bracket))
        if spec.get("keep_fun") and salt is not None:
            base -= SALT_WEIGHT * max(0.0, salt - 1)
        candidates.append({"rec": entry["rec"], "meta": meta, "shares": shares, "style_share": style_share,
                           "at_bracket": at_bracket, "salt": salt, "score": base})
        info["edhrec"] = _older(info.get("edhrec"), meta.get("fetched"))
    candidates.sort(key=lambda c: (-c["score"], c["rec"]["name"]))

    kept, dropped = [], []
    for cand in candidates:
        if len(kept) >= limit:
            break
        extras = _suggest_extras(cand, db, held, bracket, budget, kw, guard)
        if extras is None:
            dropped.append(cand["rec"]["name"])
            continue
        cand.update(extras)
        cand["score"] += (OWNED_WEIGHT * cand["owned_share"] if cand["owned_share"] is not None else 0.0)
        t = cand["tournament"]
        if bracket >= 4 and t and t["entries"] >= TOURNAMENT_MIN:
            cand["score"] += TOURNAMENT_WEIGHT * (t["conversion"] - TOURNAMENT_BASELINE)
        kept.append(cand)
    kept.sort(key=lambda c: (-c["score"], c["rec"]["name"]))
    for (source, reason), labels in failures.items():
        more = f" and {len(labels) - 3} more" if len(labels) > 3 else ""
        name = score.SOURCE_NAMES.get(source, source)
        warnings.append(f"{name} unavailable for {', '.join(labels[:3])}{more}: {reason}")
    if dropped:
        warnings.append(f"Left out because their core cards cost more than ${budget:,g}: "
                        + ", ".join(dropped) + ".")
    if info.get("edhrec"):
        age = score._age_days(info["edhrec"]["fetched"])
        info["edhrec"].update(age_days=age, cache="stale" if age and age > config.TTL["edhrec"] / config.DAY
                              else "fresh")
        if info["edhrec"]["cache"] == "stale":
            warnings.append(f"EDHREC data is {age} days old (offline or the site failed)")
    result["commanders"] = [_suggestion(rank, c, themes, style_themes, spec, bracket, bool(held))
                            for rank, c in enumerate(kept, 1)]
    return result


def _older(old, fetched):
    """The oldest `fetched` seen so far, as a sources entry (suggest fills in the age and cache state)."""
    if not fetched or (old and old["fetched"] <= fetched):
        return old
    return {"fetched": fetched, "cache": "fresh", "age_days": None}


def _suggest_extras(cand, db, held, bracket, budget, kw, guard):
    """core_cost, owned_share and tournament for one candidate, or None when its core cards cost more than the
    budget."""
    name = cand["rec"]["name"]
    sig = (guard(f"{name}'s card lists", edhrec.signals, [name], None, **kw) or [None])[0]
    core_cost, owned_share = None, None
    if sig:
        cards = []
        for raw, st in sig["cards"].items():
            rec = db.get(raw)
            if rec is not None and "Basic" not in rec["types"] and rec["name"] != name:
                cards.append((rec, _rate(st["decks"], st["of"])))
        core_cost = sum(rec["price"] or 0.0 for rec, rate in cards if rate >= CORE_INCLUSION)
        if held:
            spells = [x for x in cards if not x[0]["land"]]
            top = sorted(spells, key=lambda x: (-x[1], x[0]["name"]))[:OWNED_TOP]
            owned_share = sum(rec["name"] in held for rec, _ in top) / len(top) if top else 0.0
        if budget is not None and core_cost > budget:
            return None
    tournament = None
    if bracket >= 4:
        stats = guard(f"{name}'s tournament results", edhtop16.commander_stats, [name], **kw)
        if stats:
            tournament = {"entries": stats["entries"], "conversion": stats["conversion"]}
    return {"core_cost": core_cost, "owned_share": owned_share, "tournament": tournament}


def _suggestion(rank, c, themes, style_themes, spec, bracket, has_owned):
    n, evidence = c["meta"]["n_decks"], []
    for t in themes:
        sh = c["shares"][t]
        evidence.append(f"{t}: {sh['decks']:,} of {n:,} decks ({sh['share']:.1%})")
    if style_themes and c["style_share"] > 0:
        label = next((p["label"] for p in fantasy.menu()["playstyles"] if p["slug"] == spec.get("playstyle")),
                     spec.get("playstyle"))
        evidence.append(f"{label} themes: {c['style_share']:.0%} of its decks carry one")
    evidence.append(f"{c['at_bracket']:,} Bracket {bracket} decks")
    if c["salt"] is not None:
        evidence.append(f"salt {c['salt']:.2f}")
    if c["core_cost"] is not None:
        evidence.append(f"core cards about ${c['core_cost']:,.0f}")
    if has_owned and c["owned_share"] is not None:
        evidence.append(f"you own {c['owned_share']:.0%} of its top cards")
    t = c["tournament"]
    if t:
        caveat = "" if t["entries"] >= TOURNAMENT_CONFIDENT else " (too few to judge)"
        evidence.append(f"EDHTop16: {t['entries']:,} entries, {t['conversion']:.0%} top cut{caveat}")
    return {"rank": rank, "name": c["rec"]["name"], "ci": c["rec"]["ci"], "score": c["score"],
            "theme_share": c["shares"], "playstyle_share": c["style_share"], "bracket_decks": c["at_bracket"],
            "salt": c["salt"], "tournament": t, "core_cost": c["core_cost"], "owned_share": c["owned_share"],
            "evidence": evidence}
