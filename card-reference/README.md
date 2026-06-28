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
- **📘 Lords of Limited / 🎙 NumotTheNummy / 🎧 Limited Resources / 🎓 Limited Level-Ups** — expert notes
  parsed from `draft-guides/`, where the card name matched (gaps are mostly commons whose names were
  garbled in the source podcast/VOD transcripts)

The reviewer-grade column auto-detects its source: **DS** (Draftsim, numeric /5) if `grades/draftsim_<SET>.json`
exists, else **CGB** (CardGameBase, letter A+→F). The header caveat is set-aware (SOS = soup-inflation
warning; MKM = honest-WR guild-format note; MSH = early-data note + a 10-archetype color-pair map).

## Regenerating

Layout/columns only: edit `build_card_reference.py` (`COLS`) and re-run — instant, no LLM.

**AI takes (per-set):** follow **[`AI_TAKES_PLAYBOOK.md`](AI_TAKES_PLAYBOOK.md)** — the codified, consistent
process. The mechanical steps are deterministic via `gen_ai_takes.py` (`prep` chunks the per-card context,
`merge` validates + writes `ai_takes_<SET>.json` keyed to the real card list); the creative step is a parallel
analyst-agent fan-out under a per-set doctrine written from that set's draft guides. Then add the set's
`CAVEAT` + `ARCHETYPES` entries in `build_card_reference.py` and rebuild.

## Coverage

- **SOS** — 341/341 cards with image + 17Lands ratings + DS grade + AI take; 155/341 with ≥1 expert note.
- **MKM** — 321/321 cards with image + 17Lands ratings + CGB grade + AI take; 142/321 with ≥1 expert note.
- **MSH** — 334/334 cards with image + AI take, 270/334 with live GIH WR (early data, filling in) + 276 CGB
  grades; 234/334 with ≥1 expert note (Limited Level-Ups wired in — the largest MSH guide). Header carries a
  10-archetype color-pair map. Takes generated under the MSH slow-grindy-goodstuff doctrine.
- **BLB** — 271/271 cards with image + full-format GIH WR + CGB grade + AI take; 124/271 with ≥1 expert note
  (all 3 guides are end-of-format retrospectives). Header carries the 10-tribe color-pair map; takes are
  archetype-aware (typal/"false friend" decoding).
