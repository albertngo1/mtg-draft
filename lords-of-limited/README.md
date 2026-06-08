# Lords of Limited — set draft notes

Agent-facing draft-strategy references distilled from the
[Lords of Limited](https://www.youtube.com/@LordsofLimited/videos) YouTube channel. The consolidated
`*-draft-guide.md` files (agent-primary, hold-in-context-for-the-draft) live **flat in this
directory**; each set also has a `<set>/` folder holding its `README.md` plus a `sources/`
dig-deeper layer of per-episode notes + transcripts.

Treat all of this as expert/theory opinion — weight it like a CGB grade; **17Lands GIH WR stays primary.**

## Sets covered

| Set | Guide | Sources | Notes |
|-----|-------|---------|-------|
| **Secrets of Strixhaven (SOS)** | [SOS-draft-guide.md](./SOS-draft-guide.md) | [`sos/`](./sos/) | 10 episodes, 2026-04-13 → 2026-06-01. Soup vs aggro; Prismari (UR) strong. |
| **Murders at Karlov Manor (MKM)** | [MKM-draft-guide.md](./MKM-draft-guide.md) | [`mkm/`](./mkm/) | 6 episodes, 2024-01-22 → 2024-03-25. Quick Draft re-run **Jun 8–16 2026**. Boros (RW) top. |

## Conventions (for adding a new set)

- Write the consolidated `<SET>-draft-guide.md` **here in `lords-of-limited/`** (flat, not inside the
  set folder). Apply a **recency rule** (newest video supersedes older on conflict; prerelease/preview
  takes are weakest; the format retrospective is most authoritative).
- Create `lords-of-limited/<set-code-lowercase>/` with its own `README.md` and a `sources/` folder.
- Put per-episode notes in `<set>/sources/`, filenames **prefixed with publish date** (`YYYY-MM-DD-slug.md`)
  so they sort chronologically.
- Add a row to the table above, and a bullet under the SOS/MKM pointer in `../AGENTS.md`.
- Build pipeline: `yt-dlp` auto-captions → clean → per-episode summaries (parallel agents) → synthesize the guide.
