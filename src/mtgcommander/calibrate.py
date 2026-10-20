"""Measure what real Commander decks hold in each role and write it as commander/role_targets.json.

Why: the role targets (lands, ramp, card draw, removal, board wipes, counterspells, protection, recursion,
tutors, finishers, and the cap on nonland cards of mana value 6 or more) started as hand-set guesses, and they
sat below what roles.py's tags actually count in real decks: the average precon holds 12 ramp cards against a
target of 10 and 10 removal spells against 7. A target below what good decks hold tells `build` and `upgrade`
that a short deck is fine. So every number here is a percentile of a real sample, and the file says where each
bracket's numbers came from.

What each bracket rests on, by what the sources' terms allow:
- Bracket 2: the newest MTGJSON Commander precons, "precons as a Bracket 2 proxy". Wizards no longer ties Core
  to precons, so these are typical out-of-the-box decks, not a sample of Bracket 2 decks.
- Bracket 5: EDHTop16 top-cut decklists of the most played tournament commanders (the site invites API use).
- Brackets 3 and 4: Archidekt decks tagged with that bracket, only when "archidekt" is among the sources.
  EDHREC's and Archidekt's terms bar scripted requests and whether to use them is the user's decision, so
  without it these two are interpolated between 2 and 5 and labelled "interpolated (judgment)".
- Bracket 1: nothing is sampled for it, so it is Bracket 2 with one more land and no tutors, labelled
  "judgment".

The same decks also measure the numbers of metrics.py that no role count can stand in for, and `--write` stores
them beside the role targets in commander/metric_targets.json: same samples, same percentiles, same
interpolation for Brackets 3 and 4, and Bracket 1 equal to Bracket 2 (no sample, so the only judgment is that a
theme-first deck wants the same interaction as a precon). They are
- removal power and wipe power, the weighted sums of the removal cards and the board wipes, rounded to a tenth;
- the seven answer counts of roles.THREATS: for each kind of threat (creatures, artifacts, enchantments,
  planeswalkers, lands, graveyards, spells), how many of a deck's 99 cards can answer it, counted exactly as
  metrics.py counts "answers to each threat". These are whole cards, so like the role targets they round half up
  to whole numbers, and, like the counterspell target, answers to spells are counted only over decks whose
  commander has blue (the reader, roles.answer_bands, drops that band's minimum to 0 for a deck without blue).
The Metrics tab marks an answer count short when it is under the bracket's minimum (the 25th percentile); `upgrade`
holds a higher bar: it uses the median (the target) of each answer count as the fewest answers a swap may leave.

Run:  cd src && python3 -m mtgcommander.calibrate --out role_targets.proposed.json
(`--write` replaces both committed files; `--sources edhtop16,archidekt` measures Brackets 3 and 4 from
Archidekt instead of interpolating them.)"""
import argparse, datetime, json, math, os, re, sys
from collections import Counter
from fractions import Fraction
from . import carddb, config, decklist, metrics, net, roles
from .providers import archidekt, edhtop16

BRACKETS = (1, 2, 3, 4, 5)
DECK_SIZE = 100          # cards in a Commander deck, commanders included
MIN_DECKS = 10           # fewer decks than this at a bracket is too few to take percentiles of
MIN_ENTRIES = 150        # a tournament commander counts as "most played" with this many entries in the year
SPREAD = (25, 50, 90)    # percentiles that become min, target, max
LAND_SPREAD = (10, 50, 90)   # lands: the low end is the one that matters, a deck short of lands stumbles
TOPEND_PERCENTILE = 75   # the cap on nonland cards of mana value 6 or more
ROW_ORDER = ("land",) + roles.ROLES + ("topend",)
POWER_ORDER = ("removal_power", "wipe_power")   # the weighted sums of metrics.py, measured alongside, in file order
ANSWER_ORDER = roles.THREAT_IDS                 # and the whole-card counts of answers to each threat, after them
METRIC_ORDER = POWER_ORDER + ANSWER_ORDER
# How many numbers go on each line of a bracket's block in metric_targets.json: the two power sums, then the answers
# four and three to a line, so a line of the file never mixes the two kinds and the diff of a new run stays small.
METRIC_LINES = (len(POWER_ORDER), 4, len(ANSWER_ORDER) - 4)

# Popular commanders across the five colors, used only when Archidekt is among the sources. Each has plenty
# of Archidekt decks at Brackets 3 and 4; the exact Scryfall names are what Archidekt's commanderName takes.
ARCHIDEKT_COMMANDERS = (
    "Atraxa, Praetors' Voice", "Korvold, Fae-Cursed King", "Edgar Markov", "Muldrotha, the Gravetide",
    "Yuriko, the Tiger's Shadow", "Krenko, Mob Boss", "Urza, Lord High Artificer",
    "Selvala, Heart of the Wilds", "Miirym, Sentinel Wyrm", "The Ur-Dragon",
)

FORMAT = ("per bracket, each role is [min, target, max] cards counted over the 99 cards (98 with two "
          "commanders); topend is the most nonland cards with mana value 6 or more")
METRIC_FORMAT = ("per bracket, each metric is [min, target, max] over the 99 cards (98 with two commanders): "
                 "removal_power and wipe_power are sums as metrics.py weighs the cards, in the same units stats "
                 "prints; each answers_* is a count of whole cards, the distinct cards that can answer that kind of "
                 "threat (roles.THREATS), as stats counts them")
# "Doom Prevails Collector's Edition" is "Doom Prevails" again, with fancier printings
_TWIN = re.compile(r"\s*collector.s edition", re.I)


class NotEnoughData(net.FetchError):
    """Too few decks to calibrate (a source failed, or offline with a thin cache). A FetchError so the command
    line can report it like any other required data that is unavailable."""
    def __init__(self, reason):
        super().__init__("calibrate", "", reason)

    def __str__(self):
        return self.reason


# ----------------------------------------------------------------------------- statistics
def percentile(values, pct):
    """The pct-th percentile (0-100) of `values`, interpolating linearly between the sorted values (numpy's
    default). An exact Fraction, so a value that sits exactly on a half is not tipped by float error before
    round_half_up sees it."""
    xs = sorted(values)
    if not xs:
        raise ValueError("percentile of no values")
    pos = Fraction(pct * (len(xs) - 1), 100)
    low = math.floor(pos)
    high = min(low + 1, len(xs) - 1)
    return xs[low] + (xs[high] - xs[low]) * (pos - low)


def round_half_up(x):
    """2.5 -> 3. Python's round() sends halves to the even number (2.5 -> 2), which would make a target of
    exactly 'between 9 and 10' depend on which is even."""
    return math.floor(x + Fraction(1, 2))


def summarize(rows):
    """One bracket's numbers from its decks: {"land": [min, target, max], ..., "topend": n}. `rows` are
    {"counts": roles.counts output, "blue": bool}. min <= target <= max holds because the percentiles rise
    with their rank and rounding never reorders them."""
    out = {}
    for role in ("land",) + roles.ROLES:
        # A deck without blue was never going to run counterspells; its zero would drag the target down.
        pool = [r for r in rows if r["blue"]] if role == "counter" else rows
        spread = LAND_SPREAD if role == "land" else SPREAD
        out[role] = ([round_half_up(percentile([r["counts"][role] for r in pool], p)) for p in spread]
                     if pool else [0, 0, 0])
    out["topend"] = round_half_up(percentile([r["counts"]["topend"] for r in rows], TOPEND_PERCENTILE))
    return out


# Where Brackets 3 and 4 sit between the two measured ends when no deck tagged with them was sampled, as a
# fraction (step, of) of the way from precons (2) to cEDH (5). Judgment: the cEDH end is blue, partner-heavy
# and combo-driven, so an even thirds split pulls Upgraded decks too far toward it (30 lands, 7 tutors at 4).
BLEND = {3: (1, 4), 4: (1, 2)}


def interpolate(low, high, step, of=3):
    """A bracket `step`/`of` of the way from `low` to `high` (each {role: [min, target, max], "topend": n}),
    number by number, rounded half up. It works from the rounded numbers so anyone can check it from the
    file. A blend of two ordered triples stays ordered."""
    def mix(a, b):
        return round_half_up(Fraction(a * (of - step) + b * step, of))
    return {role: mix(v, high[role]) if role == "topend" else [mix(a, b) for a, b in zip(v, high[role])]
            for role, v in low.items()}


def exhibition(two):
    """Bracket 1 from Bracket 2 (judgment): a theme-first deck is slower and wants one more land, and it
    plays no tutors. The tutor ceiling stays Bracket 2's. The land ceiling moves up if the new target would
    pass it."""
    one = {role: v if role == "topend" else list(v) for role, v in two.items()}
    one["land"][1] += 1
    one["land"][2] = max(one["land"][2], one["land"][1])
    one["tutor"] = [0, 0, two["tutor"][2]]
    return one


def build_table(decks):
    """({bracket: numbers}, {bracket: measured?}) from {bracket: [rows]}. Brackets 2 and 5 need MIN_DECKS
    decks: they are the two ends that 3 and 4 are interpolated between and that 1 is derived from. Brackets 3
    and 4 are measured when enough decks (Archidekt) came in, else interpolated."""
    for bracket, source in ((2, "MTGJSON precons"), (5, "EDHTop16 top-cut decks")):
        n = len(decks.get(bracket, ()))
        if n < MIN_DECKS:
            raise NotEnoughData(f"Bracket {bracket} needs at least {MIN_DECKS} decks from {source}, got {n}")
    table = {b: summarize(rows) for b, rows in decks.items() if len(rows) >= MIN_DECKS}
    measured = {b: b in table for b in BRACKETS}
    for b in (3, 4):
        if not measured[b]:
            table[b] = interpolate(table[2], table[5], *BLEND[b])
    table[1] = exhibition(table[2])
    return {b: table[b] for b in BRACKETS}, measured


# ----------------------------------------------------------------------------- the metric numbers
def exact(value):
    """A deck's weighted sum as an exact fraction of thousandths, so a percentile that lands on a half is not
    tipped by float error (the sum is rounded to thousandths first: far below the tenths the file keeps)."""
    return Fraction(round(value, 3)).limit_denominator(1000)


def round_tenth(x):
    """A Fraction rounded half up to one decimal: 7.55 becomes 7.6, as round_half_up does for whole numbers."""
    return round_half_up(x * 10) / 10


def summarize_metrics(rows):
    """One bracket's metric numbers from its decks: {"removal_power": [min, target, max], "wipe_power": [...],
    "answers_creatures": [...], ...} in METRIC_ORDER, with the percentiles `summarize` uses (SPREAD). The power sums
    are rounded to a tenth. The answer counts are whole cards, so they round half up to whole numbers like the role
    counts, and a threat in roles.BLUE_THREATS (spells) is counted only over decks whose commander has blue, as
    counterspells are. A row whose power could not be measured ("power" is None) or whose answers could not
    ("answers" is None) is left out of that part."""
    out = {}
    for name in POWER_ORDER:
        pool = [exact(r["power"][name]) for r in rows if r.get("power")]
        out[name] = [round_tenth(percentile(pool, p)) for p in SPREAD] if pool else [0.0, 0.0, 0.0]
    for id_ in ANSWER_ORDER:
        pool = [r["answers"][id_] for r in rows if r.get("answers") and (r["blue"] or id_ not in roles.BLUE_THREATS)]
        out[id_] = [round_half_up(percentile(pool, p)) for p in SPREAD] if pool else [0, 0, 0]
    return out


def interpolate_metrics(low, high, step, of=3):
    """The metric numbers of a bracket `step`/`of` of the way from `low` to `high`, as `interpolate` does for
    the role numbers: the power sums rounded to a tenth, the answer counts to whole numbers (half up). It works
    from the rounded numbers so anyone can check it from the file."""
    def mix(a, b, rounding):
        return rounding(Fraction(str(a)) * (of - step) / of + Fraction(str(b)) * step / of)
    return {name: [mix(a, b, round_half_up if name in ANSWER_ORDER else round_tenth) for a, b in zip(v, high[name])]
            for name, v in low.items()}


def build_metric_table(decks):
    """({bracket: numbers}, {bracket: measured?}) for the metrics from {bracket: [rows]}, exactly as `build_table`
    does for the roles: Brackets 2 and 5 need MIN_DECKS decks with a measured power (the answer counts come from the
    same tags, so such a deck has them too), 3 and 4 are measured when enough decks came in and are otherwise
    interpolated, and Bracket 1 is Bracket 2's numbers."""
    usable = {b: [r for r in rows if r.get("power")] for b, rows in decks.items()}
    for bracket, source in ((2, "MTGJSON precons"), (5, "EDHTop16 top-cut decks")):
        n = len(usable.get(bracket, ()))
        if n < MIN_DECKS:
            raise NotEnoughData(f"Bracket {bracket} needs at least {MIN_DECKS} decks from {source}, got {n}")
    table = {b: summarize_metrics(rows) for b, rows in usable.items() if len(rows) >= MIN_DECKS}
    measured = {b: b in table for b in BRACKETS}
    for b in (3, 4):
        if not measured[b]:
            table[b] = interpolate_metrics(table[2], table[5], *BLEND[b])
    table[1] = {name: list(v) for name, v in table[2].items()}
    return {b: table[b] for b in BRACKETS}, measured


# ----------------------------------------------------------------------------- counting one deck
def split_pair(name):
    """EDHTop16 names a partner pair 'A / B' and a double-faced commander 'A // B': 'Thrasios, Triton Hero /
    Tymna the Weaver' is two commanders (a 98-card deck), 'Ral, Monsoon Mage // Ral, Leyline Prodigy' is
    one."""
    return [part.strip() for part in re.split(r"(?<!/) / (?!/)", name)]


def identity(commanders, db):
    """The commanders' combined color identity as WUBRG letters (a commander the index lacks adds none)."""
    letters = "".join(rec["ci"] for rec in (db.get(c) for c in commanders) if rec)
    return "".join(c for c in "WUBRG" if c in letters)


def _is_land(name, db):
    rec = db.get(name)
    return bool(rec and rec["land"])


def without_commanders(commanders, cards, db):
    """[(count, name)] of `cards` without the commanders (a source may list the commander among the cards)."""
    own = {db.resolve(c) or c for c in commanders}
    return [(n, name) for n, name in cards if (db.resolve(name) or name) not in own]


def deck_counts(commanders, cards, db, role_map):
    """(counts, unknown names) for a deck's 99 cards (98 with two commanders). `cards` is [(count, name)] and
    `counts` is roles.counts output. A commander that also sits among the cards is taken out of them.

    Some sources list each basic land once however many the deck runs (EDHTop16, Archidekt), so a list
    shorter than the deck holds its missing copies as basics: lands = (100 - commanders) - nonland cards. A
    name the card index does not know counts as a nonland card, so a gap in the index can never turn into a
    phantom land."""
    cards = without_commanders(commanders, cards, db)
    counts = roles.counts(cards, role_map, db)
    full = DECK_SIZE - len(commanders)
    if sum(n for n, _ in cards) < full:
        counts["land"] = full - sum(n for n, name in cards if not _is_land(name, db))
    return counts, [name for _, name in cards if db.get(name) is None]


def recent_precons(entries, today):
    """DeckList entries worth sampling, newest release first: already released, one per name (a reprint keeps
    its newest printing, which is the one decklist.precon(name) reads), and no Collector's Edition of a deck
    that is also listed (the same cards, so the deck would count twice). `today` is an ISO date."""
    names = {e["name"] for e in entries}
    out, seen = [], set()
    for e in sorted(entries, key=lambda e: (e.get("releaseDate", ""), e["name"]), reverse=True):
        plain = _TWIN.sub("", e["name"])
        if e.get("releaseDate", "") > today or e["name"] in seen or (plain != e["name"] and plain in names):
            continue
        seen.add(e["name"])
        out.append(e)
    return out


def _today():
    return datetime.date.today()


# ----------------------------------------------------------------------------- reading decks from the sources
class Sampler:
    """Reads decks from a source and turns each into a row {"counts", "blue", "power", "answers"}. Collects what the
    report must mention along the way: warnings, card names the card index lacks, and where the samples came from."""

    def __init__(self, db, refresh, offline, say):
        self.db, self.refresh, self.offline, self.say = db, refresh, offline, say
        self.warnings, self.unknown = [], Counter()
        self.precon_span = None   # (oldest, newest release) of the precons read
        self.tournament = []      # [(commander, top-cut decks read)]

    def row(self, commanders, cards):
        role_map = roles.tag([name for _, name in cards], self.db, refresh=self.refresh, offline=self.offline)
        counts, unknown = deck_counts(commanders, cards, self.db, role_map)
        self.unknown.update(unknown)
        self.unknown.update(c for c in commanders if self.db.get(c) is None)
        power, answers = self.measures(commanders, cards, role_map)
        return {"counts": counts, "blue": "U" in identity(commanders, self.db), "power": power, "answers": answers}

    def measures(self, commanders, cards, role_map):
        """({"removal_power", "wipe_power"}, {threat id: cards that answer it}) of one deck, the first as metrics.py
        weighs the removal cards and the board wipes, the second as it counts "answers to each threat" (roles.
        answer_counts, over the deck's 99 cards, commanders left out). Both are None when the Scryfall function tags
        for card attributes are unavailable (the role numbers do not need them)."""
        names = [name for _, name in without_commanders(commanders, cards, self.db)]
        attrs = roles.attributes(names, self.db, refresh=self.refresh, offline=self.offline)
        if not roles.attributes_loaded():
            return None, None
        raters = {"removal_power": metrics.rate_removal, "wipe_power": metrics.rate_wipes}
        power = {name: sum(value for _, value, _ in rate(names, role_map, attrs, self.db))
                 for name, rate in raters.items()}
        return power, roles.answer_counts(names, attrs)

    def from_precons(self, wanted):
        """Rows for the newest `wanted` precons. One that fails is skipped and the next older one takes its
        place."""
        # decklist._entries is private, but it is the only call that carries release dates (precon_names()
        # is alphabetical), and "the newest precons" needs them
        entries = recent_precons(decklist._entries(self.refresh, self.offline), _today().isoformat())
        rows, released = [], []
        for e in entries:
            if len(rows) >= wanted:
                break
            try:
                deck = decklist.precon(e["name"], refresh=self.refresh, offline=self.offline)
            except (net.FetchError, KeyError) as err:       # KeyError: decklist.UnknownPrecon
                self.warnings.append(f"precon {e['name']!r} skipped: {err}")
                continue
            if not deck["commanders"]:
                self.warnings.append(f"precon {e['name']!r} skipped: no commander listed")
                continue
            rows.append(self.row(deck["commanders"], deck["cards"]))
            released.append(deck["release"] or e.get("releaseDate", ""))
            self.say(f"precons {len(rows)}/{wanted}: {deck['name']}")
        if released:
            self.precon_span = (min(released), max(released))
        return rows

    def from_tournaments(self, commander_count, per_commander):
        """Rows for the top-cut entries among the newest `per_commander` entries of each of the
        `commander_count` most played tournament commanders. A commander whose read fails is skipped."""
        rows = []
        top = edhtop16.top_commanders(MIN_ENTRIES, refresh=self.refresh, offline=self.offline)
        for c in top[:commander_count]:
            try:
                entries = edhtop16.entries(c["name"], limit=per_commander, refresh=self.refresh,
                                           offline=self.offline)
            except net.FetchError as err:
                self.warnings.append(f"EDHTop16 commander {c['name']!r} skipped: {err}")
                continue
            if entries and not any(e["cards"] for e in entries):
                # no entry carries its cards any more, so no commander can add a deck: say why once and stop
                # asking (build_table's "needs at least N decks" error then quotes this warning)
                self.warnings.append(f"Bracket 5 has no tournament decks: {edhtop16.NO_DECKLISTS}")
                break
            commanders = split_pair(c["name"])
            cut = [e for e in entries if e["topcut"]]
            rows += [self.row(commanders, [(1, name) for name in e["cards"]]) for e in cut]
            self.tournament.append((c["name"], len(cut)))
            self.say(f"EDHTop16 {c['name']}: {len(cut)} top-cut decks among {len(entries)} entries")
        return rows

    def from_archidekt(self, bracket, commanders, per_commander):
        """Rows for up to `per_commander` Archidekt decks tagged `bracket` for each commander (a name, or a
        list of names for a pair). A commander whose read fails is skipped."""
        rows = []
        for c in commanders:
            names = [c] if isinstance(c, str) else list(c)
            try:
                found = archidekt.decks(names, bracket, limit=per_commander, refresh=self.refresh,
                                        offline=self.offline)
            except net.FetchError as err:
                self.warnings.append(f"Archidekt commander {' / '.join(names)!r} skipped at Bracket "
                                     f"{bracket}: {err}")
                continue
            rows += [self.row(d["commanders"] or names, [(1, name) for name in d["cards"]]) for d in found]
            self.say(f"Archidekt Bracket {bracket} {' / '.join(names)}: {len(found)} decks")
        return rows


# ----------------------------------------------------------------------------- the report and the file
def read_previous(path):
    """The numbers in the file at `path` as {bracket: {role: ...}}, or {} when it is missing or unreadable."""
    data = net.read_json(path)
    rows = data.get("brackets") if isinstance(data, dict) else None
    if not isinstance(rows, dict):
        return {}
    return {int(b): row for b, row in rows.items() if str(b).isdigit() and isinstance(row, dict)}


def _fmt(v):
    """8/10/13 for a [min, target, max], 8 for a plain number, none for a number the file did not have."""
    if v is None:
        return "none"
    return "/".join(str(x) for x in v) if isinstance(v, list) else str(v)


def changes(previous, brackets):
    """A readable line for every number that moved: 'Bracket 2 ramp: 8/10/13 -> 9/12/15'."""
    return [f"Bracket {b} {role}: {_fmt((previous.get(b) or {}).get(role))} -> {_fmt(new)}"
            for b in sorted(brackets) for role, new in brackets[b].items()
            if (previous.get(b) or {}).get(role) != new]


def _source_notes(samples, measured, sampler, per_commander):
    """(labels for Brackets 2 to 5, the sentences that say what the samples were), shared by the role targets and
    the metric targets, which rest on the same decks."""
    labels = {2: f"measured: {samples[2]} recent precons (precons as a Bracket 2 proxy)",
              5: f"measured: {samples[5]} EDHTop16 top-cut decks"}
    for b in (3, 4):
        labels[b] = (f"measured: {samples[b]} Archidekt decks tagged Bracket {b}" if measured[b]
                     else f"interpolated (judgment): Bracket 2 plus {BLEND[b][0]}/{BLEND[b][1]} of the way "
                          f"to Bracket 5")
    if measured[3] and measured[4]:
        middle = "Brackets 3 and 4 = Archidekt decks tagged with that bracket."
    elif measured[3] or measured[4]:
        got, other = (3, 4) if measured[3] else (4, 3)
        middle = (f"Bracket {got} = Archidekt decks tagged with it; Bracket {other} is interpolated between "
                  f"2 and 5 (judgment).")
    else:
        middle = ("Brackets 3 and 4 = interpolated between 2 and 5, a quarter and half of the way "
                  "(judgment; no Bracket 3 or 4 deck was sampled).")
    span = sampler.precon_span
    released = f" released {span[0]} to {span[1]}" if span else ""
    read = ", ".join(f"{name} ({n})" for name, n in sampler.tournament)
    sentences = [f"Bracket 2 = {samples[2]} MTGJSON Commander precons{released}, precons as a Bracket 2 proxy "
                 f"(Wizards no longer ties Core to precons).",
                 f"Bracket 5 = {samples[5]} EDHTop16 top-cut decks from the newest {per_commander} entries of each "
                 f"of: {read}.",
                 middle]
    return labels, sentences


def describe(samples, measured, sampler, per_commander):
    """(labels, method): one label per bracket saying how its numbers came about, and the method as one
    text."""
    notes, sources = _source_notes(samples, measured, sampler, per_commander)
    labels = {1: "judgment: Bracket 2 values with land target +1 and tutor target 0", **notes}
    method = " ".join([
        "Per deck, the 99 cards (98 with two commanders, commanders left out) are counted by role with "
        "roles.counts; a list that names each basic land once gets its lands recounted as 100 minus "
        "commanders minus nonland cards.",
        "Across a bracket's decks, min = 25th percentile, target = median, max = 90th percentile (lands: "
        "10th, median, 90th; topend, the cap on nonland cards of mana value 6 or more: 75th percentile); "
        "percentiles interpolate linearly between ranked decks and round half up; counterspells use only "
        "decks whose commander has blue."] + sources + [
        "Bracket 1 = Bracket 2 with land target +1 and tutor target 0 (judgment)."])
    return labels, method


def describe_metrics(samples, measured, sampler, per_commander):
    """(labels, method) for the metric numbers, as `describe` makes them for the roles (the decks are the same)."""
    notes, sources = _source_notes(samples, measured, sampler, per_commander)
    labels = {1: "judgment: the same as Bracket 2", **notes}
    tags = "; ".join(f"{roles.THREAT_NOUNS[id_]} = {' or '.join(slugs)}" for id_, _, slugs in roles.THREATS)
    method = " ".join([
        "Per deck, removal power and wipe power are the sums metrics.rate_removal and metrics.rate_wipes give over "
        "the 99 cards (98 with two commanders, commanders left out): a removal card is worth speed x reach x "
        "permanence x cost, times 1.5 if it removes again and again, and a board wipe the same, times 1.5 if it "
        "spares your own side. The weights are judgment calls.",
        "The answers_* counts are the distinct cards among those same cards that carry any Scryfall function tag of "
        f"a kind of threat, as stats counts them (roles.THREATS): {tags}.",
        "Across a bracket's decks, min = 25th percentile, target = median, max = 90th percentile; percentiles "
        "interpolate linearly between ranked decks and round half up to one decimal for the power sums and to whole "
        "numbers for the answer counts; answers to spells use only decks whose commander has blue."] + sources + [
        "Bracket 1 = Bracket 2 (judgment)."])
    return labels, method


def file_data(report):
    """What goes in commander/role_targets.json: the numbers in the format roles.targets reads, plus the notes
    that say where each bracket came from. Bracket keys become strings, as JSON requires."""
    return {"source": "measured by src/mtgcommander/calibrate.py; each bracket's label says whether it was "
                      "measured, interpolated or set by judgment",
            "as_of": report["as_of"], "format": FORMAT, "method": report["method"],
            "samples": {str(b): n for b, n in report["samples"].items()},
            "samples_blue": {str(b): n for b, n in report["samples_blue"].items()},
            "measured": {str(b): m for b, m in report["measured"].items()},
            "labels": {str(b): text for b, text in report["labels"].items()},
            "brackets": {str(b): row for b, row in report["brackets"].items()}}


def dumps(data, per_line=(4,)):
    """The file as text, laid out like the committed one: notes one to a line, then each bracket with four
    roles to a line so the numbers stay easy to scan and a change shows up as a small diff. `per_line` sizes the
    lines of a bracket's block in turn (the last size repeats): METRIC_LINES keeps the two power sums on a line of
    their own, then the answer counts."""
    lines = [f"  {json.dumps(key)}: {json.dumps(value)}" for key, value in data.items() if key != "brackets"]
    blocks = []
    for bracket, row in data["brackets"].items():
        items = [f"{json.dumps(role)}: {json.dumps(v)}" for role, v in row.items()]
        rows, start = [], 0
        while start < len(items):
            size = per_line[min(len(rows), len(per_line) - 1)]
            rows.append("      " + ", ".join(items[start:start + size]))
            start += size
        blocks.append(f'    {json.dumps(bracket)}: {{\n' + ",\n".join(rows) + '\n    }')
    lines.append('  "brackets": {\n' + ",\n".join(blocks) + "\n  }")
    return "{\n" + ",\n".join(lines) + "\n}\n"


def metric_file_data(report):
    """What goes in commander/metric_targets.json: the same notes as the role targets (see `file_data`), for the
    numbers in report["metrics"]."""
    m = report["metrics"]
    return {"source": "measured by src/mtgcommander/calibrate.py from the decks the role targets rest on; each "
                      "bracket's label says whether it was measured, interpolated or set by judgment",
            "as_of": report["as_of"], "format": METRIC_FORMAT, "method": m["method"],
            "samples": {str(b): n for b, n in m["samples"].items()},
            "samples_blue": {str(b): n for b, n in m["samples_blue"].items()},
            "measured": {str(b): v for b, v in m["measured"].items()},
            "labels": {str(b): text for b, text in m["labels"].items()},
            "brackets": {str(b): row for b, row in m["brackets"].items()}}


def _write_text(path, text):
    """Write a file atomically, like net.atomic_json: a crash never leaves half a file for a reader to trip on."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)
    return path


def write_file(report, path=None):
    """Write the report as role_targets.json (to roles.TARGETS_PATH unless `path` is given). Atomic, like
    net.atomic_json, so a crash never leaves half a file for roles.targets to trip on. Returns the path."""
    return _write_text(path or roles.TARGETS_PATH, dumps(file_data(report)))


def write_metric_file(report, path=None):
    """Write report["metrics"] as metric_targets.json (to roles.METRIC_TARGETS_PATH unless `path` is given)."""
    return _write_text(path or roles.METRIC_TARGETS_PATH, dumps(metric_file_data(report), METRIC_LINES))


def _source_names(sources):
    if sources is None:
        sources = config.SOURCES
    return {s.strip() for s in (sources.split(",") if isinstance(sources, str) else sources) if s.strip()}


def _check_tag_data(db, refresh, offline):
    """Load the function tags now. Without them roles come from rules-text patterns, which count
    differently, and targets fitted to that would be wrong for every run that does have the tags. Fail
    before any download."""
    roles.reset()                                   # load again under this run's refresh and offline mode
    mark = len(roles.WARNINGS)
    roles.tag([], db, refresh=refresh, offline=offline)
    problems = roles.WARNINGS[mark:]
    del roles.WARNINGS[mark:]
    if problems:
        raise NotEnoughData("; ".join(problems))


def _check_attribute_data(db, refresh, offline):
    """Load the attribute tags (roles.ATTRIBUTE_TAGS) now. True when they loaded. When they did not, the line the
    load left in roles.WARNINGS is taken back and False comes back: the role targets can still be measured
    without them, the metric targets cannot."""
    mark = len(roles.WARNINGS)
    roles.attributes([], db, refresh=refresh, offline=offline)
    del roles.WARNINGS[mark:]
    return roles.attributes_loaded()


def _metric_report(decks, sampler, per_commander, metrics_path):
    """report["metrics"]: the removal and wipe power numbers and the answer counts in the shape of the role numbers
    (plus "samples_blue", the decks with blue that answers to spells rest on), or None when no deck could be
    measured (the attribute tags were unavailable)."""
    if not any(r.get("power") for rows in decks.values() for r in rows):
        return None
    brackets, measured = build_metric_table(decks)
    samples = {b: len([r for r in decks.get(b, ()) if r.get("power")]) if measured[b] else 0 for b in BRACKETS}
    blue = {b: sum(r["blue"] for r in decks.get(b, ()) if r.get("answers")) if measured[b] else 0 for b in BRACKETS}
    labels, method = describe_metrics(samples, measured, sampler, per_commander)
    previous = read_previous(metrics_path)
    return {"brackets": brackets, "samples": samples, "samples_blue": blue, "measured": measured, "labels": labels,
            "method": method, "previous": previous, "changes": changes(previous, brackets), "written": None}


def run(*, sources=None, precons=60, tournament_commanders=6, entries_per_commander=150,
        archidekt_commanders=None, decks_per_bracket=10, write=False, path=None, metrics_path=None, refresh=None,
        offline=None, progress=None):
    """Sample decks, count roles, and work out the targets. Returns the report:
    {"as_of", "brackets": {b: {role: [min, target, max], ..., "topend": n}}, "samples": {b: decks},
    "samples_blue": {b: decks with blue (the counterspell sample)}, "measured": {b: bool},
    "labels": {b: how it came about}, "method", "previous": the file's numbers before,
    "changes": [str], "warnings": [str], "written": path | None,
    "metrics": the same keys (without warnings) for removal_power, wipe_power and the seven answer counts, with
    "samples_blue" the decks that answers to spells rest on; or None when the attribute tags are unavailable}.

    `sources` is the set of evidence sources a run may use (default config.SOURCES): "edhtop16" for
    Bracket 5 and "archidekt" for Brackets 3 and 4, which are interpolated without it. `precons` is how many
    recent precons stand in for Bracket 2. `tournament_commanders` and `entries_per_commander` size the
    Bracket 5 sample; `decks_per_bracket` is how many Archidekt decks are read per commander at each of
    Brackets 3 and 4. `write=True` replaces the file at `path` (default roles.TARGETS_PATH, also where
    `previous` is read from) and the metric numbers' file at `metrics_path` (default roles.METRIC_TARGETS_PATH, or
    beside `path` when only `path` is given). `progress`, if given, is called with a line of text as each source
    is read. Raises NotEnoughData when Bracket 2 or 5 has too few decks to measure."""
    chosen = _source_names(sources)
    metrics_path = metrics_path or (roles.METRIC_TARGETS_PATH if path is None else
                                    os.path.join(os.path.dirname(os.path.abspath(path)), "metric_targets.json"))
    path = path or roles.TARGETS_PATH
    db = carddb.load(refresh=refresh, offline=offline)
    _check_tag_data(db, refresh, offline)
    _check_attribute_data(db, refresh, offline)
    sampler = Sampler(db, refresh, offline, progress or (lambda line: None))
    decks = {2: sampler.from_precons(precons)}
    if "edhtop16" in chosen:
        decks[5] = sampler.from_tournaments(tournament_commanders, entries_per_commander)
    if "archidekt" in chosen:
        commanders = ARCHIDEKT_COMMANDERS if archidekt_commanders is None else archidekt_commanders
        for b in (3, 4):
            decks[b] = sampler.from_archidekt(b, commanders, decks_per_bracket)
    try:
        brackets, measured = build_table(decks)
    except NotEnoughData as err:             # say why the decks are missing, not only that they are
        raise NotEnoughData("; ".join([str(err)] + sampler.warnings[:5])) from None
    warnings = list(sampler.warnings)
    for b in (3, 4):
        if "archidekt" in chosen and not measured[b]:
            warnings.append(f"Bracket {b}: only {len(decks[b])} Archidekt decks (under {MIN_DECKS}), so it "
                            f"is interpolated")
    samples = {b: len(decks.get(b, ())) if measured[b] else 0 for b in BRACKETS}   # decks the numbers rest on
    blue = {b: sum(r["blue"] for r in decks.get(b, ())) if measured[b] else 0 for b in BRACKETS}
    warnings += [f"Bracket {b}: {blue[b]} of {samples[b]} decks have blue, so its counterspell numbers "
                 f"are thin" for b in BRACKETS if samples[b] and blue[b] < MIN_DECKS]
    if sampler.unknown:
        top = ", ".join(name for name, _ in sampler.unknown.most_common(8))
        warnings.append(f"card names not in the card index were counted as nonland cards "
                        f"({len(sampler.unknown)}): {top}")
    labels, method = describe(samples, measured, sampler, entries_per_commander)
    previous = read_previous(path)
    metric = _metric_report(decks, sampler, entries_per_commander, metrics_path)
    if metric is None:
        warnings.append("Removal and wipe power and the answer counts were not measured: the Scryfall function tags "
                        "for card attributes are unavailable, so commander/metric_targets.json is unchanged.")
    report = {"as_of": _today().isoformat(), "brackets": brackets, "samples": samples, "samples_blue": blue,
              "measured": measured, "labels": labels, "method": method, "previous": previous,
              "changes": changes(previous, brackets), "warnings": warnings, "written": None, "metrics": metric}
    if write:
        report["written"] = write_file(report, path)
        if metric is not None:
            metric["written"] = write_metric_file(report, metrics_path)
    return report


# ----------------------------------------------------------------------------- command line
def format_report(report):
    """The report as plain text: for each bracket, where its numbers came from and every role old -> new."""
    out = [f"Role targets measured {report['as_of']}  (min/target/max; the file's old numbers -> new)"]
    for b in sorted(report["brackets"]):
        out += ["", f"Bracket {b}  {report['labels'][b]}"]
        old = report["previous"].get(b) or {}
        out += [f"  {role:<11}{_fmt(old.get(role)):>11}  ->  {_fmt(report['brackets'][b][role])}"
                for role in ROW_ORDER]
    metric = report.get("metrics")
    if metric:
        out += ["", "Removal and wipe power and answer counts, measured from the same decks (min/target/max; "
                    "old -> new)"]
        for b in sorted(metric["brackets"]):
            old = metric["previous"].get(b) or {}
            out += ["", f"Bracket {b}  {metric['labels'][b]}"]
            out += [f"  {name:<22}{_fmt(old.get(name)):>14}  ->  {_fmt(metric['brackets'][b][name])}"
                    for name in METRIC_ORDER]
    if report["warnings"]:
        out += ["", "Warnings:"] + [f"  {w}" for w in report["warnings"]]
    if report.get("written"):
        out += ["", f"Wrote {report['written']}"]
    if metric and metric.get("written"):
        out += [f"Wrote {metric['written']}"]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="python3 -m mtgcommander.calibrate",
        description="Measure role targets, removal and wipe power, and answers to each kind of threat from real "
                    "decks and propose commander/role_targets.json (nothing is replaced unless --write is given).")
    ap.add_argument("--precons", type=int, default=60, help="recent precons that stand in for Bracket 2")
    ap.add_argument("--tournament-commanders", type=int, default=6, help="most played tournament commanders")
    ap.add_argument("--entries", type=int, default=150, help="newest entries read per tournament commander")
    ap.add_argument("--decks-per-bracket", type=int, default=10,
                    help="Archidekt decks per commander and bracket")
    ap.add_argument("--sources", help="comma-separated evidence sources (default: MTG_COMMANDER_SOURCES); "
                    "'archidekt' measures Brackets 3 and 4 instead of interpolating them")
    ap.add_argument("--out", help="write the proposed role targets here and leave the committed files alone "
                    "(the proposed power and answer numbers are only printed)")
    ap.add_argument("--write", action="store_true",
                    help="replace commander/role_targets.json and commander/metric_targets.json")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--refresh", action="store_true", help="re-download instead of using cached files")
    ap.add_argument("--offline", action="store_true", help="never connect; use cached files only")
    args = ap.parse_args(argv)
    try:
        report = run(sources=args.sources, precons=args.precons,
                     tournament_commanders=args.tournament_commanders, entries_per_commander=args.entries,
                     decks_per_bracket=args.decks_per_bracket, write=args.write,
                     refresh=args.refresh or None, offline=args.offline or None,
                     progress=lambda line: print(line, file=sys.stderr))
        if args.out:
            report["written"] = write_file(report, args.out)
    except net.FetchError as err:
        sys.exit(f"calibrate: {err}")
    print(json.dumps(report, indent=2) if args.json else format_report(report))


if __name__ == "__main__":
    main()
