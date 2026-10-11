"""Tests for fantasy.py: the menu, spec validation, the optional Claude translation and the spec built from a
command line.

The claude command and the token are always mocked (Isolated.setUp closes every door to the real thing), so
no test runs claude, reads a real token or touches the network. Canned menus and replies are in fixtures/."""
import argparse, copy, json, os, subprocess, tempfile, unittest
from types import SimpleNamespace
from unittest import mock
from mtgcommander import config, fantasy

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


MENU = fixture("fantasy_menu.json")      # combat, control, stax (Bracket 4+), value; four themes
REPLIES = fixture("fantasy_replies.json")  # canned `claude -p` output, clean and messy
ROLES = {"land", "ramp", "draw", "removal", "wipe", "counter", "protection", "recursion", "tutor", "finisher"}


class Isolated(unittest.TestCase):
    """Tests that may reach the Claude code path. Token, `claude` on PATH and subprocess.run are all patched."""

    def setUp(self):
        self.token = mock.patch.object(fantasy, "_token", return_value=None).start()
        self.which = mock.patch.object(fantasy.shutil, "which", return_value=None).start()
        self.run = mock.patch.object(fantasy.subprocess, "run",
                                     side_effect=AssertionError("the real claude must never run")).start()
        self.addCleanup(mock.patch.stopall)

    def claude_says(self, stdout, returncode=0, stderr=""):
        """Open the doors: a token, a claude command, and this canned answer."""
        self.token.return_value = "test-token"
        self.which.return_value = "/usr/local/bin/claude"
        self.run.side_effect = None
        self.run.return_value = SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class MenuTest(unittest.TestCase):
    def test_the_twelve_playstyles_in_the_designed_order(self):
        slugs = [p["slug"] for p in fantasy.menu()["playstyles"]]
        self.assertEqual(slugs, ["combat", "voltron", "go-wide", "aristocrats", "spellslinger", "control",
                                 "combo", "big-mana", "graveyard", "politics", "stax", "value"])

    def test_every_playstyle_describes_itself_in_one_sentence(self):
        for p in fantasy.menu()["playstyles"]:
            with self.subTest(p["slug"]):
                self.assertTrue(p["label"])
                self.assertTrue(p["description"].endswith("."))
                self.assertEqual(p["description"].count(". "), 0)  # one sentence
                self.assertIsInstance(p["themes"], list)

    def test_stax_needs_bracket_four_and_the_rest_do_not(self):
        need = {p["slug"]: p["min_bracket"] for p in fantasy.menu()["playstyles"]}
        self.assertEqual(need.pop("stax"), 4)
        self.assertEqual(set(need.values()), {1})

    def test_without_a_commander_the_themes_are_the_common_list(self):
        themes = fantasy.menu()["themes"]
        self.assertGreaterEqual(len(themes), 35)
        self.assertEqual({t["count"] for t in themes}, {None})
        slugs = {t["slug"] for t in themes}
        self.assertTrue({"tokens", "aristocrats", "plus-1-plus-1-counters", "squirrels"} <= slugs)

    def test_a_commanders_own_themes_replace_the_common_list_most_popular_first(self):
        meta = {"taglinks": [{"slug": "tokens", "label": "Tokens", "count": 1457},
                             {"slug": "squirrels", "label": "Squirrels", "count": 2200},
                             {"slug": "food", "count": 12}]}
        themes = fantasy.menu(meta)["themes"]
        self.assertEqual([(t["slug"], t["count"]) for t in themes], [("squirrels", 2200), ("tokens", 1457), ("food", 12)])
        self.assertEqual(themes[2]["label"], "Food")  # a missing label is made from the slug

    def test_a_commander_page_with_no_themes_falls_back_to_the_common_list(self):
        self.assertEqual(fantasy.menu({"taglinks": []}), fantasy.menu())
        self.assertEqual(fantasy.menu(None), fantasy.menu())


class PlaystylesFileTest(unittest.TestCase):
    """commander/playstyles.json is data other modules read; keep it self-consistent."""

    def setUp(self):
        self.data = fantasy._data()
        self.known = set(self.data["known_themes"])

    def test_role_changes_are_whole_numbers_for_known_roles(self):
        for slug, p in self.data["playstyles"].items():
            with self.subTest(slug):
                self.assertTrue(set(p["targets"]) <= ROLES)
                self.assertTrue(all(isinstance(v, int) and not isinstance(v, bool) for v in p["targets"].values()))

    def test_the_documented_examples(self):
        styles = self.data["playstyles"]
        self.assertEqual(styles["control"]["targets"], {"removal": 2, "counter": 2, "wipe": 1})
        self.assertEqual(styles["big-mana"]["targets"], {"ramp": 3, "land": 1})
        self.assertEqual(styles["combat"]["targets"]["finisher"], 1)
        self.assertEqual(styles["combat"]["targets"]["protection"], 1)
        self.assertEqual(styles["value"]["targets"], {})  # the default makes no adjustments
        self.assertEqual(styles["value"]["themes"], [])

    def test_every_theme_is_a_real_edhrec_slug(self):
        for slug, p in self.data["playstyles"].items():
            self.assertTrue(set(p["themes"]) <= self.known, slug)
        self.assertTrue({t["slug"] for t in self.data["common_themes"]} <= self.known)
        self.assertTrue(set(self.data["theme_matchers"]) <= self.known)

    def test_the_known_list_leaves_out_color_pages(self):
        self.assertTrue({"abzan", "mono-green", "colorless"}.isdisjoint(self.known))
        self.assertIn("pirates", self.known)

    def test_theme_matcher_regexes_compile(self):
        import re
        for slug, m in self.data["theme_matchers"].items():
            self.assertEqual(set(m), {"subtypes", "types", "text"}, slug)
            for pattern in m["text"]:
                re.compile(pattern)


class ValidateSpecTest(unittest.TestCase):
    def validate(self, **spec):
        return fantasy.validate_spec({"bracket": 3, **spec}, MENU)

    def test_a_clean_spec_passes_and_gets_the_defaults(self):
        spec, warnings = self.validate(themes=["tokens"], playstyle="combat")
        self.assertEqual(warnings, [])
        self.assertEqual(spec, {"themes": ["tokens"], "playstyle": "combat", "include": [], "exclude": [],
                                "weight": config.DEFAULT_FANTASY_WEIGHT, "keep_fun": True, "bracket": 3,
                                "text": None})

    def test_an_unknown_theme_is_dropped_with_a_suggestion(self):
        spec, warnings = self.validate(themes=["tokens", "tokenz"])
        self.assertEqual(spec["themes"], ["tokens"])
        (w,) = warnings
        self.assertIn("unknown theme 'tokenz' dropped", w)
        self.assertIn("tokens", w.split("Did you mean")[1])
        self.assertIn("`themes`", w)

    def test_a_real_edhrec_theme_that_is_not_on_the_menu_is_accepted(self):
        """The menu is short; a typed --theme pirates is a real EDHREC theme and must work."""
        spec, warnings = self.validate(themes=["pirates"])
        self.assertEqual((spec["themes"], warnings), (["pirates"], []))

    def test_theme_words_are_normalized_and_deduplicated(self):
        spec, warnings = self.validate(themes=["Go Wide", "+1/+1 Counters", "tokens", "Tokens"])
        self.assertEqual(spec["themes"], ["go-wide", "plus-1-plus-1-counters", "tokens"])
        self.assertEqual(warnings, [])

    def test_stax_needs_bracket_four(self):
        spec, warnings = self.validate(playstyle="stax", bracket=3)
        self.assertEqual(spec["playstyle"], "value")
        (w,) = warnings
        self.assertIn("Stax playstyle needs Bracket 4", w)
        spec, warnings = self.validate(playstyle="stax", bracket=4)
        self.assertEqual((spec["playstyle"], warnings), ("stax", []))

    def test_an_unknown_playstyle_falls_back_to_value(self):
        spec, warnings = self.validate(playstyle="comat")
        self.assertEqual(spec["playstyle"], "value")
        self.assertIn("unknown playstyle 'comat'; using value", warnings[0])
        self.assertIn("combat", warnings[0])

    def test_no_playstyle_means_value_without_a_warning(self):
        self.assertEqual(self.validate()[0]["playstyle"], "value")
        self.assertEqual(self.validate()[1], [])

    def test_the_weight_stays_between_zero_and_one(self):
        cases = {1.5: (1.0, True), -2: (0.0, True), 0.25: (0.25, False), 0: (0.0, False), 1: (1.0, False),
                 None: (config.DEFAULT_FANTASY_WEIGHT, False), float("nan"): (config.DEFAULT_FANTASY_WEIGHT, False)}
        for given, (expected, warns) in cases.items():
            with self.subTest(weight=given):
                spec, warnings = self.validate(weight=given)
                self.assertEqual(spec["weight"], expected)
                self.assertEqual(bool(warnings), warns)

    def test_keep_it_fun_defaults_on_through_bracket_three_and_off_above(self):
        """Salt penalty: on at Brackets 1-3, off at 4-5, unless the player says otherwise."""
        for n, expected in {1: True, 2: True, 3: True, 4: False, 5: False}.items():
            self.assertEqual(self.validate(bracket=n)[0]["keep_fun"], expected, n)
        self.assertFalse(self.validate(bracket=3, keep_fun=False)[0]["keep_fun"])
        self.assertTrue(self.validate(bracket=5, keep_fun=True)[0]["keep_fun"])

    def test_card_lists_are_cleaned_and_a_card_in_both_is_left_out_of_include(self):
        spec, warnings = self.validate(include=[" Sol Ring ", "sol ring", "Time Warp", ""],
                                       exclude=["time warp", "Armageddon"])
        self.assertEqual(spec["include"], ["Sol Ring"])
        self.assertEqual(spec["exclude"], ["time warp", "Armageddon"])  # excluding wins
        (w,) = warnings
        self.assertIn("Time Warp", w)

    def test_a_single_name_is_a_list_of_one(self):
        self.assertEqual(self.validate(include="Sol Ring")[0]["include"], ["Sol Ring"])

    def test_the_input_is_not_changed(self):
        spec = {"bracket": 3, "themes": ["Tokens", "nope"], "include": [" Sol Ring "], "weight": 3}
        before = copy.deepcopy(spec)
        fantasy.validate_spec(spec, MENU)
        self.assertEqual(spec, before)

    def test_the_text_is_trimmed_and_blank_text_is_none(self):
        self.assertEqual(self.validate(text="  a squirrel warlord ")[0]["text"], "a squirrel warlord")
        self.assertIsNone(self.validate(text="   ")[0]["text"])

    def test_the_bracket_must_be_one_to_five_and_none_means_the_default(self):
        for bad in (0, 6, "x"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                fantasy.validate_spec({"bracket": bad}, MENU)
        with mock.patch.object(config, "DEFAULT_BRACKET", 3):
            self.assertEqual(fantasy.validate_spec({}, MENU)[0]["bracket"], 3)


class TokenTest(unittest.TestCase):
    """The token is read as mtgdraft/ai.py reads it: the environment first, then claude-token.txt."""

    def test_the_environment_wins_and_is_stripped(self):
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "  from-env \n"}):
            self.assertEqual(fantasy._token(), "from-env")

    def test_the_file_at_the_repo_root_is_the_fallback(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.dict(os.environ), \
                mock.patch.object(config, "ROOT", root):
            os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
            self.assertIsNone(fantasy._token())  # no file at all
            path = os.path.join(root, "claude-token.txt")
            with open(path, "w") as f:
                f.write("from-file\n")
            self.assertEqual(fantasy._token(), "from-file")
            with open(path, "w") as f:
                f.write("  \n")
            self.assertIsNone(fantasy._token())  # an empty file is no token


class FromTextTest(Isolated):
    TEXT = "a squirrel warlord who drowns the table in tokens"

    def test_without_a_token_it_says_why_and_never_calls_claude(self):
        found, warnings = fantasy.from_text(self.TEXT, MENU)
        self.assertEqual(found, {})
        (w,) = warnings
        self.assertIn("no Claude token", w)
        self.assertIn("CLAUDE_CODE_OAUTH_TOKEN", w)
        self.assertIn("claude-token.txt", w)
        self.assertIn("`themes`", w)
        self.which.assert_not_called()
        self.run.assert_not_called()

    def test_without_the_claude_command_it_says_why(self):
        self.token.return_value = "test-token"
        found, warnings = fantasy.from_text(self.TEXT, MENU)
        self.assertEqual(found, {})
        self.assertIn("`claude` command is not on PATH", warnings[0])
        self.assertIn("`themes`", warnings[0])
        self.run.assert_not_called()

    def test_a_clean_answer_becomes_menu_words(self):
        self.claude_says(REPLIES["clean"])
        found, warnings = fantasy.from_text(self.TEXT, MENU)
        self.assertEqual(found, {"themes": ["squirrels", "tokens"], "playstyle": "combat"})
        self.assertEqual(warnings, [])

    def test_claude_is_called_the_way_ai_py_calls_it(self):
        self.claude_says(REPLIES["clean"])
        fantasy.from_text(self.TEXT, MENU)
        self.run.assert_called_once()
        args, kwargs = self.run.call_args
        self.assertEqual(args[0][:2], ["/usr/local/bin/claude", "-p"])
        self.assertEqual(len(args[0]), 3)
        self.assertEqual(kwargs["env"]["CLAUDE_CODE_OAUTH_TOKEN"], "test-token")
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual((kwargs["timeout"], kwargs["capture_output"], kwargs["text"]), (240, True, True))

    def test_the_prompt_gives_the_menu_and_the_text_and_forbids_naming_cards(self):
        self.claude_says(REPLIES["clean"])
        fantasy.from_text(self.TEXT, MENU)
        prompt = self.run.call_args[0][0][2]
        self.assertIn(self.TEXT, prompt)
        for word in ("combat", "control", "stax", "value", "tokens", "squirrels", "aristocrats",
                     "plus-1-plus-1-counters"):
            self.assertIn(word, prompt)
        self.assertIn("Never name a card or a commander", prompt)
        self.assertIn("Use only slugs from the two menus", prompt)
        self.assertIn('{"themes"', prompt)

    def test_a_chatty_answer_is_parsed_and_off_menu_words_are_dropped_with_warnings(self):
        """Claude wraps the JSON in prose, invents a theme, offers four real ones and picks a playstyle the
        menu does not have."""
        self.claude_says(REPLIES["chatty"])
        found, warnings = fantasy.from_text(self.TEXT, MENU)
        self.assertEqual(found, {"themes": ["tokens", "squirrels", "aristocrats"]})  # no playstyle: politics is off-menu
        joined = " | ".join(warnings)
        self.assertIn("'unicorn-farts'", joined)
        self.assertIn("kept the first 3", joined)
        self.assertIn("playstyle 'politics'", joined)

    def test_card_names_are_not_menu_words(self):
        """Claude never picks cards: a card name in `themes` is dropped like any other unknown word."""
        self.claude_says(REPLIES["cards_not_words"])
        found, warnings = fantasy.from_text(self.TEXT, MENU)
        self.assertEqual(found, {"themes": ["tokens"], "playstyle": "combat"})
        self.assertIn("'Sol Ring'", warnings[0])

    def test_a_valid_answer_that_chooses_nothing_is_not_an_error(self):
        self.claude_says(REPLIES["empty_object"])
        self.assertEqual(fantasy.from_text(self.TEXT, MENU), ({}, []))

    def test_failures_come_back_as_warnings_never_as_exceptions(self):
        cases = {  # what goes wrong: (how, expected words in the warning)
            "claude takes too long": (lambda: setattr(self.run, "side_effect", subprocess.TimeoutExpired("claude", 240)),
                                      "could not run claude"),
            "claude cannot start": (lambda: setattr(self.run, "side_effect", OSError("exec format error")),
                                    "could not run claude"),
            "claude rejects the token": (lambda: self.claude_says("", returncode=1, stderr="401 Unauthorized\nmore"),
                                         "401 Unauthorized"),
            "the reply is not JSON": (lambda: self.claude_says(REPLIES["not_json"]), "not valid JSON"),
            "the reply has no object": (lambda: self.claude_says(REPLIES["no_object"]), "no usable answer"),
            "the reply is empty": (lambda: self.claude_says(""), "no usable answer"),
        }
        for what, (arrange, words) in cases.items():
            with self.subTest(what):
                self.claude_says(REPLIES["clean"])  # open the doors, then break one thing
                arrange()
                found, warnings = fantasy.from_text(self.TEXT, MENU)
                self.assertEqual(found, {})
                (w,) = warnings
                self.assertIn(words, w)
                self.assertIn("`themes`", w)


class SpecFromArgsTest(Isolated):
    def spec(self, menu=MENU, **flags):
        return fantasy.spec_from_args(argparse.Namespace(**flags), menu=menu)

    def test_no_flags_gives_the_defaults(self):
        with mock.patch.object(config, "DEFAULT_BRACKET", 3):
            spec, warnings = fantasy.spec_from_args(argparse.Namespace())
        self.assertEqual(warnings, [])
        self.assertEqual(spec, {"themes": [], "playstyle": "value", "include": [], "exclude": [],
                                "weight": config.DEFAULT_FANTASY_WEIGHT, "keep_fun": True, "bracket": 3,
                                "text": None})

    def test_flags_become_the_spec(self):
        spec, warnings = self.spec(theme=["tokens,squirrels"], playstyle="combat", fantasy=None, fantasy_weight=0.8,
                                   include=["Sol Ring"], exclude=["Time Warp"], keep_fun=False, bracket=4)
        self.assertEqual(warnings, [])
        self.assertEqual(spec, {"themes": ["tokens", "squirrels"], "playstyle": "combat", "include": ["Sol Ring"],
                                "exclude": ["Time Warp"], "weight": 0.8, "keep_fun": False, "bracket": 4,
                                "text": None})

    def test_missing_attributes_are_fine(self):
        spec, warnings = self.spec(bracket=2)
        self.assertEqual((spec["bracket"], spec["playstyle"], spec["themes"], warnings), (2, "value", [], []))

    def test_a_typed_unknown_theme_warns(self):
        spec, warnings = self.spec(theme=["tokens", "tokenz"], bracket=3)
        self.assertEqual(spec["themes"], ["tokens"])
        self.assertIn("unknown theme 'tokenz'", warnings[0])

    def test_free_text_without_a_token_is_explained_and_kept(self):
        """Never fail silently: the spec still comes back, with the text and a warning that names the fix."""
        spec, warnings = self.spec(fantasy="a squirrel warlord", theme=["tokens"], bracket=3)
        self.assertEqual((spec["text"], spec["themes"]), ("a squirrel warlord", ["tokens"]))
        (w,) = warnings
        self.assertIn("no Claude token", w)
        self.assertIn("`themes`", w)
        self.run.assert_not_called()

    def test_claudes_words_join_the_typed_ones(self):
        self.claude_says('{"themes": ["squirrels", "tokens"], "playstyle": "control"}')
        spec, warnings = self.spec(fantasy="a squirrel warlord", theme=["aristocrats"], bracket=3)
        self.assertEqual(spec["themes"], ["aristocrats", "squirrels", "tokens"])  # typed first, no repeats
        self.assertEqual(spec["playstyle"], "control")
        self.assertEqual(warnings, [])
        self.assertEqual(spec["text"], "a squirrel warlord")

    def test_a_typed_playstyle_beats_claudes(self):
        self.claude_says('{"themes": [], "playstyle": "control"}')
        spec, _ = self.spec(fantasy="a squirrel warlord", playstyle="combat", bracket=3)
        self.assertEqual(spec["playstyle"], "combat")

    def test_claudes_stax_is_refused_below_bracket_four(self):
        self.claude_says(REPLIES["stax"])
        spec, warnings = self.spec(fantasy="lock the table down", bracket=3)
        self.assertEqual(spec["playstyle"], "value")
        self.assertIn("Stax playstyle needs Bracket 4", warnings[0])
        spec, warnings = self.spec(fantasy="lock the table down", bracket=4)
        self.assertEqual((spec["playstyle"], warnings), ("stax", []))

    def test_a_commanders_own_menu_is_what_the_words_are_checked_against(self):
        """A theme that EDHREC shows for this commander is valid even if the committed list predates it."""
        meta_menu = fantasy.menu({"taglinks": [{"slug": "zzz-brand-new-theme", "label": "Brand New", "count": 5}]})
        spec, warnings = self.spec(menu=meta_menu, theme=["zzz-brand-new-theme"], bracket=3)
        self.assertEqual((spec["themes"], warnings), (["zzz-brand-new-theme"], []))
        spec, warnings = self.spec(menu=MENU, theme=["zzz-brand-new-theme"], bracket=3)
        self.assertEqual(spec["themes"], [])


if __name__ == "__main__":
    unittest.main()
