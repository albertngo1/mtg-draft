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

## Drafting craft (Reid Duke, "Level One" — drafting only, not gameplay)

This is a **drafting** coach. The job is pick decisions + deckbuilding the pool — not in-game
play. Apply these on top of the data: the 17Lands number is a card's *average* value; these
decide whether it's the right *pick* for this deck and this seat. **Throughline for Albert: his
data-first drafting is sound; his leak is that he drafts decks that don't lose instead of decks
that win. Bias picks toward proactive threats, evasion, and a real way to close — over a marginal
extra removal or card-draw spell.**

### Card evaluation — what makes a card worth picking
- **Pick order backbone: bombs → premium removal → evasion → efficient creatures → filler.**
  "A bomb is a bomb" — raw game-winning power beats synergy and color considerations; take it P1P1
  even off-color and let it anchor you. Removal and evasion are the next tier; efficient creatures
  are the load-bearing majority of every deck.
- **Value = power × scarcity.** Premium removal ranks high because it's both strong *and* rare/
  contested. A merely-good common that always wheels is worth less than its raw power suggests
  (cross-check **ALSA**: low ALSA = take now / won't come back; high ALSA = you can wheel it).
- **Threats beat answers when you're *drafting*.** "There are no wrong threats" — a threat is never
  a dead card; an answer is dead when they have nothing to point it at. Draft **threat-dense** with
  a *focused* answer suite: removal that enables your threats (clears blockers) or covers a specific
  weakness. **Steep diminishing returns on a removal spell once the deck has ~5–6** — this is
  Albert's exact leak; stop taking the 7th piece of interaction over a body or a closer.
- **Evasion is a top draft priority** — flyers/menace win races and *close* the grindy games Albert
  loses. Weight evasive creatures up, especially for his decks.
- **Card advantage vs. tempo, as an evaluation lens.** Card-advantage cards (2-for-1s, repeatable
  value, "blanks" like a fat blocker) are worth more the longer games go; tempo cards (cheap,
  efficient, evasive) are worth more in fast games. Weight by what *your* deck wants — aggro/tempo
  prizes the latter, control the former. In Bo1 Quick Draft tempo leans favored, but that's a
  **light tiebreaker between close cards**, never a reason to skip a clearly better card.
- **Card quality can beat quantity** — one high-impact card is worth several weak ones; don't draft
  filler just to fill slots if a higher-ceiling card is available.
- **Flexibility / modality raises a card's floor** — modal, scalable (X-cost), or attack-and-block
  creatures are good picks when the power cost is small; they fill curve gaps and rescue awkward
  draws. Rarely your single best card, but reliable.
- **Irreplaceability can outweigh raw power.** Take the card you *can't* get later — bombs, removal,
  and **fixing/dual lands** — over a marginally stronger card you'll see again. Take fixing early to
  stay open and to enable later bombs.

### Reading the draft — signals, staying open, committing, pivoting
- **Stay open early, commit late.** Flexible through roughly **P1 picks 2–7**; **lock your colors by
  P1P8–9.** Strong drafters stay open longer to scoop bombs and slide into whatever's underdrafted;
  locking in P1P1–2 is a beginner crutch.
- **What an open color looks like:** premium cards arriving *late*, and/or a persistent *drought* of
  good cards in your color over several packs (the drafters upstream are taking them).
- **One late premium card is evidence, not proof.** Weigh *accumulating* evidence; don't torch your
  deck off a single pick. (Per Albert's rule: don't push a narrative onto picks.)
- **Signals are directional.** You **read** signals from your **right** (where your packs come from)
  and **send** signals to your **left** (what you pass tells downstream what's open). **Reading the
  wheel** — a good card circling back at P1P9+ — confirms that color/effect is underdrafted near you.
- **Pivoting:** if a new color is clearly a *tier* stronger, pivot **early and decisively** — the
  longer you wait the more certain you are but the less time you have to benefit; by ~P1P7–8 it's
  usually too late to switch cleanly. **P2 picks 2–3 are the last safe window.** If you're already
  committed with bombs/premium cards, stay the course and use **pack-2 reverse-direction signals**
  to find your *second* color.
- **Strengthen your own deck; don't hate-draft.** Especially here: **Quick Draft is vs. bots, so
  hate-drafting does literally nothing** — always take the best card for your deck.
- **Quick Draft caveat on signals (Arena-specific):** bots draft differently from humans — they pass
  strong cards (removal, good on-color uncommons) more freely, so **good cards wheel more often and
  signals are softer/noisier.** Practical effect: stay open a little longer, expect to pick up real
  playables late, and don't over-read a *single* late premium the way you would against humans.
  Lean on the 17Lands data as the anchor; treat bot-pass "signals" as weak evidence.

### Drafting toward an archetype (so the pool builds into a real deck)
- Have an end-state in mind and draft toward it, rather than reacting card-by-card. The three shapes,
  as *draft targets*:
  - **Aggro** — lowest curve, proactive 1–2 drops, minimal answers, needs **reach** (evasion + burn)
    to finish. Draft to *win the race*.
  - **Control** — high land count, card-draw, a few potent finishers; *needs inevitability* (a
    late-game that crushes). Structurally weak in Bo1 Quick Draft — avoid the pure answer-pile.
  - **Midrange** — versatile attack-*and*-block creatures, higher creature quality, removal + a few
    bombs. The default good Limited deck.
- **Albert's UR builds are tempo-midrange — lean them to the proactive/aggressor side:** prioritize
  cheap threats and evasion, keep removal lean, and make sure the deck has an actual *closer*
  (evasive finisher, go-wide payoff, or a bomb) rather than just card advantage. A deck needs a way
  to *win the long game* (inevitability) **or** to *end it fast* — draft toward one, not neither.

### Deckbuilding the pool (40-card Limited — Duke's concrete targets)
- **17–18 lands · ~23 nonland · 14–17 creatures · 5–8 noncreature spells** (of which **4–8 removal**,
  **0–2 combat tricks**). You want **~23 playables** out of the pool, plus basics.
- **Creature curve (peaks at three):** 1-drops 0–2 · 2-drops 2–4 · **3-drops 5–8** · 4-drops 2–3 ·
  5-drops ~2 · 6-drops 0–1. **Cap the top end — a pile of 5s is the trap** (it's why we cut/flex
  Albert's extra 5s). A genuinely better expensive card should *replace* a top-end slot, not stack
  on top of it.
- **Mana sources per color (out of ~17 lands):** can't-function-without = **11–12** · main color =
  **9–10** · secondary = **6–7** · **splash = 2–4**. Two-color ≈ even split (~9/9). Every added
  color adds risk — keep color count minimal; splash only impactful **4–6 drops** with real fixing,
  **never a 2-drop** (it can't be delivered on curve). Tapped duals are fine in slow decks, costly
  in fast ones; count fetch/choice lands as slightly less than a full source.
- **Common build pitfalls (Duke's "Draft Walkthrough"):** overvaluing expensive creatures while
  cheap playables run dry; neglecting early defense/curve in slow decks; over-splashing on shaky
  mana. Once your top-end/inevitability is secured, spend remaining picks on **curve + consistency,
  not more bombs.**

## Notes / gotchas

- Scryfall `cards/arena` returns the front face for MDFCs; the script strips `//` for matching.
- `mtga.untapped.gg` pick-order pages and 17lands.com are the live sources; the **17Lands client
  app records drafts only — no live suggestions** (it was removed from Albert's laptop).
- Quick Draft is on the **Steam/Mac build** on his MacBook Pro (not the mini).
