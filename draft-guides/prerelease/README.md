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

### ⚠ FRA is a different kind of guide from HOB

HOB synthesized five published expert reviews. **FRA synthesizes none** — at capture time
(2026-09-21) no reviewer had covered the set. It is derived from **full Scryfall set data
analyzed directly**, which changes what you can trust in it:

- **Reliable:** removal density per color, mechanic distribution, archetype support, curve shape,
  pool math. These are counts, not predictions.
- **Weak:** individual card grades and bomb ordering. One analyst reading card text, zero games.

If a future set is in the same position, prefer this shape — counting beats guessing — but label
the two tiers separately the way `FRA.md` does.

## Companion files

| File | For |
|------|-----|
| `<SET>.md` | The build reference — archetypes, grades, trio strategy, play data |
| `<SET>-onepager.md` / `.html` | A 3-minute primer for a teammate who is **playing but not building**. Deliberately short; hand this over instead of the build reference |
