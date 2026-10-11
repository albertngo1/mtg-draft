"""Tests for brackets.py: Wizards' limits as data, the card tests, check(), blocked_adds() and can_add().

Cards and combos come from small hand-written fixtures in fixtures/ (the combos in the shape
providers/spellbook.py returns); nothing here touches the network."""
import json, os, re, unittest
from mtgcommander import brackets

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


CARDS = fixture("brackets_cards.json")  # a dict by name: db.get(name) works as it does on a CardDB
COMBOS = fixture("brackets_combos.json")


def found(included=(), almost=()):
    """The fixture combos with these ids, in the shape providers.spellbook.find_combos returns."""
    return {"included": [c for c in COMBOS["included"] if c["id"] in included],
            "almost": [c for c in COMBOS["almost"] if c["id"] in almost]}


NO_COMBOS = found()
ALL_ALMOST = {"included": [], "almost": COMBOS["almost"]}


class RulesTest(unittest.TestCase):
    def test_each_bracket_has_the_limits_wizards_publish(self):
        """From Wizards' format page and the Oct 21, 2025 limits graphic (quotes are in brackets.json)."""
        expected = {  # bracket: name, most Game Changers, mass land denial allowed, extra turns, combos
            1: ("Exhibition", 0, False, "none", "none"),
            2: ("Core", 0, False, "no-chaining", "none"),
            3: ("Upgraded", 3, False, "no-chaining", "late-game"),
            4: ("Optimized", None, True, "any", "any"),
            5: ("cEDH", None, True, "any", "any"),
        }
        for n, (name, cap, mld, extra, combos) in expected.items():
            with self.subTest(bracket=n):
                r = brackets.rules(n)
                self.assertEqual((r["bracket"], r["name"], r["game_changers_max"], r["mass_land_denial"],
                                  r["extra_turns"], r["two_card_combos"]), (n, name, cap, mld, extra, combos))

    def test_wording_keeps_the_expected_turns_verbatim(self):
        """Wizards says how many turns players should get before anyone wins; "early game" is before that."""
        expected = {1: (9, "at least nine turns"), 2: (8, "at least eight turns"),
                    3: (6, "at least six turns"), 4: (4, "at least four turns"),
                    5: (None, "These games could end on any turn.")}
        for n, (turns, phrase) in expected.items():
            with self.subTest(bracket=n):
                r = brackets.rules(n)
                self.assertEqual(r["turns"], turns)
                self.assertTrue(r["wording"].startswith("Players expect:"))
                self.assertIn(phrase, r["wording"])

    def test_a_bracket_must_be_one_to_five(self):
        for bad in (0, 6, None, "x"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                brackets.rules(bad)


class DataFileTest(unittest.TestCase):
    def setUp(self):
        self.data = brackets._data()["raw"]

    def test_data_is_dated_and_sourced(self):
        self.assertRegex(self.data["as_of"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(self.data["source"])
        self.assertTrue(all(url.startswith("https://") for url in self.data["source"]))
        for key in ("mass_land_denial", "extra_turns", "two_card_combos", "game_changers"):
            quotes = self.data["definitions"][key]
            self.assertTrue(quotes, key)
            for q in quotes:
                self.assertTrue(q["text"] and q["source"].startswith("https://") and q["date"], key)

    def test_the_cards_wizards_name_are_on_the_list(self):
        """Wizards' Feb 11, 2025 article: 'Examples in this category are Armageddon, Ruination, Sunder,
        Winter Orb, and Blood Moon.'"""
        for name in ("Armageddon", "Ruination", "Sunder", "Winter Orb", "Blood Moon"):
            self.assertIn(name, self.data["mass_land_denial_cards"])

    def test_every_listed_card_says_why_and_none_is_both_listed_and_excepted(self):
        cards = self.data["mass_land_denial_cards"]
        self.assertEqual(len(set(cards)), len(cards))
        for name in cards:
            self.assertTrue(self.data["mass_land_denial_basis"].get(name), name)
        self.assertFalse(set(cards) & set(self.data["mass_land_denial_exceptions"]))

    def test_every_pattern_compiles_and_is_explained(self):
        for pattern in self.data["mass_land_denial_patterns"] + self.data["extra_turn_patterns"]:
            re.compile(pattern)
            self.assertIn(pattern, self.data["pattern_notes"])


class CardTestsTest(unittest.TestCase):
    def test_mass_land_denial_cards(self):
        cases = {  # card: why it counts
            "Armageddon": "named by Wizards; destroys every land",
            "Winter Orb": "named by Wizards; players untap at most one land",
            "Blood Moon": "named by Wizards; nonbasic lands become Mountains",
            "Sunder": "named by Wizards; returns every land to hand",
            "Boom // Bust": "a split card whose Bust half destroys all lands",
            "Desolation Angel": "kicked, it destroys all lands (found by rules text)",
            "Myojin of Infinite Rage": "an ability destroys all lands (found by rules text)",
            "Rising Waters": "lands stop untapping (found by rules text)",
            "Devastating Dreams": "each player sacrifices X lands (found by rules text)",
            "Fall of the Thran": "chapter I destroys all lands (found by rules text)",
            "Planetary Annihilation": "each player keeps six lands (found by rules text)",
            "Zhao, the Moon Slayer": "can turn nonbasic lands into Mountains (found by rules text)",
            "Bend or Break": "destroys all lands in the chosen piles (found by rules text)",
        }
        for name, why in cases.items():
            with self.subTest(name, why=why):
                self.assertTrue(brackets.is_mass_land_denial(CARDS[name]))

    def test_look_alikes_are_not_mass_land_denial(self):
        cases = {  # card: why it does not count
            "Wasteland": "destroys one nonbasic land",
            "Stone Rain": "destroys one land",
            "Strip Mine": "destroys one land",
            "Elspeth Tirel": "destroys everything except lands",
            "Scourglass": "destroys everything except artifacts and lands",
            "Ajani Vengeant": "only a rarely reached ultimate hits one player's lands",
            "Dovin Baan": "its ultimate emblem binds only opponents",
            "Vorinclex, Voice of Hunger": "Wizards: 'doesn't fully fit'; it binds only opponents",
            "From the Ashes": "gives each destroyed land back as a basic ('without replacing them')",
            "Cataclysmic Gearhulk": "its sacrifice spares lands ('non-land permanents')",
            "Sol Ring": "no land effect at all",
            "Forest": "a land is not land denial",
        }
        for name, why in cases.items():
            with self.subTest(name, why=why):
                self.assertFalse(brackets.is_mass_land_denial(CARDS.get(name, {"name": name, "text": ""})))

    def test_a_split_card_matches_by_either_name(self):
        """A record may name the whole card or only its front face; both are the curated Boom // Bust."""
        self.assertTrue(brackets.is_mass_land_denial({"name": "Boom // Bust", "front": "Boom", "text": ""}))
        self.assertTrue(brackets.is_mass_land_denial({"name": "Boom", "text": ""}))

    def test_extra_turn_cards(self):
        cases = {
            "Time Warp": "on the curated list and says so in its text",
            "Nexus of Fate": "on the curated list",
            "Medomai the Ageless": "a creature that grants an extra turn each time it connects",
            "Seedtime": "found by rules text only ('take an extra turn after this one')",
            "Emrakul, the Promised End": "found by rules text only (the opponent takes the extra turn)",
        }
        for name, why in cases.items():
            with self.subTest(name, why=why):
                self.assertTrue(brackets.is_extra_turn(CARDS[name]))

    def test_cards_that_only_mention_extra_turns_are_not_extra_turn_cards(self):
        cases = {
            "Stranglehold": "makes opponents skip extra turns",
            "Gerrard's Hourglass Pendant": "makes players skip extra turns",
            "Trouble in Pairs": "makes opponents skip extra turns",
            "Sol Ring": "no turn effect",
        }
        for name, why in cases.items():
            with self.subTest(name, why=why):
                self.assertFalse(brackets.is_extra_turn(CARDS[name]))


class CheckTest(unittest.TestCase):
    GAME_CHANGERS = ["Rhystic Study", "Cyclonic Rift", "Smothering Tithe", "Demonic Tutor"]
    HAZEL = "Hazel of the Rootbloom"

    def check(self, cards, bracket, commanders=(HAZEL,), combos=NO_COMBOS):
        return brackets.check(list(commanders), list(cards), bracket, CARDS, combos=combos)

    def test_a_list_with_nothing_restricted_meets_every_limit(self):
        r = self.check(["Sol Ring", "Forest", "Skullclamp"], 3)
        self.assertTrue(r["ok"])
        self.assertEqual(r["violations"], [])
        self.assertEqual((r["game_changers"], r["mass_land_denial"], r["extra_turns"], r["two_card_combos"]),
                         ([], [], [], []))
        self.assertEqual(r["estimated"], 1)
        # estimated 1 is below the target, so the result says limits alone cannot show intent
        self.assertTrue(any("floor" in n for n in r["notes"]))

    # -- Game Changers
    def test_three_game_changers_fit_bracket_three(self):
        r = self.check(self.GAME_CHANGERS[:3], 3)
        self.assertTrue(r["ok"])
        self.assertEqual((r["game_changers"], r["gc_max"], r["estimated"]), (self.GAME_CHANGERS[:3], 3, 3))

    def test_a_fourth_game_changer_breaks_bracket_three(self):
        r = self.check(self.GAME_CHANGERS, 3)
        self.assertFalse(r["ok"])
        (v,) = r["violations"]
        self.assertEqual((v["rule"], v["cards"], v["excess"]), ("game_changers", self.GAME_CHANGERS, 1))
        self.assertIn("Bracket 3 allows up to 3", v["message"])
        self.assertEqual(r["estimated"], 4)  # the lowest bracket with no limit on them

    def test_brackets_one_and_two_allow_no_game_changers(self):
        for n in (1, 2):
            with self.subTest(bracket=n):
                (v,) = self.check(self.GAME_CHANGERS[:1], n)["violations"]
                self.assertEqual(v["excess"], 1)
                self.assertIn("1 Game Changer (Rhystic Study); Bracket %d allows none" % n, v["message"])

    def test_brackets_four_and_five_have_no_game_changer_limit(self):
        for n in (4, 5):
            with self.subTest(bracket=n):
                r = self.check(self.GAME_CHANGERS, n)
                self.assertTrue(r["ok"])
                self.assertIsNone(r["gc_max"])
                self.assertEqual(r["game_changers"], self.GAME_CHANGERS)

    def test_the_commander_counts_as_a_game_changer(self):
        """Wizards: a commander on the Game Changers list 'counts toward one of your three'."""
        tergrid = "Tergrid, God of Fright // Tergrid's Lantern"
        r = self.check(self.GAME_CHANGERS[:3], 3, commanders=[tergrid])
        self.assertFalse(r["ok"])
        self.assertEqual(r["game_changers"][0], tergrid)
        self.assertTrue(any("your commander and a Game Changer" in n for n in r["notes"]))

    # -- mass land denial
    def test_mass_land_denial_is_over_the_limit_below_bracket_four(self):
        for n in (1, 2, 3):
            with self.subTest(bracket=n):
                (v,) = self.check(["Armageddon"], n)["violations"]
                self.assertEqual((v["rule"], v["cards"], v["excess"]),
                                 ("mass_land_denial", ["Armageddon"], 1))
        r = self.check(["Armageddon"], 4)
        self.assertTrue(r["ok"])
        self.assertEqual(r["mass_land_denial"], ["Armageddon"])  # still listed where it is allowed
        self.assertEqual(self.check(["Armageddon"], 3)["estimated"], 4)

    def test_cards_found_only_by_rules_text_are_labeled_as_guesses(self):
        r = self.check(["Armageddon", "Desolation Angel"], 3)
        (v,) = r["violations"]
        self.assertEqual(v["cards"], ["Armageddon", "Desolation Angel"])
        self.assertIn("Found by rules text (Desolation Angel)", v["message"])
        (v,) = self.check(["Armageddon"], 3)["violations"]
        self.assertNotIn("rules text", v["message"])

    # -- extra turns
    def test_one_extra_turn_card_is_fine_in_core_and_upgraded_but_not_exhibition(self):
        one = ["Time Warp"]
        (v,) = self.check(one, 1)["violations"]
        self.assertEqual((v["rule"], v["cards"], v["excess"]), ("extra_turns", one, 1))
        for n in (2, 3):
            with self.subTest(bracket=n):
                r = self.check(one, n)
                self.assertTrue(r["ok"])
                self.assertEqual(r["estimated"], 2)
                # the one-card reading of "no chaining" is the tool's judgment and says so
                self.assertTrue(any("judgment" in note for note in r["notes"]))
        # Bracket 4 has no extra-turn rule to be judged
        self.assertFalse(any("judgment" in note for note in self.check(one, 4)["notes"]))

    def test_a_second_extra_turn_card_counts_as_chaining_at_bracket_three(self):
        two = ["Time Warp", "Nexus of Fate"]
        r = self.check(two, 3)
        (v,) = r["violations"]
        self.assertEqual((v["rule"], v["cards"], v["excess"]), ("extra_turns", two, 1))
        self.assertIn("judgment", v["message"])
        self.assertEqual(r["estimated"], 4)
        self.assertTrue(self.check(two, 4)["ok"])

    # -- combos
    def test_two_card_infinite_combos_are_blocked_at_one_and_two_whatever_their_tag(self):
        """Spellbook tags Spawnsire of Ulamog + Pitiless Plunderer 'Exhibition' (min bracket 1), but it is a
        two-card infinite combo, which Brackets 1-2 do not allow."""
        c = found(["9001-0002"])
        for n in (1, 2):
            with self.subTest(bracket=n):
                (v,) = self.check([], n, combos=c)["violations"]
                self.assertEqual((v["rule"], v["cards"], v["excess"]),
                                 ("two_card_combos", ["Spawnsire of Ulamog", "Pitiless Plunderer"], 1))
                self.assertEqual(v["url"], "https://commanderspellbook.com/combo/9001-0002/")
                self.assertIn("a two-card infinite combo, which Bracket %d does not allow" % n, v["message"])
        self.assertTrue(self.check([], 3, combos=c)["ok"])
        self.assertEqual(self.check([], 1, combos=c)["estimated"], 3)

    def test_bracket_three_blocks_what_spellbook_rates_above_it(self):
        """Chatterfang + Pitiless Plunderer is tagged S (Spellbook: Bracket 4 or higher)."""
        c = found(["9001-0001"])
        r = self.check([], 3, combos=c)
        (v,) = r["violations"]
        self.assertEqual(v["cards"], ["Chatterfang, Squirrel General", "Pitiless Plunderer"])
        self.assertIn("Chatterfang, Squirrel General + Pitiless Plunderer (Infinite ETB triggers, "
                      "Infinite sacrifice triggers)", v["message"])
        self.assertIn("rates it for Bracket 4 or higher", v["message"])
        self.assertIn("cannot tell early from late", v["message"])
        self.assertEqual(r["estimated"], 4)
        self.assertTrue(self.check([], 4, combos=c)["ok"])

    def test_a_combo_is_allowed_from_the_bracket_spellbook_rates_it_for(self):
        """Demonic Consultation + Thassa's Oracle is tagged P (Bracket 3): over the limit at 2, fine at 3."""
        c = found(["9001-0004"])
        (v,) = self.check([], 2, combos=c)["violations"]
        self.assertIn("rates it for Bracket 3 or higher, and Bracket 2 allows no two-card combos",
                      v["message"])
        self.assertTrue(self.check([], 3, combos=c)["ok"])

    def test_a_core_combo_that_is_not_infinite_is_over_the_limit_only_at_exhibition(self):
        """Archaeomancer + Time Warp is tagged C (Bracket 2) and does not loop."""
        c = found(["9001-0003"])
        self.assertFalse(self.check([], 1, combos=c)["ok"])
        self.assertTrue(self.check([], 2, combos=c)["ok"])

    def test_a_larger_combo_is_allowed_with_a_note_because_wizards_limits_name_two_card_combos(self):
        c = found(["9001-0005"])  # Chatterfang + Skullclamp + Woe Strider: three cards, tagged S (Bracket 4+)
        for n in (1, 2, 3):
            r = self.check([], n, combos=c)
            self.assertTrue(r["ok"], n)
            self.assertEqual(r["two_card_combos"], [])
            self.assertTrue(any("rates it for Bracket 4 or higher" in note and "only two-card combos" in note
                                for note in r["notes"]), r["notes"])
        self.assertFalse(any("Bracket 4 or higher" in note for note in self.check([], 4, combos=c)["notes"]))

    def test_every_two_card_combo_is_listed_even_where_it_is_allowed(self):
        r = self.check([], 4, combos=found(["9001-0001", "9001-0004", "9001-0005"]))
        self.assertTrue(r["ok"])
        self.assertEqual(r["two_card_combos"], [
            {"cards": ["Chatterfang, Squirrel General", "Pitiless Plunderer"],
             "produces": ["Infinite ETB triggers", "Infinite sacrifice triggers"],
             "url": "https://commanderspellbook.com/combo/9001-0001/", "min_bracket": 4, "infinite": True},
            {"cards": ["Demonic Consultation", "Thassa's Oracle"], "produces": ["Win the game"],
             "url": "https://commanderspellbook.com/combo/9001-0004/", "min_bracket": 3, "infinite": False}])

    def test_without_combo_data_combos_are_not_checked_and_the_result_says_so(self):
        r = self.check(["Sol Ring"], 3, combos=None)
        self.assertTrue(r["ok"])
        self.assertTrue(any("Combos were not checked" in n for n in r["notes"]))
        self.assertEqual(r["two_card_combos"], [])

    # -- the list itself
    def test_unknown_names_are_noted_not_fatal(self):
        r = self.check(["Sol Ring", "Not A Real Card", "Another Fake"], 3)
        (note,) = [n for n in r["notes"] if "not found" in n]
        self.assertIn("2 card names", note)
        self.assertIn("Not A Real Card", note)
        self.assertTrue(r["ok"])

    def test_counted_pairs_and_repeats_count_a_card_once(self):
        """decklist.resolve gives (count, name) pairs; a basic land or a repeated line is one card here."""
        r = self.check([(1, "Sol Ring"), (1, "Armageddon"), "Armageddon", (10, "Forest")], 3)
        self.assertEqual(r["mass_land_denial"], ["Armageddon"])

    def test_a_single_commander_name_is_accepted(self):
        self.assertTrue(brackets.check(self.HAZEL, ["Sol Ring"], 3, CARDS, combos=NO_COMBOS)["ok"])

    def test_the_bracket_must_be_one_to_five(self):
        with self.assertRaises(ValueError):
            self.check([], 7)


class BlockedAddsTest(unittest.TestCase):
    def test_bracket_three_blocks_the_card_that_would_finish_a_tag_four_combo(self):
        out = brackets.blocked_adds(3, ALL_ALMOST)
        self.assertEqual(set(out), {"Pitiless Plunderer"})
        reason = out["Pitiless Plunderer"]
        self.assertIn("completes a two-card combo with Chatterfang, Squirrel General", reason)
        self.assertIn("rates it for Bracket 4 or higher", reason)
        # Spawnsire + Plunderer (tag R) is a second combo that the same card would finish
        self.assertIn("(and 1 more such combos)", reason)

    def test_bracket_two_also_blocks_what_would_finish_a_bracket_three_combo_or_a_two_card_infinite(self):
        out = brackets.blocked_adds(2, ALL_ALMOST)
        self.assertEqual(set(out), {"Pitiless Plunderer", "Thassa's Oracle", "Dramatic Reversal"})
        self.assertIn("rates it for Bracket 3 or higher, and Bracket 2 allows no two-card combos",
                      out["Thassa's Oracle"])
        # Isochron Scepter + Dramatic Reversal is tagged Exhibition, yet it is two-card and infinite
        self.assertIn("a two-card infinite combo, which Bracket 2 does not allow", out["Dramatic Reversal"])

    def test_a_two_card_infinite_tagged_exhibition_is_blocked_at_one_and_two_only(self):
        self.assertIn("Dramatic Reversal", brackets.blocked_adds(1, ALL_ALMOST))
        self.assertNotIn("Dramatic Reversal", brackets.blocked_adds(3, ALL_ALMOST))

    def test_a_combo_missing_two_cards_or_a_template_names_no_card_to_block(self):
        """Hazel + Skullclamp + Woe Strider lacks two cards; Chatterfang + Skullclamp lacks only 'any
        sacrifice outlet', a need that is not a card name."""
        self.assertEqual(brackets.blocked_adds(3, found(almost=["9002-0003", "9002-0005"])), {})

    def test_bracket_four_blocks_nothing_and_no_data_is_fine(self):
        self.assertEqual(brackets.blocked_adds(4, ALL_ALMOST), {})
        self.assertEqual(brackets.blocked_adds(3, None), {})
        self.assertEqual(brackets.blocked_adds(3, {"included": []}), {})


class CanAddTest(unittest.TestCase):
    def test_game_changer_limit(self):
        rhystic = CARDS["Rhystic Study"]
        self.assertEqual(brackets.can_add(rhystic, {"gc": 2}, 3), (True, ""))
        ok, why = brackets.can_add(rhystic, {"gc": 3}, 3)
        self.assertFalse(ok)
        self.assertIn("Rhystic Study is a Game Changer; Bracket 3 allows up to 3, and the list already has 3",
                      why)
        ok, why = brackets.can_add(rhystic, {}, 2)
        self.assertEqual((ok, why), (False, "Rhystic Study is a Game Changer; Bracket 2 allows none"))
        self.assertEqual(brackets.can_add(rhystic, {"gc": 9}, 4), (True, ""))

    def test_mass_land_denial_is_only_allowed_from_bracket_four(self):
        armageddon = CARDS["Armageddon"]
        ok, why = brackets.can_add(armageddon, {}, 3)
        self.assertEqual((ok, why), (False, "Armageddon is mass land denial, which Bracket 3 does not allow"))
        self.assertEqual(brackets.can_add(armageddon, {}, 4), (True, ""))

    def test_the_second_extra_turn_card_is_the_one_that_is_refused(self):
        time_warp = CARDS["Time Warp"]
        self.assertEqual(brackets.can_add(time_warp, {"extra_turns": 0}, 3), (True, ""))
        ok, why = brackets.can_add(time_warp, {"extra_turns": 1}, 3)
        self.assertFalse(ok)
        self.assertIn("would be a second extra-turn card", why)
        self.assertEqual(brackets.can_add(time_warp, {}, 1),
                         (False, "Time Warp is an extra-turn card; Bracket 1 allows none"))
        self.assertEqual(brackets.can_add(time_warp, {"extra_turns": 5}, 4), (True, ""))

    def test_an_ordinary_card_and_a_missing_state_are_fine(self):
        sol_ring = CARDS["Sol Ring"]
        for n in range(1, 6):
            self.assertEqual(brackets.can_add(sol_ring, None, n), (True, ""))
            self.assertEqual(brackets.can_add(sol_ring, {}, n), (True, ""))


if __name__ == "__main__":
    unittest.main()
