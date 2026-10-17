"""Tests for the deck pages (src/mtgcommander/web/): plain files, so these tests read the files and ask the real server
for them.

There is no JavaScript test runner in this repo (the one package is TypeScript, which compiles web-src/ to web/), so the
checks here are the ones that can be made from Python: Albert's color palette has not drifted, every file the pages name exists, the modules fit together
(every name one imports, the other exports), nothing is fetched from another site, no server text can reach the page as
markup, and the real folder is what `serve` hands out. When Node is installed the modules are also syntax checked, and
the helpers of ui.js that touch no page are run (a change with its sign, the address of a symbol's picture). What the
pages do is checked in a browser, against the real server (the frontend-verify gate in the design)."""
import json, os, pathlib, re, shutil, subprocess, tempfile, threading, unittest, urllib.error, urllib.request
from unittest import mock
from mtgcommander import carddb, net, serve
from mtgcommander.providers import scryfall_tags

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WEB = os.path.join(REPO, "src", "mtgcommander", "web")
SITE_CSS = os.path.join(REPO, "card-reference", "site", "site.css")
MODULES = ("api.js", "app.js", "ui.js", "decks.js", "deck.js", "card.js", "add.js", "metrics.js")
PAGE_FILES = ("index.html", "styles.css") + MODULES
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))      # a proxy in the environment must not see us
SVG_NAMESPACE = "http://www.w3.org/2000/svg"        # a name that identifies SVG, not an address anything is loaded from
SYMBOL_FOLDER = "https://svgs.scryfall.io/card-symbols/"      # the one address a page file names: Scryfall's mana symbols


def read(name):
    with open(os.path.join(WEB, name) if not os.path.isabs(name) else name, encoding="utf-8") as f:
        return f.read()


def without_comments(source):
    """JavaScript with its comments removed (a // inside a string is cut too, which these checks do not mind)."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"(?m)(^|[^:\"'`\\])//[^\n]*", r"\1", source)


def root_rules(path):
    """The :root rules of a stylesheet as a list of {token: value}, comments left out and spacing made even."""
    text = re.sub(r"/\*.*?\*/", "", read(path), flags=re.S)
    return [{name: " ".join(value.split()) for name, value in re.findall(r"([\w-]+)\s*:\s*([^;]+);", block)}
            for block in re.findall(r":root\s*\{([^}]*)\}", text)]


# ----------------------------------------------------------------------------- the files and how they fit together
class FilesTests(unittest.TestCase):
    def test_the_pages_are_the_files_the_design_names(self):
        # index.html, the stylesheet and the eight modules: nothing missing, nothing else in the folder
        self.assertEqual(sorted(os.listdir(WEB)), sorted(PAGE_FILES))

    def test_the_root_tokens_equal_alberts_so_the_palette_cannot_drift(self):
        # card-reference/site/site.css is the source; styles.css copies its :root block and adds no tokens of its own
        theirs, ours = root_rules(SITE_CSS), root_rules(os.path.join(WEB, "styles.css"))
        self.assertEqual(len(theirs), 1)
        self.assertIn("--gold", theirs[0])
        self.assertEqual(len(ours), 1, "styles.css must hold exactly one :root rule")
        self.assertEqual(ours[0], theirs[0])

    def test_every_file_index_html_names_exists_and_the_page_starts_the_app_as_a_module(self):
        # the stylesheet and the script are relative paths inside the folder; a data: address (the icon) is not a file
        html = read("index.html")
        names = re.findall(r'(?:src|href)="([^"]+)"', html)
        self.assertIn("styles.css", names)
        self.assertIn('<script type="module" src="app.js"></script>', html)
        for name in names:
            if name.startswith("data:"):
                continue
            with self.subTest(name=name):
                self.assertFalse(re.match(r"([a-z]+:)?//", name) or name.startswith("/"),
                                 f"{name} is not a relative path")
                self.assertTrue(os.path.isfile(os.path.join(WEB, name)),
                                f"index.html names {name}, which does not exist")
        self.assertIn('<main id="main"', html)
        self.assertIn('id="sheet-layer"', html)

    def test_every_relative_import_exists_and_none_comes_from_a_package(self):
        # no packages and no bundler: each import is "./file.js" in the same folder
        for name in MODULES:
            source = without_comments(read(name))
            specifiers = re.findall(r"""(?:from|import)\s*\(?\s*["']([^"']+)["']""", source)
            for specifier in specifiers:
                with self.subTest(module=name, specifier=specifier):
                    self.assertTrue(specifier.startswith("./"), f"{name} imports {specifier}, which is not a file here")
                    self.assertTrue(os.path.isfile(os.path.join(WEB, specifier)), f"{name} imports {specifier}")

    def test_every_name_a_module_imports_is_one_the_other_module_exports(self):
        # node --check cannot see this: a misspelled import is only a failure when the page runs
        exports = {}
        for name in MODULES:
            source = without_comments(read(name))
            found = set(re.findall(r"export\s+(?:async\s+)?(?:function\*?|const|let|class)\s+(\w+)", source))
            for group in re.findall(r"export\s*\{([^}]*)\}", source):
                found |= {part.split(" as ")[-1].strip() for part in group.split(",") if part.strip()}
            exports[name] = found
        for name in MODULES:
            source = without_comments(read(name))
            for names, target in re.findall(r"import\s*\{([^}]*)\}\s*from\s*[\"']\./([\w.]+)[\"']", source):
                for wanted in (part.split(" as ")[0].strip() for part in names.split(",") if part.strip()):
                    with self.subTest(module=name, wanted=wanted, target=target):
                        self.assertIn(wanted, exports[target], f"{name} imports {wanted} from {target}")
            for alias, target in re.findall(r"import\s*\*\s*as\s+(\w+)\s+from\s*[\"']\./([\w.]+)[\"']", source):
                for member in sorted(set(re.findall(r"(?<![\w./])%s\.(\w+)" % alias, source))):
                    with self.subTest(module=name, alias=alias, member=member, target=target):
                        self.assertIn(member, exports[target],
                                      f"{name} uses {alias}.{member}, which {target} does not export")

    def test_no_page_file_loads_anything_from_another_site(self):
        # Scryfall's card picture links come from the server's data; none is written in a file. The one address that is
        # written is the folder of Scryfall's mana symbol pictures, once, in ui.js. No CDN, no font service.
        for name in PAGE_FILES:
            text = read(name).replace(SVG_NAMESPACE, "")
            with self.subTest(file=name):
                self.assertEqual(re.findall(r"https?://[^\s\"'`)>]*", text), [SYMBOL_FOLDER] if name == "ui.js" else [],
                                 f"{name} names an address")
                text = text.replace(SYMBOL_FOLDER, "")
                self.assertEqual(re.findall(r"(?:src|href)\s*=\s*[\"']//|url\(\s*[\"']?//|@import", text), [],
                                 f"{name} loads something from another site")
                self.assertNotRegex(text, r"(?i)scryfall\.(?:io|com)|googleapis|cloudflare|jsdelivr|unpkg|cdnjs")

    def test_every_request_goes_through_api_js(self):
        # one call() with the timeout and the error kinds: nothing else may talk to the server
        for name in MODULES:
            source = without_comments(read(name))
            with self.subTest(file=name):
                uses = [word for word in ("fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon")
                        if word in source]
                self.assertEqual(uses, [] if name != "api.js" else ["fetch("])

    def test_server_text_cannot_reach_the_page_as_markup(self):
        # elements are built with textContent: a card or a deck called "<img onerror=...>" is shown as text
        for name in MODULES:
            source = without_comments(read(name))
            with self.subTest(file=name):
                self.assertNotRegex(
                    source, r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function\(")

    def test_the_suggestions_tab_shows_what_the_server_worked_out_and_subtracts_nothing(self):
        # each price point's change in score and its "Weakens interaction" note come in the server's answer
        # (`change`, `weakens`), drawn with the shared signed-number formatter and banner; the page never works out a
        # difference between two scores or compares a count with a typical one
        source = without_comments(read("deck.js"))
        suggestions = source[source.index("function suggestionResult("):source.index("function swapRow(")]
        for wanted in ("point.change", "point.weakens", "ui.signed(", "Weakens interaction", "ui.banner("):
            self.assertIn(wanted, source, wanted)
        self.assertNotRegex(suggestions, r"point\.value\s*-|value_before\s*-|-\s*result\.value_before|\.after\s*<|\.before\s*-")
        self.assertNotRegex(source, r"\.weakens\s*=|\.change\s*=")          # read, never set: the server owns them

    def test_how_far_a_number_moved_is_the_servers_change_so_no_arrow_is_drawn_and_nothing_subtracts(self):
        # the server sends `change` (value - base) beside `base`; the arrows that only said which way are gone, and no
        # file works out value - base (or base - value) for itself, in either order
        for name in PAGE_FILES:
            source = without_comments(read(name))
            with self.subTest(file=name):
                self.assertNotRegex(source, r"[▲▼]|delta__arrow")
                self.assertNotRegex(source, r"\b(?:value|base)\b\s*-\s*[\w.]*\b(?:value|base)\b")

    def test_only_ui_js_draws_a_symbol_and_the_rules_text_of_a_card_goes_through_it(self):
        # one copy of each shared piece: no other module builds a symbol picture or names its folder, and the card sheet's
        # rules text is drawn by the helper that puts a picture in place of each {...}
        for name in MODULES:
            source = without_comments(read(name))
            with self.subTest(file=name):
                if name != "ui.js":
                    self.assertNotRegex(source, r"mana-sym|card-symbols|symbolUrl|manaSymbol|symbolAsText")
        self.assertIn("ui.symbolText(", without_comments(read("card.js")))
        self.assertNotRegex(without_comments(read("card.js")), r"class:\s*\"rules\"\s*,\s*text")

    def test_the_symbol_list_in_ui_js_repeats_nothing_and_every_name_is_well_formed(self):
        # the names between the braces, as Scryfall lists them: 2, B, T, W/U, 2/W, G/P, B/G/P, HW, CHAOS, ½ and ∞
        source = without_comments(read("ui.js"))
        block = re.search(r"const SYMBOLS = new Set\(\[(.*?)\]\.join", source, re.S).group(1)
        names = " ".join(re.findall(r'"([^"]*)"', block)).split(" ")
        self.assertGreater(len(names), 80)
        self.assertEqual(sorted(names), sorted(set(names)), "a symbol is listed twice")
        for name in names:
            self.assertRegex(name, r"^(?:[0-9]+|[A-Z]+|½|∞|[WUBRGC2](?:/[WUBRGCP]){1,2})$")

    def test_the_stylesheet_uses_only_the_tokens_it_has(self):
        # every var(--x) names a token in :root (the page would silently lose that color or size otherwise)
        tokens = set(root_rules(os.path.join(WEB, "styles.css"))[0])
        css = re.sub(r"/\*.*?\*/", "", read("styles.css"), flags=re.S)
        used = set(re.findall(r"var\((--[\w-]+)", css))
        self.assertEqual(sorted(used - tokens), [])


@unittest.skipUnless(shutil.which("node"), "Node is not installed, so the modules are not syntax checked")
class SyntaxTests(unittest.TestCase):
    def test_every_module_parses_as_a_module(self):
        # `node --check` runs nothing; each module is read from standard input so that Node treats it as a module
        for name in MODULES:
            with self.subTest(module=name), open(os.path.join(WEB, name), "rb") as f:
                done = subprocess.run(["node", "--input-type=module", "--check"], stdin=f, capture_output=True,
                                      text=True, timeout=60)
            if "bad option" in done.stderr:
                self.skipTest("this Node cannot check a module read from standard input")
            self.assertEqual(done.returncode, 0, f"{name}: {done.stderr}")


SOURCE = os.path.join(REPO, "src", "mtgcommander", "web-src")
TSC = os.path.join(REPO, "node_modules", ".bin", "tsc")


class SourceTests(unittest.TestCase):
    """The modules are written in TypeScript (src/mtgcommander/web-src/) and compiled to the plain JavaScript in web/,
    which is committed, so the server hands out pages without Node. These checks keep the two folders in step."""

    def test_every_module_has_its_typescript_source_and_nothing_else_is_compiled(self):
        # types.d.ts holds only types, so it is the one source with no module of its own
        sources = sorted(name for name in os.listdir(SOURCE) if name.endswith(".ts") and not name.endswith(".d.ts"))
        self.assertEqual([name[:-3] + ".js" for name in sources], sorted(MODULES))
        self.assertEqual(sorted(name for name in os.listdir(SOURCE) if name.endswith(".d.ts")), ["types.d.ts"])

    def test_no_source_puts_server_text_into_markup_either(self):
        # the same rule as for the modules, read in the sources a person edits
        for name in os.listdir(SOURCE):
            with self.subTest(file=name):
                self.assertNotRegex(without_comments(read(os.path.join(SOURCE, name))),
                                    r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function\(")


@unittest.skipUnless(os.path.isfile(TSC), "TypeScript is not installed (npm install), so the sources are not compiled")
class CompiledTests(unittest.TestCase):
    def tsc(self, *args):
        return subprocess.run([TSC, "-p", os.path.join(REPO, "tsconfig.json"), *args], capture_output=True, text=True,
                              timeout=120, cwd=REPO)

    def test_the_sources_type_check(self):
        done = self.tsc("--noEmit")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_the_committed_modules_are_what_the_sources_compile_to(self):
        # a change to web-src/ that was not built (npm run build) would leave the served pages behind it
        with tempfile.TemporaryDirectory() as out:
            done = self.tsc("--outDir", out)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            self.assertEqual(sorted(os.listdir(out)), sorted(MODULES))
            for name in MODULES:
                with self.subTest(module=name):
                    self.assertEqual(read(os.path.join(out, name)), read(name),
                                     f"web/{name} is not what web-src/{name[:-3]}.ts compiles to: run npm run build")


def in_node(expression):
    """The JSON value of a JavaScript expression that may use `ui`, the exports of ui.js, worked out by Node. Only the
    helpers that touch no page can be run this way (nothing here builds an element)."""
    address = json.dumps(pathlib.Path(WEB, "ui.js").as_uri())
    script = f"import * as ui from {address}; process.stdout.write(JSON.stringify({expression}));"
    done = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, timeout=60)
    if re.search(r"outside a module|ERR_REQUIRE_ESM|ERR_UNKNOWN_FILE_EXTENSION|bad option", done.stderr):
        raise unittest.SkipTest("this Node cannot load a .js file as a module without a package.json")
    if done.returncode != 0:
        raise AssertionError(done.stderr)
    return json.loads(done.stdout)


MINUS = "\N{MINUS SIGN}"       # U+2212, the real minus sign, which is not the hyphen on the keyboard
DASH = "\N{EM DASH}"           # what stands for a number that is not there


@unittest.skipUnless(shutil.which("node"), "Node is not installed, so the helpers of ui.js are not run")
class PureHelperTests(unittest.TestCase):
    """The helpers in ui.js that turn numbers into text and symbols into addresses, run by Node. Each case is a worked
    example."""

    def test_a_signed_value_has_its_sign_and_its_unit(self):
        got = in_node('[ui.signedValue(14), ui.signedValue(-2), ui.signedValue(4.5, "%"), ui.signedValue(12.5, "$"), '
                      'ui.signedValue(-3.4, "$"), ui.signedValue(-16.7, "%"), ui.signedValue(0.28), '
                      'ui.signedValue(1234.5, "$")]')
        self.assertEqual(got, ["+14", MINUS + "2", "+4.5%", "+$12.50", MINUS + "$3.40", MINUS + "16.7%", "+0.28",
                               "+$1,234.50"])

    def test_a_change_of_zero_has_no_sign_and_something_that_is_not_a_number_is_a_dash(self):
        got = in_node('[ui.signedValue(0), ui.signedValue(0, "%"), ui.signedValue(null), ui.signedValue(undefined), '
                      'ui.signedValue("3"), ui.signedValue(NaN)]')
        self.assertEqual(got, ["0", "0%", DASH, DASH, DASH, DASH])

    def test_the_size_of_a_change_can_be_written_in_the_style_of_the_number_beside_it(self):
        # the stat line writes its numbers with one decimal at most: a change of 3.4 is "+3.4" there, 14.04 is "+14"
        got = in_node('[ui.signedValue(3.4, null, ui.oneDecimal), ui.signedValue(-0.16, null, ui.oneDecimal), '
                      'ui.signedValue(14.04, null, ui.oneDecimal), ui.signedValue(14.04)]')
        self.assertEqual(got, ["+3.4", MINUS + "0.2", "+14", "+14.04"])

    def test_signed_is_a_change_with_no_unit_as_it_always_was(self):
        got = in_node('[ui.signed(0.74), ui.signed(-0.2), ui.signed(0), ui.signed(null), ui.signed(1.236)]')
        self.assertEqual(got, ["+0.74", MINUS + "0.2", "0", DASH, "+1.24"])

    def test_a_symbol_is_the_picture_named_with_its_braces_and_slashes_left_out(self):
        # one generic, one colored, X, tap, hybrid, two-generic-or-color, Phyrexian, and a two-digit generic cost
        got = in_node('["{3}", "{B}", "{X}", "{T}", "{W/U}", "{2/W}", "{G/P}", "{B/G/P}", "{10}"].map(ui.symbolUrl)')
        files = ("3", "B", "X", "T", "WU", "2W", "GP", "BGP", "10")
        self.assertEqual(got, [SYMBOL_FOLDER + name + ".svg" for name in files])

    def test_the_half_and_infinity_symbols_have_picture_names_of_their_own(self):
        got = in_node('["{½}", "{∞}"].map(ui.symbolUrl)')
        self.assertEqual(got, [SYMBOL_FOLDER + "HALF.svg", SYMBOL_FOLDER + "INFINITY.svg"])

    def test_a_symbol_that_is_not_in_scryfalls_list_has_no_picture_and_is_drawn_as_text(self):
        # a hybrid written the other way round, a made-up word, lower case, no braces, one brace, none inside, two at once
        got = in_node('["{U/W}", "{foo}", "{b}", "B", "{B", "{}", "{B}{G}"].map(ui.symbolUrl)')
        self.assertEqual(got, [None] * 7)

    def test_an_item_moved_when_the_server_sent_a_change_that_is_not_zero(self):
        got = in_node('[ui.hasMoved({change: 2}), ui.hasMoved({change: -0.01}), ui.hasMoved({change: 0}), '
                      'ui.hasMoved({}), ui.hasMoved({change: null}), ui.hasMoved({base: 3, value: 5})]')
        # the last item has a base and a value that differ but no change: the pages do not work that out
        self.assertEqual(got, [True, True, False, False, False, False])


# ----------------------------------------------------------------------------- the real folder, served
class ServedPagesTests(unittest.TestCase):
    """The real src/mtgcommander/web/ folder, served by the real server (serve.make_server) over a real socket. The
    engine's collaborators are stand-ins that fail if called, as in test_serve.py: asking for a page file touches none
    of them."""

    def setUp(self):
        for door in ("fetch_json", "request", "download"):          # a test that reaches the network is a bug
            mock.patch.object(net, door, side_effect=AssertionError(f"net.{door} must not run in a test")).start()
        mock.patch.object(scryfall_tags, "INFO", {}).start()
        self.addCleanup(mock.patch.stopall)

        def never(*args, **kw):
            raise AssertionError("a page file or the status answer must not reach the engine")
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.app = serve.App(carddb.CardDB({}), self.root, web=serve.WEB_DIR, switches=serve.Switches(), wait=0.0,
                             prepare=never, combos=never, attributes=never, prices=never, upgrade=never, precon=never,
                             precon_names=never, uncommitted=lambda root: ([], None))
        self.server = serve.make_server(self.app, "127.0.0.1", 0, daemon=False)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01})
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()                                  # joins the request threads (daemon=False)
        self.thread.join()
        self.app.close()

    def get(self, path):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}")
        try:
            with OPENER.open(request, timeout=20) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as e:
            try:
                return e.code, e.headers, e.read()
            finally:
                e.close()

    def test_the_root_answers_with_index_html(self):
        # / is the shell: the same bytes as the file, as HTML
        status, headers, body = self.get("/")
        self.assertEqual((status, headers["Content-Type"]), (200, "text/html; charset=utf-8"))
        with open(os.path.join(WEB, "index.html"), "rb") as f:
            self.assertEqual(body, f.read())
        self.assertEqual(self.get("/index.html")[0], 200)

    def test_app_js_is_served_as_javascript_so_a_browser_will_run_it_as_a_module(self):
        # a module script served as text/plain is refused by the browser
        status, headers, body = self.get("/app.js")
        self.assertEqual((status, headers["Content-Type"]), (200, "text/javascript; charset=utf-8"))
        self.assertIn(b"import ", body)

    def test_every_page_file_is_served_with_its_own_type(self):
        # the stylesheet as CSS, every module as JavaScript, each exactly as it is on disk
        for name in PAGE_FILES:
            with self.subTest(file=name):
                status, headers, body = self.get("/" + name)
                self.assertEqual(status, 200)
                types = {".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                         ".html": "text/html; charset=utf-8"}
                self.assertEqual(headers["Content-Type"], types[os.path.splitext(name)[1]])
                with open(os.path.join(WEB, name), "rb") as f:
                    self.assertEqual(body, f.read())

    def test_the_status_answer_says_the_pages_are_there_and_a_hash_route_is_not_a_file(self):
        # the pages route by the address after the #, so the server never sees it; a path that is not a file is 404
        status, _, body = self.get("/api/status")
        self.assertEqual(status, 200)
        self.assertIn(b'"pages": true', body)
        self.assertEqual(self.get("/d/andy/squirrels")[0], 404)


if __name__ == "__main__":
    unittest.main()
