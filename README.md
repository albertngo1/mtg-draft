# mtg-draft

A command-line **MTG Arena draft coach**. It reads the pack you're currently looking at out of
Arena's `Player.log`, ranks every card by [17Lands](https://www.17lands.com/) win-rate data, and
prints what each card does — automating the read-pack → resolve-names → fetch-17Lands → rank loop
you'd otherwise run by hand on every pick.

Runs **locally** on the same machine where you play Arena (Windows or macOS). No account login, no
overlay, no service — just a Python script and the log Arena already writes. Stdlib only, nothing
to `pip install`.

## Prerequisites

1. **Python 3.8+** — `python --version` (Windows) / `python3 --version` (macOS).
2. **Enable Arena's detailed logs** (one time): in MTG Arena go to
   **Settings → Account → check "Detailed Logs (Plugin Support)"**, then restart Arena. Without
   this the draft-pack entries this tool reads never get written to the log.

## Quick start

```bash
# macOS / Linux
git clone <your-fork-url> mtg-draft && cd mtg-draft

# Once per set: pre-cache card text + mana values so live picks make zero network calls.
# Use the 17Lands expansion code for the set you're drafting (see "Finding the set code" below).
python3 mtg-draft.py warm --set FIN

# During the draft — read the current pack from the local log and rank it:
python3 mtg-draft.py pull --set FIN --fmt PremierDraft
```

On **Windows**, use `python` and either `mtg-draft.py` directly or the `mtg-draft.bat` wrapper:

```bat
python mtg-draft.py warm --set FIN
mtg-draft.bat pull --set FIN --fmt PremierDraft
```

On macOS/Linux there's also a `./mtg-draft.sh` wrapper (`./mtg-draft.sh pull ...`).

### Commands

```bash
# Read the current pack from the log, rank it + show oracle text (colors auto-detected from picks)
python3 mtg-draft.py pull --set FIN --fmt PremierDraft

# Audit your picks so far: creatures/spells/lands split, curve, on/off-color, CABS check
python3 mtg-draft.py pool --set FIN

# Stream: auto-print the ranked table every time a new pack appears (run in its own terminal)
python3 mtg-draft.py watch --set FIN

# Manually rank an explicit list of Arena card IDs
python3 mtg-draft.py rank --set FIN --colors UR 102690 102462 102498

# Resolve IDs to name|cmc|color|type (handy for deck audits)
python3 mtg-draft.py resolve 102690 102462

# Capture: show the background log-capture status (see "Recording the raw log stream" below)
python3 mtg-draft.py capture          # start (if needed) + status   ·   `capture stop` to end it

# Draft history: parse the captured stream into drafts/current.json + a pick-by-pick summary
python3 mtg-draft.py draft            # (see "Reconstructed draft history" below)
```

Output: a table sorted by GIH WR (on-color cards per `--colors` marked `▸`, off-color tagged
`(off)`; columns `CARD CLR R MV GIHWR IWD ALSA N tier`), **followed by a "what each card does"
section** with mana cost, P/T, and oracle text — so picks are judged on fit, not just raw stats.
Use `--brief` for the table only. `--colors` is optional — for `pull`/`pool`/`watch` it's
auto-detected from the colored pips in the cards you've already taken.

### Finding the set code

`--set` takes a **17Lands expansion code** (e.g. `FIN`, `DSK`, `MKM`). The set you're currently
drafting is in the log under the event name, e.g. `"EventName":"PremierDraft_FIN_20250613"`. The
17Lands code is the same short code, and the Scryfall set code is its lowercase form.

## Flags / config

| flag | env | default | meaning |
|---|---|---|---|
| `--set` | `MTG_SET` | `FIN` | 17Lands expansion code for the set you're drafting |
| `--fmt` | `MTG_FMT` | `PremierDraft` | PremierDraft / QuickDraft / TradDraft / Sealed |
| `--colors` | `MTG_COLORS` | (auto) | mark these colors on-color, e.g. `UR` (auto-detected if omitted) |
| `--days` | `MTG_DAYS` | `120` | 17Lands lookback window in days |
| `--brief` | | | table only, skip the oracle-text section |
| `--refresh` | | | force re-fetch of the cached 17Lands data |
| `--poll N` | | `2` | `watch` poll interval in seconds |
| `--cap-mb N` | `MTG_CAP_MB` | `50` | front-truncating size cap for the captured log stream |
| `--local` | `MTG_LOCAL` | (default) | force a local log read (this is already the default) |
| | `MTG_LOG` | auto per-OS | override the `Player.log` path |

**Default `Player.log` locations** (override with `MTG_LOG`):

| OS | Path |
|---|---|
| Windows | `%USERPROFILE%\AppData\LocalLow\Wizards Of The Coast\MTGA\Player.log` |
| macOS | `~/Library/Logs/Wizards Of The Coast/MTGA/Player.log` |
| Linux (Steam/Proton) | `~/.steam/.../compatdata/2141910/.../MTGA/Player.log` (best-effort; set `MTG_LOG`) |

## Advanced: read the log from another machine (SSH)

If Arena runs on a *different* machine than the one running this tool (e.g. you keep the script on
a server and play on a laptop), point it at the other machine over SSH instead of reading locally:

```bash
python3 mtg-draft.py pull \
  --ssh user@host \
  --ssh-key ~/.ssh/your_key \
  --set FIN --fmt PremierDraft
# also settable via MTG_SSH / MTG_SSH_KEY. When using SSH, set MTG_LOG to the log path
# ON THE REMOTE machine.
```

SSH mode is **opt-in** — it activates only when `--ssh`/`MTG_SSH` is set. With no SSH target the
tool always reads the local log.

## How it works

1. `pull` reads the last `DraftPack` array out of `Player.log` (locally by default).
2. 17Lands `card_ratings/data` for the set+format provides GIH WR / IWD / ALSA **and** the
   `mtga_id` for every card — so packs join to stats directly by ID (no fragile name-matching).
   Cached 24h in `cache/`.
3. Scryfall supplies only what 17Lands lacks — mana cost, P/T, oracle text. `warm` pre-pulls the
   whole set via the `e:<set>` search in one paginated walk; otherwise misses are resolved
   one-by-one via `cards/arena/<id>`. Cached persistently in `cache/scryfall_arena.json`.
4. Sorts by GIH WR, prints the table + the card-text section.

After `warm`, a `pull`/`rank` for that set makes **zero** network round-trips until the 24h
17Lands cache expires.

**GIH WR rough guide:** 57%+ bomb · 54–57% excellent · 52–54% solid · 50–52% filler · <50% avoid.
Use **ALSA** (Average Last Seen At) as a tiebreaker — a low ALSA means the card won't wheel, so
take it now.

## Recording the raw log stream

Every draft command (`pull` / `pool` / `watch`) automatically starts a small **background
capture process** the first time it runs. That process follows `Player.log` and mirrors
**everything it emits** — unfiltered — into `logs/player_stream.log`, and keeps following it
(re-opening across Arena restarts) until you stop it. It's idempotent: only one capture runs
at a time, no matter how many times you call `pull`.

Why: it gives a **durable, complete record** of the whole draft session, so a coach (or you)
can answer "what were my options at P1P3?" by reading the saved stream instead of re-scraping
the noisy multi-MB live log — which only ever retains the *latest* pack anyway.

```bash
python3 mtg-draft.py capture          # start it (if not running) and print status
python3 mtg-draft.py capture status   # just print status (pid, source, stream size, cap)
python3 mtg-draft.py capture stop     # stop the background capture
```

**Size cap.** The stream is bounded by a **front-truncating** cap (default **50 MB**, set with
`--cap-mb N` or `MTG_CAP_MB`): when it exceeds the cap it drops the *oldest* bytes and keeps the
most recent, so a draft in progress is never the thing trimmed. Sized from real data — a full
draft spans only ~0.25 MB of the stream, so 50 MB holds ~6 h of play (200+ draft windows) before
trimming, and the parsed draft is persisted to its own JSON regardless (the raw stream is just a
rolling buffer).

`logs/` is gitignored. The capture follows whichever log the tool is configured to read —
local by default, or a remote log when `--ssh` is set (in which case the stream is still
written locally on the machine running the tool).

## Reconstructed draft history

`draft` turns the raw capture stream into a clean, structured record of your draft. It parses every
`BotDraft` pick out of `logs/player_stream.log`, segments the stream into separate drafts, recovers
**what you took at each pick** (by diffing the cumulative picked-list — duplicate picks and the
forced final card handled), enriches every card with 17Lands GIH WR / IWD / ALSA + grades, and
writes the most recent draft to **`drafts/current.json`**:

```jsonc
{
  "set": "MKM", "event": "QuickDraft_MKM_...", "ratings_fmt": "PremierDraft (historical proxy)",
  "n_picks": 39, "draft_id": "bc3cfb81",
  "analysis": {                                   // deckbuilding metrics over the picked pool
    "colors": "WB",
    "counts": { "creatures": 21, "spells": 14, "other": 4, "lands": 0, "nonland": 39, "total": 39 },
    "curve":  { "1": 7, "2": 12, "3": 8, "4": 7, "5": 4, "6": 1 },   // nonland mana curve
    "two_drops": 12, "five_plus": 5, "removal_est": 6,
    "targets": { "creatures": "15-18", "two_drops": "5-7", "removal": "3-4", "lands": 17 },
    "themes": { "evasion": 13, "sacrifice": 12, "graveyard": 11, "clues": 8, ... },  // mechanic tags
    "archetype_lean": [ "aggro / low-curve", "aristocrats (sacrifice / life-loss)" ],
    "open_color_signal": [ { "color": "R", "color_name": "red", "late_premiums_seen": 14 }, ... ],
    "open_color_readable": "14 red, 13 green, 7 black",   // same, spelled out for the player
    "flags":   [ /* e.g. "few creatures (12/15-18)", "thin removal (~2/3-4)" */ ]
  },
  "picks": [
    { "pack": 1, "pick": 1,
      "taken":   { "name": "Teysa, Opulent Oligarch", "gih": 0.615, "tags": ["clues","tokens"], ... },
      "running": { "n": 1, "colors": "WB", "creatures": 1, "curve": {...},   // cumulative deck so far
                   "passed_by_color": {...}, "premiums_passed_by_color": {...},
                   "premiums_passed_readable": "28 green, 27 red, 14 blue", "themes": {...} },
      "offered": [ { "name": "...", "gih": ..., "taken": false, "wheel": false, "tags": [...] }, ... ] },
    ...
  ],
  "pool": [ /* every card taken */ ]
}
```

Each pick's **`running`** block is the cumulative deck state *through that pick* (no reconstruction
needed): curve, creature/spell counts, and what you've **passed by color** + **premiums passed by
color** — so open lanes show up as you draft. Offered cards carry a **`wheel`** flag (true only when
the card came back around — seen 8 picks earlier in the same pack, an 8-player lap) and **`tags`**
(mechanic/theme labels). Pool-wide, those tags roll up into **`themes`** + an **`archetype_lean`**,
and `open_color_signal` reports which colors kept flowing premium cards late (pick 5+).

It also prints a pick-by-pick summary plus a **deck readout** (creature/spell/land counts, mana
curve, removal estimate, two-drop count, open-color signals, and target-vs-actual flags drawn from
standard Limited deckbuilding rules), and flags picks where a clearly higher-GIH card was left in
the pack (`⚠ passed ...`). This lets a coach answer "what did I pass at P1P5?" or "is my curve/
creature count healthy?" from one small file instead of re-scraping the multi-MB live log.

**Persistence.** Every draft in the stream is saved to a stable, idempotent archive at
`drafts/<set>_<fingerprint>.json` (fingerprint = hash of the P1P1 pack, so re-runs overwrite the
same file rather than piling up), and the most recent is mirrored to `drafts/current.json`. `pull`
refreshes these automatically each pick. So a draft is preserved permanently once it's been seen,
even after it ages out of the rolling capture stream. `drafts/` is gitignored (local archive).

**Ratings for re-run / rotated sets:** if the drafted format has no 17Lands win-rate data yet (e.g. a
Quick Draft re-run early in its window), `draft` automatically proxies with the set's original
PremierDraft data over a wide historical window — and notes it in `ratings_fmt`.

## Using it as an agent / coach

The tool is useful standalone, but it's designed to be driven by an **LLM agent** (e.g. Claude
Code) that turns the raw rankings into pick-by-pick coaching. [`AGENTS.md`](./AGENTS.md) is the
operating manual for that agent. At a high level it covers:

- **The per-pick loop** — `warm` once, then `pull` each pick; how to read the ranked table + the
  "what each card does" block so picks are judged on *fit*, not just the GIH WR column.
- **Cross-referencing** — how to weigh a card's 17Lands win-rate against theory grades and expert
  guides (see "Third-party insight sources" below), with **17Lands GIH WR as the primary signal**
  and everything else as a decorrelated second opinion.
- **Reading 17Lands correctly** — what each column means (GIH WR / IWD / ALSA), the small-sample
  and selection-bias traps, and ALSA as a wheel/timing signal.
- **Draft strategy fundamentals** — color/curve reads, signal reading, when to commit vs. stay
  open, and building the final pool — so an agent with no MTG background can coach competently.

The manual is intentionally **generic** — it's universal Limited theory plus this tool's pipeline,
with no player-specific preferences baked in. Drive it from your assistant by pointing the agent at
`AGENTS.md` at the start of a draft and having it run the `pull` loop each pick.

### Third-party insight sources

You can feed the coach two kinds of external, set-specific knowledge. Both are treated as
**theory/expert opinion that cross-references — never overrides — the 17Lands win data**, because
their error is decorrelated from game outcomes (they flag cards worth a second look; they don't
settle them).

**1. Reviewer grades → a grade column in the ranked table.** Drop a JSON file at
`grades/<source>_<SET>.json` and the tool auto-joins it as a grade column when you `pull`/`rank`
that set. The column is labeled by source — `DS` (Draftsim, x/5), `CGB` (CardGameBase, letter tier
A+→F), or `LG` (LimitedGrades); the first source found for the set wins. The format is a flat
`card name → grade` map plus a `_source` note (the grade value is shown verbatim, so numeric and
letter scales both work; split/MDFC names are matched on their front face):

```json
{
  "_source": "draftsim.com/<set>-pick-order/ (captured 2026-06-06). Grade out of 5. Theory grades, not empirical.",
  "Some Bomb Rare": 4.5,
  "A Solid Common": 3.2
}
```

Some tier-list sites (Draftsim) are JS-rendered with no clean API, so the practical capture flow is:
open the page, save/paste the rendered HTML, parse `name → grade` into the JSON, and commit it under
`grades/` (this dir **is** committed — unlike `cache/`). **CardGameBase is server-rendered**, so its
list can be fetched directly (`cardgamebase.com/<set>-draft-tier-list/`) — that's how the bundled
`grades/cardgamebase_MKM.json` was built. Use a *theory* grade source (human
power-evaluation); don't add a second *empirical* source — another win-rate metric just duplicates
17Lands and adds noise.

**2. Expert strategy guides → `lords-of-limited/<SET>-draft-guide.md`.** For longer-form, pre-digested
set strategy (meta read, archetype tier table, per-card notes, signals), each set gets a consolidated
`<SET>-draft-guide.md` (kept flat in `lords-of-limited/`) that the agent loads once and holds in
context for the whole draft, plus a per-set `<set>/sources/` layer of per-episode notes to dig into a
specific pick. See
[`lords-of-limited/README.md`](./lords-of-limited/README.md) for the layout and the conventions for
adding a new set (date-prefixed source notes, a recency rule where the newest take wins on
conflict). Guides distilled from public content (e.g. strategy YouTube channels) are credited to
their source there.

## Data sources & credits

- **[Scryfall](https://scryfall.com/)** — card names, mana costs, oracle text (queried at runtime;
  not redistributed). Please respect their [API guidelines](https://scryfall.com/docs/api).
- **[17Lands](https://www.17lands.com/)** — draft win-rate statistics (queried at runtime).
- Magic: The Gathering is © Wizards of the Coast. This is an unofficial fan tool, not affiliated
  with or endorsed by Wizards of the Coast.

## Requirements

- Python 3 (standard library only — no pip installs).
- Outbound HTTPS to `api.scryfall.com` and `www.17lands.com`.
- MTGA "Detailed Logs (Plugin Support)" enabled.
