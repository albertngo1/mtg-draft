"""Tests for build.py: the value of a deck (role marginals, lands, top end), the exactness of the swap
arithmetic, `prepare`, `upgrade`, `build` and `suggest`.

Everything runs on a synthetic world of cards with known scores, roles and prices (World below), so each
assertion is a worked example rather than a snapshot of real data. Combos and prices come in through the
`combos_fn` and `prices` arguments; providers and net are closed, so nothing here can reach the network."""
import math, random, time, unittest
from unittest import mock
from mtgcommander import build, carddb, net, roles, score
from mtgcommander.providers import edhrec, edhtop16

CMDR = "Squirrel King"
EM = "—"


def scry(name, types="Creature", cmc=2.0, cost="", ci="", text="", price=1.0, gc=False, produced=(),
         legal="legal", rank=None, **extra):
    """A Scryfall-shaped card; carddb.card_record turns it into the record the code under test reads."""
    obj = {"oracle_id": "w-" + name, "name": name, "layout": "normal", "mana_cost": cost, "cmc": float(cmc),
           "type_line": types, "oracle_text": text, "color_identity": list(ci), "keywords": [],
           "legalities": {"commander": legal}, "prices": {"usd": str(price)}, "game_changer": gc}
    if produced:
        obj["produced_mana"] = list(produced)
    if rank:
        obj["edhrec_rank"] = rank
    obj.update(extra)
    return obj


def score_record(value, theme=0.0):
    return {"score": value, "parts": {"base": value - theme, "resid": 0.0, "theme": theme, "salt": 0.0},
            "kind": "builder", "evidence": f"test score {value:.2f}", "n": 100, "pulls": {}}


class World:
    """Cards with a score, a role and a price, plus the db / role_map / scores / prices tests hand to build."""

    def __init__(self):
        self.objs, self.values, self.role_of, self.price_of = [], {}, {}, {}
        self.card(CMDR, types=f"Legendary Creature {EM} Squirrel", cmc=3, cost="{1}{B}{G}", ci="BG",
                  power="2", toughness="2")
        for basic, color in (("Forest", "G"), ("Swamp", "B")):
            self.card(basic, types=f"Basic Land {EM} {basic}", cmc=0, ci=color, produced=[color], price=0.1)
        self.card("Wastes", types="Basic Land", cmc=0, produced=["C"], price=0.1)

    def card(self, name, **kw):
        self.objs.append(scry(name, **kw))

    def add(self, name, value, role=None, price=1.0, **kw):
        self.card(name, price=price, **kw)
        self.values[name] = value
        self.price_of[name] = price
        if role:
            self.role_of[name] = {role}

    def group(self, prefix, count, top, step, role=None, **kw):
        """`count` cards named '<prefix> 01'.. scoring top, top - step, ..."""
        for i in range(1, count + 1):
            self.add(f"{prefix} {i:02d}", round(top - step * i, 4), role, **{"price": 1.0 + (i % 5), **kw})

    def db(self):
        cards = {}
        for obj in self.objs:
            rec = carddb.card_record(obj)
            cards[rec["name"]] = rec
        return carddb.CardDB(cards)

    def scores(self, names=None):
        return {n: score_record(v) for n, v in self.values.items() if names is None or n in names}

    def prices(self):
        return dict(self.price_of)


def standard_world(cost=None):
    """A Commander world big enough to build from: every role with more cards than its maximum, 70 plain
    creatures, 10 top-end ones, 5 Game Changers, 17 nonbasic lands, and the cards that break rules."""
    w = World()
    cost = cost or (lambda i: "{2}{G}" if i % 2 else "{2}{B}")
    w.group("Rock", 14, 0.80, 0.04, "ramp", types="Artifact", cmc=2, cost="{2}")
    w.group("Draw", 14, 0.75, 0.04, "draw", types="Sorcery", cmc=3, cost="{2}{G}")
    w.group("Kill", 12, 0.70, 0.04, "removal", types="Instant", cmc=2, cost="{1}{B}")
    w.group("Wipe", 5, 0.60, 0.05, "wipe", types="Sorcery", cmc=4, cost="{2}{B}{B}")
    w.group("Ward", 6, 0.50, 0.05, "protection", types="Instant", cmc=1, cost="{G}")
    w.group("Raise", 6, 0.45, 0.05, "recursion", types="Sorcery", cmc=3, cost="{2}{B}")
    w.group("Seek", 4, 0.40, 0.05, "tutor", types="Sorcery", cmc=2, cost="{1}{B}")
    w.group("Finish", 8, 0.65, 0.05, "finisher", types="Creature", cmc=4, cost="{3}{G}")
    for i in range(1, 71):
        w.add(f"Beast {i:02d}", round(0.60 - 0.008 * i, 4), None, price=1.0 + (i % 4), types="Creature", cmc=3,
              cost=cost(i))
    w.group("Titan", 10, 0.62, 0.01, None, types="Creature", cmc=7, cost="{5}{B}{G}")
    w.group("Power", 5, 0.92, 0.02, None, types="Artifact", cmc=3, cost="{3}", price=20.0, gc=True)
    for i in range(1, 13):
        w.add(f"Dual {i:02d}", round(0.90 - 0.06 * i, 4), None, price=0.5 * i, types="Land", cmc=0,
              produced=["B", "G"], ci="BG")
    for i in range(1, 6):
        w.add(f"Utility {i:02d}", round(0.30 - 0.04 * i, 4), None, price=0.5, types="Land", cmc=0, produced=["C"])
    w.add("Combo A", 0.95, None, price=3.0, types="Creature", cmc=3, cost="{2}{G}")
    w.add("Combo B", 0.94, None, price=3.0, types="Creature", cmc=3, cost="{2}{B}")
    w.add("Blue Spell", 0.99, None, types="Instant", cmc=2, cost="{1}{U}", ci="U")
    w.add("Banned Spell", 0.99, None, types="Instant", cmc=2, cost="{1}{B}", ci="B", legal="banned")
    return w


def multirole_world():
    """standard_world plus cards that fill several roles at once, the tag pile-ups that role mass is for."""
    w = standard_world()
    kinds = ({"removal", "wipe"}, {"draw", "ramp"}, {"removal", "protection", "recursion", "finisher"},
             {"draw", "removal", "finisher"})
    for i in range(1, 13):
        name = f"Multi {i:02d}"
        w.add(name, round(0.10 + 0.02 * i, 4), None, price=1.0 + i % 3, types="Sorcery", cmc=3, cost="{2}{B}")
        w.role_of[name] = set(kinds[i % 4])
    return w


def zero_targets(**over):
    """Targets that value no role, so a test sees only the scores (a land is still worth 1.0 up to 99)."""
    t = {r: {"min": 0, "target": 0, "max": 0} for r in roles.ROLES}
    t["land"] = {"min": 0, "target": 99, "max": 99}
    t["topend"] = {"max": 99}
    t.update(over)
    return t


SPEC = {"themes": [], "playstyle": "value", "include": [], "exclude": [], "weight": 0.5, "keep_fun": True,
        "bracket": 3, "text": None}


def make_ctx(world, db, *, names=None, bracket=3, targets=None, **over):
    ctx = {"commanders": [CMDR], "ci": "BG", "bracket": bracket, "spec": dict(SPEC, bracket=bracket),
           "evidence": {"theme_weights": {}, "cards": {}, "meta": None}, "role_map": dict(world.role_of),
           "scores": world.scores(names), "targets": targets or roles.targets(bracket, "value", ci="BG"),
           "owned": set(), "include": [], "exclude": set(), "warnings": [], "sources": {}}
    ctx.update(over)
    return ctx


def deck_of(*names, commanders=(CMDR,)):
    return {"commanders": list(commanders), "cards": [(1, n) for n in names]}


class Isolated(unittest.TestCase):
    def setUp(self):
        for fn in ("fetch_json", "request", "download"):
            mock.patch.object(net, fn, side_effect=AssertionError(f"net.{fn} must not run in a test")).start()
        self.addCleanup(mock.patch.stopall)


# ----------------------------------------------------------------------------- the value of a deck
class RoleValueTests(Isolated):
    """Marginal value of the i-th card of a role with min 2, target 4, max 6 (beta = 0.2):
         i = 1, 2 -> 1.5 * beta = 0.3        below the minimum
         i = 3, 4 -> beta = 0.2              up to the target
         i = 5    -> 0.2 * (6 - 5 + 1) / (6 - 4 + 1) = 0.1333   fading toward the maximum
         i = 6    -> 0.2 * 1 / 3 = 0.0667
         i = 7+   -> 0                       nothing past the maximum"""
    MARGINALS = [0.3, 0.3, 0.2, 0.2, 0.2 * 2 / 3, 0.2 / 3, 0.0, 0.0]

    def test_the_role_marginal_at_each_stage(self):
        for i, expected in enumerate(self.MARGINALS, 1):
            with self.subTest(i=i):
                self.assertAlmostEqual(build.role_marginal(i, 2, 4, 6), expected)

    def test_a_role_whose_target_is_its_maximum_has_no_fade(self):
        self.assertEqual([build.role_marginal(i, 0, 2, 2) for i in (1, 2, 3)], [0.2, 0.2, 0.0])

    def test_the_land_marginal_at_each_stage(self):
        # target 3, max 5: full value up to the target, 0.2 * 2/3 and 0.2 * 1/3 after it, then a cost
        got = [build.land_marginal(i, 3, 5) for i in range(1, 8)]
        self.assertEqual(got[:3], [1.0, 1.0, 1.0])
        self.assertAlmostEqual(got[3], 0.2 * 2 / 3)
        self.assertAlmostEqual(got[4], 0.2 / 3)
        self.assertEqual(got[5:], [-0.2, -0.2])

    def test_deck_value_sums_the_marginals(self):
        w = World()
        for i in range(1, 8):
            w.add(f"Rock {i}", 0.0, "ramp", types="Artifact")
        w.add("Staple", 0.5, None)
        db, names = w.db(), [f"Rock {i}" for i in range(1, 8)]
        ctx = make_ctx(w, db, targets=zero_targets(ramp={"min": 2, "target": 4, "max": 6}))
        for k, expected in enumerate([0, 0.3, 0.6, 0.8, 1.0, 1.0 + 0.2 * 2 / 3, 1.2, 1.2]):
            with self.subTest(ramp_cards=k):
                self.assertAlmostEqual(build.deck_value(names[:k], ctx, db)["total"], expected)
        # a card's own score adds to the role value
        self.assertAlmostEqual(build.deck_value(names[:2] + ["Staple"], ctx, db)["total"], 0.6 + 0.5)

    def test_lands_are_worth_a_full_point_each_up_to_the_target(self):
        w = World()
        w.add("Dual", 0.4, None, types="Land", produced=["B", "G"], ci="BG")
        db = w.db()
        ctx = make_ctx(w, db, targets=zero_targets(land={"min": 2, "target": 3, "max": 5}))
        for lands, expected in ((["Forest"], 1.0), (["Forest"] * 3, 3.0), (["Forest"] * 4, 3 + 0.2 * 2 / 3),
                                (["Forest"] * 6, 3 + 0.2 * 2 / 3 + 0.2 / 3 - 0.2)):
            with self.subTest(lands=len(lands)):
                self.assertAlmostEqual(build.deck_value(lands, ctx, db)["total"], expected)
        # a nonbasic land scores like any card, and is a land too
        self.assertAlmostEqual(build.deck_value(["Dual", "Forest"], ctx, db)["total"], 2.0 + 0.4)

    def test_top_end_beyond_the_limit_costs_a_tenth_each(self):
        w = World()
        for i in range(1, 6):
            w.add(f"Titan {i}", 0.5, None, cmc=7)
        db, names = w.db(), [f"Titan {i}" for i in range(1, 6)]
        ctx = make_ctx(w, db, targets=zero_targets(topend={"max": 3}))
        self.assertAlmostEqual(build.deck_value(names[:3], ctx, db)["total"], 1.5)
        self.assertAlmostEqual(build.deck_value(names, ctx, db)["total"], 2.5 - 0.2)

    def test_power_is_the_total_without_the_theme_part(self):
        w = World()
        w.add("Themed", 0.5, None)
        db = w.db()
        ctx = make_ctx(w, db, targets=zero_targets())
        ctx["scores"]["Themed"] = score_record(0.5, theme=0.12)
        got = build.deck_value(["Themed"], ctx, db)
        self.assertAlmostEqual(got["total"], 0.5)
        self.assertAlmostEqual(got["theme"], 0.12)
        self.assertAlmostEqual(got["power"], 0.38)
        self.assertAlmostEqual(got["quality"], 0.5)      # no lands, so no land term to remove

    def test_scores_can_be_swapped_for_the_fantasy_cost(self):
        w = World()
        w.add("Themed", 0.5, None)
        db = w.db()
        ctx = make_ctx(w, db, targets=zero_targets())
        other = {"Themed": score_record(0.2)}
        self.assertAlmostEqual(build.deck_value(["Themed"], ctx, db, scores=other)["total"], 0.2)

    def test_it_reports_the_role_counts_and_lands(self):
        w = standard_world()
        db, ctx = w.db(), make_ctx(w, w.db())
        names = ["Rock 01", "Rock 02", "Draw 01", "Forest", "Swamp", "Dual 01", "Titan 01"]
        got = build.deck_value(names, ctx, db)
        self.assertEqual(got["roles"], roles.counts(names, ctx["role_map"], db))
        self.assertEqual((got["land"], got["roles"]["ramp"], got["roles"]["topend"]), (3, 2, 1))

    def test_basic_lands_have_no_score(self):
        w = World()
        w.add("Odd", 0.3, None)
        db = w.db()
        ctx = make_ctx(w, db, targets=zero_targets(land={"min": 0, "target": 0, "max": 0}))
        ctx["scores"]["Forest"] = score_record(0.9)       # even if a caller scored one, a basic is not worth it
        self.assertAlmostEqual(build.deck_value(["Forest"], ctx, db)["total"], -0.2)


class RoleMassTests(Isolated):
    """A card tagged with m roles gives 1/sqrt(m) to each, so its roles together are worth about sqrt(m) * beta
    while all of them are short, not m * beta. Between whole cards a role's value is linear."""
    # every role under its target and over its minimum (0), so each card's marginal is beta = 0.2
    TARGETS = zero_targets(**{r: {"min": 0, "target": 4, "max": 6} for r in roles.ROLES})

    def world(self):
        w = World()
        for name, held in (("Solo", {"ramp"}), ("Pair", {"ramp", "draw"}),
                           ("Triple", {"ramp", "draw", "removal"}), ("Quad", {"ramp", "draw", "removal", "wipe"})):
            w.add(name, 0.0, None, types="Artifact")
            w.role_of[name] = held
        return w

    def value(self, name, targets=None):
        w = self.world()
        db = w.db()
        return build.deck_value([name], make_ctx(w, db, targets=targets or self.TARGETS), db)["total"]

    def test_a_card_with_several_roles_earns_root_m_betas_not_m(self):
        for name, m in (("Solo", 1), ("Pair", 2), ("Triple", 3), ("Quad", 4)):
            with self.subTest(card=name):
                self.assertAlmostEqual(self.value(name), math.sqrt(m) * build.ROLE_BETA)

    def test_a_three_role_card_is_worth_1_73_betas_not_3(self):
        got = self.value("Triple")
        self.assertAlmostEqual(got / build.ROLE_BETA, 1.7320508, places=6)
        self.assertLess(got, 0.6 * 3 * build.ROLE_BETA)          # 0.35 where the three tags used to earn 0.6

    def test_below_the_minimum_each_share_earns_one_and_a_half_betas(self):
        short = zero_targets(**{r: {"min": 3, "target": 4, "max": 6} for r in roles.ROLES})
        self.assertAlmostEqual(self.value("Triple", short), math.sqrt(3) * 1.5 * build.ROLE_BETA)

    def test_whole_card_counts_are_still_whole(self):
        w = self.world()
        db = w.db()
        got = build.deck_value(["Triple", "Pair"], make_ctx(w, db, targets=self.TARGETS), db)
        self.assertEqual((got["roles"]["ramp"], got["roles"]["draw"], got["roles"]["removal"]), (2, 2, 1))

    def test_role_value_is_linear_between_whole_cards_and_flat_past_the_maximum(self):
        w = self.world()
        db = w.db()
        model = build.Model(make_ctx(w, db, targets=zero_targets(ramp={"min": 1, "target": 3, "max": 5})), db)
        # marginals 0.3, 0.2, 0.2, 0.2 * 2/3, 0.2 / 3, then 0
        cum = [0, 0.3, 0.5, 0.7, 0.7 + 0.2 * 2 / 3, 0.7 + 0.2 * 2 / 3 + 0.2 / 3]
        for k, expected in ((0, 0), (0.5, 0.15), (1, 0.3), (1.25, 0.3 + 0.25 * 0.2),
                            (3.5, 0.7 + 0.5 * 0.2 * 2 / 3), (5, cum[5]), (5.5, cum[5]), (40, cum[5]), (-1, 0)):
            with self.subTest(mass=k):
                self.assertAlmostEqual(model.role_value("ramp", k), expected)
        values = [model.role_value("ramp", k / 10) for k in range(0, 71)]
        self.assertTrue(all(a <= b + 1e-12 for a, b in zip(values, values[1:])))     # never decreases

    def test_a_swap_values_a_four_role_card_at_two_betas_and_still_lists_every_role_it_fills(self):
        # Equal scores. Before role mass the four-tag card was worth 4 * beta; now sqrt(4) = 2 betas.
        w = mini(**{"Dud": 0.0, "Plain": 0.30, "Solo": 0.30, "Quad": 0.30})
        w.role_of["Solo"] = {"ramp"}
        w.role_of["Quad"] = {"ramp", "draw", "removal", "wipe"}
        targets = zero_targets(**{r: {"min": 0, "target": 4, "max": 6} for r in roles.ROLES})
        res, _, _ = run_upgrade(w, ["Dud"], ["Plain", "Solo", "Quad"], targets=targets, max_swaps=1)
        self.assertEqual(res["swaps"][0]["add"], "Quad")                     # still the best of the three ...
        self.assertAlmostEqual(res["swaps"][0]["gain"], 0.30 + 2 * build.ROLE_BETA)     # ... but 2 betas, not 4
        self.assertEqual(res["swaps"][0]["fills"], ["ramp", "draw", "removal", "wipe"])  # fills lists all four


class SwapArithmeticTests(Isolated):
    """The search prices a swap from role mass; it must equal re-valuing both decks."""

    def test_swap_gain_equals_the_difference_of_deck_values(self):
        w = multirole_world()
        db, rng = w.db(), random.Random(7)
        ctx = make_ctx(w, db)
        model = build.Model(ctx, db)
        pool = [n for n in w.values if "Blue" not in n and "Banned" not in n]
        for trial in range(300):
            deck = rng.sample(pool, 60) + ["Forest"] * rng.randint(0, 20) + ["Swamp"] * rng.randint(0, 20)
            cut, add = rng.choice(deck), rng.choice([n for n in pool if n not in deck])
            after = list(deck)
            after.remove(cut)
            after.append(add)
            counts = roles.counts(deck, ctx["role_map"], db)
            mass = model.role_mass([model.facts(n) for n in deck])
            before_v, after_v = (build.deck_value(d, ctx, db)["total"] for d in (deck, after))
            with self.subTest(trial=trial, cut=cut, add=add):
                gain = model.swap_gain(counts, mass, model.facts(cut), model.facts(add))
                self.assertAlmostEqual(gain, after_v - before_v)

    def test_the_gain_is_exact_for_cards_that_share_several_roles(self):
        # Every pair of multi-role cards, in decks that leave their roles under, at and over target
        w = multirole_world()
        db, rng = w.db(), random.Random(5)
        ctx = make_ctx(w, db)
        model = build.Model(ctx, db)
        multi = [n for n in w.values if n.startswith("Multi")]
        rest = [n for n in w.values if not n.startswith(("Multi", "Blue", "Banned"))]
        for trial in range(120):
            deck = rng.sample(multi, rng.randint(2, 8)) + rng.sample(rest, rng.randint(0, 50))
            cut = rng.choice([n for n in deck if n.startswith("Multi")])
            add = rng.choice([n for n in multi if n not in deck] or rest)
            after = [n for n in deck if n != cut] + [add]
            counts = roles.counts(deck, ctx["role_map"], db)
            mass = model.role_mass([model.facts(n) for n in deck])
            with self.subTest(trial=trial, cut=cut, add=add):
                gain = model.swap_gain(counts, mass, model.facts(cut), model.facts(add))
                self.assertAlmostEqual(gain, build.deck_value(after, ctx, db)["total"]
                                       - build.deck_value(deck, ctx, db)["total"])

    def test_the_search_finds_the_best_pair_that_trying_every_pair_would(self):
        # The search keeps one cut per group of interchangeable cards; this checks that shortcut loses nothing.
        w = multirole_world()
        db, rng = w.db(), random.Random(11)
        ctx = make_ctx(w, db)
        model = build.Model(ctx, db)
        pool = [n for n in w.values if not n.startswith(("Power", "Blue", "Banned"))]
        for trial in range(25):
            deck = rng.sample(pool, 50) + ["Forest"] * 14 + ["Swamp"] * 14
            plan = build.Plan(model, db, "BG", 3, prices={}, owned=set())
            for n in deck:
                plan.add(n)
            adds = [n for n in pool if n not in deck]
            cuts = list(plan.cards)
            gain_of = lambda c, a: model.swap_gain(plan.counts, plan.mass, model.facts(c), model.facts(a))
            best = max(gain_of(c, a) for c in cuts for a in adds)
            found = plan.best_swap(cuts, adds, min_gain=-1e9)
            with self.subTest(trial=trial):
                self.assertAlmostEqual(found[0], best)
                self.assertAlmostEqual(gain_of(found[1], found[2]), found[0])

    def test_a_swap_inside_one_role_is_worth_only_the_score_difference(self):
        w = standard_world()
        db = w.db()
        ctx = make_ctx(w, db)
        model = build.Model(ctx, db)
        deck = ["Rock 03", "Rock 05", "Rock 07"]
        counts = roles.counts(deck, ctx["role_map"], db)
        mass = model.role_mass([model.facts(n) for n in deck])
        gain = model.swap_gain(counts, mass, model.facts("Rock 07"), model.facts("Rock 01"))
        self.assertAlmostEqual(gain, w.values["Rock 01"] - w.values["Rock 07"])

    def test_a_cut_that_refunds_enough_makes_a_dearer_add_affordable(self):
        # $11 budget, both weak cards bought and the money gone. The $5 upgrade can only be paid for by the
        # $10 card's refund, so the cheaper-to-lose $1 card is not the cut even though it is weaker.
        w = World()
        w.add("Cheap Weak", 0.10, None, price=1.0)
        w.add("Dear Weak", 0.20, None, price=10.0)
        w.add("Upgrade", 0.90, None, price=5.0)
        db = w.db()
        plan = build.Plan(build.Model(make_ctx(w, db, targets=zero_targets()), db), db, "BG", 3,
                          prices=w.prices(), owned=set(), budget=11.0)
        plan.add("Cheap Weak", buy=True)
        plan.add("Dear Weak", buy=True)
        self.assertAlmostEqual(plan.remaining(), 0.0)
        gain, cut, add = plan.best_swap(["Cheap Weak", "Dear Weak"], ["Upgrade"])
        self.assertEqual((cut, add), ("Dear Weak", "Upgrade"))
        self.assertAlmostEqual(gain, 0.90 - 0.20)
        plan.swap(cut, add)
        self.assertAlmostEqual(plan.spent, 1.0 + 5.0)               # the $10 was handed back

    def test_a_clone_is_independent_of_the_plan_it_came_from(self):
        w = standard_world()
        db = w.db()
        plan = build.Plan(build.Model(make_ctx(w, db), db), db, "BG", 3, prices=w.prices(), owned=set())
        plan.add("Rock 01")
        other = plan.clone()
        other.add("Draw 01")
        other.locked.add("Rock 01")
        self.assertEqual((plan.names(), plan.counts["draw"], plan.locked), (["Rock 01"], 0, set()))
        self.assertEqual((other.names(), other.counts["draw"]), (["Rock 01", "Draw 01"], 1))

    def test_the_search_keeps_its_counts_in_step_with_the_cards(self):
        w = standard_world()
        db = w.db()
        ctx = make_ctx(w, db)
        plan = build.Plan(build.Model(ctx, db), db, "BG", 3, prices=w.prices(), owned=set())
        for n in ["Rock 01", "Draw 02", "Forest", "Titan 01", "Dual 03", "Power 01"]:
            plan.add(n)
        plan.remove("Rock 01")
        plan.swap("Draw 02", "Kill 01")
        self.assertEqual({k: v for k, v in plan.counts.items() if v},
                         {k: v for k, v in roles.counts(plan.names(), ctx["role_map"], db).items()
                          if v and k != "mdfc_land"})
        self.assertAlmostEqual(plan.value(), build.deck_value(plan.names(), ctx, db)["total"])
        self.assertEqual(plan.rules["gc"], 1)

    def test_the_plan_keeps_whole_card_counts_and_fractional_mass_side_by_side(self):
        w = multirole_world()
        db = w.db()
        ctx = make_ctx(w, db)
        model = build.Model(ctx, db)
        plan = build.Plan(model, db, "BG", 3, prices=w.prices(), owned=set())
        self.assertEqual((w.role_of["Multi 01"], len(w.role_of["Multi 02"])), ({"draw", "ramp"}, 4))
        for n in ["Rock 01", "Multi 01", "Multi 02"]:        # one role (ramp); two (draw, ramp); four
            plan.add(n)
        self.assertEqual((plan.counts["ramp"], plan.counts["draw"], plan.counts["protection"]), (2, 1, 1))
        self.assertTrue(all(isinstance(plan.counts[r], int) for r in roles.ROLES))
        self.assertAlmostEqual(plan.mass["ramp"], 1 + 1 / math.sqrt(2))
        self.assertAlmostEqual(plan.mass["draw"], 1 / math.sqrt(2))
        self.assertAlmostEqual(plan.mass["protection"], 1 / 2)
        plan.remove("Multi 02")
        self.assertAlmostEqual(plan.mass["protection"], 0.0)
        self.assertAlmostEqual(plan.mass["draw"], 1 / math.sqrt(2))
        fresh = model.role_mass([model.facts(n) for n in plan.names()])
        for role in roles.ROLES:
            self.assertAlmostEqual(plan.mass[role], fresh[role])
        self.assertEqual(plan.counts["protection"], 0)


# ----------------------------------------------------------------------------- prepare
class PrepareTests(Isolated):
    def setUp(self):
        super().setUp()
        self.w = standard_world()
        self.db = self.w.db()
        def listed(decks):
            return {"all": {"decks": decks, "of": 100, "synergy": None}, "at": None, "themes": {},
                    "theme_global": {}, "tourn": None, "pop": None}

        fresh = {"fetched": "2026-10-11T00:00:00Z", "cache": "fresh", "age_days": 0.1}
        self.evidence = {"commanders": [CMDR], "ci": "BG", "bracket": 3, "spec": SPEC, "enabled": (),
                         "at_label": "Bracket 3", "cards": {"Rock 01": listed(90), "Titan 02": listed(10)},
                         "n": {"all": 100, "at": 0, "themes": {}, "tourn": 0}, "floor_all": 0.05,
                         "floor_at": 0.0, "tourn_totals": None, "meta": {"avg_types": {"land": 40}}, "salt": {},
                         "salt_floor": None, "theme_weights": {}, "theme_src": {}, "precon": None,
                         "popularity": False, "sources": {"edhrec": fresh}, "warnings": ["a gather warning"]}
        self.gather = mock.patch.object(score, "gather", return_value=self.evidence).start()
        self.tag = mock.patch.object(roles, "tag", side_effect=lambda names, db, **kw:
                                     {n: set(self.w.role_of.get(n, ())) for n in names}).start()

    def prepare(self, **kw):
        spec = dict(SPEC, include=kw.pop("include", []), exclude=kw.pop("exclude", []))
        return build.prepare([CMDR], 3, spec, self.db, **kw)

    def test_it_gathers_tags_scores_and_sets_targets_once(self):
        ctx = self.prepare(deck_cards=["Rock 02"])
        self.gather.assert_called_once()
        self.tag.assert_called_once()
        self.assertEqual(ctx["commanders"], [CMDR])
        self.assertEqual((ctx["ci"], ctx["bracket"]), ("BG", 3))
        self.assertEqual(ctx["role_map"]["Rock 01"], {"ramp"})
        self.assertIn("a gather warning", ctx["warnings"])
        self.assertEqual(ctx["sources"], self.evidence["sources"])
        self.assertIs(ctx["evidence"], self.evidence)

    def test_the_score_covers_the_deck_the_evidence_and_the_owned_cards_but_no_basics(self):
        ctx = self.prepare(deck_cards=["Rock 02", "Forest", "Forest"], owned=["Draw 01", "Blue Spell"])
        self.assertEqual(set(ctx["scores"]), {"Rock 02", "Rock 01", "Titan 02", "Draw 01"})
        self.assertEqual(ctx["owned"], {"Draw 01"})          # Blue Spell is outside the colors
        self.assertGreater(ctx["scores"]["Rock 01"]["score"], ctx["scores"]["Rock 02"]["score"])

    def test_include_and_exclude_are_canonicalized_and_unknown_names_are_reported(self):
        ctx = self.prepare(include=["rock 04", "Nope Card"], exclude=["TITAN 03"])
        self.assertEqual(ctx["include"], ["Rock 04"])
        self.assertEqual(ctx["exclude"], {"Titan 03"})
        self.assertTrue(any("include card 'Nope Card' was not found" in w for w in ctx["warnings"]))
        self.assertIn("Rock 04", ctx["scores"])               # an include is scored even when no source lists it

    def test_the_land_target_follows_the_commanders_average(self):
        # The commander's decks average 40 lands: the target moves to the mean of that and the bracket's own
        # target, kept inside the bracket's range (read from the shipped file, which calibration rewrites).
        land = roles.targets(3)["land"]
        expected = min(max(int((land["target"] + 40) / 2 + 0.5), land["min"]), land["max"])
        self.assertEqual(self.prepare()["targets"]["land"]["target"], expected)
        self.assertGreaterEqual(expected, land["target"])          # 40 is above any bracket's target

    def test_without_blue_there_is_no_counterspell_target(self):
        self.assertEqual(self.prepare()["targets"]["counter"]["target"], 0)

    def test_role_tag_warnings_are_moved_into_the_context(self):
        roles.WARNINGS.append("roles: tags unavailable")
        self.addCleanup(roles.WARNINGS.clear)
        ctx = self.prepare()
        self.assertIn("roles: tags unavailable", ctx["warnings"])
        self.assertEqual(roles.WARNINGS, [])

    def test_the_playstyle_shifts_the_targets(self):
        spec = dict(SPEC, playstyle="control")
        ctx = build.prepare([CMDR], 3, spec, self.db)
        plain = roles.targets(3, "value", ci="BG")
        self.assertGreater(ctx["targets"]["removal"]["target"], plain["removal"]["target"])


# ----------------------------------------------------------------------------- upgrade
def mini(**scores):
    """A small world: the commander, `scores` as {name: value}, and a card for each name."""
    w = World()
    for name, value in scores.items():
        w.add(name, value, None, price=1.0)
    return w


def run_upgrade(w, deck_names, candidate_names=None, *, targets=None, owned=(), include=(), exclude=(),
                prices=None, bracket=3, **kw):
    db = w.db()
    names = list(deck_names) + list(candidate_names or [])
    ctx = make_ctx(w, db, names=names, bracket=bracket, targets=targets or zero_targets(), owned=set(owned),
                   include=list(include), exclude=set(exclude))
    deck = deck_of(*deck_names)
    kw.setdefault("prices", prices if prices is not None else w.prices())
    return build.upgrade(ctx, deck, db, **kw), ctx, db


class UpgradeTests(Isolated):
    def world(self):
        return mini(**{"Dud A": 0.05, "Dud B": 0.10, "Dud C": 0.12, "Fine A": 0.40, "Good A": 0.70,
                       "Staple": 0.90, "Okay": 0.50, "Decent": 0.60})

    DECK = ["Dud A", "Dud B", "Dud C", "Fine A", "Good A"]

    def test_the_obviously_best_swap_comes_first(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple", "Okay", "Decent"], max_swaps=3)
        self.assertEqual([(s["cut"], s["add"]) for s in res["swaps"]],
                         [("Dud A", "Staple"), ("Dud B", "Decent"), ("Dud C", "Okay")])
        self.assertAlmostEqual(res["swaps"][0]["gain"], 0.90 - 0.05)
        self.assertEqual([s["rank"] for s in res["swaps"]], [1, 2, 3])
        self.assertTrue(all(not s["forced"] for s in res["swaps"]))

    def test_gains_add_up_to_the_change_in_value_and_the_deck_changes_accordingly(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple", "Okay", "Decent"], max_swaps=3)
        self.assertAlmostEqual(res["value_after"] - res["value_before"], sum(s["gain"] for s in res["swaps"]))
        after = {name for _, name in res["deck_after"]["cards"]}
        self.assertEqual(after, {"Fine A", "Good A", "Staple", "Okay", "Decent"})
        self.assertEqual(res["deck"]["count"], 6)
        self.assertEqual(res["command"], "upgrade")

    def test_it_stops_when_nothing_beats_the_minimum_gain(self):
        # Fine A (0.40) -> Okay (0.50) would gain only 0.10, but cutting Good A (0.70) for Okay loses
        res, _, _ = run_upgrade(self.world(), ["Dud A", "Good A"], ["Staple", "Okay"], max_swaps=5)
        self.assertEqual([(s["cut"], s["add"]) for s in res["swaps"]], [("Dud A", "Staple")])
        res, _, _ = run_upgrade(mini(**{"A": 0.50, "B": 0.51}), ["A"], ["B"])
        self.assertEqual(res["swaps"], [])          # a gain of 0.01 is under MIN_GAIN

    def test_max_swaps_caps_the_list(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple", "Okay", "Decent"], max_swaps=2)
        self.assertEqual(len(res["swaps"]), 2)

    def test_the_budget_limits_the_adds(self):
        w = mini(**{"Dud A": 0.05, "Dud B": 0.10, "Pricey Gem": 0.95, "Cheap Gem": 0.60, "Okay": 0.50})
        w.price_of.update({"Pricey Gem": 50.0, "Cheap Gem": 1.0, "Okay": 2.0})
        res, _, _ = run_upgrade(w, ["Dud A", "Dud B"], ["Pricey Gem", "Cheap Gem", "Okay"], budget=5.0,
                                max_swaps=2)
        self.assertEqual({s["add"] for s in res["swaps"]}, {"Cheap Gem", "Okay"})
        self.assertAlmostEqual(res["spent"], 3.0)
        self.assertEqual(res["budget"], 5.0)
        self.assertLessEqual(res["spent"], 5.0)

    def test_owned_cards_cost_nothing(self):
        w = mini(**{"Dud A": 0.05, "Owned Gem": 0.85, "Cheap Gem": 0.60})
        w.price_of.update({"Owned Gem": 50.0, "Cheap Gem": 1.0})
        res, _, _ = run_upgrade(w, ["Dud A"], ["Owned Gem", "Cheap Gem"], budget=1.0, owned=["Owned Gem"])
        swap = res["swaps"][0]
        self.assertEqual((swap["add"], swap["price"], swap["owned"]), ("Owned Gem", 0.0, True))
        self.assertEqual(res["spent"], 0.0)

    def test_unknown_prices_are_skipped_when_there_is_a_budget_and_ignored_when_there_is_none(self):
        w = mini(**{"Dud A": 0.05, "Mystery": 0.90, "Okay": 0.50})
        w.price_of["Okay"] = 1.0
        prices = {"Okay": 1.0}                                     # no price for Mystery
        res, _, _ = run_upgrade(w, ["Dud A"], ["Mystery", "Okay"], budget=10.0, prices=prices)
        self.assertEqual([s["add"] for s in res["swaps"]], ["Okay"])
        res, _, _ = run_upgrade(w, ["Dud A"], ["Mystery", "Okay"], prices=prices)
        self.assertEqual([s["add"] for s in res["swaps"]], ["Mystery"])
        self.assertIsNone(res["swaps"][0]["price"])

    def test_a_price_conscious_run_beats_spending_the_budget_on_one_card(self):
        # Greedy takes the $10 card (gain 0.9) and is out of money; three $2 cards are worth 1.5 together.
        w = mini(**{"Dud A": 0.0, "Dud B": 0.0, "Dud C": 0.0, "Pricey": 0.9, "Cheap A": 0.5, "Cheap B": 0.5,
                    "Cheap C": 0.5})
        w.price_of.update({"Pricey": 10.0, "Cheap A": 2.0, "Cheap B": 2.0, "Cheap C": 2.0})
        res, _, _ = run_upgrade(w, ["Dud A", "Dud B", "Dud C"], ["Pricey", "Cheap A", "Cheap B", "Cheap C"],
                                budget=10.0, max_swaps=3)
        self.assertEqual({s["add"] for s in res["swaps"]}, {"Cheap A", "Cheap B", "Cheap C"})
        self.assertAlmostEqual(res["spent"], 6.0)
        self.assertAlmostEqual(res["value_after"] - res["value_before"], 1.5)

    def test_without_a_budget_the_best_card_is_taken_whatever_it_costs(self):
        w = mini(**{"Dud A": 0.0, "Pricey": 0.9, "Cheap A": 0.5})
        w.price_of.update({"Pricey": 10.0, "Cheap A": 2.0})
        res, _, _ = run_upgrade(w, ["Dud A"], ["Pricey", "Cheap A"], max_swaps=1)
        self.assertEqual(res["swaps"][0]["add"], "Pricey")
        self.assertEqual(res["swaps"][0]["price"], 10.0)

    def test_a_tiny_budget_lists_the_cheapest_adds_that_would_help(self):
        w = mini(**{"Dud A": 0.0, "Dud B": 0.0, **{f"Gem {i}": 0.5 + i / 100 for i in range(1, 8)}})
        w.price_of.update({f"Gem {i}": float(i + 1) for i in range(1, 8)})        # $2 ... $8
        res, _, _ = run_upgrade(w, ["Dud A", "Dud B"], [f"Gem {i}" for i in range(1, 8)], budget=0.5)
        self.assertEqual(res["swaps"], [])
        self.assertEqual([c["card"] for c in res["cheap_adds"]], [f"Gem {i}" for i in range(1, 6)])
        self.assertEqual([c["price"] for c in res["cheap_adds"]], [2.0, 3.0, 4.0, 5.0, 6.0])
        self.assertTrue(all(c["gain"] > build.MIN_GAIN for c in res["cheap_adds"]))
        self.assertEqual(res["spent"], 0.0)

    def test_cheap_adds_are_empty_when_swaps_were_made(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple"], budget=100.0)
        self.assertTrue(res["swaps"])
        self.assertEqual(res["cheap_adds"], [])

    def test_a_commander_is_never_cut_even_if_it_is_listed_among_the_cards(self):
        w = self.world()
        w.add(CMDR + " Twin", 0.0, None)
        res, _, _ = run_upgrade(w, ["Dud A", "Good A"], ["Staple"], max_swaps=1)
        self.assertEqual(res["swaps"][0]["cut"], "Dud A")
        w = World()
        w.add("Staple", 0.9, None)
        db = w.db()
        ctx = make_ctx(w, db, names=["Staple"], targets=zero_targets())
        ctx["scores"][CMDR] = score_record(0.0)
        out = build.upgrade(ctx, deck_of(CMDR), db, prices=w.prices())       # the commander is also in "cards"
        self.assertEqual(out["swaps"], [])

    def test_include_cards_are_never_cut(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple", "Okay"], include=["Dud A"], max_swaps=2)
        self.assertNotIn("Dud A", [s["cut"] for s in res["swaps"]])
        self.assertEqual([s["cut"] for s in res["swaps"]], ["Dud B", "Dud C"])

    def test_exclude_cards_are_never_added(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple", "Okay"], exclude=["Staple"], max_swaps=1)
        self.assertEqual(res["swaps"][0]["add"], "Okay")

    def test_cards_outside_the_colors_or_banned_are_never_added(self):
        w = self.world()
        w.add("Blue Spell", 0.99, None, ci="U")
        w.add("Banned Spell", 0.99, None, legal="banned")
        res, _, _ = run_upgrade(w, self.DECK, ["Blue Spell", "Banned Spell", "Okay"], max_swaps=3)
        self.assertEqual([s["add"] for s in res["swaps"]], ["Okay"])

    def test_cards_already_in_the_deck_are_not_added_again(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Good A"], max_swaps=3)
        self.assertEqual(res["swaps"], [])

    def test_a_card_added_here_is_not_cut_again(self):
        res, _, _ = run_upgrade(self.world(), ["Dud A"], ["Staple", "Decent", "Okay"], max_swaps=4)
        self.assertEqual([(s["cut"], s["add"]) for s in res["swaps"]], [("Dud A", "Staple")])

    # --- roles
    def test_a_card_that_fills_a_short_role_beats_an_equally_scored_one(self):
        w = mini(**{"Dud": 0.0, "Plain": 0.50, "Ramp": 0.40})
        w.role_of["Ramp"] = {"ramp"}
        targets = zero_targets(ramp={"min": 0, "target": 3, "max": 5})
        res, _, _ = run_upgrade(w, ["Dud"], ["Plain", "Ramp"], targets=targets, max_swaps=1)
        swap = res["swaps"][0]
        self.assertEqual(swap["add"], "Ramp")                        # 0.40 + 0.2 beats 0.50
        self.assertEqual(swap["fills"], ["ramp"])
        self.assertAlmostEqual(swap["gain"], 0.40 + 0.2)
        self.assertIn("fills ramp (0 of 3)", swap["reason"])
        self.assertEqual((res["roles_before"]["ramp"], res["roles_after"]["ramp"]), (0, 1))

    def test_a_role_past_its_maximum_is_worth_nothing_more(self):
        w = mini(**{"Ramp 1": 0.30, "Ramp 2": 0.30, "Plain": 0.35, "Ramp 3": 0.40})
        w.role_of.update({"Ramp 1": {"ramp"}, "Ramp 2": {"ramp"}, "Ramp 3": {"ramp"}})
        targets = zero_targets(ramp={"min": 0, "target": 1, "max": 2})
        res, _, _ = run_upgrade(w, ["Ramp 1", "Ramp 2"], ["Plain", "Ramp 3"], targets=targets, max_swaps=1)
        # Cutting a ramp card for Ramp 3 keeps the count (gain 0.10); for Plain it goes 2 -> 1, losing the
        # fading value 0.2 * (2 - 2 + 1) / (2 - 1 + 1) = 0.1 of the second card and gaining 0.05: -0.05.
        self.assertEqual((res["swaps"][0]["cut"], res["swaps"][0]["add"]), ("Ramp 1", "Ramp 3"))
        self.assertAlmostEqual(res["swaps"][0]["gain"], 0.10)
        self.assertEqual(res["swaps"][0]["fills"], [])

    def test_the_top_end_limit_is_priced_in(self):
        w = mini(**{"Small": 0.50, "Big 1": 0.50, "Big 2": 0.50})
        for name in ("Big 1", "Big 2"):
            w.objs[-1 if name == "Big 2" else -2]["cmc"] = 7.0
        targets = zero_targets(topend={"max": 1})
        res, _, _ = run_upgrade(w, ["Small", "Big 1"], ["Big 2"], targets=targets)
        self.assertEqual(res["swaps"], [])           # Big 2 would be a second top-end card: -0.1 and no gain

    # --- bracket rules
    def gc_world(self, n=5):
        w = mini(**{"Filler": 0.3, "Staple": 0.9, "Okay": 0.5, "Decent": 0.6, "Fine": 0.4})
        for i in range(1, n + 1):
            w.add(f"GC {i}", round(1.0 - 0.1 * i, 2), None, gc=True)
        return w

    def test_a_deck_over_the_game_changer_limit_loses_its_weakest_ones_first(self):
        w = self.gc_world()
        deck = ["Filler"] + [f"GC {i}" for i in range(1, 6)]
        res, _, db = run_upgrade(w, deck, ["Staple", "Okay", "Decent", "Fine"], max_swaps=0)
        forced = [s for s in res["swaps"] if s["forced"]]
        self.assertEqual([s["cut"] for s in forced], ["GC 5", "GC 4"])        # Bracket 3 allows three
        self.assertTrue(all(s["add"] in ("Staple", "Decent") for s in forced))
        self.assertEqual(res["swaps"][:2], forced)                            # forced swaps come first
        self.assertFalse(res["bracket_before"]["ok"])
        self.assertTrue(res["bracket_after"]["ok"])
        self.assertIn("5 Game Changers", forced[0]["reason"])
        self.assertAlmostEqual(forced[0]["gain"], 0.9 - 0.5)                  # GC 5 scored 0.5

    def test_forced_swaps_happen_even_when_they_lose_value(self):
        w = self.gc_world(4)
        deck = [f"GC {i}" for i in range(1, 5)]
        res, _, _ = run_upgrade(w, deck, ["Fine"], max_swaps=0)               # the only replacement scores 0.4
        self.assertEqual([(s["cut"], s["add"]) for s in res["swaps"]], [("GC 4", "Fine")])
        self.assertLess(res["swaps"][0]["gain"], 0)
        self.assertTrue(res["swaps"][0]["forced"])

    def test_every_game_changer_goes_at_bracket_2(self):
        w = self.gc_world(3)
        res, _, _ = run_upgrade(w, ["GC 1", "GC 2", "GC 3"], ["Staple", "Okay", "Decent"], bracket=2, max_swaps=0)
        self.assertEqual(sorted(s["cut"] for s in res["swaps"]), ["GC 1", "GC 2", "GC 3"])
        self.assertTrue(res["bracket_after"]["ok"])

    def test_a_game_changer_is_only_added_while_the_limit_allows(self):
        w = self.gc_world(5)
        deck = ["Filler", "GC 3", "GC 4", "GC 5"]                             # three: the limit
        res, _, _ = run_upgrade(w, deck, ["GC 1", "GC 2"], max_swaps=5)
        # A better Game Changer may replace a worse one (the count stays at three) but never add a fourth
        self.assertEqual([(s["cut"], s["add"]) for s in res["swaps"]], [("GC 5", "GC 1"), ("GC 4", "GC 2")])
        self.assertTrue(res["bracket_after"]["ok"])
        self.assertEqual(len(res["bracket_after"]["game_changers"]), 3)

    def test_a_game_changer_that_only_the_rules_keep_out_is_reported_as_blocked(self):
        w = self.gc_world(1)
        res, _, _ = run_upgrade(w, ["Filler", "Fine"], ["GC 1"], bracket=2, max_swaps=1)
        self.assertEqual(res["swaps"], [])
        self.assertEqual([b["card"] for b in res["blocked"]], ["GC 1"])
        self.assertIn("Game Changer", res["blocked"][0]["reason"])

    def test_the_commander_counts_toward_the_game_changer_limit(self):
        w = mini(**{"Staple": 0.9, "Filler": 0.1})
        w.add("GC 1", 0.95, None, gc=True)
        for i in (2, 3):
            w.add(f"GC {i}", 0.5, None, gc=True)
        w.objs[0]["game_changer"] = True        # the commander is a Game Changer: with two in the deck, that is 3
        deck = ["Filler", "GC 2", "GC 3"]
        # With the two Game Changers locked in, GC 1 (0.95) could only replace a plain card, making a fourth
        res, _, _ = run_upgrade(w, deck, ["GC 1", "Staple"], include=["GC 2", "GC 3"], max_swaps=1)
        self.assertEqual([s["add"] for s in res["swaps"]], ["Staple"])
        self.assertEqual([b["card"] for b in res["blocked"]], ["GC 1"])
        res, _, _ = run_upgrade(w, deck, ["GC 1", "Staple"], max_swaps=2)
        # A Game Changer may replace another, keeping the count at three; never a plain card
        self.assertEqual([(s["cut"], s["add"]) for s in res["swaps"]], [("Filler", "Staple"), ("GC 2", "GC 1")])
        self.assertEqual(len(res["bracket_after"]["game_changers"]), 3)
        self.assertTrue(res["bracket_after"]["ok"])

    # --- combos
    COMBO = {"id": "1-2", "cards": [CMDR, "Combo Piece", "Fine A"], "missing": ["Combo Piece"],
             "produces": ["Infinite mana"], "bracket_tag": "R", "min_bracket": 4, "two_card": True,
             "infinite": True, "url": "https://commanderspellbook.com/combo/1-2/"}

    def combos_world(self):
        w = self.world()
        w.add("Combo Piece", 0.97, None)
        return w

    def test_the_missing_half_of_a_combo_the_bracket_forbids_is_blocked(self):
        combos = lambda commanders, cards: {"included": [], "almost": [dict(self.COMBO)]}
        res, _, _ = run_upgrade(self.combos_world(), self.DECK, ["Combo Piece", "Staple"], combos_fn=combos,
                                max_swaps=1)
        self.assertEqual(res["swaps"][0]["add"], "Staple")                    # 0.90, not 0.97
        self.assertEqual([b["card"] for b in res["blocked"]], ["Combo Piece"])
        reason = res["blocked"][0]["reason"]
        self.assertIn("completes a two-card combo with", reason)
        self.assertIn(CMDR, reason)
        self.assertTrue(reason.endswith("(needs Bracket 4)"), reason)
        self.assertGreater(res["blocked"][0]["gain"], res["swaps"][0]["gain"])

    def test_allow_combos_lifts_the_block(self):
        combos = lambda commanders, cards: {"included": [], "almost": [dict(self.COMBO)]}
        res, _, _ = run_upgrade(self.combos_world(), self.DECK, ["Combo Piece", "Staple"], combos_fn=combos,
                                allow_combos=True, max_swaps=1)
        self.assertEqual(res["swaps"][0]["add"], "Combo Piece")
        self.assertEqual(res["blocked"], [])
        self.assertTrue(any("allow-combos" in w for w in res["warnings"]))

    def test_a_combo_allowed_at_a_higher_bracket_is_not_blocked_there(self):
        combos = lambda commanders, cards: {"included": [], "almost": [dict(self.COMBO)]}
        res, _, _ = run_upgrade(self.combos_world(), self.DECK, ["Combo Piece", "Staple"], combos_fn=combos,
                                bracket=4, max_swaps=1)
        self.assertEqual(res["swaps"][0]["add"], "Combo Piece")

    def test_a_combo_already_in_the_deck_is_cut_first(self):
        # The deck holds a forbidden two-card combo; the weaker piece goes before anything else is considered
        combo = dict(self.COMBO, cards=[CMDR, "Fine A", "Good A"], missing=[])
        both_in = lambda cards: "Fine A" in cards and "Good A" in cards
        combos = lambda commanders, cards: {"included": [combo] if both_in(cards) else [], "almost": []}
        res, _, _ = run_upgrade(self.combos_world(), self.DECK, ["Staple"], combos_fn=combos, max_swaps=0)
        self.assertEqual([(s["cut"], s["forced"]) for s in res["swaps"]], [("Fine A", True)])   # 0.40 < 0.70
        self.assertTrue(res["bracket_after"]["ok"])
        self.assertFalse(res["bracket_before"]["ok"])

    def test_a_combo_two_new_cards_complete_together_is_undone(self):
        # Neither piece is a combo with the starting deck, so nothing blocks them; the final check finds it
        a_b = {"id": "9-9", "cards": ["Combo A", "Combo B"], "missing": [], "produces": ["Infinite mana"],
               "bracket_tag": "R", "min_bracket": 4, "two_card": True, "infinite": True, "url": ""}
        calls = []

        def combos(commanders, cards):
            calls.append(list(cards))
            return {"included": [a_b] if {"Combo A", "Combo B"} <= set(cards) else [], "almost": []}

        w = self.world()
        w.add("Combo A", 0.97, None)
        w.add("Combo B", 0.96, None)
        res, _, _ = run_upgrade(w, self.DECK, ["Combo A", "Combo B", "Staple"], combos_fn=combos, max_swaps=3)
        adds = {s["add"] for s in res["swaps"]}
        self.assertTrue(adds & {"Combo A", "Combo B"} and not {"Combo A", "Combo B"} <= adds, adds)
        self.assertTrue(any(w_.startswith("Undid ") for w_ in res["warnings"]), res["warnings"])
        self.assertTrue(res["bracket_after"]["ok"])
        self.assertGreater(len(calls), 1)

    def test_combos_that_cannot_be_fetched_are_a_warning_not_an_error(self):
        def combos(commanders, cards):
            raise net.FetchError("spellbook", "https://x", "offline")
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple"], combos_fn=combos, max_swaps=1)
        self.assertEqual(res["swaps"][0]["add"], "Staple")
        self.assertTrue(any("Combos were not checked" in w for w in res["warnings"]))
        self.assertTrue(any("Combos were not checked" in n for n in res["bracket_after"]["notes"]))

    # --- legality
    def test_cards_that_cannot_be_in_the_deck_are_cut_first(self):
        w = self.world()
        w.add("Blue Spell", 0.99, None, ci="U")
        w.add("Banned Spell", 0.99, None, legal="banned")
        db = w.db()
        names = self.DECK + ["Staple", "Okay", "Decent"]
        ctx = make_ctx(w, db, names=names + ["Blue Spell", "Banned Spell"], targets=zero_targets())
        deck = {"commanders": [CMDR],
                "cards": [(1, "Blue Spell"), (1, "Banned Spell"), (2, "Fine A"), (1, "Good A")]}
        res = build.upgrade(ctx, deck, db, prices=w.prices(), max_swaps=0)
        reasons = {s["cut"]: s["reason"] for s in res["swaps"]}
        self.assertEqual(set(reasons), {"Blue Spell", "Banned Spell", "Fine A"})
        self.assertIn("outside the commander's colors", reasons["Blue Spell"])
        self.assertIn("not legal in Commander", reasons["Banned Spell"])
        self.assertIn("appears 2 times", reasons["Fine A"])
        self.assertTrue(all(s["forced"] for s in res["swaps"]))

    def test_a_card_the_player_never_wants_is_cut_first(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple", "Okay"], exclude=["Fine A"], max_swaps=0)
        self.assertEqual(len(res["swaps"]), 1)
        swap = res["swaps"][0]
        self.assertEqual((swap["cut"], swap["add"], swap["forced"]), ("Fine A", "Staple", True))
        self.assertEqual(swap["reason"], "you asked never to play Fine A")

    def test_an_include_that_is_not_in_the_deck_is_flagged_not_added(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple", "Okay"], include=["Okay"], max_swaps=0)
        self.assertEqual(res["swaps"], [])
        self.assertTrue(any("Okay is in your include list but not in the deck" in w for w in res["warnings"]))

    def test_basic_lands_may_repeat(self):
        w = self.world()
        res, _, _ = run_upgrade(w, ["Forest", "Forest", "Forest", "Dud A"], ["Staple"], max_swaps=1)
        self.assertFalse([s for s in res["swaps"] if s["forced"]])

    def test_a_forced_cut_with_nothing_to_add_is_filled_by_a_basic(self):
        w = self.gc_world(1)
        res, _, _ = run_upgrade(w, ["Filler", "GC 1"], [], bracket=2, max_swaps=0)
        swap = res["swaps"][0]
        self.assertIn(swap["add"], ("Forest", "Swamp"))
        self.assertIn("a basic land fills the slot", swap["reason"])
        self.assertEqual(res["deck"]["count"], 3)

    # --- lands
    def land_world(self):
        w = mini(**{"Spell": 0.5})
        w.add("Utility Land", 0.50, None, types="Land", produced=["C"])
        w.add("Dual Land", 0.60, None, types="Land", produced=["B", "G"], ci="BG")
        return w

    def test_a_land_swaps_for_a_land_and_keeps_the_land_count(self):
        deck = ["Forest"] * 12 + ["Swamp"] * 12 + ["Spell"]
        res, _, _ = run_upgrade(self.land_world(), deck, ["Dual Land"], max_swaps=1,
                                targets=zero_targets(land={"min": 24, "target": 24, "max": 24}))
        self.assertEqual(res["swaps"][0]["add"], "Dual Land")
        self.assertEqual(res["swaps"][0]["evidence_cut"], "basic land")
        self.assertEqual(res["roles_before"]["land"], res["roles_after"]["land"])

    def test_a_swap_may_not_strip_a_color_of_its_lands(self):
        # Forest is at the floor of 8 sources, Swamp has plenty: the colorless land takes a Swamp's place.
        deck = ["Forest"] * build.MANA_FLOOR + ["Swamp"] * 20
        lands = zero_targets(land={"min": 28, "target": 28, "max": 28})
        res, _, _ = run_upgrade(self.land_world(), deck, ["Utility Land"], max_swaps=1, targets=lands)
        self.assertEqual((res["swaps"][0]["cut"], res["swaps"][0]["add"]), ("Swamp", "Utility Land"))
        deck = ["Forest"] * build.MANA_FLOOR + ["Swamp"] * build.MANA_FLOOR
        lands = zero_targets(land={"min": 16, "target": 16, "max": 16})
        res, _, _ = run_upgrade(self.land_world(), deck, ["Utility Land"], max_swaps=3, targets=lands)
        self.assertEqual(res["swaps"], [])

    def test_an_extra_land_is_worth_more_than_a_weak_spell_when_the_deck_is_short(self):
        w = mini(**{"Weak": 0.1})
        w.add("Dual Land", 0.3, None, types="Land", produced=["B", "G"], ci="BG")
        targets = zero_targets(land={"min": 1, "target": 2, "max": 4})
        res, _, _ = run_upgrade(w, ["Weak", "Forest"], ["Dual Land"], targets=targets, max_swaps=1)
        self.assertEqual((res["swaps"][0]["cut"], res["swaps"][0]["add"]), ("Weak", "Dual Land"))
        self.assertEqual(res["roles_after"]["land"], 2)
        self.assertAlmostEqual(res["swaps"][0]["gain"], 0.3 + 1.0 - 0.1)

    # --- result shape
    def test_swap_records_carry_the_evidence_and_the_fills(self):
        res, ctx, _ = run_upgrade(self.world(), self.DECK, ["Staple"], max_swaps=1)
        swap = res["swaps"][0]
        self.assertEqual(set(swap), {"rank", "cut", "add", "gain", "price", "owned", "forced", "reason", "fills",
                                     "evidence_add", "evidence_cut", "kind_add"})
        self.assertEqual(swap["evidence_add"], ctx["scores"]["Staple"]["evidence"])
        self.assertEqual(swap["evidence_cut"], ctx["scores"]["Dud A"]["evidence"])
        self.assertEqual(swap["kind_add"], "builder")
        self.assertEqual(swap["price"], 1.0)

    def test_the_result_has_every_documented_key(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple"], max_swaps=1)
        self.assertEqual(set(res), {"command", "deck", "bracket", "budget", "spent", "spec", "swaps", "blocked",
                                    "cheap_adds", "roles_before", "roles_after", "targets", "value_before",
                                    "value_after", "bracket_before", "bracket_after", "deck_after", "warnings",
                                    "sources"})
        self.assertEqual(set(res["deck"]), {"name", "commanders", "count", "ci"})
        self.assertEqual(res["deck_after"]["commanders"], [CMDR])
        self.assertEqual(res["bracket"], 3)

    def test_a_list_of_the_wrong_size_is_flagged(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple"], max_swaps=1)
        self.assertTrue(any("has 6 cards" in w for w in res["warnings"]))

    def test_the_context_is_not_changed(self):
        w = self.world()
        db = w.db()
        ctx = make_ctx(w, db, names=self.DECK + ["Staple"], targets=zero_targets())
        before = repr(sorted(ctx["scores"]))
        build.upgrade(ctx, deck_of(*self.DECK), db, prices=w.prices())
        self.assertEqual(repr(sorted(ctx["scores"])), before)
        self.assertEqual(ctx["warnings"], [])

    def test_prices_come_from_scryfall_when_none_are_given(self):
        w = self.world()
        db = w.db()
        ctx = make_ctx(w, db, names=self.DECK + ["Staple"], targets=zero_targets())
        with mock.patch.object(carddb, "cheapest_prices", return_value={"Staple": 4.5}) as cheapest:
            res = build.upgrade(ctx, deck_of(*self.DECK), db, budget=10.0)
        cheapest.assert_called_once_with(["Staple"])
        self.assertEqual((res["swaps"][0]["price"], res["spent"]), (4.5, 4.5))

    def test_without_a_budget_only_the_printed_adds_are_priced(self):
        w = self.world()
        db = w.db()
        ctx = make_ctx(w, db, names=self.DECK + ["Staple", "Okay"], targets=zero_targets())
        with mock.patch.object(carddb, "cheapest_prices", return_value={"Staple": 4.5}) as cheapest:
            res = build.upgrade(ctx, deck_of(*self.DECK), db, max_swaps=1)
        cheapest.assert_called_once_with(["Staple"])
        self.assertEqual(res["swaps"][0]["price"], 4.5)


class UpgradeSpeedTests(Isolated):
    def test_a_full_deck_against_a_full_candidate_pool_is_fast(self):
        w = standard_world()
        for i in range(1, 181):                       # on top of the world's 150 spells: 250+ candidates
            w.add(f"Extra {i:03d}", round(0.55 - 0.002 * i, 4), ("ramp", "draw", "removal", None)[i % 4],
                  price=1.0 + i % 7, types="Creature", cmc=3, cost="{2}{G}")
        db = w.db()
        deck = {"commanders": [CMDR], "cards": [(1, f"Beast {i:02d}") for i in range(1, 63)]
                + [(1, f"Dual {i:02d}") for i in range(1, 6)] + [(16, "Forest"), (16, "Swamp")]}
        ctx = make_ctx(w, db)
        started = time.time()
        res = build.upgrade(ctx, deck, db, budget=200.0, prices=w.prices(), max_swaps=15)
        elapsed = time.time() - started
        self.assertEqual(sum(k for k, _ in deck["cards"]) + 1, 100)
        self.assertGreaterEqual(len(res["swaps"]), 10)
        self.assertLess(elapsed, 3.0, f"upgrade took {elapsed:.1f}s")


# ----------------------------------------------------------------------------- build
class BuildTests(Isolated):
    @classmethod
    def setUpClass(cls):
        cls.world = standard_world()
        cls.db = cls.world.db()

    def ctx(self, **over):
        return make_ctx(self.world, self.db, **over)

    def build(self, ctx=None, **kw):
        ctx = ctx or self.ctx()
        kw.setdefault("prices", self.world.prices())
        return build.build(ctx, self.db, **kw), ctx

    def all_names(self, res):
        return [c["name"] for c in res["cards"]] + [n for n, k in res["basics"].items() for _ in range(k)]

    def test_it_builds_exactly_100_cards_at_the_land_target(self):
        res, ctx = self.build()
        self.assertEqual(res["count"], 100)
        self.assertEqual(len(self.all_names(res)) + 1, 100)                  # the commander is the 100th
        self.assertEqual(len(set(c["name"] for c in res["cards"])), len(res["cards"]))   # singleton
        self.assertEqual(res["roles"]["land"], ctx["targets"]["land"]["target"])
        self.assertEqual(res["roles"], roles.counts(self.all_names(res), ctx["role_map"], self.db))

    def test_the_result_has_every_documented_key(self):
        res, _ = self.build()
        self.assertEqual(set(res), {"command", "commanders", "ci", "bracket", "budget", "spent", "spec", "cards",
                                    "basics", "count", "roles", "targets", "value", "fantasy_cost",
                                    "bracket_check", "blocked", "warnings", "sources"})
        self.assertEqual((res["command"], res["bracket"], res["ci"]), ("build", 3, "BG"))
        self.assertEqual(set(res["cards"][0]), {"name", "section", "roles", "score", "price", "owned",
                                                "evidence", "kind"})
        self.assertIsNone(res["fantasy_cost"])                               # no themes in this context

    def test_every_role_lands_inside_the_brackets_range(self):
        res, ctx = self.build()
        for role in roles.ROLES:
            t = ctx["targets"][role]
            with self.subTest(role=role):
                self.assertGreaterEqual(res["roles"][role], t["min"])
                self.assertLessEqual(res["roles"][role], t["max"])
        self.assertLessEqual(res["roles"]["topend"], ctx["targets"]["topend"]["max"])

    def test_the_cards_are_legal_and_inside_the_colors(self):
        res, _ = self.build()
        names = self.all_names(res)
        self.assertNotIn(CMDR, names)
        for banned in ("Blue Spell", "Banned Spell"):
            self.assertNotIn(banned, names)
        self.assertTrue(all(set(self.db.get(n)["ci"]) <= set("BG") for n in names))

    def test_the_bracket_limits_are_respected(self):
        res, _ = self.build()
        power = [c["name"] for c in res["cards"] if c["name"].startswith("Power")]
        self.assertEqual(len(power), 3)                                     # three Game Changers at Bracket 3
        self.assertTrue(res["bracket_check"]["ok"])
        res2, _ = self.build(self.ctx(bracket=2, targets=roles.targets(2, "value", ci="BG")))
        self.assertFalse([c for c in res2["cards"] if c["name"].startswith("Power")])
        self.assertEqual(res2["bracket"], 2)

    def test_basics_fill_the_rest_of_the_land_target_split_between_the_colors(self):
        res, ctx = self.build()
        lands = [c for c in res["cards"] if c["section"] == "Lands"]
        self.assertEqual(sum(res["basics"].values()) + len(lands), ctx["targets"]["land"]["target"])
        self.assertEqual(set(res["basics"]), {"Forest", "Swamp"})            # at least one of each color
        self.assertTrue(all(c["score"] >= build.NONBASIC_MIN for c in lands))

    def test_basics_follow_the_colored_mana_symbols(self):
        w = standard_world(cost=lambda i: "{G}{G}{G}")                       # almost every spell is green
        db = w.db()
        res = build.build(make_ctx(w, db), db, prices=w.prices())
        self.assertGreater(res["basics"]["Forest"], res["basics"]["Swamp"])
        self.assertGreaterEqual(res["basics"]["Swamp"], 1)

    def test_a_colorless_commander_gets_wastes(self):
        w = standard_world()
        w.objs[0].update(color_identity=[], mana_cost="{3}")
        db = w.db()
        ctx = make_ctx(w, db, ci="")
        res = build.build(ctx, db, prices=w.prices())
        self.assertEqual(list(res["basics"]), ["Wastes"])
        self.assertEqual(res["count"], 100)

    def test_a_pair_of_commanders_leaves_98_slots(self):
        w = standard_world()
        w.card("Rat Queen", types=f"Legendary Creature {EM} Rat", cmc=2, cost="{B}", ci="B", power="1",
               toughness="1")
        db = w.db()
        ctx = make_ctx(w, db, commanders=[CMDR, "Rat Queen"])
        res = build.build(ctx, db, prices=w.prices())
        self.assertEqual(res["count"], 100)
        self.assertEqual(len(self.all_names(res)), 98)
        self.assertEqual(res["commanders"], [CMDR, "Rat Queen"])

    def test_include_cards_are_in_and_exclude_cards_are_out(self):
        ctx = self.ctx(include=["Seek 04", "Beast 70"], exclude={"Rock 01", "Combo A"})
        res, _ = self.build(ctx)
        names = self.all_names(res)
        self.assertIn("Seek 04", names)
        self.assertIn("Beast 70", names)                                    # the weakest card in the world
        self.assertNotIn("Rock 01", names)
        self.assertNotIn("Combo A", names)

    def test_an_include_that_cannot_be_played_is_reported_and_left_out(self):
        ctx = self.ctx(include=["Blue Spell", "Banned Spell"])
        res, _ = self.build(ctx)
        self.assertNotIn("Blue Spell", self.all_names(res))
        self.assertTrue(any("Blue Spell" in w and "colors" in w for w in res["warnings"]))
        self.assertTrue(any("Banned Spell" in w and "not legal" in w for w in res["warnings"]))

    def test_the_budget_is_kept_and_the_deck_is_still_full(self):
        res, _ = self.build(budget=60.0)
        self.assertLessEqual(res["spent"], 60.0)
        self.assertEqual(res["count"], 100)
        self.assertLessEqual(sum(c["price"] or 0 for c in res["cards"]), 60.0 + 1e-6)
        loose, _ = self.build()
        self.assertGreater(loose["value"], res["value"])                    # money buys value

    def test_a_budget_too_small_for_good_cards_still_fills_the_deck(self):
        res, _ = self.build(budget=8.0)
        self.assertEqual(res["count"], 100)
        self.assertLessEqual(res["spent"], 8.0)

    def test_owned_cards_are_free(self):
        ctx = self.ctx(owned={"Power 01", "Power 02", "Power 03"})
        res, _ = self.build(ctx, budget=10.0)
        owned = {c["name"]: c for c in res["cards"] if c["owned"]}
        self.assertTrue(set(owned) >= {"Power 01", "Power 02", "Power 03"})
        self.assertTrue(all(c["price"] == 0.0 for c in owned.values()))
        self.assertLessEqual(res["spent"], 10.0)

    def test_without_a_budget_the_best_cards_are_in(self):
        res, _ = self.build()
        names = set(self.all_names(res))
        self.assertTrue({"Combo A", "Combo B", "Rock 01", "Draw 01", "Kill 01", "Wipe 01"} <= names)
        self.assertTrue(all(c["price"] is not None for c in res["cards"]))

    def test_the_money_the_plan_tracked_matches_the_prices_of_the_cards_it_kept(self):
        # Swaps refund the card they cut; a slip there would leave the tracked spend off from the real one.
        ctx = self.ctx()
        model = build.Model(ctx, self.db)
        pool = [n for n in self.world.values if not n.startswith(("Blue", "Banned"))]
        lands = [n for n in pool if self.db.get(n)["land"]]
        spells = [n for n in pool if n not in lands]
        plan, basics = build._assemble(ctx, self.db, model, spells, lands, self.world.prices(), set(), 70.0,
                                       set(), [], [CMDR], {})
        paid = sum(self.world.price_of[n] * k for n, k in plan.cards.items() if n in self.world.price_of)
        self.assertAlmostEqual(plan.spent, paid)
        self.assertLessEqual(plan.spent, 70.0)
        self.assertEqual(sum(plan.cards.values()) + 1, 100)

    def test_the_build_is_deterministic(self):
        first, _ = self.build()
        second, _ = self.build()
        self.assertEqual(first["cards"], second["cards"])
        self.assertEqual(first["basics"], second["basics"])

    def test_cards_are_listed_by_section_then_score(self):
        res, _ = self.build()
        order = [c["section"] for c in res["cards"]]
        self.assertEqual(order, sorted(order, key=build.SECTIONS.index))
        for section in set(order):
            scores_ = [c["score"] for c in res["cards"] if c["section"] == section]
            self.assertEqual(scores_, sorted(scores_, reverse=True))
        self.assertEqual(order[-1], "Lands")

    def test_sections_follow_the_front_face_type(self):
        for types, section in (("Creature", "Creatures"), ("Artifact Creature", "Creatures"),
                               ("Legendary Planeswalker", "Planeswalkers"), ("Instant", "Instants"),
                               ("Sorcery", "Sorceries"), ("Artifact", "Artifacts"),
                               ("Enchantment", "Enchantments"),
                               ("Battle", "Battles"), ("Land", "Lands"), ("Land Creature", "Creatures"),
                               ("Kindred Instant", "Instants")):
            with self.subTest(types=types):
                rec = carddb.card_record(scry("T", types=types))
                self.assertEqual(build.section_of(rec), section)

    def test_the_card_rows_carry_roles_scores_and_evidence(self):
        res, ctx = self.build()
        row = next(c for c in res["cards"] if c["name"] == "Rock 01")
        self.assertEqual((row["section"], row["roles"], row["kind"]), ("Artifacts", ["ramp"], "builder"))
        self.assertAlmostEqual(row["score"], self.world.values["Rock 01"])
        self.assertEqual(row["evidence"], ctx["scores"]["Rock 01"]["evidence"])

    # --- combos
    def pair_combo(self):
        return {"id": "9-9", "cards": ["Combo A", "Combo B"], "missing": [], "produces": ["Infinite mana"],
                "bracket_tag": "R", "min_bracket": 4, "two_card": True, "infinite": True,
                "url": "https://commanderspellbook.com/combo/9-9/"}

    def combos_fn(self):
        combo = self.pair_combo()
        return lambda commanders, cards: {"included": [combo] if {"Combo A", "Combo B"} <= set(cards) else [],
                                          "almost": []}

    def test_a_forbidden_combo_loses_its_weaker_piece_and_the_slot_is_refilled(self):
        res, _ = self.build(combos_fn=self.combos_fn())
        names = self.all_names(res)
        self.assertIn("Combo A", names)                                      # 0.95
        self.assertNotIn("Combo B", names)                                   # 0.94 -- the weaker piece
        self.assertEqual(res["count"], 100)
        self.assertTrue(res["bracket_check"]["ok"])
        self.assertEqual([b["card"] for b in res["blocked"] if b["card"] == "Combo B"], ["Combo B"])
        reason = next(b["reason"] for b in res["blocked"] if b["card"] == "Combo B")
        self.assertIn("combo with Combo A", reason)
        self.assertIn("Bracket 3", reason)

    def test_allow_combos_keeps_both_pieces(self):
        res, _ = self.build(combos_fn=self.combos_fn(), allow_combos=True)
        self.assertTrue({"Combo A", "Combo B"} <= set(self.all_names(res)))

    def test_combos_are_not_checked_where_the_bracket_allows_them(self):
        calls = []
        combos = self.combos_fn()
        res, _ = self.build(self.ctx(bracket=4, targets=roles.targets(4, "value", ci="BG")),
                            combos_fn=lambda c, cards: calls.append(1) or combos(c, cards))
        self.assertEqual(calls, [])
        self.assertTrue({"Combo A", "Combo B"} <= set(self.all_names(res)))

    def test_unfetchable_combos_are_a_warning(self):
        def broken(commanders, cards):
            raise net.FetchError("spellbook", "https://x", "offline")
        res, _ = self.build(combos_fn=broken)
        self.assertEqual(res["count"], 100)
        self.assertTrue(any("Combos were not checked" in w for w in res["warnings"]))

    # --- rule-blocked cards
    def test_the_best_cards_the_rules_kept_out_are_listed(self):
        res, _ = self.build()
        blocked = {b["card"]: b for b in res["blocked"]}
        self.assertEqual(set(blocked), {"Power 04", "Power 05"})             # the Game Changers past the third
        self.assertIn("Game Changer", blocked["Power 04"]["reason"])
        self.assertGreater(blocked["Power 04"]["score"], blocked["Power 05"]["score"])

    def test_a_pool_too_small_to_fill_the_deck_is_padded_with_basics_and_says_so(self):
        w = World()
        for i in range(1, 21):
            w.add(f"Only {i:02d}", 0.5, None, types="Creature", cmc=2, cost="{2}{G}")
        db = w.db()
        res = build.build(make_ctx(w, db), db, prices=w.prices())
        self.assertEqual(res["count"], 100)
        self.assertTrue(any("could be filled" in x for x in res["warnings"]), res["warnings"])
        self.assertGreater(res["roles"]["land"], 36)


class PoolWideningTests(Isolated):
    def test_cheaper_cards_further_down_the_list_are_found_when_the_best_ones_are_too_dear(self):
        # 260 great creatures at $20 fill the best-250 pool, and a $60 budget buys two of them. The deck can only
        # be filled from the 120 cheap creatures below them, so the pool must reach down to those.
        w = World()
        for i in range(1, 261):
            w.add(f"Pricey {i:03d}", round(0.90 - 0.001 * i, 4), None, price=20.0, types="Creature", cmc=3,
                  cost="{2}{G}")
        for i in range(1, 121):
            w.add(f"Cheap {i:03d}", round(0.05 - 0.0001 * i, 4), None, price=0.1, types="Creature", cmc=3,
                  cost="{2}{B}")
        db = w.db()
        res = build.build(make_ctx(w, db), db, budget=60.0, prices=w.prices())
        self.assertEqual(res["count"], 100)
        self.assertFalse([x for x in res["warnings"] if "could be filled" in x], res["warnings"])
        self.assertLessEqual(res["spent"], 60.0)
        self.assertGreaterEqual(sum(1 for c in res["cards"] if c["name"].startswith("Cheap")), 55)
        self.assertGreaterEqual(sum(1 for c in res["cards"] if c["name"].startswith("Pricey")), 1)


class FantasyCostTests(Isolated):
    """Twenty 'Token' creatures that tokens decks love (90% of them, against 40% overall) and twenty 'Strong'
    ones that are better in general (60%) but nearly absent from tokens decks (10%)."""

    def setUp(self):
        super().setUp()
        self.w = standard_world()
        for i in range(1, 21):
            self.w.add(f"Token {i:02d}", 0.40, None, price=1.0, types="Creature", cmc=3, cost="{2}{G}")
            self.w.add(f"Strong {i:02d}", 0.60, None, price=1.0, types="Creature", cmc=3, cost="{2}{B}")
        self.db = self.w.db()
        stat = lambda p: {"decks": int(p * 1000), "of": 1000, "synergy": None}
        cards = {}
        for name, value in self.w.values.items():
            slots = {"all": stat(value), "at": None, "themes": {}, "theme_global": {}, "tourn": None, "pop": None}
            if name.startswith("Token"):
                slots["themes"] = {"tokens": stat(0.90)}
            elif name.startswith("Strong"):
                slots["themes"] = {"tokens": stat(0.10)}
            else:                                   # everything else is played as often in tokens decks: no pull
                slots["themes"] = {"tokens": stat(value)}
            cards[name] = slots
        self.evidence = {"commanders": [CMDR], "ci": "BG", "bracket": 3, "spec": SPEC, "enabled": (),
                         "at_label": "Bracket 3", "cards": cards,
                         "n": {"all": 1000, "at": 0, "themes": {"tokens": 1000}, "tourn": 0},
                         "floor_all": 0.05, "floor_at": 0.0, "tourn_totals": None, "meta": None, "salt": {},
                         "salt_floor": None, "theme_weights": {"tokens": 1.0}, "theme_src": {"tokens": "all"},
                         "precon": None, "popularity": False, "sources": {}, "warnings": []}
        mock.patch.object(score, "gather", return_value=self.evidence).start()
        mock.patch.object(roles, "tag", side_effect=lambda names, db, **kw:
                          {n: set(self.w.role_of.get(n, ())) for n in names}).start()

    def prepare(self, weight):
        spec = dict(SPEC, themes=["tokens"], weight=weight, keep_fun=False)
        return build.prepare([CMDR], 3, spec, self.db)

    def test_the_theme_shapes_the_deck_and_the_cost_is_reported(self):
        ctx = self.prepare(0.5)
        # tokens decks: 0.90 against the 0.40 overall pulls Token cards up by about 0.48 * 0.5; Strong cards
        # (0.10 against 0.60) are pulled down by the same
        self.assertGreater(ctx["scores"]["Token 01"]["parts"]["theme"], 0.2)
        self.assertLess(ctx["scores"]["Strong 01"]["parts"]["theme"], -0.2)
        res = build.build(ctx, self.db, prices=self.w.prices())
        names = {c["name"] for c in res["cards"]}
        token_count = sum(1 for n in names if n.startswith("Token"))
        self.assertGreaterEqual(token_count, 15)
        cost = res["fantasy_cost"]
        self.assertGreater(cost["power_max"], cost["power_with_theme"])
        self.assertAlmostEqual(cost["gap"], cost["power_max"] - cost["power_with_theme"])
        self.assertGreater(cost["gap_pct"], 0)
        self.assertLess(cost["gap_pct"], 100)
        self.assertTrue(cost["left_out"])
        self.assertTrue(all(c["name"].startswith("Strong") for c in cost["left_out"][:5]))
        self.assertTrue(all(c["name"] not in names for c in cost["left_out"]))
        self.assertEqual(cost["left_out"], sorted(cost["left_out"], key=lambda c: -c["score"]))
        self.assertTrue(cost["theme_picks"])
        self.assertTrue(all(p["name"].startswith("Token") and p["theme"] == "tokens" and p["pull"] > 0
                            for p in cost["theme_picks"]))
        self.assertLessEqual(len(cost["left_out"]), 8)
        self.assertLessEqual(len(cost["theme_picks"]), 8)

    def test_left_out_cards_are_described_without_the_theme(self):
        res = build.build(self.prepare(0.5), self.db, prices=self.w.prices())
        for card in res["fantasy_cost"]["left_out"]:
            self.assertNotIn("tokens decks", card["evidence"])

    def test_a_deck_without_the_theme_has_no_cost(self):
        res = build.build(self.prepare(0.0), self.db, prices=self.w.prices())
        self.assertIsNone(res["fantasy_cost"])
        self.assertGreater(sum(1 for c in res["cards"] if c["name"].startswith("Strong")), 15)

    def test_the_cost_is_never_negative(self):
        res = build.build(self.prepare(0.05), self.db, prices=self.w.prices())
        self.assertGreaterEqual(res["fantasy_cost"]["gap"], 0)


# ----------------------------------------------------------------------------- suggest
def meta_for(n, tags, bracket_counts, salt=0.3):
    return {"n_decks": n, "bracket_counts": bracket_counts, "taglinks": [{"slug": s, "label": s, "count": c}
                                                                      for s, c in tags.items()],
            "avg_types": {}, "mana_curve": {}, "salt": salt, "similar": [], "combos": [], "ci": "",
            "url": "https://x", "fetched": "2026-10-11T12:00:00Z"}


class SuggestTests(Isolated):
    def setUp(self):
        super().setUp()
        w = World()
        for name, ci in (("Squirrel King", "BG"), ("Rat Queen", "B"), ("Elf Lord", "G"), ("Dragon Boss", "R")):
            w.card(name, types=f"Legendary Creature {EM} Test", cmc=3, ci=ci, power="1", toughness="1", price=1.0)
        w.card("Plain Creature", types="Creature", cmc=3, ci="G")
        w.card("Banned King", types=f"Legendary Creature {EM} Test", cmc=3, ci="G", legal="banned", power="1",
               toughness="1")
        for i in range(1, 6):                                     # the staples the commanders play
            w.add(f"Staple {i}", 0.5, None, price=10.0 * i, types="Artifact")
        w.add("Cheap Staple", 0.5, None, price=0.5, types="Artifact")
        self.world, self.db = w, w.db()
        def listed(name, decks):
            return {"name": name, "decks": decks, "of": None, "theme_total": 70000, "url": ""}

        self.index = {"tokens": [listed("Squirrel King", 3000), listed("Rat Queen", 400), listed("Elf Lord", 100),
                                 listed("Dragon Boss", 900), listed("Plain Creature", 5000),
                                 listed("Banned King", 5000), listed("Not In The Index", 5000)],
                      "aristocrats": [listed("Squirrel King", 456)]}
        self.meta = {"Squirrel King": meta_for(10000, {"tokens": 3000, "aristocrats": 456}, {3: 1000, 4: 200}),
                     "Rat Queen": meta_for(1000, {"tokens": 400}, {3: 100, 4: 10}, salt=1.8),
                     "Elf Lord": meta_for(2000, {"tokens": 100}, {3: 50}),
                     "Dragon Boss": meta_for(3000, {"tokens": 900}, {3: 1000})}
        self.cards = {"Squirrel King": {f"Staple {i}": (900, 1000) for i in range(1, 6)},
                      "Rat Queen": {"Staple 1": (900, 1000), "Cheap Staple": (800, 1000),
                                    "Staple 5": (100, 1000)},
                      "Elf Lord": {"Cheap Staple": (900, 1000)},
                      "Dragon Boss": {"Cheap Staple": (900, 1000)}}
        self.theme_commanders = mock.patch.object(edhrec, "theme_commanders", side_effect=lambda t, **kw:
                                                  list(self.index.get(t, []))).start()
        self.commander_meta = mock.patch.object(edhrec, "commander_meta", side_effect=lambda c, *a, **kw:
                                                self.meta.get(c[0])).start()
        self.signals = mock.patch.object(edhrec, "signals", side_effect=self.fake_signals).start()
        self.stats = mock.patch.object(edhtop16, "commander_stats", side_effect=lambda c, *a, **kw:
                                       self.tournament.get(c[0])).start()
        self.tournament = {}

    def fake_signals(self, commanders, bracket=None, theme=None, **kw):
        cards = self.cards.get(commanders[0])
        if not cards:
            return []
        return [{"source": "edhrec", "kind": "builder", "commanders": commanders, "bracket": None, "theme": None,
                 "url": "", "fetched": "2026-10-11T12:00:00Z", "cache": "fresh", "n": 1000, "totals": None,
                 "meta": {}, "cards": {n: {"decks": d, "of": o, "synergy": None} for n, (d, o) in cards.items()}}]

    def suggest(self, **over):
        spec = dict(SPEC, themes=["tokens"], bracket=3, keep_fun=False)
        spec.update(over.pop("spec", {}))
        over.setdefault("sources", ("edhrec",))
        return build.suggest(spec, self.db, **over)

    def names(self, res):
        return [c["name"] for c in res["commanders"]]

    def test_the_commander_with_the_higher_theme_share_ranks_first(self):
        res = self.suggest()
        # Share of decks with the theme, over decks + 100: Rat Queen 400/1100 = 0.364, Squirrel King 3000/10100
        # = 0.297, Dragon Boss 900/3100 = 0.290, Elf Lord 100/2100 = 0.048; the bracket's decks add a little.
        self.assertEqual(self.names(res), ["Rat Queen", "Squirrel King", "Dragon Boss", "Elf Lord"])
        self.assertEqual([c["rank"] for c in res["commanders"]], [1, 2, 3, 4])
        self.assertTrue(all(res["commanders"][i]["score"] >= res["commanders"][i + 1]["score"] for i in range(3)))

    def test_the_numbers_behind_each_rank_are_reported(self):
        top = self.suggest()["commanders"][0]
        self.assertEqual((top["name"], top["ci"], top["bracket_decks"]), ("Rat Queen", "B", 100))
        share = top["theme_share"]["tokens"]
        self.assertEqual((share["decks"], share["of"]), (400, 1000))
        self.assertAlmostEqual(share["share"], 0.4)
        self.assertAlmostEqual(share["score_share"], 400 / 1100)
        self.assertAlmostEqual(top["score"], 400 / 1100 + 0.03 * 2.00432137378, places=5)    # log10(101)
        self.assertEqual(top["playstyle_share"], 0.0)

    def test_evidence_lines(self):
        top = next(c for c in self.suggest(spec={"keep_fun": True})["commanders"] if c["name"] == "Rat Queen")
        self.assertEqual(top["evidence"][:2], ["tokens: 400 of 1,000 decks (40.0%)", "100 Bracket 3 decks"])
        self.assertIn("salt 1.80", top["evidence"])
        self.assertIn("core cards about $10", top["evidence"])             # Staple 1 ($10) and the $0.50 one
        self.assertFalse([line for line in top["evidence"] if "you own" in line])

    def test_unplayable_candidates_are_skipped(self):
        res = self.suggest()
        for gone in ("Plain Creature", "Banned King", "Not In The Index"):
            self.assertNotIn(gone, self.names(res))

    def test_colors_keep_commanders_inside_them(self):
        self.assertEqual(self.names(self.suggest(colors="B")), ["Rat Queen"])
        self.assertEqual(self.names(self.suggest(colors="bg")), ["Rat Queen", "Squirrel King", "Elf Lord"])
        self.assertEqual(self.suggest(colors="B")["filters"], {"colors": "B", "budget": None})
        self.assertEqual(self.suggest(colors="GB")["filters"]["colors"], "BG")

    def test_limit_caps_the_list(self):
        self.assertEqual(self.names(self.suggest(limit=2)), ["Rat Queen", "Squirrel King"])

    def test_a_budget_drops_commanders_whose_core_costs_too_much_and_says_so(self):
        # Squirrel King's five staples (>= 40% of its decks) cost 10+20+30+40+50 = $150
        res = self.suggest(budget=100)
        self.assertNotIn("Squirrel King", self.names(res))
        self.assertTrue(any("Squirrel King" in w and "$100" in w for w in res["warnings"]), res["warnings"])
        self.assertEqual(res["filters"]["budget"], 100)

    def test_dropped_commanders_make_room_for_the_next_ones(self):
        res = self.suggest(budget=100, limit=3)
        self.assertEqual(self.names(res), ["Rat Queen", "Dragon Boss", "Elf Lord"])

    def test_what_you_own_lifts_a_commander(self):
        base = self.suggest()
        owned = self.suggest(owned=[f"Staple {i}" for i in range(1, 6)])
        top = {c["name"]: c for c in owned["commanders"]}
        self.assertEqual(top["Squirrel King"]["owned_share"], 1.0)
        self.assertAlmostEqual(top["Rat Queen"]["owned_share"], 2 / 3)    # Staple 1 and Staple 5 of its 3 cards
        self.assertIn("you own 100% of its top cards", top["Squirrel King"]["evidence"])
        before = {c["name"]: c["score"] for c in base["commanders"]}
        self.assertAlmostEqual(top["Squirrel King"]["score"], before["Squirrel King"] + 0.15)

    def test_owned_share_is_none_without_an_owned_list(self):
        self.assertIsNone(self.suggest()["commanders"][0]["owned_share"])

    def test_salt_costs_a_little_when_keep_it_fun_is_on(self):
        quiet = {c["name"]: c["score"] for c in self.suggest()["commanders"]}
        fun = {c["name"]: c["score"] for c in self.suggest(spec={"keep_fun": True})["commanders"]}
        self.assertAlmostEqual(fun["Rat Queen"], quiet["Rat Queen"] - 0.05 * 0.8)       # salt 1.8
        self.assertAlmostEqual(fun["Squirrel King"], quiet["Squirrel King"])             # salt 0.3 is under 1

    def test_the_tournament_record_counts_at_bracket_4_and_up(self):
        self.tournament = {"Squirrel King": {"entries": 284, "topcuts": 68, "conversion": 0.30, "win_rate": 0.27},
                           "Rat Queen": {"entries": 40, "topcuts": 0, "conversion": 0.0, "win_rate": 0.2}}
        res = self.suggest(spec={"bracket": 4})
        self.assertGreater(len(res["commanders"]), 0)
        by = {c["name"]: c for c in res["commanders"]}
        self.assertEqual(by["Squirrel King"]["tournament"], {"entries": 284, "conversion": 0.30})
        self.assertIn("EDHTop16: 284 entries, 30% top cut", by["Squirrel King"]["evidence"])
        self.assertIn("EDHTop16: 40 entries, 0% top cut (too few to judge)", by["Rat Queen"]["evidence"])
        plain = {c["name"]: c["score"] for c in self.suggest(spec={"bracket": 4})["commanders"]}
        self.tournament = {}
        no_data = {c["name"]: c["score"] for c in self.suggest(spec={"bracket": 4})["commanders"]}
        self.assertAlmostEqual(plain["Squirrel King"] - no_data["Squirrel King"], 0.2 * (0.30 - 0.2))
        self.assertAlmostEqual(plain["Rat Queen"] - no_data["Rat Queen"], 0.2 * (0.0 - 0.2))   # 40 >= 30 entries

    def test_too_few_tournament_entries_do_not_move_the_score(self):
        self.tournament = {"Rat Queen": {"entries": 12, "topcuts": 0, "conversion": 0.0, "win_rate": 0.2}}
        with_stats = {c["name"]: c["score"] for c in self.suggest(spec={"bracket": 4})["commanders"]}
        self.tournament = {}
        without = {c["name"]: c["score"] for c in self.suggest(spec={"bracket": 4})["commanders"]}
        self.assertAlmostEqual(with_stats["Rat Queen"], without["Rat Queen"])

    def test_tournament_data_is_not_fetched_below_bracket_4(self):
        self.suggest()
        self.stats.assert_not_called()

    def test_a_commander_with_almost_no_decks_in_the_theme_is_not_suggested_for_it(self):
        # Rat Queen's playstyle share is large, but 5 tokens decks are not a tokens deck
        self.meta["Rat Queen"] = meta_for(1000, {"tokens": 5, "aristocrats": 900}, {3: 100})
        res = self.suggest(spec={"playstyle": "aristocrats"})
        self.assertNotIn("Rat Queen", self.names(res))
        self.assertIn("Squirrel King", self.names(res))

    def test_the_playstyles_themes_stand_in_when_no_theme_is_named(self):
        res = self.suggest(spec={"themes": [], "playstyle": "aristocrats"})
        asked = {c.args[0] for c in self.theme_commanders.call_args_list}
        self.assertEqual(asked, {"aristocrats", "sacrifice", "lifedrain"})
        self.assertEqual(self.names(res), ["Squirrel King"])
        top = res["commanders"][0]
        self.assertAlmostEqual(top["playstyle_share"], 456 / 10000)
        self.assertTrue(any(line.startswith("Aristocrats themes:") for line in top["evidence"]))

    def test_with_nothing_to_match_there_is_a_warning(self):
        res = self.suggest(spec={"themes": [], "playstyle": "value"})
        self.assertEqual(res["commanders"], [])
        self.assertTrue(any("Pick a theme" in w for w in res["warnings"]))

    def test_without_edhrec_it_says_what_is_missing(self):
        res = self.suggest(sources=("archidekt", "edhtop16"))
        self.assertEqual(res["commanders"], [])
        self.assertTrue(any("needs EDHREC" in w for w in res["warnings"]))
        self.theme_commanders.assert_not_called()

    def test_a_failing_page_is_a_warning_and_the_rest_still_rank(self):
        self.commander_meta.side_effect = lambda c, *a, **kw: (_ for _ in ()).throw(
            net.FetchError("edhrec", "https://x", "HTTP 500")) if c[0] == "Rat Queen" else self.meta.get(c[0])
        res = self.suggest()
        self.assertNotIn("Rat Queen", self.names(res))
        self.assertIn("Squirrel King", self.names(res))
        self.assertTrue(any("EDHREC unavailable" in w and "HTTP 500" in w for w in res["warnings"]))

    def test_many_failed_pages_make_one_warning(self):
        down = net.FetchError("edhrec", "https://x", "HTTP 500")
        self.commander_meta.side_effect = lambda c, *a, **kw: (_ for _ in ()).throw(down)
        res = self.suggest()
        self.assertEqual(res["commanders"], [])
        self.assertEqual(res["warnings"], ["EDHREC unavailable for Squirrel King's page, Dragon Boss's page, "
                                           "Rat Queen's page and 1 more: HTTP 500"])

    def test_the_result_shape(self):
        res = self.suggest()
        self.assertEqual(set(res), {"command", "spec", "bracket", "filters", "commanders", "warnings", "sources"})
        self.assertEqual(set(res["commanders"][0]), {"rank", "name", "ci", "score", "theme_share",
                                                      "playstyle_share", "bracket_decks", "salt", "tournament",
                                                      "core_cost", "owned_share", "evidence"})
        self.assertEqual(res["command"], "suggest")
        self.assertEqual(res["bracket"], 3)
        self.assertIn("edhrec", res["sources"])
        self.assertEqual(res["sources"]["edhrec"]["fetched"], "2026-10-11T12:00:00Z")

    def test_candidates_are_capped_by_theme_deck_count(self):
        many = [{"name": f"Cmdr {i:02d}", "decks": 1000 - i, "of": None, "theme_total": 1, "url": ""}
                for i in range(1, 41)]
        for rec in many:
            self.world.card(rec["name"], types=f"Legendary Creature {EM} Test", cmc=3, ci="G", power="1",
                            toughness="1")
            self.meta[rec["name"]] = meta_for(5000, {"tokens": rec["decks"]}, {3: 100})
        self.db = self.world.db()
        self.index["tokens"] = many
        self.suggest(limit=40)
        self.assertEqual(self.commander_meta.call_count, build.SUGGEST_CANDIDATES)
        asked = {c.args[0][0] for c in self.commander_meta.call_args_list}
        self.assertIn("Cmdr 01", asked)
        self.assertNotIn("Cmdr 40", asked)


# ----------------------------------------------------------------------------- small helpers
class HelperTests(unittest.TestCase):
    def test_largest_remainder_split(self):
        # 10 basics, G:B pips 3:1. Each color first gets one; the other 8 split 6:2 -> G 7, B 3.
        self.assertEqual(build._allocate(10, {"G": 3.0, "B": 1.0}), {"G": 7, "B": 3})

    def test_every_color_gets_a_basic_when_there_is_room(self):
        self.assertEqual(build._allocate(5, {"W": 20.0, "U": 0.0, "B": 0.0}), {"W": 3, "U": 1, "B": 1})

    def test_with_no_symbols_the_basics_are_split_evenly(self):
        self.assertEqual(build._allocate(7, {"G": 0.0, "B": 0.0}), {"B": 4, "G": 3})

    def test_fewer_basics_than_colors_go_to_the_biggest_demand(self):
        self.assertEqual(build._allocate(1, {"G": 5.0, "B": 1.0}), {"G": 1})
        self.assertEqual(build._allocate(0, {"G": 5.0}), {})

    def test_the_split_always_adds_up(self):
        rng = random.Random(3)
        for _ in range(200):
            colors = rng.sample("WUBRG", rng.randint(1, 5))
            weights = {c: rng.random() * rng.choice((0, 1, 10)) for c in colors}
            total = rng.randint(1, 40)
            self.assertEqual(sum(build._allocate(total, weights).values()), total)

    def test_hybrid_and_phyrexian_pips(self):
        rec = carddb.card_record(scry("Hybrid", cost="{W/B}{B}{G/P}{2}"))
        got = build._pips(rec, "BG")
        self.assertAlmostEqual(got["B"], 2.0)         # {W/B} can only be paid with B in a B/G deck, plus {B}
        self.assertAlmostEqual(got["G"], 1.0)         # {G/P}
        self.assertEqual(got.get("W", 0), 0)
        both = build._pips(carddb.card_record(scry("Both", cost="{B/G}{B/G}")), "BG")
        self.assertEqual((both["B"], both["G"]), (1.0, 1.0))      # each hybrid symbol is split between its colors

    def test_short_block_reason(self):
        text = ("completes a two-card combo with X (Infinite mana): Commander Spellbook rates it for Bracket "
                "4 or higher; Bracket 3 allows two-card combos only late in the game, so it blocks them")
        self.assertEqual(build._short_block(text, 3), "completes a two-card combo with X (Infinite mana) "
                                                     "(needs Bracket 4)")
        self.assertEqual(build._short_block("completes a combo with Y: a two-card infinite combo, which "
                                            "Bracket 2 does not allow", 2),
                         "completes a combo with Y (not allowed at Bracket 2)")
        self.assertEqual(build._short_block("Foo is a Game Changer; Bracket 2 allows none", 2),
                         "Foo is a Game Changer; Bracket 2 allows none")


if __name__ == "__main__":
    unittest.main()
