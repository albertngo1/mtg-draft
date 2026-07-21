# Draft Overlay

A transparent, click-through, always-on-top window that floats the **current draft pack** over
MTG Arena — 17Lands GIH · CGB grade · ALSA · wheel flag · tags · and the pre-baked **AI take** per
card, ranked by GIH WR.

It does **no game-reading of its own**: mtg-draft's capture daemon already parses `Player.log` and
refreshes `data/drafts/current.json` every pick. The overlay just polls that file, joins two local
lookups (`card-reference/ai_takes_<SET>.json` for the take, `data/cache/cards_<SET>.ndjson` for
oracle text/guide), and draws. No network, no LLM call per pick — instant and offline.

## Prerequisites (on the drafting machine — the Mac laptop)

Everything must be **local to where Arena runs**, so run the whole tool there:

1. Clone/copy this repo to the laptop and warm the set you'll draft (once per set):
   ```bash
   python3 src/mtg-draft.py warm  --set OTJ
   python3 src/mtg-draft.py cards --set OTJ > data/cache/cards_OTJ.ndjson
   ```
2. **Run MTG Arena in windowed or borderless-windowed mode.** Exclusive fullscreen refuses *all*
   overlays (same limitation as Untapped.gg / 17Lands) — a fullscreen app owns its Space and nothing
   draws over it.

You do **not** need to start the capture daemon yourself — the overlay does it (see below). If you'd
rather manage it yourself (e.g. the SSH/remote-read setup), launch with `MTG_NO_CAPTURE=1`.

## Run

Written in **TypeScript** — `src/*.ts` compiles to `dist/*.js`, which is what Electron runs.

```bash
cd overlay
npm install        # one-time: TypeScript + Electron (~200 MB). Not Homebrew — npm only.
npm start          # runs `npm run build` (tsc → dist/) then launches Electron
```

On launch the app **auto-starts mtg-draft's capture daemon** (`python3 src/mtg-draft.py capture`) so
`current.json` stays fresh — no separate terminal, zero setup beyond warming the set. The panel appears
docked to the right edge and updates itself every pick. After editing `src/`, `npm start` rebuilds
automatically (or `npm run build` to compile without launching).

Config for the auto-capture: `MTG_NO_CAPTURE=1` disables it (you run the daemon yourself);
`MTG_PYTHON` overrides the `python3` executable.

## Controls (global hotkeys)

| Shortcut | Action |
|----------|--------|
| **⌘⇧O** | Toggle *grab* mode — catch the mouse so you can drag/resize and hover a tile to expand its take. Toggle off to make it click-through again (clicks pass to Arena). |
| **⌘⇧E** | Toggle showing every tile's AI take inline (vs. compact). |
| **⌘⇧H** | Hide / show the overlay. |

By default it's **click-through and compact**: it never steals a click from the game, and each tile
shows name · GIH% · grade · ALSA · 🎡 (wheeled) · tags. Grab it (⌘⇧O) and hover, or press ⌘⇧E, to
read the AI takes.

## Config (env vars)

| Var | Default | Meaning |
|-----|---------|---------|
| `MTG_ROOT` | parent of `overlay/` | repo root (where `data/` and `card-reference/` live) |
| `MTG_CURRENT` | `<ROOT>/data/drafts/current.json` | the structured current-pack file to poll |
| `MTG_POLL_MS` | `500` | poll interval |

## Headless smoke test

Verify the data join without launching the GUI (works anywhere Node is installed):

```bash
npm run probe                                          # tsx src/probe.ts, uses the live current.json
MTG_CURRENT=/path/to/some_current.json npm run probe   # against any current.json
# or, after a build:  node dist/probe.js
```

It prints the exact tile payload the overlay would render — GIH, grade, wheel, tags, AI take.

## How it's wired

```
src/main.ts ──spawn──► python3 src/mtg-draft.py capture   (src/capture.ts, auto-start)
                                    │
Player.log ──(capture daemon)──► data/drafts/current.json
                                                    │  poll 500ms
                                    src/pack.ts     ├─ join ai_takes_<SET>.json  (AI take by name)
                                                    └─ join cards_<SET>.ndjson   (oracle text/guide by id)
                                                    ▼
                        src/main.ts (transparent click-through window) ──► src/renderer.ts (tiles)
```

`src/pack.ts` is the Electron-free data layer shared by `main.ts` and `probe.ts`. Shared types live
in `src/global.d.ts` (ambient, so the Node side and the browser renderer share them without imports).
TypeScript config is `tsconfig.json`; build output (`dist/`) is gitignored.

## v1 limitations / next steps

- Grab mode is all-or-nothing (whole window). A later pass can use Electron's `forward` mouse events
  to grab the mouse only over a hovered tile, keeping the rest click-through without the toggle.
- Window position isn't persisted between runs yet.
- No card image on the tile (kept lean); could add a small thumbnail from the warmed Scryfall cache.
