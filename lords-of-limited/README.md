# Lords of Limited — set draft notes

Agent-facing draft-strategy references distilled from the
[Lords of Limited](https://www.youtube.com/@LordsofLimited/videos) YouTube channel, organized
**one folder per set**. Each set folder has a consolidated `*-draft-guide.md` (agent-primary,
hold-in-context-for-the-draft) plus a `sources/` dig-deeper layer of per-episode notes + transcripts.

Treat all of this as expert/theory opinion — weight it like a CGB grade; **17Lands GIH WR stays primary.**

## Sets covered

| Set | Folder | Guide | Notes |
|-----|--------|-------|-------|
| **Secrets of Strixhaven (SOS)** | [`sos/`](./sos/) | [sos/SOS-draft-guide.md](./sos/SOS-draft-guide.md) | 10 episodes, 2026-04-13 → 2026-06-01. Soup vs aggro; Prismari (UR) strong. |
| **Murders at Karlov Manor (MKM)** | [`mkm/`](./mkm/) | [mkm/MKM-draft-guide.md](./mkm/MKM-draft-guide.md) | 6 episodes, 2024-01-22 → 2024-03-25. Quick Draft re-run **Jun 8–16 2026**. Boros (RW) top. |

## Conventions (for adding a new set)

- Create `lords-of-limited/<set-code-lowercase>/` with its own `README.md`.
- Put per-episode notes in `<set>/sources/`, filenames **prefixed with publish date** (`YYYY-MM-DD-slug.md`)
  so they sort chronologically.
- Write a consolidated `<SET>-draft-guide.md` that applies a **recency rule** (newest video supersedes
  older on conflict; prerelease/preview takes are weakest; the format retrospective is most authoritative).
- Add a row to the table above, and a bullet under the SOS/MKM pointer in `../AGENTS.md`.
- Build pipeline: `yt-dlp` auto-captions → clean → per-episode summaries (parallel agents) → synthesize the guide.
