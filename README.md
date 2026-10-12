# mtg-draft

**A draft coach for MTG Arena that lives in your terminal.**

While you draft, it reads the pack you're looking at straight out of Arena's log, ranks every card by
real [17Lands](https://www.17lands.com/) win-rate data, and shows you what each card does — so every
pick is backed by data instead of a gut read.

> ### 🌐 [Browse the card references online →](https://albertngo1.github.io/mtg-draft/)
>
> **Every card in 13 sets, no install needed:** card image, live 17Lands win rates, expert grades
> and notes, and an AI take on each card, with search across all of it.
>
> **Newest — Reality Fracture (FRA):** [card reference](https://albertngo1.github.io/mtg-draft/sets/FRA.html)
> · [prerelease guide](https://albertngo1.github.io/mtg-draft/prerelease/FRA.html)
>
> Also: BLB · DFT · DSK · ECL · FIN · HOB · LCI · MH3 · MKM · MSH · OTJ · SOS

No account login. No browser extension. Nothing forced on you — the core is just a Python script
reading the log file Arena already writes on your own machine.

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

Cards in your colors are marked `▸`; off-color picks are tagged `(off)`. Below the table (not shown)
the tool prints the mana cost, stats, and oracle text for every card in the pack, so you're judging
on *fit*, not just the win-rate column.

## Why this exists

Good limited players already do this loop by hand every pick: read the pack, look up each card's
17Lands numbers, weigh them against the archetypes that are open. This tool just does it for you,
instantly, without leaving the game — and it's careful about *how* it reads the numbers. The key idea
baked in: a card's win rate is the win rate of **the decks that drafted it**, not a context-free
score. A payoff card looks amazing because the deck built around it wins — that doesn't mean it's good
in *your* pile. The tool surfaces that distinction instead of hiding it behind a single number.

## Quick start

You'll need **Python 3.8+** and a one-time Arena setting:

> In MTG Arena: **Settings → Account → check "Detailed Logs (Plugin Support)"**, then restart Arena.
> Without this, the draft packs this tool reads never get written to the log.

```bash
git clone https://github.com/albertngo1/mtg-draft && cd mtg-draft

# Once per set: pre-cache card text + data so live picks make zero network calls.
# Use the set's 17Lands code (e.g. FIN, DSK, MKM).
python3 src/mtg-draft.py warm --set FIN

# Optional: dump the whole set's lean per-card data (stats + text + grade + guide
# note) as NDJSON — load/grep it for fast per-pick lookups without re-fetching.
python3 src/mtg-draft.py cards --set FIN > data/cache/cards_FIN.ndjson

# During the draft: read the current pack and rank it. Set, format, and your
# colors are all auto-detected from the live draft.
python3 src/mtg-draft.py pull
```

On **Windows**, use `python` and the `mtg-draft.bat` wrapper (`mtg-draft.bat pull`). On macOS/Linux
there's a `./mtg-draft.sh` wrapper too. Nothing to `pip install` — it's standard library only.

Want it to update on its own? Run **`watch`** in a side pane and it reprints the ranked table every
time a new pack appears.

Playing **Sealed** instead? Open the event's deck builder in Arena, then run
`python3 src/mtg-draft.py sealed` — it reads your whole 84-card pool from the log, ranks every card,
and prints a category/curve breakdown (with copy counts) to build from.

## Two ways to use it

**🧍 Solo — no AI, no API key.** The whole ranking engine is plain Python over cached 17Lands +
Scryfall data. `warm` once, keep `watch` running beside Arena, and draft
straight off the live ranked output. Nothing leaves your machine.

**🤖 Coached — add an AI agent.** Point an LLM agent (e.g. Claude Code) at
[`AGENTS.md`](./AGENTS.md) and it drives the same loop but adds *judgment*: reading open lanes,
cross-referencing expert set guides, mana-curve warnings, and adapting when you take an off-meta
pick. It's a second opinion layered on top — the solo tool works fine without it. If you use
[Claude Code](https://claude.com/claude-code), the repo ships a `/mtg-draft` skill (in
[`.claude/skills/`](./.claude/skills/mtg-draft/)) that wires this up — just open the repo and type
`/mtg-draft`.

Either way, the 17Lands data is the source of truth and the AI is decorrelated expert color, never
the other way around.

## Commander deck builder

Play Commander (also called EDH) instead of drafting? `mtg-commander` is a second tool in the same repo. It upgrades
a deck you have, builds a full 100-card deck around a commander, and suggests commanders for the themes and playstyle
you want, each within a **budget** and one of Wizards' power **brackets** (1 Exhibition, 2 Core, 3 Upgraded, 4
Optimized, 5 cEDH, which is competitive tournament play; Bracket 3 unless you say otherwise). It also checks a
list's legality and bracket rules, and it will not recommend a card that breaks them.

```bash
# Upgrade a precon: ranked cuts and adds, at most $75 on cards you don't own (with what $20 and $40 buy on the
# way up, and a note where a step leaves you with fewer answers to some kind of threat), leaning toward tokens
python3 src/mtg-commander.py upgrade --precon "Squirreled Away" --budget 75 --theme tokens

# Check a decklist file: legality, bracket rules, role counts, mana curve
python3 src/mtg-commander.py check mydeck.txt --bracket 3

# Build from a commander
python3 src/mtg-commander.py build "Hazel of the Rootbloom" --bracket 3 --budget 150 --theme squirrels

# Every number about a deck in one report (see "Looking at a deck with stats" below)
python3 src/mtg-commander.py stats --precon "Squirreled Away" --bracket 3 --theme tokens --playstyle aristocrats
```

Same launchers as the draft coach: `./mtg-commander.sh` on macOS/Linux, `mtg-commander.bat` on Windows. It needs
Python 3.9+ and nothing to `pip install`. The first run downloads Scryfall's card file (a minute or two, once);
run `warm "<commander>"` ahead of time and `--offline` works after that.

**Looking at a deck with `stats`.** `stats` takes the same deck, bracket, theme, playstyle and owned-card flags as
`check` and `upgrade` and prints every number it can work out about a list, in six groups: power (its score and the
lowest bracket it fits), interaction (how many cards answer each kind of threat, marked short when it is under what
real decks at the bracket hold, and a *removal power* that weighs how fast, how far and how surely each removal card
works), mana (lands, ramp, card draw, the curve, the colors), playstyle (how much of each playstyle the deck is),
win plan (finishers and the combos that win) and table and money (salt, the
bracket's limits, price, what you own). A number with a usual range for the bracket sits beside it and says if it is
short of the range or over it. Add `-v` to see how each number was made, or `--json` for the same numbers as data. The
first run also saves Commander Spellbook's daily combo file (29 MB, kept for 7 days), so later runs find a list's combos
without asking the website.

**Saved decks, and the local server `serve`.** `serve` starts a small web server on your own computer. It keeps **base
decks** (a precon or a pasted list, saved once and never changed) and each player's **versions** of them as small files
in `commander/decks/`, and it answers every request to read a deck or change it (add, cut, swap, undo, or apply the
upgrade's suggestions) with all of `stats`' numbers worked out again. It also hands out the **deck pages**: open the
address it prints in a browser to see a saved deck as cards, change it, and watch its numbers move. The pages call the
server's application programming interface (API), under `/api/`. `stats --version andy/squirrels-go-wide` prints the same
numbers in the terminal, each beside its base deck's.

*What the deck pages do.* **Decks** lists your versions and the base decks. **New version** starts your own copy of a base
deck with a bracket, a budget, themes and a playstyle, and **New base deck** takes a precon from the list or a deck list
you paste in (lines it cannot read are shown with their line numbers, so you can fix or drop them). A version opens on its
cards, with four tabs. **Cards** shows every card as its picture: tap one to read it with the tool's numbers for it, then
cut it or swap it, or use **Add** to search for a card and say what it replaces. **Metrics** shows every number, each with
how it was worked out behind a tap. **Changes** lists what was added and cut against the base deck, with an Undo for each
change. **Suggestions** lists `upgrade`'s swaps by price point, which you apply one at a time or a whole price point at
once; each point shows its change in score, and a "Weakens interaction" note when it leaves the deck with fewer answers
to some kind of threat than it started with and than a typical deck at the bracket. Every change is saved the moment
you make it and every number is redrawn from the server's answer, so the pages never work a number out themselves.
The first time a commander is opened its data is downloaded, which takes several
seconds, and the page says what it is fetching. On a phone the page is one column with the numbers pinned above the cards;
on a desktop screen the metrics sit beside the cards. The only thing loaded from another site is each card's picture
(Scryfall's link, sent by the server); nothing needs installing to run the pages.

```bash
python3 src/mtg-commander.py serve                          # http://127.0.0.1:8341/, on this computer only
python3 src/mtg-commander.py serve --host 100.101.102.103   # also reachable from a phone over Tailscale (below)
```

*On your phone.* By default only this computer can reach the server. [Tailscale](https://tailscale.com) is a private
network between your own devices. With it, leave the server running, run Tailscale's own
`tailscale serve --bg --https=8443 8341`, and open `https://<this computer's name>.<your tailnet>.ts.net:8443/` on the
phone. `tailscale serve status` prints that address, and `tailscale serve --https=8443 off` stops it. Port 8443 leaves
alone any site the computer already serves at its plain Tailscale address, which plain `tailscale serve --bg 8341` would
replace. Or start the server with `--host` set to this computer's Tailscale address (`tailscale ip -4` prints it) and
open `http://<that address>:8341/`. On home Wi-Fi `--host 0.0.0.0` works too, but it listens on every network the
computer is on, so use it only on a network you trust.

*There is no login.* Anyone who can reach the server's address can change every deck; on Tailscale that means only your
own devices. The server does check that a request comes from its own pages, so a web page from another site cannot use it
through your browser, but that is not a password.

*Run one server per repo.* A deck file is written whole, to a temporary file that then replaces the old one, so a file is
never half saved. Nothing locks the files between programs, though, so two servers (or a server and an editor) can
overwrite each other's changes. Share decks the usual way, with git: the server never commits or pushes, and its
`/api/status` answer lists the deck files git does not have yet. `--decks DIR` (or the `MTG_COMMANDER_DECKS` environment
variable) picks another folder for the files.

**What the numbers mean.** At Brackets 1–4 the numbers are what experienced deck builders choose at that bracket,
not win rates; real per-card win rates exist publicly only for tournament (cEDH) play. So every line says which
kind of number it is and how many decks it comes from, and `build` shows the *fantasy cost*: what the theme you
picked gives up in strength.

The data comes from public sites (EDHREC, Archidekt, EDHTop16, Commander Spellbook, Scryfall, MTGJSON). The terms
of some of them restrict scripted access; ARCHITECTURE.md quotes them and says how to choose which sources are used.
Details: **[ARCHITECTURE.md → Commander deck builder](./ARCHITECTURE.md#commander-deck-builder)** (every command and
flag, how cards are scored, caching, bracket rules, the deck server, terms of use) and **[`commander/README.md`](./commander/README.md)**
(the three data files). With Claude Code, `/mtg-commander` (in [`.claude/skills/`](./.claude/skills/mtg-commander/))
coaches you through it.

## Learn more

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — the full reference: every command and flag, how the
  log-reading and caching work, the draft-history reconstruction, repo layout, the Commander deck
  builder, and more.
- **[AGENTS.md](./AGENTS.md)** — the operating manual for the AI coaching layer: universal limited
  theory plus how to drive this tool pick-by-pick, and how to coach Commander deck building.
- **[card-reference/](./card-reference/)** — a visual grid of every card in a set: image, 17Lands
  ratings, a reviewer letter grade where one exists, notes from the expert guides, and a per-card AI
  take. **Thirteen sets, 3,935 cards** — BLB, DFT, DSK, ECL, FIN, FRA, HOB, LCI, MH3, MKM, MSH, OTJ, SOS. Each set also
  ships a **format brief** (`card-reference/briefs/<SET>.md`): the archetype table with real 17Lands
  win rates and metagame share, the draft plan, and the things a win-rate column can't tell you —
  sequencing, combat math, copy counts, splash policy. See its README to regenerate.

  Browsable online at **[albertngo1.github.io/mtg-draft](https://albertngo1.github.io/mtg-draft/)**,
  with search across card names, stats *and* every expert note, plus rarity filters and colour-section
  jumps. GitHub Actions rebuilds and deploys it on every push that changes a reference, so the site
  cannot fall behind the Markdown.

- **[`src/sealed_algo.py`](./src/sealed_algo.py)** — a **sealed** pool → best-40 algorithm, fitted
  on 17Lands *trophy decks* (a trophy deck won the max matches for its event; 17Lands publishes the
  full sealed pool alongside the registered 40, so each one is a labelled `pool → deck` pair). It
  scores every card from sealed GIH WR, adjusts by how much *more or less* often 7-win players
  maindeck it than that win rate predicts, then searches the ten colour pairs with a front-loaded
  top-23 mean (bombs pick the colour; the 23rd playable doesn't). Hybrid pips count as either half,
  utility lands take land slots rather than spell slots, and single-off-colour-pip cards better than
  your worst include are surfaced as splash candidates.

  ```bash
  python3 src/ingest/fetch_trophies.py --set HOB --format ArenaDirect_Sealed   # once per format
  python3 src/sealed_algo.py --set HOB --pool mypool.txt                       # per pool
  python3 src/sealed_algo.py --set HOB --validate                              # leave-one-out
  python3 src/sealed_algo.py --set HOB --catalog                               # whole set, as JSON
  python3 src/sealed_algo.py --set HOB --shapes                                # deck shapes, as JSON
  python3 src/sealed_algo.py --set HOB --decks                                 # the 40s themselves
  ```

  The Mac mini's card-reference site (port 8340) drives the same script from a browser: `/decks`
  renders `--decks` and `--shapes` on one page — the trophy lists with the aggregate they add up to.

  Leave-one-out over the 100 HOB Arena Direct Sealed trophy decks: colour pair correct **47%** of
  the time (always-guess-BR baseline: 42%), in the top two **77%**, and when the pair matches
  **86%** of the algorithm's 23 spells were in the real 40. Trophy play rate correlates with sealed
  GIH WR at r=0.82, so it is worth about one point of card agreement on its own — the honest use of
  it is as a *build-decision* correction, not a second power rating.

  **On enlarging the corpus.** `/api/trophies/` returns only the 100 most recent decks, but it
  applies the `deck_colors` filter *before* that cap, so sweeping every 1-, 2- and 3-colour
  combination yields ~1,100 unique ids for a busy format. That sample is **stratified, not random**:
  a filter that fills its 100-id quota contributes 100 decks whether or not that colour pair is
  common, so counting it raw makes whichever colour was swept first look like the format's best
  pair. `fetch_trophies.py` therefore takes pair frequencies only from the unfiltered query and
  post-stratifies everything else (weight = true pair share / sampled pair share, clipped to
  [0.1, 10]), reporting a Kish effective sample size rather than the raw weighted count.

  Measured on the same 100-deck test set, 330 stratified decks scored **46% / 68% / 67%** against
  the unbiased 100's **47% / 77% / 66%** — a wash, because clipping pulled the effective sample from
  330 down to 124. Pass `--unbiased-only` (the default shipped model) unless a sweep completes far
  enough that the up-weighted strata carry real extra information. 17Lands IP-bans `event_preview`
  after roughly 120 fetches even at a 2 s delay, which is why the sweep here stopped at 330.

- **[draft-guides/](./draft-guides/)** — per-set strategy notes distilled from five limited channels
  (Lords of Limited, NumotTheNummy, Limited Resources, Limited Level-Ups, Rough Drafts). The
  ingest pipeline is channel-agnostic — [`src/ingest/channels.json`](./src/ingest/channels.json)
  registers a channel and its output contract, `fetch_subs.sh` pulls captions, `fingerprint.py`
  tracks what's been distilled, and [`src/ingest/DISTILL.md`](./src/ingest/DISTILL.md) is the
  runbook. These notes **decode** the 17Lands data rather than outranking it: the win rate says how
  good a card is, the guides say which deck's number you're looking at.

## Credits

- **[17Lands](https://www.17lands.com/)** — draft win-rate statistics (queried at runtime).
- **[Scryfall](https://scryfall.com/)** — card names, mana costs, and oracle text (queried at
  runtime, not redistributed; please respect their [API guidelines](https://scryfall.com/docs/api)).
- The limited-content creators whose public videos the `draft-guides/` notes are distilled from —
  **Lords of Limited**, **NumotTheNummy**, **Limited Resources**, **Limited Level-Ups** and
  **Rough Drafts**. Those files are summaries written for personal draft prep, not transcripts; go
  watch the originals.
- For the Commander deck builder (all queried at runtime, not redistributed; terms quoted in
  [ARCHITECTURE.md](./ARCHITECTURE.md#terms-of-use)): **[EDHREC](https://edhrec.com/)** and
  **[Archidekt](https://archidekt.com/)** (what builders play), **[EDHTop16](https://edhtop16.com/)** (cEDH
  tournament results; this tool is not endorsed by EDHTop16), **[Commander Spellbook](https://commanderspellbook.com/)**
  (combos), **[MTGJSON](https://mtgjson.com/)** (precon lists), and Scryfall again for card data and prices.

Magic: The Gathering is © Wizards of the Coast. This is an unofficial fan tool, not affiliated with
or endorsed by Wizards of the Coast, or by any of the sites it reads.

## License

[MIT](./LICENSE)
