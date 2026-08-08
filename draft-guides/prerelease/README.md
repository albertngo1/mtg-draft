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
| The Hobbit (HOB) | [HOB.md](./HOB.md) | 2026-08-07 | partly — see [`limited-resources/HOB.md`](../limited-resources/HOB.md) (commons + uncommons only; HOB.md here still has the only rare coverage) |
