"""Tests for carddb.py: card records built from Scryfall-shaped objects (including the picture links), name and
Scryfall-id matching, bulk-file reading, the index lifecycle (build, reuse, stale, offline) and the cheapest-price
batching. Nothing here touches the network; the cache folder is a temporary directory."""
import copy, gzip, json, os, shutil, tempfile, unittest
from unittest import mock
from mtgcommander import carddb, net

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SAMPLE = os.path.join(FIXTURES, "carddb_bulk_sample.jsonl")


def fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


def sample_objects():
    with open(SAMPLE, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def sample_db():
    cards = {}
    for obj in sample_objects():
        rec = carddb.card_record(obj)
        if rec and rec["name"] not in cards:
            cards[rec["name"]] = rec
    return carddb.CardDB(cards)


class TempCache(unittest.TestCase):
    """Points net's cache folder at a temporary directory and forgets any index loaded earlier."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        patcher = mock.patch.object(net, "CACHE", self.tmp)
        patcher.start()
        self.addCleanup(patcher.stop)
        carddb._MEMO.clear()
        del carddb.WARNINGS[:]
        self.addCleanup(carddb._MEMO.clear)


class NormalizeTests(unittest.TestCase):
    def test_spellings_that_must_agree(self):
        same = [
            ("Lim-D\u00fbl\u2019s  Vault", "lim-dul's vault"),    # accent, curly apostrophe, double space, case
            ("\u00c6ther Vial", "Aether Vial"),                      # the ligature MTGO and old lists use
            ("Fire/Ice", "Fire // Ice"),                              # MTGO writes split cards with one slash
            ("Fire / Ice", "fire // ice"),
            ("  Sol   Ring ", "sol ring"),
            ("Kongming, \u201cSleeping Dragon\u201d", 'Kongming, "Sleeping Dragon"'),
            ("Jaya\u2019s Immolating Inferno", "jaya`s immolating inferno"),
        ]
        for a, b in same:
            self.assertEqual(carddb.normalize(a), carddb.normalize(b), (a, b))

    def test_different_cards_stay_different(self):
        self.assertNotEqual(carddb.normalize("Sol Ring"), carddb.normalize("Sol Rings"))
        self.assertNotEqual(carddb.normalize("Fire // Ice"), carddb.normalize("Fire"))


class RecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = sample_db()

    def rec(self, name):
        return self.db.cards[name]

    def test_non_cards_are_skipped_but_illegal_cards_are_kept(self):
        by_name = {o["name"]: o for o in sample_objects()}
        self.assertIsNone(carddb.card_record(by_name["Treasure"]))
        self.assertIsNone(carddb.card_record(by_name["Brightglass Gearhulk // Brightglass Gearhulk"]))
        self.assertEqual(self.rec("Griselbrand")["legal"], "banned")   # decklists may hold it; `check` reports it

    def test_every_record_has_every_key(self):
        keys = set(self.rec("Sol Ring"))
        self.assertEqual(keys, {"name", "front", "oracle_id", "ci", "mana_cost", "cmc", "type_line", "types",
                                "subtypes", "text", "keywords", "legal", "gc", "price", "rank", "produced_mana",
                                "land", "mdfc_land", "commander_ok", "partner", "any_number", "layout",
                                "released", "image", "image_back", "scryfall_uri"})
        for rec in self.db.values():
            self.assertEqual(set(rec), keys, rec["name"])

    def test_plain_card_fields(self):
        r = self.rec("Sol Ring")
        self.assertEqual((r["ci"], r["mana_cost"], r["cmc"], r["types"], r["subtypes"]),
                         ("", "{1}", 1.0, ["Artifact"], []))
        self.assertEqual((r["price"], r["rank"], r["produced_mana"], r["gc"], r["legal"]),
                         (1.16, 1, ["C"], False, "legal"))
        hazel = self.rec("Hazel of the Rootbloom")
        self.assertEqual((hazel["ci"], hazel["types"], hazel["subtypes"]),
                         ("BG", ["Legendary", "Creature"], ["Squirrel", "Druid"]))
        self.assertEqual(self.rec("Forest")["types"], ["Basic", "Land"])

    def test_game_changer_flag(self):
        self.assertTrue(self.rec("Mana Crypt")["gc"])
        self.assertEqual([r["name"] for r in self.db.values() if r["gc"]], ["Mana Crypt"])

    def test_price_falls_back_from_normal_to_foil_to_etched(self):
        self.assertEqual(self.rec("Skullclamp")["price"], 19.13)       # only a foil price
        self.assertEqual(self.rec("Lotus Petal")["price"], 9.99)       # only an etched price
        self.assertIsNone(carddb.card_record(dict(sample_objects()[0], prices={}))["price"])

    def test_color_identity_is_in_wubrg_order(self):
        self.assertEqual(self.rec("Fire // Ice")["ci"], "UR")           # Scryfall lists ["R", "U"]
        self.assertEqual(self.rec("Lim-D\u00fbl's Vault")["ci"], "UB")
        self.assertEqual(self.rec("Thrasios, Triton Hero")["ci"], "UG")

    def test_multi_face_cards_use_the_front_face(self):
        fire = self.rec("Fire // Ice")
        self.assertEqual((fire["front"], fire["mana_cost"], fire["types"], fire["layout"]),
                         ("Fire", "{1}{R}", ["Instant"], "split"))
        self.assertEqual(fire["text"], "Fire deals 2 damage divided as you choose among one or two targets. // "
                                       "Tap target permanent. Draw a card.")
        delver = self.rec("Delver of Secrets // Insectile Aberration")
        self.assertEqual((delver["front"], delver["mana_cost"], delver["subtypes"]),
                         ("Delver of Secrets", "{U}", ["Human", "Wizard"]))
        giant = self.rec("Bonecrusher Giant // Stomp")      # Scryfall's own mana_cost is "{2}{R} // {1}{R}"
        self.assertEqual((giant["mana_cost"], giant["types"]), ("{2}{R}", ["Creature"]))
        self.assertIn("Instant \u2014 Adventure", giant["type_line"])

    def test_lands_and_modal_dfcs(self):
        self.assertTrue(self.rec("Command Tower")["land"])
        self.assertTrue(self.rec("Forest")["land"])
        mdfc = self.rec("Witch Enchanter // Witch-Blessed Meadow")
        self.assertEqual((mdfc["land"], mdfc["mdfc_land"], mdfc["produced_mana"]), (False, True, ["W"]))
        self.assertFalse(self.rec("Sol Ring")["mdfc_land"])

    def test_a_transform_cards_land_back_is_not_a_modal_dfc_land(self):
        obj = copy.deepcopy(next(o for o in sample_objects() if o["name"].startswith("Delver")))
        obj["card_faces"][1]["type_line"] = "Land"           # like Search for Azcanta // Azcanta, the Sunken Ruin
        self.assertFalse(carddb.card_record(obj)["mdfc_land"])
        obj["layout"] = "modal_dfc"
        self.assertTrue(carddb.card_record(obj)["mdfc_land"])

    def test_cards_that_allow_many_copies(self):
        self.assertTrue(self.rec("Relentless Rats")["any_number"])
        self.assertTrue(self.rec("Seven Dwarves")["any_number"])        # "up to seven" is exempted the same way
        self.assertFalse(self.rec("Sol Ring")["any_number"])

    def test_who_can_be_a_commander(self):
        cases = [
            ("Hazel of the Rootbloom", True),               # Legendary Creature
            ("Griselbrand", True),                          # banned, but the right kind of card
            ("Teferi, Temporal Archmage", True),            # "can be your commander"
            ("Esika's Chariot", True),                      # Legendary Vehicle with power and toughness
            ("The Eternity Elevator", False),               # Legendary Spacecraft without them
            ("Grist, the Hunger Tide", True),               # a creature everywhere except the battlefield
            ("Acolyte of Bahamut", True),                   # Background, next to a "Choose a Background" commander
            ("Brisela, Voice of Nightmares", False),        # the meld result is never in a deck
            ("Sol Ring", False), ("Command Tower", False), ("Bonecrusher Giant // Stomp", False),
        ]
        for name, expected in cases:
            self.assertEqual(self.rec(name)["commander_ok"], expected, name)

    def test_partner_kinds(self):
        cases = [
            ("Pir, Imaginative Rascal", "partner with Toothy, Imaginary Friend"),
            ("Toothy, Imaginary Friend", "partner with Pir, Imaginative Rascal"),
            ("Thrasios, Triton Hero", "partner"),
            ("Halsin, Emerald Archdruid", "choose a background"),
            ("Acolyte of Bahamut", "background"),
            ("The Eighth Doctor", "doctor"),
            ("Nyssa of Traken", "doctor's companion"),
            ("Sophina, Spearsage Deserter", "friends forever"),
            ("Donatello, the Brains", "partner\u2014character select"),
            ("Hazel of the Rootbloom", None),
            ("Sol Ring", None),
        ]
        for name, expected in cases:
            self.assertEqual(self.rec(name)["partner"], expected, name)

    def test_partner_from_keywords_when_the_text_is_not_there_yet(self):
        obj = dict(next(o for o in sample_objects() if o["name"] == "Hazel of the Rootbloom"), keywords=["Partner"])
        self.assertEqual(carddb.card_record(obj)["partner"], "partner")

    def test_a_reversible_card_keeps_its_oracle_id_on_the_faces(self):
        obj = copy.deepcopy(next(o for o in sample_objects() if o["name"].startswith("Delver")))
        oid = obj.pop("oracle_id")
        obj["card_faces"][0]["oracle_id"] = oid
        self.assertEqual(carddb.card_record(obj)["oracle_id"], oid)


class PictureLinkTests(unittest.TestCase):
    """`image`, `image_back` and `scryfall_uri`, read from objects shaped like Scryfall's (fixtures/carddb_images.json),
    one for each way Scryfall lays out a card's pictures: on the card (normal, split, adventure), on each face
    (transform, modal two-faced), or nowhere."""
    @classmethod
    def setUpClass(cls):
        cls.objs = {o["name"]: o for o in fixture("carddb_images.json")}

    def rec(self, name):
        return carddb.card_record(self.objs[name])

    def test_a_normal_card_has_a_front_picture_and_no_back(self):    # one picture, on the card itself
        r = self.rec("Hazel of the Rootbloom")
        self.assertEqual(r["image"], "https://cards.scryfall.io/normal/front/0/1/"
                                     "01000000-0000-4000-8000-000000000001.jpg?1700000000")
        self.assertEqual(r["image_back"], "")
        self.assertEqual(r["scryfall_uri"], "https://scryfall.com/card/blc/2/hazel-of-the-rootbloom?utm_source=api")

    def test_a_transform_card_has_a_picture_for_each_face(self):     # Delver of Secrets // Insectile Aberration
        r = self.rec("Delver of Secrets // Insectile Aberration")
        self.assertEqual(r["image"], "https://cards.scryfall.io/normal/front/0/2/"
                                     "02000000-0000-4000-8000-000000000002.jpg?1700000000")
        self.assertEqual(r["image_back"], "https://cards.scryfall.io/normal/back/0/2/"
                                          "02000000-0000-4000-8000-000000000002.jpg?1700000000")
        self.assertEqual(r["scryfall_uri"],
                         "https://scryfall.com/card/inr/60/delver-of-secrets-insectile-aberration?utm_source=api")

    def test_a_modal_two_faced_card_has_a_picture_for_each_face(self):    # Valki, God of Lies // Tibalt
        r = self.rec("Valki, God of Lies // Tibalt, Cosmic Impostor")
        self.assertTrue(r["image"].startswith("https://cards.scryfall.io/normal/front/0/3/"), r["image"])
        self.assertTrue(r["image_back"].startswith("https://cards.scryfall.io/normal/back/0/3/"), r["image_back"])
        self.assertEqual(r["layout"], "modal_dfc")

    def test_a_split_card_has_one_picture_of_both_halves(self):      # Fire // Ice: the halves have no pictures
        r = self.rec("Fire // Ice")
        self.assertEqual(r["image"], "https://cards.scryfall.io/normal/front/0/4/"
                                     "04000000-0000-4000-8000-000000000004.jpg?1700000000")
        self.assertEqual(r["image_back"], "")
        self.assertNotIn("image_uris", self.objs["Fire // Ice"]["card_faces"][0])

    def test_an_adventure_card_has_one_picture_of_both_halves(self):    # Bonecrusher Giant // Stomp
        r = self.rec("Bonecrusher Giant // Stomp")
        self.assertTrue(r["image"].startswith("https://cards.scryfall.io/normal/front/0/5/"), r["image"])
        self.assertEqual(r["image_back"], "")

    def test_a_card_with_no_pictures_has_empty_links_not_missing_keys(self):
        # Scryfall sent neither image_uris nor scryfall_uri for this one
        r = self.rec("Card Without Pictures")
        self.assertEqual((r["image"], r["image_back"], r["scryfall_uri"]), ("", "", ""))

    def test_only_the_normal_size_counts(self):         # not small, large, png, art_crop or border_crop
        obj = copy.deepcopy(self.objs["Hazel of the Rootbloom"])
        self.assertIn("/normal/", carddb.card_record(obj)["image"])
        del obj["image_uris"]["normal"]
        self.assertEqual(carddb.card_record(obj)["image"], "")

    def test_a_picture_on_the_card_wins_over_one_on_its_front_face(self):    # not a shape Scryfall sends today
        obj = copy.deepcopy(self.objs["Fire // Ice"])
        for face, side in zip(obj["card_faces"], ("front", "back")):
            face["image_uris"] = {"normal": f"https://cards.scryfall.io/normal/{side}/x.jpg"}
        r = carddb.card_record(obj)
        self.assertEqual(r["image"], obj["image_uris"]["normal"])
        self.assertEqual(r["image_back"], "https://cards.scryfall.io/normal/back/x.jpg")

    def test_every_object_gives_all_three_keys(self):
        # all six cards of the fixture
        for name in self.objs:
            self.assertTrue({"image", "image_back", "scryfall_uri"} <= set(self.rec(name)), name)


class LookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = sample_db()

    def test_any_reasonable_spelling_finds_the_card(self):
        cases = [
            ("Sol Ring", "Sol Ring"), ("sol ring", "Sol Ring"), ("SOL  RING", "Sol Ring"),
            ("Lim-Dul's Vault", "Lim-D\u00fbl's Vault"),
            ("Lim-D\u00fbl\u2019s Vault", "Lim-D\u00fbl's Vault"),
            ("Aether Vial", "Aether Vial"), ("\u00c6ther Vial", "Aether Vial"),
            ("Fire // Ice", "Fire // Ice"), ("Fire/Ice", "Fire // Ice"),
            ("Fire", "Fire // Ice"),                                    # front face of a split card
            ("Delver of Secrets", "Delver of Secrets // Insectile Aberration"),
            ("Bonecrusher Giant", "Bonecrusher Giant // Stomp"),       # front face of an adventure card
            ("Witch Enchanter", "Witch Enchanter // Witch-Blessed Meadow"),
        ]
        for spelled, canonical in cases:
            self.assertEqual(self.db.resolve(spelled), canonical, spelled)
            self.assertEqual(self.db.get(spelled)["name"], canonical, spelled)
            self.assertIn(spelled, self.db)

    def test_the_second_half_of_a_split_card_is_not_a_name(self):
        for half in ("Ice", "Stomp", "Insectile Aberration", "Witch-Blessed Meadow"):
            self.assertIsNone(self.db.resolve(half), half)
            self.assertNotIn(half, self.db)

    def test_unknown_names_give_none_and_close_suggestions(self):
        self.assertIsNone(self.db.get("Sol Rng"))
        self.assertEqual(self.db.suggest("Sol Rng")[0], "Sol Ring")
        self.assertEqual(self.db.suggest("Hazel of the Rootblom", 2)[0], "Hazel of the Rootbloom")
        self.assertEqual(self.db.suggest("zzzzzzzzzz"), [])
        self.assertLessEqual(len(self.db.suggest("Counter", 3)), 3)

    def test_suggestions_are_canonical_names_without_repeats(self):
        out = self.db.suggest("Fire Ice", 5)
        self.assertEqual(len(out), len(set(out)))
        self.assertIn("Fire // Ice", out)

    def test_a_front_face_never_hides_a_real_card_of_that_name(self):
        def rec(name, front):
            return dict(carddb.card_record(sample_objects()[0]), name=name, front=front)
        cards = {"Bind": rec("Bind", "Bind"), "Bind // Liberate": rec("Bind // Liberate", "Bind")}
        self.assertEqual(carddb.CardDB(cards).resolve("bind"), "Bind")

    def test_size_and_iteration(self):
        self.assertEqual(len(self.db), len(self.db.cards))
        self.assertEqual(len(list(self.db.values())), len(self.db))

    def test_a_card_is_found_by_its_scryfall_id(self):
        # Sol Ring by its id, and Fire // Ice by the id of the record the name 'Fire/Ice' finds
        sol_ring = self.db.get("Sol Ring")
        self.assertEqual(sol_ring["oracle_id"], "00000000-0000-4000-8000-000000000001")
        self.assertIs(self.db.by_oracle("00000000-0000-4000-8000-000000000001"), sol_ring)
        self.assertEqual(self.db.by_oracle(self.db.get("Fire/Ice")["oracle_id"])["name"], "Fire // Ice")

    def test_an_id_the_index_does_not_hold_gives_none(self):
        # an id nobody has, an empty one, and None
        self.assertIsNone(self.db.by_oracle("ffffffff-ffff-4fff-8fff-ffffffffffff"))
        self.assertIsNone(self.db.by_oracle(""))
        self.assertIsNone(self.db.by_oracle(None))

    def test_a_card_renamed_upstream_is_found_by_id_but_not_by_its_old_name(self):
        # Sol Ring is now 'Sol Ring Reforged': the old name is gone, the id still finds the card
        cards = {name: rec for name, rec in sample_db().cards.items() if name != "Sol Ring"}
        old = sample_db().get("Sol Ring")
        cards["Sol Ring Reforged"] = dict(old, name="Sol Ring Reforged", front="Sol Ring Reforged")
        db = carddb.CardDB(cards)
        self.assertIsNone(db.get("Sol Ring"))
        self.assertEqual(db.by_oracle(old["oracle_id"])["name"], "Sol Ring Reforged")

    def test_the_id_map_is_built_once_and_skips_records_without_an_id(self):
        # two records, only one with an oracle_id
        db = carddb.CardDB({"A": {"name": "A", "oracle_id": "id-a"}, "B": {"name": "B"}})
        self.assertIsNone(db._by_oracle)                 # nothing is built until it is asked for
        self.assertEqual(db.by_oracle("id-a")["name"], "A")
        first = db._by_oracle
        self.assertIsNone(db.by_oracle("id-b"))
        self.assertIs(db._by_oracle, first)              # the same map answers the second question


class BulkFileTests(unittest.TestCase):
    """The same cards in every layout Scryfall has used must read back identically."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.objs = sample_objects()[:6]

    def write(self, name, text, gz=False):
        path = os.path.join(self.tmp, name)
        with (gzip.open(path, "wt", encoding="utf-8") if gz else open(path, "w", encoding="utf-8")) as f:
            f.write(text)
        return path

    def test_json_lines_plain_and_gzipped(self):
        text = "".join(json.dumps(o) + "\n" for o in self.objs)
        self.assertEqual(list(carddb.iter_bulk(self.write("a.jsonl", text))), self.objs)
        self.assertEqual(list(carddb.iter_bulk(self.write("b.json", text, gz=True))), self.objs)   # magic wins

    def test_array_with_one_card_per_line(self):
        text = "[\n" + ",\n".join(json.dumps(o) for o in self.objs) + "\n]\n"
        self.assertEqual(list(carddb.iter_bulk(self.write("a.json", text))), self.objs)

    def test_array_on_one_line_and_pretty_printed(self):
        self.assertEqual(list(carddb.iter_bulk(self.write("a.json", json.dumps(self.objs)))), self.objs)
        self.assertEqual(list(carddb.iter_bulk(self.write("b.json", json.dumps(self.objs, indent=2)))), self.objs)

    def test_blank_lines_are_ignored(self):
        text = "\n".join(json.dumps(o) + "\n" for o in self.objs)
        self.assertEqual(list(carddb.iter_bulk(self.write("a.jsonl", text))), self.objs)

    def test_a_damaged_line_after_good_ones_is_an_error(self):
        text = json.dumps(self.objs[0]) + "\n{not json}\n"
        with self.assertRaises(ValueError):
            list(carddb.iter_bulk(self.write("a.jsonl", text)))


class IndexLifecycleTests(TempCache):
    """build_index and load() against a stand-in for Scryfall that serves the sample cards."""
    def setUp(self):
        super().setUp()
        self.downloads = []
        self.listing = fixture("carddb_bulk_list.json")
        for patcher in (mock.patch.object(net, "fetch_json", self.fake_fetch_json),
                        mock.patch.object(net, "download", self.fake_download)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_fetch_json(self, url, **kw):
        self.assertEqual(url, carddb.BULK_LIST)
        info = {"url": url, "fetched": "2026-10-11T12:00:00Z", "cache": "network", "age_days": 0}
        return copy.deepcopy(self.listing), info

    def fake_download(self, url, path, *, source):
        self.downloads.append(url)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(SAMPLE, "rb") as src, gzip.open(path, "wb") as out:    # the CDN serves gzip, no Content-Encoding
            out.write(src.read())
        return path

    def index_file(self):
        return carddb.index_path()

    def age_index(self, days):
        with open(self.index_file()) as f:
            idx = json.load(f)
        idx["ts"] -= days * 24 * 3600
        net.atomic_json(self.index_file(), idx)

    def test_first_load_builds_saves_and_deletes_the_raw_file(self):
        db = carddb.load()
        self.assertEqual(db.cache, "network")
        self.assertEqual(self.downloads,
                         ["https://data.scryfall.io/oracle-cards/oracle-cards-20261011090156.jsonl.gz"])
        with open(self.index_file()) as f:
            idx = json.load(f)
        self.assertEqual((idx["schema"], idx["source"]), (carddb.SCHEMA, self.downloads[0]))
        self.assertEqual(idx["updated"], "2026-10-11T09:01:56.463+00:00")
        self.assertEqual(set(idx), {"schema", "fetched", "ts", "source", "updated", "cards"})
        self.assertRegex(idx["fetched"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(db.fetched, idx["fetched"])
        self.assertEqual(os.listdir(os.path.dirname(self.index_file())), ["carddb.json"])   # raw download is gone
        self.assertEqual(len(db), 52)       # 55 objects - token - art series - the repeated "Pick Your Poison"
        self.assertEqual(db.get("Pick Your Poison")["legal"], "legal")   # the legal card wins whichever comes first

    def test_second_load_in_a_run_returns_the_same_object(self):
        first = carddb.load()
        self.assertIs(carddb.load(), first)
        self.assertEqual(len(self.downloads), 1)

    def test_a_fresh_index_on_disk_is_read_not_rebuilt(self):
        carddb.load()
        carddb._MEMO.clear()                # a new process
        db = carddb.load()
        self.assertEqual((db.cache, len(self.downloads)), ("fresh", 1))
        self.assertEqual(db.resolve("sol ring"), "Sol Ring")

    def test_an_index_older_than_a_week_is_rebuilt(self):
        carddb.load()
        self.age_index(8)
        carddb._MEMO.clear()
        self.assertEqual(carddb.load().cache, "network")
        self.assertEqual(len(self.downloads), 2)

    def test_refresh_forces_a_rebuild_once(self):
        carddb.load()
        carddb._MEMO.clear()
        db = carddb.load(refresh=True)
        self.assertEqual((db.cache, len(self.downloads)), ("network", 2))
        self.assertIs(carddb.load(refresh=True), db)        # already rebuilt in this process
        self.assertEqual(len(self.downloads), 2)

    def test_failed_rebuild_falls_back_to_the_old_index(self):
        carddb.load()
        self.age_index(30)
        carddb._MEMO.clear()
        with mock.patch.object(net, "download", side_effect=net.FetchError("scryfall", "u", "network error")):
            db = carddb.load()
        self.assertEqual((db.cache, len(db)), ("stale", 52))

    def test_failed_first_build_is_an_error(self):
        with mock.patch.object(net, "download", side_effect=net.FetchError("scryfall", "u", "network error")):
            with self.assertRaises(net.FetchError):
                carddb.load()
        self.assertFalse(os.path.exists(self.index_file()))

    def test_offline_uses_any_index_even_an_old_one_and_never_downloads(self):
        carddb.load()
        self.age_index(30)
        carddb._MEMO.clear()
        db = carddb.load(offline=True)
        self.assertEqual((db.cache, len(self.downloads)), ("stale", 1))

    def test_offline_without_an_index_says_how_to_fix_it(self):
        with self.assertRaisesRegex(net.FetchError, "offline.*warm"):
            carddb.load(offline=True)
        self.assertEqual(self.downloads, [])

    def test_an_index_from_another_schema_is_not_trusted(self):
        carddb.load()
        with open(self.index_file()) as f:
            idx = json.load(f)
        idx["schema"] = 0
        net.atomic_json(self.index_file(), idx)
        carddb._MEMO.clear()
        self.assertEqual(carddb.load().cache, "network")

    def test_an_index_from_before_the_picture_links_is_rebuilt(self):
        # schema 1 had no image keys; bumping to 2 makes every existing index download once more
        self.assertEqual(carddb.SCHEMA, 2)
        carddb.load()
        with open(self.index_file()) as f:
            idx = json.load(f)
        idx["schema"] = 1
        for rec in idx["cards"].values():
            for key in ("image", "image_back", "scryfall_uri"):
                del rec[key]
        net.atomic_json(self.index_file(), idx)
        carddb._MEMO.clear()
        db = carddb.load()
        self.assertEqual((db.cache, len(self.downloads)), ("network", 2))
        self.assertEqual(db.get("Sol Ring")["image"], "")        # the sample objects have no pictures to keep

    def test_a_damaged_download_is_a_fetch_error_and_leaves_no_files(self):
        def bad_download(url, path, *, source):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(b"\x1f\x8b not really gzip")
        with mock.patch.object(net, "download", bad_download):
            with self.assertRaisesRegex(net.FetchError, "damaged"):
                carddb.build_index()
        self.assertEqual(os.listdir(os.path.dirname(self.index_file())), [])      # raw file removed, no index

    def test_bulk_entry_accepts_the_older_listing_shape(self):
        self.listing["data"][0].pop("jsonl_download_uri")
        self.listing["data"][0]["download_uri"] = "https://data.scryfall.io/oracle-cards/old.json"
        url, entry = carddb.bulk_entry("oracle_cards")
        self.assertEqual(url, "https://data.scryfall.io/oracle-cards/old.json")

    def test_bulk_entry_reports_a_missing_type(self):
        with self.assertRaisesRegex(net.FetchError, "no art_tags file"):
            carddb.bulk_entry("art_tags")


class PictureLinksInTheIndexTests(TempCache):
    """The links reach the index file and come back through load(), for the layouts that matter."""
    def test_links_survive_build_save_and_load(self):
        # the pictures fixture stands in for the bulk file; a second load reads the saved index, as a new process would
        listing = fixture("carddb_bulk_list.json")

        def fake_download(url, path, *, source):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with gzip.open(path, "wt", encoding="utf-8") as out:
                out.write("".join(json.dumps(o) + "\n" for o in fixture("carddb_images.json")))
            return path
        info = {"url": carddb.BULK_LIST, "fetched": "2026-10-11T12:00:00Z", "cache": "network", "age_days": 0}
        with mock.patch.object(net, "fetch_json", return_value=(listing, info)), \
                mock.patch.object(net, "download", fake_download):
            built = carddb.load()
        carddb._MEMO.clear()                                    # a new process reads the file
        db = carddb.load(offline=True)
        for name in ("Hazel of the Rootbloom", "Delver of Secrets // Insectile Aberration", "Fire // Ice"):
            for key in ("image", "image_back", "scryfall_uri"):
                self.assertEqual(db.get(name)[key], built.get(name)[key], (name, key))
        self.assertIn("/back/", db.get("Delver of Secrets")["image_back"])
        self.assertEqual(db.get("Fire")["image_back"], "")
        self.assertEqual(db.by_oracle("ffffffff-0000-4000-8000-000000000004")["name"], "Fire // Ice")


class PriceQueryTests(unittest.TestCase):
    def test_queries_stay_under_the_limit_and_cover_every_name(self):
        names = [f"Some Card Name Number {i}" for i in range(200)]
        queries = carddb.price_queries(names)
        self.assertGreater(len(queries), 1)
        for query, chunk in queries:
            self.assertLessEqual(len(query), carddb.PRICE_QUERY_MAX)
            self.assertTrue(query.startswith("(") and query.endswith(") prefer:usd-low"))
            self.assertEqual(query.count("!"), len(chunk))
        self.assertEqual([n for _, chunk in queries for n in chunk], names)       # in order, none lost or repeated
        self.assertLess(len(queries), 10)                                          # few requests, not one per name

    def test_one_request_covers_a_small_list(self):
        self.assertEqual(carddb.price_queries(["Sol Ring", "Arcane Signet"]),
                         [('(!"Sol Ring" or !"Arcane Signet") prefer:usd-low', ["Sol Ring", "Arcane Signet"])])
        self.assertEqual(carddb.price_queries([]), [])

    def test_quotes_inside_names(self):
        self.assertEqual(carddb.name_term("Gaea's Cradle"), '!"Gaea\'s Cradle"')
        self.assertEqual(carddb.name_term('Kongming, "Sleeping Dragon"'), '!\'Kongming, "Sleeping Dragon"\'')
        self.assertIsNone(carddb.name_term('A "b" c\'d'))
        self.assertEqual(carddb.price_queries(['A "b" c\'d']), [])

    def test_parse_cheapest(self):
        out = carddb.parse_cheapest(fixture("carddb_search_prices.json"))
        self.assertEqual(out, {"Sol Ring": 0.99, "Skullclamp": 19.13})     # no USD price at all: left out


class CheapestPricesTests(TempCache):
    def setUp(self):
        super().setUp()
        self.db = sample_db()
        self.requests = []
        self.page = fixture("carddb_search_prices.json")
        for patcher in (mock.patch.object(carddb, "load", return_value=self.db),
                        mock.patch.object(net, "request", self.fake_request)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_request(self, url, **kw):
        self.requests.append(url)
        if isinstance(self.page, Exception):
            raise self.page
        return json.dumps(self.page).encode()

    def test_cheapest_price_beats_the_default_printing(self):
        out = carddb.cheapest_prices(["Sol Ring", "Skullclamp"])
        self.assertEqual(out, {"Sol Ring": 0.99, "Skullclamp": 19.13})       # the index says 1.16 for Sol Ring
        self.assertEqual(len(self.requests), 1)
        self.assertIn("prefer%3Ausd-low", self.requests[0])

    def test_a_name_with_no_search_price_falls_back_to_the_index(self):
        out = carddb.cheapest_prices(["Mana Crypt", "Arcane Signet", "Forest"])
        self.assertEqual(out, {"Mana Crypt": 150.0, "Arcane Signet": 0.38, "Forest": 0.10})

    def test_spellings_are_canonicalized_and_repeats_dropped(self):
        out = carddb.cheapest_prices(["sol ring", "Sol Ring", "Fire/Ice"])
        self.assertEqual(sorted(out), ["Fire // Ice", "Sol Ring"])

    def test_answers_are_cached_per_name_for_a_week(self):
        carddb.cheapest_prices(["Sol Ring"])
        carddb.cheapest_prices(["Sol Ring", "Skullclamp"])       # Skullclamp is new, Sol Ring is not asked again
        self.assertEqual(len(self.requests), 2)
        self.assertNotIn("Sol+Ring", self.requests[1])
        carddb.cheapest_prices(["Sol Ring", "Skullclamp"])
        self.assertEqual(len(self.requests), 2)
        with open(net.cache_file("prices", "cheapest")) as f:
            cache = json.load(f)
        self.assertEqual(sorted(cache["prices"]), ["Skullclamp", "Sol Ring"])
        for name in cache["prices"]:
            cache["prices"][name][1] -= 8 * 24 * 3600
        net.atomic_json(net.cache_file("prices", "cheapest"), cache)
        carddb.cheapest_prices(["Sol Ring"])
        self.assertEqual(len(self.requests), 3)

    def test_refresh_ignores_the_cache(self):
        carddb.cheapest_prices(["Sol Ring"])
        carddb.cheapest_prices(["Sol Ring"], refresh=True)
        self.assertEqual(len(self.requests), 2)

    def test_offline_never_searches_and_uses_cache_then_index(self):
        carddb.cheapest_prices(["Sol Ring"])
        out = carddb.cheapest_prices(["Sol Ring", "Arcane Signet"], offline=True)
        self.assertEqual(out, {"Sol Ring": 0.99, "Arcane Signet": 0.38})
        self.assertEqual(len(self.requests), 1)

    def test_a_failed_search_warns_and_uses_index_prices(self):
        self.page = net.FetchError("scryfall", "u", "rate limited (429)")
        out = carddb.cheapest_prices(["Sol Ring"])
        self.assertEqual(out, {"Sol Ring": 1.16})
        self.assertEqual(len(carddb.WARNINGS), 1)
        self.assertIn("429", carddb.WARNINGS[0])
        self.page = fixture("carddb_search_prices.json")             # the failure was not cached
        self.assertEqual(carddb.cheapest_prices(["Sol Ring"]), {"Sol Ring": 0.99})

    def test_no_match_at_all_is_not_an_error(self):
        self.page = net.NotFound("scryfall", "u", "no such page")
        self.assertEqual(carddb.cheapest_prices(["Sol Ring"]), {"Sol Ring": 1.16})
        self.assertEqual(carddb.WARNINGS, [])

    def test_more_pages_are_followed(self):
        page2 = "https://api.scryfall.com/cards/search?page=2"
        first = {"object": "list", "has_more": True, "next_page": page2, "data": [self.page["data"][0]]}
        last = {"object": "list", "has_more": False, "data": [self.page["data"][1]]}
        calls = []

        def paged(url, **kw):
            calls.append(url)
            return json.dumps(last if "page=2" in url else first).encode()
        with mock.patch.object(net, "request", paged):
            out = carddb.cheapest_prices(["Sol Ring", "Skullclamp"])
        self.assertEqual((len(calls), out), (2, {"Sol Ring": 0.99, "Skullclamp": 19.13}))


if __name__ == "__main__":
    unittest.main()
