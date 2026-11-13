# mtg-draft

A draft helper for MTG Arena that runs in your terminal. While you draft, it reads the current pack
from Arena's log file and ranks the cards by their [17Lands](https://www.17lands.com/) win rates.

**Just want to look up cards?** The [card reference site](https://albertngo1.github.io/mtg-draft/)
has every card from 14 sets with win rates, expert grades and notes, and nothing to install.
Newest set: Star Trek ([cards](https://albertngo1.github.io/mtg-draft/sets/TRK.html), launch-day
17Lands data).

## What it looks like

```
  MKM PremierDraft  (on-color = WB)

   CARD                    CLR  R  MV GIHWR   IWD    ALSA  N     CGB   tier
  -----------------------------------------------------------------------------
   Enlisted Wurm           WG   U  6  60.6%   +4.9   3.7   5396  B+    🔥bomb  (off)
   Krosan Tusker           G    C  7  56.5%   +4.1   4.6   4002  C+    excellent  (off)
  ▸Putrid Warrior          WB   C  2  55.5%   +0.0   6.8   934   C-    excellent
   Kuldotha Rebirth        R    C  1  50.0%   -0.6   6.2   856   C     filler  (off)
   ...
```

`▸` marks cards in your colors and `(off)` marks the rest. Under the table it prints each card's
cost and rules text.

A card's win rate comes from the decks that played it. A strong payoff card can look great only
because its own deck wins, so the tool shows the win rate alongside what the card does.

## Setup

You need Python 3.8 or newer. Nothing to `pip install`.

In Arena, turn on **Settings → Account → Detailed Logs (Plugin Support)** and restart the game.
Without it, Arena doesn't write the draft packs to its log.

```bash
git clone https://github.com/albertngo1/mtg-draft && cd mtg-draft

# Once per set: download card data so picks are instant (use the set's 17Lands code)
python3 src/mtg-draft.py warm --set FIN

# During a draft: rank the pack you're looking at
python3 src/mtg-draft.py pull
```

The set, format and your colors are detected from the draft automatically.

- `watch` re-ranks automatically each time a new pack shows up. Run it in a second window.
- `sealed` ranks your whole Sealed pool. Open the event's deck builder in Arena first.
- On Windows, use `mtg-draft.bat` (for example `mtg-draft.bat pull`). On macOS and Linux there's
  `./mtg-draft.sh`.

## With or without AI

The tool works on its own, with no account or API key, and nothing leaves your machine.

If you want a second opinion, point an AI agent like [Claude Code](https://claude.com/claude-code)
at [`AGENTS.md`](./AGENTS.md). It runs the same commands each pick and adds what a table can't:
which colors look open, what the expert guides say, and whether your curve is short. In Claude
Code, open the repo and type `/mtg-draft`.

The 17Lands numbers stay the main signal either way. The AI adds context on top of them.

## Commander deck builder

`mtg-commander` is a second tool in the same repo for Commander (EDH). It upgrades a deck you own,
builds a 100-card deck around a commander, or suggests commanders. Each command stays within a
budget and one of Wizards' power brackets (Bracket 4 unless you pick another).

```bash
# Upgrade a precon, spending at most $75 on cards you don't own
python3 src/mtg-commander.py upgrade --precon "Squirreled Away" --budget 75 --theme tokens

# Build a deck around a commander
python3 src/mtg-commander.py build "Hazel of the Rootbloom" --bracket 3 --budget 150

# Check a decklist's legality and bracket, or see every stat about it
python3 src/mtg-commander.py check mydeck.txt --bracket 3
python3 src/mtg-commander.py stats --precon "Squirreled Away" --bracket 3

# Web pages for saving and editing decks, at http://127.0.0.1:8341/
python3 src/mtg-commander.py serve
```

It needs Python 3.9 or newer. The first run downloads Scryfall's card data, which takes a minute or
two. At Brackets 1–4 the numbers show what experienced builders play, not win rates; public
per-card win rates only exist for competitive (cEDH) play.

The full guide covers your card collection, saved decks, using the pages from a phone, and how
cards are scored. It's in [ARCHITECTURE.md → Commander deck builder](./ARCHITECTURE.md#commander-deck-builder).

## What else is in here

- **[card-reference/](./card-reference/)**: the source for the card reference site. Each set
  page has every card's image, 17Lands stats, reviewer grades, expert notes and an AI take. It also
  has a format brief covering archetypes, the draft plan, and things the numbers miss.
- **[draft-guides/](./draft-guides/)**: per-set strategy notes summarized from five Limited
  YouTube channels and podcasts. [`src/ingest/DISTILL.md`](./src/ingest/DISTILL.md) explains how
  they're made.
- **[`src/sealed_algo.py`](./src/sealed_algo.py)**: picks the best 40 cards from a Sealed pool,
  trained on 17Lands trophy decks. See
  [ARCHITECTURE.md → Sealed pool builder](./ARCHITECTURE.md#sealed-pool-builder-srcsealed_algopy).
- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: every command and flag, and how it all works.
- **[AGENTS.md](./AGENTS.md)**: instructions for an AI coach.

## Credits

- [17Lands](https://www.17lands.com/) for draft win rates.
- [Scryfall](https://scryfall.com/) for card text and images. Data is fetched as you use the tool,
  not bundled here. Please follow their [API guidelines](https://scryfall.com/docs/api).
- Lords of Limited, NumotTheNummy, Limited Resources, Limited Level-Ups and Rough Drafts, whose
  videos the draft guides summarize. The guides are notes, not transcripts. Go watch the originals.
- For Commander: [EDHREC](https://edhrec.com/), [Archidekt](https://archidekt.com/),
  [EDHTop16](https://edhtop16.com/) (which doesn't endorse this tool),
  [Commander Spellbook](https://commanderspellbook.com/) and [MTGJSON](https://mtgjson.com/). Their
  terms are quoted in [ARCHITECTURE.md](./ARCHITECTURE.md#terms-of-use).

Magic: The Gathering is © Wizards of the Coast. This is an unofficial fan project, not affiliated
with or endorsed by Wizards of the Coast or any of the sites it uses.

## License

[MIT](./LICENSE)
