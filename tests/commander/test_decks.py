"""Tests for decks.py: base decks and versions as files, the change log and its replay, every rule `apply` checks
(in the order the module lists them), undo, revisions and conflicts, atomic writes, and two threads at once. Every
test is a worked example on a small world: the Squirreled Away precon (commander Hazel of the Rootbloom, black and
green) in a temporary decks folder. Nothing here touches the network: the card index is the sample in
fixtures/carddb_bulk_sample.jsonl and the precon lookups are stood in for."""
import contextlib, json, os, runpy, shutil, tempfile, threading, time, unittest
from unittest import mock
from mtgcommander import carddb, config, decklist, decks, net

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

SQUIRRELED_AWAY = [(1, "Sol Ring"), (1, "Skullclamp"), (1, "Chatterfang, Squirrel General"), (1, "Command Tower"),
                   (8, "Swamp"), (9, "Forest")]
SQUIRRELED_AWAY_LIST = [[n, name] for n, name in SQUIRRELED_AWAY]
PRECON = {"type": "precon", "name": "Squirreled Away", "mtgjson": "SquirreledAway_BLC"}
# ids in the sample index: Hazel ...07, Sol Ring ...01, Forest ...12, Swamp ...13
HAZEL_ID = "00000000-0000-4000-8000-000000000007"
SOL_RING_ID = "00000000-0000-4000-8000-000000000001"
FOREST_ID = "00000000-0000-4000-8000-000000000012"
SWAMP_ID = "00000000-0000-4000-8000-000000000013"


def at(minute):
    """A timestamp on the day of the build, `minute` past 20:00."""
    return f"2026-10-11T20:{minute:02d}:00Z"


def sample_cards():
    cards = {}
    with open(os.path.join(FIXTURES, "carddb_bulk_sample.jsonl"), encoding="utf-8") as f:
        for line in f:
            rec = carddb.card_record(json.loads(line))
            if rec and rec["name"] not in cards:
                cards[rec["name"]] = rec
    return cards


DB = carddb.CardDB(sample_cards())        # shared and never changed; tests that need a variant build their own


def renamed_db(old, new):
    """The sample index in which the card `old` is now called `new` (Scryfall renamed it; its id is the same)."""
    cards = sample_cards()
    cards[new] = dict(cards.pop(old), name=new, front=new)
    return carddb.CardDB(cards)


def names(pairs):
    return [name for _, name in pairs]


class DeckFiles(unittest.TestCase):
    """A temporary decks folder holding the Squirreled Away base deck, saved by andy at 20:00."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        del decks.WARNINGS[:]
        self.addCleanup(decks.WARNINGS.clear)
        self.base = decks.new_base(self.root, name="Squirreled Away", commanders=["Hazel of the Rootbloom"],
                                   cards=SQUIRRELED_AWAY, source=PRECON, created_by="andy", db=DB, now=at(0))

    def new_version(self, name="Go wide", player="andy", **kw):
        kw.setdefault("settings", {"bracket": 3})
        kw.setdefault("now", at(1))
        return decks.new_version(self.root, player=player, name=name, base_id="squirreled-away", **kw)

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def raw(self, *parts):
        with open(self.path(*parts), "rb") as f:
            return f.read()

    def stored(self, version_id="go-wide", player="andy"):
        return decks.version(self.root, player, version_id)

    def apply(self, change, version_id="go-wide", player="andy", db=DB, **kw):
        """Apply `change` on the revision the file is at now (tests of revisions call decks.apply themselves)."""
        kw.setdefault("now", at(9))
        return decks.apply(self.root, player, version_id, change, revision=self.stored(version_id, player)["revision"],
                           db=db, **kw)

    def cards(self, version_id="go-wide", player="andy", db=DB):
        return decks.current(self.base, self.stored(version_id, player), db)["cards"]

    @contextlib.contextmanager
    def unchanged(self, version_id="go-wide", player="andy"):
        """Inside this block nothing may be written: no save is even attempted (a rewrite of identical bytes would be
        a write too), the file's bytes stay the same and no other file appears. The checks also run when the block
        raises, which is the usual case for a refused change."""
        before = self.raw(player, version_id + ".json")
        folder = sorted(os.listdir(self.path(player)))
        try:
            with mock.patch.object(decks, "_write", side_effect=AssertionError("a file was saved")):
                yield
        finally:
            self.assertEqual(self.raw(player, version_id + ".json"), before, "the file was written")
            self.assertEqual(sorted(os.listdir(self.path(player))), folder)


# ----------------------------------------------------------------------------- ids
class SlugTests(unittest.TestCase):
    def test_a_typed_name_becomes_an_id(self):
        # nine typed names, each with the id it becomes (some rows say why)
        cases = [
            ("Squirrels go wide", "squirrels-go-wide"),
            ("  Hazel’s   Rootbloom!! ", "hazels-rootbloom"),     # apostrophes vanish; marks become hyphens
            ("Æther Vial", "aether-vial"),                        # accents and ligatures
            ("Lim-Dûl's Vault", "lim-duls-vault"),
            ("Fire // Ice", "fire-ice"),
            ("Up to $25", "up-to-25"),
            ("---Go---", "go"),
            ("日本語", ""),                                # nothing the id alphabet holds: the caller asks for an id
            ("", ""),
        ]
        for text, expected in cases:
            self.assertEqual(decks.slug(text), expected, text)

    def test_a_long_name_is_cut_to_64_characters(self):      # twelve "word-" is 60 characters, then "word" makes 64
        self.assertEqual(decks.slug("word " * 40), "word-" * 12 + "word")

    def test_a_cut_that_lands_on_a_hyphen_drops_it(self):    # 63 letters, a hyphen as the 64th character, then a "b"
        self.assertEqual(decks.slug("a" * 63 + " b"), "a" * 63)

    def test_every_slug_is_a_valid_id(self):
        # whatever slug() makes passes the id check, even from a 200-letter name
        for text in ("Squirrels go wide", "Æther Vial", "a" * 200, "9 lives", "Up to $25"):
            slug = decks.slug(text)
            self.assertTrue(decks.ID_PATTERN.fullmatch(slug), (text, slug))


class IdChecks(DeckFiles):
    def test_only_valid_ids_reach_the_file_system(self):
        # capitals, '..', slashes, a trailing newline, non-text: refused before any path is built
        bad = ["Andy", "-go", "", " go", "a b", "a/b", "../x", "a.json", "a" * 65, "go\n", "goé", None, 7]
        for value in bad:
            with self.assertRaises(decks.DeckError, msg=repr(value)) as ctx:
                decks.base(self.root, value)
            self.assertEqual(ctx.exception.status, 400)
            with self.assertRaises(decks.DeckError, msg=repr(value)):
                decks.version(self.root, "andy", value)
            with self.assertRaises(decks.DeckError, msg=repr(value)):
                decks.versions(self.root, value)

    def test_the_longest_and_shortest_ids_are_fine(self):
        # 'a', '0', 64 letters, 'a-b-9': valid ids with nothing saved under them are a 404, not a 400
        for value in ("a", "0", "a" * 64, "a-b-9"):
            with self.assertRaises(decks.NotFound):           # a valid id that nothing is saved under
                decks.base(self.root, value)

    def test_windows_device_names_are_not_ids(self):
        # 'con', 'nul', 'com1', 'lpt9': valid by the pattern, but Windows cannot create con.json, so they are refused
        for value in ("con", "prn", "aux", "nul", "com1", "lpt9"):
            with self.assertRaisesRegex(decks.DeckError, "Windows", msg=value):
                decks.base(self.root, value)
            with self.assertRaisesRegex(decks.DeckError, "Windows", msg=value):
                self.new_version(player=value)
        # a name that slugs to one asks for another name instead of failing on Windows later
        with self.assertRaisesRegex(decks.DeckError, "Windows"):
            decks.new_base(self.root, name="Con", commanders=["Hazel of the Rootbloom"], cards=[],
                           source={"type": "paste"}, created_by="andy", db=DB)
        for value in ("cons", "com10", "nul-1"):                   # only the exact device names are taken
            with self.assertRaises(decks.NotFound, msg=value):
                decks.base(self.root, value)

    def test_bases_cannot_be_a_player(self):       # the folder of base decks has that name
        with self.assertRaisesRegex(decks.DeckError, "bases"):
            self.new_version(player="bases")
        with self.assertRaises(decks.DeckError):
            decks.versions(self.root, "bases")
        with self.assertRaises(decks.DeckError):
            decks.apply(self.root, "bases", "go-wide", {"op": "add", "card": "Mind Stone"}, revision=0, db=DB)
        with self.assertRaises(decks.DeckError):
            decks.new_base(self.root, name="X", commanders=["Hazel of the Rootbloom"], cards=[], source={},
                           created_by="bases", db=DB)


class ErrorTests(unittest.TestCase):
    def test_each_error_has_the_http_status_a_web_server_would_answer_with(self):
        # DeckError 400, NotFound 404, Conflict 409, Invalid 422; str() is the message
        cases = [(decks.DeckError, 400), (decks.NotFound, 404), (decks.Conflict, 409), (decks.Invalid, 422)]
        for cls, status in cases:
            err = cls("Something a player can read.")
            self.assertEqual(err.status, status)
            self.assertEqual(err.message, "Something a player can read.")
            self.assertEqual(str(err), "Something a player can read.")
            self.assertIsInstance(err, decks.DeckError)

    def test_what_each_error_carries(self):
        # Conflict.revision, NotFound.suggestions and Invalid.details, and their empty defaults
        self.assertEqual(decks.Conflict("stale", revision=15).revision, 15)         # the revision to reload at
        self.assertIsNone(decks.Conflict("id taken").revision)
        self.assertEqual(decks.NotFound("no precon", ["Squirreled Away"]).suggestions, ["Squirreled Away"])
        self.assertEqual(decks.NotFound("no base").suggestions, [])
        self.assertEqual(decks.Invalid("bad lines", [{"line": 2}]).details, [{"line": 2}])
        self.assertEqual(decks.Invalid("breaks a rule").details, [])


# ----------------------------------------------------------------------------- the file format
class FormatTests(DeckFiles):
    def test_a_base_file_is_exactly_this_text(self):    # a two-line base: the layout git will diff
        base = decks.new_base(self.root, name="Two Cards", commanders=["Hazel of the Rootbloom"],
                              cards=[(1, "Sol Ring"), (9, "Forest")], source={"type": "paste"}, created_by="andy",
                              db=DB, now=at(3))
        self.assertEqual(self.raw("bases", "two-cards.json").decode("utf-8"), "\n".join([
            '{',
            ' "schema": 1,',
            ' "kind": "base",',
            ' "id": "two-cards",',
            ' "name": "Two Cards",',
            ' "source": {',
            '  "type": "paste"',
            ' },',
            ' "commanders": [',
            '  "Hazel of the Rootbloom"',
            ' ],',
            ' "cards": [',
            '  [1, "Sol Ring"],',
            '  [9, "Forest"]',
            ' ],',
            ' "created": "2026-10-11T20:03:00Z",',
            ' "created_by": "andy",',
            ' "ids": {',
            f'  "Hazel of the Rootbloom": "{HAZEL_ID}",',
            f'  "Sol Ring": "{SOL_RING_ID}",',
            f'  "Forest": "{FOREST_ID}"',
            ' }',
            '}',
            '']))
        self.assertEqual(list(base), ["schema", "kind", "id", "name", "source", "commanders", "cards", "created",
                                      "created_by", "ids"])

    def test_a_version_file_is_exactly_this_text(self):    # one change per line, in the order they happened
        self.new_version(name="Squirrels go wide", settings={"bracket": 3, "themes": ["tokens"]})
        wide = dict(version_id="squirrels-go-wide")
        self.apply({"op": "swap", "cut": "Swamp", "add": "Cultivate", "source": "suggested"}, now=at(5), **wide)
        self.apply({"op": "cut", "card": "Skullclamp"}, now=at(6), **wide)
        self.apply({"op": "undo", "of": 2}, now=at(7), **wide)
        self.assertEqual(self.raw("andy", "squirrels-go-wide.json").decode("utf-8"), "\n".join([
            '{',
            ' "schema": 1,',
            ' "kind": "version",',
            ' "id": "squirrels-go-wide",',
            ' "player": "andy",',
            ' "name": "Squirrels go wide",',
            ' "base": "squirreled-away",',
            ' "settings": {',
            '  "bracket": 3,',
            '  "themes": [',
            '   "tokens"',
            '  ]',
            ' },',
            ' "revision": 3,',
            ' "created": "2026-10-11T20:01:00Z",',
            ' "updated": "2026-10-11T20:07:00Z",',
            ' "notes": "",',
            ' "changes": [',
            f'  {{"n": 1, "at": "{at(5)}", "op": "swap", "cut": "Swamp", "cut_id": "{SWAMP_ID}", "add": "Cultivate", '
            '"add_id": "00000000-0000-4000-8000-000000000041", "source": "suggested"},',
            f'  {{"n": 2, "at": "{at(6)}", "op": "cut", "cut": "Skullclamp", '
            '"cut_id": "00000000-0000-4000-8000-000000000003", "source": "manual"},',
            f'  {{"n": 3, "at": "{at(7)}", "op": "undo", "of": 2}}',
            ' ]',
            '}',
            '']))

    def test_every_card_and_every_change_is_one_line(self):
        # three changes (the last a two-item group) are three lines; six base cards are six lines
        self.new_version()
        for change in ({"op": "add", "card": "Mind Stone"}, {"op": "cut", "card": "Skullclamp"},
                       {"op": "group", "label": "Up to $25", "items": [
                           {"op": "swap", "cut": "Swamp", "add": "Cultivate"},
                           {"op": "add", "card": "Eternal Witness"}]}):
            self.apply(change)
        lines = self.raw("andy", "go-wide.json").decode("utf-8").split("\n")
        change_lines = [line for line in lines if line.startswith('  {"n": ')]
        self.assertEqual(len(change_lines), 3)             # the group, with its items, is still one line
        self.assertIn('"op": "group"', change_lines[2])
        self.assertIn('"items": [{"op": "swap"', change_lines[2])
        base_lines = self.raw("bases", "squirreled-away.json").decode("utf-8").split("\n")
        self.assertEqual([line for line in base_lines if line.startswith("  [")],
                         ['  [1, "Sol Ring"],', '  [1, "Skullclamp"],', '  [1, "Chatterfang, Squirrel General"],',
                          '  [1, "Command Tower"],', '  [8, "Swamp"],', '  [9, "Forest"]'])

    def test_without_cards_or_changes_it_is_plain_json_with_an_indent_of_one(self):    # nothing is special-cased then
        self.new_version(settings={"bracket": 3, "themes": ["tokens", "squirrels"], "owned_precons": []})
        text = self.raw("andy", "go-wide.json").decode("utf-8")
        self.assertEqual(text, json.dumps(json.loads(text), indent=1, ensure_ascii=False) + "\n")

    def test_files_end_with_one_newline_use_unix_line_endings_and_are_utf8(self):
        # what git and every editor expect of a text file
        self.new_version()
        for parts in (("bases", "squirreled-away.json"), ("andy", "go-wide.json")):
            data = self.raw(*parts)
            self.assertTrue(data.endswith(b"}\n") and not data.endswith(b"\n\n"), parts)
            self.assertNotIn(b"\r", data)
            data.decode("utf-8")

    def test_accented_names_are_written_as_they_are_not_as_escapes(self):    # Lim-Dul's Vault, with its circumflex
        decks.new_base(self.root, name="Vault", commanders=["Hazel of the Rootbloom"], cards=[(1, "lim-dul's vault")],
                       source={"type": "paste"}, created_by="andy", db=DB)
        data = self.raw("bases", "vault.json")
        self.assertIn("Lim-Dûl's Vault".encode("utf-8"), data)
        self.assertNotIn(b"\\u00fb", data)
        self.assertEqual(decks.base(self.root, "vault")["cards"], [[1, "Lim-Dûl's Vault"]])

    def test_what_was_written_reads_back_as_the_same_dict(self):
        # base, new version, and after a swap: the returned dict, the loaded dict and the file's JSON agree
        base = decks.base(self.root, "squirreled-away")
        self.assertEqual(base, self.base)
        version = self.new_version()
        self.assertEqual(decks.version(self.root, "andy", "go-wide"), version)
        applied, _ = self.apply({"op": "swap", "cut": "Swamp", "add": "Cultivate"})
        self.assertEqual(decks.version(self.root, "andy", "go-wide"), applied)
        self.assertEqual(json.loads(self.raw("andy", "go-wide.json").decode("utf-8")), applied)

    def test_a_key_the_tool_does_not_know_is_kept_after_the_known_ones(self):    # a newer tool, or a hand edit
        self.new_version()
        path = self.path("andy", "go-wide.json")
        doc = json.loads(self.raw("andy", "go-wide.json"))
        doc["reviewed_by"] = "albert"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f)
        self.apply({"op": "add", "card": "Mind Stone"})
        written = json.loads(self.raw("andy", "go-wide.json"))
        self.assertEqual(list(written)[-2:], ["changes", "reviewed_by"])
        self.assertEqual(written["reviewed_by"], "albert")

    def test_a_file_saved_with_a_byte_order_mark_still_opens(self):    # some Windows editors add one
        self.new_version()
        path = self.path("andy", "go-wide.json")
        with open(path, "rb") as f:
            data = f.read()
        with open(path, "wb") as f:
            f.write(b"\xef\xbb\xbf" + data)
        self.assertEqual(self.stored()["name"], "Go wide")


# ----------------------------------------------------------------------------- base decks
class BaseDeckTests(DeckFiles):
    def test_names_are_saved_as_the_index_spells_them_and_every_card_gets_its_id(self):
        # sloppy spellings in, canonical out
        base = decks.new_base(self.root, name="Sloppy", commanders=["hazel of the rootbloom"],
                              cards=[[1, "sol ring"], [1, "Fire/Ice"], [1, "Delver of Secrets"], [2, "forest"]],
                              source={"type": "paste"}, created_by="andy", db=DB, now=at(2))
        self.assertEqual(base["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(base["cards"], [[1, "Sol Ring"], [1, "Fire // Ice"],
                                         [1, "Delver of Secrets // Insectile Aberration"], [2, "Forest"]])
        self.assertEqual(base["ids"], {"Hazel of the Rootbloom": HAZEL_ID, "Sol Ring": SOL_RING_ID,
                                       "Fire // Ice": DB.get("Fire // Ice")["oracle_id"],
                                       "Delver of Secrets // Insectile Aberration":
                                           DB.get("Delver of Secrets")["oracle_id"],
                                       "Forest": FOREST_ID})

    def test_the_same_card_spelled_two_ways_is_added_up(self):    # the basics of a pasted list split by art
        base = decks.new_base(self.root, name="Split", commanders=["Hazel of the Rootbloom"],
                              cards=[(4, "forest"), (1, "Sol Ring"), (5, "Forest")], source={"type": "paste"},
                              created_by="andy", db=DB)
        self.assertEqual(base["cards"], [[9, "Forest"], [1, "Sol Ring"]])

    def test_the_id_comes_from_the_name_unless_one_is_given(self):
        # 'Squirreled Away' -> squirreled-away; base_id='my-copy' overrides
        self.assertEqual(self.base["id"], "squirreled-away")
        other = decks.new_base(self.root, name="Squirreled Away (my copy)", commanders=["Hazel of the Rootbloom"],
                               cards=[], source={"type": "paste"}, created_by="andy", db=DB, base_id="my-copy")
        self.assertEqual(other["id"], "my-copy")
        self.assertTrue(os.path.exists(self.path("bases", "my-copy.json")))

    def test_the_stored_record_has_who_made_it_and_when_and_where_it_came_from(self):
        # the Squirreled Away base: precon source, created at 20:00 by andy, schema 1
        self.assertEqual(self.base["source"], PRECON)
        self.assertEqual((self.base["created"], self.base["created_by"], self.base["schema"], self.base["kind"]),
                         (at(0), "andy", 1, "base"))
        self.assertEqual(self.base["cards"], SQUIRRELED_AWAY_LIST)

    def test_a_saved_base_is_frozen(self):    # saving another deck under the same id changes nothing
        before = self.raw("bases", "squirreled-away.json")
        with self.assertRaises(decks.Conflict) as ctx:
            decks.new_base(self.root, name="Squirreled Away", commanders=["Hazel of the Rootbloom"],
                           cards=[(1, "Mind Stone")], source={"type": "paste"}, created_by="albert", db=DB)
        self.assertEqual(ctx.exception.status, 409)
        self.assertIsNone(ctx.exception.revision)              # an id clash, not a stale revision
        self.assertIn("squirreled-away", ctx.exception.message)
        self.assertEqual(self.raw("bases", "squirreled-away.json"), before)

    def test_unknown_cards_are_all_listed_with_close_names_and_nothing_is_saved(self):
        # 'Sol Rnig' and 'Zzzzzzzzzz' in one list: both reported, only the first has a close name
        with self.assertRaises(decks.Invalid) as ctx:
            decks.new_base(self.root, name="Typos", commanders=["Hazel of the Rootbloom"],
                           cards=[(1, "Sol Rnig"), (1, "Forest"), (1, "Zzzzzzzzzz")], source={"type": "paste"},
                           created_by="andy", db=DB)
        err = ctx.exception
        self.assertEqual(err.status, 422)
        self.assertEqual([d["text"] for d in err.details], ["Sol Rnig", "Zzzzzzzzzz"])
        self.assertIn("Sol Ring", err.details[0]["suggestions"])
        self.assertEqual(err.details[1]["suggestions"], [])
        self.assertIn("Sol Rnig", err.message)
        self.assertFalse(os.path.exists(self.path("bases", "typos.json")))

    def test_a_base_needs_one_or_two_commanders_that_the_index_knows(self):
        # none, three, a misspelled one, then a pair with one name given twice
        def make(commanders):
            return decks.new_base(self.root, name="X", commanders=commanders, cards=[], source={"type": "paste"},
                                  created_by="andy", db=DB, base_id="x")
        with self.assertRaisesRegex(decks.Invalid, "needs a commander"):
            make([])
        with self.assertRaisesRegex(decks.Invalid, "one or two commanders"):
            make(["Hazel of the Rootbloom", "Pir, Imaginative Rascal", "Toothy, Imaginary Friend"])
        with self.assertRaises(decks.Invalid) as ctx:
            make(["Hazle of the Rootbloom"])
        self.assertEqual(ctx.exception.details[0]["suggestions"][0], "Hazel of the Rootbloom")
        self.assertFalse(os.path.exists(self.path("bases", "x.json")))
        pair = make(["pir, imaginative rascal", "Toothy, Imaginary Friend", "Pir, Imaginative Rascal"])
        # the repeated name is the same card, not a third commander
        self.assertEqual(pair["commanders"], ["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"])

    def test_a_base_may_hold_a_banned_card_because_legality_is_checked_elsewhere(self):
        # Griselbrand in a saved base is accepted here; `brackets.legality` is what reports it
        base = decks.new_base(self.root, name="Old precon", commanders=["Hazel of the Rootbloom"],
                              cards=[(1, "Griselbrand"), (1, "Fire // Ice")], source={"type": "paste"},
                              created_by="andy", db=DB)
        self.assertEqual(names(base["cards"]), ["Griselbrand", "Fire // Ice"])

    def test_bad_input_shapes_are_400s_and_write_nothing(self):
        # a blank name, bad counts, wrong types, bad ids: each a 400, and bases/ keeps only the one file
        good = dict(name="Shape", commanders=["Hazel of the Rootbloom"], cards=[(1, "Sol Ring")],
                    source={"type": "paste"}, created_by="andy", db=DB)
        bad = [
            dict(name=""), dict(name=None), dict(name="   "),                    # no name
            dict(cards=[(0, "Sol Ring")]), dict(cards=[(True, "Sol Ring")]), dict(cards=[("2", "Sol Ring")]),
            dict(cards=[(1, "")]), dict(cards=[(1,)]), dict(cards=None), dict(cards="Sol Ring"),
            dict(commanders="Hazel of the Rootbloom"), dict(commanders=[7]),
            dict(source=None), dict(source="paste"),
            dict(created_by="Andy"), dict(created_by="bases"), dict(created_by=None),
            dict(base_id="Bad Id"), dict(name="日本語"),                 # an id cannot be made from this name
        ]
        for change in bad:
            with self.assertRaises(decks.DeckError, msg=change) as ctx:
                decks.new_base(self.root, **dict(good, **change))
            self.assertEqual(ctx.exception.status, 400, change)
        self.assertEqual(os.listdir(self.path("bases")), ["squirreled-away.json"])

    def test_a_base_is_read_back_and_a_missing_one_is_a_404(self):
        # base('squirreled-away') and base('no-such-deck')
        self.assertEqual(decks.base(self.root, "squirreled-away"), self.base)
        with self.assertRaises(decks.NotFound) as ctx:
            decks.base(self.root, "no-such-deck")
        self.assertEqual(ctx.exception.status, 404)
        self.assertIn("no-such-deck", ctx.exception.message)

    def test_bases_are_listed_by_name_ignoring_case(self):    # "alpha" sorts with the As, not after the Zs
        for name in ("zebra stripes", "Alpha", "Middle", "alpha two"):
            decks.new_base(self.root, name=name, commanders=["Hazel of the Rootbloom"], cards=[],
                           source={"type": "paste"}, created_by="andy", db=DB)
        self.assertEqual([b["name"] for b in decks.bases(self.root)],
                         ["Alpha", "alpha two", "Middle", "Squirreled Away", "zebra stripes"])

    def test_listing_with_no_folder_yet_gives_nothing(self):
        # a fresh clone has no commander/decks folder at all
        empty = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, empty, True)
        self.assertEqual((decks.bases(empty), decks.players(empty)), ([], []))
        self.assertEqual(decks.bases(os.path.join(empty, "no-such-folder")), [])
        self.assertEqual(decks.players(os.path.join(empty, "no-such-folder")), [])


class ParseListTests(unittest.TestCase):
    def test_a_list_with_a_typo_a_misspelled_commander_and_a_junk_line(self):
        # each problem comes with its line number
        text = ("Commander\n"                    # 1
                "1 Hazle of the Rootbloom\n"     # 2  misspelled commander
                "\n"                             # 3
                "Deck\n"                         # 4
                "1 Sol Ring\n"                   # 5
                "1 Sol Rnig\n"                   # 6  misspelled card
                "[Ramp]\n"                       # 7  nothing a card name can be read from
                "9 Forest\n")                    # 8
        out = decks.parse_list(text, DB)
        self.assertEqual(out["commanders"], [])
        self.assertEqual(out["cards"], [[1, "Sol Ring"], [9, "Forest"]])
        self.assertEqual([(p["line"], p["text"]) for p in out["problems"]],
                         [(2, "1 Hazle of the Rootbloom"), (6, "1 Sol Rnig"), (7, "[Ramp]")])
        self.assertEqual(out["problems"][0]["suggestions"][0], "Hazel of the Rootbloom")
        self.assertEqual(out["problems"][1]["suggestions"][0], "Sol Ring")
        self.assertEqual(out["problems"][2]["suggestions"], [])
        self.assertEqual(set(out), {"commanders", "cards", "problems"})

    def test_a_clean_list_has_no_problems_and_canonical_names(self):
        # lower case, 'Fire/Ice', a set suffix, and Forests split 4 + 5 in one list
        out = decks.parse_list("Commander\n1 hazel of the rootbloom\nDeck\n1 sol ring\n1x Fire/Ice (DMR) 215\n"
                               "4 Forest\n5 forest\n", DB)
        self.assertEqual(out, {"commanders": ["Hazel of the Rootbloom"],
                               "cards": [[1, "Sol Ring"], [1, "Fire // Ice"], [9, "Forest"]], "problems": []})

    def test_the_same_typo_on_two_lines_is_a_problem_on_each_line(self):
        # 'Sol Rnig' on line 4 and 'sol rnig' on line 6: a problem on each
        out = decks.parse_list("Commander\n1 Hazel of the Rootbloom\nDeck\n1 Sol Rnig\n1 Forest\n1 sol rnig\n", DB)
        self.assertEqual([p["line"] for p in out["problems"]], [4, 6])
        self.assertEqual(out["problems"][0]["suggestions"], out["problems"][1]["suggestions"])

    def test_a_typo_after_a_blank_line_is_reported_not_lost(self):
        # without headers, the cards after a blank line are read as more of the deck, and decklist.resolve drops the
        # ones it cannot match without a word; a saved base would lose that card for good
        out = decks.parse_list("1 Sol Ring\n\n1 Sol Rnig\n1 Forest\n", DB, commander="Hazel of the Rootbloom")
        self.assertEqual(out["cards"], [[1, "Sol Ring"], [1, "Forest"]])
        self.assertEqual([(p["line"], p["text"]) for p in out["problems"]], [(3, "1 Sol Rnig")])
        self.assertEqual(out["problems"][0]["suggestions"][0], "Sol Ring")

    def test_an_unknown_card_in_an_explicit_sideboard_is_not_a_problem(self):    # the sideboard is left out anyway
        text = "Deck\n1 Sol Ring\nSideboard\n1 Totally Fake Card\n"
        out = decks.parse_list(text, DB, commander="Hazel of the Rootbloom")
        self.assertEqual((out["cards"], out["problems"]), ([[1, "Sol Ring"]], []))

    def test_the_commander_argument_names_the_commander_when_the_list_does_not(self):
        # commander='hazel of the rootbloom' for a list that only has her among its cards
        text = "1 Sol Ring\n1 Hazel of the Rootbloom\n1 Forest\n"
        out = decks.parse_list(text, DB, commander="hazel of the rootbloom")
        self.assertEqual(out["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(out["cards"], [[1, "Sol Ring"], [1, "Forest"]])

    def test_a_misspelled_commander_argument_is_a_problem_on_no_line(self):
        # commander='Hazle of the Rootbloom': reported with line None and the close name
        out = decks.parse_list("1 Sol Ring\n", DB, commander="Hazle of the Rootbloom")
        self.assertEqual(out["commanders"], [])
        self.assertEqual(len(out["problems"]), 1)
        problem = out["problems"][0]
        self.assertEqual((problem["line"], problem["text"]), (None, "Hazle of the Rootbloom"))
        self.assertEqual(problem["suggestions"][0], "Hazel of the Rootbloom")

    def test_line_numbers_count_every_line_including_blank_ones_and_windows_line_endings(self):
        # '\r\n' endings and two blank lines put the typo on line 6
        out = decks.parse_list("Commander\r\n1 Hazel of the Rootbloom\r\n\r\n\r\nDeck\r\n1 Sol Rnig\r\n", DB)
        self.assertEqual([(p["line"], p["text"]) for p in out["problems"]], [(6, "1 Sol Rnig")])

    def test_something_that_is_not_text_is_a_400(self):
        # None, bytes and a list are not a pasted list
        for text in (None, b"1 Sol Ring", ["1 Sol Ring"]):
            with self.assertRaises(decks.DeckError, msg=text) as ctx:
                decks.parse_list(text, DB)
            self.assertEqual(ctx.exception.status, 400)

    def test_a_list_that_reads_cleanly_goes_straight_into_a_base(self):
        # parse_list's commanders and cards are new_base's arguments
        parsed = decks.parse_list("Commander\n1 Hazel of the Rootbloom\nDeck\n1 Sol Ring\n9 Forest\n", DB)
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        base = decks.new_base(root, name="Pasted", commanders=parsed["commanders"], cards=parsed["cards"],
                              source={"type": "paste"}, created_by="andy", db=DB)
        self.assertEqual(base["commanders"], ["Hazel of the Rootbloom"])
        self.assertEqual(base["cards"], [[1, "Sol Ring"], [9, "Forest"]])


class PreconBaseInputTests(DeckFiles):
    PRECON_DECK = {"name": "Squirreled Away", "code": "BLC", "file": "SquirreledAway_BLC", "release": "2024-08-02",
                   "commanders": ["Hazel of the Rootbloom"], "cards": SQUIRRELED_AWAY,
                   "fetched": "2026-10-11T12:00:00Z", "url": "https://mtgjson.com/api/v5/decks/SquirreledAway_BLC.json"}

    def test_a_precon_becomes_the_arguments_for_a_base(self):
        # 'squirreled away' -> name, commander, cards as pairs and the MTGJSON deck file name
        with mock.patch.object(decklist, "precon", return_value=self.PRECON_DECK) as precon:
            out = decks.precon_base_input("squirreled away")
        precon.assert_called_once_with("squirreled away")
        self.assertEqual(out, {"name": "Squirreled Away", "commanders": ["Hazel of the Rootbloom"],
                               "cards": SQUIRRELED_AWAY_LIST, "source": PRECON})

    def test_the_arguments_save_as_a_base(self):    # the whole precon path: lookup, then new_base
        with mock.patch.object(decklist, "precon", return_value=self.PRECON_DECK):
            out = decks.precon_base_input("Squirreled Away")
        saved = decks.new_base(self.root, created_by="albert", db=DB, base_id="squirreled-away-2", **out)
        self.assertEqual((saved["source"], saved["cards"], saved["commanders"]),
                         (PRECON, SQUIRRELED_AWAY_LIST, ["Hazel of the Rootbloom"]))

    def test_an_unknown_precon_is_a_404_that_carries_the_close_names(self):
        # 'Squirrel Army' -> close names Squirreled Away and Peace Offering
        unknown = decklist.UnknownPrecon("Squirrel Army", ["Squirreled Away", "Peace Offering"])
        with mock.patch.object(decklist, "precon", side_effect=unknown):
            with self.assertRaises(decks.NotFound) as ctx:
                decks.precon_base_input("Squirrel Army")
        err = ctx.exception
        self.assertEqual((err.status, err.suggestions), (404, ["Squirreled Away", "Peace Offering"]))
        self.assertIn("Squirrel Army", err.message)
        self.assertIn("Squirreled Away, Peace Offering", err.message)

    def test_an_unknown_precon_with_no_close_name_says_so_plainly(self):
        # 'zzzzzzzz' is close to nothing
        with mock.patch.object(decklist, "precon", side_effect=decklist.UnknownPrecon("zzzzzzzz", [])):
            with self.assertRaises(decks.NotFound) as ctx:
                decks.precon_base_input("zzzzzzzz")
        self.assertEqual((ctx.exception.suggestions, ctx.exception.message), ([], 'No precon is called "zzzzzzzz".'))

    def test_a_listed_precon_whose_deck_file_is_gone_is_a_404_too(self):
        # MTGJSON lists the deck but its file answers 404
        gone = net.NotFound("mtgjson", "https://mtgjson.com/api/v5/decks/X.json", "no such page")
        with mock.patch.object(decklist, "precon", side_effect=gone):
            with self.assertRaisesRegex(decks.NotFound, "no deck file"):
                decks.precon_base_input("Squirreled Away")

    def test_a_blank_or_non_text_precon_name_is_a_400_and_nothing_is_looked_up(self):
        with mock.patch.object(decklist, "precon") as precon:
            for name in ("", "   ", None, 7):
                with self.assertRaises(decks.DeckError, msg=name) as ctx:
                    decks.precon_base_input(name)
                self.assertEqual(ctx.exception.status, 400)
        precon.assert_not_called()

    def test_a_network_failure_is_not_turned_into_a_404(self):    # a failed download is not a missing precon
        failure = net.FetchError("mtgjson", "u", "offline (--offline) and not cached")
        with mock.patch.object(decklist, "precon", side_effect=failure):
            with self.assertRaises(net.FetchError):
                decks.precon_base_input("Squirreled Away")


# ----------------------------------------------------------------------------- versions and listing
class VersionTests(DeckFiles):
    def test_a_new_version_starts_at_revision_zero_with_no_changes(self):
        # andy's 'Squirrels go wide' on Squirreled Away at 20:01
        v = self.new_version(name="Squirrels go wide", settings={"bracket": 3, "budget": 200})
        self.assertEqual(v, {"schema": 1, "kind": "version", "id": "squirrels-go-wide", "player": "andy",
                             "name": "Squirrels go wide", "base": "squirreled-away",
                             "settings": {"bracket": 3, "budget": 200}, "revision": 0, "created": at(1),
                             "updated": at(1), "notes": "", "changes": []})

    def test_the_id_is_given_or_comes_from_the_name_and_a_taken_one_is_a_409(self):
        # 'Go wide' twice (one with an explicit id), then 'Go Wide!' (the same id), then albert's own
        self.assertEqual(self.new_version(name="Go wide")["id"], "go-wide")
        self.assertEqual(self.new_version(name="Go wide", version_id="go-wide-2")["id"], "go-wide-2")
        before = self.raw("andy", "go-wide.json")
        with self.assertRaises(decks.Conflict) as ctx:
            self.new_version(name="Go Wide!")             # the same id after slugging
        self.assertEqual((ctx.exception.status, ctx.exception.revision), (409, None))
        self.assertIn("go-wide", ctx.exception.message)
        self.assertEqual(self.raw("andy", "go-wide.json"), before)
        self.assertEqual(self.new_version(name="Go wide", player="albert")["id"], "go-wide")   # another player's folder

    def test_the_base_must_exist(self):
        # base_id 'no-such-deck': a 404, and no player folder is made
        with self.assertRaises(decks.NotFound):
            decks.new_version(self.root, player="andy", name="X", base_id="no-such-deck", settings={})
        self.assertFalse(os.path.exists(self.path("andy")))

    def test_bad_input_shapes_are_400s_and_write_nothing(self):
        # bad player, name, settings and ids: each a 400, and no player folder is made
        good = dict(player="andy", name="Shape", base_id="squirreled-away", settings={})
        bad = [dict(player="Andy"), dict(player=None), dict(player="bases"), dict(name=""), dict(name=5),
               dict(settings=None), dict(settings=[1]), dict(settings={1: 2}), dict(base_id="Squirreled Away"),
               dict(version_id="Bad Id"), dict(name="日本語")]
        for change in bad:
            with self.assertRaises(decks.DeckError, msg=change) as ctx:
                decks.new_version(self.root, **dict(good, **change))
            self.assertEqual(ctx.exception.status, 400, change)
        self.assertFalse(os.path.exists(self.path("andy")))

    def test_settings_are_stored_as_given_and_the_callers_dict_is_not_kept(self):
        # the caller adds a theme to its own dict after saving; the file and the result keep ['tokens']
        settings = {"bracket": 3, "themes": ["tokens"]}
        v = self.new_version(settings=settings)
        settings["themes"].append("squirrels")
        self.assertEqual(self.stored()["settings"]["themes"], ["tokens"])
        self.assertEqual(v["settings"]["themes"], ["tokens"])

    def test_a_version_is_read_back_and_a_missing_one_is_a_404_that_says_which_part(self):
        # andy/go-wide, andy/other and nobody/go-wide
        self.new_version()
        self.assertEqual(decks.version(self.root, "andy", "go-wide")["id"], "go-wide")
        with self.assertRaisesRegex(decks.NotFound, "no version"):
            decks.version(self.root, "andy", "other")
        with self.assertRaisesRegex(decks.NotFound, "no player"):
            decks.version(self.root, "nobody", "go-wide")

    def test_players_are_the_folders_except_bases(self):
        # andy and albert; a README file, .git and 'Not A Player' are not players
        self.assertEqual(decks.players(self.root), [])                # only "bases" exists
        self.new_version(player="andy")
        self.new_version(player="albert")
        open(self.path("README.txt"), "w").close()                    # a file is not a player
        os.mkdir(self.path(".git"))                                   # neither is a folder that cannot be an id
        os.mkdir(self.path("Not A Player"))
        self.assertEqual(decks.players(self.root), ["albert", "andy"])

    def test_versions_are_newest_first_and_a_tie_goes_by_id(self):
        # created at :10 (Middle), :30 (Newest) and :20 twice (Older a, Older b)
        for minute, name in ((10, "Middle"), (30, "Newest"), (20, "Older b"), (20, "Older a")):
            self.new_version(name=name, now=at(minute))
        self.assertEqual([v["id"] for v in decks.versions(self.root, "andy")],
                         ["newest", "older-a", "older-b", "middle"])

    def test_editing_a_version_does_not_move_it_in_the_list(self):    # newest is by when it was created
        self.new_version(name="First", now=at(10))
        self.new_version(name="Second", now=at(20))
        self.apply({"op": "add", "card": "Mind Stone"}, version_id="first", now=at(50))
        self.assertEqual([v["id"] for v in decks.versions(self.root, "andy")], ["second", "first"])

    def test_a_player_with_a_folder_but_no_versions_has_an_empty_list_and_no_folder_is_a_404(self):
        # albert has an empty folder; nobody has none
        os.mkdir(self.path("albert"))
        self.assertEqual(decks.versions(self.root, "albert"), [])
        with self.assertRaises(decks.NotFound):
            decks.versions(self.root, "nobody")

    def test_a_damaged_file_is_skipped_by_the_listing_and_named_in_the_warnings(self):
        # a git merge left markers in it
        self.new_version(name="Fine")
        self.new_version(name="Broken")
        with open(self.path("andy", "broken.json"), "w") as f:
            f.write("<<<<<<< HEAD\n{}\n=======\n{}\n>>>>>>> main\n")
        self.assertEqual([v["id"] for v in decks.versions(self.root, "andy")], ["fine"])
        self.assertEqual(len(decks.WARNINGS), 1)
        self.assertIn("broken.json", decks.WARNINGS[0])

    def test_opening_a_damaged_file_names_it(self):
        # a half-merged file: version() and apply() both name it
        self.new_version(name="Broken")
        with open(self.path("andy", "broken.json"), "w") as f:
            f.write("<<<<<<< HEAD\n")
        with self.assertRaisesRegex(ValueError, "broken.json"):
            decks.version(self.root, "andy", "broken")
        with self.assertRaisesRegex(ValueError, "broken.json"):
            decks.apply(self.root, "andy", "broken", {"op": "add", "card": "Mind Stone"}, revision=0, db=DB)

    def test_files_of_the_wrong_kind_or_schema_or_missing_pieces_are_not_used(self):
        # eight bad files (newer schema, wrong kind, missing name or base ...): none opens, none is listed
        self.new_version()
        good = json.loads(self.raw("andy", "go-wide.json"))

        def without(key):
            return {k: v for k, v in good.items() if k != key}
        cases = {"newer": dict(good, schema=2), "base-in-player-folder": dict(good, kind="base"),
                 "no-base": without("base"), "no-name": without("name"),
                 "bad-revision": dict(good, revision="3"), "bool-revision": dict(good, revision=True),
                 "changes-not-a-list": dict(good, changes={}), "not-an-object": [1, 2]}
        for stem, doc in cases.items():
            with open(self.path("andy", stem + ".json"), "w") as f:
                json.dump(doc, f)
            with self.assertRaises(ValueError, msg=stem):
                decks.version(self.root, "andy", stem)
        self.assertEqual([v["id"] for v in decks.versions(self.root, "andy")], ["go-wide"])
        self.assertEqual(len(decks.WARNINGS), len(cases))

    def test_a_hand_made_file_with_the_optional_pieces_left_out_still_opens(self):
        # no settings, revision, changes, notes, created or updated: the defaults are filled in
        self.new_version()
        good = json.loads(self.raw("andy", "go-wide.json"))
        for key in ("settings", "revision", "changes", "notes", "created", "updated"):
            del good[key]
        with open(self.path("andy", "bare.json"), "w") as f:
            json.dump(good, f)
        v = decks.version(self.root, "andy", "bare")
        self.assertEqual((v["settings"], v["revision"], v["changes"]), ({}, 0, []))
        decks.apply(self.root, "andy", "bare", {"op": "add", "card": "Mind Stone"}, revision=0, db=DB)
        self.assertEqual(decks.version(self.root, "andy", "bare")["revision"], 1)

    def test_the_id_always_comes_from_the_file_name_so_a_copied_file_cannot_claim_another_id(self):
        # go-wide.json copied to copy.json, and into albert's folder
        self.new_version()
        shutil.copy(self.path("andy", "go-wide.json"), self.path("andy", "copy.json"))
        self.assertEqual(decks.version(self.root, "andy", "copy")["id"], "copy")
        self.assertEqual(sorted(v["id"] for v in decks.versions(self.root, "andy")), ["copy", "go-wide"])
        os.makedirs(self.path("albert"))
        shutil.copy(self.path("andy", "go-wide.json"), self.path("albert", "go-wide.json"))
        self.assertEqual(decks.version(self.root, "albert", "go-wide")["player"], "albert")

    def test_leftover_temporary_files_and_other_files_are_not_listed(self):
        # go-wide.json.4242.tmp, notes.txt, 'Bad Id.json' and .hidden.json sit beside the one real version
        self.new_version()
        for name in ("go-wide.json.4242.tmp", "notes.txt", "Bad Id.json", ".hidden.json"):
            open(self.path("andy", name), "w").close()
        self.assertEqual([v["id"] for v in decks.versions(self.root, "andy")], ["go-wide"])
        self.assertEqual(decks.WARNINGS, [])


# ----------------------------------------------------------------------------- replaying the log
class ReplayTests(DeckFiles):
    def setUp(self):
        super().setUp()
        self.new_version()

    def test_the_base_alone_is_the_base_cards_and_commanders(self):
        # a version with no changes is the base
        out = decks.current(self.base, self.stored(), DB)
        self.assertEqual(out, {"commanders": ["Hazel of the Rootbloom"], "cards": SQUIRRELED_AWAY_LIST, "warnings": []})

    def test_an_add_puts_the_card_after_the_base_cards(self):
        # add Mind Stone
        self.apply({"op": "add", "card": "Mind Stone"})
        self.assertEqual(self.cards(), SQUIRRELED_AWAY_LIST + [[1, "Mind Stone"]])

    def test_a_cut_takes_out_one_copy_and_the_last_copy_removes_the_line(self):    # Swamp 8 -> 7; Skullclamp 1 -> gone
        self.apply({"op": "cut", "card": "Swamp"})
        self.apply({"op": "cut", "card": "Skullclamp"})
        expected = [[1, "Sol Ring"], [1, "Chatterfang, Squirrel General"], [1, "Command Tower"],
                    [7, "Swamp"], [9, "Forest"]]
        self.assertEqual(self.cards(), expected)

    def test_a_swap_cuts_one_card_and_adds_another_at_the_end(self):    # Swamp for Cultivate
        self.apply({"op": "swap", "cut": "Swamp", "add": "Cultivate"})
        self.assertEqual(self.cards(), [[1, "Sol Ring"], [1, "Skullclamp"], [1, "Chatterfang, Squirrel General"],
                                        [1, "Command Tower"], [7, "Swamp"], [9, "Forest"], [1, "Cultivate"]])

    def test_a_group_applies_its_items_in_order_each_seeing_the_one_before(self):
        # item 1 adds Mind Stone, item 2 swaps it for Arcane Signet, item 3 cuts a Forest
        self.apply({"op": "group", "label": "Up to $25", "items": [
            {"op": "add", "card": "Mind Stone"}, {"op": "swap", "cut": "Mind Stone", "add": "Arcane Signet"},
            {"op": "cut", "card": "Forest"}]})
        self.assertEqual(self.cards(), [[1, "Sol Ring"], [1, "Skullclamp"], [1, "Chatterfang, Squirrel General"],
                                        [1, "Command Tower"], [8, "Swamp"], [8, "Forest"], [1, "Arcane Signet"]])

    def test_the_order_is_the_base_then_additions_in_the_order_they_were_made(self):
        # Rampant Growth, Cultivate and Mind Stone, added in that order
        self.apply({"op": "add", "card": "Rampant Growth"})
        self.apply({"op": "add", "card": "Cultivate"})
        self.apply({"op": "add", "card": "Mind Stone"})
        self.assertEqual(names(self.cards())[-3:], ["Rampant Growth", "Cultivate", "Mind Stone"])

    def test_a_card_cut_and_added_again_counts_as_added_and_goes_to_the_end(self):    # Sol Ring was first in the base
        self.apply({"op": "cut", "card": "Sol Ring"})
        self.apply({"op": "add", "card": "Sol Ring"})
        self.assertEqual(names(self.cards()), ["Skullclamp", "Chatterfang, Squirrel General", "Command Tower", "Swamp",
                                               "Forest", "Sol Ring"])

    def test_an_extra_copy_of_a_basic_stays_where_the_basic_is(self):    # a tenth Forest
        self.apply({"op": "add", "card": "Forest"})
        self.assertEqual(self.cards()[-1], [10, "Forest"])

    def test_undone_changes_are_left_out_and_the_undo_itself_adds_nothing(self):
        # add Mind Stone (1), cut Skullclamp (2), undo the cut (3)
        self.apply({"op": "add", "card": "Mind Stone"})                  # change 1
        self.apply({"op": "cut", "card": "Skullclamp"})                  # change 2
        self.apply({"op": "undo", "of": 2})                              # change 3
        self.assertEqual(self.cards(), SQUIRRELED_AWAY_LIST + [[1, "Mind Stone"]])

    def test_an_undone_group_is_left_out_whole(self):
        # a two-item group, then its undo
        self.apply({"op": "group", "label": "G", "items": [
            {"op": "add", "card": "Mind Stone"}, {"op": "cut", "card": "Swamp"}]})
        self.apply({"op": "undo", "of": 1})
        self.assertEqual(self.cards(), SQUIRRELED_AWAY_LIST)

    def test_replaying_does_not_change_what_it_is_given(self):
        # current() leaves the base and version dicts exactly as they were
        self.apply({"op": "swap", "cut": "Swamp", "add": "Cultivate"})
        version = self.stored()
        base_before, version_before = json.dumps(self.base), json.dumps(version)
        decks.current(self.base, version, DB)
        self.assertEqual((json.dumps(self.base), json.dumps(version)), (base_before, version_before))

    def test_a_version_dict_with_no_changes_key_is_the_base(self):
        # {} stands for a version with no changes
        self.assertEqual(decks.current(self.base, {}, DB)["cards"], SQUIRRELED_AWAY_LIST)

    def test_a_card_renamed_upstream_still_resolves_through_the_base_ids_map(self):    # Sol Ring -> Sol Ring Reforged
        db = renamed_db("Sol Ring", "Sol Ring Reforged")
        self.assertIsNone(db.get("Sol Ring"))                           # the stored name no longer matches
        out = decks.current(self.base, self.stored(), db)
        self.assertEqual(out["cards"][0], [1, "Sol Ring Reforged"])
        self.assertEqual(out["warnings"], [])

    def test_a_card_renamed_upstream_still_resolves_through_the_changes_ids(self):
        # the player added Mind Stone and later cut Cultivate; Scryfall then renamed both
        self.apply({"op": "add", "card": "Mind Stone"})
        self.apply({"op": "swap", "cut": "Swamp", "add": "Cultivate"})
        self.apply({"op": "cut", "card": "Cultivate"})
        cards = sample_cards()
        for old, new in (("Mind Stone", "Mind Stone Reforged"), ("Cultivate", "Cultivate Reforged")):
            cards[new] = dict(cards.pop(old), name=new, front=new)
        db = carddb.CardDB(cards)
        out = decks.current(self.base, self.stored(), db)
        self.assertEqual(out["cards"], [[1, "Sol Ring"], [1, "Skullclamp"], [1, "Chatterfang, Squirrel General"],
                                        [1, "Command Tower"], [7, "Swamp"], [9, "Forest"], [1, "Mind Stone Reforged"]])
        self.assertEqual(out["warnings"], [])                           # the cut of Cultivate found its card by id

    def test_a_card_renamed_upstream_can_still_be_cut_by_its_new_name_and_the_cut_is_stored_with_the_id(self):
        # Sol Ring is now 'Sol Ring Reforged': cutting that name stores Sol Ring's old id
        db = renamed_db("Sol Ring", "Sol Ring Reforged")
        v, info = self.apply({"op": "cut", "card": "Sol Ring Reforged"}, db=db)
        self.assertEqual((info["changed"], v["changes"][-1]["cut"], v["changes"][-1]["cut_id"]),
                         (True, "Sol Ring Reforged", SOL_RING_ID))
        self.assertNotIn("Sol Ring Reforged", names(decks.current(self.base, v, db)["cards"]))

    def test_a_renamed_commander_resolves_too(self):
        # Hazel of the Rootbloom is now 'Hazel of the Rootbloom Reforged'
        db = renamed_db("Hazel of the Rootbloom", "Hazel of the Rootbloom Reforged")
        out = decks.current(self.base, self.stored(), db)
        self.assertEqual((out["commanders"], out["warnings"]), (["Hazel of the Rootbloom Reforged"], []))

    def test_a_card_the_index_no_longer_knows_stays_as_written_with_a_warning(self):
        # Skullclamp is missing from the index
        cards = sample_cards()
        del cards["Skullclamp"]
        out = decks.current(self.base, self.stored(), carddb.CardDB(cards))
        self.assertEqual(out["cards"], SQUIRRELED_AWAY_LIST)
        self.assertEqual(out["warnings"], ["Skullclamp is not in the card index; it is kept as written."])

    def test_a_card_the_index_no_longer_knows_can_still_be_cut_by_its_name(self):
        # Skullclamp is missing from the index; the base's ids map still has its id
        cards = sample_cards()
        del cards["Skullclamp"]
        db = carddb.CardDB(cards)
        v, info = self.apply({"op": "cut", "card": "Skullclamp"}, db=db)
        self.assertTrue(info["changed"])
        self.assertEqual(v["changes"][-1]["cut_id"], self.base["ids"]["Skullclamp"])    # the base's id map still has it
        self.assertNotIn("Skullclamp", names(decks.current(self.base, v, db)["cards"]))

    def test_a_commander_the_index_does_not_know_is_a_warning(self):
        # Hazel is missing from the index
        cards = sample_cards()
        del cards["Hazel of the Rootbloom"]
        out = decks.current(self.base, self.stored(), carddb.CardDB(cards))
        self.assertEqual(out["commanders"], ["Hazel of the Rootbloom"])
        self.assertIn("Hazel of the Rootbloom is not in the card index", out["warnings"][0])

    # --- a hand-edited or badly merged file opens: what cannot apply is skipped with a warning, never raised
    def broken(self, *changes):
        return decks.current(self.base, {"changes": list(changes)}, DB)

    def test_a_cut_of_a_card_the_deck_does_not_have_is_skipped_with_a_warning(self):    # two people cut the same card
        out = self.broken({"n": 1, "op": "cut", "cut": "Mind Stone"}, {"n": 2, "op": "cut", "cut": "Skullclamp"})
        self.assertEqual(names(out["cards"])[:2], ["Sol Ring", "Chatterfang, Squirrel General"])
        self.assertEqual(out["warnings"], ["Skipped change 1: it cut Mind Stone, but the deck does not have it."])

    def test_adding_a_one_copy_card_twice_keeps_one_copy_and_warns(self):    # two people added the same card
        out = self.broken({"n": 1, "op": "add", "add": "Mind Stone"}, {"n": 2, "op": "add", "add": "Mind Stone"})
        self.assertEqual(out["cards"][-1], [1, "Mind Stone"])
        self.assertEqual(out["warnings"], ["Skipped change 2: it added Mind Stone, but the deck already has a copy."])

    def test_adding_the_commander_is_skipped_with_a_warning(self):
        # a stored add of Hazel of the Rootbloom (a hand edit)
        out = self.broken({"n": 1, "op": "add", "add": "Hazel of the Rootbloom"})
        self.assertEqual(out["cards"], SQUIRRELED_AWAY_LIST)
        self.assertEqual(out["warnings"],
                         ["Skipped change 1: it added Hazel of the Rootbloom, but it is the commander."])

    def test_a_swap_that_cannot_cut_is_skipped_whole_so_its_add_does_not_land_either(self):
        # swap Mind Stone (not in the deck) for Cultivate: Cultivate does not land either
        out = self.broken({"n": 1, "op": "swap", "cut": "Mind Stone", "add": "Cultivate"})
        self.assertEqual(out["cards"], SQUIRRELED_AWAY_LIST)
        self.assertEqual(len(out["warnings"]), 1)

    def test_a_group_skips_only_the_item_that_cannot_apply(self):
        # a group of [cut Mind Stone (absent), add Cultivate]: the add still lands
        out = self.broken({"n": 1, "op": "group", "label": "G", "items": [
            {"op": "cut", "cut": "Mind Stone"}, {"op": "add", "add": "Cultivate"}]})
        self.assertEqual(out["cards"][-1], [1, "Cultivate"])
        self.assertEqual(out["warnings"], ["Skipped change 1: it cut Mind Stone, but the deck does not have it."])

    def test_entries_that_are_not_changes_are_skipped_with_a_warning_each(self):
        # a stray string, null, an unknown op, an add with no card, a swap with no add, two bad groups
        out = self.broken("a stray line", None, {"n": 3, "op": "frobnicate"}, {"n": 4, "op": "add"},
                          {"n": 5, "op": "swap", "cut": "Swamp"}, {"n": 6, "op": "group", "items": "nope"},
                          {"n": 7, "op": "group", "items": ["x", {"op": "add", "add": "Cultivate"}]})
        self.assertEqual(out["cards"], SQUIRRELED_AWAY_LIST + [[1, "Cultivate"]])
        self.assertEqual(len(out["warnings"]), 7)
        self.assertIn("'frobnicate'", out["warnings"][2])
        self.assertIn("missing a card name", out["warnings"][3])

    def test_an_undo_of_a_change_that_is_not_there_does_nothing(self):
        # undo of change 9 in a log with no change 9
        self.assertEqual(self.broken({"n": 1, "op": "undo", "of": 9})["cards"], SQUIRRELED_AWAY_LIST)

    def test_odd_numbers_and_ids_do_not_crash_the_replay(self):
        # n as a list or a string, `of` as a list, add_id as a list
        out = self.broken({"n": [1], "op": "add", "add": "Mind Stone"}, {"n": "2", "op": "undo", "of": [1]},
                          {"op": "add", "add": "Cultivate", "add_id": ["x"]})
        self.assertEqual(names(out["cards"])[-2:], ["Mind Stone", "Cultivate"])

    def test_bad_lines_in_the_base_are_skipped_with_a_warning(self):
        # base card lines that are a string, a zero count or a non-text name; a commander that is a number
        base = dict(self.base, commanders=["Hazel of the Rootbloom", 7],
                    cards=[[1, "Sol Ring"], "Forest", [0, "Swamp"], [2, 5], [1, "Skullclamp"]])
        out = decks.current(base, {}, DB)
        self.assertEqual(out["cards"], [[1, "Sol Ring"], [1, "Skullclamp"]])
        self.assertEqual(len(out["warnings"]), 4)

    def test_a_base_with_no_ids_map_still_resolves_by_name(self):
        # an old or hand-made base without `ids`
        base = {k: v for k, v in self.base.items() if k != "ids"}
        self.assertEqual(decks.current(base, {}, DB)["cards"], SQUIRRELED_AWAY_LIST)

    def test_a_longer_session_replays_to_the_list_the_player_saw_after_every_step(self):
        # the deck the player held after each step, worked out by hand; replaying the file must agree each time
        def deck(**changes):
            counts = {"Sol Ring": 1, "Skullclamp": 1, "Chatterfang, Squirrel General": 1, "Command Tower": 1,
                      "Swamp": 8, "Forest": 9}
            counts.update(changes)
            return counts
        steps = [
            ({"op": "add", "card": "Mind Stone"}, {"Mind Stone": 1}),                                       # 1
            ({"op": "swap", "cut": "Swamp", "add": "Cultivate"}, {"Swamp": 7, "Cultivate": 1}),             # 2
            ({"op": "cut", "card": "Skullclamp"}, {"Skullclamp": 0}),                                       # 3
            ({"op": "add", "card": "Forest"}, {"Forest": 10}),                                              # 4
            ({"op": "group", "label": "Up to $25", "items": [{"op": "swap", "cut": "Forest", "add": "Rampant Growth"},
                                                              {"op": "add", "card": "Eternal Witness"}]},
             {"Forest": 9, "Rampant Growth": 1, "Eternal Witness": 1}),                                      # 5
            ({"op": "undo", "of": 2}, {"Swamp": 8, "Cultivate": 0}),                                        # 6
            ({"op": "swap", "cut": "Rampant Growth", "add": "Cultivate"}, {"Rampant Growth": 0, "Cultivate": 1}),   # 7
        ]
        held = {}
        for n, (change, effect) in enumerate(steps, 1):
            self.apply(change)
            held.update(effect)
            expected = {k: v for k, v in deck(**held).items() if v}
            out = decks.current(self.base, self.stored(), DB)
            self.assertEqual({name: copies for copies, name in out["cards"]}, expected, f"after change {n}")
            self.assertEqual(out["warnings"], [], f"after change {n}")


class DiffTests(DeckFiles):
    def setUp(self):
        super().setUp()
        self.new_version()
        self.base_cards = decks.current(self.base, {}, DB)["cards"]

    def diff(self):
        return decks.diff(self.base_cards, self.cards())

    def test_nothing_changed(self):
        # a version with no changes differs from its base by nothing
        self.assertEqual(self.diff(), {"added": [], "cut": []})

    def test_added_and_cut_cards_with_their_counts(self):
        # Swamp x2 and Skullclamp out; Cultivate, Rampant Growth, Mind Stone in
        self.apply({"op": "swap", "cut": "Swamp", "add": "Cultivate"})
        self.apply({"op": "swap", "cut": "Swamp", "add": "Rampant Growth"})
        self.apply({"op": "cut", "card": "Skullclamp"})
        self.apply({"op": "add", "card": "Mind Stone"})
        self.assertEqual(self.diff(), {"added": [[1, "Cultivate"], [1, "Rampant Growth"], [1, "Mind Stone"]],
                                       "cut": [[1, "Skullclamp"], [2, "Swamp"]]})

    def test_an_extra_copy_of_a_basic_is_added_by_the_difference(self):    # Forest 9 -> 12
        for _ in range(3):
            self.apply({"op": "add", "card": "Forest"})
        self.assertEqual(self.diff(), {"added": [[3, "Forest"]], "cut": []})

    def test_a_card_cut_and_put_back_is_not_a_difference(self):
        # cut Sol Ring, then add it again
        self.apply({"op": "cut", "card": "Sol Ring"})
        self.apply({"op": "add", "card": "Sol Ring"})
        self.assertEqual(self.diff(), {"added": [], "cut": []})

    def test_an_undone_change_is_not_a_difference(self):
        # cut Skullclamp, then undo the cut
        self.apply({"op": "cut", "card": "Skullclamp"})
        self.apply({"op": "undo", "of": 1})
        self.assertEqual(self.diff(), {"added": [], "cut": []})

    def test_a_card_renamed_upstream_is_not_one_cut_and_one_added_when_the_base_is_read_through_the_index(self):
        # Sol Ring is now 'Sol Ring Reforged': as stored it looks like a swap, through the index it is no change
        db = renamed_db("Sol Ring", "Sol Ring Reforged")
        today = decks.current(self.base, self.stored(), db)["cards"]
        raw = decks.diff(self.base["cards"], today)                       # the stored names against today's
        self.assertEqual((raw["added"], raw["cut"]), ([[1, "Sol Ring Reforged"]], [[1, "Sol Ring"]]))
        through_index = decks.diff(decks.current(self.base, {}, db)["cards"], today)
        self.assertEqual(through_index, {"added": [], "cut": []})

    def test_lists_may_repeat_a_name(self):
        # [[1, 'A'], [1, 'A']] counts as two A's
        self.assertEqual(decks.diff([[1, "A"], [1, "A"]], [[1, "A"]]), {"added": [], "cut": [[1, "A"]]})


# ----------------------------------------------------------------------------- changing a version
class ApplyTests(DeckFiles):
    def setUp(self):
        super().setUp()
        self.new_version()

    # --- what each op stores, and what it answers
    def test_an_add_is_stored_with_a_number_a_time_the_name_the_index_spells_and_its_id(self):
        # 'mind stone' becomes 'Mind Stone' with the index's id
        v, info = self.apply({"op": "add", "card": "mind stone"}, now=at(5))
        self.assertEqual(v["changes"], [{"n": 1, "at": at(5), "op": "add", "add": "Mind Stone",
                                         "add_id": "00000000-0000-4000-8000-000000000006", "source": "manual"}])
        self.assertEqual(info, {"changed": True, "message": "Added Mind Stone."})

    def test_a_cut_is_stored_with_the_cards_id(self):
        # 'skullclamp' becomes 'Skullclamp' with its id
        v, info = self.apply({"op": "cut", "card": "skullclamp"}, now=at(5))
        self.assertEqual(v["changes"][0], {"n": 1, "at": at(5), "op": "cut", "cut": "Skullclamp",
                                           "cut_id": "00000000-0000-4000-8000-000000000003", "source": "manual"})
        self.assertEqual(info, {"changed": True, "message": "Cut Skullclamp."})

    def test_a_swap_is_stored_with_both_ids_and_the_tools_own_suggestion_is_marked(self):
        # Swamp for Cultivate, suggested by the tool
        v, info = self.apply({"op": "swap", "cut": "Swamp", "add": "Cultivate", "source": "suggested"}, now=at(5))
        self.assertEqual(v["changes"][0], {"n": 1, "at": at(5), "op": "swap", "cut": "Swamp", "cut_id": SWAMP_ID,
                                           "add": "Cultivate", "add_id": "00000000-0000-4000-8000-000000000041",
                                           "source": "suggested"})
        self.assertEqual(info, {"changed": True, "message": "Swapped Swamp for Cultivate."})

    def test_a_group_is_stored_as_one_change_whose_items_carry_no_number_time_or_source(self):
        # three items under 'Up to $25': a swap, a cut and an add
        v, info = self.apply({"op": "group", "label": "Up to $25", "source": "suggested", "items": [
            {"op": "swap", "cut": "Swamp", "add": "Cultivate"}, {"op": "cut", "card": "Skullclamp"},
            {"op": "add", "card": "Mind Stone"}]}, now=at(5))
        self.assertEqual(v["changes"], [{"n": 1, "at": at(5), "op": "group", "label": "Up to $25", "items": [
            {"op": "swap", "cut": "Swamp", "cut_id": SWAMP_ID, "add": "Cultivate",
             "add_id": "00000000-0000-4000-8000-000000000041"},
            {"op": "cut", "cut": "Skullclamp", "cut_id": "00000000-0000-4000-8000-000000000003"},
            {"op": "add", "add": "Mind Stone", "add_id": "00000000-0000-4000-8000-000000000006"}],
            "source": "suggested"}])
        self.assertEqual(info, {"changed": True, "message": 'Applied "Up to $25": 3 changes.'})

    def test_an_undo_is_stored_as_a_new_entry_and_the_original_stays(self):
        # cut Skullclamp (1), then undo 1 (2): both entries stay in the log
        self.apply({"op": "cut", "card": "Skullclamp"})
        v, info = self.apply({"op": "undo", "of": 1}, now=at(6))
        self.assertEqual(v["changes"][1], {"n": 2, "at": at(6), "op": "undo", "of": 1})
        self.assertEqual(v["changes"][0]["op"], "cut")                  # history is never deleted
        self.assertEqual(info, {"changed": True, "message": "Undid change 1 (cut Skullclamp)."})

    def test_the_source_defaults_to_manual_and_must_be_one_of_the_two(self):
        # no source means manual; 'robot', null and 1 are refused
        v, _ = self.apply({"op": "add", "card": "Mind Stone"})
        self.assertEqual(v["changes"][0]["source"], "manual")
        for source in ("robot", None, 1):
            with self.assertRaises(decks.DeckError, msg=source):
                self.apply({"op": "add", "card": "Cultivate", "source": source})

    def test_a_write_adds_one_to_the_revision_and_sets_updated_and_the_file_matches_the_answer(self):
        # two adds at :05 and :06 take the version from revision 0 to 2
        v, _ = self.apply({"op": "add", "card": "Mind Stone"}, now=at(5))
        self.assertEqual((v["revision"], v["updated"], v["created"]), (1, at(5), at(1)))
        self.assertEqual(self.stored(), v)
        v, _ = self.apply({"op": "add", "card": "Cultivate"}, now=at(6))
        self.assertEqual((v["revision"], v["updated"]), (2, at(6)))

    def test_change_numbers_count_up_and_follow_the_highest_number_already_in_the_file(self):
        # a hand edit renumbers change 2 as 7: the next change is 8
        self.apply({"op": "add", "card": "Mind Stone"})
        self.apply({"op": "add", "card": "Cultivate"})
        self.assertEqual([c["n"] for c in self.stored()["changes"]], [1, 2])
        doc = self.stored()
        doc["changes"][1]["n"] = 7                                      # a hand edit or a merge left a gap
        with open(self.path("andy", "go-wide.json"), "w") as f:
            json.dump(doc, f)
        v, _ = self.apply({"op": "add", "card": "Rampant Growth"})
        self.assertEqual(v["changes"][-1]["n"], 8)

    def test_a_session_stays_replayable_every_stored_change_applies_cleanly(self):
        # add, swap, cut, add again, undo the swap: no warning on replay
        for change in ({"op": "add", "card": "Mind Stone"}, {"op": "swap", "cut": "Forest", "add": "Cultivate"},
                       {"op": "cut", "card": "Mind Stone"}, {"op": "add", "card": "Mind Stone"},
                       {"op": "undo", "of": 2}):
            self.apply(change)
        self.assertEqual(decks.current(self.base, self.stored(), DB)["warnings"], [])

    # --- basics and cards that allow any number may repeat
    def test_basic_lands_and_any_number_cards_may_be_added_again(self):
        # a tenth Forest, two Relentless Rats, and a Swamp swapped for another Forest
        self.apply({"op": "add", "card": "Forest"})                         # a tenth Forest
        self.apply({"op": "add", "card": "Relentless Rats"})
        self.apply({"op": "add", "card": "Relentless Rats"})                # ... and a second Rats
        self.apply({"op": "swap", "cut": "Swamp", "add": "Forest"})         # a basic for a basic already there
        self.assertEqual({n: c for c, n in self.cards()}["Forest"], 11)
        self.assertEqual({n: c for c, n in self.cards()}["Relentless Rats"], 2)

    # --- the revision comes first
    def test_a_stale_revision_is_a_conflict_that_carries_the_current_revision(self):
        # sent revision 0 when the file is at 1
        self.apply({"op": "add", "card": "Mind Stone"})
        with self.assertRaises(decks.Conflict) as ctx, self.unchanged():
            decks.apply(self.root, "andy", "go-wide", {"op": "add", "card": "Cultivate"}, revision=0, db=DB)
        self.assertEqual((ctx.exception.status, ctx.exception.revision), (409, 1))
        self.assertIn("revision 0", ctx.exception.message)
        self.assertIn("now 1", ctx.exception.message)

    def test_a_revision_ahead_of_the_file_is_a_conflict_too(self):
        # sent revision 5 when the file is at 0
        with self.assertRaises(decks.Conflict) as ctx:
            decks.apply(self.root, "andy", "go-wide", {"op": "add", "card": "Cultivate"}, revision=5, db=DB)
        self.assertEqual(ctx.exception.revision, 0)

    def test_a_stale_revision_with_an_invalid_card_is_a_conflict_not_invalid(self):
        # revision is checked before any card rule
        self.apply({"op": "add", "card": "Mind Stone"})
        for change in ({"op": "add", "card": "Fire // Ice"},                 # outside the colors
                       {"op": "add", "card": "Griselbrand"},                 # banned
                       {"op": "add", "card": "Sol Rnig"},                    # no such card
                       {"op": "cut", "card": "Mana Crypt"},                  # not in the deck
                       {"op": "undo", "of": 99}):                            # no such change
            with self.assertRaises(decks.Conflict, msg=change), self.unchanged():
                decks.apply(self.root, "andy", "go-wide", change, revision=0, db=DB)

    def test_a_stale_revision_with_a_malformed_change_is_still_a_conflict(self):    # nothing else is checked
        self.apply({"op": "add", "card": "Mind Stone"})
        for change in ({"op": "frobnicate"}, "not an object", {"op": "add"}, None):
            with self.assertRaises(decks.Conflict, msg=change):
                decks.apply(self.root, "andy", "go-wide", change, revision=0, db=DB)

    def test_a_revision_that_is_not_a_whole_number_is_a_400(self):
        # None, '0', 0.0, True, -1 and [0]
        for revision in (None, "0", 0.0, True, -1, [0]):
            with self.assertRaises(decks.DeckError, msg=revision) as ctx:
                decks.apply(self.root, "andy", "go-wide", {"op": "add", "card": "Mind Stone"}, revision=revision, db=DB)
            self.assertEqual(ctx.exception.status, 400)

    # --- the card rules: each is a 422 with a message a player can read, and nothing is written
    def assertRefused(self, change, message, **kw):
        with self.assertRaises(decks.Invalid, msg=change) as ctx, self.unchanged():
            self.apply(change, **kw)
        self.assertEqual(ctx.exception.status, 422)
        self.assertEqual(ctx.exception.message, message)
        return ctx.exception

    def test_an_unknown_name_comes_with_up_to_three_close_names(self):
        # 'Sol Rnig' has one close name; 'Zzzzzzzzzz' has none
        err = self.assertRefused({"op": "add", "card": "Sol Rnig"},
                                 'No card is called "Sol Rnig". Close names: Sol Ring.')
        self.assertEqual(err.details, [{"text": "Sol Rnig", "suggestions": ["Sol Ring"]}])
        err = self.assertRefused({"op": "add", "card": "Zzzzzzzzzz"}, 'No card is called "Zzzzzzzzzz".')
        self.assertEqual(err.details, [{"text": "Zzzzzzzzzz", "suggestions": []}])

    def test_close_names_are_limited_to_three(self):    # five cards are close to "Test Card"; only three are offered
        cards = sample_cards()
        for letter in "ABCDE":
            name = f"Test Card {letter}"
            cards[name] = dict(cards["Mind Stone"], name=name, front=name)
        with self.assertRaises(decks.Invalid) as ctx:
            self.apply({"op": "add", "card": "Test Card"}, db=carddb.CardDB(cards))
        self.assertEqual(len(ctx.exception.details[0]["suggestions"]), 3)
        self.assertEqual(ctx.exception.message.count("Test Card "), 3)

    def test_a_banned_card(self):
        # add Griselbrand
        self.assertRefused({"op": "add", "card": "Griselbrand"}, "Griselbrand is banned in Commander.")

    def test_a_card_that_is_not_legal_in_commander(self):
        # a playtest card: the sample index holds its not-legal printing
        self.assertEqual(DB.get("Pick Your Poison")["legal"], "not_legal")
        self.assertRefused({"op": "add", "card": "Pick Your Poison"}, "Pick Your Poison is not legal in Commander.")

    def test_a_card_outside_the_commanders_colors_names_the_colors(self):
        # Counterspell (blue) and Fire // Ice (blue and red) for a black-green deck
        self.assertRefused({"op": "add", "card": "Counterspell"},
                           "Counterspell is outside the commander's colors: it has Blue in its color identity, "
                           "and the deck is Black and Green.")
        self.assertRefused({"op": "add", "card": "Fire // Ice"},
                           "Fire // Ice is outside the commander's colors: it has Blue and Red in its color identity, "
                           "and the deck is Black and Green.")

    def test_only_the_colors_that_are_outside_are_named(self):
        # Lim-Dul's Vault is blue and black; the deck has black
        self.assertRefused({"op": "add", "card": "Lim-Dul's Vault"},
                           "Lim-Dûl's Vault is outside the commander's colors: it has Blue in its color identity, "
                           "and the deck is Black and Green.")

    def test_colorless_cards_and_cards_inside_the_colors_are_fine(self):
        # five adds, all accepted
        # colorless, then green, then black cards
        for card in ("Mind Stone", "Aether Vial", "Cultivate", "Reanimate", "Demonic Tutor"):
            v, info = self.apply({"op": "add", "card": card})
            self.assertTrue(info["changed"], card)

    def test_two_commanders_share_their_colors(self):    # Pir (green) and Toothy (blue): blue is in, black is out
        decks.new_base(self.root, name="Pair", commanders=["Pir, Imaginative Rascal", "Toothy, Imaginary Friend"],
                       cards=[(1, "Sol Ring")], source={"type": "paste"}, created_by="andy", db=DB)
        decks.new_version(self.root, player="andy", name="Pair deck", base_id="pair", settings={})
        decks.apply(self.root, "andy", "pair-deck", {"op": "add", "card": "Counterspell"}, revision=0, db=DB)
        with self.assertRaisesRegex(decks.Invalid, "the deck is Blue and Green"):
            decks.apply(self.root, "andy", "pair-deck", {"op": "add", "card": "Reanimate"}, revision=1, db=DB)

    def test_a_commander_the_index_does_not_know_turns_no_card_away_for_its_colors(self):
        # Hazel is missing from the index, so Counterspell is accepted: the colors cannot be known
        cards = sample_cards()
        del cards["Hazel of the Rootbloom"]
        v, info = self.apply({"op": "add", "card": "Counterspell"}, db=carddb.CardDB(cards))
        self.assertTrue(info["changed"])                                 # the colors are unknown, so no card is refused

    def test_cutting_a_card_that_is_not_in_the_deck(self):
        # cut Mana Crypt
        self.assertRefused({"op": "cut", "card": "Mana Crypt"}, "Mana Crypt is not in the deck, so it cannot be cut.")

    def test_cutting_a_card_that_is_in_the_deck_under_another_spelling_works(self):
        # cut 'CHATTERFANG,  squirrel general'
        v, info = self.apply({"op": "cut", "card": "CHATTERFANG,  squirrel general"})
        self.assertEqual(v["changes"][0]["cut"], "Chatterfang, Squirrel General")

    def test_the_commander_cannot_be_cut(self):
        # cut 'hazel of the rootbloom'
        self.assertRefused({"op": "cut", "card": "hazel of the rootbloom"},
                           "Hazel of the Rootbloom is the commander, so it cannot be cut.")

    def test_cutting_a_name_nobody_knows_is_an_unknown_card_not_a_missing_card(self):
        # cut 'Sol Rnig'
        self.assertRefused({"op": "cut", "card": "Sol Rnig"}, 'No card is called "Sol Rnig". Close names: Sol Ring.')

    def test_a_cut_does_not_ask_whether_the_card_is_legal(self):    # cutting the banned card is how a deck gets fixed
        decks.new_base(self.root, name="Old", commanders=["Hazel of the Rootbloom"], cards=[(1, "Griselbrand")],
                       source={"type": "paste"}, created_by="andy", db=DB)
        decks.new_version(self.root, player="andy", name="Old deck", base_id="old", settings={})
        v, info = decks.apply(self.root, "andy", "old-deck", {"op": "cut", "card": "Griselbrand"}, revision=0, db=DB)
        self.assertTrue(info["changed"])

    def test_a_swap_whose_added_card_is_already_in_the_deck(self):
        # swap Swamp for Sol Ring, which the deck has
        self.assertRefused({"op": "swap", "cut": "Swamp", "add": "Sol Ring"},
                           "Sol Ring is already in the deck, and only basic lands and cards that say so may have "
                           "more than one copy.")

    def test_a_swap_that_adds_the_commander(self):
        # swap Swamp for Hazel of the Rootbloom
        self.assertRefused({"op": "swap", "cut": "Swamp", "add": "Hazel of the Rootbloom"},
                           "Hazel of the Rootbloom is the commander, so it is already in the deck.")

    def test_a_swap_whose_cut_card_is_not_in_the_deck(self):
        # swap Mana Crypt (absent) for Cultivate
        self.assertRefused({"op": "swap", "cut": "Mana Crypt", "add": "Cultivate"},
                           "Mana Crypt is not in the deck, so it cannot be cut.")

    def test_a_swap_names_an_unknown_card_on_either_side(self):
        # 'Sol Rnig' as the cut, then 'Cultivte' as the add
        self.assertRefused({"op": "swap", "cut": "Sol Rnig", "add": "Cultivate"},
                           'No card is called "Sol Rnig". Close names: Sol Ring.')
        self.assertRefused({"op": "swap", "cut": "Swamp", "add": "Cultivte"},
                           'No card is called "Cultivte". Close names: Cultivate.')

    def test_a_swap_checks_the_added_card_for_legality_and_colors(self):
        # swap Swamp for Griselbrand (banned), then for Counterspell (blue)
        self.assertRefused({"op": "swap", "cut": "Swamp", "add": "Griselbrand"}, "Griselbrand is banned in Commander.")
        self.assertRefused({"op": "swap", "cut": "Swamp", "add": "Counterspell"},
                           "Counterspell is outside the commander's colors: it has Blue in its color identity, "
                           "and the deck is Black and Green.")

    def test_the_rules_are_checked_in_the_order_the_module_lists_them(self):    # each line: the earlier rule wins
        # an unknown name beats a banned card
        self.assertRefused({"op": "swap", "cut": "Zzzzzzzzzz", "add": "Griselbrand"}, 'No card is called "Zzzzzzzzzz".')
        # the added card's legality and colors are checked before whether the cut card is in the deck
        self.assertRefused({"op": "swap", "cut": "Mana Crypt", "add": "Griselbrand"},
                           "Griselbrand is banned in Commander.")
        self.assertRefused({"op": "swap", "cut": "Mana Crypt", "add": "Counterspell"},
                           "Counterspell is outside the commander's colors: it has Blue in its color identity, "
                           "and the deck is Black and Green.")
        # a cut card that is not in the deck beats "the added card is already in the deck"
        self.assertRefused({"op": "swap", "cut": "Mana Crypt", "add": "Sol Ring"},
                           "Mana Crypt is not in the deck, so it cannot be cut.")

    def test_legality_is_checked_before_colors(self):
        # Griselbrand is banned and, for a green commander, also off-color
        decks.new_base(self.root, name="Green", commanders=["Pir, Imaginative Rascal"], cards=[],
                       source={"type": "paste"}, created_by="andy", db=DB)
        decks.new_version(self.root, player="andy", name="Green deck", base_id="green", settings={})
        with self.assertRaisesRegex(decks.Invalid, "Griselbrand is banned in Commander"):
            decks.apply(self.root, "andy", "green-deck", {"op": "add", "card": "Griselbrand"}, revision=0, db=DB)

    def test_card_rules_come_before_nothing_to_do(self):
        # a banned card already in the list is refused, not shrugged off
        decks.new_base(self.root, name="Old", commanders=["Hazel of the Rootbloom"], cards=[(1, "Griselbrand")],
                       source={"type": "paste"}, created_by="andy", db=DB)
        decks.new_version(self.root, player="andy", name="Old deck", base_id="old", settings={})
        with self.assertRaisesRegex(decks.Invalid, "banned"):
            decks.apply(self.root, "andy", "old-deck", {"op": "add", "card": "Griselbrand"}, revision=0, db=DB)

    # --- nothing to do: changed False, and not one byte written
    def assertNothingToDo(self, change, message):
        with self.unchanged():
            v, info = self.apply(change)
        self.assertEqual(info, {"changed": False, "message": message})
        self.assertEqual(v["revision"], self.stored()["revision"])
        self.assertEqual(v, self.stored())

    def test_adding_a_one_copy_card_the_deck_already_has(self):
        # add 'sol ring'
        self.assertNothingToDo({"op": "add", "card": "sol ring"}, "Sol Ring is already in the deck; nothing changed.")

    def test_adding_a_card_that_an_earlier_change_added(self):
        # add Mind Stone twice
        self.apply({"op": "add", "card": "Mind Stone"})
        self.assertNothingToDo({"op": "add", "card": "Mind Stone"},
                               "Mind Stone is already in the deck; nothing changed.")

    def test_adding_the_commander(self):
        # add Hazel of the Rootbloom
        self.assertNothingToDo({"op": "add", "card": "Hazel of the Rootbloom"},
                               "Hazel of the Rootbloom is the commander, so it is already in the deck; "
                               "nothing changed.")

    def test_a_swap_of_a_card_for_itself(self):
        # Sol Ring for 'sol ring', and Forest for Forest
        self.assertNothingToDo({"op": "swap", "cut": "Sol Ring", "add": "sol ring"},
                               "Swapping Sol Ring for itself changes nothing.")
        self.assertNothingToDo({"op": "swap", "cut": "Forest", "add": "Forest"},
                               "Swapping Forest for itself changes nothing.")

    def test_undoing_a_change_that_is_already_undone(self):
        # cut Skullclamp (1), undo 1 (2), undo 1 again
        self.apply({"op": "cut", "card": "Skullclamp"})
        self.apply({"op": "undo", "of": 1})
        self.assertNothingToDo({"op": "undo", "of": 1}, "Change 1 is already undone; nothing changed.")

    def test_a_group_in_which_every_item_does_nothing_does_nothing(self):
        # add Sol Ring (already there) and swap Forest for Forest
        self.assertNothingToDo({"op": "group", "label": "Already there", "items": [
            {"op": "add", "card": "Sol Ring"}, {"op": "swap", "cut": "Forest", "add": "Forest"}]},
            'Nothing in "Already there" changes the deck; nothing changed.')

    # --- shape: a 400
    def test_a_malformed_change_is_a_400_and_writes_nothing(self):
        # 26 shapes that are not changes: each a 400, and the file is untouched
        bad = [None, "add Mind Stone", [], {}, {"op": None}, {"op": "frobnicate"}, {"op": "ADD", "card": "Mind Stone"},
               {"op": "add"}, {"op": "add", "card": ""}, {"op": "add", "card": 5}, {"op": "cut", "card": None},
               {"op": "swap", "cut": "Swamp"}, {"op": "swap", "add": "Cultivate"},
               {"op": "swap", "cut": "", "add": "Cultivate"},
               {"op": "undo"}, {"op": "undo", "of": 0}, {"op": "undo", "of": "1"}, {"op": "undo", "of": True},
               {"op": "group"}, {"op": "group", "label": "G"}, {"op": "group", "label": "G", "items": []},
               {"op": "group", "label": "G", "items": "x"},
               {"op": "group", "label": "", "items": [{"op": "add", "card": "Cultivate"}]},
               {"op": "group", "label": "G", "items": [
                   {"op": "group", "label": "H", "items": [{"op": "add", "card": "Cultivate"}]}]},
               {"op": "group", "label": "G", "items": [{"op": "undo", "of": 1}]},
               {"op": "group", "label": "G", "items": ["add Cultivate"]}]
        for change in bad:
            with self.assertRaises(decks.DeckError, msg=change) as ctx, self.unchanged():
                self.apply(change)
            self.assertEqual(ctx.exception.status, 400, change)

    def test_a_missing_version_player_or_base_is_a_404(self):
        # no such version, no such player, then the base file removed
        with self.assertRaisesRegex(decks.NotFound, "no version"):
            decks.apply(self.root, "andy", "no-such-version", {"op": "add", "card": "Mind Stone"}, revision=0, db=DB)
        with self.assertRaisesRegex(decks.NotFound, "no player"):
            decks.apply(self.root, "nobody", "go-wide", {"op": "add", "card": "Mind Stone"}, revision=0, db=DB)
        os.remove(self.path("bases", "squirreled-away.json"))
        with self.assertRaisesRegex(decks.NotFound, "base deck .squirreled-away. of this version is missing"):
            self.apply({"op": "add", "card": "Mind Stone"})

    def test_a_version_that_names_an_impossible_base_is_an_error_naming_it_not_a_400(self):    # a hand edit
        doc = self.stored()
        doc["base"] = "../etc"
        with open(self.path("andy", "go-wide.json"), "w") as f:
            json.dump(doc, f)
        with self.assertRaisesRegex(ValueError, "impossible id"):
            self.apply({"op": "add", "card": "Mind Stone"})


class GroupTests(DeckFiles):
    def setUp(self):
        super().setUp()
        self.new_version()

    def test_a_group_is_one_revision(self):
        # two swaps of Swamp in one group: revision 1, one log entry, Swamp 8 -> 6
        v, info = self.apply({"op": "group", "label": "Up to $25", "source": "suggested", "items": [
            {"op": "swap", "cut": "Swamp", "add": "Cultivate"},
            {"op": "swap", "cut": "Swamp", "add": "Rampant Growth"}]})
        self.assertEqual((v["revision"], len(v["changes"]), len(v["changes"][0]["items"])), (1, 1, 2))
        self.assertEqual({n: c for c, n in self.cards()}["Swamp"], 6)

    def test_one_broken_rule_rejects_the_whole_group_and_names_the_item(self):    # item 2 of 3 is outside the colors
        change = {"op": "group", "label": "Up to $25", "items": [
            {"op": "swap", "cut": "Swamp", "add": "Cultivate"},
            {"op": "swap", "cut": "Forest", "add": "Counterspell"},
            {"op": "add", "card": "Mind Stone"}]}
        with self.assertRaises(decks.Invalid) as ctx, self.unchanged():
            self.apply(change)
        self.assertEqual(ctx.exception.message,
                         "Item 2 of 3 (swap Forest for Counterspell) breaks a rule: Counterspell is outside the "
                         "commander's colors: it has Blue in its color identity, and the deck is Black and Green.")
        self.assertEqual(self.stored()["revision"], 0)                        # item 1 was not kept

    def test_items_are_checked_against_the_list_as_the_earlier_items_left_it(self):
        # the second item cuts the Skullclamp the first one already cut, so it breaks the cut rule
        change = {"op": "group", "label": "G", "items": [
            {"op": "cut", "card": "Skullclamp"}, {"op": "cut", "card": "Skullclamp"}]}
        with self.assertRaises(decks.Invalid) as ctx, self.unchanged():
            self.apply(change)
        self.assertEqual(ctx.exception.message,
                         "Item 2 of 2 (cut Skullclamp) breaks a rule: Skullclamp is not in the deck, "
                         "so it cannot be cut.")

    def test_an_item_can_use_a_card_an_earlier_item_added(self):
        # the Mind Stone the first item adds is cut by the second
        v, info = self.apply({"op": "group", "label": "G", "items": [
            {"op": "add", "card": "Mind Stone"}, {"op": "swap", "cut": "Mind Stone", "add": "Arcane Signet"}]})
        self.assertTrue(info["changed"])
        self.assertEqual(names(self.cards())[-1], "Arcane Signet")
        self.assertNotIn("Mind Stone", names(self.cards()))

    def test_an_item_that_does_nothing_is_left_out_and_the_message_says_so(self):    # Sol Ring is already there
        v, info = self.apply({"op": "group", "label": "G", "items": [
            {"op": "add", "card": "Sol Ring"}, {"op": "add", "card": "Mind Stone"},
            {"op": "swap", "cut": "Forest", "add": "Forest"}]})
        self.assertEqual(v["changes"][0]["items"],
                         [{"op": "add", "add": "Mind Stone", "add_id": "00000000-0000-4000-8000-000000000006"}])
        self.assertEqual(info["message"], 'Applied "G": 1 change; 2 items already in place.')

    def test_a_group_inside_the_log_keeps_its_label_and_defaults_to_manual(self):
        # the label '  Tokens package ' is stored trimmed
        v, _ = self.apply({"op": "group", "label": "  Tokens package ", "items": [{"op": "add", "card": "Mind Stone"}]})
        self.assertEqual((v["changes"][0]["label"], v["changes"][0]["source"]), ("Tokens package", "manual"))

    def test_the_failing_items_close_names_are_passed_on(self):
        # the item 'add Sol Rnig' fails; its close name reaches the caller
        with self.assertRaises(decks.Invalid) as ctx:
            self.apply({"op": "group", "label": "G", "items": [{"op": "add", "card": "Sol Rnig"}]})
        self.assertEqual(ctx.exception.details, [{"text": "Sol Rnig", "suggestions": ["Sol Ring"]}])

    def test_a_large_group_of_swaps(self):    # eight Swamps out, eight cards in: the basics run out exactly
        cards = ["Cultivate", "Rampant Growth", "Eternal Witness", "Craterhoof Behemoth", "Heroic Intervention",
                 "Reanimate", "Demonic Tutor", "Exsanguinate"]
        v, info = self.apply({"op": "group", "label": "Everything", "items": [
            {"op": "swap", "cut": "Swamp", "add": card} for card in cards]})
        self.assertEqual(info["message"], 'Applied "Everything": 8 changes.')
        self.assertNotIn("Swamp", names(self.cards()))
        with self.assertRaises(decks.Invalid):                           # a ninth would cut a Swamp that is not there
            self.apply({"op": "group", "label": "One too many", "items": [
                {"op": "swap", "cut": "Swamp", "add": "Old Assassin"}]})


class UndoTests(DeckFiles):
    def setUp(self):
        super().setUp()
        self.new_version()

    def test_undoing_one_change_puts_the_deck_back_and_keeps_the_history(self):
        # swap Swamp for Cultivate (1), undo 1 (2)
        self.apply({"op": "swap", "cut": "Swamp", "add": "Cultivate"})
        self.apply({"op": "undo", "of": 1})
        self.assertEqual(self.cards(), SQUIRRELED_AWAY_LIST)
        self.assertEqual([c["op"] for c in self.stored()["changes"]], ["swap", "undo"])

    def test_undoing_a_group_undoes_all_of_it_at_once(self):
        # a three-item group, then one undo
        self.apply({"op": "group", "label": "Up to $25", "items": [
            {"op": "swap", "cut": "Swamp", "add": "Cultivate"}, {"op": "cut", "card": "Skullclamp"},
            {"op": "add", "card": "Mind Stone"}]})
        v, info = self.apply({"op": "undo", "of": 1})
        self.assertEqual(self.cards(), SQUIRRELED_AWAY_LIST)
        self.assertEqual((v["revision"], info["message"]), (2, 'Undid change 1 (group "Up to $25").'))

    def test_an_undo_is_blocked_by_a_later_change_that_needs_it_and_the_message_names_that_change(self):
        # change 1 added Mind Stone; change 2 cut it; without change 1 there is no Mind Stone for change 2 to cut
        self.apply({"op": "add", "card": "Mind Stone"})
        self.apply({"op": "cut", "card": "Mind Stone"})
        with self.assertRaises(decks.Invalid) as ctx, self.unchanged():
            self.apply({"op": "undo", "of": 1})
        self.assertEqual(ctx.exception.status, 422)
        self.assertEqual(ctx.exception.message,
                         "Change 1 (add Mind Stone) cannot be undone yet: change 2 cut Mind Stone, and with change 1 "
                         "undone the deck does not have it. Undo change 2 first.")

    def test_the_blocked_undo_works_once_the_later_change_is_undone_first(self):
        # add Mind Stone (1), cut it (2), undo 2, then undo 1
        self.apply({"op": "add", "card": "Mind Stone"})
        self.apply({"op": "cut", "card": "Mind Stone"})
        self.apply({"op": "undo", "of": 2})
        v, info = self.apply({"op": "undo", "of": 1})
        self.assertTrue(info["changed"])
        self.assertEqual(self.cards(), SQUIRRELED_AWAY_LIST)

    def test_an_undo_is_blocked_when_a_later_change_would_then_hold_a_second_copy(self):
        # change 1 cut Sol Ring and change 2 added it back; undoing 1 would put Sol Ring back for change 2 to add again
        self.apply({"op": "cut", "card": "Sol Ring"})
        self.apply({"op": "add", "card": "Sol Ring"})
        with self.assertRaises(decks.Invalid) as ctx, self.unchanged():
            self.apply({"op": "undo", "of": 1})
        self.assertEqual(ctx.exception.message,
                         "Change 1 (cut Sol Ring) cannot be undone yet: change 2 added Sol Ring, and with change 1 "
                         "undone the deck already has a copy. Undo change 2 first.")

    def test_an_undo_is_blocked_by_a_change_inside_a_later_group(self):
        # swap Swamp for Cultivate (1); a later group cuts that Cultivate (2); undo 1 is blocked by change 2
        self.apply({"op": "swap", "cut": "Swamp", "add": "Cultivate"})                  # change 1
        self.apply({"op": "group", "label": "G", "items": [                             # change 2
            {"op": "cut", "card": "Cultivate"}, {"op": "add", "card": "Mind Stone"}]})
        with self.assertRaisesRegex(decks.Invalid, "change 2 cut Cultivate"):
            self.apply({"op": "undo", "of": 1})

    def test_changes_that_do_not_depend_on_each_other_can_be_undone_in_any_order(self):
        # add Mind Stone (1), add Cultivate (2), cut Skullclamp (3): undo 1 first
        self.apply({"op": "add", "card": "Mind Stone"})            # 1
        self.apply({"op": "add", "card": "Cultivate"})             # 2
        self.apply({"op": "cut", "card": "Skullclamp"})            # 3
        self.apply({"op": "undo", "of": 1})                        # the oldest first, with newer changes still standing
        self.assertEqual(names(self.cards()), ["Sol Ring", "Chatterfang, Squirrel General", "Command Tower", "Swamp",
                                               "Forest", "Cultivate"])

    def test_a_later_change_that_was_itself_undone_no_longer_blocks(self):
        # add (1), cut (2), undo 2 (3): now undo 1 is allowed
        self.apply({"op": "add", "card": "Mind Stone"})            # 1
        self.apply({"op": "cut", "card": "Mind Stone"})            # 2
        self.apply({"op": "undo", "of": 2})                        # 3: the cut is cancelled, so nothing depends on 1
        v, info = self.apply({"op": "undo", "of": 1})
        self.assertTrue(info["changed"])

    def test_undoing_an_undo_is_refused_and_the_way_back_is_to_make_the_change_again(self):
        # cut Skullclamp (1), undo 1 (2), undo 2 is refused; cutting again is change 3
        self.apply({"op": "cut", "card": "Skullclamp"})
        self.apply({"op": "undo", "of": 1})
        with self.assertRaisesRegex(decks.Invalid, "Change 2 is itself an undo"), self.unchanged():
            self.apply({"op": "undo", "of": 2})
        v, info = self.apply({"op": "cut", "card": "Skullclamp"})            # the same cut again, as change 3
        self.assertEqual(v["changes"][-1]["n"], 3)
        self.assertNotIn("Skullclamp", names(self.cards()))

    def test_undoing_a_change_that_does_not_exist(self):
        # undo of change 5 when there is one change
        self.apply({"op": "add", "card": "Mind Stone"})
        with self.assertRaises(decks.Invalid) as ctx, self.unchanged():
            self.apply({"op": "undo", "of": 5})
        self.assertEqual(ctx.exception.message, "There is no change 5 to undo.")

    def test_a_problem_the_log_already_had_does_not_block_an_unrelated_undo(self):
        # a bad merge left a cut of a missing card
        self.apply({"op": "add", "card": "Mind Stone"})
        doc = self.stored()
        doc["changes"].append({"n": 2, "at": at(5), "op": "cut", "cut": "Mana Crypt", "source": "manual"})
        with open(self.path("andy", "go-wide.json"), "w") as f:
            json.dump(doc, f)
        v, info = self.apply({"op": "undo", "of": 1})
        self.assertTrue(info["changed"])

    def test_an_undo_is_checked_with_the_cards_the_index_spells_today(self):
        # Sol Ring has been renamed: cut it under its new name, then undo
        db = renamed_db("Sol Ring", "Sol Ring Reforged")
        self.apply({"op": "cut", "card": "Sol Ring Reforged"}, db=db)
        v, info = self.apply({"op": "undo", "of": 1}, db=db)
        self.assertEqual(decks.current(self.base, v, db)["cards"][0], [1, "Sol Ring Reforged"])


class UpdateTests(DeckFiles):
    def setUp(self):
        super().setUp()
        self.new_version(settings={"bracket": 3, "budget": 200, "themes": ["tokens"]})

    def update(self, **kw):
        kw.setdefault("revision", self.stored()["revision"])
        kw.setdefault("now", at(8))
        return decks.update(self.root, "andy", "go-wide", **kw)

    def test_renaming_bumps_the_revision_and_keeps_the_id_and_the_file(self):
        # '  Squirrels go very wide ' at :08: trimmed, revision 1, the file keeps its name
        v = self.update(name="  Squirrels go very wide ")
        self.assertEqual((v["name"], v["id"], v["revision"], v["updated"]),
                         ("Squirrels go very wide", "go-wide", 1, at(8)))
        self.assertEqual(self.stored(), v)
        self.assertEqual(os.listdir(self.path("andy")), ["go-wide.json"])

    def test_settings_given_replace_those_keys_and_the_rest_stay(self):    # a caller sends only the budget
        v = self.update(settings={"budget": 100})
        self.assertEqual(v["settings"], {"bracket": 3, "budget": 100, "themes": ["tokens"]})
        v = self.update(settings={"themes": [], "playstyle": "aristocrats", "budget": None})
        self.assertEqual(v["settings"], {"bracket": 3, "budget": None, "themes": [], "playstyle": "aristocrats"})
        self.assertEqual(v["revision"], 2)

    def test_name_and_settings_together_are_one_revision(self):
        # a new name and bracket 4 in one update
        v = self.update(name="New name", settings={"bracket": 4})
        self.assertEqual((v["revision"], v["name"], v["settings"]["bracket"]), (1, "New name", 4))

    def test_the_same_values_again_do_nothing(self):    # no write and no new revision
        with self.unchanged():
            v = self.update(name="Go wide", settings={"bracket": 3})
            v = self.update(settings={"themes": ["tokens"]})
        self.assertEqual(v["revision"], 0)

    def test_a_stale_revision_is_a_conflict(self):    # a phone and a desktop tab cannot overwrite each other's settings
        self.update(settings={"budget": 100})
        with self.assertRaises(decks.Conflict) as ctx, self.unchanged():
            decks.update(self.root, "andy", "go-wide", revision=0, settings={"budget": 50})
        self.assertEqual(ctx.exception.revision, 1)

    def test_an_update_and_a_change_each_need_the_revision_the_other_left(self):
        # update (0 -> 1), a stale change, a good change (1 -> 2), a stale update
        self.update(settings={"budget": 100})                                          # revision 1
        with self.assertRaises(decks.Conflict):
            decks.apply(self.root, "andy", "go-wide", {"op": "add", "card": "Mind Stone"}, revision=0, db=DB)
        v, _ = decks.apply(self.root, "andy", "go-wide", {"op": "add", "card": "Mind Stone"}, revision=1, db=DB)
        self.assertEqual(v["revision"], 2)
        with self.assertRaises(decks.Conflict):
            decks.update(self.root, "andy", "go-wide", revision=1, name="Late")

    def test_malformed_updates_are_400s(self):
        # nothing to update, a blank or non-text name, settings that are not an object, revision '0'
        for kw in (dict(), dict(name=""), dict(name=7), dict(settings=[]), dict(settings="x"), dict(settings={3: 4})):
            with self.assertRaises(decks.DeckError, msg=kw) as ctx, self.unchanged():
                self.update(**kw)
            self.assertEqual(ctx.exception.status, 400)
        with self.assertRaises(decks.DeckError):
            decks.update(self.root, "andy", "go-wide", revision="0", name="X")

    def test_a_missing_version_is_a_404(self):
        # update of andy/nope
        with self.assertRaises(decks.NotFound):
            decks.update(self.root, "andy", "nope", revision=0, name="X")


# ----------------------------------------------------------------------------- atomic writes and threads
class AtomicWriteTests(DeckFiles):
    def setUp(self):
        super().setUp()
        self.new_version()
        self.apply({"op": "add", "card": "Mind Stone"})

    def folder(self):
        return sorted(os.listdir(self.path("andy")))

    def test_a_write_that_fails_at_the_last_step_leaves_the_old_file_and_no_temporary_file(self):
        # the rename fails with 'disk full' while adding Cultivate
        before = self.raw("andy", "go-wide.json")
        with mock.patch.object(os, "replace", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                self.apply({"op": "add", "card": "Cultivate"})
        self.assertEqual(self.raw("andy", "go-wide.json"), before)
        self.assertEqual(self.folder(), ["go-wide.json"])
        self.assertEqual(self.stored()["revision"], 1)

    def test_a_write_that_fails_while_the_temporary_file_is_being_saved_leaves_nothing_behind(self):
        # the flush to disk fails after the temporary file is written
        before = self.raw("andy", "go-wide.json")
        with mock.patch.object(os, "fsync", side_effect=OSError("input/output error")):
            with self.assertRaises(OSError):
                self.apply({"op": "add", "card": "Cultivate"})
        self.assertEqual(self.raw("andy", "go-wide.json"), before)
        self.assertEqual(self.folder(), ["go-wide.json"])

    def test_the_file_is_not_touched_until_the_new_one_is_complete(self):
        # the old content is still there when the rename happens
        seen = []
        real_replace = os.replace

        def spying_replace(src, dst):
            with open(src, "rb") as new:
                seen.append((self.raw("andy", "go-wide.json"), new.read()))
            real_replace(src, dst)
        with mock.patch.object(os, "replace", spying_replace):
            self.apply({"op": "add", "card": "Cultivate"})
        old, new = seen[0]
        self.assertEqual(json.loads(old)["revision"], 1)
        self.assertEqual(json.loads(new)["revision"], 2)                  # the new file was whole before the rename
        self.assertEqual(self.raw("andy", "go-wide.json"), new)

    def test_the_temporary_file_is_in_the_same_folder_so_the_rename_cannot_cross_a_disk(self):
        # the rename's source and destination share a folder
        used = []
        real_replace = os.replace
        with mock.patch.object(os, "replace", lambda src, dst: (used.append((src, dst)), real_replace(src, dst))):
            self.apply({"op": "add", "card": "Cultivate"})
        src, dst = used[0]
        self.assertEqual(os.path.dirname(src), os.path.dirname(dst))
        self.assertNotEqual(src, dst)

    def test_creating_a_version_or_a_base_that_fails_leaves_no_file_and_no_temporary_file(self):
        # new_version and new_base with a failing rename
        with mock.patch.object(os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.new_version(name="Never saved")
            with self.assertRaises(OSError):
                decks.new_base(self.root, name="Never saved", commanders=["Hazel of the Rootbloom"], cards=[],
                               source={"type": "paste"}, created_by="andy", db=DB)
        self.assertEqual(self.folder(), ["go-wide.json"])
        self.assertEqual(os.listdir(self.path("bases")), ["squirreled-away.json"])

    def test_an_update_that_fails_changes_nothing(self):
        # renaming the deck fails at the last step
        before = self.raw("andy", "go-wide.json")
        with mock.patch.object(os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                decks.update(self.root, "andy", "go-wide", revision=1, name="Renamed")
        self.assertEqual(self.raw("andy", "go-wide.json"), before)
        self.assertEqual(self.folder(), ["go-wide.json"])

    def test_a_failed_write_can_be_retried_with_the_same_revision(self):
        # the first try fails; the same call then succeeds as change 2
        with mock.patch.object(os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.apply({"op": "add", "card": "Cultivate"})
        v, info = self.apply({"op": "add", "card": "Cultivate"})
        self.assertEqual((info["changed"], v["revision"], v["changes"][-1]["n"]), (True, 2, 2))

    def test_a_temporary_file_left_by_a_crash_does_not_get_in_the_way(self):
        # 'go-wide.json.1234.tmp' holding half a file sits in the folder
        with open(self.path("andy", "go-wide.json.1234.tmp"), "w") as f:
            f.write("{half a file")
        v, info = self.apply({"op": "add", "card": "Cultivate"})
        self.assertTrue(info["changed"])
        self.assertEqual([x["id"] for x in decks.versions(self.root, "andy")], ["go-wide"])
        self.assertEqual(decks.WARNINGS, [])


class ThreadTests(DeckFiles):
    def setUp(self):
        super().setUp()
        self.new_version()

    def slow_writes(self):
        """Every save takes a moment, so a second thread that is not held back would get in between the first one's
        check and its write."""
        real_write = decks._write

        def slow_write(path, doc):
            time.sleep(0.05)
            real_write(path, doc)
        return mock.patch.object(decks, "_write", slow_write)

    def run_threads(self, jobs):
        """Run each job in its own thread, all released at once; returns [(result, error)] in job order."""
        gate = threading.Barrier(len(jobs))
        out = [None] * len(jobs)

        def run(i, job):
            gate.wait()
            try:
                out[i] = (job(), None)
            except Exception as e:                 # noqa: BLE001  (the test inspects the error)
                out[i] = (None, e)
        threads = [threading.Thread(target=run, args=(i, job)) for i, job in enumerate(jobs)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)
            self.assertFalse(t.is_alive(), "a thread is stuck")
        return out

    def test_two_threads_changing_the_same_revision_exactly_one_wins_and_the_other_gets_a_conflict(self):
        # Mind Stone and Cultivate both sent on revision 0, released together, each save slowed to 50 ms
        def job(card):
            return lambda: decks.apply(self.root, "andy", "go-wide", {"op": "add", "card": card}, revision=0, db=DB)
        with self.slow_writes():
            results = self.run_threads([job("Mind Stone"), job("Cultivate")])
        wins = [r for r, e in results if e is None]
        losses = [e for r, e in results if e is not None]
        self.assertEqual((len(wins), len(losses)), (1, 1))
        self.assertIsInstance(losses[0], decks.Conflict)
        self.assertEqual(losses[0].revision, 1)
        stored = self.stored()
        self.assertEqual((stored["revision"], len(stored["changes"])), (1, 1))
        winner = wins[0][0]["changes"][0]["add"]
        self.assertEqual(stored["changes"][0]["add"], winner)

    def test_two_threads_making_the_same_version_exactly_one_wins(self):
        # albert's 'Same name' created twice at once
        def job():
            return decks.new_version(self.root, player="albert", name="Same name", base_id="squirreled-away",
                                     settings={})
        with self.slow_writes():
            results = self.run_threads([job, job])
        self.assertEqual(sorted(type(e).__name__ for r, e in results if e is not None), ["Conflict"])
        self.assertEqual(len([r for r, e in results if e is None]), 1)
        self.assertEqual(os.listdir(self.path("albert")), ["same-name.json"])

    def test_two_threads_making_the_same_base_exactly_one_wins(self):
        # the base 'Twin' created twice at once
        def job():
            return decks.new_base(self.root, name="Twin", commanders=["Hazel of the Rootbloom"], cards=[],
                                  source={"type": "paste"}, created_by="andy", db=DB)
        with self.slow_writes():
            results = self.run_threads([job, job])
        self.assertEqual(sorted(type(e).__name__ for r, e in results if e is not None), ["Conflict"])

    def test_changes_to_different_versions_do_not_wait_for_each_other(self):
        # each save waits until the other version's save has started, which only happens if the locks are per file
        self.new_version(name="Other")
        started = {"go-wide": threading.Event(), "other": threading.Event()}
        real_write = decks._write

        def write_when_the_other_is_writing(path, doc):
            mine = os.path.basename(path)[:-len(".json")]
            started[mine].set()
            if not started["other" if mine == "go-wide" else "go-wide"].wait(5):
                raise AssertionError(f"the save of {mine} could not overlap the other one: one lock for every file?")
            real_write(path, doc)

        def job(version_id):
            return lambda: decks.apply(self.root, "andy", version_id, {"op": "add", "card": "Mind Stone"},
                                       revision=0, db=DB)
        with mock.patch.object(decks, "_write", write_when_the_other_is_writing):
            results = self.run_threads([job("go-wide"), job("other")])
        self.assertEqual([e for r, e in results], [None, None])

    def test_eight_players_each_retry_on_a_conflict_and_every_change_lands_exactly_once(self):
        # eight cards added at once; on a Conflict a player re-reads the revision and retries
        cards = ["Mana Crypt", "Lotus Petal", "Arcane Signet", "Mind Stone", "Cultivate", "Rampant Growth",
                 "Eternal Witness", "Craterhoof Behemoth"]

        def job(card):
            def run():
                for _ in range(100):
                    try:
                        revision = decks.version(self.root, "andy", "go-wide")["revision"]
                        return decks.apply(self.root, "andy", "go-wide", {"op": "add", "card": card},
                                           revision=revision, db=DB)
                    except decks.Conflict:
                        continue
                raise AssertionError("never got in")
            return run
        results = self.run_threads([job(c) for c in cards])
        self.assertEqual([e for r, e in results], [None] * 8)
        stored = self.stored()
        self.assertEqual((stored["revision"], [c["n"] for c in stored["changes"]]), (8, list(range(1, 9))))
        self.assertEqual(sorted(c["add"] for c in stored["changes"]), sorted(cards))
        self.assertEqual(decks.current(self.base, stored, DB)["warnings"], [])
        self.assertEqual(os.listdir(self.path("andy")), ["go-wide.json"])


# ----------------------------------------------------------------------------- configuration
class ConfigTests(unittest.TestCase):
    def decks_folder(self, **environment):
        """config.DECKS as a fresh run of config.py computes it (the loaded module is left alone)."""
        env = {k: v for k, v in os.environ.items() if k != "MTG_COMMANDER_DECKS"}
        env.update(environment)
        with mock.patch.dict(os.environ, env, clear=True):
            return runpy.run_path(config.__file__)["DECKS"]

    def test_the_decks_folder_is_commander_decks_unless_the_environment_names_another(self):
        # no variable at all, then MTG_COMMANDER_DECKS=/somewhere/else
        self.assertEqual(self.decks_folder(), os.path.join(config.ROOT, "commander", "decks"))
        self.assertEqual(self.decks_folder(), os.path.join(config.COMMITTED, "decks"))
        self.assertEqual(self.decks_folder(MTG_COMMANDER_DECKS="/somewhere/else"), "/somewhere/else")

    def test_an_empty_setting_means_the_default(self):
        # MTG_COMMANDER_DECKS= (set but empty)
        self.assertEqual(self.decks_folder(MTG_COMMANDER_DECKS=""), os.path.join(config.COMMITTED, "decks"))


# ----------------------------------------------------------------------------- collections
class CollectionTests(DeckFiles):
    """andy's collection: the precons and loose cards andy owns, in andy/collection.json beside the versions."""

    def collection_file(self, doc, player="andy"):
        os.makedirs(self.path(player), exist_ok=True)
        with open(self.path(player, "collection.json"), "w", encoding="utf-8") as f:
            json.dump(doc, f)

    def test_a_player_with_no_collection_file_has_an_empty_collection_and_nothing_is_made(self):
        # nobody has saved one yet: empty, "updated" None, and no folder appears just from asking
        self.assertEqual(decks.collection(self.root, "andy"), {"schema": 1, "kind": "collection", "player": "andy",
                                                                "precons": [], "cards": [], "updated": None})
        self.assertFalse(os.path.exists(self.path("andy")))
        self.assertEqual(decks.collection_path(self.root, "andy"), self.path("andy", "collection.json"))

    def test_a_collection_file_is_exactly_this_text(self):
        # the documented key order, one precon and one card to a line, like the other deck files
        decks.save_collection(self.root, "andy", precons=["Animated Army", "Scions & Spellcraft (FINAL FANTASY XIV)"],
                              cards=[[1, "Sol Ring"]], now="2026-10-19T12:00:00Z")
        self.assertEqual(self.raw("andy", "collection.json").decode("utf-8"),
                         '{\n'
                         ' "schema": 1,\n'
                         ' "kind": "collection",\n'
                         ' "player": "andy",\n'
                         ' "precons": [\n'
                         '  "Animated Army",\n'
                         '  "Scions & Spellcraft (FINAL FANTASY XIV)"\n'
                         ' ],\n'
                         ' "cards": [\n'
                         '  [1, "Sol Ring"]\n'
                         ' ],\n'
                         ' "updated": "2026-10-19T12:00:00Z"\n'
                         '}\n')
        self.assertEqual(decks.collection(self.root, "andy")["precons"],
                         ["Animated Army", "Scions & Spellcraft (FINAL FANTASY XIV)"])

    def test_saving_precons_keeps_the_hand_edited_cards_and_any_key_the_tool_does_not_know(self):
        # andy typed two loose cards and a note into the file; adding a precon leaves them be
        self.collection_file({"schema": 1, "kind": "collection", "player": "andy", "precons": ["Animated Army"],
                              "cards": [[1, "Sol Ring"], [2, "Forest"]], "note": "the binder"})
        saved = decks.save_collection(self.root, "andy", precons=["Animated Army", "Peace Offering"], now=at(30))
        again = decks.collection(self.root, "andy")
        self.assertEqual((again["precons"], again["cards"], again["note"], again["updated"]),
                         (["Animated Army", "Peace Offering"], [[1, "Sol Ring"], [2, "Forest"]], "the binder", at(30)))
        self.assertEqual(saved, again)

    def test_a_precon_named_twice_is_kept_once(self):
        # 'animated army' after 'Animated Army' is the same box
        saved = decks.save_collection(self.root, "andy", precons=["Animated Army", " animated army "])
        self.assertEqual(saved["precons"], ["Animated Army"])

    def test_bad_arguments_are_400s_and_write_nothing(self):
        for kw in ({"precons": "Animated Army"}, {"precons": ["", "X"]}, {"precons": [], "cards": [["1", "Sol Ring"]]},
                   {"precons": [], "cards": [[0, "Sol Ring"]]}, {"precons": [], "cards": "Sol Ring"}):
            with self.subTest(kw=kw), self.assertRaises(decks.DeckError):
                decks.save_collection(self.root, "andy", **kw)
        self.assertFalse(os.path.exists(self.path("andy")))
        with self.assertRaises(decks.DeckError):                          # the folder of base decks is no player
            decks.collection(self.root, "bases")

    def test_a_damaged_file_names_itself_and_is_never_written_over(self):
        # each of these is a ValueError naming the file; save_collection leaves the file as it was
        cases = {"not json": "{ precons: [}", "wrong kind": {"schema": 1, "kind": "version", "precons": []},
                 "newer schema": {"schema": 2, "kind": "collection"},
                 "another player's": {"schema": 1, "kind": "collection", "player": "albert"},
                 "a precon that is not a name": {"schema": 1, "kind": "collection", "precons": [3]},
                 "a card line that is not a pair": {"schema": 1, "kind": "collection", "cards": [["Sol Ring", 1]]},
                 "no copies": {"schema": 1, "kind": "collection", "cards": [[0, "Sol Ring"]]},
                 "precons not a list": {"schema": 1, "kind": "collection", "precons": "Animated Army"}}
        for label, doc in cases.items():
            with self.subTest(label):
                if isinstance(doc, str):
                    os.makedirs(self.path("andy"), exist_ok=True)
                    with open(self.path("andy", "collection.json"), "w") as f:
                        f.write(doc)
                else:
                    self.collection_file(doc)
                with self.assertRaisesRegex(ValueError, "collection.json"):
                    decks.collection(self.root, "andy")
                before = self.raw("andy", "collection.json")
                with self.assertRaisesRegex(ValueError, "collection.json"):
                    decks.save_collection(self.root, "andy", precons=["Animated Army"])
                self.assertEqual(self.raw("andy", "collection.json"), before)

    def test_a_hand_made_file_that_leaves_out_the_player_and_the_lists_is_read_with_the_folders_player(self):
        self.collection_file({"schema": 1, "kind": "collection"})
        found = decks.collection(self.root, "andy")
        self.assertEqual((found["player"], found["precons"], found["cards"]), ("andy", [], []))

    def test_collection_is_not_a_version_id(self):
        # a version called "Collection" would be andy/collection.json, the collection itself
        with self.assertRaisesRegex(decks.DeckError, '"collection" cannot be a version id'):
            self.new_version(name="Collection")
        with self.assertRaises(decks.DeckError):
            self.new_version(name="Mine", version_id="collection")
        decks.save_collection(self.root, "andy", precons=["Animated Army"])
        with self.assertRaises(decks.DeckError) as caught:
            decks.version(self.root, "andy", "collection")
        self.assertEqual(caught.exception.status, 400)
        with self.assertRaises(decks.DeckError):
            decks.apply(self.root, "andy", "collection", {"op": "add", "card": "Mind Stone"}, revision=0, db=DB)
        with self.assertRaises(decks.DeckError):
            decks.update(self.root, "andy", "collection", revision=0, name="x")

    def test_the_listing_never_reads_the_collection_as_a_version(self):
        # andy has one version and a collection: one version listed, no warning about a file of the wrong kind
        self.new_version()
        decks.save_collection(self.root, "andy", precons=["Animated Army"])
        self.assertEqual([v["id"] for v in decks.versions(self.root, "andy")], ["go-wide"])
        self.assertEqual(decks.WARNINGS, [])
        # albert has only a collection: albert is a player with no versions yet
        decks.save_collection(self.root, "albert", precons=[])
        self.assertIn("albert", decks.players(self.root))
        self.assertEqual(decks.versions(self.root, "albert"), [])


class ParseListJsonTests(unittest.TestCase):
    """A pasted JSON deck in the New base deck box. Its problems are names, not lines: rewriting one line could break
    the JSON, so each unknown card comes with line None and its close names."""

    def test_a_json_deck_reads_like_a_text_one(self):
        text = json.dumps({"commanders": ["hazel of the rootbloom"], "cards": [[1, "Sol Ring"], {"name": "Forest",
                                                                                                 "count": 9}]})
        self.assertEqual(decks.parse_list(text, DB), {"commanders": ["Hazel of the Rootbloom"],
                                                     "cards": [[1, "Sol Ring"], [9, "Forest"]], "problems": []})

    def test_a_typo_in_a_json_deck_is_a_problem_on_no_line(self):
        out = decks.parse_list('{"commanders": ["Hazel of the Rootbloom"],\n "cards": ["Sol Rnig", "Forest"]}', DB)
        self.assertEqual(out["cards"], [[1, "Forest"]])
        self.assertEqual([(p["line"], p["text"]) for p in out["problems"]], [(None, "Sol Rnig")])
        self.assertEqual(out["problems"][0]["suggestions"][0], "Sol Ring")

    def test_json_that_cannot_be_read_and_a_collection_are_422s_that_say_why(self):
        for text, words in (('{"cards": [1 "Sol Ring"]}', "line 1, column 14"),
                            ('{"deck": []}', "a shape this tool does not know"),
                            ('{"schema": 1, "kind": "collection", "precons": []}', "a collection is not a deck")):
            with self.subTest(text=text), self.assertRaises(decks.Invalid) as caught:
                decks.parse_list(text, DB)
            self.assertIn(words, caught.exception.message)
            self.assertEqual(caught.exception.status, 422)

    def test_a_pasted_saved_version_is_replayed_on_its_base_deck_in_the_decks_folder(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        decks.new_base(root, name="Squirreled Away", commanders=["Hazel of the Rootbloom"], cards=SQUIRRELED_AWAY,
                       source=PRECON, created_by="andy", db=DB)
        decks.new_version(root, player="andy", name="Go wide", base_id="squirreled-away", settings={})
        decks.apply(root, "andy", "go-wide", {"op": "cut", "card": "Skullclamp"}, revision=0, db=DB)
        with open(os.path.join(root, "andy", "go-wide.json"), encoding="utf-8") as f:
            text = f.read()
        out = decks.parse_list(text, DB, root=root)
        self.assertNotIn("Skullclamp", [name for _, name in out["cards"]])
        self.assertEqual(sum(n for n, _ in out["cards"]), sum(n for n, _ in SQUIRRELED_AWAY) - 1)


if __name__ == "__main__":
    unittest.main()
