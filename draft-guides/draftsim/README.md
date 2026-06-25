# Draftsim — set draft notes

Agent-facing draft-strategy references captured from **[Draftsim](https://draftsim.com/)** written
guide articles — one `<SET>.md` per set. Unlike the other folders here (`lords-of-limited`,
`limited-resources`, `numot`), Draftsim is a **web-prose** source: these are hand-captured from
article URLs, **not** YouTube auto-caption transcripts, so they are **outside the `src/ingest/` ETL**
and the manifest carries `source_url` + `captured` date instead of video IDs.

This is separate from **`grades/draftsim_<SET>.json`**, which holds Draftsim's *numeric* pick-order
grades (the `DS` column, out of 5) consumed by `src/mtgdraft/grades.py`. The files here are the
**written strategy prose** (archetypes, mechanics, removal rankings) — reviewer/theory opinion.

As everywhere in this repo: **17Lands GIH WR is primary**; Draftsim grades/takes are a cross-reference
lens, and every WR in a soup format like SOS is archetype-conditional (multicolor/Converge inflated).

## Sets covered

| Set | Guide | Source | Captured |
|-----|-------|--------|----------|
| Secrets of Strixhaven (SOS) | [SOS.md](./SOS.md) | [mtg-sos-draft-guide](https://draftsim.com/mtg-sos-draft-guide/) | 2026-06-21 |
| Marvel Super Heroes (MSH) | [MSH.md](./MSH.md) | [mtg-msh-draft-archetypes](https://draftsim.com/mtg-msh-draft-archetypes-6-3-26/) | 2026-06-23 |
