"""The local web server for the deck pages: the application programming interface (API) that reads saved decks,
changes them, and answers with every metric after each change.

`mtg-commander serve` runs it. The pages (a later part) are plain files served from src/mtgcommander/web/; everything
they know comes from the answers below, so each formula exists once, in Python. Every answer is JSON with
`"schema": 1`, except the page files.

    GET   /api/status                         when each data source was read; the server's settings; the deck files git
                                              does not have yet (read only, 2 second limit; a note when git cannot say)
    GET   /api/players                        the players (the folders under the decks folder)
    GET   /api/menu                           the playstyles and common themes a version's settings choose from
    GET   /api/decks?player=NAME              that player's versions, newest first, each with its headline numbers
    POST  /api/decks                          {"player", "name", "base", "settings"?} makes a version; 201
    GET   /api/decks/PLAYER/ID                a version: its cards, change log, difference from its base deck and every
                                              metric (each beside the base deck's value); or 202 while it is prepared
    POST  /api/decks/PLAYER/ID/changes        {"revision", "op": add | cut | swap | group | undo, ...}; answers like the
                                              GET plus "result": {"changed", "message"}
    PATCH /api/decks/PLAYER/ID                {"revision", "name"?, "settings"?}; answers like the GET
    POST  /api/decks/PLAYER/ID/suggest        {"budget"?, "price_points"?}: what `upgrade` would change in the list now
    GET   /api/bases, POST /api/bases         list the base decks; make one from {"name"?, "precon", "player"} or
                                              {"name", "list", "commander"?, "player"}; 201
    GET   /api/precons?q=TEXT                 the precon names that match, at most 20
    GET   /api/cards?q=TEXT&deck=PLAYER/ID    cards to add: the best-scored ones not in the deck (no text), or the ones
                                              whose name matches, at most 30
    GET   /api/cards/NAME?deck=PLAYER/ID      one card's sheet: its facts, its numbers for this deck, the kinds of
                                              threat it answers, what cutting it would change and the best cards to put
                                              in its place

A deck's numbers need the engine's data (card scores, tags, combos, prices). The first time a deck is opened, and
whenever its bracket, themes, playstyle, keep-fun choice or owned precons change, that data is prepared on a background
thread (one at a time in the whole server). Until it is ready the deck answers 202
{"status": "preparing", "progress": {"requests", "message"}, "revision"}: `requests` is the number of web requests made
since this deck's preparation began, and the page asks again until it gets 200. (A deck that is ready within 0.3
seconds is simply sent.) Every route that needs a ready deck (a change, a search, a card sheet, suggestions) does
nothing and answers 202 the same way when it finds none, so open the deck first. PATCH is the exception: it saves
the new name or settings before anything else, so its 202 means "saved, the numbers are on their way". A preparation
that fails answers 500 once with the error text, and the next request tries again.

Errors are {"schema": 1, "error": {"code", "message", "details"}}. The status is the decks error's: 400 bad_request
(also a bad id, or a body that is not a JSON object), 404 not_found (details.suggestions: close names), 409 conflict
(details.revision: where the deck is now), 422 invalid (details: the problems, such as each unreadable pasted line with
its line number, or each setting that is wrong). The rest: 403 forbidden, 405, 411, 413 too_large, 415
unsupported_media_type, and 500: server_error carries the exception's own text, and data_unavailable means a data
source is down with nothing cached. A deck file that cannot be read at all is a 500 naming the file.

A card object (everywhere a card appears): name, front, image, image_back, scryfall_uri, type, cost, cmc, ci (color
identity letters), price (cheapest printing; null when nothing prices it), owned. In a deck's list it also has count,
section, new (added since the base deck), score, roles and gc (Game Changer). A deck answer has: version (its fields
and its change log, each change marked `undone`), base, spec (the settings as the engine reads them), commanders,
cards, card_count, diff, cut_cards (the base deck's cards that were cut), metrics, warnings and sources.

There is no login. The server only checks where a request comes from, so a web page from another site cannot use it
through the player's browser:
- a write (POST, PATCH) must send `Content-Type: application/json`, which makes a browser ask permission first, and
  this server never gives it;
- a request with an Origin header must come from the address the page was loaded from (the Host header);
- the Host header must name this server: the address it listens on; `localhost` and 127.0.0.1 when that address is on
  this computer; any IP address when it listens on every interface (a rebinding attack, where another site's domain
  name is pointed at this computer, needs a name); and names ending in .ts.net, Tailscale's own, which is what
  `tailscale serve` passes on;
- ids in an address are checked by the decks module, and a page file's path cannot leave src/mtgcommander/web/;
- a request body is at most 1 MB.
Anyone who can reach the address can still change every deck, so listen on this computer only, or on a Tailscale
address, unless the network is trusted. Run one server per repo: the deck files have no lock between processes.

Test switches (environment variables, all off by default) make the server slow, refuse or fail:
- MTG_SERVE_DELAY=SECONDS     wait this long after doing the work of each API request, then answer (a slow network: a
                              change that took more than the page's 10 seconds has still been saved)
- MTG_SERVE_CONFLICT=N        the next N change requests answer 409 and change nothing (1 for the next one)
- MTG_FAIL_HOSTS=HOST,...     net.request and net.download fail at once for these hosts, as if the site were down; with
                              --refresh the cache is not simply served, so the page shows its stale-data banner

Everything the server depends on is a parameter of `App` with the real thing as its default (`prepare`, `combos`,
`attributes`, `prices`, `upgrade`, `precon`, `precon_names`, `uncommitted`), so the tests run it on fakes and a small
card index with no network."""
import datetime, heapq, http.server, ipaddress, json, math, os, socket, socketserver, subprocess, threading, time
import traceback, urllib.parse
from . import brackets, build, carddb, config, decklist, decks, fantasy, metrics, net, roles, score
from .providers import scryfall_tags, spellbook

SCHEMA = 1
BODY_LIMIT = 1 << 20              # bytes: the largest request body (a pasted deck list is a few KB)
LINGER_SECONDS = 2.0              # how long to keep reading a body the server refused, so closing does not reset it
FIRST_OPEN_WAIT = 0.3             # seconds a request waits for a deck to be prepared before it answers 202
SEARCH_LIMIT = 30                 # cards in one search answer
PRECON_LIMIT = 20                 # precon names in one answer
REPLACEMENT_POOL = 60             # best-scored cards tried as a replacement for the card on a sheet
REPLACEMENTS_SHOWN = 5
GIT_TIMEOUT = 2                   # seconds git may take to list the deck files that are not committed
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TAILSCALE_SUFFIX = ".ts.net"
WILDCARD_HOSTS = ("0.0.0.0", "::", "")
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")
CACHE_ORDER = ("fresh", "network", "stale")          # worst last, as cli.py ranks them
# The settings that change what a deck's data is prepared from. The budget only matters to suggestions, so changing
# it keeps the prepared data. SETTING_KEYS are all the settings a version may hold.
PREPARE_SETTINGS = ("bracket", "themes", "playstyle", "keep_fun", "owned_precons")
SETTING_KEYS = PREPARE_SETTINGS + ("budget",)
CODES = {400: "bad_request", 403: "forbidden", 404: "not_found", 405: "method_not_allowed", 409: "conflict",
         411: "length_required", 413: "too_large", 415: "unsupported_media_type", 422: "invalid",
         500: "server_error"}
# Python's mimetypes reads the Windows registry, where .js is sometimes text/plain, and a browser refuses a module
# script served that way; the page files' types are written down here instead.
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                 ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
                 ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png",
                 ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
                 ".ico": "image/x-icon", ".woff2": "font/woff2", ".woff": "font/woff",
                 ".txt": "text/plain; charset=utf-8"}
NO_PAGES = "The deck pages are not installed yet (src/mtgcommander/web/ does not exist). The API is at /api/status."
STAGE_TEXT = {"waiting": "Waiting for another deck to finish loading", "owned": "Reading the precons you own",
              "tags": "Loading card tags", "combos": "Looking up combos and prices",
              "numbers": "Working out the numbers"}


# ----------------------------------------------------------------------------- errors and answers
class ApiError(Exception):
    """An answer that is an error: the HTTP status, a message a person can read, `details` (what the page can act on)
    and any extra headers."""

    def __init__(self, status, message, details=None, headers=None):
        super().__init__(message)
        self.status, self.message, self.details, self.headers = status, message, details, headers or {}
        self.code = CODES[status]


class Preparing(Exception):
    """Raised inside a route when the deck is not ready; it becomes the 202 answer carrying `payload`."""

    def __init__(self, payload):
        super().__init__("preparing")
        self.payload = payload


def error_answer(exc):
    """(status, payload, headers) for an exception raised while answering. The decks error classes keep their own
    status; a source that is down with nothing cached is `data_unavailable`; anything else is a 500 that carries
    its own text."""
    headers = {}
    if isinstance(exc, ApiError):
        status, code, message, details, headers = exc.status, exc.code, exc.message, exc.details, exc.headers
    elif isinstance(exc, decks.DeckError):
        status, code, message, details = exc.status, CODES[exc.status], exc.message, None
        if isinstance(exc, decks.Conflict):
            details = {"revision": exc.revision}
        elif isinstance(exc, decks.NotFound):
            details = {"suggestions": exc.suggestions}
        elif isinstance(exc, decks.Invalid):
            details = exc.details
    elif isinstance(exc, net.FetchError):
        status, code, message, details = 500, "data_unavailable", str(exc), {"source": exc.source}
    else:
        status, code, message = 500, "server_error", str(exc) or exc.__class__.__name__
        details = {"type": exc.__class__.__name__}
    return status, {"error": {"code": code, "message": message, "details": details}}, headers


def _plain(value):
    """json.dumps fallback: sets become sorted lists."""
    return sorted(value) if isinstance(value, (set, frozenset)) else str(value)


def encode(payload):
    """The bytes of an answer. A number JSON cannot hold (NaN) is a bug, so it fails loudly here instead of sending
    text a browser cannot parse."""
    return json.dumps(dict({"schema": SCHEMA}, **payload), ensure_ascii=False, allow_nan=False,
                      default=_plain).encode("utf-8")


def _refuse_constant(text):
    raise ValueError(f"{text} is not a number JSON can hold")


def parse_body(raw):
    """The request body as a dict. An empty body is {}; anything that is not a JSON object is a 400."""
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw.decode("utf-8"), parse_constant=_refuse_constant)
    except (UnicodeDecodeError, ValueError) as e:
        raise ApiError(400, f"The request body is not valid JSON ({e}).")
    except RecursionError:                              # a megabyte of "[" nests deeper than Python will go
        raise ApiError(400, "The request body is nested too deeply.")
    if not isinstance(data, dict):
        raise ApiError(400, "The request body must be a JSON object.")
    return data


# ----------------------------------------------------------------------------- settings
def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _setting_problem(key, value):
    """Why a setting's value is wrong, or None. null clears a setting."""
    if key not in SETTING_KEYS:
        return f'"{key}" is not a setting; the settings are {", ".join(SETTING_KEYS)}.'
    if value is None:
        return None
    if key == "bracket" and not (isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 5):
        return "The bracket must be a whole number from 1 to 5."
    if key == "budget" and not (_number(value) and value >= 0):
        return "The budget must be an amount of dollars, zero or more."
    if key in ("themes", "owned_precons") and not (isinstance(value, list) and all(
            isinstance(item, str) and item.strip() for item in value)):
        return f"The {key.replace('_', ' ')} must be a list of names."
    if key == "playstyle" and not isinstance(value, str):
        return "The playstyle must be a name from the playstyle menu."
    if key == "keep_fun" and not isinstance(value, bool):
        return '"keep_fun" must be true or false.'
    return None


def checked_settings(settings):
    """`settings` if every value is usable, else Invalid listing each problem. A wrong value saved in a deck would
    make the deck fail to open every time, so it is refused here, before anything is written."""
    if not isinstance(settings, dict):
        raise decks.DeckError('"settings" must be an object, for example {"bracket": 3, "budget": 200}.')
    problems = []
    for key, value in settings.items():
        text = _setting_problem(key, value)
        if text is not None:
            problems.append({"setting": key, "text": text})
    if problems:
        raise decks.Invalid(" ".join(p["text"] for p in problems), problems)
    return settings


def settings_key(doc):
    """What a deck's prepared data depends on (see PREPARE_SETTINGS), as text to compare."""
    settings = doc["settings"]
    return json.dumps([settings.get(name) for name in PREPARE_SETTINGS], sort_keys=True)


def _dollars(value, what):
    if value is not None and not (_number(value) and value >= 0):
        raise decks.Invalid(f"The {what} must be an amount of dollars, zero or more.")
    return value


# ----------------------------------------------------------------------------- small helpers
def host_name(header):
    """The name part of a Host header, lower case, without the port: 'Localhost:8341' -> 'localhost'."""
    header = header.strip().lower()
    if header.startswith("["):                                  # [::1]:8341
        return header[1:header.find("]")] if "]" in header else header
    return header.partition(":")[0]


def _is_address(name):
    try:
        ipaddress.ip_address(name)
    except ValueError:
        return False
    return True


def git_uncommitted(root):
    """(files, note): the deck files under `root` that git sees as new or changed, as git prints them (from the top
    folder of the repository), and why the list is empty when git cannot say. Read only: git is told not to take its
    index lock, and gets GIT_TIMEOUT seconds."""
    if not os.path.isdir(root):
        return [], None                                         # no deck was ever saved here
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    try:
        done = subprocess.run(["git", "-C", root, "status", "--porcelain", "--untracked-files=all", "--", "."],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                              timeout=GIT_TIMEOUT)
    except FileNotFoundError:
        return [], "git is not installed, so the deck files that are not committed yet cannot be listed."
    except subprocess.TimeoutExpired:
        return [], f"git took longer than {GIT_TIMEOUT} seconds, so the uncommitted deck files were not listed."
    except OSError as e:
        return [], f"git could not be run ({e.strerror or e}), so the uncommitted deck files were not listed."
    if done.returncode != 0:
        why = (done.stderr.strip().splitlines() or ["no reason given"])[0]
        return [], f"git could not list the uncommitted deck files ({why})."
    return [line[3:].split(" -> ")[-1] for line in done.stdout.splitlines() if len(line) > 3], None


def load_attributes(names, db, **kw):
    """roles.attributes, or None when the tag data could not be had (the metrics then say which numbers are missing,
    as `stats` does) instead of every card quietly having no tags."""
    found = roles.attributes(names, db, **kw)
    return found if roles.attributes_loaded() else None


def dated(fetched, cache):
    """A sources entry {"fetched", "cache", "age_days"} for data read at `fetched` (an ISO time)."""
    try:
        then = datetime.datetime.strptime(fetched, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        age = round((datetime.datetime.now(datetime.timezone.utc) - then).total_seconds() / config.DAY, 1)
    except (TypeError, ValueError):
        age = None
    return {"fetched": fetched, "cache": cache, "age_days": age}


def merge_sources(into, more):
    """Add the sources entries of `more` to `into`: a source keeps its oldest fetch and its worst cache state."""
    for name, info in more.items():
        old = into.get(name)
        if old is None:
            into[name] = dict(info)
            continue
        worst = max(old["cache"], info["cache"], key=lambda c: CACHE_ORDER.index(c) if c in CACHE_ORDER else 0)
        into[name] = dated(min(old["fetched"], info["fetched"]), worst)


def drain(*lists):
    """Take the non-fatal lines the data modules collect (carddb.WARNINGS, roles.WARNINGS, decks.WARNINGS) so they
    reach an answer instead of piling up."""
    out = []
    for lst in lists:
        taken = lst[:]
        del lst[:len(taken)]
        out += taken
    return out


def unique(lines):
    return list(dict.fromkeys(lines))


def version_view(doc):
    """A version as the pages see it: its fields and its change log, each change marked `undone` when a later undo
    cancels it."""
    gone = decks._undone(doc.get("changes") or [])
    changes = [dict(c, undone=c.get("n") in gone) if isinstance(c, dict) and c.get("op") != "undo" else c
               for c in doc.get("changes") or []]
    return {"id": doc["id"], "player": doc["player"], "name": doc["name"], "base": doc["base"],
            "settings": doc["settings"], "revision": doc["revision"], "created": doc.get("created"),
            "updated": doc.get("updated"), "notes": doc.get("notes", ""), "changes": changes}


def base_view(base):
    return {"id": base["id"], "name": base["name"], "source": base.get("source"), "commanders": base["commanders"],
            "created": base.get("created"), "created_by": base.get("created_by")}


def headline_of(measured):
    """(the headline, the net cost of the changes) of a metrics result."""
    cost = next((item["value"] for g in measured["groups"] if g["id"] == "changes" for item in g["items"]
                 if item["id"] == "changes_net_cost"), None)
    return measured["headline"], cost


def _differs(a, b):
    if _number(a) and _number(b):
        return abs(a - b) > 1e-9
    return a != b


class Switches:
    """The test switches (see the module docstring). `conflicts` is how many of the next changes answer 409."""

    def __init__(self, delay=0.0, conflicts=0):
        self.delay, self._conflicts, self._lock = delay, conflicts, threading.Lock()

    @classmethod
    def from_environment(cls, env=None):
        env = os.environ if env is None else env

        def number(name):
            text = env.get(name, "").strip()
            try:
                return float(text) if text else 0.0
            except ValueError:
                raise ValueError(f"{name} must be a number, not {text!r}")
        return cls(delay=number("MTG_SERVE_DELAY"), conflicts=int(number("MTG_SERVE_CONFLICT")))

    def take_conflict(self):
        """True once for each of the changes the switch says to refuse."""
        with self._lock:
            if self._conflicts > 0:
                self._conflicts -= 1
                return True
            return False

    def describe(self):
        return {"delay": self.delay, "conflict": self._conflicts, "fail_hosts": sorted(net.failing_hosts())}


# ----------------------------------------------------------------------------- one prepared deck
class Workspace:
    """The engine's data for one open deck: the context `build.prepare` gathered (evidence, card tags, scores, targets),
    the cards that context has scored, what the player owns, the attribute tags and prices looked up so far, and the
    metrics of the base deck (the "before" of every number).

    It is built once when a deck is first opened and again when its settings change. After that a change to the card
    list only extends it: a card the context has not scored is scored by preparing again, offline (about 0.13 s), so
    a tap never waits on a download. A workspace never writes a deck file, so the deck list builds one to look at
    and throws it away. Its methods run under the lock of the session that holds it."""

    def __init__(self, app, player, doc):
        self.app, self.player, self.key = app, player, settings_key(doc)
        self.base = decks.base(app.root, doc["base"])
        self.baseline = decks.current(self.base, {"changes": []}, app.db)     # the base deck as the index spells it now
        self.commanders = list(self.baseline["commanders"])
        self.spec, self.spec_warnings = fantasy.validate_spec(doc["settings"], fantasy.menu())
        self.ctx = None
        self.known, self.owned = set(), set()          # names given to prepare so far; names that cost the player $0
        self.attrs, self.prices, self._priced = {}, {}, set()      # attrs is None when the tag data is unavailable
        self.base_result = None
        self.notes = []                                # warnings from building, kept for every answer
        self.combo_info = None                         # (fetched, cache) of the last combo answer

    # --- building
    def build(self, doc, *, step=None, refresh=False, offline=None):
        """Prepare everything the numbers need. `step(stage)` is told where the work is, for the progress message."""
        step = step or (lambda stage: None)
        db = self.app.db
        current = decks.current(self.base, doc, db)
        self.known = {n for _, n in self.baseline["cards"]} | {n for _, n in current["cards"]}
        step("owned")
        self.owned = self._owned(doc, offline)
        step("scores")
        self.ctx = self._prepare(refresh=refresh, offline=offline)
        step("tags")
        self.attrs = self.app.attributes(sorted(self.known), db, refresh=refresh, offline=offline)
        step("combos")
        self.learn_prices(sorted(self.known) + self.commanders, offline=offline)
        base_combos = self._combos(self.baseline, [], offline=offline)
        step("numbers")
        self.base_result = metrics.compute(self.ctx, db, self.baseline["cards"], commanders=self.commanders,
                                           attrs=self.attrs, combos=base_combos, owned=self.owned, prices=self.prices)
        return self

    def _prepare(self, *, refresh=False, offline=None):
        return self.app.prepare(self.commanders, self.spec["bracket"], self.spec, self.app.db,
                                deck_cards=sorted(self.known), owned=sorted(self.owned), sources=self.app.sources,
                                refresh=refresh, offline=offline)

    def _owned(self, doc, offline):
        """The base deck's cards and commanders, and the cards of each precon in the settings' owned_precons."""
        owned = {n for _, n in self.baseline["cards"]} | set(self.commanders)
        for name in doc["settings"].get("owned_precons") or []:
            try:
                deck = self.app.precon(name, offline=offline)
            except (decklist.UnknownPrecon, net.FetchError) as e:
                why = e.reason if isinstance(e, net.FetchError) else str(e)
                self.notes.append(f'The precon "{name}" you own could not be read ({why}), so its cards count as '
                                  "cards you do not own.")
                continue
            owned |= {card for _, card in deck["cards"]} | set(deck["commanders"])
        return {rec["name"] for rec in (self.app.db.get(n) for n in owned) if rec is not None}

    def ensure_scored(self, current):
        """Score the cards of `current` that the context has not seen (a card just added, or one an old log brings
        back) by preparing again with them included, offline. If that fails the cards stay unscored."""
        missing = self.unscored([n for _, n in current["cards"]])
        if not missing:
            return
        self.known.update(missing)
        try:
            self.ctx = self._prepare(refresh=False, offline=True)
        except net.FetchError as e:
            self.notes.append(f"{', '.join(missing)} could not be scored ({e.reason}), so its numbers are missing.")

    def unscored(self, names):
        """The names of the nonbasic cards among `names` that the context holds no score for."""
        recs = (self.app.db.get(n) for n in names)
        return [rec["name"] for rec in recs
                if rec is not None and "Basic" not in rec["types"] and rec["name"] not in self.ctx["scores"]]

    def know_card(self, name):
        """Score, tag and price one card that need not be in the deck, so its sheet can show its numbers. A commander
        is not scored: its place in the deck is not a matter of how often other decks play it."""
        if name not in self.commanders:
            self.ensure_scored({"cards": [[1, name]]})
        if self.attrs is not None and name not in self.attrs:
            self.attrs.update(self.app.attributes([name], self.app.db))
        self.learn_prices([name])

    def learn_prices(self, names, offline=None):
        fresh = [n for n in dict.fromkeys(names) if n not in self._priced]
        if fresh:
            self.prices.update(self.app.prices(fresh, self.app.db, offline=offline))
            self._priced.update(fresh)

    def look(self, doc):
        """Bring the workspace up to date with a version's card list: score its new cards, tag and price them, and ask
        for the list's combos. Returns (the list as decks.current gives it, its combos or None, notes for the
        answer)."""
        current = decks.current(self.base, doc, self.app.db)
        self.ensure_scored(current)
        names = [n for _, n in current["cards"]] + current["commanders"]
        if self.attrs is not None:
            fresh = [n for n in names if n not in self.attrs]
            if fresh:
                self.attrs.update(self.app.attributes(fresh, self.app.db))
        self.learn_prices(names)
        notes = list(current["warnings"])
        return current, self._combos(current, notes), notes

    def _combos(self, current, notes, offline=None):
        try:
            found = self.app.combos(current["commanders"], self.copies(current), identity=self.ctx["ci"],
                                    offline=offline)
        except net.FetchError as e:
            notes.append(f"Combos were not checked: {e.source} is unavailable ({e.reason}).")
            return None
        if found.get("note"):
            notes.append(found["note"])
        if found.get("fetched"):
            self.combo_info = (found["fetched"], found.get("cache", "fresh"))
        return found

    @staticmethod
    def copies(current):
        """One name for each copy of each card (nine Forests are nine names), the commanders left out."""
        return [name for n, name in current["cards"] for _ in range(n)]

    def measure(self, current, doc, combos):
        return metrics.compute(self.ctx, self.app.db, current["cards"], commanders=current["commanders"],
                               attrs=self.attrs, combos=combos, owned=self.owned, prices=self.prices,
                               base=self.base_result, changes=doc.get("changes") or [], player=self.player)

    def source_dates(self):
        out = {name: dict(info) for name, info in (self.ctx.get("sources") or {}).items()}
        if self.combo_info:
            out["spellbook"] = dated(*self.combo_info)
        return out

    # --- cards as the pages draw them
    def price_of(self, rec):
        if "Basic" in rec["types"]:
            return 0.0
        found = self.prices.get(rec["name"])
        return rec["price"] if found is None else found

    def is_owned(self, rec):
        return "Basic" in rec["types"] or rec["name"] in self.owned

    def tile(self, name):
        """The card object: what a page needs to draw the card wherever it appears."""
        rec = self.app.db.get(name)
        if rec is None:                                         # a name the card index no longer knows
            return {"name": name, "front": name, "image": "", "image_back": "", "scryfall_uri": "", "type": "",
                    "cost": "", "cmc": 0, "ci": "", "price": None, "owned": False}
        return {"name": rec["name"], "front": rec["front"], "image": rec["image"], "image_back": rec["image_back"],
                "scryfall_uri": rec["scryfall_uri"], "type": rec["type_line"], "cost": rec["mana_cost"],
                "cmc": rec["cmc"], "ci": rec["ci"], "price": self.price_of(rec), "owned": self.is_owned(rec)}

    def score_of(self, name):
        return self.ctx["scores"].get(self.app.db.resolve(name) or name)

    def roles_of(self, name):
        return sorted(self.ctx["role_map"].get(self.app.db.resolve(name) or name) or ())

    def deck_card(self, count, name, added):
        """A card of the deck: the card object plus its copies, type section, whether it was added since the base deck,
        its score, its roles and whether it is a Game Changer."""
        rec = self.app.db.get(name)
        found = self.score_of(name)
        return dict(self.tile(name), count=count, section=build.section_of(rec) if rec else "Other",
                    new=name in added, score=round(found["score"], 2) if found else None, roles=self.roles_of(name),
                    gc=bool(rec and rec["gc"]))

    # --- what a search and a card sheet need
    def rules_state(self, current, combos):
        """{"gc", "extra_turns", "mld"}: how many Game Changers, extra-turn cards and mass land denial cards the list
        holds (the commanders count), which is what brackets.can_add reads."""
        report = brackets.check(current["commanders"], self.copies(current), self.ctx["bracket"], self.app.db,
                                combos=combos)
        return {"gc": len(report["game_changers"]), "extra_turns": len(report["extra_turns"]),
                "mld": len(report["mass_land_denial"])}

    def keep_out(self, rec, state, blocked, in_deck):
        """Why `rec` cannot be added to this deck, as {"kind": illegal | colors | in_deck | bracket, "reason"}, or None
        when it can. `blocked` is brackets.blocked_adds (the cards that would finish a combo this bracket does not
        allow); `state` is rules_state."""
        name = rec["name"]
        if rec["legal"] != "legal":
            return {"kind": "illegal", "reason": f"{name} is " + ("banned" if rec["legal"] == "banned" else "not legal")
                    + " in Commander."}
        if not set(rec["ci"]) <= set(self.ctx["ci"]):
            return {"kind": "colors", "reason": f"{name} is outside the commander's colors."}
        if in_deck and not decks._allows_many_copies(rec):
            return {"kind": "in_deck", "reason": f"{name} is already in the deck."}
        if name in blocked:
            return {"kind": "bracket", "reason": blocked[name]}
        allowed, why = brackets.can_add(rec, state, self.ctx["bracket"])
        return None if allowed else {"kind": "bracket", "reason": why}

    def best_scored(self, taken):
        """Names a deck could add (scored, legal, inside the colors, not basic, not in `taken`), best score first."""
        pool = build._candidates(self.ctx, self.app.db, set(taken) | set(self.ctx["exclude"]))
        return sorted(pool, key=lambda n: (-self.ctx["scores"][n]["score"], n))

    def search(self, current, combos, text):
        """The cards a player could add, at most SEARCH_LIMIT. With no text: the best-scored cards not in the deck.
        With text: the legal cards whose name holds every word of it, the exact name first, then the cards inside the
        deck's colors, then those with a score by score and the rest by EDHREC rank. Each result is a card object plus
        `score`, `evidence`, `gain` (the deck's value change if the card were added as one more card) and `flag`:
        null when the card can be added, else why not (see keep_out)."""
        db, ctx = self.app.db, self.ctx
        in_deck = {name for _, name in current["cards"]} | set(current["commanders"])
        state, blocked = self.rules_state(current, combos), brackets.blocked_adds(ctx["bracket"], combos)
        query = carddb.normalize(text)
        if query:
            best = heapq.nsmallest(SEARCH_LIMIT, self.app.name_matches(query),
                                   key=lambda match: self._search_order(match[0], db.get(match[1]), query))
            recs = [db.get(name) for _, name in best]
        else:
            recs = [db.get(n) for n in self.best_scored(in_deck)[:SEARCH_LIMIT]]
        prices = self.app.prices([rec["name"] for rec in recs], db, offline=True)     # cached or listed, never asked
        copies = self.copies(current)
        value_now = build.deck_value(copies, ctx, db)["total"]
        out = []
        for rec in recs:
            name, found = rec["name"], ctx["scores"].get(rec["name"])
            flag = self.keep_out(rec, state, blocked, name in in_deck)
            gain = None
            if found is not None and flag is None:
                gain = round(build.deck_value(copies + [name], ctx, db)["total"] - value_now, 3)
            tile = self.tile(name)
            if prices.get(name) is not None:
                tile["price"] = prices[name]
            out.append(dict(tile, score=round(found["score"], 2) if found else None,
                            evidence=found["evidence"] if found else None, gain=gain, flag=flag))
        return out

    def _search_order(self, key, rec, query):
        """Sort key of a name match (`key` is its normalized name): the exact name, then inside the colors, then cards
        with a score before cards without, then score (best first) or EDHREC rank (lowest first)."""
        found = self.ctx["scores"].get(rec["name"])
        inside = set(rec["ci"]) <= set(self.ctx["ci"])
        rank = rec["rank"] if rec["rank"] is not None else 10 ** 9
        return key != query, not inside, found is None, -found["score"] if found else rank, rec["name"]

    def sheet(self, current, doc, combos, rec):
        """One card's sheet for this deck (the module docstring lists the route)."""
        ctx, name = self.ctx, rec["name"]
        held = self.copies(current).count(name)
        leads = name in current["commanders"]
        found = None if leads else self.score_of(name)
        flag = None
        if not held and not leads:
            flag = self.keep_out(rec, self.rules_state(current, combos), brackets.blocked_adds(ctx["bracket"], combos),
                                 False)
        out = {"card": dict(self.tile(name), text=rec["text"], subtypes=rec["subtypes"], keywords=rec["keywords"],
                            power=rec["power"], toughness=rec["toughness"], layout=rec["layout"], legal=rec["legal"],
                            rank=rec["rank"]),
               "copies": held, "commander": leads, "flag": flag, "roles": self.roles_of(name),
               "attributes": sorted((self.attrs or {}).get(name) or ()), "answers": self._answers_of(name),
               "gc": bool(rec["gc"]), "score": None,
               "salt": ((ctx.get("evidence") or {}).get("salt") or {}).get(name),
               "combos": self._combos_with(name, combos), "removal": self._removal_of(name, rec),
               "if_cut": None, "replacements": []}
        if found:
            out["score"] = {"value": round(found["score"], 3), "kind": found["kind"], "evidence": found["evidence"],
                            "parts": {k: round(v, 3) for k, v in found["parts"].items()},
                            "pulls": found.get("pulls") or {}}
        if held:
            out["if_cut"] = self._if_cut(current, doc, combos, name)
            out["replacements"] = self._replacements(current, combos, rec)
        return out

    def _answers_of(self, name):
        """The kinds of threat the card can answer ("creatures", "artifacts" ...), by the tags metrics.THREATS counts
        for the deck's "answers to ..." numbers, so a card's sheet and the deck's numbers always agree. Empty when the
        tags are unavailable."""
        held = (self.attrs or {}).get(name) or frozenset()
        return [label.split(" to ", 1)[1] for _, label, slugs in metrics.THREATS if held & set(slugs)]

    @staticmethod
    def _combos_with(name, combos):
        """The combos that use the card: those the deck has complete, and those the card would complete."""
        if combos is None:
            return None
        return {"in_deck": [c for c in combos["included"] if name in c["cards"]],
                "would_complete": [c for c in combos["almost"] if name in c["missing"]]}

    def _removal_of(self, name, rec):
        """The breakdown of a removal card's or board wipe's quality, as the metrics work it out (null for any other
        card, and when the tags are unavailable)."""
        if self.attrs is None:
            return None
        held = self.ctx["role_map"].get(name) or ()
        for role, rate in (("removal", metrics.rate_removal), ("wipe", metrics.rate_wipes)):
            if role in held:
                _, value, line = rate([name], self.ctx["role_map"], self.attrs, self.app.db)[0]
                attrs = self.attrs.get(name) or frozenset()
                return {"role": role, "value": round(value, 3), "line": line,
                        "weights": metrics.removal_quality(rec, attrs)[1], "kinds": metrics.removal_kind(rec, attrs)}
        return None

    def _if_cut(self, current, doc, combos, name):
        """What cutting one copy would change: the deck score, and each metric item whose number moves."""
        fewer = [[n - 1, card] if card == name else [n, card] for n, card in current["cards"]]
        without = dict(current, cards=[entry for entry in fewer if entry[0] > 0])
        before = self.measure(current, doc, combos)
        after = self.measure(without, doc, self._combos(without, []))
        was = {item["id"]: item for g in before["groups"] if g["id"] != "changes" for item in g["items"]}
        moved = []
        for group in after["groups"]:
            if group["id"] == "changes":                        # the change log does not change with a what-if
                continue
            for item in group["items"]:
                old = was.get(item["id"])
                if old is not None and _differs(old["value"], item["value"]):
                    moved.append({"group": group["id"], "id": item["id"], "label": item["label"],
                                  "unit": item["unit"], "before": old["value"], "after": item["value"],
                                  "status_before": old["status"], "status": item["status"]})
        change = None
        if before["headline"]["score"] is not None and after["headline"]["score"] is not None:
            change = round(after["headline"]["score"] - before["headline"]["score"], 3)
        return {"score_change": change, "items": moved}

    def _replacements(self, current, combos, rec):
        """The best REPLACEMENTS_SHOWN cards to put in this card's place, by the deck's value after the swap, chosen
        among the REPLACEMENT_POOL best-scored cards the bracket allows (about 2.5 ms each)."""
        db, ctx, name = self.app.db, self.ctx, rec["name"]
        copies = self.copies(current)
        value_now = build.deck_value(copies, ctx, db)["total"]
        state = self.rules_state(current, combos)
        for key, leaves in (("gc", rec["gc"]), ("extra_turns", brackets.is_extra_turn(rec)),
                            ("mld", brackets.is_mass_land_denial(rec))):
            state[key] -= int(bool(leaves))                     # the card being replaced leaves the count
        blocked = brackets.blocked_adds(ctx["bracket"], combos)
        taken = {n for _, n in current["cards"]} | set(current["commanders"])
        gone = copies.index(name)
        rows = []
        for candidate in self.best_scored(taken)[:REPLACEMENT_POOL]:
            if self.keep_out(db.get(candidate), state, blocked, False) is not None:
                continue
            swapped = copies[:gone] + [candidate] + copies[gone + 1:]
            rows.append((build.deck_value(swapped, ctx, db)["total"] - value_now, candidate))
        rows.sort(key=lambda row: (-row[0], row[1]))
        best = rows[:REPLACEMENTS_SHOWN]
        prices = self.app.prices([n for _, n in best], db)
        out = []
        for gain, candidate in best:
            tile = self.tile(candidate)
            if prices.get(candidate) is not None:
                tile["price"] = prices[candidate]
            out.append({"card": tile, "gain": round(gain, 3), "evidence": ctx["scores"][candidate]["evidence"]})
        return out


# ----------------------------------------------------------------------------- one open deck
class DeckSession:
    """An open version: its workspace, the lock that serializes work on it, and the background preparation.

    `state` is idle (nothing prepared), preparing, ready, or failed (the error waits to be reported once). A request
    runs `start`, `wait` and `check`: start preparing if the deck is not ready for its current settings, give the
    preparation a moment to finish, and either carry on or raise what to answer (202, or the error). The lock
    covers each change, search and sheet, so two taps on one deck happen one after the other."""

    def __init__(self, app, player, version_id):
        self.app, self.player, self.id = app, player, version_id
        self.lock = threading.RLock()          # one change, search or answer at a time for this deck
        self._guard = threading.Lock()         # the state fields below
        self.state, self.error = "idle", None
        self.done = threading.Event()          # set while the deck is not being prepared
        self.done.set()
        self.ws = None
        self.stage, self.who, self.requests_before = "waiting", "", 0

    # --- preparing
    def start(self, doc):
        """Begin preparing in the background unless the deck is ready for these settings, a preparation is under way,
        or the error of one has not been reported yet."""
        with self._guard:
            if self.state in ("preparing", "failed") or (self.state == "ready" and self.ws.key == settings_key(doc)):
                return
            self.state, self.stage = "preparing", "waiting"
            self.done.clear()
        thread = threading.Thread(target=self._prepare, args=(doc,), name=f"prepare {self.player}/{self.id}")
        thread.daemon = True
        thread.start()
        self.app.track(thread)

    def _prepare(self, doc):
        """The preparation, on its own thread. One runs at a time in the whole server: the data sites are asked
        politely, and the request count then belongs to this deck alone."""
        try:
            with self.app.prepare_lock:
                self.requests_before, self.stage = net.STATS["requests"], "owned"
                ws = Workspace(self.app, self.player, doc)
                self.who = score.short_name(ws.commanders)
                ws.build(doc, step=self._enter, refresh=self.app.refresh)
            with self.lock:
                self.ws = ws
            outcome = ("ready", None)
        except Exception as e:                  # no caller to tell: the error is kept and raised by the next request
            outcome = ("failed", e)
        with self._guard:
            self.state, self.error = outcome
        self.done.set()

    def _enter(self, stage):
        self.stage = stage

    def wait(self, seconds):
        self.done.wait(seconds)

    def check(self, doc):
        """Return when the deck is ready for the version's settings. Otherwise raise: the error of a failed
        preparation (once; the next request tries again) or Preparing, the 202 answer."""
        with self._guard:
            if self.state == "failed":
                error, self.state, self.error = self.error, "idle", None
                raise error
            ready = self.state == "ready" and self.ws.key == settings_key(doc)
        if not ready:
            raise Preparing({"status": "preparing", "progress": self.progress(), "revision": doc["revision"]})

    def recheck(self, doc):
        """start() and check() again once the session's lock is held: the settings may have changed meanwhile."""
        self.start(doc)
        self.check(doc)

    def progress(self):
        """{"requests", "message"}: the web requests made since this deck's preparation began, and what it is doing."""
        requests = 0 if self.stage == "waiting" else net.STATS["requests"] - self.requests_before
        if self.stage == "scores":
            message = (f"Fetching EDHREC data for {self.who} (first time only)" if requests
                       else f"Loading card scores for {self.who}")
        else:
            message = STAGE_TEXT.get(self.stage, "Getting the deck ready")
        return {"requests": requests, "message": message}

    # --- answers (the caller holds the lock)
    def answer(self, doc, result=None):
        """The deck as the pages read it (the module docstring lists the keys); `result` is a change's outcome."""
        ws, db = self.ws, self.app.db
        current, combos, notes = ws.look(doc)
        difference = decks.diff(ws.baseline["cards"], current["cards"])
        added = {name for _, name in difference["added"]}
        sources = ws.source_dates()
        merge_sources(sources, self.app.index_sources())
        out = {"version": version_view(doc), "base": base_view(ws.base), "spec": ws.spec,
               "commanders": [dict(ws.tile(name), gc=bool((db.get(name) or {}).get("gc")))
                              for name in current["commanders"]],
               "cards": [ws.deck_card(n, name, added) for n, name in current["cards"]],
               "card_count": sum(n for n, _ in current["cards"]) + len(current["commanders"]),
               "diff": difference, "cut_cards": [dict(ws.tile(name), count=n) for n, name in difference["cut"]],
               "metrics": ws.measure(current, doc, combos),
               "warnings": unique(ws.spec_warnings + ws.notes + notes + list(ws.ctx.get("warnings") or [])
                                  + drain(carddb.WARNINGS, roles.WARNINGS, decks.WARNINGS)),
               "sources": sources}
        if result is not None:
            out["result"] = result
        return out

    def snapshot(self, doc):
        """What a suggestion needs, taken under the lock so the (slow) search can run without it: (the context, the list
        as {"name", "commanders", "cards"}, the commanders' colors)."""
        current, _, _ = self.ws.look(doc)
        deck = {"name": doc["name"], "commanders": current["commanders"], "cards": [tuple(e) for e in current["cards"]]}
        return self.ws.ctx, deck, self.ws.ctx["ci"]

    def listing(self, doc):
        """(headline, net cost of the changes) for the deck list: from the open deck if it is ready, else from a
        preparation tried offline and remembered for this revision; (None, None) when that would need the network."""
        with self._guard:
            ready = self.state == "ready" and self.ws.key == settings_key(doc)
        if not ready:
            return self.app.offline_headline(self.player, doc)
        with self.lock:
            current, combos, _ = self.ws.look(doc)
            return headline_of(self.ws.measure(current, doc, combos))


# ----------------------------------------------------------------------------- the server's state and routes
class App:
    """Everything the server holds: the card index, the decks folder, one DeckSession for each open version, the test
    switches, and the collaborators (the real ones by default, fakes in the tests). `dispatch` answers one request that
    has already passed the safety checks. The collaborators are called like this:

        prepare(commanders, bracket, spec, db, *, deck_cards, owned, sources, refresh, offline)    build.prepare
        combos(commanders, cards, *, identity, offline)       spellbook.combos_for (cards: one name for each copy)
        attributes(names, db, *, refresh, offline)            {name: tag slugs}, None if unavailable  load_attributes
        prices(names, db, *, offline)                         {name: dollars or None}                 carddb.deck_prices
        upgrade(ctx, deck, db, *, budget, price_points, combos_fn)                                    build.upgrade
        precon(name, *, offline)                              a precon's list                         decklist.precon
        precon_names()                                        every precon's name               decklist.precon_names
        uncommitted(root)                                     (deck files git lacks, a note)          git_uncommitted

    `refresh` re-downloads a deck's data when the deck is first opened, and only then: a server that re-downloaded on
    every tap would hammer the sites. `wait` is how long a request waits for a preparation before answering 202. `web`
    is the folder of page files, or None. `log(line)` receives a line for each request and each problem."""

    def __init__(self, db, root, *, host=config.SERVE_HOST, port=config.SERVE_PORT, offline=False, refresh=False,
                 sources=None, web=WEB_DIR, prepare=build.prepare, combos=spellbook.combos_for,
                 attributes=load_attributes, prices=carddb.deck_prices, upgrade=build.upgrade,
                 precon=decklist.precon, precon_names=decklist.precon_names, uncommitted=git_uncommitted,
                 switches=None, wait=FIRST_OPEN_WAIT, log=None):
        self.db, self.root, self.offline, self.refresh = db, os.path.abspath(root), offline, refresh
        self.sources, self.web = sources, web
        self.prepare, self.combos, self.attributes, self.prices = prepare, combos, attributes, prices
        self.upgrade, self.precon, self.precon_names, self.uncommitted = upgrade, precon, precon_names, uncommitted
        self.switches = Switches.from_environment() if switches is None else switches
        self.grace, self._log = wait, log
        self.started = net.iso(time.time())
        self.prepare_lock = threading.Lock()
        self._sessions, self._threads, self._lock = {}, [], threading.Lock()
        self._names, self._listing = None, {}
        self.host, self.port, self.allowed, self.wildcard = host, port, set(), False
        self.bind(host, port)

    def bind(self, host, port):
        """Record the address the server listens on, which decides what a Host header may say."""
        self.host, self.port = host, port
        name = host_name(host) if host.startswith("[") else host.lower()
        self.wildcard = name in WILDCARD_HOSTS
        self.allowed = {name} - set(WILDCARD_HOSTS)
        if self.wildcard or name in LOOPBACK_HOSTS:
            self.allowed |= {"localhost", "127.0.0.1"}

    def log(self, line):
        if self._log is not None:
            self._log(line)

    def track(self, thread):
        with self._lock:
            self._threads = [t for t in self._threads if t.is_alive()] + [thread]

    def close(self, timeout=5.0):
        """Wait up to `timeout` seconds in all for the background preparations to finish (the tests need them stopped
        before they end; a command that is shutting down does not want to wait on a download)."""
        with self._lock:
            threads = list(self._threads)
        deadline = time.monotonic() + timeout
        for thread in threads:
            thread.join(max(0.0, deadline - time.monotonic()))

    def session(self, player, version_id):
        with self._lock:
            return self._sessions.setdefault((player, version_id), DeckSession(self, player, version_id))

    # --- who may ask
    def host_allowed(self, header):
        """Whether a Host header names this server (see the module docstring)."""
        if not header:
            return False
        name = host_name(header)
        return name in self.allowed or name.endswith(TAILSCALE_SUFFIX) or (self.wildcard and _is_address(name))

    @staticmethod
    def origin_allowed(origin, header):
        """Whether an Origin header is the address the page was loaded from: the same host and port as the request's
        Host header (the scheme aside, since `tailscale serve` puts https in front)."""
        parts = urllib.parse.urlsplit(origin)
        return parts.scheme in ("http", "https") and parts.netloc.lower() == (header or "").strip().lower()

    def check_origin(self, host_header, origin):
        """Raise a 403 unless the request came from a place this server answers to."""
        if not self.host_allowed(host_header):
            names = ", ".join(sorted(self.allowed)) or "no host name"
            raise ApiError(403, f'This server does not answer to the address "{host_header or "(none)"}". It answers '
                                f"to {names}, to names ending in {TAILSCALE_SUFFIX}, and, when it listens on every "
                                "interface, to IP addresses.")
        if origin is not None and not self.origin_allowed(origin, host_header):
            raise ApiError(403, f'A page from "{origin}" may not use this server; only a page it served itself may.')

    # --- routing
    def dispatch(self, method, parts, query, body):
        """(status, payload, headers) for one request. Every exception becomes an error answer here; the ones that
        are not the caller's mistake are also logged with their traceback."""
        try:
            status, payload = self._route(method, parts, query, body)
            headers = {}
        except Preparing as e:
            status, payload, headers = 202, e.payload, {}
        except Exception as e:
            if not isinstance(e, (ApiError, decks.DeckError, net.FetchError)):
                self.log(traceback.format_exc().rstrip())
            status, payload, headers = error_answer(e)
        return status, payload, headers

    def _route(self, method, parts, query, body):
        allowed = []
        for verb, pattern, name in ROUTES:
            args = _match(pattern, parts)
            if args is None:
                continue
            if verb == method:
                return getattr(self, name)(args, query, body)
            allowed.append(verb)
        if allowed:
            verbs = ", ".join(sorted(set(allowed)))
            raise ApiError(405, f"{method} is not allowed here; use {verbs}.", headers={"Allow": verbs})
        raise ApiError(404, "There is nothing at this address.", {"suggestions": []})

    # --- decks that are open
    def _open(self, player, version_id):
        """The session of a deck that is ready, or Preparing. Reading the version first checks the ids."""
        doc = decks.version(self.root, player, version_id)
        session = self.session(player, version_id)
        session.start(doc)
        session.wait(self.grace)
        session.check(doc)
        return session

    def _deck_of(self, query):
        """The ready session that ?deck=PLAYER/ID names."""
        player, slash, version_id = (query.get("deck") or "").partition("/")
        if not slash:
            raise decks.DeckError('Say which deck this is for: "deck=PLAYER/ID", for example '
                                  '"deck=andy/squirrels-go-wide".')
        return self._open(player, version_id)

    def _answer(self, player, version_id):
        """The 200 answer for a deck, or Preparing: what every route that answers like the GET shares."""
        session = self._open(player, version_id)
        with session.lock:
            doc = decks.version(self.root, player, version_id)
            session.recheck(doc)
            return 200, session.answer(doc)

    # --- routes: status and lists
    def route_status(self, args, query, body):
        files, note = self.uncommitted(self.root)
        sources = self.index_sources()
        with self._lock:
            sessions = list(self._sessions.values())
        for session in sessions:
            if session.state == "ready" and session.ws is not None:
                merge_sources(sources, session.ws.source_dates())
        return 200, {"sources": sources,
                     "settings": {"host": self.host, "port": self.port, "offline": self.offline,
                                  "decks": self.root, "pages": bool(self.web and os.path.isdir(self.web)),
                                  "started": self.started, "test_switches": self.switches.describe()},
                     "uncommitted": files, "uncommitted_note": note}

    def index_sources(self):
        """The sources every deck shares: the card index and, once loaded, the function tags."""
        out = {"scryfall": dated(self.db.fetched, self.db.cache)}
        if scryfall_tags.INFO:
            info = scryfall_tags.INFO
            out["scryfall_tags"] = dated(info.get("fetched", ""), info.get("cache", "fresh"))
        return out

    def route_players(self, args, query, body):
        return 200, {"players": decks.players(self.root)}

    def route_menu(self, args, query, body):
        return 200, fantasy.menu()

    def route_decks(self, args, query, body):
        player = query.get("player")
        if not player:
            raise decks.DeckError('Say whose decks to list: "?player=andy".')
        entries = [self._listing_entry(player, doc) for doc in decks.versions(self.root, player)]
        return 200, {"versions": entries, "warnings": unique(drain(decks.WARNINGS, carddb.WARNINGS))}

    def _listing_entry(self, player, doc):
        """One line of the deck list. A version whose base deck is gone or damaged is listed with an `error`."""
        entry = {"id": doc["id"], "name": doc["name"], "base": doc["base"], "updated": doc.get("updated"),
                 "revision": doc["revision"], "settings": dict(doc["settings"])}
        try:
            base = decks.base(self.root, doc["base"])
            current = decks.current(base, doc, self.db)
            baseline = decks.current(base, {"changes": []}, self.db)
        except (decks.DeckError, ValueError) as e:
            return dict(entry, error=getattr(e, "message", None) or str(e))
        lead = self.db.get(current["commanders"][0]) if current["commanders"] else None
        difference = decks.diff(baseline["cards"], current["cards"])
        headline, spent = self.session(player, doc["id"]).listing(doc)
        return dict(entry, base_name=base["name"], commanders=current["commanders"],
                    commander_image=lead["image"] if lead else "", swaps=sum(n for n, _ in difference["added"]),
                    spent=spent, headline=headline)

    def offline_headline(self, player, doc):
        """(headline, net cost) from a workspace built offline for a deck nobody has opened yet, remembered for the
        revision and settings it was built for. (None, None) when the cache lacks something it needs."""
        key, stamp = (player, doc["id"]), (doc["revision"], settings_key(doc))
        with self._lock:
            cached = self._listing.get(key)
        if cached and cached[0] == stamp:
            return cached[1]
        try:
            ws = Workspace(self, player, doc).build(doc, offline=True)
            if ws.ctx["evidence"].get("popularity") or ws.attrs is None:
                raise net.FetchError("cache", "", "the data this deck needs is not saved yet")
            current, combos, _ = ws.look(doc)
            found = headline_of(ws.measure(current, doc, combos))
        except (net.FetchError, decks.DeckError, ValueError):
            found = (None, None)
        with self._lock:
            self._listing[key] = (stamp, found)
        return found

    def route_bases(self, args, query, body):
        return 200, {"bases": [self._base_entry(base) for base in decks.bases(self.root)],
                     "warnings": unique(drain(decks.WARNINGS))}

    def _base_entry(self, base):
        leads = [self.db.get(name) for name in base["commanders"]]
        colors = "".join(c for c in "WUBRG" if any(rec is not None and c in rec["ci"] for rec in leads))
        return dict(base_view(base), commander_image=leads[0]["image"] if leads and leads[0] else "", ci=colors,
                    card_count=sum(n for n, _ in base["cards"]) + len(base["commanders"]))

    def route_precons(self, args, query, body):
        words = carddb.normalize(query.get("q", "")).split()
        names = [n for n in self.precon_names() if all(w in carddb.normalize(n) for w in words)]
        names.sort(key=lambda n: not carddb.normalize(n).startswith(" ".join(words)))   # stable: the A-Z order stays
        return 200, {"precons": names[:PRECON_LIMIT]}

    # --- routes: making base decks and versions
    def route_base_create(self, args, query, body):
        player = body.get("player")
        if not isinstance(player, str):
            raise decks.DeckError('Say who is making the base deck: "player".')
        if ("precon" in body) == ("list" in body):
            raise decks.DeckError('Give either "precon" (the name of a precon) or "list" (a pasted deck list), '
                                  "not both.")
        if "precon" in body:
            made = decks.precon_base_input(body["precon"])
        else:
            commander = body.get("commander")
            if commander is not None and not (isinstance(commander, str) or (
                    isinstance(commander, list) and all(isinstance(c, str) for c in commander))):
                raise decks.DeckError('"commander" must be a card name, or a list of two names for partners.')
            parsed = decks.parse_list(body["list"], self.db, commander=commander)
            if parsed["problems"]:
                raise decks.Invalid(f"{len(parsed['problems'])} line(s) of the list could not be read.",
                                    parsed["problems"])
            made = {"name": None, "commanders": parsed["commanders"], "cards": parsed["cards"],
                    "source": {"type": "paste"}}
        base = decks.new_base(self.root, name=body.get("name") or made["name"], commanders=made["commanders"],
                              cards=made["cards"], source=made["source"], created_by=player, db=self.db)
        return 201, {"base": self._base_entry(base)}

    def route_deck_create(self, args, query, body):
        settings = checked_settings(body["settings"] if "settings" in body else {})
        player, base = body.get("player"), body.get("base")
        if not isinstance(player, str) or not isinstance(base, str):
            raise decks.DeckError('A new version needs "player" and "base" (the id of a base deck).')
        doc = decks.new_version(self.root, player=player, name=body.get("name"), base_id=base, settings=settings)
        return 201, {"version": version_view(doc)}

    # --- routes: one deck
    def route_deck(self, args, query, body):
        return self._answer(*args)

    def route_deck_change(self, args, query, body):
        player, version_id = args
        if "revision" not in body:
            raise decks.DeckError('Say which revision of the deck this change is made on: "revision".')
        change = {k: v for k, v in body.items() if k != "revision"}
        session = self._open(player, version_id)
        with session.lock:
            doc = decks.version(self.root, player, version_id)
            session.recheck(doc)
            if self.switches.take_conflict():
                raise decks.Conflict("This deck changed on another device (the MTG_SERVE_CONFLICT test switch asked "
                                     "for this answer). Reload it and try again.", revision=doc["revision"])
            doc, result = decks.apply(self.root, player, version_id, change, revision=body["revision"], db=self.db)
            return 200, session.answer(doc, result)

    def route_deck_update(self, args, query, body):
        player, version_id = args
        if "revision" not in body:
            raise decks.DeckError('Say which revision of the deck this change is made on: "revision".')
        settings = body.get("settings")
        if settings is not None:
            checked_settings(settings)
        decks.version(self.root, player, version_id)            # the ids are valid and the deck exists
        with self.session(player, version_id).lock:
            decks.update(self.root, player, version_id, revision=body["revision"], name=body.get("name"),
                         settings=settings)
        return self._answer(player, version_id)

    def route_deck_suggest(self, args, query, body):
        player, version_id = args
        session = self._open(player, version_id)
        with session.lock:
            doc = decks.version(self.root, player, version_id)
            session.recheck(doc)
            budget = _dollars(body["budget"] if "budget" in body else doc["settings"].get("budget"), "budget")
            points = body.get("price_points")
            if points is not None and not (isinstance(points, list) and points and all(
                    _number(p) and p > 0 for p in points)):
                raise decks.Invalid('"price_points" must be a list of dollar amounts above zero.')
            if points is not None and budget is None:
                raise decks.Invalid("Price points are steps up to a budget, so give a budget as well.")
            ctx, deck, colors = session.snapshot(doc)
            ws = session.ws
        result = self.upgrade(ctx, deck, self.db, budget=budget, price_points=points,
                              combos_fn=lambda commanders, names: self.combos(commanders, names, identity=colors))
        result = dict(result, revision=doc["revision"], budget=budget)
        result["warnings"] = unique(list(result.get("warnings") or []) + drain(carddb.WARNINGS, roles.WARNINGS))
        mentioned = [x[k] for x in result.get("swaps") or [] for k in ("cut", "add")]
        mentioned += [x["card"] for x in (result.get("blocked") or []) + (result.get("cheap_adds") or [])]
        with session.lock:
            result["cards"] = {name: ws.tile(name) for name in dict.fromkeys(mentioned)}
        return 200, result

    # --- routes: cards
    def name_matches(self, query):
        """[(normalized name, name)] of the Commander-legal cards whose name holds every word of the (normalized)
        query. The list of all names is built on the first search."""
        with self._lock:
            if self._names is None:
                self._names = [(carddb.normalize(rec["name"]), rec["name"]) for rec in self.db.values()
                               if rec["legal"] == "legal"]
            index = self._names
        words = query.split()
        return [(key, name) for key, name in index if all(w in key for w in words)]

    def route_card_search(self, args, query, body):
        session = self._deck_of(query)
        with session.lock:
            doc = decks.version(self.root, session.player, session.id)
            session.recheck(doc)
            current, combos, _ = session.ws.look(doc)
            text = query.get("q", "")
            return 200, {"query": text, "cards": session.ws.search(current, combos, text),
                         "revision": doc["revision"]}

    def route_card(self, args, query, body):
        rec = self.db.get(args[0])
        if rec is None:
            close = self.db.suggest(args[0])
            hint = f" Close names: {', '.join(close)}." if close else ""
            raise decks.NotFound(f'No card is called "{args[0]}".{hint}', close)
        session = self._deck_of(query)
        with session.lock:
            doc = decks.version(self.root, session.player, session.id)
            session.recheck(doc)
            ws = session.ws
            current, combos, notes = ws.look(doc)
            ws.know_card(rec["name"])
            sheet = ws.sheet(current, doc, combos, rec)
            sheet["revision"] = doc["revision"]
            sheet["warnings"] = unique(ws.notes + notes + drain(carddb.WARNINGS, roles.WARNINGS))
            return 200, sheet

    # --- the `stats --version` command
    def stats_result(self, player, version_id):
        """The `stats` result of a saved version, worked out right now on this thread (no server): its metrics, each
        with the base deck's value beside it. The same numbers a page shows."""
        doc = decks.version(self.root, player, version_id)
        ws = Workspace(self, player, doc).build(doc, refresh=self.refresh)
        current, combos, notes = ws.look(doc)
        measured = ws.measure(current, doc, combos)
        sources = ws.source_dates()
        merge_sources(sources, self.index_sources())
        return {"command": "stats", "version": version_view(doc),
                "deck": {"name": doc["name"], "commanders": current["commanders"], "ci": ws.ctx["ci"],
                         "count": sum(n for n, _ in current["cards"]) + len(current["commanders"])},
                "bracket": ws.spec["bracket"], "spec": ws.spec, "budget": doc["settings"].get("budget"),
                "spent": headline_of(measured)[1], "headline": measured["headline"], "groups": measured["groups"],
                "warnings": unique(ws.spec_warnings + ws.notes + notes + list(ws.ctx.get("warnings") or [])
                                   + drain(carddb.WARNINGS, roles.WARNINGS, decks.WARNINGS)),
                "sources": sources}


def _match(pattern, parts):
    """The captured segments if `parts` fits `pattern` (":" matches any one non-empty segment), else None."""
    if len(pattern) != len(parts):
        return None
    found = []
    for want, got in zip(pattern, parts):
        if want == ":":
            if not got:
                return None
            found.append(got)
        elif want != got:
            return None
    return found


ROUTES = (
    ("GET", ("api", "status"), "route_status"),
    ("GET", ("api", "players"), "route_players"),
    ("GET", ("api", "menu"), "route_menu"),
    ("GET", ("api", "decks"), "route_decks"),
    ("POST", ("api", "decks"), "route_deck_create"),
    ("GET", ("api", "decks", ":", ":"), "route_deck"),
    ("PATCH", ("api", "decks", ":", ":"), "route_deck_update"),
    ("POST", ("api", "decks", ":", ":", "changes"), "route_deck_change"),
    ("POST", ("api", "decks", ":", ":", "suggest"), "route_deck_suggest"),
    ("GET", ("api", "bases"), "route_bases"),
    ("POST", ("api", "bases"), "route_base_create"),
    ("GET", ("api", "precons"), "route_precons"),
    ("GET", ("api", "cards"), "route_card_search"),
    ("GET", ("api", "cards", ":"), "route_card"),
)


# ----------------------------------------------------------------------------- HTTP
class Handler(http.server.BaseHTTPRequestHandler):
    """One request: the safety checks that need the raw request, then App.dispatch for /api/ or a page file."""

    timeout = 30                                # a client that stops talking does not keep a thread forever

    def do_GET(self):
        self._serve("GET")

    def do_POST(self):
        self._serve("POST")

    def do_PATCH(self):
        self._serve("PATCH")

    def do_PUT(self):
        self._serve("PUT")

    def do_DELETE(self):
        self._serve("DELETE")

    def do_OPTIONS(self):                       # never answered with permission: see "Content-Type" in the docstring
        self._serve("OPTIONS")

    def do_HEAD(self):
        self._serve("HEAD")

    @property
    def app(self):
        return self.server.app

    def log_message(self, fmt, *args):
        self.app.log(f"{self.address_string()} {fmt % args}")

    def _serve(self, method):
        # a body the client announced and we have not read (yet): if we answer without reading it, drain it at the end
        self.unread = self.headers.get("Content-Length", "0").strip() not in ("", "0") or bool(
            self.headers.get("Transfer-Encoding"))
        path, _, query = self.path.partition("#")[0].partition("?")
        is_api = path == "/api" or path.startswith("/api/")
        try:
            self.app.check_origin(self.headers.get("Host"), self.headers.get("Origin"))
            if not path.startswith("/"):
                raise ApiError(400, "The request must name a path on this server, such as /api/status.")
            if is_api:
                self._api(method, path, query)
            else:
                self._page(method, path)
        except ApiError as e:                    # a refusal before any route: the wrong place, the wrong type, too big
            self._refuse(e, is_api)
        except (ConnectionError, socket.timeout):
            self.close_connection = True         # the client left, or stopped talking, mid-request: nobody to answer
        except Exception as e:
            self.app.log(traceback.format_exc().rstrip())
            self._refuse(ApiError(500, str(e) or e.__class__.__name__), is_api)
        if self.unread:
            self._drain_input()

    def _refuse(self, error, is_api):
        if is_api:
            status, payload, headers = error_answer(error)
            self._send_api(status, payload, headers)
        else:
            self._send(error.status, error.message.encode("utf-8"), "text/plain; charset=utf-8", error.headers)

    def _api(self, method, path, query):
        body = self._read_body() if method in ("POST", "PATCH") else {}
        parts = [urllib.parse.unquote(p) for p in path.strip("/").split("/")]
        asked = {k: v[0] for k, v in urllib.parse.parse_qs(query, keep_blank_values=True).items()}
        self._send_api(*self.app.dispatch(method, parts, asked, body))

    def _read_body(self):
        """The JSON body of a write. The type and length are checked before anything is read."""
        media = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if media != "application/json":
            raise ApiError(415, 'A write must send "Content-Type: application/json".')
        if self.headers.get("Transfer-Encoding"):
            raise ApiError(411, "Send the body with a Content-Length; chunked bodies are not supported.")
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            raise ApiError(411, "A write must send a Content-Length.")
        if length < 0:
            raise ApiError(400, "The Content-Length cannot be negative.")
        if length > BODY_LIMIT:
            raise ApiError(413, f"The request body is {length:,} bytes; the most this server reads is {BODY_LIMIT:,}.")
        raw = self.rfile.read(length)
        self.unread = False
        return parse_body(raw)

    def _drain_input(self):
        """Keep reading what the client is still sending (up to twice the body limit, for LINGER_SECONDS) before the
        connection closes: closing with unread data makes the operating system reset it, and the client may then never
        see the answer."""
        deadline, left = time.monotonic() + LINGER_SECONDS, 2 * BODY_LIMIT
        try:
            self.wfile.flush()
            self.connection.shutdown(socket.SHUT_WR)
            while left > 0 and time.monotonic() < deadline:
                self.connection.settimeout(max(0.05, deadline - time.monotonic()))
                chunk = self.connection.recv(65536)
                if not chunk:
                    break
                left -= len(chunk)
        except OSError:
            pass                                 # a timeout, or the client already closed

    def _send_api(self, status, payload, headers=None):
        data = encode(payload)
        if self.app.switches.delay:
            time.sleep(self.app.switches.delay)
        self._send(status, data, "application/json; charset=utf-8", headers)

    def _send(self, status, data, content_type, headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store" if content_type.startswith("application/json") else "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")          # no other site may show the pages in a frame
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    # --- the page files
    def _page(self, method, path):
        if method not in ("GET", "HEAD"):
            raise ApiError(405, f"{method} is not allowed here.", headers={"Allow": "GET, HEAD"})
        found = self._page_file(path)
        data = None
        if found is not None:
            try:
                with open(found, "rb") as f:
                    data = f.read()
            except OSError:                       # removed or locked since the check
                data = None
        if data is None:
            web = self.app.web
            raise ApiError(404, "There is nothing at this address." if web and os.path.isdir(web) else NO_PAGES)
        self._send(200, data, CONTENT_TYPES.get(os.path.splitext(found)[1].lower(), "application/octet-stream"))

    def _page_file(self, path):
        """The file a page address names, or None. The path must stay inside the web folder: no "..", no backslash or
        drive letter (Windows), and nothing a symbolic link leads out of."""
        web = self.app.web
        if not web or not os.path.isdir(web):
            return None
        parts = urllib.parse.unquote(path).lstrip("/").split("/")
        if any(p in (".", "..") or "\\" in p or ":" in p or "\x00" in p for p in parts):
            return None
        if parts[-1] == "":
            parts[-1] = "index.html"
        top = os.path.realpath(web)
        found = os.path.realpath(os.path.join(top, *parts))
        try:
            inside = os.path.commonpath([top, found]) == top
        except ValueError:                        # another drive (Windows)
            inside = False
        return found if inside and os.path.isfile(found) else None


class DeckServer(http.server.ThreadingHTTPServer):
    """The HTTP server. It does not ask DNS for the computer's name when it starts (HTTPServer does, and with no
    network that can take many seconds), and on Windows it refuses to share a port: SO_REUSEADDR there lets a second
    server bind a port that is already in use."""

    allow_reuse_address = os.name != "nt"

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[0], self.server_address[1]

    def handle_error(self, request, client_address):
        """A failure outside any route (the base class prints it to stderr): it goes to the app's log instead."""
        self.app.log(traceback.format_exc().rstrip())


def make_server(app, host=config.SERVE_HOST, port=config.SERVE_PORT, *, daemon=True):
    """A DeckServer for `app` listening on host:port (port 0 picks a free one); the app learns the address it got. With
    daemon False, closing the server waits for the requests under way (the tests want that)."""
    server = DeckServer((host, port), Handler)
    server.daemon_threads = daemon
    server.app = app
    app.bind(host, server.server_address[1])
    return server
