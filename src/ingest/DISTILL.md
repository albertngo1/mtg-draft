# Distill runbook — transcripts → draft guides

This is the **stage-2** procedure: turn the raw auto-caption transcripts in
`data/subs/<slug>/` into the committed expert-prose guides in `draft-guides/<slug>/`.

Stage 1 (fetch) is fully automated — `src/ingest/fetch_subs.sh <slug>` downloads + cleans
captions, and `src/ingest/fingerprint.py <slug>` tracks what's been distilled. Stage 2 needs an
LLM, so it's a **runbook an agent follows**, not a script. The per-channel output contract is data
in [`channels.json`](./channels.json) → each channel's `distill_format`. This file is the procedure
that reads it; the contract lives there so adding a 4th channel never means editing prose in three
READMEs again.

## Procedure

For a channel `<slug>` (one of `lords-of-limited`, `numot`, `limited-resources`,
`limited-level-ups`, `rough-drafts`):

1. **Find the work.** Start with `python3 src/ingest/fingerprint.py <slug> coverage` — per set, it
   compares transcripts on disk against the guide that should account for them, on two independent
   signals (`guide` = guide file older than its newest transcript; `unfp` = transcripts no manifest
   entry mentions). A set flagged by BOTH is very likely a real gap; one signal alone is a prompt to
   open the guide and look, not a verdict.

   Then `python3 src/ingest/fingerprint.py <slug> new --ids` prints `<SET>\t<id>` lines for every
   video that is new or whose transcript changed. On a first/full run for a channel with no manifest
   yet, that's every video in `data/subs/<slug>/worklist.json`.

   > **Run this before every distill pass, and believe it over your memory of what is done.**
   > On 2026-08-23, eight set-guides were found with transcripts fetched months earlier and never
   > distilled. Nothing was broken — `new` reports exactly those gaps and always would have. It had
   > simply never been run. Fetching is not distilling, and nothing in the pipeline connects them.
2. **Read the contract.** Open `channels.json` → `channels.<slug>.distill_format`. It tells you the
   output filename (`per_set_file`), any channel-wide files (`channel_files`), the ordered
   `sections`, the per-card `card_bullets` shape, the `recency` weighting, and `special_rules`.
3. **Distill per set.** For each set, read all of that set's transcripts in `data/subs/<slug>/<SET>/`
   and synthesize **one** `draft-guides/<slug>/<per_set_file>` following the contract + the shared
   house style below. Batch by set, not by video — the per-set file consolidates every episode.

   **Never trust an episode title to describe its scope.** Check what the transcript actually spends
   its runtime on before honoring any contract rule keyed off the title. Rough Drafts ep 75 is named
   "Goblin Plate Mail" and mentions that card 4 times in 5,281 words; the episode is a format-theory
   argument about menace and amass. A contract rule that says "a card-titled episode gets a deep-dive
   section" will make you invent content that does not exist. Cheap check before distilling:

   ```bash
   # how many of the set's cards does this episode actually discuss, and how often?
   python3 - <<'EOF'
   import json
   cards=[c['name'] for c in json.load(open('data/cache/17lands_<SET>_PremierDraft_1200d.json'))]
   t=open('data/subs/<slug>/<SET>/<id>.txt',encoding='utf-8',errors='replace').read().lower()
   hits=sorted(((t.count(n.split('//')[0].strip().lower()),n) for n in cards),reverse=True)
   print(f"words={len(t.split())}"); [print(f"{c:3d}  {n}") for c,n in hits[:15] if c]
   EOF
   ```
4. **Update channel-wide files** (e.g. numot's `general-tips.md`) if `channel_files` is non-empty.
5. **Fingerprint — LAST, and only for sets you actually distilled.**
   `python3 src/ingest/fingerprint.py <slug> update` rewrites `draft-guides/<slug>/manifest.json`
   (and records captionless videos so they aren't retried). It now SKIPS any set whose guide is
   missing or older than its newest transcript, printing `SKIP <SET>: guide missing|behind` — so it
   cannot certify undistilled work as done. `--force` overrides, and is only for repairing a
   manifest you have separately verified.

   > **Order is load-bearing: coverage → new → distill → update.** Running `update` first is what
   > caused the 2026-08-23 incident. `update` used to mark every transcript on disk as distilled
   > without checking whether any guide reflected it; one premature run marked 31 videos across 5
   > sets as done, and `new` then reported "up to date" forever. A set-level "does a guide exist"
   > check is NOT enough to catch this — a set with a stale guide passes it and still hides work.
   > Worse, those videos would have been written as `reason: no-captions`, a tombstone `new`
   > deliberately never retries. The guard now covers both paths.
6. **Refresh the format brief** for every set you touched. New guide content that isn't attached to
   a single card belongs in `card-reference/briefs/<SET>.md` (draft plan, gameplay rules,
   deckbuilding doctrine, traps, cross-source disagreements, and where the guides were wrong once
   the data landed). This is **required, not optional** — `build_card_reference.py <SET>` fails
   while the brief is missing or still holds a `TODO`. Scaffold a new one with
   `python3 card-reference/build_card_reference.py <SET> --scaffold-brief`;
   `card-reference/briefs/HOB.md` is the blueprint. Keep each brief self-contained to its own set.
7. **Rebuild the card reference** — `python3 card-reference/build_card_reference.py <SET>` — so the
   new notes and brief actually reach the drafting surface.

   **Cache gotcha:** `build_card_reference.py` reads `data/cache/17lands_<SET>_PremierDraft_1200d.json`,
   but `mtg-draft.py warm --set <SET>` only refreshes the **120d** file. Running `warm` and then
   rebuilding silently reuses stale win rates. To actually refresh the numbers the reference renders:

   ```bash
   python3 -c "import sys; sys.path.insert(0,'src'); from mtgdraft.sources import seventeen; \
     seventeen('<SET>','PremierDraft',1200,refresh=True)"
   ```

## Shared house style (`house_style: shared`)

Every channel's guides are **recency-aware**. Apply these regardless of channel; `distill_format`
only adds/overrides specifics:

- **Recency rule.** Newest take wins on conflict. The channel's `recency` field says which phase is
  weakest (usually prerelease/release-week predictions) and which is most authoritative (usually the
  end-of-format retrospective / Sunset Show). Lead the guide with this so a reader weights correctly.
- **Source timeline** — a dated table of every episode used (date, title, and where the contract asks
  for it, a Phase + Weight column).
- **Supersessions** — call out opinion *reversals* the run reveals (early take → late take, verdict).
  For `limited-resources` this is the highest-value section — never drop it.
- **Source episodes** — a `date — title (youtube_id)` list (bottom of file for `lords-of-limited`).
- **Auto-caption caveat.** These captions transcribe *speech*, so card names, college names, and
  mechanics get mangled. Correct only where you're confident from context; mark uncertain readings
  `(?)`. **Never invent content** to fill a section — omit or hedge instead.
- **Status.** These guides are expert opinion/theory that *decode* the archetype-conditional 17Lands
  data at draft time — 17Lands GIH WR stays the primary signal (see `AGENTS.md`). Don't present a
  guide take as a hard number.

## Per-channel specifics (summary — `channels.json` is authoritative)

| Channel | Per-set file | Distinctive contract |
|---|---|---|
| `lords-of-limited` | `<SET>-draft-guide.md` | `## Card notes` bullets `- **Card** — note` are **machine-parsed** into the draft JSON — keep the exact shape and real card names. |
| `numot` | `<SET>.md` + `general-tips.md` | Tier-1 sets (MKM, SOS) get `## vs Lords of Limited` (conflicts only; never edit LoL files). |
| `limited-resources` | `<SET>.md` | Preserve the LR **letter grade** inline on every `## Card tips` bullet; group by color then multicolor then artifacts/lands. |

## Adding a 4th channel

1. Add a `channels.<slug>` block to `channels.json` (incl. its `distill_format`).
2. Create `data/subs/<slug>/worklist.json` (sets → video ids).
3. `src/ingest/fetch_subs.sh <slug>` → fetch captions.
4. Follow the procedure above to distill into `draft-guides/<slug>/`.
5. `src/ingest/fingerprint.py <slug> update` → write the manifest.

No code changes are required — `fetch_subs.sh` and `fingerprint.py` are channel-agnostic and derive
every path from the slug.
