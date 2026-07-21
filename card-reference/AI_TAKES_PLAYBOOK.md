# AI-Takes Playbook (how to generate `ai_takes_<SET>.json` for a new set)

Follow this end-to-end so every set's AI takes come out consistent. The **mechanical**
steps (prep, chunk, merge) are deterministic via `gen_ai_takes.py`; the **creative** step
(writing each take) is a parallel-agent fan-out under a per-set doctrine you author from
that set's draft guides. MSH (2026-06) is the reference implementation.

## Prerequisites

- `data/cache/17lands_<SET>_PremierDraft_1200d.json` exists (run `warm --set <SET> --refresh`).
  Live GIH WR is the primary signal; pre-data sets fall back to grades + guide notes.
- `data/cache/scryfall_arena.json` is warmed for the set (also from `warm`) — it supplies each card's
  **oracle text + P/T + mana cost**, joined into the prep record by `mtga_id` so the analyst agents can
  actually READ the card. (Coverage is reported on the `prep` line as `oracle text (N)`.)
- A reviewer grade file: `grades/draftsim_<SET>.json` (DS /5) **or** `grades/cardgamebase_<SET>.json` (CGB letters).
- Whatever expert guides exist under `draft-guides/{lords-of-limited,numot,limited-resources,limited-level-ups}/`.
  All four are auto-wired by name — **before generating, confirm every guide on disk for the set is wired.**
  Two reasons a guide silently contributes 0 notes: (a) it has no `## Card tips` / `## Card notes` section (pure
  archetype-prose guides like draftsim's add nothing — intentional); (b) its bullets use a separator the parser
  doesn't accept (it takes `- **Card** — note`, `– note`, `: note`). The build's **legend is self-checking** —
  it lists only guides that actually produced notes, so if a guide you expect is missing from the rendered
  legend, it parsed nothing; go look at its bullet format.

## Steps

1. **Prep + chunk** (deterministic):
   ```
   python3 card-reference/gen_ai_takes.py prep <SET> <scratch>/chunks 12
   ```
   Emits 12 `chunk_NN.json` files, each a list of per-card context records:
   `name, color, rarity, mana, type_line, types, pt, text (oracle), gih_wr, iwd, alsa, oh_wr, gd_wr,
   play_rate, <grade>_grade, notes{LoL,Numot,LR,LLU}`.

2. **Author the per-set doctrine** — write `<scratch>/<SET>_doctrine.md` from the set's guides
   (format speed, removal benchmarks, mechanics, the color-pair archetypes, set-specific traps).
   Use the template below. The **"How to write each take" rules and stat key are STABLE — copy them
   verbatim every set**; only the format/mechanics/archetypes sections change.

3. **Fan out** — spawn one analyst agent (general-purpose) per chunk, in a single message so they run
   concurrently. Each agent: reads the doctrine + its `chunk_NN.json`, writes a take for **every** card,
   and saves `{ "<exact card name>": "<take>" }` to `<scratch>/results/chunk_NN.json` via the Write tool.
   Standard agent prompt:
   > You are an expert MTG Limited analyst writing concise "AI takes" for cards in <SET>.
   > Read the doctrine `<scratch>/<SET>_doctrine.md` and your chunk `<scratch>/chunks/chunk_NN.json`.
   > For EVERY card write one take (1-3 sentences, ~25-55 words) following the doctrine's
   > "How to write each take" rules. For null-`gih_wr` cards lean on the grade + notes and say the read
   > is provisional. Write a JSON object {exact name → take} to `<scratch>/results/chunk_NN.json`.
   > Cover every card, no omissions; valid UTF-8 JSON; verbatim names.

4. **Merge + validate** (deterministic):
   ```
   python3 card-reference/gen_ai_takes.py merge <SET> <scratch>/results
   ```
   Writes `card-reference/ai_takes_<SET>.json` keyed + ordered to the real card list. It **exits non-zero
   and lists any MISSING names** — if an agent dropped a card (common: a chunk of 28 comes back with 27),
   re-run just that card and re-merge until 0 missing. Extra/non-draftable keys are dropped automatically.

5. **Wire the doc header** in `build_card_reference.py`:
   - Add a `CAVEAT[<SET>]` line (one-sentence format framing + data-maturity note).
   - Add an `ARCHETYPES[<SET>]` entry: the color-pair archetype map as a markdown table
     (ranked, with signposts), plus removal benchmarks and any set-specific rule (e.g. MSH's
     "big-dummy" no-ETB-fatty trap). This is what makes the takes' archetype references legible.

6. **Rebuild + sanity-check:**
   ```
   python3 card-reference/build_card_reference.py <SET>
   ```
   Confirm the print line shows `AI takes: <N>/<N>`, the archetype map renders, and guide-note count
   looks right. Update the **Coverage** section of `card-reference/README.md`.

## Doctrine template (fill the per-set sections; keep the stable sections verbatim)

```
# <SET> Limited — Analyst Doctrine

You are writing a concise, decisive AI take for each card in a draft card-reference. Takes are read
by a drafter mid-pick. They must add signal BEYOND the raw numbers and grade already on the tile —
decode WHICH deck/situation a number comes from, resolve guide disagreements, give a pick-priority verdict.

## Format read           <!-- PER SET: speed (racy vs grindy), board-stall/removal density, what breaks through -->
## Removal benchmarks     <!-- PER SET: name the premium removal so "premium removal" is anchored -->
## Mechanics             <!-- PER SET: each keyword, what it wants, which color pair it anchors -->
## Archetypes            <!-- PER SET: the color-pair guilds, ranked, with signposts. THE CORE CONTEXT. -->
## Set-specific traps    <!-- PER SET: e.g. no-ETB fatties, soup-inflated multicolor WR, build-around floors -->

## How to write each take (1-3 sentences, ~25-55 words)   <!-- STABLE — copy verbatim every set -->
- READ THE CARD FIRST: judge from the `text` (oracle) + `pt` + `mana` — what it actually does (cost,
  evasion, removal quality, ETB, floor/ceiling) — then layer the numbers on top. A take that misreads
  the card is wrong even if the stats look right. (Read the text; don't restate it in the take.)
- Ground the verdict in the EXPERT `notes` (LoL / Numot / LR / LLU): fold the experts' read into your
  take and resolve any split between them — the notes are the decode of what the WR is conditioned on.
- Lead with the verdict / pick priority (bomb / premium removal / solid playable / role-player / filler / sideboard / trap).
- Decode the numbers: high GIH WR but low OH/play = a synergy/late card, not a slam; a no-ETB fatty with an
  inflated grade is a trap; flag evasion/removal in the context of the format's speed.
- Reconcile grade vs live WR when they disagree — trust live GIH WR over pre-data grades, but say so.
  For null-WR cards, lean on the grade + guide notes and say the read is provisional.
- Resolve guide splits (e.g. "Alex C / Mark D+") into one verdict.
- Name the archetype(s) the card wants when it's synergy-dependent (use the color-pair codes from Archetypes).
- Be specific and opinionated. NO hedging filler, NO restating rules text, NO "good in good decks."
  Don't just repeat a guide note — synthesize.

## Stat key (provided per card)                            <!-- STABLE — copy verbatim every set -->
text = oracle text (READ IT — what the card does) · pt = power/toughness · mana = mana cost ·
type_line = full type · gih_wr = Games-in-Hand WR (primary) · iwd = improvement-when-drawn (pp) · alsa = avg last seen at
(lower = earlier) · oh_wr/gd_wr = opening-hand / drawn WR · play_rate · <grade> = reviewer grade
(DS /5 or CGB letters; pre-data, trust live WR over it) · notes = expert guide blurbs
(LoL=Lords of Limited, Numot, LR=Limited Resources, LLU=Limited Level-Ups).
```

## Conventions that keep sets consistent

- **Take length:** 1-3 sentences, ~25-55 words. MSH/SOS/MKM all land ~50-word average — match it.
- **Verbatim card names** as JSON keys (the merge step validates against the real card list).
- **Trust live GIH WR over pre-data grades**, and say so when they conflict.
- **Archetypes are the backbone** — every synergy card's take should name its color-pair guild, and the
  doc header must carry the archetype map so those references are legible.
- **Commit caution:** the takes + parsed guide notes go to the public repo. Leave generated takes
  uncommitted and confirm with Albert before publishing (matches prior practice).
