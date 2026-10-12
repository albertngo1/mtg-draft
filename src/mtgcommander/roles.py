"""What each card does for a deck (ramp, draw, removal, ...) and how many of each a bracket expects.

A role is a job a deck needs filled in numbers: enough mana, enough cards, enough answers. The scorer values a
card more while its role is short, so this module answers two questions: which roles does a card fill (`tag`),
and what counts does a bracket ask for (`targets`).

Roles come from Scryfall's function tags (providers/scryfall_tags.py). The tag sets below were chosen by
running candidates over 60 recent Commander precons and over lists of well-known cards for each role. Result
with these sets (Oct 2026): 148 of 153 well-known cards found, and the average precon holds 12 ramp (10 spells
and mana rocks, 2 lands), 11 draw, 10 removal, 3.5 wipes, 3.6 recursion, 3 protection, 2.5 finishers, 0.5
counters and 0.4 tutors. That is a little above the Bracket 2 starting values in commander/role_targets.json,
as expected for decks built to be played out of the box; recalibrate both together when either changes.

Rules-text patterns are a fallback for cards Scryfall's volunteers have not tagged yet. Almost every older
card carries some tag, and a pattern fires on ~10% of cards the volunteers deliberately left out of a role,
so the fallback runs only for cards released in the last NEW_CARD_DAYS days that have no role tag (or for
every card when the tag data could not be loaded at all).

A card can also need something from the deck rather than fill a job in it: Cultivate and Evolving Wilds take
basic lands out of the library, and find nothing if the deck has none left. `basic_land_searches` counts how
many, so `upgrade` and `build` can keep enough basics in the list.

Finer facts about a card (how far its removal reaches, whether a land enters tapped, whether it can end the game)
come from a second set of tags, ATTRIBUTE_TAGS, through `attributes`. It is its own `scryfall_tags.load` call:
if those tags cannot be had, the roles above still work and only the metrics that need them go without."""
import collections, datetime, json, os, re
from . import config, net
from .providers import scryfall_tags

ROLES = ("ramp", "draw", "removal", "wipe", "counter", "protection", "recursion", "tutor", "finisher")
LABELS = {"ramp": "ramp", "draw": "draw", "removal": "removal", "wipe": "wipes", "counter": "counters",
          "protection": "protection", "recursion": "recursion", "tutor": "tutors", "finisher": "finishers"}
# Roles whose value does not depend on the rest of the deck, so a tournament win-rate gap for them carries
# over to casual tables (see score.py). A finisher or a recursion spell is worth what the deck makes of it.
CARRYOVER = {"ramp", "draw", "removal", "wipe", "counter", "protection", "tutor"}

# Scryfall function-tag slugs per role. A slug stands for its whole subtree (like `otag:` search does).
ROLE_TAGS = {
    "ramp": ["mana-rock", "mana-dork", "land-ramp", "extra-land", "mana-increaser"],
    "draw": ["pure-draw", "burst-draw", "draw-engine", "impulsive-draw", "repeatable-impulsive-draw",
             "life-for-cards"],
    "removal": ["removal"],
    "wipe": ["sweeper"],
    "counter": ["counterspell"],
    "protection": ["protection"],
    "recursion": ["regrowth", "reanimate"],
    "tutor": ["tutor"],
    "finisher": ["overrun", "extra-combat-phase", "alternate-win-condition", "burn-player-each", "drain-life",
                 "opponent-loses-life", "theft-mass"],
}
# Cards to take out of one tag's set before the role is assembled, keyed by (role, tag):
TAG_MINUS = {
    # A card that merely replaces itself is not card advantage: cantrips, and mana rocks or ramp spells with a
    # draw rider (Mind Stone, Commander's Sphere, Explore). Real draw engines keep their own tags.
    ("draw", "pure-draw"): ["cantrip", "mana-rock", "mana-dork", "land-ramp"],
    ("removal", "removal"): ["sweeper"],            # wipes are their own role; twice would inflate both
    ("recursion", "reanimate"): ["reanimate-self"],  # a creature that returns itself is not a recursion spell
    ("tutor", "tutor"): ["tutor-land"],              # fetching a basic land is ramp, not a tutor
}
# Lands get no role except ramp. Scryfall tags the lands that make extra mana (Ancient Tomb, Cabal Coffers,
# Gaea's Cradle) with the bare `ramp` tag, which for spells and creatures is too broad (it includes treasure).
LAND_RAMP_TAGS = ["ramp"]

# Scryfall function-tag slugs for facts about a card that are not one of the nine roles: how removal reaches and
# removes, which answers a deck holds, what kind of ramp and draw, which lands enter tapped, how a deck can win,
# and the signals each playstyle is read from. A slug stands for its whole subtree, as in ROLE_TAGS. metrics.py
# reads them; they load in their own scryfall_tags call (see `attributes`), so an old tag cache that lacks them
# never takes the roles down with it.
ATTRIBUTE_TAGS = (
    # what a removal spell can hit (its reach) and how it removes (its permanence): metrics.removal_quality
    "removal-permanent", "removal-nonland", "removal-creature", "removal-artifact", "removal-enchantment",
    "removal-planeswalker", "removal-land", "removal-burn", "removal-toughness", "doom-blade", "removal-exile",
    "removal-destroy", "removal-bounce", "repeatable-removal", "spot-removal", "multi-removal", "sweeper",
    "sweeper-one-sided",
    # other answers and protection
    "counterspell", "hate-graveyard", "protects-creature", "gives-indestructible", "gives-hexproof",
    # ramp and draw by kind
    "mana-rock", "mana-dork", "land-ramp", "extra-land", "draw-engine", "repeatable-impulsive-draw", "pure-draw",
    "burst-draw", "impulsive-draw",
    # lands that enter tapped, always or only sometimes
    "tapland", "conditional-tapland",
    # how a deck ends the game, and creatures that are hard to block
    "overrun", "extra-combat-phase", "alternate-win-condition", "burn-player-each", "drain-life",
    "opponent-loses-life", "theft-mass", "evasion",
    # the signals of each playstyle (metrics.PLAYSTYLE_SIGNALS)
    "repeatable-token-generator", "sacrifice-outlet", "free-sacrifice-outlet", "death-trigger", "graveyard-fuel",
    "cards-in-graveyard-matter", "synergy-equipment", "synergy-aura", "group-hug", "voting", "monarch-matters",
    "tax", "lockdown", "hatebear",
)

NEW_CARD_DAYS = 180
WARNINGS = []              # non-fatal problems (tag data unavailable); callers print and clear them
_MEMO = {}

# Text fallback, matched against lower-cased rules text.
_TEXT = {
    "ramp": [r"\{t\}[^:.]*: add ",
             r"search your library for (a|an|up to \w+|two|three) (basic )?(\w+ )?(land|forest|island|swamp|"
             r"mountain|plains)s?( cards?)?\b[^.]*onto the battlefield",
             r"you may play an additional land",
             r"put (a|up to \w+) (basic )?land cards? from your hand onto the battlefield"],
    "draw": [r"\bdraws? (a|an|one|two|three|four|five|x|that many|seven|\d+) (additional )?cards?\b",
             r"\bdraw cards equal to\b",
             r"exile the top (card|\w+ cards) of your library[^.]*you may (play|cast)"],
    "removal": [r"\b(destroy|exile) (up to \w+ )?target\b",
                r"deals? (\d+|x) damage to (any target|target creature|target planeswalker|up to)",
                r"target creature gets -\d+/-\d+|target creature gets -x/-x",
                r"\bfights? (target|another)",
                r"return target (nonland )?(permanent|creature|artifact|enchantment)[^.]* to its "
                r"owner's hand",
                r"target (player|opponent) sacrifices a creature"],
    "wipe": [r"\b(destroy|exile) all (\w+ )?(creatures|nonland permanents|permanents|artifacts|enchantments)",
             r"deals? (\d+|x) damage to each (other )?creature",
             r"(all|each) creatures? (get|gets) -\d+/-\d+",
             r"return all (nonland )?(permanents|creatures)[^.]* to their owners' hands",
             r"each player sacrifices (all|every)"],
    "counter": [r"\bcounter target [\w ]*?(spell|ability)\b"],
    "protection": [r"(creatures?|permanents?|artifacts?|planeswalkers?) you control (gain|gains|have|has) "
                   r"(hexproof|indestructible|shroud|protection from|ward)",
                   r"target (creature|permanent|artifact|planeswalker)[^.]* (gains|gain|has|have) "
                   r"(hexproof|indestructible|shroud|protection from)",
                   r"\bphases? out\b",
                   r"you (gain|have) (hexproof|shroud)"],
    "recursion": [r"return (up to \w+ )?(target )?(\w+ )*cards? [^.]*from (your|a|an opponent's|any) "
                  r"graveyard (to|onto)",
                  r"(put|return) [^.]*\bfrom (your|a|your opponent's|an opponent's|any) graveyard onto the "
                  r"battlefield",
                  r"return all [^.]*cards? from (your|a|each) graveyard"],
    "tutor": [r"search your library for (?!(a|an|up to \w+|two|three|x) (basic |snow |snow-covered )?"
              r"(land|forest|island|swamp|mountain|plains|wastes)\b)"],
    "finisher": [r"creatures you control get \+\d+/\+\d+[^.]*until end of turn",
                 r"each opponent loses",
                 r"additional combat phase",
                 r"you win the game"],
}
TEXT_PATTERNS = {role: re.compile("|".join(f"(?:{p})" for p in pats)) for role, pats in _TEXT.items()}
# A land that taps for two or more mana (Ancient Tomb, a bounce land) or for mana per permanent. The tap must
# be the whole cost (plus sacrificing or paying life): a filter land's "{1}, {T}: Add {B}{G}" only converts.
_BIG_LAND = re.compile(r"(?:^|[.)] )\{t\}(?:, (?:sacrifice [^:.]*|pay \d+ life))?: add "
                       r"(?:(?:\{[wubrgc]\}){2,}|[^.]* for each)")
# One search of your own library, up to the word "card(s)": group 1 is "up to two basic land" in "search your
# library for up to two basic land cards". Only "your library" matches, so Path to Exile's "its controller may
# search their library" is left out. The first words of that phrase ("up to two", "a", "X") say how many.
_LIBRARY_SEARCH = re.compile(r"search your library for ([^.:;]*?)\bcards?\b")
_BASIC = re.compile(r"\bbasic\b")
_LAND_WORD = re.compile(r"\b(?:land|plains|island|swamp|mountain|forest)s?\b")   # a land, or one of the land types
_HOW_MANY_FIRST = re.compile(r"(?:up to )?(a|an|one|two|three|x|that many)\b")
_HOW_MANY = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "x": 2, "that many": 2}

TARGETS_PATH = os.path.join(config.COMMITTED, "role_targets.json")
PLAYSTYLES_PATH = os.path.join(config.COMMITTED, "playstyles.json")


def all_slugs():
    """Every tag slug roles.py needs from the tag data (so scryfall_tags caches exactly these)."""
    slugs = {s for ss in ROLE_TAGS.values() for s in ss} | set(LAND_RAMP_TAGS)
    slugs |= {m for ms in TAG_MINUS.values() for m in ms}
    return sorted(slugs)


def role_sets(tagsets):
    """({role: set of oracle ids}, set of oracle ids of lands that ramp) from {slug: set of oracle ids}."""
    ids = {}
    for role, slugs in ROLE_TAGS.items():
        ids[role] = set()
        for slug in slugs:
            part = set(tagsets.get(slug, ()))
            for minus in TAG_MINUS.get((role, slug), ()):
                part -= tagsets.get(minus, set())
            ids[role] |= part
    land_ramp = set().union(*(tagsets.get(s, set()) for s in LAND_RAMP_TAGS))
    return ids, land_ramp


def reset():
    """Forget the loaded tag sets (tests, and a long-running process after `warm`)."""
    _MEMO.clear()


def _load_sets(refresh, offline):
    """Role sets from the tag data, loaded once per process; None when the tag data is unavailable."""
    if "sets" not in _MEMO:
        try:
            _MEMO["sets"] = role_sets(scryfall_tags.load(all_slugs(), refresh=refresh, offline=offline))
        except net.FetchError as e:
            WARNINGS.append(f"roles: Scryfall function tags unavailable, so roles come from rules-text "
                            f"patterns only ({e})")
            _MEMO["sets"] = None
    return _MEMO["sets"]


def _today():
    return datetime.date.today()


def _is_new(rec):
    released = rec.get("released") or ""
    return bool(released) and released >= (_today() - datetime.timedelta(days=NEW_CARD_DAYS)).isoformat()


def text_roles(rec):
    """Roles suggested by rules text alone (the fallback). A modal DFC's land back is ignored so the card is
    not called ramp for its land face; a land only ever gets ramp, for tapping for more than one mana."""
    text = rec["text"].split(" // ")[0] if rec["mdfc_land"] else rec["text"]
    text = text.lower()
    if rec["land"]:
        return {"ramp"} if _BIG_LAND.search(text) else set()
    return {role for role, pat in TEXT_PATTERNS.items() if pat.search(text)}


def roles_of(rec, sets):
    """The roles of one card record. `sets` is role_sets() output, or None when tag data is unavailable."""
    if sets is None:
        return text_roles(rec)
    ids, land_ramp = sets
    oid = rec["oracle_id"]
    if rec["land"]:
        return {"ramp"} if (oid in land_ramp or _BIG_LAND.search(rec["text"].lower())) else set()
    roles = {role for role, members in ids.items() if oid in members}
    if not roles and _is_new(rec):
        roles = text_roles(rec)
    return roles


def basic_land_searches(rec):
    """How many basic lands one copy of a card can take out of your library: every "search your library for
    ... basic ... card(s)" in its rules text, added up. Cultivate is 2, Evolving Wilds 1, Land Tax 3. "A", "an"
    and "one" mean 1, "two" and "three" mean 2 and 3 (also after "up to"), and "X" or "that many" is taken as 2;
    any other wording of a basic-land search still counts 1.

    Only a search for a basic land counts, and only in your own library. Three kinds of search are 0:
    - another player's search ("its controller may search their library", Path to Exile, Assassin's Trophy);
    - a search for any land or any card ("a land card", "a card": Expedition Map, Demonic Tutor);
    - a search for a land type without the word "basic" ("a Forest card", "a Swamp or Forest card"). That can
      fetch a dual land that carries the type (Overgrown Tomb is a Swamp Forest), so it needs no basic to be
      left. Counting it would force extra basics into a deck full of fetch lands, such as a cEDH list."""
    total = 0
    for found in _LIBRARY_SEARCH.finditer(rec["text"].lower()):
        target = found.group(1)
        if _BASIC.search(target):
            how_many = _HOW_MANY_FIRST.match(target)
            total += _HOW_MANY[how_many.group(1)] if how_many else 1
    return total


def searches_library_for_land(rec):
    """Whether the card searches your own library for a land: a fetch land ("a Swamp or Forest card"),
    Evolving Wilds ("a basic land card"), Myriad Landscape. Unlike `basic_land_searches` it counts a search by
    land type and counts no number of lands: it answers whether the card finds colored lands for you. A search
    for something else (Urza's Saga looks for an artifact) and another player's search do not count."""
    return any(_LAND_WORD.search(found.group(1)) for found in _LIBRARY_SEARCH.finditer(rec["text"].lower()))


def tag(names, db, *, refresh=None, offline=None):
    """{name: set of roles} for each distinct name (empty set for a name the card index does not know)."""
    sets = _load_sets(refresh, offline)
    out = {}
    for name in names:
        if name not in out:
            rec = db.get(name)
            out[name] = roles_of(rec, sets) if rec else set()
    return out


def _load_attribute_sets(refresh, offline):
    """{oracle id: frozenset of ATTRIBUTE_TAGS slugs}, loaded once per process; None when the tag data is
    unavailable. Inverted from the per-slug sets once, so each card is a single lookup afterwards."""
    if "attributes" not in _MEMO:
        try:
            by_slug = scryfall_tags.load(ATTRIBUTE_TAGS, refresh=refresh, offline=offline)
        except net.FetchError as e:
            WARNINGS.append(f"roles: Scryfall function tags for card attributes unavailable, so the removal, "
                            f"mana, land and playstyle counts that need them are not shown ({e})")
            _MEMO["attributes"] = None
        else:
            held = collections.defaultdict(list)
            for slug, ids in by_slug.items():
                for oid in ids:
                    held[oid].append(slug)
            _MEMO["attributes"] = {oid: frozenset(slugs) for oid, slugs in held.items()}
    return _MEMO["attributes"]


def attributes(names, db, *, refresh=None, offline=None):
    """{name: frozenset of ATTRIBUTE_TAGS slugs the card carries} for each distinct name (an empty set for a name
    the card index does not know). This is a separate scryfall_tags call from the one the roles use, so a tag
    cache from before these slugs existed still serves the roles offline. When the tag data cannot be had, every
    set is empty and a line is added to WARNINGS; `attributes_loaded` tells that apart from cards that simply
    carry none of the tags."""
    held = _load_attribute_sets(refresh, offline) or {}
    out = {}
    for name in names:
        if name not in out:
            rec = db.get(name)
            out[name] = held.get(rec["oracle_id"], frozenset()) if rec else frozenset()
    return out


def attributes_loaded():
    """True once `attributes` has read the tag data, False after a failed read or before the first call."""
    return _MEMO.get("attributes") is not None


def counts(names, role_map, db):
    """Counts for a list of cards: {"land": n, "mdfc_land": n, <role>: n, ..., "topend": n}.
    `names` holds one entry per copy (nine Forests are nine entries) or (count, name) pairs. A card counts
    once per role it fills; topend is nonland cards with mana value 6 or more. Unknown names are skipped."""
    out = dict.fromkeys(("land", "mdfc_land") + ROLES + ("topend",), 0)
    for item in names:
        n, name = item if isinstance(item, tuple) else (1, item)
        rec = db.get(name)
        if rec is None:
            continue
        if rec["land"]:
            out["land"] += n
        if rec["mdfc_land"]:
            out["mdfc_land"] += n
        for role in role_map.get(name) or role_map.get(rec["name"]) or ():
            out[role] += n
        if not rec["land"] and rec["cmc"] >= 6:
            out["topend"] += n
    return out


def _read_targets():
    """role_targets.json ships with the package, so a missing or damaged copy is an error."""
    with open(TARGETS_PATH) as f:
        return json.load(f)


def _read_playstyles():
    """{playstyle slug: entry} from playstyles.json; empty when the file is absent or unreadable, so targets
    still work (without adjustments) while that file is being written."""
    data = net.read_json(PLAYSTYLES_PATH)
    return (data.get("playstyles") or {}) if isinstance(data, dict) else {}


def targets(bracket, playstyle="value", *, avg_lands=None, ci=None):
    """What a deck at `bracket` should hold:
    {"land": {"min","target","max"}, <role>: {...}, "topend": {"max"}}.
    Starts from commander/role_targets.json and shifts min, target and max of each role by the playstyle's
    integer delta from commander/playstyles.json (an unknown playstyle or a missing file changes nothing).
    With `avg_lands` (EDHREC's average land count for this commander) the land target becomes the rounded
    mean of that and the adjusted bracket target, kept inside the min and max. Without blue in `ci` the
    counterspell min and target drop to 0, since there is little to count."""
    row = _read_targets()["brackets"][str(min(max(int(bracket), 1), 5))]
    out = {role: {"min": v[0], "target": v[1], "max": v[2]} for role, v in row.items() if role != "topend"}
    out["topend"] = {"max": row["topend"]}
    deltas = (_read_playstyles().get(playstyle) or {}).get("targets") or {}
    for role, delta in deltas.items():
        if role in out and isinstance(delta, int):
            out[role] = {k: max(0, v + delta) for k, v in out[role].items()}
    if avg_lands is not None:
        land = out["land"]
        land["target"] = min(max(int((land["target"] + avg_lands) / 2 + 0.5), land["min"]), land["max"])
    if ci is not None and "U" not in ci:
        out["counter"]["min"] = out["counter"]["target"] = 0
    return out
