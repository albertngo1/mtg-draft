"""Tests for cli.py: argument parsing for every command, exit codes, and each command's flow.

The engine (build.py), the providers, the card index and the network are all replaced by stand-ins, so these
tests check what cli.py itself does: which calls it makes with which arguments, what it puts in the result
(deck block, warnings, sources), what it writes with --out, and how it ends (exit code, stdout, stderr). The
report text itself is test_render.py's job; here a report is only checked for the lines that prove the right
result reached it. Deck lists are in fixtures/cli_*.txt; the card index is the small sample from test_carddb.py."""
import contextlib, datetime, gzip, io, json, os, shutil, sys, tempfile, unittest
from types import SimpleNamespace
from unittest import mock
from mtgcommander import carddb, cli, config, decklist, decks, fantasy, net, roles
from mtgcommander.providers import archidekt, edhrec, edhtop16, scryfall_tags, spellbook

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
REAL_ENGINE = cli._engine
# the loaders `stats` and `serve` call, taken before CliCase replaces them with stand-ins
REAL_ATTRIBUTES, REAL_ATTRIBUTES_LOADED = roles.attributes, roles.attributes_loaded
REAL_COMBOS_FOR = spellbook.combos_for
NOW = "2026-10-11T12:00:00Z"


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


def deck_path(name):
    return os.path.join(FIXTURES, name)


def sample_db():
    cards = {}
    with open(os.path.join(FIXTURES, "carddb_bulk_sample.jsonl"), encoding="utf-8") as f:
        for line in f:
            rec = carddb.card_record(json.loads(line))
            if rec and rec["name"] not in cards:
                cards[rec["name"]] = rec
    return carddb.CardDB(cards, fetched=NOW, cache="fresh")


def deck_text(name="cli_deck.txt"):
    with open(deck_path(name), encoding="utf-8") as f:
        return f.read()


TEST_ROLES = {"Sol Ring": {"ramp"}, "Arcane Signet": {"ramp"}, "Cultivate": {"ramp"}, "Skullclamp": {"draw"}}


class FakeEngine:
    """Stands in for build.py: records its arguments and answers with the render fixtures."""

    def __init__(self):
        self.calls = {}
        self.ctx = {"warnings": ["ctx: thin data warning"], "ci": "BG",
                    "sources": {"edhrec": {"fetched": "2026-10-11T09:12:44Z", "cache": "network", "age_days": 0.0}}}

    def prepare(self, *args, **kw):
        self.calls["prepare"] = (args, kw)
        return self.ctx

    def upgrade(self, ctx, deck, db, **kw):
        self.calls["upgrade"] = ((ctx, deck, db), kw)
        return fixture("render_upgrade.json")

    def build(self, ctx, db, **kw):
        self.calls["build"] = ((ctx, db), kw)
        return fixture("render_build.json")

    def suggest(self, spec, db, **kw):
        self.calls["suggest"] = ((spec, db), kw)
        return fixture("render_suggest.json")


class FakeMetrics:
    """Stands in for metrics.py: records its arguments and answers with the groups of the render fixture."""

    def __init__(self):
        self.calls = []

    def compute(self, ctx, db, cards, **kw):
        self.calls.append(((ctx, db, cards), kw))
        shown = fixture("render_stats.json")
        return {"schema": 1, "headline": shown["headline"], "groups": shown["groups"]}


class FakeServe:
    """Stands in for serve.py: records how `serve` and `stats --version` make the app and the server, and answers with
    canned results. `interrupt` is how the server stops (Ctrl-C); `bind_error` makes the port unavailable."""

    class Switches:
        pass

    def __init__(self):
        self.apps, self.servers, self.interrupt, self.bind_error, self.app_error = [], [], True, None, None
        self.stats = None                    # the exception stats_result raises, if any

    def App(self, db, root, **kw):
        if self.app_error:
            raise self.app_error
        app = SimpleNamespace(db=db, root=os.path.abspath(root), kw=kw, closed=False, asked=[])

        def stats_result(player, version_id):
            app.asked.append((player, version_id))
            if self.stats:
                raise self.stats
            shown = fixture("render_stats.json")
            return {"command": "stats", "deck": {"name": "Go wide", "commanders": ["Hazel of the Rootbloom"], "count": 100,
                                                 "ci": "BG"}, "bracket": 3, "spec": {"themes": ["tokens"], "playstyle": "value"},
                    "budget": 200, "spent": 185.43, "headline": shown["headline"], "groups": shown["groups"],
                    "warnings": ["serve warning"], "sources": {"edhrec": {"fetched": NOW, "cache": "fresh", "age_days": 0.1}}}

        def close(timeout=None):
            app.closed, app.waited = True, timeout
        app.stats_result, app.close = stats_result, close
        self.apps.append(app)
        return app

    def make_server(self, app, host, port):
        if self.bind_error:
            raise self.bind_error
        server = SimpleNamespace(app=app, host=host, requested=port, server_address=(host, port or 52000), served=False,
                                 closed=False, modes=[])

        def serve_forever():
            server.served = True
            server.modes.append(dict(net.MODE))            # what the run-wide mode is while the server runs
            if self.interrupt:
                raise KeyboardInterrupt

        def server_close():
            server.closed = True
        server.serve_forever, server.server_close = serve_forever, server_close
        self.servers.append(server)
        return server


class FakeComboIndex:
    """Stands in for spellbook.ComboIndex where only its size is read."""

    def __init__(self, combos):
        self.combos = combos

    def __len__(self):
        return self.combos


class CliCase(unittest.TestCase):
    """cli.run with every door closed: no network, no real card index, no claude, no cache writes."""

    def setUp(self):
        self.db = sample_db()
        self.engine = FakeEngine()
        self.validate = SimpleNamespace(run=mock.Mock(return_value={"bracket": 3, "method": "stub", "commanders": []}))
        self.metrics = FakeMetrics()
        self.serve = FakeServe()
        self.combos = {"included": [], "almost": [], "fetched": NOW, "cache": "network"}
        self.load = mock.patch.object(carddb, "load", return_value=self.db).start()
        mock.patch.object(cli, "_engine", side_effect=lambda name, command: {
            "build": self.engine, "validate": self.validate, "metrics": self.metrics, "serve": self.serve}[name]).start()
        self.prices = mock.patch.object(carddb, "deck_prices", side_effect=lambda names, db, **kw: {
            db.get(n)["name"]: 2.0 for n in names if db.get(n) is not None and "Basic" not in db.get(n)["types"]}).start()
        self.combos_call = mock.patch.object(spellbook, "find_combos", return_value=self.combos).start()
        self.combos_for = mock.patch.object(spellbook, "combos_for", return_value=dict(self.combos, via="index")).start()
        self.tag = mock.patch.object(roles, "tag", side_effect=lambda names, db, **kw: {
            n: set(TEST_ROLES.get(n, ())) for n in names}).start()
        self.attributes = mock.patch.object(roles, "attributes", side_effect=lambda names, db, **kw: {
            n: frozenset({"mana-rock"} if n == "Sol Ring" else ()) for n in names}).start()
        self.tags_loaded = True
        mock.patch.object(roles, "attributes_loaded", side_effect=lambda: self.tags_loaded).start()
        mock.patch.object(scryfall_tags, "INFO", {}).start()
        self.meta = mock.patch.object(edhrec, "commander_meta", return_value=None).start()
        mock.patch.object(decklist, "precon", side_effect=self.precon).start()
        mock.patch.object(fantasy, "_token", return_value=None).start()
        mock.patch.object(fantasy.shutil, "which", return_value=None).start()
        mock.patch.object(fantasy.subprocess, "run", side_effect=AssertionError("the real claude must never run")).start()
        for door in ("fetch_json", "request", "download"):          # a test that reaches the network is a bug
            mock.patch.object(net, door, side_effect=AssertionError(f"net.{door} must not be called in a test")).start()
        mock.patch.object(config, "PLAYER", None).start()           # MTG_COMMANDER_PLAYER in the shell must not leak in
        self.addCleanup(mock.patch.stopall)
        saved = dict(net.MODE)
        self.addCleanup(net.MODE.update, saved)
        del carddb.WARNINGS[:], roles.WARNINGS[:]

    def precon(self, name, **kw):
        if carddb.normalize(name) != "test precon":
            raise decklist.UnknownPrecon(name, ["Test Precon"])
        parsed = decklist.parse(deck_text())
        return {"name": "Test Precon", "code": "TST", "file": "TestPrecon_TST", "release": "2024-08-02",
                "commanders": parsed["commanders"], "cards": parsed["cards"], "fetched": NOW,
                "url": "https://mtgjson.com/api/v5/decks/TestPrecon_TST.json"}

    def run_cli(self, *argv, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if stdin is None:
                code = cli.run(list(argv))
            else:
                with mock.patch.object(sys, "stdin", io.StringIO(stdin)):
                    code = cli.run(list(argv))
        return SimpleNamespace(code=code, out=out.getvalue(), err=err.getvalue())

    def run_json(self, *argv, **kw):
        result = self.run_cli(*argv, "--json", **kw)
        self.assertEqual(result.code, 0, result.err)
        return json.loads(result.out)

    def tmp(self):
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: [os.remove(os.path.join(d, f)) for f in os.listdir(d)] or os.rmdir(d))
        return d


# ----------------------------------------------------------------------------- sources
class SessionTests(unittest.TestCase):
    def session(self):
        return cli.Session(cli.build_parser().parse_args(["themes"]))

    def test_a_source_keeps_its_oldest_fetch_and_its_worst_cache_state(self):
        s = self.session()
        s.add_source("edhrec", "2026-10-11T09:00:00Z", "network")
        s.add_source("edhrec", "2026-10-01T09:00:00Z", "fresh")
        s.add_source("edhrec", "2026-10-10T09:00:00Z", "stale")
        s.add_source("edhrec", "2026-10-09T09:00:00Z", "network")
        self.assertEqual((s.sources["edhrec"]["fetched"], s.sources["edhrec"]["cache"]), ("2026-10-01T09:00:00Z", "stale"))
        self.assertIsNotNone(s.sources["edhrec"]["age_days"])

    def test_nothing_is_recorded_for_a_source_with_no_date(self):
        s = self.session()
        s.add_source("edhrec", None)
        s.add_source("edhrec", "")
        self.assertEqual(s.sources, {})

    def test_a_source_that_does_not_say_where_it_came_from_is_judged_by_its_age(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        stamp = lambda age: (now - datetime.timedelta(seconds=age)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.assertEqual(cli._info(stamp(5))["cache"], "network")                      # a download from this run
        self.assertEqual(cli._info(stamp(3 * 86400))["cache"], "fresh")
        self.assertEqual(cli._info(stamp(30 * 86400))["cache"], "stale")                 # past EDHREC's 7 days
        self.assertEqual(cli._info(stamp(29 * 86400), source="mtgjson")["cache"], "fresh")   # MTGJSON keeps 30 days
        self.assertEqual(cli._info(stamp(30 * 86400), "fresh")["cache"], "fresh")       # a provider's own word wins
        self.assertEqual(cli._info("not a date")["age_days"], None)

    def test_warnings_are_not_repeated(self):
        s = self.session()
        s.warn("a")
        s.warn("a")
        s.warn("b")
        self.assertEqual(s.warnings, ["a", "b"])


# ----------------------------------------------------------------------------- parsing
class ParseTests(unittest.TestCase):
    def parse(self, *argv):
        return cli.build_parser().parse_args(list(argv))

    def test_themes(self):
        a = self.parse("themes", "--commander", "Hazel of the Rootbloom", "--partner", "X", "--json")
        self.assertEqual((a.command, a.commander, a.partner, a.json), ("themes", "Hazel of the Rootbloom", "X", True))

    def test_suggest(self):
        a = self.parse("suggest", "--theme", "tokens", "--theme", "squirrels", "--playstyle", "go-wide",
                       "--fantasy", "a squirrel army", "--bracket", "4", "--colors", "gb", "--budget", "$100",
                       "--owned", "a.txt", "--owned", "b.txt", "--owned-precon", "Squirreled Away", "--limit", "5",
                       "--no-keep-fun")
        self.assertEqual(a.theme, ["tokens", "squirrels"])
        self.assertEqual((a.playstyle, a.fantasy, a.bracket, a.colors), ("go-wide", "a squirrel army", 4, "BG"))
        self.assertEqual((a.budget, a.limit, a.keep_fun), (100.0, 5, False))
        self.assertEqual((a.owned, a.owned_precon), (["a.txt", "b.txt"], ["Squirreled Away"]))

    def test_build(self):
        a = self.parse("build", "Hazel of the Rootbloom", "--partner", "P", "--bracket", "2", "--budget", "50",
                       "--theme", "tokens", "--playstyle", "value", "--fantasy-weight", "0.8", "--include", "Sol Ring",
                       "--include", "Skullclamp", "--exclude", "Mana Crypt", "--keep-fun", "--allow-combos",
                       "--out", "deck.txt", "-v")
        self.assertEqual((a.commander, a.partner, a.bracket, a.budget), ("Hazel of the Rootbloom", "P", 2, 50.0))
        self.assertEqual((a.theme, a.playstyle, a.fantasy_weight), (["tokens"], "value", 0.8))
        self.assertEqual((a.include, a.exclude, a.keep_fun), (["Sol Ring", "Skullclamp"], ["Mana Crypt"], True))
        self.assertEqual((a.allow_combos, a.out, a.verbose), (True, "deck.txt", True))

    def test_upgrade_from_a_file_or_a_precon(self):
        a = self.parse("upgrade", "deck.txt", "--commander", "A", "--commander", "B", "--max-swaps", "7",
                       "--budget", "75.5", "--price-points", "25, $50.50,75", "--owned", "mine.txt")
        self.assertEqual((a.deckfile, a.precon, a.commander), ("deck.txt", None, ["A", "B"]))
        self.assertEqual((a.max_swaps, a.budget, a.price_points), (7, 75.5, [25.0, 50.5, 75.0]))
        a = self.parse("upgrade", "--precon", "Squirreled Away", "--theme", "tokens", "--playstyle", "aristocrats")
        self.assertEqual((a.deckfile, a.precon), (None, "Squirreled Away"))
        self.assertEqual((a.theme, a.playstyle), (["tokens"], "aristocrats"))
        # no swap limit and no named price points unless asked for: the engine picks the steps
        self.assertEqual((a.max_swaps, a.price_points, a.bracket, a.budget, a.keep_fun, a.out),
                         (None, None, None, None, None, None))

    def test_upgrade_reads_standard_input_with_a_dash(self):
        self.assertEqual(self.parse("upgrade", "-").deckfile, "-")

    def test_check(self):
        a = self.parse("check", "--precon", "Squirreled Away", "--bracket", "3")
        self.assertEqual((a.command, a.precon, a.bracket), ("check", "Squirreled Away", 3))

    def test_stats_takes_the_deck_and_the_flags_check_and_upgrade_take(self):
        a = self.parse("stats", "deck.txt", "--commander", "A", "--bracket", "4", "--theme", "tokens",
                       "--playstyle", "aristocrats", "--owned", "mine.txt", "--owned-precon", "Squirreled Away",
                       "--fantasy-weight", "0.8", "--no-keep-fun", "-v", "--json")
        self.assertEqual((a.command, a.deckfile, a.precon, a.commander, a.bracket), ("stats", "deck.txt", None, ["A"], 4))
        self.assertEqual((a.theme, a.playstyle, a.owned, a.owned_precon), (["tokens"], "aristocrats", ["mine.txt"],
                                                                         ["Squirreled Away"]))
        self.assertEqual((a.fantasy_weight, a.keep_fun, a.verbose, a.json), (0.8, False, True, True))
        a = self.parse("stats", "--precon", "Squirreled Away")
        self.assertEqual((a.deckfile, a.precon, a.verbose, a.bracket), (None, "Squirreled Away", False, None))

    def test_stats_takes_a_saved_version_instead_of_a_file_or_precon(self):
        a = self.parse("stats", "--version", "andy/squirrels-go-wide")
        self.assertEqual((a.version, a.deckfile, a.precon), ("andy/squirrels-go-wide", None, None))
        self.assertIsNone(self.parse("stats", "--precon", "Squirreled Away").version)

    def test_serve_listens_on_this_computer_only_unless_told_otherwise(self):
        a = self.parse("serve")
        self.assertEqual((a.command, a.host, a.port, a.decks), ("serve", "127.0.0.1", 8341, None))
        a = self.parse("serve", "--host", "100.101.102.103", "--port", "9000", "--decks", "mydecks", "--offline",
                       "--refresh")
        self.assertEqual((a.host, a.port, a.decks, a.offline, a.refresh), ("100.101.102.103", 9000, "mydecks", True, True))
        self.assertEqual(self.parse("serve", "--port", "0").port, 0)

    def test_serve_refuses_a_port_that_is_not_one(self):
        for port in ("x", "-1", "65536", "80.5"):
            with self.subTest(port=port):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    cli.build_parser().parse_args(["serve", "--port", port])

    def test_stats_does_not_take_the_flags_that_only_building_needs(self):
        for flag in ("--budget", "--include", "--exclude", "--allow-combos", "--out", "--max-swaps"):
            with self.subTest(flag=flag):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    cli.build_parser().parse_args(["stats", "-", flag, "x"])

    def test_warm(self):
        a = self.parse("warm", "Hazel of the Rootbloom", "--partner", "P", "--bracket", "5", "--theme", "tokens",
                       "--theme", "squirrels")
        self.assertEqual((a.commander, a.partner, a.bracket), ("Hazel of the Rootbloom", "P", 5))
        self.assertEqual(a.theme, ["tokens", "squirrels"])

    def test_validate(self):
        a = self.parse("validate", "--bracket", "3", "--commanders", "A", "B", "--commanders", "C", "--limit", "10",
                       "--sweep", "--calibrate")
        self.assertEqual((a.bracket, a.commanders), (3, [["A", "B"], ["C"]]))
        self.assertEqual((a.limit, a.sweep, a.calibrate), (10, True, True))
        a = self.parse("validate", "--bracket", "4")
        self.assertEqual((a.commanders, a.limit, a.sweep, a.calibrate), (None, 20, False, False))

    def test_the_four_global_flags_work_after_any_command(self):
        for argv in (["themes"], ["suggest", "--theme", "t"], ["build", "C"], ["upgrade", "-"], ["check", "-"],
                     ["stats", "-"], ["serve"], ["warm", "C"], ["validate", "--bracket", "3"]):
            with self.subTest(command=argv[0]):
                a = cli.build_parser().parse_args(argv + ["--json", "--refresh", "--offline", "--sources", "edhrec"])
                self.assertEqual((a.json, a.refresh, a.offline, a.sources), (True, True, True, ("edhrec",)))
                a = cli.build_parser().parse_args(argv)
                self.assertEqual((a.json, a.refresh, a.offline, a.sources), (False, False, False, config.SOURCES))

    def test_keep_fun_is_true_false_or_unset(self):
        self.assertIsNone(self.parse("build", "C").keep_fun)
        self.assertIs(self.parse("build", "C", "--keep-fun").keep_fun, True)
        self.assertIs(self.parse("build", "C", "--no-keep-fun").keep_fun, False)

    def test_sources_may_be_empty_to_turn_every_builder_source_off(self):
        self.assertEqual(self.parse("build", "C", "--sources", "").sources, ())

    def test_colors_and_money_are_cleaned_up(self):
        self.assertEqual(self.parse("suggest", "--colors", "g, b").colors, "BG")
        self.assertEqual(self.parse("build", "C", "--budget", "$1,250.50").budget, 1250.5)


class UsageErrorTests(CliCase):
    def test_a_usage_error_is_exit_one_not_argparses_two(self):
        for argv in (["frobnicate"], [], ["build"], ["build", "C", "--bracket", "9"], ["build", "C", "--bracket", "x"],
                     ["build", "C", "--nonsense"], ["validate"], ["suggest", "--colors", "xyz"],
                     ["build", "C", "--budget", "-5"], ["build", "C", "--budget", "lots"],
                     ["build", "C", "--budget", "nan"], ["build", "C", "--sources", "bing"],
                     ["upgrade", "-", "--max-swaps", "0"], ["suggest", "--limit", "x"],
                     ["upgrade", "-", "--budget", "50", "--price-points", "25,lots"],
                     ["upgrade", "-", "--budget", "50", "--price-points", "25,-5"],
                     ["upgrade", "-", "--budget", "50", "--price-points", ","]):
            with self.subTest(argv=argv):
                result = self.run_cli(*argv)
                self.assertEqual(result.code, 1, result.err)
                self.assertEqual(result.out, "")
                self.assertIn("error", result.err)

    def test_help_exits_zero_and_lists_the_commands(self):
        result = self.run_cli("--help")
        self.assertEqual(result.code, 0)
        for command in ("themes", "suggest", "build", "upgrade", "check", "stats", "serve", "warm", "validate"):
            self.assertIn(command, result.out)

    def test_a_subcommand_help_lists_its_flags(self):
        result = self.run_cli("upgrade", "--help")
        self.assertEqual(result.code, 0)
        for flag in ("--precon", "--budget", "--max-swaps", "--price-points", "--owned-precon", "--allow-combos",
                     "--out", "--json"):
            self.assertIn(flag, result.out)

    def test_main_exits_with_the_runs_code(self):
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as caught:
            cli.main(["themes"])
        self.assertEqual(caught.exception.code, 0)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            cli.main(["frobnicate"])
        self.assertEqual(caught.exception.code, 1)

    def test_no_arguments_reads_the_process_command_line(self):
        with mock.patch.object(sys, "argv", ["mtg-commander", "themes"]), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.run(), 0)
        self.assertIn("Playstyles", out.getvalue())


# ----------------------------------------------------------------------------- exit codes
class ExitCodeTests(CliCase):
    def test_an_unknown_commander_is_exit_one_with_close_matches(self):
        result = self.run_cli("build", "Hazl of the Rootbloom")
        self.assertEqual(result.code, 1)
        self.assertIn("unknown commander 'Hazl of the Rootbloom'; did you mean Hazel of the Rootbloom?", result.err)
        self.assertEqual(result.out, "")
        self.assertNotIn("prepare", self.engine.calls)

    def test_an_unknown_partner_is_reported_too(self):
        result = self.run_cli("build", "Hazel of the Rootbloom", "--partner", "Thrasios, Triton Her")
        self.assertEqual(result.code, 1)
        self.assertIn("did you mean Thrasios, Triton Hero?", result.err)

    def test_an_unknown_precon_is_exit_one_with_close_matches(self):
        for command in ("upgrade", "check"):
            with self.subTest(command=command):
                result = self.run_cli(command, "--precon", "Test Precn")
                self.assertEqual(result.code, 1)
                self.assertIn("unknown precon 'Test Precn'; closest: Test Precon", result.err)

    def test_an_unknown_owned_precon_is_exit_one(self):
        result = self.run_cli("build", "Hazel of the Rootbloom", "--owned-precon", "Nope")
        self.assertEqual(result.code, 1)
        self.assertIn("unknown precon 'Nope'", result.err)

    def test_an_unknown_card_in_a_deck_file_stops_an_upgrade(self):
        result = self.run_cli("upgrade", deck_path("cli_deck_typo.txt"))
        self.assertEqual(result.code, 1)
        self.assertIn("unknown card 'Sol Rign'; did you mean Sol Ring?", result.err)
        self.assertNotIn("prepare", self.engine.calls)

    def test_several_unknown_cards_are_listed_one_per_line(self):
        text = deck_text().replace("1 Sol Ring", "1 Sol Rign").replace("1 Skullclamp", "1 Skulclamp")
        result = self.run_cli("upgrade", "-", stdin=text)
        self.assertEqual(result.code, 1)
        self.assertIn("2 card names were not found:", result.err)
        self.assertIn("  Sol Rign   did you mean: Sol Ring", result.err)
        self.assertIn("  Skulclamp   did you mean: Skullclamp", result.err)

    def test_an_unknown_commander_named_in_the_file_is_reported_not_called_a_missing_commander(self):
        text = deck_text().replace("1 Hazel of the Rootbloom", "1 Hazl of the Rootbloom")
        result = self.run_cli("upgrade", "-", stdin=text)
        self.assertEqual(result.code, 1)
        self.assertIn("Hazl of the Rootbloom", result.err)
        self.assertNotIn("no commander found", result.err)

    def test_a_list_without_a_commander_says_how_to_name_one(self):
        text = "".join(line for line in deck_text().splitlines(True) if "Hazel" not in line and line != "Commander\n")
        result = self.run_cli("upgrade", "-", stdin=text)
        self.assertEqual(result.code, 1)
        self.assertIn("no commander found: mark it with a Commander section (or *CMDR*), or pass --commander NAME",
                      result.err)

    def test_a_deck_and_a_precon_together_or_neither_is_exit_one(self):
        for argv in (["upgrade"], ["check"], ["upgrade", deck_path("cli_deck.txt"), "--precon", "Test Precon"]):
            with self.subTest(argv=argv):
                result = self.run_cli(*argv)
                self.assertEqual(result.code, 1)
                self.assertIn("give a DECKFILE", result.err)

    def test_a_missing_deck_file_is_exit_one(self):
        result = self.run_cli("check", os.path.join(self.tmp(), "nope.txt"))
        self.assertEqual(result.code, 1)
        self.assertIn("cannot read", result.err)

    def test_data_that_cannot_be_had_is_exit_two_with_a_plain_message(self):
        self.load.side_effect = net.FetchError("scryfall", "https://api.scryfall.com/bulk-data",
                                               "offline (--offline) and no card index; run `warm` while online")
        result = self.run_cli("check", "--precon", "Test Precon")
        self.assertEqual(result.code, 2)
        self.assertEqual(result.out, "")
        self.assertIn("needed data is unavailable. scryfall: offline (--offline) and no card index", result.err)
        self.assertIn("warm COMMANDER", result.err)
        self.assertNotIn("Traceback", result.err)

    def test_a_precon_list_that_cannot_be_fetched_is_exit_two(self):
        with mock.patch.object(decklist, "precon", side_effect=net.FetchError("mtgjson", "u", "HTTP 500")):
            self.assertEqual(self.run_cli("upgrade", "--precon", "Test Precon").code, 2)

    def test_errors_never_put_anything_on_stdout_in_json_mode(self):
        result = self.run_cli("build", "Hazl", "--json")
        self.assertEqual((result.code, result.out), (1, ""))

    def test_a_command_whose_engine_file_is_missing_says_so(self):
        with mock.patch.object(cli, "_engine", REAL_ENGINE), mock.patch.dict(
                sys.modules, {"mtgcommander.validate": None, "mtgcommander.build": None}):
            validate = self.run_cli("validate", "--bracket", "3")
            upgrade = self.run_cli("upgrade", "--precon", "Test Precon")
        self.assertEqual(validate.code, 1)
        self.assertIn("validate is not implemented yet", validate.err)
        self.assertEqual(upgrade.code, 1)
        self.assertIn("upgrade is not implemented yet", upgrade.err)

    def test_an_engine_file_that_fails_on_its_own_import_is_not_called_missing(self):
        broken = ModuleNotFoundError("No module named 'nonsense'", name="nonsense")
        with mock.patch.object(cli, "_engine", REAL_ENGINE), mock.patch.object(
                cli.importlib, "import_module", side_effect=broken):
            with self.assertRaises(ModuleNotFoundError):
                cli._engine("build", "upgrade")

    def test_control_c_is_exit_130_without_a_traceback(self):
        self.load.side_effect = KeyboardInterrupt
        result = self.run_cli("check", "--precon", "Test Precon")
        self.assertEqual(result.code, 130)
        self.assertNotIn("Traceback", result.err)


# ----------------------------------------------------------------------------- the run-wide mode
class ModeTests(CliCase):
    def watch_mode(self):
        seen = {}
        self.load.side_effect = lambda *a, **k: seen.update(net.MODE) or self.db
        return seen

    def test_flags_set_the_mode_for_the_run_and_it_is_restored_after(self):
        seen = self.watch_mode()
        net.MODE.update(refresh=False, offline=False)
        self.assertEqual(self.run_cli("check", "--precon", "Test Precon", "--refresh", "--offline").code, 0)
        self.assertEqual((seen["refresh"], seen["offline"]), (True, True))
        self.assertEqual((net.MODE["refresh"], net.MODE["offline"]), (False, False))

    def test_a_run_without_the_flags_keeps_an_offline_mode_from_the_environment(self):
        seen = self.watch_mode()
        net.MODE.update(refresh=False, offline=True)       # what MTG_OFFLINE=1 sets at import
        self.assertEqual(self.run_cli("check", "--precon", "Test Precon").code, 0)
        self.assertTrue(seen["offline"])
        self.assertTrue(net.MODE["offline"])

    def test_the_mode_is_restored_after_an_error_too(self):
        net.MODE.update(refresh=False, offline=False)
        self.run_cli("build", "Hazl", "--offline")
        self.assertFalse(net.MODE["offline"])


# ----------------------------------------------------------------------------- check
class CheckTests(CliCase):
    def test_a_legal_precon_through_every_check(self):
        result = self.run_json("check", "--precon", "Test Precon")
        self.assertEqual(result["schema"], 1)
        self.assertEqual(result["command"], "check")
        self.assertEqual(result["deck"], {"name": "Test Precon", "commanders": ["Hazel of the Rootbloom"], "count": 100,
                                          "ci": "BG"})
        self.assertEqual(result["legality"], {"ok": True, "problems": []})
        self.assertEqual((result["bracket_check"]["bracket"], result["bracket_check"]["ok"]), (3, True))

    def test_a_bracket_flag_is_the_target(self):
        self.assertEqual(self.run_json("check", "--precon", "Test Precon", "--bracket", "2")["bracket_check"]["bracket"], 2)

    def test_the_combo_check_is_asked_about_the_whole_list_basics_counted_by_copy(self):
        self.run_json("check", "--precon", "Test Precon")
        commanders, names = self.combos_call.call_args[0]
        self.assertEqual(commanders, ["Hazel of the Rootbloom"])
        self.assertEqual(len(names), 99)
        self.assertEqual((names.count("Forest"), names.count("Swamp"), names.count("Sol Ring")), (40, 39, 1))

    def test_found_combos_reach_the_bracket_report(self):
        self.combos.update(included=[{"id": "1-2", "cards": ["Hazel of the Rootbloom", "Sol Ring"], "missing": [],
                                      "produces": ["Infinite mana"], "bracket_tag": "R", "min_bracket": 4,
                                      "two_card": True, "infinite": True, "url": "https://example.test/1-2/"}])
        report = self.run_json("check", "--precon", "Test Precon")["bracket_check"]
        self.assertFalse(report["ok"])
        self.assertEqual(report["two_card_combos"][0]["url"], "https://example.test/1-2/")

    def test_roles_are_counted_against_the_brackets_targets_with_a_status(self):
        roles_block = self.run_json("check", "--precon", "Test Precon")["roles"]
        self.assertEqual((roles_block["counts"]["ramp"], roles_block["counts"]["draw"]), (3, 1))
        self.assertEqual(roles_block["counts"]["land"], 82)          # 3 nonbasic lands and 79 basics
        bracket3 = roles.targets(3)["ramp"]          # whatever the shipped calibration says
        self.assertEqual(roles_block["targets"]["ramp"], bracket3)
        self.assertLess(roles_block["counts"]["ramp"], bracket3["min"])
        self.assertEqual((roles_block["status"]["ramp"], roles_block["status"]["land"]), ("low", "high"))
        self.assertEqual(roles_block["status"]["topend"], "ok")
        self.assertEqual(set(roles_block["status"]), set(roles_block["targets"]))

    def test_counterspell_targets_drop_to_zero_without_blue(self):
        targets = self.run_json("check", "--precon", "Test Precon")["roles"]["targets"]
        self.assertEqual((targets["counter"]["min"], targets["counter"]["target"]), (0, 0))

    def test_the_curve_counts_nonland_cards_by_mana_value(self):
        curve = self.run_json("check", "--precon", "Test Precon")["curve"]
        nonland = [self.db.get(n) for n in decklist.parse(deck_text())["cards"] and
                   [n for _, n in decklist.parse(deck_text())["cards"]] if not self.db.get(n)["land"]]
        self.assertEqual(sum(v for k, v in curve.items() if k != "avg"), len(nonland))
        self.assertEqual(curve["avg"], round(sum(r["cmc"] for r in nonland) / len(nonland), 2))
        self.assertEqual(list(curve), ["0", "1", "2", "3", "4", "5", "6", "7+", "avg"])
        self.assertEqual(curve["7+"], sum(1 for r in nonland if r["cmc"] >= 7))

    def test_an_unknown_card_is_a_legality_problem_and_the_check_goes_on(self):
        result = self.run_json("check", deck_path("cli_deck_typo.txt"))
        kinds = [p["kind"] for p in result["legality"]["problems"]]
        self.assertEqual(kinds, ["unknown"])                      # the typo still counts toward the 100
        problem = result["legality"]["problems"][0]
        self.assertEqual(problem["cards"], ["Sol Rign"])
        self.assertIn("did you mean Sol Ring?", problem["message"])
        self.assertFalse(result["legality"]["ok"])
        self.assertEqual(result["deck"]["name"], "cli_deck_typo.txt")
        self.assertEqual(result["roles"]["counts"]["ramp"], 2)    # Sol Ring is the one it could not read

    def test_illegal_lists_report_every_problem_and_still_analyze_the_legal_part(self):
        text = deck_text().replace("1 Sol Ring", "2 Sol Ring").replace("1 Cultivate", "1 Brainstorm")
        result = self.run_json("check", "-", stdin=text)
        kinds = [p["kind"] for p in result["legality"]["problems"]]
        self.assertEqual(kinds, ["count", "color", "duplicate"])
        self.assertEqual(result["deck"]["name"], "standard input")
        self.assertEqual(result["deck"]["count"], 101)
        self.assertGreater(result["curve"]["avg"], 0)

    def test_unreachable_combo_data_is_a_warning_not_a_failure(self):
        self.combos_call.side_effect = net.FetchError("spellbook", "https://backend.commanderspellbook.com", "HTTP 503")
        result = self.run_json("check", "--precon", "Test Precon")
        self.assertIn("Combos were not checked: spellbook is unavailable (HTTP 503).", result["warnings"])
        self.assertTrue(any("Combos were not checked" in n for n in result["bracket_check"]["notes"]))
        self.assertNotIn("spellbook", result["sources"])

    def test_the_commander_flag_overrides_an_unmarked_list(self):
        text = "".join(line for line in deck_text().splitlines(True) if "Hazel" not in line and line != "Commander\n")
        result = self.run_json("check", "-", "--commander", "Hazel of the Rootbloom", stdin=text)
        self.assertEqual(result["deck"]["commanders"], ["Hazel of the Rootbloom"])
        self.assertTrue(result["legality"]["ok"])

    def test_two_commanders_by_repeating_the_flag(self):
        text = "Deck\n" + "".join(f"1 {n}\n" for n in ("Sol Ring", "Command Tower")) + "96 Forest\n"
        result = self.run_json("check", "-", "--commander", "Thrasios, Triton Hero",
                               "--commander", "Pir, Imaginative Rascal", stdin=text)
        self.assertEqual(result["deck"]["commanders"], ["Thrasios, Triton Hero", "Pir, Imaginative Rascal"])
        self.assertEqual([p["kind"] for p in result["legality"]["problems"]], ["commander"])   # Pir wants Toothy

    def test_the_text_report_goes_to_stdout(self):
        result = self.run_cli("check", "--precon", "Test Precon")
        self.assertEqual(result.code, 0)
        self.assertIn("Test Precon: Hazel of the Rootbloom (BG), 100 cards; checked at Bracket 3", result.out)
        self.assertIn("Legality: ok", result.out)
        self.assertEqual(result.err, "")

    def test_sources_name_what_was_read_and_when(self):
        sources = self.run_json("check", "--precon", "Test Precon")["sources"]
        self.assertEqual(set(sources), {"scryfall", "mtgjson", "spellbook"})
        self.assertEqual(sources["scryfall"]["fetched"], NOW)
        self.assertEqual(sources["spellbook"]["cache"], "network")
        self.assertIn("age_days", sources["mtgjson"])

    def test_the_function_tag_data_is_a_source_when_it_was_read(self):
        scryfall_tags.INFO.update(fetched="2026-10-09T04:00:00Z", cache="fresh")
        self.assertEqual(self.run_json("check", "--precon", "Test Precon")["sources"]["scryfall_tags"]["cache"], "fresh")


# ----------------------------------------------------------------------------- stats
class StatsTests(CliCase):
    def stats(self, *argv):
        return self.run_json("stats", "--precon", "Test Precon", *argv)

    def test_a_precon_through_the_metrics_engine(self):
        result = self.stats()
        self.assertEqual((result["schema"], result["command"], result["bracket"]), (1, "stats", 3))
        self.assertEqual(result["deck"], {"name": "Test Precon", "commanders": ["Hazel of the Rootbloom"], "count": 100,
                                          "ci": "BG"})
        shown = fixture("render_stats.json")
        self.assertEqual((result["headline"], result["groups"]), (shown["headline"], shown["groups"]))
        self.assertEqual(result["spec"]["bracket"], 3)
        self.assertEqual(result["spec"]["playstyle"], "value")

    def test_the_engine_is_asked_for_the_same_context_upgrade_uses(self):
        self.stats("--bracket", "4", "--theme", "tokens", "--playstyle", "aristocrats")
        args, kw = self.engine.calls["prepare"]
        commanders, bracket, spec, db = args
        self.assertEqual((commanders, bracket), (["Hazel of the Rootbloom"], 4))
        self.assertEqual((spec["themes"], spec["playstyle"]), (["tokens"], "aristocrats"))
        names = [n for _, n in decklist.parse(deck_text())["cards"]]
        self.assertEqual(sorted(kw["deck_cards"]), sorted(set(names)))
        self.assertEqual(kw["sources"], config.SOURCES)
        self.assertEqual(kw["owned"], set())

    def test_the_metrics_get_the_deck_the_tags_the_combos_and_what_is_owned(self):
        self.stats("--owned-precon", "Test Precon")
        (ctx, db, cards), kw = self.metrics.calls[0]
        self.assertIs(ctx, self.engine.ctx)
        self.assertEqual(sum(n for n, _ in cards), 99)                       # the 99 cards, as (count, name) pairs
        self.assertEqual(kw["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(kw["attrs"]["Sol Ring"], frozenset({"mana-rock"}))
        self.assertEqual(kw["combos"]["via"], "index")
        self.assertIn("Sol Ring", kw["owned"])
        self.assertEqual(kw["prices"]["Sol Ring"], 2.0)                     # priced at the cheapest printing

    def test_every_card_and_the_commander_is_priced_at_its_cheapest_printing_like_upgrade_prices_them(self):
        # the helper `upgrade` and the deck pages use is asked for the whole list and the commander
        self.stats()
        names, db = self.prices.call_args[0]
        listed = {n for _, n in decklist.parse(deck_text())["cards"]}
        self.assertEqual((set(names), db), (listed | {"Hazel of the Rootbloom"}, self.db))
        self.assertEqual(self.metrics.calls[0][1]["prices"]["Skullclamp"], 2.0)

    def test_a_price_lookup_that_failed_is_a_warning_and_the_stats_go_on(self):
        # the helper never raises: the index prices stand in and the reason is a warning
        self.prices.side_effect = lambda names, db, **kw: carddb.WARNINGS.append("cheapest prices: scryfall: HTTP 503") or {}
        result = self.stats()
        self.assertIn("cheapest prices: scryfall: HTTP 503", result["warnings"])
        self.assertEqual(self.metrics.calls[0][1]["prices"], {})

    def test_the_attribute_tags_are_loaded_for_the_decks_cards(self):
        self.stats()
        names = self.attributes.call_args[0][0]
        self.assertEqual(sorted(set(names)), sorted(set(n for _, n in decklist.parse(deck_text())["cards"])))

    def test_without_the_attribute_tags_the_metrics_get_none_and_the_warning_the_load_left_comes_through(self):
        self.tags_loaded = False
        roles.WARNINGS.append("roles: Scryfall function tags for card attributes unavailable, so the removal, "
                              "mana, land and playstyle counts that need them are not shown (offline)")
        result = self.stats()
        self.assertIsNone(self.metrics.calls[0][1]["attrs"])
        self.assertTrue(any("attributes unavailable" in w for w in result["warnings"]))

    def test_the_combo_helper_is_asked_about_the_whole_list_with_the_commanders_colors(self):
        self.stats()
        commanders, names = self.combos_for.call_args[0]
        self.assertEqual(commanders, ["Hazel of the Rootbloom"])
        self.assertEqual((len(names), names.count("Forest"), names.count("Sol Ring")), (99, 40, 1))
        self.assertEqual(self.combos_for.call_args[1], {"identity": "BG"})
        self.combos_call.assert_not_called()                                 # the API is the helper's fallback

    def test_the_spellbook_source_is_dated_by_the_answer(self):
        self.combos_for.return_value = dict(self.combos, via="index", fetched="2026-10-10T23:00:00Z", cache="fresh")
        sources = self.stats()["sources"]
        self.assertEqual((sources["spellbook"]["fetched"], sources["spellbook"]["cache"]),
                         ("2026-10-10T23:00:00Z", "fresh"))

    def test_the_helpers_fallback_note_is_a_warning(self):
        self.combos_for.return_value = dict(self.combos, via="api", note="The combo file was not available (HTTP 503), "
                                                                       "so Commander Spellbook's API answered.")
        self.assertIn("The combo file was not available (HTTP 503), so Commander Spellbook's API answered.",
                      self.stats()["warnings"])

    def test_combos_that_cannot_be_had_are_a_warning_and_the_metrics_go_on_without_them(self):
        self.combos_for.side_effect = net.FetchError("spellbook", "https://example.test", "HTTP 503")
        result = self.stats()
        self.assertIsNone(self.metrics.calls[0][1]["combos"])
        self.assertIn("Combos were not checked: spellbook is unavailable (HTTP 503).", result["warnings"])
        self.assertNotIn("spellbook", result["sources"])

    def test_the_context_warnings_and_sources_join_the_result(self):
        result = self.stats()
        self.assertIn("ctx: thin data warning", result["warnings"])
        self.assertEqual(result["sources"]["edhrec"]["cache"], "network")
        self.assertEqual(set(result["sources"]) - {"edhrec"}, {"scryfall", "mtgjson", "spellbook"})

    def test_the_function_tag_data_is_a_source_when_it_was_read(self):
        scryfall_tags.INFO.update(fetched="2026-10-09T04:00:00Z", cache="fresh")
        self.assertEqual(self.stats()["sources"]["scryfall_tags"]["cache"], "fresh")

    def test_a_deck_file_with_an_unknown_card_stops_the_run_as_upgrade_does_and_a_precon_only_warns(self):
        result = self.run_cli("stats", deck_path("cli_deck_typo.txt"))
        self.assertEqual(result.code, 1)
        self.assertIn("Sol Rign", result.err)
        self.assertEqual(self.metrics.calls, [])

    def test_a_deck_with_no_commander_is_exit_one_with_the_way_to_fix_it(self):
        text = "".join(line for line in deck_text().splitlines(True) if "Hazel" not in line and line != "Commander\n")
        result = self.run_cli("stats", "-", stdin=text)
        self.assertEqual(result.code, 1)
        self.assertIn("no commander found", result.err)

    def test_a_deck_file_and_the_commander_flag(self):
        text = "".join(line for line in deck_text().splitlines(True) if "Hazel" not in line and line != "Commander\n")
        result = self.run_json("stats", "-", "--commander", "Hazel of the Rootbloom", stdin=text)
        self.assertEqual(result["deck"]["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(result["deck"]["name"], "standard input")

    def test_a_precon_and_a_file_together_are_exit_one(self):
        self.assertEqual(self.run_cli("stats", deck_path("cli_deck.txt"), "--precon", "Test Precon").code, 1)
        result = self.run_cli("stats")
        self.assertEqual(result.code, 1)
        self.assertIn("--version PLAYER/ID, one of the three", result.err)

    def test_an_unknown_precon_is_exit_one_with_close_names(self):
        result = self.run_cli("stats", "--precon", "Test Precom")
        self.assertEqual(result.code, 1)
        self.assertIn("Test Precon", result.err)

    def test_data_the_engine_cannot_do_without_is_exit_two(self):
        self.engine.prepare = mock.Mock(side_effect=net.FetchError("edhrec", "u", "offline and not cached"))
        result = self.run_cli("stats", "--precon", "Test Precon")
        self.assertEqual(result.code, 2)
        self.assertEqual(self.metrics.calls, [])
        self.assertIn("warm COMMANDER", result.err)

    def test_the_text_report_goes_to_stdout_and_json_is_alone_on_stdout(self):
        text = self.run_cli("stats", "--precon", "Test Precon")
        self.assertEqual(text.code, 0)
        self.assertIn("Test Precon → Bracket 3, no budget", text.out)
        self.assertIn("Score 93.77, Bracket 3 within its limits, 36 lands, removal power 5.95, cost to buy $185.43", text.out)
        self.assertNotIn("cards:", text.out)
        self.assertEqual(text.err, "")
        as_json = self.run_cli("stats", "--precon", "Test Precon", "--json")
        self.assertEqual(json.loads(as_json.out)["command"], "stats")
        self.assertEqual(as_json.err, "")

    def test_the_verbose_flag_reaches_the_report(self):
        text = self.run_cli("stats", "--precon", "Test Precon", "-v").out
        self.assertIn("cards: Tear Asunder, Assassin's Trophy", " ".join(text.split()))

    def test_the_run_wide_modes_are_in_force_while_the_combos_are_asked_for_and_restored_after(self):
        before, seen = dict(net.MODE), []
        self.combos_for.side_effect = lambda *a, **k: seen.append((net.MODE["offline"], net.MODE["refresh"])) or \
            dict(self.combos, via="index")
        self.run_json("stats", "--precon", "Test Precon", "--offline", "--refresh")
        self.assertEqual(seen, [(True, True)])
        self.assertEqual(net.MODE, before)


# ----------------------------------------------------------------------------- stats --version
class StatsVersionTests(CliCase):
    def stats(self, *argv):
        return self.run_cli("stats", "--version", "andy/go-wide", *argv)

    def test_a_saved_version_is_worked_out_by_the_servers_code_and_printed_as_a_stats_report(self):
        # `stats --version andy/go-wide`: the app is made on the decks folder, asked for the version, and the report
        # shows each number beside the base deck's
        result = self.stats()
        self.assertEqual(result.code, 0, result.err)
        app = self.serve.apps[0]
        self.assertEqual((app.root, app.asked), (os.path.abspath(config.DECKS), [("andy", "go-wide")]))
        self.assertIsNone(app.kw["web"])                                     # no pages: this is not a server
        self.assertEqual(app.kw["offline"], False)
        self.assertEqual(app.kw["sources"], config.SOURCES)
        self.assertIn("Go wide → Bracket 3, budget $200 (spent $185.43); themes: tokens; playstyle: value", result.out)
        self.assertIn("Score 93.77, Bracket 3 within its limits, 36 lands, removal power 5.95, cost to buy $185.43",
                      result.out)
        self.assertIn("(was ", result.out)
        self.assertIn("serve warning", result.out)
        self.assertEqual(self.metrics.calls, [])                             # it did not use the file path

    def test_json_carries_the_same_result(self):
        # --json: the groups with their base values, and the sources the app reported
        result = json.loads(self.stats("--json").out)
        self.assertEqual((result["schema"], result["command"], result["spent"]), (1, "stats", 185.43))
        self.assertTrue(any("base" in item for g in result["groups"] for item in g["items"]))
        self.assertEqual(result["sources"]["edhrec"]["cache"], "fresh")
        self.assertIn("serve warning", result["warnings"])
        self.assertIn("scryfall", result["sources"])                         # the card index is a source of every run

    def test_the_decks_folder_is_the_one_the_environment_names(self):
        # MTG_COMMANDER_DECKS decides config.DECKS, so a version in a temporary folder can be read
        with mock.patch.object(config, "DECKS", "/tmp/somewhere/decks"):
            self.stats()
        self.assertEqual(self.serve.apps[0].root, "/tmp/somewhere/decks")

    def test_offline_and_the_source_choice_reach_the_app(self):
        self.stats("--offline", "--sources", "edhrec")
        self.assertEqual((self.serve.apps[0].kw["offline"], self.serve.apps[0].kw["sources"]), (True, ("edhrec",)))

    def test_the_version_holds_its_own_settings_so_flags_that_set_them_are_exit_one(self):
        # the bracket, themes, playstyle, owned cards, a file or a precon all come from the version
        for flags in (["--bracket", "4"], ["--theme", "tokens"], ["--playstyle", "go-wide"], ["--owned-precon", "X"],
                      ["--owned", "mine.txt"], ["--fantasy", "squirrels"], ["--no-keep-fun"], ["--fantasy-weight", "0.8"],
                      ["--commander", "Hazel of the Rootbloom"]):
            with self.subTest(flags=flags):
                result = self.stats(*flags)
                self.assertEqual(result.code, 1)
                self.assertIn("so it cannot be combined with", result.err)
        for flags in (["--precon", "Test Precon"], ["deck.txt"]):          # a second deck is the "one of the three" mistake
            with self.subTest(flags=flags):
                result = self.stats(*flags)
                self.assertEqual(result.code, 1)
                self.assertIn("one of the three", result.err)
        self.assertEqual(self.serve.apps, [])

    def test_a_version_that_is_not_player_slash_id_is_exit_one(self):
        for text in ("go-wide", "/go-wide", "andy/", ""):
            with self.subTest(text=text):
                result = self.run_cli("stats", "--version", text)
                self.assertEqual(result.code, 1)
        self.assertIn("PLAYER/ID, for example andy/squirrels-go-wide", self.run_cli("stats", "--version", "x").err)

    def test_a_version_that_does_not_exist_is_exit_one_with_the_reason(self):
        self.serve.stats = decks.NotFound('andy has no version with the id "go-wide".')
        result = self.stats()
        self.assertEqual((result.code, result.out), (1, ""))
        self.assertIn('andy has no version with the id "go-wide".', result.err)

    def test_a_deck_file_that_cannot_be_read_is_exit_one_naming_it(self):
        self.serve.stats = ValueError("/decks/andy/go-wide.json could not be read: Expecting value")
        result = self.stats()
        self.assertEqual(result.code, 1)
        self.assertIn("/decks/andy/go-wide.json could not be read", result.err)

    def test_data_the_version_cannot_do_without_is_exit_two(self):
        self.serve.stats = net.FetchError("edhrec", "u", "offline and not cached")
        result = self.stats()
        self.assertEqual(result.code, 2)
        self.assertIn("warm COMMANDER", result.err)


# ----------------------------------------------------------------------------- what a player owns
# Three precons andy might own, each holding Sol Ring (most precons do), for naming the box a free card comes from
BOXES = {"peace offering": ("Peace Offering", ["Chatterfang, Squirrel General"], [(1, "Sol Ring"), (1, "Skullclamp")]),
         "family matters": ("Family Matters", ["Pir, Imaginative Rascal"], [(1, "Sol Ring"), (1, "Arcane Signet")]),
         "animated army": ("Animated Army", ["Thrasios, Triton Hero"], [(1, "Sol Ring")])}
SMALL_DECK = "Commander\n1 Hazel of the Rootbloom\nDeck\n1 Cultivate\n1 Mind Stone\n10 Forest\n"


class OwnedCase(CliCase):
    """A temporary decks folder (config.DECKS) for collection files, and a precon lookup that also knows BOXES."""

    def setUp(self):
        super().setUp()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        mock.patch.object(config, "DECKS", self.root).start()
        mock.patch.object(decklist, "precon", side_effect=self.box).start()
        self.deck = self.file("small.txt", SMALL_DECK)

    def box(self, name, **kw):
        found = BOXES.get(carddb.normalize(name))
        if found is None:
            return self.precon(name, **kw)
        title, commanders, cards = found
        return {"name": title, "code": "BOX", "file": title.replace(" ", ""), "release": "2025-01-01",
                "commanders": commanders, "cards": cards, "fetched": NOW, "url": "https://mtgjson.test/" + title}

    def file(self, name, text):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def owned(self):
        return self.engine.calls["prepare"][1]["owned"]

    def swaps(self, *swaps):
        """Make the engine's upgrade answer with these swaps (add, owned), each from a Forest."""
        result = fixture("render_upgrade.json")
        result["swaps"] = [dict(result["swaps"][0], rank=i, cut="Forest", add=add, owned=owned, price=1.0)
                           for i, (add, owned) in enumerate(swaps, 1)]
        self.engine.upgrade = lambda *a, **k: result


class PlayerTests(OwnedCase):
    def test_a_player_named_on_the_command_line_must_have_a_collection_file(self):
        # --player andy with no andy/collection.json: exit 1, naming the file it looked for, before any scoring
        result = self.run_cli("upgrade", self.deck, "--player", "andy")
        self.assertEqual((result.code, result.out), (1, ""))
        self.assertIn(f"andy has no collection file: there is no {os.path.join(self.root, 'andy', 'collection.json')}",
                      result.err)
        self.assertNotIn("prepare", self.engine.calls)

    def test_the_player_from_the_environment_without_a_file_is_a_warning_and_the_run_goes_on(self):
        # MTG_COMMANDER_PLAYER=andy is a standing default, so a missing file is not a stop
        with mock.patch.object(config, "PLAYER", "andy"):
            result = self.run_json("upgrade", self.deck)
        self.assertTrue(any(w.startswith("MTG_COMMANDER_PLAYER is andy, but there is no collection file at "
                                         + os.path.join(self.root, "andy", "collection.json")) for w in result["warnings"]),
                        result["warnings"])
        self.assertEqual(self.owned(), set())

    def test_the_collections_precons_and_loose_cards_count_as_owned(self):
        # andy owns Peace Offering and one loose Brainstorm: their cards cost $0, whether --player or the environment
        decks.save_collection(self.root, "andy", precons=["Peace Offering"], cards=[[1, "Brainstorm"]])
        self.assertEqual(self.run_cli("upgrade", self.deck, "--player", "Andy").code, 0)      # typed as the pages do
        self.assertEqual(self.owned(), {"Sol Ring", "Skullclamp", "Chatterfang, Squirrel General", "Brainstorm"})
        with mock.patch.object(config, "PLAYER", "andy"):
            self.assertEqual(self.run_cli("stats", self.deck).code, 0)
        self.assertEqual(self.metrics.calls[-1][1]["owned"],
                         {"Sol Ring", "Skullclamp", "Chatterfang, Squirrel General", "Brainstorm"})

    def test_a_precon_in_the_collection_that_cannot_be_found_names_the_file_to_fix(self):
        # a hand edit misspelled a precon: exit 1, as --owned-precon would, but pointing at the collection file
        decks.save_collection(self.root, "andy", precons=["Peace Ofering Typo Box"])
        result = self.run_cli("upgrade", self.deck, "--player", "andy")
        self.assertEqual(result.code, 1)
        self.assertIn(f"andy's collection ({os.path.join(self.root, 'andy', 'collection.json')}) lists a precon that "
                      "cannot be found: unknown precon 'Peace Ofering Typo Box'", result.err)

    def test_a_damaged_collection_is_exit_one_naming_the_file(self):
        os.makedirs(os.path.join(self.root, "andy"))
        self.file(os.path.join("andy", "collection.json"), "{ not json")
        result = self.run_cli("build", "Hazel of the Rootbloom", "--player", "andy")
        self.assertEqual(result.code, 1)
        self.assertIn("collection.json could not be read", result.err)

    def test_an_owned_file_may_be_a_collection_whose_precons_are_opened(self):
        # --owned andy's collection file: Family Matters' cards and the loose Brainstorm
        path = self.file("mine.json", json.dumps({"schema": 1, "kind": "collection", "precons": ["Family Matters"],
                                                  "cards": [[1, "Brainstorm"]]}))
        self.assertEqual(self.run_cli("upgrade", self.deck, "--owned", path).code, 0)
        self.assertEqual(self.owned(), {"Sol Ring", "Arcane Signet", "Pir, Imaginative Rascal", "Brainstorm"})

    def test_a_saved_version_refuses_the_player_flag(self):
        # stats --version takes the player's collection from the version's own player, so --player is refused
        result = self.run_cli("stats", "--version", "andy/go-wide", "--player", "albert")
        self.assertEqual(result.code, 1)
        self.assertIn("cannot be combined with --player", result.err)


class OwnedFromTests(OwnedCase):
    def test_upgrade_json_names_the_box_of_each_free_card_and_every_swap_has_the_key(self):
        # Sol Ring is free because andy owns Peace Offering; Brainstorm is a loose card (owned, from no box); Demonic
        # Tutor is bought
        decks.save_collection(self.root, "andy", precons=["Peace Offering"], cards=[[1, "Brainstorm"]])
        self.swaps(("Sol Ring", True), ("Brainstorm", True), ("Demonic Tutor", False))
        result = self.run_json("upgrade", self.deck, "--player", "andy")
        self.assertEqual([(s["add"], s["owned_from"]) for s in result["swaps"]],
                         [("Sol Ring", ["Peace Offering"]), ("Brainstorm", []), ("Demonic Tutor", [])])

    def test_the_report_says_which_box_one_two_or_many(self):
        # Sol Ring is in all three boxes, Skullclamp in Peace Offering alone, Arcane Signet in Family Matters alone
        self.swaps(("Sol Ring", True), ("Skullclamp", True), ("Arcane Signet", True))
        out = self.run_cli("upgrade", self.deck, "--owned-precon", "Peace Offering").out
        self.assertIn("ADD Sol Ring   +0.42  $0.00  (owned, from Peace Offering)", out)
        out = self.run_cli("upgrade", self.deck, "--owned-precon", "Peace Offering", "--owned-precon",
                           "Family Matters").out
        self.assertIn("ADD Sol Ring   +0.42  $0.00  (owned, from Family Matters or Peace Offering)", out)
        self.assertIn("ADD Skullclamp   +0.42  $0.00  (owned, from Peace Offering)", out)
        decks.save_collection(self.root, "andy", precons=["Peace Offering", "Family Matters", "Animated Army"])
        out = self.run_cli("upgrade", self.deck, "--player", "andy").out
        self.assertIn("ADD Sol Ring   +0.42  $0.00  (owned, from Animated Army, Family Matters or 1 more)", out)

    def test_the_decks_own_cards_come_from_no_box(self):
        # Mind Stone is in the deck being upgraded and in a box andy owns: it is the deck's, not the box's
        BOXES["mind box"] = ("Mind Box", ["Hazel of the Rootbloom"], [(1, "Mind Stone")])
        self.addCleanup(BOXES.pop, "mind box")
        self.swaps(("Mind Stone", True))
        result = self.run_json("upgrade", self.deck, "--owned-precon", "Mind Box")
        self.assertEqual(result["swaps"][0]["owned_from"], [])

    def test_build_names_the_box_of_each_owned_card(self):
        # the build fixture owns Sol Ring: with Peace Offering it is from that box, and every card has the key
        result = self.run_json("build", "Hazel of the Rootbloom", "--owned-precon", "Peace Offering")
        sol = next(c for c in result["cards"] if c["name"] == "Sol Ring")
        self.assertEqual(sol["owned_from"], ["Peace Offering"])
        self.assertTrue(all("owned_from" in c for c in result["cards"]))
        self.assertEqual({tuple(c["owned_from"]) for c in result["cards"] if c["name"] != "Sol Ring"}, {()})
        text = self.run_cli("build", "Hazel of the Rootbloom", "--owned-precon", "Peace Offering").out
        self.assertEqual(" ".join(next(line for line in text.splitlines() if line.startswith("  Sol Ring")).split()),
                         "Sol Ring 0.86 $0.00 owned, from Peace Offering; ramp")


class CollectionCommandTests(OwnedCase):
    def collection(self, *argv):
        return self.run_cli("collection", *argv)

    def stored(self, player="andy"):
        return decks.collection(self.root, player)

    def test_adding_a_precon_makes_the_file_and_stores_the_name_mtgjson_gives_it(self):
        # 'peace offering' typed in lower case is stored as Peace Offering, and the report lists it with its commander
        result = self.collection("--player", "andy", "--add-precon", "peace offering")
        self.assertEqual(result.code, 0, result.err)
        self.assertEqual(self.stored()["precons"], ["Peace Offering"])
        self.assertIn(f"andy's collection, in:\n  {os.path.join(self.root, 'andy', 'collection.json')}", result.out)
        self.assertIn("Made a new collection file for andy.", result.out)
        self.assertIn("Added Peace Offering.", result.out)
        self.assertIn("Peace Offering  (Chatterfang, Squirrel General)", result.out)
        self.assertIn("Loose cards: 0", result.out)

    def test_adding_one_already_there_changes_nothing_and_says_so(self):
        decks.save_collection(self.root, "andy", precons=["Peace Offering"], now="2026-10-19T12:00:00Z")
        result = self.collection("--player", "andy", "--add-precon", "Peace Offering", "--json")
        self.assertEqual(result.code, 0, result.err)
        answer = json.loads(result.out)
        self.assertEqual(answer["notes"], ["Peace Offering is already in the collection; nothing changed."])
        self.assertEqual(self.stored()["updated"], "2026-10-19T12:00:00Z")          # not written again

    def test_removing_matches_a_stored_name_ignoring_case_and_an_unknown_one_lists_what_is_stored(self):
        decks.save_collection(self.root, "andy", precons=["Peace Offering", "Family Matters"], cards=[[1, "Sol Ring"]])
        result = self.collection("--player", "andy", "--remove-precon", "FAMILY MATTERS")
        self.assertEqual(result.code, 0, result.err)
        self.assertIn("Removed Family Matters.", result.out)
        self.assertEqual((self.stored()["precons"], self.stored()["cards"]), (["Peace Offering"], [[1, "Sol Ring"]]))
        result = self.collection("--player", "andy", "--add-precon", "Family Matters", "--remove-precon", "Nope")
        self.assertEqual(result.code, 1)
        self.assertIn("andy's collection has no precon called 'Nope'. It holds: Peace Offering; Family Matters.",
                      result.err)
        self.assertEqual(self.stored()["precons"], ["Peace Offering"])                # nothing written

    def test_json_lists_each_precon_with_its_commanders_and_the_loose_cards(self):
        # Animated Army was just looked up; a precon whose list is not cached shows no commanders (None)
        decks.save_collection(self.root, "andy", precons=["Unlisted Box"], cards=[[1, "Sol Ring"], [2, "Forest"]])
        answer = json.loads(self.collection("--player", "andy", "--add-precon", "Animated Army", "--json").out)
        self.assertEqual((answer["command"], answer["player"], answer["path"]),
                         ("collection", "andy", os.path.join(self.root, "andy", "collection.json")))
        self.assertEqual(answer["precons"], [{"name": "Unlisted Box", "commanders": None},
                                             {"name": "Animated Army", "commanders": ["Thrasios, Triton Hero"]}])
        self.assertEqual((answer["cards"], answer["card_count"]), ([[1, "Sol Ring"], [2, "Forest"]], 3))
        self.assertEqual(answer["notes"], ["Added Animated Army."])
        self.assertTrue(answer["updated"])

    def test_the_player_comes_from_the_environment_and_without_one_is_exit_one(self):
        with mock.patch.object(config, "PLAYER", "albert"):
            self.assertEqual(self.collection("--add-precon", "Family Matters").code, 0)
        self.assertEqual(self.stored("albert")["precons"], ["Family Matters"])
        result = self.collection()
        self.assertEqual(result.code, 1)
        self.assertIn("--player NAME, or set MTG_COMMANDER_PLAYER", result.err)

    def test_an_unknown_precon_to_add_is_exit_one_with_close_names(self):
        result = self.collection("--player", "andy", "--add-precon", "Nope")
        self.assertEqual(result.code, 1)
        self.assertIn("unknown precon 'Nope'", result.err)
        self.assertFalse(os.path.exists(os.path.join(self.root, "andy", "collection.json")))


class JsonDeckfileTests(OwnedCase):
    def test_a_json_deck_file_is_checked_like_a_text_one(self):
        path = self.file("deck.json", json.dumps({"commanders": ["Hazel of the Rootbloom"],
                                                  "cards": [[1, "Sol Ring"], {"name": "Forest", "count": 98}]}))
        result = self.run_json("check", path)
        self.assertEqual(result["deck"], {"name": "deck.json", "commanders": ["Hazel of the Rootbloom"], "count": 100,
                                          "ci": "BG"})

    def test_a_saved_version_file_is_its_base_deck_with_its_changes(self):
        # andy's version cut one Forest for Cultivate; the base deck is found two folders up from the file
        decks.new_base(self.root, name="Small", commanders=["Hazel of the Rootbloom"],
                       cards=[(1, "Sol Ring"), (98, "Forest")], source={"type": "paste"}, created_by="andy", db=self.db)
        decks.new_version(self.root, player="andy", name="Go wide", base_id="small", settings={})
        decks.apply(self.root, "andy", "go-wide", {"op": "swap", "cut": "Forest", "add": "Cultivate"}, revision=0,
                    db=self.db)
        self.run_json("upgrade", os.path.join(self.root, "andy", "go-wide.json"))
        deck = self.engine.calls["upgrade"][0][1]
        self.assertEqual(deck["cards"], [(1, "Sol Ring"), (97, "Forest"), (1, "Cultivate")])

    def test_a_version_whose_base_deck_is_gone_is_exit_one_naming_it(self):
        path = self.file("go-wide.json", json.dumps({"schema": 1, "kind": "version", "base": "small", "changes": []}))
        result = self.run_cli("check", path)
        self.assertEqual(result.code, 1)
        self.assertIn('saved version of the base deck "small"', result.err)

    def test_a_collection_is_not_a_deck(self):
        path = self.file("mine.json", json.dumps({"schema": 1, "kind": "collection", "precons": []}))
        result = self.run_cli("stats", path)
        self.assertEqual(result.code, 1)
        self.assertIn("a collection is not a deck", result.err)
        self.assertIn("give it to --owned instead", result.err)

    def test_malformed_json_is_exit_one_with_the_line_and_column(self):
        result = self.run_cli("check", "-", stdin='{"cards": [\n  [1, "Sol Ring"]\n  [1, "Forest"]\n]}')
        self.assertEqual(result.code, 1)
        self.assertIn("Standard input starts like JSON but is not valid JSON", result.err)
        self.assertIn("line 3, column 3", result.err)

# ----------------------------------------------------------------------------- serve
class ServeTests(CliCase):
    def test_it_listens_where_it_was_told_prints_where_to_open_it_and_stops_cleanly_on_ctrl_c(self):
        # the default: this computer only; the address, the phone instructions and the no-login warning on stdout
        result = self.run_cli("serve")
        self.assertEqual((result.code, result.err.strip()), (0, "stopped."))
        server, app = self.serve.servers[0], self.serve.apps[0]
        self.assertEqual((server.host, server.requested, server.served, server.closed, app.closed),
                         ("127.0.0.1", 8341, True, True, True))
        self.assertLessEqual(app.waited, 2)                                  # a download under way is not waited for
        self.assertIn("http://127.0.0.1:8341/", result.out)
        self.assertIn(f"Saved decks are in:        {os.path.abspath(config.DECKS)}", result.out)
        self.assertIn("--host set to this computer's Tailscale address", result.out)
        self.assertIn("`tailscale serve --bg --https=8443 8341`", result.out)  # 8443: the plain address may be taken
        self.assertIn("`tailscale serve --https=8443 off` stops it", result.out)
        self.assertIn("There is no login: anyone who can reach this address can change your decks.", result.out)
        self.assertIn("Run one server at a time", result.out)
        self.assertIn("Press Ctrl-C to stop.", result.out)

    def test_a_tailscale_address_is_where_the_phone_opens_it(self):
        # --host 100.101.102.103 --port 9000: the banner names that address, and still warns
        result = self.run_cli("serve", "--host", "100.101.102.103", "--port", "9000")
        self.assertEqual(result.code, 0)
        self.assertIn("Listening on 100.101.102.103:9000. On your phone, open http://100.101.102.103:9000/", result.out)
        self.assertNotIn("tailscale serve", result.out)
        self.assertIn("There is no login", result.out)
        self.assertEqual(self.serve.servers[0].requested, 9000)

    def test_every_interface_is_called_what_it_is(self):
        # 0.0.0.0 reaches every network the computer is on, which the banner says
        result = self.run_cli("serve", "--host", "0.0.0.0", "--port", "9000")
        self.assertIn("Listening on port 9000 of every network this computer is on.", result.out)
        self.assertIn("http://<this computer's address>:9000/", result.out)
        self.assertIn("Use this only on a network you trust.", result.out)

    def test_port_zero_prints_the_port_it_got(self):
        # a free port picked by the system
        self.assertIn("http://127.0.0.1:52000/", self.run_cli("serve", "--port", "0").out)

    def test_the_decks_folder_is_the_flag_or_the_environments(self):
        self.run_cli("serve", "--decks", "elsewhere")
        self.assertEqual(self.serve.apps[0].root, os.path.abspath("elsewhere"))
        self.run_cli("serve")
        self.assertEqual(self.serve.apps[1].root, os.path.abspath(config.DECKS))

    def test_the_card_index_and_the_run_wide_modes_reach_the_app(self):
        # --offline and --sources; the card index comes from the usual load
        self.run_cli("serve", "--offline", "--sources", "edhrec")
        app = self.serve.apps[0]
        self.assertIs(app.db, self.db)
        self.assertEqual((app.kw["offline"], app.kw["refresh"], app.kw["sources"]), (True, False, ("edhrec",)))
        self.assertTrue(callable(app.kw["log"]))

    def test_refresh_means_download_again_when_a_deck_is_first_opened_not_on_every_tap(self):
        # the app is told to refresh; the run-wide mode is off while the server runs and back after
        before = dict(net.MODE)
        self.run_cli("serve", "--refresh")
        app, server = self.serve.apps[0], self.serve.servers[0]
        self.assertTrue(app.kw["refresh"])
        self.assertEqual(server.modes[0]["refresh"], False)
        self.assertEqual(net.MODE, before)

    def test_a_port_that_is_in_use_is_exit_one_with_the_reason(self):
        self.serve.bind_error = OSError(98, "Address already in use")
        result = self.run_cli("serve")
        self.assertEqual((result.code, result.out), (1, ""))
        self.assertIn("cannot listen on 127.0.0.1:8341: Address already in use", result.err)

    def test_a_test_switch_that_is_not_a_number_is_exit_one(self):
        self.serve.app_error = ValueError("MTG_SERVE_DELAY must be a number, not 'soon'")
        result = self.run_cli("serve")
        self.assertEqual(result.code, 1)
        self.assertIn("MTG_SERVE_DELAY must be a number, not 'soon'", result.err)

    def test_the_server_does_not_print_a_report_and_json_changes_nothing(self):
        # serve has no result: nothing but the banner is on stdout, --json or not
        plain = self.run_cli("serve").out
        with_json = self.run_cli("serve", "--json").out
        self.assertEqual(plain, with_json)
        self.assertNotIn("{", plain)

    def test_a_server_that_runs_until_it_is_stopped_from_outside_ends_with_exit_zero(self):
        # serve_forever returns (a shutdown from another thread)
        self.serve.interrupt = False
        result = self.run_cli("serve")
        self.assertEqual(result.code, 0)
        self.assertTrue(self.serve.servers[0].closed)


# ----------------------------------------------------------------------------- themes
class ThemesTests(CliCase):
    def test_without_a_commander_it_needs_no_card_index_and_no_network(self):
        result = self.run_json("themes")
        self.assertEqual((result["command"], result["commander"], result["commanders"]), ("themes", None, []))
        self.assertEqual([p["slug"] for p in result["playstyles"]][:3], ["combat", "voltron", "go-wide"])
        self.assertEqual(result["themes"][0]["slug"], "tokens")
        self.assertIsNone(result["themes"][0]["count"])
        self.assertEqual((result["warnings"], result["sources"]), ([], {}))
        self.load.assert_not_called()
        self.meta.assert_not_called()

    def test_a_commanders_own_themes_come_from_edhrec(self):
        self.meta.return_value = {"taglinks": [{"slug": "tokens", "label": "Tokens", "count": 1455},
                                               {"slug": "squirrels", "label": "Squirrels", "count": 524}],
                                  "fetched": "2026-10-11T09:12:44Z"}
        result = self.run_json("themes", "--commander", "hazel of the rootbloom")
        self.assertEqual(result["commander"], "Hazel of the Rootbloom")
        self.assertEqual(result["themes"], [{"slug": "tokens", "label": "Tokens", "count": 1455},
                                            {"slug": "squirrels", "label": "Squirrels", "count": 524}])
        self.assertEqual(self.meta.call_args[0][0], ["Hazel of the Rootbloom"])
        self.assertEqual(result["sources"]["edhrec"]["fetched"], "2026-10-11T09:12:44Z")

    def test_a_pair_is_asked_about_together(self):
        self.run_json("themes", "--commander", "Pir, Imaginative Rascal", "--partner", "Toothy, Imaginary Friend")
        self.assertEqual(self.meta.call_args[0][0], ["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"])

    def test_a_commander_edhrec_has_no_page_for_gets_the_common_list_and_a_warning(self):
        result = self.run_json("themes", "--commander", "Hazel of the Rootbloom")
        self.assertEqual(result["themes"][0]["count"], None)
        self.assertEqual(result["warnings"],
                         ["EDHREC has no page for Hazel of the Rootbloom, so these are the common themes."])

    def test_edhrec_being_down_is_a_warning_not_a_failure(self):
        self.meta.side_effect = net.FetchError("edhrec", "u", "rate limited (429)")
        result = self.run_json("themes", "--commander", "Hazel of the Rootbloom")
        self.assertIn("EDHREC unavailable (rate limited (429))", result["warnings"][0])
        self.assertTrue(result["themes"])

    def test_edhrec_turned_off_with_sources_says_so(self):
        result = self.run_json("themes", "--commander", "Hazel of the Rootbloom", "--sources", "archidekt")
        self.meta.assert_not_called()
        self.assertIn("EDHREC is not among --sources", result["warnings"][0])

    def test_a_partner_without_a_commander_is_a_usage_error(self):
        result = self.run_cli("themes", "--partner", "Toothy, Imaginary Friend")
        self.assertEqual(result.code, 1)
        self.assertIn("--partner needs --commander", result.err)

    def test_a_card_that_cannot_lead_is_refused(self):
        result = self.run_cli("themes", "--commander", "Sol Ring")
        self.assertEqual(result.code, 1)
        self.assertIn("cannot be a commander", result.err)

    def test_the_text_report(self):
        result = self.run_cli("themes")
        self.assertIn("Playstyles (choose one with --playstyle)", result.out)
        self.assertIn("Common themes", result.out)


# ----------------------------------------------------------------------------- upgrade
class UpgradeTests(CliCase):
    def upgrade(self, *argv, **kw):
        return self.run_cli("upgrade", "--precon", "Test Precon", *argv, **kw)

    def calls(self):
        (prep_args, prep_kw), ((ctx, deck, db), up_kw) = self.engine.calls["prepare"], self.engine.calls["upgrade"]
        return SimpleNamespace(prep_args=prep_args, prep_kw=prep_kw, ctx=ctx, deck=deck, db=db, up_kw=up_kw)

    def test_the_shared_steps_in_order_with_the_defaults(self):
        self.assertEqual(self.upgrade().code, 0)
        c = self.calls()
        commanders, bracket, spec, db = c.prep_args
        self.assertEqual((commanders, bracket, db), (["Hazel of the Rootbloom"], 3, self.db))
        self.assertEqual((spec["themes"], spec["playstyle"], spec["include"], spec["exclude"], spec["keep_fun"]),
                         ([], "value", [], [], True))
        names = c.prep_kw["deck_cards"]
        self.assertEqual((len(names), names[:3]), (22, ["Sol Ring", "Mana Crypt", "Skullclamp"]))   # distinct cards
        self.assertEqual((c.prep_kw["owned"], c.prep_kw["sources"]), (set(), config.SOURCES))
        self.assertIs(c.ctx, self.engine.ctx)
        self.assertEqual(c.deck["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(sum(n for n, _ in c.deck["cards"]), 99)
        self.assertEqual(c.deck["name"], "Test Precon")
        self.assertIs(c.db, self.db)
        self.assertEqual((c.up_kw["budget"], c.up_kw["max_swaps"], c.up_kw["price_points"], c.up_kw["allow_combos"]),
                         (None, None, None, False))
        self.assertIs(c.up_kw["combos_fn"], self.combos_call)

    def test_every_flag_reaches_the_engine(self):
        owned = os.path.join(self.tmp(), "owned.txt")
        with open(owned, "w") as f:
            f.write("1 Sol Ring\n1 Mana Crypt\n1 Brainstorm\n")
        result = self.upgrade("--bracket", "4", "--budget", "75", "--max-swaps", "9", "--price-points", "25,50",
                              "--theme", "tokens",
                              "--theme", "aristocrats,squirrels", "--playstyle", "aristocrats", "--fantasy-weight", "0.8",
                              "--include", "sol ring", "--exclude", "Mana Crypt", "--no-keep-fun", "--allow-combos",
                              "--owned", owned, "--owned-precon", "Test Precon", "--sources", "edhrec,edhtop16")
        self.assertEqual(result.code, 0, result.err)
        c = self.calls()
        spec = c.prep_args[2]
        self.assertEqual(c.prep_args[1], 4)
        self.assertEqual((spec["themes"], spec["playstyle"], spec["weight"], spec["keep_fun"], spec["bracket"]),
                         (["tokens", "aristocrats", "squirrels"], "aristocrats", 0.8, False, 4))
        self.assertEqual((spec["include"], spec["exclude"]), (["Sol Ring"], ["Mana Crypt"]))      # canonical names
        self.assertEqual(c.prep_kw["sources"], ("edhrec", "edhtop16"))
        self.assertIn("Brainstorm", c.prep_kw["owned"])                           # a card outside the colors too
        self.assertTrue({"Sol Ring", "Mana Crypt", "Skullclamp", "Chatterfang, Squirrel General"} <= c.prep_kw["owned"])
        self.assertEqual((c.up_kw["budget"], c.up_kw["max_swaps"], c.up_kw["price_points"], c.up_kw["allow_combos"]),
                         (75.0, 9, [25.0, 50.0], True))

    def test_price_points_without_a_budget_are_a_usage_error_before_anything_is_loaded(self):
        result = self.upgrade("--price-points", "25,50")
        self.assertEqual(result.code, 1)
        self.assertIn("--price-points needs --budget", result.err)
        self.assertEqual(result.out, "")
        self.load.assert_not_called()                       # not even the card index was read
        self.assertNotIn("upgrade", self.engine.calls)

    def test_the_deck_block_is_filled_in_for_a_precon(self):
        result = self.run_json("upgrade", "--precon", "Test Precon")
        self.assertEqual(result["deck"], {"name": "Test Precon", "commanders": ["Hazel of the Rootbloom"], "count": 100,
                                          "ci": "BG"})
        self.assertEqual(result["command"], "upgrade")

    def test_a_file_is_named_by_its_file_name_and_stdin_by_what_it_is(self):
        self.assertEqual(self.run_json("upgrade", deck_path("cli_deck.txt"))["deck"]["name"], "cli_deck.txt")
        self.assertEqual(self.run_json("upgrade", "-", stdin=deck_text())["deck"]["name"], "standard input")

    def test_an_owned_file_with_a_typo_warns_instead_of_stopping(self):
        result = self.run_json("upgrade", "--precon", "Test Precon", "--owned", deck_path("cli_owned.txt"))
        self.assertTrue(any("owned card name(s) are not in the card index and were ignored: Sol Rign" in w
                            for w in result["warnings"]), result["warnings"])
        self.assertIn("Brainstorm", self.calls().prep_kw["owned"])

    def test_the_json_result_merges_our_warnings_and_sources_with_the_engines(self):
        result = self.run_json("upgrade", "--precon", "Test Precon")
        self.assertEqual(result["schema"], 1)
        self.assertIn("ctx: thin data warning", result["warnings"])
        self.assertTrue(any("edhtop16: only 40 tournament entries" in w for w in result["warnings"]))
        self.assertEqual(len(result["warnings"]), len(set(result["warnings"])))
        self.assertTrue({"scryfall", "mtgjson", "edhrec", "edhtop16", "spellbook"} <= set(result["sources"]))

    def test_the_sources_we_fetched_join_the_ones_the_engine_reports(self):
        self.engine.upgrade = lambda *a, **k: {k: v for k, v in fixture("render_upgrade.json").items() if k != "sources"}
        sources = self.run_json("upgrade", "--precon", "Test Precon")["sources"]
        self.assertEqual(set(sources), {"scryfall", "mtgjson", "edhrec"})      # ours, ours, and the context's
        self.assertEqual((sources["mtgjson"]["fetched"], sources["scryfall"]["fetched"]), (NOW, NOW))

    def test_the_engines_own_source_entries_win_over_ours(self):
        self.engine.ctx["sources"]["scryfall"] = {"fetched": "2026-01-01T00:00:00Z", "cache": "fresh", "age_days": 283.0}
        result = self.run_json("upgrade", "--precon", "Test Precon")
        self.assertEqual(result["sources"]["scryfall"]["fetched"], "2026-10-09T04:00:00Z")      # the fixture's, not ours

    def test_quiet_warnings_from_the_data_modules_are_collected_and_cleared(self):
        carddb.WARNINGS.append("cheapest prices: scryfall: HTTP 503")
        roles.WARNINGS.append("roles: Scryfall function tags unavailable")
        result = self.run_json("upgrade", "--precon", "Test Precon")
        self.assertIn("cheapest prices: scryfall: HTTP 503", result["warnings"])
        self.assertIn("roles: Scryfall function tags unavailable", result["warnings"])
        self.assertEqual((carddb.WARNINGS, roles.WARNINGS), ([], []))

    def test_a_stale_card_index_warns_with_its_age(self):
        self.db.cache, self.db.fetched = "stale", "2026-10-01T00:00:00Z"
        result = self.run_json("check", "--precon", "Test Precon")
        self.assertEqual(result["sources"]["scryfall"]["cache"], "stale")
        self.assertTrue(any(w.startswith("Scryfall data is ") and "days old (offline or the site failed)" in w
                            for w in result["warnings"]), result["warnings"])

    def test_the_text_report_is_the_default_and_goes_to_stdout_alone(self):
        result = self.upgrade("--budget", "75", "--theme", "tokens")
        self.assertEqual(result.code, 0)
        self.assertIn("Test Precon → Bracket 3, budget $75 (spent $42.10); themes: tokens; playstyle: aristocrats",
                      result.out)
        self.assertIn("Hazel of the Rootbloom (BG), 100 cards", result.out)
        self.assertIn(" 1  CUT Haywire Mite  →  ADD Ashnod's Altar   +0.42  $1.20", result.out)
        self.assertEqual(result.err, "")
        self.assertTrue(result.out.endswith("\n") and not result.out.endswith("\n\n"))

    def test_verbose_adds_the_evidence_for_each_cut(self):
        self.assertNotIn("cut: in 3% of 2,310", self.upgrade().out)
        self.assertIn("cut: in 3% of 2,310", self.upgrade("-v").out)

    def test_out_writes_the_upgraded_list_for_moxfield_and_archidekt(self):
        path = os.path.join(self.tmp(), "upgraded.txt")
        result = self.upgrade("--out", path)
        self.assertEqual(result.code, 0)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.startswith("Commander\n1 Hazel of the Rootbloom\n\nDeck\n1 Arcane Signet\n"
                                        "1 Ashnod's Altar\n"))
        self.assertTrue(text.endswith("17 Forest\n17 Swamp\n"))
        self.assertIn(f"Wrote the new list to {path}", result.out)
        again = decklist.parse(text)                         # and it reads back as the same deck
        self.assertEqual(again["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(sum(n for n, _ in again["cards"]), 5 + 17 + 17)

    def test_out_in_json_mode_is_in_the_result(self):
        path = os.path.join(self.tmp(), "upgraded.txt")
        self.assertEqual(self.run_json("upgrade", "--precon", "Test Precon", "--out", path)["out"], path)

    def test_an_unwritable_out_path_is_exit_one(self):
        result = self.upgrade("--out", os.path.join(self.tmp(), "no-such-folder", "x.txt"))
        self.assertEqual(result.code, 1)
        self.assertIn("cannot write", result.err)

    def test_fantasy_text_without_a_token_is_explained_on_stderr_in_a_report(self):
        result = self.upgrade("--fantasy", "a squirrel warlord")
        self.assertEqual(result.code, 0)
        self.assertIn("note: Your --fantasy text was not read: no Claude token", result.err)
        self.assertNotIn("Your --fantasy text", result.out)         # not repeated in the report

    def test_fantasy_text_without_a_token_is_in_the_result_when_stdout_is_json(self):
        result = self.run_cli("upgrade", "--precon", "Test Precon", "--fantasy", "a squirrel warlord", "--json")
        self.assertEqual(result.err, "")
        self.assertTrue(any("Your --fantasy text was not read" in w for w in json.loads(result.out)["warnings"]))

    def test_an_unknown_theme_is_dropped_with_a_note(self):
        result = self.upgrade("--theme", "tokenz")
        self.assertIn("unknown theme 'tokenz' dropped", result.err)
        self.assertEqual(self.calls().prep_args[2]["themes"], [])

    def test_an_unknown_include_card_is_exit_one(self):
        result = self.upgrade("--include", "Sol Rign")
        self.assertEqual(result.code, 1)
        self.assertIn("unknown card 'Sol Rign'; did you mean Sol Ring?", result.err)

    def test_names_the_precon_list_has_but_the_index_lacks_are_a_warning_not_a_stop(self):
        def precon(name, **kw):
            found = self.precon(name)
            found["cards"] = found["cards"] + [(1, "Zzyzx Not A Card")]
            return found
        with mock.patch.object(decklist, "precon", side_effect=precon):
            result = self.run_json("upgrade", "--precon", "Test Precon")
        self.assertTrue(any("1 card name(s) in the precon list are not in the card index" in w
                            for w in result["warnings"]))

    def test_the_commanders_color_identity_is_the_decks(self):
        self.assertEqual(self.run_json("upgrade", "--precon", "Test Precon")["deck"]["ci"], "BG")

    def test_a_deck_the_engine_returns_nothing_for_warns_about_out(self):
        self.engine.upgrade = lambda *a, **k: dict(fixture("render_upgrade.json"), deck_after=None)
        result = self.run_json("upgrade", "--precon", "Test Precon", "--out", os.path.join(self.tmp(), "x.txt"))
        self.assertIn("the upgrade returned no deck list, so --out wrote nothing", result["warnings"])


# ----------------------------------------------------------------------------- build
class BuildTests(CliCase):
    def test_the_commander_and_the_flags_reach_the_engine(self):
        result = self.run_cli("build", "hazel of the rootbloom", "--bracket", "2", "--budget", "50", "--theme", "tokens",
                              "--playstyle", "go-wide", "--allow-combos", "--owned-precon", "Test Precon")
        self.assertEqual(result.code, 0, result.err)
        (prep_args, prep_kw), ((ctx, db), kw) = self.engine.calls["prepare"], self.engine.calls["build"]
        self.assertEqual(prep_args[:2], (["Hazel of the Rootbloom"], 2))
        self.assertEqual((prep_args[2]["themes"], prep_args[2]["playstyle"]), (["tokens"], "go-wide"))
        self.assertIn("Sol Ring", prep_kw["owned"])
        self.assertNotIn("deck_cards", prep_kw)
        self.assertIs(ctx, self.engine.ctx)
        self.assertEqual((kw["budget"], kw["allow_combos"]), (50.0, True))
        self.assertIs(kw["combos_fn"], self.combos_call)
        self.assertIn("→ Bracket 3, budget $75 (spent $61.20)", result.out)      # the fixture result reached render

    def test_a_partner_pair_is_built_together(self):
        self.run_cli("build", "Pir, Imaginative Rascal", "--partner", "Toothy, Imaginary Friend")
        self.assertEqual(self.engine.calls["prepare"][0][0], ["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"])

    def test_two_commanders_that_cannot_pair_are_refused_before_any_work(self):
        result = self.run_cli("build", "Hazel of the Rootbloom", "--partner", "Chatterfang, Squirrel General")
        self.assertEqual(result.code, 1)
        self.assertIn("cannot lead a deck together", result.err)
        self.assertNotIn("prepare", self.engine.calls)

    def test_a_card_that_cannot_lead_is_refused(self):
        result = self.run_cli("build", "Sol Ring")
        self.assertEqual(result.code, 1)
        self.assertIn("cannot be a commander", result.err)

    def test_json_result_has_the_commander_block_defaults_and_merged_notes(self):
        result = self.run_json("build", "Hazel of the Rootbloom")
        self.assertEqual((result["command"], result["ci"]), ("build", "BG"))
        self.assertEqual(result["commanders"], ["Hazel of the Rootbloom"])
        self.assertIn("ctx: thin data warning", result["warnings"])
        self.assertTrue({"edhrec", "scryfall"} <= set(result["sources"]))

    def test_out_writes_the_commanders_the_cards_and_the_basics(self):
        path = os.path.join(self.tmp(), "built.txt")
        result = self.run_cli("build", "Hazel of the Rootbloom", "--out", path)
        self.assertEqual(result.code, 0)
        with open(path, encoding="utf-8") as f:
            parsed = decklist.parse(f.read())
        self.assertEqual(parsed["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(dict((name, n) for n, name in parsed["cards"])["Forest"], 9)
        self.assertEqual(dict((name, n) for n, name in parsed["cards"])["Swamp"], 8)
        self.assertEqual(sum(n for n, _ in parsed["cards"]), 8 + 17)           # the fixture's 8 cards and 17 basics
        self.assertIn(f"Wrote the new list to {path}", result.out)

    def test_the_commander_is_not_written_twice(self):
        built = fixture("render_build.json")
        built["cards"].append({"name": "Hazel of the Rootbloom", "section": "Creatures", "roles": [], "score": 1.0,
                               "price": 4.0, "owned": False, "evidence": "", "kind": "none"})
        self.engine.build = lambda *a, **k: built
        path = os.path.join(self.tmp(), "built.txt")
        self.run_cli("build", "Hazel of the Rootbloom", "--out", path)
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read().count("Hazel of the Rootbloom"), 1)

    def test_verbose_gives_every_card_its_evidence_instead_of_the_top_twenty(self):
        built = fixture("render_build.json")
        built["cards"] = [{"name": f"Card {i:02}", "section": "Creatures", "roles": [], "score": 1 - i / 100, "price": 1.0,
                           "owned": False, "evidence": f"EVID-{i:02}", "kind": "builder"} for i in range(25)]
        self.engine.build = lambda *a, **k: built
        self.assertEqual(self.run_cli("build", "Hazel of the Rootbloom").out.count("EVID-"), 20)
        self.assertEqual(self.run_cli("build", "Hazel of the Rootbloom", "-v").out.count("EVID-"), 25)
        self.assertEqual(self.run_cli("build", "Hazel of the Rootbloom", "--verbose").out.count("EVID-"), 25)

    def test_no_sources_at_all_is_passed_through_for_the_engines_popularity_fallback(self):
        self.run_cli("build", "Hazel of the Rootbloom", "--sources", "")
        self.assertEqual(self.engine.calls["prepare"][1]["sources"], ())


# ----------------------------------------------------------------------------- suggest
class SuggestTests(CliCase):
    def test_the_spec_and_the_filters_reach_the_engine(self):
        result = self.run_cli("suggest", "--theme", "tokens", "--playstyle", "go-wide", "--bracket", "4", "--colors", "gb",
                              "--budget", "100", "--limit", "5", "--owned-precon", "Test Precon")
        self.assertEqual(result.code, 0, result.err)
        (spec, db), kw = self.engine.calls["suggest"]
        self.assertEqual((spec["themes"], spec["playstyle"], spec["bracket"]), (["tokens"], "go-wide", 4))
        self.assertIs(db, self.db)
        self.assertEqual((kw["colors"], kw["budget"], kw["limit"], kw["sources"]), ("BG", 100.0, 5, config.SOURCES))
        self.assertIn("Sol Ring", kw["owned"])
        self.assertIn("Commanders for tokens; playstyle: go-wide", result.out)

    def test_defaults(self):
        self.run_cli("suggest", "--theme", "tokens")
        (spec, _), kw = self.engine.calls["suggest"]
        self.assertEqual((spec["bracket"], spec["keep_fun"]), (3, True))
        self.assertEqual((kw["colors"], kw["budget"], kw["limit"], kw["owned"]), (None, None, 10, set()))

    def test_a_playstyle_alone_is_enough(self):
        self.assertEqual(self.run_cli("suggest", "--playstyle", "aristocrats").code, 0)

    def test_nothing_to_go_on_is_exit_one_and_points_to_the_menu(self):
        result = self.run_cli("suggest")
        self.assertEqual(result.code, 1)
        self.assertIn("suggest needs a theme or a playstyle", result.err)
        self.assertIn("`themes`", result.err)
        self.assertNotIn("suggest", self.engine.calls)

    def test_the_result_is_completed_where_the_engine_left_gaps(self):
        bare = {"commanders": []}
        self.engine.suggest = lambda *a, **k: dict(bare)
        result = self.run_json("suggest", "--theme", "tokens", "--colors", "bg", "--budget", "100")
        self.assertEqual((result["command"], result["bracket"], result["filters"]),
                         ("suggest", 3, {"colors": "BG", "budget": 100.0}))
        self.assertEqual(result["spec"]["themes"], ["tokens"])
        self.assertIn("scryfall", result["sources"])

    def test_the_engines_own_answers_are_kept(self):
        result = self.run_json("suggest", "--theme", "tokens")
        self.assertEqual(result["filters"], fixture("render_suggest.json")["filters"])


# ----------------------------------------------------------------------------- warm
class WarmTests(CliCase):
    """`warm` with every provider replaced by a stand-in that logs the call and answers with a small Signal."""

    def setUp(self):
        super().setUp()
        self.log = []
        self.decks = {"all": 12334, "bracket": 1125, "bracket_theme": 281, "theme": 1455, "global": 5000}   # deck counts
        mock.patch.object(edhrec, "signals", side_effect=self.edhrec_signals).start()
        mock.patch.object(edhrec, "bracket_theme_signal", side_effect=self.edhrec_bracket_theme).start()
        mock.patch.object(edhrec, "theme_signal", side_effect=self.edhrec_global_theme).start()
        self.salt = mock.patch.object(edhrec, "salt_scores", return_value={"Rhystic Study": 3.0}).start()
        mock.patch.object(edhtop16, "signals", side_effect=self.edhtop16_signals).start()
        mock.patch.object(archidekt, "signals", side_effect=self.archidekt_signals).start()
        self.precons = mock.patch.object(decklist, "precons_for_commander", return_value=[
            {"name": "Squirreled Away", "fetched": "2026-10-10T00:00:00Z"}]).start()
        self.prices = mock.patch.object(carddb, "cheapest_prices", side_effect=lambda names, **k: {
            n: 1.0 for n in names}).start()
        # The tag loads and the combo index answer as the real ones do on a good day. A tag load leaves a note in
        # scryfall_tags.INFO when it has read the tags (None here: it could not); the combo index answers
        # (index, {"fetched", "cache"}), or raises the FetchError that self.combo_index holds. The modes in force
        # while each was asked are kept, to show that --refresh and --offline reach them.
        self.tag_notes = {"roles": {"fetched": "2026-10-09T04:00:00Z", "cache": "fresh"},
                          "attributes": {"fetched": "2026-10-09T04:00:00Z", "cache": "fresh"}}
        self.combo_index = (111378, {"fetched": "2026-10-10T08:00:00Z", "cache": "fresh"})
        self.modes = {}
        self.tag.side_effect = self.tag_roles
        self.attributes.side_effect = self.tag_attributes
        self.local_index = mock.patch.object(spellbook, "local_index", side_effect=self.saved_combo_index).start()

    # --- stand-in tag loads and combo index
    def read_tags(self, kind):
        """What scryfall_tags.load leaves in INFO when it has read the tags (and nothing when it could not)."""
        self.modes[kind] = dict(net.MODE)
        note = self.tag_notes[kind]
        if note:
            scryfall_tags.INFO.clear()
            scryfall_tags.INFO.update(note)
        return bool(note)

    def tag_roles(self, names, db, **kw):
        self.read_tags("roles")
        return {n: set(TEST_ROLES.get(n, ())) for n in names}

    def tag_attributes(self, names, db, **kw):
        if not self.read_tags("attributes"):        # the line roles.attributes leaves when it cannot read the tags
            roles.WARNINGS.append("roles: Scryfall function tags for card attributes unavailable, so the removal, "
                                  "mana, land and playstyle counts that need them are not shown (scryfall_tags: "
                                  "HTTP 503)")
        return {n: frozenset() for n in names}

    def saved_combo_index(self, **kw):
        self.modes["combos"] = dict(net.MODE)
        if isinstance(self.combo_index, Exception):
            raise self.combo_index
        combos, info = self.combo_index
        return FakeComboIndex(combos), info

    # --- stand-in providers
    def signal(self, source, n, cards=None, kind="builder", cache="network", fetched="2026-10-11T09:12:44Z"):
        if n is None:
            return None
        cards = {"Sol Ring": {"decks": 900, "of": 1000, "synergy": 0.1},
                 "Forest": {"decks": 1000, "of": 1000, "synergy": 0.0},
                 "Cultivate": {"decks": 500, "of": 1000, "synergy": None}} if cards is None else cards
        return {"source": source, "kind": kind, "commanders": ["Hazel of the Rootbloom"], "bracket": None, "theme": None,
                "url": "u", "fetched": fetched, "cache": cache, "n": n, "cards": cards, "totals": None, "meta": {}}

    def edhrec_signals(self, commanders, bracket=None, theme=None, **kw):
        self.log.append(("edhrec", bracket, theme))
        n = self.decks["theme"] if theme else self.decks["bracket"] if bracket else self.decks["all"]
        return [self.signal("edhrec", n)] if n is not None else []

    def edhrec_bracket_theme(self, commanders, bracket, theme, **kw):
        self.log.append(("bracket_theme", bracket, theme))
        return self.signal("edhrec", self.decks["bracket_theme"])

    def edhrec_global_theme(self, theme, **kw):
        self.log.append(("global", theme))
        return self.signal("edhrec", self.decks["global"])

    def edhtop16_signals(self, commanders, bracket=None, **kw):
        self.log.append(("edhtop16", bracket))
        cards = {"Skullclamp": {"entries": 30, "games": 100, "wins": 20, "draws": 0, "topcuts": 5}}
        return [self.signal("edhtop16", 40, cards, kind="tournament")]

    def archidekt_signals(self, commanders, bracket=None, **kw):
        self.log.append(("archidekt", bracket, kw.get("limit")))
        return [self.signal("archidekt", 30)]

    def rows(self, result):
        return [(r["source"], r["what"]) for r in result["fetched"]]

    def asked(self, kind):
        return [entry for entry in self.log if entry[0] == kind]

    # --- the steps
    def test_a_commander_at_a_bracket_with_a_theme(self):
        result = self.run_json("warm", "hazel of the rootbloom", "--theme", "tokens")
        self.assertEqual((result["command"], result["commanders"], result["bracket"], result["themes"]),
                         ("warm", ["Hazel of the Rootbloom"], 3, ["tokens"]))
        self.assertEqual(self.rows(result), [
            ("scryfall", f"card index ({len(self.db):,} cards)"),
            ("scryfall_tags", f"function tags for card attributes ({len(roles.ATTRIBUTE_TAGS)} tags)"),
            ("spellbook", "combo index (111,378 combos)"),
            ("edhrec", "all-bracket page (12,334 decks)"),
            ("edhrec", "Bracket 3 page (1,125 decks)"),
            ("edhrec", "tokens decks at Bracket 3 (281 decks)"),
            ("edhrec", "salt list (1 cards)"),
            ("edhtop16", "tournament results (40 entries with decklists)"),
            ("mtgjson", "precons with this commander: Squirreled Away"),
            ("scryfall_tags", "function tags (roles of 3 candidate cards)"),
            ("scryfall", "cheapest printings of 3 candidate cards")])
        for row in result["fetched"]:
            self.assertEqual(set(row), {"source", "what", "cache", "fetched"})
        every_bracket = next(r for r in result["fetched"] if r["what"].startswith("all-bracket page"))
        self.assertEqual((every_bracket["cache"], every_bracket["fetched"]), ("network", "2026-10-11T09:12:44Z"))
        self.assertEqual(result["warnings"], [])

    def test_a_thin_theme_page_is_widened_to_all_brackets_the_way_the_engine_does(self):
        self.decks["bracket_theme"] = 10                      # under the thin line
        result = self.run_json("warm", "Hazel of the Rootbloom", "--theme", "tokens")
        self.assertEqual([e for e in self.log if "tokens" in e],
                         [("bracket_theme", 3, "tokens"), ("edhrec", None, "tokens")])
        self.assertIn(("edhrec", "tokens decks, all brackets (1,455 decks)"), self.rows(result))

    def test_with_no_theme_page_at_all_the_theme_across_all_commanders_is_read(self):
        self.decks.update(bracket_theme=None, theme=None)
        result = self.run_json("warm", "Hazel of the Rootbloom", "--theme", "tokens")
        self.assertEqual([e for e in self.log if "tokens" in e],
                         [("bracket_theme", 3, "tokens"), ("edhrec", None, "tokens"), ("global", "tokens")])
        self.assertIn(("edhrec", "tokens decks across all commanders (5,000 decks)"), self.rows(result))

    def test_a_page_that_does_not_exist_is_a_row_not_a_warning(self):
        self.decks.update(bracket_theme=None, theme=None)
        self.decks["global"] = None
        result = self.run_json("warm", "Hazel of the Rootbloom", "--theme", "tokens")
        missing = [r for r in result["fetched"] if r["cache"] == "none"]
        self.assertEqual([r["what"] for r in missing], ["tokens decks at Bracket 3 (no such page)",
                                                         "tokens decks, all brackets (no such page)",
                                                         "tokens decks across all commanders (no such page)"])
        self.assertEqual(result["warnings"], [])

    def test_a_commander_edhrec_does_not_know_is_a_warning(self):
        self.decks.update(all=None, bracket=None)
        result = self.run_json("warm", "Hazel of the Rootbloom", "--sources", "edhrec")
        self.assertIn("EDHREC has no page for Hazel of the Rootbloom.", result["warnings"])

    def test_the_tournament_term_is_fetched_only_where_the_engine_weights_it(self):
        for bracket, expected in ((1, False), (2, False), (3, True), (4, True), (5, True)):
            with self.subTest(bracket=bracket):
                self.log[:] = []
                self.run_json("warm", "Hazel of the Rootbloom", "--bracket", str(bracket))
                self.assertEqual(bool(self.asked("edhtop16")), expected)

    def test_a_failed_step_is_a_warning_and_the_rest_carry_on(self):
        self.salt.side_effect = net.FetchError("edhrec", "u", "HTTP 503")
        result = self.run_json("warm", "Hazel of the Rootbloom")
        self.assertIn("edhrec: salt list could not be downloaded (edhrec: HTTP 503)", result["warnings"])
        self.assertNotIn(("edhrec", "salt list (1 cards)"), self.rows(result))
        self.assertIn("edhtop16", [r["source"] for r in result["fetched"]])
        self.assertIn("mtgjson", [r["source"] for r in result["fetched"]])

    def test_every_provider_failing_is_still_exit_zero_with_a_warning_for_each(self):
        err = net.FetchError("edhrec", "u", "network error")
        for target in (edhrec.signals, edhrec.salt_scores, edhtop16.signals, archidekt.signals,
                       decklist.precons_for_commander):
            target.side_effect = err
        self.combo_index = err                                   # and the combo index, and the attribute tags
        self.tag_notes["attributes"] = None
        result = self.run_json("warm", "Hazel of the Rootbloom")
        self.assertEqual(self.rows(result), [("scryfall", f"card index ({len(self.db):,} cards)")])
        # two pages, salt, two Archidekt reads, tournaments, precons, the combo index, the attribute tags
        self.assertEqual(len(result["warnings"]), 9)
        self.assertFalse(any("has no page" in w for w in result["warnings"]))    # a failure is not a missing page

    def test_a_thin_bracket_borrows_from_its_neighbours_and_archidekt(self):
        self.decks["bracket"] = 12
        result = self.run_json("warm", "Hazel of the Rootbloom", "--bracket", "3")
        self.assertIn(("edhrec", 2, None), self.log)
        self.assertIn(("edhrec", 4, None), self.log)
        self.assertEqual(self.asked("archidekt"), [("archidekt", 3, 30)])
        self.assertIn(("archidekt", "Bracket 3 decks (30 decks)"), self.rows(result))

    def test_the_edge_brackets_have_only_one_neighbour(self):
        self.decks["bracket"] = 12
        self.run_json("warm", "Hazel of the Rootbloom", "--bracket", "1")
        self.assertIn(("edhrec", 2, None), self.log)
        self.assertNotIn(("edhrec", 0, None), self.log)

    def test_a_thick_bracket_does_not(self):
        self.run_json("warm", "Hazel of the Rootbloom", "--bracket", "3")
        self.assertNotIn(("edhrec", 2, None), self.log)
        self.assertEqual(self.asked("archidekt"), [])

    def test_without_edhrec_the_archidekt_decks_stand_in(self):
        result = self.run_json("warm", "Hazel of the Rootbloom", "--sources", "archidekt,edhtop16")
        self.assertEqual(self.asked("archidekt"), [("archidekt", 3, 30), ("archidekt", None, 30)])
        self.assertEqual(self.asked("edhrec") + self.asked("bracket_theme"), [])
        self.assertNotIn("edhrec", {r["source"] for r in result["fetched"]})

    def test_sources_turned_off_are_not_fetched(self):
        self.run_json("warm", "Hazel of the Rootbloom", "--sources", "edhrec")
        self.assertEqual((self.asked("edhtop16"), self.asked("archidekt")), ([], []))

    def test_prices_and_tags_cover_the_cards_the_pages_play_most_but_not_basic_lands(self):
        self.run_json("warm", "Hazel of the Rootbloom")
        names = self.prices.call_args[0][0]
        self.assertEqual(sorted(names), ["Cultivate", "Skullclamp", "Sol Ring"])      # Forest is a basic land
        self.assertEqual(self.tag.call_args[0][0], names)
        self.assertEqual(len(set(names)), len(names))

    def test_the_candidates_are_the_most_played_first_and_capped_per_page(self):
        big = {f"Card {i}": {"decks": 1000 - i, "of": 1000, "synergy": None} for i in range(2000)}
        self.db.cards.update({n: dict(self.db.get("Sol Ring"), name=n, front=n) for n in big})
        self.db._alias = None
        with mock.patch.object(edhrec, "signals", return_value=[self.signal("edhrec", 100, big)]):
            self.run_json("warm", "Hazel of the Rootbloom", "--sources", "edhrec")
        names = self.prices.call_args[0][0]
        self.assertEqual(names, [f"Card {i}" for i in range(cli.PER_PAGE)])

    def test_the_candidates_are_capped_overall(self):
        pages = [self.signal("edhrec", 100, {f"Page {p} Card {i}": {"decks": 900, "of": 1000, "synergy": None}
                                              for i in range(cli.PER_PAGE)}) for p in range(6)]
        for sig in pages:
            self.db.cards.update({n: dict(self.db.get("Sol Ring"), name=n, front=n) for n in sig["cards"]})
        self.db._alias = None
        with mock.patch.object(edhrec, "signals", side_effect=[[p] for p in pages] + [[]] * 10):
            self.run_json("warm", "Hazel of the Rootbloom", "--sources", "edhrec", "--theme", "a", "--theme", "b",
                          "--theme", "c", "--theme", "d")
        self.assertLessEqual(len(self.prices.call_args[0][0]), cli.MAX_CANDIDATES)

    def test_tags_are_listed_only_when_they_were_read(self):
        self.tag_notes.update(roles=None, attributes=None)    # INFO stays empty: nothing says tags were loaded
        rows = {r["source"] for r in self.run_json("warm", "Hazel of the Rootbloom")["fetched"]}
        self.assertNotIn("scryfall_tags", rows)

    def test_a_pair_warms_both_and_looks_for_precons_of_each(self):
        self.run_json("warm", "Pir, Imaginative Rascal", "--partner", "Toothy, Imaginary Friend")
        self.assertEqual([c[0][0] for c in self.precons.call_args_list],
                         ["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"])

    def test_themes_may_be_comma_separated_and_repeated(self):
        result = self.run_json("warm", "Hazel of the Rootbloom", "--theme", "tokens,squirrels", "--theme", "food")
        self.assertEqual(result["themes"], ["tokens", "squirrels", "food"])

    def test_sources_in_the_result_carry_fetch_dates(self):
        sources = self.run_json("warm", "Hazel of the Rootbloom")["sources"]
        self.assertEqual((sources["edhrec"]["fetched"], sources["edhrec"]["cache"]), ("2026-10-11T09:12:44Z", "network"))
        self.assertIn("age_days", sources["edhtop16"])

    def test_a_stale_page_is_reported_in_its_row_and_warned_about(self):
        stale = self.signal("edhrec", 12334, cache="stale", fetched="2026-09-20T00:00:00Z")
        with mock.patch.object(edhrec, "signals", return_value=[stale]):
            result = self.run_json("warm", "Hazel of the Rootbloom")
        every_bracket = next(r for r in result["fetched"] if r["what"].startswith("all-bracket page"))
        self.assertEqual(every_bracket["cache"], "stale")
        self.assertTrue(any(w.startswith("EDHREC data is ") for w in result["warnings"]), result["warnings"])

    def test_an_unknown_commander_is_exit_one(self):
        self.assertEqual(self.run_cli("warm", "Hazl of the Rootbloom").code, 1)

    def test_a_mistyped_commander_stops_before_the_big_downloads(self):
        # worked example: "Hazl" is caught before the 29 MB combo file or the tag file is downloaded
        self.assertEqual(self.run_cli("warm", "Hazl of the Rootbloom").code, 1)
        self.local_index.assert_not_called()
        self.attributes.assert_not_called()

    def test_the_text_report(self):
        result = self.run_cli("warm", "Hazel of the Rootbloom", "--theme", "tokens")
        self.assertEqual(result.code, 0)
        self.assertIn("Downloaded for Hazel of the Rootbloom at Bracket 3; themes: tokens", result.out)
        self.assertIn("all-bracket page (12,334 decks)", result.out)

    # --- the two downloads that belong to no commander: the card attribute tags and the combo index
    def shared_rows(self, result):
        """The two rows that come right after the card index."""
        return result["fetched"][1:3]

    def test_online_with_nothing_saved_both_are_downloaded_and_follow_the_card_index(self):
        # worked example: a first run on a new computer. Scryfall's tags and Spellbook's daily file are downloaded
        # now, so each row says `network` and when, and --json carries the rows in the shape of every other row.
        self.tag_notes["attributes"] = {"fetched": "2026-10-12T05:00:20Z", "cache": "network"}
        self.combo_index = (111378, {"fetched": "2026-10-12T05:01:10Z", "cache": "network"})
        result = self.run_json("warm", "Hazel of the Rootbloom")
        self.assertEqual(self.shared_rows(result), [
            {"source": "scryfall_tags", "what": f"function tags for card attributes ({len(roles.ATTRIBUTE_TAGS)} tags)",
             "cache": "network", "fetched": "2026-10-12T05:00:20Z"},
            {"source": "spellbook", "what": "combo index (111,378 combos)", "cache": "network",
             "fetched": "2026-10-12T05:01:10Z"}])
        self.assertEqual(result["warnings"], [])
        self.assertEqual((result["sources"]["spellbook"]["cache"], result["sources"]["spellbook"]["fetched"]),
                         ("network", "2026-10-12T05:01:10Z"))
        self.assertIn("scryfall_tags", result["sources"])

    def test_the_text_report_lists_both_in_its_table(self):
        out = self.run_cli("warm", "Hazel of the Rootbloom").out
        self.assertIn(f"function tags for card attributes ({len(roles.ATTRIBUTE_TAGS)} tags)", out)
        self.assertIn("combo index (111,378 combos)", out)

    def test_both_are_asked_for_the_way_stats_and_serve_ask(self):
        # the same two calls, with no mode of their own, so the run-wide --refresh and --offline decide
        self.run_json("warm", "Hazel of the Rootbloom")
        self.attributes.assert_called_once_with([], self.db)
        self.local_index.assert_called_once_with()

    def test_offline_the_rows_report_the_saved_copies_and_the_flag_reaches_both(self):
        # worked example: --offline on a plane, with the tags three weeks old (in date for 30 days) and the combo
        # index nine days old (past its 7). Each is read as it is: the tags are fresh, the index is stale and says so.
        self.tag_notes["attributes"] = {"fetched": "2026-09-21T04:00:00Z", "cache": "fresh"}
        self.combo_index = (111378, {"fetched": "2026-10-03T08:00:00Z", "cache": "stale"})
        result = self.run_json("warm", "Hazel of the Rootbloom", "--offline")
        tags, combos = self.shared_rows(result)
        self.assertEqual((tags["cache"], tags["fetched"]), ("fresh", "2026-09-21T04:00:00Z"))
        self.assertEqual((combos["cache"], combos["fetched"]), ("stale", "2026-10-03T08:00:00Z"))
        self.assertTrue(any(w.startswith("Commander Spellbook data is ") for w in result["warnings"]),
                        result["warnings"])
        self.assertTrue(self.modes["attributes"]["offline"] and self.modes["combos"]["offline"])

    def test_refresh_reaches_both_and_a_plain_run_does_not_ask_for_it(self):
        self.run_json("warm", "Hazel of the Rootbloom", "--refresh")
        self.assertTrue(self.modes["attributes"]["refresh"] and self.modes["combos"]["refresh"])
        self.run_json("warm", "Hazel of the Rootbloom")
        self.assertFalse(self.modes["attributes"]["refresh"] or self.modes["combos"]["refresh"])

    def test_both_are_downloaded_whatever_evidence_sources_are_on(self):
        # Scryfall and Spellbook are not among --sources: they are always used
        result = self.run_json("warm", "Hazel of the Rootbloom", "--sources", "")
        self.assertEqual([r["source"] for r in self.shared_rows(result)], ["scryfall_tags", "spellbook"])

    def test_a_combo_index_that_cannot_be_built_is_a_warning_and_the_rest_of_warm_carries_on(self):
        # worked example: Spellbook's file host is down on a first run
        self.combo_index = net.FetchError("spellbook", spellbook.VARIANTS_URL, "download failed: timed out")
        result = self.run_json("warm", "Hazel of the Rootbloom", "--theme", "tokens")
        self.assertIn("spellbook: combo index could not be downloaded (spellbook: download failed: timed out)",
                      result["warnings"])
        self.assertNotIn("spellbook", {r["source"] for r in result["fetched"]})
        self.assertEqual(self.rows(result)[1][0], "scryfall_tags")                  # the step before it ran
        self.assertEqual([r["source"] for r in result["fetched"]][2:],
                         ["edhrec", "edhrec", "edhrec", "edhrec", "edhtop16", "mtgjson", "scryfall_tags", "scryfall"])

    def test_attribute_tags_that_cannot_be_had_are_a_warning_and_the_rest_of_warm_carries_on(self):
        # worked example: Scryfall's tag file cannot be fetched on a first run. roles.attributes does not raise: it
        # leaves its own line among the warnings, and warm must not list tags it did not get.
        self.tag_notes["attributes"] = None
        result = self.run_json("warm", "Hazel of the Rootbloom", "--theme", "tokens")
        self.assertTrue(any(w.startswith("roles: Scryfall function tags for card attributes unavailable")
                            for w in result["warnings"]), result["warnings"])
        what = [r["what"] for r in result["fetched"]]
        self.assertFalse(any(w.startswith("function tags for card attributes") for w in what))
        self.assertEqual(self.rows(result)[1], ("spellbook", "combo index (111,378 combos)"))     # the step after ran
        self.assertIn("function tags (roles of 3 candidate cards)", what)                      # and the role tags
        self.assertIn("cheapest printings of 3 candidate cards", what)

    def test_a_failed_combo_index_does_not_hide_that_edhrec_has_no_page(self):
        # worked example: Spellbook is down, and EDHREC has no page for this commander. The warning "EDHREC has no
        # page" is only held back when a failed EDHREC download has already been warned about.
        self.combo_index = net.FetchError("spellbook", "u", "HTTP 503")
        self.decks.update(all=None, bracket=None)
        result = self.run_json("warm", "Hazel of the Rootbloom", "--sources", "edhrec")
        self.assertIn("spellbook: combo index could not be downloaded (spellbook: HTTP 503)", result["warnings"])
        self.assertIn("EDHREC has no page for Hazel of the Rootbloom.", result["warnings"])

    def test_role_tags_that_cannot_be_read_do_not_borrow_the_date_of_the_attribute_tags(self):
        # worked example: the attribute tags were read a moment ago and left their date in scryfall_tags.INFO; the
        # role tags then cannot be read. Their row must not be written from the date the attribute tags left.
        self.tag_notes["roles"] = None
        result = self.run_json("warm", "Hazel of the Rootbloom")
        what = [r["what"] for r in result["fetched"]]
        self.assertIn(f"function tags for card attributes ({len(roles.ATTRIBUTE_TAGS)} tags)", what)
        self.assertFalse(any(w.startswith("function tags (roles of") for w in what), what)


# ----------------------------------------------------------------------------- warm and the cache folder
class WarmCacheTests(CliCase):
    """`warm` with the real attribute-tag load and the real combo index, working on a temporary cache folder. Only the
    two downloads are replaced, by the small tag tree and daily combo file in fixtures/. What the stand-ins in
    WarmTests cannot show is shown here: the files `warm` saves are the ones a later run, `stats` among them, finds."""

    TAGS_URL = "https://data.scryfall.io/oracle-tags/t.jsonl.gz"

    def setUp(self):
        super().setUp()
        self.cache = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.cache, True)
        self.downloads = []
        for patcher in (mock.patch.object(net, "CACHE", self.cache),
                        mock.patch.object(net, "download", self.download),
                        mock.patch.object(carddb, "bulk_entry", lambda kind, **kw: (self.TAGS_URL, {})),
                        mock.patch.object(roles, "attributes", REAL_ATTRIBUTES),
                        mock.patch.object(roles, "attributes_loaded", REAL_ATTRIBUTES_LOADED),
                        mock.patch.object(spellbook, "combos_for", REAL_COMBOS_FOR),
                        mock.patch.object(decklist, "precons_for_commander", return_value=[])):
            patcher.start()
        self.new_run()
        self.addCleanup(self.new_run)

    def new_run(self):
        """What a later command-line run starts with: nothing loaded yet, only the saved files."""
        roles.reset()
        spellbook.reset()
        scryfall_tags.INFO.clear()

    def download(self, url, path, *, source, decode=True):
        self.downloads.append(url)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if url == spellbook.VARIANTS_URL:
            shutil.copyfile(os.path.join(FIXTURES, "spellbook_variants.json"), path)
        else:
            with open(os.path.join(FIXTURES, "scryfall_tags_sample.jsonl"), "rb") as src, gzip.open(path, "wb") as out:
                out.write(src.read())

    def warm(self, *flags):
        """`warm` for Hazel with every evidence source off, so that only the card index, the two downloads that belong
        to no commander and the precons remain."""
        return self.run_json("warm", "Hazel of the Rootbloom", "--sources", "", *flags)

    def age_saved(self, source, key, days):
        """Make the saved file of a source `days` older, in both clocks it keeps."""
        path = net.cache_file(source, key)
        doc = net.read_json(path)
        doc["ts"] -= days * config.DAY
        doc["fetched"] = net.iso(doc["ts"])
        net.atomic_json(path, doc)

    def test_a_first_online_run_saves_both_and_a_later_offline_run_finds_them_without_downloading(self):
        # worked example: warm on the train station's wifi, then --offline on the train
        first = self.warm()
        self.assertEqual([(r["source"], r["cache"]) for r in first["fetched"][1:3]],
                         [("scryfall_tags", "network"), ("spellbook", "network")])
        self.assertEqual(len(self.downloads), 2)                  # Scryfall's tag file and Spellbook's daily file, once
        self.new_run()
        again = self.warm("--offline")
        self.assertEqual(len(self.downloads), 2)                  # nothing more
        self.assertEqual([(r["source"], r["what"], r["cache"], r["fetched"]) for r in again["fetched"][1:3]],
                         [(r["source"], r["what"], "fresh", r["fetched"]) for r in first["fetched"][1:3]])
        self.assertEqual(again["warnings"], [])

    def test_what_stats_asks_for_offline_is_what_warm_saved(self):
        # the calls `stats` makes (roles.attributes, spellbook.combos_for), offline, in a run of their own
        self.warm()
        self.new_run()
        attrs = roles.attributes(["Sol Ring"], self.db, offline=True)
        self.assertTrue(roles.attributes_loaded())
        self.assertEqual(attrs, {"Sol Ring": frozenset({"mana-rock"})})    # Sol Ring's tag, read from the saved file
        found = spellbook.combos_for(["Hazel of the Rootbloom"], ["Skullclamp"], identity="BG", offline=True)
        self.assertEqual((found["via"], [c["id"] for c in found["included"]]), ("index", ["9100-9101"]))
        self.assertEqual(len(self.downloads), 2)

    def test_online_with_both_saved_and_in_date_nothing_is_downloaded_again(self):
        self.warm()
        self.new_run()
        again = self.warm()
        self.assertEqual(len(self.downloads), 2)
        self.assertEqual([r["cache"] for r in again["fetched"][1:3]], ["fresh", "fresh"])

    def test_refresh_downloads_both_again(self):
        self.warm()
        self.new_run()
        again = self.warm("--refresh")
        self.assertEqual(len(self.downloads), 4)
        self.assertEqual([r["cache"] for r in again["fetched"][1:3]], ["network", "network"])

    def test_offline_with_nothing_saved_both_are_warnings_and_nothing_is_downloaded(self):
        # worked example: --offline on a computer that has never run warm; the card index and the precons are
        # still listed, and the run is not an error
        result = self.warm("--offline")
        self.assertEqual(self.downloads, [])
        self.assertEqual([r["source"] for r in result["fetched"]], ["scryfall", "mtgjson"])
        warnings = " | ".join(result["warnings"])
        self.assertIn("spellbook: combo index could not be downloaded (spellbook: offline (--offline) and no saved "
                      "combo file", warnings)
        self.assertIn("roles: Scryfall function tags for card attributes unavailable", warnings)

    def test_offline_with_copies_past_their_lifetime_the_rows_say_stale_and_the_age(self):
        # worked example: the tags kept 30 days, now 31 days old; the combo index kept 7 days, now 9
        self.warm()
        self.age_saved("scryfall", "tags", 31)
        self.age_saved("spellbook", "variants", 9)
        self.new_run()
        result = self.warm("--offline")
        self.assertEqual(len(self.downloads), 2)                  # the first run's; --offline added none
        self.assertEqual([r["cache"] for r in result["fetched"][1:3]], ["stale", "stale"])
        self.assertIn("Commander Spellbook data is 9.0 days old (offline or the site failed)", result["warnings"])
        self.assertIn("Scryfall function tags data is 31.0 days old (offline or the site failed)", result["warnings"])


# ----------------------------------------------------------------------------- validate
class ValidateTests(CliCase):
    def test_the_arguments_reach_validate_run(self):
        result = self.run_cli("validate", "--bracket", "3")
        self.assertEqual(result.code, 0, result.err)
        self.validate.run.assert_called_once_with(3, commanders=None, limit=20, sweep=False, calibrate=False,
                                                  sources=config.SOURCES)

    def test_the_sources_flag_decides_which_real_decks_validate_may_read(self):
        # --sources is how the user turns Archidekt (held-out lists) and EDHTop16 (tournament decks) on or off
        self.run_cli("validate", "--bracket", "5", "--sources", "edhrec,edhtop16")
        self.assertEqual(self.validate.run.call_args.kwargs["sources"], ("edhrec", "edhtop16"))

    def test_commanders_are_checked_against_the_index_and_flattened(self):
        self.run_cli("validate", "--bracket", "4", "--commanders", "hazel of the rootbloom",
                     "Chatterfang, Squirrel General",
                     "--commanders", "Thrasios, Triton Hero", "--limit", "5", "--sweep", "--calibrate")
        self.validate.run.assert_called_once_with(
            4, commanders=["Hazel of the Rootbloom", "Chatterfang, Squirrel General", "Thrasios, Triton Hero"],
            limit=5, sweep=True, calibrate=True, sources=config.SOURCES)

    def test_an_unknown_commander_is_exit_one(self):
        result = self.run_cli("validate", "--bracket", "3", "--commanders", "Hazl of the Rootbloom")
        self.assertEqual(result.code, 1)
        self.assertIn("did you mean Hazel of the Rootbloom?", result.err)
        self.validate.run.assert_not_called()

    def test_the_result_is_completed_and_printed(self):
        result = self.run_json("validate", "--bracket", "3")
        self.assertEqual((result["command"], result["bracket"]), ("validate", 3))
        self.assertEqual((result["warnings"], result["sources"]), ([], {}))
        self.assertIn("Validation at Bracket 3: stub", self.run_cli("validate", "--bracket", "3").out)


# ----------------------------------------------------------------------------- output
class OutputTests(CliCase):
    def test_json_is_the_only_thing_on_stdout(self):
        result = self.run_cli("check", "--precon", "Test Precon", "--json")
        self.assertTrue(result.out.startswith('{\n  "schema": 1,'))
        json.loads(result.out)
        self.assertEqual(result.err, "")

    def test_every_json_result_has_schema_first_and_warnings_and_sources(self):
        for argv in (["themes"], ["check", "--precon", "Test Precon"], ["upgrade", "--precon", "Test Precon"],
                     ["build", "Hazel of the Rootbloom"], ["suggest", "--theme", "tokens"],
                     ["validate", "--bracket", "3"]):
            with self.subTest(command=argv[0]):
                body = self.run_json(*argv)
                self.assertEqual(list(body)[0], "schema")
                self.assertEqual(body["schema"], 1)
                self.assertIsInstance(body["warnings"], list)
                self.assertIsInstance(body["sources"], dict)

    def test_a_legacy_code_page_gets_question_marks_instead_of_a_crash(self):
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="ascii", errors="strict")
        with mock.patch.object(sys, "stdout", stream):
            cli._emit("Hazel → Bracket 3 — ok")
            stream.flush()
        self.assertEqual(raw.getvalue(), b"Hazel ? Bracket 3 ? ok\n")

    def test_a_closed_pipe_is_not_an_error(self):
        class Closed:
            encoding = "utf-8"

            def write(self, text):
                raise BrokenPipeError

            def fileno(self):
                return os.open(os.devnull, os.O_WRONLY)

        with mock.patch.object(sys, "stdout", Closed()), mock.patch.object(os, "dup2") as dup2:
            cli._emit("anything")
        dup2.assert_called_once()


if __name__ == "__main__":
    unittest.main()
