"""Tests for providers/edhtop16.py. The network is replaced by recorded-shape answers in fixtures/ (see
edhtop16.py's docstring for the persisted queries and what each returns)."""
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

    def body(self, i):
        return self.calls[i][1]["data"]


def patched(fake):
    return mock.patch.object(net, "fetch_json", fake)


KEY_OF_ID = {query_id: key for key, (_, query_id) in edhtop16.PERSISTED.items()}


class FakeSite(FakeFetch):
    """The whole API: each route is a function from a request's variables to its answer (an Exception is
    raised), picked by the persisted query id in the request body. A query nobody wrote a route for fails."""
    def __init__(self, routes, cache="network"):
        super().__init__(cache=cache)
        self.routes = routes

    def __call__(self, url, **kw):
        self.calls.append((url, kw))
        answer = self.routes[KEY_OF_ID[kw["data"]["extensions"]["pastoria-id"]]](kw["data"]["variables"])
        if isinstance(answer, Exception):
            raise answer
        return answer, {"url": url, "fetched": "2026-10-11T12:00:00Z", "cache": self.cache, "age_days": 0.0}

    def asked(self, key):
        """The variables of every request for this persisted query, in order."""
        return [kw["data"]["variables"] for _, kw in self.calls
                if KEY_OF_ID[kw["data"]["extensions"]["pastoria-id"]] == key]


# Chatterfang's six window entries (fixtures: E1-E5 on the first page, E1 again and E6 on the second):
#   E1 3-1-0   E2 1-2-1   E3 2-2-0 (no decklist)   E4 2-1-1   E5 0-4-0   E6 2-1-1
# 24 games, 10 wins, 3 draws in all. The decks that ran each staple, all time (OLD1 and OLD2 are older than the
# window); Skullclamp's list is the recorded fixture, the others are built from these ids.
CARD_DECKS = {"Sol Ring": ["E1", "E2", "E3", "E4", "E5", "E6", "OLD1"],
              "Mana Crypt": ["E6", "OLD1"],
              "Demonic Tutor": ["OLD1"]}               # only a deck from before the window
WINDOW_TOTALS = {"entries": 6, "games": 24, "wins": 10, "draws": 3, "topcuts": 0}


def card_page(ids, cursor=None, more=False):
    """A card-entries answer for these entry ids."""
    edges = [{"node": {"id": i, "standing": 1, "wins": 0, "losses": 0, "draws": 0}, "cursor": str(k)}
             for k, i in enumerate(ids, 1)]
    return {"data": {"commander": {"cardEntries": {"edges": edges,
                                                   "pageInfo": {"endCursor": cursor, "hasNextPage": more}}}}}


def chatterfang_site(**override):
    """The API with Chatterfang's recorded answers; `override` replaces routes by their persisted key."""
    def card(variables):
        if variables["cardName"] == "Skullclamp":
            return fixture("edhtop16_card_entries.json")
        return card_page(CARD_DECKS.get(variables["cardName"], []))
    routes = {"stats": lambda v: fixture("edhtop16_stats.json"),
              "entries": lambda v: fixture("edhtop16_entries_page1.json"),
              "entries_more": lambda v: fixture("edhtop16_entries_page2.json"),
              "staples": lambda v: fixture("edhtop16_staples.json"),
              "card_entries": card}
    routes.update(override)
    return FakeSite(routes)


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
    def node(self, **over):
        node = {"id": "X", "wins": 2, "losses": 1, "draws": 1, "standing": 3, "decklist": "https://topdeck.gg/deck/t/X",
                "tournament": {"TID": "t", "name": "T", "size": 40, "tournamentDate": "2026-10-10T19:00:00.000Z"}}
        node.update(over)
        return node

    def test_record_and_tournament_fields(self):
        entry = edhtop16.parse_entry(self.node())
        self.assertEqual((entry["id"], entry["wins"], entry["losses"], entry["draws"], entry["standing"]),
                         ("X", 2, 1, 1, 3))
        self.assertEqual(entry["tournament"],
                         {"name": "T", "date": "2026-10-10", "size": 40, "tid": "t", "top_cut": None})

    def test_the_site_gives_no_card_list_and_no_top_cut_size_so_both_are_unknown(self):
        # A winner (standing 1) still reads as "did not make the cut": the persisted queries cannot say
        entry = edhtop16.parse_entry(self.node(standing=1))
        self.assertEqual((entry["cards"], entry["topcut"]), ([], False))

    def test_an_entry_without_a_decklist_is_kept(self):
        # The player never submitted a list, but the 2-1-1 record is still a result
        entry = edhtop16.parse_entry(self.node(decklist=None, decklistUrl=None))
        self.assertEqual((entry["id"], entry["wins"]), ("X", 2))

    def test_a_node_without_an_id_is_dropped(self):
        # Without an id it could not be matched to the decks that ran a card
        self.assertIsNone(edhtop16.parse_entry(self.node(id=None)))
        self.assertIsNone(edhtop16.parse_entry({}))

    def test_a_missing_tournament_is_not_a_crash(self):
        entry = edhtop16.parse_entry(self.node(tournament=None))
        self.assertEqual(entry["tournament"]["date"], "")


class ParsePageTests(unittest.TestCase):
    def test_the_first_entries_page_keeps_every_entry_and_returns_the_cursor(self):
        found, cursor = edhtop16.parse_entries(fixture("edhtop16_entries_page1.json"))
        # E3 submitted no decklist: it is still an entry
        self.assertEqual([e["id"] for e in found], ["E1", "E2", "E3", "E4", "E5"])
        self.assertEqual(cursor, "5")

    def test_the_follow_up_page_answers_under_node_and_the_last_page_has_no_cursor(self):
        found, cursor = edhtop16.parse_entries(fixture("edhtop16_entries_page2.json"))
        self.assertEqual([e["id"] for e in found], ["E1", "E6"])
        self.assertIsNone(cursor)

    def test_the_commander_node_id_comes_from_the_first_page(self):
        self.assertEqual(edhtop16.parse_commander_id(fixture("edhtop16_entries_page1.json")),
                         "Q29tbWFuZGVyOjExOQ==")

    def test_unknown_commander_is_an_empty_page_without_an_id(self):
        missing = fixture("edhtop16_entries_missing.json")
        self.assertEqual(edhtop16.parse_entries(missing), ([], None))
        self.assertIsNone(edhtop16.parse_commander_id(missing))

    def test_stats(self):
        # 284 entries x 23.94% conversion = 67.99: 68 top cuts. The query has no game win rate.
        self.assertEqual(edhtop16.parse_stats(fixture("edhtop16_stats.json")),
                         {"entries": 284, "topcuts": 68, "conversion": 0.2394, "win_rate": None})

    def test_stats_of_an_unknown_commander_is_none(self):
        self.assertIsNone(edhtop16.parse_stats(fixture("edhtop16_entries_missing.json")))

    def test_staples_are_the_card_names_most_played_first(self):
        self.assertEqual(edhtop16.parse_staples(fixture("edhtop16_staples.json")),
                         ["Sol Ring", "Skullclamp", "Mana Crypt", "Demonic Tutor"])
        self.assertEqual(edhtop16.parse_staples(fixture("edhtop16_entries_missing.json")), [])

    def test_the_decks_that_ran_a_card_are_a_set_of_entry_ids(self):
        ids, last, cursor = edhtop16.parse_card_entries(fixture("edhtop16_card_entries.json"))
        self.assertEqual(ids, {"E1", "E4", "E6", "OLD1", "OLD2"})
        self.assertEqual(last, "OLD2")      # the page's oldest deck: signals() stops paging once it is outside
        self.assertIsNone(cursor)           # the window
        self.assertEqual(edhtop16.parse_card_entries(card_page([])), (set(), None, None))

    def test_commander_list(self):
        found, cursor = edhtop16.parse_commanders(fixture("edhtop16_commanders.json"))
        self.assertEqual(found[0],
                         {"name": "Sisay, Weatherlight Captain", "entries": 3340, "conversion": 0.2805})
        self.assertEqual(len(found), 3)
        self.assertIsNone(cursor)


class GraphqlErrorTests(unittest.TestCase):
    def test_an_error_object_gives_its_message(self):
        self.assertEqual(edhtop16._graphql_errors({"errors": [{"message": "database timeout"}]}),
                         ["database timeout"])

    def test_a_bare_string_error_counts_too(self):
        # 2026-10-19: the gate against plain-text queries answers like this, and it was once read as "no errors"
        refusal = "Only persisted queries are allowed in production. Plain text queries are disabled."
        self.assertEqual(edhtop16._graphql_errors({"errors": [refusal]}), [refusal])

    def test_no_rows_is_left_out_whatever_its_shape(self):
        # It means an unknown commander, not a failure
        self.assertEqual(edhtop16._graphql_errors(fixture("edhtop16_entries_missing.json")), [])
        self.assertEqual(edhtop16._graphql_errors({"errors": ["Query returned no rows"]}), [])

    def test_no_rows_does_not_hide_a_real_error_next_to_it(self):
        errors = [{"message": "Query returned no rows"}, "boom", {"message": "bang"}]
        self.assertEqual(edhtop16._graphql_errors({"errors": errors}), ["boom", "bang"])

    def test_an_error_object_without_a_message_still_counts(self):
        self.assertEqual(len(edhtop16._graphql_errors({"errors": [{"extensions": {"code": "X"}}]})), 1)

    def test_empty_entries_are_not_errors(self):
        for errors in (None, [], [""], [None], [{}]):
            with self.subTest(errors=errors):
                self.assertEqual(edhtop16._graphql_errors({"errors": errors, "data": {}}), [])


def record(entry_id, wins, losses, draws, topcut, cards):
    """An entry that carries its own card list, as validate.py's held-out decks do."""
    return {"id": entry_id, "wins": wins, "losses": losses, "draws": draws, "standing": 1, "topcut": topcut,
            "cards": cards, "tournament": {}}


class SignalFromEntriesTests(unittest.TestCase):
    """Four entries with card lists, worked by hand:
        E1  3-1-0  cut     Sol Ring, Skullclamp, Forest, Swamp, Pitiless Plunderer
        E2  1-2-1  no cut  Sol Ring, Forest, Swamp, Demonic Tutor
        E4  2-1-1  no cut  Sol Ring, Skullclamp, Forest        (a Swiss-only event: nobody makes a cut)
        E6  2-1-1  cut     Sol Ring, Skullclamp, Mana Crypt, Forest"""
    entries = [record("E1", 3, 1, 0, True, ["Sol Ring", "Skullclamp", "Forest", "Swamp", "Pitiless Plunderer"]),
               record("E2", 1, 2, 1, False, ["Sol Ring", "Forest", "Swamp", "Demonic Tutor"]),
               record("E4", 2, 1, 1, False, ["Sol Ring", "Skullclamp", "Forest"]),
               record("E6", 2, 1, 1, True, ["Sol Ring", "Skullclamp", "Mana Crypt", "Forest"])]

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

    def test_a_card_listed_twice_in_one_deck_counts_once(self):
        sig = self.signal([record("E1", 3, 1, 0, True, ["Sol Ring", "Forest", "Sol Ring"])])
        self.assertEqual(sig["cards"]["Sol Ring"]["entries"], 1)

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


class RequestTests(unittest.TestCase):
    def test_a_persisted_query_is_sent_by_id_with_no_query_text(self):
        fake = FakeFetch(fixture("edhtop16_stats.json"))
        with patched(fake):
            edhtop16.commander_stats(["Chatterfang, Squirrel General"], "SIX_MONTHS")
        url, kw = fake.calls[0]
        self.assertEqual((url, kw["source"]), ("https://edhtop16.com/api/graphql", "edhtop16"))
        self.assertEqual(fake.body(0), {"variables": {"commander": "Chatterfang, Squirrel General",
                                                      "minEventSize": 0, "timePeriod": "SIX_MONTHS"},
                                        "extensions": {"pastoria-id": "365ea6c7d469ca7dc4420af2a9ac0e94"}})
        self.assertNotIn("query", fake.body(0))

    def test_every_query_has_its_own_id(self):
        ids = [query_id for _, query_id in edhtop16.PERSISTED.values()]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertTrue(all(len(i) == 32 and set(i) <= set("0123456789abcdef") for i in ids))

    def test_a_refreshed_id_never_reads_an_answer_cached_under_the_old_one(self):
        variables = {"commander": "Hazel of the Rootbloom"}
        self.assertNotEqual(edhtop16._cache_key("stats", "a" * 32, variables, "Hazel of the Rootbloom"),
                            edhtop16._cache_key("stats", "b" * 32, variables, "Hazel of the Rootbloom"))

    def test_the_cache_file_name_reads_as_query_then_commander(self):
        key = edhtop16._cache_key("stats", "a" * 32, {"commander": "X"}, "Hazel of the Rootbloom")
        self.assertTrue(key.startswith("stats-hazel-of-the-rootbloom-"), key)


class EntriesTests(unittest.TestCase):
    def test_both_queries_are_followed_and_a_repeated_entry_is_kept_once(self):
        # The second page repeats E1 (a new tournament shifted the boundary between two runs)
        site = chatterfang_site()
        with patched(site):
            found = edhtop16.entries(PAIR, "ONE_YEAR")
        self.assertEqual([e["id"] for e in found], ["E1", "E2", "E3", "E4", "E5", "E6"])
        filters = {"minEventSize": 0, "timePeriod": "ONE_YEAR", "sortBy": "NEW", "maxStanding": None}
        self.assertEqual(site.asked("entries"), [{"commander": "Thrasios, Triton Hero / Tymna the Weaver", **filters}])
        # the follow-up is keyed by the commander's node id from the first answer, 200 at a time
        self.assertEqual(site.asked("entries_more"),
                         [{"id": "Q29tbWFuZGVyOjExOQ==", "count": 200, "cursor": "5", **filters}])

    def test_a_commander_with_one_page_costs_one_request(self):
        one_page = fixture("edhtop16_entries_page1.json")
        one_page["data"]["commander"]["entries"]["pageInfo"] = {"endCursor": "5", "hasNextPage": False}
        site = chatterfang_site(entries=lambda v: one_page)
        with patched(site):
            found = edhtop16.entries(["Hazel of the Rootbloom"], "ONE_YEAR")
        self.assertEqual(len(found), 5)
        self.assertEqual(len(site.calls), 1)

    def test_each_page_has_its_own_cache_file(self):
        site = chatterfang_site()
        with patched(site):
            edhtop16.entries(["Hazel of the Rootbloom"], "ONE_YEAR")
        keys = [kw["key"] for _, kw in site.calls]
        self.assertEqual(len(set(keys)), 2)
        self.assertTrue(keys[0].startswith("entries-hazel-of-the-rootbloom-"), keys[0])
        self.assertTrue(keys[1].startswith("entries_more-hazel-of-the-rootbloom-"), keys[1])

    def test_limit_stops_the_read_early(self):
        site = chatterfang_site()
        with patched(site):
            found, _, truncated = edhtop16._collect(["Hazel of the Rootbloom"], "ONE_YEAR", 2, None, None)
        self.assertEqual([e["id"] for e in found], ["E1", "E2"])
        self.assertEqual(len(site.calls), 1)
        self.assertTrue(truncated)  # three more entries were on that page and a second page follows

    def test_a_limit_the_data_does_not_reach_cuts_nothing(self):
        with patched(chatterfang_site()):
            found, _, truncated = edhtop16._collect(["Hazel of the Rootbloom"], "ONE_YEAR", 100, None, None)
        self.assertEqual(len(found), 6)
        self.assertFalse(truncated)

    def test_a_cursor_that_does_not_advance_cannot_loop_forever(self):
        # The follow-up page claims there is more, from the same cursor "5" the first page ended on
        stuck = fixture("edhtop16_entries_page2.json")
        stuck["data"]["node"]["entries"]["pageInfo"] = {"endCursor": "5", "hasNextPage": True}
        site = chatterfang_site(entries_more=lambda v: stuck)
        with patched(site):
            found = edhtop16.entries(["Hazel of the Rootbloom"], "ONE_YEAR")
        self.assertEqual(len(site.calls), 2)
        self.assertEqual([e["id"] for e in found], ["E1", "E2", "E3", "E4", "E5", "E6"])

    def test_a_cursor_with_no_commander_id_to_ask_by_ends_the_read(self):
        no_id = fixture("edhtop16_entries_page1.json")
        del no_id["data"]["commander"]["id"]
        site = chatterfang_site(entries=lambda v: no_id)
        with patched(site):
            found = edhtop16.entries(["Hazel of the Rootbloom"], "ONE_YEAR")
        self.assertEqual((len(found), len(site.calls)), (5, 1))

    def test_entries_carry_no_card_list_and_no_top_cut(self):
        with patched(chatterfang_site()):
            found = edhtop16.entries(["Hazel of the Rootbloom"], "ONE_YEAR")
        self.assertTrue(all(e["cards"] == [] and e["topcut"] is False for e in found))

    def test_unknown_commander_has_no_entries(self):
        fake = FakeFetch(fixture("edhtop16_entries_missing.json"))
        with patched(fake):
            self.assertEqual(edhtop16.entries(["No Such Commander"], "ONE_YEAR"), [])
        self.assertEqual(len(fake.calls), 1)

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
    REFUSAL = {"errors": ["Only persisted queries are allowed in production. Plain text queries are disabled."]}

    def failing_with(self, answer, call):
        """Run `call` against a fake net that answers `answer`, with a cache file standing in for the one net
        would have written. Returns (the FetchError, whether the cache file survived)."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cached.json")
            with open(path, "w") as f:
                f.write("{}")
            with patched(FakeFetch(answer)), mock.patch.object(net, "cache_file", return_value=path):
                with self.assertRaises(net.FetchError) as caught:
                    call()
            return caught.exception, os.path.exists(path)

    def test_a_graphql_error_is_raised_and_not_left_in_the_cache(self):
        # The API reports transient failures with HTTP 200; net would keep that answer for a day
        err, kept = self.failing_with({"errors": [{"message": "database timeout"}], "data": None},
                                      lambda: edhtop16.commander_stats(["Hazel of the Rootbloom"]))
        self.assertIn("database timeout", str(err))
        self.assertFalse(kept)

    def test_the_plain_text_refusal_is_an_error_not_an_empty_answer(self):
        # 2026-10-19: HTTP 200 and string errors. It used to read as "no such commander" and was cached.
        calls = {"stats": lambda: edhtop16.commander_stats(["Hazel of the Rootbloom"]),
                 "entries": lambda: edhtop16.entries(["Hazel of the Rootbloom"]),
                 "signals": lambda: edhtop16.signals(["Hazel of the Rootbloom"], 5),
                 "top commanders": lambda: edhtop16.top_commanders(150)}
        for label, call in calls.items():
            with self.subTest(call=label):
                err, kept = self.failing_with(self.REFUSAL, call)
                self.assertIn("Only persisted queries are allowed", str(err))
                self.assertEqual(err.source, "edhtop16")
                self.assertFalse(kept)

    def test_no_rows_is_not_an_error_it_means_unknown_commander(self):
        with patched(FakeFetch(fixture("edhtop16_entries_missing.json"))):
            self.assertIsNone(edhtop16.commander_stats(["No Such Commander"]))

    def test_network_failure_propagates(self):
        with patched(FakeFetch(net.FetchError("edhtop16", "u", "HTTP 503"))):
            with self.assertRaises(net.FetchError) as caught:
                edhtop16.entries(["Hazel of the Rootbloom"])
        self.assertEqual(caught.exception.reason, "HTTP 503")

    def test_offline_without_a_cached_answer_propagates_unchanged(self):
        offline = net.FetchError("edhtop16", "u", "offline (--offline) and not cached; run `warm` while online")
        with patched(FakeFetch(offline)):
            with self.assertRaises(net.FetchError) as caught:
                edhtop16.commander_stats(["Hazel of the Rootbloom"])
        self.assertIn("offline", caught.exception.reason)


class StaleQueryIdTests(unittest.TestCase):
    """What the site does with an id it no longer knows is HTTP 400 and the text "Unable to find persisted
    query: <id>". These go through the real net.fetch_json, with net.request standing in for the wire."""
    def run_against(self, wire_error):
        """(the FetchError commander_stats ends in, the files left in the cache) when net.request fails so."""
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(net, "request", side_effect=wire_error), mock.patch.object(net, "CACHE", tmp):
                with self.assertRaises(net.FetchError) as caught:
                    edhtop16.commander_stats(["Hazel of the Rootbloom"], refresh=False, offline=False)
            left = [name for _, _, names in os.walk(tmp) for name in names]
            return caught.exception, left

    def test_an_id_the_site_does_not_know_says_the_ids_need_refreshing(self):
        err, cached = self.run_against(net.FetchError("edhtop16", edhtop16.API, "HTTP 400"))
        self.assertEqual(type(err), net.FetchError)
        self.assertEqual(err.source, "edhtop16")
        self.assertIn("no longer recognizes its query id for page_CommanderStatsQuery", err.reason)
        self.assertIn("365ea6c7d469ca7dc4420af2a9ac0e94", err.reason)
        self.assertIn("PERSISTED", err.reason)
        self.assertIn("docstring", err.reason)
        self.assertEqual(cached, [])  # a rejection is never kept as if it were an answer

    def test_other_http_errors_keep_net_s_own_wording(self):
        for reason in ("HTTP 500", "HTTP 403", "network error: timed out"):
            with self.subTest(reason=reason):
                err, _ = self.run_against(net.FetchError("edhtop16", edhtop16.API, reason))
                self.assertEqual(err.reason, reason)

    def test_a_404_from_the_api_is_an_error_and_not_a_remembered_missing_page(self):
        # net would cache a 404 for a day and score.py would read the NotFound as "nothing to report"
        err, cached = self.run_against(net.NotFound("edhtop16", edhtop16.API, "no such page (HTTP 404)"))
        self.assertEqual(type(err), net.FetchError)
        self.assertNotIsInstance(err, net.NotFound)
        self.assertIn("moved", err.reason)
        self.assertEqual(cached, [])


class SignalsTests(unittest.TestCase):
    def signal(self, site=None, **kw):
        with patched(site or chatterfang_site()):
            return edhtop16.signals(["Chatterfang, Squirrel General"], 5, **kw)[0]

    def test_a_theme_gets_no_signal_and_no_request(self):
        fake = FakeFetch()
        with patched(fake):
            self.assertEqual(edhtop16.signals(["Hazel of the Rootbloom"], 3, "tokens"), [])
        self.assertEqual(fake.calls, [])

    def test_totals_and_n_cover_the_window(self):
        sig = self.signal()
        self.assertEqual(sig["n"], 6)
        self.assertEqual(sig["totals"], WINDOW_TOTALS)

    def test_a_card_counts_only_the_window_entries_that_ran_it(self):
        cards = self.signal()["cards"]
        stats = lambda *v: dict(zip(("entries", "games", "wins", "draws", "topcuts"), v))
        self.assertEqual(cards["Sol Ring"], WINDOW_TOTALS)       # every window deck; OLD1 is outside the window
        self.assertEqual(cards["Skullclamp"], stats(3, 12, 7, 2, 0))   # E1, E4, E6 (3-1-0, 2-1-1, 2-1-1); not OLD1/OLD2
        self.assertEqual(cards["Mana Crypt"], stats(1, 4, 2, 1, 0))    # E6 only: OLD1 is not in the window

    def test_a_staple_only_old_decks_ran_gets_no_record(self):
        # Demonic Tutor is a top-100 card, but the only deck that ran it is from before the window
        sig = self.signal()
        self.assertNotIn("Demonic Tutor", sig["cards"])
        self.assertEqual(sig["meta"]["cards_checked"], 4)

    def test_a_card_outside_the_staples_is_never_looked_up_and_has_no_record(self):
        # E1 ran Pitiless Plunderer, but it is not among the 100 most played cards, so it is never looked up
        # (score.gather marks such a card as not looked up; see test_score)
        site = chatterfang_site(card_entries=lambda v: card_page(["E1", "E2"]))
        sig = self.signal(site)
        self.assertEqual(set(sig["cards"]), {"Sol Ring", "Skullclamp", "Mana Crypt", "Demonic Tutor"})
        self.assertNotIn("Pitiless Plunderer", {v["cardName"] for v in site.asked("card_entries")})

    def test_the_staples_are_looked_up_one_by_one_in_most_played_order(self):
        site = chatterfang_site()
        self.signal(site)
        self.assertEqual([v["cardName"] for v in site.asked("card_entries")],
                         ["Sol Ring", "Skullclamp", "Mana Crypt", "Demonic Tutor"])
        name = "Chatterfang, Squirrel General"
        self.assertEqual(site.asked("card_entries")[0],
                         {"commander": name, "commanderName": name, "cardName": "Sol Ring", "count": 1000,
                          "cursor": None, "sortBy": "NEW"})
        self.assertEqual(site.asked("staples"), [{"commander": "Chatterfang, Squirrel General",
                                                  "staplesSortBy": "MOST_PLAYED"}])
        # 2 entry pages + staples + 4 cards + the site's own totals
        self.assertEqual(len(site.calls), 8)

    def test_a_card_in_over_a_thousand_decks_is_read_page_by_page(self):
        # the decks come newest first, as on the site: the window's six, then the older ones
        pages = {None: card_page(["E1", "E2", "E3"], cursor="3", more=True),
                 "3": card_page(["E4", "E5", "E6"], cursor="6", more=True),
                 "6": card_page(["OLD1", "OLD2"], cursor="8", more=False)}
        site = chatterfang_site(card_entries=lambda v: pages[v["cursor"]] if v["cardName"] == "Sol Ring"
                                else card_page([]))
        sig = self.signal(site)
        self.assertEqual(sig["cards"]["Sol Ring"], WINDOW_TOTALS)     # E1-E6 spread over two pages
        self.assertEqual([v["cursor"] for v in site.asked("card_entries")][:3], [None, "3", "6"])

    def test_paging_stops_once_a_page_ends_before_the_window(self):
        # Sol Ring's first page already ends on OLD1, a deck older than the window: every later page is older
        # still, so the 5,000 all-time decks behind it are never asked for
        pages = {None: card_page(["E1", "E2", "E3", "E4", "E5", "E6", "OLD1"], cursor="7", more=True)}
        site = chatterfang_site(card_entries=lambda v: pages[v["cursor"]] if v["cardName"] == "Sol Ring"
                                else card_page([]))
        sig = self.signal(site)
        self.assertEqual(sig["cards"]["Sol Ring"], WINDOW_TOTALS)
        self.assertEqual([v["cursor"] for v in site.asked("card_entries") if v["cardName"] == "Sol Ring"], [None])

    def test_the_signal_names_the_cards_it_looked_up(self):
        # score.gather reads meta["checked"] to tell "not looked up" from "no deck ran it"
        meta = self.signal()["meta"]
        self.assertEqual(meta["checked"], ["Sol Ring", "Skullclamp", "Mana Crypt", "Demonic Tutor"])
        self.assertEqual(meta["cards_checked"], 4)

    def test_a_card_cursor_that_does_not_advance_cannot_loop_forever(self):
        stuck = card_page(["E1"], cursor="1", more=True)
        site = chatterfang_site(card_entries=lambda v: stuck)
        sig = self.signal(site)
        self.assertEqual(sig["cards"]["Sol Ring"]["entries"], 1)
        self.assertEqual(len(site.asked("card_entries")), 8)  # two requests for each of the four cards

    def test_a_limit_shrinks_the_window_and_both_totals_and_cards_follow_it(self):
        # The newest two entries are E1 and E2; the staples are looked up as before but only count those two
        sig = self.signal(limit=2)
        self.assertEqual(sig["n"], 2)
        self.assertEqual(sig["totals"], {"entries": 2, "games": 8, "wins": 4, "draws": 1, "topcuts": 0})
        self.assertEqual(sig["cards"]["Sol Ring"], sig["totals"])
        self.assertEqual(sig["cards"]["Skullclamp"]["entries"], 1)   # E1 only
        self.assertNotIn("Mana Crypt", sig["cards"])                 # E6 is outside the two newest
        self.assertTrue(sig["meta"]["truncated"])

    def test_signal_carries_the_sites_own_totals_and_where_the_data_came_from(self):
        sig = self.signal()
        self.assertEqual(sig["fetched"], "2026-10-11T12:00:00Z")
        self.assertEqual(sig["cache"], "network")
        self.assertEqual(sig["url"], "https://edhtop16.com/commander/Chatterfang%2C%20Squirrel%20General")
        self.assertEqual(sig["meta"]["stats"], {"entries": 284, "topcuts": 68, "conversion": 0.2394,
                                                "win_rate": None})
        self.assertFalse(sig["meta"]["truncated"])
        self.assertEqual(sig["meta"]["time_period"], "ONE_YEAR")
        self.assertEqual((sig["source"], sig["kind"]), ("edhtop16", "tournament"))

    def test_cache_state_is_reported_as_stale_if_any_request_was_stale(self):
        site = chatterfang_site()
        site.cache = "stale"
        self.assertEqual(self.signal(site)["cache"], "stale")

    def test_the_period_is_asked_of_every_query_that_takes_one(self):
        site = chatterfang_site()
        self.signal(site, time_period="SIX_MONTHS")
        asked = site.asked("entries") + site.asked("entries_more") + site.asked("stats")
        self.assertEqual({v["timePeriod"] for v in asked}, {"SIX_MONTHS"})

    def test_unknown_commander_gets_no_signal_and_is_not_looked_up_further(self):
        site = chatterfang_site(entries=lambda v: fixture("edhtop16_entries_missing.json"))
        with patched(site):
            self.assertEqual(edhtop16.signals(["No Such Commander"], 5), [])
        self.assertEqual(len(site.calls), 1)

    def test_one_failed_card_lookup_fails_the_whole_read(self):
        # A card left out quietly would read as "no tournament play"; score.gather turns this into a warning
        def card(v):
            if v["cardName"] == "Mana Crypt":
                return net.FetchError("edhtop16", edhtop16.API, "HTTP 503")
            return card_page(["E1"])
        with patched(chatterfang_site(card_entries=card)):
            with self.assertRaises(net.FetchError):
                edhtop16.signals(["Chatterfang, Squirrel General"], 5)

    def test_commander_stats_asks_for_the_period(self):
        fake = FakeFetch(fixture("edhtop16_stats.json"))
        with patched(fake):
            stats = edhtop16.commander_stats(["Chatterfang, Squirrel General"], "SIX_MONTHS")
        self.assertEqual(stats, {"entries": 284, "topcuts": 68, "conversion": 0.2394, "win_rate": None})
        self.assertEqual(fake.variables(0), {"commander": "Chatterfang, Squirrel General", "minEventSize": 0,
                                             "timePeriod": "SIX_MONTHS"})


class TopCommandersTests(unittest.TestCase):
    def test_most_played_first(self):
        fake = FakeFetch(fixture("edhtop16_commanders.json"))
        with patched(fake):
            top = edhtop16.top_commanders(150)
        self.assertEqual([c["name"] for c in top],
                         ["Kinnan, Bonder Prodigy", "Sisay, Weatherlight Captain",
                          "Thrasios, Triton Hero / Tymna the Weaver"])
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.variables(0), {"count": 48, "cursor": None, "colorId": None, "minEntries": 150,
                                             "minSize": 0, "sortBy": "POPULARITY", "timePeriod": "ONE_YEAR"})
        self.assertEqual(fake.body(0)["extensions"], {"pastoria-id": "adb86c7711e577a33ffd053410380b2b"})

    def second_page(self):
        return {"data": {"commanders": {"pageInfo": {"hasNextPage": False, "endCursor": "4"}, "edges": [
            {"node": {"name": "Magda, Brazen Outlaw", "stats": {"count": 1850, "conversionRate": 0.2886}}}]}}}

    def test_the_rest_comes_from_the_second_query_by_cursor(self):
        # The first query ignores its cursor, so only the other one pages
        first = fixture("edhtop16_commanders.json")
        first["data"]["commanders"]["pageInfo"] = {"hasNextPage": True, "endCursor": "3"}
        site = FakeSite({"commanders": lambda v: first, "commanders_more": lambda v: self.second_page()})
        with patched(site):
            top = edhtop16.top_commanders(150)
        self.assertEqual(len(top), 4)
        self.assertEqual(site.asked("commanders")[0]["cursor"], None)
        self.assertEqual([v["cursor"] for v in site.asked("commanders_more")], ["3"])
        self.assertEqual(site.asked("commanders_more")[0]["minEntries"], 150)

    def test_a_cursor_that_does_not_advance_cannot_loop_forever(self):
        first = fixture("edhtop16_commanders.json")
        first["data"]["commanders"]["pageInfo"] = {"hasNextPage": True, "endCursor": "3"}
        stuck = self.second_page()
        stuck["data"]["commanders"]["pageInfo"] = {"hasNextPage": True, "endCursor": "3"}
        site = FakeSite({"commanders": lambda v: first, "commanders_more": lambda v: stuck})
        with patched(site):
            top = edhtop16.top_commanders(150)
        self.assertEqual(len(site.calls), 2)
        self.assertEqual(len(top), 4)


if __name__ == "__main__":
    unittest.main()
