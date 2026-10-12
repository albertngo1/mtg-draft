"""Tests for serve.py: the deck server's API, driven over a real socket (port 0) with urllib on a small world of cards.

Nothing here reaches the network. The engine's collaborators (`prepare`, `combos`, `attributes`, `prices`, `upgrade`,
the precon lists and git) are the fakes in `Fakes`, which answer from the `World` below and record how they were
called; the card index is a few dozen hand-made cards; the metrics, the bracket rules and the deck files are the real
code. The world is Hazel of the Rootbloom's black and green deck, "Squirreled Away" in miniature: its base deck holds
nine different cards and eight basic lands, and the cards EDHREC "lists" for Hazel are the ones with a score.

Every test is a worked example on that world, with a one-line comment naming the scenario. Each test starts its own
server and stops it in tearDown (the request threads are joined, so nothing is left running and no socket is left
open); the suite is also run with `-X dev -W error`, which turns an unclosed socket into a failure."""
import collections, http.client, json, os, re, shutil, socket, subprocess, tempfile, threading, time, unittest
import urllib.error, urllib.parse, urllib.request
from types import SimpleNamespace
from unittest import mock
from mtgcommander import build, carddb, decklist, decks, net, render, roles, serve
from mtgcommander.providers import scryfall_tags, spellbook

CMDR = "Hazel of the Rootbloom"
EM = "—"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))      # a proxy in the environment must not see us
DECK = "/api/decks/andy/go-wide"
BASE_CARDS = [(1, "Sol Ring"), (1, "Arcane Signet"), (1, "Cultivate"), (1, "Go for the Throat"),
              (1, "Maelstrom Pulse"), (1, "Peregrin Took"), (1, "Ogre Slumlord"), (1, "Squirrel Mob"),
              (1, "Command Tower"), (4, "Forest"), (4, "Swamp")]
SETTINGS = {"bracket": 3, "budget": 50, "themes": ["tokens"], "playstyle": "aristocrats"}


def scry(name, types="Creature", cmc=2.0, cost="", text="", ci="", price=1.0, gc=False, legal="legal", rank=None):
    """A Scryfall-shaped card; carddb.card_record turns it into the record the server reads."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return {"oracle_id": "w-" + slug, "name": name, "layout": "normal", "mana_cost": cost, "cmc": float(cmc),
            "type_line": types, "oracle_text": text, "color_identity": list(ci), "keywords": [],
            "legalities": {"commander": legal}, "prices": {"usd": str(price)} if price is not None else {},
            "game_changer": gc, "edhrec_rank": rank, "image_uris": {"normal": f"https://img.test/{slug}.jpg"},
            "scryfall_uri": f"https://scryfall.test/{slug}"}


def score_record(value, kind="builder", evidence=None):
    return {"score": value, "parts": {"base": value, "resid": 0.0, "theme": 0.0, "salt": 0.0}, "kind": kind,
            "evidence": evidence or f"in {int(value * 100)}% of 1,125 Bracket 3 Hazel decks", "n": 1125, "pulls": {}}


class World:
    """Cards with their roles, attribute tags, scores and prices. A card with a score is one EDHREC lists for Hazel;
    a card without one is in the card index only, so the server has to score it when it is added."""

    def __init__(self):
        self.objs, self.role_of, self.attr_of, self.score_of, self.listed = [], {}, {}, {}, []
        self.combos = {"included": [], "almost": []}
        self.add(CMDR, f"Legendary Creature {EM} Squirrel Druid", 4, "{2}{B}{G}", "BG", price=3.95)
        for basic, color in (("Forest", "G"), ("Swamp", "B")):
            self.add(basic, f"Basic Land {EM} {basic}", 0, "", color, price=0.1)
        # the base deck
        self.add("Sol Ring", "Artifact", 1, "{1}", "", roles=["ramp"], attrs=["mana-rock"], score=0.9, price=1.5)
        self.add("Arcane Signet", "Artifact", 2, "{2}", "", roles=["ramp"], attrs=["mana-rock"], score=0.8, price=0.5)
        self.add("Cultivate", "Sorcery", 3, "{2}{G}", "G", roles=["ramp"], attrs=["land-ramp"], score=0.5, price=0.4)
        self.add("Go for the Throat", "Instant", 2, "{1}{B}", "B", roles=["removal"],
                 attrs=["removal-creature", "removal-destroy"], score=0.6, price=1.0)
        self.add("Maelstrom Pulse", "Sorcery", 3, "{1}{B}{G}", "BG", roles=["removal"],
                 attrs=["removal-permanent", "removal-destroy"], score=0.55, price=0.8)
        self.add("Peregrin Took", f"Legendary Creature {EM} Halfling Rogue", 2, "{1}{G}", "G", score=0.4, price=0.4)
        self.add("Ogre Slumlord", f"Creature {EM} Ogre Rogue", 5, "{3}{B}{B}", "B", score=0.1, price=0.3)
        self.add("Squirrel Mob", f"Creature {EM} Squirrel", 3, "{2}{G}", "G", score=0.3, price=0.3)
        self.add("Command Tower", "Land", 0, "", "", score=0.7, price=0.2)
        # cards EDHREC lists that the deck does not have yet
        self.add("Assassin's Trophy", "Instant", 2, "{B}{G}", "BG", roles=["removal"],
                 attrs=["removal-permanent", "removal-destroy"], score=0.7, price=2.0)
        self.add("Eternal Witness", f"Creature {EM} Human Shaman", 3, "{1}{G}{G}", "G", roles=["recursion"],
                 score=0.65, price=1.0)
        self.add("Mind Stone", "Artifact", 2, "{2}", "", roles=["ramp"], attrs=["mana-rock"], score=0.45, price=0.3)
        self.add("Demonic Tutor", "Sorcery", 2, "{1}{B}", "B", roles=["tutor"], score=0.5, price=25.0)
        self.add("Mana Crypt", "Artifact", 0, "{0}", "", roles=["ramp"], attrs=["mana-rock"], score=0.95,
                 price=150.0, gc=True)
        self.add("Craterhoof Behemoth", f"Creature {EM} Beast", 8, "{5}{G}{G}{G}", "G", roles=["finisher"],
                 attrs=["overrun"], score=0.8, price=20.0)
        self.add("Squirrel Nest", "Enchantment", 3, "{2}{G}", "G", score=0.35, price=0.5)
        # cards the index knows that EDHREC does not list for Hazel
        self.add("Unlisted Charm", "Instant", 1, "{G}", "G", price=0.2)
        self.add("Squirrel Hunter", f"Creature {EM} Human Archer", 2, "{1}{G}", "G", price=0.2, rank=900)
        self.add("Squirrel Prophet", f"Creature {EM} Squirrel Wizard", 2, "{1}{U}", "U", price=0.2, rank=300)
        self.add("Swords to Plowshares", "Instant", 1, "{W}", "W", price=2.0)
        self.add("Lim-Dûl's Vault", "Instant", 2, "{U}{B}", "UB", price=0.5)
        self.add("Griselbrand", f"Legendary Creature {EM} Demon", 8, "{4}{B}{B}{B}{B}", "B", legal="banned")

    def add(self, name, types, cmc, cost, ci, *, roles=(), attrs=(), score=None, **kw):
        self.objs.append(scry(name, types, cmc, cost, ci=ci, **kw))
        self.role_of[name], self.attr_of[name] = set(roles), frozenset(attrs)
        if score is not None:
            self.score_of[name] = score_record(score)
            self.listed.append(name)
        return name

    def db(self):
        return carddb.CardDB({rec["name"]: rec for rec in (carddb.card_record(obj) for obj in self.objs)})

    def score(self, name):
        """A card's score as the engine would give it: the listed score, or "not on this commander's lists"."""
        return self.score_of.get(name) or score_record(0.0, "none", "not on this commander's EDHREC lists (under ~5% of decks)")

    def price(self, name):
        for obj in self.objs:
            if obj["name"] == name:
                return float(obj["prices"]["usd"])
        return None


class Fakes:
    """The collaborators of serve.App, answering from the World and recording every call. `hold` makes prepare wait
    (a first open that takes time); `prepare_error` and `offline_error` make it fail."""

    def __init__(self, world):
        self.world, self.calls = world, collections.defaultdict(list)
        self.hold = threading.Event()
        self.hold.set()
        self.entered = threading.Event()               # set when prepare has been called
        self.prepare_error = self.offline_error = None
        self.popularity = False
        self.tags_available = True
        self.upgrade_result = None
        self.git_files = (["commander/decks/andy/go-wide.json"], None)

    def prepare(self, commanders, bracket, spec, db, *, deck_cards=(), owned=(), sources=None, refresh=None,
                offline=None, **kw):
        self.calls["prepare"].append({"commanders": list(commanders), "bracket": bracket, "spec": spec,
                                      "deck_cards": list(deck_cards), "owned": list(owned), "refresh": refresh,
                                      "offline": offline, "sources": sources})
        self.entered.set()
        if not self.hold.wait(10):
            raise AssertionError("a test left prepare held")
        if offline and self.offline_error:
            raise self.offline_error
        if self.prepare_error:
            raise self.prepare_error
        names = [n for n in dict.fromkeys(list(deck_cards) + self.world.listed)
                 if db.get(n) is not None and "Basic" not in db.get(n)["types"]]
        targets = {role: {"min": 1, "target": 2, "max": 3} for role in roles.ROLES}
        targets["land"] = {"min": 3, "target": 4, "max": 5}
        targets["topend"] = {"max": 1}
        return {"commanders": list(commanders), "ci": "BG", "bracket": bracket, "spec": spec,
                "evidence": {"theme_weights": {}, "cards": {}, "salt": {"Craterhoof Behemoth": 2.0}, "meta": None,
                             "popularity": self.popularity},
                "role_map": {n: set(self.world.role_of.get(n, ())) for n in names},
                "scores": {n: self.world.score(n) for n in names}, "targets": targets,
                "owned": set(owned), "include": [], "exclude": set(), "warnings": ["fake context warning"],
                "sources": {"edhrec": {"fetched": "2026-10-11T09:00:00Z", "cache": "fresh", "age_days": 0.1}}}

    def attributes(self, names, db, **kw):
        self.calls["attributes"].append(list(names))
        if not self.tags_available:
            return None
        return {n: self.world.attr_of.get(n, frozenset()) for n in names}

    def combos(self, commanders, cards, *, identity=None, offline=None):
        self.calls["combos"].append({"cards": list(cards), "identity": identity, "offline": offline})
        return dict(self.world.combos, fetched="2026-10-11T08:00:00Z", cache="fresh", via="index")

    def prices(self, names, db, *, offline=None):
        self.calls["prices"].append({"names": list(names), "offline": offline})
        return {db.get(n)["name"]: self.world.price(db.get(n)["name"]) for n in names
                if db.get(n) is not None and "Basic" not in db.get(n)["types"]}

    def upgrade(self, ctx, deck, db, *, budget=None, price_points=None, combos_fn=None, **kw):
        self.calls["upgrade"].append({"ctx": ctx, "deck": deck, "budget": budget, "price_points": price_points,
                                      "combos": combos_fn(deck["commanders"], [n for _, n in deck["cards"]])})
        if self.upgrade_result is not None:
            return self.upgrade_result
        swap = {"cut": "Ogre Slumlord", "add": "Mind Stone", "gain": 0.4, "price": 0.3, "owned": False, "forced": False,
                "reason": "fills ramp", "fills": ["ramp"], "evidence_add": "in 45% of decks", "kind_add": "builder",
                "evidence_cut": "in 10% of decks", "price_point": 25.0, "rank": 1}
        return {"command": "upgrade", "bracket": 3, "budget": budget, "spent": 0.3, "swaps": [swap],
                "price_points": [{"budget": 25.0, "spent": 0.3, "value": 5.0, "swaps": 1}],
                "blocked": [{"card": "Craterhoof Behemoth", "reason": "completes a combo", "gain": 0.5}],
                "cheap_adds": [], "warnings": ["fake upgrade warning"], "sources": {}}

    def precon(self, name, **kw):
        self.calls["precon"].append(name)
        if carddb.normalize(name) != "squirreled away":
            raise decklist.UnknownPrecon(name, ["Squirreled Away"])
        return {"name": "Squirreled Away", "code": "BLC", "file": "SquirreledAway_BLC", "release": "2024-08-02",
                "commanders": [CMDR], "cards": list(BASE_CARDS), "fetched": "2026-10-11T00:00:00Z", "url": "x"}

    def precon_names(self):
        return ["Animated Army", "Family Matters", "Peace Offering", "Squirreled Away"] + \
               [f"Test Precon {i:02d}" for i in range(30)]


class Reply:
    """What a call got back: the status, the JSON body (or text) and the headers."""

    def __init__(self, status, data, headers):
        self.status, self.headers = status, headers
        try:
            self.body = json.loads(data)
        except ValueError:
            self.body = None
        self.text = data.decode("utf-8", "replace")

    def __getitem__(self, key):
        return self.body[key]

    def error(self):
        return self.body["error"]


class ServerCase(unittest.TestCase):
    """A server on a free port, with a temporary decks folder holding the Squirreled Away base deck and andy's version
    "go-wide"; both are stopped, and their threads joined, when the test ends."""

    wait = 5.0                    # seconds a request waits for a preparation: long, so a fast fake is answered at once
    web = None
    base_cards = BASE_CARDS

    def extra_cards(self, world):
        """A hook: a test class adds its own cards to the world before the server starts."""

    def make_app_kwargs(self):
        return {}

    def setUp(self):
        for door in ("fetch_json", "request", "download"):          # a test that reaches the network is a bug
            mock.patch.object(net, door, side_effect=AssertionError(f"net.{door} must not run in a test")).start()
        mock.patch.object(scryfall_tags, "INFO", {}).start()          # what another test's tag load left behind
        self.addCleanup(mock.patch.stopall)
        del carddb.WARNINGS[:], roles.WARNINGS[:], decks.WARNINGS[:]
        self.addCleanup(lambda: [lst.clear() for lst in (carddb.WARNINGS, roles.WARNINGS, decks.WARNINGS)])
        self.world = World()
        self.extra_cards(self.world)
        self.db = self.world.db()
        self.fakes = Fakes(self.world)
        mock.patch.object(decklist, "precon", side_effect=self.fakes.precon).start()
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        decks.new_base(self.root, name="Squirreled Away", commanders=[CMDR], cards=self.base_cards,
                       source={"type": "precon", "name": "Squirreled Away", "mtgjson": "SquirreledAway_BLC"},
                       created_by="andy", db=self.db, now="2026-10-11T20:00:00Z")
        decks.new_version(self.root, player="andy", name="Go wide", base_id="squirreled-away", settings=dict(SETTINGS),
                          now="2026-10-11T20:01:00Z")
        self.logged = []
        options = dict(web=self.web, wait=self.wait, switches=serve.Switches(), log=self.logged.append,
                       prepare=self.fakes.prepare, combos=self.fakes.combos, attributes=self.fakes.attributes,
                       prices=self.fakes.prices, upgrade=self.fakes.upgrade, precon=self.fakes.precon,
                       precon_names=self.fakes.precon_names, uncommitted=lambda root: self.fakes.git_files)
        options.update(self.make_app_kwargs())
        self.app = serve.App(self.db, self.root, **options)
        self.server = serve.make_server(self.app, "127.0.0.1", 0, daemon=False)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01})
        self.thread.start()
        self.addCleanup(self.check_log)
        self.addCleanup(self.stop)

    def stop(self):
        self.fakes.hold.set()                                      # a test that held prepare must not hang the join
        self.server.shutdown()
        self.server.server_close()                                 # joins the request threads (daemon=False)
        self.thread.join()
        self.app.close()

    def check_log(self):
        """No traceback was logged: a request that failed unexpectedly shows up here, not as a quiet 500."""
        bad = [line for line in self.logged if "Traceback" in line]
        self.assertEqual(bad, [], "the server logged an unexpected error")

    # --- calls
    def call(self, method, path, body=None, headers=None, raw=None):
        """One request over a real socket: (status, parsed body, headers) as a Reply. `body` is sent as JSON with the
        JSON content type unless `headers` says otherwise; `raw` sends exactly these bytes."""
        data = raw if raw is not None else (None if body is None else json.dumps(body).encode("utf-8"))
        sent = dict(headers or {})
        if data is not None:
            sent.setdefault("Content-Type", "application/json")
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, method=method, headers=sent)
        try:
            with OPENER.open(request, timeout=20) as response:
                return Reply(response.status, response.read(), response.headers)
        except urllib.error.HTTPError as e:
            try:
                return Reply(e.code, e.read(), e.headers)
            finally:
                e.close()

    def get(self, path, **kw):
        return self.call("GET", path, **kw)

    def post(self, path, body=None, **kw):
        return self.call("POST", path, {} if body is None else body, **kw)

    def patch(self, path, body, **kw):
        return self.call("PATCH", path, body, **kw)

    def raw(self, method, path, headers=None, body=None):
        """A request with exact control of the headers (http.client sends the path and Host as given)."""
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            conn.putrequest(method, path, skip_host="Host" in (headers or {}), skip_accept_encoding=True)
            for name, value in (headers or {}).items():
                conn.putheader(name, value)
            if body is not None and "Content-Length" not in (headers or {}):
                conn.putheader("Content-Length", str(len(body)))
            conn.endheaders(body)
            response = conn.getresponse()
            return Reply(response.status, response.read(), response.headers)
        finally:
            conn.close()

    def open_deck(self, path=DECK):
        """GET the deck until it is ready (the fakes are quick, so this is one request)."""
        deadline = time.monotonic() + 10
        while True:
            reply = self.get(path)
            if reply.status != 202 or time.monotonic() > deadline:
                return reply
            time.sleep(0.01)

    def change(self, change, revision=None, path=DECK):
        """POST a change on the revision the deck is at now (unless `revision` says otherwise)."""
        if revision is None:
            revision = decks.version(self.root, *path.split("/")[3:5])["revision"]
        return self.post(path + "/changes", dict(change, revision=revision))

    def stored(self, version_id="go-wide", player="andy"):
        return decks.version(self.root, player, version_id)

    def combo(self, cards, produces, missing=(), tag="E"):
        """A combo as providers.spellbook makes it (a two-card one when two cards are given)."""
        return spellbook._combo("1-2", list(cards), [], list(produces), tag, len(cards), list(missing))

    def item(self, reply, item_id):
        for group in reply["metrics"]["groups"]:
            for item in group["items"]:
                if item["id"] == item_id:
                    return item
        raise AssertionError(f"no metric item {item_id}")

    def deck_value(self, reply):
        """build.deck_value of the cards in an answer, worked out from the same context the fake prepare builds."""
        ctx = self.fakes.prepare([CMDR], 3, {}, self.db, deck_cards=[c["name"] for c in reply["cards"]])
        copies = [c["name"] for c in reply["cards"] for _ in range(c["count"])]
        return round(build.deck_value(copies, ctx, self.db)["total"], 2)


# ----------------------------------------------------------------------------- opening a deck
class OpenDeckTests(ServerCase):
    def test_the_deck_answer_holds_everything_a_page_draws(self):
        # open andy's version: version, base, spec, commanders, cards, counts, difference, metrics, warnings, sources
        reply = self.open_deck()
        self.assertEqual(reply.status, 200)
        self.assertEqual(sorted(reply.body), sorted(["schema", "version", "base", "spec", "commanders", "cards",
                                                     "card_count", "diff", "cut_cards", "metrics", "warnings",
                                                     "sources"]))
        self.assertEqual(reply["schema"], 1)
        self.assertEqual((reply["version"]["id"], reply["version"]["player"], reply["version"]["revision"]),
                         ("go-wide", "andy", 0))
        self.assertEqual(reply["base"]["name"], "Squirreled Away")
        self.assertEqual(reply["card_count"], 18)                      # nine different cards, eight basics, the commander
        self.assertEqual(reply["diff"], {"added": [], "cut": []})
        self.assertEqual(reply["cut_cards"], [])
        self.assertEqual(reply["spec"]["bracket"], 3)
        self.assertEqual(reply["spec"]["themes"], ["tokens"])
        self.assertEqual([g["id"] for g in reply["metrics"]["groups"]],
                         ["power", "interaction", "mana", "playstyle", "win", "table", "changes"])

    def test_a_card_has_the_keys_a_page_needs(self):
        # Sol Ring in the deck list, and the commander: image, type, cost, price, owned, count, section, roles ...
        reply = self.open_deck()
        card = next(c for c in reply["cards"] if c["name"] == "Sol Ring")
        self.assertEqual(sorted(card), sorted(["name", "front", "image", "image_back", "scryfall_uri", "type", "cost",
                                               "cmc", "ci", "price", "owned", "count", "section", "new", "score",
                                               "roles", "gc"]))
        self.assertEqual((card["image"], card["type"], card["cost"], card["cmc"]),
                         ("https://img.test/sol-ring.jpg", "Artifact", "{1}", 1.0))
        self.assertEqual((card["count"], card["section"], card["new"], card["owned"]), (1, "Artifacts", False, True))
        self.assertEqual((card["price"], card["score"], card["roles"], card["gc"]), (1.5, 0.9, ["ramp"], False))
        commander = reply["commanders"][0]
        self.assertEqual((commander["name"], commander["ci"], commander["owned"]), (CMDR, "BG", True))
        self.assertEqual(sorted(commander), sorted(["name", "front", "image", "image_back", "scryfall_uri", "type",
                                                    "cost", "cmc", "ci", "price", "owned", "gc"]))

    def test_basic_lands_are_one_card_with_a_count_and_cost_nothing(self):
        # four Forests and four Swamps: one entry each with count 4, free and owned
        forest = next(c for c in self.open_deck()["cards"] if c["name"] == "Forest")
        self.assertEqual((forest["count"], forest["section"], forest["price"], forest["owned"]), (4, "Lands", 0.0, True))

    def test_the_headline_and_the_base_decks_values_come_with_every_metric(self):
        # the unchanged deck costs nothing to buy, and each item carries the base deck's value to compare with
        reply = self.open_deck()
        headline = reply["metrics"]["headline"]
        self.assertEqual((headline["bracket"], headline["price"], headline["bracket_ok"]), (3, 0.0, True))
        self.assertEqual(headline["score"], self.deck_value(reply))
        score = self.item(reply, "score")
        self.assertEqual(score["base"], score["value"])

    def test_a_first_open_that_takes_time_answers_202_with_progress_and_then_200(self):
        # the preparation is held: 202 at once, the request count and message move, then the deck is ready
        self.app.grace = 0
        self.fakes.hold.clear()
        first = self.get(DECK)
        self.assertEqual(first.status, 202)
        self.assertEqual(first.body, {"schema": 1, "status": "preparing", "revision": 0,
                                      "progress": first["progress"]})
        self.assertTrue(self.fakes.entered.wait(5))
        net.STATS["requests"] += 3                                    # three EDHREC pages fetched since it began
        deadline = time.monotonic() + 5
        while self.get(DECK)["progress"]["message"] != "Fetching EDHREC data for Hazel (first time only)":
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.01)
        progress = self.get(DECK)["progress"]
        self.assertEqual(progress["requests"], 3)
        self.fakes.hold.set()
        ready = self.open_deck()
        self.assertEqual(ready.status, 200)
        self.assertEqual(ready["version"]["id"], "go-wide")
        self.assertEqual(len(self.fakes.calls["prepare"]), 1)         # the polling did not start more preparations

    def test_the_progress_message_says_it_is_loading_scores_before_any_page_is_fetched(self):
        # nothing fetched yet, so "Loading card scores", not "Fetching ..."
        self.app.grace = 0
        self.fakes.hold.clear()
        self.get(DECK)
        self.assertTrue(self.fakes.entered.wait(5))
        deadline = time.monotonic() + 5
        while self.get(DECK)["progress"]["message"] != "Loading card scores for Hazel":
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.01)
        self.fakes.hold.set()

    def test_a_preparation_that_is_quick_is_answered_without_a_202(self):
        # the default wait lets a fast preparation finish inside the first request
        self.assertEqual(self.get(DECK).status, 200)

    def test_a_failed_preparation_answers_500_with_its_text_once_and_the_next_request_tries_again(self):
        # EDHREC is down and nothing is cached: data_unavailable carrying the error text; the retry works
        self.fakes.prepare_error = net.FetchError("edhrec", "https://json.edhrec.com/x", "offline and not cached")
        failed = self.get(DECK)
        self.assertEqual(failed.status, 500)
        self.assertEqual(failed.error()["code"], "data_unavailable")
        self.assertIn("offline and not cached", failed.error()["message"])
        self.assertEqual(failed.error()["details"], {"source": "edhrec"})
        self.fakes.prepare_error = None
        self.assertEqual(self.get(DECK).status, 200)
        self.assertEqual(len(self.fakes.calls["prepare"]), 2)

    def test_an_unexpected_error_is_a_500_with_the_exceptions_own_text_and_is_logged(self):
        # a bug in the engine: the page shows the real text, the server log keeps the traceback
        self.fakes.prepare_error = KeyError("no such evidence")
        failed = self.get(DECK)
        self.assertEqual((failed.status, failed.error()["code"]), (500, "server_error"))
        self.assertIn("no such evidence", failed.error()["message"])
        self.assertEqual(failed.error()["details"], {"type": "KeyError"})
        self.assertTrue(any("KeyError: 'no such evidence'" in line for line in self.logged))
        self.logged.clear()
        self.fakes.prepare_error = None

    def test_a_deck_file_that_cannot_be_read_is_a_500_that_names_the_file(self):
        # a git merge left markers in the file: the message carries its path
        path = os.path.join(self.root, "andy", "go-wide.json")
        with open(path, "w") as f:
            f.write("<<<<<<< HEAD\n{}\n")
        failed = self.get(DECK)
        self.assertEqual((failed.status, failed.error()["code"]), (500, "server_error"))
        self.assertIn(path, failed.error()["message"])
        self.logged[:] = [line for line in self.logged if "Traceback" not in line]

    def test_an_unknown_deck_is_404_a_bad_id_is_400(self):
        # no such version, no such player, and ids the decks module refuses
        missing = self.get("/api/decks/andy/nope")
        self.assertEqual((missing.status, missing.error()["code"]), (404, "not_found"))
        self.assertEqual(missing.error()["details"], {"suggestions": []})
        self.assertEqual(self.get("/api/decks/zed/go-wide").status, 404)
        for bad in ("/api/decks/Andy/go-wide", "/api/decks/andy/Go-Wide", "/api/decks/andy/..", "/api/decks/andy/con",
                    "/api/decks/bases/go-wide"):
            with self.subTest(path=bad):
                self.assertEqual(self.get(bad).status, 400)

    def test_a_deck_whose_base_is_missing_is_404(self):
        # the base deck file was deleted: the version cannot be opened, and says which base
        os.remove(os.path.join(self.root, "bases", "squirreled-away.json"))
        failed = self.get(DECK)
        self.assertEqual(failed.status, 404)
        self.assertIn("squirreled-away", failed.error()["message"])

    def test_the_owned_precons_in_the_settings_are_read_and_their_cards_count_as_owned(self):
        # owning Squirreled Away makes its cards cost nothing; a precon that cannot be read is a warning
        decks.update(self.root, "andy", "go-wide", revision=0, settings={"owned_precons": ["Squirreled Away", "Nope"]})
        reply = self.open_deck()
        self.assertEqual(reply.status, 200)
        self.assertIn("Squirreled Away", self.fakes.calls["precon"])
        owned = self.fakes.calls["prepare"][0]["owned"]
        self.assertIn("Sol Ring", owned)
        self.assertTrue(any('The precon "Nope" you own could not be read' in w for w in reply["warnings"]))

    def test_the_context_warnings_and_the_sources_come_with_the_answer(self):
        # the engine's own warning, and each source with its date and cache state (edhrec, combos, card index)
        reply = self.open_deck()
        self.assertIn("fake context warning", reply["warnings"])
        self.assertEqual(sorted(reply["sources"]), ["edhrec", "scryfall", "spellbook"])
        self.assertEqual(reply["sources"]["edhrec"]["cache"], "fresh")
        self.assertEqual(reply["sources"]["spellbook"]["fetched"], "2026-10-11T08:00:00Z")

    def test_the_tag_data_is_a_source_once_it_has_been_read(self):
        # the function tags were loaded 2026-10-09: the banner shows their date as well
        scryfall_tags.INFO.update(fetched="2026-10-09T04:00:00Z", cache="stale")
        sources = self.open_deck()["sources"]
        self.assertEqual((sources["scryfall_tags"]["fetched"], sources["scryfall_tags"]["cache"]),
                         ("2026-10-09T04:00:00Z", "stale"))

    def test_missing_tag_data_leaves_those_numbers_without_a_value_and_says_so(self):
        # offline with no saved tags: removal power has no value, and its why line says what is missing
        self.fakes.tags_available = False
        removal = self.item(self.open_deck(), "removal_power")
        self.assertIsNone(removal["value"])
        self.assertIn("function tags", removal["why"][0])

    def test_a_card_sheet_answers_no_threats_when_the_tag_data_is_missing(self):
        # without the function tags nothing is known about what a card answers: the list is empty, not a guess
        self.fakes.tags_available = False
        self.open_deck()
        reply = self.get("/api/cards/Go%20for%20the%20Throat?deck=andy/go-wide")
        self.assertEqual((reply.status, reply["answers"]), (200, []))

    def test_the_first_open_asks_the_engine_for_the_base_and_current_cards_and_the_owned_ones(self):
        # prepare is given the settings as a spec, the commander, every card of the list and the base deck as owned
        self.open_deck()
        call = self.fakes.calls["prepare"][0]
        self.assertEqual((call["commanders"], call["bracket"], call["refresh"]), ([CMDR], 3, False))
        self.assertEqual((call["spec"]["themes"], call["spec"]["playstyle"]), (["tokens"], "aristocrats"))
        self.assertEqual(sorted(call["deck_cards"]), sorted({n for _, n in BASE_CARDS}))
        self.assertEqual(sorted(call["owned"]), sorted({n for _, n in BASE_CARDS} | {CMDR}))

    def test_refresh_downloads_again_on_the_first_open_only(self):
        # serve --refresh: the first preparation asks for fresh data; a later re-score never does
        self.app.refresh = True
        self.open_deck()
        self.change({"op": "add", "card": "Unlisted Charm"})
        first, again = self.fakes.calls["prepare"]
        self.assertEqual((first["refresh"], again["refresh"]), (True, False))

    def test_a_change_made_outside_the_server_shows_up_on_the_next_read(self):
        # git pulled a new revision of the file (here: decks.apply from "another process"): no restart needed
        self.open_deck()
        decks.apply(self.root, "andy", "go-wide", {"op": "add", "card": "Mind Stone"}, revision=0, db=self.db)
        reply = self.get(DECK)
        self.assertEqual((reply["version"]["revision"], reply["diff"]["added"]), (1, [[1, "Mind Stone"]]))

    def test_a_card_that_arrives_with_the_file_and_has_no_score_is_scored_when_the_deck_is_read(self):
        # the pulled file adds Unlisted Charm, which this server has never scored
        self.open_deck()
        decks.apply(self.root, "andy", "go-wide", {"op": "add", "card": "Unlisted Charm"}, revision=0, db=self.db)
        reply = self.get(DECK)
        charm = next(c for c in reply["cards"] if c["name"] == "Unlisted Charm")
        self.assertEqual(charm["score"], 0.0)
        self.assertEqual(len(self.fakes.calls["prepare"]), 2)
        self.get(DECK)
        self.assertEqual(len(self.fakes.calls["prepare"]), 2)                    # once, not on every read

    def test_settings_changed_outside_the_server_prepare_the_deck_again(self):
        # the file now says Bracket 4: the next read notices that the prepared data is for Bracket 3
        self.open_deck()
        decks.update(self.root, "andy", "go-wide", revision=0, settings={"bracket": 4})
        reply = self.open_deck()
        self.assertEqual((reply["spec"]["bracket"], len(self.fakes.calls["prepare"])), (4, 2))

    def test_two_decks_are_independent_each_has_its_own_revision_and_cards(self):
        # andy's go-wide and albert's copy of the same base change side by side
        decks.new_version(self.root, player="albert", name="Mine", base_id="squirreled-away", settings={"bracket": 2})
        self.open_deck()
        self.open_deck("/api/decks/albert/mine")
        self.change({"op": "add", "card": "Mind Stone"})
        mine = self.change({"op": "add", "card": "Eternal Witness"}, path="/api/decks/albert/mine")
        self.assertEqual(mine["diff"]["added"], [[1, "Eternal Witness"]])
        self.assertEqual((self.stored()["revision"], self.stored("mine", "albert")["revision"]), (1, 1))
        self.assertEqual(self.get(DECK)["diff"]["added"], [[1, "Mind Stone"]])

    def test_non_ascii_names_travel_as_utf8(self):
        # Lim-Dûl's Vault: found by its plain spelling, flagged, and addressed percent-encoded
        self.open_deck()
        found = self.get("/api/cards?q=" + urllib.parse.quote("lim-dul") + "&deck=andy/go-wide")
        self.assertEqual([c["name"] for c in found["cards"]], ["Lim-Dûl's Vault"])
        self.assertEqual(found["cards"][0]["flag"]["kind"], "colors")
        sheet = self.get("/api/cards/" + urllib.parse.quote("Lim-Dûl's Vault", safe="") + "?deck=andy/go-wide")
        self.assertEqual(sheet["card"]["name"], "Lim-Dûl's Vault")

    def test_a_cut_cards_tile_is_listed_so_the_changes_tab_can_draw_it(self):
        # after cutting Ogre Slumlord the answer lists it under cut_cards, and the diff names it
        self.open_deck()
        reply = self.change({"op": "cut", "card": "Ogre Slumlord"})
        self.assertEqual(reply["diff"], {"added": [], "cut": [[1, "Ogre Slumlord"]]})
        self.assertEqual([(c["name"], c["count"], c["image"]) for c in reply["cut_cards"]],
                         [("Ogre Slumlord", 1, "https://img.test/ogre-slumlord.jpg")])


# ----------------------------------------------------------------------------- changing a deck
class ChangeTests(ServerCase):
    def setUp(self):
        super().setUp()
        self.before = self.open_deck()

    def test_adding_a_card_saves_it_and_answers_with_the_new_numbers(self):
        # add Mind Stone: revision 1, the card is new and costs its price, the score is the deck's value now
        reply = self.change({"op": "add", "card": "Mind Stone"})
        self.assertEqual(reply.status, 200)
        self.assertEqual(reply["result"], {"changed": True, "message": "Added Mind Stone."})
        self.assertEqual(reply["version"]["revision"], 1)
        stone = next(c for c in reply["cards"] if c["name"] == "Mind Stone")
        self.assertEqual((stone["new"], stone["owned"], stone["price"]), (True, False, 0.3))
        self.assertEqual(reply["diff"]["added"], [[1, "Mind Stone"]])
        self.assertEqual(reply["metrics"]["headline"]["price"], 0.3)
        self.assertEqual(reply["metrics"]["headline"]["score"], self.deck_value(reply))
        self.assertGreater(reply["metrics"]["headline"]["score"], self.before["metrics"]["headline"]["score"])
        self.assertEqual(self.stored()["revision"], 1)
        self.assertEqual(self.stored()["changes"][0]["add"], "Mind Stone")

    def test_a_swap_cuts_one_card_and_adds_another(self):
        # swap Ogre Slumlord for Eternal Witness: both sides in the difference and in the change log
        reply = self.change({"op": "swap", "cut": "Ogre Slumlord", "add": "Eternal Witness"})
        self.assertEqual(reply["result"]["message"], "Swapped Ogre Slumlord for Eternal Witness.")
        self.assertEqual(reply["diff"], {"added": [[1, "Eternal Witness"]], "cut": [[1, "Ogre Slumlord"]]})
        self.assertEqual(reply["card_count"], self.before["card_count"])
        self.assertEqual(self.stored()["changes"][0]["source"], "manual")

    def test_a_suggested_swap_is_marked_as_the_tools_suggestion(self):
        # the Suggestions tab applies a swap with source "suggested"; the change log keeps who picked it
        reply = self.change({"op": "swap", "cut": "Ogre Slumlord", "add": "Mind Stone", "source": "suggested"})
        self.assertEqual(reply.status, 200)
        self.assertEqual(self.stored()["changes"][0]["source"], "suggested")

    def test_a_price_point_is_one_group_and_one_undo_reverses_all_of_it(self):
        # apply "Up to $25" (two swaps) as a group: revision 1; undo it: both swaps are gone, still one revision more
        group = {"op": "group", "label": "Up to $25", "source": "suggested", "items": [
            {"op": "swap", "cut": "Ogre Slumlord", "add": "Mind Stone"},
            {"op": "swap", "cut": "Squirrel Mob", "add": "Eternal Witness"}]}
        applied = self.change(group)
        self.assertEqual((applied["version"]["revision"], len(applied["diff"]["added"])), (1, 2))
        undone = self.change({"op": "undo", "of": 1})
        self.assertEqual(undone["version"]["revision"], 2)
        self.assertEqual(undone["diff"], {"added": [], "cut": []})
        self.assertEqual(undone["metrics"]["headline"]["score"], self.before["metrics"]["headline"]["score"])

    def test_the_change_log_marks_an_undone_change(self):
        # after the undo, change 1 says undone: true and the undo entry itself is not marked
        self.change({"op": "add", "card": "Mind Stone"})
        reply = self.change({"op": "undo", "of": 1})
        first, undo = reply["version"]["changes"]
        self.assertEqual((first["n"], first["undone"]), (1, True))
        self.assertEqual((undo["op"], undo["of"], "undone" in undo), ("undo", 1, False))

    def test_a_change_that_does_nothing_says_so_and_keeps_the_revision(self):
        # Sol Ring is already in the deck: changed false, no write, same revision
        reply = self.change({"op": "add", "card": "Sol Ring"})
        self.assertEqual(reply.status, 200)
        self.assertEqual(reply["result"], {"changed": False, "message": "Sol Ring is already in the deck; nothing changed."})
        self.assertEqual(reply["version"]["revision"], 0)
        self.assertEqual(self.stored()["changes"], [])

    def test_a_stale_revision_is_409_carrying_the_current_one_and_changes_nothing(self):
        # the page last saw revision 0; another device made revision 1
        self.change({"op": "add", "card": "Mind Stone"})
        stale = self.change({"op": "add", "card": "Eternal Witness"}, revision=0)
        self.assertEqual((stale.status, stale.error()["code"]), (409, "conflict"))
        self.assertEqual(stale.error()["details"], {"revision": 1})
        self.assertEqual([c["add"] for c in self.stored()["changes"]], ["Mind Stone"])

    def test_two_clients_changing_one_deck_one_wins_one_gets_409_and_the_file_stays_valid(self):
        # a phone and a desktop both send revision 0 at the same moment: exactly one change lands
        gate = threading.Barrier(2)
        replies = {}

        def client(name, card):
            gate.wait()
            replies[name] = self.change({"op": "add", "card": card}, revision=0)
        threads = [threading.Thread(target=client, args=args) for args in (("phone", "Mind Stone"),
                                                                           ("desktop", "Eternal Witness"))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(r.status for r in replies.values()), [200, 409])
        winner = next(n for n, r in replies.items() if r.status == 200)
        loser = next(n for n, r in replies.items() if r.status == 409)
        self.assertEqual(replies[loser].error()["details"], {"revision": 1})
        stored = self.stored()
        self.assertEqual((stored["revision"], len(stored["changes"])), (1, 1))      # valid JSON that decks can replay
        self.assertEqual(stored["changes"][0]["add"], "Mind Stone" if winner == "phone" else "Eternal Witness")
        self.assertEqual(self.get(DECK)["version"]["revision"], 1)

    def test_a_card_the_index_does_not_know_is_422_with_close_names(self):
        # a typo: the message and details.suggestions offer the real name
        reply = self.change({"op": "add", "card": "Sol Rign"})
        self.assertEqual((reply.status, reply.error()["code"]), (422, "invalid"))
        self.assertIn("No card is called", reply.error()["message"])
        self.assertEqual(reply.error()["details"][0]["text"], "Sol Rign")
        self.assertIn("Sol Ring", reply.error()["details"][0]["suggestions"])
        self.assertEqual(self.stored()["revision"], 0)

    def test_a_card_outside_the_commanders_colors_is_422_with_a_reason(self):
        # Swords to Plowshares is white; the deck is black and green
        reply = self.change({"op": "add", "card": "Swords to Plowshares"})
        self.assertEqual(reply.status, 422)
        self.assertIn("outside the commander's colors", reply.error()["message"])

    def test_a_group_with_one_broken_item_is_422_naming_the_item_and_changes_nothing(self):
        # item 2 cuts a card the deck does not have: the whole group is refused
        reply = self.change({"op": "group", "label": "Up to $25", "items": [
            {"op": "swap", "cut": "Ogre Slumlord", "add": "Mind Stone"}, {"op": "cut", "card": "Mana Crypt"}]})
        self.assertEqual(reply.status, 422)
        self.assertIn("Item 2 of 2", reply.error()["message"])
        self.assertEqual(self.stored()["revision"], 0)

    def test_an_undo_that_a_later_change_depends_on_is_422(self):
        # change 2 cuts the Mind Stone that change 1 added, so change 1 cannot be undone first
        self.change({"op": "add", "card": "Mind Stone"})
        self.change({"op": "cut", "card": "Mind Stone"})
        reply = self.change({"op": "undo", "of": 1})
        self.assertEqual(reply.status, 422)
        self.assertIn("Undo change 2 first", reply.error()["message"])

    def test_a_change_without_a_revision_or_with_an_unknown_op_is_400(self):
        # the shape is wrong, not a deck rule
        missing = self.post(DECK + "/changes", {"op": "add", "card": "Mind Stone"})
        self.assertEqual((missing.status, missing.error()["code"]), (400, "bad_request"))
        self.assertIn('"revision"', missing.error()["message"])
        unknown = self.change({"op": "shuffle"})
        self.assertEqual(unknown.status, 400)

    def test_a_change_to_an_unknown_deck_is_404(self):
        # no such version: the ids are checked before anything else
        self.assertEqual(self.post("/api/decks/andy/nope/changes", {"revision": 0, "op": "cut", "card": "x"}).status, 404)

    def test_a_card_with_no_score_makes_the_server_prepare_again_with_it_included_offline(self):
        # Unlisted Charm is in no EDHREC list: adding it prepares again, offline, and the answer scores it "none"
        self.assertEqual(len(self.fakes.calls["prepare"]), 1)
        reply = self.change({"op": "add", "card": "Unlisted Charm"})
        self.assertEqual(reply.status, 200)
        self.assertEqual(len(self.fakes.calls["prepare"]), 2)
        again = self.fakes.calls["prepare"][1]
        self.assertIn("Unlisted Charm", again["deck_cards"])
        self.assertTrue(set(n for _, n in BASE_CARDS) <= set(again["deck_cards"]))   # the old cards keep their scores
        self.assertEqual((again["offline"], again["refresh"]), (True, False))
        charm = next(c for c in reply["cards"] if c["name"] == "Unlisted Charm")
        self.assertEqual(charm["score"], 0.0)
        self.change({"op": "add", "card": "Mind Stone"})                      # a scored card needs no new preparation
        self.assertEqual(len(self.fakes.calls["prepare"]), 2)

    def test_a_card_that_cannot_be_scored_is_kept_with_a_warning_and_no_error(self):
        # the offline re-preparation fails (cache gone): the change is saved and the answer says the card is unscored
        self.fakes.offline_error = net.FetchError("edhrec", "u", "offline and not cached")
        reply = self.change({"op": "add", "card": "Unlisted Charm"})
        self.assertEqual(reply.status, 200)
        self.assertTrue(any("Unlisted Charm could not be scored" in w for w in reply["warnings"]))
        self.assertEqual(self.stored()["revision"], 1)

    def test_a_new_cards_price_is_looked_up_and_failed_lookups_are_warnings(self):
        # the cheapest printing of Craterhoof is asked for; the fake's lookup fails once and leaves its warning
        self.fakes.calls["prices"].clear()
        carddb.WARNINGS.append("cheapest prices: scryfall: HTTP 503")
        reply = self.change({"op": "add", "card": "Craterhoof Behemoth"})
        self.assertEqual([c["names"] for c in self.fakes.calls["prices"]], [["Craterhoof Behemoth"]])
        self.assertIsNone(self.fakes.calls["prices"][0]["offline"])
        self.assertEqual(reply["metrics"]["headline"]["price"], 20.0)
        self.assertIn("cheapest prices: scryfall: HTTP 503", reply["warnings"])

    def test_the_bracket_banner_comes_from_the_headline_when_a_change_breaks_a_limit(self):
        # Mana Crypt is a Game Changer; at Bracket 1 that is over the limit, and bracket_ok turns false
        decks.update(self.root, "andy", "go-wide", revision=0, settings={"bracket": 1})
        self.assertTrue(self.open_deck()["metrics"]["headline"]["bracket_ok"])
        reply = self.change({"op": "add", "card": "Mana Crypt"})
        self.assertFalse(reply["metrics"]["headline"]["bracket_ok"])
        self.assertIn("Mana Crypt", self.item(reply, "bracket")["why"][0])

    def test_a_change_while_the_deck_is_still_being_prepared_does_nothing_and_answers_202(self):
        # open the deck on a slow preparation, change it at once: 202, and the file is untouched
        other = decks.new_version(self.root, player="andy", name="Second", base_id="squirreled-away", settings={})
        self.fakes.hold.clear()
        self.app.grace = 0
        reply = self.post("/api/decks/andy/second/changes", {"revision": 0, "op": "add", "card": "Mind Stone"})
        self.assertEqual(reply.status, 202)
        self.assertEqual(reply["revision"], 0)
        self.assertEqual(self.stored("second")["changes"], [])
        self.fakes.hold.set()
        self.assertEqual(other["revision"], 0)

    def test_the_stored_change_is_replayed_by_a_fresh_get(self):
        # what the answer showed is what the next GET shows
        changed = self.change({"op": "swap", "cut": "Ogre Slumlord", "add": "Eternal Witness"})
        again = self.get(DECK)
        self.assertEqual(again["cards"], changed["cards"])
        self.assertEqual(again["metrics"], changed["metrics"])


# ----------------------------------------------------------------------------- name and settings
class UpdateTests(ServerCase):
    def setUp(self):
        super().setUp()
        self.open_deck()

    def test_renaming_a_deck_bumps_the_revision_and_keeps_the_prepared_data(self):
        # a new name changes nothing the engine reads, so no new preparation
        reply = self.patch(DECK, {"revision": 0, "name": "Squirrels go wide"})
        self.assertEqual(reply.status, 200)
        self.assertEqual((reply["version"]["name"], reply["version"]["revision"]), ("Squirrels go wide", 1))
        self.assertEqual(len(self.fakes.calls["prepare"]), 1)

    def test_changing_the_budget_keeps_the_prepared_data_too(self):
        # the budget only matters to suggestions
        reply = self.patch(DECK, {"revision": 0, "settings": {"budget": 200}})
        self.assertEqual((reply.status, reply["version"]["settings"]["budget"], reply["version"]["revision"]),
                         (200, 200, 1))
        self.assertEqual(len(self.fakes.calls["prepare"]), 1)

    def test_changing_the_bracket_prepares_the_deck_again_and_recomputes_every_metric(self):
        # bracket 3 -> 4: a second preparation for Bracket 4, the answer's spec and bracket item follow
        reply = self.patch(DECK, {"revision": 0, "settings": {"bracket": 4}})
        self.assertEqual(reply.status, 200)
        self.assertEqual(reply["version"]["revision"], 1)
        self.assertEqual(len(self.fakes.calls["prepare"]), 2)
        self.assertEqual(self.fakes.calls["prepare"][1]["bracket"], 4)
        self.assertEqual((reply["spec"]["bracket"], self.item(reply, "bracket")["value"]), (4, 4))
        self.assertEqual(self.stored()["settings"]["bracket"], 4)
        self.assertEqual(self.stored()["settings"]["themes"], ["tokens"])        # the other settings are kept

    def test_a_settings_change_that_takes_time_answers_202_with_the_saved_revision(self):
        # the new data is slow to prepare: the settings are saved (revision 1) and the page polls
        self.fakes.hold.clear()
        self.app.grace = 0
        reply = self.patch(DECK, {"revision": 0, "settings": {"themes": ["squirrels"]}})
        self.assertEqual((reply.status, reply["status"], reply["revision"]), (202, "preparing", 1))
        self.assertEqual(self.stored()["settings"]["themes"], ["squirrels"])
        self.fakes.hold.set()
        ready = self.open_deck()
        self.assertEqual((ready.status, ready["spec"]["themes"]), (200, ["squirrels"]))

    def test_a_stale_revision_is_409_and_nothing_is_saved(self):
        # another device already changed the deck
        self.change({"op": "add", "card": "Mind Stone"})
        stale = self.patch(DECK, {"revision": 0, "name": "Too late"})
        self.assertEqual((stale.status, stale.error()["details"]), (409, {"revision": 1}))
        self.assertEqual(self.stored()["name"], "Go wide")

    def test_settings_that_would_break_the_deck_are_422_listing_each_one_and_are_not_saved(self):
        # bracket 9, a negative budget, a string for themes and a setting nobody knows
        reply = self.patch(DECK, {"revision": 0, "settings": {"bracket": 9, "budget": -5, "themes": "tokens",
                                                              "colour": "red"}})
        self.assertEqual((reply.status, reply.error()["code"]), (422, "invalid"))
        self.assertEqual(sorted(p["setting"] for p in reply.error()["details"]),
                         ["bracket", "budget", "colour", "themes"])
        self.assertEqual(self.stored()["settings"], SETTINGS)
        self.assertEqual(self.stored()["revision"], 0)

    def test_each_setting_has_its_own_check(self):
        # booleans are not numbers, floats are not brackets, null clears a setting
        bad = [{"bracket": 3.5}, {"bracket": True}, {"bracket": 0}, {"budget": "lots"}, {"budget": True},
               {"playstyle": 3}, {"keep_fun": "yes"}, {"owned_precons": ["Squirreled Away", ""]}, {"themes": [1]}]
        for settings in bad:
            with self.subTest(settings=settings):
                self.assertEqual(self.patch(DECK, {"revision": 0, "settings": settings}).status, 422)
        cleared = self.patch(DECK, {"revision": 0, "settings": {"budget": None, "keep_fun": False}})
        self.assertEqual(cleared.status, 200)
        self.assertEqual((self.stored()["settings"]["budget"], self.stored()["settings"]["keep_fun"]), (None, False))

    def test_a_patch_with_nothing_to_change_or_no_revision_is_400(self):
        # the shape is wrong
        self.assertEqual(self.patch(DECK, {"revision": 0}).status, 400)
        self.assertEqual(self.patch(DECK, {"name": "x"}).status, 400)
        self.assertEqual(self.patch(DECK, {"revision": 0, "settings": [1]}).status, 400)

    def test_a_patch_to_an_unknown_deck_is_404(self):
        # a rename of a version that does not exist
        self.assertEqual(self.patch("/api/decks/andy/nope", {"revision": 0, "name": "x"}).status, 404)

    def test_an_unopened_deck_can_be_renamed_and_is_then_prepared(self):
        # a second version nobody has opened: PATCH saves the name, then prepares it like an open
        decks.new_version(self.root, player="andy", name="Second", base_id="squirreled-away", settings={})
        reply = self.patch("/api/decks/andy/second", {"revision": 0, "name": "Renamed"})
        self.assertEqual((reply.status, reply["version"]["name"]), (200, "Renamed"))


# ----------------------------------------------------------------------------- suggestions
class SuggestTests(ServerCase):
    def setUp(self):
        super().setUp()
        self.open_deck()

    def test_suggestions_run_upgrade_on_the_current_list_with_the_versions_budget(self):
        # budget 50 comes from the settings; the answer is the upgrade result plus the revision it was made for
        self.change({"op": "add", "card": "Mind Stone"})
        reply = self.post(DECK + "/suggest")
        self.assertEqual(reply.status, 200)
        call = self.fakes.calls["upgrade"][0]
        self.assertEqual((call["budget"], call["price_points"]), (50, None))
        self.assertIn((1, "Mind Stone"), call["deck"]["cards"])                      # the list as it is now
        self.assertEqual(call["deck"]["commanders"], [CMDR])
        self.assertEqual(self.fakes.calls["combos"][-1]["identity"], "BG")        # combos asked with the colors
        self.assertEqual((reply["revision"], reply["budget"]), (1, 50))
        self.assertEqual(reply["swaps"][0]["add"], "Mind Stone")
        self.assertEqual(reply["price_points"][0]["budget"], 25.0)
        self.assertIn("fake upgrade warning", reply["warnings"])

    def test_the_answer_carries_a_card_object_for_every_card_it_names(self):
        # the page draws the swap's two cards and the blocked card without asking for them one by one
        reply = self.post(DECK + "/suggest")
        self.assertEqual(sorted(reply["cards"]), ["Craterhoof Behemoth", "Mind Stone", "Ogre Slumlord"])
        self.assertEqual(reply["cards"]["Mind Stone"]["image"], "https://img.test/mind-stone.jpg")
        self.assertEqual(reply["cards"]["Mind Stone"]["owned"], False)

    def test_an_explicit_budget_and_price_points_win_over_the_settings(self):
        # $100 in steps of 25 and 50
        reply = self.post(DECK + "/suggest", {"budget": 100, "price_points": [25, 50]})
        self.assertEqual(reply.status, 200)
        call = self.fakes.calls["upgrade"][0]
        self.assertEqual((call["budget"], call["price_points"]), (100, [25, 50]))

    def test_no_budget_at_all_asks_upgrade_without_one(self):
        # "budget": null clears the settings' budget for this request
        self.post(DECK + "/suggest", {"budget": None})
        self.assertIsNone(self.fakes.calls["upgrade"][0]["budget"])

    def test_a_bad_budget_or_price_points_are_422(self):
        # a negative budget, a text budget, price points with no budget, price points that are not amounts
        for body in ({"budget": -1}, {"budget": "lots"}, {"budget": None, "price_points": [25]},
                     {"price_points": []}, {"price_points": [25, "x"]}, {"price_points": [0]}):
            with self.subTest(body=body):
                self.assertEqual(self.post(DECK + "/suggest", body).status, 422)
        self.assertEqual(self.fakes.calls["upgrade"], [])

    def test_suggestions_for_an_unknown_deck_are_404_and_for_a_bad_id_400(self):
        # ids are checked before suggestions run
        self.assertEqual(self.post("/api/decks/andy/nope/suggest").status, 404)
        self.assertEqual(self.post("/api/decks/Andy/go-wide/suggest").status, 400)

    def test_suggestions_for_a_deck_that_is_not_ready_answer_202(self):
        # a second version, preparation held
        decks.new_version(self.root, player="andy", name="Second", base_id="squirreled-away", settings={})
        self.fakes.hold.clear()
        self.app.grace = 0
        self.assertEqual(self.post("/api/decks/andy/second/suggest").status, 202)
        self.fakes.hold.set()

    def test_suggestions_do_not_hold_the_decks_lock_while_they_run(self):
        # a change made while upgrade is running is not made to wait for it
        started, release = threading.Event(), threading.Event()
        real = self.fakes.upgrade

        def slow(*args, **kw):
            started.set()
            if not release.wait(10):
                raise AssertionError("never released")
            return real(*args, **kw)
        self.app.upgrade = slow
        results = []
        thread = threading.Thread(target=lambda: results.append(self.post(DECK + "/suggest")))
        thread.start()
        self.assertTrue(started.wait(5))
        changed = self.change({"op": "add", "card": "Mind Stone"})
        self.assertEqual(changed.status, 200)
        release.set()
        thread.join()
        self.assertEqual(results[0]["revision"], 0)                               # made for the list before the change
        self.assertEqual(self.stored()["revision"], 1)


# ----------------------------------------------------------------------------- card search
class SearchCase(ServerCase):
    def setUp(self):
        super().setUp()
        self.open_deck()

    def search(self, text="", deck="andy/go-wide"):
        return self.get(f"/api/cards?q={urllib.parse.quote(text)}&deck={deck}")

    def names_of(self, reply):
        return [c["name"] for c in reply["cards"]]


class SearchTests(SearchCase):
    def test_no_text_lists_the_best_scored_cards_not_in_the_deck(self):
        # Mana Crypt .95, Craterhoof .8, Assassin's Trophy .7 ...: none from the deck, none outside the colors
        reply = self.search()
        self.assertEqual(reply.status, 200)
        names = self.names_of(reply)
        self.assertEqual(names[:4], ["Mana Crypt", "Craterhoof Behemoth", "Assassin's Trophy", "Eternal Witness"])
        self.assertFalse({n for _, n in BASE_CARDS} & set(names))
        self.assertNotIn("Swords to Plowshares", names)
        self.assertEqual((reply["query"], reply["revision"]), ("", 0))

    def test_a_result_has_the_card_its_score_evidence_gain_and_flag(self):
        # Assassin's Trophy: a card object plus score, evidence, the deck value gained as an extra card, no flag
        trophy = next(c for c in self.search()["cards"] if c["name"] == "Assassin's Trophy")
        self.assertEqual(sorted(trophy), sorted(["name", "front", "image", "image_back", "scryfall_uri", "type", "cost",
                                                 "cmc", "ci", "price", "owned", "score", "evidence", "gain", "flag"]))
        self.assertEqual((trophy["score"], trophy["price"], trophy["owned"], trophy["flag"]), (0.7, 2.0, False, None))
        self.assertEqual(trophy["evidence"], "in 70% of 1,125 Bracket 3 Hazel decks")
        copies = [c["name"] for c in self.open_deck()["cards"] for _ in range(c["count"])]
        ctx = self.fakes.prepare([CMDR], 3, {}, self.db, deck_cards=copies)
        gain = build.deck_value(copies + ["Assassin's Trophy"], ctx, self.db)["total"] - \
            build.deck_value(copies, ctx, self.db)["total"]
        self.assertEqual(trophy["gain"], round(gain, 3))

    def test_a_card_that_would_finish_a_combo_the_bracket_forbids_is_flagged_with_the_reason(self):
        # Craterhoof completes a two-card infinite combo Spellbook rates for Bracket 4; at Bracket 3 it is kept out
        self.world.combos = {"included": [], "almost": [
            self.combo(["Peregrin Took", "Craterhoof Behemoth"], ["Infinite creatures"], missing=["Craterhoof Behemoth"],
                       tag="R")]}
        hoof = next(c for c in self.search()["cards"] if c["name"] == "Craterhoof Behemoth")
        self.assertEqual(hoof["flag"]["kind"], "bracket")
        self.assertIn("completes a two-card combo with Peregrin Took", hoof["flag"]["reason"])
        self.assertIsNone(hoof["gain"])                                           # no gain is offered for a kept-out card

    def test_a_game_changer_over_the_brackets_limit_is_flagged_too(self):
        # Bracket 1 allows no Game Changers: Mana Crypt is kept out by the rules, not by a combo
        decks.update(self.root, "andy", "go-wide", revision=0, settings={"bracket": 1})
        self.open_deck()
        crypt = next(c for c in self.search()["cards"] if c["name"] == "Mana Crypt")
        self.assertEqual(crypt["flag"]["kind"], "bracket")
        self.assertIn("Game Changer", crypt["flag"]["reason"])

    def test_a_name_search_finds_cards_in_the_colors_first_and_flags_the_rest(self):
        # "squirrel": the green ones (scored by score, then unscored by rank), then the blue one flagged colors
        reply = self.search("squirrel")
        self.assertEqual(self.names_of(reply), ["Squirrel Nest", "Squirrel Mob", "Squirrel Hunter", "Squirrel Prophet"])
        flags = {c["name"]: c["flag"] and c["flag"]["kind"] for c in reply["cards"]}
        self.assertEqual(flags, {"Squirrel Mob": "in_deck", "Squirrel Nest": None, "Squirrel Hunter": None,
                                 "Squirrel Prophet": "colors"})
        prophet = reply["cards"][-1]
        self.assertEqual(prophet["flag"]["reason"], "Squirrel Prophet is outside the commander's colors.")
        self.assertEqual((prophet["score"], prophet["evidence"], prophet["gain"]), (None, None, None))

    def test_the_exact_name_comes_first_and_every_word_must_match(self):
        # "mob squirrel" in any order finds only Squirrel Mob; a full name goes first
        self.assertEqual(self.names_of(self.search("mob squirrel")), ["Squirrel Mob"])
        self.assertEqual(self.names_of(self.search("Sol Ring"))[:1], ["Sol Ring"])
        self.assertEqual(self.names_of(self.search("sol ring"))[:1], ["Sol Ring"])           # case does not matter

    def test_banned_cards_are_not_shown_and_a_search_with_no_match_is_empty(self):
        # Griselbrand is banned in Commander; nothing is called zzz
        self.assertEqual(self.search("griselbrand")["cards"], [])
        self.assertEqual(self.search("zzz")["cards"], [])

    def test_a_card_already_in_the_deck_is_shown_flagged_and_a_basic_land_is_not(self):
        # Sol Ring is in the deck; a second Forest is allowed
        ring = self.search("sol ring")["cards"][0]
        self.assertEqual(ring["flag"]["kind"], "in_deck")
        self.assertIsNone(self.search("forest")["cards"][0]["flag"])

    def test_search_prices_come_from_the_cache_or_the_index_and_never_ask_scryfall(self):
        # a keystroke must not wait on a lookup: the price helper is called offline
        self.fakes.calls["prices"].clear()
        self.search("squirrel")
        self.assertEqual([c["offline"] for c in self.fakes.calls["prices"]], [True])

    def test_a_search_without_a_deck_is_400_and_for_a_deck_not_ready_202(self):
        # ?deck is required; a version that is still being prepared answers 202
        self.assertEqual(self.get("/api/cards?q=sol").status, 400)
        self.assertEqual(self.get("/api/cards?q=sol&deck=andy").status, 400)
        self.assertEqual(self.get("/api/cards?q=sol&deck=andy/nope").status, 404)
        decks.new_version(self.root, player="andy", name="Second", base_id="squirreled-away", settings={})
        self.fakes.hold.clear()
        self.app.grace = 0
        self.assertEqual(self.search(deck="andy/second").status, 202)
        self.fakes.hold.set()


class SearchLimitTests(SearchCase):
    def extra_cards(self, world):
        for i in range(40):
            world.add(f"Acorn Card {i:02d}", f"Creature {EM} Squirrel", 2, "{1}{G}", "G", score=0.01 + i / 100)

    def test_at_most_thirty_cards_come_back_best_first(self):
        # forty acorns match "acorn": the thirty with the highest scores, in order
        names = self.names_of(self.search("acorn"))
        self.assertEqual(len(names), 30)
        self.assertEqual(names[:3], ["Acorn Card 39", "Acorn Card 38", "Acorn Card 37"])
        self.assertEqual(len(self.search()["cards"]), 30)


# ----------------------------------------------------------------------------- the card sheet
class SheetTests(SearchCase):
    def sheet(self, name, deck="andy/go-wide"):
        return self.get(f"/api/cards/{urllib.parse.quote(name, safe='')}?deck={deck}")

    def test_the_sheet_of_a_card_in_the_deck(self):
        # Go for the Throat: the card with its text, its numbers for this deck, removal breakdown, roles and tags
        reply = self.sheet("Go for the Throat")
        self.assertEqual(reply.status, 200)
        self.assertEqual(sorted(reply.body), sorted(["schema", "card", "copies", "commander", "flag", "roles",
                                                     "attributes", "answers", "gc", "score", "salt", "combos", "removal",
                                                     "if_cut", "replacements", "revision", "warnings"]))
        card = reply["card"]
        self.assertEqual((card["name"], card["type"], card["cost"], card["price"], card["owned"]),
                         ("Go for the Throat", "Instant", "{1}{B}", 1.0, True))
        self.assertEqual((reply["copies"], reply["commander"], reply["flag"], reply["roles"]), (1, False, None, ["removal"]))
        self.assertEqual(reply["attributes"], ["removal-creature", "removal-destroy"])
        self.assertEqual(reply["score"]["value"], 0.6)
        self.assertEqual((reply["score"]["kind"], reply["score"]["evidence"]),
                         ("builder", "in 60% of 1,125 Bracket 3 Hazel decks"))
        self.assertEqual(sorted(reply["score"]["parts"]), ["base", "resid", "salt", "theme"])

    def test_a_sheet_names_the_kinds_of_threat_the_card_answers(self):
        # Go for the Throat is tagged removal-creature, so it answers creatures; Sol Ring and Maelstrom Pulse (tagged
        # removal-permanent, which is not one of the seven kinds) answer none
        self.assertEqual(self.sheet("Go for the Throat")["answers"], ["creatures"])
        self.assertEqual(self.sheet("Sol Ring")["answers"], [])
        self.assertEqual(self.sheet("Maelstrom Pulse")["answers"], [])

    def test_a_removal_cards_breakdown_shows_its_four_weights(self):
        # an instant (1.0) that destroys (0.9) creatures only (0.7) for MV 2 (1.0) = 0.63
        removal = self.sheet("Go for the Throat")["removal"]
        self.assertEqual(removal["role"], "removal")
        self.assertAlmostEqual(removal["value"], 0.63)
        self.assertEqual(removal["weights"], {"speed": 1.0, "reach": 0.7, "permanence": 0.9, "cost": 1.0, "repeatable": 1.0})
        self.assertEqual(removal["kinds"]["reach"], "creatures only")
        self.assertEqual(removal["line"], "Go for the Throat 0.63 = instant 1.0 × creatures only 0.7 × destroy 0.9 × MV 2 1.0")
        self.assertIsNone(self.sheet("Sol Ring")["removal"])

    def test_cutting_a_card_lists_only_the_metric_items_that_change(self):
        # cutting Go for the Throat moves removal and the creature answers; tutors and the combo counts do not move
        reply = self.sheet("Go for the Throat")
        moved = {(i["group"], i["id"]): i for i in reply["if_cut"]["items"]}
        self.assertIn(("interaction", "removal_power"), moved)
        self.assertIn(("interaction", "answers_creatures"), moved)
        self.assertAlmostEqual(moved[("interaction", "removal_power")]["before"] - moved[("interaction", "removal_power")]["after"], 0.63, places=2)
        self.assertNotIn("tutors", {i["id"] for i in reply["if_cut"]["items"]})
        self.assertNotIn("changes", {i["group"] for i in reply["if_cut"]["items"]})
        for item in reply["if_cut"]["items"]:
            self.assertNotEqual(item["before"], item["after"])
        self.assertEqual(sorted(reply["if_cut"]["items"][0]), sorted(["group", "id", "label", "unit", "before", "after",
                                                                       "status_before", "status"]))
        deck = self.open_deck()
        without = [c for c in deck["cards"] if c["name"] != "Go for the Throat"]
        copies = [c["name"] for c in without for _ in range(c["count"])]
        ctx = self.fakes.prepare([CMDR], 3, {}, self.db, deck_cards=copies)
        expected = build.deck_value(copies, ctx, self.db)["total"] - build.deck_value(
            copies + ["Go for the Throat"], ctx, self.db)["total"]
        self.assertAlmostEqual(reply["if_cut"]["score_change"], expected, places=2)

    def test_the_best_replacements_are_ranked_by_the_decks_value_after_the_swap(self):
        # Go for the Throat out, each candidate in: top five by gain, none from the deck, none outside the colors
        reply = self.sheet("Go for the Throat")
        names = [r["card"]["name"] for r in reply["replacements"]]
        gains = [r["gain"] for r in reply["replacements"]]
        self.assertEqual(len(names), 5)
        self.assertEqual(gains, sorted(gains, reverse=True))
        deck = self.open_deck()
        copies = [c["name"] for c in deck["cards"] for _ in range(c["count"])]
        ctx = self.fakes.prepare([CMDR], 3, {}, self.db, deck_cards=copies)
        now = build.deck_value(copies, ctx, self.db)["total"]
        at = copies.index("Go for the Throat")
        options = {}
        for candidate in self.world.listed:
            rec = self.db.get(candidate)
            if candidate in copies or not set(rec["ci"]) <= set("BG"):
                continue                                               # (Bracket 3 has room for Mana Crypt, a Game Changer)
            options[candidate] = build.deck_value(copies[:at] + [candidate] + copies[at + 1:], ctx, self.db)["total"] - now
        self.assertEqual(names, sorted(options, key=lambda n: (-options[n], n))[:5])
        self.assertEqual(reply["replacements"][0]["gain"], round(options[names[0]], 3))
        self.assertEqual(sorted(reply["replacements"][0]), ["card", "evidence", "gain"])
        self.assertIsNotNone(reply["replacements"][0]["card"]["price"])

    def test_a_replacement_the_bracket_forbids_is_left_out(self):
        # Craterhoof would finish a combo Bracket 3 does not allow, so it is not offered in anyone's place
        self.world.combos = {"included": [], "almost": [
            self.combo(["Peregrin Took", "Craterhoof Behemoth"], ["Infinite creatures"], missing=["Craterhoof Behemoth"],
                       tag="R")]}
        names = [r["card"]["name"] for r in self.sheet("Ogre Slumlord")["replacements"]]
        self.assertNotIn("Craterhoof Behemoth", names)

    def test_the_sheet_of_a_card_not_in_the_deck_has_no_cut_or_replacements_and_may_be_flagged(self):
        # Swords to Plowshares: white, so the flag says why it cannot be added; nothing to cut
        reply = self.sheet("Swords to Plowshares")
        self.assertEqual(reply.status, 200)
        self.assertEqual(reply["copies"], 0)
        self.assertEqual(reply["flag"], {"kind": "colors", "reason": "Swords to Plowshares is outside the commander's colors."})
        self.assertEqual((reply["if_cut"], reply["replacements"]), (None, []))

    def test_a_card_nothing_lists_is_scored_none_so_its_sheet_has_evidence(self):
        # Unlisted Charm: prepared again with it included, evidence "not on this commander's lists"
        reply = self.sheet("Unlisted Charm")
        self.assertEqual(reply["score"]["kind"], "none")
        self.assertIn("not on this commander's EDHREC lists", reply["score"]["evidence"])
        self.assertIn("Unlisted Charm", self.fakes.calls["prepare"][-1]["deck_cards"])
        self.assertEqual(self.fakes.calls["prepare"][-1]["offline"], True)

    def test_a_sheets_price_is_looked_up_for_that_one_card(self):
        # opening the sheet of Demonic Tutor asks for its cheapest printing (online unless the server is offline)
        self.fakes.calls["prices"].clear()
        reply = self.sheet("Demonic Tutor")
        self.assertEqual(reply["card"]["price"], 25.0)
        self.assertEqual(self.fakes.calls["prices"][0]["names"], ["Demonic Tutor"])
        self.assertIsNone(self.fakes.calls["prices"][0]["offline"])

    def test_the_combos_a_card_is_in_and_would_complete_are_listed(self):
        # Sol Ring is in a complete combo; Mind Stone would finish another
        self.world.combos = {"included": [self.combo(["Sol Ring", "Peregrin Took"], ["Infinite mana"])],
                             "almost": [self.combo(["Mind Stone", "Peregrin Took"], ["Infinite mana"],
                                                   missing=["Mind Stone"])]}
        ring = self.sheet("Sol Ring")["combos"]
        self.assertEqual([c["cards"] for c in ring["in_deck"]], [["Sol Ring", "Peregrin Took"]])
        self.assertEqual(ring["would_complete"], [])
        stone = self.sheet("Mind Stone")["combos"]
        self.assertEqual([c["missing"] for c in stone["would_complete"]], [["Mind Stone"]])
        self.assertEqual(stone["in_deck"], [])

    def test_the_commanders_sheet_has_no_flag_no_score_and_nothing_to_cut(self):
        # Hazel leads the deck: how often other decks play her is not a score, and she is not scored by the server
        before = len(self.fakes.calls["prepare"])
        reply = self.sheet(CMDR)
        self.assertEqual((reply["commander"], reply["flag"], reply["if_cut"], reply["copies"], reply["score"]),
                         (True, None, None, 0, None))
        self.assertEqual(reply["replacements"], [])
        self.assertEqual(len(self.fakes.calls["prepare"]), before)

    def test_a_game_changer_and_a_cards_salt_are_on_the_sheet(self):
        # Mana Crypt is a Game Changer; Craterhoof has EDHREC salt 2.0
        self.assertTrue(self.sheet("Mana Crypt")["gc"])
        self.assertEqual(self.sheet("Craterhoof Behemoth")["salt"], 2.0)
        self.assertIsNone(self.sheet("Sol Ring")["salt"])

    def test_an_unknown_card_is_404_with_close_names_and_a_missing_deck_is_400(self):
        # a typo in the address, and no ?deck
        missing = self.sheet("Sol Rign")
        self.assertEqual(missing.status, 404)
        self.assertIn("Sol Ring", missing.error()["details"]["suggestions"])
        self.assertEqual(self.get("/api/cards/Sol%20Ring").status, 400)

    def test_a_name_with_slashes_travels_percent_encoded(self):
        # "Fire // Ice" has two slashes: encoded as one segment it still finds the card
        self.world.add("Fire // Ice", "Instant // Instant", 4, "{1}{R} // {1}{U}", "RU", price=0.2)
        self.app.db.cards["Fire // Ice"] = carddb.card_record(self.world.objs[-1])
        self.assertEqual(self.sheet("Fire // Ice")["card"]["name"], "Fire // Ice")


# ----------------------------------------------------------------------------- bases, versions, lists
class ListTests(ServerCase):
    def test_the_players_are_the_folders_except_bases(self):
        # andy has a folder; so does albert after his first version
        decks.new_version(self.root, player="albert", name="Mine", base_id="squirreled-away", settings={})
        self.assertEqual(self.get("/api/players").body, {"schema": 1, "players": ["albert", "andy"]})

    def test_the_menu_lists_the_playstyles_and_common_themes(self):
        # the choices the new-version form offers
        menu = self.get("/api/menu")
        self.assertEqual(menu.status, 200)
        self.assertEqual(len(menu["playstyles"]), 12)
        self.assertEqual(sorted(menu["playstyles"][0]), ["description", "label", "min_bracket", "slug", "themes"])
        self.assertEqual(menu["themes"][0]["slug"], "tokens")

    def test_the_deck_list_gives_each_version_its_headline_from_a_ready_deck(self):
        # after the deck is open, the list shows its numbers (no preparation of its own)
        opened = self.open_deck()
        prepares = len(self.fakes.calls["prepare"])
        listing = self.get("/api/decks?player=andy")
        self.assertEqual(listing.status, 200)
        entry = listing["versions"][0]
        self.assertEqual(sorted(entry), sorted(["id", "name", "base", "updated", "revision", "settings", "base_name",
                                                "commanders", "commander_image", "swaps", "spent", "headline"]))
        self.assertEqual(entry["settings"], SETTINGS)                  # the pages show the bracket, themes and playstyle
        self.assertEqual((entry["id"], entry["base_name"], entry["commanders"], entry["swaps"], entry["spent"]),
                         ("go-wide", "Squirreled Away", [CMDR], 0, 0.0))
        self.assertEqual(entry["commander_image"], "https://img.test/hazel-of-the-rootbloom.jpg")
        self.assertEqual(entry["headline"], opened["metrics"]["headline"])
        self.assertEqual(len(self.fakes.calls["prepare"]), prepares)

    def test_a_deck_nobody_opened_gets_its_headline_from_a_preparation_tried_offline(self):
        # the engine's data is cached: prepare is called offline, the headline is the number the open deck will show
        listing = self.get("/api/decks?player=andy")
        entry = listing["versions"][0]
        self.assertEqual(self.fakes.calls["prepare"][0]["offline"], True)
        self.assertIsNotNone(entry["headline"])
        self.assertEqual(entry["headline"], self.open_deck()["metrics"]["headline"])

    def test_the_offline_headline_is_remembered_until_the_deck_changes(self):
        # a second list does not prepare again; a change (revision 1) makes it work it out afresh
        self.get("/api/decks?player=andy")
        self.get("/api/decks?player=andy")
        self.assertEqual(len(self.fakes.calls["prepare"]), 1)
        decks.apply(self.root, "andy", "go-wide", {"op": "add", "card": "Mind Stone"}, revision=0, db=self.db)
        entry = self.get("/api/decks?player=andy")["versions"][0]
        self.assertEqual((len(self.fakes.calls["prepare"]), entry["swaps"], entry["revision"]), (2, 1, 1))
        self.assertEqual(entry["spent"], 0.3)

    def test_a_deck_whose_data_is_not_cached_has_no_headline_rather_than_a_wrong_one(self):
        # offline preparation fails, or falls back to generic popularity scores, or has no tags: headline null
        for name, set_up in (("fails", lambda: setattr(self.fakes, "offline_error", net.FetchError("e", "u", "x"))),
                             ("generic", lambda: setattr(self.fakes, "popularity", True)),
                             ("no tags", lambda: setattr(self.fakes, "tags_available", False))):
            with self.subTest(name):
                self.app._listing.clear()
                self.fakes.offline_error, self.fakes.popularity, self.fakes.tags_available = None, False, True
                set_up()
                entry = self.get("/api/decks?player=andy")["versions"][0]
                self.assertEqual((entry["headline"], entry["spent"]), (None, None))
                self.assertEqual(entry["name"], "Go wide")

    def test_a_version_whose_base_is_missing_is_listed_with_an_error(self):
        # the rest of the list still works
        decks.new_version(self.root, player="andy", name="Orphan", base_id="squirreled-away", settings={})
        os.remove(os.path.join(self.root, "bases", "squirreled-away.json"))
        listing = self.get("/api/decks?player=andy")
        self.assertEqual(listing.status, 200)
        self.assertEqual(len(listing["versions"]), 2)
        self.assertTrue(all("error" in v and "squirreled-away" in v["error"] for v in listing["versions"]))

    def test_an_unreadable_deck_file_is_skipped_and_named_in_the_warnings(self):
        # a broken file in andy's folder does not hide the others
        with open(os.path.join(self.root, "andy", "broken.json"), "w") as f:
            f.write("{")
        listing = self.get("/api/decks?player=andy")
        self.assertEqual([v["id"] for v in listing["versions"]], ["go-wide"])
        self.assertTrue(any("broken.json" in w for w in listing["warnings"]))

    def test_the_list_needs_a_player_and_an_unknown_player_is_404(self):
        # no ?player, a player with no folder, a player id with capitals
        self.assertEqual(self.get("/api/decks").status, 400)
        self.assertEqual(self.get("/api/decks?player=zed").status, 404)
        self.assertEqual(self.get("/api/decks?player=Andy").status, 400)

    def test_versions_are_listed_newest_first(self):
        # a second version made later comes first
        decks.new_version(self.root, player="andy", name="Newer", base_id="squirreled-away", settings={},
                          now="2026-10-12T09:00:00Z")
        self.assertEqual([v["id"] for v in self.get("/api/decks?player=andy")["versions"]], ["newer", "go-wide"])


class BaseTests(ServerCase):
    def test_a_precon_becomes_a_base_deck(self):
        # copy Squirreled Away under another name; the file records who made it and where it came from
        reply = self.post("/api/bases", {"name": "Squirrels again", "precon": "squirreled away", "player": "albert"})
        self.assertEqual(reply.status, 201)
        base = reply["base"]
        self.assertEqual((base["id"], base["name"], base["created_by"]), ("squirrels-again", "Squirrels again", "albert"))
        self.assertEqual(base["source"], {"type": "precon", "name": "Squirreled Away", "mtgjson": "SquirreledAway_BLC"})
        self.assertEqual((base["commanders"], base["card_count"]), ([CMDR], 18))
        self.assertTrue(os.path.exists(os.path.join(self.root, "bases", "squirrels-again.json")))

    def test_a_precon_base_without_a_name_takes_the_precons(self):
        # no name given: the precon's own name is used, and that id is taken here
        reply = self.post("/api/bases", {"precon": "Squirreled Away", "player": "andy"})
        self.assertEqual((reply.status, reply.error()["code"]), (409, "conflict"))

    def test_a_pasted_list_becomes_a_base_deck(self):
        # three cards and a commander marked in the text
        text = f"Commander\n1 {CMDR}\n\nDeck\n1 Sol Ring\n2 Forest\n1 Mind Stone\n"
        reply = self.post("/api/bases", {"name": "Pasted", "list": text, "player": "andy"})
        self.assertEqual(reply.status, 201)
        self.assertEqual((reply["base"]["id"], reply["base"]["source"], reply["base"]["card_count"]),
                         ("pasted", {"type": "paste"}, 5))

    def test_a_pasted_list_can_name_its_commander_in_the_request(self):
        # no marker in the list, so the request says who leads it
        reply = self.post("/api/bases", {"name": "Plain", "list": "1 Sol Ring\n1 Forest\n", "commander": CMDR,
                                         "player": "andy"})
        self.assertEqual((reply.status, reply["base"]["commanders"]), (201, [CMDR]))
        missing = self.post("/api/bases", {"name": "Headless", "list": "1 Sol Ring\n", "player": "andy"})
        self.assertEqual((missing.status, missing.error()["message"]), (422, "A base deck needs a commander."))

    def test_unreadable_lines_are_422_with_their_line_numbers_and_close_names(self):
        # line 3 has a typo
        text = f"Commander\n1 {CMDR}\n1 Sol Rign\n1 Forest\n"
        reply = self.post("/api/bases", {"name": "Typo", "list": text, "player": "andy"})
        self.assertEqual((reply.status, reply.error()["code"]), (422, "invalid"))
        problem = reply.error()["details"][0]
        self.assertEqual((problem["line"], problem["text"]), (3, "1 Sol Rign"))
        self.assertIn("Sol Ring", problem["suggestions"])
        self.assertFalse(os.path.exists(os.path.join(self.root, "bases", "typo.json")))

    def test_an_unknown_precon_is_404_with_close_names(self):
        # a typo in the precon's name
        reply = self.post("/api/bases", {"name": "X", "precon": "Squirrled Away", "player": "andy"})
        self.assertEqual((reply.status, reply.error()["code"]), (404, "not_found"))
        self.assertEqual(reply.error()["details"], {"suggestions": ["Squirreled Away"]})
        self.assertIn("Squirreled Away", reply.error()["message"])

    def test_a_base_id_that_is_taken_is_409(self):
        # "Squirreled Away" is already a base deck
        reply = self.post("/api/bases", {"name": "Squirreled Away", "list": f"Commander\n1 {CMDR}\n", "player": "andy"})
        self.assertEqual((reply.status, reply.error()["code"]), (409, "conflict"))
        self.assertEqual(reply.error()["details"], {"revision": None})

    def test_a_request_with_both_or_neither_source_or_no_player_is_400(self):
        # the shape is wrong
        for body in ({"name": "X", "player": "andy"}, {"name": "X", "player": "andy", "precon": "a", "list": "b"},
                     {"name": "X", "precon": "Squirreled Away"}, {"name": "X", "list": "1 Sol Ring", "player": "andy",
                                                                 "commander": 5}):
            with self.subTest(body=body):
                self.assertEqual(self.post("/api/bases", body).status, 400)

    def test_the_base_decks_are_listed_by_name_with_their_commander_and_card_count(self):
        # one base deck so far
        listing = self.get("/api/bases")
        self.assertEqual(listing.status, 200)
        self.assertEqual([(b["id"], b["card_count"], b["commander_image"]) for b in listing["bases"]],
                         [("squirreled-away", 18, "https://img.test/hazel-of-the-rootbloom.jpg")])

    def test_a_base_deck_says_its_colors_in_the_order_white_blue_black_red_green(self):
        # Hazel is black and green; a base deck led by two partners has both of their colors, and a card the index
        # does not know adds none (the base deck list shows these letters beside the commander's name)
        self.assertEqual(self.get("/api/bases")["bases"][0]["ci"], "BG")
        made = decks.new_base(self.root, name="Two", commanders=[CMDR, "Swords to Plowshares"], cards=[(1, "Sol Ring")],
                              source={"type": "paste"}, created_by="andy", db=self.db)
        entry = next(b for b in self.get("/api/bases")["bases"] if b["id"] == made["id"])
        self.assertEqual(entry["ci"], "WBG")
        self.assertEqual(entry["commanders"], [CMDR, "Swords to Plowshares"])

    def test_the_precon_search_matches_words_and_returns_at_most_twenty(self):
        # "squir" finds one; "test precon" matches thirty names, twenty are returned
        self.assertEqual(self.get("/api/precons?q=squir")["precons"], ["Squirreled Away"])
        self.assertEqual(self.get("/api/precons?q=AWAY%20squirreled")["precons"], ["Squirreled Away"])
        many = self.get("/api/precons?q=test%20precon")["precons"]
        self.assertEqual((len(many), many[0]), (20, "Test Precon 00"))
        self.assertEqual(len(self.get("/api/precons")["precons"]), 20)
        self.assertEqual(self.get("/api/precons?q=zzz")["precons"], [])


class VersionCreateTests(ServerCase):
    def test_a_version_is_made_from_a_base_with_its_settings(self):
        # albert starts "Budget squirrels" from Squirreled Away: 201, revision 0, no changes, the file is saved
        reply = self.post("/api/decks", {"player": "albert", "name": "Budget squirrels", "base": "squirreled-away",
                                         "settings": {"bracket": 2, "budget": 50}})
        self.assertEqual(reply.status, 201)
        version = reply["version"]
        self.assertEqual((version["id"], version["player"], version["revision"], version["changes"]),
                         ("budget-squirrels", "albert", 0, []))
        self.assertEqual(version["settings"], {"bracket": 2, "budget": 50})
        self.assertTrue(os.path.exists(os.path.join(self.root, "albert", "budget-squirrels.json")))
        self.assertEqual(self.open_deck("/api/decks/albert/budget-squirrels").status, 200)

    def test_settings_may_be_left_out(self):
        # a version made with no settings at all stores an empty object
        reply = self.post("/api/decks", {"player": "albert", "name": "Plain", "base": "squirreled-away"})
        self.assertEqual((reply.status, reply["version"]["settings"]), (201, {}))

    def test_a_name_already_taken_is_409(self):
        # andy already has "Go wide"
        reply = self.post("/api/decks", {"player": "andy", "name": "Go wide", "base": "squirreled-away"})
        self.assertEqual((reply.status, reply.error()["code"]), (409, "conflict"))

    def test_an_unknown_base_is_404(self):
        # a version of a base deck that was never saved
        reply = self.post("/api/decks", {"player": "andy", "name": "X", "base": "nope"})
        self.assertEqual(reply.status, 404)

    def test_settings_that_would_break_the_deck_are_422_before_anything_is_saved(self):
        # bracket 6
        reply = self.post("/api/decks", {"player": "andy", "name": "Bad", "base": "squirreled-away",
                                         "settings": {"bracket": 6}})
        self.assertEqual((reply.status, reply.error()["details"][0]["setting"]), (422, "bracket"))
        self.assertFalse(os.path.exists(os.path.join(self.root, "andy", "bad.json")))

    def test_a_request_without_a_player_a_base_or_a_name_is_400(self):
        # each missing field, and settings that are not an object
        for body in ({"name": "X", "base": "squirreled-away"}, {"player": "andy", "name": "X"},
                     {"player": "andy", "base": "squirreled-away"}, {"player": "andy", "name": "X",
                                                                    "base": "squirreled-away", "settings": 5}):
            with self.subTest(body=body):
                self.assertEqual(self.post("/api/decks", body).status, 400)

    def test_bases_cannot_be_a_player_and_ids_follow_the_decks_rule(self):
        # the folder of base decks, and a player name with capitals
        for player in ("bases", "Albert", "con"):
            with self.subTest(player=player):
                self.assertEqual(self.post("/api/decks", {"player": player, "name": "X",
                                                          "base": "squirreled-away"}).status, 400)


# ----------------------------------------------------------------------------- status
class StatusTests(ServerCase):
    def test_status_reports_the_sources_the_servers_settings_and_the_uncommitted_files(self):
        # the card index, the decks folder, the address and what git says is new
        self.open_deck()
        reply = self.get("/api/status")
        self.assertEqual(reply.status, 200)
        self.assertEqual(sorted(reply.body), ["schema", "settings", "sources", "uncommitted", "uncommitted_note"])
        settings = reply["settings"]
        self.assertEqual((settings["host"], settings["port"], settings["offline"], settings["decks"]),
                         ("127.0.0.1", self.port, False, os.path.abspath(self.root)))
        self.assertEqual(settings["test_switches"], {"delay": 0.0, "conflict": 0, "fail_hosts": []})
        self.assertIn("scryfall", reply["sources"])
        self.assertIn("edhrec", reply["sources"])                                # from the deck that is open
        self.assertEqual(reply["uncommitted"], ["commander/decks/andy/go-wide.json"])
        self.assertIsNone(reply["uncommitted_note"])
        self.assertFalse(settings["pages"])

    def test_status_says_why_the_uncommitted_files_are_not_listed(self):
        # git is not installed here
        self.fakes.git_files = ([], "git is not installed, so the deck files that are not committed yet cannot be listed.")
        reply = self.get("/api/status")
        self.assertEqual(reply["uncommitted"], [])
        self.assertIn("git is not installed", reply["uncommitted_note"])

    def test_status_shows_the_active_test_switches(self):
        # delay, a pending conflict, a failing host
        self.app.switches = serve.Switches(delay=0.001, conflicts=2)
        with mock.patch.dict(os.environ, {"MTG_FAIL_HOSTS": "json.edhrec.com, EDHTOP16.com"}):
            switches = self.get("/api/status")["settings"]["test_switches"]
        self.assertEqual(switches, {"delay": 0.001, "conflict": 2, "fail_hosts": ["edhtop16.com", "json.edhrec.com"]})


class GitStatusTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)

    def run_git(self, **result):
        done = SimpleNamespace(returncode=result.get("code", 0), stdout=result.get("out", ""), stderr=result.get("err", ""))
        return mock.patch.object(serve.subprocess, "run", return_value=done)

    def test_the_files_git_sees_as_new_or_changed_are_listed_untracked_ones_one_by_one(self):
        # a modified file, an untracked one and a rename (the new name counts)
        out = " M commander/decks/andy/go-wide.json\n?? commander/decks/albert/new.json\nR  a.json -> commander/decks/b.json\n"
        with self.run_git(out=out) as run:
            self.assertEqual(serve.git_uncommitted(self.root), (["commander/decks/andy/go-wide.json",
                                                                 "commander/decks/albert/new.json",
                                                                 "commander/decks/b.json"], None))
        args, kw = run.call_args
        self.assertEqual(args[0], ["git", "-C", self.root, "status", "--porcelain", "--untracked-files=all", "--", "."])
        self.assertEqual(kw["timeout"], 2)
        self.assertEqual(kw["env"]["GIT_OPTIONAL_LOCKS"], "0")                  # read only: git takes no lock

    def test_a_clean_folder_is_an_empty_list_and_no_note(self):
        # git has nothing to report
        with self.run_git(out=""):
            self.assertEqual(serve.git_uncommitted(self.root), ([], None))

    def test_a_folder_that_does_not_exist_yet_is_an_empty_list_and_git_is_not_run(self):
        # no deck was ever saved here
        with self.run_git() as run:
            self.assertEqual(serve.git_uncommitted(os.path.join(self.root, "nothing-yet")), ([], None))
        run.assert_not_called()

    def test_git_missing_slow_or_failing_is_an_empty_list_with_a_note(self):
        # not installed, over two seconds, not a repository
        with mock.patch.object(serve.subprocess, "run", side_effect=FileNotFoundError()):
            files, note = serve.git_uncommitted(self.root)
        self.assertEqual((files, "not installed" in note), ([], True))
        with mock.patch.object(serve.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 2)):
            files, note = serve.git_uncommitted(self.root)
        self.assertEqual((files, "longer than 2 seconds" in note), ([], True))
        with self.run_git(code=128, err="fatal: not a git repository (or any of the parent directories): .git\n"):
            files, note = serve.git_uncommitted(self.root)
        self.assertEqual((files, "not a git repository" in note), ([], True))
        with mock.patch.object(serve.subprocess, "run", side_effect=PermissionError(13, "Permission denied")):
            self.assertEqual(serve.git_uncommitted(self.root)[0], [])

    def test_a_real_git_repository_lists_a_new_deck_file(self):
        # the actual git, in a throwaway repository (skipped where git is absent)
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        subprocess.run(["git", "init", "-q", self.root], check=True, env=env, capture_output=True)
        folder = os.path.join(self.root, "commander", "decks", "andy")
        os.makedirs(folder)
        with open(os.path.join(folder, "a.json"), "w") as f:
            f.write("{}")
        files, note = serve.git_uncommitted(os.path.join(self.root, "commander", "decks"))
        self.assertEqual((files, note), (["commander/decks/andy/a.json"], None))


# ----------------------------------------------------------------------------- safety
class SafetyTests(ServerCase):
    def test_a_host_header_that_is_not_this_server_is_403(self):
        # DNS rebinding: a page on evil.example whose name now points at 127.0.0.1
        for host in ("evil.example", "evil.example:8341", f"127.0.0.1.evil.example:{self.port}", "localhost.evil.example"):
            with self.subTest(host=host):
                reply = self.get("/api/status", headers={"Host": host})
                self.assertEqual((reply.status, reply.error()["code"]), (403, "forbidden"))
                self.assertIn("does not answer to the address", reply.error()["message"])

    def test_the_servers_own_names_are_accepted(self):
        # 127.0.0.1, localhost (any case, any port), and Tailscale's own names
        for host in (f"127.0.0.1:{self.port}", f"localhost:{self.port}", "LOCALHOST", "mac.tail1234.ts.net",
                     "mac.tail1234.ts.net:8341"):
            with self.subTest(host=host):
                self.assertEqual(self.get("/api/status", headers={"Host": host}).status, 200)

    def test_a_request_with_no_host_header_is_403(self):
        # HTTP/1.0 without Host: browsers never do this, so nothing legitimate is lost
        conn = socket.create_connection(("127.0.0.1", self.port), timeout=10)
        try:
            conn.sendall(b"GET /api/status HTTP/1.0\r\n\r\n")
            data = b""
            while True:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
        finally:
            conn.close()
        self.assertTrue(data.startswith(b"HTTP/1.0 403"))

    def test_a_foreign_origin_is_403_even_for_a_read(self):
        # a page from another site calling the API through the player's browser
        for origin in ("http://evil.example", "https://evil.example:8341", "null", "http://127.0.0.1:1",
                       f"http://localhost:{self.port}"):
            with self.subTest(origin=origin):
                reply = self.get("/api/status", headers={"Origin": origin})
                self.assertEqual((reply.status, reply.error()["code"]), (403, "forbidden"))
                self.assertIn("may not use this server", reply.error()["message"])
        self.assertEqual(self.post(DECK + "/changes", {"revision": 0, "op": "add", "card": "Mind Stone"},
                                   headers={"Origin": "http://evil.example"}).status, 403)
        self.assertEqual(self.stored()["revision"], 0)

    def test_the_servers_own_origin_is_accepted(self):
        # the page it served calls back: Origin equals the Host the page was loaded from
        origin = f"http://127.0.0.1:{self.port}"
        self.assertEqual(self.get("/api/status", headers={"Origin": origin}).status, 200)
        self.assertEqual(self.get("/api/status", headers={"Host": "mac.tail1234.ts.net",
                                                          "Origin": "https://mac.tail1234.ts.net"}).status, 200)

    def test_a_write_without_the_json_content_type_is_415(self):
        # a browser form post (urllib's default), plain text, and no Content-Type at all
        body = json.dumps({"revision": 0, "op": "add", "card": "Mind Stone"}).encode()
        form = self.call("POST", DECK + "/changes", raw=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
        text = self.call("POST", DECK + "/changes", raw=body, headers={"Content-Type": "text/plain"})
        none = self.raw("POST", DECK + "/changes", headers={"Host": f"127.0.0.1:{self.port}"}, body=body)
        for reply in (form, text, none):
            self.assertEqual((reply.status, reply.error()["code"]), (415, "unsupported_media_type"))
        self.assertEqual(self.stored()["revision"], 0)

    def test_the_json_content_type_may_carry_a_charset(self):
        # Application/JSON; charset=utf-8 is still JSON
        reply = self.call("POST", DECK + "/suggest", raw=b"{}", headers={"Content-Type": "Application/JSON; charset=utf-8"})
        self.assertNotEqual(reply.status, 415)

    def test_a_body_over_one_megabyte_is_413_and_nothing_is_read(self):
        # the length is checked first; the oversized body is not parsed
        big = b'{"revision": 0, "op": "add", "card": "' + b"x" * (1 << 20) + b'"}'
        reply = self.call("POST", DECK + "/changes", raw=big)
        self.assertEqual((reply.status, reply.error()["code"]), (413, "too_large"))
        self.assertEqual(self.stored()["revision"], 0)

    def test_a_length_that_claims_more_than_the_limit_is_413_before_any_of_it_is_sent(self):
        # Content-Length 2,000,000 with a tiny body
        reply = self.raw("POST", DECK + "/changes", headers={"Host": f"127.0.0.1:{self.port}",
                                                             "Content-Type": "application/json",
                                                             "Content-Length": "2000000"}, body=b"{}")
        self.assertEqual(reply.status, 413)

    def test_a_body_of_exactly_one_megabyte_is_read(self):
        # padded with spaces, it is still the JSON {} and the request is answered normally
        body = b"{}" + b" " * ((1 << 20) - 2)
        self.assertEqual(len(body), 1 << 20)
        self.assertEqual(self.call("POST", DECK + "/suggest", raw=body).status, 200)

    def test_a_write_with_no_length_or_chunked_is_411(self):
        # no Content-Length, then a chunked body
        none = self.raw("POST", DECK + "/suggest", headers={"Host": f"127.0.0.1:{self.port}",
                                                           "Content-Type": "application/json"})
        chunked = self.raw("POST", DECK + "/suggest", headers={"Host": f"127.0.0.1:{self.port}",
                                                              "Content-Type": "application/json",
                                                              "Transfer-Encoding": "chunked"}, body=b"2\r\n{}\r\n0\r\n\r\n")
        self.assertEqual((none.status, chunked.status), (411, 411))

    def test_a_body_that_is_not_a_json_object_is_400(self):
        # broken JSON, a list, a number, NaN and bytes that are not UTF-8
        for raw in (b"{", b"[1]", b"5", b'{"revision": NaN}', b"\xff\xfe", b'"text"'):
            with self.subTest(raw=raw):
                reply = self.call("POST", DECK + "/changes", raw=raw)
                self.assertEqual((reply.status, reply.error()["code"]), (400, "bad_request"))

    def test_a_body_nested_deeper_than_python_can_read_is_400_not_a_crash(self):
        # a megabyte of opening brackets
        reply = self.call("POST", DECK + "/changes", raw=b"[" * 200000)
        self.assertEqual((reply.status, reply.error()["message"]), (400, "The request body is nested too deeply."))

    def test_an_empty_body_is_an_empty_object(self):
        # a POST with no body at all (suggest needs none)
        self.assertEqual(self.call("POST", DECK + "/suggest", raw=b"").status, 200)

    def test_ids_are_checked_before_they_reach_the_file_system(self):
        # capitals, a dot-dot, encoded slashes and a device name never become a path
        for path in ("/api/decks/Andy/x", "/api/decks/andy/..", "/api/decks/%2e%2e/x", "/api/decks/andy/a%2Fb",
                     "/api/decks/andy/nul", "/api/decks/andy/%2e%2e%2f%2e%2e%2fetc"):
            with self.subTest(path=path):
                self.assertEqual(self.get(path).status, 400, path)

    def test_a_method_that_is_not_allowed_is_405_naming_the_methods_that_are(self):
        # PUT and DELETE on a deck, POST on the status, OPTIONS anywhere: no permission is ever given
        put = self.call("PUT", DECK, {})
        self.assertEqual((put.status, put.headers["Allow"]), (405, "GET, PATCH"))
        self.assertEqual(self.call("DELETE", DECK).status, 405)
        self.assertEqual((self.post("/api/status", {}).status, self.post("/api/status", {}).headers["Allow"]), (405, "GET"))
        options = self.call("OPTIONS", "/api/decks", headers={"Origin": "http://evil.example"})
        self.assertEqual(options.status, 403)
        options = self.call("OPTIONS", "/api/decks")
        self.assertEqual(options.status, 405)
        self.assertIsNone(options.headers.get("Access-Control-Allow-Origin"))
        self.assertIsNone(options.headers.get("Access-Control-Allow-Methods"))

    def test_a_request_that_is_not_a_path_on_this_server_is_400(self):
        # a proxy-style absolute URL names another server's address
        reply = self.raw("GET", "http://evil.example/api/status", headers={"Host": f"127.0.0.1:{self.port}"})
        self.assertEqual(reply.status, 400)
        self.assertEqual(self.raw("GET", "*", headers={"Host": f"127.0.0.1:{self.port}"}).status, 400)

    def test_head_on_an_api_address_is_405_with_no_body(self):
        # HEAD is for page files only
        head = self.raw("HEAD", "/api/status", headers={"Host": f"127.0.0.1:{self.port}"})
        self.assertEqual((head.status, head.text), (405, ""))

    def test_a_failure_outside_any_route_is_logged_and_the_connection_closes(self):
        # the socket server's own error report goes to the app's log, not to stderr
        with mock.patch.object(serve.Handler, "handle", side_effect=RuntimeError("broken handler")):
            with self.assertRaises((urllib.error.URLError, http.client.HTTPException, ConnectionError)):
                self.get("/api/status")
        deadline = time.monotonic() + 5
        while not any("broken handler" in line for line in self.logged) and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(any("RuntimeError: broken handler" in line for line in self.logged))
        self.logged.clear()

    def test_an_address_nothing_serves_is_a_json_404_under_api(self):
        # /api/nothing and /api itself
        reply = self.get("/api/nothing")
        self.assertEqual((reply.status, reply.error()["code"]), (404, "not_found"))
        self.assertEqual(self.get("/api").status, 404)

    def test_every_answer_carries_the_headers_that_keep_it_out_of_frames_and_caches(self):
        # the status answer's headers
        reply = self.get("/api/status")
        self.assertEqual(reply.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(reply.headers["X-Frame-Options"], "DENY")
        self.assertEqual(reply.headers["Cache-Control"], "no-store")
        self.assertEqual(reply.headers["Content-Type"], "application/json; charset=utf-8")

    def test_the_wrong_host_is_refused_for_a_write_whose_body_is_unread_without_a_reset(self):
        # a 403 for a POST must reach the client even though the body was never read
        body = json.dumps({"revision": 0, "op": "add", "card": "Mind Stone", "pad": "x" * 200000}).encode()
        reply = self.call("POST", DECK + "/changes", raw=body, headers={"Host": "evil.example"})
        self.assertEqual(reply.status, 403)


class HostPolicyTests(unittest.TestCase):
    """Which Host headers each way of starting the server accepts (App.host_allowed, no socket needed)."""

    def app(self, host):
        return serve.App(carddb.CardDB({}), tempfile.gettempdir(), host=host, switches=serve.Switches())

    def test_listening_on_this_computer_accepts_its_own_names_only(self):
        # 127.0.0.1: itself, localhost and Tailscale's names; nothing else
        app = self.app("127.0.0.1")
        for host in ("127.0.0.1:8341", "localhost", "LocalHost:80", "foo.ts.net", "a.b.ts.net:8341"):
            self.assertTrue(app.host_allowed(host), host)
        for host in ("", "10.0.0.5:8341", "evil.example", "127.0.0.2", "[::1]:8341", "ts.net.evil.example"):
            self.assertFalse(app.host_allowed(host), host)

    def test_listening_on_a_tailscale_address_accepts_that_address_and_tailscale_names(self):
        # 100.101.102.103: no localhost
        app = self.app("100.101.102.103")
        self.assertTrue(app.host_allowed("100.101.102.103:8341"))
        self.assertTrue(app.host_allowed("mac.tail1234.ts.net"))
        for host in ("localhost", "127.0.0.1", "100.101.102.104", "evil.example"):
            self.assertFalse(app.host_allowed(host), host)

    def test_listening_on_every_interface_accepts_any_ip_address_but_no_other_name(self):
        # a rebinding attack needs a DNS name, never an address
        app = self.app("0.0.0.0")
        for host in ("192.168.1.20:8341", "10.0.0.5", "[fe80::1]:8341", "localhost", "127.0.0.1"):
            self.assertTrue(app.host_allowed(host), host)
        for host in ("evil.example", "192.168.1.20.evil.example", "mymac.local"):
            self.assertFalse(app.host_allowed(host), host)

    def test_a_named_address_accepts_that_name(self):
        # --host mymac.local
        app = self.app("mymac.local")
        self.assertTrue(app.host_allowed("mymac.local:8341"))
        self.assertFalse(app.host_allowed("evil.example"))

    def test_origins_must_equal_the_host_the_page_came_from(self):
        # same host and port passes whatever the scheme; everything else fails
        app = self.app("127.0.0.1")
        self.assertTrue(app.origin_allowed("http://127.0.0.1:8341", "127.0.0.1:8341"))
        self.assertTrue(app.origin_allowed("HTTPS://Mac.tail1234.ts.net", "mac.tail1234.ts.net"))
        for origin in ("null", "http://evil.example", "http://127.0.0.1:8342", "file://", "ftp://127.0.0.1:8341", ""):
            self.assertFalse(app.origin_allowed(origin, "127.0.0.1:8341"), origin)


# ----------------------------------------------------------------------------- page files
class PageTests(ServerCase):
    """A web folder with a few files, and a file beside it that no address may reach."""

    def setUp(self):
        top = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, top, True)
        self.web = os.path.join(top, "web")
        self.secret = os.path.join(top, "secret")
        os.makedirs(self.secret)
        for name, text in (("index.html", "<h1>decks</h1>"), ("app.js", "export const x = 1;"), ("styles.css", "body{}"),
                           (os.path.join("sub", "card.js"), "// nested"), ("data.bin", "bin")):
            path = os.path.join(self.web, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(text)
        for path in (os.path.join(self.secret, "secret.txt"), os.path.join(top, "outside.txt")):
            with open(path, "w") as f:
                f.write("TOP SECRET")
        super().setUp()

    def make_app_kwargs(self):
        return {"web": self.web}

    def test_the_root_serves_index_html_and_files_have_their_own_types(self):
        # modules need a JavaScript type even where the registry says otherwise
        index = self.get("/")
        self.assertEqual((index.status, index.text, index.headers["Content-Type"]), (200, "<h1>decks</h1>", "text/html; charset=utf-8"))
        self.assertEqual(self.get("/app.js").headers["Content-Type"], "text/javascript; charset=utf-8")
        self.assertEqual(self.get("/styles.css").headers["Content-Type"], "text/css; charset=utf-8")
        self.assertEqual(self.get("/sub/card.js").text, "// nested")
        self.assertEqual(self.get("/data.bin").headers["Content-Type"], "application/octet-stream")
        self.assertEqual(self.get("/app.js").headers["Cache-Control"], "no-cache")
        self.assertEqual(self.get("/").headers["X-Frame-Options"], "DENY")

    def test_a_page_file_can_be_asked_for_with_head_but_not_changed(self):
        # HEAD gives the headers, POST is 405
        head = self.raw("HEAD", "/app.js", headers={"Host": f"127.0.0.1:{self.port}"})
        self.assertEqual((head.status, head.text), (200, ""))
        refused = self.call("POST", "/app.js", {})
        self.assertEqual((refused.status, refused.headers["Allow"]), (405, "GET, HEAD"))

    def test_a_path_cannot_leave_the_web_folder(self):
        # dots, encoded dots, backslashes and drive letters; none of them reads the file next to the folder
        for path in ("/../outside.txt", "/%2e%2e/outside.txt", "/sub/../../outside.txt", "/..%2foutside.txt",
                     "/sub/%2e%2e/%2e%2e/outside.txt", "/..\\outside.txt", "/C:/Windows/win.ini", "//etc/passwd",
                     "/sub/..%5c..%5coutside.txt", "/%00", "/./app.js"):
            with self.subTest(path=path):
                reply = self.raw("GET", path, headers={"Host": f"127.0.0.1:{self.port}"})
                self.assertEqual(reply.status, 404, path)
                self.assertNotIn("TOP SECRET", reply.text)

    def test_a_symbolic_link_out_of_the_web_folder_is_not_followed(self):
        # a link inside web/ pointing at a file outside it
        try:
            os.symlink(os.path.join(self.secret, "secret.txt"), os.path.join(self.web, "link.txt"))
        except (OSError, NotImplementedError, AttributeError):
            self.skipTest("symbolic links are not available here")
        reply = self.get("/link.txt")
        self.assertEqual(reply.status, 404)
        self.assertNotIn("TOP SECRET", reply.text)

    def test_a_missing_file_is_404_and_a_folder_without_an_index_is_404(self):
        # nothing.js, sub/ and sub
        self.assertEqual(self.get("/nothing.js").status, 404)
        self.assertEqual(self.get("/sub/").status, 404)
        self.assertEqual(self.get("/sub").status, 404)

    def test_the_api_still_answers_beside_the_pages(self):
        # the status answer says the pages are there
        self.assertEqual(self.get("/api/status").status, 200)
        self.assertTrue(self.get("/api/status")["settings"]["pages"])

    def test_a_page_request_from_the_wrong_host_is_refused_as_text(self):
        # a rebinding attempt on a page, not on the API
        reply = self.get("/", headers={"Host": "evil.example"})
        self.assertEqual(reply.status, 403)
        self.assertIn("does not answer to the address", reply.text)
        self.assertEqual(reply.headers["Content-Type"], "text/plain; charset=utf-8")


class NoPagesTests(ServerCase):
    def test_without_a_web_folder_the_root_is_404_with_a_note_and_the_api_works(self):
        # before the pages exist: src/mtgcommander/web/ is absent
        root = self.get("/")
        self.assertEqual(root.status, 404)
        self.assertIn("deck pages are not installed yet", root.text)
        self.assertEqual(self.get("/app.js").status, 404)
        self.assertEqual(self.get("/api/status").status, 200)
        self.assertFalse(self.get("/api/status")["settings"]["pages"])

    def test_the_real_web_folder_is_where_the_pages_will_be(self):
        # src/mtgcommander/web/, next to serve.py
        self.assertEqual(serve.WEB_DIR, os.path.join(os.path.dirname(os.path.abspath(serve.__file__)), "web"))


# ----------------------------------------------------------------------------- the test switches
class SwitchTests(ServerCase):
    def test_the_delay_switch_waits_after_the_work_and_before_the_answer(self):
        # 0.3 seconds: a change that takes longer than the page's patience has still been saved
        self.open_deck()
        self.app.switches = serve.Switches(delay=0.3)
        started = time.monotonic()
        reply = self.change({"op": "add", "card": "Mind Stone"})
        self.assertGreaterEqual(time.monotonic() - started, 0.3)
        self.assertEqual(reply.status, 200)
        started = time.monotonic()
        self.get("/api/nothing")                                                   # errors are slow too
        self.assertGreaterEqual(time.monotonic() - started, 0.3)
        self.assertEqual(self.stored()["revision"], 1)                             # saved before the wait ended
        with mock.patch.object(serve.time, "sleep") as sleep:                      # and the wait is the switch's number
            self.app.switches = serve.Switches(delay=7)
            self.get("/api/status")
        sleep.assert_called_once_with(7)

    def test_with_the_switch_off_nothing_waits(self):
        # no sleep at all when MTG_SERVE_DELAY is not set
        with mock.patch.object(serve.time, "sleep") as sleep:
            self.assertEqual(self.get("/api/status").status, 200)
        sleep.assert_not_called()

    def test_the_conflict_switch_refuses_the_next_change_with_the_real_revision_and_then_lets_one_through(self):
        # MTG_SERVE_CONFLICT=1: the first change answers 409 and nothing is written; resending it works
        self.open_deck()
        self.app.switches = serve.Switches(conflicts=1)
        refused = self.change({"op": "add", "card": "Mind Stone"})
        self.assertEqual((refused.status, refused.error()["code"], refused.error()["details"]), (409, "conflict", {"revision": 0}))
        self.assertIn("MTG_SERVE_CONFLICT", refused.error()["message"])
        self.assertEqual(self.stored()["revision"], 0)
        self.assertEqual(self.get(DECK)["version"]["revision"], 0)               # reloading shows the same deck
        self.assertEqual(self.change({"op": "add", "card": "Mind Stone"}).status, 200)
        self.assertEqual(self.change({"op": "add", "card": "Eternal Witness"}).status, 200)

    def test_the_conflict_switch_can_refuse_several_changes(self):
        # MTG_SERVE_CONFLICT=2: two refusals, then a change goes through
        self.open_deck()
        self.app.switches = serve.Switches(conflicts=2)
        statuses = [self.change({"op": "add", "card": "Mind Stone"}).status for _ in range(3)]
        self.assertEqual(statuses, [409, 409, 200])

    def test_the_conflict_switch_is_not_spent_by_a_request_that_is_not_a_change(self):
        # a read, a search and a bad change do not use it up
        self.open_deck()
        self.app.switches = serve.Switches(conflicts=1)
        self.get(DECK)
        self.get(f"/api/cards?q=sol&deck=andy/go-wide")
        self.assertEqual(self.post(DECK + "/changes", {"op": "add", "card": "Mind Stone"}).status, 400)
        self.assertEqual(self.change({"op": "add", "card": "Mind Stone"}).status, 409)

    def test_the_switches_are_read_from_the_environment(self):
        # 1.5 seconds and 3 conflicts; unset means off
        env = {"MTG_SERVE_DELAY": "1.5", "MTG_SERVE_CONFLICT": "3"}
        switches = serve.Switches.from_environment(env)
        self.assertEqual((switches.delay, switches.describe()["conflict"]), (1.5, 3))
        off = serve.Switches.from_environment({})
        self.assertEqual((off.delay, off.describe()["conflict"]), (0.0, 0))
        with mock.patch.dict(os.environ, env):
            self.assertEqual(serve.App(self.db, self.root).switches.delay, 1.5)

    def test_a_switch_with_a_value_that_is_not_a_number_is_an_error_that_names_it(self):
        # MTG_SERVE_DELAY=soon
        for name in ("MTG_SERVE_DELAY", "MTG_SERVE_CONFLICT"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, f"{name} must be a number, not 'soon'"):
                    serve.Switches.from_environment({name: "soon"})


# ----------------------------------------------------------------------------- sessions and preparation
class PreparationTests(ServerCase):
    def test_one_deck_is_prepared_at_a_time_and_the_other_waits_with_a_message(self):
        # open two decks while the first preparation is held: the second reports that it is waiting
        decks.new_version(self.root, player="andy", name="Second", base_id="squirreled-away", settings={})
        self.app.grace = 0
        self.fakes.hold.clear()
        self.get(DECK)
        self.assertTrue(self.fakes.entered.wait(5))
        second = self.get("/api/decks/andy/second")
        self.assertEqual(second.status, 202)
        self.assertEqual(second["progress"], {"requests": 0, "message": "Waiting for another deck to finish loading"})
        self.assertEqual(len(self.fakes.calls["prepare"]), 1)
        self.fakes.hold.set()
        self.assertEqual(self.open_deck().status, 200)
        self.assertEqual(self.open_deck("/api/decks/andy/second").status, 200)
        self.assertEqual(len(self.fakes.calls["prepare"]), 2)

    def test_the_server_keeps_answering_other_requests_while_a_deck_is_being_prepared(self):
        # a first open that takes a long time must not stop the deck list, the status or another deck
        decks.new_version(self.root, player="andy", name="Second", base_id="squirreled-away", settings={})
        self.app.grace = 0
        self.fakes.hold.clear()
        self.get(DECK)
        self.assertTrue(self.fakes.entered.wait(5))
        started = time.monotonic()
        self.assertEqual(self.get("/api/status").status, 200)
        self.assertEqual(self.get("/api/players").status, 200)
        self.assertEqual(self.get("/api/bases").status, 200)
        self.assertLess(time.monotonic() - started, 2)
        self.fakes.hold.set()

    def test_two_requests_for_one_unprepared_deck_start_only_one_preparation(self):
        # polling, and a second tab: the same job serves them both
        self.app.grace = 0
        self.fakes.hold.clear()
        replies = [self.get(DECK) for _ in range(5)]
        self.assertEqual({r.status for r in replies}, {202})
        self.fakes.hold.set()
        self.assertEqual(self.open_deck().status, 200)
        self.assertEqual(len(self.fakes.calls["prepare"]), 1)

    def test_close_waits_for_the_background_preparations(self):
        # nothing is left running after close(): the job has finished
        self.app.grace = 0
        self.fakes.hold.clear()
        self.get(DECK)
        self.assertTrue(self.fakes.entered.wait(5))
        timer = threading.Timer(0.1, self.fakes.hold.set)
        timer.start()
        self.app.close()
        timer.join()
        self.assertEqual(self.app.session("andy", "go-wide").state, "ready")

    def test_the_card_index_is_not_asked_for_the_computers_name_when_the_server_starts(self):
        # HTTPServer would ask DNS (getfqdn), which can take many seconds with no network
        with mock.patch.object(socket, "getfqdn", side_effect=AssertionError("DNS was asked")):
            server = serve.make_server(self.app, "127.0.0.1", 0, daemon=False)
            server.server_close()

    def test_an_error_in_a_request_thread_is_logged_not_printed(self):
        # a failure outside any route goes to the app's log
        with mock.patch.object(serve.App, "dispatch", side_effect=RuntimeError("broken")):
            reply = self.get("/api/status")
        self.assertEqual((reply.status, reply.error()["message"]), (500, "broken"))
        self.assertTrue(any("RuntimeError: broken" in line for line in self.logged))
        self.logged.clear()


# ----------------------------------------------------------------------------- the stats command's workspace
class StatsResultTests(ServerCase):
    def test_a_saved_version_gives_a_stats_result_with_the_base_decks_values_beside_it(self):
        # `stats --version andy/go-wide` after a swap: the headline, every group, and what the report prints
        self.open_deck()
        self.change({"op": "swap", "cut": "Ogre Slumlord", "add": "Mind Stone"})
        result = self.app.stats_result("andy", "go-wide")
        self.assertEqual((result["command"], result["bracket"], result["budget"]), ("stats", 3, 50))
        self.assertEqual(result["deck"], {"name": "Go wide", "commanders": [CMDR], "ci": "BG", "count": 18})
        self.assertEqual(result["spent"], 0.3)
        self.assertEqual(result["headline"]["price"], 0.3)
        self.assertEqual(result["spec"]["playstyle"], "aristocrats")
        score = next(i for g in result["groups"] for i in g["items"] if i["id"] == "score")
        self.assertNotEqual(score["base"], score["value"])
        self.assertIn("fake context warning", result["warnings"])
        self.assertIn("edhrec", result["sources"])
        text = render.stats_report(result)
        self.assertIn("Go wide → Bracket 3, budget $50 (spent $0.30); themes: tokens; playstyle: aristocrats", text)
        self.assertIn("(was ", text)
        self.assertIn("is the value in the base deck.", text)

    def test_the_numbers_are_the_ones_the_page_shows(self):
        # the same code answers both, so the headline and every item value agree
        opened = self.open_deck()
        result = self.app.stats_result("andy", "go-wide")
        self.assertEqual(result["headline"], opened["metrics"]["headline"])
        self.assertEqual(result["groups"], opened["metrics"]["groups"])

    def test_an_unknown_version_raises_not_found(self):
        # andy has no version called nope
        with self.assertRaises(decks.NotFound):
            self.app.stats_result("andy", "nope")


class HelperTests(unittest.TestCase):
    """Small unit tests of the helpers that need no server."""

    def test_the_real_engine_is_what_the_app_uses_unless_a_test_says_otherwise(self):
        # the defaults are the real functions
        app = serve.App(carddb.CardDB({}), tempfile.gettempdir(), switches=serve.Switches())
        self.assertEqual((app.prepare, app.combos, app.prices, app.upgrade), (build.prepare, spellbook.combos_for,
                                                                              carddb.deck_prices, build.upgrade))
        self.assertEqual((app.attributes, app.precon, app.precon_names, app.uncommitted),
                         (serve.load_attributes, decklist.precon, decklist.precon_names, serve.git_uncommitted))
        self.assertEqual((app.host, app.port, app.web), ("127.0.0.1", 8341, serve.WEB_DIR))

    def test_tag_data_that_could_not_be_had_is_none_not_a_set_of_empty_sets(self):
        # the metrics need to know the difference between "no tags" and "unavailable"
        with mock.patch.object(roles, "attributes", return_value={"Sol Ring": frozenset()}), \
                mock.patch.object(roles, "attributes_loaded", return_value=False):
            self.assertIsNone(serve.load_attributes(["Sol Ring"], None))
        with mock.patch.object(roles, "attributes", return_value={"Sol Ring": frozenset()}) as attributes, \
                mock.patch.object(roles, "attributes_loaded", return_value=True):
            self.assertEqual(serve.load_attributes(["Sol Ring"], None, offline=True), {"Sol Ring": frozenset()})
        self.assertEqual(attributes.call_args[1], {"offline": True})

    def test_a_change_log_entry_that_is_not_an_object_passes_through_the_version_view(self):
        # a hand-edited file: the view must not fail on it
        doc = {"id": "x", "player": "andy", "name": "X", "base": "b", "settings": {}, "revision": 1,
               "changes": [{"n": 1, "op": "add", "add": "A"}, "junk", {"n": 2, "op": "undo", "of": 1}]}
        changes = serve.version_view(doc)["changes"]
        self.assertEqual([c if isinstance(c, str) else c.get("undone") for c in changes], [True, "junk", None])

    def test_host_names_lose_their_port_and_case(self):
        # Host headers as browsers write them, with IPv6 in brackets
        self.assertEqual(serve.host_name("LocalHost:8341"), "localhost")
        self.assertEqual(serve.host_name("[::1]:8341"), "::1")
        self.assertEqual(serve.host_name("example.com"), "example.com")
        self.assertEqual(serve.host_name("[broken"), "[broken")

    def test_encode_refuses_a_number_json_cannot_hold_and_turns_sets_into_lists(self):
        # NaN is a bug; a set of owned cards is a sorted list
        with self.assertRaises(ValueError):
            serve.encode({"x": float("nan")})
        self.assertEqual(json.loads(serve.encode({"owned": {"b", "a"}})), {"schema": 1, "owned": ["a", "b"]})

    def test_sources_keep_the_oldest_fetch_and_the_worst_cache_state(self):
        # edhrec seen fresh and stale; scryfall only once
        into = {"edhrec": {"fetched": "2026-10-11T09:00:00Z", "cache": "fresh", "age_days": 0.1}}
        serve.merge_sources(into, {"edhrec": {"fetched": "2026-10-01T09:00:00Z", "cache": "stale", "age_days": 10.0},
                                   "scryfall": {"fetched": "2026-10-10T09:00:00Z", "cache": "network", "age_days": 1.0}})
        self.assertEqual((into["edhrec"]["fetched"], into["edhrec"]["cache"]), ("2026-10-01T09:00:00Z", "stale"))
        self.assertEqual(into["scryfall"]["cache"], "network")
        self.assertIsNone(serve.dated("not a date", "fresh")["age_days"])

    def test_the_modules_warning_lists_are_emptied_into_one_list(self):
        # carddb, roles and decks leave their warnings in lists
        a, b = ["one"], ["two", "three"]
        self.assertEqual(serve.drain(a, b), ["one", "two", "three"])
        self.assertEqual((a, b), ([], []))

    def test_a_route_pattern_captures_its_segments(self):
        # /api/decks/andy/go-wide gives andy and go-wide; an empty segment fits nothing
        self.assertEqual(serve._match(("api", "decks", ":", ":"), ["api", "decks", "andy", "go-wide"]), ["andy", "go-wide"])
        self.assertIsNone(serve._match(("api", "decks", ":", ":"), ["api", "decks", "andy", ""]))
        self.assertIsNone(serve._match(("api", "decks"), ["api", "decks", "andy"]))


if __name__ == "__main__":
    unittest.main()
