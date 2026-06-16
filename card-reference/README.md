# Card Reference

Single-file, visual card references for a set: every draftable card as a tile in a
3-per-row grid, with image, 17Lands ratings, Draftsim grade, expert-guide notes, and an AI take.

## Files

- `build_card_reference.py` — generator. `python3 build_card_reference.py [SET]` (default `SOS`).
- `ai_takes_<SET>.json` — pre-generated per-card AI verdicts (name → take), committed so the
  build is reproducible without re-running the LLM pass.
- `<SET>-card-reference.md` — the output (open in any Markdown viewer; images are remote Scryfall URLs).

## Per-card tile

- **Image** (Scryfall, 190px)
- **Ratings:** GIH WR (primary) · IWD · ALSA · DS (Draftsim /5) · OH WR · GD WR · play rate —
  from `data/cache/17lands_<SET>_PremierDraft_1200d.json`
- **🤖 AI take** — independent, data-decoding verdict (flags soup-inflated win-rates, gives pick priority)
- **📘 Lords of Limited / 🎙 NumotTheNummy / 🎧 Limited Resources** — expert notes parsed from
  `draft-guides/`, where the card name matched (gaps are mostly commons whose names were garbled
  in the source podcast/VOD transcripts)

The reviewer-grade column auto-detects its source: **DS** (Draftsim, numeric /5) if `grades/draftsim_<SET>.json`
exists, else **CGB** (CardGameBase, letter A+→F). The header caveat is set-aware (SOS = soup-inflation
warning; MKM = honest-WR guild-format note).

## Regenerating

Layout/columns only: edit `build_card_reference.py` (`COLS`) and re-run — instant, no LLM.

The AI takes were produced one-off by fanning all cards out to parallel analyst agents under the
SOS soup-format doctrine. To rebuild them for a new set, regenerate `ai_takes_<SET>.json` the same way.

## Coverage

- **SOS** — 341/341 cards with image + 17Lands ratings + DS grade + AI take; 155/341 with ≥1 expert note.
- **MKM** — 321/321 cards with image + 17Lands ratings + CGB grade + AI take; 142/321 with ≥1 expert note.
