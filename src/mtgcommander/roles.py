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
every card when the tag data could not be loaded at all)."""
import datetime, json, os, re
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


def tag(names, db, *, refresh=None, offline=None):
    """{name: set of roles} for each distinct name (empty set for a name the card index does not know)."""
    sets = _load_sets(refresh, offline)
    out = {}
    for name in names:
        if name not in out:
            rec = db.get(name)
            out[name] = roles_of(rec, sets) if rec else set()
    return out


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
