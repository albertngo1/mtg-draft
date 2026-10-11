"""Tests for providers/edhrec.py: the parsers against hand-written fixtures in EDHREC's page shape, and the
provider calls against a stand-in for net.fetch_json. Nothing here touches the network or the cache folder."""
import copy, json, os, unittest
from unittest import mock
from mtgcommander import net
from mtgcommander.providers import edhrec

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
HAZEL = ["Hazel of the Rootbloom"]
HAZEL_PAGE = "commanders/hazel-of-the-rootbloom"
POPULAR_FIRST = ["Teysa Karlov", "Sephiroth, Fabled SOLDIER", "The Great Goblin"]   # top list, then new
SALTY = {"Stasis": 3.05, "Winter Orb": 2.96, "Tergrid, God of Fright": 2.7}


def fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


class FakeSite:
    """Stands in for net.fetch_json. Serves payloads by page path (the url without host and '.json') and
    records every request; a path that is not served answers like EDHREC does for a page that is missing."""
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def __call__(self, url, **kw):
        self.calls.append((url, kw))
        path = url[len(edhrec.BASE):-len(".json")]
        if path not in self.pages:
            raise net.NotFound(kw["source"], url, "no such page")
        return copy.deepcopy(self.pages[path]), {"url": url, "fetched": "2026-10-11T12:00:00Z",
                                                 "cache": "network", "age_days": 0.0}

    @property
    def paths(self):
        return [url[len(edhrec.BASE):-len(".json")] for url, _ in self.calls]


def with_decks(page, n):
    page = copy.deepcopy(page)
    page["container"]["json_dict"]["card"]["num_decks"] = n
    return page


class SiteTestCase(unittest.TestCase):
    def serve(self, pages):
        self.site = FakeSite(pages)
        patcher = mock.patch.object(net, "fetch_json", self.site)
        patcher.start()
        self.addCleanup(patcher.stop)


class SlugTests(unittest.TestCase):
    def test_names_with_punctuation_and_accents(self):
        cases = [
            ("Ms. Bumbleflower", "ms-bumbleflower"),
            ("Lim-Dûl the Necromancer", "lim-dul-the-necromancer"),        # accent folds, hyphen stays
            ("Yuriko, the Tiger's Shadow", "yuriko-the-tigers-shadow"),   # comma splits, apostrophe vanishes
            ("Yuriko, the Tiger’s Shadow", "yuriko-the-tigers-shadow"),   # typographic apostrophe
            ("Éowyn, Shieldmaiden", "eowyn-shieldmaiden"),
            ("K'rrik, Son of Yawgmoth", "krrik-son-of-yawgmoth"),
            ("Atraxa, Praetors' Voice", "atraxa-praetors-voice"),
            ("The Ur-Dragon", "the-ur-dragon"),
            ("Hazel of the Rootbloom", "hazel-of-the-rootbloom"),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(edhrec.slug(name), expected)
                self.assertTrue(edhrec.slug(name).isascii())   # a non-ASCII url would crash urllib

    def test_double_faced_commander_uses_its_front_face(self):
        self.assertEqual(edhrec.slug("Esika, God of the Tree // The Prismatic Bridge"),
                         "esika-god-of-the-tree")
        self.assertEqual(edhrec.slug("Jace, Vryn's Prodigy // Jace, Telepath Unbound"), "jace-vryns-prodigy")

    def test_partners_are_joined_alphabetically_in_either_order(self):
        kraum, tymna = "Kraum, Ludevic's Opus", "Tymna the Weaver"
        self.assertEqual(edhrec.commander_slug([kraum, tymna]), "kraum-ludevics-opus-tymna-the-weaver")
        self.assertEqual(edhrec.commander_slug([tymna, kraum]), "kraum-ludevics-opus-tymna-the-weaver")
        # EDHREC sorts a 'partner with' pair too, not in the order the card prints them
        self.assertEqual(edhrec.commander_slug(["Pako, Arcane Retriever", "Haldan, Avid Arcanist"]),
                         "haldan-avid-arcanist-pako-arcane-retriever")

    def test_single_commander_and_a_bare_string(self):
        self.assertEqual(edhrec.commander_slug(HAZEL), "hazel-of-the-rootbloom")
        self.assertEqual(edhrec.commander_slug("Hazel of the Rootbloom"), "hazel-of-the-rootbloom")

    def test_theme_label_or_slug(self):
        cases = [
            ("tokens", "tokens"),                                   # already a slug
            ("plus-1-plus-1-counters", "plus-1-plus-1-counters"),
            ("+1/+1 Counters", "plus-1-plus-1-counters"),
            ("-1/-1 Counters", "minus-1-minus-1-counters"),
            ("Self-Mill", "self-mill"),
            ("Tap / Untap", "tap-untap"),
            ("Day / Night", "day-night"),
            ("Dragon's Approach", "dragons-approach"),
            ("Lands Matter", "lands-matter"),
            ("  Aristocrats ", "aristocrats"),
            ("lands matter", "lands-matter"),
        ]
        for theme, expected in cases:
            with self.subTest(theme=theme):
                self.assertEqual(edhrec.theme_slug(theme), expected)


class ParseTests(unittest.TestCase):
    def test_cards_are_deduplicated_across_lists(self):
        cards = edhrec.parse_cards(fixture("edhrec_commander.json"))
        self.assertEqual(sorted(cards), ["Chatterfang, Squirrel General", "Forest", "Gardenize",
                                         "Heroic Intervention", "Revitalizing Repast", "Skullclamp"])
        self.assertEqual(cards["Skullclamp"], {"decks": 900, "of": 1000, "synergy": 0.5})
        # the modal double-faced card is listed as an instant and as a land, with the same numbers
        self.assertEqual(cards["Revitalizing Repast"], {"decks": 120, "of": 1000, "synergy": -0.09})

    def test_a_new_card_keeps_its_own_pool_and_a_missing_synergy_stays_none(self):
        cards = edhrec.parse_cards(fixture("edhrec_commander.json"))
        self.assertEqual(cards["Gardenize"]["of"], 400)             # only decks built since its release
        self.assertIsNone(cards["Heroic Intervention"]["synergy"])

    def test_basic_lands_are_kept_and_an_entry_without_a_pool_is_dropped(self):
        cards = edhrec.parse_cards(fixture("edhrec_commander.json"))
        self.assertEqual(cards["Forest"]["decks"], 990)
        self.assertNotIn("Listed Without A Pool", cards)            # potential_decks 0 would divide by zero

    def test_lists_can_be_skipped(self):
        cards = edhrec.parse_cards(fixture("edhrec_commander.json"), skip=("topcards",))
        self.assertNotIn("Skullclamp", cards)
        self.assertIn("Gardenize", cards)

    def test_commander_meta(self):
        meta = edhrec.parse_meta(fixture("edhrec_commander.json"), {"url": "u", "fetched": "f"})
        self.assertEqual(meta["n_decks"], 1000)
        self.assertEqual(meta["bracket_counts"], {1: 20, 2: 2000, 3: 1000, 4: 300, 5: 10})   # keys are ints
        self.assertEqual(meta["taglinks"], [
            {"slug": "tokens", "label": "Tokens", "count": 400},
            {"slug": "plus-1-plus-1-counters", "label": "+1/+1 Counters", "count": 90}])
        self.assertEqual(meta["avg_types"], {"creature": 28, "instant": 8, "sorcery": 9, "artifact": 9,
                                             "enchantment": 7, "battle": 0, "planeswalker": 1, "land": 37,
                                             "basic": 18, "nonbasic": 19})
        self.assertEqual(meta["mana_curve"], {1: 8, 2: 16, 3: 18})
        self.assertEqual(meta["salt"], 0.31)
        self.assertEqual(meta["similar"], ["Chatterfang, Squirrel General", "Camellia, the Seedmiser"])
        self.assertEqual(meta["combos"], ["Camellia, the Seedmiser + Gilded Goose",
                                          "Chatterfang, Squirrel General + Pitiless Plunderer"])
        self.assertEqual(meta["ci"], "BG")                          # the page says G, B; we say WUBRG order
        self.assertEqual((meta["url"], meta["fetched"]), ("u", "f"))

    def test_color_identity_is_in_wubrg_order(self):
        cases = [(["W", "U", "B", "R"], "WUBR"), (["R", "W"], "WR"), (["G", "B", "U"], "UBG"), ([], "")]
        for letters, expected in cases:
            page = {"container": {"json_dict": {"card": {"color_identity": letters}}}}
            self.assertEqual(edhrec.parse_meta(page)["ci"], expected)

    def test_a_bare_page_gives_an_empty_meta_not_an_error(self):
        meta = edhrec.parse_meta({})
        self.assertEqual((meta["n_decks"], meta["salt"], meta["ci"]), (0, None, ""))
        self.assertEqual((meta["bracket_counts"], meta["taglinks"], meta["avg_types"], meta["combos"]),
                         ({}, [], {}, []))

    def test_theme_commanders_lead_with_the_popular_ones_and_appear_once(self):
        found = edhrec.parse_theme_commanders(fixture("edhrec_theme_index.json"))
        self.assertEqual([c["name"] for c in found], POPULAR_FIRST)
        teysa = found[0]
        self.assertEqual(teysa["decks"], 3500)                      # Teysa decks tagged Aristocrats
        self.assertIsNone(teysa["of"])                              # the index does not give her total decks
        self.assertEqual(teysa["theme_total"], 7000)                # potential_decks: the theme's site total
        self.assertEqual(teysa["url"], "https://edhrec.com/commanders/teysa-karlov/aristocrats")

    def test_salt_scores_keep_only_cards_with_a_salt_value(self):
        self.assertEqual(edhrec.parse_salt(fixture("edhrec_salt.json")), SALTY)


class SignalTests(SiteTestCase):
    def setUp(self):
        page = fixture("edhrec_commander.json")
        self.serve({
            HAZEL_PAGE: page,
            HAZEL_PAGE + "/upgraded": with_decks(page, 100),
            HAZEL_PAGE + "/tokens": with_decks(page, 40),
            HAZEL_PAGE + "/plus-1-plus-1-counters": with_decks(page, 30),
            HAZEL_PAGE + "/upgraded/tokens": with_decks(page, 25),
        })

    def test_all_bracket_signal(self):
        found = edhrec.signals(HAZEL)
        self.assertEqual(len(found), 1)
        sig = found[0]
        self.assertEqual((sig["source"], sig["kind"], sig["commanders"], sig["bracket"], sig["theme"]),
                         ("edhrec", "builder", HAZEL, None, None))
        self.assertEqual((sig["n"], len(sig["cards"]), sig["totals"]), (1000, 6, None))
        self.assertEqual(sig["url"], edhrec.BASE + HAZEL_PAGE + ".json")
        self.assertEqual((sig["fetched"], sig["cache"]), ("2026-10-11T12:00:00Z", "network"))
        self.assertEqual(sig["meta"]["n_decks"], 1000)              # a page's meta is its commander_meta
        self.assertEqual(self.site.paths, [HAZEL_PAGE])
        self.assertEqual(self.site.calls[0][1]["source"], "edhrec")

    def test_each_bracket_has_its_own_page(self):
        names = {1: "exhibition", 2: "core", 3: "upgraded", 4: "optimized", 5: "cedh"}
        page = fixture("edhrec_commander.json")
        self.serve({f"{HAZEL_PAGE}/{name}": with_decks(page, 10 * b) for b, name in names.items()})
        for bracket in names:
            sig = edhrec.signals(HAZEL, bracket)[0]
            self.assertEqual((sig["bracket"], sig["theme"], sig["n"]), (bracket, None, 10 * bracket))
        self.assertEqual(self.site.paths, [f"{HAZEL_PAGE}/{name}" for name in names.values()])
        self.assertEqual(edhrec.BRACKET_SLUGS, names)

    def test_a_theme_wins_over_a_bracket_and_the_signal_says_all_brackets(self):
        sig = edhrec.signals(HAZEL, 3, "tokens")[0]
        self.assertEqual(self.site.paths, [HAZEL_PAGE + "/tokens"])    # not .../upgraded/tokens
        self.assertEqual((sig["bracket"], sig["theme"], sig["n"]), (None, "tokens", 40))

    def test_a_theme_label_is_turned_into_its_slug(self):
        sig = edhrec.signals(HAZEL, theme="+1/+1 Counters")[0]
        self.assertEqual(self.site.paths, [HAZEL_PAGE + "/plus-1-plus-1-counters"])
        self.assertEqual(sig["theme"], "plus-1-plus-1-counters")

    def test_bracket_and_theme_together_have_their_own_page(self):
        sig = edhrec.bracket_theme_signal(HAZEL, 3, "Tokens")
        self.assertEqual(self.site.paths, [HAZEL_PAGE + "/upgraded/tokens"])
        self.assertEqual((sig["bracket"], sig["theme"], sig["n"]), (3, "tokens", 25))
        self.assertIsNone(edhrec.bracket_theme_signal(HAZEL, 4, "tokens"))

    def test_a_missing_page_is_no_signal(self):
        self.assertEqual(edhrec.signals(HAZEL, theme="stax"), [])
        self.assertEqual(edhrec.signals(["Nobody Home"]), [])
        self.assertIsNone(edhrec.commander_meta(["Nobody Home"]))

    def test_no_commander_means_no_request(self):
        self.assertEqual(edhrec.signals([]), [])
        self.assertIsNone(edhrec.commander_meta([]))
        self.assertEqual(self.site.calls, [])

    def test_a_bracket_outside_one_to_five_is_a_mistake(self):
        for bad in (0, 6, "3"):
            with self.subTest(bracket=bad):
                self.assertRaises(ValueError, edhrec.signals, HAZEL, bad)
                self.assertRaises(ValueError, edhrec.commander_meta, HAZEL, bad)
        self.assertEqual(self.site.calls, [])

    def test_run_wide_modes_pass_through_to_net(self):
        edhrec.signals(HAZEL, refresh=True, offline=False)
        edhrec.commander_meta(HAZEL, 3, refresh=None, offline=True)
        first, second = (kw for _, kw in self.site.calls)
        self.assertEqual((first["refresh"], first["offline"]), (True, False))
        self.assertEqual((second["refresh"], second["offline"]), (None, True))

    def test_every_page_has_its_own_cache_key(self):
        edhrec.signals(HAZEL)
        edhrec.signals(HAZEL, 3)
        edhrec.signals(HAZEL, theme="tokens")
        keys = [kw["key"] for _, kw in self.site.calls]
        self.assertEqual(len(set(keys)), 3)
        self.assertEqual(keys[1], "commanders__hazel-of-the-rootbloom__upgraded")

    def test_commander_meta_reads_the_bracket_page_when_asked(self):
        self.assertEqual(edhrec.commander_meta(HAZEL)["n_decks"], 1000)
        meta = edhrec.commander_meta(HAZEL, 3)
        self.assertEqual(meta["n_decks"], 100)
        self.assertEqual(meta["bracket_counts"][3], 1000)           # still every bracket's count
        self.assertEqual(meta["url"], edhrec.BASE + HAZEL_PAGE + "/upgraded.json")

    def test_a_page_with_no_cards_says_nothing(self):
        empty = copy.deepcopy(fixture("edhrec_commander.json"))
        empty["container"]["json_dict"]["cardlists"] = []
        self.serve({HAZEL_PAGE: empty})
        self.assertEqual(edhrec.signals(HAZEL), [])

    def test_a_page_without_card_lists_is_a_format_change_not_silence(self):
        self.serve({HAZEL_PAGE: {"container": {"json_dict": {}}}, "tags/tokens": ["not", "a", "page"]})
        self.assertRaises(net.FetchError, edhrec.signals, HAZEL)
        self.assertRaises(net.FetchError, edhrec.theme_commanders, "tokens")


class RedirectTests(SiteTestCase):
    WILSON = ["Wilson, Refined Grizzly", "Master Chef"]
    GUESS = "commanders/master-chef-wilson-refined-grizzly"        # names can't show a Background goes last
    REAL = "commanders/wilson-refined-grizzly-master-chef"

    def test_the_guess_for_a_commander_and_background_is_alphabetical(self):
        self.assertEqual("commanders/" + edhrec.commander_slug(self.WILSON), self.GUESS)

    def test_a_redirect_leads_to_the_real_page(self):
        self.serve({self.GUESS: {"redirect": "/" + self.REAL}, self.REAL: fixture("edhrec_commander.json")})
        sig = edhrec.signals(self.WILSON)[0]
        self.assertEqual(self.site.paths, [self.GUESS, self.REAL])
        self.assertEqual(sig["url"], edhrec.BASE + self.REAL + ".json")   # the page the data came from
        self.assertEqual(sig["n"], 1000)

    def test_sub_pages_redirect_too(self):
        self.serve({self.GUESS + "/upgraded": {"redirect": "/" + self.REAL + "/upgraded"},
                    self.REAL + "/upgraded": fixture("edhrec_commander.json")})
        self.assertEqual(edhrec.signals(self.WILSON, 3)[0]["bracket"], 3)
        self.assertEqual(self.site.paths, [self.GUESS + "/upgraded", self.REAL + "/upgraded"])

    def test_a_redirect_that_never_ends_is_given_up_on(self):
        page = fixture("edhrec_commander.json")
        self.serve({"commanders/a": {"redirect": "/commanders/b"},
                    "commanders/b": {"redirect": "/commanders/c"},
                    "commanders/c": {"redirect": "/commanders/d"}, "commanders/d": page})
        self.assertEqual(edhrec._page("commanders/a"), (None, None))
        self.assertEqual(len(self.site.calls), edhrec.MAX_REDIRECTS + 1)

    def test_a_redirect_to_an_unknown_kind_of_page_is_not_followed(self):
        self.serve({self.GUESS: {"redirect": "/cards/sol-ring"},
                    "cards/sol-ring": fixture("edhrec_commander.json")})
        self.assertEqual(edhrec.signals(self.WILSON), [])
        self.assertEqual(self.site.paths, [self.GUESS])

    def test_a_redirect_to_a_missing_page_is_no_signal(self):
        self.serve({self.GUESS: {"redirect": "/" + self.REAL}})
        self.assertEqual(edhrec.signals(self.WILSON), [])


class ThemeAndSaltTests(SiteTestCase):
    def setUp(self):
        self.serve({"tags/aristocrats": fixture("edhrec_theme_index.json"),
                    "top/salt": fixture("edhrec_salt.json")})

    def test_theme_commanders(self):
        found = edhrec.theme_commanders("Aristocrats")              # a label works as well as the slug
        self.assertEqual([c["name"] for c in found], POPULAR_FIRST)
        self.assertEqual(self.site.paths, ["tags/aristocrats"])
        self.assertEqual(edhrec.theme_commanders("not-a-theme"), [])

    def test_theme_signal_is_card_evidence_without_the_commanders(self):
        sig = edhrec.theme_signal("aristocrats")
        self.assertEqual((sig["source"], sig["kind"], sig["commanders"], sig["bracket"], sig["theme"]),
                         ("edhrec", "builder", [], None, "aristocrats"))
        self.assertEqual(sorted(sig["cards"]), ["Blood Artist", "Pitiless Plunderer", "Sol Ring"])
        self.assertEqual(sig["cards"]["Blood Artist"], {"decks": 3400, "of": 6700, "synergy": 0.39})
        self.assertEqual(sig["n"], 7000)                            # a colorless card fits every theme deck
        self.assertEqual(sig["meta"], {"label": "Aristocrats"})
        self.assertEqual(sig["url"], edhrec.BASE + "tags/aristocrats.json")
        self.assertIsNone(edhrec.theme_signal("not-a-theme"))

    def test_salt_scores(self):
        self.assertEqual(edhrec.salt_scores(), SALTY)
        self.assertEqual(self.site.paths, ["top/salt"])

    def test_salt_scores_are_empty_when_the_page_is_gone(self):
        self.serve({})
        self.assertEqual(edhrec.salt_scores(), {})


if __name__ == "__main__":
    unittest.main()
