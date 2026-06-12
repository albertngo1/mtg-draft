# Limited Resources draft guides

Per-set draft notes distilled from the **Limited Resources** podcast (Marshall Sutcliffe + Luis Scott-Vargas / "LSV"). The third expert-prose channel for the draft coach, alongside `lords-of-limited/` and `numot/`.

- **Source:** the Limited Resources YouTube channel (audio podcast). Episode types covered: set-review (commons/uncommons + rares/mythics), format overview, archetype deep-dives, draft walkthroughs, and the end-of-format Sunset Show.
- **Built:** 2026-06-11, from YouTube auto-caption transcripts (`data/subs/limited-resources/<SET>/<id>.txt`, gitignored). LR is audio-only on YouTube, so card/mechanic names are heavily mangled; corrected only where confident from context, uncertain readings marked `(?)`.
- **Status:** expert opinion / theory. At draft time these guides **decode** the archetype-conditional 17Lands data (see [`AGENTS.md`](../../AGENTS.md)) — 17Lands GIH WR remains the primary signal, the guide tells you which archetype's number you're reading.

## Sets covered

| Set | Episodes | Window | Sunset |
|---|---|---|---|
| MKM (Murders at Karlov Manor) | 6 (#735–743) | 2024-01-31 → 2024-03-29 | ✓ |
| SOS (Secrets of Strixhaven) | 6 (#849–857) | 2026-04-15 → 2026-06-11 | ✓ |

## House style

Every guide is **recency-aware** (matches the SOS/MKM convention shared with lords-of-limited and numot):

- `## ⚠ Recency rule (read first)` — newest episode wins on any conflict; release-week set-review grades (#735/#736 in MKM; #849/#850 in SOS) are **predictions made before any games** and are the weakest evidence; the Sunset Show is the most authoritative source.
- `### Source timeline` — dated table of every episode used, with `Phase` (release-week / early / mid / late / Sunset) and `Weight` (Weakest → Strongest).
- `## Supersessions` — opinion REVERSALS the run reveals (early take → late take, verdict).
- `## Format speed / meta read` — settled reads on speed, on-the-play, color tier, archetype dominance, bomb density.
- `## Archetypes` — 10 two-color pairs, ranked by the settled Sunset Show read.
- `## Card tips` — per-card bullet entries with the LR letter grade preserved inline (`- **Card** — grade (#735 release). Late take if reversed.`), grouped by color (W/U/B/R/G), then multicolor, then artifacts/lands.

## Why LR alongside lords-of-limited + numot

The three channels are **decorrelated** by lens:

- **Lords of Limited** — gameplay + set-strategy show; archetype-first, with explicit archetype hierarchy ranks.
- **NumotTheNummy** — pure draft VODs; opinions surface as Kenji-while-drafting commentary; strongest signal on *which cards are actually playable late*.
- **Limited Resources** — review/theory lens; preserves explicit per-card **letter grades** from the release-week reviews and the public **Sunset Show retrospective**. Strongest signal on *what the format experts believed at release vs after grinding it out*.

The supersession sections in each LR guide are the single highest-leverage product of this channel — they show which release-week grades flipped, and by how much.

## Pipeline

Raw transcripts fetched via `src/ingest/fetch_subs.sh limited-resources` (idempotent; yt-dlp auto-captions → `data/subs/limited-resources/<SET>/<id>.txt` + `meta.tsv`). Distillation is manual / one-shot per set — no fingerprint registry yet (the corpus is small enough to re-distill from scratch when a new set ships).
