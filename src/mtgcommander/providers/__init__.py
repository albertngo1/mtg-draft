"""Card-evidence providers: one module per data source, all registered in SIGNAL_PROVIDERS.

Each registered module defines NAME, KIND ("builder": what deck builders chose; "tournament":
tournament results) and

    signals(commanders, bracket=None, theme=None, *, refresh=None, offline=None) -> list[dict]

which returns Signal records in the shape below (an empty list when the source has no page for
that commander, bracket or theme). Adding a source later, such as playgroup.gg or a log of your
own games, is one new module plus one entry in SIGNAL_PROVIDERS; score.gather() does not change.

Signal record:
    {"source": "edhrec", "kind": "builder", "commanders": ["Hazel of the Rootbloom"],
     "bracket": 3 | None,            # None = all brackets pooled
     "theme": "tokens" | None,
     "url": "https://...", "fetched": "2026-10-11T12:00:00Z", "cache": "fresh" | "network" | "stale",
     "n": 1124,                      # decks (builder) or entries with decklists (tournament)
     "cards": {card name as the source spells it: stats},
     "totals": {...} | None,         # tournament only: the same stats summed over every entry
     "meta": {...}}                  # source extras, documented in each provider module

Builder stats: {"decks": int, "of": int, "synergy": float | None}       (inclusion = decks / of)
Tournament stats, summed over the entries that ran the card:
    {"entries": int, "games": int, "wins": int, "draws": int, "topcuts": int}

Commander Spellbook (combos) and Scryfall function tags are lookups, not card evidence, so their
modules live here but are not registered in SIGNAL_PROVIDERS."""
import importlib

SIGNAL_PROVIDERS = ("edhrec", "archidekt", "edhtop16")  # module names, imported on first use


def modules(names=None):
    """The provider modules to ask, in registry order (or just `names`)."""
    return [importlib.import_module(f"{__name__}.{n}") for n in (names or SIGNAL_PROVIDERS)]
