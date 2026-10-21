"""Validation: does the builder build what experienced players build, and does it keep to the rules?

Why: a card score is only a claim until a real deck is held out and the build is asked to find it. This is
sealed_algo.py's --validate for Commander: hold one real list out, build without it, and count how many of its
non-basic cards the build also plays. The number alone says little (most of a cEDH list is staples anyone
would guess), so every overlap sits beside a baseline that needs no model, the same number of most-played
cards of the other decks. The build earns its keep only by beating that baseline.

What is held out, by what each source's terms allow:
- Bracket 5: EDHTop16 top-cut decklists (the site invites API use). Leave-one-out per deck: the build is
  handed the tournament results of every other entry (score.py's tournament term) and reads EDHREC's cEDH
  page when EDHREC is among the sources.
- Brackets 1-4: Archidekt lists tagged with that bracket, the only public source of them, read only when
  "archidekt" is among the sources (its terms bar scripted requests, so that is the user's call). One build
  per commander is compared with all of its lists. The builds never read Archidekt themselves: a build that
  had seen the lists would be marked on its own homework. They read EDHREC, which cannot drop one held-out
  list (it is one of thousands), so these overlaps are somewhat optimistic, and the baseline shares that
  optimism.
- Any bracket: the share of builds that pass brackets.check with Commander Spellbook's combos. At Bracket 3
  also the upgrade check: the newest precons are upgraded within a budget, and each should end nearer to the
  role targets without overspending.

What the numbers do not say: overlap is "builds like real players at this bracket", never "wins more". Pilots
reuse their lists, so a held-out cEDH deck usually has a near-copy among the other entries, which lifts the
build and the baseline alike; read the gap between them. Only Bracket 5 has results to fit a weight to, so
`sweep` re-runs it over a grid of the tournament weight and its shrinkage. Weight 0 switches the tournament
data off altogether (score.gather reads it only when the weight is above 0), so that row is "EDHREC alone".

The pure pieces (overlap, baseline, bands, distances) are plain functions so tests can check them on worked
examples; the _Run class holds what one run shares (card index, sources, warnings) and does the fetching."""
import contextlib, datetime, sys
from collections import Counter, namedtuple
from . import brackets, build, calibrate, carddb, config, decklist, net, roles, score
from .providers import archidekt, edhtop16, spellbook

TOURNAMENT_BRACKET = 5
TIME_PERIOD = "ONE_YEAR"        # EDHTop16 window: the one calibrate.py reads, so its cached pages are reused
TOP_COMMANDERS = 4              # most played tournament commanders validated when none are named
MIN_ENTRIES = calibrate.MIN_ENTRIES   # entries in the window before a commander counts as "most played"
ENTRIES = 150                   # newest entries read per commander (calibrate.py reads the same 150)
SWEEP_LIMIT = 8                 # held-out decks per commander in the weight sweep (one build per grid cell)
SWEEP_WEIGHTS = (0, 0.5, 1, 2)  # score.W_BRACKET[5] values tried
SWEEP_SHRINKS = (25, 50, 100)   # score.K_RESID values tried

# Popular commanders across the color wheel for Brackets 1-4, each with plenty of Archidekt lists at Brackets
# 2-4. Not calibrate.ARCHIDEKT_COMMANDERS: those lists fit the role targets, and the decks that set a target
# should not also be the ones that mark the build against it.
VALIDATION_COMMANDERS = (
    "Heliod, Sun-Crowned", "Talrand, Sky Summoner", "Meren of Clan Nel Toth", "Prosper, Tome-Bound",
    "Ezuri, Claw of Progress", "Kaalia of the Vast",
)
IQR = (25, 75)                  # the "middle half" of real lists that a build's role counts should fall in
MIN_IQR_DECKS = 5               # a quartile band over fewer lists is noise

UPGRADE_BRACKET = 3
UPGRADE_PRECONS = 10
UPGRADE_BUDGET = 50.0
UPGRADE_FAILURES = 5            # unreadable precons tolerated before the check gives up (each retry is slow)
CENT = 0.005                    # build.py rounds spending to cents

COMBOS_UNCHECKED = "Combos were not checked"    # the note brackets.check adds when Spellbook was out of reach
CACHE_ORDER = ("fresh", "network", "stale")     # worst last, as score.py ranks them
JUST_FETCHED = 120              # seconds: a download this young happened during this run

Outcome = namedtuple("Outcome", "overlap baseline")     # one held-out deck


# ----------------------------------------------------------------------------- the arithmetic
def spec_for(bracket):
    """What `build COMMANDER --bracket N` asks for with no theme: no fantasy weight, and the bracket's own
    default for keeping it fun (fantasy.validate_spec: on at Brackets 1-3)."""
    return {"themes": [], "playstyle": "value", "weight": 0, "keep_fun": bracket <= 3, "bracket": bracket,
            "include": [], "exclude": [], "text": None}


def nonbasic_cards(db, names, skip=()):
    """(set of canonical names, how many names the card index lacks): a deck's non-basic cards, the commanders
    (`skip`) left out. Every deck has basic lands for free, so counting them would only pad overlap and
    baseline alike."""
    cards, unknown = set(), 0
    for raw in names:
        rec = db.get(raw)
        if rec is None:
            unknown += 1
        elif "Basic" not in rec["types"] and rec["name"] not in skip:
            cards.add(rec["name"])
    return cards, unknown


def overlap(held, other):
    """The share of the held-out deck's cards that `other` also has (0 to 1). `held` must not be empty."""
    return len(held & other) / len(held)


def most_played(counts, n):
    """The n cards played in the most decks. Ties go to the earlier name, so a run can be repeated exactly."""
    return {name for name, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:n]}


def built_cards(result, commanders):
    """The non-basic cards of a build result (basic lands are not among its rows), commanders left out."""
    return {row["name"] for row in result["cards"]} - set(commanders)


def inclusion_ranking(evidence, n, skip=()):
    """The n cards the sources list most often at the bracket, as a set: the baseline for Brackets 1-4. A
    card's rate at the bracket decides, its all-bracket rate breaks ties (and ranks cards the bracket page
    does not list). A card with no rate at all is never guessed."""
    ranked = []
    for name, card in evidence["cards"].items():
        slots = (card.get("at"), card.get("all"))
        rates = [st["decks"] / st["of"] if st and st.get("of") else 0.0 for st in slots]
        if name not in skip and any(rates):
            ranked.append((-rates[0], -rates[1], name))
    return {name for _, _, name in sorted(ranked)[:n]}


def roles_inside_band(built, decks, blue):
    """(roles inside, roles compared): for each role, whether the build's count lies within the middle half
    (IQR percentiles) of the real decks' counts. Counterspells are left out for a commander without blue,
    whose real decks hold none either (calibrate.summarize makes the same exception). `built` is a
    roles.counts-shaped dict and `decks` a list of them."""
    inside = compared = 0
    for role in calibrate.ROW_ORDER:
        if role == "counter" and not blue:
            continue
        low, high = (calibrate.percentile([d[role] for d in decks], p) for p in IQR)
        compared += 1
        inside += low <= built[role] <= high
    return inside, compared


def band_distance(counts, targets):
    """How far a deck's role counts sit outside the bracket's bands: for every role in `targets`, the cards
    short of its minimum or over its maximum (top-end has only a maximum), added up. 0 means every role is
    inside its band, so a smaller number is a deck nearer to what the bracket expects."""
    return sum(max(0, band.get("min", 0) - counts.get(role, 0), counts.get(role, 0) - band["max"])
               for role, band in targets.items())


def bracket_verdict(result, bracket):
    """True when the build follows the bracket's rules, False when it breaks one, None when it passes but its
    combo rule could not be checked because Commander Spellbook was out of reach. Only Brackets 1-3 limit
    combos; brackets.check words the unchecked case the same for every bracket, so the bracket decides."""
    report = result["bracket_check"]
    if not report["ok"]:
        return False
    combos_matter = brackets.rules(bracket)["two_card_combos"] != "any"
    if combos_matter and any(n.startswith(COMBOS_UNCHECKED) for n in report.get("notes") or ()):
        return None
    return True


def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else None


def _round(x):
    return None if x is None else round(x, 4)


def _say(message):
    """A progress line, only when a person is watching (stderr is a terminal): never in piped or --json."""
    if sys.stderr.isatty():
        print(f"  {message} ...", file=sys.stderr, flush=True)


def _today():
    return datetime.date.today().isoformat()


def _age_seconds(fetched):
    try:
        then = datetime.datetime.strptime(fetched, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None
    return (datetime.datetime.now(datetime.timezone.utc) - then).total_seconds()


def _age_days(fetched):
    seconds = _age_seconds(fetched)
    return None if seconds is None else round(seconds / config.DAY, 1)


@contextlib.contextmanager
def tournament_weights(weight, shrink):
    """Set score.W_BRACKET[5] and score.K_RESID for the length of the block, then put the old values back,
    whatever happens inside: the sweep must never leave the weights the rest of the process scores with
    changed."""
    old_weight, old_shrink = score.W_BRACKET[TOURNAMENT_BRACKET], score.K_RESID
    score.W_BRACKET[TOURNAMENT_BRACKET], score.K_RESID = weight, shrink
    try:
        yield
    finally:
        score.W_BRACKET[TOURNAMENT_BRACKET], score.K_RESID = old_weight, old_shrink


# ----------------------------------------------------------------------------- reading real decks
def read_tournament_entries(name, refresh=None, offline=None):
    """(entries, info) for a commander's newest ENTRIES EDHTop16 entries with decklists, newest first, and
    {"fetched", "cache"} for the report's source list. edhtop16.entries() would do, but it drops that info;
    the private _collect is what entries() and signals() both stand on, and its pages are the ones
    calibrate.py has already cached."""
    entries, info, _ = edhtop16._collect(name, TIME_PERIOD, ENTRIES, refresh, offline)
    return entries, info


def read_archidekt_decks(commanders, bracket, limit, refresh=None, offline=None):
    """(decks, info): up to `limit` complete Archidekt decks of exactly these commanders at the bracket,
    newest first, with {"fetched", "cache"} (the oldest download, the worst cache state; None without a deck).
    Reads archidekt._collect for the same reason as read_tournament_entries."""
    found, infos = archidekt._collect(commanders, bracket, limit, refresh, offline)
    if not infos:
        return found, None
    return found, {"fetched": min(i["fetched"] for i in infos),
                   "cache": max((i["cache"] for i in infos), key=CACHE_ORDER.index)}


class Pool:
    """A tournament commander's entries, read once. For each entry it keeps the non-basic cards as a set, and
    for the whole pool how many entries played each card, so a held-out deck's overlap, its baseline and the
    signal the build is handed all come from the same other entries."""

    def __init__(self, db, commanders, entries, info):
        self.commanders, self.entries, self.info = list(commanders), entries, info
        found = [nonbasic_cards(db, e["cards"], set(self.commanders)) for e in entries]
        self.cards = [cards for cards, _ in found]
        self.unknown = sum(n for _, n in found)
        self.play = Counter(card for cards in self.cards for card in cards)

    def held_out(self, limit):
        """Indexes of the `limit` newest top-cut entries (entries come newest first)."""
        return [i for i, e in enumerate(self.entries) if e["topcut"] and self.cards[i]][:limit]

    def signal_without(self, i):
        """The tournament Signal score.gather would read from every entry but the i-th."""
        others = self.entries[:i] + self.entries[i + 1:]
        return edhtop16.signals_from_entries(others, self.commanders, time_period=TIME_PERIOD,
                                             fetched=self.info["fetched"], cache=self.info["cache"])

    def baseline(self, i, n):
        """The n cards most played by the entries other than the i-th (Counter subtraction drops what falls to
        zero, so a card only the held-out deck played is not a guess)."""
        return most_played(self.play - Counter(self.cards[i]), n)


# ----------------------------------------------------------------------------- one run
class _Run:
    """What one validation run shares: the card index, the sources, and the warnings and source dates the
    result carries. Its methods fetch real decks, build, and score the builds with the functions above."""

    def __init__(self, db, sources, refresh, offline):
        if isinstance(sources, str):                 # "edhrec,edhtop16", as calibrate.run also accepts
            sources = [s.strip() for s in sources.split(",") if s.strip()]
        self.db, self.sources = db, tuple(sources)
        # Validation builds never read Archidekt: at Brackets 1-4 it supplies the held-out lists, and a build
        # that has seen them would be marked on its own homework (see the module docstring).
        self.build_sources = tuple(s for s in self.sources if s != "archidekt")
        self.kw = {"refresh": refresh, "offline": offline}
        self.warnings, self.failed, self.dates = [], [], {}

    # --- what the result carries
    def warn(self, message):
        if message not in self.warnings:
            self.warnings.append(message)

    def fail(self, message):
        """A warning for something skipped because data could not be had. If nothing at all succeeds, the run
        reports the failures as unavailable data (exit code 2) instead of an empty table."""
        self.failed.append(message)
        self.warn(message)

    def nothing_worked(self):
        if self.failed:
            raise net.FetchError("validate", "", "; ".join(self.failed[:3]))

    def note_source(self, name, fetched, cache=None):
        """Keep, per source, its oldest fetch and its worst cache state. A source that does not say (a precon
        list) gets the answer from its age: just downloaded, in date, or past its lifetime."""
        if not fetched:
            return
        if cache is None:
            age = _age_seconds(fetched) or 0.0
            cache = ("network" if age < JUST_FETCHED else
                     "stale" if age > config.TTL.get(name, 7 * config.DAY) else "fresh")
        old = self.dates.get(name)
        if old:
            fetched, cache = min(old["fetched"], fetched), max(old["cache"], cache, key=CACHE_ORDER.index)
        self.dates[name] = {"fetched": fetched, "cache": cache}

    def absorb(self, result):
        """Take the warnings and sources a build or upgrade result reports."""
        for line in result.get("warnings") or ():
            self.warn(line)
        for name, info in (result.get("sources") or {}).items():
            self.note_source(name, info.get("fetched"), info.get("cache"))

    def finish(self):
        """(warnings, sources) for the result: each source with its age, and one warning for every source that
        served an expired copy."""
        sources = {}
        for name, info in self.dates.items():
            days = _age_days(info["fetched"])
            sources[name] = dict(info, age_days=days)
            if info["cache"] == "stale":
                age = f"{days} days old" if days is not None else "out of date"
                self.warn(f"{score.SOURCE_NAMES.get(name, name)} data is {age} (offline or the site failed)")
        return self.warnings, sources

    # --- building and scoring
    def build_deck(self, commanders, bracket, *, signal=None, combos_fn=None, allow_combos=False):
        """prepare + build with validation's settings. No budget, and prices={}: with no budget a price cannot
        change which cards are picked, and each lookup is a request to Scryfall."""
        ctx = build.prepare(commanders, bracket, spec_for(bracket), self.db, sources=self.build_sources,
                            tournament_signal=signal, **self.kw)
        result = build.build(ctx, self.db, combos_fn=combos_fn, allow_combos=allow_combos, prices={})
        self.absorb(result)
        return ctx, result

    def ok_rate(self, verdicts):
        """The share of builds that follow their bracket's rules, over the builds whose rules could all be
        checked (None when none could)."""
        checked = [v for v in verdicts if v is not None]
        if len(checked) < len(verdicts):
            self.warn(f"Commander Spellbook was unreachable for {len(verdicts) - len(checked)} of "
                      f"{len(verdicts)} builds, so their combo rule was not checked; the rate leaves them "
                      "out.")
        return _round(sum(checked) / len(checked)) if checked else None

    @staticmethod
    def row(name, outcomes):
        return {"name": name, "decks": len(outcomes), "overlap": _round(mean(o.overlap for o in outcomes)),
                "baseline": _round(mean(o.baseline for o in outcomes))}

    def body(self, method, rows, outcomes, verdicts, in_band=None, sweep=None):
        """The parts of the result that depend on the bracket."""
        return {"method": method, "commanders": rows,
                "overall": {"overlap": _round(mean(o.overlap for o in outcomes)),
                            "baseline": _round(mean(o.baseline for o in outcomes)), "n": len(outcomes)},
                "roles_in_iqr": in_band, "bracket_ok_rate": self.ok_rate(verdicts), "sweep": sweep}

    # --- Bracket 5
    def tournament(self, commanders, limit, sweep):
        method = (f"leave-one-out on EDHTop16 top-cut decks (up to {limit} per commander, from each one's "
                  f"newest {ENTRIES} entries): build without the held-out deck's entry, count how many of "
                  "its non-basic cards the build also plays, and compare with the same number of "
                  "most-played cards of the other entries. Pilots reuse lists and EDHREC's cEDH page may "
                  "hold the held-out list, so read the gap to the baseline, not the absolute number.")
        if "edhtop16" not in self.sources:
            self.warn("Bracket 5 is checked against EDHTop16 tournament decks, and EDHTop16 is not among the "
                      "sources, so nothing was measured. Add it with --sources.")
            return self.body(method, [], [], [])
        pools = self._read_pools(commanders, limit)
        rows, outcomes, verdicts = [], [], []
        for shown, pool, held in pools:
            done = []
            for n, i in enumerate(held, 1):
                _say(f"Bracket 5, {shown}: deck {n} of {len(held)}")
                try:
                    outcome, verdict = self._hold_out(pool, i)
                except net.FetchError as err:
                    self.fail(f"{shown}: a held-out deck was skipped ({err})")
                    continue
                done.append(outcome)
                verdicts.append(verdict)
            if done:
                rows.append(self.row(shown, done))
                outcomes += done
        if not outcomes:
            self.nothing_worked()
        table = self._weight_sweep(pools) if sweep and outcomes else None
        if table:
            weight = score.W_BRACKET[TOURNAMENT_BRACKET]
            shipped = f"W_BRACKET[5] = {weight:g} and K_RESID = {score.K_RESID:g}"
            method += (f" Sweep: mean overlap over the newest {SWEEP_LIMIT} held-out decks per commander for "
                       f"each pair; this build ships {shipped}.")
        return self.body(method, rows, outcomes, verdicts, sweep=table)

    def _read_pools(self, commanders, limit):
        """[(name shown, Pool, held-out indexes)] for every commander with a top-cut deck to hold out."""
        pools = []
        for shown, name, names in self._tournament_commanders(commanders):
            _say(f"reading EDHTop16 entries for {shown}")
            try:
                entries, info = read_tournament_entries(name, **self.kw)
            except net.FetchError as err:
                self.fail(f"EDHTop16 commander {shown!r} was skipped: {err}")
                continue
            self.note_source("edhtop16", info["fetched"], info["cache"])
            if not entries:
                self.warn(f"EDHTop16 has no entries with decklists for {shown}.")
                continue
            if not any(e["cards"] for e in entries):   # what every entry looks like since 2026-10-19
                self.warn(f"{shown}: no deck to hold out. {edhtop16.NO_DECKLISTS}.")
                continue
            pool = Pool(self.db, names, entries, info)
            if pool.unknown:
                self.warn(f"{pool.unknown} card name(s) in {shown}'s decklists are not in the card index and "
                          "were left out of the comparison.")
            held = pool.held_out(limit)
            if held:
                pools.append((shown, pool, held))
            else:
                self.warn(f"{shown}: no top-cut deck among its {len(entries)} newest EDHTop16 entries.")
        return pools

    def _tournament_commanders(self, commanders):
        """[(name shown, EDHTop16's name, [canonical commanders])]: the commanders asked for, else the most
        played in tournaments (a partner pair is one entry, named 'A / B')."""
        if commanders:
            return [(c, edhtop16.commander_name([c]), [c]) for c in commanders]
        out = []
        for found in edhtop16.top_commanders(MIN_ENTRIES, **self.kw)[:TOP_COMMANDERS]:
            parts = [self.db.resolve(p) for p in calibrate.split_pair(found["name"])]
            if None in parts:
                self.warn(f"{found['name']} was skipped: the card index does not know all of its cards.")
            else:
                out.append((found["name"], found["name"], parts))
        return out

    def _hold_out(self, pool, i):
        """(Outcome, verdict): build for the commanders without entry i, and compare with the entry."""
        _, result = self.build_deck(pool.commanders, TOURNAMENT_BRACKET, signal=pool.signal_without(i),
                                    allow_combos=True)
        built, held = built_cards(result, pool.commanders), pool.cards[i]
        outcome = Outcome(overlap(held, built), overlap(held, pool.baseline(i, len(built))))
        return outcome, bracket_verdict(result, TOURNAMENT_BRACKET)

    def _weight_sweep(self, pools):
        """[{"w_bracket", "k_resid", "overlap", "decks"}]: mean overlap for each pair of weights, on the
        first SWEEP_LIMIT held-out decks of each commander. K_RESID only scales the residual, which weight 0
        switches off, so that row is built once and shown under every K."""
        cells, rows = {}, []
        for weight in SWEEP_WEIGHTS:
            for shrink in SWEEP_SHRINKS:
                key = (weight, shrink) if weight else (0, None)
                if key not in cells:
                    _say(f"weight sweep: W_BRACKET[5] = {weight:g}, K_RESID = {shrink:g}")
                    cells[key] = self._sweep_cell(weight, shrink, pools)
                rows.append({"w_bracket": weight, "k_resid": shrink, "overlap": _round(mean(cells[key])),
                             "decks": len(cells[key])})
        return rows

    def _sweep_cell(self, weight, shrink, pools):
        overlaps = []
        with tournament_weights(weight, shrink):
            for shown, pool, held in pools:
                for i in held[:SWEEP_LIMIT]:
                    try:
                        overlaps.append(self._hold_out(pool, i)[0].overlap)
                    except net.FetchError as err:
                        self.fail(f"{shown}: a sweep build was skipped ({err})")
        return overlaps

    # --- Brackets 1-4
    def casual(self, bracket, commanders, limit, sweep):
        names = list(commanders) if commanders else list(VALIDATION_COMMANDERS)
        compare = "archidekt" in self.sources
        if compare:
            method = (f"one Bracket {bracket} build per commander from EDHREC (the builds never read "
                      f"Archidekt), compared with up to {limit} recent Archidekt Bracket {bracket} lists "
                      "each: overlap is the share of a list's non-basic cards the build also plays, the "
                      "baseline is the same number of cards the sources list most often at the bracket, and "
                      "role counts are checked against the middle half (25th to 75th percentile) of those "
                      "lists. EDHREC's numbers cannot exclude one held-out list (it is one of thousands).")
        else:
            method = (f"Bracket {bracket} rules checked on one build per commander; overlap was not measured "
                      "because there are no held-out lists.")
            self.warn(f"Overlap at Bracket {bracket} needs real lists tagged with that bracket, and only "
                      "Archidekt has them. Archidekt is not among the sources (its terms bar scripted "
                      "requests, so it is your call: --sources edhrec,archidekt,edhtop16), so overlap, "
                      "baseline and role bands are left empty. The rule checks still ran.")
        if sweep:
            self.warn("The weight sweep runs at Bracket 5 only: it is the one bracket with tournament "
                      "results to hold out.")
        rows, outcomes, verdicts, band = [], [], [], [0, 0]
        for n, name in enumerate(names, 1):
            _say(f"Bracket {bracket}, {name} ({n} of {len(names)})")
            try:
                row, found, verdict, inside = self._casual_commander(bracket, name, limit, compare)
            except net.FetchError as err:
                self.fail(f"{name} was skipped: {err}")
                continue
            rows.append(row)
            outcomes += found
            verdicts.append(verdict)
            band = [band[0] + inside[0], band[1] + inside[1]]
        if not rows:
            self.nothing_worked()
        in_band = _round(band[0] / band[1]) if band[1] else None
        return self.body(method, rows, outcomes, verdicts, in_band=in_band)

    def _casual_commander(self, bracket, name, limit, compare):
        """(row, [Outcome], verdict, (roles inside, roles compared)) for one commander: one build, then every
        held-out Archidekt list scored against it."""
        ctx, result = self.build_deck([name], bracket, combos_fn=spellbook.find_combos)
        verdict, commanders = bracket_verdict(result, bracket), ctx["commanders"]
        decks = self._archidekt_lists(commanders, bracket, limit) if compare else []
        built = built_cards(result, commanders)
        guess = inclusion_ranking(ctx["evidence"], len(built), set(commanders))
        outcomes, unknown = [], 0
        for deck in decks:
            held, missing = nonbasic_cards(self.db, deck["cards"], set(commanders))
            unknown += missing
            if held:
                outcomes.append(Outcome(overlap(held, built), overlap(held, guess)))
        if unknown:
            self.warn(f"{unknown} card name(s) in {name}'s Archidekt lists are not in the card index and "
                      "were left out of the comparison.")
        inside = self._role_band(ctx, result, decks) if decks else (0, 0)
        in_band = _round(inside[0] / inside[1]) if inside[1] else None
        row = dict(self.row(name, outcomes), roles_in_iqr=in_band)
        return row, outcomes, verdict, inside

    def _archidekt_lists(self, commanders, bracket, limit):
        """The held-out lists for a commander; [] with a warning when there are none or Archidekt failed."""
        shown = " + ".join(commanders)
        try:
            decks, info = read_archidekt_decks(commanders, bracket, limit, **self.kw)
        except net.FetchError as err:
            self.fail(f"Archidekt lists for {shown} were skipped: {err}")
            return []
        if info:
            self.note_source("archidekt", info["fetched"], info["cache"])
        if not decks:
            self.warn(f"No complete Archidekt Bracket {bracket} deck was found for {shown}.")
        return decks

    def _role_band(self, ctx, result, decks):
        """(roles inside, roles compared) for the build against the real lists' role counts; (0, 0) when there
        are too few lists for a quartile band to mean anything."""
        if len(decks) < MIN_IQR_DECKS:
            self.warn(f"{' + '.join(ctx['commanders'])}: only {len(decks)} Archidekt lists (under "
                      f"{MIN_IQR_DECKS}), so its role counts were not compared.")
            return 0, 0
        names = list(dict.fromkeys(card for deck in decks for card in deck["cards"]))
        role_map = roles.tag(names, self.db, **self.kw)
        counts = [calibrate.deck_counts(ctx["commanders"], [(1, c) for c in deck["cards"]], self.db,
                                        role_map)[0] for deck in decks]
        blue = "U" in calibrate.identity(ctx["commanders"], self.db)
        return roles_inside_band(result["roles"], counts, blue)

    # --- the upgrade check (Bracket 3)
    def upgrade_check(self):
        """Upgrade the newest precons at UPGRADE_BRACKET within UPGRADE_BUDGET and report how many ended
        nearer to the role targets, and whether every spend stayed inside the budget. A precon already inside
        every band cannot move closer and counts as unchanged. None when no precon could be read."""
        listed = decklist._entries(self.kw["refresh"], self.kw["offline"])   # the call that has release dates
        entries = calibrate.recent_precons(listed, _today())
        rows, failures = [], 0
        for entry in entries:
            if len(rows) >= UPGRADE_PRECONS or failures >= UPGRADE_FAILURES:
                break
            _say(f"upgrade check {len(rows) + 1} of {UPGRADE_PRECONS}: {entry['name']}")
            try:
                row = self._upgrade_precon(entry["name"])
            except (net.FetchError, decklist.UnknownPrecon) as err:
                self.fail(f"Precon {entry['name']!r} was skipped in the upgrade check: {err}")
                row = None
            if row:
                rows.append(row)
            else:
                failures += 1
        if not rows:
            return None
        closer = sum(r["gap_after"] < r["gap_before"] for r in rows)
        farther = sum(r["gap_after"] > r["gap_before"] for r in rows)
        over = [r["precon"] for r in rows if r["spent"] > UPGRADE_BUDGET + CENT]
        return {"bracket": UPGRADE_BRACKET, "budget": UPGRADE_BUDGET, "precons": len(rows), "closer": closer,
                "same": len(rows) - closer - farther, "farther": farther,
                "share_closer": _round(closer / len(rows)), "within_budget": not over, "over_budget": over,
                "rows": rows}

    def _upgrade_precon(self, name):
        """The check's row for one precon, or None (with a warning) when the card index cannot place it."""
        deck = decklist.precon(name, **self.kw)
        self.note_source("mtgjson", deck["fetched"])
        found = decklist.resolve({"commanders": deck["commanders"], "cards": deck["cards"], "sideboard": [],
                                  "unparsed": []}, self.db)
        if not found["commanders"]:
            self.warn(f"{deck['name']} was skipped in the upgrade check: the card index does not know its "
                      "commander.")
            return None
        if found["unknown"]:
            self.warn(f"{deck['name']}: {len(found['unknown'])} card name(s) not in the card index were left "
                      "out of the upgrade check.")
        ctx = build.prepare(found["commanders"], UPGRADE_BRACKET, spec_for(UPGRADE_BRACKET), self.db,
                            deck_cards=[card for _, card in found["cards"]], sources=self.build_sources,
                            **self.kw)
        result = build.upgrade(ctx, dict(found, name=deck["name"]), self.db, budget=UPGRADE_BUDGET,
                               combos_fn=spellbook.find_combos)
        self.absorb(result)
        return {"precon": deck["name"],
                "gap_before": band_distance(result["roles_before"], result["targets"]),
                "gap_after": band_distance(result["roles_after"], result["targets"]),
                "spent": result["spent"], "swaps": len(result["swaps"])}


def _refit(job):
    """calibrate.run(write=True): re-measure the role targets and rewrite commander/role_targets.json. Runs
    after the validation, so the numbers above describe the targets as committed. (A function of its own
    because run()'s `calibrate` flag hides the module inside it.)"""
    try:
        report = calibrate.run(sources=job.sources, write=True, progress=_say, **job.kw)
    except net.FetchError as err:
        job.warn(f"Calibration failed: {err}")
        return None
    for line in report.get("warnings") or ():       # the report prints in a few lines; its warnings go here
        job.warn(f"Calibration: {line}")
    return report


def run(bracket, commanders=None, *, limit=20, sweep=False, calibrate=False, sources=None, refresh=None,
        offline=None):
    """Validate the builder at `bracket` and return the result (see the design doc, "Command line and result
    shapes"): {"command": "validate", "bracket", "method", "commanders": [{"name", "decks", "overlap",
    "baseline"}], "overall": {"overlap", "baseline", "n"}, "roles_in_iqr", "bracket_ok_rate", "sweep",
    "calibration", "upgrade_check", "warnings", "sources"}.

    `commanders` are canonical names (default: the four most played tournament commanders at Bracket 5, else
    VALIDATION_COMMANDERS); `limit` is held-out decks per commander. `sources` is the set of evidence
    sources a run may use (default config.SOURCES): "edhtop16" is the Bracket 5 exam, "archidekt" the Bracket
    1-4 exam, and a source that is off leaves its numbers None with a warning that says why. A commander or
    deck that cannot be read is skipped with a warning; if nothing at all could be, FetchError."""
    brackets.rules(bracket)                        # an out-of-range bracket fails here, not after downloads
    job = _Run(carddb.load(refresh=refresh, offline=offline),
               config.SOURCES if sources is None else sources, refresh, offline)
    if bracket == TOURNAMENT_BRACKET:
        body = job.tournament(commanders, limit, sweep)
    else:
        body = job.casual(bracket, commanders, limit, sweep)
    check = job.upgrade_check() if bracket == UPGRADE_BRACKET else None
    refit = _refit(job) if calibrate else None
    warnings, dates = job.finish()
    return {"command": "validate", "bracket": bracket, **body, "calibration": refit, "upgrade_check": check,
            "warnings": warnings, "sources": dates}
