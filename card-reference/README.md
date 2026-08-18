# Card Reference

Single-file, visual card references for a set: every draftable card as a tile in a
3-per-row grid, with image, 17Lands ratings, Draftsim grade, expert-guide notes, and an AI take.

## Files

- `build_card_reference.py` — generator. `python3 build_card_reference.py [SET]` (default `SOS`).
- `ai_takes_<SET>.json` — pre-generated per-card AI verdicts (name → take), committed so the
  build is reproducible without re-running the LLM pass.
- **Format brief** — an optional per-set `BRIEF` entry in the generator, rendered between the
  archetype map and the card grid. This is where the expert-guide commentary that *isn't* attached
  to a single card goes: the draft plan, gameplay rules, deckbuilding doctrine, traps, and any
  cross-source disagreements. The point is that the reference is self-contained — you should never
  have to open `draft-guides/` in a second window while drafting. HOB ships one.
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

**AI takes cover all nine sets.** The original five (SOS/MKM/MSH/BLB/ECL) were regenerated 2026-07-12
after the prep record began carrying each card's **oracle text + P/T + mana** (joined from Scryfall — MSH
by name, since its cards have no `arena_id`) — so the takes read what each card actually does and ground
the verdict in the expert notes, not just the stat columns. **DFT** (2026-07-18), **OTJ** (2026-07-21),
**DSK** (2026-07-23) and **HOB** (2026-08-13) were then added under the same pipeline. All nine are 100% covered. (The DSK pass
also fixed the shared guide-note parser to accept LoL's `[**Card**](link) (mana gloss) — note` bullet form
and Numot's `**Card:** note` colon-in-bold form, which recovered notes across ~20 sets — e.g. DSK 1→51.)

- **HOB** — 188/188 cards with image + AI take, 174/188 with live GIH WR (young: 1.63M PremierDraft games, two
  days after Arena release) + 188 CGB grades + 115 LR grades; 138/188 with ≥1 expert note (LR 865, Limited
  Level-Ups primer, Lords of Limited crash course). **First set to carry two reviewer-grade sources at once**
  (LR and CGB render side by side). Header carries a 5-archetype map with live archetype win rates. Also the
  first set built through the pre-data path: scaffolded from Scryfall while 17Lands was empty, then refreshed
  in place. Scryfall reports no `arena_id` for HOB, so oracle text joins by name.
- **SOS** — 341/341 cards with image + 17Lands ratings + DS grade + AI take; 155/341 with ≥1 expert note.
- **MKM** — 321/321 cards with image + 17Lands ratings + CGB grade + AI take; 142/321 with ≥1 expert note.
- **MSH** — 334/334 cards with image + AI take, 285/334 with live GIH WR (mature: ~15.2M PremierDraft games,
  QuickDraft + Sealed also live) + 276 CGB grades; 234/334 with ≥1 expert note (Limited Level-Ups wired in —
  the largest MSH guide). Header carries a 10-archetype color-pair map. Takes under the MSH slow-grindy doctrine.
- **BLB** — 271/271 cards with image + full-format GIH WR + CGB grade + AI take; 124/271 with ≥1 expert note
  (all 3 guides are end-of-format retrospectives). Header carries the 10-tribe color-pair map; takes are
  archetype-aware (typal/"false friend" decoding).
- **ECL** — 288/288 cards with image + AI take, 273/288 with live GIH WR (mature: ~22.2M PremierDraft games);
  103/288 with ≥1 expert note (LoL + Numot; no reviewer-grade file exists yet). Header carries the tribal
  color-pair map. Takes under the ECL tribal-synergy doctrine; GIH WR decoded for removal-underrating and
  payoff-inflation.
- **DFT** — 281/281 cards with image + AI take, 277/281 with live GIH WR (finished format, Feb–Mar 2025);
  271/281 with CGB grade (the 10 without are special-guest reprints); 76/281 with ≥1 expert note (LoL + Numot).
  Header carries a 9-row color-pair archetype map. Takes under the DFT slow-vehicles doctrine (Green ≥ Black
  best at common, blue-uncommons elite); GIH WR decoded for green-fatty inflation and cheap-removal underrating.
- **OTJ** — 376/376 cards with image + AI take, 364/376 with live GIH WR (finished format, 2024); 376/376 with
  CGB grade; 61/376 with ≥1 expert note (LoL + Numot). Header carries a 10-row color-pair archetype map + a
  Big Score (OTP) bonus-sheet note. Takes under the OTJ bombs-and-removal doctrine (Green best / GW mounts,
  blue underrated/open, red weakest); GIH WR decoded for multicolor-soup + build-around-payoff inflation and
  efficient-removal underrating.
- **DSK** — 281/281 cards with image + AI take, 272/281 with live GIH WR (finished format, Sep–Oct 2024);
  271/281 with CGB grade; 51/281 with ≥1 expert note (LoL + Numot). Header carries a 10-row color-pair
  archetype map. Takes under the DSK graveyard-matters-midrange doctrine (Green > Black >> Blue > White > Red;
  Delirium/Manifest Dread/Eerie axes, 4-toughness magic number); GIH WR decoded for synergy/build-around-payoff
  inflation and cheap-exile-removal underrating.
