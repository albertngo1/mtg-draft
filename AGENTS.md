# MTGA Draft Coaching — Operating Manual

This is the manual for the **agent** running live MTG Arena draft coaching for Albert.
The repetitive data work (read pack → resolve names → fetch 17Lands → rank) is automated
by `mtg-draft.py`. Your job is the judgment: cross-referencing, color/curve reads, and
honest recommendations.

## Quick start

**Once per set**, pre-cache it so live picks make zero network round-trips:

```bash
cd ~/src/mtg-draft
./mtg-draft.sh warm --set <SET>         # caches card text + mana value for the whole set
```

Then, each pick (when Albert says "next" or starts a draft):

```bash
./mtg-draft.sh pull --colors UR         # set --colors to his current colors once known
```

That SSHes the laptop, reads the **current** pack from `Player.log`, and prints (a) a table
ranked by GIH WR with on-color cards marked `▸`, and (b) a **"what each card does"** section
with oracle text + P/T. Then you:

1. **Read what the cards actually do** — the text block is there so you judge *fit*, not just
   stats. A 55%-card that's a 2-drop flyer in his colors can beat a 58%-card that's a 6-mana
   durdle. Don't recommend off the GIH column alone.
2. **Cross-reference one external source** for the meaningful picks — usually Card Game Base.
   `WebFetch https://cardgamebase.com/<set>-draft-tier-list/` asking for letter grades of the
   top few cards. (Deliberately NOT scripted — the page scrape is fragile.)
3. Give the pick with reasoning, applying the strategy fundamentals below. See the rules.

If reading the log over SSH ever fails, fall back to the manual flow: have Albert read you
the pack, then `./mtg-draft.sh rank --colors UR <id1> <id2> ...`.

## The tool

| command | what it does |
|---|---|
| `./mtg-draft.sh warm` | pre-cache the whole set's text + mana value (run once per set) |
| `./mtg-draft.sh pull` | read latest `DraftPack` from `Player.log` (SSH), rank it + show card text |
| `./mtg-draft.sh rank ID...` | rank an explicit list of Arena card IDs |
| `./mtg-draft.sh resolve ID...` | `name\|cmc\|color\|type` for IDs (handy for deck audits) |

Flags: `--set SOS` `--fmt QuickDraft` `--colors UR` `--days 120` `--brief` (table only) `--refresh`.
Config via env: `MTG_SET MTG_FMT MTG_COLORS MTG_SSH MTG_SSH_KEY MTG_LOG`.

**Caching (so we don't re-query every pick):** the pack→stats join is by `mtga_id`, which 17Lands
already provides — so Scryfall is only needed for cost/oracle-text. `warm` pulls the whole set
from Scryfall's `e:<set>` search in one paginated walk; after that, `pull`/`rank` for that set
make **zero** live queries until the 17Lands dataset's 24h cache expires. Caches live in `cache/`
(gitignored): `17lands_<SET>_<FMT>.json` (24h TTL) and `scryfall_arena.json` (persistent).
`--refresh` forces a 17Lands re-pull.

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

## Draft strategy fundamentals (Reid Duke, "Level One")

Durable principles to apply on top of the data — the 17Lands number tells you a card's
*average* value, but these decide whether it's right *for this deck, this pick, this game*.

- **Threats vs. answers.** The core tension of Magic. You win by deploying threats faster than
  they're answered, or by answering threats before they kill you. A pile of answers with no
  threats can't win — it just doesn't lose. **This is Albert's recurring failure** (answer-heavy,
  finisher-light). Bias picks toward proactive threats; treat "another removal spell" as having
  steep diminishing returns once the deck has ~5–6.
- **Who is the beatdown?** Every matchup has an aggressor and a defender; misassigning the role
  loses games. The faster/lower-curve deck must *race* (attack, force the issue); the slower deck
  must *stabilize and grind*. Albert's decks default to playing defense even when they're the
  beatdown — that's why he stabilizes but can't close. When his deck is the proactive one, the
  coaching is "you are the beatdown: curve out, attack, don't durdle."
- **Card advantage.** Two-for-ones and card draw win long games. But it's a *means*, not the goal —
  card advantage with no way to convert it to damage just delays the loss (see: his 1-3 control run).
- **Tempo.** Mana/turns efficiency. Cheap interaction, evasion, and on-curve threats let you do
  more per turn than the opponent. In Bo1 Quick Draft tempo/aggro is structurally favored over
  grindy control (no sideboard, games reward closing fast) — but per Albert's rule this is a
  *light* tiebreaker between close cards, not a reason to skip better cards.
- **Board position.** Control of the battlefield dictates combat. Evasive threats (flyers) and
  efficient bodies translate board control into a clock — exactly what closes the games he loses.
- **Mana & curve.** Consistent mana + a smooth curve = casting your spells on time. Cap top-end
  (~5–6 cards at 5+), fill 2–3, and don't strain a greedy 2-color base with a third color.
- **Mulligans (when he asks about a hand).** Keep hands that *advance your role* at acceptable risk:
  right land count, at least one early play, and a path to the game plan. Ship hands with no
  early action or no way to use the mana. Don't keep a clump of expensive cards on the play.
- **Combat heuristics.** Attack when it advances your role; block to preserve board control.
  Evaluate trades over future turns, not just immediate value. The beatdown attacks into
  unfavorable-looking boards more often than the defender does.
- **Bluffing / information.** Holding up open mana or attacking into a possible trick applies
  pressure and forces mistakes; a known-empty hand invites the opponent to take risks. Minor in
  Bo1-vs-bots, but relevant when he's reading a real opponent's lines.

The thread tying these to Albert: his data-first drafting is sound; his leak is **role and
closing** — he builds decks that don't lose rather than decks that win. Push threats, evasion,
and "you are the beatdown" framing over a marginal extra answer or card-draw spell.

## Notes / gotchas

- Scryfall `cards/arena` returns the front face for MDFCs; the script strips `//` for matching.
- `mtga.untapped.gg` pick-order pages and 17lands.com are the live sources; the **17Lands client
  app records drafts only — no live suggestions** (it was removed from Albert's laptop).
- Quick Draft is on the **Steam/Mac build** on his MacBook Pro (not the mini).
