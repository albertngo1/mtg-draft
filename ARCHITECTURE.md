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
```

The first run downloads Scryfall's card file and builds a local index of about 35,000 cards (24 MB). That takes a
minute or two, once; the index is rebuilt after 7 days. Everything else it downloads is cached too (see
[Data sources, caching and offline use](#data-sources-caching-and-offline-use)).

### Terms used here

| term | meaning |
|---|---|
| **Bracket** | Wizards of the Coast's 1–5 power scale: 1 Exhibition, 2 Core, 3 Upgraded, 4 Optimized, 5 cEDH. **cEDH** is competitive Commander, meaning tournament play. The default is Bracket 3. |
| **Game Changer** | a card on Wizards' list of cards that push a deck up the scale (53 on 2026-10-11, flagged on each card in Scryfall's data). Bracket 3 allows up to three; Brackets 1 and 2 allow none. |
| **Precon** | a preconstructed deck sold ready to play. Precon lists come from MTGJSON. |
| **Inclusion** | the share of a commander's decks that play a card. **Synergy** is EDHREC's inclusion with this commander minus the inclusion across all decks of the same colors. |
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
Squirreled Away → Bracket 3, budget $75 (spent $65.44); themes: tokens; playstyle: aristocrats
 1  CUT Forest  →  ADD Thornvault Forager   +1.31  $2.88
    in 66% of 1,125 Bracket 3 Hazel decks (all brackets 59%, synergy +57%); +10% in sacrifice decks,
    +3% in tokens decks; fills: ramp, tutor
...
Sources: EDHREC 2026-10-11, EDHTop16 2026-10-11, Scryfall 2026-10-11, MTGJSON 2026-10-11.
At Bracket 3 these numbers show what deck builders chose, not how often decks won.
```

The number after the swap (`+1.31`) is its gain: the change in the deck's value, in the same units as a card score (a
card every builder plays scores about 1; see [How a deck is valued](#how-a-deck-is-valued-and-how-swaps-are-chosen)).

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
         [--theme T] [--playstyle P] [--fantasy TEXT] [--fantasy-weight W] [--keep-fun | --no-keep-fun]
         [--include CARD] [--exclude CARD] [--owned FILE] [--owned-precon NAME] [--allow-combos]
         [--out FILE] [-v]
check    [DECKFILE] [--precon NAME] [--commander NAME] [--bracket N]
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
| `warm` | downloads what the other commands need for one commander, so they can run with `--offline` |
| `validate` | measures how closely builds match real decks (see [Validation](#validation)) |

The four flags every command takes, then the rest (help text as `--help` prints it):

| flag | commands | meaning |
|---|---|---|
| `--json` | all | print the result as JSON (`"schema": 1`), not a report |
| `--refresh` | all | download again instead of using cached data |
| `--offline` | all | never connect; use cached data only (see `warm`) |
| `--sources LIST` | all | card-evidence sources to use, comma-separated (choices `edhrec`, `archidekt`, `edhtop16`) |
| `DECKFILE` | upgrade, check | a decklist file; `-` reads standard input |
| `--precon NAME` | upgrade, check | use a preconstructed deck by name instead of a file |
| `--commander NAME` | upgrade, check | the commander, when the list does not mark it (repeat for a partner) |
| `COMMANDER` | build, warm | the commander |
| `--partner NAME` | build, warm, themes | a second commander (Partner or Background); `themes` also needs `--commander` |
| `--commander NAME` | themes | list this commander's own themes |
| `--bracket N` | suggest, build, upgrade, check, warm; required by validate | power level 1-5 (default 3): 1 Exhibition, 2 Core, 3 Upgraded, 4 Optimized, 5 cEDH |
| `--budget USD` | suggest, build, upgrade | build and upgrade: most to spend on cards you do not own; suggest: most to spend on the deck's core cards |
| `--max-swaps N` | upgrade | most swaps to suggest (default 15) |
| `--theme T` | suggest, build, upgrade, warm | a theme to build around, e.g. tokens (repeat the flag or separate with commas); for `warm`, a theme to download |
| `--playstyle P` | suggest, build, upgrade | how the deck plays, e.g. go-wide (see `themes`) |
| `--fantasy TEXT` | suggest, build, upgrade | the deck you imagine, in your own words (Claude turns it into themes; needs a token) |
| `--fantasy-weight W` | build, upgrade | 0 = pure power, 1 = theme above all (default 0.5) |
| `--keep-fun`, `--no-keep-fun` | suggest, build, upgrade | penalize cards that are frustrating to play against (default on at Brackets 1-3) |
| `--include CARD` | build, upgrade | a card the deck must keep (repeatable) |
| `--exclude CARD` | build, upgrade | a card the deck must not play (repeatable) |
| `--owned FILE` | suggest, build, upgrade | a decklist of cards you own; they cost $0 (repeatable) |
| `--owned-precon NAME` | suggest, build, upgrade | a precon you own, e.g. "Squirreled Away" (repeatable) |
| `--allow-combos` | build, upgrade | allow two-card combos the bracket would block |
| `--out FILE` | build, upgrade | write the deck list here (Moxfield and Archidekt import it) |
| `-v`, `--verbose` | build, upgrade | show the evidence for every card (for `upgrade`, for each cut as well) |
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
| `CLAUDE_CODE_OAUTH_TOKEN` | the Claude token `--fantasy` needs; a gitignored `claude-token.txt` at the repo root works too, the same file the replay uses |

**Output.** Reports stay within 100 columns, so a phone terminal does not wrap a table mid-word. `--json` prints
only the result on stdout, `{"schema": 1, ...}`; `warnings` (a list of strings) and `sources` (each source with
`fetched`, `cache` and `age_days`) are on every command. Progress, notes and errors go to stderr. `--out FILE`
writes a `Commander` section and a `Deck` section, which Moxfield and Archidekt both import.

**Exit codes.** `0` success. `1` a mistake you can fix (unknown card or precon, bad flags), with close matches
printed ("did you mean ..."). `2` data the command cannot do without is unavailable (offline with nothing
cached, or the site is down). `130` stopped with Ctrl-C.

**Deck files.** `upgrade` and `check` read what players paste: `1 Sol Ring`, `1x Sol Ring` or `Sol Ring`; set and
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
| `net.py` | the one HTTP client: per-host pacing, retries with back-off, the file cache, `--offline` and `--refresh` |
| `carddb.py` | Scryfall's bulk card file boiled down to one record per card; forgiving name matching; cheapest prices |
| `decklist.py` | reads pasted lists, matches names to real cards, loads precons from MTGJSON, writes lists |
| `providers/` | one module per data source, registered in `providers/__init__.py` (`SIGNAL_PROVIDERS`) |
| `providers/edhrec.py` | what builders chose, per commander, bracket and theme; themes, salt, average land count |
| `providers/archidekt.py` | bracket-tagged decklists: the second builder source |
| `providers/edhtop16.py` | cEDH tournament entries with decklists and results: the tournament source |
| `providers/spellbook.py` | Commander Spellbook combos (in a list, and one card away) with their bracket tags |
| `providers/scryfall_tags.py` | Scryfall's community function tags as sets of cards |
| `roles.py` | what each card does (ramp, draw, ...) from those tags; the per-bracket targets |
| `brackets.py` | Wizards' bracket rules as data, the four checks, and the legality check |
| `fantasy.py` | the fantasy spec: the theme and playstyle menu, and the optional `claude -p` step for free text |
| `score.py` | card scores: gathers the evidence once, then plain arithmetic |
| `build.py` | the deck value, and `upgrade`, `build` and `suggest` on top of it |
| `calibrate.py` | measures role targets from real decks and writes `commander/role_targets.json` |
| `validate.py` | `validate`: held-out checks of builds against real decks |
| `render.py` | the text reports and the JSON |
| `commander/` (repo root) | committed reference data (`brackets.json`, `role_targets.json`, `playstyles.json`); see [`commander/README.md`](./commander/README.md) |
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
         │    ├─ providers.spellbook.find_combos   combos in the deck, and combos one card away
         │    ├─ brackets.check / blocked_adds     Game Changers, mass land denial, extra turns, two-card combos
         │    ├─ forced swaps first, then the best swap one at a time, under budget and bracket
         │    └─ combo check of the finished list; a swap that completes a banned combo is undone
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
| `NONBASIC_MIN` | 0.10 | a nonbasic land needs at least this score to take a slot from a basic |
| `COMBO_ROUNDS` | 3 | how often a banned combo found in the finished list is repaired |
| `LAND_BUDGET_SHARE` | 0.10 | the share of a `build` budget held back for nonbasic lands |

Both searches are local, not optimal: a swap that needs two cards to change at once is invisible to them.

- **`upgrade`** makes forced swaps first: anything that breaks the format (banned or not legal, outside the
  commander's colors, extra copies, a card you `--exclude`d) or the bracket (too many Game Changers, extra-turn cards or
  mass land denial; the weaker half of a banned combo). Each is replaced by the best legal add that fits the budget (a
  basic land if none does). Then it repeats the best affordable swap above `MIN_GAIN`, up to `--max-swaps`. It never
  cuts the commander or an `--include` card. The deck's own cards and anything you own cost $0; other adds are priced
  at Scryfall's cheapest printing. With a budget, the swaps are run again with a growing penalty per dollar and the
  run that ends with the most valuable deck is kept, so one pricey card does not eat the whole budget. When a budget
  allows no swap, the report lists the cheapest useful adds.
- **`build`** fills the nonland slots greedily by marginal value (your `--include` cards first), swaps until nothing
  improves, adds nonbasic lands that score at least `NONBASIC_MIN`, then splits basics by the colored mana symbols
  in the deck. It checks the finished list for banned combos and repairs it, up to `COMBO_ROUNDS` times.
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
python3 -m mtgcommander.calibrate --write             # replaces commander/role_targets.json
python3 -m mtgcommander.calibrate --sources edhtop16,archidekt   # measure Brackets 3 and 4 from Archidekt too
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

`validate --calibrate` runs the same calibration after the validation and rewrites the file, so the validation
numbers describe the targets as they were committed. It does not touch the score weights above.

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
| Commander Spellbook | combos in a list and combos one card away, each with a bracket tag | rules check | 7 days | `backend.commanderspellbook.com` |
| Scryfall | card data, function tags, cheapest printing | rules, roles, prices | card index 7 days, tags 30, prices 7 | `api.scryfall.com`, `data.scryfall.io` |
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
MTGJSON; the function tags; and the cheapest prices of about 500 likely cards. It does not fetch Commander
Spellbook combos: those answers are cached per exact card list, so an `--offline` run can check combos only for lists
it has checked online before (the list you give it, and the list after the swaps). For any other list it prints
"Combos were not checked", and the combo limit is not verified.

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

### Edge cases

| case | what happens |
|---|---|
| Unknown card name | `build` and `upgrade` stop before scoring with close matches ("did you mean ..."); `check` lists it as a problem and checks the rest. Unknown names inside a precon list are skipped with a warning |
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
  API host's `robots.txt` says `Disallow: /`.
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
building"): 81% against 82% at Bracket 5, 49% against 51% at Bracket 3, every build within the bracket's limits.

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
(`tests/commander/fixtures/`, never downloaded pages), touch no network, and run in a couple of seconds.

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
  - **[Commander Spellbook](https://commanderspellbook.com/)** — the combo database behind the combo checks. Credit
    and link back, as its API guidelines ask.
  - **[MTGJSON](https://mtgjson.com/)** — preconstructed deck lists.
  - **[Wizards of the Coast's Commander format page](https://magic.wizards.com/en/formats/commander)** — the bracket
    definitions and the Game Changers list. `commander/brackets.json` quotes their wording with its source and date.
- Magic: The Gathering is © Wizards of the Coast. This is an unofficial fan tool, not affiliated
  with or endorsed by Wizards of the Coast, or by any of the sites it reads.

## Requirements

- Python 3 (standard library only — no pip installs). The draft coach runs on 3.8+; the Commander builder needs 3.9+.
- Outbound HTTPS to `api.scryfall.com` and `www.17lands.com` (the draft coach).
- Outbound HTTPS for the Commander builder: `api.scryfall.com`, `data.scryfall.io` (Scryfall's bulk files),
  `json.edhrec.com`, `archidekt.com`, `edhtop16.com`, `backend.commanderspellbook.com` and `mtgjson.com`. After
  `warm`, `--offline` runs need none of them.
- MTGA "Detailed Logs (Plugin Support)" enabled (the draft coach).
- Optional, for `--fantasy`: the `claude` command-line tool on your `PATH` and a Claude token (see
  [Using it as an agent / coach](#using-it-as-an-agent--coach)).
