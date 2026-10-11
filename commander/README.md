# commander/ — the data files behind `mtg-commander`

Three small JSON files that the Commander deck builder reads every run. They are committed, so a rule change is a data
edit rather than a code change, and each one stamps its own source and date. This page says what each holds, where it
came from, which parts are measured and which are judgment, and how to regenerate the one that can be regenerated.
For how the tool uses them, see [ARCHITECTURE.md → Commander deck builder](../ARCHITECTURE.md#commander-deck-builder).

| file | holds | made by | measured or judgment |
|---|---|---|---|
| [`brackets.json`](./brackets.json) | Wizards of the Coast's Commander Brackets: the wording, the checkable limits, and the lists of cards the checks look for | copied by hand from Wizards' pages, with source and date | Wizards' words are copied; the limits table was transcribed from an image; how a program reads "chained" or "before turn 6" is judgment |
| [`role_targets.json`](./role_targets.json) | how many lands, ramp, card draw, removal and so on a deck at each bracket holds, as `[min, target, max]` | `src/mtgcommander/calibrate.py` | Brackets 2 and 5 are measured from real decks; Brackets 3 and 4 are interpolated; Bracket 1 is judgment |
| [`playstyles.json`](./playstyles.json) | the menu of playstyles and themes you can ask for | by hand | the role changes per playstyle are judgment; the theme names are checked against EDHREC's list |

## `brackets.json`

**What it holds.**

| key | content |
|---|---|
| `schema`, `as_of`, `status` | file version; the day it was read (2026-10-11); Wizards' note that "Commander Brackets are currently in beta" |
| `source`, `source_notes` | the seven pages it was built from, and for each its date and what it was used for |
| `brackets` | for Brackets 1 to 5: `name`, `wording` (what players expect), `turns` (how long a game should last), `limits_wording`, and the checkable limits `game_changers_max`, `mass_land_denial`, `extra_turns`, `two_card_combos` |
| `definitions` | Wizards' own sentences about mass land denial, extra turns, two-card combos, Game Changers and intent, each with its source URL and date |
| `conflicts` | the six places where Wizards' articles disagree, and which one the file follows |
| `mass_land_denial_cards`, `_basis`, `_patterns`, `_exceptions` | 27 named cards, the reason each is listed, 8 text patterns that find more, and the one card (`From the Ashes`) that is excepted because it replaces the lands it destroys |
| `extra_turn_cards`, `extra_turn_patterns` | 23 named cards and 2 text patterns that find extra-turn cards |

**Where it came from** (all read 2026-10-11):

- Wizards' [Commander format page](https://magic.wizards.com/en/formats/commander): the "Players expect" wording and the
  Game Changers limits (bracket entries last updated 2025-11-05).
- The October 21, 2025 article: the expected game length for each bracket (at least 9, 8, 6 and 4 turns; none for
  Bracket 5), the removal of the tutor limits, Core no longer tied to precons, and the turn-six reading of "early game".
- The February 9, 2026 article: the newest. It adds Farewell and Biorhythm to the Game Changers list and changes no
  bracket.
- The February 11, 2025 article ("Introducing Commander Brackets Beta"): the definition of mass land denial, the rule
  against chaining extra turns, the two-card combo rule.
- The April 22, 2025 article: intent matters most, and Wizards has not published an exact list of mass land destruction.
- A [graphic by Rachel Weeks](https://bsky.app/profile/wachelreeks.com/post/3m3ptspaivs27), linked from the October
  2025 article: the per-bracket limits table. It is an image, so its text was **transcribed by eye**; the file's
  `source_notes` and `field_notes` say so.

**Measured or judgment.**

- Copied from Wizards: `wording`, `turns`, and the quotes in `definitions`.
- The limits table (`limits_wording`) is a transcription of an image. If you spot a typo, fix the file and say so.
- Judgment, because a program cannot count what Wizards wrote: `extra_turns: "no-chaining"` is read as at most one
  extra-turn card; `two_card_combos: "late-game"` (Bracket 3, "before turn 6") is read as "block every two-card combo
  Commander Spellbook rates above this bracket", since the tool cannot tell early from late. The tool's messages
  say when they apply one of these readings.
- The card lists are curated, because Wizards publishes no complete list. It named five examples of mass land denial
  (Armageddon, Ruination, Sunder, Winter Orb, Blood Moon); the other 22 were added because they fit its wording, and
  `mass_land_denial_basis` says why for each. Cards found only by a text pattern are labeled that way in reports.
- Not in the file: the **Game Changers list** (the tool reads Scryfall's `game_changer` flag on each card; 53 cards on
  2026-10-11, matching Wizards' list), **tutors** (Wizards removed their limits in October 2025) and **intent**, which
  Wizards says decides a deck's real bracket.

**When Wizards changes the rules:** edit the values, add the article to `source` and `source_notes`, move `as_of`,
and add a `conflicts` entry if it disagrees with an older one. The unit tests read this file (`python3 -m unittest
discover -s tests -t .` from the repo root).

## `role_targets.json`

**What it holds.** For each bracket, `[min, target, max]` cards for `land`, `ramp`, `draw`, `removal`, `wipe`,
`counter`, `protection`, `recursion`, `tutor` and `finisher`, plus `topend`: the most nonland cards of mana value 6 or
more. `build` and `upgrade` value a card more while its role is below the target, and `check` marks a role low or high
against the range. At run time `roles.targets()` shifts the numbers a little for the playstyle, for the commander's
average land count, and for a commander without blue (no counterspell minimum).

The file also records how it was made: `source`, `as_of`, `method` (in words), `samples` and `samples_blue` (decks per
bracket), `measured` (true or false per bracket) and `labels` (a sentence per bracket).

**Measured or judgment.** What each bracket rests on is limited by what the data sources' terms allow:

| bracket | how its numbers are made |
|---|---|
| 2 | measured: the newest 60 MTGJSON Commander precons, as a Bracket 2 proxy. Wizards no longer ties Core to precons, so these are typical out-of-the-box decks, not a sample of Bracket 2 decks |
| 5 | measured: EDHTop16 top-cut decklists of the most played tournament commanders |
| 3, 4 | measured from Archidekt decks tagged with that bracket only when `archidekt` is among the sources; otherwise interpolated between Brackets 2 and 5 (a quarter and half of the way) and labeled *interpolated (judgment)* |
| 1 | judgment: Bracket 2 with one more land and no tutors |

A target is what real decks of that kind hold (25th percentile, median and 90th percentile of the sample; lands use the
10th, median and 90th; `topend` uses the 75th), not a proof that it wins. Read the file's `labels` and `samples` for what
the committed numbers rest on.

**Regenerate it.** From the `src` folder (the first run needs the network; everything it reads is cached):

```bash
cd src
python3 -m mtgcommander.calibrate                  # prints each number old -> new; replaces nothing
python3 -m mtgcommander.calibrate --out role_targets.proposed.json   # writes a proposal here, leaves the committed file alone
python3 -m mtgcommander.calibrate --write          # replaces commander/role_targets.json
```

| option | meaning (default) |
|---|---|
| `--precons N` | recent precons that stand in for Bracket 2 (60) |
| `--tournament-commanders N`, `--entries N` | the most played tournament commanders (6) and the newest entries read from each (150) |
| `--decks-per-bracket N` | Archidekt decks per commander and bracket, used only when `archidekt` is a source (10) |
| `--sources LIST` | evidence sources to read, e.g. `edhtop16,archidekt` to measure Brackets 3 and 4 (the `MTG_COMMANDER_SOURCES` setting) |
| `--json`, `--refresh`, `--offline` | print the report as JSON; download again; use the cache only |

Brackets 2 and 5 each need at least 10 decks; if a source comes up short the run stops and says which. Afterwards run
the unit tests: they check the file's shape and stamps, and that faster brackets run fewer lands, more tutors and a
lower top end, whatever the numbers.

`validate --calibrate` runs this same calibration after the validation and rewrites the file, so the validation numbers
describe the targets as they were committed. (The score weights are separate: `validate --bracket 5 --sweep` tries a
grid of them.)

## `playstyles.json`

| key | content |
|---|---|
| `playstyles` | the 12 playstyles: `combat`, `voltron`, `go-wide`, `aristocrats`, `spellslinger`, `control`, `combo`, `big-mana`, `graveyard`, `politics`, `stax`, `value`. Each has a `label`, a one-sentence `description`, the EDHREC `themes` it leans toward (counted at half the weight of a theme you name), `targets` (a whole-number change to the bracket's role targets; negative means fewer) and `min_bracket` (`stax` needs 4) |
| `common_themes` | 41 themes shown by `themes` when no commander is named |
| `known_themes` | 416 EDHREC theme names, so a typed `--theme` is checked against real ones |
| `theme_matchers` | 35 weak matchers (subtypes, card types, text patterns) used only when no EDHREC page covers a theme |

**Where it came from.** The theme names are EDHREC's, checked on 2026-10-11 against the tags sitemap its `robots.txt`
lists, <https://edhrec.com/sitemaps/tags.xml>; `known_themes` leaves out EDHREC's color-identity pages. The playstyles
are this tool's own menu.

**Judgment.** The role changes per playstyle (`control` adds 2 removal, 2 counterspells and 1 board wipe; `big-mana`
adds 3 ramp and 1 land) are judgment calls, not fitted to data. So are the theme matchers. To add a theme, spell it as
EDHREC does (`plus-1-plus-1-counters`); the unit tests check that every theme a playstyle names is a real EDHREC theme.
