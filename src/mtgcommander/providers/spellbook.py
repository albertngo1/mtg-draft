"""Commander Spellbook: combos a decklist has, combos one card away, and the bracket each combo implies.

Why this source: Wizards' brackets limit two-card infinite combos, and finding those by hand is the job
Spellbook already does. `find-my-combos` answers "which combos does this list contain?" and "which would one
more card complete?", and tags every combo with a bracket. The second answer keeps `upgrade` from adding the
missing half of a combo the target bracket does not allow. Please credit Commander Spellbook
(https://commanderspellbook.com) wherever combos are shown; every Combo carries its page URL.

What the API does (OpenAPI schema at /schema/, version 7.1.9, read 2026-10-11):
- POST /find-my-combos {"commanders": [{"card": n}], "main": [{"card": n, "quantity": q}]} answers
  {"count", "next", "previous", "results": {"identity", "included", "almostIncluded", ...}}. A page holds up
  to 1000 variants across all buckets and `next` is the URL of the following page (POST the same body there).
  Only `included` and `almostIncluded` are used: the other buckets need a colour or a commander the deck
  does not have.
- Names match case-insensitively but otherwise exactly. A double-faced card must be written "Front // Back"
  (the Scryfall name); a front-face-only or unknown name is silently ignored, so callers pass canonical names.
- A variant (one combo) has `id` ("3000-4871"), `uses` [{card: {name}, quantity}] (the commander is one of
  them), `requires` [{template: {name}, quantity}] (a non-card need such as "any sacrifice outlet"),
  `produces` [{feature: {name}}] and `bracketTag`. `almostIncluded` is a combo with one piece missing.
- POST /estimate-bracket takes the same body and returns Spellbook's own verdict for the whole list.
"""
import collections, hashlib, json
from .. import net

NAME = "spellbook"
API = "https://backend.commanderspellbook.com"
SITE = "https://commanderspellbook.com"
FIND_URL, ESTIMATE_URL = API + "/find-my-combos", API + "/estimate-bracket"
MAX_PAGES = 5  # 1000 variants a page; a list needing more is a cEDH pile, and page one has the popular combos

# Spellbook tags every combo with the kind of deck it belongs in. Its own words are in the site source
# (SpaceCowMedia/commander-spellbook-site, src/lib/brackets.ts: BRACKET_DESCRIPTION_MAP, BRACKET_FIT_MAP) and
# the backend (spellbook/models/variant.py: BracketTag, the Variant.bracket column, estimate_bracket), read
# 2026-10-11. `lowest` is the lowest bracket the tag can fit (the backend's own Variant.bracket numbers).
# `min_bracket` is the lowest bracket it surely fits (the site's `sure` column). They differ for the two
# borderline tags, and we take the upper end so a deck never lands a bracket too low because of a combo:
# Chatterfang + Pitiless Plunderer is tagged S, and Bracket 3 must block it. `meaning` quotes Spellbook's
# description of the tag, so `check` can say why a combo was blocked.
BRACKET_TAGS = {
    "R": {"label": "Ruthless", "min_bracket": 4, "lowest": 4,
          "meaning": "For competitive decks at brackets 4+"},
    "S": {"label": "Spicy", "min_bracket": 4, "lowest": 3,
          "meaning": "Probably 3 or 4, but hard to classify"},
    "P": {"label": "Powerful", "min_bracket": 3, "lowest": 3,
          "meaning": "For strong decks in bracket 3+"},
    "O": {"label": "Oddball", "min_bracket": 3, "lowest": 2,
          "meaning": "Probably 2 or 3, but hard to classify"},
    "C": {"label": "Core", "min_bracket": 2, "lowest": 2,
          "meaning": "For unoptimized decks in bracket 2+"},
    "E": {"label": "Exhibition", "min_bracket": 1, "lowest": 1,
          "meaning": "For any deck"},
    # Banned cards are illegal in every bracket; 5 is the top of the scale, the nearest an int gets to "never"
    "B": {"label": "Not Legal", "min_bracket": 5, "lowest": None,
          "meaning": "Not legal in any bracket"},
}

# Spellbook's classification of a combo inside a whole-list estimate: (its camelCase key, our snake_case key)
_COMBO_FLAGS = (("relevant", "relevant"), ("borderlineRelevant", "borderline_relevant"),
                ("arguablyTwoCard", "arguably_two_card"), ("definitelyTwoCard", "definitely_two_card"),
                ("speed", "speed"), ("extraTurn", "extra_turn"), ("massLandDenial", "mass_land_denial"),
                ("lock", "lock"), ("skipTurns", "skip_turns"),
                ("controlAllOpponents", "control_all_opponents"),
                ("controlSomeOpponents", "control_some_opponents"))
_CARD_FLAGS = (("banned", "banned"), ("gameChanger", "game_changers"), ("massLandDenial", "mass_land_denial"),
               ("extraTurn", "extra_turns"))


# ---------------------------------------------------------------- pure parsing
def bracket_needed(tag, two_card, infinite):
    """The lowest bracket that allows a combo with this tag. A tag we do not know (or none) falls back to the
    Wizards rule of thumb: a two-card infinite combo needs Bracket 4, anything else fits anywhere."""
    known = BRACKET_TAGS.get(tag)
    if known:
        return known["min_bracket"]
    return 4 if two_card and infinite else 1


def parse_combo(variant, have=None):
    """One Spellbook variant → a Combo. `have` is the casefolded set of the deck's card names; with it,
    `missing` lists the combo's cards the deck lacks (always empty for a combo that is already included)."""
    uses, requires = variant.get("uses") or [], variant.get("requires") or []
    cards = [u["card"]["name"] for u in uses if u.get("card")]
    templates = [t["template"]["name"] for t in requires if t.get("template")]
    produces = [p["feature"]["name"] for p in variant.get("produces") or [] if p.get("feature")]
    # A template is a need the deck must meet too, so "two cards + a template" is a three-piece combo
    pieces = sum(u.get("quantity") or 1 for u in uses) + sum(t.get("quantity") or 1 for t in requires)
    two_card, infinite = pieces == 2, any("infinite" in p.lower() for p in produces)
    tag = variant.get("bracketTag") or None
    return {"id": str(variant.get("id", "")), "cards": cards, "requires": templates,
            "missing": [] if have is None else [n for n in cards if n.casefold() not in have],
            "produces": produces, "bracket_tag": tag, "min_bracket": bracket_needed(tag, two_card, infinite),
            "two_card": two_card, "infinite": infinite, "url": f"{SITE}/combo/{variant.get('id', '')}/"}


def parse_results(results, deck_names):
    """{"included": [Combo], "almost": [Combo]} from the `results` object of one find-my-combos page."""
    have = {n.casefold() for n in deck_names}
    return {"included": [parse_combo(v) for v in results.get("included") or []],
            "almost": [parse_combo(v, have) for v in results.get("almostIncluded") or []]}


def parse_estimate(payload):
    """Spellbook's verdict on a whole list: {"tag", "label", "min_bracket", "lowest", "meaning", "banned",
    "game_changers", "mass_land_denial", "extra_turns", "combos"}. Each combo is a Combo plus Spellbook's own
    classification of it (speed, relevant, definitely_two_card, lock, ...)."""
    tag = payload.get("bracketTag")
    known = BRACKET_TAGS.get(tag, {})
    out = {"tag": tag, "label": known.get("label"), "min_bracket": known.get("min_bracket"),
           "lowest": known.get("lowest"), "meaning": known.get("meaning")}
    for theirs, ours in _CARD_FLAGS:
        out[ours] = [c["card"]["name"] for c in payload.get("cards") or [] if c.get(theirs)]
    out["combos"] = []
    for classified in payload.get("combos") or []:
        combo = parse_combo(classified.get("combo") or {})
        combo.update({ours: classified.get(theirs) for theirs, ours in _COMBO_FLAGS})
        out["combos"].append(combo)
    return out


# ---------------------------------------------------------------- network
def _deck_body(commanders, cards):
    """The request body. Repeated names (basic lands) become a quantity; the order is fixed so it hashes the
    same whatever order the caller listed the cards in."""
    copies = collections.Counter(cards)
    return {"commanders": [{"card": n} for n in sorted(commanders)],
            "main": [{"card": n, "quantity": q} if q > 1 else {"card": n} for n, q in sorted(copies.items())]}


def _digest(body):
    return hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def _merge_info(infos):
    """One fetched time and cache state for a read of several pages: the oldest page, the worst state."""
    states = {i["cache"] for i in infos}
    return {"fetched": min(i["fetched"] for i in infos),
            "cache": "stale" if "stale" in states else "network" if "network" in states else "fresh"}


def find_combos(commanders, cards, *, refresh=None, offline=None):
    """Combos in this list and combos one card away:
    {"included": [Combo], "almost": [Combo], "fetched": ISO, "cache": "fresh" | "network" | "stale"}.
    `cards` are the deck's other cards by canonical name (a double-faced card as "Front // Back"). Cached
    under a hash of the sorted names; the body is too long to serve as a URL key."""
    body = _deck_body(commanders, cards)
    base, deck_names = _digest(body), list(commanders) + list(cards)
    found, infos, url = {"included": [], "almost": []}, [], FIND_URL
    for page in range(MAX_PAGES):
        payload, info = net.fetch_json(url, source=NAME, key=f"combos-{base}-{page}", data=body,
                                       refresh=refresh, offline=offline)
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, dict):
            raise net.FetchError(NAME, url, "the answer has no `results` object (the API may have changed)")
        infos.append(info)
        part = parse_results(results, deck_names)
        found["included"] += part["included"]
        found["almost"] += part["almost"]
        url = payload.get("next")
        if not url or not url.startswith(API + "/"):
            break
    found.update(_merge_info(infos))
    return found


def estimate_bracket(commanders, cards, *, refresh=None, offline=None):
    """Spellbook's own bracket estimate for the list (see parse_estimate); None if the endpoint is gone."""
    body = _deck_body(commanders, cards)
    try:
        payload, info = net.fetch_json(ESTIMATE_URL, source=NAME, key=f"estimate-{_digest(body)}", data=body,
                                       refresh=refresh, offline=offline)
    except net.NotFound:
        return None
    if not isinstance(payload, dict) or "bracketTag" not in payload:
        raise net.FetchError(NAME, ESTIMATE_URL, "the answer has no `bracketTag` (the API may have changed)")
    return dict(parse_estimate(payload), fetched=info["fetched"], cache=info["cache"])
