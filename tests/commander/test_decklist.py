"""Tests for decklist.py: reading pasted lists in the formats players actually have, matching names to cards, and
the MTGJSON precon lookups against a stand-in for net.fetch_json. No network, no cache folder."""
import copy, json, os, unittest
from unittest import mock
from mtgcommander import carddb, decklist, net

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


def sample_db():
    cards = {}
    with open(os.path.join(FIXTURES, "carddb_bulk_sample.jsonl"), encoding="utf-8") as f:
        for line in f:
            rec = carddb.card_record(json.loads(line))
            if rec and rec["name"] not in cards:
                cards[rec["name"]] = rec
    return carddb.CardDB(cards)


class ParseTests(unittest.TestCase):
    def cards(self, text):
        return decklist.parse(text)["cards"]

    def test_quantity_styles(self):
        text = "1 Sol Ring\n1x Arcane Signet\n4 Forest\n12x Swamp\nSkullclamp\n"
        self.assertEqual(self.cards(text), [(1, "Sol Ring"), (1, "Arcane Signet"), (4, "Forest"), (12, "Swamp"),
                                            (1, "Skullclamp")])

    def test_a_name_that_starts_with_x_is_not_a_quantity_mark(self):
        self.assertEqual(self.cards("1 Xenagos, God of Revels\n2 X Marks the Spot\n"),
                         [(1, "Xenagos, God of Revels"), (2, "X Marks the Spot")])

    def test_set_and_collector_suffixes_foil_marks_and_tags_are_dropped(self):
        text = ("1 Sol Ring (CMM) 400\n"
                "1 Sol Ring (cmm) 400 *F*\n"
                "1x Arcane Signet (cmm) 400 [Ramp]\n"
                "1 Command Tower (CMR) 350 *E* [Land,Mana]\n"
                "1 Skullclamp (MM3)\n"
                "1 Lotus Petal (PLST) MOC-379 ^Mana,#37d67a^\n"
                "1 Bonecrusher Giant // Stomp (ELD) 115\n")
        self.assertEqual([name for _, name in self.cards(text)],
                         ["Sol Ring", "Sol Ring", "Arcane Signet", "Command Tower", "Skullclamp", "Lotus Petal",
                          "Bonecrusher Giant // Stomp"])

    def test_card_names_with_parentheses_survive(self):
        self.assertEqual(self.cards("1 B.F.M. (Big Furry Monster)\n1 Erase (Not the Urza's Legacy One)\n"),
                         [(1, "B.F.M. (Big Furry Monster)"), (1, "Erase (Not the Urza's Legacy One)")])

    def test_commander_markers(self):
        p = decklist.parse("1 Hazel of the Rootbloom *CMDR*\n1 Sol Ring\n")
        self.assertEqual((p["commanders"], p["cards"]), (["Hazel of the Rootbloom"], [(1, "Sol Ring")]))
        p = decklist.parse("1x Hazel of the Rootbloom (blc) 95 [Commander{top}]\n1x Sol Ring (cmm) 400 [Ramp]\n")
        self.assertEqual((p["commanders"], p["cards"]), (["Hazel of the Rootbloom"], [(1, "Sol Ring")]))

    def test_archidekt_categories_choose_where_a_card_goes(self):
        text = ("1x Sol Ring (cmm) 400 [Ramp]\n"
                "1x Mana Crypt (2xm) 270 *F* [Maybeboard{noDeck}{noPrice}]\n"
                "1x Skullclamp (mm3) 1 [Sideboard{noDeck}]\n"
                "1x Lotus Petal [Considering]\n")
        p = decklist.parse(text)
        self.assertEqual((p["cards"], p["sideboard"]), ([(1, "Sol Ring")], [(1, "Skullclamp")]))

    def test_section_headers_in_every_style(self):
        for header in ("Commander", "commander:", "// Commander", "# Commander", "COMMANDERS (1)", "Commander (1):"):
            p = decklist.parse(f"{header}\n1 Hazel of the Rootbloom\n\nDeck\n1 Sol Ring\n")
            self.assertEqual((p["commanders"], p["cards"], p["sectioned"]),
                             (["Hazel of the Rootbloom"], [(1, "Sol Ring")], True), header)
        for header in ("Deck", "Main", "Mainboard", "Main Deck", "Deck (99)", "// Deck:"):
            p = decklist.parse(f"Commander\n1 Hazel of the Rootbloom\n{header}\n1 Sol Ring\n")
            self.assertEqual(p["cards"], [(1, "Sol Ring")], header)

    def test_sideboard_companion_maybeboard_considering_tokens(self):
        text = ("Deck\n1 Sol Ring\nSideboard\n1 Skullclamp\nCompanion\n1 Lotus Petal\n"
                "Maybeboard\n1 Mana Crypt\nConsidering\n1 Forest\nTokens\n1 Treasure\nDeck\n1 Command Tower\n")
        p = decklist.parse(text)
        self.assertEqual(p["cards"], [(1, "Sol Ring"), (1, "Command Tower")])
        self.assertEqual(p["sideboard"], [(1, "Skullclamp"), (1, "Lotus Petal")])

    def test_card_type_headings_change_nothing(self):
        p = decklist.parse("Creatures (2)\n1 Hazel of the Rootbloom\n\nArtifacts\n1 Sol Ring\n\n"
                           "Lands (1)\n1 Forest\n")
        self.assertEqual([n for _, n in p["cards"]], ["Hazel of the Rootbloom", "Sol Ring", "Forest"])
        self.assertEqual((p["sideboard"], p["unparsed"]), ([], []))

    def test_mtgo_style_blank_line_starts_the_sideboard(self):
        p = decklist.parse("1 Sol Ring\n1 Arcane Signet\n\n1 Hazel of the Rootbloom\n")
        self.assertEqual((p["cards"], p["sideboard"], p["sectioned"]),
                         ([(1, "Sol Ring"), (1, "Arcane Signet")], [(1, "Hazel of the Rootbloom")], False))
        p = decklist.parse("1 Sol Ring\nSB: 1 Hazel of the Rootbloom\n")
        self.assertEqual((p["cards"], p["sideboard"]), ([(1, "Sol Ring")], [(1, "Hazel of the Rootbloom")]))

    def test_blank_lines_are_inert_when_there_are_headers(self):
        p = decklist.parse("Deck\n1 Sol Ring\n\n1 Arcane Signet\n\n\n1 Forest\n")
        self.assertEqual(len(p["cards"]), 3)

    def test_comments_blank_lines_and_junk(self):
        p = decklist.parse("# my deck\n// ramp\n\n1 Sol Ring\n[Ramp]\n\n")
        self.assertEqual(p["cards"], [(1, "Sol Ring")])
        self.assertEqual(p["unparsed"], ["[Ramp]"])             # only a category tag: nothing to read

    def test_windows_line_endings_and_byte_order_mark(self):
        self.assertEqual(self.cards("1 Sol Ring\r\n2 Forest\r\n"), [(1, "Sol Ring"), (2, "Forest")])

    def test_empty_text(self):
        self.assertEqual(decklist.parse(""), {"commanders": [], "cards": [], "sideboard": [], "unparsed": [],
                                              "sectioned": False, "blank_split": False})

    def test_load_reads_a_file_and_standard_input(self):
        import io, tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8-sig") as f:
            f.write("Commander\n1 Hazel of the Rootbloom\nDeck\n1 Sol Ring\n")
        self.addCleanup(os.remove, f.name)
        self.assertEqual(decklist.load(f.name)["commanders"], ["Hazel of the Rootbloom"])    # no BOM in the name
        with mock.patch("sys.stdin", io.StringIO("3 Forest\n")):
            self.assertEqual(decklist.load("-")["cards"], [(3, "Forest")])


class ResolveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = sample_db()

    def resolve(self, text, **kw):
        return decklist.resolve(decklist.parse(text), self.db, **kw)

    def test_names_become_canonical_and_repeats_are_added(self):
        r = self.resolve("Commander\n1 hazel of the rootbloom\nDeck\n1 sol ring\n1 Sol Ring (CMM) 400 *F*\n"
                         "1 Fire/Ice\n1 Lim-Dul's Vault\n1 Delver of Secrets\n4 Forest\n5 Forest\n")
        self.assertEqual(r["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(r["cards"], [(2, "Sol Ring"), (1, "Fire // Ice"), (1, "Lim-Dûl's Vault"),
                                      (1, "Delver of Secrets // Insectile Aberration"), (9, "Forest")])
        self.assertEqual((r["unknown"], r["warnings"]), ([], []))

    def test_unknown_names_come_with_suggestions_and_are_reported_once(self):
        r = self.resolve("Commander\n1 Hazel of the Rootbloom\nDeck\n1 Sol Rng\n1 sol rng\n1 Skullclamp\n")
        self.assertEqual(r["cards"], [(1, "Skullclamp")])
        self.assertEqual(len(r["unknown"]), 1)
        self.assertEqual(r["unknown"][0]["name"], "Sol Rng")
        self.assertEqual(r["unknown"][0]["suggestions"][0], "Sol Ring")

    def test_only_the_first_unknown_names_get_suggestions(self):
        text = "Deck\n" + "".join(f"1 Not A Real Card {i}\n" for i in range(decklist.SUGGEST_LIMIT + 5))
        unknown = self.resolve(text)["unknown"]
        self.assertEqual(len(unknown), decklist.SUGGEST_LIMIT + 5)             # every one is still reported
        self.assertTrue(all(u["suggestions"] == self.db.suggest(u["name"]) for u in unknown[:decklist.SUGGEST_LIMIT]))
        self.assertTrue(all(u["suggestions"] == [] for u in unknown[decklist.SUGGEST_LIMIT:]))

    def test_unknown_commander_is_unknown_not_missing(self):
        r = self.resolve("Commander\n1 Hazle of the Rootbloom\nDeck\n1 Sol Ring\n")
        self.assertEqual(r["commanders"], [])
        self.assertEqual(r["unknown"][0]["suggestions"][0], "Hazel of the Rootbloom")
        self.assertEqual(r["warnings"], [])          # `unknown` already says it; no second complaint

    def test_commander_argument_wins_and_is_removed_from_the_cards(self):
        r = self.resolve("1 Sol Ring\n1 Hazel of the Rootbloom\n1 Forest\n", commander="hazel of the rootbloom")
        self.assertEqual(r["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(r["cards"], [(1, "Sol Ring"), (1, "Forest")])
        r = self.resolve("Commander\n1 Hazel of the Rootbloom\nDeck\n1 Sol Ring\n",
                         commander=["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"])
        self.assertEqual(r["commanders"], ["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"])
        self.assertEqual(len(r["warnings"]), 1)      # it replaced the commander named in the list

    def test_two_commanders(self):
        r = self.resolve("Commander\n1 Pir, Imaginative Rascal\n1 Toothy, Imaginary Friend\nDeck\n1 Sol Ring\n")
        self.assertEqual(r["commanders"], ["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"])

    def test_a_commander_listed_among_the_cards_is_one_copy_not_two(self):
        r = self.resolve("Commander\n1 Hazel of the Rootbloom\nDeck\n1 Hazel of the Rootbloom\n1 Sol Ring\n")
        self.assertEqual(r["cards"], [(1, "Sol Ring")])

    def test_mtgo_style_sideboard_holds_the_commander(self):
        r = self.resolve("1 Sol Ring\n1 Forest\n\n1 Hazel of the Rootbloom\n")
        self.assertEqual((r["commanders"], r["cards"]),
                         (["Hazel of the Rootbloom"], [(1, "Sol Ring"), (1, "Forest")]))
        self.assertIn("sideboard", r["warnings"][0])
        r = self.resolve("1 Sol Ring\n\n1 Pir, Imaginative Rascal\n1 Toothy, Imaginary Friend\n")
        self.assertEqual(r["commanders"], ["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"])

    def test_cards_after_a_blank_line_that_cannot_lead_a_deck_join_it(self):
        r = self.resolve("1 Sol Ring\n\n1 Skullclamp\n")
        self.assertEqual(r["commanders"], [])
        self.assertEqual(sorted(n for _, n in r["cards"]), ["Skullclamp", "Sol Ring"])
        self.assertTrue(any("no commander" in w for w in r["warnings"]))
        self.assertTrue(any("after a blank line" in w for w in r["warnings"]))

    def test_an_explicit_sideboard_that_cannot_lead_a_deck_is_ignored(self):
        r = self.resolve("Deck\n1 Sol Ring\nSideboard\n1 Skullclamp\n")
        self.assertEqual(r["cards"], [(1, "Sol Ring")])
        self.assertTrue(any("ignored 1 sideboard" in w for w in r["warnings"]))

    def test_three_sideboard_creatures_are_not_a_commander_pair(self):
        r = self.resolve("1 Sol Ring\n\n1 Hazel of the Rootbloom\n1 Pir, Imaginative Rascal\n"
                         "1 Toothy, Imaginary Friend\n")
        self.assertEqual(r["commanders"], [])

    def test_a_declared_commander_beats_the_sideboard_guess(self):
        r = self.resolve("Commander\n1 Hazel of the Rootbloom\nDeck\n1 Sol Ring\nSideboard\n"
                         "1 Pir, Imaginative Rascal\n")
        self.assertEqual(r["commanders"], ["Hazel of the Rootbloom"])

    def test_no_commander_anywhere(self):
        r = self.resolve("1 Sol Ring\n1 Forest\n")
        self.assertEqual(r["commanders"], [])
        self.assertTrue(any("no commander" in w for w in r["warnings"]))

    def test_unreadable_lines_become_warnings(self):
        r = self.resolve("Commander\n1 Hazel of the Rootbloom\nDeck\n1 Sol Ring\n[Ramp]\n")
        self.assertEqual(len(r["warnings"]), 1)
        self.assertIn("[Ramp]", r["warnings"][0])


class ToTextTests(unittest.TestCase):
    def test_shape(self):
        self.assertEqual(decklist.to_text(["Hazel of the Rootbloom"], [(1, "Sol Ring"), (9, "Forest")]),
                         "Commander\n1 Hazel of the Rootbloom\n\nDeck\n1 Sol Ring\n9 Forest\n")

    def test_round_trip_through_parse_and_resolve(self):
        db = sample_db()
        cards = [(1, "Sol Ring"), (1, "Fire // Ice"), (9, "Forest")]
        text = decklist.to_text(["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"], cards)
        r = decklist.resolve(decklist.parse(text), db)
        pair = ["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"]
        self.assertEqual((r["commanders"], r["cards"]), (pair, cards))


class FakeMtgjson:
    """Stands in for net.fetch_json: DeckList.json, deck files and the Scryfall printings search."""
    def __init__(self):
        self.calls = []
        self.decklist = fixture("decklist_mtgjson_decklist.json")
        other = {"data": {"name": "Evasive Maneuvers", "mainBoard": [],
                          "commander": [{"name": "Some Other Commander"}]}}
        self.decks = {"SquirreledAway_BLC": fixture("decklist_mtgjson_deck.json"),
                      "PeaceOffering_BLC": fixture("decklist_mtgjson_deck_other.json"),
                      "EvasiveManeuvers_C13": copy.deepcopy(other), "EvasiveManeuvers_C16": copy.deepcopy(other)}
        self.printings = fixture("decklist_scryfall_printings.json")

    def __call__(self, url, **kw):
        self.calls.append((url, kw))
        info = {"url": url, "fetched": "2026-10-11T12:00:00Z", "cache": "network", "age_days": 0.0}
        if url.endswith("/DeckList.json"):
            return copy.deepcopy(self.decklist), info
        if "/decks/" in url:
            name = url.rsplit("/", 1)[1][:-len(".json")]
            if name not in self.decks:
                raise net.NotFound(kw["source"], url, "no such page")
            return copy.deepcopy(self.decks[name]), info
        if url.startswith(carddb.SEARCH):
            if not self.printings:
                raise net.NotFound(kw["source"], url, "no such page")
            return copy.deepcopy(self.printings), info
        raise AssertionError("unexpected request " + url)

    def urls(self):
        return [u for u, _ in self.calls]


class PreconTests(unittest.TestCase):
    def setUp(self):
        self.site = FakeMtgjson()
        patcher = mock.patch.object(net, "fetch_json", self.site)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_names_are_commander_decks_only_sorted_without_repeats(self):
        self.assertEqual(decklist.precon_names(), ["Evasive Maneuvers", "Peace Offering", "Squirreled Away"])

    def test_precon_record(self):
        p = decklist.precon("Squirreled Away")
        self.assertEqual((p["name"], p["code"], p["file"], p["release"]),
                         ("Squirreled Away", "BLC", "SquirreledAway_BLC", "2024-08-02"))
        self.assertEqual(p["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(p["cards"], [(1, "Sol Ring"), (1, "Skullclamp"), (1, "Chatterfang, Squirrel General"),
                                      (1, "Command Tower"), (8, "Swamp"), (9, "Forest")])   # basics added up
        self.assertEqual((p["fetched"], p["url"]),
                         ("2026-10-11T12:00:00Z", "https://mtgjson.com/api/v5/decks/SquirreledAway_BLC.json"))

    def test_requests_use_the_mtgjson_source_and_cache_keys(self):
        decklist.precon("Squirreled Away")
        for url, kw in self.site.calls:
            self.assertEqual(kw["source"], "mtgjson")
        self.assertEqual(self.site.urls(), ["https://mtgjson.com/api/v5/DeckList.json",
                                            "https://mtgjson.com/api/v5/decks/SquirreledAway_BLC.json"])

    def test_refresh_and_offline_are_passed_through(self):
        decklist.precon("Squirreled Away", refresh=True, offline=False)
        for _, kw in self.site.calls:
            self.assertEqual((kw["refresh"], kw["offline"]), (True, False))

    def test_name_matching_ignores_case_and_punctuation(self):
        for spelled in ("squirreled away", "SQUIRRELED  AWAY", "Squirreled-Away"):
            self.assertEqual(decklist.precon(spelled)["file"], "SquirreledAway_BLC", spelled)

    def test_a_typo_resolves_to_the_one_close_deck(self):
        self.assertEqual(decklist.precon("Squirelled Away")["name"], "Squirreled Away")

    def test_an_unknown_name_raises_a_keyerror_with_close_names(self):
        with self.assertRaises(KeyError) as ctx:
            decklist.precon("Squirrel Army")
        err = ctx.exception
        self.assertIsInstance(err, decklist.UnknownPrecon)
        self.assertIn("Squirreled Away", err.suggestions)
        self.assertIn("Squirreled Away", str(err))
        with self.assertRaises(KeyError):
            decklist.precon("zzzzzzzz")

    def test_a_repeated_name_picks_the_newest_release(self):
        self.site.decks["EvasiveManeuvers_C16"] = {"data": {
            "name": "Evasive Maneuvers", "code": "C16", "commander": [], "mainBoard": [],
            "releaseDate": "2016-11-11"}}
        self.assertEqual(decklist.precon("evasive maneuvers")["code"], "C16")

    def test_a_deck_with_no_commander_or_cards_still_parses(self):
        self.site.decks["PeaceOffering_BLC"] = {"data": {}}
        p = decklist.precon("Peace Offering")
        self.assertEqual((p["commanders"], p["cards"], p["code"], p["release"]), ([], [], "BLC", "2024-08-02"))


class PreconsForCommanderTests(unittest.TestCase):
    def setUp(self):
        self.site = FakeMtgjson()
        patcher = mock.patch.object(net, "fetch_json", self.site)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_sets_come_from_printings_and_decks_are_matched_by_commander(self):
        decks = decklist.precons_for_commander("Hazel of the Rootbloom")
        self.assertEqual([d["name"] for d in decks], ["Squirreled Away"])
        urls = self.site.urls()
        # the promo printing's set (PBLC) has no deck; the other BLC deck is read but does not match
        self.assertIn("https://mtgjson.com/api/v5/decks/PeaceOffering_BLC.json", urls)
        self.assertNotIn("https://mtgjson.com/api/v5/decks/EvasiveManeuvers_C13.json", urls)   # other sets: unread
        search = [kw for u, kw in self.site.calls if u.startswith(carddb.SEARCH)][0]
        self.assertEqual(search["source"], "scryfall")

    def test_the_search_asks_for_every_printing_of_exactly_this_card(self):
        decklist.precons_for_commander("Hazel of the Rootbloom")
        url = self.site.urls()[0]
        self.assertIn("unique=prints", url)
        self.assertIn("%21%22Hazel+of+the+Rootbloom%22", url)       # !"Hazel of the Rootbloom"

    def test_a_double_faced_commander_matches_by_front_face(self):
        self.site.printings = {"data": [{"set": "blc"}], "has_more": False}
        full = "Esika, God of the Tree // The Prismatic Bridge"
        self.site.decks["PeaceOffering_BLC"]["data"]["commander"] = [{"name": full}]
        for spelled in ("Esika, God of the Tree", full):
            found = decklist.precons_for_commander(spelled)
            self.assertEqual([d["name"] for d in found], ["Peace Offering"], spelled)

    def test_no_printings_or_no_deck_gives_an_empty_list(self):
        self.site.printings = None
        self.assertEqual(decklist.precons_for_commander("Sol Ring"), [])
        self.site.printings = {"data": [{"set": "c13"}], "has_more": False}
        self.assertEqual(decklist.precons_for_commander("Sol Ring"), [])      # C13 has a deck, not this commander's
        self.site.printings = {"data": [{"set": "jmp"}], "has_more": False}
        self.assertEqual(decklist.precons_for_commander("Sol Ring"), [])      # Jumpstart is not a Commander product

    def test_a_listed_deck_whose_file_is_missing_is_skipped(self):
        del self.site.decks["PeaceOffering_BLC"]
        found = decklist.precons_for_commander("Hazel of the Rootbloom")
        self.assertEqual([d["name"] for d in found], ["Squirreled Away"])

    def test_newest_first(self):
        self.site.printings = {"data": [{"set": "c13"}, {"set": "c16"}], "has_more": False}
        for code, year in (("C13", "2013"), ("C16", "2016")):
            self.site.decks[f"EvasiveManeuvers_{code}"] = {"data": {
                "name": "Evasive Maneuvers", "code": code, "releaseDate": f"{year}-11-01",
                "commander": [{"name": "Edgar Markov"}], "mainBoard": []}}
        self.assertEqual([d["code"] for d in decklist.precons_for_commander("Edgar Markov")], ["C16", "C13"])


if __name__ == "__main__":
    unittest.main()


class BlankLineGroupsTest(unittest.TestCase):
    """Hand-typed lists separate groups with blank lines; Commander has no sideboard, so nothing is dropped."""

    def setUp(self):
        from mtgcommander import carddb
        recs = {"Hazel of the Rootbloom": True, "Sol Ring": False, "Arcane Signet": False, "Forest": False}
        self.db = carddb.CardDB({n: {"name": n, "front": n, "commander_ok": ok, "types": []}
                                 for n, ok in recs.items()})

    def test_groups_after_blank_lines_stay_in_the_deck(self):
        parsed = decklist.parse("1 Sol Ring\n\n1 Arcane Signet\n30 Forest\n")
        r = decklist.resolve(parsed, self.db, commander="Hazel of the Rootbloom")
        self.assertEqual(sorted(r["cards"], key=lambda c: c[1]),
                         [(1, "Arcane Signet"), (30, "Forest"), (1, "Sol Ring")])
        self.assertTrue(any("after a blank line" in w for w in r["warnings"]))

    def test_a_lone_commander_line_before_the_gap_leads_the_deck(self):
        parsed = decklist.parse("1 Hazel of the Rootbloom\n\n1 Sol Ring\n1 Arcane Signet\n1 Forest\n")
        r = decklist.resolve(parsed, self.db)
        self.assertEqual(r["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(sorted(r["cards"]), [(1, "Arcane Signet"), (1, "Forest"), (1, "Sol Ring")])

    def test_mtgo_style_commander_after_the_gap_still_works(self):
        parsed = decklist.parse("1 Sol Ring\n1 Arcane Signet\n\n1 Hazel of the Rootbloom\n")
        r = decklist.resolve(parsed, self.db)
        self.assertEqual(r["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(sorted(r["cards"]), [(1, "Arcane Signet"), (1, "Sol Ring")])
