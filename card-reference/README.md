# Card Reference

Single-file, visual card references for a set: every draftable card as a tile in a
3-per-row grid, with image, 17Lands ratings, Draftsim grade, expert-guide notes, and an AI take.

## Files

- `build_card_reference.py` — generator. `python3 build_card_reference.py [SET]` (default `SOS`).
- `ai_takes_<SET>.json` — pre-generated per-card AI verdicts (name → take), committed so the
  build is reproducible without re-running the LLM pass.
- `briefs/<SET>.md` — **the per-set format brief, REQUIRED for every set.** Rendered between the
  archetype map and the card grid. This is where the expert-guide commentary that *isn't* attached
  to a single card goes: the draft plan, gameplay rules, deckbuilding doctrine, traps, and any
  cross-source disagreements. The point is that the reference is self-contained — you should never
  have to open `draft-guides/` in a second window while drafting.
  **[`briefs/HOB.md`](briefs/HOB.md) is the blueprint.** Keep each brief self-contained to its own
  set: no comparisons to other sets, except when quoting an expert's own words verbatim.
  The build **fails** if `briefs/<SET>.md` is missing or still contains a `TODO`, so a newly
  scraped set structurally cannot ship without one:
  ```
  python3 build_card_reference.py <SET> --scaffold-brief   # write the house template, then fill it in
  python3 build_card_reference.py <SET> --no-brief         # throwaway build only; never commit one
  ```
- `<SET>-card-reference.md` — the output (open in any Markdown viewer; images are remote Scryfall URLs).
- `fetch_archetypes.py` — pulls each colour pair's **real** win rate and share of the metagame from
  17Lands. `python3 fetch_archetypes.py <SET> [EVENT_TYPE] [--refresh]`. Use this, never the obvious
  workaround of averaging the gold cards legal in each pair — that proxy conflates card quality with
  archetype quality, rests on 3-8 cards, and measured against this endpoint it mis-ranked pairs by up
  to five places. The archetype table above each brief comes from here.
- `build_site.py` + `site/` — the static-site generator behind the browsable web version (below).

## Browsable web version — https://albertngo1.github.io/mtg-draft/

The same references, published as a static site: a landing page listing every set (card count,
colour split, grade source, whether it carries a format brief) and a per-set page with the full
card grid. Each set page adds what a Markdown file can't do — a search box that matches card names,
stats and every expert note; rarity filters; a sticky colour-section jump strip; and a collapsed
format brief so the grid is the first thing you see. Card tiles reflow from five columns down to
two on a phone.

**`build_site.py` reads the `<SET>-card-reference.md` files off disk at build time** and rebuilds
the whole site, so a new set appears (and an edited one updates) with no code change:

```
python3 card-reference/build_site.py                 # -> ./docs   (local preview; gitignored)
python3 card-reference/build_site.py --out /tmp/prev # preview build somewhere else
python3 -m http.server 8000 --directory docs         # then open http://127.0.0.1:8000/
```

Standard library only — it ships its own small Markdown renderer, and `site/site.css` +
`site/site.js` are copied verbatim into `docs/assets/`. Nothing is loaded from a CDN.

**Publishing is automatic — you do not run this to publish.**
[`.github/workflows/pages.yml`](../.github/workflows/pages.yml) rebuilds and deploys the site on
every push to `main` that touches a `<SET>-card-reference.md`, the `site/` template, or the
generator. GitHub Pages serves the workflow's artifact directly, so **the live site cannot lag the
Markdown** — regenerate a reference, push, and the site follows.

`docs/` is **gitignored**: it is generated output, it is rebuilt in CI, and committing it churned
~4.7 MB of history per rebuild. Run `build_site.py` locally only to preview. To force a rebuild
without changing a file: `gh workflow run pages.yml --ref main`.

## Per-card tile

- **Image** (Scryfall, 190px)
- **Ratings:** GIH WR (primary) · IWD · ALSA · DS (Draftsim /5) · OH WR · GD WR · play rate —
  from `data/cache/17lands_<SET>_PremierDraft_1200d.json`
- **🤖 AI take** — independent, data-decoding verdict (flags soup-inflated win-rates, gives pick priority)
- **📘 Lords of Limited / 🎙 NumotTheNummy / 🎧 Limited Resources / 🎓 Limited Level-Ups / 🎬 Rough
  Drafts** — expert notes parsed from `draft-guides/`. Names are matched exactly first, then a single
  fuzzy pass against the set's real card list, because auto-caption transcripts mangle card names
  ("Cactus Durantula" for Cactarantula, "Magitech Armor" for Magitek Armor). The pass uses a 0.78
  similarity cutoff and **refuses near-ties**, so a garble that could plausibly be two different cards
  is dropped rather than attached to the wrong tile. Each build prints what it recovered.

The reviewer-grade column auto-detects its source: **DS** (Draftsim, numeric /5) if `grades/draftsim_<SET>.json`
exists, else **CGB** (CardGameBase, letter A+→F). The header caveat is set-aware (SOS = soup-inflation
warning; MKM = honest-WR guild-format note; MSH = early-data note + a 10-archetype color-pair map).

## Alternate image host (`alt_images_<SET>.json`)

If `card-reference/alt_images_<SET>.json` exists (a committed `{mtga_id: url}` map), the default build
uses those image URLs instead of Scryfall's. **ECL ships one pointing at TCGplayer's CDN**: ECL is a
brand-new set whose images are still cold at Scryfall's edge, so VS Code's preview burst (see below)
404s ~half of them — but TCGplayer's CDN is fully warm and serves the whole burst at 100% (verified
288/288 @120 concurrent). This keeps the committed `ECL-card-reference.md` a single remote-hotlink file
that loads reliably in **both VS Code and GitHub** — no local folder, no embedding needed. Regenerate the
map with a Scryfall→TCGplayer id lookup if a set needs it. The two options below are host-agnostic
fallbacks for any set.

## Viewing offline / in VS Code (`--local-images` / `--embed-images`)

The default `<SET>-card-reference.md` hotlinks card images from `cards.scryfall.io`. That's fine on
GitHub (images are proxied + cached server-side), but a client-side viewer like **VS Code's Markdown
preview pre-loads the whole document at once**, firing ~300 concurrent image requests. For a
**brand-new set** whose images aren't yet warm across Scryfall's CDN edges, that burst makes Scryfall
404 a large fraction of them, so cards show as broken "?" boxes (older sets are fully edge-cached and
survive the burst). `loading="lazy"` doesn't help — VS Code loads all images regardless for scroll-sync.

Fix — build a copy that doesn't hotlink. Two options:

```
python3 build_card_reference.py ECL --embed-images   # ONE self-contained file (recommended)
python3 build_card_reference.py ECL --local-images   # images in a sibling folder
```

- **`--embed-images`** inlines every card image as a base64 `data:` URI and writes
  `<SET>-card-reference.embedded.md` — a single self-contained file (~34 MB for ECL) with **no
  external dependencies**: no folder, no network, works offline anywhere you can open the `.md`. This
  is the simplest thing to open in VS Code.
- **`--local-images`** downloads images into `data/card-images/<SET>/` and writes
  `<SET>-card-reference.local.md` referencing them by relative path — smaller `.md`, but it needs the
  sibling folder to travel with it.

Both fetch Scryfall's `normal` size with 6 workers (under the burst threshold) and retry cold-edge
404s; `data/card-images/<SET>/` doubles as a download cache so a second build of either mode is
instant. Both output files are gitignored (the committed `.md` stays remote-hotlink for GitHub, which
proxies images server-side). Note: 17Lands occasionally hands out a stale `?timestamp` image URL that
404s permanently — the warmed Scryfall cache (`data/cache/scryfall_arena.json`, `image_url` per card)
has the current one.

## Regenerating

Layout/columns only: edit `build_card_reference.py` (`COLS`) and re-run — instant, no LLM.

**AI takes (per-set):** follow **[`AI_TAKES_PLAYBOOK.md`](AI_TAKES_PLAYBOOK.md)** — the codified, consistent
process. The mechanical steps are deterministic via `gen_ai_takes.py` (`prep` chunks the per-card context,
`merge` validates + writes `ai_takes_<SET>.json` keyed to the real card list); the creative step is a parallel
analyst-agent fan-out under a per-set doctrine written from that set's draft guides. Then add the set's
`CAVEAT` + `ARCHETYPES` entries in `build_card_reference.py` and rebuild.

## Coverage

Cards within each color group are ordered by **play rate (play %)**, highest first — except **HOB**, which
uses a rank-average of **ALSA + play rate**. On a young set those two are populated by every draft while GIH
WR lags, so they sort the whole card list rather than just the measured part.

**AI takes cover all ten sets.** The original five (SOS/MKM/MSH/BLB/ECL) were regenerated 2026-07-12
after the prep record began carrying each card's **oracle text + P/T + mana** (joined from Scryfall — MSH
by name, since its cards have no `arena_id`) — so the takes read what each card actually does and ground
the verdict in the expert notes, not just the stat columns. **DFT** (2026-07-18), **OTJ** (2026-07-21),
**DSK** (2026-07-23), **HOB** (2026-08-13) and **FIN** (2026-08-20, 357 cards) were then added under the
same pipeline. All ten are 100% covered. (The DSK pass
also fixed the shared guide-note parser to accept LoL's `[**Card**](link) (mana gloss) — note` bullet form
and Numot's `**Card:** note` colon-in-bold form, which recovered notes across ~20 sets — e.g. DSK 1→51.)

| Set | Cards | Live GIH WR | Sample | Guide notes | Reviewer grades |
|---|---|---|---|---|---|
| **BLB** | 271 | 265 | 27.6M | 150 | CGB 261 |
| **DFT** | 281 | 277 | 25.7M | 93 | CGB 271 |
| **DSK** | 281 | 272 | 34.6M | 60 | CGB 271 |
| **ECL** | 288 | 273 | 22.2M | 108 | — |
| **FIN** | 357 | 348 | 42.1M | 63 | — |
| **HOB** | 188 | 179 | 6.5M | 182 | CGB 188 · LR 183 |
| **MKM** | 321 | 296 | 28.6M | 147 | CGB 321 |
| **MSH** | 334 | 289 | 19.0M | 259 | CGB 276 |
| **OTJ** | 376 | 364 | 38.6M | 75 | CGB 376 |
| **SOS** | 341 | 327 | 29.2M | 166 | DS 341 |

**Every set is at 100% for images, AI takes and a format brief** — those three are the floor. What
varies is how much the rest of the world has written about a set:

- **Guide-note coverage tracks how many channels covered the set**, not its quality. MSH and HOB have
  four channels each; DSK and OTJ have two, and it shows.
- **ECL and FIN carry no reviewer grade at all** — no CardGameBase, Draftsim or Limited Resources file
  exists for them, so their tiles run on live win rates, guide notes and the AI take alone.
- **Sample size varies by two orders of magnitude at card level.** FIN's 42.1M games and OTJ's 38.6M
  are settled; bonus-sheet reprints inside any set sit in the low thousands and deserve much wider
  error bars than the commons beside them.
- **Cards short of a live GIH WR are genuinely unplayed rather than merely unmeasured** — they show
  ratings as blank rather than guessing.

To regenerate these numbers, run `build_card_reference.py <SET>` and read its summary line; it prints
card count, AI-take coverage, guide-note count and every grade source it found.
