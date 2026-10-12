"""Tests for roles.py and providers/scryfall_tags.py: tag trees expanded the way Scryfall's `otag:` search does,
the cache and fallback behaviour of the tag loader, role assembly, the rules-text fallback, role counts and the
bracket targets. Nothing here touches the network; caches live in a temporary directory."""
import datetime, gzip, json, os, shutil, tempfile, unittest, urllib.parse
from unittest import mock
from mtgcommander import carddb, net, roles
from mtgcommander.providers import scryfall_tags

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
TODAY = datetime.date(2026, 10, 11)


def jsonl(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def sample_db():
    cards = {}
    for obj in jsonl("carddb_bulk_sample.jsonl"):
        rec = carddb.card_record(obj)
        if rec and rec["name"] not in cards:
            cards[rec["name"]] = rec
    return carddb.CardDB(cards)


def fixture_tagsets(slugs):
    """What scryfall_tags.load would return for the sample tag tree."""
    tags, names = scryfall_tags.index_tags(jsonl("scryfall_tags_sample.jsonl"))
    return scryfall_tags.expand(tags, names, slugs)


def rec(text, type_line="Sorcery", **extra):
    """A card record made from rules text alone."""
    obj = {"object": "card", "oracle_id": "x", "name": "Test Card", "layout": "normal", "type_line": type_line,
           "oracle_text": text, "cmc": 3.0, "color_identity": [], "keywords": [],
           "legalities": {"commander": "legal"}}
    obj.update(extra)
    return carddb.card_record(obj)


FROZEN_TARGETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures",
                              "calibrate_previous.json")


class TempCache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        patcher = mock.patch.object(net, "CACHE", self.tmp)
        patcher.start()
        self.addCleanup(patcher.stop)


# ----------------------------------------------------------------------------- scryfall_tags: the tree
class TagTreeTests(unittest.TestCase):
    def setUp(self):
        self.tags, self.names = scryfall_tags.index_tags(jsonl("scryfall_tags_sample.jsonl"))
        self.ids = {o["name"]: o["oracle_id"] for o in jsonl("carddb_bulk_sample.jsonl")}

    def expand(self, *slugs):
        return scryfall_tags.expand(self.tags, self.names, slugs)

    def test_a_parent_includes_its_descendants_like_otag_search(self):
        ramp = self.expand("ramp")["ramp"]
        # Ancient Tomb is tagged `ramp` itself, Sol Ring `mana-rock`, Arcane Signet `utility-mana-rock` (a
        # grandchild), Cultivate `land-ramp`
        self.assertEqual(ramp, {self.ids[n] for n in ("Ancient Tomb", "Sol Ring", "Mind Stone", "Arcane Signet",
                                                      "Cultivate", "Rampant Growth")})
        rocks = self.expand("mana-rock")["mana-rock"]
        self.assertEqual(rocks, {self.ids[n] for n in ("Sol Ring", "Mind Stone", "Arcane Signet")})

    def test_a_leaf_holds_only_its_own_cards(self):
        self.assertEqual(self.expand("cantrip")["cantrip"], {self.ids["Brainstorm"]})

    def test_aliases_find_the_tag_and_slugs_win_over_aliases(self):
        self.assertEqual(self.expand("wipe")["wipe"], self.expand("sweeper")["sweeper"])
        tags, names = scryfall_tags.index_tags([
            {"id": "a", "slug": "first", "aliases": ["second"], "taggings": [{"oracle_id": "A"}], "child_ids": []},
            {"id": "b", "slug": "second", "aliases": [], "taggings": [{"oracle_id": "B"}], "child_ids": []}])
        self.assertEqual(scryfall_tags.expand(tags, names, ["second"]), {"second": {"B"}})

    def test_an_unknown_slug_is_an_empty_set_not_an_error(self):
        self.assertEqual(self.expand("no-such-tag"), {"no-such-tag": set()})

    def test_a_cycle_in_the_tree_does_not_loop_forever(self):
        tags, names = scryfall_tags.index_tags([
            {"id": "a", "slug": "a", "taggings": [{"oracle_id": "A"}], "child_ids": ["b"]},
            {"id": "b", "slug": "b", "taggings": [{"oracle_id": "B"}], "child_ids": ["a"]}])
        self.assertEqual(scryfall_tags.expand(tags, names, ["a"]), {"a": {"A", "B"}})

    def test_a_child_listed_but_missing_from_the_file_is_skipped(self):
        tags, names = scryfall_tags.index_tags([
            {"id": "a", "slug": "a", "taggings": [{"oracle_id": "A"}], "child_ids": ["gone"]}])
        self.assertEqual(scryfall_tags.expand(tags, names, ["a"]), {"a": {"A"}})


# ----------------------------------------------------------------------------- scryfall_tags: loading and cache
class TagLoadTests(TempCache):
    def setUp(self):
        super().setUp()
        self.downloads, self.searches = [], []
        self.bulk_ok = True
        self.listing = {"data": [{"type": "oracle_tags",
                                  "jsonl_download_uri": "https://data.scryfall.io/oracle-tags/t.jsonl.gz"}]}
        for patcher in (mock.patch.object(carddb, "bulk_entry", self.fake_bulk_entry),
                        mock.patch.object(net, "download", self.fake_download),
                        mock.patch.object(net, "request", self.fake_request)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_bulk_entry(self, kind, **kw):
        self.assertEqual(kind, "oracle_tags")
        if not self.bulk_ok:
            raise net.FetchError("scryfall", carddb.BULK_LIST, "network error")
        return self.listing["data"][0]["jsonl_download_uri"], self.listing["data"][0]

    def fake_download(self, url, path, *, source):
        self.downloads.append(url)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(os.path.join(FIXTURES, "scryfall_tags_sample.jsonl"), "rb") as src, gzip.open(path, "wb") as out:
            out.write(src.read())

    def fake_request(self, url, **kw):
        """`otag:<slug>` search pages: the sample tag tree, 2 cards per page."""
        self.searches.append(url)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        page_no = int(query.get("page", ["1"])[0])
        slug = query["q"][0][len("otag:"):]
        tags, names = scryfall_tags.index_tags(jsonl("scryfall_tags_sample.jsonl"))
        ids = sorted(scryfall_tags.expand(tags, names, [slug])[slug])
        if not ids:
            raise net.NotFound("scryfall_tags", url, "no such page")
        chunk = ids[(page_no - 1) * 2: page_no * 2]
        more = page_no * 2 < len(ids)
        body = {"object": "list", "has_more": more, "data": [{"oracle_id": i} for i in chunk]}
        if more:
            body["next_page"] = url.split("&page=")[0] + f"&page={page_no + 1}"
        return json.dumps(body).encode()

    def cache_doc(self):
        with open(net.cache_file("scryfall", "tags")) as f:
            return json.load(f)

    def age_cache(self, days):
        doc = self.cache_doc()
        doc["ts"] -= days * 24 * 3600
        net.atomic_json(net.cache_file("scryfall", "tags"), doc)

    def test_builds_from_the_bulk_file_and_keeps_only_requested_tags(self):
        out = scryfall_tags.load(["ramp", "cantrip", "wipe"])
        expected = fixture_tagsets(["ramp", "cantrip", "wipe"])
        self.assertEqual(out, expected)
        self.assertEqual(sorted(self.cache_doc()["tags"]), ["cantrip", "ramp", "wipe"])
        self.assertEqual(self.cache_doc()["method"], "bulk")
        self.assertEqual((scryfall_tags.INFO["cache"], scryfall_tags.INFO["method"]), ("network", "bulk"))
        folder = os.path.dirname(net.cache_file("scryfall", "tags"))
        self.assertEqual(os.listdir(folder), ["tags.json"])           # the raw download is gone
        self.assertEqual(self.searches, [])

    def test_result_values_are_sets_of_oracle_ids(self):
        out = scryfall_tags.load(["cantrip"])
        self.assertIsInstance(out["cantrip"], set)
        self.assertEqual(len(out["cantrip"]), 1)

    def test_a_single_slug_string_is_one_tag_not_a_list_of_letters(self):
        self.assertEqual(list(scryfall_tags.load("cantrip")), ["cantrip"])

    def test_served_from_cache_while_fresh_and_complete(self):
        scryfall_tags.load(["ramp", "cantrip"])
        out = scryfall_tags.load(["cantrip"])                   # a subset of what is cached
        self.assertEqual((len(self.downloads), scryfall_tags.INFO["cache"]), (1, "fresh"))
        self.assertEqual(out, fixture_tagsets(["cantrip"]))

    def test_asking_for_a_new_tag_rebuilds_and_keeps_the_old_ones(self):
        scryfall_tags.load(["ramp"])
        scryfall_tags.load(["cantrip"])
        self.assertEqual(len(self.downloads), 2)
        self.assertEqual(sorted(self.cache_doc()["tags"]), ["cantrip", "ramp"])
        scryfall_tags.load(["ramp"])
        self.assertEqual(len(self.downloads), 2)

    def test_an_unknown_slug_is_cached_as_empty_so_it_does_not_rebuild_every_run(self):
        self.assertEqual(scryfall_tags.load(["no-such-tag"]), {"no-such-tag": set()})
        scryfall_tags.load(["no-such-tag"])
        self.assertEqual(len(self.downloads), 1)

    def test_older_than_thirty_days_rebuilds(self):
        scryfall_tags.load(["ramp"])
        self.age_cache(29)
        scryfall_tags.load(["ramp"])
        self.assertEqual(len(self.downloads), 1)
        self.age_cache(2)
        scryfall_tags.load(["ramp"])
        self.assertEqual(len(self.downloads), 2)

    def test_refresh_rebuilds(self):
        scryfall_tags.load(["ramp"])
        scryfall_tags.load(["ramp"], refresh=True)
        self.assertEqual(len(self.downloads), 2)

    def test_failed_rebuild_serves_the_stale_cache(self):
        scryfall_tags.load(["ramp"])
        self.age_cache(40)
        self.bulk_ok = False
        with mock.patch.object(net, "request", side_effect=net.FetchError("scryfall_tags", "u", "network error")):
            out = scryfall_tags.load(["ramp"])
        self.assertEqual((out, scryfall_tags.INFO["cache"]), (fixture_tagsets(["ramp"]), "stale"))

    def test_offline_serves_any_cache_and_never_downloads(self):
        scryfall_tags.load(["ramp"])
        self.age_cache(90)
        out = scryfall_tags.load(["ramp"], offline=True)
        self.assertEqual((out, scryfall_tags.INFO["cache"], len(self.downloads)),
                         (fixture_tagsets(["ramp"]), "stale", 1))

    def test_offline_without_the_tags_says_how_to_fix_it(self):
        with self.assertRaisesRegex(net.FetchError, "offline.*warm"):
            scryfall_tags.load(["ramp"], offline=True)
        scryfall_tags.load(["ramp"])
        with self.assertRaisesRegex(net.FetchError, "offline"):
            scryfall_tags.load(["cantrip"], offline=True)          # cached, but not this tag
        self.assertEqual(len(self.downloads), 1)

    def test_falls_back_to_otag_searches_when_the_bulk_file_is_unavailable(self):
        self.bulk_ok = False
        out = scryfall_tags.load(["ramp", "sweeper"])
        self.assertEqual(out, fixture_tagsets(["ramp", "sweeper"]))
        self.assertEqual(self.cache_doc()["method"], "search")
        self.assertTrue(all("otag%3A" in u for u in self.searches))
        self.assertGreater(len(self.searches), 2)                  # ramp has 6 cards: three pages of two

    def test_a_damaged_download_also_falls_back_to_searches(self):
        def bad(url, path, *, source):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(b"\x1f\x8bgarbage")
        with mock.patch.object(net, "download", bad):
            out = scryfall_tags.load(["cantrip"])
        self.assertEqual((out, self.cache_doc()["method"]), (fixture_tagsets(["cantrip"]), "search"))
        self.assertEqual(os.listdir(os.path.dirname(net.cache_file("scryfall", "tags"))), ["tags.json"])

    def test_a_tag_nobody_uses_is_empty_in_search_mode(self):
        self.bulk_ok = False
        self.assertEqual(scryfall_tags.load(["no-such-tag"]), {"no-such-tag": set()})

    def test_both_sources_failing_is_an_error_without_a_cache(self):
        self.bulk_ok = False
        with mock.patch.object(net, "request", side_effect=net.FetchError("scryfall_tags", "u", "network error")):
            with self.assertRaises(net.FetchError):
                scryfall_tags.load(["ramp"])


class OldTagCacheTests(TempCache):
    """A tag cache saved before the attribute slugs existed must keep the roles working offline: the roles and the
    attributes are two separate loads, and only the second one fails. Uses the real scryfall_tags.load over a
    temporary cache; the downloads are the sample tag tree."""

    def setUp(self):
        super().setUp()
        roles.reset()
        del roles.WARNINGS[:]
        self.addCleanup(roles.reset)
        self.addCleanup(roles.WARNINGS.clear)
        self.db = sample_db()
        self.downloads = []

        def fake_download(url, path, *, source):
            self.downloads.append(url)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(os.path.join(FIXTURES, "scryfall_tags_sample.jsonl"), "rb") as src, \
                    gzip.open(path, "wb") as out:
                out.write(src.read())
        listing = ("https://data.scryfall.io/oracle-tags/t.jsonl.gz", {"type": "oracle_tags"})
        for patcher in (mock.patch.object(carddb, "bulk_entry", return_value=listing),
                        mock.patch.object(net, "download", fake_download),
                        mock.patch.object(roles, "_today", return_value=TODAY)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def save_role_tags_only(self):
        """Run once while online with just the role slugs, as a cache from before attributes existed would hold."""
        roles.tag(["Sol Ring"], self.db)
        roles.reset()
        self.assertEqual(len(self.downloads), 1)

    def test_roles_still_work_offline_when_only_the_attribute_tags_are_missing(self):
        self.save_role_tags_only()
        found = roles.tag(["Sol Ring", "Swords to Plowshares"], self.db, offline=True)
        attrs = roles.attributes(["Swords to Plowshares"], self.db, offline=True)
        self.assertEqual(found, {"Sol Ring": {"ramp"}, "Swords to Plowshares": {"removal"}})
        self.assertEqual(attrs, {"Swords to Plowshares": frozenset()})
        self.assertEqual(len(self.downloads), 1)                      # offline never downloads
        self.assertEqual(len(roles.WARNINGS), 1)
        self.assertIn("attributes unavailable", roles.WARNINGS[0])
        self.assertIn("offline", roles.WARNINGS[0])                   # the reason from scryfall_tags comes along
        self.assertFalse(roles.attributes_loaded())

    def test_asking_for_attributes_online_saves_them_beside_the_role_tags(self):
        self.save_role_tags_only()
        attrs = roles.attributes(["Swords to Plowshares"], self.db)
        self.assertEqual(attrs["Swords to Plowshares"], {"removal-creature", "removal-exile", "spot-removal"})
        self.assertEqual(len(self.downloads), 2)                      # one more download for the new slugs
        roles.reset()
        found = roles.tag(["Sol Ring"], self.db, offline=True)        # the role tags were kept in the same file
        attrs = roles.attributes(["Swords to Plowshares"], self.db, offline=True)
        self.assertEqual((found, len(self.downloads)), ({"Sol Ring": {"ramp"}}, 2))
        self.assertIn("removal-exile", attrs["Swords to Plowshares"])
        self.assertTrue(roles.attributes_loaded())
        self.assertEqual(roles.WARNINGS, [])


# ----------------------------------------------------------------------------- roles: tag sets → roles
class RoleDefinitionTests(unittest.TestCase):
    def test_every_role_has_tags_and_no_role_is_missing(self):
        self.assertEqual(set(roles.ROLE_TAGS), set(roles.ROLES))
        self.assertEqual(set(roles.LABELS), set(roles.ROLES))
        self.assertTrue(roles.CARRYOVER <= set(roles.ROLES))
        for role, slugs in roles.ROLE_TAGS.items():
            self.assertTrue(slugs, role)

    def test_subtractions_refer_to_real_includes(self):
        for (role, slug), minus in roles.TAG_MINUS.items():
            self.assertIn(slug, roles.ROLE_TAGS[role])
            self.assertTrue(minus)

    def test_all_slugs_covers_includes_subtractions_and_land_tags(self):
        slugs = roles.all_slugs()
        self.assertEqual(slugs, sorted(set(slugs)))
        for needed in ("mana-rock", "cantrip", "sweeper", "tutor-land", "reanimate-self", "ramp", "overrun"):
            self.assertIn(needed, slugs)

    def test_role_sets_apply_the_subtractions_to_the_right_include_only(self):
        tagsets = {"pure-draw": {"a", "b", "c"}, "cantrip": {"b"}, "mana-rock": {"c"}, "draw-engine": {"b", "d"},
                   "removal": {"r", "w"}, "sweeper": {"w"}, "ramp": {"land1", "x"}}
        ids, land_ramp = roles.role_sets(tagsets)
        self.assertEqual(ids["draw"], {"a", "b", "d"})       # b is a cantrip but also an engine; c is a rock
        self.assertEqual(ids["removal"], {"r"})
        self.assertEqual(ids["wipe"], {"w"})
        self.assertEqual(land_ramp, {"land1", "x"})
        self.assertEqual(ids["counter"], set())              # a tag that was not loaded is just empty

    def test_sample_tree_assembles_into_the_expected_roles(self):
        ids, land_ramp = roles.role_sets(fixture_tagsets(roles.all_slugs()))
        by_name = {o["name"]: o["oracle_id"] for o in jsonl("carddb_bulk_sample.jsonl")}

        def roles_of(name):
            return {r for r, members in ids.items() if by_name[name] in members}
        self.assertEqual(roles_of("Sol Ring"), {"ramp"})
        self.assertEqual(roles_of("Arcane Signet"), {"ramp"})
        self.assertEqual(roles_of("Mind Stone"), {"ramp"})                 # a rock that can draw is still a rock
        self.assertEqual(roles_of("Brainstorm"), set())                    # a cantrip is not card advantage
        self.assertEqual(roles_of("Rhystic Study"), {"draw"})
        self.assertEqual(roles_of("Skullclamp"), {"draw"})
        self.assertEqual(roles_of("Rampant Growth"), {"ramp"})             # fetching a basic is ramp, not a tutor
        self.assertEqual(roles_of("Demonic Tutor"), {"tutor"})
        self.assertEqual(roles_of("Wrath of God"), {"wipe"})               # not also removal
        self.assertEqual(roles_of("Swords to Plowshares"), {"removal"})
        self.assertEqual(roles_of("Reanimate"), {"recursion"})
        self.assertEqual(roles_of("Relentless Rats"), set())               # reanimates itself only
        self.assertEqual(roles_of("Exsanguinate"), {"finisher"})
        self.assertIn(by_name["Ancient Tomb"], land_ramp)


class TagTests(unittest.TestCase):
    """roles.tag with the sample tag tree standing in for scryfall_tags.load."""
    def setUp(self):
        roles.reset()
        del roles.WARNINGS[:]
        self.addCleanup(roles.reset)
        self.addCleanup(roles.WARNINGS.clear)
        self.db = sample_db()
        self.loads = []
        for patcher in (mock.patch.object(scryfall_tags, "load", self.fake_load),
                        mock.patch.object(roles, "_today", return_value=TODAY),
                        mock.patch.dict(net.MODE, {"offline": False})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_load(self, tags, **kw):
        self.loads.append((list(tags), kw))
        return fixture_tagsets(tags)

    def tag(self, *names):
        return roles.tag(list(names), self.db)

    def test_roles_by_card(self):
        cases = {
            "Sol Ring": {"ramp"}, "Cultivate": {"ramp"}, "Mind Stone": {"ramp"}, "Brainstorm": set(),
            "Rhystic Study": {"draw"}, "Swords to Plowshares": {"removal"}, "Fire // Ice": {"removal"},
            "Wrath of God": {"wipe"}, "Counterspell": {"counter"}, "Demonic Tutor": {"tutor"},
            "Rampant Growth": {"ramp"}, "Eternal Witness": {"recursion"}, "Heroic Intervention": {"protection"},
            "Craterhoof Behemoth": {"finisher"}, "Exsanguinate": {"finisher"}, "Forest": set(),
        }
        out = self.tag(*cases)
        for name, expected in cases.items():
            self.assertEqual(out[name], expected, name)

    def test_lands_get_no_role_except_ramp_for_lands_that_make_extra_mana(self):
        out = self.tag("Ancient Tomb", "Command Tower", "Terramorphic Expanse", "Forest")
        self.assertEqual(out, {"Ancient Tomb": {"ramp"}, "Command Tower": set(),
                               "Terramorphic Expanse": set(), "Forest": set()})

    def test_a_modal_dfc_with_a_land_back_is_tagged_as_its_front_spell(self):
        name = "Witch Enchanter // Witch-Blessed Meadow"
        self.assertEqual(self.tag(name), {name: set()})

    def test_only_new_cards_without_role_tags_use_the_text_fallback(self):
        out = self.tag("Fresh Assassin", "Old Assassin")
        self.assertEqual(out["Fresh Assassin"], {"removal"})     # released a month ago, not tagged yet
        self.assertEqual(out["Old Assassin"], set())             # same text, but old: Scryfall's taggers left it out

    def test_the_fallback_does_not_override_tags(self):
        db = self.db
        tagged = db.cards["Counterspell"]["oracle_id"]
        fresh = dict(db.cards["Fresh Assassin"], oracle_id=tagged)       # a new card that does have a tag
        self.assertEqual(roles.roles_of(fresh, roles.role_sets(fixture_tagsets(roles.all_slugs()))), {"counter"})

    def test_unknown_names_get_an_empty_set_and_every_name_is_present_once(self):
        out = self.tag("Sol Ring", "Nope", "Sol Ring", "sol ring")
        self.assertEqual(set(out), {"Sol Ring", "Nope", "sol ring"})
        self.assertEqual((out["Nope"], out["sol ring"]), (set(), {"ramp"}))

    def test_tags_are_loaded_once_per_process_with_the_modes_passed_through(self):
        roles.tag(["Sol Ring"], self.db, refresh=True, offline=False)
        roles.tag(["Cultivate"], self.db)
        self.assertEqual(len(self.loads), 1)
        self.assertEqual(self.loads[0][0], roles.all_slugs())
        self.assertEqual(self.loads[0][1], {"refresh": True, "offline": False})

    def offline_then_online(self, call):
        """Run `call(offline)` offline while the tag data is missing, then online while it is there; the tag loads
        it saw are in self.loads."""
        real = self.fake_load

        def load(tags, **kw):
            if kw.get("offline"):
                raise net.FetchError("scryfall_tags", "u", "offline (--offline) and no tag cache")
            return real(tags, **kw)
        with mock.patch.object(scryfall_tags, "load", load):
            first = call(True)
            second = call(False)
        return first, second

    def test_a_load_that_failed_offline_is_not_remembered_so_the_same_call_online_still_works(self):
        # the deck server tries offline to list decks before it opens one online: the second call reads the tags
        self.offline_then_online(lambda offline: roles.tag(["Sol Ring"], self.db, offline=offline))
        self.assertEqual([kw["offline"] for _, kw in self.loads], [False])             # the online call went to the data
        self.assertIsNotNone(roles._MEMO["sets"])                                      # and now the sets are kept
        self.assertEqual(len(roles.WARNINGS), 1)                                       # only the offline try warned

    def test_a_load_that_failed_with_the_run_wide_mode_offline_is_not_remembered_either(self):
        # offline=None means "the run-wide mode"; here that is --offline, so the next call tries again
        with mock.patch.dict(net.MODE, {"offline": True}), mock.patch.object(
                scryfall_tags, "load", side_effect=net.FetchError("scryfall_tags", "u", "no tag cache")) as load:
            roles.tag(["Sol Ring"], self.db)
            roles.tag(["Sol Ring"], self.db)
        self.assertEqual(load.call_count, 2)

    def test_a_load_that_failed_online_is_remembered_and_not_asked_again(self):
        # the existing rule for a real outage: one warning, no retry on every call
        with mock.patch.object(scryfall_tags, "load", side_effect=net.FetchError("scryfall_tags", "u", "HTTP 503")) as load:
            roles.tag(["Sol Ring"], self.db, offline=False)
            roles.tag(["Sol Ring"], self.db, offline=False)
        self.assertEqual(load.call_count, 1)

    def test_without_tag_data_every_card_falls_back_to_text_and_a_warning_is_left(self):
        with mock.patch.object(scryfall_tags, "load", side_effect=net.FetchError("scryfall_tags", "u", "offline")):
            out = self.tag("Old Assassin", "Hazel of the Rootbloom", "Ancient Tomb", "Command Tower", "Sol Ring")
            self.tag("Sol Ring")
        self.assertEqual(out["Old Assassin"], {"removal"})
        self.assertEqual(out["Hazel of the Rootbloom"], {"ramp"})
        self.assertEqual(out["Ancient Tomb"], {"ramp"})
        self.assertEqual(out["Command Tower"], set())
        self.assertEqual(len(roles.WARNINGS), 1)                   # reported once, not retried per call
        self.assertIn("function tags unavailable", roles.WARNINGS[0])


class AttributeDefinitionTests(unittest.TestCase):
    """The attribute slugs, checked against the sample tag tree the way the role slugs are: each one must be a tag
    in it, so a misspelled slug (which would load as an empty set and quietly count nothing) is caught here."""

    def test_every_attribute_slug_is_a_tag_of_the_sample_tree(self):
        _, names = scryfall_tags.index_tags(jsonl("scryfall_tags_sample.jsonl"))
        self.assertEqual([slug for slug in roles.ATTRIBUTE_TAGS if slug not in names], [])

    def test_there_is_no_repeated_slug_and_every_role_free_fact_the_metrics_read_is_listed(self):
        self.assertEqual(len(roles.ATTRIBUTE_TAGS), len(set(roles.ATTRIBUTE_TAGS)))
        for needed in ("removal-permanent", "removal-nonland", "removal-burn", "removal-toughness", "doom-blade",
                       "sweeper", "counterspell", "mana-rock", "mana-dork", "land-ramp", "extra-land", "draw-engine",
                       "repeatable-impulsive-draw", "pure-draw", "burst-draw", "impulsive-draw", "overrun",
                       "extra-combat-phase", "alternate-win-condition", "burn-player-each", "drain-life",
                       "opponent-loses-life", "theft-mass", "tapland", "conditional-tapland", "evasion"):
            self.assertIn(needed, roles.ATTRIBUTE_TAGS)

    def test_a_slug_stands_for_its_subtree_as_otag_search_does(self):
        # in Scryfall's tree removal-permanent is a child of removal-creature: a card tagged with the child is
        # also tagged with the parent
        sets = fixture_tagsets(["removal-creature", "removal-permanent"])
        ids = {o["name"]: o["oracle_id"] for o in jsonl("carddb_bulk_sample.jsonl")}
        self.assertIn(ids["Old Assassin"], sets["removal-creature"])
        self.assertIn(ids["Old Assassin"], sets["removal-permanent"])
        self.assertNotIn(ids["Swords to Plowshares"], sets["removal-permanent"])


class AttributeTests(unittest.TestCase):
    """roles.attributes with the sample tag tree standing in for scryfall_tags.load."""

    def setUp(self):
        roles.reset()
        del roles.WARNINGS[:]
        self.addCleanup(roles.reset)
        self.addCleanup(roles.WARNINGS.clear)
        self.db = sample_db()
        self.loads = []
        for patcher in (mock.patch.object(scryfall_tags, "load", self.fake_load),
                        mock.patch.dict(net.MODE, {"offline": False})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_load(self, tags, **kw):
        self.loads.append((list(tags), kw))
        return fixture_tagsets(tags)

    def test_each_card_gets_the_attribute_slugs_it_carries(self):
        out = roles.attributes(["Swords to Plowshares", "Wrath of God", "Heroic Intervention", "Sol Ring"], self.db)
        self.assertEqual(out["Swords to Plowshares"], {"removal-creature", "removal-exile", "spot-removal"})
        self.assertEqual(out["Wrath of God"], {"removal-creature", "removal-destroy", "sweeper"})
        self.assertEqual(out["Heroic Intervention"], {"protects-creature", "gives-indestructible", "gives-hexproof"})
        self.assertEqual(out["Sol Ring"], {"mana-rock"})          # a role's slug is an attribute slug too
        self.assertEqual(roles.attributes(["Eternal Witness"], self.db)["Eternal Witness"], frozenset())
        self.assertTrue(all(isinstance(v, frozenset) for v in out.values()))

    def test_a_slug_that_is_both_a_role_tag_and_an_attribute_tag_is_reported(self):
        out = roles.attributes(["Counterspell", "Wrath of God"], self.db)
        self.assertEqual(out["Counterspell"], {"counterspell"})
        self.assertIn("sweeper", out["Wrath of God"])

    def test_a_card_in_a_child_tag_also_carries_the_parent(self):
        out = roles.attributes(["Old Assassin"], self.db)
        self.assertEqual(out["Old Assassin"], {"removal-creature", "removal-permanent", "removal-destroy"})

    def test_every_distinct_name_is_present_once_and_an_unknown_name_has_no_attributes(self):
        out = roles.attributes(["Swords to Plowshares", "Nope", "Swords to Plowshares", "swords to plowshares"],
                               self.db)
        self.assertEqual(set(out), {"Swords to Plowshares", "Nope", "swords to plowshares"})
        self.assertEqual(out["Nope"], frozenset())
        self.assertEqual(out["swords to plowshares"], out["Swords to Plowshares"])    # another spelling still finds it

    def test_the_attribute_tags_are_one_load_of_their_own_with_the_modes_passed_through(self):
        roles.tag(["Sol Ring"], self.db)
        roles.attributes(["Sol Ring"], self.db, refresh=True, offline=False)
        roles.attributes(["Wrath of God"], self.db)
        self.assertEqual([slugs for slugs, _ in self.loads], [roles.all_slugs(), list(roles.ATTRIBUTE_TAGS)])
        self.assertEqual(self.loads[1][1], {"refresh": True, "offline": False})

    def test_unavailable_tags_leave_empty_sets_one_warning_and_no_retry(self):
        with mock.patch.object(scryfall_tags, "load", side_effect=net.FetchError("scryfall_tags", "u", "offline")):
            out = roles.attributes(["Swords to Plowshares", "Wrath of God"], self.db)
            roles.attributes(["Swords to Plowshares"], self.db)
        self.assertEqual(out, {"Swords to Plowshares": frozenset(), "Wrath of God": frozenset()})
        self.assertEqual(len(roles.WARNINGS), 1)                    # reported once, not retried per call
        self.assertIn("function tags for card attributes unavailable", roles.WARNINGS[0])
        self.assertFalse(roles.attributes_loaded())

    def test_attributes_that_failed_to_load_offline_load_when_the_same_call_is_made_online(self):
        # the deck list tries offline first; opening the deck online must still be able to read the tags
        real = self.fake_load

        def load(tags, **kw):
            if kw.get("offline"):
                raise net.FetchError("scryfall_tags", "u", "offline (--offline) and no tag cache")
            return real(tags, **kw)
        with mock.patch.object(scryfall_tags, "load", load):
            first = roles.attributes(["Sol Ring"], self.db, offline=True)
            self.assertFalse(roles.attributes_loaded())
            second = roles.attributes(["Sol Ring"], self.db, offline=False)
        self.assertEqual((first["Sol Ring"], second["Sol Ring"]), (frozenset(), {"mana-rock"}))
        self.assertTrue(roles.attributes_loaded())

    def test_attributes_are_loaded_once_a_call_has_read_them(self):
        self.assertFalse(roles.attributes_loaded())                 # before the first call
        roles.attributes(["Sol Ring"], self.db)
        self.assertTrue(roles.attributes_loaded())
        roles.reset()
        self.assertFalse(roles.attributes_loaded())

    def test_the_attribute_load_does_not_touch_the_role_warnings(self):
        with mock.patch.object(scryfall_tags, "load", side_effect=net.FetchError("scryfall_tags", "u", "offline")):
            roles.attributes(["Sol Ring"], self.db)
        self.assertEqual(len(roles.WARNINGS), 1)
        self.assertNotIn("roles come from rules-text", roles.WARNINGS[0])    # the roles' own warning is another one


class TextFallbackTests(unittest.TestCase):
    def roles(self, text, type_line="Sorcery"):
        return roles.text_roles(rec(text, type_line))

    def test_each_role_fires_on_typical_text(self):
        cases = [
            ("{T}: Add {G}.", "Creature — Elf", "ramp"),
            ("Search your library for a basic land card, put it onto the battlefield tapped.", "Sorcery", "ramp"),
            ("Search your library for up to two basic land cards, put them onto the battlefield tapped.",
             "Sorcery", "ramp"),
            ("You may play an additional land on each of your turns.", "Enchantment", "ramp"),
            ("Draw two cards.", "Sorcery", "draw"),
            ("When this creature enters, draw a card.", "Creature — Merfolk", "draw"),
            ("Destroy target creature.", "Instant", "removal"),
            ("Exile target nonland permanent.", "Instant", "removal"),
            ("Test Card deals 3 damage to any target.", "Instant", "removal"),
            ("Target creature gets -3/-3 until end of turn.", "Instant", "removal"),
            ("Destroy all creatures.", "Sorcery", "wipe"),
            ("Test Card deals 3 damage to each creature.", "Sorcery", "wipe"),
            ("All creatures get -2/-2 until end of turn.", "Sorcery", "wipe"),
            ("Counter target spell.", "Instant", "counter"),
            ("Counter target noncreature spell unless its controller pays {2}.", "Instant", "counter"),
            ("Counter target activated or triggered ability.", "Instant", "counter"),
            ("Permanents you control gain hexproof and indestructible until end of turn.", "Instant", "protection"),
            ("Target creature gains protection from the color of your choice until end of turn.",
             "Instant", "protection"),
            ("Target creature you control phases out.", "Instant", "protection"),
            ("Return target creature card from your graveyard to your hand.", "Sorcery", "recursion"),
            ("Put target creature card from a graveyard onto the battlefield under your control.",
             "Sorcery", "recursion"),
            ("Search your library for a card, put it into your hand, then shuffle.", "Sorcery", "tutor"),
            ("Search your library for an artifact card, reveal it, put it into your hand.", "Sorcery", "tutor"),
            ("Creatures you control get +3/+3 and gain trample until end of turn.", "Sorcery", "finisher"),
            ("Each opponent loses 2 life.", "Sorcery", "finisher"),
            ("After this main phase, there is an additional combat phase.", "Sorcery", "finisher"),
            ("You win the game.", "Enchantment", "finisher"),
        ]
        for text, type_line, role in cases:
            self.assertIn(role, self.roles(text, type_line), text)

    def test_texts_that_look_similar_but_are_not_the_role(self):
        cases = [
            ("Search your library for a basic land card, reveal it, put it into your hand.", "tutor"),   # ramp
            ("Search your library for up to two Forest cards.", "tutor"),
            ("Destroy all creatures.", "removal"),                  # a wipe is not spot removal
            ("Put a +1/+1 counter on target creature.", "counter"),
            ("Creatures you control get +1/+1.", "finisher"),       # an anthem is not a finisher
            ("Search your library for a creature card, reveal it, put it into your hand.", "ramp"),
            ("Target creature gets +2/+2 until end of turn.", "removal"),
            ("Exile target card from a graveyard.", "recursion"),
            ("Flying", "draw"),
        ]
        for text, role in cases:
            self.assertNotIn(role, self.roles(text), text)

    def test_a_card_can_fill_several_roles(self):
        self.assertEqual(self.roles("Destroy target creature. Draw a card."), {"removal", "draw"})

    def test_a_land_only_ever_ramps_and_only_for_extra_mana(self):
        self.assertEqual(roles.text_roles(rec("{T}: Add {C}{C}. Test Card deals 2 damage to you.", "Land")), {"ramp"})
        self.assertEqual(roles.text_roles(rec("{T}: Add {B} for each Swamp you control.", "Land")), {"ramp"})
        self.assertEqual(roles.text_roles(rec("{T}: Add one mana of any color.", "Land")), set())
        self.assertEqual(roles.text_roles(rec("{T}: Add {G}. Draw a card.", "Land")), set())

    def test_bounce_lands_and_sacrifice_lands_ramp_but_filter_lands_only_convert(self):
        def land(text):
            return roles.text_roles(rec(text, "Land"))
        bounce = "When Test Card enters, return a land you control to its owner's hand. {T}: Add {B}{G}."
        self.assertEqual(land(bounce), {"ramp"})
        self.assertEqual(land("{T}, Sacrifice Test Card: Add {C}{C}."), {"ramp"})
        self.assertEqual(land("{T}, Pay 1 life: Add {B}{G}."), {"ramp"})
        # filter lands only convert mana (Viridescent Bog, Mystic Gate)
        self.assertEqual(land("{T}: Add {C}. {1}, {T}: Add {B}{G}."), set())
        self.assertEqual(land("{T}: Add {C}. {W/U}, {T}: Add {W}{W}, {W}{U}, or {U}{U}."), set())

    def test_a_modal_dfcs_land_face_is_not_called_ramp(self):
        mdfc = next(carddb.card_record(o) for o in jsonl("carddb_bulk_sample.jsonl")
                    if o["name"].startswith("Witch Enchanter"))
        self.assertEqual(roles.text_roles(mdfc), {"removal"})       # "{T}: Add {W}" is on the land back

    def test_matching_ignores_case(self):
        self.assertIn("counter", self.roles("COUNTER TARGET SPELL."))


class BasicLandSearchTests(unittest.TestCase):
    """How many basic lands a card can take from your library, read from real rules text. A deck needs that many
    basics left or the card finds nothing. Only a search of your own library for a *basic* land counts."""
    TWO_BASICS = ("Search your library for up to two basic land cards, reveal those cards, put one onto the "
                  "battlefield tapped and the other into your hand, then shuffle.")
    FETCH_FOR_A_BASIC = "Search your library for a basic land card, put it onto the battlefield tapped, then shuffle."

    def searches(self, text, type_line="Sorcery"):
        return roles.basic_land_searches(rec(text, type_line))

    def test_a_card_that_fetches_basic_lands_counts_how_many_it_can_take(self):
        cases = [
            ("Cultivate", "Sorcery", self.TWO_BASICS, 2),
            ("Kodama's Reach", "Sorcery — Arcane", self.TWO_BASICS, 2),
            ("Evolving Wilds", "Land", "{T}, Sacrifice Test Card: " + self.FETCH_FOR_A_BASIC, 1),
            ("Terramorphic Expanse", "Land", "{T}, Sacrifice Test Card: " + self.FETCH_FOR_A_BASIC, 1),
            ("Sakura-Tribe Elder", "Creature — Snake Shaman", "Sacrifice Test Card: Search your library for a "
             "basic land card, put that card onto the battlefield tapped, then shuffle.", 1),
            ("Myriad Landscape", "Land", "Test Card enters tapped. {T}: Add {C}. {2}, {T}, Sacrifice Test Card: "
             "Search your library for up to two basic land cards that share a land type, put them onto the "
             "battlefield tapped, then shuffle.", 2),
            ("Blighted Woodland", "Land", "{T}: Add {C}. {3}{G}, {T}, Sacrifice Test Card: Search your library for "
             "up to two basic land cards, put them onto the battlefield tapped, then shuffle.", 2),
            ("Land Tax", "Enchantment", "At the beginning of your upkeep, if an opponent controls more lands than "
             "you, you may search your library for up to three basic land cards, reveal them, put them into your "
             "hand, then shuffle.", 3),
            ("Boundless Realms", "Sorcery", "Search your library for up to X basic land cards, where X is the "
             "number of lands you control. Put those cards onto the battlefield tapped, then shuffle.", 2),
        ]
        for name, type_line, text, expected in cases:
            with self.subTest(card=name):
                self.assertEqual(self.searches(text, type_line), expected)

    def test_a_search_for_a_land_type_without_the_word_basic_counts_nothing(self):
        # These can fetch a dual land that carries the type (Overgrown Tomb is a Swamp Forest), so they need no
        # basic left in the deck; counting them would force extra basics into a deck full of fetch lands.
        cases = [
            ("Nature's Lore", "Sorcery", "Search your library for a Forest card, put that card onto the "
             "battlefield, then shuffle."),
            ("Farseek", "Sorcery", "Search your library for a Plains, Island, Swamp, or Mountain card, put it "
             "onto the battlefield tapped, then shuffle."),
            ("Verdant Catacombs", "Land", "{T}, Pay 1 life, Sacrifice Test Card: Search your library for a Swamp "
             "or Forest card, put it onto the battlefield, then shuffle."),
            ("Binding the Old Gods", "Enchantment — Saga", "I — Destroy target nonland permanent an opponent "
             "controls. II — Search your library for a Forest card, put it onto the battlefield tapped, then "
             "shuffle. III — Creatures you control gain deathtouch until end of turn."),
            ("Skyshroud Claim", "Sorcery", "Search your library for up to two Forest cards, put them onto the "
             "battlefield, then shuffle."),
        ]
        for name, type_line, text in cases:
            with self.subTest(card=name):
                self.assertEqual(self.searches(text, type_line), 0)

    def test_a_search_of_another_players_library_or_for_any_land_or_card_counts_nothing(self):
        cases = [
            ("Path to Exile", "Instant", "Exile target creature. Its controller may search their library for a "
             "basic land card, put that card onto the battlefield tapped, then shuffle."),
            ("Assassin's Trophy", "Instant", "Destroy target permanent an opponent controls. Its controller may "
             "search their library for a basic land card, put it onto the battlefield, then shuffle."),
            ("Ghost Quarter", "Land", "{T}: Add {C}. {T}, Sacrifice Test Card: Destroy target land. Its "
             "controller may search their library for a basic land card, put it onto the battlefield tapped, "
             "then shuffle."),
            ("Expedition Map", "Artifact", "{2}, {T}, Sacrifice Test Card: Search your library for a land card, "
             "reveal it, put it into your hand, then shuffle."),
            ("Demonic Tutor", "Sorcery", "Search your library for a card, put that card into your hand, then "
             "shuffle."),
        ]
        for name, type_line, text in cases:
            with self.subTest(card=name):
                self.assertEqual(self.searches(text, type_line), 0)

    def test_every_search_in_the_text_is_added_up(self):
        # A made-up card with two searches: one basic land when it enters, up to two when it dies.
        text = ("When Test Card enters, search your library for a basic land card, put it onto the battlefield "
                "tapped, then shuffle. When Test Card dies, search your library for up to two basic land cards, "
                "reveal them, put them into your hand, then shuffle.")
        self.assertEqual(self.searches(text, "Creature — Elemental"), 3)

    def test_how_many_is_read_from_the_count_word(self):
        for how_many, expected in (("a", 1), ("an", 1), ("one", 1), ("two", 2), ("up to two", 2), ("three", 3),
                                   ("up to three", 3), ("X", 2), ("up to X", 2), ("that many", 2)):
            with self.subTest(how_many=how_many):
                text = f"Search your library for {how_many} basic land cards, put them into your hand."
                self.assertEqual(self.searches(text), expected)

    def test_a_basic_land_search_in_words_the_count_list_lacks_still_counts_one(self):
        self.assertEqual(self.searches("Search your library for up to four basic land cards, then shuffle."), 1)

    def test_a_card_with_no_search_or_a_plain_land_counts_nothing(self):
        self.assertEqual(self.searches("Draw two cards.", "Sorcery"), 0)
        self.assertEqual(self.searches("{T}: Add {C}.", "Land"), 0)
        self.assertEqual(self.searches("", "Basic Land — Forest"), 0)


class LandSearchTests(unittest.TestCase):
    """Whether a card finds you a land (of any kind, by type or as a basic): what separates a fetch land from a
    land that only makes colorless mana."""

    def finds_land(self, text, type_line="Land"):
        return roles.searches_library_for_land(rec(text, type_line))

    def test_cards_that_search_your_own_library_for_a_land_do(self):
        cases = [
            ("Verdant Catacombs", "{T}, Pay 1 life, Sacrifice Test Card: Search your library for a Swamp or "
             "Forest card, put it onto the battlefield, then shuffle."),
            ("Evolving Wilds", "{T}, Sacrifice Test Card: Search your library for a basic land card, put it onto "
             "the battlefield tapped, then shuffle."),
            ("Myriad Landscape", "Test Card enters tapped. {T}: Add {C}. {2}, {T}, Sacrifice Test Card: Search your "
             "library for up to two basic land cards that share a land type, put them onto the battlefield tapped, "
             "then shuffle."),
            ("Flooded Strand", "{T}, Pay 1 life, Sacrifice Test Card: Search your library for a Plains or Island "
             "card, put it onto the battlefield, then shuffle."),
            ("Fabled Passage", "{T}, Sacrifice Test Card: Search your library for a basic land card, put it onto "
             "the battlefield tapped, then shuffle. Then if you control four or more lands, untap that land."),
        ]
        for name, text in cases:
            with self.subTest(card=name):
                self.assertTrue(self.finds_land(text))

    def test_a_search_for_something_else_or_in_another_library_does_not(self):
        cases = [
            ("Urza's Saga", "{T}: Add {C}. {2}, {T}: Create a Construct token. {2}, {T}, Sacrifice Test Card: Search "
             "your library for an artifact card with mana cost {0} or {1}, put it onto the battlefield, then "
             "shuffle."),
            ("Ghost Quarter", "{T}: Add {C}. {T}, Sacrifice Test Card: Destroy target land. Its controller may "
             "search their library for a basic land card, put it onto the battlefield tapped, then shuffle."),
            ("Ancient Tomb", "{T}: Add {C}{C}. Test Card deals 2 damage to you."),
            ("Reliquary Tower", "You have no maximum hand size. {T}: Add {C}."),
        ]
        for name, text in cases:
            with self.subTest(card=name):
                self.assertFalse(self.finds_land(text))

    def test_a_spell_that_fetches_a_land_counts_too(self):
        self.assertTrue(self.finds_land("Search your library for a Forest card, put it onto the battlefield, then "
                                        "shuffle.", "Sorcery"))


# ----------------------------------------------------------------------------- roles: counts and targets
class CountsTests(unittest.TestCase):
    def setUp(self):
        self.db = sample_db()
        self.role_map = {"Sol Ring": {"ramp"}, "Ancient Tomb": {"ramp"}, "Craterhoof Behemoth": {"finisher"},
                         "Witch Enchanter // Witch-Blessed Meadow": {"removal"},
                         "Hazel of the Rootbloom": {"ramp", "draw"},
                         "Teferi, Temporal Archmage": set()}

    def test_counts(self):
        names = (["Sol Ring", "Ancient Tomb", "Command Tower", "Forest", "Forest", "Forest", "Hazel of the Rootbloom",
                  "Witch Enchanter // Witch-Blessed Meadow", "Craterhoof Behemoth", "Teferi, Temporal Archmage"])
        c = roles.counts(names, self.role_map, self.db)
        self.assertEqual(c["land"], 5)                  # Ancient Tomb, Command Tower, three Forests; not the MDFC
        self.assertEqual(c["mdfc_land"], 1)
        self.assertEqual((c["ramp"], c["draw"], c["removal"], c["finisher"]), (3, 1, 1, 1))   # Hazel: both roles
        self.assertEqual(c["topend"], 2)                # Craterhoof (8) and Teferi (6); lands never count
        for role in roles.ROLES + ("land", "mdfc_land", "topend"):
            self.assertIn(role, c)
        self.assertEqual(c["wipe"] + c["counter"] + c["tutor"], 0)

    def test_count_name_pairs_work_like_repeated_names(self):
        pairs = roles.counts([(9, "Forest"), (1, "Sol Ring")], self.role_map, self.db)
        names = roles.counts(["Forest"] * 9 + ["Sol Ring"], self.role_map, self.db)
        self.assertEqual(pairs, names)
        self.assertEqual((pairs["land"], pairs["ramp"]), (9, 1))

    def test_another_spelling_of_a_name_is_counted_and_unknown_names_are_skipped(self):
        c = roles.counts(["sol ring", "Not A Card"], self.role_map, self.db)
        self.assertEqual((c["ramp"], c["land"]), (1, 0))

    def test_empty(self):
        self.assertEqual(set(roles.counts([], {}, self.db).values()), {0})


class TargetsTests(unittest.TestCase):
    """targets() logic, run against a frozen copy of the hand-set starting values (fixtures/
    calibrate_previous.json), so re-calibrating commander/role_targets.json never moves these numbers."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "playstyles.json")
        for attr, value in (("PLAYSTYLES_PATH", self.path), ("TARGETS_PATH", FROZEN_TARGETS)):
            patcher = mock.patch.object(roles, attr, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def playstyles(self, **styles):
        with open(self.path, "w") as f:
            json.dump({"playstyles": {k: {"label": k, "targets": v, "min_bracket": 1} for k, v in styles.items()}}, f)

    def test_shape_and_a_bracket_3_example(self):
        t = roles.targets(3)
        self.assertEqual(set(t), set(roles.ROLES) | {"land", "topend"})
        self.assertEqual(t["ramp"], {"min": 9, "target": 11, "max": 14})
        self.assertEqual(t["land"], {"min": 34, "target": 36, "max": 38})
        self.assertEqual(t["topend"], {"max": 7})
        for role in roles.ROLES:
            self.assertEqual(set(t[role]), {"min", "target", "max"})

    def test_brackets_differ_in_the_expected_direction(self):
        self.assertGreater(roles.targets(5)["counter"]["target"], roles.targets(1)["counter"]["target"])
        self.assertGreater(roles.targets(5)["tutor"]["target"], roles.targets(2)["tutor"]["target"])
        self.assertLess(roles.targets(5)["land"]["target"], roles.targets(1)["land"]["target"])
        self.assertLess(roles.targets(5)["topend"]["max"], roles.targets(1)["topend"]["max"])

    def test_a_bracket_outside_one_to_five_is_clamped(self):
        self.assertEqual(roles.targets(0), roles.targets(1))
        self.assertEqual(roles.targets(9), roles.targets(5))

    def test_playstyle_deltas_shift_min_target_and_max(self):
        self.playstyles(control={"removal": 2, "counter": 2, "wipe": 1}, graveyard={"recursion": 2})
        base, ctl = roles.targets(3), roles.targets(3, "control")
        self.assertEqual(ctl["removal"], {"min": 8, "target": 10, "max": 14})      # base 6/8/12
        self.assertEqual(ctl["counter"], {"min": 2, "target": 3, "max": 8})        # base 0/1/6
        self.assertEqual(ctl["wipe"], {"min": 2, "target": 4, "max": 6})           # base 1/3/5
        for role in ("ramp", "draw", "land", "topend"):
            self.assertEqual(ctl[role], base[role], role)

    def test_negative_deltas_stop_at_zero_and_can_move_land_and_topend(self):
        self.playstyles(odd={"draw": -20, "land": 1, "topend": -3, "nonsense": 4, "ramp": "lots"})
        t, base = roles.targets(3, "odd"), roles.targets(3)
        self.assertEqual(t["draw"], {"min": 0, "target": 0, "max": 0})
        self.assertEqual(t["land"], {"min": 35, "target": 37, "max": 39})
        self.assertEqual(t["topend"], {"max": 4})
        self.assertEqual(t["ramp"], base["ramp"])                   # a delta that is not a number is ignored
        self.assertNotIn("nonsense", t)

    def test_unknown_playstyle_missing_or_damaged_file_change_nothing(self):
        base = roles.targets(3)
        self.assertEqual(roles.targets(3, "value"), base)              # no file at all
        self.playstyles(control={"removal": 2})
        self.assertEqual(roles.targets(3, "no-such-style"), base)
        self.assertEqual(roles.targets(3, None), base)
        with open(self.path, "w") as f:
            f.write("{not json")
        self.assertEqual(roles.targets(3, "control"), base)
        with open(self.path, "w") as f:
            json.dump(["wrong", "shape"], f)
        self.assertEqual(roles.targets(3, "control"), base)

    def test_average_lands_pull_the_land_target_toward_the_commanders_norm(self):
        cases = [(38, 37), (31.4, 34), (36, 36), (37, 37), (20, 34), (50, 38)]   # (EDHREC average, resulting target)
        for avg, expected in cases:
            self.assertEqual(roles.targets(3, avg_lands=avg)["land"]["target"], expected, avg)
        t = roles.targets(3, avg_lands=38)
        self.assertEqual((t["land"]["min"], t["land"]["max"]), (34, 38))   # the range itself does not move

    def test_average_lands_apply_after_the_playstyle(self):
        self.playstyles(ramp_heavy={"land": 2})                      # bracket 3 land 34/36/38 → 36/38/40
        self.assertEqual(roles.targets(3, "ramp_heavy", avg_lands=36)["land"], {"min": 36, "target": 37, "max": 40})
        self.assertEqual(roles.targets(3, "ramp_heavy", avg_lands=44)["land"]["target"], 40)    # mean 41, capped

    def test_without_blue_counterspells_are_not_needed(self):
        for ci in ("BG", "", "WRG"):
            c = roles.targets(5, ci=ci)["counter"]
            self.assertEqual((c["min"], c["target"], c["max"]), (0, 0, 12), ci)
        for ci in ("U", "UB", "WUBRG"):
            self.assertEqual(roles.targets(5, ci=ci)["counter"], {"min": 2, "target": 6, "max": 12}, ci)
        self.assertEqual(roles.targets(5)["counter"], {"min": 2, "target": 6, "max": 12})     # colors unknown

    def test_everything_together(self):
        self.playstyles(control={"counter": 2})
        t = roles.targets(4, "control", avg_lands=36, ci="BR")
        # the delta raised max to 10; no blue zeroed min and target
        self.assertEqual(t["counter"], {"min": 0, "target": 0, "max": 10})
        self.assertEqual(t["land"]["target"], 35)


class TargetsFileTests(unittest.TestCase):
    """commander/role_targets.json is data that ships with the package and is regenerated by calibrate.py: check
    its shape, its stamps and the orderings any calibration must keep, not particular numbers."""
    @classmethod
    def setUpClass(cls):
        with open(roles.TARGETS_PATH) as f:
            cls.data = json.load(f)

    def test_stamped_with_source_and_date(self):
        self.assertTrue(self.data["source"].strip())
        self.assertRegex(self.data["as_of"], r"^\d{4}-\d\d-\d\d$")

    def test_every_bracket_has_every_role_in_order(self):
        self.assertEqual(sorted(self.data["brackets"]), ["1", "2", "3", "4", "5"])
        for b, row in self.data["brackets"].items():
            self.assertEqual(set(row), set(roles.ROLES) | {"land", "topend"}, b)
            for role, v in row.items():
                if role == "topend":
                    self.assertIsInstance(v, int)
                else:
                    self.assertEqual(len(v), 3, (b, role))
                    self.assertLessEqual(v[0], v[1], (b, role))
                    self.assertLessEqual(v[1], v[2], (b, role))

    def test_faster_brackets_run_fewer_lands_more_tutors_and_a_lower_top_end(self):
        b = [self.data["brackets"][str(i)] for i in range(1, 6)]
        lands = [row["land"][1] for row in b]
        tutors = [row["tutor"][1] for row in b]
        topend = [row["topend"] for row in b]
        self.assertEqual(lands, sorted(lands, reverse=True))
        self.assertEqual(tutors, sorted(tutors))
        self.assertEqual(topend, sorted(topend, reverse=True))
        self.assertLess(b[4]["land"][1], b[1]["land"][1])           # cEDH runs clearly fewer lands than a precon


if __name__ == "__main__":
    unittest.main()
