"""Tests for calibrate.py: the percentile arithmetic, the land recount for lists that name each basic land
once, the blue-only counterspell sample, interpolation and the labels, the file format (read back through
roles.targets), the choice of precons, and whole runs with every source replaced by hand-made decks. Nothing
here touches the network."""
import contextlib, datetime, io, json, os, random, shutil, statistics, tempfile, types, unittest
from fractions import Fraction
from unittest import mock
from mtgcommander import calibrate, carddb, config, decklist, net, roles
from mtgcommander.providers import archidekt, edhtop16

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
TODAY = datetime.date(2026, 10, 11)
KINNAN, HAZEL = "Kinnan, Bonder Prodigy", "Hazel of the Rootbloom"
TYMNA, THRASIOS = "Tymna the Weaver", "Thrasios, Triton Hero"
PAIR = f"{THRASIOS} / {TYMNA}"                  # how EDHTop16 names a partner pair
ALL_ROLES = ("land",) + roles.ROLES


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


def card(name, type_line="Sorcery", cmc=3.0):
    """A minimal Scryfall card object."""
    return {"object": "card", "oracle_id": "id-" + name, "name": name, "layout": "normal",
            "type_line": type_line, "oracle_text": "", "cmc": cmc, "color_identity": [], "keywords": [],
            "legalities": {"commander": "legal"}}


def sample_db():
    """The named cards of calibrate_cards.json plus pools of generated ones: 'Ramp 001' ... one pool per role,
    'Filler 001' ... (no role) and 'Topend 001' ... (mana value 7, no role)."""
    objs = fixture("calibrate_cards.json")
    objs += [card(f"{kind.title()} {i:03d}") for kind in roles.ROLES + ("filler",) for i in range(1, 101)]
    objs += [card(f"Topend {i:03d}", cmc=7.0) for i in range(1, 11)]
    return carddb.CardDB({rec["name"]: rec for rec in map(carddb.card_record, objs)})


def spells(**counts):
    """Names of generated cards: spells(ramp=2, filler=1) -> ['Ramp 001', 'Ramp 002', 'Filler 001']."""
    return [f"{kind.title()} {i:03d}" for kind, n in counts.items() for i in range(1, n + 1)]


NAMED_ROLES = {"Sol Ring": {"ramp"}, "Rhystic Study": {"draw"}, "Swords to Plowshares": {"removal"},
               "Counterspell": {"counter"}, "Craterhoof Behemoth": {"finisher"}}


def fake_tag(names, db, **kw):
    """roles.tag for the cards above: a generated card has the role its name begins with."""
    return {n: NAMED_ROLES.get(n) or ({n.split()[0].lower()} & set(roles.ROLES)) for n in names}


def deck_row(blue=True, **counts):
    """One deck as summarize() reads it: role counts (zero unless given) and whether the commander has
    blue."""
    return {"counts": {**dict.fromkeys(ALL_ROLES + ("mdfc_land", "topend"), 0), **counts}, "blue": blue}


def numbers(topend=0, **per_role):
    """One bracket's numbers: every role [0, 0, 0] unless given."""
    out = {role: [0, 0, 0] for role in ALL_ROLES}
    out.update({role: list(v) for role, v in per_role.items()})
    out["topend"] = topend
    return out


# ----------------------------------------------------------------------------- the arithmetic
class PercentileTests(unittest.TestCase):
    def test_linear_interpolation_between_ranked_values(self):
        xs = [1, 2, 3, 4, 5]
        self.assertEqual([calibrate.percentile(xs, p) for p in (0, 25, 50, 100)], [1, 2, 3, 5])
        self.assertEqual(calibrate.percentile(xs, 90), Fraction(23, 5))        # 4 + 0.6 of the way to 5
        self.assertEqual(calibrate.percentile([1, 2, 3, 4], 50), Fraction(5, 2))
        self.assertEqual(calibrate.percentile([0, 10], 25), Fraction(5, 2))

    def test_order_of_the_input_does_not_matter_and_one_value_is_every_percentile(self):
        self.assertEqual(calibrate.percentile([5, 1, 3], 50), 3)
        self.assertEqual([calibrate.percentile([7], p) for p in (10, 50, 90)], [7, 7, 7])

    def test_no_values_is_an_error_not_a_zero(self):
        with self.assertRaises(ValueError):
            calibrate.percentile([], 50)

    def test_agrees_with_the_standard_librarys_inclusive_quantiles(self):
        rng = random.Random(11)
        for _ in range(40):
            data = [rng.randint(0, 40) for _ in range(rng.randint(5, 60))]
            cuts = statistics.quantiles(data, n=100, method="inclusive")
            for p in (10, 25, 50, 75, 90):
                self.assertAlmostEqual(float(calibrate.percentile(data, p)), cuts[p - 1], places=9)

    def test_halves_round_up_not_to_the_even_number(self):
        cases = [(Fraction(1, 2), 1), (Fraction(3, 2), 2), (Fraction(5, 2), 3), (Fraction(7, 3), 2),
                 (Fraction(17, 3), 6), (4, 4), (2.5, 3), (11.5, 12)]
        for x, expected in cases:
            self.assertEqual(calibrate.round_half_up(x), expected, x)
        self.assertEqual(round(2.5), 2)      # the behavior this replaces


class SummarizeTests(unittest.TestCase):
    def rows(self):
        ramp = [8, 9, 10, 10, 11, 12, 12, 13, 14, 15, 16]
        land = [33, 34, 35, 36, 36, 37, 37, 37, 38, 38, 40]
        topend = [2, 3, 3, 4, 5, 5, 6, 7, 8, 9, 12]
        return [deck_row(ramp=r, land=l, topend=t) for r, l, t in zip(ramp, land, topend)]

    def test_min_target_max_are_the_25th_percentile_median_and_90th_percentile(self):
        # eleven decks: positions 2.5, 5 and 9 of 0..10
        self.assertEqual(calibrate.summarize(self.rows())["ramp"], [10, 12, 15])

    def test_lands_use_the_10th_percentile_for_their_minimum(self):
        self.assertEqual(calibrate.summarize(self.rows())["land"], [34, 37, 38])

    def test_topend_is_one_number_the_75th_percentile(self):
        # position 7.5 sits between 7 and 8: the half goes up
        self.assertEqual(calibrate.summarize(self.rows())["topend"], 8)

    def test_a_target_between_two_counts_rounds_up(self):
        rows = [deck_row(ramp=r) for r in (11, 12, 13, 14)]
        self.assertEqual(calibrate.summarize(rows)["ramp"], [12, 13, 14])     # median 12.5

    def test_counterspell_numbers_come_only_from_decks_with_blue(self):
        rows = ([deck_row(blue=True, counter=c, ramp=i) for i, c in enumerate((2, 4, 6, 8))]
                + [deck_row(blue=False, counter=0, ramp=4 + i) for i in range(6)])
        out = calibrate.summarize(rows)
        self.assertEqual(out["counter"], [4, 5, 7])          # over 2, 4, 6, 8: 3.5, 5, 7.4
        self.assertEqual(out["ramp"], [2, 5, 8])             # every other role counts all ten decks (0..9)

    def test_no_blue_deck_means_zero_counterspells_not_an_error(self):
        rows = [deck_row(blue=False, counter=3) for _ in range(5)]
        self.assertEqual(calibrate.summarize(rows)["counter"], [0, 0, 0])

    def test_every_role_comes_back_in_the_files_order_and_stays_min_target_max(self):
        rng = random.Random(5)
        for _ in range(30):
            counted = ALL_ROLES + ("topend",)
            rows = [deck_row(blue=rng.random() < 0.5, **{r: rng.randint(0, 40) for r in counted})
                    for _ in range(rng.randint(3, 50))]
            out = calibrate.summarize(rows)
            self.assertEqual(list(out), list(calibrate.ROW_ORDER))
            for role in ALL_ROLES:
                lo, mid, hi = out[role]
                self.assertTrue(lo <= mid <= hi, (role, out[role]))


# ----------------------------------------------------------------------------- one deck
class DeckCountTests(unittest.TestCase):
    def setUp(self):
        self.db = sample_db()

    def count(self, commanders, cards):
        return calibrate.deck_counts(commanders, cards, self.db, fake_tag([n for _, n in cards], self.db))

    def test_a_complete_list_keeps_its_counted_lands(self):
        lands = [(20, "Forest"), (16, "Island"), (1, "Command Tower")]
        cards = [(1, n) for n in spells(ramp=10, filler=52)] + lands
        counts, unknown = self.count([KINNAN], cards)               # 62 spells + 37 lands = 99 cards
        self.assertEqual((counts["land"], counts["ramp"], unknown), (37, 10, []))

    def test_a_list_that_names_each_basic_land_once_gets_its_lands_recounted(self):
        lands = [(1, "Forest"), (1, "Island"), (1, "Command Tower")]
        cards = [(1, n) for n in spells(ramp=10, filler=52)] + lands
        counts, _ = self.count([KINNAN], cards)                     # 65 names listed, 99 cards in the deck
        self.assertEqual(counts["land"], 37)                        # 99 - 62 spells (the names alone say 3)
        self.assertEqual(counts["ramp"], 10)                        # roles still come from the listed cards

    def test_two_commanders_leave_98_cards(self):
        cards = [(1, n) for n in spells(filler=62)] + [(1, "Forest"), (1, "Island"), (1, "Command Tower")]
        counts, _ = self.count([TYMNA, THRASIOS], cards)
        self.assertEqual(counts["land"], 36)                        # 98 - 62

    def test_a_commander_listed_among_the_cards_is_not_one_of_them(self):
        cards = [(1, n) for n in spells(filler=62)] + [(1, "Forest"), (1, "kinnan, bonder prodigy")]
        counts, _ = self.count([KINNAN], cards)
        self.assertEqual(counts["land"], 37)       # kept in as a 63rd spell it would leave 36

    def test_a_name_the_card_index_lacks_counts_as_a_spell_and_never_as_a_land(self):
        cards = [(1, n) for n in spells(filler=61)] + [(1, "Brand New Card"), (1, "Forest")]
        counts, unknown = self.count([KINNAN], cards)
        self.assertEqual((counts["land"], unknown), (99 - 62, ["Brand New Card"]))

    def test_a_spell_that_ramps_is_not_a_land(self):
        cards = [(1, n) for n in spells(filler=62)] + [(1, "Command Tower"), (1, "Sol Ring")]
        counts, _ = self.count([KINNAN], cards)
        self.assertEqual((counts["land"], counts["ramp"]), (99 - 63, 1))    # Sol Ring is a spell that ramps

    def test_split_pair_reads_partners_but_not_double_faced_names(self):
        self.assertEqual(calibrate.split_pair(PAIR), [THRASIOS, TYMNA])
        self.assertEqual(calibrate.split_pair(KINNAN), [KINNAN])
        double_faced = "Ral, Monsoon Mage // Ral, Leyline Prodigy"
        self.assertEqual(calibrate.split_pair(double_faced), [double_faced])

    def test_a_decks_blue_comes_from_its_commanders_color_identity(self):
        ident = lambda *cmdrs: calibrate.identity(list(cmdrs), self.db)
        self.assertEqual(ident(KINNAN), "UG")
        self.assertEqual(ident(HAZEL), "BG")
        self.assertEqual(ident(TYMNA, THRASIOS), "WUBG")           # a pair adds up, in WUBRG order
        self.assertEqual(ident("Not A Commander"), "")


# ----------------------------------------------------------------------------- the five brackets
class TableTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(calibrate, "MIN_DECKS", 3)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.two = numbers(land=[35, 37, 39], ramp=[8, 10, 13], tutor=[0, 1, 3], topend=8)
        self.five = numbers(land=[26, 29, 32], ramp=[14, 19, 25], tutor=[8, 10, 12], topend=2)

    def test_bracket_3_is_a_third_of_the_way_from_2_to_5_and_bracket_4_two_thirds(self):
        three = calibrate.interpolate(self.two, self.five, 1)
        four = calibrate.interpolate(self.two, self.five, 2)
        self.assertEqual(three["ramp"], [10, 13, 17])       # 8+2, 10+3, 13+4
        self.assertEqual(four["ramp"], [12, 16, 21])        # 8+4, 10+6, 13+8
        self.assertEqual((three["topend"], four["topend"]), (6, 4))

    def test_interpolation_rounds_each_number_half_up(self):
        three = calibrate.interpolate(self.two, self.five, 1)
        four = calibrate.interpolate(self.two, self.five, 2)
        self.assertEqual(three["land"], [32, 34, 37])       # 32, 34.33, 36.67
        self.assertEqual(four["land"], [29, 32, 34])        # 29, 31.67, 34.33
        self.assertEqual(three["tutor"], [3, 4, 6])         # 2.67 up to 3
        self.assertEqual(four["tutor"], [5, 7, 9])          # 5.33 down to 5
        halfway = calibrate.interpolate(numbers(ramp=[0, 1, 2]), numbers(ramp=[1, 2, 3]), 1, of=2)
        self.assertEqual(halfway["ramp"], [1, 2, 3])        # 0.5 -> 1, 1.5 -> 2, 2.5 -> 3

    def test_an_interpolated_bracket_stays_in_order_and_leaves_its_ends_alone(self):
        before = (json.dumps(self.two), json.dumps(self.five))
        for step in (1, 2):
            mid = calibrate.interpolate(self.two, self.five, step)
            for role in ALL_ROLES:
                self.assertTrue(mid[role][0] <= mid[role][1] <= mid[role][2], role)
        self.assertEqual((json.dumps(self.two), json.dumps(self.five)), before)

    def test_bracket_1_is_bracket_2_with_one_more_land_and_no_tutors(self):
        one = calibrate.exhibition(self.two)
        self.assertEqual(one["land"], [35, 38, 39])
        self.assertEqual(one["tutor"], [0, 0, 3])           # the ceiling stays Bracket 2's
        for role in ALL_ROLES + ("topend",):
            if role not in ("land", "tutor"):
                self.assertEqual(one[role], self.two[role], role)
        self.assertEqual(self.two["land"], [35, 37, 39])    # Bracket 2 itself is untouched

    def test_bracket_1s_land_ceiling_moves_up_when_the_target_would_pass_it(self):
        one = calibrate.exhibition(numbers(land=[35, 37, 37]))
        self.assertEqual(one["land"], [35, 38, 38])

    def test_without_decks_for_3_and_4_they_are_interpolated_and_not_measured(self):
        table, measured = calibrate.build_table({2: [deck_row(ramp=r) for r in range(8, 14)],
                                                 5: [deck_row(ramp=r) for r in range(14, 20)]})
        self.assertEqual(measured, {1: False, 2: True, 3: False, 4: False, 5: True})
        self.assertEqual(list(table), [1, 2, 3, 4, 5])
        self.assertEqual(table[3], calibrate.interpolate(table[2], table[5], *calibrate.BLEND[3]))
        self.assertEqual(table[4], calibrate.interpolate(table[2], table[5], *calibrate.BLEND[4]))
        self.assertEqual(table[1], calibrate.exhibition(table[2]))

    def test_measured_decks_for_a_bracket_replace_its_interpolation(self):
        decks = {2: [deck_row(ramp=r) for r in range(8, 14)], 5: [deck_row(ramp=r) for r in range(14, 20)],
                 3: [deck_row(ramp=20) for _ in range(3)]}
        table, measured = calibrate.build_table(decks)
        self.assertEqual((measured[3], measured[4]), (True, False))
        self.assertEqual(table[3]["ramp"], [20, 20, 20])
        self.assertEqual(table[4], calibrate.interpolate(table[2], table[5], *calibrate.BLEND[4]))   # from 2 and 5, not from 3

    def test_too_few_decks_at_a_bracket_is_not_measured(self):
        five = [deck_row() for _ in range(5)]
        decks = {2: five, 5: five, 4: [deck_row(), deck_row()]}
        self.assertFalse(calibrate.build_table(decks)[1][4])

    def test_brackets_2_and_5_are_required_and_the_error_is_a_fetch_error(self):
        enough = [deck_row() for _ in range(3)]
        short_5 = "Bracket 5 needs at least 3 decks from EDHTop16.*got 2"
        with self.assertRaisesRegex(calibrate.NotEnoughData, short_5):
            calibrate.build_table({2: enough, 5: enough[:2]})
        no_2 = "Bracket 2 needs at least 3 decks from MTGJSON.*got 0"
        with self.assertRaisesRegex(calibrate.NotEnoughData, no_2):
            calibrate.build_table({5: enough})
        # a FetchError, so the command line exits 2 ("required data unavailable") for these
        self.assertTrue(issubclass(calibrate.NotEnoughData, net.FetchError))


# ----------------------------------------------------------------------------- which precons
class PreconChoiceTests(unittest.TestCase):
    def test_newest_first_released_only_one_per_name_and_no_collectors_edition_twin(self):
        entries = calibrate.recent_precons(fixture("calibrate_decklist.json"), TODAY.isoformat())
        self.assertEqual([(e["name"], e["releaseDate"]) for e in entries],
                         [("Newest Deck", "2026-10-02"), ("Reprinted Deck", "2025-06-13"),
                          ("Middle Deck", "2025-01-01"), ("Only Fancy Collector's Edition", "2024-01-01"),
                          ("Old Deck", "2020-05-05")])
        # skipped: the Collector's Edition twin, the deck not out yet, the older printing of a repeated name

    def test_a_collectors_edition_with_no_plain_twin_is_a_deck_of_its_own(self):
        entries = calibrate.recent_precons(fixture("calibrate_decklist.json"), "2030-01-01")
        names = [e["name"] for e in entries]
        self.assertIn("Only Fancy Collector's Edition", names)
        self.assertIn("Future Deck", names)                 # released by 2030, so it counts then

    def test_curly_apostrophes_in_the_twin_name_are_handled_too(self):
        entries = [{"name": "Foo", "releaseDate": "2025-01-01"},
                   {"name": "Foo Collector’s Edition", "releaseDate": "2025-01-01"}]
        self.assertEqual([e["name"] for e in calibrate.recent_precons(entries, "2026-01-01")], ["Foo"])


# ----------------------------------------------------------------------------- the file
def sample_report():
    """A report built from hand-made decks for Brackets 2 and 5, labelled as run() would."""
    rows2 = [deck_row(land=33 + i % 5, ramp=8 + i, tutor=i % 2, counter=i % 3, topend=6 + i % 4)
             for i in range(12)]
    rows5 = [deck_row(land=27 + i % 3, ramp=16 + i, tutor=8 + i % 4, counter=4 + i % 5, topend=2 + i % 2)
             for i in range(12)]
    brackets, measured = calibrate.build_table({2: rows2, 5: rows5})
    samples = {1: 0, 2: 12, 3: 0, 4: 0, 5: 12}
    sampler = types.SimpleNamespace(precon_span=("2024-02-09", "2026-10-02"),
                                    tournament=[(KINNAN, 7), (PAIR, 5)])
    labels, method = calibrate.describe(samples, measured, sampler, 150)
    return {"as_of": "2026-10-11", "brackets": brackets, "samples": samples,
            "samples_blue": {b: 0 for b in samples}, "measured": measured, "labels": labels, "method": method}


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "role_targets.json")
        no_playstyles = os.path.join(self.tmp, "none.json")
        for name, value in (("TARGETS_PATH", self.path), ("PLAYSTYLES_PATH", no_playstyles)):
            patcher = mock.patch.object(roles, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(calibrate, "MIN_DECKS", 3)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_written_file_reads_back_through_roles_targets(self):
        report = sample_report()
        self.assertEqual(calibrate.write_file(report), self.path)           # default: roles.TARGETS_PATH
        for b, row in report["brackets"].items():
            t = roles.targets(b)
            self.assertEqual(set(t), set(ALL_ROLES) | {"topend"})
            for role in ALL_ROLES:
                self.assertEqual([t[role]["min"], t[role]["target"], t[role]["max"]], row[role], (b, role))
            self.assertEqual(t["topend"], {"max": row["topend"]})

    def test_the_file_is_stamped_with_where_every_bracket_came_from(self):
        report = sample_report()
        calibrate.write_file(report, self.path)
        with open(self.path) as f:
            data = json.load(f)
        self.assertEqual(set(data), {"source", "as_of", "format", "method", "samples", "samples_blue",
                                     "measured", "labels", "brackets"})
        self.assertEqual(data["as_of"], "2026-10-11")
        self.assertEqual(data["samples"], {"1": 0, "2": 12, "3": 0, "4": 0, "5": 12})
        self.assertEqual(data["measured"], {"1": False, "2": True, "3": False, "4": False, "5": True})
        self.assertEqual(sorted(data["brackets"]), ["1", "2", "3", "4", "5"])
        self.assertEqual(data["labels"]["1"][:9], "judgment:")
        self.assertIn("precons as a Bracket 2 proxy", data["labels"]["2"])
        self.assertTrue(data["labels"]["3"].startswith("interpolated (judgment)"))
        self.assertTrue(data["labels"]["4"].startswith("interpolated (judgment)"))
        self.assertIn("EDHTop16 top-cut", data["labels"]["5"])
        self.assertEqual(data["method"], report["method"])

    def test_the_method_text_names_the_samples_the_percentiles_and_the_judgment_calls(self):
        method = sample_report()["method"]
        for phrase in ("25th percentile", "median", "90th percentile", "10th", "75th percentile",
                       "round half up", "only decks whose commander has blue",
                       "12 MTGJSON Commander precons released 2024-02-09 to 2026-10-02",
                       "precons as a Bracket 2 proxy", "12 EDHTop16 top-cut decks",
                       f"{KINNAN} (7), {PAIR} (5)", "Brackets 3 and 4 = interpolated", "judgment",
                       "Bracket 1 = Bracket 2 with land target +1 and tutor target 0"):
            self.assertIn(phrase, method)

    def test_the_method_text_says_which_of_3_and_4_were_measured(self):
        sampler = types.SimpleNamespace(precon_span=None, tournament=[(KINNAN, 7)])
        samples = {1: 0, 2: 12, 3: 20, 4: 0, 5: 12}
        measured = {1: False, 2: True, 3: True, 4: False, 5: True}
        labels, method = calibrate.describe(samples, measured, sampler, 150)
        self.assertEqual(labels[3], "measured: 20 Archidekt decks tagged Bracket 3")
        self.assertEqual(labels[4], "interpolated (judgment): Bracket 2 plus 1/2 of the way to Bracket 5")
        self.assertIn("Bracket 3 = Archidekt decks tagged with it; Bracket 4 is interpolated", method)
        measured[4] = True
        self.assertIn("Brackets 3 and 4 = Archidekt decks tagged with that bracket", calibrate.describe(
            samples, measured, sampler, 150)[1])

    def test_the_numbers_are_laid_out_exactly_like_the_committed_file(self):
        with open(os.path.join(FIXTURES, "calibrate_previous.json")) as f:
            committed = f.read()
        data = json.loads(committed)
        every = range(1, 6)
        report = {"as_of": "2026-10-11", "method": "m", "samples": dict.fromkeys(every, 0),
                  "samples_blue": dict.fromkeys(every, 0), "measured": dict.fromkeys(every, False),
                  "labels": dict.fromkeys(every, "judgment"),
                  "brackets": {int(b): row for b, row in data["brackets"].items()}}
        text = calibrate.dumps(calibrate.file_data(report))
        tail = lambda s: s[s.index('  "brackets": {'):]
        self.assertEqual(tail(text), tail(committed))
        self.assertEqual(json.loads(text)["brackets"], data["brackets"])
        self.assertTrue(text.startswith("{\n") and text.endswith("}\n"))

    def test_writing_leaves_no_temporary_file_and_replaces_an_existing_one(self):
        with open(self.path, "w") as f:
            f.write("old")
        calibrate.write_file(sample_report())
        self.assertEqual(os.listdir(self.tmp), ["role_targets.json"])
        with open(self.path) as f:
            self.assertEqual(json.load(f)["as_of"], "2026-10-11")

    def test_a_folder_that_does_not_exist_yet_is_created(self):
        target = os.path.join(self.tmp, "new", "deeper", "out.json")
        calibrate.write_file(sample_report(), target)
        self.assertTrue(os.path.exists(target))


class PreviousAndChangesTests(unittest.TestCase):
    def previous(self):
        return calibrate.read_previous(os.path.join(FIXTURES, "calibrate_previous.json"))

    def test_the_previous_numbers_are_read_with_integer_bracket_keys(self):
        prev = self.previous()
        self.assertEqual(sorted(prev), [1, 2, 3, 4, 5])
        self.assertEqual(prev[2]["ramp"], [8, 10, 13])
        self.assertEqual(prev[5]["topend"], 3)

    def test_a_missing_or_damaged_file_means_no_previous_numbers(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        self.assertEqual(calibrate.read_previous(os.path.join(tmp, "none.json")), {})
        for text in ("{not json", "[1, 2]", '{"brackets": [1]}'):
            path = os.path.join(tmp, "bad.json")
            with open(path, "w") as f:
                f.write(text)
            self.assertEqual(calibrate.read_previous(path), {}, text)

    def test_only_the_numbers_that_moved_are_listed(self):
        prev = self.previous()
        new = {b: {role: list(v) if isinstance(v, list) else v for role, v in row.items()}
               for b, row in prev.items()}
        self.assertEqual(calibrate.changes(prev, new), [])
        new[2]["ramp"] = [9, 12, 15]
        new[5]["topend"] = 4
        self.assertEqual(calibrate.changes(prev, new),
                         ["Bracket 2 ramp: 8/10/13 -> 9/12/15", "Bracket 5 topend: 3 -> 4"])

    def test_a_number_with_no_previous_value_is_shown_as_new(self):
        self.assertEqual(calibrate.changes({}, {3: {"land": [30, 33, 36], "topend": 5}}),
                         ["Bracket 3 land: none -> 30/33/36", "Bracket 3 topend: none -> 5"])


# ----------------------------------------------------------------------------- whole runs
class RunTests(unittest.TestCase):
    """run() with every source replaced by hand-made decks. Five precons (ramp 10 to 18, three of them with a
    blue commander), two tournament commanders (one single, one partner pair) and a third whose read fails."""
    PRECON_RAMP = {"Newest Deck": 10, "Reprinted Deck": 12, "Middle Deck": 14,
                   "Only Fancy Collector's Edition": 16, "Old Deck": 18}
    PRECON_COMMANDER = {"Newest Deck": KINNAN, "Reprinted Deck": HAZEL, "Middle Deck": KINNAN,
                        "Only Fancy Collector's Edition": HAZEL, "Old Deck": KINNAN}
    PRECON_COUNTER = {"Newest Deck": 2, "Middle Deck": 4, "Old Deck": 6}   # the blue ones; the rest run none

    def setUp(self):
        self.db = sample_db()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "role_targets.json")
        shutil.copy(os.path.join(FIXTURES, "calibrate_previous.json"), self.path)
        self.precon_calls, self.entries_calls, self.archidekt_calls, self.seen = [], [], [], []
        self.top = [{"name": KINNAN, "entries": 900, "conversion": 0.27},
                    {"name": PAIR, "entries": 700, "conversion": 0.3},
                    {"name": HAZEL, "entries": 400, "conversion": 0.2}]
        self.unknown_card = None
        self.archidekt_decks = {}
        patches = [
            mock.patch.object(calibrate, "MIN_DECKS", 4),
            mock.patch.object(calibrate, "_today", lambda: TODAY),
            mock.patch.object(carddb, "load", self.load), mock.patch.object(roles, "tag", self.tag),
            mock.patch.object(roles, "TARGETS_PATH", self.path),
            mock.patch.object(decklist, "_entries", self.decklist_entries),
            mock.patch.object(decklist, "precon", self.precon),
            mock.patch.object(edhtop16, "top_commanders", self.top_commanders),
            mock.patch.object(edhtop16, "entries", self.entries),
            mock.patch.object(archidekt, "decks", self.archidekt),
            mock.patch.object(config, "SOURCES", ("edhrec", "edhtop16")),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    # the sources; each records the refresh and offline mode it was given
    def load(self, **kw):
        self.seen.append(("carddb", kw.get("refresh"), kw.get("offline")))
        return self.db

    def tag(self, names, db, **kw):
        self.seen.append(("tag", kw.get("refresh"), kw.get("offline")))
        return fake_tag(names, db)

    def decklist_entries(self, refresh, offline):
        self.seen.append(("decklist._entries", refresh, offline))
        return fixture("calibrate_decklist.json")

    def precon(self, name, **kw):
        self.seen.append(("decklist.precon", kw.get("refresh"), kw.get("offline")))
        self.precon_calls.append(name)
        if name == "Newest Deck" and getattr(self, "newest_fails", False):
            raise net.FetchError("mtgjson", "https://mtgjson.com/x", "HTTP 500")
        ramp, counter = self.PRECON_RAMP[name], self.PRECON_COUNTER.get(name, 0)
        spell_names = spells(ramp=ramp, counter=counter, filler=62 - ramp - counter)
        if self.unknown_card:
            spell_names[-1] = self.unknown_card
        lands = [(21, "Forest"), (15, "Island"), (1, "Command Tower")]       # 37 lands
        cards = [(1, n) for n in spell_names] + lands
        return {"name": name, "code": "XXX", "file": "f", "release": "2025-01-01",
                "commanders": [self.PRECON_COMMANDER[name]], "cards": cards, "fetched": "", "url": ""}

    def top_commanders(self, min_entries=150, *a, **kw):
        self.seen.append(("top_commanders", kw.get("refresh"), kw.get("offline")))
        self.min_entries = min_entries
        return self.top

    def tournament_entry(self, ramp, topcut, commanders=1):
        """A collapsed list like EDHTop16's: each basic land once. 71 spells = 28 lands in a 99-card deck."""
        nonland = 71 if commanders == 1 else 70
        names = spells(ramp=ramp, counter=5, topend=2, filler=nonland - ramp - 5 - 2)
        if self.unknown_card:
            names[-1] = self.unknown_card
        names += ["Forest", "Island", "Command Tower"]
        return {"id": f"{ramp}", "wins": 3, "losses": 1, "draws": 0, "standing": 1 if topcut else 30,
                "topcut": topcut, "cards": names, "tournament": {}}

    def entries(self, commanders, time_period="ONE_YEAR", *, limit=None, **kw):
        self.seen.append(("entries", kw.get("refresh"), kw.get("offline")))
        self.entries_calls.append((commanders, limit))
        if commanders == KINNAN:         # four top cuts (ramp 16 to 19) and two entries that missed the cut
            return ([self.tournament_entry(r, True) for r in (16, 17, 18, 19)]
                    + [self.tournament_entry(40, False) for _ in range(2)])
        if commanders == PAIR:           # three top cuts (ramp 20 to 22) and one that missed
            cut = [self.tournament_entry(r, True, 2) for r in (20, 21, 22)]
            return cut + [self.tournament_entry(40, False, 2)]
        raise net.FetchError("edhtop16", "https://edhtop16.com/api/graphql", "HTTP 503")

    def archidekt(self, commanders, bracket=None, *, limit=40, **kw):
        self.archidekt_calls.append((commanders, bracket, limit))
        return self.archidekt_decks.get((commanders[0], bracket), [])

    def archidekt_deck(self, commander, ramp):
        names = spells(ramp=ramp, filler=62 - ramp) + ["Forest", "Island", "Command Tower"]
        return {"id": 1, "url": "", "bracket": 3, "commanders": [commander], "cards": names, "updated": "",
                "size": 100}

    def run_it(self, **kw):
        kw.setdefault("precons", 5)
        kw.setdefault("tournament_commanders", 3)
        return calibrate.run(**kw)

    # the whole run
    def test_a_run_without_archidekt_measures_2_and_5_and_interpolates_the_rest(self):
        report = self.run_it()
        self.assertEqual(report["measured"], {1: False, 2: True, 3: False, 4: False, 5: True})
        self.assertEqual(report["samples"], {1: 0, 2: 5, 3: 0, 4: 0, 5: 7})
        two, five = report["brackets"][2], report["brackets"][5]
        self.assertEqual(two["ramp"], [12, 14, 17])        # 10, 12, 14, 16, 18: positions 1, 2 and 3.6
        self.assertEqual(two["land"], [37, 37, 37])        # full counts: 21 + 15 + 1
        self.assertEqual(two["counter"], [3, 4, 6])        # only the blue decks: 2, 4, 6
        self.assertEqual(five["ramp"], [18, 19, 21])       # the 7 top cuts, ramp 16 to 22 (the 40s missed)
        self.assertEqual(five["land"], [28, 28, 28])       # recounted: 99 (98 for the pair) - 71 (70) spells
        self.assertEqual(five["counter"], [5, 5, 5])
        self.assertEqual(five["topend"], 2)
        self.assertEqual(report["brackets"][3]["ramp"], [14, 15, 18])      # 2 plus a quarter of the way to 5
        self.assertEqual(report["brackets"][4]["ramp"], [15, 17, 19])      # halfway: 15, 16.5 up to 17, 19
        self.assertEqual(report["brackets"][1]["land"], [37, 38, 38])      # B2's 37, one more, ceiling moved
        self.assertEqual(report["brackets"][1]["tutor"], [0, 0, 0])

    def test_the_report_labels_what_each_bracket_rests_on(self):
        report = self.run_it()
        self.assertEqual(report["labels"][2], "measured: 5 recent precons (precons as a Bracket 2 proxy)")
        self.assertEqual(report["labels"][5], "measured: 7 EDHTop16 top-cut decks")
        self.assertTrue(report["labels"][3].startswith("interpolated (judgment)"))
        self.assertTrue(report["labels"][1].startswith("judgment"))
        self.assertIn(f"{KINNAN} (4), {PAIR} (3)", report["method"])      # the failed commander is not listed

    def test_sources_are_read_the_way_the_design_says(self):
        self.run_it(entries_per_commander=150)
        # newest first; the twin, the future deck and the older printing of a repeated name are never read
        self.assertEqual(self.precon_calls, ["Newest Deck", "Reprinted Deck", "Middle Deck",
                                             "Only Fancy Collector's Edition", "Old Deck"])
        self.assertEqual(self.min_entries, 150)
        self.assertEqual(self.entries_calls, [(KINNAN, 150), (PAIR, 150), (HAZEL, 150)])

    def test_the_precon_count_stops_the_reading(self):
        self.run_it(precons=4)
        self.assertEqual(self.precon_calls, ["Newest Deck", "Reprinted Deck", "Middle Deck",
                                             "Only Fancy Collector's Edition"])

    def test_only_as_many_tournament_commanders_as_asked_are_read(self):
        self.run_it(tournament_commanders=2)
        self.assertEqual([c for c, _ in self.entries_calls], [KINNAN, PAIR])

    def test_archidekt_is_never_asked_unless_it_is_among_the_sources(self):
        for sources in (None, ("edhtop16",), ("edhrec", "edhtop16"), "edhtop16"):
            self.run_it(sources=sources)
        self.assertEqual(self.archidekt_calls, [])

    def test_the_default_sources_come_from_config(self):
        with mock.patch.object(config, "SOURCES", ("edhrec",)):        # no EDHTop16: no Bracket 5 to measure
            with self.assertRaisesRegex(calibrate.NotEnoughData, "Bracket 5 needs"):
                self.run_it()
        self.assertEqual(self.entries_calls, [])
        with mock.patch.object(config, "SOURCES", ("edhtop16", "archidekt")):
            self.run_it(archidekt_commanders=[KINNAN])
        self.assertEqual([(c, b) for c, b, _ in self.archidekt_calls], [([KINNAN], 3), ([KINNAN], 4)])

    def test_with_archidekt_on_brackets_3_and_4_are_measured(self):
        self.archidekt_decks = {(KINNAN, 3): [self.archidekt_deck(KINNAN, 20) for _ in range(3)],
                                (HAZEL, 3): [self.archidekt_deck(HAZEL, 20) for _ in range(2)],
                                (KINNAN, 4): [self.archidekt_deck(KINNAN, 24) for _ in range(3)],
                                (HAZEL, 4): [self.archidekt_deck(HAZEL, 24) for _ in range(1)]}
        report = self.run_it(sources=("edhtop16", "archidekt"), archidekt_commanders=[KINNAN, HAZEL],
                             decks_per_bracket=7)
        self.assertEqual(self.archidekt_calls,
                         [([KINNAN], 3, 7), ([HAZEL], 3, 7), ([KINNAN], 4, 7), ([HAZEL], 4, 7)])
        self.assertEqual(report["measured"], {1: False, 2: True, 3: True, 4: True, 5: True})
        self.assertEqual((report["samples"][3], report["samples"][4]), (5, 4))
        self.assertEqual(report["brackets"][3]["ramp"], [20, 20, 20])
        self.assertEqual(report["brackets"][4]["ramp"], [24, 24, 24])
        self.assertEqual(report["brackets"][4]["land"], [37, 37, 37])      # recounted: 99 - 62 spells
        self.assertEqual(report["labels"][3], "measured: 5 Archidekt decks tagged Bracket 3")
        self.assertIn("Brackets 3 and 4 = Archidekt decks tagged with that bracket", report["method"])

    def test_too_few_archidekt_decks_fall_back_to_interpolation_with_a_warning(self):
        self.archidekt_decks = {(KINNAN, 3): [self.archidekt_deck(KINNAN, 20) for _ in range(5)],
                                (KINNAN, 4): [self.archidekt_deck(KINNAN, 24) for _ in range(2)]}
        report = self.run_it(sources=("edhtop16", "archidekt"), archidekt_commanders=[KINNAN])
        self.assertEqual((report["measured"][3], report["measured"][4]), (True, False))
        brackets = report["brackets"]
        self.assertEqual(brackets[4], calibrate.interpolate(brackets[2], brackets[5], *calibrate.BLEND[4]))
        self.assertIn("Bracket 4: only 2 Archidekt decks (under 4), so it is interpolated",
                      report["warnings"])
        self.assertIn("Bracket 3 = Archidekt decks tagged with it; Bracket 4 is interpolated",
                      report["method"])

    def test_an_archidekt_commander_that_fails_is_skipped_with_a_warning(self):
        def fail_for_hazel(commanders, bracket=None, *, limit=40, **kw):
            if commanders == [HAZEL]:
                raise net.FetchError("archidekt", "https://archidekt.com/api", "HTTP 500")
            return [self.archidekt_deck(KINNAN, 20) for _ in range(4)]
        with mock.patch.object(archidekt, "decks", fail_for_hazel):
            report = self.run_it(sources=("edhtop16", "archidekt"), archidekt_commanders=[KINNAN, HAZEL])
        self.assertEqual(report["samples"][3], 4)
        skipped = [w for w in report["warnings"] if w.startswith("Archidekt commander 'Hazel")]
        self.assertEqual(len(skipped), 2)                   # once at each of Brackets 3 and 4

    def test_a_precon_that_fails_is_skipped_and_the_next_older_one_takes_its_place(self):
        self.newest_fails = True
        report = self.run_it(precons=4)
        self.assertEqual(self.precon_calls[0], "Newest Deck")
        self.assertEqual(report["samples"][2], 4)
        self.assertEqual(self.precon_calls[-1], "Old Deck")
        skipped = "precon 'Newest Deck' skipped: mtgjson: HTTP 500"
        self.assertTrue(any(w.startswith(skipped) for w in report["warnings"]))

    def test_a_tournament_commander_that_fails_is_skipped_with_a_warning(self):
        report = self.run_it()
        self.assertTrue(any(w.startswith(f"EDHTop16 commander '{HAZEL}' skipped: edhtop16: HTTP 503")
                            for w in report["warnings"]))

    def test_a_thin_blue_sample_is_called_out(self):
        report = self.run_it()
        self.assertEqual(report["samples_blue"], {1: 0, 2: 3, 3: 0, 4: 0, 5: 7})
        self.assertIn("Bracket 2: 3 of 5 decks have blue, so its counterspell numbers are thin",
                      report["warnings"])
        self.assertFalse([w for w in report["warnings"] if w.startswith("Bracket 5")])

    def test_card_names_the_index_lacks_are_reported_once_and_counted_as_spells(self):
        self.unknown_card = "Brand New Card"
        report = self.run_it()
        notes = [w for w in report["warnings"] if "not in the card index" in w]
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0], "card names not in the card index were counted as nonland cards (1): "
                                   "Brand New Card")
        self.assertEqual(report["brackets"][5]["land"], [28, 28, 28])     # no phantom 29th land from the gap

    def test_the_report_carries_the_previous_numbers_and_what_moved(self):
        report = self.run_it()
        self.assertEqual(report["previous"][2]["ramp"], [8, 10, 13])
        self.assertIn("Bracket 2 ramp: 8/10/13 -> 12/14/17", report["changes"])
        self.assertEqual(report["as_of"], "2026-10-11")
        again = calibrate.changes(report["brackets"], report["brackets"])
        self.assertEqual(again, [])

    def test_missing_function_tags_stop_the_run_before_anything_is_downloaded(self):
        before = list(roles.WARNINGS)

        def no_tags(names, db, **kw):
            roles.WARNINGS.append("roles: Scryfall function tags unavailable, so roles come from rules text")
            return {}
        with mock.patch.object(roles, "tag", no_tags):
            with self.assertRaisesRegex(calibrate.NotEnoughData, "function tags unavailable"):
                self.run_it()
        self.assertEqual((self.precon_calls, self.entries_calls), ([], []))
        self.assertEqual(roles.WARNINGS, before)         # the run cleans up the warning it caused

    def test_too_few_decks_is_an_error_that_includes_why(self):
        self.top = [{"name": HAZEL, "entries": 400, "conversion": 0.2}]       # its read fails: no B5 deck
        with self.assertRaises(calibrate.NotEnoughData) as caught:
            self.run_it()
        message = str(caught.exception)
        self.assertIn("Bracket 5 needs at least 4 decks from EDHTop16 top-cut decks, got 0", message)
        self.assertIn("HTTP 503", message)

    def test_no_precons_at_all_is_an_error(self):
        message = "Bracket 2 needs at least 4 decks from MTGJSON.*got 0"
        with self.assertRaisesRegex(calibrate.NotEnoughData, message):
            self.run_it(precons=0)

    def test_write_false_leaves_the_file_alone_and_write_true_replaces_it(self):
        with open(self.path) as f:
            before = f.read()
        self.assertIsNone(self.run_it()["written"])
        with open(self.path) as f:
            self.assertEqual(f.read(), before)
        report = self.run_it(write=True)
        self.assertEqual(report["written"], self.path)                      # default path: roles.TARGETS_PATH
        self.assertEqual(roles.targets(2)["ramp"], {"min": 12, "target": 14, "max": 17})
        with open(self.path) as f:
            data = json.load(f)
        self.assertEqual((data["as_of"], data["samples"]["5"]), ("2026-10-11", 7))

    def test_write_goes_to_the_given_path_and_previous_is_read_from_it(self):
        other = os.path.join(self.tmp, "other.json")
        report = self.run_it(write=True, path=other)
        self.assertEqual(report["written"], other)
        self.assertEqual(report["previous"], {})            # the file did not exist yet
        self.assertEqual(roles.targets(5)["ramp"]["target"], 16)      # roles still reads self.path, untouched

    def test_refresh_and_offline_are_passed_down_to_every_source(self):
        self.run_it(refresh=True, offline=False)
        self.assertEqual({label for label, _, _ in self.seen},
                         {"carddb", "tag", "decklist._entries", "decklist.precon", "top_commanders",
                          "entries"})
        for label, refresh, offline in self.seen:
            self.assertEqual((refresh, offline), (True, False), label)

    def test_the_fixed_archidekt_commanders_are_ten_distinct_names(self):
        names = calibrate.ARCHIDEKT_COMMANDERS
        self.assertEqual((len(names), len(set(names))), (10, 10))
        self.assertTrue(all(isinstance(n, str) and n for n in names))


class CommandLineTests(unittest.TestCase):
    def report(self):
        report = sample_report()
        report.update(previous={2: {"ramp": [8, 10, 13]}}, changes=[], warnings=["a warning"], written=None)
        return report

    def test_the_text_report_shows_every_role_old_and_new_and_the_warnings(self):
        text = calibrate.format_report(self.report())
        self.assertIn("Bracket 2  measured: 12 recent precons (precons as a Bracket 2 proxy)", text)
        self.assertIn("Bracket 3  interpolated (judgment)", text)
        ramp_line = next(line for line in text.splitlines()
                         if line.startswith("  ramp") and "8/10/13" in line)
        self.assertIn("->", ramp_line)
        self.assertEqual(text.count("  land "), 5)               # one land row per bracket
        self.assertTrue(text.rstrip().endswith("Warnings:\n  a warning"))

    def run_main(self, *argv, report=None, error=None):
        out = io.StringIO()
        def fake_run(**kw):
            if error:
                raise error
            self.kw = kw
            return report or self.report()
        with mock.patch.object(calibrate, "run", fake_run), contextlib.redirect_stdout(out):
            calibrate.main(list(argv))
        return out.getvalue()

    def test_out_writes_the_proposed_file_without_asking_run_to_overwrite_anything(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        target = os.path.join(tmp, "proposed.json")
        text = self.run_main("--out", target, "--sources", "edhtop16", "--precons", "12", "--entries", "50")
        self.assertFalse(self.kw["write"])
        self.assertEqual((self.kw["sources"], self.kw["precons"], self.kw["entries_per_commander"]),
                         ("edhtop16", 12, 50))
        self.assertIn("Bracket 5", text)
        self.assertTrue(text.rstrip().endswith(f"Wrote {target}"))         # says where the proposal went
        with open(target) as f:
            self.assertEqual(sorted(json.load(f)["brackets"]), ["1", "2", "3", "4", "5"])

    def test_write_is_passed_through_and_json_prints_the_report(self):
        text = self.run_main("--write", "--json")
        self.assertTrue(self.kw["write"])
        self.assertEqual(json.loads(text)["as_of"], "2026-10-11")

    def test_missing_data_exits_with_a_message_not_a_traceback(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_main(error=calibrate.NotEnoughData("Bracket 5 needs at least 10 decks"))
        self.assertEqual(str(caught.exception), "calibrate: Bracket 5 needs at least 10 decks")


if __name__ == "__main__":
    unittest.main()
