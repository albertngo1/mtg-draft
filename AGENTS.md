# MTGA Draft Coaching — Operating Manual

This is the manual for an **agent** (e.g. an LLM assistant) running live MTG Arena draft
coaching for a player. The repetitive data work (read pack → resolve names → fetch 17Lands →
rank) is automated by `src/mtg-draft.py`. Your job is the judgment: cross-referencing, color/curve
reads, and honest recommendations.

## Quick start

**At the start of each draft**, do these one-time prep steps so every pick is fast:

```bash
python3 src/mtg-draft.py warm  --set <SET>                      # caches card text + mana value
python3 src/mtg-draft.py cards --set <SET> > data/cache/cards_<SET>.ndjson   # whole-set lean data
```

**Build the `cards` NDJSON once, then grep the pack's IDs out of it per pick.** It's one JSON record
*per line* — `id, name, color, cmc, pt, type, grade, gih, gp, pr, alsa, iwd, n, text, guide, inflation`
(where **gp** = Games Played win rate and **pr** = play rate, the % of decks that maindeck it) —
i.e. every card's stats AND oracle text AND **expert guide note AND inflation flag** (the last two
the live `pull` table does *not* print inline). It's all *static* for the draft, so it never needs
re-fetching. Each pick: run `pull --brief` (just the pack's IDs + the deck-state line — tiny), then
`grep '"id": "<id>"' data/cache/cards_<SET>.ndjson` for those IDs → the full card data, instant and
local. This kills per-pick oracle-text streaming and every "let me read the card" second fetch — the
main time-to-turn cost — AND surfaces the guide/inflation that the table omits. (A ~320-card set is
~34k tokens / one giant payload, so grep-per-pick beats loading it all into context; if you do want
it resident, the NDJSON reads in chunks by line.)

…and **fetch a tier list ONCE and keep the grades in context for the whole draft** — e.g.
`WebFetch https://cardgamebase.com/<set>-draft-tier-list/` asking for *every* card's letter grade
(and the set's color-pair archetypes while you're there). Hold that list; cross-reference it per
pick from memory with **no further fetches.** One fetch up front beats paying ~10s on every close
pick.

**Set-specific expert notes — read at draft start if they exist for the set.** Pre-digested
strategy guides live flat in [`draft-guides/lords-of-limited/`](./draft-guides/lords-of-limited/) as `<SET>-draft-guide.md`
(see its README for the index). For the drafted set, **load that set's `<SET>-draft-guide.md` and
hold it in context for the whole draft** — each is a dense, lookup-optimized synthesis (meta read,
archetype/guild tier table, format principles, a **card-notes table** to cross-reference per pick,
signals, supersessions). **This guide is the lead lens for every pick** — the set's archetypes,
which color pairs are strongest *in this set*, and the card's role within them drive the
recommendation — and it **decodes** the 17Lands columns: every GIH WR is *archetype-conditional* (the
soup deck's number, not yours), and the guide tells you which archetype's number you're reading. So
**ALSA** is the one orthogonal signal, and **GIH WR transfers or inflates by card type** (see Coaching rules).
Each guide encodes a **recency rule: on conflict
the newest source wins** (prerelease/preview takes are weak predictions; the format retrospective
is most authoritative — supersessions are marked inline). Each guide ends with a `## Source episodes`
list (`date — title (youtube_id)`); raw transcripts for the bulk sets live in `data/subs/lords-of-limited/<CODE>/`
(gitignored).

A **second** expert-notes source lives flat in [`draft-guides/numot/`](./draft-guides/numot/) as `<SET>.md` — draft tips
distilled from NumotTheNummy (Kenji Egashira) draft VODs (`draft-guides/numot/general-tips.md` holds the
evergreen principles). If the drafted set has a `draft-guides/numot/<SET>.md`, load it at draft start alongside
the LoL guide and treat both as lead-lens expert opinion (GIH WR remains a tiebreaker only).
`MKM.md`/`SOS.md` are deepest (full VOD coverage); the rest sample ~4 end-of-format VODs. Numot's
`vs Lords of Limited` sections flag where the two experts disagree.

Then, each pick (when the player says "next" or starts a draft):

```bash
python3 src/mtg-draft.py pull                  # set/fmt auto-detect from the draft's EventName,
                                               # colors from picks; --set/--fmt/--colors override
```

That reads the **current** pack from `Player.log` (locally by default), and prints (a) a **`DECK`
deck-state line** read from `data/drafts/current.json` — creature/spell counts, removal, two-drops,
curve, archetype lean, top themes (`THEMES:`), a `TRIBES:` line of creature-subtype counts
(e.g. `Detective 5`, only subtypes at ≥3 shown — surfaces an emergent tribal lane the way `THEMES:`
surfaces mechanics), the open-color signal, premiums passed by color, and a `NEED`
line of **progress-scaled** gaps (so it reads as a live priority, not end-state alarm-bells at
pick 3) — so the live deck picture is in front of you every pick; (b) a table ranked by GIH WR with
on-color cards marked `▸`; and (c) a **"what each card does"** section with oracle text + P/T.
**NEVER state a card count or how many copies of a card you have from memory — read the `POOL (N): …` line `pull` prints (the exact taken cards, live-sourced) every pick.** **Lead with the `DECK` line** and let its `NEED` steer the pick (creature-priority when bodies
are below target, stop stacking removal once at the cap, lean toward the open colors).

**Draft history (so you don't forget earlier picks):** a side-car capture mirrors the whole
`Player.log` stream and, each pick, auto-refreshes the structured store — **no manual `pull` needed
as long as the capture daemon runs.** Each draft is persisted as a self-contained bundle folder
`data/drafts/<set>_<YYYY-MM-DD>_<fingerprint>/` (the date is parsed from the draft's `EventName`
8-digit suffix — e.g. `QuickDraft_MKM_20260611` → `2026-06-11`, falling back to the bundle's
`raw.log` mtime when the EventName has no parseable date; it's **deterministic**, never wall-clock,
so it stays the idempotency key and a re-run overwrites the same folder) holding `draft.json` (the
enriched cumulative store), `raw.log`
(this draft's stream slice), and `replay.md` (the coached audit, auto-written **once** when the
draft first completes and never re-rendered after that — re-run `src/replay.py <draft.json>
<replay.md>` by hand to refresh one). The replay includes a model-written `🤖 Take` per pick (one
`claude -p` call fed each pick's point-in-time state) **by default whenever the gitignored
`claude-token.txt` exists at the repo root** — the token file is the opt-in; set `MTG_REPLAY_AI=0`
to force the deterministic-only replay (or `=1` to force takes on). The most recent draft's
`draft.json` is also mirrored to **`data/drafts/current.json`**.
Run `python3 src/mtg-draft.py draft` to (re)build on demand. **To answer any question about earlier
picks ("what did I pass at P1P5?", "what's my curve/colors so far?"), READ `data/drafts/current.json`
(or a specific draft's `draft.json`) instead of re-reading the raw log** — the live log only retains
the current pack.

*The follower is poll-based, not `tail -F`.* MTGA buffers/flushes its `Player.log` in bursts and
rewrites/truncates it; an `ssh tail -F` follows unreliably (it can stay alive but stop delivering
bytes — a silent wedge). The remote follower instead **polls**: each tick it reads the remote size
(`wc -c`) and fetches only the bytes past its offset (`tail -c +N`); a smaller size means truncation,
so it resets the offset and re-reads. This keeps the capture **self-sufficient — `current.json` stays
fresh with no dependence on the `pull`/AI path** (verify with a standalone `watch`). Diagnostics (byte-arrival cadence,
truncation resets, ssh errors, idle gaps) log always-on to **`data/logs/capture-debug.log`** (capped).
A command-path health check still recycles a follower whose stream has gone stale.
*Lead every pick with the deck-state line `pull` prints* (`DECK (current.json): N creatures · …`,
read from the structured store): when creatures are below the 15–17 target, bias picks toward bodies.
*The ETL is truncation-resilient.* When a truncation makes the follower re-dump a short copy of a draft
already captured in full, the reconstructor collapses stream segments by fingerprint and **keeps the
most-complete (max-picks) instance**, so a truncated re-dump can never regress a draft's history. Each pick has a cumulative `running` block (curve, counts, what you've passed by color +
premiums passed by color, **plus `premiums_seen_by_color` / `premiums_seen_readable`** — premiums
SEEN (taken + passed) by color, the *unconfounded* openness read, plus **`needs` / `needs_readable`** — what the deck-so-far is still short
on, scaled to draft progress, e.g. `"2-drops (1), removal (~0)"` or `"on track"`; steer the next
pick toward these gaps), offered cards carry `wheel` (true only on a real 8-player lap, pick≥9),
`tags`, and — when applicable — **`inflation`** (the card's GIH WR is selection-bias-inflated; a
Converge/colors-of-mana or `{X}` card whose number reflects soup/big-X pilots, NOT your 2-color
deck — the Snarl Song trap, with a plain-English caveat to read it well below the headline) and
**`guide`** (the LoL set guide's expert one-liner on that card). The pool rolls up into `themes` +
`archetype_lean` + `open_color_signal` (colors with premiums still SEEN — taken + passed — late,
pick≥5) — use these for signal reads and deckbuilding, don't recompute them.
**Read openness from premiums SEEN late, NOT from premiums *passed*.** A premium surviving to pick
5+ means that color is underdrafted upstream *whether or not you took it*. `passed_by_color` /
`premiums_passed_by_color` count only cards you DIDN'T take — so they're **structurally blind to
your own drafted colors** (you keep the premiums you take, so your main color never accrues a passed
count and reads as dry/closed — e.g. you're being fed green every pack and scooping it, yet "green:
1 passed" reads as dead). That's the confound the SEEN metrics fix: `premiums_seen_by_color` and the
SEEN-late `open_color_signal` include taken + passed, so your own heavily-drafted color reads
correctly. Keep `passed_by_color` / `premiums_passed_by_color` only as the **"what am I shipping
left / signaling to my left"** view — never as the openness read for your own colors.
**Color signals are pre-spelled-out** for you and the player: `running.passed_readable` /
`running.premiums_passed_readable` / **`running.premiums_seen_readable`** (e.g. `"28 green, 27 red,
14 blue"`) and `analysis.open_color_readable` (the seen-late open-lane line) — **always present
these in plain English ("28 green premiums seen"), never as `G28 R27` shorthand.** The raw `*_by_color` maps and per-entry `color_name`
are still there if you need the numbers. For re-run/rotated sets with no live win-rate data yet,
**both the store AND the live `pull`/`rank` table** auto-proxy the set's original PremierDraft
ratings over a wide historical window (noted in `ratings_fmt` and in the table header).

Then, on the current pack, you:

1. **Start from the guide, not the table.** Which color pairs are strongest *in this set*, what
   archetype is the pool building toward, and what role does this card play in it? The guide's
   card-notes + the set's archetype tiers are the lead lens — lead the recommendation with them.
2. **Read what the cards actually do** — the text block is there so you judge *fit*, not just
   stats. A 2-drop flyer in your colors and on-archetype beats a higher-GIH 6-mana durdle. Don't
   recommend off the GIH column at all — it's a tiebreaker, not the headline.
3. **Cross-reference an external grade.** If `grades/<source>_<SET>.json` exists it auto-shows as a
   grade column labeled by source — `DS` (Draftsim, x/5), `CGB` (CardGameBase, letter tier A+→F),
   or `LG` (LimitedGrades); the first source found for the set wins (priority DS→CGB→LG). Split/MDFC
   cards are matched on their front face automatically. Otherwise pull the grade **from the tier list
   you fetched at draft start**, no new WebFetch.
   *Why a theory grade earns a column:* it's a *reviewer* grade built from human power-evaluation,
   not game outcomes — so it has **decorrelated error** from 17Lands. It agrees with the win data
   on bombs and diverges most on thin-sample / mushy-middle cards. So treat a grade-vs-17Lands
   disagreement as a *flag to look at the card by hand* (often a selection-bias-inflated synergy
   creature), **not** as proof the grade is right — in the thin-sample region neither source has
   ground truth. The reviewer grade and the guide are the power read; GIH WR only breaks ties.
   *Do NOT add a second empirical source (Untapped/etc.).* Untapped's In-Hand WR is the same metric
   as 17Lands GIH WR (same-format rho≈0.955 — it agrees more than 17Lands does with itself across
   Quick-vs-Premier). A source that fails identically to 17Lands can't flag a 17Lands mistake, so
   it's pure bloat. Only sources with a *different method* (theory grades) add anything.
   *Adding a grade source for a set:* tier-list sites are usually JS-rendered with no clean API —
   paste the rendered HTML, parse name→grade into `grades/<source>_<SET>.json` (committed dir, NOT
   `data/cache/`), treat as theory grades. **CardGameBase is server-rendered**, so its tier list IS
   WebFetch-able directly (`cardgamebase.com/<set>-draft-tier-list/`) — that's how `cardgamebase_MKM.json`
   was built. Draftsim's pick-order pages are JS-rendered and need the paste-the-HTML route.
4. Give the pick with reasoning, applying the strategy fundamentals below.

If the live read ever fails, fall back to the manual flow: have the player read you the pack, then
`python3 src/mtg-draft.py rank --colors UR <id1> <id2> ...`.

## The tool

| command | what it does |
|---|---|
| `python3 src/mtg-draft.py warm` | pre-cache the whole set's text + mana value (run once per set) |
| `python3 src/mtg-draft.py cards` | dump the whole set's lean per-card data as JSON — load into context once per draft so each pick is a lookup, not a re-fetch |
| `python3 src/mtg-draft.py pull` | read the current pack from `Player.log` (Quick `DraftPack` or Premier `Draft.Notify`), rank it + show card text |
| `python3 src/mtg-draft.py pool` | audit picks so far: creatures/spells/lands, curve, CABS check |
| `python3 src/mtg-draft.py watch` | stream the ranked table standalone each time a new pack appears |
| `python3 src/mtg-draft.py rank ID...` | rank an explicit list of Arena card IDs |
| `python3 src/mtg-draft.py resolve ID...` | `name\|cmc\|color\|type` for IDs (handy for deck audits) |
| `python3 src/mtg-draft.py draft` | (re)build the structured store from the capture stream → `data/drafts/current.json` + summary |
| `python3 src/mtg-draft.py capture [status\|stop]` | show / start / stop the background log-capture daemon |

Flags: `--set FIN` `--fmt PremierDraft` `--colors UR` `--days 120` `--brief` (table only)
`--refresh`. Config via env: `MTG_SET MTG_FMT MTG_COLORS MTG_LOG`. For `pull`/`pool`/`watch`,
set/fmt **auto-detect from the live draft's EventName**; precedence is flag > EventName > env >
default (so a stale `MTG_SET` can't silently rank against the wrong set). The fmt slot is adopted
only when it's a real 17Lands format — special events (`MWM_SOS_...`) put junk there. Reading the
log from another machine is opt-in via `--ssh` / `--ssh-key` (or `MTG_SSH` / `MTG_SSH_KEY`) — see
ARCHITECTURE.md's "Advanced: read the log from another machine (SSH)" section (and its warning that
the key must run a normal login shell, **not** a forced-command / reverse-tunnel key).

**Caching (so you don't re-query every pick):** the pack→stats join is by `mtga_id`, which 17Lands
already provides — so Scryfall is only needed for cost/oracle-text. `warm` pulls the whole set from
Scryfall's `e:<set>` search in one paginated walk; after that, `pull`/`rank` for that set make
**zero** live queries until the 17Lands dataset's 24h cache expires. Caches live in `data/cache/`
(gitignored): `17lands_<SET>_<FMT>.json` (24h TTL) and `scryfall_arena.json` (persistent).
`--refresh` forces a 17Lands re-pull.

Each Scryfall entry stores `cmc`/`mana`/`pt`/`color`/`rarity`/`text` **plus** the parsed
`type_line` and its split `types` (supertypes+card types, e.g. `["Legendary","Creature"]`) and
`subtypes` (post-dash, e.g. `["Human","Detective"]` — so creature tribes are tracked now, not just
the broad `type`), along with `keywords`, `loyalty`, and `color_identity`. Those structured fields
flow onto every card record in `draft.json`/`current.json` and feed the `tribes`/`tribes_readable`
aggregation. The cache is **schema-versioned**: each entry stamps `_v` (current schema = 2). On
load, an entry missing `_v`/below schema and lacking the rich fields is treated as a cache miss and
transparently re-fetched, so any set **self-heals** to the rich schema on its next draft — no manual
`warm --refresh` needed after a schema bump.

**New set each season:** nothing to change for the live commands — `pull`/`pool`/`watch` detect
set/fmt from the pack payload's `"EventName":"<FMT>_<SET>_<date>"`. Just `warm --set <SET>` once
(and add grades/guide files if available). `--set`/`MTG_SET` still work as overrides.

## How the live read works (for when the script breaks)

- Log: read locally by default from the per-OS `Player.log` path (override with `MTG_LOG`); the
  ARCHITECTURE.md lists the default path for each platform. SSH mode is opt-in (`--ssh`/`--ssh-key`).
- Quick Draft (vs bots): the current pack is the **last** line matching `DraftPack`. Shape:
  `{"CurrentModule":"...Draft","Payload":"{...\"DraftPack\":[\"<id>\",...],\"PickedCards\":[...]}"}`
  `PackNumber`/`PickNumber` are 0-indexed; `PickedCards` is everything taken so far.
- Premier / Traditional Draft (vs humans): there is **no `DraftPack`**. The pack is the last
  `Draft.Notify` (plain JSON, `PackCards` is a CSV, `SelfPack`/`SelfPick` are **1-indexed**); picks
  are `MakePick` (escaped JSON `GrpIds`, logged twice per pick — dedupe by `(Pack, Pick)`); there is
  no cumulative pool, so it's rebuilt from `MakePick`, and the event/set/fmt come from the event-join
  course line (`…EventName…:"PremierDraft_<SET>_<date>"`), not the pack line. `pull` falls back to
  this shape automatically when no `DraftPack` is present, reading the local log/stream blob.
- IDs are MTGA grpIds = Scryfall Arena IDs: `https://api.scryfall.com/cards/arena/<id>`
  (needs `Accept: application/json` or you get HTTP 400).
- 17Lands: `https://www.17lands.com/card_ratings/data?expansion=<SET>&format=<FMT>&start_date=..&end_date=..`
  Columns used: `ever_drawn_win_rate` (GIH WR), `drawn_improvement_win_rate` (IWD), `avg_seen` (ALSA).

## Coaching rules

**Lead every pick with the guide read** — the set's archetypes, which color pairs are strongest *in
this set*, and the card's role in the open archetype. Present that first, then the supporting data
(ALSA, then GIH WR / IWD read through the lens below). The reason the guide leads isn't that it's
unbiased — it's the decoder for what the win-rate number is actually measuring:

**The core principle: every GIH WR is archetype-conditional. Decode it; don't rank guide-vs-stat.**
A card's win rate is a *conditional* statistic — it's the win rate of *the decks that actually drafted
that card*, not a context-free measure of the card. It answers "how did the archetypes that play this
card do with it," not "how good is this card in *my* deck." The whole skill is **decoding what the
number is conditioned on and asking whether your deck matches that archetype:**
- **Low archetype concentration** — colorless, mono-pip, generically-good two-color cards that nearly
  every deck in those colors plays. The conditioning ≈ unconditional, so the WR **transfers**: trust
  it as a **strong primary input**, near co-equal with the guide.
- **High archetype concentration** — Converge/X-cost payoffs, build-arounds, multicolor synergy pieces.
  The number *is the soup/payoff deck's result*, not yours. Discount hard unless you're building that
  deck. (Snarl Song's 60.7% GIH is soup casting it at X=4–5 for two 5/5s; in 2-color GW it's two 2/2s
  for six mana — a C, not a bomb. **Mentally substitute your real X / your real support before reading
  the number.**)

**The discipline that keeps this honest — name the mechanism.** "That win rate doesn't apply to *us*"
is exactly right for Snarl Song and exactly how motivated reasoning sounds when it's wrong. The test:
**to discount a card's WR you must be able to name the concrete mechanism by which the conditioning
fails for your deck** — X = your color count, double-off-color pips you can't cast, needs a graveyard
you're not filling, needs a go-wide board you don't have, needs a payoff you didn't draft. *If you
can't name a mechanism, the WR transfers and you don't get to override it.* No nameable mechanism =
you're rationalizing past an inconvenient number, not decoding it.

**Spend the decoding effort where it matters — the flagged minority, not every pick.** Most cards in
a pack are low-concentration commons where the WR just transfers; don't turn a vanilla 2-drop into a
philosophy exercise. The "whose deck is this number from" machinery only needs to fire on the ~10–20
high-conditioning cards in a set (payoffs, Converge/X-cost, multicolor synergy, build-arounds). For
everything else, trust the number and move fast.
- **This is why the guide leads — not because it's "less biased."** The guide is built from archetype
  tiers too; it carries the *same* archetypal lens. Its job is to **decode** the stat: "A in soup, C in
  2-color" makes the hidden conditioning explicit where the single aggregate number buries it. Guide +
  stat answer different questions — the guide tells you *which archetype's number* you're looking at.
- **ALSA is the exception** that stays genuinely separate: it measures draft *behavior* (what's
  contested / open), not a game outcome, so it isn't archetype-conditioned the same way. Surface it
  every meaningful pick (low = take now, won't wheel; high = you can speculate it comes back).
- **IWD inherits all of this and adds variance.** It's a win-rate delta (GIH WR minus games-not-drawn
  WR), so it carries the same archetype conditioning *plus* the noise of a difference of two numbers.
  Treat it with **more** skepticism than GIH WR — a flag for "does this card do something when it
  lands," never a primary signal.

**Format note (a consequence, not a separate axis):** format matters only because it changes how
*concentrated* archetypes are. SOS buries everything into invisible soup, so almost every payoff WR is
mis-conditioned — distrust the column hard. A grindy two-color-guild format like **MKM** concentrates
far less (the archetypes the data represents *are* the decks you draft), so more cards fall in the
"transfers well" bucket and GIH WR backs up toward primary. **Don't over-fit the SOS-era distrust to a
format where the conditioning is benign.**

- **Always surface the data, even though it's not the lead.** The table still prints; present it as
  a reference (ALSA + grade), with GIH WR / IWD alongside. Format: Card | Color | ALSA | Grade | GIH WR | IWD.
- **Push back, don't capitulate.** When the player challenges a pick, re-examine honestly. If the
  pick was right, hold ground with a full argument — coaching means disagreeing when the read says so.
- **Don't over-correct on small samples.** A 1-3 run is variance, not proof. Don't push a narrative.
- **Bo1 / closing-speed lens is a LIGHT tiebreaker only** — use it between cards that are otherwise
  close, never to skip a card the guide/archetype read clearly prefers.
- **Match response depth to pick difficulty (keep turns fast — your output is the bottleneck).**
  *Obvious pick* (one card clearly best for the open archetype, no curve/signal tension) → compact
  table of the top few + **"Pick: X — one-line reason."** *Close / contested pick* (two cards the
  guide rates similarly, or a curve/CABS/signal/archetype tradeoff, or the player challenges) →
  full treatment: card text, guide note, grade, ALSA/IWD, the argument. Don't write an essay for a
  blowout pick. Pushback only fires when a pick is questioned.

GIH WR reference bands (for the *tiebreaker* read only): **57%+ bomb · 54–57% excellent · 52–54%
solid · 50–52% filler · <50% avoid.** Treat these as a sanity check on the guide, not a pick order.

## Common leaks to coach against (use for tiebreakers & deckbuilding)

These are the most common drafting mistakes; watch the player's pool for them and steer against them.

- **Committing to colors too early.** Locking colors in P1P1–2 is a beginner crutch; it forecloses
  open lanes. The coaching fix: **picks 1–5 take the best card on raw power, color be damned;
  narrate wheel/signal evidence from ~pick 4; explicitly call the open lane around picks 6–8; lock
  by ~P1P9–10 (P2P2–3 = last clean pivot).** When the player reaches to "stay in our colors" before
  pick 8, push back. This is a *timing* correction, NOT card-evaluation bias — keep judging each
  card on the guide read (best card / open archetype), not on staying in-color.
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
Apply these on top of the guide read: the 17Lands GIH WR is a card's *average* value across all
decks that played it; these fundamentals decide whether it's the right *pick* for *this* deck and
this seat. **Throughline: archetype-first drafting (know the set's strong color pairs and build
toward one) beats picking down a win-rate column, and the common failure is drafting decks that
don't *lose* instead of decks that *win*. Bias picks toward proactive threats, evasion, and a real
way to close — over a marginal extra removal or card-draw spell.**

### Reading the 17Lands numbers (and their traps)
- **GIH WR is archetype-conditional — read it through that lens (and check `N`).** It's the win rate
  of the decks that *drafted* the card, not a context-free measure. How much you trust it depends on
  the card's archetype concentration (see the core principle in Coaching rules): it's a **strong
  primary input** for cleanly-castable cards whose WR transfers, a **tiebreaker** for
  payoff/multicolor cards whose number belongs to soup. Either way, a card with only a few hundred
  games has a noisy WR; `n/a` usually means "barely drafted" (often = weak/niche) — don't crown or
  bury on a small-N number.
- **The selection bias is the conditioning made concrete — especially on payoff/build-around cards.**
  A multicolor payoff, a spells-matter creature, a Converge/X-cost body, a graveyard card, etc. posts
  a high WR because it sat in decks built to enable it — **that doesn't transfer to a deck that
  can't.** Substitute *your* deck's real support (real X, real color count) before reading the
  number. Conversely, a colorless/always-castable card's WR transfers well.
- **What each column is for:** **ALSA** = how late it wheels (low = take now / contested; high =
  you can speculate it comes back) — the primary signal, and the only one orthogonal to win rate
  (it measures draft behavior, not outcomes); **GIH WR** = average power across the decks that
  played it, a *tiebreaker* only; **IWD** = a win-rate *delta* (how much it swings a game when
  drawn) — same family as GIH WR but noisier (a difference of two noisy numbers, with the same
  selection bias), so an even weaker tiebreaker. Use IWD only as a flag for whether a card actually
  does something when it lands. Always show ALSA.
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
  [`draft-guides/lords-of-limited/<SET>-draft-guide.md`](./draft-guides/lords-of-limited/)), load it for the format's meta read,
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
  *single* late premium the way you would against humans. Lean on the guide's archetype read and
  ALSA as the anchor.

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
- **How to apply it (important nuance):** CABS is a *deck-shape* discipline, not
  a card-by-card override. Don't refuse a card-draw spell the guide rates highly — but **use CABS as
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
