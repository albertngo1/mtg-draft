"""Tests for validate.py: the overlap and baseline arithmetic on worked examples, leave-one-out (the held-out entry
really is absent from what the build sees), the weight sweep and its restore, the Bracket 1-4 comparison with
Archidekt lists, the paths where a source is off, the rule rate, the upgrade check's distances, and the shape of
the result.

The builder (build.prepare / build / upgrade), the card index, the real-deck readers and the network are
replaced by stand-ins, so each test checks what validate.py itself decides. The world is tiny and hand-made:
validate_cards.json (the cards), validate_entries.json (six EDHTop16 entries for one commander, four of them
top-cut), validate_archidekt_decks.json (five Archidekt lists for Heliod) and validate_decklist.json (precons).
Every expected number below is worked out by hand in the comment beside it."""
import contextlib, io, json, os, sys, time, unittest
from unittest import mock
from mtgcommander import brackets, build, calibrate, carddb, cli, config, decklist, net, roles, score, validate
from mtgcommander.providers import edhtop16, spellbook

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
NOW = "2026-10-11T12:00:00Z"
INFO = {"fetched": NOW, "cache": "fresh"}
KINNAN, THRASIOS, TYMNA = "Kinnan, Bonder Prodigy", "Thrasios, Triton Hero", "Tymna the Weaver"
HELIOD = "Heliod, Sun-Crowned"
PAIR = f"{THRASIOS} / {TYMNA}"                     # how EDHTop16 names a partner pair
SOURCES = {"edhrec": {"fetched": NOW, "cache": "fresh", "age_days": 0.1}}
ROLES_OF = {"Sol Ring": {"ramp"}, "Mana Vault": {"ramp"}, "Arcane Signet": {"ramp"}, "Rhystic Study": {"draw"},
            "Swords to Plowshares": {"removal"}}
ALL_ROLES = dict.fromkeys(("land", "mdfc_land") + roles.ROLES + ("topend",), 0)


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


def sample_db():
    records = [carddb.card_record(obj) for obj in fixture("validate_cards.json")]
    return carddb.CardDB({r["name"]: r for r in records}, fetched=NOW, cache="fresh")


def counts(**over):
    """A roles.counts-shaped dict: zero everywhere unless given."""
    return dict(ALL_ROLES, **over)


class FakeBuilder:
    """Stands in for build.prepare, build.build and build.upgrade, and records every call.

    `picks` is the non-basic cards a build plays: a list, or a function of the (W_BRACKET[5], K_RESID) in force
    when prepare ran (so a sweep test can make the build better at one setting). `fail_at` raises RuntimeError
    for that pair of weights, the way a bug would. `upgrades` maps a precon name to (counts before, counts
    after, spent) for build.upgrade; any other precon ends nearer the targets for $10."""

    def __init__(self, picks=(), roles_built=None, evidence=None, check=None, upgrades=None, fail_at=None):
        self.picks, self.roles_built = picks, roles_built or counts()
        self.evidence = evidence or {"cards": {}}
        self.check = check or {"ok": True, "notes": []}
        self.upgrades, self.fail_at = upgrades or {}, fail_at
        self.prepared, self.built, self.upgraded = [], [], []

    def prepare(self, commanders, bracket, spec, db, **kw):
        weights = (score.W_BRACKET[5], score.K_RESID)
        if weights == self.fail_at:
            raise RuntimeError("a bug in the builder")
        call = dict(kw, commanders=list(commanders), bracket=bracket, spec=spec, weights=weights)
        self.prepared.append(call)
        return {"commanders": [db.resolve(c) or c for c in commanders], "bracket": bracket,
                "evidence": self.evidence, "sources": dict(SOURCES), "warnings": [], "call": call}

    def build(self, ctx, db, **kw):
        self.built.append(kw)
        picks = self.picks(ctx["call"]["weights"]) if callable(self.picks) else self.picks
        return {"cards": [{"name": n} for n in picks], "roles": dict(self.roles_built),
                "bracket_check": dict(self.check), "warnings": [], "sources": ctx["sources"]}

    def upgrade(self, ctx, deck, db, **kw):
        self.upgraded.append(dict(kw, deck=deck))
        before, after, spent = self.upgrades.get(deck["name"], (counts(ramp=5), counts(ramp=8), 10.0))
        targets = {"ramp": {"min": 8, "target": 10, "max": 13}, "topend": {"max": 8}}
        return {"roles_before": before, "roles_after": after, "targets": targets, "spent": spent,
                "swaps": [{}] * 3, "warnings": [], "sources": ctx["sources"]}


class Isolated(unittest.TestCase):
    """validate.run with every door closed: no network, no real card index, no real Archidekt or EDHTop16."""

    def setUp(self):
        self.db = sample_db()
        self.reads = []                                    # (EDHTop16 name, kwargs) for every entries read
        mock.patch.object(carddb, "load", return_value=self.db).start()
        for door in ("fetch_json", "request", "download"):
            mock.patch.object(net, door, side_effect=AssertionError(f"net.{door} must not run in a test")).start()
        mock.patch.object(validate, "read_tournament_entries", side_effect=self.entries).start()
        mock.patch.object(validate, "read_archidekt_decks",
                          side_effect=AssertionError("Archidekt must not be read in this test")).start()
        mock.patch.object(edhtop16, "top_commanders",
                          return_value=[{"name": PAIR, "entries": 900, "conversion": 0.3},
                                        {"name": KINNAN, "entries": 800, "conversion": 0.3}]).start()
        mock.patch.object(decklist, "_entries", return_value=[]).start()
        mock.patch.object(roles, "tag", side_effect=lambda names, db, **kw: {n: set(ROLES_OF.get(n, ()))
                                                                            for n in names}).start()
        mock.patch.object(validate, "_today", return_value="2026-10-11").start()
        self.addCleanup(mock.patch.stopall)
        self.weights = (dict(score.W_BRACKET), score.K_RESID)
        self.addCleanup(self.assert_weights_unchanged)

    def assert_weights_unchanged(self):
        self.assertEqual((score.W_BRACKET, score.K_RESID), self.weights)

    def entries(self, name, **kw):
        self.reads.append((name, kw))
        return fixture("validate_entries.json"), dict(INFO)

    def use(self, builder):
        """Route build.prepare / build / upgrade to `builder`; returns it."""
        mock.patch.object(build, "prepare", side_effect=builder.prepare).start()
        mock.patch.object(build, "build", side_effect=builder.build).start()
        mock.patch.object(build, "upgrade", side_effect=builder.upgrade).start()
        return builder


# ----------------------------------------------------------------------------- the arithmetic
class ArithmeticTests(Isolated):
    def test_non_basic_cards_leave_out_basics_commanders_and_names_the_index_lacks(self):
        names = ["sol ring", "Island", "Snow-Covered Island", KINNAN, "Command Tower", "Not A Real Card"]
        cards, unknown = validate.nonbasic_cards(self.db, names, skip={KINNAN})
        self.assertEqual(cards, {"Sol Ring", "Command Tower"})      # spelled any way; snow basics are basics
        self.assertEqual(unknown, 1)

    def test_overlap_is_the_share_of_the_held_out_decks_cards_the_other_deck_has(self):
        held = {"Sol Ring", "Mana Vault", "Rhystic Study", "Force of Will", "One-Off 1"}
        built = {"Sol Ring", "Mana Vault", "Rhystic Study", "Demonic Tutor"}
        self.assertEqual(validate.overlap(held, built), 3 / 5)       # 3 of the 5 held-out cards; its 4th is not counted
        self.assertEqual(validate.overlap(held, set()), 0.0)
        self.assertEqual(validate.overlap(held, held | {"extra"}), 1.0)

    def test_most_played_takes_the_most_played_and_breaks_ties_by_name(self):
        counts_ = {"Sol Ring": 5, "Mana Vault": 4, "Rhystic Study": 3, "Force of Will": 3, "Demonic Tutor": 3}
        self.assertEqual(validate.most_played(counts_, 2), {"Sol Ring", "Mana Vault"})
        self.assertEqual(validate.most_played(counts_, 4),
                         {"Sol Ring", "Mana Vault", "Demonic Tutor", "Force of Will"})
        self.assertEqual(validate.most_played(counts_, 99), set(counts_))
        self.assertEqual(validate.most_played(counts_, 0), set())

    def test_the_baseline_for_brackets_one_to_four_ranks_by_the_bracket_rate_then_the_all_bracket_rate(self):
        def st(decks):
            return {"decks": decks, "of": 100, "synergy": None}
        evidence = {"cards": {
            "Sol Ring": {"at": st(90), "all": st(80)},
            "Swords to Plowshares": {"at": st(80), "all": st(10)},
            "Rhystic Study": {"at": st(70), "all": None},
            "Mana Vault": {"at": None, "all": st(95)},                  # popular overall, not listed at the bracket
            "One-Off 1": {"at": None, "all": None},                     # on a theme page only: never a guess
            HELIOD: {"at": st(99), "all": st(99)}}}                     # the commander is not a card to guess
        self.assertEqual(validate.inclusion_ranking(evidence, 3, skip={HELIOD}),
                         {"Sol Ring", "Swords to Plowshares", "Rhystic Study"})
        # asked for more than it has evidence for, it stops rather than padding with cards nobody listed
        self.assertEqual(validate.inclusion_ranking(evidence, 9, skip={HELIOD}),
                         {"Sol Ring", "Swords to Plowshares", "Rhystic Study", "Mana Vault"})

    def test_roles_inside_the_middle_half_of_real_lists(self):
        # five real lists with 1 2 2 3 3 ramp: the 25th and 75th percentiles are 2 and 3
        decks = [counts(ramp=n) for n in (1, 2, 2, 3, 3)]
        self.assertEqual(validate.roles_inside_band(counts(ramp=2), decks, blue=True), (11, 11))
        # 4 ramp is outside [2, 3]; every other role (all 0 in every list) matches the build's 0
        self.assertEqual(validate.roles_inside_band(counts(ramp=4), decks, blue=True), (10, 11))
        # a commander without blue is not asked about counterspells: one role fewer compared
        self.assertEqual(validate.roles_inside_band(counts(ramp=4), decks, blue=False), (9, 10))

    def test_band_distance_adds_the_cards_outside_each_roles_band(self):
        targets = {"land": {"min": 35, "target": 37, "max": 39}, "ramp": {"min": 8, "target": 10, "max": 13},
                   "draw": {"min": 7, "target": 9, "max": 13}, "topend": {"max": 8}}
        have = {"land": 36, "ramp": 5, "draw": 15, "topend": 10}
        # land inside (0); ramp 3 short of 8; draw 2 over 13; top-end 2 over 8
        self.assertEqual(validate.band_distance(have, targets), 7)
        self.assertEqual(validate.band_distance({"land": 35, "ramp": 13, "draw": 7, "topend": 0}, targets), 0)
        self.assertEqual(validate.band_distance({}, targets), 35 + 8 + 7)     # a role the deck lacks counts as 0

    def test_the_spec_is_a_plain_build_with_the_brackets_own_keep_it_fun_default(self):
        self.assertEqual(validate.spec_for(5), {"themes": [], "playstyle": "value", "weight": 0, "keep_fun": False,
                                                "bracket": 5, "include": [], "exclude": [], "text": None})
        self.assertEqual([validate.spec_for(b)["keep_fun"] for b in range(1, 6)], [True, True, True, False, False])

    def test_the_tournament_weights_are_put_back_even_when_the_block_fails(self):
        before = (score.W_BRACKET[5], score.K_RESID)
        with validate.tournament_weights(2, 100):
            self.assertEqual((score.W_BRACKET[5], score.K_RESID), (2, 100))
        self.assertEqual((score.W_BRACKET[5], score.K_RESID), before)
        with self.assertRaises(ZeroDivisionError), validate.tournament_weights(0, 25):
            1 / 0
        self.assertEqual((score.W_BRACKET[5], score.K_RESID), before)


class BracketVerdictTests(Isolated):
    """The verdict reads brackets.check's own report, so these use the real check on a two-card list."""

    def report(self, bracket, cards, combos):
        return {"bracket_check": brackets.check([HELIOD], cards, bracket, self.db, combos=combos)}

    def test_a_list_within_the_limits_passes(self):
        result = self.report(3, ["Sol Ring"], {"included": [], "almost": []})
        self.assertIs(validate.bracket_verdict(result, 3), True)

    def test_a_game_changer_fails_bracket_one_whether_or_not_combos_were_checked(self):
        for combos in ({"included": [], "almost": []}, None):
            self.assertIs(validate.bracket_verdict(self.report(1, ["Rhystic Study"], combos), 1), False)

    def test_a_pass_whose_combo_rule_could_not_be_checked_is_unknown_where_combos_are_limited(self):
        result = self.report(3, ["Sol Ring"], None)                 # Commander Spellbook out of reach
        self.assertIn("Combos were not checked", " ".join(result["bracket_check"]["notes"]))
        self.assertIsNone(validate.bracket_verdict(result, 3))
        # Bracket 4 has no combo limit, so there is nothing to have missed
        self.assertIs(validate.bracket_verdict(self.report(4, ["Sol Ring"], None), 4), True)


# ----------------------------------------------------------------------------- reading real decks
class ReaderTests(unittest.TestCase):
    def test_the_tournament_reader_asks_for_the_cached_window_and_keeps_the_fetch_info(self):
        with mock.patch.object(edhtop16, "_collect", return_value=(["entry"], INFO, False)) as collect:
            found = validate.read_tournament_entries(PAIR, refresh=True, offline=False)
        self.assertEqual(found, (["entry"], INFO))
        collect.assert_called_once_with(PAIR, "ONE_YEAR", 150, True, False)

    def test_the_archidekt_reader_reports_its_oldest_download_and_worst_cache_state(self):
        infos = [{"fetched": "2026-10-10T00:00:00Z", "cache": "fresh"},
                 {"fetched": "2026-10-01T00:00:00Z", "cache": "stale"},
                 {"fetched": "2026-10-11T00:00:00Z", "cache": "network"}]
        with mock.patch.object(validate.archidekt, "_collect", return_value=(["deck"], infos)):
            self.assertEqual(validate.read_archidekt_decks([HELIOD], 3, 5),
                             (["deck"], {"fetched": "2026-10-01T00:00:00Z", "cache": "stale"}))
        with mock.patch.object(validate.archidekt, "_collect", return_value=([], [])):
            self.assertEqual(validate.read_archidekt_decks([HELIOD], 3, 5), ([], None))


class PoolTests(Isolated):
    def setUp(self):
        super().setUp()
        self.pool = validate.Pool(self.db, [KINNAN], fixture("validate_entries.json"), dict(INFO))

    def test_the_held_out_decks_are_the_newest_top_cut_entries(self):
        # e1, e2, e4 and e6 made the top cut; e3 and e5 did not
        self.assertEqual(self.pool.held_out(20), [0, 1, 3, 5])
        self.assertEqual(self.pool.held_out(2), [0, 1])

    def test_an_entry_of_only_basic_lands_and_unknown_cards_cannot_be_held_out(self):
        entries = fixture("validate_entries.json")
        entries[0]["cards"] = ["Island", "Forest", "No Such Card"]
        pool = validate.Pool(self.db, [KINNAN], entries, dict(INFO))
        self.assertEqual(pool.held_out(20), [1, 3, 5])
        self.assertEqual(pool.unknown, 1)

    def test_the_signal_leaves_out_exactly_the_held_out_entry(self):
        signal = self.pool.signal_without(1)                         # e2 held out
        self.assertEqual((signal["n"], signal["totals"]["entries"]), (5, 5))
        self.assertNotIn("One-Off 2", signal["cards"])               # e2's own card
        self.assertEqual(signal["cards"]["One-Off 1"]["entries"], 1)
        self.assertEqual(signal["cards"]["Sol Ring"]["entries"], 5)  # in all six entries, five without e2
        self.assertEqual((signal["fetched"], signal["cache"], signal["commanders"]), (NOW, "fresh", [KINNAN]))

    def test_the_baseline_counts_only_the_other_entries(self):
        # with e1 out, Sol Ring is played by 5 entries, Mana Vault by 4, and Demonic Tutor / Force of Will /
        # Rhystic Study by 3 each (ties by name: Demonic Tutor and Force of Will win the last two places)
        self.assertEqual(self.pool.baseline(0, 4), {"Sol Ring", "Mana Vault", "Demonic Tutor", "Force of Will"})
        # a card only the held-out deck played has no vote: One-Off 1 is absent however many guesses are asked
        self.assertNotIn("One-Off 1", self.pool.baseline(0, 99))
        self.assertIn("One-Off 2", self.pool.baseline(0, 99))


# ----------------------------------------------------------------------------- Bracket 5
BUILT = ["Sol Ring", "Mana Vault", "Rhystic Study", "Force of Will"]      # what the stand-in build plays


class LeaveOneOutTests(Isolated):
    def run5(self, builder=None, **kw):
        self.builder = self.use(builder or FakeBuilder(BUILT))
        return validate.run(5, [KINNAN], sources=("edhrec", "edhtop16"), **kw)

    def test_overlap_and_baseline_for_every_top_cut_deck(self):
        result = self.run5(limit=4)
        # held out in turn: e1, e2, e4, e6 (the newest four top-cut entries). The build plays Sol Ring, Mana
        # Vault, Rhystic Study and Force of Will, so its overlap with each deck's 5 non-basic cards is
        #   e1 {SR MV RS FoW One-Off1} 4/5   e2 {SR MV RS DT One-Off2} 3/5   e4 {SR RS FoW VT One-Off4} 3/5
        #   e6 {SR MV FoW DT One-Off6} 3/5                                          mean 2.6/4 = 0.65
        # The baseline guesses the same 4 cards from the other five entries' play counts:
        #   e1: SR MV DT FoW -> 3/5   e2: SR FoW MV RS -> 3/5   e4: MV SR DT FoW -> 2/5   e6: SR MV RS FoW -> 3/5
        #                                                                           mean 2.2/4 = 0.55
        self.assertEqual(result["commanders"], [{"name": KINNAN, "decks": 4, "overlap": 0.65, "baseline": 0.55}])
        self.assertEqual(result["overall"], {"overlap": 0.65, "baseline": 0.55, "n": 4})

    def test_the_limit_takes_the_newest_top_cut_decks_only(self):
        result = self.run5(limit=2)                              # e1 and e2: (0.8 + 0.6) / 2 and (0.6 + 0.6) / 2
        self.assertEqual(result["overall"], {"overlap": 0.7, "baseline": 0.6, "n": 2})

    def test_the_held_out_entry_is_absent_from_what_the_build_is_handed(self):
        self.run5(limit=4)
        signals = [call["tournament_signal"] for call in self.builder.prepared]
        self.assertEqual(len(signals), 4)
        for signal, held in zip(signals, ("One-Off 1", "One-Off 2", "One-Off 4", "One-Off 6")):
            self.assertEqual(signal["n"], 5)                         # six entries, one held out: n - 1
            self.assertNotIn(held, signal["cards"])                  # its own card is nowhere in the signal
            others = {"One-Off 1", "One-Off 2", "One-Off 3", "One-Off 4", "One-Off 5", "One-Off 6"} - {held}
            self.assertLessEqual(others, set(signal["cards"]))       # every other entry is still there

    def test_the_build_is_asked_for_a_plain_bracket_5_deck_without_prices_or_a_budget(self):
        self.run5(limit=1)
        call, = self.builder.prepared
        self.assertEqual((call["commanders"], call["bracket"], call["spec"]), ([KINNAN], 5, validate.spec_for(5)))
        self.assertEqual(self.builder.built, [{"combos_fn": None, "allow_combos": True, "prices": {}}])

    def test_builds_never_read_archidekt_even_when_it_is_among_the_sources(self):
        self.builder = self.use(FakeBuilder(BUILT))
        validate.run(5, [KINNAN], limit=1, sources=("edhrec", "archidekt", "edhtop16"))
        self.assertEqual(self.builder.prepared[0]["sources"], ("edhrec", "edhtop16"))

    def test_refresh_and_offline_reach_the_reads_and_the_build(self):
        self.builder = self.use(FakeBuilder(BUILT))
        validate.run(5, [KINNAN], limit=1, sources=("edhtop16",), refresh=True, offline=False)
        self.assertEqual(self.reads, [(KINNAN, {"refresh": True, "offline": False})])
        self.assertEqual((self.builder.prepared[0]["refresh"], self.builder.prepared[0]["offline"]), (True, False))

    def test_by_default_it_validates_the_most_played_tournament_commanders_and_splits_a_pair(self):
        self.builder = self.use(FakeBuilder(BUILT))
        result = validate.run(5, limit=1, sources=("edhtop16",))
        self.assertEqual([r["name"] for r in result["commanders"]], [PAIR, KINNAN])
        self.assertEqual([c["commanders"] for c in self.builder.prepared], [[THRASIOS, TYMNA], [KINNAN]])
        self.assertEqual(self.reads[0][0], PAIR)                    # EDHTop16 knows the pair under its joined name
        self.assertEqual(edhtop16.top_commanders.call_args.args, (validate.MIN_ENTRIES,))

    def test_a_default_commander_the_card_index_does_not_know_is_skipped_with_a_warning(self):
        edhtop16.top_commanders.return_value = [{"name": "Brand New Legend", "entries": 900, "conversion": 0.3},
                                                {"name": KINNAN, "entries": 800, "conversion": 0.3}]
        self.use(FakeBuilder(BUILT))
        result = validate.run(5, limit=1, sources=("edhtop16",))
        self.assertEqual([r["name"] for r in result["commanders"]], [KINNAN])
        self.assertTrue(any("Brand New Legend was skipped" in w for w in result["warnings"]))

    def test_a_commander_whose_entries_cannot_be_read_is_skipped_and_the_others_still_run(self):
        self.use(FakeBuilder(BUILT))

        def entries(name, **kw):
            if name == PAIR:
                raise net.FetchError("edhtop16", "https://edhtop16.com", "HTTP 500")
            return fixture("validate_entries.json"), dict(INFO)
        validate.read_tournament_entries.side_effect = entries
        result = validate.run(5, limit=1, sources=("edhtop16",))
        self.assertEqual([r["name"] for r in result["commanders"]], [KINNAN])
        self.assertTrue(any("EDHTop16 commander" in w and "HTTP 500" in w for w in result["warnings"]))

    def test_when_nothing_can_be_read_the_data_is_unavailable(self):
        self.use(FakeBuilder(BUILT))
        validate.read_tournament_entries.side_effect = net.FetchError("edhtop16", "u", "offline (--offline)")
        with self.assertRaises(net.FetchError) as caught:
            validate.run(5, limit=1, sources=("edhtop16",))
        self.assertIn("offline", str(caught.exception))

    def test_a_deck_whose_build_fails_to_fetch_is_skipped_with_a_warning(self):
        builder = self.use(FakeBuilder(BUILT))
        real_prepare = builder.prepare
        calls = []

        def prepare(*a, **kw):
            calls.append(1)
            if len(calls) == 2:
                raise net.FetchError("edhrec", "u", "HTTP 503")
            return real_prepare(*a, **kw)
        build.prepare.side_effect = prepare
        result = validate.run(5, [KINNAN], limit=4, sources=("edhtop16",))
        self.assertEqual(result["commanders"][0]["decks"], 3)
        self.assertTrue(any("a held-out deck was skipped" in w for w in result["warnings"]))

    def test_a_commander_with_no_top_cut_deck_is_named_in_a_warning(self):
        def entries(name, **kw):
            return [dict(e, topcut=False) for e in fixture("validate_entries.json")], dict(INFO)
        validate.read_tournament_entries.side_effect = entries
        self.use(FakeBuilder(BUILT))
        result = validate.run(5, [KINNAN], sources=("edhtop16",))
        self.assertEqual((result["commanders"], result["overall"]["n"]), ([], 0))
        self.assertIn(f"{KINNAN}: no top-cut deck among its 6 newest EDHTop16 entries.", result["warnings"])

    def test_names_the_card_index_lacks_are_reported_not_silently_dropped(self):
        def entries(name, **kw):
            data = fixture("validate_entries.json")
            data[0]["cards"].append("Mystery Card")
            return data, dict(INFO)
        validate.read_tournament_entries.side_effect = entries
        result = self.run5(limit=1)
        self.assertTrue(any("1 card name(s)" in w and "not in the card index" in w for w in result["warnings"]))

    def test_without_edhtop16_nothing_is_measured_and_the_warning_says_how_to_fix_it(self):
        builder = self.use(FakeBuilder(BUILT))
        result = validate.run(5, [KINNAN], sources=("edhrec", "archidekt"))
        self.assertEqual((builder.prepared, result["commanders"], result["bracket_ok_rate"]), ([], [], None))
        self.assertEqual(result["overall"], {"overlap": None, "baseline": None, "n": 0})
        self.assertTrue(any("EDHTop16 is not among the sources" in w for w in result["warnings"]))

    def test_bracket_5_has_no_role_bands_or_upgrade_check(self):
        result = self.run5(limit=1)
        self.assertEqual((result["roles_in_iqr"], result["upgrade_check"], result["calibration"]),
                         (None, None, None))


# ----------------------------------------------------------------------------- the weight sweep
class SweepTests(Isolated):
    GRID = {(w, k) for w in validate.SWEEP_WEIGHTS for k in validate.SWEEP_SHRINKS}

    def best_at_the_shipped_weights(self):
        """A build that finds the cards only at the shipped weights, so the sweep has something to rank."""
        shipped = (score.W_BRACKET[5], score.K_RESID)
        return FakeBuilder(lambda weights: BUILT if weights == shipped else ["Mana Vault"])

    def test_every_pair_of_weights_gets_a_row_with_its_mean_overlap(self):
        builder = self.use(self.best_at_the_shipped_weights())
        with mock.patch.object(validate, "SWEEP_LIMIT", 2):
            result = validate.run(5, [KINNAN], limit=2, sweep=True, sources=("edhtop16",))
        rows = {(r["w_bracket"], r["k_resid"]): r for r in result["sweep"]}
        self.assertEqual(set(rows), self.GRID)
        # the shipped pair finds all four cards: (4/5 + 3/5) / 2 = 0.7; any other plays only Mana Vault, 1/5 each
        for pair, row in rows.items():
            self.assertEqual((row["overlap"], row["decks"]), (0.7, 2) if pair == (1.0, 50) else (0.2, 2), pair)
        self.assertEqual(result["overall"]["overlap"], 0.7)          # the main pass runs at the shipped weights
        self.assertIn("W_BRACKET[5] = 1 and K_RESID = 50", result["method"])

    def test_weight_zero_is_built_once_because_the_shrinkage_only_scales_the_residual(self):
        builder = self.use(FakeBuilder(BUILT))
        with mock.patch.object(validate, "SWEEP_LIMIT", 1):
            result = validate.run(5, [KINNAN], limit=1, sweep=True, sources=("edhtop16",))
        seen = [call["weights"] for call in builder.prepared]
        self.assertEqual([w for w in seen if w[0] == 0], [(0, 25)])    # one build for the whole W = 0 row
        self.assertEqual(len(seen), 1 + 1 + 9)                         # main pass, the W = 0 cell, nine other cells
        zero = [r["overlap"] for r in result["sweep"] if r["w_bracket"] == 0]
        self.assertEqual(len(zero), 3)
        self.assertEqual(len(set(zero)), 1)

    def test_only_the_first_few_held_out_decks_of_each_commander_are_swept(self):
        builder = self.use(FakeBuilder(BUILT))
        with mock.patch.object(validate, "SWEEP_LIMIT", 3):
            result = validate.run(5, [KINNAN], limit=4, sweep=True, sources=("edhtop16",))
        self.assertEqual(result["commanders"][0]["decks"], 4)          # the main pass used all four
        self.assertEqual({r["decks"] for r in result["sweep"]}, {3})

    def test_the_weights_are_back_where_they_were_after_a_sweep(self):
        self.use(FakeBuilder(BUILT))
        validate.run(5, [KINNAN], limit=1, sweep=True, sources=("edhtop16",))
        self.assert_weights_unchanged()

    def test_the_weights_are_back_where_they_were_when_a_build_blows_up_mid_sweep(self):
        self.use(FakeBuilder(BUILT, fail_at=(0.5, 50)))
        with self.assertRaises(RuntimeError):
            validate.run(5, [KINNAN], limit=1, sweep=True, sources=("edhtop16",))
        self.assert_weights_unchanged()                                # also checked again in cleanup

    def test_no_sweep_unless_asked(self):
        self.use(FakeBuilder(BUILT))
        self.assertIsNone(validate.run(5, [KINNAN], limit=1, sources=("edhtop16",))["sweep"])

    def test_below_bracket_5_a_sweep_request_is_declined_with_a_warning(self):
        self.use(FakeBuilder(BUILT))
        result = validate.run(4, [HELIOD], sweep=True, sources=("edhrec",))
        self.assertIsNone(result["sweep"])
        self.assertTrue(any("sweep runs at Bracket 5 only" in w for w in result["warnings"]))


# ----------------------------------------------------------------------------- Brackets 1-4
def rated(decks):
    return {"decks": decks, "of": 100, "synergy": None}


EVIDENCE = {"cards": {                      # what the sources list at the bracket (the baseline's only input)
    "Sol Ring": {"at": rated(90), "all": rated(80)},
    "Swords to Plowshares": {"at": rated(80), "all": rated(10)},
    "Rhystic Study": {"at": rated(70), "all": None},
    "Arcane Signet": {"at": rated(60), "all": None},
    "Command Tower": {"at": rated(50), "all": None},
    "Mana Vault": {"at": None, "all": rated(95)},
    HELIOD: {"at": rated(99), "all": rated(99)}}}
CASUAL_BUILT = ["Sol Ring", "Arcane Signet", "Command Tower"]
# the build's role counts against five real lists whose lands are all 95 (their 4 nonland cards recounted as
# 99 - 4), ramp 1 2 2 3 3, draw 0 0 1 1 1, removal 0 0 1 1 1 and nothing else: only the build's 2 draw cards
# (the lists' middle half is 0 to 1) lie outside, so 9 of the 10 roles compared for a commander without blue
CASUAL_ROLES = counts(land=95, ramp=2, draw=2, removal=1)


class CasualTests(Isolated):
    def setUp(self):
        super().setUp()
        self.builder = self.use(FakeBuilder(CASUAL_BUILT, CASUAL_ROLES, EVIDENCE))
        self.lists(fixture("validate_archidekt_decks.json"))

    def lists(self, decks):
        """What the Archidekt reader returns from now on."""
        validate.read_archidekt_decks.side_effect = lambda *a, **kw: (decks, dict(INFO))

    def run4(self, **kw):
        return validate.run(4, [HELIOD], limit=5, sources=("edhrec", "archidekt"), **kw)

    def test_overlap_and_baseline_against_the_real_lists_at_the_bracket(self):
        result = self.run4()
        # the five lists hold (non-basic) SR AS RS StP CT / SR AS MV RS CT / SR RS StP CT O1 / SR AS MV CT O2 /
        # SR AS StP CT O3. The build plays SR AS CT: 3/5 3/5 2/5 3/5 3/5 -> 0.56. The baseline guesses the same
        # number of cards the evidence lists most at the bracket, SR StP RS (never the commander, never
        # Mana Vault, which is listed only across brackets): 3/5 2/5 3/5 1/5 2/5 -> 0.44.
        self.assertEqual(result["commanders"],
                         [{"name": HELIOD, "decks": 5, "overlap": 0.56, "baseline": 0.44, "roles_in_iqr": 0.9}])
        self.assertEqual(result["overall"], {"overlap": 0.56, "baseline": 0.44, "n": 5})

    def test_the_build_is_made_once_per_commander_from_edhrec_without_archidekt(self):
        self.run4()
        call, = self.builder.prepared
        self.assertEqual((call["commanders"], call["bracket"], call["sources"]), ([HELIOD], 4, ("edhrec",)))
        self.assertEqual(call["spec"], validate.spec_for(4))
        self.assertEqual(self.builder.built, [{"combos_fn": spellbook.find_combos, "allow_combos": False,
                                               "prices": {}}])

    def test_role_counts_are_compared_with_the_middle_half_of_the_lists(self):
        result = self.run4()
        self.assertEqual(result["roles_in_iqr"], 0.9)              # 9 of the 10 roles compared (no counterspells)
        self.assertEqual(result["bracket_ok_rate"], 1.0)

    def test_too_few_lists_leave_the_role_bands_out_with_a_warning(self):
        self.lists(fixture("validate_archidekt_decks.json")[:3])
        result = self.run4()
        self.assertEqual((result["roles_in_iqr"], result["commanders"][0]["roles_in_iqr"]), (None, None))
        self.assertEqual(result["commanders"][0]["decks"], 3)
        self.assertTrue(any("only 3 Archidekt lists (under 5)" in w for w in result["warnings"]))

    def test_the_archidekt_lists_are_asked_for_at_the_bracket_with_the_limit(self):
        self.run4(refresh=True)
        validate.read_archidekt_decks.assert_called_once_with([HELIOD], 4, 5, refresh=True, offline=None)

    def test_a_commander_with_no_lists_at_the_bracket_gets_a_warning_and_empty_numbers(self):
        validate.read_archidekt_decks.side_effect = lambda *a, **kw: ([], None)
        result = self.run4()
        self.assertEqual(result["commanders"][0], {"name": HELIOD, "decks": 0, "overlap": None, "baseline": None,
                                                   "roles_in_iqr": None})
        self.assertIn(f"No complete Archidekt Bracket 4 deck was found for {HELIOD}.", result["warnings"])

    def test_archidekt_failing_keeps_the_commanders_rule_check(self):
        validate.read_archidekt_decks.side_effect = net.FetchError("archidekt", "u", "HTTP 500")
        result = self.run4()
        self.assertEqual((result["commanders"][0]["decks"], result["bracket_ok_rate"]), (0, 1.0))
        self.assertTrue(any("Archidekt lists for" in w and "HTTP 500" in w for w in result["warnings"]))

    def test_without_a_commander_given_six_popular_ones_are_built(self):
        result = validate.run(4, limit=5, sources=("edhrec", "archidekt"))
        self.assertEqual([r["name"] for r in result["commanders"]], list(validate.VALIDATION_COMMANDERS))
        self.assertEqual(len(validate.VALIDATION_COMMANDERS), 6)
        self.assertFalse(set(validate.VALIDATION_COMMANDERS) & set(calibrate.ARCHIDEKT_COMMANDERS))

    def test_the_method_says_what_edhrec_cannot_do(self):
        method = self.run4()["method"]
        self.assertIn("EDHREC's numbers cannot exclude one held-out list", method)
        self.assertIn("never read Archidekt", method)


class NoHeldOutSourceTests(Isolated):
    def test_without_archidekt_overlap_is_empty_and_the_warning_says_why(self):
        builder = self.use(FakeBuilder(CASUAL_BUILT, CASUAL_ROLES, EVIDENCE))
        result = validate.run(4, [HELIOD], sources=("edhrec", "edhtop16"))        # Archidekt would raise if read
        self.assertEqual(result["commanders"], [{"name": HELIOD, "decks": 0, "overlap": None, "baseline": None,
                                                 "roles_in_iqr": None}])
        self.assertEqual(result["overall"], {"overlap": None, "baseline": None, "n": 0})
        self.assertIsNone(result["roles_in_iqr"])
        warning, = [w for w in result["warnings"] if "Archidekt is not among the sources" in w]
        self.assertIn("only Archidekt has them", warning)
        self.assertEqual(len(builder.prepared), 1)                          # the rule check still built the deck
        self.assertEqual(result["bracket_ok_rate"], 1.0)
        self.assertIn("overlap was not measured", result["method"])

    def test_with_no_deck_builder_source_at_all_the_rules_are_still_checked(self):
        builder = self.use(FakeBuilder(CASUAL_BUILT, CASUAL_ROLES, EVIDENCE))
        result = validate.run(2, [HELIOD], sources=("edhtop16",))
        self.assertEqual(builder.prepared[0]["sources"], ("edhtop16",))
        self.assertEqual((result["overall"]["overlap"], result["bracket_ok_rate"]), (None, 1.0))

    def test_the_rate_counts_builds_that_break_a_rule_and_leaves_out_unchecked_ones(self):
        failing = {"ok": False, "notes": []}
        self.use(FakeBuilder(CASUAL_BUILT, check=failing))
        result = validate.run(2, [HELIOD, KINNAN], sources=("edhtop16",))
        self.assertEqual(result["bracket_ok_rate"], 0.0)

        unchecked = {"ok": True, "notes": ["Combos were not checked (no Commander Spellbook data), so the estimate "
                                           "ignores them."]}
        self.use(FakeBuilder(CASUAL_BUILT, check=unchecked))
        result = validate.run(2, [HELIOD, KINNAN], sources=("edhtop16",))
        self.assertIsNone(result["bracket_ok_rate"])
        self.assertTrue(any("unreachable for 2 of 2 builds" in w for w in result["warnings"]))

    def test_a_commander_whose_build_cannot_be_made_is_skipped_and_if_none_can_the_data_is_unavailable(self):
        builder = self.use(FakeBuilder(CASUAL_BUILT))
        real = builder.prepare

        def prepare(commanders, *a, **kw):
            if commanders == [HELIOD]:
                raise net.FetchError("edhrec", "u", "HTTP 503")
            return real(commanders, *a, **kw)
        build.prepare.side_effect = prepare
        result = validate.run(2, [HELIOD, KINNAN], sources=("edhrec",))
        self.assertEqual([r["name"] for r in result["commanders"]], [KINNAN])
        build.prepare.side_effect = net.FetchError("edhrec", "u", "HTTP 503")
        with self.assertRaises(net.FetchError):
            validate.run(2, [HELIOD], sources=("edhrec",))


# ----------------------------------------------------------------------------- the upgrade check
class UpgradeCheckTests(Isolated):
    def setUp(self):
        super().setUp()
        decklist._entries.return_value = fixture("validate_decklist.json")
        self.asked = []

        def precon(name, **kw):
            self.asked.append(name)
            return {"name": name, "code": "TST", "file": "x", "release": "2026-01-01", "commanders": [HELIOD],
                    "cards": [(1, "Sol Ring"), (1, "Arcane Signet"), (1, "Swords to Plowshares")],
                    "fetched": NOW, "url": "https://mtgjson.com/api/v5/decks/x.json"}
        mock.patch.object(decklist, "precon", side_effect=precon).start()

    def check(self, builder=None, **kw):
        self.builder = self.use(builder or FakeBuilder(CASUAL_BUILT))
        return validate.run(3, [HELIOD], sources=("edhrec",), **kw)["upgrade_check"]

    def test_it_upgrades_the_ten_newest_precons_skipping_twins_and_unreleased_decks(self):
        check = self.check()
        # twelve released decks are listed; the Collector's Edition of the newest, a deck released in 2027 and an
        # older printing of "Precon 05" are not decks to upgrade
        self.assertEqual(self.asked, [f"Precon {n:02d}" for n in range(1, 11)])
        self.assertEqual([r["precon"] for r in check["rows"]], self.asked)
        self.assertEqual((check["bracket"], check["budget"], check["precons"]), (3, 50.0, 10))

    def test_each_upgrade_gets_the_bracket_3_budget_and_the_precons_own_cards(self):
        self.check()
        first = self.builder.upgraded[0]
        self.assertEqual((first["budget"], first["combos_fn"]), (50.0, spellbook.find_combos))
        self.assertEqual(first["deck"]["commanders"], [HELIOD])
        self.assertEqual(first["deck"]["cards"],
                         [(1, "Sol Ring"), (1, "Arcane Signet"), (1, "Swords to Plowshares")])
        prepared = self.builder.prepared[1]                              # [0] is Heliod's own rule-check build
        self.assertEqual((prepared["bracket"], prepared["deck_cards"]),
                         (3, ["Sol Ring", "Arcane Signet", "Swords to Plowshares"]))

    def test_the_share_that_moved_closer_to_the_role_bands(self):
        # targets: ramp 8-13, top-end at most 8. Before/after band distance:
        better = (counts(ramp=5, topend=9), counts(ramp=8, topend=8))        # 3 + 1 = 4 -> 0: closer
        same = (counts(ramp=6), counts(ramp=6))                               # 2 -> 2
        worse = (counts(ramp=7), counts(ramp=4))                              # 1 -> 4: farther
        inside = (counts(ramp=9), counts(ramp=9))                             # 0 -> 0: nothing to improve
        builder = FakeBuilder(CASUAL_BUILT, upgrades={
            "Precon 01": better + (20.0,), "Precon 02": same + (20.0,), "Precon 03": worse + (20.0,),
            "Precon 04": inside + (0.0,)})
        check = self.check(builder)
        rows = {r["precon"]: r for r in check["rows"]}
        self.assertEqual([rows[f"Precon 0{n}"]["gap_before"] for n in (1, 2, 3, 4)], [4, 2, 1, 0])
        self.assertEqual([rows[f"Precon 0{n}"]["gap_after"] for n in (1, 2, 3, 4)], [0, 2, 4, 0])
        # the six unscripted decks go from 3 short to 0: closer; so closer = 1 + 6, same = 2, farther = 1
        self.assertEqual((check["closer"], check["same"], check["farther"]), (7, 2, 1))
        self.assertEqual(check["share_closer"], 0.7)

    def test_a_spend_over_the_budget_is_named_but_a_rounding_cent_is_not(self):
        builder = FakeBuilder(CASUAL_BUILT, upgrades={
            "Precon 01": (counts(ramp=5), counts(ramp=8), 50.0),
            "Precon 02": (counts(ramp=5), counts(ramp=8), 50.004),
            "Precon 03": (counts(ramp=5), counts(ramp=8), 50.01)})
        check = self.check(builder)
        self.assertEqual((check["within_budget"], check["over_budget"]), (False, ["Precon 03"]))
        self.assertTrue(self.check()["within_budget"])                       # nothing over $50 in the default

    def test_a_precon_that_cannot_be_read_is_skipped_and_the_next_older_one_takes_its_place(self):
        real = decklist.precon.side_effect

        def precon(name, **kw):
            if name == "Precon 02":
                raise net.FetchError("mtgjson", "u", "HTTP 500")
            return real(name, **kw)
        decklist.precon.side_effect = precon
        check = self.check()
        self.assertEqual(check["precons"], 10)
        self.assertNotIn("Precon 02", [r["precon"] for r in check["rows"]])
        self.assertIn("Precon 11", [r["precon"] for r in check["rows"]])

    def test_the_check_gives_up_after_a_few_unreadable_precons(self):
        decklist.precon.side_effect = net.FetchError("mtgjson", "u", "HTTP 500")
        self.assertIsNone(self.check())
        self.assertEqual(len(self.asked), 0)                                  # the stand-in raised before recording
        self.assertEqual(decklist.precon.call_count, validate.UPGRADE_FAILURES)

    def test_only_bracket_3_runs_the_upgrade_check(self):
        self.use(FakeBuilder(CASUAL_BUILT))
        for bracket in (2, 4):
            self.assertIsNone(validate.run(bracket, [HELIOD], sources=("edhrec",))["upgrade_check"])
        self.assertEqual(self.asked, [])

    def test_the_precon_commander_the_index_does_not_know_is_skipped_with_a_warning(self):
        real = decklist.precon.side_effect

        def precon(name, **kw):
            deck = real(name, **kw)
            return dict(deck, commanders=["Nobody Special"]) if name == "Precon 01" else deck
        decklist.precon.side_effect = precon
        self.builder = self.use(FakeBuilder(CASUAL_BUILT))
        result = validate.run(3, [HELIOD], sources=("edhrec",))
        self.assertNotIn("Precon 01", [r["precon"] for r in result["upgrade_check"]["rows"]])
        self.assertTrue(any("Precon 01 was skipped in the upgrade check" in w for w in result["warnings"]))


# ----------------------------------------------------------------------------- the result
class ResultTests(Isolated):
    def test_the_result_has_every_key_of_the_contract_and_is_json(self):
        self.use(FakeBuilder(BUILT))
        result = validate.run(5, [KINNAN], limit=2, sources=("edhtop16",))
        self.assertEqual(list(result), ["command", "bracket", "method", "commanders", "overall", "roles_in_iqr",
                                        "bracket_ok_rate", "sweep", "calibration", "upgrade_check", "warnings",
                                        "sources"])
        self.assertEqual((result["command"], result["bracket"], result["bracket_ok_rate"]), ("validate", 5, 1.0))
        json.dumps(result)

    def test_sources_carry_their_dates_and_an_expired_copy_is_warned_about(self):
        self.use(FakeBuilder(BUILT))
        validate.read_tournament_entries.side_effect = lambda name, **kw: (
            fixture("validate_entries.json"), {"fetched": "2026-09-01T00:00:00Z", "cache": "stale"})
        result = validate.run(5, [KINNAN], limit=1, sources=("edhrec", "edhtop16"))
        self.assertEqual(result["sources"]["edhtop16"]["cache"], "stale")
        self.assertEqual(result["sources"]["edhtop16"]["fetched"], "2026-09-01T00:00:00Z")
        self.assertIsNotNone(result["sources"]["edhtop16"]["age_days"])
        self.assertEqual(result["sources"]["edhrec"]["cache"], "fresh")        # from the builds' own report
        stale = "days old (offline or the site failed)"
        self.assertTrue(any(w.startswith("EDHTop16 data is ") and w.endswith(stale) for w in result["warnings"]))

    def test_a_precon_list_with_no_cache_state_is_dated_from_its_age(self):
        job = validate._Run(self.db, (), None, None)
        job.note_source("mtgjson", "2000-01-01T00:00:00Z")
        job.note_source("scryfall", net.iso(time.time()))
        self.assertEqual((job.dates["mtgjson"]["cache"], job.dates["scryfall"]["cache"]), ("stale", "network"))

    def test_the_oldest_fetch_and_the_worst_cache_state_win(self):
        job = validate._Run(self.db, (), None, None)
        job.note_source("edhrec", "2026-10-05T00:00:00Z", "stale")
        job.note_source("edhrec", "2026-10-01T00:00:00Z", "network")
        job.note_source("edhrec", "2026-10-09T00:00:00Z", "fresh")
        self.assertEqual(job.dates["edhrec"], {"fetched": "2026-10-01T00:00:00Z", "cache": "stale"})

    def test_sources_may_be_a_comma_separated_string_as_calibrate_accepts(self):
        builder = self.use(FakeBuilder(BUILT))
        validate.run(5, [KINNAN], limit=1, sources="edhrec, archidekt,edhtop16")
        self.assertEqual(builder.prepared[0]["sources"], ("edhrec", "edhtop16"))

    def test_an_out_of_range_bracket_fails_before_anything_is_downloaded(self):
        with self.assertRaises(ValueError):
            validate.run(6)

    def test_a_calibration_request_refits_the_targets_after_the_validation_and_reports_it(self):
        self.use(FakeBuilder(BUILT))
        report = {"as_of": "2026-10-11", "brackets": {5: {"land": [26, 29, 32]}}, "changes": [], "warnings": []}
        with mock.patch.object(calibrate, "run", return_value=report) as refit:
            result = validate.run(5, [KINNAN], limit=1, calibrate=True, sources=("edhtop16",), refresh=True)
        self.assertIs(result["calibration"], report)
        _, kw = refit.call_args
        self.assertEqual((kw["sources"], kw["write"], kw["refresh"], kw["offline"]),
                         (("edhtop16",), True, True, None))
        self.assertEqual(result["overall"]["n"], 1)                             # the validation still ran

    def test_the_calibrations_own_warnings_join_the_runs(self):
        self.use(FakeBuilder(BUILT))
        report = {"brackets": {}, "changes": [], "warnings": ["Bracket 5: 4 of 120 decks have blue"]}
        with mock.patch.object(calibrate, "run", return_value=report):
            result = validate.run(5, [KINNAN], limit=1, calibrate=True, sources=("edhtop16",))
        self.assertIn("Calibration: Bracket 5: 4 of 120 decks have blue", result["warnings"])

    def test_no_calibration_unless_asked(self):
        self.use(FakeBuilder(BUILT))
        with mock.patch.object(calibrate, "run") as refit:
            validate.run(5, [KINNAN], limit=1, sources=("edhtop16",))
        refit.assert_not_called()

    def test_a_failed_calibration_is_a_warning_not_the_end_of_the_run(self):
        self.use(FakeBuilder(BUILT))
        with mock.patch.object(calibrate, "run", side_effect=calibrate.NotEnoughData("Bracket 5 needs 10 decks")):
            result = validate.run(5, [KINNAN], limit=1, calibrate=True, sources=("edhtop16",))
        self.assertIsNone(result["calibration"])
        self.assertIn("Calibration failed: Bracket 5 needs 10 decks", result["warnings"])


class ProgressTests(Isolated):
    def run_with_stderr(self, tty):
        stream = io.StringIO()
        stream.isatty = lambda: tty
        self.use(FakeBuilder(BUILT))
        with mock.patch.object(sys, "stderr", stream):
            validate.run(5, [KINNAN], limit=2, sources=("edhtop16",))
        return stream.getvalue()

    def test_progress_lines_appear_only_on_a_terminal(self):
        self.assertEqual(self.run_with_stderr(tty=False), "")
        shown = self.run_with_stderr(tty=True)
        self.assertIn(f"Bracket 5, {KINNAN}: deck 2 of 2 ...", shown)


class CommandLineTests(Isolated):
    """The real engine behind the real command line (only the builder and the readers are stand-ins)."""

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.run(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_json_output_has_the_contract_keys_and_the_schema(self):
        self.use(FakeBuilder(BUILT))
        code, out, err = self.run_cli("validate", "--bracket", "5", "--commanders", KINNAN, "--limit", "2",
                                      "--sources", "edhtop16", "--json")
        self.assertEqual((code, err), (0, ""))
        body = json.loads(out)
        self.assertEqual(list(body)[:2], ["schema", "command"])
        self.assertEqual(body["overall"], {"overlap": 0.7, "baseline": 0.6, "n": 2})
        self.assertIn("edhtop16", body["sources"])

    def test_the_text_report_prints_the_table_and_the_overall_line(self):
        self.use(FakeBuilder(BUILT))
        code, out, _ = self.run_cli("validate", "--bracket", "5", "--commanders", KINNAN, "--limit", "4",
                                    "--sources", "edhtop16")
        self.assertEqual(code, 0)
        self.assertIn("Validation at Bracket 5: leave-one-out on EDHTop16 top-cut decks", out)
        self.assertIn("overlap 65% against a baseline of 55% (n = 4)", out)
        self.assertTrue(all(len(line) <= 100 for line in out.splitlines()), out)

    def test_the_sources_flag_reaches_the_engine_and_archidekt_stays_off_by_that_flag(self):
        self.use(FakeBuilder(CASUAL_BUILT, CASUAL_ROLES, EVIDENCE))
        code, out, _ = self.run_cli("validate", "--bracket", "4", "--commanders", HELIOD, "--sources", "edhrec")
        self.assertEqual(code, 0)
        self.assertIn("Archidekt is not among the sources", " ".join(out.split()))     # the report wraps lines


if __name__ == "__main__":
    unittest.main()
