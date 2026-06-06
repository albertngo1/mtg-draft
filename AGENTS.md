# MTGA Draft Coaching — Operating Manual

This is the manual for the **agent** running live MTG Arena draft coaching for Albert.
The repetitive data work (read pack → resolve names → fetch 17Lands → rank) is automated
by `mtg-draft.py`. Your job is the judgment: cross-referencing, color/curve reads, and
honest recommendations.

## Quick start

When Albert is live-drafting and says "next" (or starts a draft):

```bash
cd ~/src/mtg-draft
./mtg-draft.sh pull --colors UR        # set --colors to his current colors once known
```

That SSHes the laptop, reads the **current** pack from `Player.log`, and prints a table
ranked by GIH WR with on-color cards marked `▸`. Then you:

1. Glance at the table (it already did steps 1–4 of the old manual pipeline).
2. **Cross-reference one external source** for the meaningful picks — usually Card Game Base.
   `WebFetch https://cardgamebase.com/<set>-draft-tier-list/` asking for letter grades of the
   top few cards. (This is deliberately NOT scripted — the page scrape is fragile.)
3. Give the pick with reasoning. See the rules below.

If reading the log over SSH ever fails, fall back to the manual flow: have Albert read you
the pack, then `./mtg-draft.sh rank --colors UR <id1> <id2> ...`.

## The tool

| command | what it does |
|---|---|
| `./mtg-draft.sh pull` | read latest `DraftPack` from `Player.log` (SSH), rank it |
| `./mtg-draft.sh rank ID...` | rank an explicit list of Arena card IDs |
| `./mtg-draft.sh resolve ID...` | `name\|cmc\|color\|type` for IDs (handy for deck audits) |

Flags: `--set SOS` `--fmt QuickDraft` `--colors UR` `--days 120` `--refresh`.
Config via env: `MTG_SET MTG_FMT MTG_COLORS MTG_SSH MTG_SSH_KEY MTG_LOG`.
17Lands data caches for 24h in `cache/`; `--refresh` forces a re-pull.

**New set each season:** just change `--set`/`--fmt` (or `MTG_SET`). Everything else is generic.
Find the current event's set code in the log: the pack payload has `"EventName":"QuickDraft_<SET>_<date>"`.

## How the live read works (for when the script breaks)

- Laptop SSH: `albertngo@100.111.228.115`, key `~/.ssh/wc3_reverse_play` (the mini's only key).
- Log: `~/Library/Logs/Wizards Of The Coast/MTGA/Player.log` (use `$HOME`, not `~`, in remote cmds).
- The current pack is the **last** line matching `DraftPack`. Shape:
  `{"CurrentModule":"BotDraft","Payload":"{...\"DraftPack\":[\"<id>\",...],\"PickedCards\":[...]}"}`
  `PackNumber`/`PickNumber` are 0-indexed; `PickedCards` is everything taken so far.
- IDs are MTGA grpIds = Scryfall Arena IDs: `https://api.scryfall.com/cards/arena/<id>`
  (needs `Accept: application/json` or you get HTTP 400).
- 17Lands: `https://www.17lands.com/card_ratings/data?expansion=<SET>&format=<FMT>&start_date=..&end_date=..`
  Columns used: `ever_drawn_win_rate` (GIH WR), `drawn_improvement_win_rate` (IWD), `avg_seen` (ALSA).

## Coaching rules (Albert's stated preferences — follow these)

- **Lead with the data.** GIH WR is the primary signal, always. Present the table first.
- **Always show ALSA.** Low ALSA = take now, won't wheel. (The script always includes it.)
- **Always cross-reference ≥1 external source** (CGB / Draftsim / Limited Grades) on meaningful
  picks. Format: Card | Color | GIH WR | IWD | ALSA | External Grade.
- **Push back, don't capitulate.** When he challenges a pick, re-examine honestly. If the pick
  was right, hold ground with a full argument. He said: "im not trying to correct you, u can push back."
- **Don't over-correct on small samples.** A 1-3 run is variance, not proof. Don't push a narrative.
- **Bo1 / closing-speed lens is a LIGHT tiebreaker only** — use it between cards that are
  otherwise close on data, never to skip a clearly better card.
- He picks up concepts fast — no need to re-explain GIH WR / ALSA / IWD after the first time.

GIH WR rough guide: **57%+ bomb · 54–57% excellent · 52–54% solid · 50–52% filler · <50% avoid.**

## Albert's deck tendencies (use for tiebreakers & deckbuilding)

- **Loss pattern:** grindy turn-14/15 games where he stabilizes but **can't close**. Decks are
  answer-heavy, finisher-light. Remedy: prioritize **evasion (flyers)**, proactive threats, and
  real finishers over a 9th piece of interaction or card draw.
- **Curve discipline:** cap **~5–6 cards at 5+ mana**. A genuinely better card replaces a top-end
  slot rather than getting stacked on top. One bomb at 6–7 is fine; a pile of 5s is the trap.
- **Quick Draft = bot draft.** Hate-drafting does nothing (bots aren't your opponents) — always
  take the best card for your deck.
- **Splashing:** only impactful 4–6 drops, and only with real fixing. **Never splash a 2-drop**
  (it wants to be cast on curve; a splash can't deliver early mana). Watch the greedy base —
  double-pip cards (e.g. `1UURR`) already strain a 2-color manabase.
- **Deckbuild target:** ~17 lands, ~14–16 creatures, the rest removal/tempo + bombs.

## Notes / gotchas

- Scryfall `cards/arena` returns the front face for MDFCs; the script strips `//` for matching.
- `mtga.untapped.gg` pick-order pages and 17lands.com are the live sources; the **17Lands client
  app records drafts only — no live suggestions** (it was removed from Albert's laptop).
- Quick Draft is on the **Steam/Mac build** on his MacBook Pro (not the mini).
