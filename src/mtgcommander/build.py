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
affordable swap above MIN_GAIN. `build` fills the nonland slots greedily, swaps until nothing improves, then
picks lands. Both are local searches, not optima: a swap that needs two cards to change at once is invisible
to them, and each result says what it left out and why.

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

Facts = collections.namedtuple("Facts", "name score theme roles w land topend gc extra mld sources basic")


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
    under power-only scores)."""

    def __init__(self, ctx, db, scores=None):
        self.db, self.ci = db, ctx["ci"]
        self.scores = ctx["scores"] if scores is None else scores
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
                found = Facts(name, 0.0, 0.0, (), 0.0, False, False, 0, 0, 0, frozenset(), False)
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
                              lands_for, basic)
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
    flags and, for lands, colors) differ only by score, so each such group is represented by its weakest
    member. That keeps a round near 250 adds x 35 groups instead of 250 x 100."""

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
        self.bought = {}                                 # name -> price paid in this run (refunded on a cut)
        self.spent = 0.0
        self.locked = set()                              # names that may not be cut
        self._rule_memo = {}

    def clone(self):
        """An independent copy (the model, card index and price table are shared; they never change)."""
        other = Plan(self.m, self.db, self.ci, self.bracket, prices=self.prices, owned=self.owned,
                     budget=self.budget, blocked=self.blocked)
        other.cards, other.order = collections.Counter(self.cards), list(self.order)
        other.counts, other.mass, other.score_sum = dict(self.counts), dict(self.mass), self.score_sum
        other.rules, other.sources = dict(self.rules), collections.Counter(self.sources)
        other.bought, other.spent, other.locked = dict(self.bought), self.spent, set(self.locked)
        other._rule_memo = self._rule_memo           # depends only on (card, rule state), so it can be shared
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
        refund = self.bought.pop(f.name, 0.0)
        self.spent -= refund

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
        gone = cut or Facts("", 0, 0, (), 0.0, False, False, 0, 0, 0, frozenset(), False)
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

    # --- search
    def _groups(self, cuts):
        """Cut candidates grouped by interchangeable role signature, weakest first within a group:
        [[(Facts, loss, refund), ...], ...]."""
        groups = {}
        for name in cuts:
            f = self.m.facts(name)
            sig = (f.roles, f.land, f.topend, f.gc, f.extra, f.mld, f.sources)
            groups.setdefault(sig, []).append(f)
        out = []
        for members in groups.values():
            members.sort(key=lambda f: (f.score, f.name))
            out.append([(f, self.m.cut_value(self.counts, self.mass, f), self.bought.get(f.name, 0.0))
                        for f in members])
        return out

    def best_swap(self, cuts, adds, *, min_gain=MIN_GAIN, lam=0.0, watch=None):
        """The best (gain, cut, add) among `cuts` and `adds` that is affordable, passes the bracket's limits
        and beats `min_gain`, or None. With `lam` > 0 the best is the one with the most gain minus `lam` per
        dollar of the add (the gain returned is still the real one). `watch`, if given, collects what almost
        happened:
        watch["blocked"][add] = (best gain, why the rules or a combo forbid it) and
        watch["costly"][add] = (best gain, price) for adds that only the budget stopped."""
        rem, best, best_key = self.remaining(), None, None
        groups = self._groups(cuts)
        for a in adds:
            fa = self.m.facts(a)
            need = self.price(a)
            if rem is not None and need is None:
                continue
            win = self.m.add_value(self.counts, self.mass, fa)
            risky = bool(fa.gc or fa.extra or fa.mld)
            any_gain, rule_pass, hit = None, False, None
            for members in groups:
                for fc, loss, refund in members:
                    if (fc.land or fa.land) and not self.mana_ok(fc, fa):
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
        """A basic land for a slot nothing else can fill: the color with the fewest lands per pip."""
        if not self.colors:
            return "Wastes"
        pips = collections.Counter()
        for n, k in self.cards.items():
            rec = self.db.get(n)
            if rec and not rec["land"]:
                for c, v in _pips(rec, self.ci).items():
                    pips[c] += v * k
        return BASIC_FOR[min(self.colors, key=lambda c: (self.sources[c] / (pips[c] + 1), c))]


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
        fc = self.m.facts(cut)
        sc_add, sc_cut = self.ctx["scores"].get(add) or {}, self.ctx["scores"].get(cut) or {}
        return {"cut": cut, "add": add, "gain": gain, "price": self.cost(add), "owned": add in self.owned,
                "forced": forced, "reason": reason, "fills": fills,
                "evidence_add": sc_add.get("evidence", ""), "kind_add": sc_add.get("kind", "none"),
                "evidence_cut": "basic land" if fc.basic else sc_cut.get("evidence", "not scored")}


def _optional_swaps(plan, ledger, pool, max_swaps, lam, watch):
    """Apply up to `max_swaps` best swaps to `plan`; returns their records, best first as they were found."""
    out = []
    while len(out) < max_swaps:
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


def upgrade(ctx, deck, db, *, budget=None, max_swaps=15, combos_fn=None, allow_combos=False, prices=None):
    """Ranked cut/add swaps for `deck` ({"commanders", "cards": [(count, name)]}, names canonical) within a
    budget and the target bracket. See the module docstring for the method; the result shape is in the design
    doc ("Command line and result shapes"). The deck's own cards and `ctx["owned"]` cost nothing.

    With a budget the greedy "best gain first" can spend it all on one pricey card, so the optional swaps are
    run again with a growing penalty per dollar (PRICE_LAMBDAS) and the run that ends with the most valuable
    deck wins. Every printed gain is still the real gain of that swap at the moment it was made."""
    warnings = list(ctx["warnings"])
    bracket, ci = ctx["bracket"], ctx["ci"]
    commanders = list(deck.get("commanders") or ctx["commanders"])
    model = Model(ctx, db)
    deck_names = [n for k, n in deck["cards"] for _ in range(k)]
    includes, spec_exclude = set(ctx["include"]), set(ctx["exclude"])

    combos = _find_combos(combos_fn, commanders, deck_names, warnings)
    if allow_combos:
        combos = {"included": [], "almost": []}
        warnings.append("Combo limits are lifted (--allow-combos); no combo is checked or blocked.")
    blocked = {} if combos is None else brackets.blocked_adds(bracket, combos)
    report_before = brackets.check(commanders, deck_names, bracket, db, combos=combos)

    taken_names = set(deck_names) | set(commanders) | spec_exclude
    pool = _prune(_candidates(ctx, db, taken_names), model, MAX_CANDIDATES)
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

    # --- the best swaps, one at a time; with a budget, try several prices-matter settings
    watch = {}
    trial = plan.clone()
    taken = _optional_swaps(trial, ledger, pool, max_swaps, 0.0, watch)
    if budget is not None and _budget_bound(watch):
        for lam in PRICE_LAMBDAS[1:]:
            other, other_watch = plan.clone(), {}
            got = _optional_swaps(other, ledger, pool, max_swaps, lam, other_watch)
            if other.value() > trial.value() + EPS:
                trial, taken, watch = other, got, other_watch
    plan, swaps = trial, swaps + taken

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
    return {"command": "upgrade",
            "deck": {"name": deck.get("name", ""), "commanders": commanders,
                     "count": len(final_names) + len(commanders), "ci": ci},
            "bracket": bracket, "budget": budget, "spent": round(spent, 2), "spec": ctx["spec"],
            "swaps": swaps, "blocked": blocked_list, "cheap_adds": cheap,
            "roles_before": counts_before, "roles_after": value_after["roles"], "targets": ctx["targets"],
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

    # nonbasic lands by score, leaving room for at least one basic per color
    plan.budget = budget
    room = land_target - len(plan.colors) if plan.colors else land_target
    for name in sorted((n for n in lands if n not in banned and n not in plan.cards),
                       key=lambda n: (-model.facts(n).score, n)):
        f = model.facts(name)
        if plan.counts["land"] >= room or f.score < NONBASIC_MIN:
            break
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
