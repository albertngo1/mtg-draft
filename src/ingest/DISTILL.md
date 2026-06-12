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

For a channel `<slug>` (one of `lords-of-limited`, `numot`, `limited-resources`):

1. **Find the work.** `python3 src/ingest/fingerprint.py <slug> new --ids` prints `<SET>\t<id>`
   lines for every video that is new or whose transcript changed. On a first/full run for a channel
   with no manifest yet, that's every video in `data/subs/<slug>/worklist.json`.
2. **Read the contract.** Open `channels.json` → `channels.<slug>.distill_format`. It tells you the
   output filename (`per_set_file`), any channel-wide files (`channel_files`), the ordered
   `sections`, the per-card `card_bullets` shape, the `recency` weighting, and `special_rules`.
3. **Distill per set.** For each set, read all of that set's transcripts in `data/subs/<slug>/<SET>/`
   and synthesize **one** `draft-guides/<slug>/<per_set_file>` following the contract + the shared
   house style below. Batch by set, not by video — the per-set file consolidates every episode.
4. **Update channel-wide files** (e.g. numot's `general-tips.md`) if `channel_files` is non-empty.
5. **Fingerprint.** `python3 src/ingest/fingerprint.py <slug> update` rewrites
   `draft-guides/<slug>/manifest.json` to mark everything distilled (and records captionless videos
   so they aren't retried).

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
