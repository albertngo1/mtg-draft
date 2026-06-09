# MTGA Draft Coaching — Operating Manual

This is the manual for an **agent** (e.g. an LLM assistant) running live MTG Arena draft
coaching for a player. The repetitive data work (read pack → resolve names → fetch 17Lands →
rank) is automated by `mtg-draft.py`. Your job is the judgment: cross-referencing, color/curve
reads, and honest recommendations.

## Quick start

**At the start of each draft**, do two one-time prep steps so every pick is fast:

```bash
python3 mtg-draft.py warm --set <SET>        # caches card text + mana value for the whole set
```

…and **fetch a tier list ONCE and keep the grades in context for the whole draft** — e.g.
`WebFetch https://cardgamebase.com/<set>-draft-tier-list/` asking for *every* card's letter grade
(and the set's color-pair archetypes while you're there). Hold that list; cross-reference it per
pick from memory with **no further fetches.** One fetch up front beats paying ~10s on every close
pick.

**Set-specific expert notes — read at draft start if they exist for the set.** Pre-digested
strategy guides live flat in [`lords-of-limited/`](./lords-of-limited/) as `<SET>-draft-guide.md`
(see its README for the index). For the drafted set, **load that set's `<SET>-draft-guide.md` and
hold it in context for the whole draft** — each is a dense, lookup-optimized synthesis (meta read,
archetype/guild tier table, format principles, a **card-notes table** to cross-reference per pick,
signals, supersessions). Treat as *theory/expert opinion* (same weight as a tier-list grade), not
ground truth — **17Lands GIH WR stays primary.** Each guide encodes a **recency rule: on conflict
the newest source wins** (prerelease/preview takes are weak predictions; the format retrospective
is most authoritative — supersessions are marked inline). Per-episode notes + transcripts live in
each set's `lords-of-limited/<set>/sources/` — open one only to dig into a specific pick's rationale.

Then, each pick (when the player says "next" or starts a draft):

```bash
python3 mtg-draft.py pull                  # colors auto-detect from picks; pass --colors UR to override
```

That reads the **current** pack from `Player.log` (locally by default), and prints (a) a table
ranked by GIH WR with on-color cards marked `▸`, and (b) a **"what each card does"** section with
oracle text + P/T.

**Draft history (so you don't forget earlier picks):** `pull` also runs a side-car capture of the
whole `Player.log` stream and, each pick, refreshes **`drafts/current.json`** — a structured record
of the *entire* draft so far (every pack you saw, every card offered with its ratings, and what you
took at each pick). Run `python3 mtg-draft.py draft` to (re)build it on demand. **To answer any
question about earlier picks ("what did I pass at P1P5?", "what's my curve/colors so far?"), READ
`drafts/current.json` instead of re-reading the raw log** — the live log only retains the current
pack. For re-run/rotated sets with no live win-rate data yet, it auto-proxies PremierDraft ratings
(noted in `ratings_fmt`).

Then, on the current pack, you:

1. **Read what the cards actually do** — the text block is there so you judge *fit*, not just
   stats. A 55%-card that's a 2-drop flyer in your colors can beat a 58%-card that's a 6-mana
   durdle. Don't recommend off the GIH column alone.
2. **Cross-reference an external grade.** If `grades/<source>_<SET>.json` exists it auto-shows as a
   `DS` column (e.g. Draftsim) in the table. Otherwise pull the grade **from the tier list you
   fetched at draft start**, no new WebFetch.
   *Why a theory grade earns a column:* it's a *reviewer* grade built from human power-evaluation,
   not game outcomes — so it has **decorrelated error** from 17Lands. It agrees with the win data
   on bombs and diverges most on thin-sample / mushy-middle cards. So treat a grade-vs-17Lands
   disagreement as a *flag to look at the card by hand* (often a selection-bias-inflated synergy
   creature), **not** as proof the grade is right — in the thin-sample region neither source has
   ground truth. 17Lands GIH WR stays primary.
   *Do NOT add a second empirical source (Untapped/etc.).* Untapped's In-Hand WR is the same metric
   as 17Lands GIH WR (same-format rho≈0.955 — it agrees more than 17Lands does with itself across
   Quick-vs-Premier). A source that fails identically to 17Lands can't flag a 17Lands mistake, so
   it's pure bloat. Only sources with a *different method* (theory grades) add anything.
   *Adding a grade source for a set:* tier-list sites are usually JS-rendered with no clean API —
   paste the rendered HTML, parse name→grade into `grades/<source>_<SET>.json` (committed dir, NOT
   `cache/`), treat as theory grades.
3. Give the pick with reasoning, applying the strategy fundamentals below.

If the live read ever fails, fall back to the manual flow: have the player read you the pack, then
`python3 mtg-draft.py rank --colors UR <id1> <id2> ...`.

## The tool

| command | what it does |
|---|---|
| `python3 mtg-draft.py warm` | pre-cache the whole set's text + mana value (run once per set) |
| `python3 mtg-draft.py pull` | read latest `DraftPack` from `Player.log`, rank it + show card text |
| `python3 mtg-draft.py pool` | audit picks so far: creatures/spells/lands, curve, CABS check |
| `python3 mtg-draft.py rank ID...` | rank an explicit list of Arena card IDs |
| `python3 mtg-draft.py resolve ID...` | `name\|cmc\|color\|type` for IDs (handy for deck audits) |

Flags: `--set FIN` `--fmt PremierDraft` `--colors UR` `--days 120` `--brief` (table only)
`--refresh`. Config via env: `MTG_SET MTG_FMT MTG_COLORS MTG_LOG`. Reading the log from another
machine is opt-in via `--ssh` / `--ssh-key` (or `MTG_SSH` / `MTG_SSH_KEY`) — see the README's
"Advanced" section.

**Caching (so you don't re-query every pick):** the pack→stats join is by `mtga_id`, which 17Lands
already provides — so Scryfall is only needed for cost/oracle-text. `warm` pulls the whole set from
Scryfall's `e:<set>` search in one paginated walk; after that, `pull`/`rank` for that set make
**zero** live queries until the 17Lands dataset's 24h cache expires. Caches live in `cache/`
(gitignored): `17lands_<SET>_<FMT>.json` (24h TTL) and `scryfall_arena.json` (persistent).
`--refresh` forces a 17Lands re-pull.

**New set each season:** just change `--set`/`--fmt` (or `MTG_SET`). Everything else is generic.
Find the current event's set code in the log: the pack payload has `"EventName":"<FMT>_<SET>_<date>"`.

## How the live read works (for when the script breaks)

- Log: read locally by default from the per-OS `Player.log` path (override with `MTG_LOG`); the
  README lists the default path for each platform. SSH mode is opt-in (`--ssh`/`--ssh-key`).
- The current pack is the **last** line matching `DraftPack`. Shape:
  `{"CurrentModule":"...Draft","Payload":"{...\"DraftPack\":[\"<id>\",...],\"PickedCards\":[...]}"}`
  `PackNumber`/`PickNumber` are 0-indexed; `PickedCards` is everything taken so far.
- IDs are MTGA grpIds = Scryfall Arena IDs: `https://api.scryfall.com/cards/arena/<id>`
  (needs `Accept: application/json` or you get HTTP 400).
- 17Lands: `https://www.17lands.com/card_ratings/data?expansion=<SET>&format=<FMT>&start_date=..&end_date=..`
  Columns used: `ever_drawn_win_rate` (GIH WR), `drawn_improvement_win_rate` (IWD), `avg_seen` (ALSA).

## Coaching rules

- **Lead with the data.** GIH WR is the primary signal, always. Present the table first.
- **Always show ALSA.** Low ALSA = take now, won't wheel. (The script always includes it.)
- **Cross-reference the external grade** (tier list, fetched once at draft start and held in
  context) on meaningful/close picks. Format: Card | Color | GIH WR | IWD | ALSA | External Grade.
  Skip it on blowout-obvious picks.
- **Push back, don't capitulate.** When the player challenges a pick, re-examine honestly. If the
  pick was right, hold ground with a full argument — coaching means disagreeing when the data says so.
- **Don't over-correct on small samples.** A 1-3 run is variance, not proof. Don't push a narrative.
- **Bo1 / closing-speed lens is a LIGHT tiebreaker only** — use it between cards that are otherwise
  close on data, never to skip a clearly better card.
- **Match response depth to pick difficulty (keep turns fast — your output is the bottleneck, the
  data is ~2s).** *Obvious pick* (one card clearly best on-color, big GIH gap, no curve/signal
  tension) → compact table of the top few + **"Pick: X — one-line reason."** *Close / contested
  pick* (top 2–3 within ~1.5% GIH, or a curve/CABS/signal tradeoff, or the player challenges) →
  full treatment: card text, grade, the comparison, the argument. Don't write an essay for a
  blowout pick. The non-negotiables stay cheap: the table still shows ALSA + grade; pushback only
  fires when a pick is questioned.

GIH WR rough guide: **57%+ bomb · 54–57% excellent · 52–54% solid · 50–52% filler · <50% avoid.**

## Common leaks to coach against (use for tiebreakers & deckbuilding)

These are the most common drafting mistakes; watch the player's pool for them and steer against them.

- **Committing to colors too early.** Locking colors in P1P1–2 is a beginner crutch; it forecloses
  open lanes. The coaching fix: **picks 1–5 take the best card on raw power, color be damned;
  narrate wheel/signal evidence from ~pick 4; explicitly call the open lane around picks 6–8; lock
  by ~P1P9–10 (P2P2–3 = last clean pivot).** When the player reaches to "stay in our colors" before
  pick 8, push back. This is a *timing* correction, NOT card-evaluation bias — keep 17Lands GIH WR
  primary on every pick.
- **Answer-heavy, finisher-light decks** that stabilize but **can't close** grindy late games.
  Remedy: prioritize **evasion (flyers)**, proactive threats, and real finishers over a 9th piece
  of interaction or card draw.
- **Curve discipline:** cap **~5–6 cards at 5+ mana**. A genuinely better card replaces a top-end
  slot rather than getting stacked on top. One bomb at 6–7 is fine; a pile of 5s is the trap.
- **Hate-drafting in Quick Draft (vs. bots) does nothing** — bots aren't your opponents. Always take
  the best card for your deck.
- **Splashing:** only impactful 4–6 drops, and only with real fixing. **Never splash a 2-drop** (it
  wants to be cast on curve; a splash can't deliver early mana). Watch the greedy base — double-pip
  cards (e.g. `1UURR`) already strain a 2-color manabase.
- **Deckbuild target:** ~17 lands, ~14–16 creatures, the rest removal/tempo + bombs.

## Drafting craft (Reid Duke, "Level One" — drafting only, not gameplay)

This is a **drafting** coach. The job is pick decisions + deckbuilding the pool — not in-game play.
Apply these on top of the data: the 17Lands number is a card's *average* value; these decide
whether it's the right *pick* for this deck and this seat. **Throughline: data-first drafting is
sound, but the common failure is drafting decks that don't *lose* instead of decks that *win*. Bias
picks toward proactive threats, evasion, and a real way to close — over a marginal extra removal or
card-draw spell.**

### Reading the 17Lands numbers (and their traps)
- **GIH WR is the anchor, but check the sample size (`N`).** A card with only a few hundred games
  has a noisy/unreliable win rate; `n/a` usually means "barely drafted" (often = weak/niche). Don't
  crown or bury a card on a small-N number — say it's uncertain.
- **GIH WR has selection bias — especially on payoff/build-around cards.** The number reflects the
  decks that *played* the card. A multicolor payoff, a spells-matter creature, a graveyard card,
  etc. posts a high WR because it sat in decks built to enable it — **that doesn't transfer to a
  deck that can't.** Discount payoff cards for *your* deck's actual support. Conversely, a
  colorless/always-castable card's WR transfers well.
- **What each column is for:** **GIH WR** = overall power (primary); **IWD** = how much it *swings*
  a game when drawn (impact — high IWD + modest GIH = high-impact but wants a longer game or a
  setup); **ALSA** = how late it wheels (low = take now / contested; high = you can speculate it
  comes back). Always show ALSA.
- **Match the format.** Use the data for the format being drafted (QuickDraft vs PremierDraft). If
  QuickDraft data is thin for a new set, PremierDraft is a larger-sample proxy — note when you fall
  back to it. (`--fmt` controls this.)
- **The tool prints oracle text — read it.** A 55% 2-drop flyer in your colors can beat a 58%
  6-mana durdle. Judge cost, color, evasion, and role, not just the GIH column.

### Card evaluation — what makes a card worth picking
- **Pick order backbone: bombs → premium removal → evasion → efficient creatures → filler** (the
  "BREAD" heuristic: Bombs, Removal, Evasion, Aggro/Advantage, Dregs). "A bomb is a bomb" — raw
  game-winning power beats synergy and color considerations; take it P1P1 even off-color and let it
  anchor you. Removal and evasion are the next tier; efficient creatures are the load-bearing
  majority of every deck.
- **Value = power × scarcity.** Premium removal ranks high because it's both strong *and* rare/
  contested. A merely-good common that always wheels is worth less than its raw power suggests
  (cross-check **ALSA**: low = take now / won't come back; high = you can wheel it).
- **Threats beat answers when you're *drafting*.** "There are no wrong threats" — a threat is never
  a dead card; an answer is dead when they have nothing to point it at. Draft **threat-dense** with
  a *focused* answer suite: removal that enables your threats (clears blockers) or covers a specific
  weakness. **Steep diminishing returns on a removal spell once the deck has ~5–6** — stop taking
  the 7th piece of interaction over a body or a closer.
- **Removal quality rubric.** Not all removal is equal — *premium* = cheap, **unconditional**, and
  kills (ideally exiles) most things at instant speed. *Discount* it when it's expensive (a 5-mana
  kill spell is slow), conditional (only small creatures / only attackers / only one card type /
  needs a setup), sorcery-speed, or "tuck/bounce" that doesn't permanently answer.
- **Evasion is a top draft priority** — flyers/menace win races and *close* grindy games. Weight
  evasive creatures up.
- **Card advantage vs. tempo, as an evaluation lens.** Card-advantage cards (2-for-1s, repeatable
  value, fat blockers) are worth more the longer games go; tempo cards (cheap, efficient, evasive)
  are worth more in fast games. Weight by what *your* deck wants — aggro/tempo prizes the latter,
  control the former. In Bo1 Quick Draft tempo leans favored, but that's a **light tiebreaker
  between close cards**, never a reason to skip a clearly better card.
- **Card quality can beat quantity** — one high-impact card is worth several weak ones; don't draft
  filler just to fill slots if a higher-ceiling card is available.
- **Flexibility / modality raises a card's floor** — modal, scalable (X-cost), or attack-and-block
  creatures are good picks when the power cost is small; they fill curve gaps and rescue awkward
  draws. Rarely your single best card, but reliable.
- **Irreplaceability can outweigh raw power.** Take the card you *can't* get later — bombs, removal,
  and **fixing/dual lands** — over a marginally stronger card you'll see again. Take fixing early to
  stay open and to enable later bombs.

### Reading the draft — signals, staying open, committing, pivoting
- **At draft start, learn the set's archetypes.** Pull the set's color-pair overview so you know the
  ~10 two-color gameplans and which are strong — it frames every pick and tells you what a wheeling
  card signals. **If the set has a synthesized guide in this repo** (see Quick start —
  [`lords-of-limited/<SET>-draft-guide.md`](./lords-of-limited/)), load it for the format's meta read,
  tier list, and card notes before the first pick.
- **Stay open early, commit late.** Flexible through roughly **P1 picks 2–7**; **lock your colors by
  P1P8–9.** Strong drafters stay open longer to scoop bombs and slide into whatever's underdrafted.
- **What an open color looks like:** premium cards arriving *late*, and/or a persistent *drought* of
  good cards in your color over several packs (the drafters upstream are taking them).
- **One late premium card is evidence, not proof.** Weigh *accumulating* evidence; don't torch your
  deck off a single pick.
- **Signals are directional.** You **read** signals from your **right** (where your packs come from)
  and **send** signals to your **left**. **Reading the wheel** — a good card circling back at P1P9+
  — confirms that color/effect is underdrafted near you.
- **Pivoting:** if a new color is clearly a *tier* stronger, pivot **early and decisively** — by
  ~P1P7–8 it's usually too late to switch cleanly. **P2 picks 2–3 are the last safe window.** If
  you're already committed with bombs/premium cards, stay the course and use **pack-2
  reverse-direction signals** to find your *second* color.
- **Strengthen your own deck; don't hate-draft.** Especially in **Quick Draft (vs. bots), where
  hate-drafting does literally nothing** — always take the best card for your deck.
- **Raredraft only on dead picks.** Arena keeps *every* card you draft (collection value), so in a
  pick where nothing is playable for your deck, taking a rare/mythic for the collection is fine —
  but **never over an actual playable.**
- **Quick Draft caveat on signals (Arena-specific):** bots draft differently from humans — they pass
  strong cards more freely, so **good cards wheel more often and signals are softer/noisier.**
  Practical effect: stay open a little longer, expect real playables late, and don't over-read a
  *single* late premium the way you would against humans. Lean on the 17Lands data as the anchor.

### Drafting toward an archetype (so the pool builds into a real deck)
- Have an end-state in mind and draft toward it, rather than reacting card-by-card. The three shapes
  as *draft targets*:
  - **Aggro** — lowest curve, proactive 1–2 drops, minimal answers, needs **reach** (evasion + burn)
    to finish. Draft to *win the race*.
  - **Control** — high land count, card-draw, a few potent finishers; *needs inevitability*.
    Structurally weak in Bo1 Quick Draft — avoid the pure answer-pile.
  - **Midrange** — versatile attack-*and*-block creatures, higher creature quality, removal + a few
    bombs. The default good Limited deck.
- **Tempo-midrange decks want the proactive side:** prioritize cheap threats and evasion, keep
  removal lean, and make sure the deck has an actual *closer* (evasive finisher, go-wide payoff, or
  a bomb) rather than just card advantage. A deck needs a way to *win the long game* (inevitability)
  **or** to *end it fast* — draft toward one, not neither.

### Deckbuilding the pool (40-card Limited — Duke's concrete targets)
- **17–18 lands · ~23 nonland · 14–17 creatures · 5–8 noncreature spells** (of which **4–8
  removal**, **0–2 combat tricks**). You want **~23 playables** out of the pool, plus basics.
- **Creature curve (peaks at three):** 1-drops 0–2 · 2-drops 2–4 · **3-drops 5–8** · 4-drops 2–3 ·
  5-drops ~2 · 6-drops 0–1. **Cap the top end — a pile of 5s is the trap.** A genuinely better
  expensive card should *replace* a top-end slot, not stack on top of it.
- **Mana sources per color (out of ~17 lands):** can't-function-without = **11–12** · main color =
  **9–10** · secondary = **6–7** · **splash = 2–4**. Two-color ≈ even split (~9/9). Every added
  color adds risk — keep color count minimal; splash only impactful **4–6 drops** with real fixing,
  **never a 2-drop**. Tapped duals are fine in slow decks, costly in fast ones.
- **Common build pitfalls (Duke's "Draft Walkthrough"):** overvaluing expensive creatures while
  cheap playables run dry; neglecting early defense/curve in slow decks; over-splashing on shaky
  mana. Once your top-end/inevitability is secured, spend remaining picks on **curve + consistency,
  not more bombs.**

### CABS — the board-density discipline (Marshall Sutcliffe)
**CABS = "Cards that Affect the Board State"**: creatures, removal, and combat tricks. The thesis:
**~99% of Limited games are won with creatures**, so a deck needs a high *density* of board-affecting
cards and only a *few* that don't touch the board. This is the baseline aggressive Limited shape —
and it's the antidote to the "answer-heavy / can't-close, too many durdle spells" pattern.
- **Count your CABS as you draft and build.** Target the deck around **15–18 creatures** plus your
  removal/tricks; treat non-board cards (card draw, counters, enchantments, lifegain) as a small
  *budget*, not a free-for-all.
- Sutcliffe's commandments (the baseline "CABS deck"): **two colors only; strong curve weighted to
  2–3-mana creatures; 15–18 creatures; minimize card-draw / enchantments / counters / lifegain;
  prefer cards that stand alone over fragile synergies; straightforward proactive plan; consistent
  over high-variance.**
- **How to apply it as a data-led coach (important nuance):** CABS is a *deck-shape* discipline, not
  a card-by-card override. Don't refuse a card-draw spell the 17Lands data loves — but **use CABS as
  the tiebreaker and the budget cap:** when a non-board value card is close to a body/removal, take
  the board card, and notice when the pool is drifting durdle-heavy. Default toward maximizing CABS
  density and a 2–3-drop-heavy curve; that's the build that closes games.

## Notes / gotchas

- Scryfall `cards/arena` returns the front face for MDFCs; the script strips `//` for matching.
- The **17Lands client app records drafts only — it gives no live pick suggestions.** This tool is
  the live layer; the client is for post-draft review.
- MTGA draft queues: **Quick Draft** (vs. bots, Bo1, cheapest), **Premier Draft** (vs. humans, Bo1),
  **Traditional Draft** (vs. humans, Bo3 with sideboard — the only Bo3 queue). Control/sideboard-
  dependent decks are viable in Traditional; Premier and Quick both reward proactive/tempo decks.
