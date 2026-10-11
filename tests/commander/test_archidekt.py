"""Tests for providers/archidekt.py: the parsers against hand-written fixtures in Archidekt's shape, and the
search-then-download logic against a stand-in for net.fetch_json. Nothing here touches the network or the
cache folder."""
import copy, inspect, json, os, unittest, urllib.parse
from unittest import mock
from mtgcommander import net
from mtgcommander.providers import archidekt

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
HAZEL = ["Hazel of the Rootbloom"]
CHATTERFANG = ("Chatterfang, Squirrel General",)
ESIKA = "Esika, God of the Tree // The Prismatic Bridge"


def fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


def deck_object(deck_id, commanders=("Hazel of the Rootbloom",), bracket=3, swamps=None):
    """A deck detail built from the fixture: 100 main-deck cards, the commander(s) swapped in, and the number
    of Swamps adjustable to make the deck short or long."""
    deck = fixture("archidekt_deck.json")
    deck["id"], deck["edhBracket"] = deck_id, bracket
    entries = deck["cards"]
    swamp = next(e for e in entries if e["card"]["oracleCard"]["name"] == "Swamp")
    entries[0]["card"]["oracleCard"]["name"] = commanders[0]
    for partner in commanders[1:]:
        entries.append({"categories": ["Commander"], "quantity": 1, "deletedAt": None, "companion": False,
                        "card": {"oracleCard": {"name": partner}}})
        swamp["quantity"] -= 1                   # the partner takes a slot of the 100
    if swamps is not None:
        swamp["quantity"] = swamps
    return deck


def rename(deck, old, new):
    for entry in deck["cards"]:
        if entry["card"]["oracleCard"]["name"] == old:
            entry["card"]["oracleCard"]["name"] = new
    return deck


def summary(deck_id, size=100, bracket=3):
    return {"id": deck_id, "name": f"Deck {deck_id}", "size": size, "edhBracket": bracket,
            "updatedAt": "2026-10-11T14:40:21.020828Z", "private": False, "unlisted": False}


def search_page(*summaries, more=False):
    return {"count": len(summaries), "next": "http://archidekt.com/api/decks/v3/?page=2" if more else None,
            "results": list(summaries)}


def query_of(url):
    return urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)


class FakeArchidekt:
    """Stands in for net.fetch_json. `pages` maps a search page number to its payload, `decks` maps a deck id
    to its payload (None = deleted since the search). `state` and `fetched` say what an answer reports about
    its cache, keyed by deck id, or by "search" for the search pages; the default is a fresh download.
    Every request is recorded."""
    def __init__(self, pages, decks, state=None, fetched=None):
        self.pages, self.decks = pages, decks
        self.state, self.fetched, self.calls = state or {}, fetched or {}, []

    def __call__(self, url, **kw):
        self.calls.append((url, kw))
        if kw["source"] == "archidekt_search":
            who = "search"
            payload = self.pages[int(query_of(url)["page"][0])]
        else:
            who = int(url.rstrip("/").rsplit("/", 1)[1])
            if self.decks.get(who) is None:
                raise net.NotFound(kw["source"], url, "no such deck")
            payload = self.decks[who]
        info = {"url": url, "fetched": self.fetched.get(who, "2026-10-11T12:00:00Z"),
                "cache": self.state.get(who, "network"), "age_days": 0.0}
        return copy.deepcopy(payload), info

    @property
    def searched(self):
        return [query_of(u)["page"][0] for u, kw in self.calls if kw["source"] == "archidekt_search"]

    @property
    def downloaded(self):
        return [int(u.rstrip("/").rsplit("/", 1)[1]) for u, kw in self.calls if kw["source"] == "archidekt"]


class SiteTestCase(unittest.TestCase):
    def serve(self, pages, decks, **kw):
        self.site = FakeArchidekt(pages, decks, **kw)
        patcher = mock.patch.object(net, "fetch_json", self.site)
        patcher.start()
        self.addCleanup(patcher.stop)


class ParseTests(unittest.TestCase):
    def test_search_url_carries_the_filters_found_in_the_real_api(self):
        url = archidekt.search_url("Kraum, Ludevic's Opus", 3, 2)
        self.assertEqual(url.split("?")[0], "https://archidekt.com/api/decks/v3/")
        self.assertEqual(query_of(url), {"commanderName": ["Kraum, Ludevic's Opus"], "edhBracket": ["3"],
                                         "formats": ["3"], "orderBy": ["-updatedAt"], "page": ["2"]})

    def test_no_bracket_means_no_bracket_filter(self):
        query = query_of(archidekt.search_url("Hazel of the Rootbloom"))
        self.assertNotIn("edhBracket", query)
        self.assertEqual(query["page"], ["1"])

    def test_a_double_faced_commander_is_searched_by_its_full_name(self):
        # the front face alone finds nothing on Archidekt
        self.assertEqual(query_of(archidekt.search_url(ESIKA))["commanderName"], [ESIKA])

    def test_search_summaries(self):
        rows = archidekt.parse_search(fixture("archidekt_search.json"))
        self.assertEqual([r["id"] for r in rows], [101, 102, 103, 105])          # 104 is private
        self.assertEqual(rows[0], {"id": 101, "size": 100, "bracket": 3, "updated": "2026-10-11T14:40:21Z"})
        self.assertIsNone(rows[2]["bracket"])                                     # not rated yet
        self.assertEqual(archidekt.parse_search({"count": -1, "next": None, "results": []}), [])

    def test_deck_record(self):
        deck = archidekt.parse_deck(fixture("archidekt_deck.json"))
        self.assertEqual((deck["id"], deck["url"], deck["bracket"], deck["updated"]),
                         (101, "https://archidekt.com/decks/101", 3, "2026-10-11T14:40:21Z"))
        self.assertEqual(deck["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(deck["cards"], [
            "Skullclamp", "Sol Ring", "Westvale Abbey // Ormendahl, Profane Prince", "Pitiless Plunderer",
            "Burgeoning", "Forest", "Swamp"])
        self.assertEqual(deck["size"], 100)                      # copies, the commander included

    def test_which_cards_count_toward_the_deck(self):
        cards = archidekt.parse_deck(fixture("archidekt_deck.json"))["cards"]
        self.assertIn("Burgeoning", cards)                # ['Ramp', 'Maybeboard']: the first category decides
        for name, why in [("Grim Backwoods", "first category is Maybeboard"),
                          ("Squirrel Sovereign", "Sideboard, though Archidekt flags it included in the deck"),
                          ("Squirrel Token", "its category is switched off for the deck"),
                          ("Chatterfang, Squirrel General", "deleted from the deck"),
                          ("Lurrus of the Dream-Den", "a companion sits outside the 100"),
                          ("Hazel of the Rootbloom", "the commander is listed apart")]:
            with self.subTest(name=name):
                self.assertNotIn(name, cards, why)

    def test_a_card_with_no_category_is_in_the_deck(self):
        island = {"categories": [], "quantity": 3, "card": {"oracleCard": {"name": "Island"}}}
        deck = archidekt.parse_deck({"categories": [], "cards": [island]})
        self.assertEqual((deck["cards"], deck["size"]), (["Island"], 3))

    def test_partners_are_both_commanders(self):
        deck = archidekt.parse_deck(deck_object(7, ("Kraum, Ludevic's Opus", "Tymna the Weaver")))
        self.assertEqual(deck["commanders"], ["Kraum, Ludevic's Opus", "Tymna the Weaver"])
        self.assertEqual(deck["size"], 100)

    def test_a_card_in_two_entries_is_listed_once_but_counted_twice(self):
        obj = {"categories": [], "cards": [
            {"categories": ["Land"], "quantity": 2, "card": {"oracleCard": {"name": "Forest"}}},
            {"categories": ["Land"], "quantity": 3, "card": {"oracleCard": {"name": "Forest"}}}]}
        deck = archidekt.parse_deck(obj)
        self.assertEqual((deck["cards"], deck["size"]), (["Forest"], 5))

    def test_a_bare_deck_gives_an_empty_record(self):
        deck = archidekt.parse_deck({})
        self.assertEqual((deck["commanders"], deck["cards"], deck["size"], deck["bracket"]),
                         ([], [], 0, None))


class DecksTests(SiteTestCase):
    def test_complete_decks_of_the_commander_newest_first(self):
        self.serve({1: search_page(summary(101), summary(102, size=113), summary(103), summary(104),
                                   summary(105), summary(106))},
                   {101: deck_object(101),
                    103: deck_object(103, CHATTERFANG),            # plays Hazel, but she is not the commander
                    104: deck_object(104, swamps=34),              # the summary says 100, the list is 90
                    105: None,                                     # deleted since the search
                    106: deck_object(106)})
        found = archidekt.decks(HAZEL, 3, limit=5)
        self.assertEqual([d["id"] for d in found], [101, 106])
        self.assertEqual(self.site.downloaded, [101, 103, 104, 105, 106])   # 102 (113 cards) is skipped

    def test_stops_at_the_limit_without_asking_for_another_page(self):
        # the limit is reached on the last deck of page 1, which says there is a page 2: not to be fetched
        self.serve({1: search_page(summary(1), summary(2), more=True), 2: search_page(summary(3))},
                   {i: deck_object(i) for i in (1, 2, 3)})
        self.assertEqual([d["id"] for d in archidekt.decks(HAZEL, 3, limit=2)], [1, 2])
        self.assertEqual((self.site.searched, self.site.downloaded), (["1"], [1, 2]))

    def test_the_next_page_is_fetched_only_when_needed(self):
        self.serve({1: search_page(summary(1), more=True), 2: search_page(summary(2), summary(3))},
                   {i: deck_object(i) for i in (1, 2, 3)})
        self.assertEqual([d["id"] for d in archidekt.decks(HAZEL, 3, limit=3)], [1, 2, 3])
        self.assertEqual(self.site.searched, ["1", "2"])

    def test_a_deck_listed_on_two_pages_counts_once(self):
        self.serve({1: search_page(summary(1), more=True), 2: search_page(summary(1), summary(2))},
                   {i: deck_object(i) for i in (1, 2)})
        self.assertEqual([d["id"] for d in archidekt.decks(HAZEL, 3, limit=5)], [1, 2])
        self.assertEqual(self.site.downloaded, [1, 2])

    def test_search_pages_are_capped(self):
        pages = {n: search_page(summary(n, size=1), more=True) for n in range(1, 20)}   # never a usable deck
        self.serve(pages, {})
        self.assertEqual(archidekt.decks(HAZEL, 3, limit=5), [])
        self.assertEqual(len(self.site.searched), archidekt.MAX_PAGES)

    def test_the_bracket_is_checked_again_on_the_deck(self):
        self.serve({1: search_page(summary(1), summary(2), summary(3))},
                   {1: deck_object(1), 2: deck_object(2, bracket=2), 3: deck_object(3, bracket=None)})
        rated_3 = archidekt.decks(HAZEL, 3)                          # owners re-rate decks after a search
        self.assertEqual([d["id"] for d in rated_3], [1])
        self.assertEqual([d["id"] for d in archidekt.decks(HAZEL, None)], [1, 2, 3])   # no bracket: any

    def test_a_pair_is_searched_by_its_first_name_and_both_must_be_commanders(self):
        kraum, tymna = "Kraum, Ludevic's Opus", "Tymna the Weaver"
        self.serve({1: search_page(*(summary(i) for i in range(1, 6)))},
                   {1: deck_object(1, (kraum, tymna)),
                    2: deck_object(2, (kraum,)),                       # Kraum alone is another deck
                    3: deck_object(3, (kraum, "Thrasios, Triton Hero")),
                    4: deck_object(4, (tymna, kraum)),                 # the order in the deck does not matter
                    5: deck_object(5, (kraum, tymna, "Third Wheel"))})
        found = archidekt.decks([kraum, tymna], 3)
        self.assertEqual([d["id"] for d in found], [1, 4])
        self.assertEqual(query_of(self.site.calls[0][0])["commanderName"], [kraum])

    def test_commander_names_match_across_accents_apostrophes_and_double_faces(self):
        self.serve({1: search_page(summary(1), summary(2))},
                   {1: deck_object(1, ("Esika, God of the Tree",)),          # this deck lists the front face
                    2: deck_object(2, ("Lim-Dul the Necromancer",))})
        self.assertEqual([d["id"] for d in archidekt.decks([ESIKA], 3)], [1])
        self.assertEqual([d["id"] for d in archidekt.decks(["Lim-Dûl the Necromancer"], 3)], [2])

    def test_downloads_are_capped_so_a_pair_search_cannot_run_away(self):
        self.serve({1: search_page(*(summary(i) for i in range(1, 21)))},
                   {i: deck_object(i, CHATTERFANG) for i in range(1, 21)})
        self.assertEqual(archidekt.decks(HAZEL, 3, limit=2), [])
        self.assertEqual(len(self.site.downloaded), archidekt.DOWNLOADS_PER_DECK * 2)

    def test_decks_already_cached_do_not_count_against_the_cap(self):
        self.serve({1: search_page(*(summary(i) for i in range(1, 21)))},
                   {i: deck_object(i, CHATTERFANG) for i in range(1, 21)},
                   state={i: "fresh" for i in range(1, 21)})
        self.assertEqual(archidekt.decks(HAZEL, 3, limit=2), [])
        self.assertEqual(len(self.site.downloaded), 20)         # all 20 looked at, none of them a download

    def test_no_commanders_or_no_room_means_no_request(self):
        self.serve({}, {})
        self.assertEqual(archidekt.decks([], 3), [])
        self.assertEqual(archidekt.decks(HAZEL, 3, limit=0), [])
        self.assertEqual(self.site.calls, [])

    def test_a_response_in_the_wrong_shape_is_an_error_not_an_empty_answer(self):
        self.serve({1: {"detail": "gone"}}, {})
        self.assertRaises(net.FetchError, archidekt.decks, HAZEL, 3)
        self.serve({1: search_page(summary(1))}, {1: {"detail": "gone"}})
        self.assertRaises(net.FetchError, archidekt.decks, HAZEL, 3)

    def test_sources_and_cache_keys(self):
        self.serve({1: search_page(summary(101))}, {101: deck_object(101)})
        archidekt.decks(HAZEL, 3, limit=1)
        (_, search), (_, deck) = self.site.calls
        self.assertEqual((search["source"], search["key"]),
                         ("archidekt_search", "search_Hazel of the Rootbloom_3_p1"))
        self.assertEqual((deck["source"], deck["key"]), ("archidekt", "deck_101"))

    def test_run_wide_modes_pass_through_to_net(self):
        self.serve({1: search_page(summary(101))}, {101: deck_object(101)})
        archidekt.decks(HAZEL, 3, limit=1, refresh=True, offline=False)
        for _, kw in self.site.calls:
            self.assertEqual((kw["refresh"], kw["offline"]), (True, False))

    def test_default_limit_matches_the_contract(self):
        self.assertEqual(inspect.signature(archidekt.decks).parameters["limit"].default, 40)
        self.assertEqual(inspect.signature(archidekt.signals).parameters["limit"].default, 40)


class SignalTests(SiteTestCase):
    def three_decks(self, **kw):
        a, b, c = deck_object(101), rename(deck_object(102), "Skullclamp", "Blood Artist"), deck_object(103)
        self.serve({1: search_page(summary(101), summary(102), summary(103))}, {101: a, 102: b, 103: c}, **kw)

    def test_signal_counts_how_many_decks_play_each_card(self):
        self.three_decks()
        found = archidekt.signals(HAZEL, 3, limit=3)
        self.assertEqual(len(found), 1)
        sig = found[0]
        self.assertEqual((sig["source"], sig["kind"], sig["commanders"], sig["bracket"], sig["theme"]),
                         ("archidekt", "builder", HAZEL, 3, None))
        self.assertEqual((sig["n"], sig["totals"], sig["meta"]), (3, None, {"deck_ids": [101, 102, 103]}))
        self.assertEqual(sig["cards"]["Skullclamp"], {"decks": 2, "of": 3, "synergy": None})
        self.assertEqual(sig["cards"]["Blood Artist"], {"decks": 1, "of": 3, "synergy": None})
        self.assertEqual(sig["cards"]["Forest"], {"decks": 3, "of": 3, "synergy": None})
        self.assertNotIn("Hazel of the Rootbloom", sig["cards"])        # a commander is not a card to add
        self.assertTrue(sig["url"].startswith("https://archidekt.com/api/decks/v3/?commanderName="))

    def test_signal_is_as_old_as_its_oldest_piece(self):
        self.three_decks(fetched={"search": "2026-10-11T12:00:00Z", 101: "2026-10-09T08:00:00Z",
                                  102: "2026-10-05T09:00:00Z", 103: "2026-10-10T10:00:00Z"})
        self.assertEqual(archidekt.signals(HAZEL, 3, limit=3)[0]["fetched"], "2026-10-05T09:00:00Z")

    def test_signal_is_as_unsure_as_its_least_sure_piece(self):
        everything_cached = {"search": "fresh", 101: "fresh", 102: "fresh", 103: "fresh"}
        cases = [({}, "fresh"), ({102: "network"}, "network"), ({"search": "network"}, "network"),
                 ({102: "stale", 103: "network"}, "stale")]
        for change, expected in cases:
            with self.subTest(change=change):
                self.three_decks(state={**everything_cached, **change})
                self.assertEqual(archidekt.signals(HAZEL, 3, limit=3)[0]["cache"], expected)

    def test_a_theme_gets_nothing_and_asks_for_nothing(self):
        self.three_decks()
        self.assertEqual(archidekt.signals(HAZEL, 3, "tokens"), [])
        self.assertEqual(self.site.calls, [])

    def test_no_qualifying_deck_means_no_signal(self):
        self.serve({1: search_page(summary(1))}, {1: deck_object(1, CHATTERFANG)})
        self.assertEqual(archidekt.signals(HAZEL, 3), [])

    def test_unknown_commander_means_no_signal(self):
        self.serve({1: {"count": -1, "next": None, "results": []}}, {})
        self.assertEqual(archidekt.signals(["Nobody Home"], 3), [])
        self.assertEqual(self.site.downloaded, [])


if __name__ == "__main__":
    unittest.main()
