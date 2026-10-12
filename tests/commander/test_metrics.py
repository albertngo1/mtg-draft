"""Tests for metrics.py: the removal power weights one by one, the seven groups of items on small decks whose every
number is worked out by hand in a comment, the one shape every item has, and the before -> after values.

Everything runs on a synthetic world of cards with known roles, attribute tags, prices and scores (World below),
so each assertion is a worked example rather than a snapshot of real data. Tags, combos, prices and the targets
file come in through arguments or are patched, and net is closed, so nothing here can reach the network."""
import copy, json, os, shutil, tempfile, time, unittest
from unittest import mock
from mtgcommander import brackets, build, carddb, fantasy, metrics, net, roles, score
from mtgcommander.providers import spellbook

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
CMDR = "Squirrel King"
EM = "—"
GROUP_IDS = ["power", "interaction", "mana", "playstyle", "win", "table", "changes"]
ITEM_KEYS = ["id", "label", "value", "unit", "target", "status", "why", "cards"]
BAND = {"min": 1, "target": 2, "max": 3}


def valueless_roles():
    """Targets that value no role, so a deck's value is its card scores plus 1.0 for each land (up to 99 lands)."""
    targets = {role: {"min": 0, "target": 0, "max": 0} for role in roles.ROLES}
    targets["land"] = {"min": 0, "target": 99, "max": 99}
    targets["topend"] = {"max": 99}
    return targets


def scry(name, types="Creature", cmc=2.0, cost="", text="", ci="", price=1.0, gc=False, produced=(), keywords=()):
    """A Scryfall-shaped card; carddb.card_record turns it into the record the code under test reads."""
    obj = {"oracle_id": "m-" + name, "name": name, "layout": "normal", "mana_cost": cost, "cmc": float(cmc),
           "type_line": types, "oracle_text": text, "color_identity": list(ci), "keywords": list(keywords),
           "legalities": {"commander": "legal"}, "prices": {"usd": str(price)} if price is not None else {},
           "game_changer": gc}
    if produced:
        obj["produced_mana"] = list(produced)
    return obj


def score_record(value, theme=0.0):
    return {"score": value, "parts": {"base": value - theme, "resid": 0.0, "theme": theme, "salt": 0.0},
            "kind": "builder", "evidence": f"test score {value:.2f}", "n": 100, "pulls": {}}


class World:
    """Cards with roles, attribute tags, scores, prices and (sometimes) a power, plus the db, attrs and ctx tests
    hand to metrics.compute."""

    def __init__(self):
        self.objs, self.role_of, self.attr_of, self.score_of, self.power_of = [], {}, {}, {}, {}
        self.add(CMDR, types=f"Legendary Creature {EM} Squirrel", cmc=3, cost="{1}{B}{G}", ci="BG", price=5.0)
        for basic, color in (("Forest", "G"), ("Swamp", "B")):
            self.add(basic, types=f"Basic Land {EM} {basic}", cmc=0, ci=color, produced=[color], price=0.1)

    def add(self, name, types="Creature", cmc=2, cost="", *, roles=(), attrs=(), score=0.0, theme=0.0, power=None,
            **kw):
        self.objs.append(scry(name, types, cmc, cost, **kw))
        self.role_of[name], self.attr_of[name] = set(roles), frozenset(attrs)
        self.score_of[name] = score_record(score, theme)
        if power is not None:
            self.power_of[name] = power
        return name

    def db(self):
        cards = {}
        for obj in self.objs:
            rec = carddb.card_record(obj)
            if rec["name"] in self.power_of:
                rec["power"] = self.power_of[rec["name"]]
            cards[rec["name"]] = rec
        return carddb.CardDB(cards)

    def attrs(self):
        return dict(self.attr_of)

    def ctx(self, bracket=3, **over):
        targets = {role: dict(BAND) for role in roles.ROLES}
        targets["land"] = {"min": 16, "target": 17, "max": 18}
        targets["topend"] = {"max": 1}
        ctx = {"commanders": [CMDR], "ci": "BG", "bracket": bracket,
               "spec": {"themes": [], "playstyle": "value", "weight": 0.5, "keep_fun": True, "bracket": bracket},
               "evidence": {"theme_weights": {}, "cards": {}, "salt": {}, "meta": None},
               "role_map": {n: set(r) for n, r in self.role_of.items()}, "scores": dict(self.score_of),
               "targets": targets, "owned": set(), "include": [], "exclude": set(), "warnings": [], "sources": {}}
        ctx.update(over)
        return ctx


def deck(*entries):
    """[(count, name)] from names, or (name, count) pairs: deck("Forest", ("Swamp", 3))."""
    return [(1, e) if isinstance(e, str) else (e[1], e[0]) for e in entries]


def items_of(result):
    return {item["id"]: item for g in result["groups"] for item in g["items"]}


def combo(cards, produces, missing=(), tag="E", pieces=None, variant_id="1-2"):
    """A Combo as spellbook makes it."""
    return spellbook._combo(variant_id, list(cards), [], list(produces), tag, len(cards) if pieces is None else pieces,
                            list(missing))


class MetricsCase(unittest.TestCase):
    """compute with every door closed, on a World the test fills."""

    def setUp(self):
        self.world = World()
        for fn in ("fetch_json", "request", "download"):
            mock.patch.object(net, fn, side_effect=AssertionError(f"net.{fn} must not run in a test")).start()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.targets_path = os.path.join(self.tmp, "metric_targets.json")
        # no file yet: removal and wipe power have no band, and an answer count is short only at 0
        mock.patch.object(roles, "METRIC_TARGETS_PATH", self.targets_path).start()
        self.addCleanup(mock.patch.stopall)

    def write_targets(self, **per_bracket):
        """Write a metric_targets.json: write_targets(**{"3": {"removal_power": [2.0, 3.0, 4.0]}})."""
        with open(self.targets_path, "w") as f:
            json.dump({"brackets": per_bracket}, f)

    def compute(self, cards, *, ctx=None, attrs=True, **kw):
        ctx = ctx or self.world.ctx()
        kw.setdefault("combos", {"included": [], "almost": []})
        return metrics.compute(ctx, self.world.db(), cards, commanders=[CMDR],
                               attrs=self.world.attrs() if attrs else None, **kw)

    def items(self, cards, **kw):
        return items_of(self.compute(cards, **kw))


# ----------------------------------------------------------------------------- removal power: the weights
class RemovalWeightTests(unittest.TestCase):
    """removal_quality(rec, attrs) = speed x reach x permanence x cost x repeatable, and each weight is a worked
    example: every test changes one factor of an otherwise neutral card (a sorcery that destroys a creature only,
    for 2 mana: 0.75 x 0.7 x 0.9 x 1.0 = 0.4725) and shows the product."""

    BASE = {"removal-creature", "removal-destroy"}

    def rec(self, types="Sorcery", cmc=2, keywords=()):
        return carddb.card_record(scry("Test Removal", types, cmc, keywords=keywords))

    def quality(self, attrs=BASE, **card):
        return metrics.removal_quality(self.rec(**card), frozenset(attrs))

    def test_the_neutral_card_is_the_product_of_its_four_weights(self):
        value, weights = self.quality()
        # sorcery speed 0.75 x creatures only 0.7 x destroy 0.9 x MV 2 1.0 x not repeatable 1.0
        self.assertEqual(weights, {"speed": 0.75, "reach": 0.7, "permanence": 0.9, "cost": 1.0, "repeatable": 1.0})
        self.assertAlmostEqual(value, 0.4725)

    def test_assassins_trophy_is_the_designs_example(self):
        # instant 1.0 x any permanent 1.0 x destroy 0.9 x MV 2 1.0 = 0.90
        value, weights = self.quality({"removal-permanent", "removal-destroy"}, types="Instant", cmc=2)
        self.assertEqual(weights, {"speed": 1.0, "reach": 1.0, "permanence": 0.9, "cost": 1.0, "repeatable": 1.0})
        self.assertAlmostEqual(value, 0.90)

    # --- speed
    def test_speed_an_instant_is_1_0(self):
        # 1.0 x 0.7 x 0.9 x 1.0 = 0.63
        value, weights = self.quality(types="Instant")
        self.assertEqual(weights["speed"], 1.0)
        self.assertAlmostEqual(value, 0.63)

    def test_speed_flash_is_1_0_too(self):
        # a Flash creature is as quick as an instant: 1.0 x 0.7 x 0.9 x 1.0 = 0.63
        value, weights = self.quality(types="Creature", keywords=["Flash"])
        self.assertEqual(weights["speed"], 1.0)
        self.assertAlmostEqual(value, 0.63)

    def test_speed_a_sorcery_or_any_other_card_is_0_75(self):
        for types in ("Sorcery", "Creature", "Enchantment", "Artifact"):
            with self.subTest(types=types):
                self.assertEqual(self.quality(types=types)[1]["speed"], 0.75)

    def test_speed_a_repeatable_ability_can_be_used_at_any_time_so_it_is_1_0(self):
        # a creature with an ability that removes again and again: 1.0 x 0.7 x 0.9 x 1.0 x 1.5 = 0.945
        value, weights = self.quality(self.BASE | {"repeatable-removal"}, types="Creature")
        self.assertEqual((weights["speed"], weights["repeatable"]), (1.0, 1.5))
        self.assertAlmostEqual(value, 0.945)

    def test_speed_a_planeswalkers_loyalty_ability_works_only_on_your_own_turn_so_it_is_0_75(self):
        # 0.75 x 0.7 x 0.9 x 1.0 x 1.5 = 0.70875; the speed of an ability does not rescue a planeswalker
        value, weights = self.quality(self.BASE | {"repeatable-removal"}, types="Legendary Planeswalker")
        self.assertEqual((weights["speed"], weights["repeatable"]), (0.75, 1.5))
        self.assertAlmostEqual(value, 0.70875)

    # --- reach
    def test_reach_any_permanent_is_1_0(self):
        # 0.75 x 1.0 x 0.9 x 1.0 = 0.675
        value, weights = self.quality({"removal-permanent", "removal-destroy"})
        self.assertEqual(weights["reach"], 1.0)
        self.assertAlmostEqual(value, 0.675)

    def test_reach_any_nonland_permanent_is_1_0_too(self):
        self.assertEqual(self.quality({"removal-nonland", "removal-destroy"})[1]["reach"], 1.0)

    def test_reach_creatures_and_planeswalkers_is_0_8(self):
        # 0.75 x 0.8 x 0.9 x 1.0 = 0.54
        value, weights = self.quality({"removal-creature", "removal-planeswalker", "removal-destroy"})
        self.assertEqual(weights["reach"], 0.8)
        self.assertAlmostEqual(value, 0.54)

    def test_reach_creatures_only_is_0_7(self):
        self.assertEqual(self.quality({"removal-creature", "removal-destroy"})[1]["reach"], 0.7)

    def test_reach_one_kind_of_permanent_such_as_artifacts_or_enchantments_is_0_6(self):
        # 0.75 x 0.6 x 0.9 x 1.0 = 0.405
        for tags in ({"removal-artifact"}, {"removal-enchantment"}, {"removal-artifact", "removal-enchantment"},
                     {"removal-land"}, set()):
            with self.subTest(tags=sorted(tags)):
                value, weights = self.quality(tags | {"removal-destroy"})
                self.assertEqual(weights["reach"], 0.6)
                self.assertAlmostEqual(value, 0.405)

    def test_reach_removal_with_a_condition_is_0_6_whatever_it_could_otherwise_hit(self):
        # toughness limits, "nonblack" and damage: 0.75 x 0.6 x 0.9 x 1.0 = 0.405, though it hits any permanent
        for tag in ("removal-toughness", "doom-blade", "removal-burn"):
            with self.subTest(tag=tag):
                value, weights = self.quality({"removal-permanent", "removal-destroy", tag})
                self.assertEqual(weights["reach"], 0.6)
                self.assertAlmostEqual(value, 0.405)

    # --- permanence
    def test_permanence_exile_is_1_0(self):
        # 0.75 x 0.7 x 1.0 x 1.0 = 0.525
        value, weights = self.quality({"removal-creature", "removal-exile"})
        self.assertEqual(weights["permanence"], 1.0)
        self.assertAlmostEqual(value, 0.525)

    def test_permanence_destroy_is_0_9(self):
        self.assertEqual(self.quality({"removal-creature", "removal-destroy"})[1]["permanence"], 0.9)

    def test_permanence_damage_or_a_shrinking_effect_is_0_8_when_the_card_says_nothing_better(self):
        # 0.75 x 0.7 x 0.8 x 1.0 = 0.42
        value, weights = self.quality({"removal-creature"})
        self.assertEqual(weights["permanence"], 0.8)
        self.assertAlmostEqual(value, 0.42)

    def test_permanence_bounce_is_0_5(self):
        # 0.75 x 0.7 x 0.5 x 1.0 = 0.2625
        value, weights = self.quality({"removal-creature", "removal-bounce"})
        self.assertEqual(weights["permanence"], 0.5)
        self.assertAlmostEqual(value, 0.2625)

    def test_permanence_the_best_one_wins_when_a_card_has_several(self):
        self.assertEqual(self.quality({"removal-creature", "removal-exile", "removal-destroy",
                                       "removal-bounce"})[1]["permanence"], 1.0)
        self.assertEqual(self.quality({"removal-creature", "removal-destroy", "removal-bounce"})[1]["permanence"], 0.9)

    # --- cost
    def test_cost_two_or_less_is_1_0_three_0_9_four_0_8_five_or_more_0_65(self):
        # every other weight stays at the neutral card's 0.75 x 0.7 x 0.9 = 0.4725
        for mana_value, expected_cost in ((0, 1.0), (1, 1.0), (2, 1.0), (3, 0.9), (4, 0.8), (5, 0.65), (6, 0.65),
                                          (11, 0.65)):
            with self.subTest(mana_value=mana_value):
                value, weights = self.quality(cmc=mana_value)
                self.assertEqual(weights["cost"], expected_cost)
                self.assertAlmostEqual(value, 0.4725 * expected_cost)

    # --- repeatable
    def test_repeatable_removal_is_worth_half_again_as_much(self):
        # an enchantment whose ability removes again and again (usable at any time, so speed 1.0):
        # 1.0 x 0.7 x 0.9 x 1.0 x 1.5 = 0.945, half again the 0.63 the same card would be worth once
        value, weights = self.quality(self.BASE | {"repeatable-removal"}, types="Enchantment")
        self.assertEqual(weights["repeatable"], 1.5)
        self.assertAlmostEqual(value, 0.945)
        self.assertAlmostEqual(value / 1.5, 0.63)

    def test_a_card_that_is_not_repeatable_has_a_repeatable_weight_of_1(self):
        self.assertEqual(self.quality()[1]["repeatable"], 1.0)

    def test_the_value_is_always_the_product_of_the_five_weights(self):
        for attrs in (self.BASE, self.BASE | {"repeatable-removal"}, {"removal-permanent", "removal-exile"}, set()):
            for types, cmc in (("Instant", 1), ("Sorcery", 4), ("Creature", 6)):
                value, w = self.quality(attrs, types=types, cmc=cmc)
                self.assertAlmostEqual(value, w["speed"] * w["reach"] * w["permanence"] * w["cost"] * w["repeatable"])

    def test_the_weights_come_back_with_the_five_names_the_item_shape_documents(self):
        self.assertEqual(sorted(self.quality()[1]), ["cost", "permanence", "reach", "repeatable", "speed"])

    def test_a_list_of_slugs_works_as_well_as_a_set(self):
        self.assertAlmostEqual(self.quality(["removal-creature", "removal-destroy"])[0], 0.4725)


class ArithmeticLineTests(MetricsCase):
    """The `why` line of a removal card shows the arithmetic, in the words of the design."""

    def lines(self, name, role="removal"):
        item = self.items(deck(name))["removal_power" if role == "removal" else "wipe_power"]
        return item["why"]

    def test_the_designs_example_line_for_assassins_trophy(self):
        self.world.add("Assassin's Trophy", "Instant", 2, "{B}{G}", roles=["removal"],
                       attrs=["removal-permanent", "removal-destroy"])
        self.assertEqual(self.lines("Assassin's Trophy"),
                         ["Assassin's Trophy 0.90 = instant 1.0 × any permanent 1.0 × destroy 0.9 × MV 2 1.0"])

    def test_a_repeatable_card_shows_the_extra_factor_last(self):
        self.world.add("Pinger", "Creature", 3, "{2}{G}", roles=["removal"],
                       attrs=["removal-creature", "removal-toughness", "repeatable-removal"])
        # repeatable ability 1.0 x conditional 0.6 x damage 0.8 x MV 3 0.9 x 1.5 = 0.648
        self.assertEqual(self.lines("Pinger"), ["Pinger 0.65 = repeatable ability 1.0 × conditional 0.6 × "
                                                "damage or -X/-X 0.8 × MV 3 0.9 × repeatable 1.5"])

    def test_a_one_sided_wipe_shows_its_extra_factor(self):
        self.world.add("Clean Sweep", "Sorcery", 5, "{3}{B}{B}", roles=["wipe"],
                       attrs=["removal-creature", "removal-exile", "sweeper", "sweeper-one-sided"])
        # sorcery speed 0.75 x creatures only 0.7 x exile 1.0 x MV 5 0.65 = 0.34125; one-sided x 1.5 = 0.511875
        self.assertEqual(self.lines("Clean Sweep", "wipe"), ["Clean Sweep 0.51 = sorcery speed 0.75 × creatures "
                                                            "only 0.7 × exile 1.0 × MV 5 0.65 × one-sided 1.5"])

    def test_the_weights_print_the_way_the_design_writes_them(self):
        for weight, text in ((1.0, "1.0"), (0.9, "0.9"), (0.65, "0.65"), (0.75, "0.75"), (1.5, "1.5"), (0.5, "0.5")):
            self.assertEqual(metrics._weight(weight), text)


# ----------------------------------------------------------------------------- group: power
class PowerGroupTests(MetricsCase):
    def setUp(self):
        super().setUp()
        w = self.world
        w.add("Staple", "Creature", 3, "{2}{G}", score=0.5, theme=0.1)
        w.add("Filler", "Creature", 2, "{1}{B}", score=0.3)
        w.add("Power Crypt", "Artifact", 1, "{1}", score=0.9, gc=True)
        w.add("Mind Games", "Artifact", 1, "{1}", score=0.8, gc=True)
        w.add("Rich Pack", "Artifact", 1, "{1}", score=0.8, gc=True)
        w.add("Sixth Sense", "Artifact", 1, "{1}", score=0.8, gc=True)
        w.add("Time Warp", "Sorcery", 5, "{3}{U}{U}", ci="U")
        w.add("Armageddon", "Sorcery", 4, "{3}{W}", ci="W")
        w.add("Hunter", "Sorcery", 2, "{1}{B}", roles=["tutor"])

    def power(self, names, **kw):
        return self.items(deck(*names), **kw)

    def test_the_score_is_the_decks_value_split_into_card_power_and_theme_fit(self):
        # with no value for any role, the value is the card scores plus 1.0 for each land:
        # Staple 0.5 (of which theme 0.1) + Filler 0.3 + Forest 1.0 + Swamp 1.0 = 2.8; without the theme part 2.7
        ctx = self.world.ctx(targets=valueless_roles())
        got = self.items(deck("Staple", "Filler", "Forest", "Swamp"), ctx=ctx)
        self.assertEqual((got["score"]["value"], got["score_power"]["value"], got["score_theme"]["value"]),
                         (2.8, 2.7, 0.1))
        self.assertIsNone(got["score"]["unit"])

    def test_the_score_follows_build_deck_value_exactly(self):
        ctx = self.world.ctx()
        names = ["Staple", "Filler", "Hunter", "Forest", "Swamp"]
        value = build.deck_value(names, ctx, self.world.db())
        got = self.items(deck(*names), ctx=ctx)
        self.assertEqual(got["score"]["value"], round(value["total"], 2))
        self.assertEqual(got["score_power"]["value"], round(value["power"], 2))

    def test_a_deck_with_no_game_changers_no_extra_turns_and_no_land_denial_fits_bracket_1(self):
        # the chosen bracket (3) is what the bracket item shows; the floor is 1, as for nearly every precon
        got = self.power(["Staple", "Filler", "Forest"])
        self.assertEqual((got["bracket"]["value"], got["bracket"]["status"], got["bracket"]["target"]),
                         (3, "inside", {"min": None, "target": 3, "max": 3}))
        self.assertIn("Within Bracket 3's limits", got["bracket"]["why"][0])
        self.assertEqual((got["bracket_floor"]["value"], got["bracket_floor"]["status"]), (1, None))
        self.assertIn("Brackets 1 and 2 have the same limits", got["bracket_floor"]["why"][0])

    def test_one_extra_turn_card_lifts_the_floor_to_bracket_2(self):
        # Bracket 1 allows none; Bracket 2 allows one that is not chained
        self.assertEqual(self.power(["Staple", "Time Warp"])["bracket_floor"]["value"], 2)

    def test_three_game_changers_lift_it_to_3_and_a_fourth_to_4(self):
        self.assertEqual(self.power(["Staple", "Power Crypt", "Mind Games", "Rich Pack"])["bracket_floor"]["value"], 3)
        self.assertEqual(self.power(["Staple", "Power Crypt", "Mind Games", "Rich Pack", "Sixth Sense"])
                         ["bracket_floor"]["value"], 4)

    def test_mass_land_denial_lifts_it_to_4(self):
        self.assertEqual(self.power(["Staple", "Armageddon"])["bracket_floor"]["value"], 4)

    def test_a_deck_over_the_chosen_bracket_is_over_and_the_reasons_are_listed(self):
        got = self.power(["Staple", "Armageddon"])["bracket"]
        self.assertEqual(got["status"], "over")
        self.assertTrue(any("Mass land denial is not allowed in Bracket 3" in line for line in got["why"]))

    def test_the_chosen_bracket_decides_over_or_inside(self):
        # mass land denial breaks Bracket 3 but not Bracket 5; the floor says 4 either way
        got = self.items(deck("Staple", "Armageddon"), ctx=self.world.ctx(bracket=5))
        self.assertEqual((got["bracket"]["value"], got["bracket"]["status"]), (5, "inside"))
        self.assertEqual(got["bracket_floor"]["value"], 4)

    def test_game_changers_used_and_allowed(self):
        got = self.power(["Staple", "Power Crypt", "Mind Games"])["game_changers"]
        self.assertEqual((got["value"], got["target"], got["status"]), (2, {"min": None, "target": None, "max": 3},
                                                                        "inside"))
        self.assertEqual(got["cards"], ["Power Crypt", "Mind Games"])
        self.assertEqual(got["why"], ["Bracket 3 allows up to 3."])

    def test_a_fourth_game_changer_is_over_the_limit_at_bracket_3(self):
        got = self.power(["Power Crypt", "Mind Games", "Rich Pack", "Sixth Sense"])["game_changers"]
        self.assertEqual((got["value"], got["status"]), (4, "over"))

    def test_brackets_with_no_game_changer_limit_say_any_number(self):
        got = self.items(deck("Power Crypt"), ctx=self.world.ctx(bracket=4))["game_changers"]
        self.assertEqual((got["target"]["max"], got["status"], got["why"]), (None, "inside",
                                                                            ["Bracket 4 allows any number."]))

    def test_tutors_are_the_role_count_against_the_roles_band(self):
        got = self.power(["Hunter", "Staple"])["tutors"]
        self.assertEqual((got["value"], got["target"], got["status"], got["cards"]), (1, BAND, "inside", ["Hunter"]))
        self.assertEqual(self.power(["Staple"])["tutors"]["status"], "short")

    def test_combos_in_the_deck_and_one_card_away_are_counted_and_described(self):
        done = combo(["Staple", "Filler"], ["Infinite mana"], tag="S", variant_id="1-2")
        near = combo(["Staple", "Hunter"], ["Infinite damage"], missing=["Hunter"], tag="E", variant_id="3-4")
        got = self.power(["Staple", "Filler"], combos={"included": [done], "almost": [near]})
        self.assertEqual(got["combos_in_deck"]["value"], 1)
        self.assertEqual(got["combos_in_deck"]["cards"], ["Staple", "Filler"])
        self.assertEqual(got["combos_in_deck"]["why"], [
            "Staple + Filler → Infinite mana (Bracket 4 and up; https://commanderspellbook.com/combo/1-2/)"])
        self.assertEqual(got["combos_one_away"]["value"], 1)
        self.assertEqual(got["combos_one_away"]["cards"], ["Hunter"])
        self.assertEqual(got["combos_one_away"]["why"], [
            "Add Hunter to complete Staple + Hunter → Infinite damage (any bracket; "
            "https://commanderspellbook.com/combo/3-4/)"])

    def test_no_combos_found_says_so(self):
        got = self.power(["Staple"])
        self.assertEqual((got["combos_in_deck"]["value"], got["combos_one_away"]["value"]), (0, 0))
        self.assertIn("No combo", got["combos_in_deck"]["why"][0])

    def test_a_long_list_of_almost_combos_names_the_first_few_and_the_count_of_the_rest(self):
        # two-card combos first, then the shorter ones; 12 combos, MAX_LISTED shown
        near = [combo(["A%d" % i, "B%d" % i, "C%d" % i], ["x"], missing=["B%d" % i], variant_id="9-%d" % i)
                for i in range(8)]
        near += [combo(["D%d" % i, "E%d" % i], ["x"], missing=["E%d" % i], variant_id="8-%d" % i) for i in range(4)]
        got = self.power(["Staple"], combos={"included": [], "almost": near})["combos_one_away"]
        self.assertEqual(got["value"], 12)
        self.assertEqual(len(got["why"]), metrics.MAX_LISTED + 1)
        self.assertEqual(got["why"][-1], "and 2 more (two-card combos are listed first)")
        self.assertTrue(got["why"][0].startswith("Add E0 to complete D0 + E0"))      # a two-card combo leads
        self.assertEqual(got["cards"][:4], ["E0", "E1", "E2", "E3"])

    def test_combos_that_were_not_checked_have_no_number(self):
        got = self.power(["Staple"], combos=None)
        for key in ("combos_in_deck", "combos_one_away"):
            self.assertEqual((got[key]["value"], got[key]["status"]), (None, None))
            self.assertIn("Combos were not checked", got[key]["why"][0])
        self.assertTrue(any("Combos were not checked" in line for line in got["bracket"]["why"]))


# ----------------------------------------------------------------------------- group: interaction
class InteractionGroupTests(MetricsCase):
    def setUp(self):
        super().setUp()
        w = self.world
        trophy = ["removal-permanent", "removal-destroy", "removal-creature", "removal-artifact",
                  "removal-enchantment", "removal-planeswalker", "removal-land"]
        w.add("Assassin's Trophy", "Instant", 2, "{B}{G}", roles=["removal"], attrs=trophy)               # 0.90
        w.add("Exile Bolt", "Instant", 1, "{B}", roles=["removal"], attrs=["removal-creature", "removal-exile"])  # 0.70
        w.add("Slow Plague", "Sorcery", 4, "{2}{B}{B}", roles=["removal"],
              attrs=["removal-creature", "removal-planeswalker", "removal-destroy"])                      # 0.432
        w.add("Pinger", "Creature", 3, "{2}{G}", roles=["removal"],
              attrs=["removal-creature", "removal-toughness", "repeatable-removal"])                      # 0.648
        w.add("Wrath Mock", "Sorcery", 4, "{2}{B}{B}", roles=["wipe"],
              attrs=["removal-creature", "removal-destroy", "sweeper"])                                   # 0.378
        w.add("One Sided Wrath", "Sorcery", 5, "{3}{B}{B}", roles=["wipe"],
              attrs=["removal-creature", "removal-toughness", "sweeper", "sweeper-one-sided"])            # 0.351
        w.add("Counter Magic", "Instant", 2, "{1}{U}", roles=["counter"], attrs=["counterspell"])
        w.add("Ward Charm", "Instant", 1, "{G}", roles=["protection"])
        w.add("Flash Guard", "Creature", 3, "{2}{G}", roles=["protection"], keywords=["Flash"])
        w.add("Grave Hate", "Instant", 1, "{B}", attrs=["hate-graveyard"])
        w.add("Bear", "Creature", 2, "{1}{G}")
        self.everything = ["Assassin's Trophy", "Exile Bolt", "Slow Plague", "Pinger", "Wrath Mock", "One Sided Wrath",
                           "Counter Magic", "Ward Charm", "Flash Guard", "Grave Hate", "Bear"]

    def test_removal_power_is_the_sum_of_the_removal_cards_strongest_first(self):
        got = self.items(deck(*self.everything))["removal_power"]
        # 0.90 + 0.70 + 0.648 + 0.432 = 2.68
        self.assertEqual(got["value"], 2.68)
        self.assertEqual(got["cards"], ["Assassin's Trophy", "Exile Bolt", "Pinger", "Slow Plague"])
        self.assertEqual([line.split(" = ")[0] for line in got["why"]], [
            "Assassin's Trophy 0.90", "Exile Bolt 0.70", "Pinger 0.65", "Slow Plague 0.43"])

    def test_wipe_power_is_the_same_for_the_wipes_and_a_one_sided_wipe_counts_half_again(self):
        got = self.items(deck(*self.everything))["wipe_power"]
        # Wrath Mock: 0.75 x 0.7 x 0.9 x 0.8 = 0.378. One Sided Wrath: 0.75 x 0.6 x 0.8 x 0.65 = 0.234, x 1.5 = 0.351
        self.assertEqual(got["value"], 0.73)
        self.assertEqual(got["cards"], ["Wrath Mock", "One Sided Wrath"])
        self.assertTrue(got["why"][1].endswith("× one-sided 1.5"))

    def test_a_wipe_is_not_also_counted_as_removal(self):
        self.assertNotIn("Wrath Mock", self.items(deck(*self.everything))["removal_power"]["cards"])

    def test_a_deck_with_no_removal_has_power_0_and_says_so(self):
        got = self.items(deck("Bear"))["removal_power"]
        self.assertEqual((got["value"], got["why"], got["cards"]), (0, ["No removal cards."], []))

    def test_a_card_counts_once_however_many_copies_the_list_names(self):
        self.assertEqual(self.items(deck(("Exile Bolt", 3)))["removal_power"]["value"], 0.7)

    def test_the_band_comes_from_the_metric_targets_file_for_the_chosen_bracket(self):
        self.write_targets(**{"3": {"removal_power": [2.0, 3.0, 4.0], "wipe_power": [0.5, 1.0, 2.0]},
                              "5": {"removal_power": [1.0, 2.0, 2.5], "wipe_power": [0.0, 0.0, 0.5]}})
        got = self.items(deck(*self.everything))
        self.assertEqual(got["removal_power"]["target"], {"min": 2.0, "target": 3.0, "max": 4.0})
        self.assertEqual((got["removal_power"]["status"], got["wipe_power"]["status"]), ("inside", "inside"))
        five = self.items(deck(*self.everything), ctx=self.world.ctx(bracket=5))
        self.assertEqual((five["removal_power"]["status"], five["wipe_power"]["status"]), ("over", "over"))
        small = self.items(deck("Exile Bolt"))
        self.assertEqual(small["removal_power"]["status"], "short")          # 0.70 against a minimum of 2.0

    def test_with_no_targets_file_the_two_have_a_value_and_no_band(self):
        got = self.items(deck(*self.everything))
        self.assertEqual((got["removal_power"]["target"], got["removal_power"]["status"]), (None, None))
        self.assertEqual((got["wipe_power"]["target"], got["wipe_power"]["status"]), (None, None))

    def test_a_damaged_targets_file_means_no_band_not_a_crash(self):
        for text in ("{not json", "[1]", '{"brackets": []}', '{"brackets": {"3": {"removal_power": [1, 2]}}}'):
            with open(self.targets_path, "w") as f:
                f.write(text)
            self.assertEqual(self.items(deck("Exile Bolt"))["removal_power"]["target"], None, text)

    def test_targets_read_one_bracket_and_clamp_the_number(self):
        self.write_targets(**{"1": {"removal_power": [1.0, 2.0, 3.0]}, "5": {"removal_power": [4.0, 5.0, 6.0]}})
        self.assertEqual(metrics.targets(1), {"removal_power": {"min": 1.0, "target": 2.0, "max": 3.0}})
        self.assertEqual(metrics.targets(0)["removal_power"]["min"], 1.0)          # clamped to 1
        self.assertEqual(metrics.targets(9)["removal_power"]["min"], 4.0)          # clamped to 5
        self.assertEqual(metrics.targets(2), {})

    def test_answers_to_each_threat_list_the_cards_that_can_deal_with_it(self):
        got = self.items(deck(*self.everything))
        self.assertEqual(got["answers_creatures"]["value"], 6)       # Trophy, Exile Bolt, Slow Plague, Pinger, both wipes
        self.assertEqual(got["answers_artifacts"]["cards"], ["Assassin's Trophy"])
        self.assertEqual(got["answers_enchantments"]["cards"], ["Assassin's Trophy"])
        self.assertEqual(got["answers_planeswalkers"]["cards"], ["Assassin's Trophy", "Slow Plague"])
        self.assertEqual(got["answers_lands"]["cards"], ["Assassin's Trophy"])
        self.assertEqual(got["answers_graveyards"]["cards"], ["Grave Hate"])
        self.assertEqual(got["answers_spells"]["cards"], ["Counter Magic"])

    def test_a_sweeper_counts_as_an_answer_to_creatures(self):
        self.world.add("Sweeper Only", "Sorcery", 4, "{2}{B}{B}", attrs=["sweeper"])
        self.assertEqual(self.items(deck("Sweeper Only"))["answers_creatures"]["cards"], ["Sweeper Only"])

    def test_a_threat_nothing_answers_is_short_and_one_answer_is_enough(self):
        got = self.items(deck("Exile Bolt", "Bear"))
        self.assertEqual((got["answers_artifacts"]["value"], got["answers_artifacts"]["status"]), (0, "short"))
        self.assertEqual(got["answers_artifacts"]["target"], {"min": 1, "target": None, "max": None})
        self.assertEqual((got["answers_creatures"]["value"], got["answers_creatures"]["status"]), (1, "inside"))
        self.assertEqual(got["answers_artifacts"]["why"], ["Nothing in the deck can."])

    def test_counterspells_and_protection_are_role_counts_against_the_band(self):
        got = self.items(deck("Counter Magic", "Ward Charm", "Flash Guard", "Bear"))
        self.assertEqual((got["counterspells"]["value"], got["counterspells"]["status"]), (1, "inside"))
        self.assertEqual((got["protection"]["value"], got["protection"]["cards"]), (2, ["Ward Charm", "Flash Guard"]))

    def test_the_share_of_interaction_at_instant_speed(self):
        got = self.items(deck(*self.everything))["instant_share"]
        # interaction: Trophy, Exile Bolt, Slow Plague, Pinger, Wrath Mock, One Sided Wrath, Counter Magic, Ward Charm,
        # Flash Guard = 9 (Pinger is a creature with no flash). Instants or flash: Trophy, Exile Bolt, Counter Magic,
        # Ward Charm, Flash Guard = 5. 5 / 9 = 55.6%
        self.assertEqual((got["value"], got["unit"]), (55.6, "%"))
        self.assertEqual(got["cards"], ["Assassin's Trophy", "Exile Bolt", "Counter Magic", "Ward Charm", "Flash Guard"])
        self.assertEqual(got["why"], ["5 of 9 removal, wipe, counterspell and protection cards are instants or have "
                                      "flash."])

    def test_a_deck_with_no_interaction_has_no_share(self):
        got = self.items(deck("Bear"))["instant_share"]
        self.assertEqual((got["value"], got["why"]), (None, ["The deck has no interaction cards."]))

    def test_without_tag_data_the_tag_items_have_no_value_and_the_role_items_still_do(self):
        got = self.items(deck(*self.everything), attrs=False)
        for key in ("removal_power", "wipe_power", "answers_creatures", "answers_spells"):
            self.assertEqual((got[key]["value"], got[key]["status"]), (None, None), key)
            self.assertIn("function tags", got[key]["why"][0])
        self.assertEqual(got["counterspells"]["value"], 1)
        self.assertEqual(got["instant_share"]["value"], 55.6)


# ----------------------------------------------------------------------------- group: interaction, answer bands
class AnswerBandTests(MetricsCase):
    """Each "answers to ..." item takes its band from commander/metric_targets.json (what real decks at the bracket
    hold), so a count is short when it is fewer than their 25th percentile, like every other count; a threat the file
    has no row for needs one answer, as before."""
    # Bracket 3 as a calibration might have measured it: creatures 7/10/14, enchantments 3/4/7, spells 2/3/5
    BRACKET_3 = {"answers_creatures": [7, 10, 14], "answers_artifacts": [3, 4, 6], "answers_enchantments": [3, 4, 7],
                 "answers_planeswalkers": [2, 3, 8], "answers_lands": [0, 1, 2], "answers_graveyards": [0, 1, 3],
                 "answers_spells": [2, 3, 5]}

    def setUp(self):
        super().setUp()
        w = self.world
        w.add("Pulse", "Instant", 3, "{2}{B}{G}", attrs=["removal-artifact", "removal-enchantment",
                                                          "removal-planeswalker"])
        for i in range(1, 10):
            w.add(f"Disenchant {i}", "Instant", 1, "{G}", attrs=["removal-enchantment"])
        w.add("Wrath Mock", "Sorcery", 4, "{2}{B}{B}", roles=["wipe"], attrs=["sweeper"])
        w.add("Counter Magic", "Instant", 2, "{1}{U}", roles=["counter"], attrs=["counterspell"])
        w.add("Counter Two", "Instant", 3, "{2}{U}", roles=["counter"], attrs=["counterspell"])
        w.add("Bear", "Creature", 2, "{1}{G}")
        self.write_targets(**{"3": self.BRACKET_3})

    def test_each_item_takes_the_measured_band_for_the_chosen_bracket(self):
        got = self.items(deck("Pulse", "Bear"))
        for id_, (low, mid, high) in self.BRACKET_3.items():
            band = got[id_]["target"]
            expected = {"min": low, "target": mid, "max": high}
            if id_ == "answers_spells":
                expected["min"] = expected["target"] = 0            # the commander has no blue: see the next test
            self.assertEqual(band, expected, id_)
        self.write_targets(**{"5": {"answers_enchantments": [4, 4, 6]}})
        five = self.items(deck("Pulse"), ctx=self.world.ctx(bracket=5))
        self.assertEqual(five["answers_enchantments"]["target"], {"min": 4, "target": 4, "max": 6})

    def test_short_is_fewer_than_the_25th_percentile_not_only_none(self):
        # Bracket 3 enchantments run 3/4/7: one is no longer enough, three is the least that is not short
        one = self.items(deck("Bear"))["answers_enchantments"]
        self.assertEqual((one["value"], one["status"]), (0, "short"))
        for count, status in ((1, "short"), (2, "short"), (3, "inside"), (4, "inside"), (7, "inside"), (8, "over")):
            names = ["Disenchant %d" % i for i in range(1, count + 1)]
            got = self.items(deck(*names, "Bear"))["answers_enchantments"]
            self.assertEqual((got["value"], got["status"]), (count, status), count)

    def test_a_card_that_answers_three_kinds_counts_for_each_of_them(self):
        got = self.items(deck("Pulse", "Disenchant 1", "Disenchant 2"))
        self.assertEqual(got["answers_enchantments"]["value"], 3)             # Pulse and two Disenchants
        self.assertEqual((got["answers_artifacts"]["value"], got["answers_planeswalkers"]["value"]), (1, 1))
        self.assertEqual(got["answers_enchantments"]["status"], "inside")     # 3 is the 25th percentile
        self.assertEqual(got["answers_planeswalkers"]["status"], "short")     # 1 against a minimum of 2

    def test_without_blue_in_the_colors_no_counterspell_is_not_short(self):
        # the counterspell rule: a deck without blue is not expected to hold any, whatever real blue decks hold
        black_green = self.items(deck("Bear"))["answers_spells"]
        self.assertEqual((black_green["value"], black_green["status"]), (0, "inside"))
        self.assertEqual(black_green["target"], {"min": 0, "target": 0, "max": 5})
        blue = self.items(deck("Bear"), ctx=self.world.ctx(ci="UB"))["answers_spells"]
        self.assertEqual((blue["value"], blue["status"]), (0, "short"))
        self.assertEqual(blue["target"], {"min": 2, "target": 3, "max": 5})
        enough = self.items(deck("Counter Magic", "Counter Two"), ctx=self.world.ctx(ci="UB"))["answers_spells"]
        self.assertEqual((enough["value"], enough["status"]), (2, "inside"))

    def test_a_threat_the_file_has_no_row_for_still_needs_one_answer(self):
        self.write_targets(**{"3": {"answers_creatures": [7, 10, 14]}})
        got = self.items(deck("Pulse", "Bear"))
        self.assertEqual(got["answers_creatures"]["target"], {"min": 7, "target": 10, "max": 14})
        self.assertEqual(got["answers_artifacts"]["target"], {"min": 1, "target": None, "max": None})
        self.assertEqual((got["answers_artifacts"]["value"], got["answers_artifacts"]["status"]), (1, "inside"))
        self.assertEqual((got["answers_lands"]["value"], got["answers_lands"]["status"]), (0, "short"))
        self.assertEqual(got["answers_lands"]["why"], ["Nothing in the deck can."])     # no band, no extra line

    def test_a_bracket_the_file_lacks_falls_back_for_every_threat(self):
        got = self.items(deck("Pulse"), ctx=self.world.ctx(bracket=2))
        for id_ in roles.THREAT_IDS:
            self.assertEqual(got[id_]["target"], {"min": 1, "target": None, "max": None}, id_)

    def test_a_measured_band_says_where_it_comes_from_and_what_short_means(self):
        got = self.items(deck("Pulse", "Disenchant 1"))
        self.assertEqual(got["answers_enchantments"]["why"], [
            "2 cards can deal with it",
            "Decks at Bracket 3 usually hold 3 to 7 (typically 4); fewer than 3 is short."])
        self.assertEqual(got["answers_lands"]["why"], [
            "Nothing in the deck can.", "Decks at Bracket 3 usually hold 0 to 2 (typically 1); no minimum applies."])
        # a deck without blue is told why counterspells are not asked of it, not what blue decks hold
        self.assertEqual(got["answers_spells"]["why"], ["Nothing in the deck can.",
                                                         "The commander's colors have no blue, so none is expected."])

    def test_one_answer_reads_as_one_card_not_one_cards(self):
        got = self.items(deck("Wrath Mock", "Bear"))["answers_creatures"]
        self.assertEqual(got["why"][0], "1 card can deal with it")

    def test_the_cards_listed_for_a_count_are_the_cards_the_count_is_made_of(self):
        got = self.items(deck("Pulse", "Disenchant 1", "Wrath Mock", "Bear"))
        self.assertEqual(got["answers_enchantments"]["cards"], ["Pulse", "Disenchant 1"])
        self.assertEqual(got["answers_creatures"]["cards"], ["Wrath Mock"])

    def test_the_counts_are_the_ones_calibrate_measures_for_a_deck(self):
        # calibrate counts with roles.answer_counts over the same names; the item values must be exactly those
        names = ["Pulse", "Disenchant 1", "Disenchant 2", "Wrath Mock", "Counter Magic", "Bear"]
        counted = roles.answer_counts(names, self.world.attrs())
        got = self.items(deck(*names))
        for id_ in roles.THREAT_IDS:
            self.assertEqual(got[id_]["value"], counted[id_], id_)
        self.assertEqual(sum(counted.values()), 7)       # Pulse 3 + two Disenchants 2 + Wrath Mock 1 + Counter Magic 1

    def test_a_card_listed_twice_counts_once_as_it_does_in_calibrate(self):
        names = ["Pulse", "Pulse", "Bear"]
        self.assertEqual(self.items(deck(("Pulse", 2), "Bear"))["answers_artifacts"]["value"],
                         roles.answer_counts(names, self.world.attrs())["answers_artifacts"])
        self.assertEqual(self.items(deck(("Pulse", 2), "Bear"))["answers_artifacts"]["value"], 1)


class ThreatTableTests(unittest.TestCase):
    def test_the_threat_table_lives_in_roles_and_metrics_keeps_the_name_for_serve_and_the_tests(self):
        self.assertIs(metrics.THREATS, roles.THREATS)

    def test_metrics_targets_is_the_roles_reader_so_the_file_is_read_in_one_place(self):
        with mock.patch.object(roles, "metric_targets", return_value={"x": {"min": 1}}) as reader:
            self.assertEqual(metrics.targets(4), {"x": {"min": 1}})
        reader.assert_called_once_with(4)
        self.assertFalse(hasattr(metrics, "TARGETS_PATH"))      # the path moved with the reader: a stale patch fails


# ----------------------------------------------------------------------------- group: mana and consistency
class ManaGroupTests(MetricsCase):
    """One deck of 17 lands and 12 spells, every number worked out below."""

    def setUp(self):
        super().setUp()
        w = self.world
        both = ["B", "G"]
        w.add("Temple Bog", "Land", 0, produced=both, ci="BG", attrs=["tapland"])
        w.add("Check Fen", "Land", 0, produced=both, ci="BG", attrs=["conditional-tapland"])
        w.add("Shock Mire", "Land", 0, produced=both, ci="BG", attrs=["tapland", "conditional-tapland"])
        w.add("Dual Land", "Land", 0, produced=both, ci="BG")
        w.add("Evolving Wilds", "Land", 0, text="{T}, Sacrifice Evolving Wilds: Search your library for a basic land "
              "card, put it onto the battlefield tapped, then shuffle.")
        w.add("Verdant Fetch", "Land", 0, text="{T}, Pay 1 life, Sacrifice Verdant Fetch: Search your library for a "
              "Swamp or Forest card, put it onto the battlefield, then shuffle.")
        w.add("Ancient Tomb", "Land", 0, produced=["C"], text="{T}: Add {C}{C}. Ancient Tomb deals 2 damage to you.",
              roles=["ramp"])
        w.add("Quiet Waste", "Land", 0, produced=["C"], text="{T}: Add {C}.")
        w.add("Urza's Mock", "Land", 0, produced=["C"], text="{T}: Add {C}. {2}, {T}, Sacrifice Urza's Mock: Search "
              "your library for an artifact card, put it onto the battlefield, then shuffle.")
        w.add("Mind Rock", "Artifact", 2, "{2}", roles=["ramp"], attrs=["mana-rock"])
        w.add("Elf Dork", "Creature", 1, "{G}", roles=["ramp"], attrs=["mana-dork"])
        w.add("Land Fetch Spell", "Sorcery", 3, "{2}{G}", roles=["ramp"], attrs=["land-ramp"],
              text="Search your library for up to two basic land cards, put them onto the battlefield tapped.")
        w.add("Odd Ramp", "Artifact", 3, "{3}", roles=["ramp"])
        w.add("Draw Engine", "Enchantment", 3, "{2}{B}", roles=["draw"], attrs=["draw-engine"])
        w.add("Repeat Impulse", "Creature", 2, "{1}{G}", roles=["draw"], attrs=["repeatable-impulsive-draw"])
        w.add("Pure Draw", "Sorcery", 3, "{2}{G}", roles=["draw"], attrs=["pure-draw"])
        w.add("Burst Draw", "Sorcery", 5, "{3}{B}{B}", roles=["draw"], attrs=["burst-draw"])
        w.add("Engine And Pure", "Enchantment", 4, "{2}{B}{G}", roles=["draw"], attrs=["draw-engine", "pure-draw"])
        w.add("Odd Draw", "Sorcery", 2, "{1}{B}", roles=["draw"])
        w.add("Titan A", "Creature", 7, "{5}{B}{G}")
        w.add("Titan B", "Creature", 6, "{4}{B}{G}")
        self.cards = deck(("Forest", 5), ("Swamp", 3), "Temple Bog", "Check Fen", "Shock Mire", "Dual Land",
                          "Evolving Wilds", "Verdant Fetch", "Ancient Tomb", "Quiet Waste", "Urza's Mock",
                          "Mind Rock", "Elf Dork", "Land Fetch Spell", "Odd Ramp", "Draw Engine", "Repeat Impulse",
                          "Pure Draw", "Burst Draw", "Engine And Pure", "Odd Draw", "Titan A", "Titan B")
        self.got = self.items(self.cards)

    def test_lands_are_the_land_count_against_the_land_band_and_list_the_nonbasic_ones(self):
        got = self.got["lands"]
        self.assertEqual((got["value"], got["target"], got["status"]), (17, {"min": 16, "target": 17, "max": 18}, "inside"))
        self.assertEqual(got["why"], ["17 lands, 8 of them basic."])
        self.assertEqual(len(got["cards"]), 9)
        self.assertNotIn("Forest", got["cards"])

    def test_ramp_and_draw_are_role_counts_against_their_bands(self):
        # ramp: Ancient Tomb (a land that makes extra mana), Mind Rock, Elf Dork, Land Fetch Spell, Odd Ramp = 5
        self.assertEqual((self.got["ramp"]["value"], self.got["ramp"]["status"]), (5, "over"))
        self.assertEqual(self.got["draw"]["value"], 6)
        self.assertEqual(self.got["draw"]["status"], "over")

    def test_ramp_is_split_into_rocks_creatures_and_land_ramp(self):
        self.assertEqual((self.got["ramp_rocks"]["value"], self.got["ramp_rocks"]["cards"]), (1, ["Mind Rock"]))
        self.assertEqual((self.got["ramp_creatures"]["value"], self.got["ramp_creatures"]["cards"]), (1, ["Elf Dork"]))
        self.assertEqual((self.got["ramp_lands"]["value"], self.got["ramp_lands"]["cards"]), (1, ["Land Fetch Spell"]))

    def test_draw_is_split_into_engines_and_one_shot_and_a_card_is_in_one_of_them(self):
        self.assertEqual(self.got["draw_engines"]["cards"], ["Draw Engine", "Repeat Impulse", "Engine And Pure"])
        self.assertEqual(self.got["draw_one_shot"]["cards"], ["Pure Draw", "Burst Draw"])      # Engine And Pure is an engine

    def test_the_curve_counts_nonland_cards_at_each_mana_value(self):
        # mana values: Mind Rock 2, Elf Dork 1, Land Fetch Spell 3, Odd Ramp 3, Draw Engine 3, Repeat Impulse 2,
        # Pure Draw 3, Burst Draw 5, Engine And Pure 4, Odd Draw 2, Titan A 7, Titan B 6
        counts = [self.got[f"curve_{n}"]["value"] for n in range(8)]
        self.assertEqual(counts, [0, 1, 3, 4, 1, 1, 1, 1])
        self.assertEqual(sum(counts), 12)
        self.assertEqual(self.got["curve_2"]["cards"], ["Mind Rock", "Repeat Impulse", "Odd Draw"])
        self.assertEqual(self.got["curve_7"]["label"], "Cards with mana value 7 or more")
        self.assertEqual(self.got["curve_1"]["label"], "Cards with mana value 1")

    def test_a_mana_value_of_eight_or_more_goes_in_the_last_step(self):
        self.world.add("Eldrazi", "Creature", 11, "{9}{B}{G}")
        got = self.items(self.cards + deck("Eldrazi"))
        self.assertEqual(got["curve_7"]["value"], 2)

    def test_the_average_mana_value_is_over_the_nonland_cards(self):
        # (2+1+3+3+3+2+3+5+4+2+7+6) / 12 = 41 / 12 = 3.4167
        self.assertEqual(self.got["avg_mana_value"]["value"], 3.42)

    def test_a_deck_of_lands_only_has_no_average(self):
        self.assertIsNone(self.items(deck(("Forest", 3)))["avg_mana_value"]["value"])

    def test_color_sources_are_the_lands_that_make_the_color_against_the_colored_symbols(self):
        # green sources: 5 Forest + Temple Bog, Check Fen, Shock Mire, Dual Land = 9. Green symbols: Elf Dork 1, Land
        # Fetch Spell 1, Repeat Impulse 1, Pure Draw 1, Engine And Pure 1, Titan A 1, Titan B 1 = 7.
        # Black sources: 3 Swamp + the same 4 = 7. Black symbols: Draw Engine 1, Burst Draw 2, Engine And Pure 1,
        # Odd Draw 1, Titan A 1, Titan B 1 = 7
        self.assertEqual(self.got["sources_green"]["value"], 9)
        self.assertEqual(self.got["sources_black"]["value"], 7)
        self.assertEqual(self.got["sources_green"]["why"], [
            "9 lands make green mana for 7 green mana symbols in the nonland cards (1.29 lands for each symbol)."])
        self.assertEqual(self.got["sources_black"]["label"], "Black sources")
        self.assertNotIn("sources_red", self.got)                 # only the commander's colors

    def test_a_color_no_card_needs_says_so(self):
        got = self.items(deck(("Forest", 2), ("Swamp", 2)))
        self.assertEqual(got["sources_green"]["why"], ["2 lands make green mana; no nonland card needs it."])

    def test_a_colorless_commander_has_no_color_items(self):
        got = self.items(deck(("Forest", 2)), ctx=self.world.ctx(ci=""))
        self.assertFalse([k for k in got if k.startswith("sources_")])

    def test_basics_are_held_against_what_the_land_searchers_can_take(self):
        # Land Fetch Spell takes 2 basic lands and Evolving Wilds 1: 3. Verdant Fetch looks for land types, not
        # basics, and counts none. The deck has two colors. It needs max(2, 3) = 3 and has 8.
        got = self.got["basics"]
        self.assertEqual((got["value"], got["target"], got["status"]), (8, {"min": 3, "target": None, "max": None},
                                                                       "inside"))
        self.assertEqual(got["cards"], ["Evolving Wilds", "Land Fetch Spell"])
        self.assertIn("take 3 basic lands (Evolving Wilds 1, Land Fetch Spell 2)", got["why"][0])

    def test_too_few_basics_for_the_searchers_is_short(self):
        got = self.items(deck("Forest", "Swamp", "Evolving Wilds", "Land Fetch Spell"))["basics"]
        self.assertEqual((got["value"], got["target"]["min"], got["status"]), (2, 3, "short"))

    def test_one_basic_for_each_color_is_the_least_even_with_no_searchers(self):
        self.world.add("Bear", "Creature", 2)
        got = self.items(deck("Forest", "Bear"))["basics"]
        self.assertEqual((got["value"], got["target"]["min"], got["status"]), (1, 2, "short"))

    def test_lands_that_enter_tapped_always_and_sometimes_are_two_items(self):
        # Temple Bog is tagged tapland. Check Fen is conditional-tapland. Shock Mire carries both tags and counts as
        # "sometimes": a land that can enter untapped is not always tapped
        self.assertEqual(self.got["tapped_always"]["cards"], ["Temple Bog"])
        self.assertEqual(self.got["tapped_sometimes"]["cards"], ["Check Fen", "Shock Mire"])
        self.assertEqual((self.got["tapped_always"]["value"], self.got["tapped_sometimes"]["value"]), (1, 2))

    def test_a_nonland_card_with_the_tapland_tag_is_not_a_tapped_land(self):
        self.world.add("Tapped Spell", "Artifact", 2, attrs=["tapland"])
        self.assertNotIn("Tapped Spell", self.items(self.cards + deck("Tapped Spell"))["tapped_always"]["cards"])

    def test_lands_that_make_only_colorless_mana_leave_out_the_lands_that_fetch_a_land(self):
        # Ancient Tomb, Quiet Waste and Urza's Mock make only {C}. Urza's Mock searches for an artifact, not a land,
        # so it stays. Evolving Wilds and Verdant Fetch make no mana but find lands that do, so they go.
        self.assertEqual(self.got["colorless_lands"]["cards"], ["Ancient Tomb", "Quiet Waste", "Urza's Mock"])
        self.assertEqual(self.got["colorless_lands"]["value"], 3)

    def test_cards_costing_6_or_more_are_held_against_the_limit(self):
        got = self.got["topend"]
        self.assertEqual((got["value"], got["target"], got["status"]), (2, {"min": None, "target": None, "max": 1},
                                                                       "over"))
        self.assertEqual(got["cards"], ["Titan A", "Titan B"])

    def test_without_tag_data_the_tag_items_have_no_value_and_the_others_still_do(self):
        got = self.items(self.cards, attrs=False)
        for key in ("ramp_rocks", "draw_engines", "tapped_always", "tapped_sometimes"):
            self.assertEqual((got[key]["value"], got[key]["status"]), (None, None), key)
        self.assertEqual((got["lands"]["value"], got["colorless_lands"]["value"], got["avg_mana_value"]["value"]),
                         (17, 3, 3.42))


# ----------------------------------------------------------------------------- group: playstyle
class PlaystyleGroupTests(MetricsCase):
    def setUp(self):
        super().setUp()
        w = self.world
        w.add("Outlet", "Artifact", 2, attrs=["sacrifice-outlet"], score=0.4, theme=0.2)
        w.add("Free Outlet", "Creature", 2, attrs=["sacrifice-outlet", "free-sacrifice-outlet"], score=0.4, theme=0.03)
        w.add("Death Watcher", "Creature", 3, attrs=["death-trigger"], score=0.3, theme=0.01)
        w.add("Outlet And Trigger", "Creature", 3, attrs=["sacrifice-outlet", "death-trigger"], score=0.3)
        w.add("Token Maker", "Enchantment", 3, attrs=["repeatable-token-generator"], score=0.3, theme=-0.2)
        w.add("Zap", "Instant", 1)
        w.add("Study", "Sorcery", 2)
        w.add("Big Spell", "Sorcery", 6, "{5}{G}")
        w.add("Mana Rock", "Artifact", 2, roles=["ramp"], attrs=["mana-rock"])

    def test_every_playstyle_in_the_file_has_a_mapping_and_every_mapping_a_playstyle(self):
        slugs = {p["slug"] for p in fantasy.menu()["playstyles"]}
        self.assertEqual(set(metrics.PLAYSTYLE_SIGNALS), slugs)
        self.assertEqual(len(slugs), 12)

    def test_every_signal_names_a_real_tag_role_or_type(self):
        types = {"Instant", "Sorcery", "Creature", "Artifact", "Enchantment", "Land", "Planeswalker"}
        for slug, (meaning, signals) in metrics.PLAYSTYLE_SIGNALS.items():
            self.assertTrue(meaning, slug)
            self.assertTrue(signals, slug)
            for kind, key, weight in signals:
                with self.subTest(playstyle=slug, kind=kind, key=key):
                    if kind == "tag":
                        self.assertIn(key, roles.ATTRIBUTE_TAGS)
                    elif kind == "role":
                        self.assertIn(key, roles.ROLES)
                    elif kind == "type":
                        self.assertIn(key, types)
                    else:
                        self.assertEqual(kind, "cost")
                        self.assertIsInstance(key, (int, float))
                    self.assertGreater(weight, 0)

    def test_aristocrats_counts_outlets_and_death_triggers_with_a_free_outlet_at_1_5(self):
        names = ["Outlet", "Free Outlet", "Death Watcher", "Outlet And Trigger", "Zap", "Study"]
        got = self.items(deck(*names, ("Forest", 4)))["style_aristocrats"]
        # nonland cards: 6. Outlet 1.0, Free Outlet 1.5 (its best signal), Death Watcher 1.0, Outlet And Trigger 1.0
        # (it matches two signals but counts once), Zap 0, Study 0 = 4.5 / 6 = 75.0%
        self.assertEqual((got["value"], got["unit"]), (75.0, "%"))
        self.assertEqual(got["cards"], ["Outlet", "Free Outlet", "Death Watcher", "Outlet And Trigger"])
        self.assertEqual(got["label"], "Aristocrats")

    def test_go_wide_counts_cards_that_keep_making_tokens(self):
        got = self.items(deck("Token Maker", "Zap", "Study", "Outlet"))["style_go_wide"]
        self.assertEqual((got["value"], got["cards"]), (25.0, ["Token Maker"]))             # 1 of 4

    def test_spellslinger_counts_instants_and_sorceries_by_type(self):
        got = self.items(deck("Zap", "Study", "Outlet", "Death Watcher"))["style_spellslinger"]
        self.assertEqual((got["value"], got["cards"]), (50.0, ["Zap", "Study"]))

    def test_control_counts_removal_wipes_and_counterspells_by_role(self):
        self.world.role_of["Zap"] = {"removal"}
        self.world.role_of["Study"] = {"counter", "draw"}
        got = self.items(deck("Zap", "Study", "Outlet", "Death Watcher"))["style_control"]
        self.assertEqual((got["value"], got["cards"]), (50.0, ["Zap", "Study"]))

    def test_big_mana_counts_ramp_and_cards_costing_6_or_more(self):
        got = self.items(deck("Mana Rock", "Big Spell", "Zap", "Study"))["style_big_mana"]
        self.assertEqual((got["value"], got["cards"]), (50.0, ["Mana Rock", "Big Spell"]))

    def test_the_chosen_playstyle_says_so(self):
        got = self.items(deck("Outlet"), ctx=self.world.ctx(spec={"playstyle": "aristocrats", "bracket": 3}))
        self.assertIn("This is the playstyle you chose.", got["style_aristocrats"]["why"])
        self.assertNotIn("This is the playstyle you chose.", got["style_voltron"]["why"])

    def test_there_is_one_item_per_playstyle_in_the_files_order(self):
        got = self.compute(deck("Outlet"))
        ids = [i["id"] for g in got["groups"] if g["id"] == "playstyle" for i in g["items"]]
        self.assertEqual(ids[1:13], ["style_" + p["slug"].replace("-", "_") for p in fantasy.menu()["playstyles"]])

    def test_a_deck_of_lands_only_has_no_densities(self):
        got = self.items(deck(("Forest", 3)))
        self.assertIsNone(got["style_aristocrats"]["value"])

    def test_without_tag_data_only_the_playstyles_that_need_tags_lose_their_number(self):
        got = self.items(deck("Outlet", "Zap", "Study"), attrs=False)
        self.assertIsNone(got["style_aristocrats"]["value"])
        self.assertEqual(got["style_spellslinger"]["value"], 66.7)                          # types only
        self.assertEqual(got["style_control"]["value"], 0.0)                                # roles only

    def test_theme_fit_is_the_share_of_nonland_cards_with_a_theme_score_above_the_show_line(self):
        # theme scores: Outlet 0.2 and Free Outlet 0.03 are above SHOW_PULL (0.02); Death Watcher 0.01 and Token Maker
        # -0.2 are not; Outlet And Trigger has none. 2 of 5 = 40.0%
        ctx = self.world.ctx(evidence={"theme_weights": {"sacrifice": 1.0, "tokens": 0.5}, "cards": {}, "salt": {}})
        names = ["Outlet", "Free Outlet", "Death Watcher", "Outlet And Trigger", "Token Maker"]
        got = self.items(deck(*names, ("Forest", 3)), ctx=ctx)["theme_fit"]
        self.assertEqual((got["value"], got["unit"], got["cards"]), (40.0, "%", ["Outlet", "Free Outlet"]))
        self.assertIn("2 of 5 nonland cards", got["why"][0])
        self.assertEqual(score.SHOW_PULL, 0.02)

    def test_theme_fit_needs_a_theme_or_a_playstyle(self):
        got = self.items(deck("Outlet"))["theme_fit"]
        self.assertEqual((got["value"], got["status"]), (None, None))
        self.assertIn("No theme or playstyle was chosen", got["why"][0])

    def test_synergy_is_the_mean_edhrec_synergy_of_the_nonland_cards_that_have_one(self):
        cards = {"Outlet": {"all": {"decks": 5, "of": 10, "synergy": 0.5}, "at": None, "themes": {}},
                 "Free Outlet": {"all": {"decks": 5, "of": 10, "synergy": 0.1},
                                 "at": {"decks": 6, "of": 10, "synergy": 0.3}, "themes": {}},     # the bracket's own wins
                 "Death Watcher": {"all": {"decks": 5, "of": 10, "synergy": None}, "at": None, "themes": {}},
                 "Forest": {"all": {"decks": 9, "of": 10, "synergy": 0.9}, "at": None, "themes": {}}}
        ctx = self.world.ctx(evidence={"theme_weights": {}, "cards": cards, "salt": {}})
        got = self.items(deck("Outlet", "Free Outlet", "Death Watcher", "Forest"), ctx=ctx)["synergy"]
        # (0.5 + 0.3) / 2 = 0.4: Free Outlet's bracket page (0.3) beats its all-bracket page (0.1); Death Watcher has no
        # number; a land is not a nonland card
        self.assertEqual((got["value"], got["unit"]), (40.0, "%"))
        self.assertEqual(got["cards"], ["Outlet", "Free Outlet"])
        self.assertIn("over 2 nonland cards", got["why"][0])

    def test_no_synergy_anywhere_means_no_number(self):
        got = self.items(deck("Outlet"))["synergy"]
        self.assertEqual(got["value"], None)
        self.assertIn("EDHREC", got["why"][0])

    def test_creatures_are_counted_by_the_creature_type(self):
        got = self.items(deck("Free Outlet", "Death Watcher", "Zap", ("Forest", 2)))["creatures"]
        self.assertEqual((got["value"], got["cards"]), (2, ["Free Outlet", "Death Watcher"]))


# ----------------------------------------------------------------------------- group: win plan
class WinGroupTests(MetricsCase):
    def setUp(self):
        super().setUp()
        w = self.world
        w.add("Overrun Mock", "Creature", 6, "{4}{G}{G}", roles=["finisher"], attrs=["overrun"])
        w.add("Drain Mock", "Creature", 4, roles=["finisher"], attrs=["drain-life"])
        w.add("Burn Each", "Sorcery", 3, roles=["finisher"], attrs=["burn-player-each"])
        w.add("Life Loss", "Sorcery", 2, roles=["finisher"], attrs=["opponent-loses-life"])
        w.add("Extra Combat", "Enchantment", 4, roles=["finisher"], attrs=["extra-combat-phase"])
        w.add("Win Con", "Enchantment", 7, roles=["finisher"], attrs=["alternate-win-condition"])
        w.add("Thief", "Sorcery", 8, roles=["finisher"], attrs=["theft-mass"])
        w.add("Flyer One", "Creature", 3, attrs=["evasion"], power="2")
        w.add("Flyer Two", "Creature", 4, attrs=["evasion"], power="3")
        w.add("Star Flyer", "Creature", 4, attrs=["evasion"], power="*")
        w.add("Wing Aura", "Enchantment — Aura", 2, attrs=["evasion"])
        w.add("Walker", "Creature", 2)
        self.cards = deck("Overrun Mock", "Drain Mock", "Burn Each", "Life Loss", "Extra Combat", "Win Con", "Thief",
                          "Flyer One", "Flyer Two", "Star Flyer", "Wing Aura", "Walker")

    def test_finishers_are_the_role_count_against_the_band(self):
        got = self.items(self.cards)["finishers"]
        self.assertEqual((got["value"], got["status"]), (7, "over"))              # band 1-3

    def test_finishers_by_kind(self):
        got = self.items(self.cards)
        self.assertEqual(got["finishers_overrun"]["cards"], ["Overrun Mock"])
        self.assertEqual(got["finishers_drain"]["cards"], ["Drain Mock", "Burn Each", "Life Loss"])
        self.assertEqual(got["finishers_extra_combat"]["cards"], ["Extra Combat"])
        self.assertEqual(got["finishers_alt_win"]["cards"], ["Win Con"])
        self.assertEqual(got["finishers_theft"]["cards"], ["Thief"])
        self.assertEqual([got[k]["value"] for k in ("finishers_overrun", "finishers_drain", "finishers_extra_combat",
                                                    "finishers_alt_win", "finishers_theft")], [1, 3, 1, 1, 1])

    def test_a_kind_with_no_card_is_zero(self):
        self.assertEqual(self.items(deck("Walker"))["finishers_theft"]["value"], 0)

    def test_creatures_that_are_hard_to_block_are_creatures_with_the_evasion_tag(self):
        got = self.items(self.cards)["evasive_creatures"]
        self.assertEqual((got["value"], got["cards"]), (3, ["Flyer One", "Flyer Two", "Star Flyer"]))   # not the Aura

    def test_their_total_power_adds_the_numbers_and_leaves_out_a_power_that_varies(self):
        got = self.items(self.cards)["evasive_power"]
        self.assertEqual(got["value"], 5)                                          # 2 + 3
        self.assertEqual(got["why"], ["Flyer One 2", "Flyer Two 3", "Power that varies is left out: Star Flyer."])

    def test_when_every_power_varies_the_total_is_zero_and_says_which_were_left_out(self):
        # the card index records power for every creature ("*" when it varies), so nothing is unknown, only left out
        self.world.power_of.clear()
        got = self.items(self.cards)["evasive_power"]
        self.assertEqual((got["value"], got["why"]),
                         (0, ["Power that varies is left out: Flyer One, Flyer Two, Star Flyer."]))

    def test_no_hard_to_block_creature_is_a_total_power_of_zero_whatever_the_index_records(self):
        self.world.power_of.clear()
        self.assertEqual(self.items(deck("Walker"))["evasive_power"]["value"], 0)

    def test_combos_that_win_are_the_complete_combos_with_a_game_ending_result(self):
        wins = combo(["Drain Mock", "Walker"], ["Infinite damage"], variant_id="1-2")
        loop = combo(["Flyer One", "Flyer Two"], ["Infinite creature ETB"], variant_id="3-4")
        got = self.items(self.cards, combos={"included": [wins, loop], "almost": []})["combos_win"]
        self.assertEqual((got["value"], got["cards"]), (1, ["Drain Mock", "Walker"]))
        self.assertIn("Infinite damage", got["why"][0])

    def test_no_winning_combo_says_so_and_unchecked_combos_have_no_number(self):
        none = self.items(self.cards)["combos_win"]
        self.assertEqual((none["value"], none["why"]), (0, ["No complete combo ends the game by itself."]))
        unknown = self.items(self.cards, combos=None)["combos_win"]
        self.assertEqual((unknown["value"], unknown["why"]), (None, [metrics.NO_COMBOS]))

    def test_the_rule_for_a_combo_that_wins_on_real_result_names(self):
        # names from the 2026-10-11 file; True means the combo ends the game for the opponents
        cases = [
            ("Win the game", True), ("Win the game at the beginning of your next upkeep", True),
            ("Target opponent loses the game", True), ("Each opponent loses the game", True),
            ("Target player loses the game on each of your turns", True), ("Up to three target opponents lose the game", True),
            ("Each opponent with an even life total loses the game", True),
            ("Infinite damage", True), ("Infinite damage to one opponent", True), ("Infinite combat damage", True),
            ("Near-infinite damage", True), ("Near-infinite damage to all players", True),
            ("Infinite lifeloss", True), ("Infinite lifeloss for target opponent", True),
            ("Near-infinite lifeloss for all players", True),
            ("Infinite damage to creatures", False), ("Infinite damage to all creatures", False),
            ("Infinite damage to some creatures", False), ("Near-infinite damage to creatures", False),
            ("You can't lose the game due to having 0 or less life", False),
            ("You are unable to lose the game due to damage or lifeloss", False),
            ("Infinite lifegain", False), ("Infinite lifegain triggers", False), ("Infinite mill", False),
            ("Infinite turns", False), ("Infinite creature ETB", False), ("Infinite colored mana", False),
            ("Lock", False), ("Infinite storm count", False),
        ]
        for result, expected in cases:
            with self.subTest(result=result):
                self.assertEqual(metrics.ends_the_game(combo(["A", "B"], [result])), expected)

    def test_one_winning_result_among_others_is_enough(self):
        self.assertTrue(metrics.ends_the_game(combo(["A", "B"], ["Infinite mana", "Infinite damage"])))
        self.assertFalse(metrics.ends_the_game(combo(["A", "B"], [])))

    def test_without_tag_data_the_tag_items_have_no_value(self):
        got = self.items(self.cards, attrs=False)
        for key in ("finishers_overrun", "evasive_creatures", "evasive_power"):
            self.assertEqual(got[key]["value"], None, key)
        self.assertEqual(got["finishers"]["value"], 7)


# ----------------------------------------------------------------------------- group: table and money
class TableGroupTests(MetricsCase):
    def setUp(self):
        super().setUp()
        w = self.world
        w.add("Pricey", "Artifact", 2, price=10.0)
        w.add("Cheap", "Creature", 2, price=2.5)
        w.add("Owned Card", "Creature", 2, price=7.0)
        w.add("Unknown Price", "Creature", 2, price=None)
        w.add("Salty", "Enchantment", 3, price=1.0)
        w.add("Salter", "Enchantment", 3, price=1.0)
        w.add("Saltiest", "Enchantment", 3, price=1.0)
        w.add("Mild", "Enchantment", 3, price=1.0)
        w.add("Time Warp", "Sorcery", 5, "{3}{U}{U}", ci="U")
        w.add("Armageddon", "Sorcery", 4, "{3}{W}", ci="W")
        w.add("Crypt", "Artifact", 1, gc=True)

    def test_salt_is_the_total_and_the_three_saltiest_cards(self):
        salt = {"Salty": 1.5, "Salter": 2.0, "Saltiest": 3.0, "Mild": 0.5, "Not In The Deck": 4.0}
        ctx = self.world.ctx(evidence={"theme_weights": {}, "cards": {}, "salt": salt})
        got = self.items(deck("Salty", "Salter", "Saltiest", "Mild", "Cheap"), ctx=ctx)["salt"]
        self.assertEqual(got["value"], 7.0)                                         # 1.5 + 2.0 + 3.0 + 0.5
        self.assertEqual(got["cards"], ["Saltiest", "Salter", "Salty"])
        self.assertEqual(got["why"], ["Saltiest 3.0", "Salter 2.0", "Salty 1.5"])

    def test_no_card_on_the_salt_list_is_zero_and_says_so(self):
        ctx = self.world.ctx(evidence={"theme_weights": {}, "cards": {}, "salt": {"Elsewhere": 3.0}})
        got = self.items(deck("Cheap"), ctx=ctx)["salt"]
        self.assertEqual((got["value"], got["why"]), (0, ["No card in the deck is on EDHREC's salt list."]))

    def test_without_salt_data_there_is_no_number(self):
        got = self.items(deck("Cheap"))["salt"]
        self.assertEqual(got["value"], None)
        self.assertIn("Brackets 1-3", got["why"][0])

    def test_the_brackets_limits_are_counts_against_the_brackets_allowance(self):
        got = self.items(deck("Crypt", "Time Warp", "Cheap"))
        self.assertEqual((got["limit_game_changers"]["value"], got["limit_game_changers"]["target"]["max"],
                          got["limit_game_changers"]["status"]), (1, 3, "inside"))
        self.assertEqual((got["limit_extra_turns"]["value"], got["limit_extra_turns"]["target"]["max"],
                          got["limit_extra_turns"]["status"]), (1, 1, "inside"))
        self.assertEqual((got["limit_mass_land_denial"]["value"], got["limit_mass_land_denial"]["target"]["max"]),
                         (0, 0))
        self.assertEqual(got["limit_extra_turns"]["cards"], ["Time Warp"])

    def test_a_limit_that_is_broken_is_over_and_says_which_card(self):
        got = self.items(deck("Armageddon", "Time Warp"))
        self.assertEqual((got["limit_mass_land_denial"]["value"], got["limit_mass_land_denial"]["status"]), (1, "over"))
        self.assertIn("Armageddon", got["limit_mass_land_denial"]["why"][0])
        self.assertEqual(got["limit_mass_land_denial"]["cards"], ["Armageddon"])

    def test_two_extra_turn_cards_are_chaining_at_bracket_3(self):
        self.world.add("Walk the Aeons", "Sorcery", 6, ci="U")
        got = self.items(deck("Time Warp", "Walk the Aeons"))["limit_extra_turns"]
        self.assertEqual((got["value"], got["status"]), (2, "over"))

    def test_a_bracket_that_allows_everything_has_no_ceiling(self):
        got = self.items(deck("Armageddon", "Time Warp", "Crypt"), ctx=self.world.ctx(bracket=5))
        self.assertEqual([got[k]["target"]["max"] for k in ("limit_game_changers", "limit_extra_turns",
                                                           "limit_mass_land_denial")], [None, None, None])
        self.assertEqual(got["limit_mass_land_denial"]["status"], "inside")

    def test_bracket_1_allows_no_extra_turns_at_all(self):
        got = self.items(deck("Time Warp"), ctx=self.world.ctx(bracket=1))["limit_extra_turns"]
        self.assertEqual((got["target"]["max"], got["status"]), (0, "over"))

    def test_two_card_combos_over_the_limit_make_the_item_over(self):
        banned = combo(["Cheap", "Pricey"], ["Infinite mana"], tag="R")                   # a two-card combo for Bracket 4
        fine = combo(["Cheap", "Owned Card"], ["Infinite mana"], tag="E")
        got = self.items(deck("Cheap", "Pricey", "Owned Card"), combos={"included": [banned, fine], "almost": []})
        item = got["limit_two_card_combos"]
        self.assertEqual((item["value"], item["status"]), (2, "over"))
        self.assertEqual(item["cards"], ["Cheap", "Pricey", "Owned Card"])
        self.assertIn("Bracket 4", item["why"][0])
        ok = self.items(deck("Cheap", "Owned Card"), combos={"included": [fine], "almost": []})["limit_two_card_combos"]
        self.assertEqual((ok["value"], ok["status"]), (1, "inside"))

    def test_two_card_combos_not_checked_have_no_number(self):
        got = self.items(deck("Cheap"), combos=None)["limit_two_card_combos"]
        self.assertEqual((got["value"], got["status"]), (None, None))

    # --- money
    def money(self, cards, **kw):
        got = self.items(cards, **kw)
        return got["price_total"], got["price_to_buy"], got["owned_share"]

    def test_total_price_is_every_card_at_its_price_with_basic_lands_free(self):
        total, to_buy, share = self.money(deck("Pricey", "Cheap", ("Forest", 4)))
        # the commander 5.00 + Pricey 10.00 + Cheap 2.50 = 17.50; four Forests are free
        self.assertEqual((total["value"], total["unit"]), (17.5, "$"))
        self.assertEqual(to_buy["value"], 17.5)

    def test_owned_cards_are_in_the_total_but_cost_nothing_to_buy(self):
        total, to_buy, share = self.money(deck("Pricey", "Cheap", "Owned Card", ("Forest", 2)), owned=["Owned Card"])
        self.assertEqual((total["value"], to_buy["value"]), (24.5, 17.5))           # 5 + 10 + 2.5 + 7; 7 is owned
        # cards: the commander, Pricey, Cheap, Owned Card and two Forests = 6. Owned: Owned Card and the two Forests
        self.assertEqual((share["value"], share["unit"]), (50.0, "%"))
        self.assertEqual(share["why"], ["3 of 6 cards, the commander included; basic lands count as owned."])

    def test_the_commander_can_be_owned_too(self):
        total, to_buy, _ = self.money(deck("Pricey"), owned=[CMDR])
        self.assertEqual((total["value"], to_buy["value"]), (15.0, 10.0))

    def test_owned_names_are_matched_in_any_spelling(self):
        _, to_buy, _ = self.money(deck("Pricey"), owned=["pricey"])
        self.assertEqual(to_buy["value"], 5.0)                                       # only the commander is left to buy

    def test_a_price_passed_in_replaces_the_card_indexs_price(self):
        total, to_buy, _ = self.money(deck("Pricey", "Cheap"), prices={"Pricey": 12.0, "Cheap": 0.5})
        self.assertEqual((total["value"], to_buy["value"]), (17.5, 17.5))            # 5 + 12 + 0.5

    def test_a_card_with_no_price_is_named_and_counted_as_nothing(self):
        total, to_buy, _ = self.money(deck("Pricey", "Unknown Price"))
        self.assertEqual((total["value"], to_buy["value"]), (15.0, 15.0))
        self.assertIn("1 cards have no price and count as $0: Unknown Price", total["why"][1])

    def test_the_priciest_cards_to_buy_are_listed_first(self):
        _, to_buy, _ = self.money(deck("Cheap", "Pricey", "Owned Card"), owned=["Owned Card"])
        self.assertEqual(to_buy["cards"], ["Pricey", CMDR, "Cheap"])
        self.assertEqual(to_buy["why"], ["Pricey $10.00", f"{CMDR} $5.00", "Cheap $2.50"])


# ----------------------------------------------------------------------------- group: changes and before -> after
LOG = [
    {"n": 1, "at": "2026-10-11T20:05:00Z", "op": "swap", "cut": "Forest", "add": "Pricey", "source": "suggested"},
    {"n": 2, "at": "2026-10-11T20:06:00Z", "op": "cut", "cut": "Swamp", "source": "manual"},
    {"n": 3, "at": "2026-10-11T20:07:00Z", "op": "add", "add": "Cheap", "source": "manual"},
    {"n": 4, "at": "2026-10-11T20:08:00Z", "op": "group", "label": "Up to $25", "source": "suggested",
     "items": [{"op": "swap", "cut": "Forest", "add": "Elf Dork"}, {"op": "swap", "cut": "Forest", "add": "Mind Rock"}]},
    {"n": 5, "at": "2026-10-11T20:09:00Z", "op": "undo", "of": 3},
]


class ChangesTests(MetricsCase):
    def setUp(self):
        super().setUp()
        w = self.world
        w.add("Pricey", "Artifact", 2, price=10.0)
        w.add("Cheap", "Creature", 2, price=2.5)
        w.add("Elf Dork", "Creature", 1, price=1.0)
        w.add("Mind Rock", "Artifact", 2, price=1.0)
        w.add("Old Card", "Creature", 2, price=4.0)
        self.db = w.db()

    def net(self, log):
        added, cut = metrics.net_changes(log, self.db)
        return {k: len(v) for k, v in added.items()}, {k: len(v) for k, v in cut.items()}

    def test_the_log_is_replayed_skipping_what_was_undone_and_opening_groups(self):
        added, cut = self.net(LOG)
        # swap 1: Forest out, Pricey in. Cut 2: Swamp. Add 3 (undone by 5). Group 4: two Forests out, Elf Dork and
        # Mind Rock in
        self.assertEqual(added, {"Pricey": 1, "Elf Dork": 1, "Mind Rock": 1})
        self.assertEqual(cut, {"Forest": 3, "Swamp": 1})

    def test_a_card_added_and_then_cut_cancels_out_and_so_does_cut_and_then_added(self):
        log = [{"n": 1, "op": "add", "add": "Pricey"}, {"n": 2, "op": "cut", "cut": "Pricey"},
               {"n": 3, "op": "cut", "cut": "Old Card"}, {"n": 4, "op": "add", "add": "Old Card"},
               {"n": 5, "op": "swap", "cut": "Cheap", "add": "Elf Dork"}]
        self.assertEqual(self.net(log), ({"Elf Dork": 1}, {"Cheap": 1}))

    def test_a_card_added_twice_counts_twice(self):
        log = [{"n": 1, "op": "add", "add": "Forest"}, {"n": 2, "op": "add", "add": "Forest"}]
        self.assertEqual(self.net(log), ({"Forest": 2}, {}))

    def test_an_undone_group_leaves_nothing(self):
        log = [LOG[3], {"n": 6, "op": "undo", "of": 4}]
        self.assertEqual(self.net(log), ({}, {}))

    def test_an_empty_or_missing_log_changes_nothing(self):
        self.assertEqual(self.net([]), ({}, {}))
        self.assertEqual(metrics.net_changes(None, self.db), ({}, {}))

    def test_names_in_the_log_are_matched_in_any_spelling(self):
        log = [{"n": 1, "op": "add", "add": "pricey"}, {"n": 2, "op": "cut", "cut": "PRICEY"}]
        self.assertEqual(self.net(log), ({}, {}))

    def test_the_changes_group_lists_who_when_and_why(self):
        got = self.items(deck("Pricey", "Elf Dork", "Mind Rock"), base=self.compute(deck("Old Card")), changes=LOG,
                         player="andy")
        added, cut = got["changes_added"], got["changes_cut"]
        self.assertEqual((added["value"], added["cards"]), (3, ["Pricey", "Elf Dork", "Mind Rock"]))
        self.assertEqual(added["why"], [
            "Pricey: change 1, 2026-10-11, by andy, suggested by the tool",
            "Elf Dork: change 4, in \"Up to $25\", 2026-10-11, by andy, suggested by the tool",
            "Mind Rock: change 4, in \"Up to $25\", 2026-10-11, by andy, suggested by the tool"])
        self.assertEqual((cut["value"], cut["cards"]), (4, ["Forest", "Swamp"]))
        self.assertEqual(cut["why"][0], "Forest × 3: change 1, 2026-10-11, by andy, suggested by the tool")
        self.assertEqual(cut["why"][1], "Swamp: change 2, 2026-10-11, by andy, picked by hand")

    def test_without_a_player_the_line_leaves_who_out(self):
        got = self.items(deck("Pricey"), base=self.compute(deck("Old Card")), changes=LOG[:1])["changes_added"]
        self.assertEqual(got["why"], ["Pricey: change 1, 2026-10-11, suggested by the tool"])

    def test_the_net_cost_is_the_added_cards_minus_the_cut_ones_at_todays_prices(self):
        # added: Pricey 10.00 + Elf Dork 1.00 + Mind Rock 1.00 = 12.00; the cut cards are basic lands, worth nothing
        got = self.items(deck("Pricey"), base=self.compute(deck("Old Card")), changes=LOG)["changes_net_cost"]
        self.assertEqual((got["value"], got["unit"]), (12.0, "$"))

    def test_owned_cards_added_cost_nothing_and_cut_cards_you_paid_for_are_taken_off(self):
        log = [{"n": 1, "op": "swap", "cut": "Old Card", "add": "Pricey"},
               {"n": 2, "op": "swap", "cut": "Cheap", "add": "Elf Dork"}]
        got = self.items(deck("Pricey"), base=self.compute(deck("Old Card")), changes=log,
                         owned=["Elf Dork", "Old Card"])["changes_net_cost"]
        # paid for Pricey 10.00 (Elf Dork is owned); Old Card is owned, so cutting it gives back nothing; Cheap is not
        # owned, so cutting it gives back 2.50
        self.assertEqual(got["value"], 7.5)
        self.assertIn("Added: $10.00 for 1 of 2 cards", got["why"][0])
        self.assertIn("Cut: $2.50 for 1 of 2 cards you did not own", got["why"][1])

    def test_the_group_exists_only_with_a_base_deck(self):
        self.assertEqual([g["id"] for g in self.compute(deck("Pricey"))["groups"]], GROUP_IDS[:-1])
        with_base = self.compute(deck("Pricey"), base=self.compute(deck("Old Card")), changes=LOG)
        self.assertEqual([g["id"] for g in with_base["groups"]], GROUP_IDS)
        self.assertEqual(with_base["groups"][-1]["label"], "Changes from the base deck")

    def test_a_base_deck_with_no_log_gives_items_that_say_the_log_is_missing(self):
        got = self.items(deck("Pricey"), base=self.compute(deck("Old Card")))
        for key in ("changes_added", "changes_cut", "changes_net_cost"):
            self.assertEqual((got[key]["value"], got[key]["why"]), (None, ["The change log was not given."]))


class BaseValueTests(MetricsCase):
    def setUp(self):
        super().setUp()
        w = self.world
        w.add("Trophy", "Instant", 2, roles=["removal"], attrs=["removal-permanent", "removal-destroy"], price=1.0)
        w.add("Sorcery Kill", "Sorcery", 2, roles=["removal"], attrs=["removal-permanent", "removal-destroy"], price=1.0)
        w.add("Bear", "Creature", 2, price=1.0)
        self.before = self.compute(deck("Trophy", "Sorcery Kill", "Bear"))
        self.after = self.compute(deck("Trophy", "Bear"), base=self.before, changes=[])

    def test_every_item_of_every_group_but_the_changes_carries_its_value_in_the_base_deck(self):
        for group in self.after["groups"]:
            for item in group["items"]:
                if group["id"] == "changes":
                    self.assertNotIn("base", item, item["id"])
                elif item["value"] is not None:
                    self.assertIn("base", item, item["id"])

    def test_before_and_after_for_removal_power(self):
        got = items_of(self.after)["removal_power"]
        # Trophy 0.90 + Sorcery Kill 0.675 = 1.575 -> 1.57 before (round half to even in floats: 1.575 -> 1.57); Trophy
        # alone 0.90 after
        self.assertEqual((got["base"], got["value"]), (round(0.9 + 0.675, 2), 0.9))

    def test_base_is_the_value_the_base_result_holds(self):
        before = items_of(self.before)
        for key, item in items_of(self.after).items():
            if "base" in item:
                self.assertEqual(item["base"], before[key]["value"], key)

    def test_an_item_the_base_could_not_compute_gets_no_base(self):
        no_tags = self.compute(deck("Trophy", "Sorcery Kill", "Bear"), attrs=False)
        got = items_of(self.compute(deck("Trophy", "Bear"), base=no_tags, changes=[]))
        self.assertNotIn("base", got["removal_power"])
        self.assertIn("base", got["lands"])

    def test_a_result_with_no_base_has_no_base_keys(self):
        self.assertFalse([i for i in items_of(self.before).values() if "base" in i])

    def test_the_base_result_is_not_changed_by_being_the_base(self):
        copy_before = copy.deepcopy(self.before)
        self.compute(deck("Bear"), base=self.before, changes=[])
        self.assertEqual(self.before, copy_before)


# ----------------------------------------------------------------------------- the whole result
class ResultShapeTests(MetricsCase):
    def setUp(self):
        super().setUp()
        w = self.world
        w.add("Trophy", "Instant", 2, "{B}{G}", roles=["removal"], attrs=["removal-permanent", "removal-destroy"],
              score=0.6, theme=0.1, price=3.0)
        w.add("Pinger", "Creature", 3, "{2}{G}", roles=["removal", "finisher"],
              attrs=["removal-creature", "repeatable-removal", "evasion"], score=0.4, price=2.0, power="2")
        w.add("Temple Bog", "Land", 0, produced=["B", "G"], ci="BG", attrs=["tapland"])
        w.add("Mind Rock", "Artifact", 2, "{2}", roles=["ramp"], attrs=["mana-rock"], price=1.0)
        self.cards = deck("Trophy", "Pinger", "Temple Bog", "Mind Rock", ("Forest", 3), ("Swamp", 2))
        self.base = self.compute(deck("Trophy", "Forest"))

    def scenarios(self):
        yield "plain", self.compute(self.cards)
        yield "no tags", self.compute(self.cards, attrs=False)
        yield "no combos", self.compute(self.cards, combos=None)
        yield "with a base", self.compute(self.cards, base=self.base, changes=LOG, player="andy")
        yield "nothing at all", self.compute([])
        yield "lands only", self.compute(deck(("Forest", 3)))

    def test_the_result_has_a_schema_a_headline_and_the_groups_in_order(self):
        result = self.compute(self.cards)
        self.assertEqual(list(result), ["schema", "headline", "groups"])
        self.assertEqual(result["schema"], 1)
        self.assertEqual([g["id"] for g in result["groups"]], GROUP_IDS[:-1])
        self.assertEqual([g["label"] for g in result["groups"]], ["Power", "Interaction", "Mana and consistency",
                                                                  "Playstyle", "Win plan", "Table and money"])

    def test_the_registry_is_id_label_applies_compute_and_only_the_changes_group_can_be_left_out(self):
        self.assertEqual([entry[0] for entry in metrics.GROUPS], GROUP_IDS)
        for group_id, label, applies, compute in metrics.GROUPS:
            self.assertTrue(label and callable(applies) and callable(compute), group_id)

    def test_every_item_of_every_group_has_exactly_the_documented_shape(self):
        for name, result in self.scenarios():
            for group in result["groups"]:
                self.assertEqual(sorted(group), ["id", "items", "label"])
                for item in group["items"]:
                    with self.subTest(scenario=name, item=item["id"]):
                        base = ["base"] if "base" in item else []
                        self.assertEqual(sorted(item), sorted(ITEM_KEYS + base))
                        self.assertIsInstance(item["id"], str)
                        self.assertIsInstance(item["label"], str)
                        self.assertTrue(item["value"] is None or isinstance(item["value"], (int, float)))
                        self.assertIn(item["unit"], (None, "%", "$"))
                        self.assertIn(item["status"], (None, "short", "inside", "over"))
                        self.assertTrue(item["target"] is None or sorted(item["target"]) == ["max", "min", "target"])
                        self.assertTrue(all(isinstance(line, str) for line in item["why"]))
                        self.assertTrue(all(isinstance(card, str) for card in item["cards"]))
                        if item["value"] is None:
                            self.assertTrue(item["why"], "an item with no value says why")
                            self.assertIsNone(item["status"])
                        if item["status"] is not None and item["id"] != "limit_two_card_combos":
                            self.assertIsNotNone(item["target"])            # a status is always against a band

    def test_item_ids_are_unique_across_the_result(self):
        for name, result in self.scenarios():
            ids = [i["id"] for g in result["groups"] for i in g["items"]]
            self.assertEqual(len(ids), len(set(ids)), name)

    def test_the_same_item_ids_come_out_whatever_data_was_available(self):
        plain = [i["id"] for g in self.compute(self.cards)["groups"] for i in g["items"]]
        for name, result in list(self.scenarios())[1:3]:
            self.assertEqual([i["id"] for g in result["groups"] for i in g["items"]], plain, name)

    def test_the_headline_has_the_five_numbers_a_page_pins(self):
        result = self.compute(self.cards, owned=["Trophy"])
        items = items_of(result)
        self.assertEqual(list(result["headline"]), ["score", "bracket", "bracket_ok", "lands", "removal_power", "price"])
        self.assertEqual(result["headline"], {"score": items["score"]["value"], "bracket": items["bracket"]["value"],
                                              "bracket_ok": items["bracket"]["status"] == "inside",
                                              "lands": items["lands"]["value"],
                                              "removal_power": items["removal_power"]["value"],
                                              "price": items["price_to_buy"]["value"]})
        self.assertEqual(result["headline"]["lands"], 6)
        # the commander 5 + Pinger 2 + Temple Bog 1 + Mind Rock 1; Trophy is owned and the basic lands are free
        self.assertEqual(result["headline"]["price"], 9.0)

    def test_the_headline_has_no_number_where_the_item_has_none(self):
        self.assertIsNone(self.compute(self.cards, attrs=False)["headline"]["removal_power"])

    def test_the_result_is_plain_json(self):
        for name, result in self.scenarios():
            self.assertEqual(json.loads(json.dumps(result)), result, name)

    def test_compute_changes_none_of_its_inputs(self):
        ctx, cards, attrs = self.world.ctx(), copy.deepcopy(self.cards), self.world.attrs()
        frozen = (copy.deepcopy(ctx), copy.deepcopy(cards), copy.deepcopy(attrs), copy.deepcopy(LOG))
        metrics.compute(ctx, self.world.db(), cards, commanders=[CMDR], attrs=attrs,
                        combos={"included": [], "almost": []}, base=self.base, changes=LOG, owned=["Trophy"],
                        prices={"Trophy": 9.0})
        self.assertEqual((ctx, cards, attrs, LOG), frozen)

    def test_two_runs_on_the_same_input_give_the_same_result(self):
        self.assertEqual(self.compute(self.cards), self.compute(self.cards))

    def test_names_can_be_listed_one_per_copy_or_as_count_name_pairs(self):
        pairs = self.compute(deck(("Forest", 3), "Trophy"))
        flat = self.compute(["Forest", "Forest", "Forest", "Trophy"])
        lists = self.compute([[3, "Forest"], [1, "Trophy"]])
        self.assertEqual(pairs, flat)
        self.assertEqual(pairs, lists)

    def test_a_name_the_card_index_lacks_is_skipped_as_roles_counts_skips_it(self):
        self.assertEqual(self.compute(self.cards + deck("No Such Card")), self.compute(self.cards))

    def test_a_card_missing_from_the_context_counts_as_a_card_with_no_role_and_no_score(self):
        self.world.add("Late Add", "Creature", 2, price=1.0)
        ctx = self.world.ctx()
        del ctx["role_map"]["Late Add"], ctx["scores"]["Late Add"]
        got = items_of(self.compute(self.cards + deck("Late Add"), ctx=ctx))
        self.assertEqual(got["creatures"]["value"], 2)           # Pinger and Late Add

    def test_a_deck_of_nothing_does_not_crash(self):
        got = items_of(self.compute([]))
        self.assertEqual((got["lands"]["value"], got["avg_mana_value"]["value"], got["instant_share"]["value"]),
                         (0, None, None))

    def test_compute_takes_a_few_milliseconds_not_seconds(self):
        # not a benchmark (the real-data timing is in the pull request); a guard against an accidental scan of
        # something large: 100 runs of a small deck must finish within a few seconds even on a slow machine
        start = time.perf_counter()
        for _ in range(100):
            self.compute(self.cards)
        self.assertLess(time.perf_counter() - start, 5.0)


class PriceAgreementTests(MetricsCase):
    """`stats` and `upgrade` price a card the same way. The card index holds the default printing's price; `upgrade`
    charges the cheapest printing, and so do carddb.deck_prices, `stats` and the deck pages, which makes the cost to buy of
    a list an upgrade made equal to what the upgrade spent."""

    def setUp(self):
        super().setUp()
        # `upgrade` asks for the attribute tags: tags that load and that no card carries, not this machine's cache
        mock.patch.object(roles, "attributes",
                          side_effect=lambda names, db, **kw: {n: frozenset() for n in names}).start()
        mock.patch.object(roles, "attributes_loaded", return_value=True).start()
        w = self.world
        for name, score in (("Old A", 0.1), ("Old B", 0.1), ("Old C", 0.2)):
            w.add(name, "Creature", 2, score=score, price=0.5)
        w.add("New X", "Creature", 2, score=0.9, price=10.0)       # the default printing costs 10.00, the cheapest 6.00
        w.add("New Y", "Creature", 2, score=0.8, price=4.0)        # 4.00 and 3.00
        self.cheapest = {"New X": 6.0, "New Y": 3.0, "Old A": 0.5, "Old B": 0.5, "Old C": 0.5}
        self.before = ["Old A", "Old B", "Old C"]

    def test_the_cost_to_buy_of_the_list_an_upgrade_made_is_what_the_upgrade_spent(self):
        # a $20 upgrade buys New X ($6.00) and New Y ($3.00): $9.00; stats of the new list, owning the old one, says $9.00
        db, ctx = self.world.db(), self.world.ctx(targets=valueless_roles())
        result = build.upgrade(ctx, {"commanders": [CMDR], "cards": [(1, n) for n in self.before]}, db, budget=20,
                               prices=self.cheapest)
        self.assertEqual(sorted(x["add"] for x in result["swaps"]), ["New X", "New Y"])
        self.assertEqual(result["spent"], 9.0)
        names = [name for _, name in result["deck_after"]["cards"]]
        with mock.patch.object(carddb, "cheapest_prices", return_value=self.cheapest):
            prices = carddb.deck_prices(names + [CMDR], db)
        priced = metrics.compute(ctx, db, result["deck_after"]["cards"], commanders=[CMDR], owned=self.before + [CMDR],
                                 prices=prices, attrs=None, combos=None)
        self.assertEqual(priced["headline"]["price"], 9.0)
        indexed = metrics.compute(ctx, db, result["deck_after"]["cards"], commanders=[CMDR], owned=self.before + [CMDR],
                                  attrs=None, combos=None)
        self.assertEqual(indexed["headline"]["price"], 14.0)       # the index's prices: $10.00 + $4.00, not what was spent


if __name__ == "__main__":
    unittest.main()
