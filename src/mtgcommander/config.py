"""Paths, cache lifetimes and defaults for the Commander deck builder (the mtgcommander package).

Mirrors mtgdraft/config.py: everything downloaded lives under the gitignored data/ folder, so no
third-party data is committed. The small reference files the builder reads (bracket rules, role
targets, the playstyle menu) are committed under commander/ and stamp their own source and date."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root (this file is src/mtgcommander/)
CACHE = os.path.join(ROOT, "data", "cache", "commander")  # one subfolder per source; gitignored
COMMITTED = os.path.join(ROOT, "commander")               # brackets.json, role_targets.json, playstyles.json
os.makedirs(CACHE, exist_ok=True)

DEFAULT_BRACKET = int(os.environ.get("MTG_BRACKET", "3"))  # no bracket given → Bracket 3 (Upgraded)
DEFAULT_FANTASY_WEIGHT = 0.5                                # 0 = pure power, 1 = theme above all

# Card-evidence sources a run may query (providers/ SIGNAL_PROVIDERS). All three are on by default: below
# Bracket 5, EDHREC and Archidekt are the only evidence of what a commander's players run, though their terms
# bar scripted requests (ARCHITECTURE.md, "Terms of use"). MTG_COMMANDER_SOURCES or the --sources flag picks
# the set; without a deck-builder source, scores fall back to Scryfall's popularity rank.
SOURCES = tuple(s.strip() for s in os.environ.get("MTG_COMMANDER_SOURCES", "edhrec,archidekt,edhtop16").split(",")
                if s.strip())

DAY = 24 * 3600
TTL = {                          # how long a cached download counts as fresh, per source (seconds)
    "scryfall": 7 * DAY,         # card index (bulk file), searches, Game Changer flags
    "scryfall_tags": 30 * DAY,   # function tags change slowly
    "prices": 7 * DAY,
    "edhrec": 7 * DAY,
    "archidekt_search": 7 * DAY, # which decks exist for a commander and bracket
    "archidekt": 30 * DAY,       # one decklist
    "edhtop16": 1 * DAY,         # tournaments finish every day
    "spellbook": 7 * DAY,
    "mtgjson": 30 * DAY,         # a printed precon's list never changes
}

UA = {"User-Agent": "mtg-draft-commander/0.1 (+https://github.com/albertngo1/mtg-draft)",
      "Accept": "application/json"}
