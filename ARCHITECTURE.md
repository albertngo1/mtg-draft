# mtg-draft — architecture & full reference

> This is the complete reference: every command, flag, data path, and internal module, plus how the
> pieces fit together. For a quick overview and getting started, see the [README](./README.md). For
> the AI coaching layer's operating manual, see [AGENTS.md](./AGENTS.md). The repo also ships a separate
> **Commander deck builder** (`mtg-commander`); it has its own section,
> [Commander deck builder](#commander-deck-builder), and shares no code with the draft coach.

A command-line **MTG Arena draft coach**. It reads the pack you're currently looking at out of
Arena's `Player.log`, ranks every card by [17Lands](https://www.17lands.com/) win-rate data, and
prints what each card does — automating the read-pack → resolve-names → fetch-17Lands → rank loop
you'd otherwise run by hand on every pick.

Runs **locally** on the same machine where you play Arena (Windows or macOS). No account login, no
overlay, no service — just a Python script and the log Arena already writes. Stdlib only, nothing
to `pip install`.

## Two ways to use it: solo (no AI) or coached (AI)

The tool splits cleanly into a **deterministic core** and an **optional AI layer**. Pick whichever
you want — the core never depends on the AI.

**Solo — no AI, no account, no API key.** Everything that reads the pack and ranks it is plain
Python over cached 17Lands + Scryfall data. `warm` the set once, then keep **`watch`** running in a
side pane: each time a new pack appears it auto-prints the GIH-WR-ranked table, what each card does,
and your pool's curve/colors (colors auto-inferred as you pick) — no per-pick command, no network
call per pick (17Lands is cached), nothing leaves the machine. You draft straight off it; it's a
live 17Lands overlay. → see [Commands](#commands) — `warm`, `watch`, `pull`, `pool`, `draft`.

**Coached — adds an LLM agent (Claude Code).** Point an agent at [`AGENTS.md`](./AGENTS.md) and it
drives the same pack-reading loop, but turns the raw rankings into pick-by-pick *judgment*:
lane/signal reads, cross-referencing CGB tier grades + the expert guides in
[`draft-guides/`](./draft-guides/), mana-math warnings, and adapting when you override a pick. After
the draft it can also write a coached **replay** (one `claude -p` call per completed draft,
auto-enabled when the gitignored `claude-token.txt` exists — see [Reconstructed draft
history](#reconstructed-draft-history)). This layer is a *second opinion on top of* the solo
layer — skip it and nothing in the core stops working. → see [Using it as an agent /
coach](#using-it-as-an-agent--coach).

Either way, the **set guide + archetype read is the lead lens** (which color pairs are strongest in
the set, the card's role in the open archetype). The key idea: **every GIH WR is
archetype-conditional** — it's the win rate of *the decks that drafted the card*, not a context-free
measure (a Converge payoff's high WR is the soup deck's result, not yours). So the guide leads
because it **decodes** what the number is conditioned on ("A in soup, C in 2-color"), not because
it's unbiased. WR **transfers** for cleanly-castable cards (trust it) and is **inflated** for
payoffs/multicolor (discount unless you're that deck); **ALSA** is the one column orthogonal to win
rate (draft behavior, not outcome) and **IWD** is a noisier win-rate delta — a flag only. See
AGENTS.md for the full treatment. The AI take is decorrelated expert color, not the source of truth.

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
python3 src/mtg-draft.py warm --set FIN

# During the draft — read the current pack from the local log and rank it.
# Set + format are auto-detected from the live draft's event name (override with --set/--fmt):
python3 src/mtg-draft.py pull
```

On **Windows**, use `python` and either `src/mtg-draft.py` directly or the `mtg-draft.bat` wrapper:

```bat
python src/mtg-draft.py warm --set FIN
mtg-draft.bat pull
```

On macOS/Linux there's also a `./mtg-draft.sh` wrapper (`./mtg-draft.sh pull ...`).

### Commands

```bash
# Read the current pack from the log, rank it + show oracle text (set/fmt auto-detected from the
# live draft's event name, colors auto-detected from your picks)
python3 src/mtg-draft.py pull

# Audit your picks so far: creatures/spells/lands split, curve, on/off-color, CABS check
python3 src/mtg-draft.py pool

# Sealed: read your whole 6-pack pool from the log (deck-builder open in Arena), rank it + show
# oracle text, then a category/curve breakdown that keeps copy counts ("Tackle Artist x3")
python3 src/mtg-draft.py sealed

# Stream: auto-print the ranked table every time a new pack appears (run in its own terminal)
python3 src/mtg-draft.py watch

# Manually rank an explicit list of Arena card IDs
python3 src/mtg-draft.py rank --set FIN --colors UR 102690 102462 102498

# Resolve IDs to name|cmc|color|type (handy for deck audits)
python3 src/mtg-draft.py resolve 102690 102462

# Whole-set lean data as NDJSON — one card per line: stats + oracle text + guide note + inflation
# flag. Build once per draft, then grep the pack's IDs out of it per pick (instant, local) instead
# of re-streaming oracle text. Surfaces the guide/inflation the live `pull` table doesn't print.
python3 src/mtg-draft.py cards --set FIN > data/cache/cards_FIN.ndjson

# Capture: show the background log-capture status (see "Recording the raw log stream" below)
python3 src/mtg-draft.py capture          # start (if needed) + status   ·   `capture stop` to end it

# Draft history: parse the captured stream into data/drafts/current.json + a pick-by-pick summary
python3 src/mtg-draft.py draft            # (see "Reconstructed draft history" below)
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

For `pull`/`pool`/`watch` (and the capture daemon's auto-enrich), **set and format are auto-detected
from that event name** — `--set` is only needed for `warm`/`rank`, or to override the detection. The
format slot is adopted only when it's a real 17Lands format (special events like Midweek Magic put
other tokens there). If the format has **no win-rate data yet** (e.g. a Quick-Draft re-run early in
its window), the ranked table and the draft store automatically fall back to the set's original
**PremierDraft data over a wide historical window** — noted in the table header and in the store's
`ratings_fmt`.

## Flags / config

| flag | env | default | meaning |
|---|---|---|---|
| `--set` | `MTG_SET` | (auto) | 17Lands expansion code — auto-detected from the live draft for `pull`/`pool`/`watch`; the flag overrides (fallback default `FIN`) |
| `--fmt` | `MTG_FMT` | (auto) | PremierDraft / QuickDraft / TradDraft / Sealed — auto-detected from the live draft; the flag overrides (fallback default `PremierDraft`) |
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
python3 src/mtg-draft.py pull \
  --ssh user@host \
  --ssh-key ~/.ssh/your_key \
  --set FIN --fmt PremierDraft
# also settable via MTG_SSH / MTG_SSH_KEY. When using SSH, set MTG_LOG to the log path
# ON THE REMOTE machine.
```

SSH mode is **opt-in** — it activates only when `--ssh`/`MTG_SSH` is set. With no SSH target the
tool always reads the local log.

**The `mtg-draft.sh` wrapper auto-wires SSH from the capture config.** If the capture daemon's
`data/logs/.capture.json` carries an `ssh` / `ssh_key` / `log` (it does once you've run `capture`
against a remote — see "Keeping capture always-on"), the wrapper exports `MTG_SSH` / `MTG_SSH_KEY` /
`MTG_LOG` from it before invoking Python, so `./mtg-draft.sh pull` reaches the remote log with **no
flags**. It only fills blanks — anything you set in the environment still wins.

> **The key must run a normal login shell — don't reuse a forced-command key.** The tool reads the
> log by sending a remote command (`tail … | grep DraftPack`). If `--ssh-key` points at a key that's
> pinned to a fixed command on the remote (an `authorized_keys` entry with `command="…"`, as a
> reverse-tunnel / port-forward-only key usually is), the remote ignores the command the tool sends
> and runs its own — so `pull` returns **"No DraftPack found"** (or a bare exit 1) even though
> authentication succeeds and the host is up. Use a key whose `authorized_keys` entry has **no**
> `command=` restriction. Quick check: `ssh -i ~/.ssh/your_key user@host 'echo ok'` must print `ok`
> — if it prints nothing and exits 1, the key is forced-command and won't work here.

## Repository layout

```
mtg-draft/
├─ mtg-draft.sh / mtg-draft.bat   # launchers (run from the repo root)
├─ mtg-commander.sh / .bat        # launchers for the Commander deck builder
├─ src/
│  ├─ mtg-draft.py                # thin entry shim → mtgdraft.cli.main()
│  ├─ mtg-commander.py            # thin entry shim → mtgcommander.cli.main()
│  ├─ mtgcommander/               # the Commander deck builder (module map: "Commander deck builder" below)
│  ├─ replay.py                   # render a captured draft into a coached markdown replay
│  └─ mtgdraft/                   # the package (one concern per module)
│     ├─ config.py                #   paths, defaults, colour names, log-path detection
│     ├─ sources.py              #   17Lands + Scryfall fetch/cache (warm, seventeen, resolve)
│     ├─ grades.py                #   reviewer-grade + LoL guide-note loaders
│     ├─ analysis.py              #   tags, inflation, deck-needs, archetype, removal regex
│     ├─ logread.py               #   read Player.log → current pack / picks / colours
│     ├─ capture.py               #   the streaming daemon (+ auto-enrich hook)
│     ├─ etl.py                   #   reconstruct drafts → enrich → current.json
│     ├─ render.py                #   table / pool / summary printers, watch
│     └─ cli.py                   #   arg parse + command dispatch (main)
├─ grades/                        # committed reviewer grades: <source>_<SET>.json
├─ draft-guides/                  # committed expert set guides (two channels)
│  ├─ lords-of-limited/           #   Lords of Limited <SET>-draft-guide.md (one per set)
│  └─ numot/                      #   NumotTheNummy VOD-distilled <SET>.md notes (+ manifest.json)
├─ card-reference/                # visual card-reference builder + ai_takes_<SET>.json + <SET>-card-reference.md
│  └─ briefs/<SET>.md            #   REQUIRED per-set format brief (build fails without it)
├─ commander/                     # committed reference data for the Commander builder: brackets.json,
│                                 #   role_targets.json, playstyles.json (what each holds: commander/README.md)
├─ tests/commander/               # the Commander builder's unit tests (standard-library unittest, no network)
└─ data/                          # generated, gitignored
   ├─ cache/                      # 17Lands + Scryfall caches, + cards_<SET>.ndjson exports
   │  └─ commander/<source>/      #   the Commander builder's downloads, one folder per source
   ├─ drafts/                     # per-draft bundles <set>_<date>_<fp>/{draft.json,raw.log,replay.md} + current.json
   └─ logs/                       # raw Player.log capture stream
```

Paths resolve relative to the repo root regardless of where you invoke from, so
`python3 src/mtg-draft.py …`, `./mtg-draft.sh …`, and the `.bat` wrapper are interchangeable.

## How it works

1. `pull` reads the current pack out of `Player.log` (locally by default). Quick Draft logs it as a
   `DraftPack` array (carrying `PickedCards` + `EventName` on the same line); Premier/Traditional
   (human) drafts have no `DraftPack` — there the pack is the last `Draft.Notify` (`PackCards` CSV),
   the pool is rebuilt from `MakePick` (`GrpIds`), and set/fmt come from the event-join course line.
   **Sealed** has neither — `sealed` reads the deck-builder's `"Course":{…"CardPool":[…]…}` line
   (the whole 84-card pool at once; set/fmt from its `InternalEventName`). That line is logged once
   when the builder opens and scrolls out of the live tail quickly, so `sealed` scans the capture
   daemon's full-history stream mirror first (filtering to the singular `"Course":{` payload so the
   plural `"Courses":[…]` event-hub list — whose first `CardPool` may be another event — is ignored).
2. 17Lands `card_ratings/data` for the set+format provides GIH WR / IWD / ALSA **and** the
   `mtga_id` for every card — so packs join to stats directly by ID (no fragile name-matching).
   Cached 24h in `data/cache/`.
3. Scryfall supplies only what 17Lands lacks — mana cost, P/T, oracle text. `warm` pre-pulls the
   whole set via the `e:<set>` search in one paginated walk; otherwise misses are resolved
   one-by-one via `cards/arena/<id>`. Cached persistently in `data/cache/scryfall_arena.json`.

   **New-set fallback.** Scryfall does not assign `arena_id` until some weeks after a set reaches
   Arena, so for a just-released set *every* id lookup 404s and the whole set would cache as
   failed placeholders — the table still ranks correctly (that join is on 17Lands' own `mtga_id`)
   but shows `MV 0` with an empty card-text section, and `infer_colors` silently returns no colors
   because it counts mana pips. So both paths take the 17Lands card names and fall back to an
   exact-name lookup, re-keying the result onto the Arena id: `set_fetch` name-joins the whole
   paginated walk at once, `resolve_ids` does it per-card via `cards/named?exact=`. Nothing
   downstream changes — the cache stays id-keyed. `warm` reports how many were matched by name.
4. Sorts by GIH WR, prints the table + the card-text section.

After `warm`, a `pull`/`rank` for that set makes **zero** network round-trips until the 24h
17Lands cache expires.

**GIH WR rough guide:** 57%+ bomb · 54–57% excellent · 52–54% solid · 50–52% filler · <50% avoid.
Use **ALSA** (Average Last Seen At) as a tiebreaker — a low ALSA means the card won't wheel, so
take it now.

## Recording the raw log stream

Every draft command (`pull` / `pool` / `watch`) automatically starts a small **background
capture process** the first time it runs. That process follows `Player.log` and mirrors
**everything it emits** — unfiltered — into `data/logs/player_stream.log`, and keeps following it
(re-opening across Arena restarts) until you stop it. It's idempotent: only one capture runs
at a time, no matter how many times you call `pull`.

Why: it gives a **durable, complete record** of the whole draft session, so a coach (or you)
can answer "what were my options at P1P3?" by reading the saved stream instead of re-scraping
the noisy multi-MB live log — which only ever retains the *latest* pack anyway.

**Auto-enrich.** As picks stream in, the capture process also re-parses the stream and refreshes
`data/drafts/current.json` on its own (best-effort, fully isolated so an enrich error can never kill
the byte capture). So the structured draft store stays live with **no manual `pull`** — as long as
the daemon is running it doesn't matter whether you ever open the tool. It's skipped only if the
Scryfall cache is cold (run `warm` once), so the background process never makes surprise network
calls on a cold start.

```bash
python3 src/mtg-draft.py capture          # start it (if not running) and print status
python3 src/mtg-draft.py capture status   # just print status (pid, source, stream size, cap)
python3 src/mtg-draft.py capture stop     # stop the background capture
```

**Size cap.** The stream is bounded by a **front-truncating** cap (default **50 MB**, set with
`--cap-mb N` or `MTG_CAP_MB`): when it exceeds the cap it drops the *oldest* bytes and keeps the
most recent, so a draft in progress is never the thing trimmed. Sized from real data — a full
draft spans only ~0.25 MB of the stream, so 50 MB holds ~6 h of play (200+ draft windows) before
trimming, and the parsed draft is persisted to its own JSON regardless (the raw stream is just a
rolling buffer).

`data/logs/` is gitignored. The capture follows whichever log the tool is configured to read —
local by default, or a remote log when `--ssh` is set (in which case the stream is still
written locally on the machine running the tool).

### Keeping capture always-on (run it as a service)

The auto-start above only fires *while you have the tool open* — if you run a command, capture lives
until you `capture stop` or reboot. For a hands-off setup — e.g. an always-on box that follows Arena
on **another** machine over SSH, so every draft is saved with zero interaction — run the follower
under your OS service manager with restart-on-failure.

The long-lived worker is the hidden `_tail` command; it reads its source config (local vs SSH
target, log path, size cap) from `data/logs/.capture.json`. Generate that file once by running
`capture` with the source you want (it writes `.capture.json`, and you can then stop the ad-hoc
process), or write it yourself:

```json
{ "out": "/path/to/mtg-draft/data/logs/player_stream.log",
  "log": "/Users/you/Library/Logs/Wizards Of The Coast/MTGA/Player.log",
  "cap_mb": 50,
  "ssh": "user@arena-host",
  "ssh_key": "/Users/you/.ssh/id_arena" }
```

(Drop the `ssh`/`ssh_key` keys for a local follow; `log` is then the local path.) Then supervise
`python3 src/mtg-draft.py _tail data/logs/.capture.json`. On **macOS**, a `KeepAlive` LaunchAgent
at `~/Library/LaunchAgents/` does it:

```xml
<!-- com.mtg-draft.capture.plist — adjust paths/label; keep your SSH details OUT of any repo -->
<key>ProgramArguments</key>
<array>
  <string>python3</string>
  <string>/path/to/mtg-draft/src/mtg-draft.py</string>
  <string>_tail</string>
  <string>/path/to/mtg-draft/data/logs/.capture.json</string>
</array>
<key>RunAtLoad</key><true/>
<key>KeepAlive</key><true/>
```

Load with `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mtg-draft.capture.plist`
(`bootout` to unload). On Linux use a `systemd --user` unit with `Restart=always`; on Windows, a
Task Scheduler task set to "run whether logged on or not" with restart-on-failure. The follower
already self-heals across SSH drops and Arena's own log truncation, so the supervisor only needs to
cover full process death. Note: auto-enrich still needs the Scryfall cache warmed once per set
(`warm --set <CODE>`) — until then the raw byte capture is preserved but bundles aren't built.

## Reconstructed draft history

`draft` turns the raw capture stream into a clean, structured record of your draft. It parses every
`BotDraft` pick out of `data/logs/player_stream.log`, segments the stream into separate drafts, recovers
**what you took at each pick** (by diffing the cumulative picked-list — duplicate picks and the
forced final card handled), enriches every card with 17Lands GIH WR / IWD / ALSA + grades, and
writes the most recent draft to **`data/drafts/current.json`**:

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
                   "needs": ["2-drops (1)"], "needs_readable": "2-drops (1)",  // gaps, scaled to progress
                   "passed_by_color": {...}, "premiums_passed_by_color": {...},
                   "premiums_passed_readable": "28 green, 27 red, 14 blue", "themes": {...} },
      "offered": [ { "name": "...", "gih": ..., "taken": false, "wheel": false, "tags": [...],
                     "inflation": { "kind": "converge", "note": "..." },  // only when GIH is inflated
                     "guide": "expert one-liner from the set guide" }, ... ] },   // only if the guide notes it
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

**Per-draft bundles.** Every draft in the stream is persisted as a self-contained **bundle folder**,
`data/drafts/<set>_<YYYY-MM-DD_HHMM>_<fingerprint>/`. The **fingerprint** = hash of the P1P1 pack
(the real identity key, so re-runs overwrite the same folder rather than piling up). The **stamp** is
`YYYY-MM-DD_HHMM`: the day comes from the EventName's date (or first-creation day if it's malformed —
MKM Quick Draft logs a garbled 7-digit date), and the `HHMM` time is stamped once at first creation so
**multiple drafts on the same day get distinct, chronologically-ordered folders**. The stamp is
**reused from the existing folder name** on every later run, so it stays a stable idempotency key (it
can't drift to wall-clock "now" and mint a second folder). Each bundle holds three artifacts:

| file | what |
|---|---|
| `draft.json` | the enriched cumulative data store (every pick: offered+ratings+tags+inflation+guide, `running` state, `analysis`) |
| `raw.log` | just **this draft's** slice of the rolling stream (its `BotDraft` lines), spliced out by the P1P1 segmentation |
| `replay.md` | the coached audit/playback — **auto-generated once the draft completes** (final pack drafted to its last pick) |

The **chronologically newest** draft's `draft.json` (max bundle date, NOT list position — the
reconstructor emits all Quick drafts before all Premier ones, so position would pick a stale Premier
re-dump) is mirrored to `data/drafts/current.json`. A bundle also **self-heals**: if a later pass
reconstructs more picks than the one on disk (e.g. it was first written mid-draft at 1 pick), it's
re-enriched rather than skipped. The capture daemon refreshes all of this automatically each pick (or
you can run `draft`/`pull`). So a draft is preserved permanently once seen — bundle and all — even
after it ages out of the rolling capture stream.
Completion is detected from the log itself (pick count reaches the final pack's last pick), so the
replay fires whether or not you ever drove the tool. `data/drafts/` is gitignored (local archive).

**AI takes in the replay (opt-in).** The per-pick replay notes are deterministic heuristics by default.
Pass `--ai` to `replay.py` (`python3 src/replay.py <draft.json> <out.md> --ai`) to add a model-written
**`🤖 Take`** under each pick — one batched `claude -p` call that's fed each pick's *point-in-time*
deck state (no hindsight) plus the tool's coaching doctrine, so the takes match the same philosophy as
the rest of the tool. Each card in the payload carries its **oracle text + P/T** (joined back on at
take-time from the Scryfall cache by id — the model reads what the card actually *does*, not just its
stat columns) and its **per-card LoL guide note** (joined from the guide by name); the prompt also
appends **both set-level expert guides** (Lords of Limited + NumotTheNummy) as archetype/meta context,
so takes reflect the experts' reads, newest-source-wins on conflict. It needs a long-lived
`CLAUDE_CODE_OAUTH_TOKEN` (env, or a gitignored
`claude-token.txt` at the repo root). To have the daemon's auto-replays include takes too, set
`MTG_REPLAY_AI=1`; it's off by default so the background capture stays token-free and offline. Failures
are silent — the deterministic replay is unaffected.

**Ratings for re-run / rotated sets:** if the drafted format has no 17Lands win-rate data yet (e.g. a
Quick Draft re-run early in its window), `draft` automatically proxies with the set's original
PremierDraft data over a wide historical window — and notes it in `ratings_fmt`.

## Using it as an agent / coach

This is the **AI layer** from [Two ways to use
it](#two-ways-to-use-it-solo-no-ai-or-coached-ai). The solo CLI stands on its own, but the tool is
also designed to be driven by an **LLM agent** (e.g. Claude Code) that turns the raw rankings into
pick-by-pick coaching. [`AGENTS.md`](./AGENTS.md) is the operating manual for that agent. At a high
level it covers:

- **The per-pick loop** — `warm` once, then `pull` each pick; how to read the ranked table + the
  "what each card does" block so picks are judged on *fit*, not just the GIH WR column.
- **Cross-referencing** — how to weigh the expert guides + theory grades (the lead lens; see
  "Third-party insight sources" below) against the 17Lands columns: **every WR is
  archetype-conditional, the guide decodes what it's conditioned on, ALSA is the orthogonal signal,
  and GIH WR transfers or inflates by card type.**
- **Reading 17Lands correctly** — every WR is conditional on the decks that drafted the card; how to
  tell transfers-well (cleanly-castable) from inflated (payoffs/multicolor), the small-sample trap,
  ALSA as the orthogonal wheel/timing signal, and IWD as a noisier delta.
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
`grades/` (this dir **is** committed — unlike `data/cache/`). **CardGameBase is server-rendered**, so its
list can be fetched directly (`cardgamebase.com/<set>-draft-tier-list/`) — that's how the bundled
`grades/cardgamebase_MKM.json` was built. Use a *theory* grade source (human
power-evaluation); don't add a second *empirical* source — another win-rate metric just duplicates
17Lands and adds noise.

**2. Expert strategy guides → `draft-guides/lords-of-limited/<SET>-draft-guide.md`.** For longer-form, pre-digested
set strategy (meta read, archetype tier table, per-card notes, signals), each set gets a consolidated
`<SET>-draft-guide.md` (kept flat in `draft-guides/lords-of-limited/`, guide-only) that the agent loads once and holds in
context for the whole draft. The guide's **`## Card notes`** bullets (`- **Card** — note`) are also parsed
automatically and attached to each offered card as a `guide` field in the draft JSON, so the expert
one-liner travels with the card. See
[`draft-guides/lords-of-limited/README.md`](./draft-guides/lords-of-limited/README.md) for the layout and the conventions for
adding a new set (date-prefixed source notes, a recency rule where the newest take wins on
conflict). Guides distilled from public content (e.g. strategy YouTube channels) are credited to
their source there.

**3. NumotTheNummy VOD notes → `draft-guides/numot/<SET>.md`.** A second expert-notes source, distilled from
NumotTheNummy (Kenji Egashira) regular Arena draft VODs: per-set tips (`MKM.md`/`SOS.md` deepest,
38 other sets sampled), `general-tips.md` for evergreen principles, and a `## vs Lords of Limited`
section per tier-1 set flagging where the two experts disagree. The agent loads `draft-guides/numot/<SET>.md`
at draft start alongside the LoL guide; same status (theory/expert opinion, 17Lands GIH WR stays
primary). The scrape is fingerprinted in `draft-guides/numot/manifest.json` so re-runs only fetch/distill new
or changed VODs — see [`draft-guides/numot/README.md`](./draft-guides/numot/README.md) and `src/ingest/fingerprint.py numot`.

**Ingest is channel-agnostic.** All expert-prose channels share one pipeline keyed off
[`src/ingest/channels.json`](./src/ingest/channels.json): `fetch_subs.sh <slug>` (fetch + clean
captions), `fingerprint.py <slug>` (incremental manifest), and the distill output contract
(`channels.<slug>.distill_format`). The stage-2 runbook for turning transcripts into guides is
[`src/ingest/DISTILL.md`](./src/ingest/DISTILL.md). Adding a new YouTuber is a channels.json entry +
a worklist — no code changes.

## Commander deck builder

`mtg-commander` upgrades, builds and checks **Commander** decks. Commander (also called **EDH**, for Elder Dragon
Highlander) is a 100-card format with one copy of each card (basic lands excepted), led by a **commander** and
usually played by three or four people. It is a separate tool from the draft coach: it never reads Arena's log,
shares no code with `src/mtgdraft/`, and no existing module changed for it. Like the rest of the repo it is
standard library only, but it needs **Python 3.9+** (the draft coach runs on 3.8+).

Run it from the repo root. macOS and Linux also have `./mtg-commander.sh`; Windows has `mtg-commander.bat`:

```bash
# Ranked cuts and adds for a precon: at most $75 on cards you do not own, leaning toward tokens
python3 src/mtg-commander.py upgrade --precon "Squirreled Away" --budget 75 --theme tokens

# Legality, bracket rules, role counts and mana curve for a list in a file
python3 src/mtg-commander.py check mydeck.txt --bracket 3

# A full 100-card list around a commander
python3 src/mtg-commander.py build "Hazel of the Rootbloom" --bracket 3 --budget 150 --theme squirrels

# Every number about a list: power, interaction, mana, playstyle, win plan, money
python3 src/mtg-commander.py stats --precon "Squirreled Away" --bracket 3 --theme tokens --playstyle aristocrats

# The local server for the deck pages, and the numbers of a version it has saved (see "The deck server" below)
python3 src/mtg-commander.py serve
python3 src/mtg-commander.py stats --version andy/squirrels-go-wide
```

The first run downloads Scryfall's card file and builds a local index of about 35,000 cards (31 MB). That takes a
minute or two, once; the index is rebuilt after 7 days. Everything else it downloads is cached too (see
[Data sources, caching and offline use](#data-sources-caching-and-offline-use)).

### Terms used here

| term | meaning |
|---|---|
| **Bracket** | Wizards of the Coast's 1–5 power scale: 1 Exhibition, 2 Core, 3 Upgraded, 4 Optimized, 5 cEDH. **cEDH** is competitive Commander, meaning tournament play. The default is Bracket 3. |
| **Game Changer** | a card on Wizards' list of cards that push a deck up the scale (53 on 2026-10-11, flagged on each card in Scryfall's data). Bracket 3 allows up to three; Brackets 1 and 2 allow none. |
| **Precon** | a preconstructed deck sold ready to play. Precon lists come from MTGJSON. |
| **Base deck**, **version** | a base deck is where a saved deck starts (a precon or a pasted list) and never changes; a version is one player's copy of a base deck with every change they made. Both are files ([Deck files](#deck-files)); `serve` reads and changes them. |
| **Price point** | a dollar amount `upgrade` stops at on the way up to your budget (for $200: $25, $50, $100 and $200). The report shows what the swaps found up to each amount come to. |
| **Inclusion** | the share of a commander's decks that play a card. **Synergy** is EDHREC's inclusion with this commander minus the inclusion across all decks of the same colors. |
| **Removal power** | the sum, over a deck's removal cards, of how quick, how far-reaching, how lasting and how cheap each is (see [Deck metrics and `stats`](#deck-metrics-and-stats)). The tool's own measure, with weights that are judgment calls |
| **Role** | a job a deck needs in numbers: ramp (extra mana), card draw, removal, board wipes, counterspells, protection, recursion, tutors, finishers. |
| **Fantasy** | the experience the player wants from the deck: themes (squirrels, tokens), a playstyle (go-wide, control), how much to favor them, and cards to keep or avoid. |
| **Salt** | EDHREC's player-voted score, 0 to 4, for how frustrating a card is to play against. |
| **Builder choice**, **tournament result** | the two kinds of evidence. Every number the tool prints is one of them (or a labeled fallback), with the number of decks behind it. |

### What the numbers are, and are not

No public source records which casual Commander decks win, so there is no casual win rate to rank by. At
Brackets 1–4 the best signal available is what experienced builders chose at that bracket, and that is what the
tool uses: a card's base score is its inclusion rate among decks of that bracket (EDHREC, with Archidekt as a
second source), pulled toward the all-bracket rate while the bracket has few decks. That is a choice, not a win
rate. Every line says which it is and how many decks it rests on, and every report below Bracket 5 ends with
*"At Bracket N these numbers show what deck builders chose, not how often decks won."* Real per-card win rates
exist publicly only for tournament (cEDH) play, through EDHTop16. They set the score at Bracket 5 and enter as a
small, shrunk correction for mana, card draw and interaction at Brackets 3 and 4.

The shrinking matters for the reason it matters in the draft coach: a card's win rate belongs to the decks that
played it. In EDHTop16's Chatterfang decks for the year to 2026-10-11, the lists that ran Skullclamp reached the
top cut 14% of the time (165 entries) and the lists that did not reached it 38% of the time (119 entries). That
gap says the two groups are different kinds of deck, not that Skullclamp is bad. So the tournament term is
shrunk by sample size, capped, weighted by bracket (0 at Brackets 1 and 2) and applied below Bracket 5 only to
roles whose value does not depend on the rest of the deck.

Each card's evidence has a kind: `builder` (inclusion among decks at the bracket), `tournament` (Bracket 5 play
rate), `popularity` (Scryfall's overall EDHREC rank, used only when no deck-builder data is available) or `none`
(on no list). Example output, from cached data of 2026-10-11 (the numbers move as the data and weights are updated):

```
Squirreled Away → Bracket 3, budget $75 (spent $71.44); themes: tokens; playstyle: aristocrats
Hazel of the Rootbloom (BG), 100 cards

Price points (each includes the ones above it):
  $20   spend $19.41   value 90.5 (+10.7)   25 swaps
  $40   spend $39.72   value 92.2 (+12.4)   31 swaps
  $75   spend $71.44   value 92.9 (+13.1)   35 swaps

Up to $20:
 1  CUT Swamp  →  ADD Peregrin Took   +0.96  $0.42
    in 57% of 1,125 Bracket 3 Hazel decks (all brackets 49%, synergy +45%); +8% in sacrifice decks
...
Sources: EDHREC 2026-10-11, EDHTop16 2026-10-11, Scryfall 2026-10-11, MTGJSON 2026-10-11.
At Bracket 3 these numbers show what deck builders chose, not how often decks won.
```

The number after the swap (`+0.96`) is its gain: the change in the deck's value, in the same units as a card score (a
card every builder plays scores about 1; see [How a deck is valued](#how-a-deck-is-valued-and-how-swaps-are-chosen)).
With a budget the report also shows what less money would buy: each *price point* line sums up every swap found up to
that amount (the money it spends, the deck's value and its change from the start, the number of swaps), and the swap
list is split with a heading such as `Up to $20:` where a step begins (how the steps work is in
[How a deck is valued and how swaps are chosen](#how-a-deck-is-valued-and-how-swaps-are-chosen)). A price point that
has brought the deck's answers to some kind of threat down from the starting count to what a typical deck at the
bracket holds, or under it, has a note under its line (`fewer answers: creatures 14 → 10 (typical 10), planeswalkers
7 → 3 (typical 3)`), and an `Answers:` line under `Roles:` gives the kinds whose count changed (`creatures 14→10`). With
a budget but only one price point there is no price-point block, so the note goes under the `Answers:` line; without a
budget there are no price points and only the `Answers:` line is shown.

### Commander commands and flags

```
mtg-commander <command> [--json] [--refresh] [--offline] [--sources LIST] ...

themes   [--commander NAME] [--partner NAME]
suggest  [--theme T] [--playstyle P] [--fantasy TEXT] [--keep-fun | --no-keep-fun] [--bracket N]
         [--colors WUBRG] [--budget USD] [--owned FILE] [--owned-precon NAME] [--limit N]
build    COMMANDER [--partner NAME] [--bracket N] [--budget USD] [--theme T] [--playstyle P]
         [--fantasy TEXT] [--fantasy-weight W] [--keep-fun | --no-keep-fun] [--include CARD]
         [--exclude CARD] [--owned FILE] [--owned-precon NAME] [--allow-combos] [--out FILE] [-v]
upgrade  [DECKFILE] [--precon NAME] [--commander NAME] [--bracket N] [--budget USD] [--max-swaps N]
         [--price-points LIST] [--theme T] [--playstyle P] [--fantasy TEXT] [--fantasy-weight W]
         [--keep-fun | --no-keep-fun] [--include CARD] [--exclude CARD] [--owned FILE]
         [--owned-precon NAME] [--allow-combos] [--out FILE] [-v]
check    [DECKFILE] [--precon NAME] [--commander NAME] [--bracket N]
stats    [DECKFILE] [--precon NAME] [--version PLAYER/ID] [--commander NAME] [--bracket N] [--theme T]
         [--playstyle P] [--fantasy TEXT] [--fantasy-weight W] [--keep-fun | --no-keep-fun] [--owned FILE]
         [--owned-precon NAME] [-v]
serve    [--host ADDRESS] [--port N] [--decks DIR]
warm     COMMANDER [--partner NAME] [--bracket N] [--theme T]
validate --bracket N [--commanders NAME [NAME ...]] [--limit N] [--sweep] [--calibrate]
```

| command | what it does |
|---|---|
| `themes` | prints the 12 playstyles and a menu of themes: the commander's own EDHREC themes with deck counts when you name one, otherwise 41 common themes |
| `suggest` | ranks commanders for the themes and playstyle you name (give at least one of `--theme`, `--playstyle`, `--fantasy`). Candidates come from EDHREC's theme pages, so it needs EDHREC |
| `build` | builds a 100-card list around a commander, with the evidence for each card, the role counts, the bracket check and the *fantasy cost* (below) |
| `upgrade` | ranked cut/add swaps for a deck from a file, standard input (`-`) or a precon, within a budget and a bracket |
| `check` | legality (100 cards, colors, duplicates, banned cards), the bracket rules, role counts against the bracket's range, and the mana curve |
| `stats` | every number about a list: score and bracket, interaction (answers to each kind of threat, removal power), mana (lands, ramp, draw, curve, colors, tapped and colorless lands), playstyle, win plan, salt, price and what you own. Groups and formulas: [Deck metrics and `stats`](#deck-metrics-and-stats). With `--version PLAYER/ID` it shows a saved version, each number beside its base deck's |
| `serve` | runs the local web server for the deck pages until Ctrl-C: saved decks, with every metric worked out again after each change. Prints its address, how to reach it from a phone, and that there is no login. See [The deck server](#the-deck-server) |
| `warm` | downloads what the other commands need for one commander, so they can run with `--offline` |
| `validate` | measures how closely builds match real decks (see [Validation](#validation)) |

The four flags every command takes, then the rest (help text as `--help` prints it):

| flag | commands | meaning |
|---|---|---|
| `--json` | all | print the result as JSON (`"schema": 1`), not a report |
| `--refresh` | all | download again instead of using cached data (for `serve`: the card index as it starts, and a deck's data when the deck is first opened, not on every tap) |
| `--offline` | all | never connect; use cached data only (see `warm`) |
| `--sources LIST` | all | card-evidence sources to use, comma-separated (choices `edhrec`, `archidekt`, `edhtop16`) |
| `DECKFILE` | upgrade, check, stats | a decklist file; `-` reads standard input |
| `--precon NAME` | upgrade, check, stats | use a preconstructed deck by name instead of a file |
| `--version PLAYER/ID` | stats | a saved version instead of a file or precon, e.g. `andy/squirrels-go-wide`. Its bracket, themes, playstyle and owned precons come from the version, so the flags that set those cannot be given beside it |
| `--host ADDRESS` | serve | the address to listen on (default `127.0.0.1`, this computer only); a Tailscale address makes it reachable from a phone |
| `--port N` | serve | the port to listen on (default 8341; 0 picks a free one) |
| `--decks DIR` | serve | the folder of saved decks (default `commander/decks/`, or `MTG_COMMANDER_DECKS`) |
| `--commander NAME` | upgrade, check, stats | the commander, when the list does not mark it (repeat for a partner) |
| `COMMANDER` | build, warm | the commander |
| `--partner NAME` | build, warm, themes | a second commander (Partner or Background); `themes` also needs `--commander` |
| `--commander NAME` | themes | list this commander's own themes |
| `--bracket N` | suggest, build, upgrade, check, stats, warm; required by validate | power level 1-5 (default 3): 1 Exhibition, 2 Core, 3 Upgraded, 4 Optimized, 5 cEDH |
| `--budget USD` | suggest, build, upgrade | build and upgrade: most to spend on cards you do not own; suggest: most to spend on the deck's core cards |
| `--max-swaps N` | upgrade | most swaps to suggest (default: no limit) |
| `--price-points LIST` | upgrade | dollar amounts, comma-separated, to show what the swaps buy on the way up to `--budget`, e.g. `25,50,100`; needs `--budget`. Default: the budget, half of it, a quarter, and so on (at most four, none under $10) |
| `--theme T` | suggest, build, upgrade, stats, warm | a theme to build around, e.g. tokens (repeat the flag or separate with commas); for `warm`, a theme to download |
| `--playstyle P` | suggest, build, upgrade, stats | how the deck plays, e.g. go-wide (see `themes`) |
| `--fantasy TEXT` | suggest, build, upgrade, stats | the deck you imagine, in your own words (Claude turns it into themes; needs a token) |
| `--fantasy-weight W` | build, upgrade, stats | 0 = pure power, 1 = theme above all (default 0.5) |
| `--keep-fun`, `--no-keep-fun` | suggest, build, upgrade, stats | penalize cards that are frustrating to play against (default on at Brackets 1-3) |
| `--include CARD` | build, upgrade | a card the deck must keep (repeatable) |
| `--exclude CARD` | build, upgrade | a card the deck must not play (repeatable) |
| `--owned FILE` | suggest, build, upgrade, stats | a decklist of cards you own; they cost $0 (repeatable) |
| `--owned-precon NAME` | suggest, build, upgrade, stats | a precon you own, e.g. "Squirreled Away" (repeatable) |
| `--allow-combos` | build, upgrade | allow two-card combos the bracket would block |
| `--out FILE` | build, upgrade | write the deck list here (Moxfield and Archidekt import it) |
| `-v`, `--verbose` | build, upgrade, stats | show the evidence for every card (for `upgrade`, for each cut as well; for `stats`, how each number was worked out and its cards) |
| `--colors WUBRG` | suggest | only commanders inside these colors |
| `--limit N` | suggest, validate | suggest: commanders to show (default 10); validate: real decks held out per commander (default 20) |
| `--commanders NAME [NAME ...]` | validate | commanders to test (default: the four most played in tournaments at Bracket 5, else six popular ones) |
| `--sweep` | validate | Bracket 5 only: also try a grid of tournament weights (`W_BRACKET[5]`, `K_RESID`) |
| `--calibrate` | validate | also re-measure the role targets and rewrite `commander/role_targets.json` |

| environment variable | meaning |
|---|---|
| `MTG_BRACKET` | the bracket used when `--bracket` is not given (otherwise 3) |
| `MTG_COMMANDER_SOURCES` | comma-separated card-evidence sources, the same choices as `--sources` |
| `MTG_OFFLINE=1` | the same as `--offline` on every run |
| `MTG_COMMANDER_DECKS` | the folder of saved decks (otherwise `commander/decks/` in the repo; see [Deck files](#deck-files)) |
| `CLAUDE_CODE_OAUTH_TOKEN` | the Claude token `--fantasy` needs; a gitignored `claude-token.txt` at the repo root works too, the same file the replay uses |
| `MTG_SERVE_DELAY`, `MTG_SERVE_CONFLICT`, `MTG_FAIL_HOSTS` | test switches for `serve`, all off by default (see [The deck server](#the-deck-server)) |

**Output.** Reports stay within 100 columns, so a phone terminal does not wrap a table mid-word. `--json` prints
only the result on stdout, `{"schema": 1, ...}`; `warnings` (a list of strings) and `sources` (each source with
`fetched`, `cache` and `age_days`) are on every command. Progress, notes and errors go to stderr. `--out FILE`
writes a `Commander` section and a `Deck` section, which Moxfield and Archidekt both import.

**Exit codes.** `0` success. `1` a mistake you can fix (unknown card or precon, bad flags), with close matches
printed ("did you mean ..."). `2` data the command cannot do without is unavailable (offline with nothing
cached, or the site is down). `130` stopped with Ctrl-C.

**Pasted lists.** `upgrade` and `check` read what players paste: `1 Sol Ring`, `1x Sol Ring` or `Sol Ring`; set and
collector suffixes (`(CMM) 400`); foil marks (`*F*`); Archidekt category tags (`[Ramp]`, `[Commander{top}]`);
`Commander`, `Deck`, `Sideboard` and `Maybeboard` headers; MTGO's `SB:` lines. The commander is the card under a
`Commander` header, marked `*CMDR*`, or named with `--commander`. Maybeboard, considering and token cards are
ignored.

### Module map

| file | what it does |
|---|---|
| `src/mtg-commander.py` | thin entry script, same shape as `src/mtg-draft.py`; calls `mtgcommander.cli.main()` |
| `mtg-commander.sh`, `mtg-commander.bat` | launchers that run it from the repo root |
| `src/mtgcommander/` | the package; the files below are in it unless a path is given |
| `cli.py` | argparse commands: turns arguments into calls and results into output; owns the exit codes |
| `config.py` | paths, how long each source's cache stays fresh, default bracket, default sources, the User-Agent |
| `net.py` | the one HTTP client: per-host pacing, retries with back-off, the file cache, `--offline` and `--refresh`; `download` streams a large file to disk (unzipped on the way, unless told not to); a count of the requests made (the deck server's progress) and the `MTG_FAIL_HOSTS` test switch |
| `carddb.py` | Scryfall's bulk card file boiled down to one record per card (with links to its pictures); forgiving name matching; cheapest prices, and `deck_prices`, the one way a deck's cards are priced |
| `decklist.py` | reads pasted lists, matches names to real cards, loads precons from MTGJSON, writes lists |
| `decks.py` | saved decks: base decks and each player's versions as JSON files, with an append-only change log, replay, undo and revisions (see [Deck files](#deck-files)) |
| `serve.py` | the local web server for the deck pages: the application programming interface (API) over `decks.py` and `metrics.py`, one session for each open deck, the safety checks and the test switches (see [The deck server](#the-deck-server)) |
| `web/` | the deck pages: `index.html`, `styles.css` and eight JavaScript modules, plain files the server hands out (see [The deck pages](#the-deck-pages)) |
| `providers/` | one module per data source, registered in `providers/__init__.py` (`SIGNAL_PROVIDERS`) |
| `providers/edhrec.py` | what builders chose, per commander, bracket and theme; themes, salt, average land count |
| `providers/archidekt.py` | bracket-tagged decklists: the second builder source |
| `providers/edhtop16.py` | cEDH tournament entries with decklists and results: the tournament source |
| `providers/spellbook.py` | Commander Spellbook combos (in a list, and one card away) with their bracket tags: its web service, and a local index of its daily file (`combos_for` tries the index first) |
| `providers/scryfall_tags.py` | Scryfall's community function tags as sets of cards |
| `roles.py` | what each card does (ramp, draw, ...) from those tags; finer facts about a card (`attributes`), among them which kinds of threat it answers (`THREATS`); the per-bracket targets, and the one reader of `commander/metric_targets.json` (`answer_bands`) |
| `brackets.py` | Wizards' bracket rules as data, the four checks, and the legality check |
| `fantasy.py` | the fantasy spec: the theme and playstyle menu, and the optional `claude -p` step for free text |
| `score.py` | card scores: gathers the evidence once, then plain arithmetic |
| `build.py` | the deck value, and `upgrade`, `build` and `suggest` on top of it |
| `metrics.py` | every metric of one deck in one item shape, the registry of metric groups, and removal power |
| `calibrate.py` | measures role targets, removal and wipe power, and the answers to each kind of threat, from real decks and writes `commander/role_targets.json` and `commander/metric_targets.json` |
| `validate.py` | `validate`: held-out checks of builds against real decks |
| `render.py` | the text reports and the JSON |
| `commander/` (repo root) | committed reference data (`brackets.json`, `role_targets.json`, `metric_targets.json`, `playstyles.json`); see [`commander/README.md`](./commander/README.md) |
| `tests/commander/` (repo root) | unit tests with small hand-made fixtures; no network |

A provider answers one call, `signals(commanders, bracket=None, theme=None)`, and returns records that carry a
sample size, a source and a fetch time. Adding another source later (a log of your own games, say) is one new
module plus one name in `SIGNAL_PROVIDERS`; `score.gather()` does not change.

### The `upgrade` call chain

```
$ ./mtg-commander.sh upgrade --precon "Squirreled Away" --budget 75 --theme tokens
 └─ src/mtg-commander.py                      entry script
     └─ cli.main() → run()                    argparse subcommands; net.configure(refresh, offline)
         ├─ carddb.load()                     Scryfall oracle_cards bulk file → compact index (7 days)
         ├─ decklist.precon(name)             MTGJSON DeckList.json → deck file (30 days)   [or decklist.load(path)]
         ├─ decklist.resolve(parsed, db)      canonical names; close matches for unknown ones
         ├─ fantasy.spec_from_args(args)      menu words (+ one `claude -p` call for --fantasy text)
         ├─ build.prepare(...)                gather, tag and score once
         │    ├─ score.gather(...)            asks every enabled provider:
         │    │    ├─ providers.edhrec        all-bracket page, bracket page, theme pages, commander_meta, salt list
         │    │    ├─ providers.archidekt     only when EDHREC has no page, or the bracket is thin
         │    │    ├─ providers.edhtop16      tournament entries, only when the bracket's weight is above 0
         │    │    └─ decklist.precons_for_commander   Brackets 2–3: the commander's newest precon, for the discount
         │    ├─ roles.tag(...)               providers.scryfall_tags (oracle_tags bulk) + text fallback for new cards
         │    ├─ score.card_scores(...)       base + resid + theme + salt
         │    └─ roles.targets(...)           role_targets.json + playstyle deltas + EDHREC's average land count
         ├─ build.upgrade(ctx, deck, db, ...)
         │    ├─ roles.attributes(deck + candidates)  which kinds of threat each card answers (None: the tags did not load)
         │    ├─ providers.spellbook.find_combos   combos in the deck, and combos one card away
         │    ├─ brackets.check / blocked_adds     Game Changers, mass land denial, extra turns, two-card combos
         │    ├─ forced swaps first; then roles.answer_bands sets the answers floors; then the best swap one at a
         │    │  time, under budget, bracket and floors; with a budget, step by step up the price points
         │    ├─ combo check of the finished list; a swap that completes a banned combo is undone
         │    └─ the price-point lines: the kept swaps replayed on the starting list, one line per point, each with
         │       its answers, the kinds it leaves thinner (`weakens`) and its change in value
         └─ render.text(result), or render.as_json(result) with --json
```

### How a card is scored

For commander C, bracket B and fantasy F, `score.py` gives each card a score that is the sum of four signed parts:

```
score(card) = base + resid + theme + salt

base  = (decks_at + K_BASE · p_all) / (of_at + K_BASE)                     what builders chose at this bracket
resid = W_BRACKET[B] · clamp(RESID_SCALE · gap · n / (n + K_RESID), ±RESID_CAP)   tournament win-rate gap
theme = clamp(fantasy_weight · THEME_SCALE · weighted_mean_pull, ±THEME_CAP)     how much the themes favor it
salt  = −SALT_GAMMA · (salt − floor) / (SALT_MAX − floor)                  only when keep-fun is on
```

- `decks_at` / `of_at`: decks at bracket B that play the card, over decks that could (EDHREC's `num_decks` and
  `potential_decks`). `p_all` is the same ratio over all brackets. Adding `K_BASE` pretend decks at the all-bracket
  rate keeps a bracket with a handful of decks from swinging a score. A card missing from a page that exists was
  played in fewer decks than the page's listing line (about 5%), so it is scored at that line (or at its
  all-bracket rate, if that is lower), not at zero.
- `gap`: game win rate with the card minus without it, from EDHTop16 entries (wins ÷ games). `n` is the entries on
  the thinner side, so a staple in 98% of decks, with a handful of decks without it, cannot produce a confident gap.
  Below Bracket 5 the term applies only to roles in `roles.CARRYOVER` (ramp, draw, removal, wipe, counter,
  protection, tutor). A finisher or a recursion spell is worth what its deck makes of it.
- `pull` per theme: `(decks_t + K_THEME · p_ref) / (of_t + K_THEME) − p_ref`, from the best page that exists: this
  commander's decks with the theme at this bracket (if it has at least `THIN` decks), else at any bracket, else the
  theme across all commanders (its synergy × `GLOBAL_SYNERGY_FACTOR`), else a flat `MATCHER_PULL` when the card's
  subtype, type or text fits the theme (`theme_matchers` in `playstyles.json`). A theme you name counts fully; a theme
  the playstyle leans toward counts `PLAYSTYLE_THEME_WEIGHT`.
- `salt`: EDHREC's list of its 100 saltiest cards; `floor` is the lowest salt on that list, so a card off the list
  costs nothing.

Four special cases:

- **Thin bracket.** Under `THIN` (50) decks at the bracket, the tool pools the neighboring brackets and, if that
  source is on, Archidekt decks, and warns with the counts: "Thin data: only N Bracket B ... decks on EDHREC (under
  50); widened with ...".
- **Precon discount (Brackets 2–3).** Many lists for a precon's commander stay close to the box, so a stock card's
  inclusion partly measures inertia. The tool estimates the share `s` of near-stock lists from the 10th percentile
  of the precon's nonland cards' base scores (`PRECON_PERCENTILE`, capped at `PRECON_S_MAX`) and rescales each
  precon card to `max(0, (base − s) / (1 − s))`. These cards are labeled `precon-adjusted`.
- **Bracket 5.** With at least `TOURN_MIN` (30) tournament entries, `base` is the play rate among those decks,
  shrunk toward the cEDH builders' rate the same way: `(entries_with_card + K_BASE · p_at) / (entries + K_BASE)`.
- **No deck-builder data at all** (both builder sources off, failed or without a page for the commander). A card
  scores by Scryfall's overall EDHREC rank, `POP_WEIGHT · (1 − ln(rank) / ln(POP_MAX_RANK))`, over the best
  `POP_POOL` cards inside the colors, and the report warns that the result is good-stuff staples, not what this
  commander's players run.

| constant | value | what it does |
|---|---|---|
| `K_BASE` | 200 | pretend decks at the all-bracket rate mixed into a bracket's inclusion rate (and into the Bracket 5 play rate) |
| `K_THEME` | 50 | the same, for a theme page measured against the rate it is compared with |
| `K_RESID` | 50 | shrinks the win-rate gap by `n / (n + 50)`: with 50 entries on the thinner side, half the gap counts |
| `RESID_SCALE` | 4.0 | win-rate gaps (±5 points) are small next to inclusion gaps, so the gap is scaled up before it is added |
| `RESID_CAP` | 0.2 | the scaled gap never moves a score by more than this, before the bracket weight |
| `W_BRACKET` | 1: 0.0, 2: 0.0, 3: 0.2, 4: 0.5, 5: 1.0 | how much of the tournament term counts at each bracket. Only Bracket 5 can be fitted to results; Brackets 3 and 4 are judgment calls |
| `THEME_SCALE` | 2.5 | a theme pull is a few points of inclusion; scaled up it can matter beside the base score. Judgment until validation fits it |
| `THEME_CAP` | 0.5 | the theme part never moves a score by more than this. Judgment until validation fits it |
| `SALT_GAMMA` | 0.15 | the largest salt penalty, for a salt-4 card |
| `SALT_MAX` | 4.0 | EDHREC's salt runs 0 to 4 |
| `THIN` | 50 | a bracket with fewer decks than this borrows from its neighbors |
| `TOURN_MIN` | 30 | tournament entries needed before play rates replace the builder rate at Bracket 5 |
| `PRECON_PERCENTILE`, `PRECON_S_MAX` | 0.10, 0.6 | how the near-stock share `s` is read off a precon, and its ceiling |
| `PLAYSTYLE_THEME_WEIGHT` | 0.5 | a playstyle's themes count half as much as a theme you named |
| `GLOBAL_SYNERGY_FACTOR`, `MATCHER_PULL` | 0.5, 0.1 | weaker theme evidence: the all-commanders theme page, and a card-text match |
| `POP_WEIGHT`, `POP_MAX_RANK`, `POP_POOL` | 0.3, 4000, 700 | the popularity fallback: the top card scores 0.3, ranks past 4,000 score 0, 700 candidates |

Only the Bracket 5 weights can be fitted to results: `validate --bracket 5 --sweep` tries a grid of `W_BRACKET[5]`
and `K_RESID` and shows the overlap for each. The rest are judgment calls, and the code comments say which.

### How a deck is valued and how swaps are chosen

All three commands ask the same question, "what is this deck worth?", and differ in what they may change. In
`build.py`:

```
value(deck) = Σ score(card) over nonbasic cards
            + Σ over roles R_role(mass_role)                  the role bonus
            + L(lands)                                        the land bonus
            − TOPEND_PENALTY · max(0, topend − max_topend)    too many cards of mana value 6+
```

Each role has a minimum, a target and a maximum for the bracket (`commander/role_targets.json`). The *i*-th card of a
role is worth `1.5 · ROLE_BETA` up to the minimum, `ROLE_BETA` up to the target, then fades linearly to 0 at the
maximum. So a second board wipe is worth less than the first, and a card that fills a short role beats an equally
popular one that does not. Lands are worth `LAND_BETA` each up to the land target, then fade the same way. A card
tagged for *m* roles counts `1 / √m` toward each (its role mass), so a card tagged for three jobs is not three full
cards. A swap's gain is `value(deck − cut + add) − value(deck)`, worked out from role mass rather than by
re-scoring the deck, because the search asks for it tens of thousands of times.

| constant | value | what it does |
|---|---|---|
| `ROLE_BETA` | 0.20 | value of a card that fills a role up to its target (1.5× below the minimum), in score units |
| `LAND_BETA` | 1.0 | value of each land up to the land target; high on purpose, so a land is not traded for a spell lightly |
| `TOPEND_PENALTY` | 0.10 | per nonland card of mana value 6+ above the bracket's limit |
| `MIN_GAIN` | 0.02 | a swap must beat this to be printed |
| `MAX_CANDIDATES`, `MAX_LAND_CANDIDATES` | 250, 80 | adds considered, best first (`build` also considers 80 nonbasic lands) |
| `BUILD_ITERATIONS` | 300 | cap on `build`'s swap search |
| `NONBASIC_MIN` | 0.10 | a nonbasic land needs at least this score to take a slot from a basic, in `build` and in `upgrade` |
| `MANA_FLOOR` | 8 | no swap leaves a color with fewer lands that make it than this (or than it had, if it had fewer) |
| `PRICE_POINTS_SHOWN`, `PRICE_POINT_MIN`, `PRICE_POINT_ROUND` | 4, $10, $5 | when `upgrade` picks the price points itself: at most four (the budget included), none under $10, each halved amount rounded half-up to a multiple of $5 |
| `COMBO_ROUNDS` | 3 | how often a banned combo found in the finished list is repaired |
| `LAND_BUDGET_SHARE` | 0.10 | the share of a `build` budget held back for nonbasic lands |

Both searches are local, not optimal: a swap that needs two cards to change at once is invisible to them.

- **`upgrade`** makes forced swaps first: anything that breaks the format (banned or not legal, outside the
  commander's colors, extra copies, a card you `--exclude`d) or the bracket (too many Game Changers, extra-turn cards or
  mass land denial; the weaker half of a banned combo). Each is replaced by the best legal add that fits the budget (a
  basic land if none does). Then it repeats the best affordable swap above `MIN_GAIN`. There is no limit on how many
  unless you set `--max-swaps`: it stops when nothing beats `MIN_GAIN` or the money is gone. It never cuts the
  commander or an `--include` card. The deck's own cards and anything you own cost $0; other adds are priced at
  Scryfall's cheapest printing. With a budget, the swaps are run again with a growing penalty per dollar and the run
  that ends with the most valuable deck is kept, so one pricey card does not eat the whole budget. When a budget
  allows no swap, the report lists the cheapest useful adds.
- **Price points.** With a budget, `upgrade` climbs in steps instead of searching once for the whole amount. The steps
  are the budget, half of it, a quarter, and so on (at most four, none under $10, each halved amount rounded to a
  multiple of $5): a $200 budget gives $25, $50, $100 and $200, and $75 gives $20, $40 and $75. `--price-points
  25,50,100` sets your own; an amount at or over the budget is dropped, and the budget is always the last step. Each
  step is the search above with its amount as the cap, starting from the list the step before left. Money already
  spent counts toward the cap, and a card bought in an earlier step is never cut later. So the first swaps are what a
  small budget would buy, and each bigger step only adds to them. The forced swaps come first and may spend up to the
  whole budget, even if that is more than the first step. `--max-swaps` counts across all the steps. After the combo
  check, each step is summed up from the swaps that were kept: the money spent, the deck's value, and how many swaps
  there are so far. The report prints one line per step and splits the swap list where a step begins; `--json` has
  `price_points[]`, and each swap says which step found it (`price_point`; none for a forced swap). With one step (the
  budget alone, or no budget) the report prints no price-point block, but a note on the single step goes under its
  `Answers:` line. Each entry of `price_points[]` also says what the step did to the deck's answers: `change` (its
  `value` less the result's `value_before`, to 2 decimals, so a page never subtracts), `answers` (`{threat id: cards
  that answer it}` for the list at that step, `null` without tags) and `weakens` (see below).
- **Answers in an upgrade.** The deck's value counts removal cards but not what each one can hit, so a long upgrade
  could trade away the last cards that answer enchantments or planeswalkers without the value noticing (Squirreled Away
  at Bracket 3 and $200, without the rule below, went from 14 answers to creatures to 9 and from 7 to planeswalkers to
  2). So `upgrade` reads the attribute tags of the deck and of every candidate (`roles.attributes`, one request) and
  gives each card the set of threats it answers (`roles.THREATS`: creatures, artifacts, enchantments, planeswalkers,
  lands, graveyards, spells). Once the forced swaps are done (a banned card, one outside the colors or one over a
  bracket's limit must go whatever it answers), no swap may leave a threat with fewer answers than the smaller of what
  the list has now and what a typical deck at the bracket holds: the band's `target`, the median of real decks
  (`commander/metric_targets.json`, through `roles.answer_bands`; for spells, 0 in colors without blue). A list with 7
  answers to enchantments and a typical count of 4 may trade down to 4 but not to 3; a list that starts with 2 keeps
  its 2, though it may swap one for another; and an answer to one threat does not pay for the loss of an answer to
  another. This is a higher bar than the Metrics tab's `short`, which is the band's `min`, the 25th percentile: a count
  can sit above `short` and still be held where it is. The check is `Plan.keeps_answers`, used in `best_swap` next to
  the land and basic-land rules, and the groups of interchangeable cuts also split by the threats a card answers, so a
  flexible answer is never judged as a creature-only one. A card counts once for each threat it answers and once
  however many copies the list holds, as `stats` counts. The combo repair (undoing a swap that completes a combo the
  bracket forbids) is not held to the floor: a bracket rule outranks it. Without the tags (offline with no tag cache,
  say) no floor applies and a warning says answers to each kind of threat were not checked; `build` makes a deck from
  nothing and keeps no floor. On the Squirreled Away example the list starts with 14, 9, 7 and 7 answers to creatures,
  artifacts, enchantments and planeswalkers against typical counts of 10, 4, 4 and 3, and ends at 10, 7, 6 and 3, with
  39 swaps and the same $144.33 as without the floor, for a deck score of 92.88 where the search without it reached
  92.90. The result also reports how far it went: `answers_before` and `answers_after` (`{threat id: count}`, `null`
  without tags) and, for each price point, `weakens`: the threats whose count at that point is under the starting
  list's count and at or under the bracket's typical count (the median), as `{"id", "label", "before", "after",
  "target"}` with `label` the short noun (`"enchantments"`) and `target` the typical count. An entry means the point
  has used up all of that threat's surplus over a typical deck (7 answers to enchantments down to 4, where a deck
  usually holds 4); a threat that fell but is still above the typical count (7 down to 5) is not listed, nor is one with
  no band in the file, and one a forced swap or the combo repair took under the typical count is listed too.
- **Basic lands in an upgrade.** A basic land scores 0, so any scored nonbasic land looks like an improvement over one,
  and a long upgrade could replace every basic. Three rules prevent that.
  1. A nonbasic land needs a score of at least `NONBASIC_MIN` to take a basic's slot, the rule `build` already used.
  2. The deck keeps the basics its land searchers need: as many as the cards in it can take, and at least as many as it
     has colors. Cultivate takes two and Evolving Wilds one; a search for a *basic* land counts, but a search for
     "a Forest card" does not, because it can fetch a dual land that has the type. Those basics are split among the
     colors the way `build` splits basics (one each, the rest by colored mana symbols), so the searchers can still
     find every color. A swap that would cut a basic below the total, or below its color's share, is skipped. A swap
     that cuts anything else is always allowed, even one that adds a searcher to a deck that is short of basics. As
     before, no swap leaves a color with fewer than `MANA_FLOOR` lands that make it.
  3. When cutting a basic ties with cutting another card, an unscored nonbasic land goes first, then the basic of
     the color with the most lands per colored mana symbol. A deck that needs more green loses Swamps before Forests.
- **`build`** fills the nonland slots greedily by marginal value (your `--include` cards first), swaps until nothing
  improves, adds nonbasic lands that score at least `NONBASIC_MIN` (leaving room for the basics its land searchers can
  take: a searching land counts its own search, and is skipped if it no longer fits), then splits basics by the
  colored mana symbols in the deck. It checks the finished list for banned combos and repairs it, up to
  `COMBO_ROUNDS` times.
- **Fantasy cost.** When you ask for a theme, `build` builds the deck a second time with the fantasy weight at 0 (pure
  power), values both under power-only scores, and reports the gap in points and as a percent, the strongest cards the
  theme left out, and the cards it pulled in.
- **`suggest`** starts from the 30 commanders (`SUGGEST_CANDIDATES`) with the most decks in your themes on EDHREC's
  theme pages, then ranks them by their share of decks with your themes (counts shrunk by `SHARE_SHRINK`, 100 decks),
  plus `PLAYSTYLE_WEIGHT` (0.5) × the share with the playstyle's themes, plus `BRACKET_DECKS_WEIGHT` (0.03) per digit
  of decks at the bracket, minus `SALT_WEIGHT` (0.05) per salt point above 1 when keep-fun is on. A commander with
  fewer than `MIN_THEME_DECKS` (20) decks in your themes is skipped. The top `--limit` then get the slower extras:
  the price of their core cards (those in at least `CORE_INCLUSION`, 40%, of its decks; dropped if over `--budget`),
  `OWNED_WEIGHT` (0.15) × the share of their top 60 nonland cards you own, and at Bracket 4 and up a tournament bonus
  of `TOURNAMENT_WEIGHT` (0.2) × (top-cut rate − `TOURNAMENT_BASELINE`, 0.2), counted from `TOURNAMENT_MIN` (30)
  entries and shown without a "too few to judge" note from `TOURNAMENT_CONFIDENT` (100).

### Roles, targets and calibration

Roles come from Scryfall's function tags (the community labels behind searches like `otag:ramp`), read from its
`oracle_tags` bulk file and expanded to child tags. `roles.py` lists the tag set for each of nine roles: `ramp`,
`draw`, `removal`, `wipe`, `counter`, `protection`, `recursion`, `tutor`, `finisher`. Lands get no role except
`ramp` (a land that makes extra mana: Scryfall tags it `ramp`, or it taps for two or more). A text-pattern fallback
runs only for cards released in the last 180 days that no volunteer has tagged yet, or for every card if the tag file
cannot be loaded. The tag sets were chosen by running candidates over 60 recent precons and lists of well-known cards
for each role: 148 of 153 well-known cards found (October 2026, recorded in `roles.py`). `top-end` counts nonland
cards of mana value 6 or more.

`commander/role_targets.json` holds `[min, target, max]` for each role and bracket, and the most `top-end` cards.
`roles.targets()` starts there and then:

- shifts each role by the playstyle's whole-number change from `commander/playstyles.json` (`control` adds 2 removal,
  2 counterspells and 1 wipe; `big-mana` adds 3 ramp and 1 land). These are judgment calls, not fitted;
- moves the land target to the rounded mean of the bracket's target and EDHREC's average land count for this
  commander, kept between the bracket's minimum and maximum;
- drops the counterspell minimum and target to 0 for a commander without blue.

To re-measure the targets from real decks (it needs the network the first time; everything it reads is cached):

```bash
cd src
python3 -m mtgcommander.calibrate                     # prints the proposed numbers; nothing is replaced
python3 -m mtgcommander.calibrate --write             # replaces commander/role_targets.json and commander/metric_targets.json
python3 -m mtgcommander.calibrate --sources edhtop16,archidekt   # measure Brackets 3 and 4 from Archidekt too
python3 -m mtgcommander.calibrate --offline --sources edhtop16   # the committed numbers again, from the cache alone
```

Percentiles over each bracket's decks give the numbers: minimum = 25th, target = median, maximum = 90th (lands:
10th, median, 90th; the `top-end` cap: 75th; counterspells are counted only over decks whose commander has blue).
What each bracket rests on is limited by what the sources' terms allow:

| bracket | how its numbers are made |
|---|---|
| 2 | the newest 60 MTGJSON precons, as a Bracket 2 proxy. Wizards no longer ties Core to precons, so these are typical out-of-the-box decks, not a sample of Bracket 2 decks |
| 5 | EDHTop16 top-cut decklists of the most played tournament commanders (the site invites use of its public application programming interface, or API) |
| 3, 4 | Archidekt decks tagged with that bracket, only when `archidekt` is among the sources; otherwise interpolated between 2 and 5 (a quarter and half of the way) and labeled *interpolated (judgment)* |
| 1 | Bracket 2 with one more land and no tutors, labeled *judgment* |

`validate --calibrate` runs the same calibration after the validation and rewrites the files (the role targets and
`metric_targets.json`), so the validation numbers describe the targets as they were committed. It does not touch the
score weights above.

### Deck metrics and `stats`

`stats` prints every number the tool can work out about one list. `metrics.py` works them all out, in one call, so the
command and the deck pages show the same numbers.

```
$ ./mtg-commander.sh stats --precon "Squirreled Away" --bracket 3 --theme tokens --playstyle aristocrats
 └─ cli.cmd_stats
     ├─ carddb.load, decklist.precon, fantasy.spec_from_args       as for upgrade
     ├─ build.prepare(...)                      the evidence, role tags, card scores and targets, once
     ├─ roles.attributes(names, db)             the attribute tags (a request of their own: the roles never wait on it)
     ├─ spellbook.combos_for(commanders, cards, identity=colors)    the local combo index, the API as the fallback
     ├─ carddb.deck_prices(names, db)           each card at its cheapest printing, as upgrade prices it
     ├─ metrics.compute(ctx, db, cards, ...)    build.deck_value, roles.counts and brackets.check once, then each
     │                                          group of metrics.GROUPS reads those facts
     └─ render.stats_report(result), or render.as_json(result) with --json
```

Every number is an **item**, in one shape:

```json
{"id": "removal_power", "label": "Removal power", "value": 5.95, "unit": null,
 "target": {"min": 3.4, "target": 4.2, "max": 6.8}, "status": "inside",
 "why": ["Tear Asunder 1.00 = instant 1.0 × any permanent 1.0 × exile 1.0 × MV 2 1.0", "..."],
 "cards": ["Tear Asunder", "..."], "base": 7.61, "change": -1.66}
```

| field | meaning |
|---|---|
| `value` | the number; `null` when it cannot be had (the tags, combos or card data it needs are missing). `why` then says what is missing, and nothing is guessed |
| `unit` | `"%"`, `"$"` or `null` |
| `target` | the bracket's usual range: `min`, `target`, `max`. Any part is `null` when the range has no such end ("at least 1", "at most 8"). `null` for a number with no range |
| `status` | `"short"` (below `min`), `"inside"` or `"over"` (above `max`); `null` without a value or a range |
| `why` | how the number was worked out, one line for each fact |
| `cards` | the cards behind the number |
| `base` | the same item's value in the base deck; present only when `compute` was given one, so a page can show *before → after* |
| `change` | how far `value` moved from `base`: `value` − `base`, rounded to 2 decimals, 0 when equal. Present only when both are numbers (an item with no value has none), so a page can show *−1.66 from 7.61* without subtracting |

The items sit in groups, a registry in `metrics.GROUPS` of `(id, label, applies, compute)`. A page draws any group from
the item shape, so a new metric is one more item in one function and no page changes. `metrics.compute(ctx, db, cards,
commanders=..., attrs=..., combos=..., owned=..., prices=..., base=..., changes=...)` returns `{"schema": 1, "headline":
{score, bracket, lands, removal_power, price}, "groups": [{id, label, items}]}`. It is plain arithmetic on what
`build.prepare` gathered, about 4 to 6 milliseconds for a 100-card list, so a page can run it after every tap. The
headline `price` is the cost to buy: what the cards you do not own would cost.

| group | what is in it |
|---|---|
| `power` | deck score (and its card-power and theme parts, from `build.deck_value`); the chosen bracket, inside or over its limits, and the lowest bracket those limits allow (a floor); Game Changers used and allowed; combos in the list and one card away; tutors |
| `interaction` | removal power and wipe power; answers to creatures (removal that hits creatures, and board wipes), artifacts, enchantments, planeswalkers, lands, graveyards and spells (each against the bracket's measured band, below: fewer than its 25th percentile is marked short); counterspells; protection; the share of those removal, wipe, counterspell and protection cards that are instants or have flash |
| `mana` | lands, ramp and card draw against the role targets; ramp split into rocks, creatures that make mana and land ramp; draw split into engines and one-shot draw; the curve (an item for each mana value, 0 to 7 or more) and the average mana value; for each of the commander's colors, the lands that make it against the colored mana symbols of the nonland cards; basic lands against what the land searchers can take; lands that always and that sometimes enter tapped; lands that make only colorless mana; cards costing 6 or more against the limit |
| `playstyle` | theme fit (the share of nonland cards whose score has a theme part above `score.SHOW_PULL`); one item for each of the 12 playstyles; the creature count; synergy with the commander (the mean EDHREC synergy of the nonland cards that have one) |
| `win` | finishers (the role count) and by kind (overrun, drain, extra combat, alternate win, theft); combos in the list that win; creatures that are hard to block and their total power |
| `table` | salt (the total over the list and the three saltiest cards); the bracket's limits (Game Changers, extra-turn cards, mass land denial, two-card combos); total price, cost to buy and the share of cards you own |
| `changes` | only with a base deck (`stats --version`, and the deck pages): the cards added and cut, with who, when and why from the change log, and the net cost |

**Removal power.** A removal card is worth `speed × reach × permanence × cost`, times 1.5 if it removes again and again.
A board wipe is worth the same, times 1.5 if it spares your own side (Scryfall's `sweeper-one-sided`). The weights are
judgment calls, and each card's `why` line shows its arithmetic:
`Assassin's Trophy 0.90 = instant 1.0 × any permanent 1.0 × destroy 0.9 × MV 2 1.0`.

| factor | weights |
|---|---|
| speed | instant or flash 1.0; an ability that works again and again 1.0 (it can be used at any time, but a planeswalker's loyalty ability works only on your turn, so it is 0.75); anything else 0.75 |
| reach | any permanent or any nonland permanent 1.0; creatures and planeswalkers 0.8; creatures only 0.7; one kind of permanent (artifacts, enchantments, lands) 0.6; removal with a condition (a toughness limit, "nonblack", damage) 0.6, whatever it could otherwise hit |
| permanence | exile 1.0; destroy 0.9; damage or -X/-X 0.8; bounce 0.5; a card with several takes the best |
| cost | mana value 2 or less 1.0; 3, 0.9; 4, 0.8; 5 or more 0.65 |

All of these read Scryfall function tags, so the tags a card carries decide its weights (`roles.ATTRIBUTE_TAGS` lists
them, and `roles.attributes()` loads them as a separate request from the role tags: if they cannot be had, the roles
still work and only the items that need them go without a value).

**The bands for removal and wipe power, and for answers to each threat,** are in `commander/metric_targets.json`,
measured the way the role targets are: `calibrate.py` weighs the removal cards and the board wipes of the same decks
(the 60 newest precons for Bracket 2, 248 EDHTop16 top-cut decks for Bracket 5), counts the cards that answer each
kind of threat, takes the 25th percentile, median and 90th percentile, and interpolates Brackets 3 and 4 and copies
Bracket 2 to Bracket 1 (both judgment, labeled in the file). The power sums round half up to a tenth. The answer
counts are whole cards, so they round half up to whole numbers, as the role targets do. Answers to spells are measured
over the decks whose commander has blue only (32 of the 60 precons, all 248 tournament decks, recorded as
`samples_blue`), and `roles.answer_bands`, the one place that file is read, drops that band's minimum and target to 0
for a commander without blue: the rule the counterspell role already follows. The power numbers were measured on
2026-10-11 and measured again, unchanged, on 2026-10-12 from the same cached samples, when the answer counts were
added. The files `--write` replaces are both `role_targets.json` and `metric_targets.json`; `--out` writes only the
role proposal and prints the power and answer numbers.

| bracket | removal power (min / target / max) | wipe power |
|---|---|---|
| 1, 2 | 3.7 / 4.6 / 7.6 | 0.9 / 1.1 / 2.3 |
| 3 | 3.4 / 4.2 / 6.8 | 0.7 / 0.8 / 1.9 |
| 4 | 3.0 / 3.8 / 6.0 | 0.5 / 0.6 / 1.6 |
| 5 | 2.3 / 3.0 / 4.3 | 0.0 / 0.0 / 0.8 |

What counts as an answer is one table, `roles.THREATS`: a card answers a kind of threat when it carries any of these
Scryfall function tags. A card counts once for each kind it answers (Maelstrom Pulse answers three) and once however
many copies a list names. The Metrics tab counts with it and `calibrate.py` measures with it.

| answers to | tags | bracket 1, 2 | bracket 3 | bracket 4 | bracket 5 |
|---|---|---|---|---|---|
| creatures | `removal-creature`, `sweeper` | 8 / 11 / 15 | 7 / 10 / 14 | 7 / 9 / 13 | 5 / 6 / 10 |
| artifacts | `removal-artifact` | 3 / 4 / 6 | 3 / 4 / 6 | 4 / 4 / 6 | 4 / 4 / 6 |
| enchantments | `removal-enchantment` | 3 / 4 / 7 | 3 / 4 / 7 | 4 / 4 / 7 | 4 / 4 / 6 |
| planeswalkers | `removal-planeswalker` | 2 / 3 / 8 | 2 / 3 / 8 | 3 / 4 / 7 | 3 / 4 / 6 |
| lands | `removal-land` | 0 / 1 / 2 | 0 / 1 / 2 | 0 / 1 / 2 | 0 / 1 / 2 |
| graveyards | `hate-graveyard` | 0 / 1 / 3 | 0 / 1 / 3 | 1 / 1 / 3 | 1 / 1 / 3 |
| spells (blue decks) | `counterspell` | 0 / 1 / 2 | 2 / 3 / 5 | 5 / 6 / 8 | 9 / 10 / 13 |

Each answers item on the Metrics tab uses the bracket's band: a count under the minimum (the 25th percentile) is
`short`, one over the maximum (the 90th) is `over`. `upgrade` reads the same bands but keeps a deck's answers down to
the target, the median (see
[How a deck is valued and how swaps are chosen](#how-a-deck-is-valued-and-how-swaps-are-chosen)). Before the bands were
measured the tab called a count short only at 0. If the file has no row for a threat the old rule (at least one) stands.

**The playstyle profile.** Each of the 12 playstyles in `commander/playstyles.json` gets an item: the share of the
deck's nonland cards that signal it (a free sacrifice outlet counts 1.5, any other signal 1). A card counts once, at the
best weight among the signals it matches. The table is `PLAYSTYLE_SIGNALS` at the top of `metrics.py`, and every line is
a judgment about which cards say "this deck plays that way":

| playstyle | counts | signals |
|---|---|---|
| `combat` | cards that are hard to block, extra combat phases and mass pumps | tags `evasion`, `extra-combat-phase`, `overrun` |
| `voltron` | Equipment and Aura support | tags `synergy-equipment`, `synergy-aura` |
| `go-wide` | cards that keep making tokens | tag `repeatable-token-generator` |
| `aristocrats` | sacrifice outlets (a free one counts 1.5) and death triggers | tags `sacrifice-outlet`, `free-sacrifice-outlet`, `death-trigger` |
| `spellslinger` | instants and sorceries | the card types |
| `control` | removal, board wipes and counterspells | the roles `removal`, `wipe`, `counter` |
| `combo` | tutors and cards that win on their own | the role `tutor`, tag `alternate-win-condition` |
| `big-mana` | ramp and cards that cost 6 or more | the role `ramp`, mana value 6 or more |
| `graveyard` | cards that fill the graveyard, count it or bring cards back | tags `graveyard-fuel`, `cards-in-graveyard-matter`, the role `recursion` |
| `politics` | group hug, voting and monarch cards | tags `group-hug`, `voting`, `monarch-matters` |
| `stax` | cards that tax or lock down what opponents can do | tags `tax`, `lockdown`, `hatebear` |
| `value` | card draw that keeps paying | tags `draw-engine`, `repeatable-impulsive-draw` |

**Combos from a local index.** Commander Spellbook's developer guide says to use its web service, its
application programming interface (API), for "a few HTTP calls per user interaction" and to read bulk data from the
file it publishes: `https://json.commanderspellbook.com/variants.json.gz`,
rebuilt daily (29 MB gzipped, 687 MB unzipped, 114,450 variants on 2026-10-11). `providers/spellbook.py` downloads it
once, reads it one variant at a time (`json` cannot stream, so the reader decodes a variant, forgets it and reads on;
memory stays near 100 MB), and saves a compact index of 9.7 MB (`data/cache/commander/spellbook/variants.json`, kept 7
days): the combo's id, its cards, templates and results, its bracket tag and colors. Building it takes a few seconds,
loading and indexing it about a quarter of a second, and finding a deck's combos then about 3 milliseconds.

- **Included** means the deck holds every card the combo uses (all the copies it needs), the commanders counted among
  the cards; **almost** means exactly one card is missing and the combo's colors fit inside the commanders' colors. A
  combo that needs a certain card to be the commander is offered only to a deck led by it.
- **Left out of the index:** combos with a card that is banned in Commander (1,525), combos with a card not yet
  released (1,547) and any variant that is not marked OK. None of them can be built.
- **Combos that need a template** (a class of card such as "Persist Creature"; 6,367 of them) are kept in the index but
  never offered. Whether a deck holds a card of that class is a Scryfall search the API runs for each deck, and it counts
  an unmet template as a missing piece. Without that search the local index would have to guess, so it leaves these out:
  it can miss a template combo the API would list, and it never lists one the API would not. On 7 real lists (two
  Squirreled Away lists, four other precons, a cEDH list) its combos were all in the API's answer, and the only ones
  the API had and the index lacked were template combos and combos with a banned card.
- **`combos_for`** tries the index and falls back to the API when the index cannot be had (the download failed, or
  `--offline` with nothing saved); the answer says which one gave it and why. `stats` calls it; `check`, `build` and
  `upgrade` still ask the API. `--offline` runs `stats` from the saved index, so `stats` can check combos for a list it
  has never seen, which the API's per-list answers cannot.

**What `stats` leaves out or does differently.**

- *Creature power.* The card index records power as Scryfall writes it, so a power that varies (`*`, `1+*`) is left
  out of the total for hard-to-block creatures, and the `why` line names those creatures.
- *Prices.* `stats`, `upgrade` and the deck server all price a card at Scryfall's cheapest printing (`carddb.deck_prices`),
  so the cost to buy of the list an upgrade made is what the upgrade spent. Squirreled Away upgraded with `--budget 200
  --theme tokens --playstyle aristocrats` (owning three other precons) spends $185.43, and `stats` of the resulting
  list, with the same owned precons, shows a cost to buy of $185.43; the card index's default-printing prices showed
  $201.95. When Scryfall cannot be asked (offline, or a failed search) a card keeps the card index's price and a warning
  says why. A price you pass in (`prices=`) replaces both.
- *Owned cards.* `--owned` and `--owned-precon` make cards cost $0. The cards of the list itself do not, unlike in
  `upgrade`, so the cost to buy is what the whole list would cost you.
- *`warm`* does not fetch the attribute tags or the combo file; the first online `stats` run saves both (tags for 30
  days, the combo index for 7).

### Bracket rules

`commander/brackets.json` stores Wizards' rules as data, with the source URLs and the date each was read, so a rule
change is a data edit. The tool checks the four limits a program can count; everything else is intent, which
Wizards says matters most.

| bracket | Game Changers | mass land denial | extra turns | two-card combos |
|---|---|---|---|---|
| 1 Exhibition | none | not allowed | none | none |
| 2 Core | none | not allowed | not chained | none |
| 3 Upgraded | up to 3 | not allowed | not chained | none before turn 6 |
| 4 Optimized | any | allowed | any | any |
| 5 cEDH | any | allowed | any | any |

Game Changers come from Scryfall's `game_changer` flag on each card; the commander counts toward the limit.
Where Wizards' wording needs a decision from a program, the tool makes one and says so in its messages:

- **Chaining extra turns (Brackets 2 and 3).** Wizards says extra-turn cards "are not intended to be chained in
  succession or looped". The tool reads that as at most one extra-turn card, so a second one counts as chaining. That
  reading is its own judgment, not a Wizards rule, and its messages say so. (23 named cards plus two text patterns.)
- **Two-card combos.** Commander Spellbook tags every combo with the kind of deck it belongs in. The tool maps the tags
  to the lowest bracket they fit: `R` Ruthless 4, `S` Spicy 4, `P` Powerful 3, `O` Oddball 3, `C` Core 2,
  `E` Exhibition 1, `B` Not Legal 5. At Bracket 3 ("before turn 6") the tool cannot tell early from late, so it
  blocks every two-card combo Spellbook rates above Bracket 3. At Brackets 1 and 2 it blocks every two-card infinite
  combo whatever its tag (Spellbook's tags do not cover that rule), and any other two-card combo rated above the
  bracket. A longer combo is never over a limit, because Wizards' limits name two-card combos; it is noted instead.
  `--allow-combos` lifts the check.
- **Blocked adds.** `upgrade` and `build` also use the combos that one more card would complete: they never add the
  missing half of a combo the bracket does not allow, and name it under "Blocked".
- **Mass land denial.** Wizards publishes no complete list, so the tool uses 27 named cards plus 8 text patterns
  (38 Commander-legal cards flagged on 2026-10-11, with `From the Ashes` excepted because it replaces the lands it
  destroys). A card found only by its text is labeled as such, with a note to check with your pod.
- **The estimated bracket.** `check` reports the lowest bracket whose countable limits the list meets. It is a floor:
  how a deck plays decides the real bracket.
- **Not checked:** tutors (Wizards removed the limits in October 2025) and anything about how the deck plays.

The bracket wording, the dates and the places where Wizards' articles disagree (and which one wins) are in
[`commander/README.md`](./commander/README.md).

### Data sources, caching and offline use

| source | gives | kind | cache lifetime (TTL) | host |
|---|---|---|---|---|
| EDHREC | per commander, bracket and theme: decks that play each card, synergy; theme lists; the salt list; average land count | builder choice | 7 days | `json.edhrec.com` |
| Archidekt | decklists tagged with a bracket | builder choice | 7 days for a search, 30 for a deck | `archidekt.com` |
| EDHTop16 | cEDH tournament entries: decklists with wins, losses, draws, standing | tournament result | 1 day | `edhtop16.com` |
| Commander Spellbook | combos in a list and combos one card away, each with a bracket tag: from the API for `check`, `build` and `upgrade` (per list), and from the daily combo file, boiled down to a local index, for `stats` | rules check | API answers 7 days; the combo index 7 days | `backend.commanderspellbook.com`, `json.commanderspellbook.com` |
| Scryfall | card data, function tags (the role tags and the attribute tags, saved in one file), cheapest printing | rules, roles, prices | card index 7 days, tags 30, prices 7 | `api.scryfall.com`, `data.scryfall.io` |
| MTGJSON | precon decklists | input | 30 days (the list of precons: 7) | `mtgjson.com` |

TTL, short for time to live, is how long a cached download counts as fresh. The values live in `config.py`.

**Cache.** Every download is a JSON file under `data/cache/commander/<source>/` (gitignored, like the 17Lands
cache), written atomically. A page that does not exist (HTTP 404, or EDHREC's 403) is cached too, so it is not
asked for again until its TTL passes. Reports mark each source with its fetch date and `(stale)` when an expired
copy was served; `--json` carries `fetched`, `cache` (`fresh`, `network` or `stale`) and `age_days`.

**Pacing and retries.** `net.py` waits between requests to one host: 1 second for EDHREC, Archidekt, EDHTop16 and
Commander Spellbook, 0.5 seconds for Scryfall's API and MTGJSON, none for Scryfall's bulk-file host. It retries 429
and 5xx answers and network errors up to four times, waiting 1, 2, 4 and 8 seconds (or the server's `Retry-After`, up
to 60). When the network fails and an old copy exists, it serves the copy and says how old it is. Requests carry the
User-Agent `mtg-draft-commander/0.1 (+https://github.com/albertngo1/mtg-draft)`.

**`warm COMMANDER`** downloads ahead of time what the other commands will ask for: the card index; EDHREC's
all-bracket and bracket pages, the pages for each `--theme`, the salt list, and neighboring brackets when the bracket
is thin; Archidekt decks when they are used; EDHTop16 results at Bracket 3 and up; the commander's precons from
MTGJSON; the function tags (the role tags); and the cheapest prices of about 500 likely cards. It does not fetch
Commander Spellbook combos: those answers are cached per exact card list, so an `--offline` `check`, `build` or
`upgrade` can check combos only for lists it has checked online before (the list you give it, and the list after the
swaps). For any other list it prints "Combos were not checked", and the combo limit is not verified. `stats` is the
exception once it has run online one time: it saves the combo index and the attribute tags, and then works for any list
with `--offline`.

**`--offline`** never connects. It uses whatever is cached, even expired, and says so. A source with nothing
cached is skipped with a warning that names it; if the card index (or a precon list) is missing, the command stops
with exit code 2. **`--refresh`** downloads again instead of using the cache (and rebuilds the card index, a
25 MB download); if the download fails it still falls back to the old copy.

**`--sources`.** Three sources feed the scores: `edhrec`, `archidekt` and `edhtop16`. Choose them for one run with
`--sources edhrec,edhtop16`, or for every run with the `MTG_COMMANDER_SOURCES` environment variable (a
comma-separated list). Scryfall, MTGJSON and Commander Spellbook are not part of this list; they are always used.
EDHREC is the main builder source, Archidekt stands in when EDHREC has no page or a thin bracket, and EDHTop16
supplies the tournament term (Brackets 3 and up). With neither deck-builder source (`edhrec`, `archidekt`) on, scores
fall back to Scryfall's overall popularity rank, `suggest` cannot run (it needs EDHREC's theme pages), and `themes`
shows the common themes. The terms of two of these sources restrict scripted access, so which of them are on by
default is a separate decision; see [Terms of use](#terms-of-use).

### Deck files

`decks.py` keeps decks between runs. A **base deck** is where a deck starts, a precon or a pasted list. It is written
once and never changes. A **version** is one player's copy of a base deck plus every change that player made to it:
cards added, cut or swapped, and the undoing of any of those. Each is one small JSON file in the repo, so players share
decks through git, and `decks.py` is the only code that reads or writes them.

```
commander/decks/                  (the MTG_COMMANDER_DECKS environment variable names another folder)
  bases/<base-id>.json            one base deck
  <player>/<version-id>.json      one version, in its player's own folder
```

A player is a folder name, and an id is a file name. Both use lowercase letters, digits and hyphens, so `Squirrels go
wide` becomes `squirrels-go-wide`; `bases` cannot be a player because it is the folder of base decks. Each player
has a folder of their own, so two players never edit the same file.

**The change log is the truth.** A version stores its changes, not its card list. The list is the base deck's cards
with the changes replayed in order, so the log and the list cannot disagree, and "cards added" and "cards cut" are
only the difference between that list and the base deck's. The log is **append-only**: an undo deletes nothing, it adds
an entry that points at an older change, and a group of swaps (a whole price point from `upgrade`, say) is one entry,
so one undo reverses all of it. Two things follow. Nothing about how a deck reached its present state is ever lost,
and a git diff of a deck file reads as the new changes at its end, plus the new revision and update time.

```json
{"n": 1, "at": "2026-10-11T20:05:00Z", "op": "swap", "cut": "Swamp", "cut_id": "...", "add": "Cultivate",
 "add_id": "...", "source": "suggested"}
```

`n` is the change's number, `op` is `add`, `cut`, `swap`, `group` or `undo`, and `source` says whether the player
chose it (`manual`) or the tool suggested it (`suggested`). A file holds card names and changes, never a score, a price
or anything else a data source supplied; those are looked up again each time. Each name sits beside the card's Scryfall
`oracle_id`, the id that every printing of a card shares and that survives a rename (a base deck keeps a map of them
under `ids`), so a card Scryfall later renames still replays. The list is read by looking up each name, then its id,
and a change that cannot apply (a file edited by hand or merged badly) is skipped with a warning, so a damaged file
still opens. A file git left merge-conflict markers in cannot be read at all; opening it names the file, and a listing
skips it and names it in `decks.WARNINGS`.

**Rules for a change.** A change is checked in this order, and the first rule that applies decides:

| step | rule | answer |
|---|---|---|
| 1 | the `revision` the caller sends is the file's current one | otherwise `Conflict` (409), carrying the current revision; nothing else is checked |
| 2 | the card is known (the message offers up to three close names), legal in Commander, inside the commanders' colors; a card to cut is in the list; a swap's new card is not already in the list (basic lands and cards that allow any number excepted) | otherwise `Invalid` (422), with a message a player can read |
| 3 | nothing to do: adding a one-copy card the list already has, adding the commander, swapping a card for itself, undoing a change that is already undone | `changed: false`; nothing is written and the revision stays |
| 4 | a group: its items are checked in order against the list as the earlier items left it | one broken rule rejects the whole group and names the item |
| 5 | an undo: the change exists, is not itself an undo, and the list replayed without it is still valid | otherwise `Invalid`, naming the later change that depends on it ("change 9 cut Mind Stone") |

Malformed input (an unknown `op`, a missing field, a bad id) is a `DeckError` (400) and a missing player, base deck,
version or precon is a `NotFound` (404). Each error class carries the HTTP `status` a web server would answer with.
Nothing limits a deck's size; a list of 101 cards is for the caller to point out, not an error here.

**Revisions, locks and the one-server assumption.** `revision` counts a version's saved writes: the first change makes
it 1. Every change is made on a revision, so a phone and a desktop tab (or two players) cannot overwrite each other;
changing the name or settings with `update` counts too. A lock for each file, inside the process, covers the whole read,
check and write, so two requests at once cannot both pass the revision check. There is no lock between processes: the
usual tool, `fcntl`, does not exist on Windows, which the `.bat` launchers support. **One server process per repo is
assumed.** Every write goes to a temporary file in the same folder and is then renamed over the old file, so a reader
never sees half a file, and a write that fails leaves the old file as it was.

**On disk.** A file is JSON indented by one space, with non-ASCII characters written as they are, a newline at the
end, and each card of a base deck and each change of a version on a single line, so a git diff shows one line per
card or change. The keys come in a fixed order, listed at the top of `decks.py`.

### The deck server

`serve.py` is the local web server behind the deck pages (the pages are plain files in `src/mtgcommander/web/`, which the
server also hands out; see [The deck pages](#the-deck-pages)). It keeps no deck of its own: the files are `decks.py`'s. Its job is to take a request, call
`decks.py` and `metrics.py`, and answer with the whole deck and every metric worked out again, so a page redraws from one
answer and no formula exists twice. These answers are the server's application programming interface (API). It uses only
the standard library: `http.server`, one thread for each request.

```
$ ./mtg-commander.sh serve
 └─ cli.cmd_serve                       loads the card index, makes App and the server, prints the address
     └─ Handler._serve                  one request: the Host and Origin checks; for a write, the type and size of the body
         └─ App.dispatch → route_*      the decks.py calls: version, apply, update, new_version, new_base ...
             └─ DeckSession             one for each open version: a lock, and the Workspace its numbers come from
                 └─ Workspace.look      score any new card; tag and price it; ask for the list's combos
                     └─ metrics.compute the base deck's metrics are `base=`, the change log is `changes=`
```

**Addresses.** Every answer is JSON with `"schema": 1`.

| address | does |
|---|---|
| `GET /api/status` | when each data source was read; the server's settings (host, port, offline, decks folder); the deck files git does not have yet (`git status --porcelain`, read only, 2 seconds at most, with a note saying why when git cannot tell) |
| `GET /api/players` | the players: the folders under the decks folder |
| `GET /api/menu` | the playstyles and common themes a version's settings choose from |
| `GET /api/decks?player=NAME` | that player's versions, newest first: id, name, base deck, its settings (bracket, budget, themes, playstyle), commanders and picture, revision, cards swapped, what the changes cost, and the headline numbers (from the open deck, else from a preparation tried offline, else `null`) |
| `POST /api/decks` | `{"player", "name", "base", "settings"?}` makes a version; 201 |
| `GET /api/decks/PLAYER/ID` | the version: `version` (with its change log, each change marked `undone` or not), `base`, `spec` (the settings as the engine reads them), `commanders`, `cards`, `card_count`, `diff`, `cut_cards`, `metrics` (every item beside the base deck's value and how far it moved), `warnings` and `sources`; or 202 |
| `POST /api/decks/PLAYER/ID/changes` | `{"revision", "op": ...}` as in [Deck files](#deck-files), with `"source"`; answers like the GET plus `"result": {"changed", "message"}` |
| `PATCH /api/decks/PLAYER/ID` | `{"revision", "name"?, "settings"?}`; answers like the GET |
| `POST /api/decks/PLAYER/ID/suggest` | `{"budget"?, "price_points"?}`: `upgrade` on the list as it is now, with the settings' budget unless one is given. The result of `upgrade`, plus `revision` and `cards` (a card object for each card it names). It keeps nothing: ask again after every change |
| `GET /api/bases`, `POST /api/bases` | the base decks, each with its commanders, their picture and colors (`ci`, as WUBRG letters) and card count; make one from `{"name"?, "precon", "player"}` or `{"name", "list", "commander"?, "player"}`; 201 |
| `GET /api/precons?q=TEXT` | precon names that hold every word, at most 20 |
| `GET /api/cards?q=TEXT&deck=PLAYER/ID` | cards to add, at most 30. With no text, the best-scored cards not in the deck. With text, the Commander-legal cards whose name holds every word: the exact name first, then the commander's colors, then by score (a card with none, by EDHREC rank). Each is a card object plus `score`, `evidence`, `gain` (the deck's value change if it were added as one more card) and `flag`: `null`, or `{"kind": "illegal" \| "colors" \| "in_deck" \| "bracket", "reason"}` for a card that cannot be added |
| `GET /api/cards/NAME?deck=PLAYER/ID` | the card's sheet: facts and rules text, copies in the deck, roles, attribute tags, `answers` (the kinds of threat it answers, by the tags the deck's "answers to ..." numbers count), score with its evidence and parts, salt, Game Changer, the combos it is in and would complete, the removal breakdown, `if_cut` (the deck score change and only the metric items that move) and `replacements` (the five best cards to put in its place, by the deck's value after the swap) |

A **card object** has `name`, `front`, `image`, `image_back`, `scryfall_uri`, `type`, `cost`, `cmc`, `ci` (color identity
letters), `price` (cheapest printing; `null` when nothing prices it) and `owned` (in the base deck or a precon the
player owns, or a basic land). In a deck's list it also has `count`, `section` (Creatures, Lands ...), `new` (added since
the base deck), `score`, `roles` and `gc` (Game Changer).

**Preparing a deck, and the 202 answer.** A deck's numbers need the engine's data: the commander's EDHREC pages, role
tags, scores, combos and prices. The first time a deck is opened, and whenever its bracket, themes, playstyle,
keep-fun choice or owned precons change, the server prepares that data on a background thread, one deck at a time
(the sites are asked politely, and the request count then belongs to one deck). Until it is ready the deck answers
`202 {"status": "preparing", "progress": {"requests", "message"}, "revision"}`, where `requests` is the number of web
requests made since that deck's preparation began, and the message says what it is doing ("Fetching EDHREC data for
Hazel (first time only)"). The page asks again until it gets 200. A deck that is ready within 0.3 seconds is simply
sent: with a warm cache a first open takes under a second. A route that needs a ready deck (a change, a search, a card
sheet, suggestions) does nothing and answers 202 the same way when it finds none, so a page opens the deck first.
`PATCH` is the exception: it saves the new name or settings first, so its 202 means "saved, the numbers are on their
way". A preparation that fails answers 500 once, with the error text, and the next request tries again. The deck list
never waits on the network: for a deck nobody has opened it tries a preparation offline, and shows no headline numbers
when the cache does not have what that needs.

**What a change does.** The route holds the deck's lock, then calls `decks.apply`, so the revision check, the card
rules and the write are one step: of two devices that send the same revision, one succeeds and the other gets 409 with
the revision to reload at. The answer is built from the file as `decks.current` replays it. A card the engine has not
scored (one no EDHREC list mentions) is scored by preparing again with it included, offline (about 0.13 seconds), so
a tap never waits on a download; the card's price is looked up at its cheapest printing. If that scoring fails the
change is still saved and a warning says the card is unscored. A deck file changed outside the server (`git pull`) is
read afresh on every request, so there is nothing to restart.

**Errors.** `{"schema": 1, "error": {"code", "message", "details"}}`; the status comes from the `decks.py` error classes.

| status | `code` | when | `details` |
|---|---|---|---|
| 400 | `bad_request` | a bad id, a missing field, an unknown op, a body that is not a JSON object | `null` |
| 403 | `forbidden` | the Host or Origin check failed | `null` |
| 404 | `not_found` | no such player, deck, base deck, precon or card | `{"suggestions": [close names]}` |
| 405, 411, 413, 415 | `method_not_allowed`, `length_required`, `too_large`, `unsupported_media_type` | the method, the body's length (none, chunked, over 1 MB) or its type (not `application/json`) | `null` |
| 409 | `conflict` | a stale revision, or an id already taken | `{"revision": the deck's revision now}` (`null` for an id) |
| 422 | `invalid` | a deck rule, a setting that is wrong, a pasted list with lines that cannot be read | the problems, e.g. `[{"line": 3, "text": ..., "suggestions": [...]}]` |
| 500 | `server_error` | anything else: the exception's own text, or the file that cannot be read | `{"type": the exception's class}` |
| 500 | `data_unavailable` | a data source is down and nothing is cached | `{"source": ...}` |

**Safety.** There is no login, so the server checks where a request comes from instead.

- A write (`POST`, `PATCH`) must send `Content-Type: application/json`. A browser then asks permission before sending
  it from another site, and the server never gives it (an `OPTIONS` request is refused, with no permission headers).
- A request with an `Origin` header must have the same host and port as its `Host` header: the page that was loaded from
  this server. A page from another site is refused (403).
- The `Host` header must name this server, which stops a rebinding attack (a page on another site whose domain name has
  been pointed at your computer, so the browser treats the server as part of that site). It accepts the address the
  server listens on; `localhost` and `127.0.0.1` when that is this computer; any IP address when it listens on every
  interface (`--host 0.0.0.0`), since rebinding needs a domain name; and names ending in `.ts.net`, Tailscale's own,
  which is what `tailscale serve` passes on.
- Ids are checked by `decks.py` before they reach a file path. A page file's path cannot leave `src/mtgcommander/web/`
  (no `..`, backslash or drive letter, and a symbolic link out of the folder is not followed). A request body is at
  most 1 MB.
- Every answer carries `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`.

None of this is a password: anyone who can reach the address can change every deck. Listen on this computer only, or on a
Tailscale address, unless the network is trusted.

**Test switches** (environment variables, off by default) let a test make the server slow, refuse or fail. The browser
checks for the pages use them.

| variable | does |
|---|---|
| `MTG_SERVE_DELAY=SECONDS` | waits that long after doing the work of each API request, then answers: a change that took longer than the page's patience has still been saved |
| `MTG_SERVE_CONFLICT=N` | the next N change requests answer 409 with the deck's real revision and change nothing |
| `MTG_FAIL_HOSTS=HOST,...` | `net.request` and `net.download` fail at once for these hosts, as if the site were down. With `--refresh` the cache is not simply served, so the page shows its stale-data banner |

**Running it.** One server per repo: deck files are written whole and replaced atomically, but nothing locks them
between programs. `--refresh` downloads the card index again as the server starts, and a deck's data again when the deck is first opened (and only then). `--offline`
never connects. The tests (`tests/commander/test_serve.py`) start a real server on a free port with fakes for the engine's
network, git and the card index's data, and cover every route, each error, the safety checks and the switches.

### The deck pages

The pages are plain files in `src/mtgcommander/web/`, handed out by the server. There is no build step and there are no
packages: each file is a JavaScript module (`<script type="module" src="app.js">`) that a browser loads straight from the
server. Nothing is fetched from another site except each card's picture, whose Scryfall link is part of the server's
answer (the page's `Content-Security-Policy` allows pictures from any https address and everything else only from the
server itself).

| file | job |
|---|---|
| `index.html` | the shell: the stylesheet, the script, a `<main>`, and the layers for sheets and messages |
| `styles.css` | Albert's color palette (the `:root` block, copied from `card-reference/site/site.css` and kept equal by a test) and the components. Phone first: one column, the numbers pinned above the tabs, touch targets of at least 44 px. From 1024 px wide the card grid has the metrics beside it |
| `api.js` | the one `call(method, path, body)`, with a 10 second limit and one error type whose `kind` is `unreachable`, `timeout`, `conflict`, `invalid`, `not_found` or `server`. A 202 (the deck is still being prepared) is an answer, not an error; `callReady` asks again every second until it gets the deck |
| `app.js` | the address (hash) router, the state, the queue that saves one change at a time for each deck, and the redraw from the state |
| `ui.js` | the pieces every screen shares, one copy each: card tile, chip, stat, toast, banner, sheet and button (and the few helpers they need) |
| `decks.js` | Decks, New version and New base deck |
| `deck.js` | the Deck screen: the header, the numbers, and the Cards, Metrics, Changes and Suggestions tabs |
| `card.js` | the card sheet: picture (with a flip for a two-faced card), rules text, why it is in the deck, removal power, what cutting it would change, replacements, Cut and Swap |
| `add.js` | the Add a card sheet: search, then "what does it replace?" |
| `metrics.js` | draws any metric group from the one item shape (label, value with unit, band, status, before and after, and `why` behind a tap) |

**Addresses.** They follow the `#`, so a reload keeps the place, and names are encoded with `encodeURIComponent` (card
names hold spaces, commas, apostrophes and `//`): `#/` (Decks), `#/new` and `#/new?base=ID`, `#/new-base`,
`#/d/PLAYER/ID` (the Cards tab) and the same with `/metrics`, `/changes` or `/suggestions`, `#/d/PLAYER/ID/card/NAME`
(a card's sheet) and `#/d/PLAYER/ID/add` (`?cut=NAME` to swap a card, `?card=NAME` to add one). A sheet is an address of its
own, so Back closes it. The only thing kept on the device is the chosen player, in `localStorage`, and every read and write
is guarded: the pages work without it.

**The rule: the pages never work out a number.** Every number on screen came in the server's answer, so each formula
exists once, in Python, where the tests are. The pages sort, fold and format: how many tiles are in a section or behind a
filter chip, how long a bar is next to the longest in its picture, a price as dollars. They subtract nothing: how far a
number moved from the base deck's value is the item's `change`, which the server works out, and the pages print it with
its sign (`+3.4` beside the score, `36 −2 from 38` in a row of the Metrics tab). A metric the pages have never heard of
is drawn as a row, so a new metric needs no page code.

**One change at a time for each deck.** A tap puts a request in `app.js`'s queue and dims its card; the numbers fade, and
nothing moves until the answer comes. Then everything is redrawn from the answer. If a request fails, the ones behind it are
not sent, and the message offers to send them all again.

| state | what the page does |
|---|---|
| success | redraws from the answer, and a toast names the change with an Undo (`{"op": "undo", "of": n}`) |
| `result.changed` is false | shows the server's message and changes nothing |
| 409 | reloads the deck, says "This deck changed on another device, so it was reloaded", and offers the change again |
| 422 (and 400) | shows the reason and puts the card back |
| unreachable, or no answer in 10 seconds | a banner naming `mtg-commander serve` (and Tailscale, when the page was opened from another device) with Retry. After a timeout Retry first reads the deck: if its revision has moved on, the change was saved after all and is not sent twice |
| 500 | the server's own text |
| 202 | the first open of a commander: shows the server's message and how many web requests it has made, and asks every second until the deck is ready |
| not 100 cards | a banner ("101 cards. Cut one to get back to 100.") |
| `bracket_ok` is false | a banner naming the cards, from the `bracket` item's `why`, with Undo |
| a source did not answer | a banner naming it and the date of the data the numbers use |

Suggestions are asked for again after every change, and a price point from before a change is never applied: its Apply
buttons are off until the new answer arrives. Each price point shows its change in score beside the two scores (the
server's `change`, to one decimal), and one that has brought the deck's answers to some kind of threat down from the
starting count to what a typical deck holds, or under it, has a "Weakens interaction" note under it, one banner naming
each kind with its count before and after and the typical count (`enchantments 7 → 4 (typical 4)`), from the server's
`weakens`: the page subtracts and compares nothing.

**Checking them.** `tests/commander/test_web.py` checks what Python can: the palette matches Albert's, every file the page
names and every `import` exists and exports what is imported, nothing is loaded from another site, no server text is put
into markup (`innerHTML` is never used), and the real folder is served with the right types. When Node is installed it
also syntax checks each module. What the pages do is checked in a browser against the real server, at 390 and 1280 px, with
the test switches (`MTG_SERVE_DELAY` for a timeout, `MTG_SERVE_CONFLICT` for a 409, `MTG_FAIL_HOSTS` with `--refresh` for
stale data, and a stopped server for unreachable).

### Edge cases

| case | what happens |
|---|---|
| Unknown card name | `build`, `upgrade` and `stats` stop before scoring with close matches ("did you mean ..."); `check` lists it as a problem and checks the rest. Unknown names inside a precon list are skipped with a warning |
| Illegal list (wrong colors, duplicates, banned cards, not 100 cards) | `check` reports every problem and still checks the rest. `upgrade` cuts illegal cards first and says why |
| Little data (under 50 decks at the bracket) | pools the neighboring brackets and, if on, Archidekt decks; prints "Thin data" with the counts |
| A source is down or `--offline` | uses the cache and says how old it is; with no cache, skips that signal and names it in the warnings; stops (exit 2) only if the card index or a precon list is missing |
| Rate limited (HTTP 429) | waits and retries, then stops asking that source with a message pointing at `warm` |
| Budget too small | lists the cheapest useful adds; swaps from cards you own still appear, because they cost $0 |
| Deck above the target bracket | the forced cuts come first, marked as forced |
| Two commanders | `--partner NAME` (`build`, `warm`, `themes`) or `--commander` twice (`upgrade`, `check`). Colors combine; EDHREC's page for the pair is used; pairings checked are Partner, Partner with, Friends forever, Choose a Background with a Background, and a Doctor with a Doctor's companion |
| Cards allowed in any number (Relentless Rats, Hare Apparent) | exempt from the one-copy rule, as are basic lands |
| `--fantasy` without a Claude token | says why (a note on stderr, or in `warnings` with `--json`), reads no words from the text, and points to `themes`; `--theme` and `--playstyle` still work |
| Claude names a word not on the menu | dropped with a warning; Claude may choose at most 3 themes and one playstyle, and never a card |
| `stax` below Bracket 4 | falls back to `value` with a warning |
| `stats` without the attribute tags (offline, nothing saved) | the items that need them (removal and wipe power, answers, ramp and draw kinds, tapped lands, finishers by kind, most playstyles) have no value and say why; the role counts, the curve, colors, price and the rest still print |
| `stats` cannot get the combo file | falls back to the API with a warning; if that fails too, the combo items have no value and the combo limit is not verified |
| A deck is changed on two devices at once | one change is saved; the other gets 409 with the current revision, and the page reloads ([The deck server](#the-deck-server)) |
| A data source fails while a deck is open | the deck uses the cached copy and its `sources` entry says `stale`; a source with nothing cached is a warning, or a 500 `data_unavailable` if the deck cannot be prepared at all |

### Terms of use

What each source's own terms say about scripted access. This tool's requests are automated, so read these before you
use a source. Quotes are copied from the pages named, read on 2026-10-11.

- **EDHREC** ([terms](https://edhrec.com/terms), effective August 6, 2024) licenses access "solely for your own
  personal, noncommercial use", and its acceptable-use list says you agree not to "use software or automated agents
  or scripts to ... generate automated searches, requests, or queries to the Site". The pages this tool reads
  (`json.edhrec.com`) are the files EDHREC's own site loads, not a documented API.
- **Archidekt** ([terms](https://archidekt.com/terms), effective September 7, 2018) has the same two clauses, word
  for word.
- **EDHTop16** ([terms](https://edhtop16.com/terms), updated August 2, 2026): "We provide an API for developers and
  data enthusiasts." It also bars "excessive automated requests" and says its statistics "may not be reproduced or
  redistributed without permission", so the cache stays local and out of git. This tool uses only that API, one
  request a second, cached for a day. Its terms say "Applications using our API must not imply endorsement by
  EDHTop16": **this tool is not endorsed by EDHTop16.**
- **Commander Spellbook** ([guidelines for API consumers](https://spacecowmedia.github.io/commander-spellbook-backend/api.html))
  asks for "a few HTTP calls per user interaction", says "80 requests per minute should be a safe rate", asks
  users to name their service in the User-Agent (this tool sends `mtg-draft-commander/0.1`) and says "Please credit us
  and link back to commanderspellbook.com where applicable". The credit is under Data sources & credits below. Its
  API host's `robots.txt` says `Disallow: /`. The same guide says "Do not use the HTTP API to export the whole
  dataset" and publishes the whole dataset as one daily file ("Gzipped. Prefer this one.", "Fetch it on a schedule of
  your own and read it locally"). `stats` reads that file, once every 7 days, and keeps only a compact index of it.
- **Scryfall** ([API documentation](https://scryfall.com/docs/api)): "All HTTP requests to api.scryfall.com must
  include a User-Agent header and an Accept header" (this tool sends both), and the search endpoints are limited to
  2 requests a second (it waits 500 ms between requests to that host). It encourages caching "at least for 24
  hours" (the card index is kept 7 days) and says "You may not simply repackage, republish, or proxy Scryfall data",
  so the cache stays local and out of git.
- **MTGJSON** ([license](https://mtgjson.com/license/)) is MIT, which grants permission "to deal in the Software
  without restriction". Its `robots.txt` disallows `/api/v5/*.json`, the pattern of the documented download files
  (`DeckList.json`, `decks/<name>.json`) this tool reads, once each, and caches for 30 days.

Which sources a run uses is one setting: `--sources` for a run, `MTG_COMMANDER_SOURCES` for every run (a
comma-separated list of `edhrec`, `archidekt`, `edhtop16`). With neither deck-builder source (EDHREC, Archidekt)
among them, the scores fall back to Scryfall's overall popularity rank: good-stuff staples for the colors, not what
this commander's players run.

**Default: all three are on.** Below Bracket 5, EDHREC and Archidekt are the only evidence of what this
commander's players run, so the builder reads them unless told not to, although their terms bar scripted requests.
Requests to them go out one a second with the tool's User-Agent (`mtg-draft-commander/0.1`), and their answers are
cached (EDHREC pages and Archidekt searches for 7 days, Archidekt decks for 30), so repeating a run inside those
windows sends them nothing. To leave them out, set `MTG_COMMANDER_SOURCES=edhtop16` or pass `--sources edhtop16`.

### Validation

`validate --bracket N` asks whether the builder builds what experienced players build, and whether it keeps to the
rules. It is `sealed_algo.py --validate` for Commander: hold a real list out, build without it, and count how many of
the list's non-basic cards the build also plays. That number alone says little (most of a cEDH list is staples anyone
would guess), so every overlap sits beside a baseline that needs no model, the same number of most-played cards. The
baseline is hard to beat on overlap, since it is what most builders start from; the build gives a little of it up for
the budget, the bracket's limits and the role targets. The measured results are in AGENTS.md ("Commander deck
building"): 81% against 82% at Bracket 5, 48% against 51% at Bracket 3, every build within the bracket's limits.

- **Bracket 5** (needs `edhtop16`). For each commander, take its newest 150 EDHTop16 entries and hold out its top-cut
  decks one at a time, up to `--limit`. The build is handed the tournament results of every other entry, and reads
  EDHREC's cEDH page when EDHREC is a source. The baseline is the same number of cards most played by the other
  entries. Pilots reuse their lists, and EDHREC's cEDH page may hold the held-out list, so read the gap to the
  baseline, not the absolute number. With no `--commanders`, it uses the four most played in tournaments (at least 150
  entries in the year). `--sweep` repeats the builds over a grid of `W_BRACKET[5]` (0, 0.5, 1, 2) and `K_RESID` (25,
  50, 100), on the newest 8 held-out decks per commander; weight 0 is "EDHREC alone".
- **Brackets 1–4** (the overlap needs `archidekt`). One build per commander (default: six popular ones) from EDHREC,
  compared with up to `--limit` recent Archidekt lists tagged with that bracket. The builds never read Archidekt, so
  they are not marked on their own homework, but EDHREC cannot drop one held-out list (it is one of thousands), so
  these overlaps are somewhat optimistic, and the baseline (the same number of cards the sources list most often at
  the bracket) shares that optimism. The build's role counts are also checked against the middle half (25th to 75th
  percentile) of those lists. With `archidekt` off, only the rule check runs, and the report says so.
- **Any bracket:** the share of builds that follow the bracket's rules, with Commander Spellbook's combos.
- **Bracket 3:** an upgrade check. The newest 10 precons are upgraded within $50, and each should end nearer the
  bracket's role targets without overspending.

Overlap with real lists shows the tool builds like real players at that bracket. It does not show that its decks win,
and at Brackets 1–4 no public data could.

### Tests

```bash
python3 -m unittest discover -s tests -t . -v      # from the repo root
```

The tests are standard-library `unittest`, replay small hand-made fixtures in each source's shape
(`tests/commander/fixtures/`, never downloaded pages), touch no network, and run in a few seconds. The deck server's
tests start a real server on a free port and stop it, with its threads, when each test ends.

## Data sources & credits

- **[Scryfall](https://scryfall.com/)** — card names, mana costs, oracle text (queried at runtime;
  not redistributed). Please respect their [API guidelines](https://scryfall.com/docs/api). The Commander
  builder also reads Scryfall's bulk card file, function tags, prices and Game Changer flags.
- **[17Lands](https://www.17lands.com/)** — draft win-rate statistics (queried at runtime).
- **Commander deck builder** (all queried at runtime, cached locally, not redistributed; their terms are quoted
  under [Terms of use](#terms-of-use)):
  - **[EDHREC](https://edhrec.com/)** — what Commander players build, per commander, bracket and theme, plus salt.
  - **[Archidekt](https://archidekt.com/)** — decklists tagged with a bracket.
  - **[EDHTop16](https://edhtop16.com/)** — cEDH tournament results through its public API. Its tournament data comes
    from TopDeck.gg. This tool is not endorsed by EDHTop16.
  - **[Commander Spellbook](https://commanderspellbook.com/)** — the combo database behind the combo checks (its API,
    and its daily combo file for `stats`). Credit and link back, as its API guidelines ask; every combo `stats`
    prints carries its page address.
  - **[MTGJSON](https://mtgjson.com/)** — preconstructed deck lists.
  - **[Wizards of the Coast's Commander format page](https://magic.wizards.com/en/formats/commander)** — the bracket
    definitions and the Game Changers list. `commander/brackets.json` quotes their wording with its source and date.
- Magic: The Gathering is © Wizards of the Coast. This is an unofficial fan tool, not affiliated
  with or endorsed by Wizards of the Coast, or by any of the sites it reads.

## Requirements

- Python 3 (standard library only — no pip installs). The draft coach runs on 3.8+; the Commander builder needs 3.9+.
- Outbound HTTPS to `api.scryfall.com` and `www.17lands.com` (the draft coach).
- Outbound HTTPS for the Commander builder: `api.scryfall.com`, `data.scryfall.io` (Scryfall's bulk files),
  `json.edhrec.com`, `archidekt.com`, `edhtop16.com`, `backend.commanderspellbook.com`, `json.commanderspellbook.com`
  (the daily combo file, for `stats`) and `mtgjson.com`. After `warm`, `--offline` runs need none of them.
- MTGA "Detailed Logs (Plugin Support)" enabled (the draft coach).
- Optional, for `--fantasy`: the `claude` command-line tool on your `PATH` and a Claude token (see
  [Using it as an agent / coach](#using-it-as-an-agent--coach)).
