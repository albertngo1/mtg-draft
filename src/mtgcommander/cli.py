"""Command line for mtg-commander: nine commands, one set of shared steps.

Why it is thin: scoring and deck search live in score.py and build.py, formatting lives in render.py, and the
data lives behind carddb, decklist and the providers. This module only turns arguments into calls and results
into output, so each command reads as: load the card index, find the commander(s), build the spec, call the
engine, print. The steps every command shares (the card index, a deck or precon, the owned cards, the spec, the
warnings and sources that end up in the report) are the helpers below.

Exit codes: 0 success; 1 a mistake the user can fix (unknown card or precon, bad flags), with close matches
printed; 2 data this run cannot do without is unavailable (offline with nothing cached, or the site is down).
argparse itself exits 2 on a bad flag, so `_Parser` turns that into 1.

`--json` prints render.as_json(result) and nothing else on stdout; progress, notes and errors go to stderr.
`serve` is the one command that does not end with a report: it runs the deck pages' server until Ctrl-C."""
import argparse, datetime, importlib, math, os, sys, time
from . import brackets, carddb, config, decklist, decks, fantasy, net, providers, render, roles
from .providers import archidekt, edhrec, edhtop16, scryfall_tags, spellbook

OK, USER_ERROR, UNAVAILABLE = 0, 1, 2
CACHE_ORDER = ("fresh", "network", "stale")          # worst last, as score.py ranks them
SOURCE_LABELS = {"edhrec": "EDHREC", "archidekt": "Archidekt", "edhtop16": "EDHTop16", "scryfall": "Scryfall",
                 "scryfall_tags": "Scryfall function tags", "mtgjson": "MTGJSON", "spellbook": "Commander Spellbook"}
JUST_FETCHED = 120                                   # seconds: a download this young happened in this run
PER_PAGE, MAX_CANDIDATES = 150, 500                  # `warm`: cards taken from each page, and cards priced in all


class UserError(Exception):
    """Something the user can fix. The message is printed as is and the exit code is 1."""


# ----------------------------------------------------------------------------- arguments
class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(USER_ERROR, f"{self.prog}: error: {message}\n")   # argparse's own exit code, 2, means "no data"


def _money(text):
    try:
        value = float(text.replace("$", "").replace(",", ""))
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an amount of money: {text!r}")
    if not math.isfinite(value) or value < 0:
        raise argparse.ArgumentTypeError(f"a budget must be zero or more dollars, not {text!r}")
    return value


def _price_points(text):
    """'25,50,100' -> [25.0, 50.0, 100.0]: the dollar amounts an upgrade is stepped through."""
    amounts = [_money(part) for part in text.split(",") if part.strip()]
    if not amounts:
        raise argparse.ArgumentTypeError(f"not a list of dollar amounts: {text!r}")
    return amounts


def _count(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a whole number: {text!r}")
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be 1 or more, not {value}")
    return value


def _port(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a port number: {text!r}")
    if not 0 <= value <= 65535:
        raise argparse.ArgumentTypeError(f"a port is a number from 0 to 65535, not {value}")
    return value


def _colors(text):
    """'bg' -> 'BG': color letters in WUBRG order."""
    letters = text.upper().replace(",", "").replace(" ", "")
    if not letters or set(letters) - set("WUBRG"):
        raise argparse.ArgumentTypeError(f"use the letters W U B R G (white, blue, black, red, green), not {text!r}")
    return "".join(c for c in "WUBRG" if c in letters)


def _sources(text):
    names = tuple(s.strip().lower() for s in text.split(",") if s.strip())
    unknown = [s for s in names if s not in providers.SIGNAL_PROVIDERS]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown source {', '.join(unknown)}; the sources are "
                                         f"{', '.join(providers.SIGNAL_PROVIDERS)}")
    return names


def _bracket_flag(p, required=False):
    p.add_argument("--bracket", type=int, choices=range(1, 6), metavar="N", required=required,
                   help=f"power level 1-5 (default {config.DEFAULT_BRACKET}): 1 Exhibition, 2 Core, 3 Upgraded, "
                        "4 Optimized, 5 cEDH")


def _fantasy_flags(p, weight=True, cards=True):
    p.add_argument("--theme", action="append", metavar="T",
                   help="a theme to build around, e.g. tokens (repeat the flag or separate with commas)")
    p.add_argument("--playstyle", metavar="P", help="how the deck plays, e.g. go-wide (see `themes`)")
    p.add_argument("--fantasy", metavar="TEXT",
                   help="the deck you imagine, in your own words (Claude turns it into themes; needs a token)")
    if weight:
        p.add_argument("--fantasy-weight", type=float, metavar="W",
                       help=f"0 = pure power, 1 = theme above all (default {config.DEFAULT_FANTASY_WEIGHT})")
    p.add_argument("--keep-fun", action=argparse.BooleanOptionalAction, default=None,
                   help="penalize cards that are frustrating to play against (default on at Brackets 1-3)")
    if cards:
        p.add_argument("--include", action="append", metavar="CARD", help="a card the deck must keep (repeatable)")
        p.add_argument("--exclude", action="append", metavar="CARD",
                       help="a card the deck must not play (repeatable)")


def _owned_flags(p):
    p.add_argument("--owned", action="append", metavar="FILE",
                   help="a decklist of cards you own; they cost $0 (repeatable)")
    p.add_argument("--owned-precon", action="append", metavar="NAME",
                   help="a precon you own, e.g. \"Squirreled Away\" (repeatable)")


def _deck_source(p):
    p.add_argument("deckfile", nargs="?", metavar="DECKFILE", help="a decklist file; - reads standard input")
    p.add_argument("--precon", metavar="NAME", help="use a preconstructed deck by name instead of a file")
    p.add_argument("--commander", action="append", metavar="NAME",
                   help="the commander, when the list does not mark it (repeat for a partner)")


def build_parser():
    common = _Parser(add_help=False)
    common.add_argument("--json", action="store_true", help='print the result as JSON ("schema": 1), not a report')
    common.add_argument("--refresh", action="store_true", help="download again instead of using cached data")
    common.add_argument("--offline", action="store_true", help="never connect; use cached data only (see `warm`)")
    common.add_argument("--sources", type=_sources, default=config.SOURCES, metavar="LIST",
                        help="card-evidence sources to use, comma-separated (default " + ",".join(config.SOURCES)
                             + "; choices " + ", ".join(providers.SIGNAL_PROVIDERS) + ")")
    parser = _Parser(prog="mtg-commander", description="Build and upgrade Commander decks from deck-builder and "
                     "tournament data, within a budget and a power bracket.")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def command(name, text):
        return sub.add_parser(name, parents=[common], help=text, description=text)

    p = command("themes", "list the playstyles and themes you can ask for")
    p.add_argument("--commander", metavar="NAME", help="list this commander's own themes")
    p.add_argument("--partner", metavar="NAME", help="the commander's partner or Background")

    p = command("suggest", "rank commanders for a theme and playstyle")
    _fantasy_flags(p, weight=False, cards=False)
    _bracket_flag(p)
    p.add_argument("--colors", type=_colors, metavar="WUBRG", help="only commanders inside these colors")
    p.add_argument("--budget", type=_money, metavar="USD", help="most to spend on the deck's core cards")
    _owned_flags(p)
    p.add_argument("--limit", type=_count, default=10, metavar="N", help="commanders to show (default 10)")

    p = command("build", "build a 100-card deck around a commander")
    p.add_argument("commander", metavar="COMMANDER")
    p.add_argument("--partner", metavar="NAME", help="a second commander (Partner or Background)")
    _bracket_flag(p)
    p.add_argument("--budget", type=_money, metavar="USD", help="most to spend on cards you do not own")
    _fantasy_flags(p)
    _owned_flags(p)
    p.add_argument("--allow-combos", action="store_true", help="allow two-card combos the bracket would block")
    p.add_argument("--out", metavar="FILE", help="write the deck list here (Moxfield and Archidekt import it)")
    p.add_argument("-v", "--verbose", action="store_true", help="show the evidence for every card")

    p = command("upgrade", "suggest ranked cuts and adds for a deck you have")
    _deck_source(p)
    _bracket_flag(p)
    p.add_argument("--budget", type=_money, metavar="USD", help="most to spend on cards you do not own")
    p.add_argument("--max-swaps", type=_count, default=None, metavar="N",
                   help="most swaps to suggest (default: no limit)")
    p.add_argument("--price-points", type=_price_points, metavar="LIST",
                   help="dollar amounts, comma-separated, to show what the swaps buy on the way up to --budget "
                        "(e.g. 25,50,100; default: the budget, half of it, a quarter, ...)")
    _fantasy_flags(p)
    _owned_flags(p)
    p.add_argument("--allow-combos", action="store_true", help="allow two-card combos the bracket would block")
    p.add_argument("--out", metavar="FILE", help="write the upgraded deck list here")
    p.add_argument("-v", "--verbose", action="store_true", help="show the evidence for each cut as well")

    p = command("check", "check a deck's legality, bracket, roles and mana curve")
    _deck_source(p)
    _bracket_flag(p)

    p = command("stats", "show every metric of a deck: power, interaction, mana, playstyle, win plan and money")
    _deck_source(p)
    p.add_argument("--version", metavar="PLAYER/ID",
                   help="a saved version (see `serve`) instead of a file or precon: its bracket, themes, playstyle and "
                        "owned precons come from the version, and each number is shown beside its base deck's")
    _bracket_flag(p)
    _fantasy_flags(p, cards=False)
    _owned_flags(p)
    p.add_argument("-v", "--verbose", action="store_true", help="show how each number was worked out")

    p = command("serve", "run the local server for the deck pages (saved decks, with every metric after each change)")
    p.add_argument("--host", default=config.SERVE_HOST, metavar="ADDRESS",
                   help=f"the address to listen on (default {config.SERVE_HOST}: this computer only); use this "
                        "computer's Tailscale address to reach it from a phone")
    p.add_argument("--port", type=_port, default=config.SERVE_PORT, metavar="N",
                   help=f"the port to listen on (default {config.SERVE_PORT})")
    p.add_argument("--decks", metavar="DIR",
                   help="the folder of saved decks (default: commander/decks in the repo, or MTG_COMMANDER_DECKS)")

    p = command("warm", "download everything for a commander ahead of time (for --offline)")
    p.add_argument("commander", metavar="COMMANDER")
    p.add_argument("--partner", metavar="NAME", help="a second commander (Partner or Background)")
    _bracket_flag(p)
    p.add_argument("--theme", action="append", metavar="T", help="a theme to download (repeatable)")

    p = command("validate", "measure how closely builds match real decks")
    _bracket_flag(p, required=True)
    p.add_argument("--commanders", action="append", nargs="+", metavar="NAME",
                   help="commanders to test (default: the four most played in tournaments at Bracket 5, "
                        "else six popular ones)")
    p.add_argument("--limit", type=_count, default=20, metavar="N",
                   help="real decks held out per commander (default 20)")
    p.add_argument("--sweep", action="store_true",
                   help="Bracket 5 only: also try a grid of tournament weights (W_BRACKET[5], K_RESID)")
    p.add_argument("--calibrate", action="store_true",
                   help="also re-measure the role targets and rewrite commander/role_targets.json")
    return parser


# ----------------------------------------------------------------------------- one run
def _age_seconds(fetched):
    try:
        then = datetime.datetime.strptime(fetched, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None
    return (datetime.datetime.now(datetime.timezone.utc) - then).total_seconds()


def _info(fetched, cache=None, source="edhrec"):
    """A sources entry {"fetched", "cache", "age_days"}. A provider that does not say where its data came from
    (a precon list, a commander page) gets the answer from its age: just downloaded, in date, or past its TTL."""
    age = _age_seconds(fetched)
    if cache is None:
        cache = ("fresh" if age is None else "network" if age < JUST_FETCHED
                 else "stale" if age > config.TTL.get(source, 7 * config.DAY) else "fresh")
    return {"fetched": fetched, "cache": cache, "age_days": None if age is None else round(age / config.DAY, 1)}


class Session:
    """One command-line run: the parsed arguments, the card index once loaded, and what the report needs from
    every step (warnings to print, sources with their fetch dates)."""

    def __init__(self, args):
        self.args, self.warnings, self.sources, self._db = args, [], {}, None
        self.enabled = tuple(getattr(args, "sources", config.SOURCES))
        self.text = not args.json

    def warn(self, message):
        if message not in self.warnings:
            self.warnings.append(message)

    def early(self, notes):
        """Notes the user should see before a long wait (the fantasy text could not be read): on stderr for a
        report, in the result's warnings when stdout must stay JSON."""
        for note in notes:
            if self.text:
                print(f"note: {note}", file=sys.stderr)
            else:
                self.warn(note)

    def progress(self, message):
        if sys.stderr.isatty():
            print(f"  {message} ...", file=sys.stderr, flush=True)

    def add_source(self, name, fetched, cache=None):
        """Remember a source for the footer: its oldest fetch and its worst cache state."""
        if not fetched:
            return
        new, old = _info(fetched, cache, name), self.sources.get(name)
        if old:
            worst = max(old["cache"], new["cache"], key=lambda c: CACHE_ORDER.index(c) if c in CACHE_ORDER else 0)
            new = _info(min(old["fetched"], fetched), worst, name)
        self.sources[name] = new

    def db(self):
        if self._db is None:
            if not os.path.exists(carddb.index_path()) and not net.MODE["offline"]:
                self.progress("downloading the card index (first run only; it takes a minute or two)")
            self._db = carddb.load()
            self.add_source("scryfall", self._db.fetched, self._db.cache)
        return self._db


def _engine(name, command):
    """build.py or validate.py, imported when a command needs it, so themes, check and warm work without them."""
    full = f"{__package__}.{name}"
    try:
        return importlib.import_module(full)
    except ModuleNotFoundError as e:
        if e.name != full:
            raise
        raise UserError(f"{command} is not implemented yet (src/mtgcommander/{name}.py is missing)")


# ----------------------------------------------------------------------------- shared steps
def _unknown_error(unknown, what="card"):
    """A UserError for names the card index does not know, each with its close matches."""
    if len(unknown) == 1:
        u = unknown[0]
        hint = f"; did you mean {', '.join(u['suggestions'])}?" if u["suggestions"] else ""
        return UserError(f"unknown {what} {u['name']!r}{hint}")
    lines = [f"{len(unknown)} {what} names were not found:"]
    for u in unknown:
        hint = f"   did you mean: {', '.join(u['suggestions'])}" if u["suggestions"] else ""
        lines.append(f"  {u['name']}{hint}")
    return UserError("\n".join(lines))


def _canonical(db, names, what="card"):
    """Canonical card names for `names`, or a UserError listing every one the index lacks."""
    found, unknown = [], []
    for raw in names:
        rec = db.get(raw)
        if rec is None:
            unknown.append({"name": raw, "suggestions": db.suggest(raw)})
        elif rec["name"] not in found:
            found.append(rec["name"])
    if unknown:
        raise _unknown_error(unknown, what)
    return found


def _lead(db, names):
    """The commander(s) from names given on the command line: they exist and can lead a deck together."""
    commanders = _canonical(db, names, "commander")
    found = brackets.legality(commanders, [], db)["problems"]      # the count is beside the point with no cards
    problems = [p["message"] for p in found if p["kind"] == "commander"]
    if problems:
        raise UserError(" ".join(problems))
    return commanders


def _ci(db, commanders):
    held = {c for name in commanders for c in (db.get(name) or {}).get("ci", "")}
    return "".join(c for c in "WUBRG" if c in held)


def _theme_slugs(themes):
    return [t.strip() for item in themes or [] for t in item.split(",") if t.strip()]


def _menu(session, commanders):
    """The theme menu to check words against: this commander's own EDHREC themes when the player named a theme
    or wrote a free-text fantasy (so Claude chooses from themes the commander really has), else the common one.
    A failed page is the engine's to report; here it only means the common menu."""
    meta = None
    if commanders and "edhrec" in session.enabled and (session.args.theme or session.args.fantasy):
        try:
            meta = edhrec.commander_meta(commanders)
        except net.FetchError:
            meta = None
    return fantasy.menu(meta)


def _spec(session, db, commanders):
    """The validated fantasy spec; include and exclude are matched to real cards."""
    spec, notes = fantasy.spec_from_args(session.args, menu=_menu(session, commanders))
    session.early(notes)
    spec["include"] = _canonical(db, spec["include"])
    spec["exclude"] = _canonical(db, spec["exclude"])
    return spec


def _owned_names(session, db, parsed, label):
    """Canonical names in an owned-cards list. A collection has no sideboard, so those cards count too."""
    parsed = dict(parsed, cards=list(parsed["cards"]) + list(parsed["sideboard"]), sideboard=[])
    found = decklist.resolve(parsed, db)
    if found["unknown"]:
        shown = ", ".join(u["name"] for u in found["unknown"][:5]) + (", ..." if len(found["unknown"]) > 5 else "")
        session.warn(f"{label}: {len(found['unknown'])} owned card name(s) are not in the card index and were "
                     f"ignored: {shown}")
    return {c for _, c in found["cards"]} | set(found["commanders"])


def _precon(session, name):
    try:
        found = decklist.precon(name)
    except decklist.UnknownPrecon as e:
        raise UserError(str(e))
    session.add_source("mtgjson", found["fetched"])
    return found, {"commanders": found["commanders"], "cards": found["cards"], "sideboard": [], "unparsed": []}


def _owned(session, db):
    """The cards the player owns (they cost $0): --owned decklists and --owned-precon boxes."""
    owned = set()
    for path in session.args.owned or []:
        try:
            parsed = decklist.load(path)
        except OSError as e:
            raise UserError(f"cannot read {path}: {e.strerror or e}")
        owned |= _owned_names(session, db, parsed, path)
    for name in session.args.owned_precon or []:
        found, parsed = _precon(session, name)
        owned |= _owned_names(session, db, parsed, found["name"])
    return owned


def _load_deck(session, db):
    """(name, parsed list, resolved deck) from DECKFILE or --precon. A precon is a product the player cannot
    edit, so a name MTGJSON spells in a way the card index does not match is a warning; in a file it is the
    caller's to report."""
    a = session.args
    if bool(a.deckfile) == bool(a.precon):
        raise UserError("give a DECKFILE (use - for standard input) or --precon NAME, one of the two")
    if a.precon:
        found, parsed = _precon(session, a.precon)
        name = found["name"]
    else:
        try:
            parsed = decklist.load(a.deckfile)
        except OSError as e:
            raise UserError(f"cannot read {a.deckfile}: {e.strerror or e}")
        name = "standard input" if a.deckfile == "-" else os.path.basename(a.deckfile)
    deck = decklist.resolve(parsed, db, commander=a.commander or None)
    for note in deck["warnings"]:
        session.warn(note)
    return name, parsed, deck


def _deck_info(name, deck, db):
    """The result's "deck" block. `count` includes the commanders, as a Commander deck's 100 does."""
    return {"name": name, "commanders": deck["commanders"], "count": sum(n for n, _ in deck["cards"]) +
            len(deck["commanders"]), "ci": _ci(db, deck["commanders"])}


def _need_commander(deck):
    if deck["commanders"]:
        return deck["commanders"]
    if deck["unknown"]:
        raise _unknown_error(deck["unknown"])
    raise UserError("no commander found: mark it with a Commander section (or *CMDR*), or pass --commander NAME")


def _upgradeable(session, deck, precon):
    """Unknown names stop an upgrade (the engine cannot score what it cannot find), except in a precon."""
    if deck["unknown"]:
        if not precon:
            raise _unknown_error(deck["unknown"])
        names = ", ".join(u["name"] for u in deck["unknown"][:5])
        session.warn(f"{len(deck['unknown'])} card name(s) in the precon list are not in the card index and were "
                     f"left out: {names}")


def _write_list(path, commanders, cards):
    """Save a deck list that Moxfield and Archidekt both import."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(decklist.to_text(commanders, [(n, name) for n, name in cards]))
    except OSError as e:
        raise UserError(f"cannot write {path}: {e.strerror or e}")


def _dedupe(*lists):
    out = []
    for item in (x for lst in lists for x in lst or ()):
        if item not in out:
            out.append(item)
    return out


def _finish(session, result, ctx=None):
    """Complete a result with every warning gathered along the way (ours, the engine context's, the result's own,
    and the quiet ones the data modules collect) and every source. Where both name a source, the engine's entry
    wins, and the engine is also the one that warns about its own stale sources."""
    ctx = ctx or {}
    notes = list(carddb.WARNINGS) + list(roles.WARNINGS)
    del carddb.WARNINGS[:], roles.WARNINGS[:]
    theirs = ctx.get("sources") or {}
    for name, info in session.sources.items():
        if info["cache"] == "stale" and name not in theirs:
            age = f"{info['age_days']} days old" if info["age_days"] is not None else "out of date"
            session.warn(f"{SOURCE_LABELS.get(name, name)} data is {age} (offline or the site failed)")
    result["warnings"] = _dedupe(session.warnings, ctx.get("warnings"), result.get("warnings"), notes)
    result["sources"] = {**session.sources, **theirs, **(result.get("sources") or {})}
    return result


def _emit(text):
    """Print to stdout. A Windows pipe with a legacy code page cannot hold → or —; those become ?, and a reader
    that closed the pipe (| head) is not an error."""
    try:
        try:
            sys.stdout.write(text + "\n")
        except UnicodeEncodeError:
            encoding = sys.stdout.encoding or "ascii"
            sys.stdout.write((text + "\n").encode(encoding, "replace").decode(encoding))
        sys.stdout.flush()
    except BrokenPipeError:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())   # nothing left to flush at exit


# ----------------------------------------------------------------------------- commands
def cmd_themes(session):
    a = session.args
    names, meta = [], None
    if a.partner and not a.commander:
        raise UserError("--partner needs --commander")
    if a.commander:
        names = _lead(session.db(), [a.commander] + ([a.partner] if a.partner else []))
        if "edhrec" in session.enabled:
            try:
                meta = edhrec.commander_meta(names)
            except net.FetchError as e:
                session.warn(f"EDHREC unavailable ({e.reason}), so these are the common themes, not "
                             f"{' + '.join(names)}'s own.")
            else:
                if meta is None:
                    session.warn(f"EDHREC has no page for {' + '.join(names)}, so these are the common themes.")
                else:
                    session.add_source("edhrec", meta.get("fetched"))
        else:
            session.warn("EDHREC is not among --sources, so these are the common themes.")
    menu = fantasy.menu(meta)
    return _finish(session, {"command": "themes", "commander": " + ".join(names) or None, "commanders": names,
                             "playstyles": menu["playstyles"], "themes": menu["themes"]})


def cmd_suggest(session):
    a, db = session.args, session.db()
    spec = _spec(session, db, [])
    if not spec["themes"] and spec["playstyle"] == "value":
        raise UserError("suggest needs a theme or a playstyle: pass --theme, --playstyle or --fantasy "
                        "(the `themes` command lists the choices)")
    engine = _engine("build", "suggest")
    result = engine.suggest(spec, db, colors=a.colors, budget=a.budget, owned=_owned(session, db), limit=a.limit,
                            sources=session.enabled)
    result.setdefault("command", "suggest")
    result.setdefault("spec", spec)
    result.setdefault("bracket", spec["bracket"])
    result.setdefault("filters", {"colors": a.colors, "budget": a.budget})
    return _finish(session, result)


def cmd_build(session):
    a, db = session.args, session.db()
    commanders = _lead(db, [a.commander] + ([a.partner] if a.partner else []))
    spec, owned = _spec(session, db, commanders), _owned(session, db)
    engine = _engine("build", "build")
    ctx = engine.prepare(commanders, spec["bracket"], spec, db, owned=owned, sources=session.enabled)
    result = engine.build(ctx, db, budget=a.budget, combos_fn=spellbook.find_combos, allow_combos=a.allow_combos)
    result.setdefault("command", "build")
    result.setdefault("commanders", commanders)
    result.setdefault("ci", _ci(db, commanders))
    result.setdefault("spec", spec)
    result.setdefault("budget", a.budget)
    if a.out:
        cards = [(1, c["name"]) for c in result.get("cards") or [] if c["name"] not in commanders]
        basics = [(n, basic) for basic, n in (result.get("basics") or {}).items() if n]
        _write_list(a.out, commanders, cards + basics)
        result["out"] = a.out
    return _finish(session, result, ctx)


def cmd_upgrade(session):
    a = session.args
    if a.price_points is not None and a.budget is None:
        raise UserError("--price-points needs --budget: the price points are steps up to it")
    db = session.db()
    name, _, deck = _load_deck(session, db)
    commanders = _need_commander(deck)
    _upgradeable(session, deck, bool(a.precon))
    spec = _spec(session, db, commanders)
    names = [card for _, card in deck["cards"]]
    engine = _engine("build", "upgrade")
    ctx = engine.prepare(commanders, spec["bracket"], spec, db, deck_cards=names, owned=_owned(session, db),
                         sources=session.enabled)
    result = engine.upgrade(ctx, dict(deck, name=name), db, budget=a.budget, max_swaps=a.max_swaps,
                            price_points=a.price_points, combos_fn=spellbook.find_combos,
                            allow_combos=a.allow_combos)
    result["command"] = "upgrade"
    result["deck"] = _deck_info(name, deck, db)
    result.setdefault("spec", spec)
    result.setdefault("budget", a.budget)
    after = result.get("deck_after")
    if a.out and after:
        _write_list(a.out, after["commanders"], after["cards"])
        result["out"] = a.out
    elif a.out:
        session.warn("the upgrade returned no deck list, so --out wrote nothing")
    return _finish(session, result, ctx)


def _status(counts, targets):
    return {key: render.role_status(counts.get(key, 0), t) for key, t in targets.items()}


def _curve(cards, db):
    """Nonland cards by mana value: {"0".."6", "7+": count, "avg": mean mana value}."""
    curve, total, n = dict.fromkeys(render.CURVE_KEYS, 0), 0.0, 0
    for count, name in cards:
        rec = db.get(name)
        if rec is None or rec["land"]:
            continue
        curve["7+" if rec["cmc"] >= 7 else str(int(rec["cmc"]))] += count
        total, n = total + rec["cmc"] * count, n + count
    curve["avg"] = round(total / n, 2) if n else 0.0
    return curve


def cmd_check(session):
    a, db = session.args, session.db()
    name, parsed, deck = _load_deck(session, db)
    commanders = _need_commander(deck)
    bracket = a.bracket or config.DEFAULT_BRACKET
    cards = deck["cards"]
    # A name the index lacks still counts toward the 100 (it is reported once, below, as "unknown").
    lost = [(n, raw) for n, raw in parsed["cards"] if db.get(raw) is None]
    legality = brackets.legality(commanders, cards + lost, db)
    if deck["unknown"]:
        shown = "; ".join(u["name"] + (f" (did you mean {', '.join(u['suggestions'])}?)" if u["suggestions"] else "")
                          for u in deck["unknown"])
        legality["problems"].append({"kind": "unknown", "cards": [u["name"] for u in deck["unknown"]],
                                     "message": f"Not found in the card index, so not checked: {shown}."})
        legality["ok"] = False
    names = [card for n, card in cards for _ in range(n)]
    combos = None
    try:
        combos = spellbook.find_combos(commanders, names)
        session.add_source("spellbook", combos.get("fetched"), combos.get("cache"))
    except net.FetchError as e:
        session.warn(f"Combos were not checked: {e.source} is unavailable ({e.reason}).")
    report = brackets.check(commanders, cards, bracket, db, combos=combos)
    role_map = roles.tag([card for _, card in cards], db)
    if scryfall_tags.INFO:
        session.add_source("scryfall_tags", scryfall_tags.INFO.get("fetched"), scryfall_tags.INFO.get("cache"))
    counts = roles.counts(cards, role_map, db)
    targets = roles.targets(bracket, ci=_ci(db, commanders))
    return _finish(session, {"command": "check", "deck": _deck_info(name, deck, db), "legality": legality,
                             "bracket": bracket, "bracket_check": report,
                             "roles": {"counts": counts, "targets": targets, "status": _status(counts, targets)},
                             "curve": _curve(cards, db)})


STATS_VERSION_CLASHES = ("deckfile", "precon", "commander", "bracket", "theme", "playstyle", "fantasy",
                         "fantasy_weight", "keep_fun", "owned", "owned_precon")


def _stats_of_version(session, db):
    """`stats --version PLAYER/ID`: the metrics of a saved version, worked out by the same code the deck pages use
    (serve.App), so the numbers agree with the pages. The version holds its own bracket, themes, playstyle and owned
    precons, so none of those flags may be given beside it."""
    a = session.args
    clash = ["a DECKFILE" if name == "deckfile" else "--" + name.replace("_", "-")
             for name in STATS_VERSION_CLASHES if getattr(a, name, None) is not None]
    if clash:
        raise UserError("--version takes the deck and its settings from the saved version, so it cannot be combined "
                        f"with {', '.join(clash)}")
    player, slash, version_id = a.version.partition("/")
    if not (player and slash and version_id):
        raise UserError(f"--version takes PLAYER/ID, for example andy/squirrels-go-wide, not {a.version!r}")
    serve = _engine("serve", "stats")
    app = serve.App(db, config.DECKS, offline=net.MODE["offline"], sources=session.enabled, web=None,
                    switches=serve.Switches())
    session.progress(f"working out the metrics of {a.version}")
    try:
        result = app.stats_result(player, version_id)
    except decks.DeckError as e:
        raise UserError(e.message)
    except ValueError as e:                              # a deck file that cannot be read says which
        raise UserError(str(e))
    return _finish(session, result)


def cmd_stats(session):
    """Every metric of one deck (metrics.py). It reads the same inputs `upgrade` does (the evidence for the
    commander, the roles, the targets) plus the attribute tags, and asks `spellbook.combos_for`, which answers from
    the local combo index and falls back to the API. Cards you own (--owned, --owned-precon) cost $0; the deck's
    own cards do not, so the cost to buy is what the whole list would cost you. Cards are priced at their cheapest
    printing, as `upgrade` prices them (carddb.deck_prices), so the cost to buy of the list an upgrade made is what
    the upgrade spent.

    With --version it shows a saved version instead (see _stats_of_version)."""
    a, db = session.args, session.db()
    if bool(a.deckfile) + bool(a.precon) + bool(a.version) != 1:
        raise UserError("give a DECKFILE (use - for standard input), --precon NAME or --version PLAYER/ID, one of the "
                        "three")
    if a.version:
        return _stats_of_version(session, db)
    name, _, deck = _load_deck(session, db)
    commanders = _need_commander(deck)
    _upgradeable(session, deck, bool(a.precon))
    spec = _spec(session, db, commanders)
    names = [card for _, card in deck["cards"]]
    owned = _owned(session, db)
    ctx = _engine("build", "stats").prepare(commanders, spec["bracket"], spec, db, deck_cards=names, owned=owned,
                                            sources=session.enabled)
    attrs = roles.attributes(names, db)
    if scryfall_tags.INFO:
        session.add_source("scryfall_tags", scryfall_tags.INFO.get("fetched"), scryfall_tags.INFO.get("cache"))
    session.progress("looking up the cheapest prices")
    prices = carddb.deck_prices(names + commanders, db)
    combos = None
    try:
        copies = [card for n, card in deck["cards"] for _ in range(n)]
        combos = spellbook.combos_for(commanders, copies, identity=ctx["ci"])
        session.add_source("spellbook", combos.get("fetched"), combos.get("cache"))
        if combos.get("note"):
            session.warn(combos["note"])
    except net.FetchError as e:
        session.warn(f"Combos were not checked: {e.source} is unavailable ({e.reason}).")
    result = _engine("metrics", "stats").compute(ctx, db, deck["cards"], commanders=commanders,
                                                 attrs=attrs if roles.attributes_loaded() else None,
                                                 combos=combos, owned=owned, prices=prices)
    result.update(command="stats", deck=_deck_info(name, deck, db), bracket=spec["bracket"], spec=spec)
    return _finish(session, result, ctx)


# ----------------------------------------------------------------------------- serve
def _serve_banner(host, port, root):
    """What `serve` prints once it is listening: where to open it, how to reach it from a phone, and that there is no
    login."""
    everywhere = host in ("0.0.0.0", "::", "")
    lines = ["mtg-commander deck server is running.", ""]
    if host in ("127.0.0.1", "localhost", "::1"):
        lines += [f"  Open it on this computer:  http://{host}:{port}/", f"  Saved decks are in:        {root}", "",
                  "To reach it from your phone over Tailscale, either:",
                  f"  - leave it running and run Tailscale's own `tailscale serve --bg --https=8443 {port}`, then open",
                  "    https://<this computer's name>.<your tailnet>.ts.net:8443/ on the phone (`tailscale serve status`",
                  "    prints it; `tailscale serve --https=8443 off` stops it). Port 8443 leaves alone any site this",
                  "    computer already serves at its plain Tailscale address; or",
                  "  - stop it and start it again with --host set to this computer's Tailscale address",
                  "    (`tailscale ip -4` prints it), for example `serve --host 100.101.102.103`, then open",
                  f"    http://100.101.102.103:{port}/ on the phone."]
    elif everywhere:
        lines += [f"  Listening on port {port} of every network this computer is on.",
                  f"  From another device, open http://<this computer's address>:{port}/",
                  f"  Saved decks are in:  {root}", "", "  Use this only on a network you trust."]
    else:
        lines += [f"  Listening on {host}:{port}. On your phone, open http://{host}:{port}/",
                  f"  Saved decks are in:  {root}"]
    lines += ["", "There is no login: anyone who can reach this address can change your decks. On Tailscale",
              "that means only your own devices. Run one server at a time, since the deck files are not locked",
              "between programs.", "Press Ctrl-C to stop."]
    return "\n".join(lines)


def _log_line(line):
    print(f"{time.strftime('%H:%M:%S')} {line}", file=sys.stderr, flush=True)


def cmd_serve(session):
    """Run the deck pages' server (serve.py) until Ctrl-C. `--refresh` means "download a deck's data again when the deck
    is first opened", not "on every tap", so it is handed to the server and switched off here. There is no result to
    print: the address and the warning about having no login are printed once, when the server is listening."""
    a = session.args
    db = session.db()
    serve = _engine("serve", "serve")
    refresh, net.MODE["refresh"] = net.MODE["refresh"], False
    try:
        app = serve.App(db, a.decks or config.DECKS, offline=net.MODE["offline"], refresh=refresh,
                        sources=session.enabled, log=_log_line)
        server = serve.make_server(app, a.host, a.port)
    except ValueError as e:                              # a test switch with a value that is not a number
        raise UserError(str(e))
    except OSError as e:
        raise UserError(f"cannot listen on {a.host}:{a.port}: {e.strerror or e}")
    _emit(_serve_banner(a.host, server.server_address[1], app.root))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close(timeout=1.0)                           # a download under way is abandoned, not waited for
    print("stopped.", file=sys.stderr)


def cmd_validate(session):
    a = session.args
    engine = _engine("validate", "validate")
    commanders = _canonical(session.db(), [n for group in a.commanders for n in group], "commander") \
        if a.commanders else None
    result = engine.run(a.bracket, commanders=commanders, limit=a.limit, sweep=a.sweep, calibrate=a.calibrate,
                        sources=session.enabled)
    result.setdefault("command", "validate")
    result.setdefault("bracket", a.bracket)
    return _finish(session, result)


# ----------------------------------------------------------------------------- warm
def _score_constants():
    """What the engine uses to decide which pages to read: the bracket weights of the tournament term, the deck
    count under which a bracket counts as thin, and how many Archidekt decks widen it. The contract's values
    stand in when score.py is not there."""
    try:
        from . import score
    except ImportError:
        return {3: 0.2, 4: 0.5, 5: 1.0}, 50, 30
    return (getattr(score, "W_BRACKET", {3: 0.2, 4: 0.5, 5: 1.0}), getattr(score, "THIN", 50),
            getattr(score, "ARCHIDEKT_LIMIT", 30))


def _signal(found):
    """The Signal in a provider's answer, which is a list of one, a Signal, or nothing."""
    if isinstance(found, list):
        return found[0] if found else None
    return found


def _top_names(sig, db, limit=PER_PAGE):
    """Canonical names of the cards a page plays most, most played first (basic lands cost nothing to price)."""
    def share(stats):
        if stats.get("of"):
            return stats["decks"] / stats["of"]
        return stats.get("entries", 0) / max(1, sig["n"])      # a tournament page counts entries, not decks

    out = []
    for raw, stats in sorted(sig["cards"].items(), key=lambda kv: -share(kv[1]))[:limit]:
        rec = db.get(raw)
        if rec and "Basic" not in rec["types"] and rec["name"] not in out:
            out.append(rec["name"])
    return out


class _Downloads:
    """The steps of `warm`. Each download becomes a row {"source", "what", "cache", "fetched"} or, when it fails,
    a warning, and the next step still runs: one site being down must not stop the rest."""

    def __init__(self, session):
        self.session, self.rows, self.signals, self.failed = session, [], [], []

    def record(self, source, what, cache, fetched):
        self.rows.append({"source": source, "what": what, "cache": cache, "fetched": fetched})
        self.session.add_source(source, fetched, cache)

    def attempt(self, label, fn):
        """(True, fn()) or, when the download fails, (False, None) and a warning."""
        self.session.progress(label)
        try:
            return True, fn()
        except net.FetchError as e:
            self.failed.append(label)
            self.session.warn(f"{label} could not be downloaded ({e.source}: {e.reason})")
            return False, None

    def page(self, source, what, fn):
        """One provider call that answers with a Signal; returns it (None when there is no such page)."""
        ok, found = self.attempt(f"{source}: {what}", fn)
        sig = _signal(found)
        if sig:
            self.signals.append(sig)
            unit = "entries with decklists" if sig.get("kind") == "tournament" else "decks"
            self.record(sig.get("source", source), f"{what} ({sig['n']:,} {unit})", sig.get("cache"),
                        sig.get("fetched"))
        elif ok:
            self.rows.append({"source": source, "what": f"{what} (no such page)", "cache": "none", "fetched": None})
        return sig

    def deck_pages(self, commanders, bracket, limit):
        """Archidekt decks: the stand-in for EDHREC, or what widens a thin bracket."""
        self.page("archidekt", f"Bracket {bracket} decks",
                  lambda: archidekt.signals(commanders, bracket, limit=limit))
        return self.page("archidekt", "decks, all brackets",
                         lambda: archidekt.signals(commanders, None, limit=limit))


def _warm_edhrec(dl, commanders, bracket, themes, thin, deck_limit, archidekt_on):
    """EDHREC's pages in the order score.gather asks for them, with the same fallbacks."""
    every = dl.page("edhrec", "all-bracket page", lambda: edhrec.signals(commanders))
    here = dl.page("edhrec", f"Bracket {bracket} page", lambda: edhrec.signals(commanders, bracket))
    if not (every or here) and not dl.failed:              # a failed download has been warned about already
        dl.session.warn(f"EDHREC has no page for {' + '.join(commanders)}.")
    for t in themes:
        sig = dl.page("edhrec", f"{t} decks at Bracket {bracket}",
                      lambda t=t: edhrec.bracket_theme_signal(commanders, bracket, t))
        if not sig or sig["n"] < thin:
            sig = dl.page("edhrec", f"{t} decks, all brackets", lambda t=t: edhrec.signals(commanders, None, t))
        if not sig:
            dl.page("edhrec", f"{t} decks across all commanders", lambda t=t: edhrec.theme_signal(t))
    ok, salt = dl.attempt("edhrec: salt list", edhrec.salt_scores)
    if ok:
        dl.record("edhrec", f"salt list ({len(salt):,} cards)", "ok", None)
    if (every or here) and (here["n"] if here else 0) < thin:       # a thin bracket borrows from its neighbors
        for b in (bracket - 1, bracket + 1):
            if 1 <= b <= 5:
                dl.page("edhrec", f"Bracket {b} page (neighbor)", lambda b=b: edhrec.signals(commanders, b))
        if archidekt_on:
            dl.page("archidekt", f"Bracket {bracket} decks",
                    lambda: archidekt.signals(commanders, bracket, limit=deck_limit))
    elif not (every or here) and archidekt_on:
        dl.deck_pages(commanders, bracket, deck_limit)


def cmd_warm(session):
    a, db = session.args, session.db()
    commanders = _lead(db, [a.commander] + ([a.partner] if a.partner else []))
    bracket, themes = a.bracket or config.DEFAULT_BRACKET, _theme_slugs(a.theme)
    weights, thin, deck_limit = _score_constants()
    dl = _Downloads(session)
    dl.record("scryfall", f"card index ({len(db):,} cards)", db.cache, db.fetched)
    if "edhrec" in session.enabled:
        _warm_edhrec(dl, commanders, bracket, themes, thin, deck_limit, "archidekt" in session.enabled)
    elif "archidekt" in session.enabled:
        dl.deck_pages(commanders, bracket, deck_limit)
    if "edhtop16" in session.enabled and weights.get(bracket, 0) > 0:
        dl.page("edhtop16", "tournament results", lambda: edhtop16.signals(commanders, bracket))

    def precons():
        found = {}
        for c in commanders:
            found.update({d["name"]: d for d in decklist.precons_for_commander(c)})
        return list(found.values())

    ok, decks = dl.attempt("mtgjson: precons", precons)
    if ok:
        names = ", ".join(d["name"] for d in decks) or "none"
        oldest = min((d["fetched"] for d in decks), default=None)
        dl.record("mtgjson", f"precons with this commander: {names}", "ok", oldest)
    candidates = list(dict.fromkeys(n for sig in dl.signals for n in _top_names(sig, db)))[:MAX_CANDIDATES]
    if candidates:
        ok, _ = dl.attempt("scryfall_tags: card roles", lambda: roles.tag(candidates, db))
        if ok and scryfall_tags.INFO:
            dl.record("scryfall_tags", f"function tags (roles of {len(candidates):,} candidate cards)",
                      scryfall_tags.INFO.get("cache"), scryfall_tags.INFO.get("fetched"))
        ok, prices = dl.attempt("scryfall: cheapest prices", lambda: carddb.cheapest_prices(candidates))
        if ok:
            dl.record("scryfall", f"cheapest printings of {len(prices):,} candidate cards", "ok", None)
    return _finish(session, {"command": "warm", "commanders": commanders, "bracket": bracket, "themes": themes,
                             "fetched": dl.rows})


COMMANDS = {"themes": cmd_themes, "suggest": cmd_suggest, "build": cmd_build, "upgrade": cmd_upgrade,
            "check": cmd_check, "stats": cmd_stats, "serve": cmd_serve, "warm": cmd_warm, "validate": cmd_validate}


# ----------------------------------------------------------------------------- entry points
def run(argv=None):
    """Run one command and return its exit code (main() exits with it). The run-wide --refresh / --offline mode
    is restored afterwards, so a caller that runs several commands in one process starts each clean."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:                               # --help (0), or a usage error (USER_ERROR)
        return e.code if isinstance(e.code, int) else USER_ERROR
    saved = dict(net.MODE)
    # Only a flag that was given overrides the mode: MTG_OFFLINE=1 in the environment must survive a bare run.
    net.configure(refresh=args.refresh or None, offline=args.offline or None)
    try:
        result = COMMANDS[args.command](Session(args))
        if result is not None:                            # `serve` prints as it runs and has no report
            _emit(render.as_json(result) if args.json else render.text(result, verbose=getattr(args, "verbose", False)))
        return OK
    except UserError as e:
        print(f"error: {e}", file=sys.stderr)
        return USER_ERROR
    except net.FetchError as e:
        print(f"error: needed data is unavailable. {e.source}: {e.reason}\n"
              "Run `warm COMMANDER` while online to download it ahead of time, or try again later.", file=sys.stderr)
        return UNAVAILABLE
    except KeyboardInterrupt:
        print("stopped.", file=sys.stderr)
        return 130
    finally:
        net.MODE.update(saved)


def main(argv=None):
    sys.exit(run(argv))
