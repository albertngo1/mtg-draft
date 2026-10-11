"""Tests for providers/edhtop16.py. The network is replaced by recorded GraphQL answers in fixtures/."""
import json, os, tempfile, unittest
from unittest import mock

from mtgcommander import net
from mtgcommander.providers import edhtop16

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


class FakeFetch:
    """Stands in for net.fetch_json: hands out the queued answers in order and records every call.
    An answer that is an Exception is raised instead of returned."""
    def __init__(self, *answers, cache="network"):
        self.answers, self.calls, self.cache = list(answers), [], cache

    def __call__(self, url, **kw):
        self.calls.append((url, kw))
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer, {"url": url, "fetched": "2026-10-11T12:00:00Z", "cache": self.cache, "age_days": 0.0}

    def variables(self, i):
        return self.calls[i][1]["data"]["variables"]


def patched(fake):
    return mock.patch.object(net, "fetch_json", fake)


PAIR = ["Tymna the Weaver", "Thrasios, Triton Hero"]


class NameTests(unittest.TestCase):
    def test_single_commander_keeps_its_name(self):
        name = "Chatterfang, Squirrel General"
        self.assertEqual(edhtop16.commander_name([name]), name)

    def test_partner_pair_is_alphabetical_whatever_order_it_is_given_in(self):
        # EDHTop16 lists "Thrasios, Triton Hero / Tymna the Weaver", never the reverse
        want = "Thrasios, Triton Hero / Tymna the Weaver"
        self.assertEqual(edhtop16.commander_name(PAIR), want)
        self.assertEqual(edhtop16.commander_name(list(reversed(PAIR))), want)

    def test_double_faced_commander_keeps_both_faces(self):
        name = "Etali, Primal Conqueror // Etali, Primal Sickness"
        self.assertEqual(edhtop16.commander_name([name]), name)

    def test_page_url_encodes_the_name(self):
        self.assertEqual(edhtop16._page_url(["Hazel of the Rootbloom"]),
                         "https://edhtop16.com/commander/Hazel%20of%20the%20Rootbloom")


class ParseEntryTests(unittest.TestCase):
    def node(self, standing, top_cut, cards=("Sol Ring",)):
        return {"id": "X", "wins": 2, "losses": 1, "draws": 1, "standing": standing,
                "maindeck": [{"name": c} for c in cards],
                "tournament": {"TID": "t", "name": "T", "size": 40, "topCut": top_cut,
                               "tournamentDate": "2026-10-10T19:00:00.000Z"}}

    def test_reaching_the_cut_means_standing_within_the_top_cut_size(self):
        # (standing, top-cut size, made the cut?) - a 16-player cut includes 16th place, not 17th
        cases = [(1, 16, True), (16, 16, True), (17, 16, False), (3, 4, True), (5, 4, False)]
        for standing, cut, made in cases:
            with self.subTest(standing=standing, cut=cut):
                self.assertEqual(edhtop16.parse_entry(self.node(standing, cut))["topcut"], made)

    def test_an_event_without_a_cut_has_no_top_cut_finishers(self):
        # Swiss-only events report topCut 0, so even the winner did not "convert"
        self.assertFalse(edhtop16.parse_entry(self.node(1, 0))["topcut"])

    def test_an_unranked_entry_did_not_make_the_cut(self):
        self.assertFalse(edhtop16.parse_entry(self.node(None, 16))["topcut"])

    def test_record_and_tournament_fields(self):
        entry = edhtop16.parse_entry(self.node(1, 16))
        self.assertEqual((entry["wins"], entry["losses"], entry["draws"], entry["standing"]), (2, 1, 1, 1))
        self.assertEqual(entry["tournament"],
                         {"name": "T", "date": "2026-10-10", "size": 40, "tid": "t", "top_cut": 16})

    def test_a_card_listed_twice_counts_once(self):
        entry = edhtop16.parse_entry(self.node(1, 4, cards=("Sol Ring", "Forest", "Sol Ring")))
        self.assertEqual(entry["cards"], ["Sol Ring", "Forest"])

    def test_no_decklist_means_no_entry(self):
        self.assertIsNone(edhtop16.parse_entry(self.node(1, 4, cards=())))
        self.assertIsNone(edhtop16.parse_entry({"id": "X", "maindeck": None}))


class ParsePageTests(unittest.TestCase):
    def test_entries_without_a_decklist_are_dropped_and_the_cursor_is_returned(self):
        found, cursor = edhtop16.parse_entries(fixture("edhtop16_entries_page1.json"))
        # E3 has an empty maindeck and E5 has none at all
        self.assertEqual([e["id"] for e in found], ["E1", "E2", "E4"])
        self.assertEqual(cursor, "5")

    def test_last_page_has_no_cursor(self):
        found, cursor = edhtop16.parse_entries(fixture("edhtop16_entries_page2.json"))
        self.assertEqual(len(found), 2)
        self.assertIsNone(cursor)

    def test_unknown_commander_is_an_empty_page(self):
        self.assertEqual(edhtop16.parse_entries(fixture("edhtop16_entries_missing.json")), ([], None))

    def test_stats(self):
        self.assertEqual(edhtop16.parse_stats(fixture("edhtop16_stats.json")),
                         {"entries": 284, "topcuts": 68, "conversion": 0.2394, "win_rate": 0.1998})

    def test_stats_of_an_unknown_commander_is_none(self):
        self.assertIsNone(edhtop16.parse_stats(fixture("edhtop16_entries_missing.json")))

    def test_commander_list(self):
        found, cursor = edhtop16.parse_commanders(fixture("edhtop16_commanders.json"))
        self.assertEqual(found[0],
                         {"name": "Sisay, Weatherlight Captain", "entries": 3340, "conversion": 0.2805})
        self.assertEqual(len(found), 3)
        self.assertIsNone(cursor)


class SignalTests(unittest.TestCase):
    """The four fixture entries with decklists, worked by hand:
        E1  3-1-0  cut     Sol Ring, Skullclamp, Forest, Swamp, Pitiless Plunderer
        E2  1-2-1  no cut  Sol Ring, Forest, Swamp, Demonic Tutor
        E4  2-1-1  no cut  Sol Ring, Skullclamp, Forest        (a Swiss-only event: nobody makes a cut)
        E6  2-1-1  cut     Sol Ring, Skullclamp, Mana Crypt, Forest"""
    @classmethod
    def setUpClass(cls):
        page1, _ = edhtop16.parse_entries(fixture("edhtop16_entries_page1.json"))
        page2, _ = edhtop16.parse_entries(fixture("edhtop16_entries_page2.json"))
        by_id = {e["id"]: e for e in page1 + page2}
        cls.entries = [by_id[i] for i in ("E1", "E2", "E4", "E6")]

    def signal(self, entries=None):
        return edhtop16.signals_from_entries(self.entries if entries is None else entries, ["Chatterfang"])

    def test_totals_cover_every_entry(self):
        sig = self.signal()
        self.assertEqual(sig["n"], 4)
        self.assertEqual(sig["totals"], {"entries": 4, "games": 16, "wins": 8, "draws": 3, "topcuts": 2})

    def test_a_card_in_every_deck_matches_the_totals(self):
        self.assertEqual(self.signal()["cards"]["Sol Ring"], self.signal()["totals"])

    def test_a_card_counts_only_the_entries_that_ran_it(self):
        cards = self.signal()["cards"]
        stats = lambda *v: dict(zip(("entries", "games", "wins", "draws", "topcuts"), v))
        self.assertEqual(cards["Skullclamp"], stats(3, 12, 7, 2, 2))     # E1, E4, E6
        self.assertEqual(cards["Swamp"], stats(2, 8, 4, 1, 1))           # E1, E2
        self.assertEqual(cards["Demonic Tutor"], stats(1, 4, 1, 1, 0))   # E2
        self.assertEqual(cards["Mana Crypt"], stats(1, 4, 2, 1, 1))      # E6

    def test_signal_record_shape(self):
        sig = self.signal()
        self.assertEqual((sig["source"], sig["kind"], sig["bracket"], sig["theme"]),
                         ("edhtop16", "tournament", None, None))
        self.assertEqual(sig["commanders"], ["Chatterfang"])
        for key in ("url", "fetched", "cache", "n", "cards", "totals", "meta"):
            self.assertIn(key, sig)

    def test_holding_a_deck_out_removes_exactly_its_contribution(self):
        held_out = [e for e in self.entries if e["id"] != "E6"]
        sig = self.signal(held_out)
        self.assertEqual(sig["n"], 3)
        self.assertNotIn("Mana Crypt", sig["cards"])
        self.assertEqual(sig["cards"]["Skullclamp"]["entries"], 2)
        self.assertEqual(sig["totals"]["topcuts"], 1)

    def test_building_a_signal_leaves_its_input_alone(self):
        before = json.dumps(self.entries, sort_keys=True)
        self.signal()
        self.assertEqual(json.dumps(self.entries, sort_keys=True), before)

    def test_no_entries_make_an_empty_signal(self):
        sig = self.signal([])
        self.assertEqual((sig["n"], sig["cards"]), (0, {}))
        self.assertEqual(sig["totals"], {"entries": 0, "games": 0, "wins": 0, "draws": 0, "topcuts": 0})


class EntriesTests(unittest.TestCase):
    def test_pages_are_followed_and_a_repeated_entry_is_kept_once(self):
        # The second page repeats E1 (a new tournament shifted the boundary between two runs)
        fake = FakeFetch(fixture("edhtop16_entries_page1.json"), fixture("edhtop16_entries_page2.json"))
        with patched(fake):
            found = edhtop16.entries(PAIR, "ONE_YEAR")
        self.assertEqual([e["id"] for e in found], ["E1", "E2", "E4", "E6"])
        self.assertEqual(len(fake.calls), 2)
        url, kw = fake.calls[0]
        self.assertEqual((url, kw["source"]), ("https://edhtop16.com/api/graphql", "edhtop16"))
        self.assertEqual(fake.variables(0), {"name": "Thrasios, Triton Hero / Tymna the Weaver",
                                             "first": edhtop16.PAGE, "after": None, "period": "ONE_YEAR"})
        self.assertEqual(fake.variables(1)["after"], "5")

    def test_each_page_has_its_own_cache_file(self):
        fake = FakeFetch(fixture("edhtop16_entries_page1.json"), fixture("edhtop16_entries_page2.json"))
        with patched(fake):
            edhtop16.entries(["Hazel of the Rootbloom"], "ONE_YEAR")
        keys = [kw["key"] for _, kw in fake.calls]
        self.assertEqual(len(set(keys)), 2)
        self.assertTrue(all(k.startswith("entries-hazel-of-the-rootbloom-") for k in keys))

    def test_limit_stops_the_read_early(self):
        fake = FakeFetch(fixture("edhtop16_entries_page1.json"))
        with patched(fake):
            found = edhtop16.entries(["Hazel of the Rootbloom"], "ONE_YEAR", limit=2)
        self.assertEqual([e["id"] for e in found], ["E1", "E2"])
        self.assertEqual(len(fake.calls), 1)

    def test_a_cursor_that_does_not_advance_cannot_loop_forever(self):
        stuck = fixture("edhtop16_entries_page1.json")  # always says "more, from cursor 5"
        fake = FakeFetch(stuck, stuck, stuck)
        with patched(fake):
            found = edhtop16.entries(["Hazel of the Rootbloom"], "ONE_YEAR")
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual(len(found), 3)

    def test_unknown_commander_has_no_entries(self):
        with patched(FakeFetch(fixture("edhtop16_entries_missing.json"))):
            self.assertEqual(edhtop16.entries(["No Such Commander"], "ONE_YEAR"), [])

    def test_the_run_wide_modes_pass_through_to_net(self):
        fake = FakeFetch(fixture("edhtop16_entries_missing.json"))
        with patched(fake):
            edhtop16.entries(["No Such Commander"], "ONE_YEAR", refresh=True, offline=False)
        self.assertEqual((fake.calls[0][1]["refresh"], fake.calls[0][1]["offline"]), (True, False))

    def test_a_time_period_the_site_does_not_have_is_refused_before_any_request(self):
        fake = FakeFetch()
        with patched(fake):
            with self.assertRaises(ValueError):
                edhtop16.entries(["Hazel of the Rootbloom"], "ONE_DECADE")
        self.assertEqual(fake.calls, [])


class ErrorTests(unittest.TestCase):
    def test_a_graphql_error_is_raised_and_not_left_in_the_cache(self):
        # The API reports transient failures with HTTP 200; net would keep that answer for a day
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cached.json")
            with open(path, "w") as f:
                f.write("{}")
            fake = FakeFetch({"errors": [{"message": "database timeout"}], "data": None})
            with patched(fake), mock.patch.object(net, "cache_file", return_value=path):
                with self.assertRaises(net.FetchError) as caught:
                    edhtop16.commander_stats(["Hazel of the Rootbloom"])
            self.assertIn("database timeout", str(caught.exception))
            self.assertFalse(os.path.exists(path))

    def test_no_rows_is_not_an_error_it_means_unknown_commander(self):
        with patched(FakeFetch(fixture("edhtop16_entries_missing.json"))):
            self.assertIsNone(edhtop16.commander_stats(["No Such Commander"]))

    def test_network_failure_propagates(self):
        with patched(FakeFetch(net.FetchError("edhtop16", "u", "HTTP 503"))):
            with self.assertRaises(net.FetchError):
                edhtop16.entries(["Hazel of the Rootbloom"])


class SignalsTests(unittest.TestCase):
    def test_a_theme_gets_no_signal_and_no_request(self):
        fake = FakeFetch()
        with patched(fake):
            self.assertEqual(edhtop16.signals(["Hazel of the Rootbloom"], 3, "tokens"), [])
        self.assertEqual(fake.calls, [])

    def test_signal_carries_the_sites_own_totals_and_where_the_data_came_from(self):
        fake = FakeFetch(fixture("edhtop16_entries_page2.json"), fixture("edhtop16_stats.json"))
        with patched(fake):
            sigs = edhtop16.signals(["Hazel of the Rootbloom"], 5)
        self.assertEqual(len(sigs), 1)
        sig = sigs[0]
        self.assertEqual(sig["n"], 2)
        self.assertEqual(sig["fetched"], "2026-10-11T12:00:00Z")
        self.assertEqual(sig["cache"], "network")
        self.assertEqual(sig["url"], "https://edhtop16.com/commander/Hazel%20of%20the%20Rootbloom")
        self.assertEqual(sig["meta"]["stats"]["topcuts"], 68)
        self.assertFalse(sig["meta"]["truncated"])
        self.assertEqual(sig["meta"]["time_period"], "ONE_YEAR")

    def test_a_limit_that_cuts_the_data_is_reported(self):
        fake = FakeFetch(fixture("edhtop16_entries_page1.json"), fixture("edhtop16_stats.json"))
        with patched(fake):
            sig = edhtop16.signals(["Hazel of the Rootbloom"], 5, limit=2)[0]
        self.assertEqual(sig["n"], 2)
        self.assertTrue(sig["meta"]["truncated"])

    def test_cache_state_is_reported_as_stale_if_any_page_was_stale(self):
        fake = FakeFetch(fixture("edhtop16_entries_page1.json"), fixture("edhtop16_entries_page2.json"),
                         fixture("edhtop16_stats.json"), cache="stale")
        with patched(fake):
            sig = edhtop16.signals(["Hazel of the Rootbloom"], 5)[0]
        self.assertEqual(sig["cache"], "stale")

    def test_unknown_commander_gets_no_signal(self):
        with patched(FakeFetch(fixture("edhtop16_entries_missing.json"))):
            self.assertEqual(edhtop16.signals(["No Such Commander"], 5), [])

    def test_commander_stats_asks_for_the_period(self):
        fake = FakeFetch(fixture("edhtop16_stats.json"))
        with patched(fake):
            stats = edhtop16.commander_stats(["Chatterfang, Squirrel General"], "SIX_MONTHS")
        self.assertEqual(stats["entries"], 284)
        self.assertEqual(fake.variables(0), {"name": "Chatterfang, Squirrel General", "period": "SIX_MONTHS"})


class TopCommandersTests(unittest.TestCase):
    def test_most_played_first(self):
        fake = FakeFetch(fixture("edhtop16_commanders.json"))
        with patched(fake):
            top = edhtop16.top_commanders(150)
        self.assertEqual([c["name"] for c in top],
                         ["Kinnan, Bonder Prodigy", "Sisay, Weatherlight Captain",
                          "Thrasios, Triton Hero / Tymna the Weaver"])
        self.assertEqual(fake.variables(0)["minEntries"], 150)

    def test_pages_are_followed(self):
        first = fixture("edhtop16_commanders.json")
        first["data"]["commanders"]["pageInfo"] = {"hasNextPage": True, "endCursor": "3"}
        second = {"data": {"commanders": {"pageInfo": {"hasNextPage": False, "endCursor": "4"}, "edges": [
            {"node": {"name": "Magda, Brazen Outlaw", "stats": {"count": 1850, "conversionRate": 0.2886}}}]}}}
        fake = FakeFetch(first, second)
        with patched(fake):
            top = edhtop16.top_commanders(150)
        self.assertEqual(len(top), 4)
        self.assertEqual(fake.variables(1)["after"], "3")


if __name__ == "__main__":
    unittest.main()
