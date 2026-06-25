# Limited Level-Ups — set draft guides

Per-set Limited guides distilled from **[Limited Level-Ups](https://www.youtube.com/@limitedlevel-ups)**
(Alex / Chord_O_Calls) — a Limited-focused podcast/video channel. Unusually deep per set because
the channel splits its set review across **per-color episodes** (W/U/B/R/G + Multicolor/Colorless +
a Rare/Mythic review), plus prerelease/first-impressions guides and occasional early-access draft VODs.

Channel #4 in the ingest pipeline (after lords-of-limited, numot, limited-resources). Same ETL:
`src/ingest/fetch_subs.sh limited-level-ups` → transcripts in `data/subs/limited-level-ups/<SET>/`;
distill per `src/ingest/DISTILL.md` + the `limited-level-ups` contract in `src/ingest/channels.json`.

Each `<SET>.md` preserves Alex's **per-card letter grade** inline, grouped by color. As everywhere
in this repo: **17Lands GIH WR is primary**; these grades are a reviewer/theory cross-reference lens.

## Sets covered

| Set | Guide | Sources |
|-----|-------|---------|
| Marvel Super Heroes (MSH) | [MSH.md](./MSH.md) | 10 episodes (First Impressions, per-color reviews, Rare/Mythic, Prerelease, Early-Access draft) |
