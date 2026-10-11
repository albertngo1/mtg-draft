"""Tests for providers/spellbook.py. The network is replaced by recorded answers in fixtures/."""
import copy, json, os, unittest
from unittest import mock

from mtgcommander import net
from mtgcommander.providers import spellbook

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
COMMANDER = "Chatterfang, Squirrel General"
DECK = ["Pitiless Plunderer", "Zulaport Cutthroat", "Hazel's Brewmaster", "Forest", "Forest", "Sol Ring"]


def fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


class FakeFetch:
    """Stands in for net.fetch_json: hands out the queued answers in order and records every call.
    An answer that is an Exception is raised instead of returned."""
    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def __call__(self, url, **kw):
        self.calls.append((url, kw))
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer, {"url": url, "fetched": "2026-10-11T12:00:00Z", "cache": "network", "age_days": 0.0}


def patched(fake):
    return mock.patch.object(net, "fetch_json", fake)


class BracketTagTests(unittest.TestCase):
    def test_the_table_matches_spellbooks_own_definitions(self):
        # tag: (label, lowest bracket it can fit, lowest bracket it surely fits), from Spellbook's site source
        want = {"R": ("Ruthless", 4, 4), "S": ("Spicy", 3, 4), "P": ("Powerful", 3, 3),
                "O": ("Oddball", 2, 3), "C": ("Core", 2, 2), "E": ("Exhibition", 1, 1)}
        for tag, (label, lowest, sure) in want.items():
            with self.subTest(tag=tag):
                entry = spellbook.BRACKET_TAGS[tag]
                self.assertEqual((entry["label"], entry["lowest"], entry["min_bracket"]),
                                 (label, lowest, sure))

    def test_banned_combos_fit_no_bracket_below_the_top(self):
        self.assertEqual(spellbook.BRACKET_TAGS["B"]["min_bracket"], 5)
        self.assertIsNone(spellbook.BRACKET_TAGS["B"]["lowest"])

    def test_every_tag_explains_itself(self):
        for tag, entry in spellbook.BRACKET_TAGS.items():
            with self.subTest(tag=tag):
                self.assertTrue(entry["meaning"])
                self.assertTrue(1 <= entry["min_bracket"] <= 5)

    def test_a_known_tag_decides_whatever_the_combo_looks_like(self):
        self.assertEqual(spellbook.bracket_needed("E", True, True), 1)
        self.assertEqual(spellbook.bracket_needed("R", False, False), 4)

    def test_an_unknown_tag_falls_back_to_the_two_card_infinite_rule(self):
        # (two cards, infinite) → Bracket 4; anything else → fits any bracket
        for tag in ("Z", None):
            with self.subTest(tag=tag):
                self.assertEqual(spellbook.bracket_needed(tag, True, True), 4)
                self.assertEqual(spellbook.bracket_needed(tag, True, False), 1)
                self.assertEqual(spellbook.bracket_needed(tag, False, True), 1)


class ParseComboTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = fixture("spellbook_find_my_combos.json")["results"]
        cls.parsed = spellbook.parse_results(cls.results, [COMMANDER] + DECK)

    def almost(self, combo_id):
        return next(c for c in self.parsed["almost"] if c["id"] == combo_id)

    def test_an_included_two_card_infinite_combo(self):
        combo = self.parsed["included"][0]
        self.assertEqual(combo["id"], "3000-4871")
        self.assertEqual(combo["cards"], ["Chatterfang, Squirrel General", "Pitiless Plunderer"])
        self.assertEqual(combo["produces"], ["Infinite Treasure tokens", "Infinite colored mana"])
        self.assertTrue(combo["two_card"] and combo["infinite"])
        self.assertEqual((combo["bracket_tag"], combo["min_bracket"]), ("S", 4))  # blocked at Bracket 3
        self.assertEqual(combo["missing"], [])
        self.assertEqual(combo["url"], "https://commanderspellbook.com/combo/3000-4871/")

    def test_an_almost_combo_names_the_card_that_would_complete_it(self):
        # Zulaport Cutthroat and the commander are in the deck; Warren Soultrader is not
        combo = self.almost("1385-3000-5670")
        self.assertEqual(combo["missing"], ["Warren Soultrader"])
        self.assertFalse(combo["two_card"])
        self.assertEqual((combo["bracket_tag"], combo["min_bracket"]), ("E", 1))

    def test_the_missing_half_of_a_ruthless_two_card_combo(self):
        combo = self.almost("4762-5856")
        self.assertEqual(combo["missing"], ["Devoted Druid"])
        self.assertTrue(combo["two_card"] and combo["infinite"])
        self.assertEqual(combo["min_bracket"], 4)

    def test_names_are_compared_without_regard_to_case(self):
        parsed = spellbook.parse_results(self.results, ["chatterfang, squirrel general", "WARREN SOULTRADER",
                                                        "zulaport cutthroat"])
        combo = next(c for c in parsed["almost"] if c["id"] == "1385-3000-5670")
        self.assertEqual(combo["missing"], [])

    def test_a_template_makes_two_cards_a_three_piece_combo(self):
        # Fable + Combat Celebrant also need "any sacrifice outlet", so Wizards' two-card rule does not apply
        combo = self.almost("2105-3337--140")
        self.assertFalse(combo["two_card"])
        self.assertEqual(combo["requires"], ["Any sacrifice outlet"])
        self.assertEqual(combo["missing"], ["Fable of the Mirror-Breaker // Reflection of Kiki-Jiki",
                                            "Combat Celebrant"])

    def test_infinite_means_a_produced_feature_that_says_so(self):
        # "Win the game" is a finish, not a loop; "Infinite damage" is a loop
        self.assertFalse(self.almost("9-9")["infinite"])
        self.assertTrue(self.almost("8-8")["infinite"])

    def test_unknown_tags_use_the_fallback_rule(self):
        self.assertEqual(self.almost("9-9")["min_bracket"], 1)  # two cards but not infinite
        self.assertEqual(self.almost("8-8")["min_bracket"], 4)  # two cards and infinite

    def test_combos_that_need_another_colour_are_not_returned(self):
        ids = [c["id"] for c in self.parsed["included"] + self.parsed["almost"]]
        self.assertNotIn("7-7", ids)

    def test_a_card_with_two_copies_counts_both(self):
        variant = {"id": "1-1", "bracketTag": "R", "uses": [{"card": {"name": "Rat"}, "quantity": 2}],
                   "requires": [], "produces": [{"feature": {"name": "Infinite damage"}}]}
        self.assertTrue(spellbook.parse_combo(variant)["two_card"])

    def test_a_variant_missing_optional_parts_still_parses(self):
        combo = spellbook.parse_combo({"id": "5-5"})
        self.assertEqual((combo["cards"], combo["produces"], combo["bracket_tag"]), ([], [], None))
        self.assertFalse(combo["two_card"])


class EstimateParseTests(unittest.TestCase):
    def test_deck_level_verdict_and_flagged_cards(self):
        est = spellbook.parse_estimate(fixture("spellbook_estimate_bracket.json"))
        self.assertEqual((est["tag"], est["label"], est["min_bracket"], est["lowest"]),
                         ("P", "Powerful", 3, 3))
        self.assertEqual(est["game_changers"], ["Rhystic Study"])
        self.assertEqual(est["mass_land_denial"], ["Armageddon"])
        self.assertEqual(est["extra_turns"], ["Time Warp"])
        self.assertEqual(est["banned"], ["Black Lotus"])

    def test_combos_carry_spellbooks_own_classification(self):
        combo = spellbook.parse_estimate(fixture("spellbook_estimate_bracket.json"))["combos"][0]
        self.assertEqual(combo["id"], "3000-4871")
        self.assertEqual((combo["speed"], combo["relevant"], combo["definitely_two_card"]), (5, True, False))
        self.assertTrue(combo["arguably_two_card"])
        self.assertFalse(combo["lock"])

    def test_an_unknown_deck_tag_is_passed_through_without_a_bracket(self):
        est = spellbook.parse_estimate({"bracketTag": "Z", "cards": [], "combos": []})
        self.assertEqual((est["tag"], est["label"], est["min_bracket"]), ("Z", None, None))


class RequestTests(unittest.TestCase):
    def test_body_lists_commanders_and_folds_repeated_names_into_a_quantity(self):
        body = spellbook._deck_body([COMMANDER], DECK)
        self.assertEqual(body["commanders"], [{"card": COMMANDER}])
        self.assertIn({"card": "Forest", "quantity": 2}, body["main"])
        self.assertIn({"card": "Sol Ring"}, body["main"])

    def test_find_combos_posts_the_deck_and_returns_both_lists(self):
        fake = FakeFetch(fixture("spellbook_find_my_combos.json"))
        with patched(fake):
            found = spellbook.find_combos([COMMANDER], DECK)
        url, kw = fake.calls[0]
        self.assertEqual((url, kw["source"]),
                         ("https://backend.commanderspellbook.com/find-my-combos", "spellbook"))
        self.assertEqual(kw["data"], spellbook._deck_body([COMMANDER], DECK))
        self.assertEqual(len(found["included"]), 1)
        self.assertEqual(len(found["almost"]), 5)
        self.assertEqual((found["fetched"], found["cache"]), ("2026-10-11T12:00:00Z", "network"))

    def test_cache_key_does_not_depend_on_the_order_of_the_cards(self):
        fake = FakeFetch(fixture("spellbook_find_my_combos.json"), fixture("spellbook_find_my_combos.json"),
                         fixture("spellbook_find_my_combos.json"))
        with patched(fake):
            spellbook.find_combos([COMMANDER], DECK)
            spellbook.find_combos([COMMANDER], list(reversed(DECK)))
            spellbook.find_combos([COMMANDER], DECK + ["Skullclamp"])
        keys = [kw["key"] for _, kw in fake.calls]
        self.assertEqual(keys[0], keys[1])
        self.assertNotEqual(keys[0], keys[2])
        self.assertTrue(keys[0].startswith("combos-"))

    def test_the_run_wide_modes_pass_through_to_net(self):
        fake = FakeFetch(fixture("spellbook_find_my_combos.json"))
        with patched(fake):
            spellbook.find_combos([COMMANDER], DECK, refresh=True, offline=False)
        self.assertEqual((fake.calls[0][1]["refresh"], fake.calls[0][1]["offline"]), (True, False))

    def test_a_second_page_is_requested_and_merged(self):
        page1, page2 = fixture("spellbook_find_my_combos.json"), fixture("spellbook_find_my_combos.json")
        page1["next"] = "https://backend.commanderspellbook.com/find-my-combos?limit=5&offset=5"
        page2["results"]["included"] = []
        page2["results"]["almostIncluded"] = copy.deepcopy(page2["results"]["almostIncluded"][:1])
        fake = FakeFetch(page1, page2)
        with patched(fake):
            found = spellbook.find_combos([COMMANDER], DECK)
        self.assertEqual(fake.calls[1][0], page1["next"])
        self.assertNotEqual(fake.calls[0][1]["key"], fake.calls[1][1]["key"])
        self.assertEqual((len(found["included"]), len(found["almost"])), (1, 6))

    def test_a_next_link_to_another_host_is_not_followed(self):
        page = fixture("spellbook_find_my_combos.json")
        page["next"] = "https://example.com/find-my-combos?offset=5"
        fake = FakeFetch(page)
        with patched(fake):
            spellbook.find_combos([COMMANDER], DECK)
        self.assertEqual(len(fake.calls), 1)

    def test_pages_stop_at_the_limit(self):
        def endless():
            page = fixture("spellbook_find_my_combos.json")
            page["next"] = "https://backend.commanderspellbook.com/find-my-combos?offset=1"
            return page
        fake = FakeFetch(*[endless() for _ in range(spellbook.MAX_PAGES + 3)])
        with patched(fake):
            spellbook.find_combos([COMMANDER], DECK)
        self.assertEqual(len(fake.calls), spellbook.MAX_PAGES)

    def test_an_answer_without_results_is_an_error(self):
        with patched(FakeFetch({"detail": "something else"})):
            with self.assertRaises(net.FetchError):
                spellbook.find_combos([COMMANDER], DECK)

    def test_network_failure_propagates(self):
        with patched(FakeFetch(net.FetchError("spellbook", "u", "HTTP 503"))):
            with self.assertRaises(net.FetchError):
                spellbook.find_combos([COMMANDER], DECK)


class EstimateBracketTests(unittest.TestCase):
    def test_the_estimate_endpoint_is_called_with_the_same_body(self):
        fake = FakeFetch(fixture("spellbook_estimate_bracket.json"))
        with patched(fake):
            est = spellbook.estimate_bracket([COMMANDER], DECK)
        url, kw = fake.calls[0]
        self.assertEqual(url, "https://backend.commanderspellbook.com/estimate-bracket")
        self.assertEqual(kw["data"], spellbook._deck_body([COMMANDER], DECK))
        self.assertTrue(kw["key"].startswith("estimate-"))
        self.assertEqual((est["tag"], est["fetched"], est["cache"]), ("P", "2026-10-11T12:00:00Z", "network"))

    def test_none_when_the_endpoint_is_gone(self):
        with patched(FakeFetch(net.NotFound("spellbook", "u", "no such page (HTTP 404)"))):
            self.assertIsNone(spellbook.estimate_bracket([COMMANDER], DECK))

    def test_an_answer_that_is_not_an_estimate_is_an_error(self):
        with patched(FakeFetch({"detail": "something else"})):
            with self.assertRaises(net.FetchError):
                spellbook.estimate_bracket([COMMANDER], DECK)


if __name__ == "__main__":
    unittest.main()
