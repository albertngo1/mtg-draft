"""Tests for build.py: the value of a deck (role marginals, lands, top end), the exactness of the swap
arithmetic, `prepare`, `upgrade`, `build` and `suggest`.

Everything runs on a synthetic world of cards with known scores, roles and prices (World below), so each
assertion is a worked example rather than a snapshot of real data. Combos and prices come in through the
`combos_fn` and `prices` arguments; providers and net are closed, so nothing here can reach the network."""
import collections, json, math, os, random, shutil, tempfile, time, unittest
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
        # `upgrade` asks for the attribute tags (which kinds of threat each card answers). Left alone that would read
        # whatever tag cache this machine has, or fail on one that has none, so every test starts with tags that load
        # and that no card carries: the answers floors then bind nothing, and the AnswerTests below set real ones.
        self.tag_calls = []
        mock.patch.object(roles, "attributes", side_effect=self.no_tags).start()
        mock.patch.object(roles, "attributes_loaded", return_value=True).start()
        self.addCleanup(mock.patch.stopall)

    def no_tags(self, names, db, **kw):
        self.tag_calls.append(list(names))
        return {name: frozenset() for name in names}

    def set_tags(self, tags, loaded=True):
        """Give the cards of a test attribute tags, {card name: slugs}; a card that is not in it carries none.
        `loaded=False` is the tag data being unavailable."""
        def tagged(names, db, **kw):
            self.tag_calls.append(list(names))
            return {n: frozenset(tags.get(n, ())) for n in names}
        roles.attributes.side_effect = tagged
        roles.attributes_loaded.return_value = loaded

    def set_bands(self, **bands):
        """Fix the answer bands of the bracket: set_bands(enchantments=(4, 5, 9)) is a minimum of 4 answers to
        enchantments, a target of 5 and a maximum of 9. A kind that is not named has no band."""
        fixed = {f"answers_{kind}": {"min": lo, "target": mid, "max": hi} for kind, (lo, mid, hi) in bands.items()}
        return mock.patch.object(roles, "answer_bands", return_value=fixed).start()


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


def run_upgrade(w, deck_names, candidate_names=None, *, targets=None, owned=(), include=(), exclude=(), keep=(),
                prices=None, bracket=3, **kw):
    db = w.db()
    names = list(deck_names) + list(candidate_names or [])
    more = {"keep": set(keep)} if keep else {}                 # the key is optional: prepare never sets it
    ctx = make_ctx(w, db, names=names, bracket=bracket, targets=targets or zero_targets(), owned=set(owned),
                   include=list(include), exclude=set(exclude), **more)
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

    # --- keep: cards the caller wants to stay through the optional swaps (the deck pages keep what the player added)
    def test_kept_cards_are_never_cut_by_an_optional_swap(self):
        # Dud A (0.05) would go first; kept, it stays and Dud B and Dud C go. A kept card is in the deck, so there is
        # nothing to say about an include that is missing from it
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple", "Okay"], keep=["Dud A"], max_swaps=2)
        self.assertEqual([s["cut"] for s in res["swaps"]], ["Dud B", "Dud C"])
        self.assertEqual([w for w in res["warnings"] if "include" in w], [])

    def test_a_kept_card_that_breaks_a_bracket_limit_is_still_cut_by_the_forced_swap(self):
        # unlike an include (the player's own list, which no repair touches), keep holds back only the optional swaps:
        # the two weakest of five Game Changers go as they would without it, with nothing said about a repair that
        # could not be made
        w = self.gc_world()
        deck = ["Filler"] + [f"GC {i}" for i in range(1, 6)]
        res, _, _ = run_upgrade(w, deck, ["Staple", "Okay", "Decent", "Fine"], keep=["GC 5", "GC 4"], max_swaps=0)
        self.assertEqual([s["cut"] for s in res["swaps"] if s["forced"]], ["GC 5", "GC 4"])
        self.assertTrue(res["bracket_after"]["ok"])
        self.assertEqual([w for w in res["warnings"] if "Could not fix" in w], [])

    def test_a_kept_card_that_is_banned_now_is_still_cut_first(self):
        w = self.world()
        w.add("Banned Spell", 0.99, None, legal="banned")
        res, _, _ = run_upgrade(w, self.DECK + ["Banned Spell"], ["Staple"], keep=["Banned Spell"], max_swaps=0)
        self.assertEqual([(s["cut"], s["forced"]) for s in res["swaps"]], [("Banned Spell", True)])
        self.assertIn("not legal in Commander", res["swaps"][0]["reason"])

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

    # --- basic lands: the two ways a long upgrade used to ruin the mana
    CULTIVATE = ("Search your library for up to two basic land cards, reveal those cards, put one onto the "
                 "battlefield tapped and the other into your hand, then shuffle.")
    EVOLVING_WILDS = ("{T}, Sacrifice Evolving Wilds: Search your library for a basic land card, put it onto the "
                      "battlefield tapped, then shuffle.")

    def test_upgrade_keeps_basics_for_the_decks_land_searchers(self):
        # Evolving Wilds (one basic) and Cultivate (two) can take three basic lands out of the library. A basic
        # scores 0, so each of the eight two-color lands beats one; with nothing to stop it every basic went and
        # both searchers found nothing.
        w = World()
        w.add("Cultivate", 0.80, None, types="Sorcery", cmc=3, cost="{2}{G}", text=self.CULTIVATE)
        w.add("Evolving Wilds", 0.70, None, types="Land", text=self.EVOLVING_WILDS)
        duals = [f"Dual {i}" for i in range(1, 9)]
        for name in duals:
            w.add(name, 0.60, None, types="Land", produced=["B", "G"], ci="BG")
        deck = ["Cultivate", "Evolving Wilds"] + ["Forest"] * 4 + ["Swamp"] * 4
        nine_lands = zero_targets(land={"min": 9, "target": 9, "max": 9})     # a land for a land changes nothing
        res, _, _ = run_upgrade(w, deck, duals, targets=nine_lands)
        kept = {name: n for n, name in res["deck_after"]["cards"]}
        self.assertEqual(kept.get("Forest", 0) + kept.get("Swamp", 0), 3,
                         "Evolving Wilds and Cultivate can take 3 basics, so 3 must stay in the deck")

    def test_upgrade_cuts_the_basic_of_the_color_the_deck_needs_least(self):
        # A green deck: six {G}{G} creatures and two {B} ones (12 green symbols to 2 black), with 14 Forest listed
        # before 14 Swamp. Six colorless utility lands take six basic slots. Equal gains used to go to whichever
        # basic came first in the list, so all six Forests went and the green deck was left with 8 green sources
        # against 14 black.
        w = World()
        spells = [f"Green Beast {i}" for i in range(1, 7)] + [f"Black Imp {i}" for i in range(1, 3)]
        for name in spells:
            w.add(name, 0.50, None, types="Creature", cmc=2, cost="{G}{G}" if "Green" in name else "{B}")
        utility = [f"Utility Land {i}" for i in range(1, 7)]
        for name in utility:
            w.add(name, 0.50, None, types="Land", produced=["C"])
        deck = spells + ["Forest"] * 14 + ["Swamp"] * 14
        twenty_eight_lands = zero_targets(land={"min": 28, "target": 28, "max": 28})
        res, _, _ = run_upgrade(w, deck, utility, targets=twenty_eight_lands)
        kept = {name: n for n, name in res["deck_after"]["cards"]}
        self.assertEqual((kept["Forest"], kept["Swamp"]), (14, 8),
                         "the black basics are the ones to cut: black has the most lands per colored symbol")

    def test_upgrade_keeps_basics_of_every_color_for_its_searchers(self):
        # The same green deck with Cultivate and Evolving Wilds, which can take 3 basics. Black has the most lands
        # per symbol, so the Swamps go first; with only a total to keep, all four went and the searchers could
        # fetch nothing but Forests. The 3 basics kept are split the way `build` splits basics (one per color,
        # the rest by colored symbols: 13 green to 2 black), so one Swamp stays.
        w = World()
        w.add("Cultivate", 0.80, None, types="Sorcery", cmc=3, cost="{2}{G}", text=self.CULTIVATE)
        w.add("Evolving Wilds", 0.70, None, types="Land", text=self.EVOLVING_WILDS)
        spells = [f"Green Beast {i}" for i in range(1, 7)] + [f"Black Imp {i}" for i in range(1, 3)]
        for name in spells:
            w.add(name, 0.50, None, types="Creature", cmc=2, cost="{G}{G}" if "Green" in name else "{B}")
        duals = [f"Dual {i}" for i in range(1, 9)]
        for name in duals:
            w.add(name, 0.60, None, types="Land", produced=["B", "G"], ci="BG")
        deck = ["Cultivate", "Evolving Wilds"] + spells + ["Forest"] * 4 + ["Swamp"] * 4
        nine_lands = zero_targets(land={"min": 9, "target": 9, "max": 9})
        res, _, _ = run_upgrade(w, deck, duals, targets=nine_lands)
        kept = {name: n for n, name in res["deck_after"]["cards"]}
        self.assertEqual((kept.get("Forest", 0), kept.get("Swamp", 0)), (2, 1),
                         "3 basics stay for the searchers, and black keeps one of them")

    # --- result shape
    def test_swap_records_carry_the_evidence_and_the_fills(self):
        res, ctx, _ = run_upgrade(self.world(), self.DECK, ["Staple"], max_swaps=1)
        swap = res["swaps"][0]
        self.assertEqual(set(swap), {"rank", "cut", "add", "gain", "price", "owned", "forced", "reason", "fills",
                                     "evidence_add", "evidence_cut", "kind_add", "price_point"})
        self.assertIsNone(swap["price_point"])                    # no budget, so no price points to belong to
        self.assertEqual(swap["evidence_add"], ctx["scores"]["Staple"]["evidence"])
        self.assertEqual(swap["evidence_cut"], ctx["scores"]["Dud A"]["evidence"])
        self.assertEqual(swap["kind_add"], "builder")
        self.assertEqual(swap["price"], 1.0)

    def test_the_result_has_every_documented_key(self):
        res, _, _ = run_upgrade(self.world(), self.DECK, ["Staple"], max_swaps=1)
        self.assertEqual(set(res), {"command", "deck", "bracket", "budget", "spent", "spec", "swaps",
                                    "price_points", "blocked", "cheap_adds", "roles_before", "roles_after",
                                    "answers_before", "answers_after", "targets", "value_before", "value_after",
                                    "bracket_before", "bracket_after", "deck_after", "warnings", "sources"})
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

    def test_no_swap_limit_and_four_price_points_is_still_fast(self):
        # The default for a $200 budget: the price-aware sweep runs at $25, $50, $100 and $200, each as long as
        # swaps keep beating MIN_GAIN. About 60 swaps here, a bit over half a second.
        w = standard_world()
        for i in range(1, 181):
            w.add(f"Extra {i:03d}", round(0.55 - 0.002 * i, 4), ("ramp", "draw", "removal", None)[i % 4],
                  price=1.0 + i % 7, types="Creature", cmc=3, cost="{2}{G}")
        db = w.db()
        deck = {"commanders": [CMDR], "cards": [(1, f"Beast {i:02d}") for i in range(1, 63)]
                + [(1, f"Dual {i:02d}") for i in range(1, 6)] + [(16, "Forest"), (16, "Swamp")]}
        started = time.time()
        res = build.upgrade(make_ctx(w, db), deck, db, budget=200.0, prices=w.prices())
        elapsed = time.time() - started
        self.assertEqual([p["budget"] for p in res["price_points"]], [25.0, 50.0, 100.0, 200.0])
        self.assertGreater(len(res["swaps"]), 15)                      # more than the old default cap allowed
        self.assertLess(elapsed, 3.0, f"upgrade took {elapsed:.1f}s")


# ----------------------------------------------------------------------------- price points
class PricePointTests(Isolated):
    """A budget is climbed in steps, the price points. Each step may spend up to its amount, counting what the
    steps before it spent, and builds on the list they left: the first swaps are what a small wallet would buy,
    and each bigger one only adds to them."""

    def test_a_budget_halves_down_to_at_most_four_round_price_points(self):
        cases = [
            (200, [25, 50, 100, 200]),     # halves 100, 50, 25; a fourth half (12.5) would be a fifth point
            (1000, [125, 250, 500, 1000]),
            (75, [20, 40, 75]),            # 37.5 rounds half-up to 40, 18.75 to 20; the next half, 9.4, is under $10
            (50, [15, 25, 50]),            # 25, then 12.5 rounds half-up (not to an even 10) to 15; 6.25 is too small
            (30, [15, 30]),                # 15; the next half, 7.5, is under $10
            (15, [15]),                    # half of it, 7.5, is under $10: the budget stands alone
            (5, [5]),
            (0, [0]),
            (75.5, [20, 40, 75.5]),        # only the halves are rounded; the budget keeps its cents
        ]
        for budget, expected in cases:
            with self.subTest(budget=budget):
                self.assertEqual(build.default_price_points(budget), expected)

    def test_named_price_points_are_sorted_once_each_and_end_at_the_budget(self):
        ladder = build._price_ladder
        self.assertEqual(ladder(100, [50, 25, 50]), [25, 50, 100])
        self.assertEqual(ladder(100, [150, 100, 40]), [40, 100])      # at or over the budget: dropped
        self.assertEqual(ladder(100, [0, -5, 40]), [40, 100])         # only amounts above $0 count
        self.assertEqual(ladder(100, []), [100])
        self.assertEqual(ladder(100, None), build.default_price_points(100))
        self.assertEqual((ladder(None, [25, 50]), ladder(None, None)), ([], []))     # no budget, no steps

    # Eight duds to replace and six cards to buy, each with a score and a price:
    #   Cheap A 0.50 $2   Cheap B 0.45 $3   Mid A 0.70 $8   Mid B 0.65 $9   Dear A 0.90 $18   Dear B 0.85 $20
    DUDS = [f"Dud {i}" for i in range(1, 9)]
    BUYS = ["Cheap A", "Cheap B", "Mid A", "Mid B", "Dear A", "Dear B"]

    def world(self):
        w = mini(**{name: 0.0 for name in self.DUDS})
        for name, value, price in (("Cheap A", 0.50, 2.0), ("Cheap B", 0.45, 3.0), ("Mid A", 0.70, 8.0),
                                   ("Mid B", 0.65, 9.0), ("Dear A", 0.90, 18.0), ("Dear B", 0.85, 20.0)):
            w.add(name, value, None, price=price)
        return w

    def upgrade(self, **kw):
        return run_upgrade(self.world(), self.DUDS, self.BUYS, **kw)

    def by_hand(self, res, ctx, db, point):
        """What a price point should say, rebuilt without the engine's helper: apply the kept swaps found up to
        that point, in order, to the starting list and value it."""
        kept = [s for s in res["swaps"] if s["price_point"] is None or s["price_point"] <= point]
        names = list(self.DUDS)
        for s in kept:
            names.remove(s["cut"])
            names.append(s["add"])
        return {"spent": round(sum(s["price"] or 0.0 for s in kept), 2),
                "value": build.deck_value(names, ctx, db)["total"], "swaps": len(kept)}

    def test_each_step_buys_within_its_price_point_and_builds_on_the_one_before(self):
        res, ctx, db = self.upgrade(budget=40.0, price_points=[10, 25])
        steps = {}
        for s in res["swaps"]:
            steps.setdefault(s["price_point"], []).append(s["add"])
        # $10 buys Mid A and Cheap A; $25 adds Mid B and Cheap B with the $15 on top; $40 adds Dear A with $18
        self.assertEqual({p: sorted(adds) for p, adds in steps.items()},
                         {10.0: ["Cheap A", "Mid A"], 25.0: ["Cheap B", "Mid B"], 40.0: ["Dear A"]})
        self.assertEqual([p["budget"] for p in res["price_points"]], [10.0, 25.0, 40.0])
        self.assertEqual([p["spent"] for p in res["price_points"]], [10.0, 22.0, 40.0])
        self.assertEqual([p["swaps"] for p in res["price_points"]], [2, 4, 5])
        for p in res["price_points"]:
            self.assertLessEqual(p["spent"], p["budget"])           # no forced swaps here, so nothing goes over
        values = [p["value"] for p in res["price_points"]]
        self.assertEqual(values, sorted(values))                    # more money never leaves the deck worth less
        self.assertGreater(values[0], res["value_before"])

    def test_the_summaries_equal_a_replay_of_the_kept_swaps_and_the_last_one_is_the_whole_result(self):
        res, ctx, db = self.upgrade(budget=40.0, price_points=[10, 25])
        for line in res["price_points"]:
            with self.subTest(point=line["budget"]):
                want = self.by_hand(res, ctx, db, line["budget"])
                self.assertEqual((line["spent"], line["swaps"]), (want["spent"], want["swaps"]))
                self.assertAlmostEqual(line["value"], want["value"])
        last = res["price_points"][-1]
        self.assertEqual((last["budget"], last["spent"], last["swaps"]), (40.0, res["spent"], len(res["swaps"])))
        self.assertAlmostEqual(last["value"], res["value_after"])

    def test_swaps_are_tagged_with_their_step_in_order_and_a_later_step_never_cuts_an_earlier_buy(self):
        res, _, _ = self.upgrade(budget=40.0, price_points=[10, 25])
        tags = [s["price_point"] for s in res["swaps"]]
        self.assertEqual(tags, sorted(tags))
        self.assertTrue(set(tags) <= {10.0, 25.0, 40.0})
        bought = set()
        for s in res["swaps"]:
            self.assertNotIn(s["cut"], bought)
            bought.add(s["add"])

    def test_the_default_steps_are_used_when_none_are_named(self):
        res, _, _ = self.upgrade(budget=40.0)
        self.assertEqual([p["budget"] for p in res["price_points"]], build.default_price_points(40.0))
        self.assertEqual([p["budget"] for p in res["price_points"]], [10.0, 20.0, 40.0])

    def test_named_steps_at_or_over_the_budget_are_dropped_and_the_budget_closes_the_list(self):
        res, _, _ = self.upgrade(budget=40.0, price_points=[60, 25, 40, 25])
        self.assertEqual([p["budget"] for p in res["price_points"]], [25.0, 40.0])

    def test_one_price_point_is_the_plain_budget_run(self):
        # $10 is too small to halve, so the budget stands alone: a single step, which is the run `upgrade` made
        # before steps existed. Naming that one point, or points that leave only the budget, changes nothing.
        w = mini(**{"Dud A": 0.0, "Dud B": 0.0, "Dud C": 0.0, "Pricey": 0.9, "Cheap A": 0.5, "Cheap B": 0.5,
                    "Cheap C": 0.5})
        w.price_of.update({"Pricey": 10.0, "Cheap A": 2.0, "Cheap B": 2.0, "Cheap C": 2.0})
        deck, buys = ["Dud A", "Dud B", "Dud C"], ["Pricey", "Cheap A", "Cheap B", "Cheap C"]
        plain, _, _ = run_upgrade(w, deck, buys, budget=10.0)
        self.assertEqual({s["add"] for s in plain["swaps"]}, {"Cheap A", "Cheap B", "Cheap C"})   # price-aware
        self.assertEqual([p["budget"] for p in plain["price_points"]], [10.0])
        self.assertEqual({s["price_point"] for s in plain["swaps"]}, {10.0})

        def shape(res):
            swaps = [(s["cut"], s["add"], s["gain"], s["price"]) for s in res["swaps"]]
            return swaps, res["spent"], res["value_after"]

        for points in ([10], [], [10, 50], [0, 10]):
            with self.subTest(price_points=points):
                same, _, _ = run_upgrade(w, deck, buys, budget=10.0, price_points=points)
                self.assertEqual(shape(same), shape(plain))
                self.assertEqual(same["price_points"], plain["price_points"])

    def test_without_a_budget_there_are_no_steps(self):
        res, _, _ = self.upgrade(price_points=[10, 25])             # named points mean nothing with no budget
        self.assertEqual(res["price_points"], [])
        self.assertTrue(res["swaps"])
        self.assertEqual({s["price_point"] for s in res["swaps"]}, {None})

    def test_the_swap_limit_counts_across_the_steps(self):
        res, _, _ = self.upgrade(budget=40.0, price_points=[10, 25], max_swaps=3)
        # two swaps at $10, then one at $25; the third step has nothing left to do
        self.assertEqual([s["price_point"] for s in res["swaps"]], [10.0, 10.0, 25.0])
        self.assertEqual([p["swaps"] for p in res["price_points"]], [2, 3, 3])
        self.assertEqual(res["price_points"][1]["spent"], res["price_points"][2]["spent"])

    def test_forced_swaps_belong_to_no_step_and_may_spend_past_a_small_first_point(self):
        # Bracket 2 allows no Game Changers, so GC 1 must go, and the best legal replacement is the $30 Gem. That is
        # forced, so it may use the budget ($40) whatever the first price point ($10) says. Inside that first step
        # nothing more can be paid for, but the owned Gem still costs nothing, so it is taken; the $2 Okay waits
        # for the second step.
        w = mini(**{"Dud 1": 0.0, "Dud 2": 0.0, "Gem": 0.9, "Okay": 0.6, "Owned Gem": 0.55})
        w.add("GC 1", 0.5, None, gc=True)
        w.price_of.update({"Gem": 30.0, "Okay": 2.0, "Owned Gem": 25.0})
        res, _, _ = run_upgrade(w, ["GC 1", "Dud 1", "Dud 2"], ["Gem", "Okay", "Owned Gem"], bracket=2,
                                budget=40.0, price_points=[10], owned=["Owned Gem"])
        self.assertEqual([(s["add"], s["forced"], s["price_point"]) for s in res["swaps"]],
                         [("Gem", True, None), ("Owned Gem", False, 10.0), ("Okay", False, 40.0)])
        self.assertEqual([(p["budget"], p["spent"], p["swaps"]) for p in res["price_points"]],
                         [(10.0, 30.0, 2), (40.0, 32.0, 3)])          # the first line is over $10: the forced Gem

    def test_a_combo_repair_that_undoes_a_swap_leaves_the_steps_true_to_the_kept_swaps(self):
        # Combo A and Combo B are harmless one at a time and both fit inside the first step, so the repair undoes
        # the later one (B) after the search. The step lines must describe the swaps that were kept.
        pair = {"id": "9-9", "cards": ["Combo A", "Combo B"], "missing": [], "produces": ["Infinite mana"],
                "bracket_tag": "R", "min_bracket": 4, "two_card": True, "infinite": True, "url": ""}
        combos = lambda commanders, cards: {"included": [pair] if {"Combo A", "Combo B"} <= set(cards) else [],
                                            "almost": []}
        w = mini(**{name: 0.0 for name in self.DUDS[:5]})
        for name, value, price in (("Combo A", 0.97, 3.0), ("Combo B", 0.96, 3.0), ("Staple", 0.90, 1.0),
                                   ("Okay", 0.50, 2.0)):
            w.add(name, value, None, price=price)
        res, ctx, db = run_upgrade(w, self.DUDS[:5], ["Combo A", "Combo B", "Staple", "Okay"], budget=20.0,
                                   price_points=[8], combos_fn=combos)
        adds = [(s["add"], s["price_point"]) for s in res["swaps"]]
        self.assertEqual(adds, [("Combo A", 8.0), ("Staple", 8.0), ("Okay", 20.0)])     # B was undone
        self.assertTrue(any(x.startswith("Undid ") and "Combo B" in x for x in res["warnings"]), res["warnings"])
        self.assertEqual([(p["budget"], p["spent"], p["swaps"]) for p in res["price_points"]],
                         [(8.0, 4.0, 2), (20.0, 6.0, 3)])
        for line in res["price_points"]:
            names = list(self.DUDS[:5])
            for s in [s for s in res["swaps"] if s["price_point"] <= line["budget"]]:
                names.remove(s["cut"])
                names.append(s["add"])
            self.assertAlmostEqual(line["value"], build.deck_value(names, ctx, db)["total"])
        self.assertAlmostEqual(res["price_points"][-1]["value"], res["value_after"])

    def test_each_price_point_line_has_the_documented_keys(self):
        res, _, _ = self.upgrade(budget=40.0)
        self.assertEqual(set(res["price_points"][0]), {"budget", "spent", "value", "swaps", "change", "answers",
                                                       "weakens"})


# ----------------------------------------------------------------------------- answers to each kind of threat
ENCH, WALK, ARTI, CREA, SPEL = ("answers_enchantments", "answers_planeswalkers", "answers_artifacts",
                                "answers_creatures", "answers_spells")
ENCH_TAG, WALK_TAG, SPELL_TAG = ["removal-enchantment"], ["removal-planeswalker"], ["counterspell"]


class KeepsAnswersTests(Isolated):
    """Plan.keeps_answers: after a swap each kind of threat keeps at least min(the answers it has now, its floor), the
    floor being what a typical deck at the bracket holds (`upgrade` takes it from the band's target). Every case is a
    list with a known number of answers to enchantments (Ench 1, 2, ...), one answer to planeswalkers, and a Bear that
    answers nothing."""

    def keeps(self, cut, add, *, ench, floors, extra=()):
        names = {"Bear": 0.1, "Dud": 0.1, "Ench New": 0.9, "Walker 1": 0.0, "Walker New": 0.9, "Pulse": 0.0,
                 "Pulse New": 0.9}
        names.update({f"Ench {i}": 0.0 for i in range(1, ench + 1)})
        w = mini(**names)
        db = w.db()
        answers = {name: frozenset({ENCH}) for name in names if name.startswith("Ench")}
        answers.update({"Walker 1": frozenset({WALK}), "Walker New": frozenset({WALK}),
                        "Pulse": frozenset({ENCH, WALK}), "Pulse New": frozenset({ENCH, WALK})})
        model = build.Model(make_ctx(w, db, names=list(names), targets=zero_targets()), db, answers=answers)
        plan = build.Plan(model, db, "BG", 3, prices={}, owned=set())
        for name in ["Bear", "Walker 1"] + [f"Ench {i}" for i in range(1, ench + 1)] + list(extra):
            plan.add(name)
        plan.answer_floors = floors
        return plan.keeps_answers(model.facts(cut), model.facts(add))

    def test_worked_examples_one_kind_of_threat(self):
        cases = [
            # (answers to enchantments, floors, card cut, card added, whether the swap may happen, the situation)
            (7, {ENCH: 4}, "Ench 1", "Dud", True, "7 answers and a floor of 4: it may fall to 6"),
            (5, {ENCH: 4}, "Ench 1", "Dud", True, "5 answers: it may trade down to 4, the floor itself"),
            (4, {ENCH: 4}, "Ench 1", "Dud", False, "4 answers is the floor: it may not fall to 3"),
            (2, {ENCH: 4}, "Ench 1", "Dud", False, "a list that starts under the floor keeps what it has"),
            (2, {ENCH: 4}, "Ench 1", "Ench New", True, "under the floor, another answer of that kind may replace one"),
            (4, {ENCH: 4}, "Ench 1", "Ench New", True, "at the floor, one answer for another answer is fine"),
            (4, {ENCH: 4}, "Ench 1", "Walker New", False, "an answer to planeswalkers does not make up for one to "
                                                           "enchantments"),
            (4, {ENCH: 4}, "Bear", "Dud", True, "a card that answers nothing can always be cut"),
            (4, {ENCH: 4}, "Bear", "Ench New", True, "and an answer can always be added"),
            (4, {ENCH: 0}, "Ench 1", "Dud", True, "a floor of 0 asks for nothing"),
            (0, {ENCH: 4}, "Bear", "Dud", True, "no answers at all and nothing cut that answered anything"),
            (4, {WALK: 1}, "Ench 1", "Dud", True, "a kind with no floor may be thinned out completely"),
            (4, {}, "Ench 1", "Dud", True, "no floors at all (build, or no tags): every swap passes"),
            (4, {ENCH: 4}, "Walker 1", "Dud", True, "the walker answer is not an answer to enchantments"),
            (4, {ENCH: 4, WALK: 1}, "Walker 1", "Dud", False, "but with a floor of 1 for planeswalkers it stays"),
        ]
        for ench, floors, cut, add, passes, why in cases:
            with self.subTest(why):
                self.assertIs(self.keeps(cut, add, ench=ench, floors=floors), passes)

    def test_worked_examples_a_card_that_answers_two_kinds(self):
        # Pulse answers enchantments and planeswalkers, so the list holds 5 answers to enchantments (4 Ench and Pulse)
        # and 2 to planeswalkers (Walker 1 and Pulse); both are at their floors
        floors = {ENCH: 5, WALK: 2}
        cases = [
            ("Pulse", "Ench New", False, "cutting Pulse for an answer to enchantments loses a planeswalker answer"),
            ("Pulse", "Walker New", False, "and for an answer to planeswalkers it loses an enchantment answer"),
            ("Pulse", "Pulse New", True, "another card that answers both keeps both"),
            ("Pulse", "Dud", False, "a card that answers nothing keeps neither"),
            ("Ench 1", "Pulse New", True, "an answer to enchantments for a card that answers both is fine"),
        ]
        for cut, add, passes, why in cases:
            with self.subTest(why):
                self.assertIs(self.keeps(cut, add, ench=4, floors=floors, extra=["Pulse"]), passes)

    def test_a_swap_is_refused_exactly_when_it_thins_out_a_kind_that_is_down_to_its_floor(self):
        # `best_swap` skips the check when no kind of threat is at its floor (`_tight_answers`); that shortcut must
        # agree with the check itself in every state: refused <=> a kind in the tight set is cut and not added back
        rng = random.Random(11)
        kinds = [ENCH, WALK, ARTI]
        cards = {f"Card {i}": frozenset(rng.sample(kinds, rng.randint(0, 3))) for i in range(12)}
        w = mini(**{name: 0.1 for name in cards})
        db = w.db()
        model = build.Model(make_ctx(w, db, names=list(cards), targets=zero_targets()), db, answers=cards)
        seen_refused = seen_tight = 0
        for _ in range(60):
            plan = build.Plan(model, db, "BG", 3, prices={}, owned=set())
            held = rng.sample(list(cards), rng.randint(2, 10))
            for name in held:
                plan.add(name)
            plan.answer_floors = {k: rng.randint(0, 4) for k in rng.sample(kinds, rng.randint(0, 3))}
            tight = plan._tight_answers()
            for cut in held:
                for add in cards:
                    if add in held:
                        continue
                    fc, fa = model.facts(cut), model.facts(add)
                    refused = not plan.keeps_answers(fc, fa)
                    self.assertEqual(refused, bool(tight & (fc.answers - fa.answers)), (held, cut, add, tight))
                    seen_refused += refused
                    seen_tight += bool(tight)
        self.assertGreater(seen_refused, 20)                  # the random states did exercise both outcomes
        self.assertGreater(seen_tight, 20)

    def test_the_shortcut_never_changes_which_swap_best_swap_picks(self):
        # best_swap asks keeps_answers only for the groups that answer a kind of threat down to its floor; asking for
        # every group that answers anything with a floor must pick exactly the same swap, in states where the floors
        # do refuse some
        rng = random.Random(23)
        kinds = [ENCH, WALK, ARTI]
        cards = {f"Card {i:02d}": frozenset(rng.sample(kinds, rng.randint(0, 2))) for i in range(16)}
        w = mini(**{name: round(0.05 * i, 2) for i, name in enumerate(cards)})
        db = w.db()
        model = build.Model(make_ctx(w, db, names=list(cards), targets=zero_targets()), db, answers=cards)
        refusals = 0
        for _ in range(80):
            plan = build.Plan(model, db, "BG", 3, prices={}, owned=set())
            held = rng.sample(list(cards), rng.randint(4, 11))
            for name in held:
                plan.add(name)
            plan.answer_floors = {k: rng.randint(0, 4) for k in rng.sample(kinds, rng.randint(1, 3))}
            adds = [n for n in cards if n not in held]
            quick = plan.best_swap(held, adds, min_gain=-math.inf)
            with mock.patch.object(build.Plan, "_tight_answers", lambda self: set(self.answer_floors)):
                full = plan.best_swap(held, adds, min_gain=-math.inf)
            self.assertEqual(quick, full, (held, plan.answer_floors))
            plan.answer_floors = {}
            refusals += plan.best_swap(held, adds, min_gain=-math.inf) != quick     # with no floors it would differ
        self.assertGreater(refusals, 10)

    def test_a_kind_with_no_answers_or_a_floor_of_zero_is_never_tight(self):
        w = mini(Pulse=0.1)
        db = w.db()
        model = build.Model(make_ctx(w, db, targets=zero_targets()), db, answers={"Pulse": frozenset({ENCH})})
        plan = build.Plan(model, db, "BG", 3, prices={}, owned=set())
        plan.answer_floors = {ENCH: 2, WALK: 0, ARTI: 3}
        self.assertEqual(plan._tight_answers(), set())              # nothing answers anything yet: nothing to thin out
        plan.add("Pulse")
        self.assertEqual(plan._tight_answers(), {ENCH})             # 1 answer against a floor of 2
        plan.answer_floors = {ENCH: 0}
        self.assertEqual(plan._tight_answers(), set())              # a floor of 0 asks for nothing

    def test_each_kind_is_judged_on_its_own_even_when_the_other_is_far_above_its_floor(self):
        # 9 answers to enchantments (floor 4) do not pay for the last planeswalker answer (floor 1)
        self.assertFalse(self.keeps("Walker 1", "Ench New", ench=9, floors={ENCH: 4, WALK: 1}))


class AnswerTrackingTests(Isolated):
    """Facts carry the threats a card answers, the Plan keeps a count for each, and cuts that cover different
    threats are never one group."""

    TAGS = {"Pulse": ["removal-artifact", "removal-enchantment", "removal-planeswalker", "spot-removal"],
            "Disenchant": ["removal-enchantment"], "Smash": ["removal-artifact"], "Wrath": ["sweeper"],
            "Slay": ["removal-creature", "sweeper"], "Hush": ["counterspell"], "Rock": ["mana-rock"], "Bear": []}

    def setUp(self):
        super().setUp()
        self.world = mini(**{name: 0.1 * i for i, name in enumerate(self.TAGS)})
        self.db = self.world.db()
        self.answers = {name: roles.threats_answered(slugs) for name, slugs in self.TAGS.items()}
        self.ctx = make_ctx(self.world, self.db, names=list(self.TAGS), targets=zero_targets())
        self.model = build.Model(self.ctx, self.db, answers=self.answers)

    def plan(self):
        return build.Plan(self.model, self.db, "BG", 3, prices={}, owned=set())

    def test_the_facts_of_a_card_say_which_threats_it_answers(self):
        self.assertEqual(self.model.facts("Pulse").answers, frozenset({ARTI, ENCH, WALK}))
        self.assertEqual(self.model.facts("Slay").answers, frozenset({CREA}))           # two tags, one kind
        self.assertEqual(self.model.facts("Rock").answers, frozenset())
        self.assertEqual(self.model.facts("Not A Card").answers, frozenset())           # a name the index lacks
        self.assertIsInstance(self.model.facts("Hush").answers, frozenset)

    def test_a_model_given_no_answers_has_cards_that_answer_nothing(self):
        bare = build.Model(self.ctx, self.db)
        self.assertEqual({bare.facts(n).answers for n in self.TAGS}, {frozenset()})

    def test_a_plan_counts_a_card_once_for_each_threat_it_answers(self):
        plan = self.plan()
        for name in ("Pulse", "Disenchant", "Wrath", "Bear"):
            plan.add(name)
        self.assertEqual(dict(+plan.answers), {ARTI: 1, ENCH: 2, WALK: 1, CREA: 1})
        plan.remove("Pulse")
        self.assertEqual(dict(+plan.answers), {ENCH: 1, CREA: 1})
        plan.swap("Disenchant", "Smash")
        self.assertEqual(dict(+plan.answers), {ARTI: 1, CREA: 1})

    def test_a_second_copy_of_a_card_does_not_count_twice_as_metrics_counts_distinct_cards(self):
        plan = self.plan()
        plan.add("Disenchant")
        plan.add("Disenchant")
        self.assertEqual(plan.answers[ENCH], 1)
        plan.remove("Disenchant")
        self.assertEqual(plan.answers[ENCH], 1)                     # one copy is still in the list
        plan.remove("Disenchant")
        self.assertEqual(plan.answers[ENCH], 0)

    def test_a_clone_has_its_own_counts_and_floors(self):
        plan = self.plan()
        plan.add("Pulse")
        plan.answer_floors = {ENCH: 1}
        other = plan.clone()
        other.add("Disenchant")
        other.answer_floors[WALK] = 5
        self.assertEqual((plan.answers[ENCH], other.answers[ENCH]), (1, 2))
        self.assertEqual((plan.answer_floors, other.answer_floors), ({ENCH: 1}, {ENCH: 1, WALK: 5}))

    def test_the_counts_always_equal_the_distinct_cards_that_answer_each_threat(self):
        # the number the Metrics tab and calibrate.py count with: roles.answer_counts over the list
        rng = random.Random(7)
        plan, names = self.plan(), list(self.TAGS)
        for step in range(400):
            held = list(plan.cards)
            if held and rng.random() < 0.4:
                plan.remove(rng.choice(held))
            else:
                plan.add(rng.choice(names))
            if step % 50 == 0:
                plan = plan.clone()
            counted = roles.answer_counts(plan.names(), {n: frozenset(self.TAGS[n]) for n in names})
            self.assertEqual({t: plan.answers[t] for t in roles.THREAT_IDS}, counted, step)

    def test_cuts_that_cover_different_threats_are_never_in_one_group(self):
        # three cards alike in every other way: Disenchant and Disenchant Too answer enchantments, Smash artifacts
        w = mini(**{"Disenchant": 0.1, "Disenchant Too": 0.2, "Smash": 0.3, "Bear": 0.4})
        db = w.db()
        answers = {"Disenchant": frozenset({ENCH}), "Disenchant Too": frozenset({ENCH}), "Smash": frozenset({ARTI})}
        plan = build.Plan(build.Model(make_ctx(w, db, targets=zero_targets()), db, answers=answers), db, "BG", 3,
                          prices={}, owned=set())
        groups = plan._groups(["Disenchant", "Disenchant Too", "Smash", "Bear"])
        shape = sorted(sorted(f.name for f, _, _ in group) for group in groups)
        self.assertEqual(shape, [["Bear"], ["Disenchant", "Disenchant Too"], ["Smash"]])

    def test_a_card_that_answers_two_kinds_is_not_grouped_with_one_that_answers_one(self):
        w = mini(**{"Pulse": 0.1, "Disenchant": 0.2})
        db = w.db()
        answers = {"Pulse": frozenset({ARTI, ENCH, WALK}), "Disenchant": frozenset({ENCH})}
        plan = build.Plan(build.Model(make_ctx(w, db, targets=zero_targets()), db, answers=answers), db, "BG", 3,
                          prices={}, owned=set())
        self.assertEqual(len(plan._groups(["Pulse", "Disenchant"])), 2)

    def test_without_answers_the_groups_are_what_they_were_before(self):
        w = mini(**{"A": 0.1, "B": 0.2, "C": 0.3})
        db = w.db()
        plan = build.Plan(build.Model(make_ctx(w, db, targets=zero_targets()), db), db, "BG", 3, prices={},
                          owned=set())
        self.assertEqual([[f.name for f, _, _ in group] for group in plan._groups(["A", "B", "C"])], [["A", "B", "C"]])


class UpgradeAnswersTests(Isolated):
    """`upgrade` keeps a deck's answers: the weakest cards go first, and answers to a kind of threat stay down to what a
    typical deck at the bracket holds (the band's target; the band's min, which the Metrics tab calls short, is a lower
    bar that the upgrade does not use). A deck of N answers to enchantments that score 0.00 (its weakest cards), five
    plain cards at 0.10 and staples at 0.94 and below that would replace every card: only the floor stops them. Bands
    are (min, target, max); these tests give them a min well under the target, so a floor taken from the wrong one
    shows."""

    def world(self, have, **cards):
        names = {f"Ench {i}": 0.0 for i in range(1, have + 1)}
        names.update({f"Plain {i}": 0.10 for i in range(1, 6)})
        w = mini(**names)
        for i in range(1, have + 7):
            w.add(f"Staple {i}", round(0.95 - 0.01 * i, 2), None, price=1.0)
        for name, value in cards.items():
            w.add(name, value, None, price=1.0)
        return w

    def deck(self, have, *more):
        return [f"Ench {i}" for i in range(1, have + 1)] + [f"Plain {i}" for i in range(1, 6)] + list(more)

    def candidates(self, have, *more):
        return [f"Staple {i}" for i in range(1, have + 7)] + list(more)

    def tags(self, have, **extra):
        tags = {f"Ench {i}": ENCH_TAG for i in range(1, have + 1)}
        tags.update(extra)
        self.set_tags(tags)

    def upgrade(self, w, deck, candidates, *, ci="BG", **kw):
        db = w.db()
        ctx = make_ctx(w, db, names=deck + candidates, targets=zero_targets(), ci=ci)
        kw.setdefault("prices", w.prices())
        return build.upgrade(ctx, deck_of(*deck), db, **kw), ctx, db

    def kept(self, res, prefix):
        return sorted(n for _, n in res["deck_after"]["cards"] if n.startswith(prefix))

    # --- the guard in a whole upgrade
    def test_a_deck_with_7_answers_and_a_typical_count_of_4_trades_down_to_4_but_not_to_3(self):
        self.tags(7)
        self.set_bands(enchantments=(2, 4, 9))                     # a typical deck holds 4; only a quarter hold fewer than 2
        res, _, _ = self.upgrade(self.world(7), self.deck(7), self.candidates(7))
        self.assertEqual((res["answers_before"][ENCH], res["answers_after"][ENCH]), (7, 4))
        self.assertEqual(len(self.kept(res, "Ench")), 4)
        self.assertEqual(len(res["swaps"]), 3 + 5)                  # three of the answers go, and all five plain cards
        self.assertEqual({s["cut"][:5] for s in res["swaps"]}, {"Ench ", "Plain"})
        self.set_bands()                                           # no floor: the same deck loses every one of them
        free, _, _ = self.upgrade(self.world(7), self.deck(7), self.candidates(7))
        self.assertEqual((free["answers_after"][ENCH], len(free["swaps"])), (0, 7 + 5))

    def test_a_deck_at_the_typical_count_keeps_every_answer_and_gives_up_the_other_cards(self):
        self.tags(4)
        self.set_bands(enchantments=(2, 4, 9))
        res, _, _ = self.upgrade(self.world(4), self.deck(4), self.candidates(4))
        self.assertEqual(self.kept(res, "Ench"), [f"Ench {i}" for i in range(1, 5)])
        self.assertEqual({s["cut"][:5] for s in res["swaps"]}, {"Plain"})
        self.assertEqual((res["answers_before"][ENCH], res["answers_after"][ENCH]), (4, 4))

    def test_a_deck_that_starts_below_the_typical_count_keeps_the_answers_it_has(self):
        # it holds 2 where a typical deck holds 4, but more than the 1 a quarter of decks get by on (the min): the
        # upgrade must not use the min, which would let it trade one of the two away
        self.tags(2)
        self.set_bands(enchantments=(1, 4, 9))
        res, _, _ = self.upgrade(self.world(2), self.deck(2), self.candidates(2))
        self.assertEqual(self.kept(res, "Ench"), ["Ench 1", "Ench 2"])
        self.assertEqual((res["answers_before"][ENCH], res["answers_after"][ENCH]), (2, 2))

    def test_an_answer_to_the_same_kind_may_take_the_place_of_one_even_at_the_floor(self):
        self.tags(4, **{"Better Ench": ENCH_TAG})
        self.set_bands(enchantments=(2, 4, 9))
        w = self.world(4, **{"Better Ench": 0.99})
        res, _, _ = self.upgrade(w, self.deck(4), self.candidates(4, "Better Ench"))
        first = res["swaps"][0]
        self.assertEqual((first["cut"][:5], first["add"]), ("Ench ", "Better Ench"))     # the best gain of all
        self.assertEqual(res["answers_after"][ENCH], 4)
        self.assertIn("Better Ench", self.kept(res, "Better"))

    def test_an_answer_to_another_kind_does_not_buy_the_right_to_cut_an_answer(self):
        self.tags(4, **{"Walker Answer": WALK_TAG})
        self.set_bands(enchantments=(2, 4, 9))
        w = self.world(4, **{"Walker Answer": 0.99})
        res, _, _ = self.upgrade(w, self.deck(4), self.candidates(4, "Walker Answer"))
        first = res["swaps"][0]
        self.assertEqual(first["add"], "Walker Answer")
        self.assertTrue(first["cut"].startswith("Plain"), first)      # not an Ench, whatever its score: at the floor
        self.assertEqual((res["answers_after"][ENCH], res["answers_after"][WALK]), (4, 1))

    def test_floors_apply_to_the_optional_swaps_only_a_forced_swap_still_cuts_a_banned_answer(self):
        # Banned Ench is the third answer to enchantments and a typical deck holds 4, but the card is not legal in
        # Commander: it goes first. Afterwards the floor is what the list has left (2)
        self.tags(2, **{"Banned Ench": ENCH_TAG})
        self.set_bands(enchantments=(2, 4, 9))
        w = self.world(2)
        w.add("Banned Ench", 0.5, None, price=1.0, legal="banned")
        res, _, _ = self.upgrade(w, self.deck(2, "Banned Ench"), self.candidates(2))
        first = res["swaps"][0]
        self.assertEqual((first["forced"], first["cut"]), (True, "Banned Ench"))
        self.assertTrue(first["add"].startswith("Staple"))              # the replacement is not held to the floor
        self.assertEqual(self.kept(res, "Ench"), ["Ench 1", "Ench 2"])  # then the floor holds what is left
        self.assertEqual((res["answers_before"][ENCH], res["answers_after"][ENCH]), (3, 2))
        self.assertTrue(all(not s["forced"] for s in res["swaps"][1:]))

    def test_a_forced_swap_may_cut_the_last_answer_of_a_kind_and_the_floor_is_then_zero(self):
        self.tags(0, **{"Banned Ench": ENCH_TAG})
        self.set_bands(enchantments=(2, 4, 9))
        w = self.world(0)
        w.add("Banned Ench", 0.5, None, price=1.0, legal="banned")
        res, _, _ = self.upgrade(w, self.deck(0, "Banned Ench"), self.candidates(0))
        self.assertEqual((res["answers_before"][ENCH], res["answers_after"][ENCH]), (1, 0))

    def test_the_floors_come_from_the_bracket_file_and_a_deck_without_blue_has_no_spell_floor(self):
        # the real reader, on a file: at Bracket 3 a quarter of decks hold 3 answers to spells or fewer and a typical
        # deck holds 4. A black-green deck is not asked for counterspells; the same deck with blue keeps 4, the
        # typical count, and not 3, the min
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "metric_targets.json")
        with open(path, "w") as f:
            json.dump({"brackets": {"3": {"answers_spells": [3, 4, 6]}}}, f)
        mock.patch.object(roles, "METRIC_TARGETS_PATH", path).start()
        w = self.world(0)
        for i in range(1, 6):
            w.add(f"Counter {i}", 0.0, None, price=1.0)
        deck = self.deck(0) + [f"Counter {i}" for i in range(1, 6)]
        self.set_tags({name: SPELL_TAG for name in deck if name.startswith("Counter")})
        without_blue, _, _ = self.upgrade(w, deck, self.candidates(0), ci="BG")
        self.assertEqual((without_blue["answers_before"][SPEL], without_blue["answers_after"][SPEL]), (5, 0))
        with_blue, _, _ = self.upgrade(w, deck, self.candidates(0), ci="BGU")
        self.assertEqual((with_blue["answers_before"][SPEL], with_blue["answers_after"][SPEL]), (5, 4))

    def test_no_tags_means_no_floor_and_a_warning_that_answers_were_not_checked(self):
        self.set_tags({f"Ench {i}": ENCH_TAG for i in range(1, 8)}, loaded=False)
        bands = self.set_bands(enchantments=(2, 4, 9))
        res, _, _ = self.upgrade(self.world(7), self.deck(7), self.candidates(7), budget=20.0, price_points=[10])
        self.assertEqual(self.kept(res, "Ench"), [])                  # nothing held anything back
        self.assertEqual(len(res["swaps"]), 7 + 5)
        notes = [w for w in res["warnings"] if "were not checked" in w]
        self.assertEqual(len(notes), 1)
        for noun in ("creatures", "artifacts", "enchantments", "planeswalkers", "lands", "graveyards", "spells"):
            self.assertIn(noun, notes[0])
        self.assertIn("function tags", notes[0])
        bands.assert_not_called()                                      # no floors were even looked up
        self.assertEqual((res["answers_before"], res["answers_after"]), (None, None))
        for line in res["price_points"]:
            self.assertEqual((line["answers"], line["weakens"]), (None, []))
            self.assertIsInstance(line["change"], float)

    def test_with_tags_there_is_no_such_warning(self):
        self.tags(4)
        self.set_bands(enchantments=(2, 4, 9))
        res, _, _ = self.upgrade(self.world(4), self.deck(4), self.candidates(4))
        self.assertEqual([w for w in res["warnings"] if "were not checked" in w], [])

    def test_a_bracket_without_a_band_for_a_kind_leaves_that_kind_free(self):
        self.tags(7)
        self.set_bands(planeswalkers=(2, 3, 8))                      # no row for enchantments
        res, _, _ = self.upgrade(self.world(7), self.deck(7), self.candidates(7))
        self.assertEqual(res["answers_after"][ENCH], 0)

    def test_the_tags_are_asked_for_once_for_the_deck_and_every_candidate(self):
        self.tags(4)
        self.set_bands(enchantments=(2, 4, 9))
        w = self.world(4)
        self.upgrade(w, self.deck(4), self.candidates(4))
        self.assertEqual(len(self.tag_calls), 1)
        asked = set(self.tag_calls[0])
        self.assertTrue(set(self.deck(4)) | set(self.candidates(4)) <= asked)

    def test_the_result_counts_are_the_counts_of_the_lists_the_swaps_made(self):
        self.tags(7, **{"Better Ench": ENCH_TAG, "Walker Answer": WALK_TAG})
        self.set_bands(enchantments=(2, 4, 9))
        w = self.world(7, **{"Better Ench": 0.99, "Walker Answer": 0.97})
        res, _, _ = self.upgrade(w, self.deck(7), self.candidates(7, "Better Ench", "Walker Answer"))
        tags = {f"Ench {i}": frozenset(ENCH_TAG) for i in range(1, 8)}
        tags.update({"Better Ench": frozenset(ENCH_TAG), "Walker Answer": frozenset(WALK_TAG)})
        after = [n for _, n in res["deck_after"]["cards"]]
        self.assertEqual(res["answers_after"], roles.answer_counts(after, tags))
        self.assertEqual(res["answers_before"], roles.answer_counts(self.deck(7), tags))
        self.assertEqual(list(res["answers_after"]), list(roles.THREAT_IDS))

    def test_the_combo_repair_may_take_a_kind_under_its_floor_because_a_bracket_rule_outranks_it(self):
        # W and X form a two-card combo Bracket 3 forbids. The search adds W (replacing Plain 1), then X, an answer to
        # enchantments (replacing Plain 2, so the list holds 5), then Staple 1 in place of Ench 1 (allowed: 5 answers
        # against a floor of 4, and it leaves 4). The repair then undoes X, the later piece, and with it one answer:
        # the list ends with 3, under the floor, because the combo rule comes first
        self.set_bands(enchantments=(2, 4, 9))
        enchants = ["Ench 1", "Ench 2", "Ench 3", "Ench 4"]
        w = mini(**{n: 0.05 for n in enchants}, **{"Plain 1": 0.0, "Plain 2": 0.0})
        for name, value in (("W", 0.99), ("X", 0.95), ("Staple 1", 0.5)):
            w.add(name, value, None, price=1.0)
        deck = enchants + ["Plain 1", "Plain 2"]
        self.set_tags({**{n: ENCH_TAG for n in enchants}, "X": ENCH_TAG})

        def combos(commanders, names):
            both = {"W", "X"} <= set(names)
            return {"included": [{"id": "1-2", "cards": ["W", "X"], "missing": [], "produces": ["win"],
                                  "min_bracket": 4, "two_card": True, "url": ""}] if both else [], "almost": []}
        res, _, _ = self.upgrade(w, deck, ["W", "X", "Staple 1"], combos_fn=combos)
        undone = [x for x in res["warnings"] if x.startswith("Undid ")]
        self.assertEqual(len(undone), 1, res["warnings"])
        self.assertIn("X", undone[0])
        self.assertEqual([(x["cut"], x["add"]) for x in res["swaps"]], [("Plain 1", "W"), ("Ench 1", "Staple 1")])
        self.assertEqual((res["answers_before"][ENCH], res["answers_after"][ENCH]), (4, 3))

    def test_a_combo_repair_that_does_not_touch_an_answer_leaves_the_floor_met(self):
        # the same two cards, neither an answer: the repair undoes a swap that never changed the count
        self.tags(4)
        self.set_bands(enchantments=(2, 4, 9))
        w = self.world(4)
        combos = lambda commanders, names: {"included": [{"id": "1-2", "cards": ["Staple 1", "Staple 2"], "missing": [],
                                                          "produces": ["win"], "min_bracket": 4, "two_card": True,
                                                          "url": ""}] if {"Staple 1", "Staple 2"} <= set(names) else [],
                                            "almost": []}
        res, _, _ = self.upgrade(w, self.deck(4), self.candidates(4), combos_fn=combos)
        self.assertTrue(any(x.startswith("Undid ") for x in res["warnings"]), res["warnings"])
        self.assertEqual(res["answers_after"][ENCH], 4)


class BuildKeepsNoAnswerFloorTests(Isolated):
    """`build` makes a deck from nothing: it has no starting answers to keep, so it behaves as it did before."""

    def test_build_ignores_tags_and_bands_entirely(self):
        w = standard_world()
        db = w.db()
        ctx = make_ctx(w, db)
        plain = build.build(ctx, db, prices=w.prices())
        self.assertEqual(self.tag_calls, [])
        # the same build when every Kill card answers enchantments and the bracket demands 12 of them
        self.set_tags({f"Kill {i:02d}": ENCH_TAG for i in range(1, 13)})
        bands = self.set_bands(enchantments=(12, 12, 12))
        tagged = build.build(ctx, db, prices=w.prices())
        self.assertEqual(self.tag_calls, [])                           # build never asked for the tags
        bands.assert_not_called()
        self.assertEqual((tagged["cards"], tagged["basics"], tagged["value"]),
                         (plain["cards"], plain["basics"], plain["value"]))
        self.assertNotIn("answers_before", tagged)
        self.assertNotIn("answers_after", tagged)

    def test_a_plan_made_for_a_build_has_no_floors(self):
        w = mini(A=0.1)
        db = w.db()
        plan = build.Plan(build.Model(make_ctx(w, db, targets=zero_targets()), db), db, "BG", 3, prices={},
                          owned=set())
        self.assertEqual(plan.answer_floors, {})
        self.assertTrue(plan.keeps_answers(plan.m.facts("A"), plan.m.facts("A")))


class PricePointAnswerTests(Isolated):
    """Each price point reports the answers its list holds, the kinds it has brought down from the starting count to
    what a typical deck holds or under it (`weakens`: it used up all of that kind's surplus), and how far its value
    moved from the start. Seven answers to enchantments (0.00) and five plain cards (0.10) are replaced by buys of $5
    each, two at a time as the price points $10, $20 and $30 allow. Optional swaps never take a kind under what a
    typical deck holds, so with a typical count of 4 the answers go 7, 5, 4, 4: the third swap of the second point
    reaches the floor and the cuts after it are plain cards."""
    BUYS = [f"Buy {i}" for i in range(1, 13)]

    def setUp(self):
        super().setUp()
        names = {f"Ench {i}": 0.0 for i in range(1, 8)}
        names.update({f"Plain {i}": 0.10 for i in range(1, 6)})
        self.world = mini(**names)
        for i, name in enumerate(self.BUYS):
            self.world.add(name, round(0.9 - 0.01 * i, 2), None, price=5.0)
        self.deck = [f"Ench {i}" for i in range(1, 8)] + [f"Plain {i}" for i in range(1, 6)]
        self.set_tags({f"Ench {i}": ENCH_TAG for i in range(1, 8)})

    def upgrade(self, **kw):
        return run_upgrade(self.world, self.deck, self.BUYS, budget=30.0, price_points=[10, 20], **kw)

    def test_the_answers_at_each_point_are_counted_on_the_list_at_that_point(self):
        self.set_bands(enchantments=(2, 4, 9))
        res, _, _ = self.upgrade()
        self.assertEqual([p["swaps"] for p in res["price_points"]], [2, 4, 6])
        self.assertEqual([p["answers"][ENCH] for p in res["price_points"]], [5, 4, 4])     # 7 less 2, 3 and 3: the floor
        for line in res["price_points"]:
            self.assertEqual(list(line["answers"]), list(roles.THREAT_IDS))
            self.assertEqual(line["answers"][WALK], 0)
        self.assertEqual(res["price_points"][-1]["answers"], res["answers_after"])

    def test_a_count_still_above_the_typical_count_is_not_listed(self):
        self.set_bands(enchantments=(2, 4, 9))
        res, _, _ = self.upgrade()
        first = res["price_points"][0]
        self.assertEqual(first["answers"][ENCH], 5)                    # 7 -> 5: fewer, but a deck usually holds 4
        self.assertEqual(first["weakens"], [])

    def test_a_count_brought_exactly_down_to_the_typical_count_is_listed(self):
        self.set_bands(enchantments=(2, 4, 9))
        res, _, _ = self.upgrade()
        second, third = res["price_points"][1:]
        entry = {"id": ENCH, "label": "enchantments", "before": 7, "after": 4, "target": 4}
        self.assertEqual(second["weakens"], [entry])                   # 7 -> 4, where a deck usually holds 4
        self.assertEqual(third["weakens"], [entry])                    # the floor held it there
        self.assertEqual(res["answers_before"][ENCH], 7)

    def test_the_first_point_that_lands_on_the_typical_count_is_the_first_to_list_it(self):
        self.set_bands(enchantments=(2, 5, 9))                         # typical 5: two swaps bring 7 down to exactly 5
        res, _, _ = self.upgrade()
        first, second = res["price_points"][:2]
        self.assertEqual(first["answers"][ENCH], 5)
        self.assertEqual(first["weakens"], [{"id": ENCH, "label": "enchantments", "before": 7, "after": 5, "target": 5}])
        self.assertEqual(second["answers"][ENCH], 5)                   # and the floor keeps it there

    def test_a_count_a_forced_swap_took_under_the_typical_count_is_listed_from_the_first_point(self):
        # three legal answers and a banned one make 4, a typical deck's count; the banned card must go whatever it
        # answers, which leaves 3, under the typical count, and the floor then keeps the 3
        self.world.add("Banned Ench", 0.5, None, price=1.0, legal="banned")
        self.set_tags({**{f"Ench {i}": ENCH_TAG for i in range(1, 4)}, "Banned Ench": ENCH_TAG})
        self.set_bands(enchantments=(2, 4, 9))
        deck = ["Ench 1", "Ench 2", "Ench 3", "Banned Ench"] + [f"Plain {i}" for i in range(1, 6)]
        res, _, _ = run_upgrade(self.world, deck, self.BUYS, budget=30.0, price_points=[10, 20])
        self.assertTrue(res["swaps"][0]["forced"])
        entry = {"id": ENCH, "label": "enchantments", "before": 4, "after": 3, "target": 4}
        for line in res["price_points"]:
            self.assertEqual((line["answers"][ENCH], line["weakens"]), (3, [entry]))

    def test_a_kind_that_did_not_fall_is_no_weakness_even_when_it_was_under_the_typical_count_all_along(self):
        # Walker 1 is the deck's only answer to planeswalkers (typical 3): the floor is what the list has, so the
        # upgrade leaves it be, and a kind that did not fall is not listed
        self.world.add("Walker 1", 0.0, None, price=1.0)
        self.set_tags({**{f"Ench {i}": ENCH_TAG for i in range(1, 8)}, "Walker 1": WALK_TAG})
        self.set_bands(enchantments=(2, 4, 9), planeswalkers=(1, 3, 8))
        res, _, _ = run_upgrade(self.world, self.deck + ["Walker 1"], self.BUYS, budget=30.0, price_points=[10, 20])
        for line in res["price_points"]:
            self.assertEqual(line["answers"][WALK], 1)
            self.assertNotIn(WALK, [w["id"] for w in line["weakens"]])

    def test_a_kind_the_bracket_has_no_band_for_is_never_listed(self):
        self.set_bands(planeswalkers=(1, 3, 8))                        # nothing for enchantments
        res, _, _ = self.upgrade()
        self.assertEqual(res["price_points"][-1]["answers"][ENCH], 1)    # six buys cut six of the seven, with no floor
        self.assertTrue(all(line["weakens"] == [] for line in res["price_points"]))

    def test_several_weakened_kinds_are_listed_in_the_order_stats_lists_them(self):
        # three answers to artifacts that score below everything else go first, down to a typical 1; the enchantments
        # follow, down to a typical 4
        for i in range(1, 4):
            self.world.add(f"Smash {i}", -0.001, None, price=1.0)
        self.set_tags({**{f"Ench {i}": ENCH_TAG for i in range(1, 8)},
                       **{f"Smash {i}": ["removal-artifact"] for i in range(1, 4)}})
        self.set_bands(enchantments=(2, 4, 9), artifacts=(0, 1, 6))
        deck = self.deck + [f"Smash {i}" for i in range(1, 4)]
        res, _, _ = run_upgrade(self.world, deck, self.BUYS, budget=30.0, price_points=[10, 20])
        last = res["price_points"][-1]
        self.assertEqual([w["id"] for w in last["weakens"]], [ARTI, ENCH])       # artifacts come before enchantments
        self.assertEqual(last["weakens"][0], {"id": ARTI, "label": "artifacts", "before": 3, "after": 1, "target": 1})
        self.assertEqual(last["weakens"][1], {"id": ENCH, "label": "enchantments", "before": 7, "after": 4, "target": 4})

    def test_a_deck_without_blue_that_loses_its_counterspells_is_listed_against_a_typical_count_of_0(self):
        # the real reader on a file: a deck without blue is not expected to hold any, so its typical count is 0 and
        # its floor is 0; a counterspell it does hold goes like any other weak card, and the note says what it did
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "metric_targets.json")
        with open(path, "w") as f:
            json.dump({"brackets": {"3": {"answers_spells": [3, 4, 6]}}}, f)
        mock.patch.object(roles, "METRIC_TARGETS_PATH", path).start()
        for i in range(1, 3):
            self.world.add(f"Counter {i}", -0.001, None, price=1.0)
        self.set_tags({f"Counter {i}": SPELL_TAG for i in range(1, 3)})
        res, _, _ = run_upgrade(self.world, self.deck + ["Counter 1", "Counter 2"], self.BUYS, budget=30.0,
                                price_points=[10, 20])
        first = res["price_points"][0]
        self.assertEqual(first["weakens"], [{"id": SPEL, "label": "spells", "before": 2, "after": 0, "target": 0}])

    def test_change_is_the_points_value_less_the_starting_value_to_two_decimals(self):
        self.set_bands(enchantments=(2, 4, 9))
        res, _, _ = self.upgrade()
        for line in res["price_points"]:
            self.assertEqual(line["change"], round(line["value"] - res["value_before"], 2))
        changes = [line["change"] for line in res["price_points"]]
        self.assertEqual(changes, sorted(changes))
        self.assertGreater(changes[0], 0)

    def test_without_a_budget_there_are_no_points_but_the_result_still_reports_its_answers(self):
        self.set_bands(enchantments=(2, 4, 9))
        res, _, _ = run_upgrade(self.world, self.deck, self.BUYS)
        self.assertEqual(res["price_points"], [])
        self.assertEqual((res["answers_before"][ENCH], res["answers_after"][ENCH]), (7, 4))


# ----------------------------------------------------------------------------- basic lands
class BasicLandRuleTests(Isolated):
    """The rules that keep a long upgrade from ruining the mana: basics are kept for the cards that search for
    them, a nonbasic land must earn a basic's slot, and the right basic is the one that goes."""
    CULTIVATE = UpgradeTests.CULTIVATE
    EVOLVING_WILDS = UpgradeTests.EVOLVING_WILDS

    def world(self):
        w = World()
        w.add("Cultivate", 0.50, None, types="Sorcery", cmc=3, cost="{2}{G}", text=self.CULTIVATE)   # takes 2
        w.add("Evolving Wilds", 0.50, None, types="Land", text=self.EVOLVING_WILDS)                    # takes 1
        w.add("Weak Spell", 0.05, None, types="Creature", cmc=2, cost="{1}{B}")      # a creature almost nobody plays
        w.add("Green Beast", 0.50, None, types="Creature", cmc=3, cost="{1}{G}{G}")  # two green symbols
        w.add("Black Imp", 0.50, None, types="Creature", cmc=2, cost="{1}{B}")       # one black symbol
        w.add("Dual Land", 0.60, None, types="Land", produced=["B", "G"], ci="BG")   # a dual builders play
        w.add("Barely Scored Land", 0.05, None, types="Land", produced=["B", "G"], ci="BG")   # under NONBASIC_MIN
        w.add("Utility Land", 0.00, None, types="Land", produced=["C"])              # a colorless land nobody plays
        return w

    def plan(self, w, cards, ci="BG"):
        db = w.db()
        plan = build.Plan(build.Model(make_ctx(w, db), db), db, ci, 3, prices={}, owned=set())
        for name in cards:
            plan.add(name)
        return plan

    def ok(self, plan, cut, add):
        f = plan.m.facts
        return plan.basics_ok(f(cut), f(add))

    # --- what a card needs
    def test_the_facts_carry_how_many_basic_lands_a_card_searches_for(self):
        w = self.world()
        model = build.Model(make_ctx(w, w.db()), w.db())
        self.assertEqual([model.facts(n).fetch for n in ("Cultivate", "Evolving Wilds", "Dual Land", "Forest")],
                         [2, 1, 0, 0])
        self.assertEqual(model.facts("Not A Card").fetch, 0)

    def test_the_plan_totals_the_basics_the_searches_and_the_symbols_of_its_cards(self):
        w = self.world()
        plan = self.plan(w, ["Cultivate", "Evolving Wilds", "Forest", "Forest", "Swamp", "Green Beast", "Black Imp"])
        self.assertEqual((plan.basics, plan.basic_demand), (3, 3))
        # Cultivate {G}, Green Beast {G}{G} and Black Imp {B}
        self.assertEqual((plan.pips["G"], plan.pips["B"]), (3, 1))
        self.assertEqual(plan.sources["G"], 2)

    def test_the_totals_follow_every_add_remove_swap_and_clone(self):
        w = self.world()
        db = w.db()

        def from_scratch(plan):
            basics = sum("Basic" in db.get(n)["types"] for n in plan.names())
            demand = sum(roles.basic_land_searches(db.get(n)) for n in plan.names())
            pips = collections.Counter()
            for n in plan.names():
                if not db.get(n)["land"]:
                    for color, v in build._pips(db.get(n), "BG").items():
                        pips[color] += v
            return basics, demand, +pips          # unary plus drops colors whose count fell to zero

        def kept(plan):
            return plan.basics, plan.basic_demand, +plan.pips

        plan = self.plan(w, ["Cultivate", "Evolving Wilds", "Forest", "Forest", "Swamp", "Green Beast", "Black Imp"])
        self.assertEqual(kept(plan), from_scratch(plan))
        plan.remove("Forest")
        plan.swap("Cultivate", "Dual Land")
        self.assertEqual(kept(plan), from_scratch(plan))
        other = plan.clone()
        other.add("Swamp")
        other.swap("Black Imp", "Evolving Wilds")
        other.remove("Green Beast")
        self.assertEqual(kept(other), from_scratch(other))
        self.assertEqual(kept(plan), from_scratch(plan))              # the original did not move
        self.assertIsNot(other.pips, plan.pips)

    def test_a_filler_basic_goes_to_the_color_with_the_fewest_lands_per_colored_symbol(self):
        w = self.world()
        green_heavy = self.plan(w, ["Green Beast"] + ["Forest"] * 3 + ["Swamp"] * 3)
        self.assertEqual(green_heavy.filler(), "Forest")               # 3 lands for 2 green symbols, 3 for 0 black
        black_heavy = self.plan(w, ["Black Imp"] + ["Forest"] * 3 + ["Swamp"] * 3)
        self.assertEqual(black_heavy.filler(), "Swamp")
        even = self.plan(w, ["Forest", "Swamp"])
        self.assertEqual(even.filler(), "Swamp")                       # a tie goes to the first color letter: B
        self.assertEqual(self.plan(w, [], ci="").filler(), "Wastes")

    # --- the floor
    def test_a_basic_may_go_while_the_searchers_still_have_targets(self):
        w = self.world()
        # Cultivate (2) and Evolving Wilds (1) can take 3 basics
        four = self.plan(w, ["Cultivate", "Evolving Wilds"] + ["Forest"] * 2 + ["Swamp"] * 2)
        self.assertEqual(four.basic_demand, 3)
        self.assertTrue(self.ok(four, "Swamp", "Dual Land"))           # 3 basics left for 3 to take
        # ...but not a Forest: the 3 kept basics split one per color and the rest by colored symbols, and the
        # deck's only symbol is Cultivate's {G}, so green keeps 2 of them
        self.assertFalse(self.ok(four, "Forest", "Dual Land"))
        three = self.plan(w, ["Cultivate", "Evolving Wilds"] + ["Forest"] * 2 + ["Swamp"])
        self.assertFalse(self.ok(three, "Forest", "Dual Land"))        # 2 left would leave one search with no target

    def test_a_deck_keeps_at_least_as_many_basics_as_it_has_colors_even_with_no_searchers(self):
        w = self.world()
        self.assertFalse(self.ok(self.plan(w, ["Forest", "Swamp"]), "Forest", "Dual Land"))
        self.assertTrue(self.ok(self.plan(w, ["Forest", "Swamp", "Swamp"]), "Swamp", "Dual Land"))
        self.assertFalse(self.ok(self.plan(w, ["Forest", "Swamp", "Swamp"]), "Forest", "Dual Land"))  # the last one
        mono = self.plan(w, ["Forest"], ci="G")
        self.assertFalse(self.ok(mono, "Forest", "Dual Land"))
        self.assertTrue(self.ok(self.plan(w, ["Forest", "Forest"], ci="G"), "Forest", "Dual Land"))

    def test_a_colorless_deck_needs_no_basics_unless_its_searchers_do(self):
        w = self.world()
        w.add("Wastes Fetch", 0.5, None, types="Sorcery", cmc=2, text=self.CULTIVATE)
        self.assertTrue(self.ok(self.plan(w, ["Wastes"], ci=""), "Wastes", "Dual Land"))
        self.assertFalse(self.ok(self.plan(w, ["Wastes", "Wastes", "Wastes Fetch"], ci=""), "Wastes", "Dual Land"))

    def test_the_floor_counts_the_searches_of_the_card_being_added(self):
        w = self.world()
        plan = self.plan(w, ["Cultivate"] + ["Forest"] * 2 + ["Swamp"])      # 3 basics, 2 to take
        self.assertTrue(self.ok(plan, "Forest", "Dual Land"))                # 2 left for 2
        self.assertFalse(self.ok(plan, "Forest", "Evolving Wilds"))          # Wilds takes a third: 2 left for 3
        plan.add("Swamp")
        self.assertTrue(self.ok(plan, "Swamp", "Evolving Wilds"))            # 3 left for 3, green keeps its 2
        self.assertFalse(self.ok(plan, "Forest", "Evolving Wilds"))          # 3 left, but only 1 of them green

    def test_adding_a_searcher_by_cutting_something_else_stays_legal_even_when_the_deck_is_short(self):
        w = self.world()
        short = self.plan(w, ["Weak Spell", "Cultivate", "Forest", "Swamp"])      # 2 basics, 2 to take
        self.assertTrue(self.ok(short, "Weak Spell", "Evolving Wilds"))           # a spell goes: 3 searches, 2 basics
        self.assertTrue(self.ok(short, "Cultivate", "Evolving Wilds"))            # so does another nonbasic
        self.assertFalse(self.ok(short, "Forest", "Evolving Wilds"))              # but a basic may not

    def test_a_spell_may_take_a_basics_slot_whatever_it_scores_but_a_land_must_score_the_minimum(self):
        w = self.world()
        plan = self.plan(w, ["Forest", "Forest", "Swamp", "Swamp"])
        self.assertTrue(self.ok(plan, "Forest", "Weak Spell"))
        self.assertFalse(self.ok(plan, "Forest", "Barely Scored Land"))            # 0.05 is under NONBASIC_MIN
        self.assertFalse(self.ok(plan, "Forest", "Utility Land"))                  # and 0.00 is not enough either
        self.assertTrue(self.ok(plan, "Forest", "Dual Land"))
        w.add("Just Enough Land", build.NONBASIC_MIN, None, types="Land", produced=["B", "G"], ci="BG")
        self.assertTrue(self.ok(self.plan(w, ["Forest", "Forest", "Swamp", "Swamp"]), "Forest", "Just Enough Land"))

    def test_a_swap_that_cuts_no_basic_passes_whatever_the_floor_and_the_land_score_say(self):
        w = self.world()
        bare = self.plan(w, ["Weak Spell", "Utility Land"])                         # not one basic
        self.assertTrue(self.ok(bare, "Weak Spell", "Barely Scored Land"))
        self.assertTrue(self.ok(bare, "Utility Land", "Evolving Wilds"))

    # --- which basic goes
    def test_ties_between_cuts_go_to_nonbasic_cards_first_then_to_the_color_with_the_most_lands_per_symbol(self):
        w = self.world()
        # Green Beast and Utility Land first (in the order they came), then the basics. Green has 3 lands for its
        # 2 symbols, black 2 lands for none, so black has the most lands per symbol and Swamp heads the basics.
        plan = self.plan(w, ["Green Beast", "Forest", "Forest", "Forest", "Swamp", "Swamp", "Utility Land"])
        order = [group[0][0].name for group in plan._groups(list(plan.cards))]
        self.assertEqual(order, ["Green Beast", "Utility Land", "Swamp", "Forest"])
        plan = self.plan(w, ["Black Imp", "Black Imp", "Forest", "Forest", "Swamp", "Swamp", "Swamp"])
        order = [group[0][0].name for group in plan._groups(list(plan.cards))]
        self.assertEqual(order, ["Black Imp", "Forest", "Swamp"])               # now black is the short color

    def test_a_basic_that_makes_none_of_the_decks_colors_goes_before_the_colored_ones(self):
        w = self.world()
        plan = self.plan(w, ["Green Beast", "Forest", "Forest", "Swamp", "Wastes"])
        order = [group[0][0].name for group in plan._groups(list(plan.cards))]
        self.assertEqual(order[-3:], ["Wastes", "Swamp", "Forest"])

    def test_an_unscored_nonbasic_land_is_cut_before_a_basic_of_the_same_worth(self):
        # Utility Land scores 0, like a basic, so cutting either costs the same; the utility land is listed last
        w = self.world()
        res, _, _ = run_upgrade(w, ["Forest"] * 4 + ["Swamp"] * 4 + ["Utility Land"], ["Dual Land"],
                                targets=zero_targets(land={"min": 9, "target": 9, "max": 9}), max_swaps=1)
        self.assertEqual((res["swaps"][0]["cut"], res["swaps"][0]["add"]), ("Utility Land", "Dual Land"))

    def test_a_land_that_scores_under_the_minimum_does_not_take_a_basics_slot_in_an_upgrade(self):
        w = self.world()
        res, _, _ = run_upgrade(w, ["Forest"] * 4 + ["Swamp"] * 4, ["Barely Scored Land", "Dual Land"],
                                targets=zero_targets(land={"min": 8, "target": 8, "max": 8}))
        self.assertEqual([s["add"] for s in res["swaps"]], ["Dual Land"])   # 0.05 would have beaten a basic's 0

    def test_a_searcher_may_replace_a_spell_in_a_deck_with_only_two_basics(self):
        w = self.world()
        res, _, _ = run_upgrade(w, ["Weak Spell", "Forest", "Swamp"], ["Cultivate"], max_swaps=3,
                                targets=zero_targets(land={"min": 2, "target": 2, "max": 2}))
        self.assertEqual([(s["cut"], s["add"]) for s in res["swaps"]], [("Weak Spell", "Cultivate")])
        kept = {name: n for n, name in res["deck_after"]["cards"]}
        self.assertEqual((kept["Forest"], kept["Swamp"]), (1, 1))        # the swap cut a spell, so no basic went


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

    def test_build_keeps_room_for_the_basics_its_land_searchers_take(self):
        # Ten Cultivates take 20 basic lands out of the library. The world's 17 nonbasic lands would leave only 18
        # basics of the 35 lands, so the nonbasic lands stop at 35 - 20 = 15, the best 15 by score.
        w = standard_world()
        for i in range(1, 11):
            w.add(f"Fetch Spell {i:02d}", 0.95, None, types="Sorcery", cmc=3, cost="{2}{G}",
                  text=UpgradeTests.CULTIVATE)
        db = w.db()
        res = build.build(make_ctx(w, db), db, prices=w.prices())
        names = self.all_names(res)
        self.assertEqual(sum(1 for n in names if n.startswith("Fetch Spell")), 10)
        self.assertEqual(sum(roles.basic_land_searches(db.get(n)) for n in names), 20)
        lands = [c for c in res["cards"] if c["section"] == "Lands"]
        self.assertEqual(len(lands), 15)
        self.assertEqual(sum(res["basics"].values()), 20)
        self.assertEqual(res["roles"]["land"], 35)
        self.assertEqual({c["name"] for c in lands}, {f"Dual {i:02d}" for i in range(1, 11)}
                         | {"Dual 11", "Dual 12", "Utility 01", "Utility 02", "Utility 03"})

    def test_a_searching_land_that_no_longer_fits_is_skipped_for_a_plainer_one(self):
        # Ten Cultivates need 20 basics. Each Evolving Wilds-style land then takes a land slot AND one more basic, so
        # after seven of them (7 lands, 27 basics) one slot of the 35 is open. An eighth would need 28 basics for its
        # slot and cannot have it; Dual 01 searches for nothing, so it takes the last slot.
        w = standard_world()
        for i in range(1, 11):
            w.add(f"Fetch Spell {i:02d}", 0.95, None, types="Sorcery", cmc=3, cost="{2}{G}",
                  text=UpgradeTests.CULTIVATE)
        for i in range(1, 9):
            w.add(f"Fetch Land {i}", round(0.99 - 0.01 * i, 2), None, types="Land", text=UpgradeTests.EVOLVING_WILDS)
        db = w.db()
        res = build.build(make_ctx(w, db), db, prices=w.prices())
        lands = {c["name"] for c in res["cards"] if c["section"] == "Lands"}
        self.assertEqual({n for n in lands if n.startswith("Fetch Land")}, {f"Fetch Land {i}" for i in range(1, 8)})
        self.assertIn("Dual 01", lands)
        self.assertEqual(len(lands), 8)
        self.assertEqual(sum(res["basics"].values()), 27)           # 20 for the Cultivates and 7 for the Wilds
        self.assertEqual(res["roles"]["land"], 35)

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
