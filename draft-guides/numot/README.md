# numot/ — NumotTheNummy draft notes

Distilled draft tips from **NumotTheNummy** (Kenji Egashira) regular MTG Arena draft VODs,
compiled into per-set reference files for the draft coach.

- **Source:** the NumotTheNummy YouTube channel, *regular draft* VODs only (cube, sealed,
  constructed, and alchemy content excluded).
- **Built:** 2026-06-10, from YouTube auto-caption transcripts (`data/numot-subs/<SET>/<id>.txt`,
  gitignored). Auto-captions mangle card/mechanic names heavily; names were corrected only where
  confident from context, and uncertain readings are marked `(?)`. Treat as expert
  opinion/theory — at draft time these **decode** the archetype-conditional 17Lands data (see AGENTS.md).
- **Coverage tiers:**
  - **Tier 1 (deepest):** `MKM.md` (all 21 VODs) and `SOS.md` (all 33 VODs). Each has a
    `## vs Lords of Limited` section noting only genuine conflicts with the matching
    `draft-guides/lords-of-limited/<SET>-draft-guide.md` (LoL files are not modified).
  - **Tier 2 (thinner):** 38 other Arena-draftable sets, ~4 end-of-format VODs each
    (AFR has 3 — one VOD had no captions).

## Files

- `general-tips.md` — evergreen, set-independent draft & play principles, deduped and themed
  (picking, signals, curve/deckbuild, play patterns, mindset).
- `<SET>.md` — one per set (codes match Arena/17Lands, e.g. `MKM.md`, `SOS.md`, `NEO.md`).
  Sections: Format speed/meta read · Archetypes · Card interactions & combos · Card tips · Pitfalls.
- `manifest.json` — content fingerprint of the scrape (see below).

## Incremental updates (fingerprinting)

`manifest.json` records a content fingerprint (`sha1` + word count) of every transcript that has
been distilled into the notes, plus videos known to have no captions. This lets a future run skip
work that's already done instead of re-fetching and re-summarizing all 205 VODs.

Tool: `src/fingerprint_numot.py`

```sh
# After adding/re-enumerating VODs in data/numot-subs/worklist.json:
python3 src/fingerprint_numot.py new          # what's new or changed (human-readable)
python3 src/fingerprint_numot.py new --ids     # bare "<SET>\t<id>" lines to drive a fetch/distill loop

# After fetching + distilling those into numot/<SET>.md:
python3 src/fingerprint_numot.py update        # rewrite manifest.json to mark them done
```

`fetch_subs.sh` is already idempotent at the fetch layer (it skips any video with an existing
`.txt`). The manifest adds the missing piece — **distill-layer** idempotency — so stage 2 only
processes videos that are new or whose transcript changed. Captionless videos are recorded too, so
they aren't retried every run.
