"""EDHREC provider: what Commander deck builders chose, per commander, per bracket and per theme.

Why EDHREC comes first: one JSON page lists a commander's whole card pool with inclusion counts for a bracket,
where Archidekt needs a request per deck. The pages are the unofficial files EDHREC's own site reads, so the
parsers tolerate missing fields, and a page that lacks the card-list structure altogether raises FetchError
("the site may have changed its format") instead of quietly returning nothing.

Page addresses (verified 2026-10-11), all under https://json.edhrec.com/pages/:
  commanders/<slug>.json                     all brackets pooled
  commanders/<slug>/<bracket>.json           exhibition | core | upgraded | optimized | cedh  (Brackets 1-5)
  commanders/<slug>/<theme>.json             this commander's decks tagged with the theme
  commanders/<slug>/<bracket>/<theme>.json   both at once (bracket first; <theme>/<bracket> does not exist)
  tags/<theme>.json                          the theme across all commanders: top commanders and card lists
  top/salt.json                              the 100 saltiest cards
A missing page answers 403 (net turns that into NotFound). A page asked for under a non-canonical address
answers 200 with {"redirect": "/commanders/<canonical>"} instead, for example a partner pair in the other
order; _page follows it.

Quirks the other modules should know:
- A commander page lists every card played in at least about 5% of its decks (the creatures list stops at the
  top 50, about 10%). A card missing from the page is therefore below that line, not unknown.
- `potential_decks` is the number of decks that could have run the card (a new card counts only decks built
  since its release), so inclusion is num_decks / potential_decks, not num_decks / the page's deck count.
- On a commander's bracket page `bracket_counts` still describes ALL its decks; on a theme page it describes
  the theme's decks. On a theme INDEX page (tags/) a commander's `potential_decks` is the theme's deck count
  across the whole site (about 70,000 for Aristocrats; fewer for a recent commander, which counts only decks
  built since its release), never that commander's own decks.
- Basic lands are listed like any other card. A modal double-faced card sits in two lists, with the same
  numbers in both.

Cards are named as EDHREC spells them (front face only for double-faced cards); score.gather canonicalizes."""
import re, unicodedata
from .. import net

NAME = "edhrec"
KIND = "builder"
BASE = "https://json.edhrec.com/pages/"
SITE = "https://edhrec.com"                  # the human pages, for links in reports
BRACKET_SLUGS = {1: "exhibition", 2: "core", 3: "upgraded", 4: "optimized", 5: "cedh"}
COMMANDER_LISTS = ("topcommanders", "newcommanders")   # the lists on a theme index page that hold commanders
AVG_TYPES = ("creature", "instant", "sorcery", "artifact", "enchantment", "battle", "planeswalker",
             "land", "basic", "nonbasic")    # a commander page's average card count per type, over its decks
MAX_REDIRECTS = 2
_PAGE_PATH = re.compile(r"(commanders|tags)(/[a-z0-9-]+)+")   # the only kind of redirect target we follow


# ---------------------------------------------------------------- addresses
def slug(name):
    """EDHREC's page slug for a card name: 'Lim-Dûl the Necromancer' -> 'lim-dul-the-necromancer'.
    Accents fold to ASCII, apostrophes vanish, every other run of punctuation becomes one hyphen. A
    double-faced or adventure commander uses its front face only ('Esika, God of the Tree // The Prismatic
    Bridge' -> 'esika-god-of-the-tree'); EDHREC has no page for the pair of faces."""
    front = unicodedata.normalize("NFKD", name.split("//")[0]).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"['\u2018\u2019`]", "", front)).strip("-")


def commander_slug(commanders):
    """Slug of one commander's page, or of a pair's combined page (partners, or a commander and a Background).
    Partners are joined alphabetically ('kraum-ludevics-opus-tymna-the-weaver'; Pako + Haldan gives
    'haldan-avid-arcanist-pako-arcane-retriever'). A Background goes last instead ('wilson-refined-grizzly-
    master-chef'), which names alone cannot show, so that pair's first request lands on a redirect that
    _page follows."""
    names = [commanders] if isinstance(commanders, str) else commanders
    return "-".join(sorted(slug(c) for c in names))


def theme_slug(theme):
    """EDHREC's slug for a theme, given the slug itself or its label: '+1/+1 Counters' ->
    'plus-1-plus-1-counters', 'Tap / Untap' -> 'tap-untap'. Reproduces 409 of the 410 labels on EDHREC's
    theme list; the exception is the plural 'Miracles' (slug 'miracle'), which only the slug form reaches."""
    t = theme.strip()
    if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", t):
        return t
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower().replace("'", "")
    t = re.sub(r"(^|[\s/])-(?=\d)", r"\1 minus ", t.replace("+", " plus "))   # '-1/-1' -> 'minus 1/ minus 1'
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def _bracket_slug(bracket):
    if bracket not in BRACKET_SLUGS:
        raise ValueError(f"bracket must be 1-5, got {bracket!r}")
    return BRACKET_SLUGS[bracket]


def _page(path, *, refresh=None, offline=None):
    """(payload, info) for pages/<path>.json, or (None, None) when EDHREC has no such page. Follows the
    redirect note a non-canonical address answers with, at most MAX_REDIRECTS times, and only to a page of a
    known kind. A page that exists but has no card lists means the site changed its layout: FetchError."""
    for _ in range(MAX_REDIRECTS + 1):
        try:
            payload, info = net.fetch_json(f"{BASE}{path}.json", source=NAME, key=path.replace("/", "__"),
                                           refresh=refresh, offline=offline)
        except net.NotFound:
            return None, None
        target = payload.get("redirect") if isinstance(payload, dict) else None
        if not target:
            jd = _json_dict(payload)
            if "cardlists" not in jd:
                if jd.get("card"):                            # a real page with too few decks to list cards
                    return None, None                          # (Ms. Bumbleflower + food: 3 decks)
                raise net.FetchError(NAME, info["url"],
                                     "the page has no card lists (EDHREC may have changed its format)")
            return payload, info
        path = re.sub(r"\.json$", "", str(target).strip("/"))
        if not _PAGE_PATH.fullmatch(path):
            return None, None
    return None, None


# ---------------------------------------------------------------- parsing (pure; tests feed these dicts)
def _json_dict(page):
    return ((page.get("container") or {}).get("json_dict") or {}) if isinstance(page, dict) else {}


def _wubrg(letters):
    return "".join(c for c in "WUBRG" if c in letters)


def parse_cards(page, skip=()):
    """Builder stats for every card on a commander or theme page: {name: {"decks", "of", "synergy"}}.
    `skip` names lists to leave out (a theme index page keeps its commanders in two). A card can sit in
    several lists (a modal double-faced card is both a spell and a land) with the same numbers; the first
    sighting wins."""
    cards = {}
    for lst in _json_dict(page).get("cardlists") or []:
        if lst.get("tag") in skip:
            continue
        for cv in lst.get("cardviews") or []:
            name, decks, of = cv.get("name"), cv.get("num_decks"), cv.get("potential_decks")
            if not name or name in cards or decks is None or not of:
                continue
            cards[name] = {"decks": int(decks), "of": int(of), "synergy": cv.get("synergy")}
    return cards


def parse_meta(page, info=None):
    """The commander_meta record for one commander (or commander-and-theme) page."""
    card = _json_dict(page).get("card") or {}
    panels = page.get("panels") or {}
    tags = panels.get("taglinks") or page.get("tag_counts") or []
    counts = page.get("bracket_counts") or {}
    return {
        "n_decks": int(card.get("num_decks") or 0),
        "bracket_counts": {int(k): v for k, v in counts.items() if str(k).isdigit()},
        "taglinks": [{"slug": t["slug"], "label": t.get("value", t["slug"]), "count": t.get("count", 0)}
                     for t in tags if t.get("slug")],
        "avg_types": {k: page[k] for k in AVG_TYPES if isinstance(page.get(k), (int, float))},
        "mana_curve": {int(k): v for k, v in (panels.get("mana_curve") or {}).items() if str(k).isdigit()},
        "salt": card.get("salt"),
        "similar": [s for s in page.get("similar") or [] if isinstance(s, str)],
        "combos": [c["value"] for c in panels.get("combocounts") or [] if c.get("value")],
        "ci": _wubrg(card.get("color_identity") or []),
        "url": (info or {}).get("url", ""),
        "fetched": (info or {}).get("fetched", ""),
    }


def parse_theme_commanders(page):
    """Commanders on a theme index page, top then new, each once:
    {"name", "decks", "of", "theme_total", "url"}. `decks` is how many of that commander's decks carry the
    theme. `of` is None: the index does not give the commander's own deck count (commander_meta(name)
    ["n_decks"] does). `theme_total` is what the index calls potential_decks, the theme's deck count across
    the whole site."""
    lists = {lst.get("tag"): lst for lst in _json_dict(page).get("cardlists") or []}
    out, seen = [], set()
    for tag in COMMANDER_LISTS:           # the file puts the new commanders first; the popular ones lead here
        for cv in (lists.get(tag) or {}).get("cardviews") or []:
            name = cv.get("name")
            if not name or name in seen or cv.get("num_decks") is None:
                continue
            seen.add(name)
            url = cv.get("url") or ""
            out.append({"name": name, "decks": int(cv["num_decks"]), "of": None,
                        "theme_total": cv.get("potential_decks"),
                        "url": SITE + url if url.startswith("/") else url})
    return out


def parse_salt(page):
    """{card name: salt} from the saltiest-cards page (salt runs 0-4; the list holds 100 cards)."""
    return {cv["name"]: float(cv["salt"]) for lst in _json_dict(page).get("cardlists") or []
            for cv in lst.get("cardviews") or [] if cv.get("name") and cv.get("salt") is not None}


# ---------------------------------------------------------------- the provider calls
def _commander_signals(commanders, path_tail, bracket, theme, refresh, offline):
    if not commanders:
        return []
    path = f"commanders/{commander_slug(commanders)}{path_tail}"
    page, info = _page(path, refresh=refresh, offline=offline)
    if not page:
        return []
    meta = parse_meta(page, info)
    cards = parse_cards(page)
    if not cards:                      # a page with no cards says nothing
        return []
    return [{"source": NAME, "kind": KIND, "commanders": list(commanders), "bracket": bracket, "theme": theme,
             "url": info["url"], "fetched": info["fetched"], "cache": info["cache"],
             "n": meta["n_decks"], "cards": cards, "totals": None, "meta": meta}]


def signals(commanders, bracket=None, theme=None, *, refresh=None, offline=None):
    """The builder Signal for the page that matches, as a list of one (empty when EDHREC has no such page).
    A theme wins over a bracket: it returns the commander's all-bracket theme page with bracket None, because
    score.py measures a theme's pull against the all-bracket rate. bracket_theme_signal() has the page that
    combines both. A theme may be a slug or a label."""
    if theme:
        wanted = theme_slug(theme)
        return _commander_signals(commanders, "/" + wanted, None, wanted, refresh, offline)
    tail = "/" + _bracket_slug(bracket) if bracket is not None else ""
    return _commander_signals(commanders, tail, bracket, None, refresh, offline)


def bracket_theme_signal(commanders, bracket, theme, *, refresh=None, offline=None):
    """The page for this commander's decks at one bracket AND tagged with one theme (Hazel, Bracket 3,
    tokens: 281 decks). signals() does not use it; it is here for a caller that wants the theme measured
    inside the bracket. Returns a Signal or None."""
    wanted = theme_slug(theme)
    tail = f"/{_bracket_slug(bracket)}/{wanted}"
    found = _commander_signals(commanders, tail, bracket, wanted, refresh, offline)
    return found[0] if found else None


def commander_meta(commanders, bracket=None, *, refresh=None, offline=None):
    """What the commander's page says about the commander itself (see parse_meta), or None when there is no
    page. `n_decks` is the bracket's deck count when a bracket is given; `bracket_counts` always covers every
    bracket."""
    if not commanders:
        return None
    tail = "/" + _bracket_slug(bracket) if bracket is not None else ""
    page, info = _page(f"commanders/{commander_slug(commanders)}{tail}", refresh=refresh, offline=offline)
    return parse_meta(page, info) if page else None


def theme_commanders(theme, *, refresh=None, offline=None):
    """The commanders EDHREC lists for a theme, top then new:
    [{"name", "decks", "of", "theme_total", "url"}] (see parse_theme_commanders)."""
    page, _ = _page(f"tags/{theme_slug(theme)}", refresh=refresh, offline=offline)
    return parse_theme_commanders(page) if page else []


def theme_signal(theme, *, refresh=None, offline=None):
    """The theme across all commanders as card evidence, or None when EDHREC has no such theme. `n` is the
    number of decks site-wide with the theme (the index states no total, but any colorless card's
    potential_decks is it). `synergy` is EDHREC's own: a card's rate in these decks minus its rate in decks
    of the same colors."""
    page, info = _page(f"tags/{theme_slug(theme)}", refresh=refresh, offline=offline)
    cards = parse_cards(page, skip=COMMANDER_LISTS) if page else {}
    if not cards:
        return None
    return {"source": NAME, "kind": KIND, "commanders": [], "bracket": None, "theme": theme_slug(theme),
            "url": info["url"], "fetched": info["fetched"], "cache": info["cache"],
            "n": max(c["of"] for c in cards.values()), "cards": cards, "totals": None,
            "meta": {"label": page.get("header")}}


def salt_scores(*, refresh=None, offline=None):
    """{card name: salt} for EDHREC's 100 saltiest cards ({} when the page is gone). Only the top 100 are
    listed (the lowest is about 1.7 of 4), so a card missing here is below that, not unknown."""
    page, _ = _page("top/salt", refresh=refresh, offline=offline)
    return parse_salt(page) if page else {}
