# Prerelease — multi-source prerelease syntheses

Agent-facing draft/sealed references for sets whose **prerelease is imminent and no gameplay data
exists yet**. Each `<SET>.md` synthesizes several written prerelease sources at once (Wizards'
official guide, Draftsim, Card Game Base, MTG Arena Zone) rather than tracking one channel.

Like [`draftsim/`](../draftsim/), this is a **web-prose** source: hand-captured from article URLs,
**outside** the `src/ingest/` YouTube ETL, so the manifest carries `source_urls` + `captured` instead
of video IDs.

## ⚠ These are the weakest guides in the repo, by construction

Under the house recency rule, prerelease/preview takes are the *lowest*-weight evidence tier — every
grade in them is a reviewer's prediction made before a single game. A guide here exists to cover the
window between a set's prerelease and its Arena release, and nothing more.

**Retire or rewrite each file once real data lands:**
1. 17Lands GIH WR (available from the set's Arena release) supersedes every card grade here.
2. The `limited-resources/<SET>.md` and `lords-of-limited/<SET>-draft-guide.md` guides supersede the
   archetype and format reads.

If a set in this folder already has a post-release guide in another folder, prefer that one.

## Sets covered

| Set | Guide | Prerelease | Superseded by |
|-----|-------|-----------|---------------|
| The Hobbit (HOB) | [HOB.md](./HOB.md) | 2026-08-07 | largely — [`limited-level-ups/HOB.md`](../limited-level-ups/HOB.md) covers archetypes, commons, uncommons, **rares and mythics**; [`limited-resources/HOB.md`](../limited-resources/HOB.md) covers commons + uncommons. Retire once 17Lands GIH WR lands (Arena 2026-08-11). |
| Reality Fracture (FRA) | [FRA.md](./FRA.md) | 2026-09-25 | not yet — no channel guide exists. Retire once 17Lands GIH WR lands, or when any of `limited-resources/`, `limited-level-ups/`, `lords-of-limited/` publish FRA. |

### FRA sources

FRA synthesizes four written sources plus full set data: the Wizards official prerelease guide,
Draftsim's 0–10 set review, LimitedMTG's counted draft & sealed guide, and MTG Arena Zone's
colour-by-colour reviews.

Draftsim's grades for all 280 non-basic FRA cards are captured to
[`grades/draftsim_FRA.json`](../../grades/draftsim_FRA.json) (converted from 0–10 to the /5 the
card-reference generator renders), so the set already carries a reviewer-grade file before release.

**A note on method.** The first draft of `FRA.md` was written from card data alone, on the
assumption that no reviews existed yet. They did — nobody had checked. That version also analysed
only mono-coloured cards and silently skipped all 75 multicolour ones, which produced a wrong
structural read (five allied factions rather than the real ten archetypes) and wrong removal
counts. Both errors were caught by reconciling against the published sources. The lesson for the
next set in this folder: **search for coverage before concluding there is none, and check that a
set-wide count actually covers gold and hybrid cards.**

## Companion files

| File | For |
|------|-----|
| `<SET>.md` | The build reference — archetypes, grades, trio strategy, play data |
| `<SET>-onepager.md` / `.html` | A 3-minute primer for a teammate who is **playing but not building**. Deliberately short; hand this over instead of the build reference |
