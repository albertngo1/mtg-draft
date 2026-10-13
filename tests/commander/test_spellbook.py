"""Tests for providers/spellbook.py. The network is replaced by recorded answers in fixtures/: the API's answers
for find-my-combos and estimate-bracket, and a small daily file (spellbook_variants.json, in the shape of the real
variants.json.gz) for the local index. Nothing here touches the network; caches live in a temporary directory."""
import copy, gzip, json, os, shutil, tempfile, time, unittest
from unittest import mock

from mtgcommander import config, net
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


# ----------------------------------------------------------------------------- the local combo index
COMMANDER_NAME = "Chatterfang, Squirrel General"
HAZEL = "Hazel of the Rootbloom"
# the fixture's variants, by id: 12 in the file, 9 after the 3 nobody can use are left out
KEPT_IDS = ["3000-4871", "1385-3000-5670", "997-6982--5", "9000-9001", "9100-9101", "9200-9201", "9300--88",
            "9400-9401-9402", "9500-9501"]
INDEX_DECK = ["Pitiless Plunderer", "Zulaport Cutthroat", "Sol Ring", "Skullclamp", "Relentless Rats", "Forest"]


def raw_variant(variant_id):
    return next(v for v in fixture("spellbook_variants.json")["variants"] if v["id"] == variant_id)


class TempCache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        mock.patch.object(net, "CACHE", self.tmp).start()
        self.addCleanup(mock.patch.stopall)
        spellbook.reset()
        self.addCleanup(spellbook.reset)


class DailyFileCase(TempCache):
    """The daily file saved in the temporary folder, as plain JSON and gzipped."""

    def setUp(self):
        super().setUp()
        self.plain = os.path.join(self.tmp, "variants.json")
        self.gzipped = os.path.join(self.tmp, "variants.json.gz")
        with open(os.path.join(FIXTURES, "spellbook_variants.json"), "rb") as f:
            self.raw = f.read()
        with open(self.plain, "wb") as f:
            f.write(self.raw)
        with gzip.open(self.gzipped, "wb") as f:
            f.write(self.raw)

    def ids(self, path, **kw):
        info, variants = spellbook.open_daily_file(path, **kw)
        return info, [v["id"] for v in variants]


class ReduceVariantTests(unittest.TestCase):
    def test_a_usable_variant_keeps_its_cards_results_tag_and_colors(self):
        kept, why = spellbook.reduce_variant(raw_variant("3000-4871"))
        self.assertEqual(why, "")
        self.assertEqual(kept, {"id": "3000-4871", "cards": [COMMANDER_NAME, "Pitiless Plunderer"], "requires": [],
                                "produces": ["Infinite Treasure tokens", "Infinite colored mana"], "tag": "S",
                                "identity": "BG", "leaders": []})

    def test_a_card_needed_twice_is_listed_twice(self):
        kept, _ = spellbook.reduce_variant(raw_variant("9200-9201"))
        self.assertEqual(kept["cards"], ["Relentless Rats", "Relentless Rats", "Sol Ring"])

    def test_a_card_that_must_be_the_commander_is_remembered(self):
        kept, _ = spellbook.reduce_variant(raw_variant("9100-9101"))
        self.assertEqual((kept["leaders"], kept["cards"]), ([HAZEL], [HAZEL, "Skullclamp"]))

    def test_a_template_is_kept_by_name(self):
        kept, _ = spellbook.reduce_variant(raw_variant("997-6982--5"))
        self.assertEqual(kept["requires"], ["Persist Creature"])

    def test_variants_nobody_can_use_are_left_out_with_the_reason(self):
        self.assertEqual(spellbook.reduce_variant(raw_variant("1368-4808-4856")), (None, "not legal"))   # Black Lotus
        self.assertEqual(spellbook.reduce_variant(raw_variant("8000-8001")), (None, "spoiler"))          # a card not out yet
        self.assertEqual(spellbook.reduce_variant(raw_variant("9600-9601")), (None, "status"))           # a draft
        self.assertEqual(spellbook.reduce_variant({"id": "1", "uses": []}), (None, "no cards"))

    def test_a_spoiler_flag_on_a_card_alone_is_enough(self):
        variant = copy.deepcopy(raw_variant("3000-4871"))
        variant["uses"][1]["card"]["spoiler"] = True
        self.assertEqual(spellbook.reduce_variant(variant), (None, "spoiler"))

    def test_a_variant_without_legalities_or_status_counts_as_legal_and_fine(self):
        kept, _ = spellbook.reduce_variant({"id": "1-2", "uses": [{"card": {"name": "A"}}], "produces": []})
        self.assertEqual((kept["cards"], kept["tag"], kept["identity"]), (["A"], "", ""))

    def test_colors_come_out_in_wubrg_order_and_colorless_is_empty(self):
        for text, expected in (("GWUB", "WUBG"), ("BG", "BG"), ("C", ""), ("", ""), (None, ""), ("WUBRG", "WUBRG")):
            self.assertEqual(spellbook._colors(text), expected, text)


class DailyFileTests(DailyFileCase):
    def test_every_variant_is_read_one_at_a_time_whatever_the_chunk_size(self):
        every = [v["id"] for v in fixture("spellbook_variants.json")["variants"]]
        for path in (self.plain, self.gzipped):
            for chunk in (1, 5, 64, 1000, spellbook.READ_CHUNK):
                with self.subTest(file=os.path.basename(path), chunk=chunk):
                    info, ids = self.ids(path, chunk=chunk)
                    self.assertEqual(ids, every)
                    self.assertEqual(info, {"timestamp": "2026-10-11T23:11:42.250594+00:00", "version": "7.1.9"})

    def test_the_list_after_the_variants_is_never_read(self):
        # the file ends with an `aliases` list of {"id", "variant"}: reading it as variants would add two more
        self.assertEqual(len(self.ids(self.plain)[1]), 12)

    def test_a_gzip_is_recognized_by_its_first_bytes_not_its_name(self):
        renamed = os.path.join(self.tmp, "daily.json")
        shutil.copy(self.gzipped, renamed)
        self.assertEqual(len(self.ids(renamed)[1]), 12)

    def test_names_with_accents_survive_any_chunk_boundary(self):
        info, variants = spellbook.open_daily_file(self.gzipped, chunk=3)
        names = [u["card"]["name"] for v in variants for u in v["uses"]]
        self.assertIn("Lim-D\u00fbl's Vault", names)

    def test_a_file_cut_off_in_the_middle_of_a_variant_is_an_error(self):
        cut = os.path.join(self.tmp, "cut.json")
        with open(cut, "wb") as f:
            f.write(self.raw[:self.raw.index(b"9100-9101")])
        for chunk in (7, spellbook.READ_CHUNK):
            with self.subTest(chunk=chunk):
                _, variants = spellbook.open_daily_file(cut, chunk=chunk)
                with self.assertRaises(ValueError):
                    list(variants)

    def test_a_list_that_never_closes_is_an_error(self):
        text = self.raw.decode("utf-8")
        end = text.index('"aliases"')                    # drop the closing bracket of the variants and all after
        cut = os.path.join(self.tmp, "open.json")
        with open(cut, "w", encoding="utf-8") as f:
            f.write(text[:end].rstrip().rstrip(",").rstrip("]"))
        _, variants = spellbook.open_daily_file(cut)
        with self.assertRaisesRegex(ValueError, "never ends"):
            list(variants)

    def test_a_truncated_gzip_is_an_error(self):
        short = os.path.join(self.tmp, "short.json.gz")
        with open(self.gzipped, "rb") as src, open(short, "wb") as out:
            out.write(src.read()[:200])
        with self.assertRaises((EOFError, ValueError, OSError)):
            list(spellbook.open_daily_file(short)[1])

    def test_a_file_with_no_list_of_variants_is_an_error(self):
        other = os.path.join(self.tmp, "other.json")
        with open(other, "w") as f:
            f.write('{"timestamp": "x", "version": "1", "cards": []}')
        with self.assertRaisesRegex(ValueError, "no list of variants"):
            spellbook.open_daily_file(other)

    def test_a_variant_larger_than_any_real_one_is_an_error_instead_of_filling_memory(self):
        with mock.patch.object(spellbook, "VARIANT_MAX", 100):
            _, variants = spellbook.open_daily_file(self.plain, chunk=64)
            with self.assertRaisesRegex(ValueError, "could not be read"):
                list(variants)


class ReduceFileTests(DailyFileCase):
    def setUp(self):
        super().setUp()
        self.doc = spellbook.reduce_file(self.gzipped)

    def test_the_document_says_where_it_came_from_and_what_it_left_out(self):
        doc = self.doc
        self.assertEqual((doc["schema"], doc["source"], doc["dump"], doc["version"]),
                         (spellbook.INDEX_SCHEMA, spellbook.VARIANTS_URL, "2026-10-11T23:11:42.250594+00:00", "7.1.9"))
        self.assertEqual(doc["dropped"], {"not legal": 1, "spoiler": 1, "status": 1})
        self.assertEqual([row[0] for row in doc["variants"]], KEPT_IDS)
        self.assertTrue(doc["fetched"].endswith("Z") and doc["ts"] > 0)

    def test_each_text_is_stored_once_and_a_row_holds_numbers_into_the_tables(self):
        doc = self.doc
        for table in ("names", "templates", "features"):
            self.assertEqual(len(doc[table]), len(set(doc[table])), table)
        row = doc["variants"][0]
        self.assertEqual([doc["names"][i] for i in row[1]], [COMMANDER_NAME, "Pitiless Plunderer"])
        self.assertEqual([doc["features"][i] for i in row[3]], ["Infinite Treasure tokens", "Infinite colored mana"])
        self.assertEqual((row[0], row[2], row[4], row[5], row[6]), ("3000-4871", [], "S", "BG", []))
        template_row = next(r for r in doc["variants"] if r[0] == "997-6982--5")
        self.assertEqual([doc["templates"][i] for i in template_row[2]], ["Persist Creature"])

    def test_chatterfang_is_one_name_however_many_variants_use_it(self):
        self.assertEqual(self.doc["names"].count(COMMANDER_NAME), 1)

    def test_the_document_is_far_smaller_than_the_file(self):
        self.assertLess(len(json.dumps(self.doc)), len(self.raw) // 3)


class MatchTests(DailyFileCase):
    def setUp(self):
        super().setUp()
        self.index = spellbook.ComboIndex(spellbook.reduce_file(self.plain))

    def ids(self, found):
        return {"included": [c["id"] for c in found["included"]], "almost": [c["id"] for c in found["almost"]]}

    def match(self, commanders=(COMMANDER_NAME,), cards=INDEX_DECK, identity="BG"):
        return self.ids(self.index.match(list(commanders), list(cards), identity))

    def test_included_means_the_deck_holds_every_card_and_almost_means_one_is_missing(self):
        # Chatterfang + Pitiless Plunderer are both here; Zulaport Cutthroat + Warren Soultrader + Chatterfang lacks
        # Warren Soultrader; the combo with Mirkwood Bats and Plague of Vermin lacks two cards
        got = self.match()
        self.assertEqual(got["included"], ["3000-4871"])
        self.assertIn("1385-3000-5670", got["almost"])
        self.assertNotIn("9400-9401-9402", got["almost"] + got["included"])

    def test_the_commander_counts_as_one_of_the_cards(self):
        # with Chatterfang in the 99 instead of the command zone the answer is the same
        self.assertEqual(self.match(commanders=["Someone Else"], cards=INDEX_DECK + [COMMANDER_NAME]),
                         self.match())

    def test_an_almost_combo_names_the_card_that_would_complete_it(self):
        almost = {c["id"]: c for c in self.index.match([COMMANDER_NAME], INDEX_DECK, "BG")["almost"]}
        self.assertEqual(almost["1385-3000-5670"]["missing"], ["Warren Soultrader"])
        self.assertEqual(almost["9300--88"]["missing"], ["Emeritus of Abundance // Regrowth"])

    def test_an_included_combo_is_the_same_dict_the_api_parser_makes(self):
        found = self.index.match([COMMANDER_NAME], INDEX_DECK, "BG")
        self.assertEqual(found["included"][0], spellbook.parse_combo(raw_variant("3000-4871")))
        have = {n.casefold() for n in [COMMANDER_NAME] + INDEX_DECK}
        almost = next(c for c in found["almost"] if c["id"] == "1385-3000-5670")
        self.assertEqual(almost, spellbook.parse_combo(raw_variant("1385-3000-5670"), have))

    def test_the_bracket_facts_of_a_combo_are_read_as_for_the_api(self):
        combo = self.index.match([COMMANDER_NAME], INDEX_DECK, "BG")["included"][0]
        self.assertEqual((combo["two_card"], combo["infinite"], combo["bracket_tag"], combo["min_bracket"]),
                         (True, True, "S", 4))
        self.assertEqual(combo["url"], "https://commanderspellbook.com/combo/3000-4871/")

    def test_names_are_compared_without_regard_to_case(self):
        lower = [n.lower() for n in INDEX_DECK]
        self.assertEqual(self.match(commanders=[COMMANDER_NAME.upper()], cards=lower), self.match())

    def test_a_combo_with_a_missing_card_outside_the_commanders_colors_is_not_offered(self):
        # Chatterfang + Dockside Extortionist is a red combo; Lim-Dul's Vault is blue and black
        self.assertNotIn("9000-9001", self.match(identity="BG")["almost"])
        self.assertNotIn("9500-9501", self.match(identity="BG")["almost"])
        self.assertIn("9000-9001", self.match(identity="BGR")["almost"])
        self.assertIn("9500-9501", self.match(identity="UBG", cards=INDEX_DECK)["almost"])

    def test_without_the_colors_nothing_is_filtered(self):
        got = self.match(identity=None)["almost"]
        self.assertIn("9000-9001", got)
        self.assertIn("9500-9501", got)

    def test_a_colorless_deck_gets_only_colorless_combos(self):
        got = self.match(identity="")
        self.assertEqual(got["almost"], [])

    def test_a_combo_that_needs_a_commander_waits_for_that_commander(self):
        # Hazel + Skullclamp: Hazel must lead the deck. As a card in someone else's deck it does not count.
        as_card = self.match(commanders=[COMMANDER_NAME], cards=[HAZEL, "Skullclamp"])
        self.assertNotIn("9100-9101", as_card["included"] + as_card["almost"])
        as_leader = self.match(commanders=[HAZEL], cards=["Skullclamp"])
        self.assertEqual(as_leader["included"], ["9100-9101"])
        one_away = self.match(commanders=[HAZEL], cards=["Forest"])
        self.assertIn("9100-9101", one_away["almost"])

    def test_a_card_needed_twice_counts_only_when_the_deck_holds_both_copies(self):
        # Relentless Rats twice + Sol Ring: the deck has one Rats and one Sol Ring, so the second Rats is missing
        almost = {c["id"]: c for c in self.index.match([COMMANDER_NAME], INDEX_DECK, "BG")["almost"]}
        self.assertEqual(almost["9200-9201"]["missing"], ["Relentless Rats"])
        self.assertEqual(almost["9200-9201"]["cards"], ["Relentless Rats", "Sol Ring"])    # each name once
        self.assertFalse(almost["9200-9201"]["two_card"])                                  # three pieces, not two
        both = self.match(cards=INDEX_DECK + ["Relentless Rats"])
        self.assertIn("9200-9201", both["included"])

    def test_a_combo_of_one_card_is_one_card_away_from_every_deck_without_it(self):
        self.assertIn("9300--88", self.match()["almost"])
        has_it = self.match(cards=INDEX_DECK + ["Emeritus of Abundance // Regrowth"])
        self.assertIn("9300--88", has_it["included"])
        self.assertNotIn("9300--88", has_it["almost"])

    def test_a_combo_that_needs_a_template_is_never_offered(self):
        # the API counts an unmet template as a missing piece and the local index cannot check one
        both = self.match(cards=["Woe Strider", "Stalwart Successor"])
        one = self.match(cards=["Woe Strider"])
        for got in (both, one):
            self.assertNotIn("997-6982--5", got["included"] + got["almost"])
        self.assertIn("Persist Creature", self.index.templates)             # it is in the index, kept for later

    def test_the_answer_lists_combos_in_the_files_order(self):
        got = self.match(identity=None)["almost"]
        self.assertEqual(got, [i for i in KEPT_IDS if i in got])

    def test_cards_the_index_has_never_heard_of_are_ignored(self):
        self.assertEqual(self.match(cards=INDEX_DECK + ["Made Up Card"]), self.match())

    def test_an_empty_deck_matches_only_single_card_combos_as_almost(self):
        got = self.index.match([], [], None)
        self.assertEqual(got["included"], [])
        self.assertEqual([c["id"] for c in got["almost"]], ["9300--88"])

    def test_a_second_lookup_gives_the_same_answer(self):
        self.assertEqual(self.match(), self.match())


class IndexCase(TempCache):
    """A temporary cache and a stand-in for the download of the daily file (the fixture, gzipped)."""

    def setUp(self):
        super().setUp()
        self.downloads = []
        self.fail_download = None
        self.fixture = os.path.join(FIXTURES, "spellbook_variants.json")
        mock.patch.object(net, "download", self.fake_download).start()
        self.path = net.cache_file("spellbook", "variants")

    def fake_download(self, url, path, *, source, decode=True):
        self.downloads.append((url, source, decode))
        if self.fail_download:
            raise self.fail_download
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(self.fixture, "rb") as src, gzip.open(path, "wb") as out:      # served gzipped, as the real file is
            out.write(src.read())

    def saved(self):
        with open(self.path) as f:
            return json.load(f)

    def age(self, days):
        doc = self.saved()
        doc["ts"] -= days * config.DAY
        net.atomic_json(self.path, doc)


class LocalIndexTests(IndexCase):
    """local_index: the index is built from the download once, saved, served while fresh, and rebuilt when old."""

    def test_the_first_call_downloads_the_file_without_unzipping_it_and_saves_the_index(self):
        index, info = spellbook.local_index()
        self.assertEqual(self.downloads, [(spellbook.VARIANTS_URL, "spellbook", False)])
        self.assertEqual(info["cache"], "network")
        self.assertEqual([row[0] for row in self.saved()["variants"]], KEPT_IDS)
        self.assertEqual(len(index), 9)
        self.assertEqual(os.listdir(os.path.dirname(self.path)), ["variants.json"])      # the download is gone

    def test_a_second_call_in_the_same_process_does_not_read_the_file_again(self):
        first = spellbook.local_index()
        with mock.patch.object(net, "read_json", side_effect=AssertionError("read twice")):
            self.assertIs(spellbook.local_index(), first)

    def test_a_new_process_reads_the_saved_index_while_it_is_under_seven_days_old(self):
        spellbook.local_index()
        spellbook.reset()
        self.age(6)
        index, info = spellbook.local_index()
        self.assertEqual((info["cache"], len(self.downloads), len(index)), ("fresh", 1, 9))

    def test_an_index_older_than_seven_days_is_rebuilt(self):
        spellbook.local_index()
        spellbook.reset()
        self.age(8)
        _, info = spellbook.local_index()
        self.assertEqual((info["cache"], len(self.downloads)), ("network", 2))

    def test_the_lifetime_is_seven_days(self):
        self.assertEqual(config.TTL["spellbook_variants"], 7 * config.DAY)

    def test_a_failed_rebuild_serves_the_old_index_as_stale(self):
        spellbook.local_index()
        spellbook.reset()
        self.age(30)
        self.fail_download = net.FetchError("spellbook", "u", "HTTP 503")
        index, info = spellbook.local_index()
        self.assertEqual((info["cache"], len(index)), ("stale", 9))

    def test_a_failed_download_with_nothing_saved_is_an_error(self):
        self.fail_download = net.FetchError("spellbook", "u", "HTTP 503")
        with self.assertRaises(net.FetchError):
            spellbook.local_index()

    def test_offline_serves_any_saved_index_and_never_downloads(self):
        spellbook.local_index()
        spellbook.reset()
        self.age(90)
        _, info = spellbook.local_index(offline=True)
        self.assertEqual((info["cache"], len(self.downloads)), ("stale", 1))

    def test_offline_with_nothing_saved_says_how_to_fix_it(self):
        with self.assertRaisesRegex(net.FetchError, r"offline.*no saved combo file.*`warm` \(or `stats`\)"):
            spellbook.local_index(offline=True)
        self.assertEqual(self.downloads, [])

    def test_the_run_wide_offline_mode_applies_when_no_mode_is_passed(self):
        with mock.patch.dict(net.MODE, {"offline": True}):
            with self.assertRaises(net.FetchError):
                spellbook.local_index()

    def test_refresh_downloads_again_but_only_once_in_a_run(self):
        spellbook.local_index()
        spellbook.reset()
        spellbook.local_index(refresh=True)
        spellbook.local_index(refresh=True)                    # this run has just downloaded it
        self.assertEqual(len(self.downloads), 2)

    def test_an_index_of_another_schema_is_rebuilt(self):
        spellbook.local_index()
        spellbook.reset()
        doc = self.saved()
        doc["schema"] = spellbook.INDEX_SCHEMA + 1
        net.atomic_json(self.path, doc)
        _, info = spellbook.local_index()
        self.assertEqual((info["cache"], len(self.downloads)), ("network", 2))

    def test_a_damaged_download_is_an_error_and_leaves_nothing_behind(self):
        def bad(url, path, *, source, decode=True):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(b"\x1f\x8bgarbage")
        with mock.patch.object(net, "download", bad):
            with self.assertRaisesRegex(net.FetchError, "damaged"):
                spellbook.local_index()
        self.assertEqual(os.listdir(os.path.dirname(self.path)) if os.path.isdir(os.path.dirname(self.path)) else [],
                         [])

    def test_a_file_with_no_usable_combos_is_an_error(self):
        empty = os.path.join(self.tmp, "empty.json")
        with open(empty, "w") as f:
            json.dump({"timestamp": "t", "version": "v", "variants": []}, f)
        self.fixture = empty
        with self.assertRaisesRegex(net.FetchError, "no combos"):
            spellbook.local_index()
        self.assertFalse(os.path.exists(self.path))


class FindCombosLocalTests(IndexCase):
    """find_combos_local and combos_for: the same answer as find_combos, from the index when it can be had."""

    def test_the_answer_has_the_shape_of_find_combos(self):
        found = spellbook.find_combos_local([COMMANDER_NAME], INDEX_DECK, identity="BG")
        self.assertEqual(sorted(found), ["almost", "cache", "fetched", "included"])
        self.assertEqual((found["cache"], [c["id"] for c in found["included"]]), ("network", ["3000-4871"]))
        self.assertTrue(found["fetched"].endswith("Z"))

    def test_the_colors_reach_the_match(self):
        names = lambda found: {c["id"] for c in found["almost"]}
        self.assertNotIn("9000-9001", names(spellbook.find_combos_local([COMMANDER_NAME], INDEX_DECK, identity="BG")))
        self.assertIn("9000-9001", names(spellbook.find_combos_local([COMMANDER_NAME], INDEX_DECK)))

    def test_combos_for_answers_from_the_index_and_says_so(self):
        found = spellbook.combos_for([COMMANDER_NAME], INDEX_DECK, identity="BG")
        self.assertEqual(found["via"], "index")
        self.assertNotIn("note", found)

    def test_combos_for_falls_back_to_the_api_and_says_why(self):
        self.fail_download = net.FetchError("spellbook", "u", "HTTP 503")
        fake = FakeFetch(fixture("spellbook_find_my_combos.json"))
        with patched(fake):
            found = spellbook.combos_for([COMMANDER], DECK)
        self.assertEqual(found["via"], "api")
        self.assertEqual(len(found["included"]), 1)
        self.assertIn("HTTP 503", found["note"])
        self.assertIn("API", found["note"])
        self.assertEqual(fake.calls[0][0], spellbook.FIND_URL)

    def test_combos_for_when_both_fail_names_both_reasons(self):
        self.fail_download = net.FetchError("spellbook", "u", "HTTP 503")
        with patched(FakeFetch(net.FetchError("spellbook", spellbook.FIND_URL, "HTTP 500"))):
            with self.assertRaises(net.FetchError) as caught:
                spellbook.combos_for([COMMANDER], DECK)
        self.assertIn("HTTP 500", str(caught.exception))
        self.assertIn("HTTP 503", str(caught.exception))

    def test_offline_the_api_fallback_is_offline_too(self):
        fake = FakeFetch(net.FetchError("spellbook", spellbook.FIND_URL, "offline (--offline) and not cached"))
        with patched(fake):
            with self.assertRaises(net.FetchError):
                spellbook.combos_for([COMMANDER], DECK, offline=True)
        self.assertTrue(fake.calls[0][1]["offline"])


if __name__ == "__main__":
    unittest.main()
