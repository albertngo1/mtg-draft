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

## Draft strategy fundamentals (Reid Duke, "Level One" — read from the source articles)

Apply these on top of the data: the 17Lands number is a card's *average* value; these decide
whether it's right *for this deck, this pick, this game*. **The throughline for Albert: his
data-first drafting is sound; his leak is role + closing — he builds decks that don't lose
instead of decks that win. Push threats, evasion, and "you are the beatdown" over a marginal
extra answer or card-draw spell.**

### Resources & the shape of a game
- **The two-stage game (the master skill).** Early game, *mana* is the bottleneck → **tempo**
  rules (develop the board fastest, use all your mana every turn, missed land drops/wasted mana =
  lost tempo). Late game, mana is abundant and hands empty → **card advantage** rules (squeeze
  value, grind). Correctly identifying which stage you're in is the key decision. Aggro wants to
  win in stage one; control wants to survive to stage two.
- **Card advantage.** Real edge = netting more usable cards than the opponent: 2-for-1s, removal,
  repeatable value, and "blanking" their cards (a big blocker neutralizing several attackers).
  *Virtual* card advantage counts too — their dead/flooded/outclassed cards. **Card quality can
  beat quantity; one high-impact threat beats several weak cards.** But card advantage is a
  *means* — with no way to convert it to damage it only delays losing (his 1-3 control run).
- **Tempo.** Board presence / pace. The proactive player holds the tempo edge (keeps mana up,
  forces the opponent to react). Cheap, efficient, evasive cards win on tempo before slower
  "better" cards come online. Pure tempo plays (bounce) trade cards for speed — only worth it when
  already ahead. In Bo1 Quick Draft tempo/aggro is structurally favored — but per Albert's rule
  it's a *light* tiebreaker between close cards, never a reason to skip a clearly better card.
- **Investment.** Value earlier compounds (an effect now enables more plays). Ramp/draw engines
  cost tempo up front; only worth it if the game lasts long enough to collect — invest in slow
  matchups, avoid vs fast aggro. When you do, point payoffs at immediate board impact.

### Threats, answers, inevitability
- **Threats vs. answers.** "There are no wrong threats" — a threat is never a dead card; an answer
  is dead when they have nothing to answer. Answer-heavy decks are reactive, follow the opponent's
  plan, and only *delay* losing. **This is Albert's recurring failure.** Draft threat-dense; keep
  a *focused* answer suite — removal that enables your threats (clears blockers) or covers a
  specific vulnerability. Steep diminishing returns on a removal spell past ~5–6.
- **Inevitability.** Who wins if the game goes infinitely long (unlimited mana, +30 cards each)?
  That player must *stall, draw, gain life, and wait*; the other must *force action and end it
  fast*. It's a matchup question, not an absolute. Evasion, engines, and lifegain/sweepers grant
  it; aggro often has it only in *short* games.

### Role — the single most important in-game read
- **Who is the beatdown?** Every game has an aggressor and a defender; getting it wrong loses with
  the better cards. Decide via: (1) whoever has **inevitability** must be the aggressor and force
  the game; (2) whoever can **win faster** takes the beatdown role. Roles are *fluid* in Limited —
  they shift with play/draw, draws, and board state; **reassess constantly. Albert's decks default
  to defense even when they're the beatdown — that's the root of "stabilize but can't close."** When
  his deck is the proactive one: curve out, attack, don't durdle.
- **Damage racing.** A race = neither can profitably block; first to zero loses. Life is asymmetric:
  **early life is cheap (take 3 to keep a mana creature), the last point is priceless — spend life
  early for board, hoard it late.** Chump-block once a creature has done its job, not before, not
  too late. **"Turn the corner":** stabilize → build board → swing with everything before they draw
  answers; even defensive decks want to end fast to deny draw steps. Race math: evasion + reach win
  races; attack whenever safe even while defending (one shaved turn = one fewer of their draws).

### Combat, sequencing, timing
- **Attack/block.** Creatures earn value every turn they attack or block — passivity wastes them,
  recklessness loses them. On even trades, generally attack if you can, block if you can; an even
  trade that saves life while developing favors the blocker (esp. on the draw). Make race trades
  *sooner*. The blocker has the information edge (acts last). Players bluff and block *less* than
  you'd expect — profitable attacks exist even with an empty hand.
- **Sequencing & timing.** Plan the whole turn before acting. Maximize what *you* know before your
  decisions, minimize what *they* know before theirs. Default: **lands before attacks** (hides your
  tricks/mana); **cast spells at the last possible moment** (keeps options open, multiplies what
  they play around) — exceptions: cast early if it gives info for this turn, or immediately if
  they're tapped out. Combat tricks last; deploy creatures *before* combat to tax their mana.
  Fire damage-removal before they can pump; unconditional removal before they untap (dodge
  protection/hexproof).
- **Flexibility.** Flexible/modal cards raise your floor and consistency — take them whenever the
  power cost is small. They fill curve gaps and rescue misaligned draws; they're rarely your single
  best play but they're insurance against variance.

### Playing the position
- **Ahead → simplify** (trade aggressively, a simple board is controllable; play around the
  specific cards that could reverse it, assume they have them). **Behind → complicate** (preserve
  decision points, play to your outs, take extra damage to keep outs alive, never concede early).
- **Safe vs. scared.** Playing safe = avoiding needless risk when a long game favors you. Playing
  *scared* = over-hedging vs unlikely cards, which loses even when they never had it — and **giving
  them extra draw steps is itself a real cost.** First ask whether a long game favors you; if you're
  being raced, you can't afford caution — push. Don't play around the sweeper vs control (they win
  off a clean board anyway). Use EV, not "good players always have it."

### Mulligans (when Albert asks about a hand)
- **"Two to Five Lands" rule:** keep 2–5 lands, mulligan 0/1/6/7 — right ~90% of the time. But land
  count isn't enough: also confirm the right **colors** and **castable spells on turns 1–3**.
- **Limited adjusts:** mulligan *less* than Constructed (slower, lower-power, no redundancy/tutors —
  each lost card hurts more). Rarely keep 1-landers (only on the draw with multiple 1-drops + a
  proactive play); keep a 6-lander only in extremes (bad mana needing all colors, or a single cheap
  bomb). Strained mana → keep imperfect hands with all your colors; clean mana → ship borderline
  hands. **Avoid the "needs both lands AND spells" trap.** Match to role: aggro ships slow hands
  even with good lands; mulligan harder into fast decks. Once you've already mulliganed, loosen up.
- **Play or draw:** **default to the play** (~always correct). Tempo edge is biggest in fast
  games/decks. Draw only when early races are unlikely and the game will go long (more common in
  Sealed than Draft).

### Drafting the deck
- **Pick order:** **bombs first** ("a bomb is a bomb" — beats synergy/color), then removal &
  evasion, then efficient creatures (the backbone). Value = power **×** scarcity (premium removal is
  high because it's both strong and rare).
- **Signals.** An open color = strong cards arriving *late*, and/or a persistent drought in your own
  color. One late premium is *evidence, not proof* — weigh accumulating evidence, don't overreact to
  one pick. **Read signals from your right** (where packs come from); **you send signals left.** A
  good card *wheeling* confirms that color/effect is under-drafted.
- **Color commitment:** stay flexible ~picks 2–7 of pack 1; lock by picks 8–9. Pack-2 picks 2–3 are
  the last safe window to switch — pivot *early and decisively* if a new color is clearly a tier
  stronger; if already committed with bombs, stay and read pack 2 for your second color. Take
  **fixing/dual lands early** to stay open. **Irreplaceability can beat raw power** — take the card
  you can't get later over a marginally stronger one you'll see again.
- **Strengthen your deck, don't hate-draft** (especially true here — Quick Draft is vs bots, so
  hate-drafting does literally nothing).

### Deckbuilding numbers (40-card Limited — Duke's concrete targets)
- **17–18 lands** · **~23 nonland** · **14–17 creatures** · **5–8 noncreature spells** (of which
  **4–8 removal**, **0–2 combat tricks**).
- **Creature curve (peaks at three):** 1-drops 0–2 · 2-drops 2–4 · **3-drops 5–8** · 4-drops 2–3 ·
  5-drops ~2 · 6-drops 0–1. (So cap top-end; this is why piling on 5s is the trap.)
- **Mana sources per color (out of ~17 lands):** can't-function-without = **11–12** · main = **9–10**
  · secondary = **6–7** · **splash = 2–4**. Two-color ≈ even split (~9/9). Every extra color adds
  risk — keep color count minimal; for splashes lean on nonbasic fixing, not basics. Tapped duals
  are fine in slow decks, costly in fast ones.
- **Archetype shapes:** *Aggro* = lowest curve, proactive 1–2 drops, minimal answers, needs reach
  (evasion + burn); you're the aggressor, win the race. *Control* = high land count, card draw,
  few potent finishers (low creature count blanks their removal), needs inevitability; you're the
  defender. *Midrange* = versatile cards that attack *and* block, higher creature quality, "defend
  then turn the corner" — must read the matchup and switch roles. **Albert's UR builds are
  tempo-midrange; the coaching is to lean them toward the proactive/aggressor side of that.**

## Notes / gotchas

- Scryfall `cards/arena` returns the front face for MDFCs; the script strips `//` for matching.
- `mtga.untapped.gg` pick-order pages and 17lands.com are the live sources; the **17Lands client
  app records drafts only — no live suggestions** (it was removed from Albert's laptop).
- Quick Draft is on the **Steam/Mac build** on his MacBook Pro (not the mini).
