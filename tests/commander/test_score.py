"""Tests for score.py: the base score and its shrinkage, the precon discount, the tournament residual, theme
pull, salt, the evidence text, and `gather` (which sources it asks, what it does when one fails, how it widens a
thin bracket, the no-data fallback).

card_scores is pure arithmetic on an evidence dict, so most tests build a tiny evidence by hand and check the
numbers against the formula worked out in the comment above each assertion. gather's providers are replaced
with canned answers from fixtures/score_signals.json; net is closed (Isolated.setUp), so nothing here can reach
the network."""
import copy, json, os, tempfile, unittest
from unittest import mock
from mtgcommander import carddb, decklist, net, score
from mtgcommander.providers import archidekt, edhrec, edhtop16

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
TESSA = "Tessa, Squirrel Queen"


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


def plain_card(name, type_line="Creature — Test", cmc=2.0, text="", ci=(), legal="legal", price=1.0,
               rank=None):
    """A minimal Scryfall-shaped card, for the many cards a test needs but does not care about."""
    obj = {"oracle_id": "gen-" + name, "name": name, "layout": "normal", "mana_cost": "", "cmc": cmc,
           "type_line": type_line, "oracle_text": text, "color_identity": list(ci), "keywords": [],
           "legalities": {"commander": legal}, "prices": {"usd": str(price)}}
    if rank is not None:
        obj["edhrec_rank"] = rank
    return obj


def make_db(extra=()):
    cards = {}
    for obj in fixture("score_cards.json") + list(extra):
        rec = carddb.card_record(obj)
        cards[rec["name"]] = rec
    return carddb.CardDB(cards)


def stats(decks, of, synergy=None):
    return {"decks": decks, "of": of, "synergy": synergy}


def card(**slots):
    """An evidence entry with every slot present."""
    entry = {"all": None, "at": None, "themes": {}, "theme_global": {}, "tourn": None, "pop": None}
    entry.update(slots)
    return entry


def evidence(cards=None, *, bracket=3, n_all=10000, n_at=1000, n_tourn=0, floor_all=0.05, floor_at=0.05,
             **extra):
    ev = {"commanders": [TESSA], "ci": "BG", "bracket": bracket, "spec": {}, "enabled": ("edhrec",),
          "at_label": f"Bracket {bracket}", "cards": cards or {},
          "n": {"all": n_all, "at": n_at, "themes": {}, "tourn": n_tourn},
          "floor_all": floor_all, "floor_at": floor_at, "tourn_totals": None, "meta": None, "salt": {},
          "salt_floor": None, "theme_weights": {}, "theme_src": {}, "precon": None, "popularity": False,
          "sources": {}, "warnings": []}
    ev.update(extra)
    return ev


SPEC = {"weight": 0.5, "keep_fun": False}
FUN = {"weight": 0.5, "keep_fun": True}
PLAIN_SPEC = {"themes": [], "playstyle": "value", "weight": 0.5, "keep_fun": False, "bracket": 3}


def one(ev, name, spec=SPEC, role_map=None, db=None):
    return score.card_scores(ev, spec, db or make_db(), role_map or {}, names=[name])[name]


class Isolated(unittest.TestCase):
    """Closes every door to the network, whatever the test does."""

    def setUp(self):
        for fn in ("fetch_json", "request", "download"):
            mock.patch.object(net, fn, side_effect=AssertionError(f"net.{fn} must not run in a test")).start()
        self.addCleanup(mock.patch.stopall)


# ----------------------------------------------------------------------------- the base score
class BaseScoreTests(Isolated):
    def test_the_bracket_rate_is_pulled_toward_the_all_bracket_rate(self):
        # 90 of 100 Bracket 3 decks, 50% over all brackets: (90 + 200 * 0.5) / (100 + 200) = 0.6333
        ev = evidence({"Sol Ring": card(all=stats(5000, 10000), at=stats(90, 100))}, n_at=100)
        r = one(ev, "Sol Ring")
        self.assertAlmostEqual(r["parts"]["base"], 190 / 300)
        self.assertEqual((r["kind"], r["n"]), ("builder", 100))
        self.assertAlmostEqual(r["score"], r["parts"]["base"])

    def test_a_large_bracket_sample_barely_moves(self):
        # 900 of 1,000 against an all-bracket 50%: (900 + 100) / 1200 = 0.8333, close to its own 0.9
        ev = evidence({"Sol Ring": card(all=stats(5000, 10000), at=stats(900, 1000))})
        self.assertAlmostEqual(one(ev, "Sol Ring")["parts"]["base"], 1000 / 1200)

    def test_a_card_missing_from_the_bracket_page_sits_at_its_listing_line(self):
        # Played in 30% overall but not listed at Bracket 3, whose list stops at 6%: p_at = min(0.30, 0.06),
        # so (0.06 * 1000 + 200 * 0.30) / (1000 + 200) = 0.1
        ev = evidence({"Arcane Signet": card(all=stats(3000, 10000))}, n_at=1000, floor_at=0.06)
        r = one(ev, "Arcane Signet")
        self.assertAlmostEqual(r["parts"]["base"], 0.1)
        self.assertIn("rare at Bracket 3", r["evidence"])

    def test_without_a_bracket_page_the_all_bracket_rate_stands_in(self):
        ev = evidence({"Arcane Signet": card(all=stats(3000, 10000))}, n_at=0)
        self.assertAlmostEqual(one(ev, "Arcane Signet")["parts"]["base"], 0.3)

    def test_without_an_all_bracket_page_the_bracket_rate_stands_alone(self):
        ev = evidence({"Sol Ring": card(at=stats(90, 100))}, n_all=0, n_at=100)
        self.assertAlmostEqual(one(ev, "Sol Ring")["parts"]["base"], 0.9)

    def test_a_card_listed_at_the_bracket_only_is_pulled_toward_the_all_page_line(self):
        # In 20% of Bracket 3 decks, absent from the all-bracket page (which lists down to 5%): its overall rate
        # is taken as min(0.20, 0.05) = 0.05, so (200 + 200 * 0.05) / (1000 + 200) = 0.175
        ev = evidence({"Skullclamp": card(at=stats(200, 1000))}, floor_all=0.05)
        self.assertAlmostEqual(one(ev, "Skullclamp")["parts"]["base"], 210 / 1200)

    def test_named_cards_the_sources_never_heard_of_score_zero_and_say_why(self):
        r = one(evidence(), "Sakura-Tribe Elder")
        self.assertEqual((r["score"], r["kind"], r["n"]), (0.0, "none", 0))
        self.assertEqual(r["evidence"], "not on this commander's EDHREC lists (under ~5% of decks)")

    def test_names_none_scores_every_card_in_the_evidence(self):
        ev = evidence({"Sol Ring": card(at=stats(9, 10)), "Skullclamp": card(at=stats(5, 10))},
                      n_all=0, n_at=10)
        self.assertEqual(set(score.card_scores(ev, SPEC, make_db(), {})), {"Sol Ring", "Skullclamp"})

    def test_a_name_is_canonicalized_before_it_is_scored(self):
        ev = evidence({"Sol Ring": card(at=stats(9, 10))}, n_all=0, n_at=10)
        self.assertEqual(list(score.card_scores(ev, SPEC, make_db(), {}, names=["sol ring"])), ["Sol Ring"])

    def test_evidence_text_matches_the_design_example(self):
        ev = evidence({"Sol Ring": card(all=stats(8100, 10000), at=stats(934, 1125, 0.49))}, n_at=1125)
        self.assertEqual(one(ev, "Sol Ring")["evidence"],
                         "in 83% of 1,125 Bracket 3 Tessa decks (all brackets 81%, synergy +49%)")


# ----------------------------------------------------------------------------- precon discount
class PreconTests(Isolated):
    NAMES = [f"Precon Card {i}" for i in range(10)]

    def setUp(self):
        super().setUp()
        self.db = make_db([plain_card(n) for n in self.NAMES])

    def evidence(self, rates, **precon):
        """Precon cards 0..9 played in `rates[i]` of the commander's decks (None: on no list)."""
        cards = {n: card(all=stats(int(r * 10000), 10000)) for n, r in zip(self.NAMES, rates) if r}
        cards["Sol Ring"] = card(all=stats(5000, 10000))
        return evidence(cards, n_at=0, precon={"name": "Test Precon", "cards": self.NAMES + ["Command Tower"],
                                               **precon})

    def test_stock_cards_are_rescaled_by_the_share_of_near_stock_lists(self):
        # Rates 0%, 10%, ..., 90%. The 10th percentile (position 0.9 of 0..9) is 0.09: that share of lists
        # still plays the weakest precon cards only because it left the box alone.
        ev = self.evidence([i / 10 for i in range(10)])
        got = score.card_scores(ev, SPEC, self.db, {}, names=self.NAMES + ["Sol Ring"])
        s = 0.09
        self.assertAlmostEqual(got["Precon Card 5"]["parts"]["base"], (0.5 - s) / (1 - s))   # 0.4505
        self.assertAlmostEqual(got["Precon Card 1"]["parts"]["base"], (0.1 - s) / (1 - s))   # 0.0110
        self.assertEqual(got["Precon Card 0"]["parts"]["base"], 0.0)                          # never below 0
        self.assertIn("precon-adjusted", got["Precon Card 5"]["evidence"])

    def test_a_card_that_is_not_in_the_precon_keeps_its_rate(self):
        ev = self.evidence([i / 10 for i in range(10)])
        got = one(ev, "Sol Ring", db=self.db)
        self.assertAlmostEqual(got["parts"]["base"], 0.5)
        self.assertNotIn("precon", got["evidence"])

    def test_a_precon_card_at_the_floor_is_worth_nothing(self):
        ev = self.evidence([i / 10 for i in range(10)])
        self.assertEqual(one(ev, "Precon Card 0", db=self.db)["parts"]["base"], 0.0)

    def test_lands_do_not_drag_the_percentile_down(self):
        # Command Tower is in the precon and on no list (base 0); counting it would put s at 0.
        ev = self.evidence([i / 10 for i in range(10)])
        got = score.card_scores(ev, SPEC, self.db, {}, names=["Precon Card 5"])
        self.assertGreater(got["Precon Card 5"]["parts"]["base"], 0.4)

    def test_the_share_is_capped_at_0_6(self):
        # A precon whose every card is in 90% of lists: s would be 0.9, but no more than 0.6 can be inertia.
        ev = self.evidence([0.9] * 10)
        self.assertAlmostEqual(one(ev, "Precon Card 3", db=self.db)["parts"]["base"], (0.9 - 0.6) / 0.4)

    def test_an_explicit_share_in_the_evidence_is_used_as_given(self):
        ev = self.evidence([i / 10 for i in range(10)], s=0.2)
        self.assertAlmostEqual(one(ev, "Precon Card 5", db=self.db)["parts"]["base"], (0.5 - 0.2) / 0.8)

    def test_the_discount_only_touches_builder_evidence(self):
        ev = self.evidence([i / 10 for i in range(10)])
        ev["popularity"], ev["n"]["all"] = True, 0
        ev["cards"] = {"Precon Card 5": card(pop=10)}
        self.assertEqual(one(ev, "Precon Card 5", db=self.db)["kind"], "popularity")


# ----------------------------------------------------------------------------- the tournament residual
class ResidualTests(Isolated):
    TOTALS = {"entries": 300, "games": 1200, "wins": 600, "draws": 0, "topcuts": 60}

    def evidence(self, wins, entries=100, games=400, *, bracket=3):
        # with the card: wins / games; without it: (600 - wins) / (1200 - games)
        tourn = {"entries": entries, "games": games, "wins": wins, "draws": 0, "topcuts": 5}
        return evidence({"Sol Ring": card(at=stats(90, 100), tourn=tourn)}, bracket=bracket, n_at=100,
                        n_tourn=300, tourn_totals=dict(self.TOTALS))

    RAMP = {"Sol Ring": {"ramp"}}

    def test_a_card_that_wins_more_gets_a_small_positive_nudge(self):
        # With 212/400 = 0.53, without 388/800 = 0.485: gap 0.045, n = min(100, 200) = 100,
        # resid = 4 * 0.045 * 100 / 150 = 0.12, and Bracket 3 weights it 0.2.
        r = one(self.evidence(212), "Sol Ring", role_map=self.RAMP)
        self.assertAlmostEqual(r["parts"]["resid"], 0.2 * 0.12)
        self.assertIn("cEDH results: +4.5 pts game win rate over 100 entries (weight 0.2)", r["evidence"])

    def test_a_card_that_wins_less_gets_a_negative_one(self):
        r = one(self.evidence(188), "Sol Ring", role_map=self.RAMP)   # 0.47 against 0.515
        self.assertAlmostEqual(r["parts"]["resid"], -0.2 * 4 * 0.045 * 100 / 150)
        self.assertIn("-4.5 pts", r["evidence"])

    def test_the_residual_is_capped(self):
        # A 15-point gap would be 4 * 0.15 * 100 / 150 = 0.4 before the cap; the cap is 0.2 (times the weight).
        r = one(self.evidence(240), "Sol Ring", role_map=self.RAMP)
        self.assertAlmostEqual(r["parts"]["resid"], 0.2 * score.RESID_CAP)

    def test_a_thin_side_shrinks_it(self):
        # In 299 of 300 entries: one entry played without the card (3 wins in 4 games), so the 25-point gap
        # rests on one deck. n = min(299, 1) = 1: resid = 4 * -0.2508 * 1 / 51 = -0.0197, times 0.2 -- where
        # counting only the entries with the card would give the full cap, -0.04.
        ev = self.evidence(597, entries=299, games=1196)
        r = one(ev, "Sol Ring", role_map=self.RAMP)
        self.assertAlmostEqual(r["parts"]["resid"], 0.2 * 4 * (597 / 1196 - 3 / 4) / 51)
        self.assertGreater(r["parts"]["resid"], -0.005)
        self.assertNotIn("cEDH results", r["evidence"])

    def test_the_weight_grows_with_the_bracket(self):
        for bracket, weight in ((2, 0.0), (3, 0.2), (4, 0.5), (5, 1.0)):
            with self.subTest(bracket=bracket):
                r = one(self.evidence(212, bracket=bracket), "Sol Ring", role_map=self.RAMP)
                self.assertAlmostEqual(r["parts"]["resid"], weight * 0.12)

    def test_below_bracket_5_only_roles_that_carry_over_get_it(self):
        ev = self.evidence(212)
        for roles_, expected in (({"ramp"}, True), ({"draw"}, True), ({"removal"}, True), ({"tutor"}, True),
                                 ({"finisher"}, False), ({"recursion"}, False), (set(), False)):
            with self.subTest(roles=roles_):
                r = one(ev, "Sol Ring", role_map={"Sol Ring": roles_})
                self.assertEqual(r["parts"]["resid"] != 0, expected)

    def test_at_bracket_5_every_card_gets_it(self):
        r = one(self.evidence(212, bracket=5), "Sol Ring", role_map={"Sol Ring": {"finisher"}})
        self.assertAlmostEqual(r["parts"]["resid"], 0.12)

    def test_a_card_with_no_tournament_games_gets_nothing(self):
        ev = self.evidence(0, entries=0, games=0)
        self.assertEqual(one(ev, "Sol Ring", role_map=self.RAMP)["parts"]["resid"], 0.0)


# ----------------------------------------------------------------------------- tournament base at Bracket 5
class CedhBaseTests(Isolated):
    def evidence(self, n_tourn, entries):
        totals = {"entries": n_tourn, "games": 4 * n_tourn, "wins": 2 * n_tourn, "draws": 0, "topcuts": 0}
        return evidence({"Sol Ring": card(at=stats(500, 1000), all=stats(500, 1000),
                                          tourn={"entries": entries, "games": 4 * entries, "wins": 2 * entries,
                                                 "draws": 0, "topcuts": 0})},
                        bracket=5, n_at=1000, n_tourn=n_tourn, tourn_totals=totals)

    def test_the_tournament_play_rate_replaces_the_builder_rate(self):
        # 60 of 100 entries, shrunk a little toward the cEDH page's 50%: (60 + 25 * 0.5) / (100 + 25) = 0.58
        r = one(self.evidence(100, 60), "Sol Ring")
        self.assertAlmostEqual(r["parts"]["base"], (60 + score.K_TOURN * 0.5) / (100 + score.K_TOURN))
        self.assertAlmostEqual(r["parts"]["base"], 0.58)
        self.assertEqual(r["kind"], "tournament")
        self.assertTrue(r["evidence"].startswith("in 60% of 100 cEDH tournament decks"))

    def test_too_few_entries_leave_the_builder_rate(self):
        r = one(self.evidence(29, 20), "Sol Ring")
        self.assertEqual(r["kind"], "builder")
        self.assertAlmostEqual(r["parts"]["base"], (500 + 200 * 0.5) / 1200)

    def test_a_card_no_entry_played_has_a_low_base(self):
        ev = self.evidence(100, 60)
        ev["cards"]["Skullclamp"] = card(at=stats(400, 1000), all=stats(400, 1000))
        # no entry played it: only the small cEDH-page prior is left, (0 + 25 * 0.4) / (100 + 25) = 0.08
        self.assertAlmostEqual(one(ev, "Skullclamp")["parts"]["base"], 0.08)

    def test_a_card_the_tournament_source_did_not_look_up_keeps_the_builder_rate(self):
        # EDHTop16 lists only a commander's 100 most played cards. Skullclamp was not among them, so its
        # 0 entries mean "not looked at", not "no deck ran it": the cEDH builders' rate stands,
        # (400 + 200 * 0.4) / (1000 + 200) = 0.40, where reading it as unplayed would give 0.08
        ev = self.evidence(100, 60)
        ev["cards"]["Skullclamp"] = card(at=stats(400, 1000), all=stats(400, 1000), tourn_unchecked=True)
        r = one(ev, "Skullclamp")
        self.assertEqual(r["kind"], "builder")
        self.assertAlmostEqual(r["parts"]["base"], (400 + 200 * 0.4) / 1200)
        self.assertEqual(one(ev, "Sol Ring")["kind"], "tournament")   # a looked-up card is unchanged


# ----------------------------------------------------------------------------- theme pull
class ThemePullTests(Isolated):
    def themed(self, src, cards, *, sizes=None, weights=None):
        weights = weights or {"tokens": 1.0}
        return evidence(cards, theme_weights=weights, theme_src={t: src for t in weights},
                        n={"all": 10000, "at": 1000, "themes": sizes or {t: 300 for t in weights}, "tourn": 0})

    def test_a_bracket_theme_page_is_compared_with_the_bracket_rate(self):
        # 40% of Bracket 3 decks play it; 150 of the 300 Bracket 3 tokens decks do. Shrunk with 50
        # pseudo-decks of the 40%: p_t = (150 + 50 * 0.4) / 350 = 0.4857, a pull of +0.0857. The theme part is
        # that times the fantasy weight (0.5) and THEME_SCALE (2.5).
        card_ = card(at=stats(400, 1000), all=stats(5000, 10000), themes={"tokens": stats(150, 300)})
        r = one(self.themed("at", {"Sol Ring": card_}), "Sol Ring")
        self.assertAlmostEqual(r["pulls"]["tokens"], 170 / 350 - 0.4)
        self.assertAlmostEqual(r["parts"]["theme"], 0.5 * score.THEME_SCALE * (170 / 350 - 0.4))

    def test_an_all_bracket_theme_page_is_compared_with_the_all_bracket_rate(self):
        # The same card, but the theme page spans every bracket: 600 of 1,000 tokens decks play it, so
        # p_t = (600 + 50 * 0.5) / 1050 against p_all = 0.5 (not against the 0.4 of the one bracket).
        card_ = card(at=stats(400, 1000), all=stats(5000, 10000), themes={"tokens": stats(600, 1000)})
        r = one(self.themed("all", {"Sol Ring": card_}, sizes={"tokens": 1000}), "Sol Ring")
        self.assertAlmostEqual(r["pulls"]["tokens"], 625 / 1050 - 0.5)

    def test_the_text_names_the_pull(self):
        # p_t = (136 + 50 * 0.4) / 300 = 0.52 against 0.4: "+12% in tokens decks"
        card_ = card(at=stats(400, 1000), themes={"tokens": stats(136, 250)})
        r = one(self.themed("at", {"Sol Ring": card_}, sizes={"tokens": 250}), "Sol Ring")
        self.assertAlmostEqual(r["parts"]["theme"], 0.5 * score.THEME_SCALE * 0.12)
        self.assertIn("+12% in tokens decks", r["evidence"])        # the text shows the pull, not the part

    def test_a_card_absent_from_the_theme_page_is_pulled_down(self):
        # Played in 40% of Bracket 3 decks but in under ~5% of the tokens decks: p_t = 50 * 0.4 / 350
        card_ = card(at=stats(400, 1000))
        r = one(self.themed("at", {"Sol Ring": card_}), "Sol Ring")
        self.assertAlmostEqual(r["pulls"]["tokens"], 20 / 350 - 0.4)
        self.assertLess(r["parts"]["theme"], 0)

    def test_a_card_missing_from_a_capped_theme_page_played_under_its_floor_not_in_none(self):
        # The page of 1,000 tokens decks lists nothing below 10%. A card in 30% of Bracket 3 decks that is
        # missing from it was in under 10% of the tokens decks: p_t = (0.10 * 1000 + 50 * 0.30) / 1050, a pull
        # of -0.19.
        # (Counted as none, it would be 15 / 1050 - 0.30 = -0.29.)
        ev = self.themed("at", {"Sol Ring": card(at=stats(300, 1000))}, sizes={"tokens": 1000})
        none_at_all = one(ev, "Sol Ring")["pulls"]["tokens"]
        ev["floor_themes"] = {"tokens": 0.10}
        self.assertAlmostEqual(none_at_all, 15 / 1050 - 0.30)
        self.assertAlmostEqual(one(ev, "Sol Ring")["pulls"]["tokens"], 115 / 1050 - 0.30)

    def test_a_card_below_the_pages_floor_is_not_pulled_either_way(self):
        # In 5% of Bracket 3 decks, and the page cannot see below 10%: it may well play at the page's own rate
        ev = self.themed("at", {"Sol Ring": card(at=stats(50, 1000))}, sizes={"tokens": 1000})
        ev["floor_themes"] = {"tokens": 0.10}
        self.assertAlmostEqual(one(ev, "Sol Ring")["pulls"]["tokens"], 0.0)

    def test_the_floor_applies_to_the_page_the_theme_actually_uses(self):
        ev = self.themed("all", {"Sol Ring": card(all=stats(3000, 10000), at=stats(400, 1000))},
                         sizes={"tokens": 2000})
        ev["floor_themes"] = {"tokens": 0.10}
        # compared with the all-bracket rate (0.30), not the Bracket 3 one (0.40)
        self.assertAlmostEqual(one(ev, "Sol Ring")["pulls"]["tokens"], (0.10 * 2000 + 50 * 0.30) / 2050 - 0.30)

    def test_a_card_a_theme_page_lists_keeps_its_own_numbers_whatever_the_floor(self):
        ev = self.themed("at", {"Sol Ring": card(at=stats(300, 1000), themes={"tokens": stats(150, 300)})})
        ev["floor_themes"] = {"tokens": 0.10}
        self.assertAlmostEqual(one(ev, "Sol Ring")["pulls"]["tokens"], (150 + 50 * 0.30) / 350 - 0.30)

    def test_a_card_only_the_theme_page_lists_is_pulled_up_from_zero(self):
        card_ = card(themes={"tokens": stats(60, 300)})
        r = one(self.themed("at", {"Sol Ring": card_}), "Sol Ring")
        self.assertAlmostEqual(r["pulls"]["tokens"], 60 / 350)

    def test_the_theme_page_for_all_commanders_gives_half_its_synergy(self):
        card_ = card(theme_global={"sacrifice": stats(9000, 70000, 0.30)})
        ev = self.themed("global", {"Pitiless Plunderer": card_}, weights={"sacrifice": 1.0})
        r = one(ev, "Pitiless Plunderer")
        self.assertAlmostEqual(r["pulls"]["sacrifice"], 0.15)
        self.assertAlmostEqual(r["parts"]["theme"], 0.5 * score.THEME_SCALE * 0.15)
        self.assertIn("sacrifice synergy +30% (all commanders)", r["evidence"])

    def test_the_theme_part_is_scaled_and_capped(self):
        # A card in 30% of Bracket 3 decks and 90% of 300 tokens decks: p_t = (270 + 15) / 350 = 0.814, a
        # pull of +0.514; scaled by the full fantasy weight and THEME_SCALE that is 1.29, held to THEME_CAP.
        up = card(at=stats(300, 1000), themes={"tokens": stats(270, 300)})
        # 80% of Bracket 3 decks but missing from the page (no floor known): p_t = 40 / 350, a pull of -0.686
        down = card(at=stats(800, 1000))
        ev = self.themed("at", {"Up": up, "Down": down})
        both = score.card_scores(ev, {"weight": 1.0, "keep_fun": False}, make_db(), {}, names=["Up", "Down"])
        self.assertAlmostEqual(both["Up"]["pulls"]["tokens"], 285 / 350 - 0.30)
        self.assertEqual(both["Up"]["parts"]["theme"], score.THEME_CAP)
        self.assertEqual(both["Down"]["parts"]["theme"], -score.THEME_CAP)
        half = score.card_scores(ev, {"weight": 0.1, "keep_fun": False}, make_db(), {}, names=["Up"])
        self.assertAlmostEqual(half["Up"]["parts"]["theme"], 0.1 * score.THEME_SCALE * (285 / 350 - 0.30))

    def test_negative_synergy_on_the_all_commanders_page_is_no_pull(self):
        card_ = card(theme_global={"sacrifice": stats(100, 70000, -0.20)})
        ev = self.themed("global", {"Skullclamp": card_}, weights={"sacrifice": 1.0})
        self.assertEqual(one(ev, "Skullclamp")["pulls"]["sacrifice"], 0.0)

    def test_card_text_is_the_last_resort(self):
        # No page at all for the theme: a card that makes tokens still fits "tokens", a rock does not.
        ev = self.themed(None, {"Pitiless Plunderer": card(), "Sol Ring": card()})
        plunderer, sol = one(ev, "Pitiless Plunderer"), one(ev, "Sol Ring")
        self.assertAlmostEqual(plunderer["pulls"]["tokens"], score.MATCHER_PULL)
        self.assertEqual(sol["pulls"]["tokens"], 0.0)
        self.assertIn("fits tokens (by card text)", plunderer["evidence"])

    def test_a_card_that_is_on_no_list_can_still_fit_by_text(self):
        ev = self.themed(None, {})
        part = one(ev, "Pitiless Plunderer")["parts"]["theme"]
        self.assertAlmostEqual(part, 0.5 * score.THEME_SCALE * score.MATCHER_PULL)

    def test_the_term_is_the_weighted_mean_of_the_themes_times_the_fantasy_weight(self):
        # tokens (weight 1) and aristocrats (weight 0.5, from a playstyle) both fit by text; lifegain does not:
        # (1 * 0.1 + 0.5 * 0.1 + 0.5 * 0) / 2.0 = 0.075, times the weight 0.5 and THEME_SCALE
        ev = self.themed(None, {}, weights={"tokens": 1.0, "aristocrats": 0.5, "lifegain": 0.5})
        self.assertAlmostEqual(one(ev, "Pitiless Plunderer")["parts"]["theme"], 0.5 * score.THEME_SCALE * 0.075)

    def test_weight_zero_means_no_theme_term(self):
        ev = self.themed(None, {})
        r = one(ev, "Pitiless Plunderer", spec={"weight": 0.0, "keep_fun": False})
        self.assertEqual(r["parts"]["theme"], 0.0)
        self.assertNotIn("fits tokens", r["evidence"])

    def test_no_themes_means_no_term(self):
        self.assertEqual(one(evidence({"Sol Ring": card(at=stats(9, 10))}), "Sol Ring")["parts"]["theme"], 0.0)

    def test_a_small_pull_is_not_printed(self):
        card_ = card(at=stats(400, 1000), themes={"tokens": stats(122, 300)})   # p_t = 142/350 vs 0.4: +0.0057
        r = one(self.themed("at", {"Sol Ring": card_}), "Sol Ring")
        self.assertNotIn("tokens decks", r["evidence"])


# ----------------------------------------------------------------------------- salt
class SaltTests(Isolated):
    SALT = {"Toxic Deluge": 3.0, "Crux of Fate": 2.0}

    def evidence(self, **extra):
        return evidence({}, salt=dict(self.SALT), **extra)

    def test_salt_above_the_lists_floor_costs_a_little(self):
        # The list's lowest salt (2.0) is the floor: Toxic Deluge's 3.0 costs 0.15 * (3 - 2) / (4 - 2) = 0.075
        r = one(self.evidence(), "Toxic Deluge", spec=FUN)
        self.assertAlmostEqual(r["parts"]["salt"], -0.075)
        self.assertAlmostEqual(r["score"], -0.075)
        self.assertIn("salt 3.0", r["evidence"])

    def test_the_card_at_the_floor_is_free(self):
        r = one(self.evidence(), "Crux of Fate", spec=FUN)
        self.assertEqual(r["parts"]["salt"], 0.0)
        self.assertNotIn("salt", r["evidence"])

    def test_cards_outside_the_list_are_free(self):
        self.assertEqual(one(self.evidence(), "Sol Ring", spec=FUN)["parts"]["salt"], 0.0)

    def test_without_keep_it_fun_salt_costs_nothing(self):
        self.assertEqual(one(self.evidence(), "Toxic Deluge", spec=SPEC)["parts"]["salt"], 0.0)

    def test_the_floor_can_be_set_in_the_evidence(self):
        r = one(self.evidence(salt_floor=1.0), "Toxic Deluge", spec=FUN)
        self.assertAlmostEqual(r["parts"]["salt"], -0.15 * (3.0 - 1.0) / (4.0 - 1.0))

    def test_all_the_parts_add_up_to_the_score(self):
        ev = evidence({"Toxic Deluge": card(all=stats(5000, 10000), at=stats(500, 1000))}, salt=dict(self.SALT),
                      theme_weights={"tokens": 1.0}, theme_src={"tokens": None})
        r = one(ev, "Toxic Deluge", spec=FUN)
        self.assertAlmostEqual(sum(r["parts"].values()), r["score"])
        self.assertLess(r["parts"]["salt"], 0)


# ----------------------------------------------------------------------------- the no-data fallback
class PopularityTests(Isolated):
    def evidence(self, **cards):
        return evidence({n: card(pop=r) for n, r in cards.items()}, n_all=0, n_at=0, popularity=True)

    def test_the_most_popular_card_scores_the_popularity_weight(self):
        r = one(self.evidence(**{"Sol Ring": 1}), "Sol Ring")
        self.assertAlmostEqual(r["parts"]["base"], score.POP_WEIGHT)
        self.assertEqual((r["kind"], r["evidence"]), ("popularity", "EDHREC rank #1 overall (via Scryfall)"))

    def test_the_weight_falls_with_the_log_of_the_rank(self):
        import math
        r = one(self.evidence(Skullclamp=120), "Skullclamp")
        self.assertAlmostEqual(r["parts"]["base"], 0.3 * (1 - math.log(120) / math.log(4000)))

    def test_a_card_at_the_cutoff_scores_zero(self):
        self.assertAlmostEqual(one(self.evidence(Skullclamp=4000), "Skullclamp")["parts"]["base"], 0.0)

    def test_a_card_outside_the_pool_uses_its_rank_in_the_card_index(self):
        # Chatterfang is not in the evidence but the index knows its rank (1050)
        r = one(self.evidence(), "Chatterfang, Squirrel General")
        self.assertEqual(r["kind"], "popularity")
        self.assertIn("#1,050", r["evidence"])

    def test_a_card_with_no_rank_is_not_scored(self):
        r = one(self.evidence(), "Forest")
        self.assertEqual(r["kind"], "none")
        self.assertIn("most-played", r["evidence"])


# ----------------------------------------------------------------------------- small helpers
class HelperTests(unittest.TestCase):
    def test_short_names(self):
        for given, expected in (("Hazel of the Rootbloom", "Hazel"),
                                ("Chatterfang, Squirrel General", "Chatterfang"),
                                ("Tymna the Weaver", "Tymna the Weaver"),
                                ("Esika, God of the Tree // The Prismatic Bridge", "Esika"),
                                (["Kraum, Ludevic's Opus", "Tymna the Weaver"], "Kraum & Tymna the Weaver")):
            with self.subTest(given=given):
                self.assertEqual(score.short_name(given), expected)

    def test_pooling_counts_a_missing_card_as_decks_without_it(self):
        pooled, total = score._pool([(100, {"A": stats(50, 100, 0.2)}), (300, {"A": stats(30, 300, 0.4),
                                                                               "B": stats(60, 300)})])
        self.assertEqual(total, 400)
        self.assertEqual((pooled["A"]["decks"], pooled["A"]["of"]), (80, 400))
        self.assertEqual((pooled["B"]["decks"], pooled["B"]["of"]), (60, 400))   # 100 decks that lack B
        self.assertAlmostEqual(pooled["A"]["synergy"], (0.2 * 100 + 0.4 * 300) / 400)
        self.assertIsNone(pooled["B"]["synergy"])

    def test_percentile_interpolates(self):
        self.assertAlmostEqual(score._percentile([0.0, 0.1, 0.2, 0.3], 0.5), 0.15)
        self.assertEqual(score._percentile([], 0.1), 0.0)


# ----------------------------------------------------------------------------- gather
class GatherTests(Isolated):
    def setUp(self):
        super().setUp()
        self.db = make_db()
        self.sig = fixture("score_signals.json")
        self.pages = {}          # (bracket, theme) -> Signal, or an exception to raise
        self.bracket_theme = {}  # (bracket, theme) -> Signal
        self.globals_ = {}       # theme -> Signal
        self.archidekt = {}      # bracket -> Signal
        self.tournament = None
        self.precons = []
        self.salt = dict(self.sig["salt"])
        counts = {int(k): v for k, v in self.sig["meta"]["bracket_counts"].items()}
        self.meta = {**self.sig["meta"], "bracket_counts": counts}

        def answer(value):
            if isinstance(value, Exception):
                raise value
            return [copy.deepcopy(value)] if value else []

        edhrec_page = lambda c, bracket=None, theme=None, **kw: answer(self.pages.get((bracket, theme)))
        self.signals = mock.patch.object(edhrec, "signals", side_effect=edhrec_page).start()
        self.bt = mock.patch.object(edhrec, "bracket_theme_signal", side_effect=lambda c, b, t, **kw:
                                    (answer(self.bracket_theme.get((b, t))) or [None])[0]).start()
        self.glob = mock.patch.object(edhrec, "theme_signal", side_effect=lambda t, **kw:
                                      (answer(self.globals_.get(t)) or [None])[0]).start()
        self.meta_mock = mock.patch.object(edhrec, "commander_meta",
                                           side_effect=lambda c, *a, **kw: self.meta).start()
        self.salt_mock = mock.patch.object(edhrec, "salt_scores", side_effect=lambda **kw: self.salt).start()
        self.arch = mock.patch.object(
            archidekt, "signals",
            side_effect=lambda c, bracket=None, theme=None, **kw: answer(self.archidekt.get(bracket))).start()
        self.top = mock.patch.object(edhtop16, "signals", side_effect=lambda c, *a, **kw:
                                     answer(self.tournament)).start()
        self.precon_mock = mock.patch.object(decklist, "precons_for_commander",
                                             side_effect=lambda c, **kw: self.precons).start()

    def standard_pages(self):
        self.pages = {(None, None): self.sig["all"], (3, None): self.sig["b3"]}
        self.bracket_theme = {(3, "tokens"): self.sig["tokens_b3"]}
        self.tournament = self.sig["tournament"]

    def gather(self, bracket=3, spec=None, **kw):
        spec = spec or {"themes": ["tokens"], "playstyle": "value", "weight": 0.5, "keep_fun": True,
                        "bracket": bracket}
        kw.setdefault("sources", ("edhrec", "archidekt", "edhtop16"))   # not whatever the environment sets
        return score.gather([TESSA], bracket, spec, self.db, **kw)

    # --- the normal path
    def test_everything_is_fetched_and_keyed_by_canonical_name(self):
        self.standard_pages()
        ev = self.gather()
        self.assertEqual(set(ev["cards"]), {"Sol Ring", "Arcane Signet", "Skullclamp", "Toxic Deluge",
                                            "Chatterfang, Squirrel General"})
        self.assertEqual(ev["ci"], "BG")
        self.assertEqual(ev["n"], {"all": 10000, "at": 1000, "themes": {"tokens": 300}, "tourn": 100})
        self.assertEqual(ev["cards"]["Sol Ring"]["all"], stats(9000, 10000, 0.10))
        self.assertEqual(ev["cards"]["Sol Ring"]["at"], stats(950, 1000, 0.12))
        self.assertEqual(ev["cards"]["Sol Ring"]["themes"]["tokens"], stats(270, 300, 0.10))
        self.assertEqual(ev["cards"]["Sol Ring"]["tourn"]["entries"], 90)
        self.assertEqual(ev["tourn_totals"]["games"], 400)
        self.assertEqual(ev["theme_src"], {"tokens": "at"})
        self.assertEqual(ev["theme_weights"], {"tokens": 1.0})
        self.assertAlmostEqual(ev["floor_themes"]["tokens"], 200 / 300)   # Chatterfang: 200 of 300 tokens decks
        self.assertEqual(ev["meta"]["n_decks"], 10000)

    def test_basic_lands_the_commander_and_unknown_names_are_left_out(self):
        self.standard_pages()
        ev = self.gather()
        for left_out in ("Forest", TESSA, "Card Nobody Has Heard Of"):
            self.assertNotIn(left_out, ev["cards"])
        self.assertIn("Chatterfang, Squirrel General", ev["cards"])   # was "chatterfang, squirrel general"

    def test_listing_lines_are_the_lowest_inclusion_each_page_lists(self):
        self.standard_pages()
        ev = self.gather()
        self.assertAlmostEqual(ev["floor_at"], 0.06)     # Toxic Deluge, 60 of 1,000
        self.assertAlmostEqual(ev["floor_all"], 0.08)    # Toxic Deluge, 800 of 10,000

    def test_salt_is_fetched_only_when_keep_it_fun_is_on(self):
        self.standard_pages()
        ev = self.gather()
        self.assertEqual(ev["salt"], {"Toxic Deluge": 3.0, "Crux of Fate": 2.0, "Mana Crypt": 2.5})
        self.assertEqual(ev["salt_floor"], 2.0)
        self.salt_mock.reset_mock()
        ev = self.gather(spec=PLAIN_SPEC)
        self.salt_mock.assert_not_called()
        self.assertEqual(ev["salt"], {})

    def test_the_oldest_fetch_of_each_source_is_reported(self):
        self.standard_pages()
        self.pages[(3, None)]["fetched"] = "2026-10-09T00:00:00Z"
        ev = self.gather()
        self.assertEqual(ev["sources"]["edhrec"]["fetched"], "2026-10-09T00:00:00Z")
        self.assertEqual(ev["sources"]["edhtop16"]["fetched"], "2026-10-11T06:00:00Z")
        self.assertEqual(ev["sources"]["edhrec"]["cache"], "fresh")
        self.assertIsInstance(ev["sources"]["edhrec"]["age_days"], float)
        self.assertEqual(ev["warnings"], [])

    def test_stale_data_is_reported_with_its_age(self):
        self.standard_pages()
        self.pages[(None, None)].update(cache="stale", fetched="2026-09-01T00:00:00Z")
        ev = self.gather()
        self.assertEqual(ev["sources"]["edhrec"]["cache"], "stale")
        tail = "days old (offline or the site failed)"
        self.assertTrue(any(w.startswith("EDHREC data is ") and w.endswith(tail) for w in ev["warnings"]),
                        ev["warnings"])

    # --- failures
    def test_a_failed_source_is_a_warning_naming_it_and_the_run_goes_on(self):
        self.standard_pages()
        self.pages[(3, None)] = net.FetchError("edhrec", "https://x", "HTTP 500")
        self.pages[(2, None)], self.pages[(4, None)] = self.sig["b2"], self.sig["b4"]
        ev = self.gather()
        self.assertIn("EDHREC unavailable for the Bracket 3 page: HTTP 500", ev["warnings"])
        self.assertTrue(ev["cards"], "the other pages still gave a pool")
        self.assertGreater(ev["n"]["all"], 0)

    def test_a_missing_page_is_not_an_error(self):
        self.standard_pages()
        self.pages[(3, None)] = net.NotFound("edhrec", "https://x", "no such page")
        ev = self.gather()
        self.assertFalse([w for w in ev["warnings"] if "unavailable" in w], ev["warnings"])

    def test_a_failed_theme_page_falls_back_to_the_next_page_for_that_theme(self):
        self.standard_pages()
        self.bracket_theme = {}
        self.pages[(None, "tokens")] = self.sig["tokens_all"]
        ev = self.gather()
        self.assertEqual(ev["theme_src"], {"tokens": "all"})
        self.assertEqual(ev["n"]["themes"], {"tokens": 2000})
        self.assertEqual(ev["cards"]["Skullclamp"]["themes"]["tokens"], stats(1500, 2000, 0.50))
        self.assertEqual(ev["floor_themes"], {"tokens": 0.75})             # the page the theme actually uses

    def test_a_thin_bracket_theme_page_is_not_used(self):
        self.standard_pages()
        thin = copy.deepcopy(self.sig["tokens_b3"])
        thin["n"] = score.THIN - 1
        self.bracket_theme = {(3, "tokens"): thin}
        self.pages[(None, "tokens")] = self.sig["tokens_all"]
        self.assertEqual(self.gather()["theme_src"], {"tokens": "all"})

    def test_with_no_commander_theme_page_the_all_commanders_page_is_used(self):
        self.standard_pages()
        self.bracket_theme = {}
        spec = {"themes": ["sacrifice"], "playstyle": "value", "weight": 0.5, "keep_fun": False, "bracket": 3}
        self.globals_ = {"sacrifice": self.sig["global_sacrifice"]}
        ev = self.gather(spec=spec)
        self.assertEqual(ev["theme_src"], {"sacrifice": "global"})
        self.assertEqual(ev["floor_themes"], {})                           # only a commander's own page has one
        self.assertEqual(ev["cards"]["Pitiless Plunderer"]["theme_global"]["sacrifice"]["synergy"], 0.30)

    def test_a_playstyles_themes_count_half(self):
        self.standard_pages()
        spec = dict(PLAIN_SPEC, themes=["tokens"], playstyle="aristocrats")
        ev = self.gather(spec=spec)
        self.assertEqual(ev["theme_weights"], {"tokens": 1.0, "aristocrats": 0.5, "sacrifice": 0.5,
                                               "lifedrain": 0.5})
        self.assertEqual(ev["theme_src"]["aristocrats"], None)    # no page anywhere: card text decides

    def test_a_theme_named_by_the_player_and_the_playstyle_counts_fully(self):
        self.standard_pages()
        spec = {"themes": ["aristocrats"], "playstyle": "aristocrats", "weight": 0.5, "keep_fun": False,
                "bracket": 3}
        self.assertEqual(self.gather(spec=spec)["theme_weights"]["aristocrats"], 1.0)

    # --- thin brackets
    def test_a_thin_bracket_borrows_its_neighbours_and_archidekt(self):
        self.pages = {(None, None): self.sig["all"], (3, None): self.sig["b3_thin"], (2, None): self.sig["b2"],
                      (4, None): self.sig["b4"]}
        self.archidekt = {3: self.sig["archidekt_b3"]}
        ev = self.gather(spec=PLAIN_SPEC)
        self.assertEqual(ev["n"]["at"], 20 + 600 + 200 + 10)
        sol, clamp, signet = (ev["cards"][n]["at"] for n in ("Sol Ring", "Skullclamp", "Arcane Signet"))
        self.assertEqual((sol["decks"], sol["of"]), (18 + 500 + 190 + 9, 830))
        self.assertEqual((clamp["decks"], clamp["of"]), (8 + 0 + 120 + 0, 830))    # absent pages add "of" only
        self.assertEqual((signet["decks"], signet["of"]), (300, 830))
        self.assertEqual(ev["at_label"], "Brackets 2-4 + Archidekt")
        thin = [w for w in ev["warnings"] if w.startswith("Thin data")]
        self.assertEqual(len(thin), 1)
        for fragment in ("only 20 Bracket 3 Tessa", "Bracket 2 (600 decks)", "Bracket 4 (200 decks)",
                         "10 Archidekt decks", "830 decks in all"):
            self.assertIn(fragment, thin[0])

    def test_a_thin_bracket_with_nothing_to_borrow_says_so(self):
        self.pages = {(None, None): self.sig["all"], (3, None): self.sig["b3_thin"]}
        ev = self.gather(spec=PLAIN_SPEC)
        self.assertEqual(ev["n"]["at"], 20)
        self.assertTrue(any("no neighbouring bracket or Archidekt data" in w for w in ev["warnings"]))

    def test_bracket_1_has_only_one_neighbour(self):
        self.pages = {(None, None): self.sig["all"], (1, None): self.sig["b3_thin"], (2, None): self.sig["b2"]}
        ev = self.gather(1, spec={"themes": [], "playstyle": "value", "weight": 0.5, "keep_fun": False,
                                  "bracket": 1})
        self.assertEqual(ev["n"]["at"], 620)
        self.assertEqual([c.args[1] for c in self.signals.call_args_list if c.args[1] is not None], [1, 2])

    def test_a_missing_bracket_page_is_replaced_by_its_neighbours(self):
        self.pages = {(None, None): self.sig["all"], (2, None): self.sig["b2"], (4, None): self.sig["b4"]}
        ev = self.gather(spec=PLAIN_SPEC)
        self.assertEqual(ev["n"]["at"], 800)
        self.assertEqual(ev["at_label"], "Brackets 2-4")

    # --- no EDHREC
    def test_archidekt_stands_in_when_edhrec_is_off(self):
        wide = copy.deepcopy(self.sig["archidekt_b3"])
        wide.update(bracket=None, n=30)
        self.archidekt = {3: self.sig["archidekt_b3"], None: wide}
        ev = self.gather(sources=("archidekt",))
        self.signals.assert_not_called()
        self.assertEqual((ev["n"]["at"], ev["n"]["all"]), (10, 30))
        self.assertEqual(ev["at_label"], "Archidekt Bracket 3")
        self.assertIn("Sol Ring", ev["cards"])
        self.assertTrue(any("Thin data: only 10 Archidekt" in w for w in ev["warnings"]), ev["warnings"])
        self.assertEqual(set(ev["sources"]), {"archidekt"})

    def test_archidekt_stands_in_when_edhrec_has_no_page(self):
        self.archidekt = {3: self.sig["archidekt_b3"]}
        ev = self.gather()
        self.assertEqual(ev["n"]["at"], 10)
        self.assertTrue(any("EDHREC has no data" in w for w in ev["warnings"]))

    def test_with_no_builder_data_at_all_scores_come_from_scryfalls_popularity_rank(self):
        ev = self.gather(sources=())
        self.assertTrue(ev["popularity"])
        self.assertEqual(ev["n"]["all"] + ev["n"]["at"], 0)
        # Commander-legal, inside B/G, not basic, ranked <= 4000: not Mana Crypt (banned), the blue cards, the
        # commander or the basics
        self.assertEqual(set(ev["cards"]), {"Sol Ring", "Arcane Signet", "Skullclamp", "Toxic Deluge",
                                            "Crux of Fate", "Chatterfang, Squirrel General", "Pitiless Plunderer",
                                            "Command Tower", "Woodland Cemetery", "Bojuka Bog",
                                            "Sakura-Tribe Elder"})
        self.assertEqual(ev["cards"]["Sol Ring"]["pop"], 1)
        self.assertTrue(any("generic" in w and "Tessa" in w for w in ev["warnings"]), ev["warnings"])
        got = score.card_scores(ev, {"weight": 0.0, "keep_fun": False}, self.db, {})
        self.assertTrue(all(r["kind"] == "popularity" for r in got.values()))

    def test_every_source_failing_also_falls_back(self):
        down = net.FetchError("edhrec", "u", "down")
        self.pages = {(None, None): down, (3, None): down}
        ev = self.gather()
        self.assertTrue(ev["popularity"])
        self.assertIn("EDHREC unavailable for the all-bracket page: down", ev["warnings"])

    def test_the_popularity_pool_is_capped(self):
        extra = [plain_card(f"Rank Card {i}", ci="G", rank=100 + i) for i in range(800)]
        ev = score.gather([TESSA], 3, {"themes": [], "playstyle": "value", "weight": 0.5, "keep_fun": False},
                          make_db(extra), sources=())
        self.assertEqual(len(ev["cards"]), score.POP_POOL)

    # --- tournament
    def test_tournament_data_is_only_fetched_where_it_has_weight(self):
        self.standard_pages()
        self.gather(2)
        self.top.assert_not_called()
        self.gather(3)
        self.top.assert_called_once()

    def test_a_tournament_signal_passed_in_replaces_the_fetch(self):
        self.standard_pages()
        held_out = copy.deepcopy(self.sig["tournament"])
        held_out["n"] = 99
        ev = self.gather(tournament_signal=held_out)
        self.top.assert_not_called()
        self.assertEqual(ev["n"]["tourn"], 99)

    def test_cards_the_tournament_source_did_not_look_up_are_marked(self):
        # the signal says it looked up only Sol Ring (EDHTop16: a commander's 100 most played cards); every
        # other card the builders know is marked, so Bracket 5 does not read its missing entries as 0
        self.standard_pages()
        partial = copy.deepcopy(self.sig["tournament"])
        partial.setdefault("meta", {})["checked"] = ["Sol Ring"]
        ev = self.gather(tournament_signal=partial)
        self.assertNotIn("tourn_unchecked", ev["cards"]["Sol Ring"])
        self.assertTrue(ev["cards"]["Skullclamp"]["tourn_unchecked"])

    def test_a_signal_that_saw_every_card_marks_none(self):
        # a signal built from whole decklists (validate's held-out decks) has no "checked" list
        self.standard_pages()
        whole = copy.deepcopy(self.sig["tournament"])
        (whole.get("meta") or {}).pop("checked", None)
        ev = self.gather(tournament_signal=whole)
        self.assertFalse(any(c.get("tourn_unchecked") for c in ev["cards"].values()))

    def test_a_tournament_signal_passed_in_is_ignored_where_it_has_no_weight(self):
        self.standard_pages()
        ev = self.gather(2, tournament_signal=self.sig["tournament"])
        self.assertEqual(ev["n"]["tourn"], 0)

    def test_without_edhtop16_enabled_there_is_no_tournament_data(self):
        self.standard_pages()
        ev = self.gather(sources=("edhrec", "archidekt"))
        self.top.assert_not_called()
        self.assertEqual(ev["n"]["tourn"], 0)

    # --- precons
    def test_a_precon_is_remembered_at_brackets_2_and_3(self):
        self.standard_pages()
        self.pages[(2, None)] = self.sig["b2"]
        deck = [(1, "Sol Ring"), (1, "Skullclamp"), (1, "Arcane Signet"), (9, "Forest"), (1, "Command Tower"),
                (1, TESSA)]
        self.precons = [{"name": "Test Precon", "cards": deck}]
        ev = self.gather()
        self.assertEqual(ev["precon"]["name"], "Test Precon")
        self.assertEqual(ev["precon"]["cards"], ["Sol Ring", "Skullclamp", "Arcane Signet", "Command Tower"])
        # s = 10th percentile of the three nonland cards' bases (the land and the basic are not counted):
        #   Arcane Signet: listed overall (30%), not at Bracket 3 (list stops at 6%): (60 + 60) / 1200 = 0.1
        #   Skullclamp (700 + 200 * 0.6) / 1200 = 0.6833,  Sol Ring (950 + 200 * 0.9) / 1200 = 0.9417
        # position 0.1 * 2 = 0.2 of the sorted list: 0.1 + 0.2 * (0.6833 - 0.1)
        self.assertAlmostEqual(ev["precon"]["s"], 0.1 + 0.2 * (820 / 1200 - 0.1))
        self.assertEqual(self.gather(2)["precon"]["name"], "Test Precon")

    def test_no_precon_is_looked_up_at_brackets_4_and_5(self):
        self.pages = {(None, None): self.sig["all"], (4, None): self.sig["b4"]}
        self.gather(4)
        self.precon_mock.assert_not_called()

    def test_a_commander_without_a_precon_has_none(self):
        self.standard_pages()
        self.assertIsNone(self.gather()["precon"])

    def test_a_failed_precon_lookup_is_a_warning_not_an_error(self):
        self.standard_pages()
        self.precon_mock.side_effect = net.FetchError("mtgjson", "https://x", "offline")
        ev = self.gather()
        self.assertIsNone(ev["precon"])
        self.assertIn("MTGJSON unavailable for precon decks: offline", ev["warnings"])

    def test_the_precon_discount_reaches_the_scores(self):
        self.standard_pages()
        self.precons = [{"name": "Test Precon", "cards": [(1, "Sol Ring"), (1, "Skullclamp")]}]
        ev = self.gather()
        s = ev["precon"]["s"]
        sol = score.card_scores(ev, SPEC, self.db, {}, names=["Sol Ring"])["Sol Ring"]
        self.assertAlmostEqual(sol["parts"]["base"], (1130 / 1200 - s) / (1 - s))



# ----------------------------------------------------------------------------- the real EDHTop16 provider in gather
class RealTournamentSourceTests(Isolated):
    """gather with edhtop16.signals NOT replaced: only the network underneath it is faked, so what the site
    answers (or refuses) is followed all the way to the evidence and its warnings."""
    REFUSAL = {"errors": ["Only persisted queries are allowed in production. Plain text queries are disabled."]}
    SPEC = {"themes": [], "playstyle": "value", "weight": 0.5, "keep_fun": False, "bracket": 5}

    def setUp(self):
        super().setUp()
        self.db = make_db()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        mock.patch.object(net, "CACHE", tmp.name).start()      # a cache file the provider deletes is a scratch one
        self.asked = []

    def serve(self, answer):
        """Make net.fetch_json answer every EDHTop16 request with answer(persisted key): a payload to return,
        or an Exception to raise."""
        key_of_id = {query_id: key for key, (_, query_id) in edhtop16.PERSISTED.items()}

        def fetch(url, **kw):
            key = key_of_id[kw["data"]["extensions"]["pastoria-id"]]
            self.asked.append(key)
            result = answer(key)
            if isinstance(result, Exception):
                raise result
            return result, {"url": url, "fetched": "2026-10-11T06:00:00Z", "cache": "network", "age_days": 0.1}
        mock.patch.object(net, "fetch_json", fetch).start()

    def gather(self):
        return score.gather([TESSA], 5, self.SPEC, self.db, sources=("edhtop16",))

    def test_a_working_site_gives_tournament_evidence_and_no_warning(self):
        # The control for the failures below: the same run with the site answering
        one_page = fixture("edhtop16_entries_page1.json")
        one_page["data"]["commander"]["entries"]["pageInfo"] = {"endCursor": "5", "hasNextPage": False}
        deck = {"data": {"commander": {"cardEntries": {"edges": [{"node": {"id": "E1"}}, {"node": {"id": "E4"}}],
                                                       "pageInfo": {"endCursor": "2", "hasNextPage": False}}}}}
        routes = {"entries": one_page, "stats": fixture("edhtop16_stats.json"),
                  "staples": {"data": {"commander": {"staples": [{"name": "Sol Ring"}]}}}, "card_entries": deck}
        self.serve(lambda key: routes[key])
        ev = self.gather()
        self.assertEqual(ev["n"]["tourn"], 5)                         # E1-E5, the whole window
        self.assertEqual(ev["cards"]["Sol Ring"]["tourn"]["entries"], 2)    # E1 and E4 ran it
        self.assertEqual(ev["tourn_totals"]["games"], 20)
        self.assertIn("edhtop16", ev["sources"])
        self.assertEqual([w for w in ev["warnings"] if "EDHTop16" in w], [])

    def test_the_plain_text_refusal_is_a_warning_not_silently_no_data(self):
        # 2026-10-19: this answer used to read as "no such commander": no evidence and no warning at all
        self.serve(lambda key: self.REFUSAL)
        ev = self.gather()
        self.assertEqual(ev["n"]["tourn"], 0)
        self.assertNotIn("edhtop16", ev["sources"])
        self.assertTrue(any(w.startswith("EDHTop16 unavailable for tournament results:")
                            and "Only persisted queries are allowed" in w for w in ev["warnings"]), ev["warnings"])

    def test_a_query_id_the_site_no_longer_knows_is_a_warning_that_says_to_refresh_the_ids(self):
        self.serve(lambda key: net.FetchError("edhtop16", edhtop16.API, "HTTP 400"))
        ev = self.gather()
        self.assertTrue(any(w.startswith("EDHTop16 unavailable for tournament results:")
                            and "no longer recognizes its query id" in w and "PERSISTED" in w
                            for w in ev["warnings"]), ev["warnings"])

    def test_a_failure_halfway_through_the_card_lookups_still_warns(self):
        one_page = fixture("edhtop16_entries_page1.json")
        one_page["data"]["commander"]["entries"]["pageInfo"] = {"endCursor": "5", "hasNextPage": False}
        routes = {"entries": one_page, "stats": fixture("edhtop16_stats.json"),
                  "staples": {"data": {"commander": {"staples": [{"name": "Sol Ring"}]}}},
                  "card_entries": net.FetchError("edhtop16", edhtop16.API, "HTTP 503")}
        self.serve(lambda key: routes[key])
        ev = self.gather()
        self.assertEqual(ev["n"]["tourn"], 0)      # no half-built evidence: a missing card would read as unplayed
        self.assertIn("EDHTop16 unavailable for tournament results: HTTP 503", ev["warnings"])

    def test_an_unknown_commander_is_not_a_warning(self):
        self.serve(lambda key: fixture("edhtop16_entries_missing.json"))
        ev = self.gather()
        self.assertEqual(ev["n"]["tourn"], 0)
        self.assertEqual([w for w in ev["warnings"] if "EDHTop16" in w], [])


if __name__ == "__main__":
    unittest.main()
