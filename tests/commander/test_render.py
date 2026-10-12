"""Tests for render.py: the text reports and the JSON wrapper, from small hand-made result dicts in fixtures/.

The fixtures are in the shapes the design lists for each command (the engine's output), so a golden substring
here is also a check that the report reads the documented keys. Every report must stay within 100 characters a
line (phone width), even for long card names and long evidence. Nothing here touches the network."""
import json, os, unittest
from mtgcommander import render, roles

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
COMMANDS = ("check", "upgrade", "build", "suggest", "themes", "warm", "validate", "stats")


def fixture(command):
    with open(os.path.join(FIXTURES, f"render_{command}.json"), encoding="utf-8") as f:
        return json.load(f)


def line_with(text, start):
    """The first line that begins with `start`."""
    return next(line for line in text.splitlines() if line.startswith(start))


class WidthMixin:
    def assertFits(self, text):
        for line in text.splitlines():
            self.assertLessEqual(len(line), 100, line)
            self.assertEqual(line, line.rstrip(), "trailing space: " + repr(line))


class JsonTests(unittest.TestCase):
    def test_the_schema_comes_first_and_the_rest_follows(self):
        out = json.loads(render.as_json({"command": "check", "warnings": []}))
        self.assertEqual(list(out), ["schema", "command", "warnings"])
        self.assertEqual(out["schema"], 1)

    def test_the_text_starts_with_the_schema_line(self):
        self.assertTrue(render.as_json(fixture("upgrade")).startswith('{\n  "schema": 1,\n  "command": "upgrade"'))

    def test_a_schema_key_in_the_result_does_not_win(self):
        self.assertEqual(json.loads(render.as_json({"schema": 7, "command": "x"}))["schema"], 1)

    def test_accents_stay_readable(self):
        out = render.as_json({"command": "build", "cards": [{"name": "Lim-Dûl's Vault"}]})
        self.assertIn("Lim-Dûl's Vault", out)
        self.assertNotIn("\\u00fb", out)

    def test_sets_become_sorted_lists_instead_of_failing(self):
        out = json.loads(render.as_json({"command": "build", "owned": {"b", "a"}}))
        self.assertEqual(out["owned"], ["a", "b"])

    def test_every_fixture_survives_a_round_trip(self):
        for command in COMMANDS:
            with self.subTest(command=command):
                result = fixture(command)
                body = json.loads(render.as_json(result))
                self.assertEqual({k: v for k, v in body.items() if k != "schema"}, result)


class EveryReportTests(unittest.TestCase, WidthMixin):
    def test_each_fixture_renders_within_phone_width(self):
        for command in COMMANDS:
            with self.subTest(command=command):
                text = render.text(fixture(command))
                self.assertTrue(text.strip())
                self.assertFits(text)

    def test_long_names_long_evidence_and_long_warnings_still_fit(self):
        long_name = "Aaaaaaaaaaaaaaaaaaaaaaaaaaa, Bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb // Ccccccccccccccccccccccccccc Dddd"
        long_text = "in 62% of 1,125 Bracket 3 Hazel decks " * 8
        up = fixture("upgrade")
        up["deck"]["name"] = long_name
        up["swaps"][0].update(cut=long_name, add=long_name, evidence_add=long_text, evidence_cut=long_text)
        up["blocked"][0]["reason"] = long_text
        up["warnings"] = [long_text]
        build = fixture("build")
        build["cards"][0].update(name=long_name, evidence=long_text)
        build["warnings"] = [long_text]
        check = fixture("check")
        check["legality"]["problems"][0]["message"] = long_text
        check["bracket_check"]["notes"] = [long_text]
        for result, verbose in ((up, True), (build, True), (check, False)):
            with self.subTest(command=result["command"]):
                self.assertFits(render.text(result, verbose=verbose))

    def test_a_result_with_only_its_command_still_prints(self):
        for command in COMMANDS:
            with self.subTest(command=command):
                text = render.text({"command": command})
                self.assertIsInstance(text, str)
                self.assertFits(text)

    def test_the_text_has_no_trailing_newline_so_print_adds_exactly_one(self):
        self.assertFalse(render.text(fixture("check")).endswith("\n"))

    def test_an_unknown_command_is_an_error_not_an_empty_report(self):
        with self.assertRaises(ValueError):
            render.text({"command": "frobnicate"})
        with self.assertRaises(ValueError):
            render.text({})

    def test_the_footer_names_every_source_with_its_fetch_date(self):
        text = render.text(fixture("upgrade"))
        for needle in ("EDHREC 2026-10-11", "EDHTop16 2026-10-10", "Commander Spellbook 2026-10-11",
                       "Scryfall 2026-10-09", "MTGJSON 2026-10-01"):
            self.assertIn(needle, " ".join(text.split()))      # the footer wraps, so compare without line breaks


class UpgradeTests(unittest.TestCase, WidthMixin):
    def setUp(self):
        self.result = fixture("upgrade")
        self.text = render.text(self.result)

    def test_the_header_follows_the_designs_example(self):
        self.assertEqual(self.text.splitlines()[0], "Squirreled Away → Bracket 3, budget $75 (spent $42.10); "
                                                    "themes: tokens; playstyle: aristocrats")
        self.assertEqual(self.text.splitlines()[1], "Hazel of the Rootbloom (BG), 100 cards")

    def test_a_swap_is_one_line_with_gain_and_price_and_an_indented_evidence_line(self):
        lines = self.text.splitlines()
        i = lines.index(" 1  CUT Haywire Mite  →  ADD Ashnod's Altar   +0.42  $1.20")
        self.assertTrue(lines[i + 1].startswith("    in 38% of 2,310 Bracket 3 Hazel decks (all brackets 35%"))
        self.assertIn("fills: ramp", lines[i + 1] + lines[i + 2])

    def test_an_owned_add_costs_nothing_and_says_why(self):
        self.assertIn(" 2  CUT Poison-Tip Archer  →  ADD Blood Artist   +0.31  $0.00  (owned)", self.text)

    def test_fills_lists_every_role_the_add_covers(self):
        self.assertIn("fills: finisher, draw", self.text)

    def test_blocked_cards_say_why(self):
        self.assertIn("Blocked: Pitiless Plunderer — completes a two-card infinite combo with Chatterfang", self.text)
        self.assertIn("Blocked: Ruination — mass land denial, which Bracket 3 does not allow", self.text)

    def test_only_the_roles_that_changed_are_listed_plus_lands(self):
        roles = line_with(self.text, "Roles:")
        self.assertEqual(roles, "Roles: lands 36→36  ramp 9→11  draw 8→10  removal 7→5  tutors 0→1  "
                                "finishers 3→4")
        for unchanged in ("wipes", "protection", "recursion", "counters"):
            self.assertNotIn(unchanged, roles)

    def test_a_role_still_outside_its_range_is_called_out(self):
        self.assertIn("Still off target: removal 5 (want 6-12)", self.text)

    def test_value_and_bracket_lines(self):
        self.assertIn("Value: 18.2 → 21.7 (+3.5)", self.text)
        self.assertIn("Bracket 3 limits: met before → met after; Game Changers 0 → 1 of 3", self.text)

    def test_a_deck_value_dict_prints_its_total(self):
        self.result["value_before"] = {"total": 18.2, "power": 15.0, "theme": 3.2}
        self.result["value_after"] = {"total": 21.7, "power": 17.0, "theme": 4.7}
        self.assertIn("Value: 18.2 → 21.7 (+3.5)", render.text(self.result))

    def test_cheap_adds_are_listed_when_there_are_some(self):
        self.assertIn("Cheapest useful adds:", self.text)
        self.assertIn("  Mind Stone  +0.09  $0.30", self.text)
        self.result["cheap_adds"] = []
        self.assertNotIn("Cheapest useful adds", render.text(self.result))

    def test_the_footer_says_plainly_that_below_bracket_five_these_are_builder_choices(self):
        flat = " ".join(self.text.split())
        self.assertIn("At Bracket 3 these numbers show what deck builders chose, not how often decks won.", flat)
        for bracket in (1, 2, 3, 4):
            with self.subTest(bracket=bracket):
                self.result["bracket"] = bracket
                self.assertIn(f"At Bracket {bracket} these numbers show what deck builders chose",
                              " ".join(render.text(self.result).split()))

    def test_bracket_five_does_not_claim_the_numbers_are_builder_choices(self):
        self.result["bracket"] = 5
        flat = " ".join(render.text(self.result).split())
        self.assertNotIn("not how often decks won", flat)
        self.assertIn("lean on tournament decks and results", flat)

    def test_a_source_reads_as_its_name(self):
        self.result["sources"]["scryfall_tags"] = {"fetched": "2026-10-09T04:00:00Z", "cache": "fresh"}
        self.result["sources"]["new_site"] = {"fetched": "2026-10-09T04:00:00Z", "cache": "fresh"}
        flat = " ".join(render.text(self.result).split())
        self.assertIn("Scryfall function tags 2026-10-09", flat)
        self.assertIn("new site 2026-10-09", flat)              # an unknown source still reads as words

    def test_a_stale_source_is_marked_in_the_footer(self):
        self.result["sources"]["edhrec"]["cache"] = "stale"
        self.assertIn("EDHREC 2026-10-11 (stale)", " ".join(render.text(self.result).split()))

    def test_warnings_come_last(self):
        lines = self.text.splitlines()
        self.assertIn("Warnings:", lines)
        self.assertGreater(lines.index("Warnings:"), max(i for i, l in enumerate(lines) if l.startswith("Sources:")))
        self.assertIn("  - edhtop16: only 40 tournament entries", self.text)

    def test_a_forced_cut_comes_with_its_reason(self):
        swap = self.result["swaps"][0]
        swap.update(forced=True, owned=False, reason="Bracket 3 allows up to 3 Game Changers; this list has 4.")
        text = render.text(self.result)
        self.assertIn("+0.42  $1.20  (forced)", text)
        self.assertIn("    forced: Bracket 3 allows up to 3 Game Changers; this list has 4.", text)

    def test_owned_and_forced_marks_go_together(self):
        self.result["swaps"][1]["forced"] = True
        self.assertIn("(owned, forced)", render.text(self.result))

    def test_evidence_for_the_cut_shows_only_when_verbose(self):
        self.assertNotIn("cut: in 3% of 2,310", self.text)
        self.assertIn("    cut: in 3% of 2,310 Bracket 3 Hazel decks", render.text(self.result, verbose=True))

    def test_the_verbose_flag_can_also_ride_in_the_result(self):
        self.result["verbose"] = True
        self.assertIn("cut: in 3% of 2,310", render.text(self.result))
        self.assertNotIn("cut: in 3% of 2,310", render.text(self.result, verbose=False))

    def test_two_long_names_move_to_two_lines_instead_of_overflowing(self):
        name = "Mmmmmmmmmmmmmmmmm, Nnnnnnnnnnnnnn // Ooooooooooooooooo"   # 52 characters, a long double-faced card
        self.result["swaps"][0].update(cut=name, add=name)
        text = render.text(self.result)
        self.assertIn(f" 1  CUT {name}", text.splitlines())
        self.assertIn(f"    ADD {name}   +0.42  $1.20", text.splitlines())
        self.assertFits(text)

    def test_a_card_without_data_says_so(self):
        self.result["swaps"][3].update(evidence_add="", fills=[])
        self.assertIn("    no deck data for this card", render.text(self.result))

    def test_no_swaps_says_why_nothing_is_shown(self):
        self.result["swaps"] = []
        self.assertIn("No swaps: nothing available improves this deck within the budget and the Bracket 3 rules.",
                      render.text(self.result))

    def test_no_budget_and_no_themes(self):
        self.result.update(budget=None, spent=0.0)
        self.result["spec"].update(themes=[], playstyle="value")
        first = render.text(self.result).splitlines()[0]
        self.assertEqual(first, "Squirreled Away → Bracket 3, no budget (spent $0.00); themes: none; playstyle: value")

    def test_a_fractional_budget_keeps_its_cents(self):
        self.result["budget"] = 75.5
        self.assertIn("budget $75.50 (spent $42.10)", render.text(self.result))

    def test_a_list_still_over_the_limit_after_the_swaps_says_so(self):
        problem = {"rule": "game_changers", "cards": ["A"], "message": "4 Game Changers; Bracket 3 allows up to 3."}
        self.result["bracket_after"].update(ok=False, violations=[problem])
        text = render.text(self.result)
        self.assertIn("1 problem after", text)
        self.assertIn("  Still over the limit:\n    - 4 Game Changers; Bracket 3 allows up to 3.", text)

    def test_bare_bracket_numbers_in_place_of_reports_still_print(self):
        self.result.update(bracket_before=2, bracket_after=3)
        self.assertIn("Bracket 3 limits: estimated 2 before → estimated 3 after", render.text(self.result))

    def test_the_written_file_is_named(self):
        self.result["out"] = "upgraded.txt"
        self.assertIn("Wrote the new list to upgraded.txt", render.text(self.result))

    def test_many_blocked_cards_are_cut_off_with_a_count(self):
        self.result["blocked"] = [{"card": f"Card {i}", "reason": "completes a combo"} for i in range(13)]
        text = render.text(self.result)
        self.assertIn("Blocked: Card 9 — completes a combo", text)
        self.assertNotIn("Card 10", text)
        self.assertIn("Blocked: and 3 more (see --json)", text)

    def test_swaps_print_in_the_order_given_numbered_by_rank(self):
        self.result["swaps"] = list(reversed(self.result["swaps"]))
        self.result["swaps"][0]["rank"] = 7
        self.assertIn(" 7  CUT Swarmyard Massacre", render.text(self.result))

    # --- answers to each kind of threat
    def test_the_answers_line_lists_the_kinds_whose_count_changed_right_after_the_roles(self):
        # the fixture: creatures 9 -> 8, planeswalkers 3 -> 2, spells 0 -> 1; artifacts, enchantments, lands and
        # graveyards stay where they were
        lines = self.text.splitlines()
        at = lines.index("Answers: creatures 9→8  planeswalkers 3→2  spells 0→1")
        self.assertTrue(lines[at - 1].startswith("Roles:"), lines[at - 1])                 # straight under the roles
        # the roles' own follow-up comes after the answers
        self.assertEqual(lines[at + 1], "Still off target: removal 5 (want 6-12)")

    def test_a_kind_that_did_not_change_is_not_listed(self):
        line = line_with(self.text, "Answers:")
        for unchanged in ("artifacts", "enchantments", "lands", "graveyards"):
            self.assertNotIn(unchanged, line)

    def test_no_change_in_any_kind_prints_no_answers_line(self):
        self.result["answers_after"] = dict(self.result["answers_before"])
        self.assertNotIn("Answers:", render.text(self.result))

    def test_without_tag_data_there_are_no_counts_and_no_line(self):
        self.result["answers_before"] = self.result["answers_after"] = None
        self.assertNotIn("Answers:", render.text(self.result))
        del self.result["answers_before"], self.result["answers_after"]
        self.assertNotIn("Answers:", render.text(self.result))
        self.result["answers_before"] = {"answers_creatures": 3}                  # one side missing: nothing to compare
        self.assertNotIn("Answers:", render.text(self.result))

    def test_all_seven_kinds_changing_wrap_inside_phone_width_under_the_label(self):
        self.result["answers_before"] = {id_: 9 for id_ in roles.THREAT_IDS}
        self.result["answers_after"] = {id_: 12 for id_ in roles.THREAT_IDS}
        text = render.text(self.result)
        self.assertFits(text)
        lines = text.splitlines()
        at = next(i for i, l in enumerate(lines) if l.startswith("Answers:"))
        self.assertEqual(lines[at], "Answers: creatures 9→12  artifacts 9→12  enchantments 9→12  planeswalkers 9→12  "
                                    "lands 9→12")
        self.assertEqual(lines[at + 1], "         graveyards 9→12  spells 9→12")

    def test_the_answers_line_still_prints_when_the_roles_are_missing(self):
        del self.result["roles_before"], self.result["roles_after"]
        text = render.text(self.result)
        self.assertNotIn("Roles:", text)
        self.assertIn("Answers: creatures 9→8", text)

    def test_json_carries_the_answers_before_and_after(self):
        body = json.loads(render.as_json(self.result))
        self.assertEqual(body["answers_before"], self.result["answers_before"])
        self.assertEqual(body["answers_after"]["answers_spells"], 1)

    # --- price points: the budget climbed in steps
    def stepped(self):
        """The fixture's four swaps split over two price points: the first two found at $25, the other two at $75.
        The first two cost $1.20 and nothing (the second is owned); the deck was worth 18.2 to start."""
        for i, swap in enumerate(self.result["swaps"]):
            swap["price_point"] = 25.0 if i < 2 else 75.0
        self.result["price_points"] = [{"budget": 25.0, "spent": 1.2, "value": 18.9, "swaps": 2},
                                       {"budget": 75.0, "spent": 42.1, "value": 21.7, "swaps": 4}]
        return render.text(self.result).splitlines()

    def test_two_price_points_get_a_short_block_of_one_line_each_before_the_swaps(self):
        lines = self.stepped()
        self.assertEqual(lines[2:8], [
            "",
            "Price points (each includes the ones above it):",
            "  $25   spend  $1.20   value 18.9 (+0.7)   2 swaps",      # the change is from the 18.2 it started at
            "  $75   spend $42.10   value 21.7 (+3.5)   4 swaps",
            "",
            "Up to $25:"])
        self.assertTrue(lines[8].startswith(" 1  CUT Haywire Mite"))

    def test_the_swap_list_has_a_divider_where_the_price_point_changes(self):
        lines = self.stepped()
        at = lines.index("Up to $75:")
        self.assertEqual(lines[at - 1], "")                                  # set apart from the swap above it
        self.assertTrue(lines[at + 1].startswith(" 3  CUT Moonstone Eulogist"))
        # and none between swaps 1 and 2, which share a price point
        self.assertEqual([l for l in lines if l.startswith("Up to ")], ["Up to $25:", "Up to $75:"])

    def test_the_columns_line_up_whatever_the_amounts(self):
        self.stepped()
        self.result["price_points"] = [
            {"budget": 50.0, "spent": 48.2, "value": 91.0, "swaps": 9},
            {"budget": 1250.5, "spent": 1249.99, "value": 104.9, "swaps": 120}]
        self.result["value_before"] = 79.8
        lines = render.text(self.result).splitlines()
        rows = lines[lines.index("Price points (each includes the ones above it):") + 1:][:2]
        self.assertEqual(rows, ["  $50         spend    $48.20   value  91.0 (+11.2)     9 swaps",
                                "  $1,250.50   spend $1,249.99   value 104.9 (+25.1)   120 swaps"])
        self.assertEqual(len(rows[0]), len(rows[1]))
        self.assertFits("\n".join(lines))

    def test_forced_swaps_come_first_and_belong_to_no_price_point(self):
        self.stepped()
        self.result["swaps"][0].update(forced=True, owned=False, price_point=None,
                                       reason="Bracket 3 allows up to 3 Game Changers.")
        lines = render.text(self.result).splitlines()
        first = next(i for i, l in enumerate(lines) if l.startswith(" 1  CUT"))
        # straight from the block to the forced swap: there is no step above it
        self.assertEqual(lines[first - 2:first], ["  $75   spend $42.10   value 21.7 (+3.5)   4 swaps", ""])
        second = next(i for i, l in enumerate(lines) if l.startswith(" 2  CUT"))
        self.assertEqual(lines[second - 2:second], ["", "Up to $25:"])      # the first swap that has a step gets one

    def test_a_price_point_nothing_was_found_at_keeps_its_line_but_has_no_divider(self):
        self.stepped()
        self.result["price_points"].insert(1, {"budget": 50.0, "spent": 1.2, "value": 18.9, "swaps": 2})
        lines = render.text(self.result).splitlines()
        self.assertIn("  $50   spend  $1.20   value 18.9 (+0.7)   2 swaps", lines)
        self.assertEqual([l for l in lines if l.startswith("Up to ")], ["Up to $25:", "Up to $75:"])

    def test_one_price_point_or_none_changes_nothing(self):
        plain = render.text(self.result)
        self.assertNotIn("Price points", plain)
        self.assertNotIn("Up to ", plain)
        self.result["price_points"] = []
        self.assertEqual(render.text(self.result), plain)
        for swap in self.result["swaps"]:                          # a lone point is just the budget
            swap["price_point"] = 75.0
        self.result["price_points"] = [{"budget": 75.0, "spent": 42.1, "value": 21.7, "swaps": 4}]
        self.assertEqual(render.text(self.result), plain)

    def test_a_price_point_line_with_fields_missing_still_prints(self):
        self.result["price_points"] = [{"budget": 25.0}, {"budget": 75.0}]
        text = render.text(self.result)
        self.assertIn("  $25   spend $?   value ?   0 swaps", text)
        self.assertFits(text)

    def test_a_line_without_a_value_keeps_the_columns_of_the_others(self):
        self.stepped()
        del self.result["price_points"][1]["value"]
        lines = render.text(self.result).splitlines()
        rows = lines[lines.index("Price points (each includes the ones above it):") + 1:][:2]
        self.assertEqual(rows, ["  $25   spend  $1.20   value 18.9 (+0.7)   2 swaps",
                                "  $75   spend $42.10   value    ?          4 swaps"])
        self.assertEqual(len(rows[0]), len(rows[1]))

    # --- price points that leave the deck with fewer answers
    WEAK_ENCH = {"id": "answers_enchantments", "label": "enchantments", "before": 7, "after": 4, "target": 5}
    WEAK_WALK = {"id": "answers_planeswalkers", "label": "planeswalkers", "before": 7, "after": 3, "target": 5}

    def test_a_price_point_that_leaves_fewer_answers_carries_a_note_right_under_its_line(self):
        self.stepped()
        self.result["price_points"][1]["weakens"] = [self.WEAK_ENCH, self.WEAK_WALK]
        lines = render.text(self.result).splitlines()
        at = lines.index("  $75   spend $42.10   value 21.7 (+3.5)   4 swaps")
        self.assertEqual(lines[at + 1], "        fewer answers: enchantments 7 → 4 (typical 5), "
                                        "planeswalkers 7 → 3 (typical 5)")
        self.assertEqual(lines[at + 2], "")                              # then the swaps, as before
        # the first point has none, so nothing sits under it
        first = lines.index("  $25   spend  $1.20   value 18.9 (+0.7)   2 swaps")
        self.assertEqual(lines[first + 1], "  $75   spend $42.10   value 21.7 (+3.5)   4 swaps")

    def test_the_note_lines_up_under_the_spend_column_whatever_the_width_of_the_amounts(self):
        self.stepped()
        self.result["price_points"] = [
            {"budget": 50.0, "spent": 48.2, "value": 91.0, "swaps": 9, "weakens": [self.WEAK_ENCH]},
            {"budget": 1250.5, "spent": 1249.99, "value": 104.9, "swaps": 120}]
        self.result["value_before"] = 79.8
        lines = render.text(self.result).splitlines()
        at = next(i for i, l in enumerate(lines) if l.startswith("  $50 "))
        self.assertEqual(lines[at].index("spend"), lines[at + 1].index("fewer answers:"))

    def test_a_long_note_wraps_inside_phone_width_with_its_continuation_indented(self):
        self.stepped()
        weak = [dict(self.WEAK_ENCH, id=f"answers_{k}", label=k, before=12, after=1, target=6)
                for k in ("creatures", "artifacts", "enchantments", "planeswalkers", "graveyards", "spells")]
        self.result["price_points"][1]["weakens"] = weak
        text = render.text(self.result)
        self.assertFits(text)
        lines = text.splitlines()
        at = next(i for i, l in enumerate(lines) if l.startswith("        fewer answers: creatures 12 → 1"))
        self.assertTrue(lines[at + 1].startswith("            "))          # indented further than the note's first line
        self.assertIn("spells 12 → 1 (typical 6)", " ".join(l.strip() for l in lines[at:at + 3]))

    def test_the_points_own_change_is_what_prints_and_the_start_is_only_a_fallback(self):
        self.stepped()
        self.result["price_points"][0]["change"] = 0.74
        self.result["price_points"][1]["change"] = -1.26
        rows = render.text(self.result).splitlines()
        self.assertIn("  $25   spend  $1.20   value 18.9 (+0.7)   2 swaps", rows)       # 0.74 to one decimal
        # -1.26 to one decimal, not the +3.5 the start would give
        self.assertIn("  $75   spend $42.10   value 21.7 (-1.3)   4 swaps", rows)

    def test_a_point_with_an_empty_or_missing_weakens_prints_no_note(self):
        self.stepped()
        self.result["price_points"][0]["weakens"] = []
        self.assertNotIn("fewer answers", render.text(self.result))

    def test_the_label_falls_back_to_the_id_when_a_hand_made_entry_has_none(self):
        self.stepped()
        self.result["price_points"][0]["weakens"] = [{"id": "answers_lands", "before": 2, "after": 0, "target": 1}]
        self.assertIn("fewer answers: answers_lands 2 → 0 (typical 1)", render.text(self.result))

    def test_json_carries_the_price_points_and_the_step_of_each_swap(self):
        self.stepped()
        body = json.loads(render.as_json(self.result))
        self.assertEqual(body["price_points"], self.result["price_points"])
        self.assertEqual([s["price_point"] for s in body["swaps"]], [25.0, 25.0, 75.0, 75.0])


class BuildTests(unittest.TestCase, WidthMixin):
    def setUp(self):
        self.result = fixture("build")
        self.text = render.text(self.result)

    def test_header_counts_and_sections_in_the_designed_order(self):
        lines = self.text.splitlines()
        self.assertEqual(lines[0], "Hazel of the Rootbloom (BG) → Bracket 3, budget $75 (spent $61.20)")
        self.assertEqual(lines[1], "  themes: tokens; playstyle: go-wide")      # one line would be 102 wide
        self.assertEqual(lines[2], "25 cards plus the commander")
        order = [l for l in lines if l.endswith(")") and l.split(" ")[0] in render.SECTIONS]
        self.assertEqual([l.split(" ")[0] for l in order], ["Creatures", "Sorceries", "Artifacts", "Lands"])
        self.assertIn("Lands (18)", lines)                     # one nonbasic land and 17 basics

    def test_a_card_is_one_line_with_its_score_price_owned_mark_and_roles(self):
        line = line_with(self.text, "  Sol Ring")
        self.assertEqual(" ".join(line.split()), "Sol Ring 0.86 $0.00 owned, ramp")
        self.assertEqual(" ".join(line_with(self.text, "  Skullclamp").split()), "Skullclamp 0.58 $19.13 draw")

    def test_basics_are_one_line_most_numerous_first(self):
        self.assertIn("  Basics: Forest 9, Swamp 8", self.text)

    def test_cards_keep_the_engines_order_within_a_section(self):
        lines = self.text.splitlines()
        at = lambda start: lines.index(line_with(self.text, start))
        self.assertLess(at("  Sol Ring"), at("  Arcane Signet"))
        self.assertLess(at("  Arcane Signet"), at("  Skullclamp"))
        self.result["cards"].reverse()
        flipped = render.text(self.result).splitlines()
        self.assertLess(flipped.index(line_with("\n".join(flipped), "  Skullclamp")),
                        flipped.index(line_with("\n".join(flipped), "  Sol Ring")))

    def test_roles_against_targets_flag_what_is_off(self):
        roles = " ".join(" ".join(l.strip() for l in self.text.splitlines()
                                  if l.startswith("Roles:") or l.startswith("       ")).split())
        self.assertIn("lands 18 (34-38) LOW", roles)
        self.assertIn("counters 0 (0-6) protection", roles)    # in range: no flag
        self.assertIn("top-end 0 (max 7)", roles)

    def test_spent_and_value(self):
        self.assertIn("Spent $61.20 of $75; 2 of the cards are ones you own", self.text)
        self.assertIn("Value: 33.5 (power 29.8, theme 3.7)", self.text)

    def test_the_fantasy_cost_block(self):
        self.assertIn("Fantasy cost: The theme costs 2.1 points of strength (6%).", self.text)
        self.assertIn("  Strength 33.5 with the theme, 35.6 without it.", self.text)
        self.assertIn("  Left out: Rhystic Study (0.45), Eternal Witness (0.40).", self.text)
        self.assertIn("  Theme picks: Zulaport Cutthroat (tokens).", self.text)

    def test_the_gap_percent_is_the_engines_percent_number(self):
        for stored, shown in ((5.9, "(6%)"), (12.2, "(12%)"), (0.3, "(<1%)")):
            with self.subTest(stored=stored):
                self.result["fantasy_cost"]["gap_pct"] = stored
                self.assertIn(f"points of strength {shown}.", render.text(self.result))

    def test_without_a_gap_percent_it_is_worked_out_from_the_two_strengths(self):
        self.result["fantasy_cost"].pop("gap_pct")
        self.assertIn("The theme costs 2.1 points of strength (6%).", render.text(self.result))

    def test_a_theme_that_costs_nothing_says_so(self):
        self.result["fantasy_cost"].update(gap=0.0, gap_pct=0.0)
        self.assertIn("Fantasy cost: the theme costs nothing", render.text(self.result))

    def test_no_fantasy_block_without_a_fantasy_cost(self):
        self.result["fantasy_cost"] = None
        self.assertNotIn("Fantasy cost", render.text(self.result))

    def test_the_bracket_check_and_blocked_cards(self):
        self.assertIn("Bracket 3: ok; Game Changers 1 of 3; extra turns 0; mass land denial 0; two-card combos 0",
                      self.text)
        self.assertIn("Blocked: Pitiless Plunderer — completes a two-card infinite combo", self.text)

    def test_a_check_report_stored_under_bracket_itself_is_found_too(self):
        self.result["bracket"] = self.result.pop("bracket_check")
        text = render.text(self.result)
        self.assertIn("Bracket 3: ok; Game Changers 1 of 3", text)
        self.assertEqual(text.splitlines()[0].split(" → ")[1][:9], "Bracket 3")

    def test_violations_are_listed(self):
        self.result["bracket_check"].update(ok=False,
                                            violations=[{"message": "4 Game Changers; Bracket 3 allows up to 3."}])
        text = render.text(self.result)
        self.assertIn("Bracket 3: 1 problem;", text)
        self.assertIn("  - 4 Game Changers; Bracket 3 allows up to 3.", text)

    def evidence_cards(self, count):
        """`count` creature cards with score 1.00, 0.99, ... and an evidence line marked EVID-<n>."""
        self.result["cards"] = [{"name": f"Card {i:02}", "section": "Creatures", "roles": [], "score": 1 - i / 100,
                                 "price": 1.0, "owned": False, "evidence": f"EVID-{i:02}", "kind": "builder"}
                                for i in range(count)]
        self.result["basics"] = {}

    def test_only_the_twenty_highest_scoring_cards_get_evidence_by_default(self):
        self.evidence_cards(30)
        text = render.text(self.result)
        self.assertEqual(text.count("EVID-"), 20)
        self.assertIn("EVID-19", text)
        self.assertNotIn("EVID-20", text)

    def test_the_twenty_are_chosen_by_score_not_by_position(self):
        self.evidence_cards(30)
        self.result["cards"].reverse()                          # the best cards now come last
        text = render.text(self.result)
        self.assertIn("EVID-00", text)
        self.assertNotIn("EVID-29", text)

    def test_verbose_gives_every_card_its_evidence(self):
        self.evidence_cards(30)
        self.assertEqual(render.text(self.result, verbose=True).count("EVID-"), 30)
        self.result["verbose"] = True
        self.assertEqual(render.text(self.result).count("EVID-"), 30)

    def test_the_commander_is_not_listed_among_the_cards(self):
        self.result["cards"].append({"name": "Hazel of the Rootbloom", "section": "Creatures", "roles": [],
                                     "score": 1.0, "price": 4.0, "owned": False, "evidence": "", "kind": "none"})
        text = render.text(self.result)
        self.assertNotIn("  Hazel of the Rootbloom ", text)
        self.assertIn("25 cards plus the commander", text)

    def test_two_commanders(self):
        self.result.update(commanders=["Thrasios, Triton Hero", "Tymna the Weaver"], ci="WUBG")
        text = render.text(self.result)
        self.assertEqual(text.splitlines()[0].split(" → ")[0], "Thrasios, Triton Hero + Tymna the Weaver (WUBG)")
        self.assertIn("cards plus the commanders", text)

    def test_a_card_with_no_section_still_prints_under_other(self):
        self.result["cards"].append({"name": "Mystery Card", "section": None, "roles": [], "score": 0.1, "price": 1.0,
                                     "owned": False, "evidence": "", "kind": "none"})
        text = render.text(self.result)
        self.assertIn("Other (1)", text)
        self.assertIn("  Mystery Card", text)

    def test_a_colorless_commander(self):
        self.result.update(ci="")
        self.assertTrue(render.text(self.result).startswith("Hazel of the Rootbloom (colorless) →"))


class SuggestTests(unittest.TestCase, WidthMixin):
    def setUp(self):
        self.result = fixture("suggest")
        self.text = render.text(self.result)

    def test_header_and_ranked_commanders(self):
        lines = self.text.splitlines()
        self.assertEqual(lines[0], "Commanders for tokens; playstyle: go-wide (Bracket 3, colors BG, budget $100)")
        self.assertIn(" 1  Hazel of the Rootbloom (BG)   score 0.62", lines)
        self.assertIn(" 2  Chatterfang, Squirrel General (BG)   score 0.55", lines)

    def test_each_evidence_line_is_indented_under_its_commander(self):
        lines = self.text.splitlines()
        i = lines.index(" 1  Hazel of the Rootbloom (BG)   score 0.62")
        self.assertEqual(lines[i + 1], "      tokens: 1,457 of 12,321 Hazel decks (12%); go-wide themes 21%")
        self.assertTrue(lines[i + 3].startswith("      40 tournament entries"))

    def test_a_commander_without_evidence_text_is_described_from_its_numbers(self):
        self.assertIn("      tokens: 9,800 of 24,000 decks (41%)", self.text)
        self.assertIn("      5,100 decks at this bracket", self.text)
        self.assertIn("      you own 20% of them", self.text)

    def test_no_match_says_what_to_try(self):
        self.result["commanders"] = []
        self.assertIn("No commander matched. Try fewer themes, other colors, or a larger budget.",
                      render.text(self.result))

    def test_no_filters(self):
        self.result["filters"] = {"colors": None, "budget": None}
        self.assertTrue(render.text(self.result).startswith("Commanders for tokens; playstyle: go-wide (Bracket 3)"))

    def test_the_footer_carries_the_builder_choice_caveat(self):
        self.assertIn("not how often decks won", " ".join(self.text.split()))


class CheckTests(unittest.TestCase, WidthMixin):
    def setUp(self):
        self.result = fixture("check")
        self.text = render.text(self.result)

    def test_header(self):
        self.assertEqual(self.text.splitlines()[0],
                         "Squirreled Away: Hazel of the Rootbloom (BG), 101 cards; checked at Bracket 3")

    def test_legality_problems_are_listed_with_their_messages(self):
        self.assertIn("Legality: 3 problems", self.text)
        self.assertIn("  - 1 card outside the commander's colors (BG): Swords to Plowshares.", self.text)
        self.assertIn("  - Not found in the card index: Sol Rign (did you mean Sol Ring?).", self.text)

    def test_a_legal_list_says_ok(self):
        self.result["legality"] = {"ok": True, "problems": []}
        self.assertIn("Legality: ok", render.text(self.result))

    def test_the_bracket_block(self):
        self.assertIn("Bracket 3: 1 problem", self.text)
        self.assertIn("  Game Changers: 2 of 3 (Demonic Tutor, Skullclamp)", self.text)
        self.assertIn("  Mass land denial: none", self.text)
        self.assertIn("  Extra turns: none", self.text)
        self.assertIn("  Two-card combos: 1", self.text)

    def test_a_combo_shows_its_cards_its_result_and_its_link(self):
        lines = self.text.splitlines()
        i = lines.index("    Chatterfang, Squirrel General + Pitiless Plunderer (Infinite mana, Infinite tokens)")
        self.assertEqual(lines[i + 1], "      https://commanderspellbook.com/combo/3000-4871/")

    def test_the_estimate_and_notes(self):
        flat = " ".join(self.text.split())
        self.assertIn("Lowest bracket the list fits: 4 (a floor;", flat)
        self.assertIn("Note: Wizards says intent and how a deck plays decide its bracket", flat)

    def test_no_limit_brackets_say_so(self):
        self.result["bracket_check"].update(bracket=4, gc_max=None, violations=[], ok=True)
        self.result["bracket"] = 4
        self.assertIn("  Game Changers: 2 (no limit) (Demonic Tutor, Skullclamp)", render.text(self.result))

    def test_the_roles_table_gives_count_range_target_and_status(self):
        rows = {l.split()[0]: " ".join(l.split()) for l in self.text.splitlines() if l.startswith("  ")
                and l.split() and l.split()[0] in ("lands", "ramp", "draw", "wipes", "top-end")}
        self.assertEqual(rows["lands"], "lands 36 34-38 36 ok")
        self.assertEqual(rows["ramp"], "ramp 8 9-14 11 low, 1 short")
        self.assertEqual(rows["wipes"], "wipes 6 1-5 3 high, 1 over")
        self.assertEqual(rows["top-end"], "top-end 5 max 7 ok")

    def test_status_is_computed_when_the_result_omits_it(self):
        del self.result["roles"]["status"]
        flat = render.text(self.result)
        self.assertIn("low, 1 short", flat)
        self.assertIn("high, 1 over", flat)

    def test_the_curve(self):
        flat = " ".join(self.text.split())
        self.assertIn("Curve of nonland cards (mana value:count) 0:1 1:9 2:14 3:16 4:9 5:6 6:4 7+:1 average 3.1", flat)

    def test_the_footer_lists_sources_but_makes_no_builder_choice_claim(self):
        flat = " ".join(self.text.split())
        self.assertIn("Sources: Commander Spellbook 2026-10-11 (stale), Scryfall 2026-10-09, MTGJSON 2026-10-01.", flat)
        self.assertNotIn("deck builders chose", flat)

    def test_warnings(self):
        self.assertIn("  - Commander Spellbook was not reachable", self.text)


class ThemesWarmValidateTests(unittest.TestCase, WidthMixin):
    def test_themes_lists_playstyles_then_themes_with_counts(self):
        text = render.text(fixture("themes"))
        lines = text.splitlines()
        self.assertEqual(lines[0], "Playstyles (choose one with --playstyle)")
        self.assertTrue(lines[1].startswith("  combat        Combat        Win by attacking"))
        self.assertIn("Themes for Hazel of the Rootbloom (choose with --theme)", lines)
        self.assertEqual(" ".join(line_with(text, "  tokens").split()), "tokens Tokens 1,457")
        self.assertEqual(" ".join(line_with(text, "  squirrels").split()), "squirrels Squirrels")   # no count known

    def test_a_long_theme_list_is_cut_off_with_a_count(self):
        result = fixture("themes")
        result["themes"] = [{"slug": f"theme-{i}", "label": f"Theme {i}", "count": 100 - i} for i in range(45)]
        text = render.text(result)
        self.assertIn("  theme-29", text)
        self.assertNotIn("  theme-30", text)
        self.assertIn("  and 15 more (--json lists them all)", text)

    def test_a_playstyle_that_needs_a_higher_bracket_says_so(self):
        self.assertIn("(Bracket 4 and up)", render.text(fixture("themes")))

    def test_without_a_commander_the_list_is_called_common(self):
        result = fixture("themes")
        result.update(commander=None, commanders=[])
        self.assertIn("Common themes (choose with --theme;", render.text(result))

    def test_warm_prints_one_row_per_download_with_its_cache_state(self):
        text = render.text(fixture("warm"))
        self.assertEqual(text.splitlines()[0], "Downloaded for Hazel of the Rootbloom at Bracket 3; themes: tokens")
        self.assertEqual(" ".join(line_with(text, "  edhrec        network  2026-10-11  all").split()),
                         "edhrec network 2026-10-11 all-bracket page (12,321 decks)")
        self.assertIn("edhrec        stale    2026-10-01  tokens page for this commander (1,457 decks)", text)
        self.assertIn("fresh = already cached and in date; network = downloaded now; stale = an old copy", text)
        self.assertIn("ok = in the cache, with no date to show", " ".join(text.split()))
        self.assertIn("  - edhrec: no page for the Bracket 3 tokens combination; skipped.", text)

    def test_warm_with_nothing_says_so(self):
        result = fixture("warm")
        result["fetched"] = []
        self.assertIn("Nothing was downloaded.", render.text(result))

    def test_validate_table_and_summary(self):
        text = render.text(fixture("validate"))
        self.assertEqual(text.splitlines()[0],
                         "Validation at Bracket 3: leave-one-out against Archidekt Bracket 3 lists")
        self.assertEqual(" ".join(line_with(text, "  Hazel").split()), "Hazel of the Rootbloom 38 62% 55%")
        self.assertIn("Overall: overlap 61% against a baseline of 55% (n = 79)", text)
        self.assertIn("Role counts inside the middle half of real lists: 83%", text)
        self.assertIn("Builds that follow the Bracket rules: 100%", text)

    def test_validate_prints_free_form_sweep_and_calibration_blocks(self):
        text = render.text(fixture("validate"))
        self.assertIn("Weight sweep:", text)
        self.assertEqual(" ".join(line_with(text, "     0.2").split()), "0.2 0.61")
        self.assertIn("Calibration:", text)
        self.assertIn("  k_base: 200", text)
        self.assertIn("  note: judgment call at Bracket 3", text)

    def test_validate_without_a_sweep_or_calibration_omits_them(self):
        result = fixture("validate")
        result.update(sweep=None, calibration=None)
        text = render.text(result)
        self.assertNotIn("Weight sweep", text)
        self.assertNotIn("Calibration", text)

    def test_role_rates_per_role_print_as_a_list(self):
        result = fixture("validate")
        result["roles_in_iqr"] = {"ramp": 0.9, "draw": 0.75}
        text = render.text(result)
        self.assertIn("Role counts inside the middle half of real lists:", text)
        self.assertIn("  ramp: 90%", text)

    def test_the_upgrade_check_says_how_many_precons_moved_and_whether_the_money_held(self):
        text = render.text(fixture("validate"))
        flat = " ".join(text.split())                              # the header wraps at phone width
        self.assertIn("Upgrade check at Bracket 3 (budget $50): 1 of 3 precons ended nearer the role targets, "
                      "1 unchanged, 1 farther; every spend stayed within the budget.", flat)
        self.assertEqual(" ".join(line_with(text, "  Squirreled Away").split()), "Squirreled Away 9 3 $41.20 8")
        self.assertIn("0 means every role is inside its band", " ".join(text.split()))

    def test_a_partner_pair_widens_the_commander_column_so_the_figures_stay_lined_up(self):
        result = fixture("validate")
        pair = "Rograkh, Son of Rohgahh / Silas Renn, Seeker Adept"
        result["commanders"].append({"name": pair, "decks": 3, "overlap": 0.93, "baseline": 0.94})
        text = render.text(result)
        self.assertFits(text)
        self.assertEqual(" ".join(line_with(text, "  Rograkh").split()), f"{pair} 3 93% 94%")
        ends = {len(line_with(text, f"  {name}").rstrip()) for name in ("Hazel", "Chatterfang", "Rograkh")}
        self.assertEqual(len(ends), 1)                              # every row ends in the same column

    def test_an_overspend_is_named(self):
        result = fixture("validate")
        result["upgrade_check"].update(within_budget=False, over_budget=["Squirreled Away"])
        self.assertIn("over budget: Squirreled Away.", " ".join(render.text(result).split()))

    def test_a_long_precon_name_widens_its_column_so_the_numbers_stay_lined_up(self):
        text = render.text(fixture("validate"))
        self.assertFits(text)
        long_name = "Starter Commander Deck With A Rather Long Name"
        ends = {line_with(text, f"  {name}").index(figure) for name, figure in
                (("Squirreled Away", "9"), (long_name, "2"))}
        self.assertEqual(len(ends), 1)                              # "gap before" ends in one column for every row

    def test_without_an_upgrade_check_the_block_is_left_out(self):
        result = fixture("validate")
        result["upgrade_check"] = None
        self.assertNotIn("Upgrade check", render.text(result))

    def test_a_bracket_5_sweep_prints_as_a_table_of_percentages_with_one_decimal(self):
        result = fixture("validate")
        result["sweep"] = [{"w_bracket": w, "k_resid": k, "overlap": 0.7 + w / 100 + k / 10000, "decks": 32}
                           for w in (0, 1) for k in (25, 50)]
        text = render.text(result)
        self.assertIn("Weight sweep (mean overlap for each W_BRACKET[5] and K_RESID):", text)
        self.assertEqual(" ".join(line_with(text, "          0       25").split()), "0 25 70.2% 32")
        self.assertEqual(" ".join(line_with(text, "          1       50").split()), "1 50 71.5% 32")

    def test_a_calibration_report_prints_in_a_few_lines(self):
        result = fixture("validate")
        result["calibration"] = {
            "as_of": "2026-10-11", "written": "/repo/commander/role_targets.json",
            "labels": {"1": "judgment: Bracket 2 values with land target +1", "2": "measured: 60 recent precons",
                       "5": "measured: 120 EDHTop16 top-cut decks"},
            "changes": [f"Bracket 2 ramp: 8/10/13 -> 9/12/{n}" for n in range(15)],
            "brackets": {"1": {"land": [35, 38, 40]}}, "previous": {"1": {"land": [34, 37, 39]}}}
        text = render.text(result)
        self.assertIn("Calibration (wrote /repo/commander/role_targets.json):", text)
        self.assertIn("  Bracket 5: measured: 120 EDHTop16 top-cut decks", text)
        self.assertIn("  15 role numbers changed:", text)
        self.assertIn("    Bracket 2 ramp: 8/10/13 -> 9/12/11", text)
        self.assertNotIn("9/12/12", text)                          # only the first twelve are listed
        self.assertIn("    and 3 more", text)
        self.assertNotIn("previous", text)                         # the raw report is not dumped
        self.assertFits(text)

    def test_a_calibration_that_changed_nothing_says_so(self):
        result = fixture("validate")
        result["calibration"] = {"written": None, "labels": {"2": "measured: 60 recent precons"}, "changes": []}
        text = render.text(result)
        self.assertIn("Calibration (nothing written):", text)
        self.assertIn("  0 role numbers changed.", text)

    def test_a_calibration_that_also_wrote_the_power_numbers_names_that_file(self):
        result = fixture("validate")
        result["calibration"] = {"written": "/repo/commander/role_targets.json", "labels": {"2": "measured"},
                                 "changes": [], "metrics": {"written": "/repo/commander/metric_targets.json"}}
        text = render.text(result)
        self.assertIn("  Also wrote /repo/commander/metric_targets.json (removal and wipe power, and answer counts).",
                      text)
        result["calibration"]["metrics"] = None
        self.assertNotIn("Also wrote", render.text(result))

    def test_with_no_real_deck_compared_the_overall_line_says_so_instead_of_printing_question_marks(self):
        result = fixture("validate")
        result["commanders"] = [{"name": "Heliod, Sun-Crowned", "decks": 0, "overlap": None, "baseline": None}]
        result["overall"] = {"overlap": None, "baseline": None, "n": 0}
        text = render.text(result)
        self.assertIn("Overall: no real deck was compared (see the warnings).", text)
        self.assertEqual(" ".join(line_with(text, "  Heliod").split()), "Heliod, Sun-Crowned 0 ? ?")
        self.assertNotIn("against a baseline", text)


class StatsTests(unittest.TestCase, WidthMixin):
    def setUp(self):
        self.result = fixture("stats")
        self.text = render.text(self.result)
        self.flat_lines = [" ".join(line.split()) for line in self.text.splitlines()]

    def line(self, start):
        """The text of the first line that starts with `start` (spaces squeezed), so columns do not matter."""
        return next(l for l in self.flat_lines if l.startswith(start))

    def test_the_header_names_the_deck_the_bracket_and_the_fantasy(self):
        lines = self.text.splitlines()
        self.assertEqual(lines[0], "Squirreled Away → Bracket 3, no budget; themes: tokens; playstyle: aristocrats")
        self.assertEqual(lines[1], "Hazel of the Rootbloom (BG), 100 cards")

    def test_the_headline_has_the_five_numbers(self):
        self.assertIn("Score 93.77, Bracket 3 within its limits, 36 lands, removal power 5.95, cost to buy $185.43",
                      self.flat_lines)

    def test_every_group_has_a_heading_in_order(self):
        headings = [l for l in self.text.splitlines() if l and not l.startswith(" ")]
        order = [h for h in headings if h in ("Power", "Interaction", "Mana and consistency", "Playstyle", "Win plan",
                                              "Table and money", "Changes from the base deck")]
        self.assertEqual(order, ["Power", "Interaction", "Mana and consistency", "Playstyle", "Win plan",
                                 "Table and money", "Changes from the base deck"])

    def test_an_item_is_a_label_its_value_its_band_its_status_and_the_base_value(self):
        self.assertEqual(self.line("Removal power"), "Removal power 5.95 want 3.4-6.8 ok (was 7.61)")
        self.assertEqual(self.line("Lands "), "Lands 36 want 34-36 ok (was 38)")
        self.assertEqual(self.line("Tutors"), "Tutors 2 want 2-4 ok (was 0)")

    def test_a_number_outside_its_band_is_marked_short_or_over(self):
        self.assertEqual(self.line("Wipe power"), "Wipe power 0.61 want 0.7-1.9 SHORT (was 0.61)")
        self.assertEqual(self.line("Cards costing 6 or more"), "Cards costing 6 or more 9 max 8 OVER (was 5)")
        self.assertEqual(self.line("Finishers"), "Finishers 7 want 1-6 OVER (was 6)")
        self.assertEqual(self.line("Answers to spells"), "Answers to spells 0 at least 1 SHORT (was 0)")

    def test_a_band_with_one_end_reads_as_a_limit(self):
        self.assertEqual(self.line("Game Changers"), "Game Changers 0 max 3 ok (was 0)")
        self.assertEqual(self.line("Answers to creatures"), "Answers to creatures 10 at least 1 ok (was 14)")

    def test_shares_and_money_carry_their_units(self):
        self.assertEqual(self.line("Interaction at instant speed"), "Interaction at instant speed 43.8% (was 25%)")
        self.assertEqual(self.line("Cost to buy"), "Cost to buy $185.43 (was $0.00)")
        self.assertEqual(self.line("Cards you own"), "Cards you own 67.7% (was 100%)")

    def test_decimals_are_shown_to_two_places_without_trailing_zeros(self):
        self.assertEqual(self.line("Deck score"), "Deck score 93.77 (was 79.82)")
        self.assertEqual(self.line("Average mana value"), "Average mana value 2.84 (was 3.31)")
        self.assertEqual(self.line("Salt"), "Salt 0 (was 0)")

    def test_an_item_with_no_value_shows_a_dash_and_says_why_even_without_the_verbose_flag(self):
        lines = self.text.splitlines()
        i = next(n for n, l in enumerate(lines) if l.strip().startswith("Synergy with the commander"))
        self.assertEqual(" ".join(lines[i].split()), "Synergy with the commander -")
        self.assertTrue(lines[i + 1].startswith("      - No card has an EDHREC synergy score"))

    def test_the_card_index_not_recording_power_is_said_in_the_report(self):
        self.assertIn("The card index does not record creature power yet.", " ".join(self.text.split()))

    def test_without_the_verbose_flag_the_arithmetic_and_the_cards_stay_out(self):
        self.assertNotIn("Tear Asunder", self.text)
        self.assertNotIn("cards:", self.text)

    def test_the_verbose_flag_adds_each_items_cards_and_how_its_number_was_made(self):
        text = render.text(self.result, verbose=True)
        flat = " ".join(text.split())
        self.assertIn("cards: Tear Asunder, Assassin's Trophy", flat)
        self.assertIn("- Tear Asunder 1.00 = instant 1.0 × any permanent 1.0 × exile 1.0 × MV 2 1.0", flat)
        self.assertGreater(len(text.splitlines()), len(self.text.splitlines()))
        self.assertFits(text)

    def test_a_footnote_explains_the_was_column_only_when_there_is_one(self):
        self.assertIn("(was N) is the value in the base deck.", self.text)
        for group in self.result["groups"]:
            for item in group["items"]:
                item.pop("base", None)
        self.assertNotIn("(was N)", render.text(self.result))

    def test_the_footer_names_the_sources_and_the_kind_of_number(self):
        flat = " ".join(self.text.split())
        self.assertIn("Commander Spellbook 2026-10-11", flat)
        self.assertIn("Scryfall function tags 2026-10-09", flat)
        self.assertIn("At Bracket 3 these numbers show what deck builders chose, not how often decks won.", flat)

    def test_warnings_come_after_the_groups(self):
        lines = self.text.splitlines()
        self.assertGreater(lines.index("Warnings:"), lines.index("Changes from the base deck"))
        self.assertIn("  - Combos were checked against Commander Spellbook's daily file.", lines)

    def test_a_very_long_label_still_fits_the_page_width(self):
        self.result["groups"][0]["items"][0]["label"] = "A very long label " * 6
        self.assertFits(render.text(self.result))

    def test_the_json_keeps_the_schema_first_and_every_item_whole(self):
        body = json.loads(render.as_json(self.result))
        self.assertEqual(list(body)[:2], ["schema", "command"])
        self.assertEqual(body["schema"], 1)
        self.assertEqual(body["groups"], self.result["groups"])
        self.assertEqual(body["headline"], self.result["headline"])

    def test_a_result_without_groups_prints_only_its_header(self):
        text = render.text({"command": "stats", "deck": {"name": "Empty", "commanders": [], "count": 0}})
        self.assertTrue(text.startswith("Empty → Bracket ?, no budget"))
        self.assertFits(text)


if __name__ == "__main__":
    unittest.main()
