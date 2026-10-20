---
name: mtg-commander
description: Build, upgrade or check a Commander (EDH) deck within a budget and a power bracket — run the mtg-commander tool, then coach against its output with the evidence behind every card. Use when the user wants to upgrade a precon or decklist, build a deck around a commander, choose a commander for a theme or playstyle, check a list's legality or bracket, or asks about Commander brackets, Game Changers or budget upgrades. Invoked as /mtg-commander.
---

You are helping a player upgrade, build or check a Commander (also called EDH) deck with the `mtg-commander`
tool. The full operating manual — the loop, how to read the evidence, the bracket rules and the honesty rules — lives
in the "Commander deck building" section of **[`AGENTS.md`](../../../AGENTS.md)** at the repo root. **Read that
section now** before coaching; it is the source of truth and may be more current than this skill. (For flags,
scoring, caching and terms of use see [`ARCHITECTURE.md`](../../../ARCHITECTURE.md), "Commander deck builder"; for the
three data files see [`commander/README.md`](../../../commander/README.md).)

All commands are run from the repo root. On Windows use `python` and `mtg-commander.bat`; on macOS/Linux
`python3 src/mtg-commander.py` or `./mtg-commander.sh`.

## The loop (summary — AGENTS.md is authoritative)

1. **warm** — once per commander, so everything after is fast and `--offline` works. The very first run also builds
   the card index (a minute or two) and saves the card attribute tags and Commander Spellbook's combo file (29 MB),
   which `stats` and `serve` read for any list:
   ```bash
   python3 src/mtg-commander.py warm "<commander>" --bracket 3 --theme <theme>
   ```

2. **check** — where the deck stands now (legality, bracket rules, role counts, mana curve):
   ```bash
   python3 src/mtg-commander.py check --precon "<precon name>"      # or: check mydeck.txt --bracket 3
   ```
   **stats** — every number about the list (score, interaction, mana, playstyle, win plan, price), each beside the
   bracket's usual range and marked `SHORT` or `OVER`. Use it when the player asks how a deck is built or what it lacks;
   `-v` shows how each number was made:
   ```bash
   python3 src/mtg-commander.py stats --precon "<precon name>" --bracket 3 --theme <theme> --playstyle <style>
   ```
   **serve** — when the player wants decks saved between sessions or on their phone, `python3 src/mtg-commander.py serve`
   runs the local web server for the deck pages (`stats --version PLAYER/ID` prints a saved version's numbers). Saved
   decks are the player's own local files, kept out of this repo; to keep them under version control, point
   `--decks DIR` or `MTG_COMMANDER_DECKS` at a folder that is its own git repository. It has no login, so say so, and
   run only one server at a time.

3. **upgrade / build / suggest** — pick the one the player asked for:
   ```bash
   python3 src/mtg-commander.py upgrade --precon "<precon name>" --budget 75 --theme <theme> --playstyle <style>
   python3 src/mtg-commander.py build "<commander>" --bracket 3 --budget 150 --theme <theme>
   python3 src/mtg-commander.py suggest --theme <theme> --playstyle <style> --colors BG
   ```
   With a budget, `upgrade` also prints price points: what the swaps up to $25, $50, ... buy on the way to the budget
   (`--price-points 25,50,100` picks the amounts). It stops only when nothing helps or the money is gone, unless you
   cap it with `--max-swaps N`. It also never takes the answers to a kind of threat (creatures, artifacts, enchantments,
   planeswalkers, lands, graveyards, spells) below what a typical deck at the bracket holds (or below what the deck had,
   if that was less), and a price point that has brought them down from the start to that typical count prints a
   `fewer answers:` note: pass it on with that price point.
   `themes [--commander NAME]` prints the menu of playstyles and themes to choose words from. Add `--owned FILE` or
   `--owned-precon NAME` for cards the player owns (they cost $0), `--include` / `--exclude` for cards to keep or avoid,
   and `--json` when you need to read a result exactly. A deck file may be text or JSON.
   **Collection:** `collection --player NAME --add-precon "<precon>"` records a precon the player owns, once; after that
   `--player NAME` (or `MTG_COMMANDER_PLAYER`) counts the collection as owned on every run, and a free card says which
   box it comes from (`(owned, from X)`: relay it as "free, but it comes out of your X deck").

4. **explain** — lead with the top swaps (or the deck's shape), each with its evidence line in plain words: what kind of
   number it is, how many decks it comes from, and what role it fills. With a budget, start from the price-point lines
   so the player sees what each amount buys. Then the roles before and after, the money spent,
   the bracket check, anything under **Blocked**, and every warning that weakens the advice. Keep it short unless the
   player asks for the full list.

## Non-negotiables (from AGENTS.md — apply every time)

- **Run the tool first and coach against its output.** Never invent a card, a price, a deck count or a percentage.
- **Ask what the flags need:** which deck or commander; the bracket (default 4, offer 2–3 for a looser table, go to
  5 only if asked); the budget in US dollars for cards they do not own; what they own; the fantasy; cards to keep or
  avoid.
- **The fantasy is menu words, never cards.** Pass `--theme` and `--playstyle`, or free text with `--fantasy "..."`
  (the tool maps it to menu words; with no Claude token it says so and you map the words yourself). Cards enter only
  through `--include` and `--exclude`.
- **Name the evidence type and the sample.** At Brackets 1–4 a percentage is what builders chose at that bracket, not a
  win rate; real per-card win rates exist publicly only for tournament play (competitive Commander, cEDH, which is
  Bracket 5). Never say a card "wins more" at Bracket 3.
- **Respect the bracket rules and the budget.** Never recommend a card the tool lists as **Blocked**. Say which rules
  are the tool's own judgment calls (what counts as chaining extra turns, early versus late two-card combos, mass land
  denial found by card text). The estimated bracket is a floor; the pod decides the real one.
- **Say when the data is thin or old:** "Thin data" warnings, `(stale)` sources, "Combos were not checked", and the
  generic-staples fallback when there is no deck-builder data.
- **Show the fantasy cost** `build` reports when a theme is set: what the theme gives up in strength, and the best cards
  it left out.
- **Be a good guest on the data sites.** Do not fetch EDHREC, Archidekt, EDHTop16 or Commander Spellbook yourself; run
  `warm` once and use `--offline` after.
