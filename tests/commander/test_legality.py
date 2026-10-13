"""Tests for brackets.legality(): is the list a legal Commander deck, and which rule does it break.

Cards are real-shaped records built from the small Scryfall sample in fixtures/ (see test_carddb.py); a few
synthetic partners are copies of a sample record with another name, so every pairing rule has a yes and a no.
Nothing here touches the network."""
import copy, json, os, unittest
from mtgcommander import brackets, carddb

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def sample_cards():
    cards = {}
    with open(os.path.join(FIXTURES, "carddb_bulk_sample.jsonl"), encoding="utf-8") as f:
        for line in f:
            rec = carddb.card_record(json.loads(line))
            if rec and rec["name"] not in cards:
                cards[rec["name"]] = rec
    return cards


def variant(base, name, **changes):
    """A copy of a sample record under another name, for a card the sample lacks (a second partner)."""
    rec = copy.deepcopy(base)
    rec.update(name=name, front=name, oracle_id=name.lower().replace(" ", "-"), **changes)
    return rec


CARDS = sample_cards()
CARDS["Tymna the Weaver"] = variant(CARDS["Thrasios, Triton Hero"], "Tymna the Weaver", ci="WB")
CARDS["Kydele, Chosen of Kruphix"] = variant(CARDS["Thrasios, Triton Hero"], "Kydele, Chosen of Kruphix", ci="UG")
CARDS["Ardenn, Intrepid Archaeologist"] = variant(CARDS["Sophina, Spearsage Deserter"],
                                                  "Ardenn, Intrepid Archaeologist")
CARDS["Michelangelo, the Heart"] = variant(CARDS["Donatello, the Brains"], "Michelangelo, the Heart")
CARDS["Banned Restricted Card"] = variant(CARDS["Sol Ring"], "Banned Restricted Card", legal="restricted")
CARDS["Green Dwarves"] = variant(CARDS["Seven Dwarves"], "Green Dwarves", ci="G")   # "up to seven cards named"
DB = carddb.CardDB(CARDS)

HAZEL = "Hazel of the Rootbloom"  # a Legendary Creature in black and green, the usual single commander here


def filler(total, *named):
    """(count, name) pairs: the named cards once each, topped up with Forest and Swamp to `total` cards."""
    rest = total - len(named)
    return [(1, n) for n in named] + [(rest - rest // 2, "Forest"), (rest // 2, "Swamp")]


def kinds(report):
    return [p["kind"] for p in report["problems"]]


def problem(report, kind):
    return next(p for p in report["problems"] if p["kind"] == kind)


class LegalDeckTests(unittest.TestCase):
    def test_a_clean_hundred_card_list_is_legal(self):
        report = brackets.legality([HAZEL], filler(99, "Sol Ring", "Arcane Signet", "Command Tower"), DB)
        self.assertEqual(report, {"ok": True, "problems": []})

    def test_a_single_name_is_the_commander_and_bare_names_count_once(self):
        report = brackets.legality(HAZEL, ["Sol Ring"] + ["Forest"] * 49 + ["Swamp"] * 49, DB)
        self.assertTrue(report["ok"], report)

    def test_basic_lands_and_any_number_cards_may_repeat(self):
        cards = [(4, "Relentless Rats"), (7, "Green Dwarves")]
        cards += filler(99 - 11, "Sol Ring")
        self.assertTrue(brackets.legality([HAZEL], cards, DB)["ok"])

    def test_names_are_matched_loosely_like_a_decklist_would_spell_them(self):
        cards = [(1, "sol ring"), (1, "Bonecrusher Giant")] + filler(97)  # lower case; front face alone
        self.assertEqual(kinds(brackets.legality([HAZEL], cards, DB)), ["color"])  # red card, not a typo


class CountTests(unittest.TestCase):
    def test_ninety_eight_cards_and_a_commander_is_one_short(self):
        report = brackets.legality([HAZEL], filler(98), DB)
        self.assertEqual(kinds(report), ["count"])
        self.assertIn("99", problem(report, "count")["message"])    # 98 + the commander
        self.assertIn("100", problem(report, "count")["message"])

    def test_one_card_too_many_is_reported_too(self):
        self.assertEqual(kinds(brackets.legality([HAZEL], filler(100), DB)), ["count"])

    def test_two_commanders_count_toward_the_hundred(self):
        report = brackets.legality(["Thrasios, Triton Hero", "Tymna the Weaver"], filler(98, "Sol Ring"), DB)
        self.assertTrue(report["ok"], report)

    def test_a_name_the_index_lacks_still_counts_toward_the_total_but_is_not_flagged(self):
        cards = filler(98) + [(1, "Sol Rign")]           # the typo is the caller's report; the total is whole
        self.assertTrue(brackets.legality([HAZEL], cards, DB)["ok"])


class CardRuleTests(unittest.TestCase):
    def test_a_card_outside_the_commanders_colors_is_a_color_problem(self):
        cards = filler(99, "Swords to Plowshares", "Brainstorm", "Sol Ring", "Command Tower")
        report = brackets.legality([HAZEL], cards, DB)
        self.assertEqual(kinds(report), ["color"])
        self.assertEqual(problem(report, "color")["cards"], ["Swords to Plowshares", "Brainstorm"])
        self.assertIn("(BG)", problem(report, "color")["message"])

    def test_colorless_cards_and_basic_lands_of_the_commanders_colors_fit_anywhere(self):
        self.assertTrue(brackets.legality([HAZEL], filler(99, "Sol Ring", "Mana Crypt"), DB)["ok"])

    def test_a_colorless_commander_says_so(self):
        cards = filler(99, "Cultivate")
        report = brackets.legality(["The Eternity Elevator"], cards, DB)
        # The Elevator is a Spacecraft with no power and toughness here, so it also cannot lead; the colors are
        # what this test reads.
        self.assertIn("colorless", problem(report, "color")["message"])

    def test_two_commanders_share_one_identity_the_union_of_both(self):
        pair = ["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"]          # green and blue
        report = brackets.legality(pair, filler(98, "Rhystic Study", "Demonic Tutor"), DB)
        self.assertEqual(problem(report, "color")["cards"], ["Demonic Tutor", "Swamp"])  # black is outside G+U

    def test_a_second_copy_of_a_normal_card_is_a_duplicate(self):
        report = brackets.legality([HAZEL], [(2, "Sol Ring")] + filler(97), DB)
        self.assertEqual(kinds(report), ["duplicate"])
        self.assertEqual(problem(report, "duplicate")["cards"], ["Sol Ring"])
        self.assertIn("Sol Ring x2", problem(report, "duplicate")["message"])

    def test_the_same_card_spelled_two_ways_is_still_a_duplicate(self):
        cards = [(1, "Sol Ring"), (1, "sol ring")] + filler(97)
        self.assertEqual(kinds(brackets.legality([HAZEL], cards, DB)), ["duplicate"])

    def test_the_commander_also_in_the_ninety_nine_is_a_duplicate(self):
        report = brackets.legality([HAZEL], filler(99, HAZEL), DB)
        self.assertEqual(problem(report, "duplicate")["cards"], [HAZEL])

    def test_a_banned_card_is_banned_whether_it_leads_or_not(self):
        report = brackets.legality([HAZEL], filler(99, "Griselbrand"), DB)
        self.assertEqual(problem(report, "banned")["cards"], ["Griselbrand"])
        lead = brackets.legality(["Griselbrand"], filler(99), DB)
        self.assertEqual(problem(lead, "banned")["cards"], ["Griselbrand"])

    def test_cards_that_are_not_legal_or_are_restricted_are_not_legal(self):
        report = brackets.legality([HAZEL], filler(99, "Pick Your Poison", "Banned Restricted Card"), DB)
        self.assertEqual(problem(report, "not_legal")["cards"], ["Pick Your Poison", "Banned Restricted Card"])
        self.assertNotIn("banned", kinds(report))

    def test_every_kind_at_once_in_order_of_importance(self):
        cards = [(2, "Sol Ring"), (1, "Griselbrand"), (1, "Pick Your Poison"), (1, "Brainstorm")] + filler(50)
        report = brackets.legality([HAZEL], cards, DB)
        self.assertEqual(kinds(report), ["count", "banned", "not_legal", "color", "duplicate"])
        self.assertFalse(report["ok"])

    def test_a_long_list_of_offenders_is_shortened_in_the_message_but_kept_in_cards(self):
        names = ["Swords to Plowshares", "Wrath of God", "Brainstorm", "Counterspell", "Rhystic Study", "Fire // Ice",
                 "Bonecrusher Giant // Stomp", "Witch Enchanter // Witch-Blessed Meadow",
                 "Delver of Secrets // Insectile Aberration", "Acolyte of Bahamut"]
        report = brackets.legality([HAZEL], [(1, n) for n in names] + filler(89), DB)
        color = problem(report, "color")
        self.assertEqual(len(color["cards"]), 10)
        self.assertIn("and 2 more", color["message"])


class CommanderTests(unittest.TestCase):
    def check(self, commanders, total=99):
        return brackets.legality(commanders, filler(total - (len(commanders) - 1)), DB)

    def assertLegalPair(self, a, b):
        report = self.check([a, b])
        self.assertNotIn("commander", kinds(report), report)
        self.assertEqual(kinds(self.check([b, a])), kinds(report))   # the order does not matter

    def assertIllegalPair(self, a, b):
        self.assertIn("commander", kinds(self.check([a, b])))
        self.assertIn("commander", kinds(self.check([b, a])))

    def test_a_legendary_creature_can_lead(self):
        self.assertNotIn("commander", kinds(self.check([HAZEL])))

    def test_a_card_that_cannot_lead_is_a_commander_problem(self):
        report = self.check(["Sol Ring"])
        self.assertIn("cannot be a commander", problem(report, "commander")["message"])

    def test_no_commander_is_a_problem_and_skips_the_color_check(self):
        report = brackets.legality([], filler(100, "Swords to Plowshares"), DB)
        self.assertEqual(kinds(report), ["commander"])
        self.assertIn("no commander", problem(report, "commander")["message"])

    def test_an_unknown_commander_is_reported_not_raised(self):
        report = brackets.legality(["Hazl of the Rootbloom"], filler(99), DB)
        self.assertIn("not found in the card index", problem(report, "commander")["message"])

    def test_three_commanders_are_too_many(self):
        report = brackets.legality(["Thrasios, Triton Hero", "Tymna the Weaver", "Kydele, Chosen of Kruphix"],
                                   filler(97), DB)
        self.assertIn("one or two commanders", problem(report, "commander")["message"])

    def test_two_partners_can_pair(self):
        self.assertLegalPair("Thrasios, Triton Hero", "Tymna the Weaver")

    def test_partner_with_pairs_only_the_two_named_cards(self):
        self.assertLegalPair("Pir, Imaginative Rascal", "Toothy, Imaginary Friend")
        self.assertIllegalPair("Pir, Imaginative Rascal", "Thrasios, Triton Hero")    # Pir wants Toothy
        self.assertIllegalPair("Toothy, Imaginary Friend", "Thrasios, Triton Hero")

    def test_friends_forever_pairs_with_friends_forever(self):
        self.assertLegalPair("Sophina, Spearsage Deserter", "Ardenn, Intrepid Archaeologist")
        self.assertIllegalPair("Sophina, Spearsage Deserter", "Thrasios, Triton Hero")

    def test_character_select_pairs_with_the_same_restriction_only(self):
        self.assertLegalPair("Donatello, the Brains", "Michelangelo, the Heart")
        self.assertIllegalPair("Donatello, the Brains", "Thrasios, Triton Hero")

    def test_choose_a_background_pairs_with_a_background(self):
        self.assertLegalPair("Halsin, Emerald Archdruid", "Acolyte of Bahamut")
        self.assertIllegalPair("Halsin, Emerald Archdruid", "Thrasios, Triton Hero")

    def test_a_background_cannot_lead_alone(self):
        self.assertIn("needs a commander with Choose a Background", problem(self.check(["Acolyte of Bahamut"]),
                                                                           "commander")["message"])

    def test_a_doctor_pairs_with_a_doctors_companion(self):
        self.assertLegalPair("The Eighth Doctor", "Nyssa of Traken")
        self.assertIllegalPair("The Eighth Doctor", "Thrasios, Triton Hero")

    def test_two_commanders_with_no_pairing_ability_cannot_share_a_deck(self):
        report = self.check([HAZEL, "Chatterfang, Squirrel General"])
        self.assertIn("cannot lead a deck together", problem(report, "commander")["message"])
        self.assertIn("no pairing ability", problem(report, "commander")["message"])

    def test_two_of_one_family_without_each_other_cannot_pair(self):
        self.assertIllegalPair("Halsin, Emerald Archdruid", "The Eighth Doctor")      # background vs doctor


if __name__ == "__main__":
    unittest.main()
