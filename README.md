# mtg-draft

Live MTG Arena draft coaching helper. Turns a pack's Arena card IDs into a 17Lands-ranked
table — automating the read-pack → resolve-names → fetch-17Lands → rank loop that used to be
run by hand on every pick.

No service, no ports — it's a CLI run on the mini. The agent-facing coaching workflow and
Albert's draft preferences live in [`AGENTS.md`](./AGENTS.md).

## Usage

```bash
cd ~/src/mtg-draft

# Live: SSH the laptop, read the current pack from Player.log, rank it
./mtg-draft.sh pull --colors UR

# Manual: rank an explicit list of Arena card IDs
./mtg-draft.sh rank --colors UR 102690 102462 102498

# Resolve IDs to name|cmc|color|type (handy for deck audits)
./mtg-draft.sh resolve 102690 102462
```

Output is sorted by GIH WR; on-color cards (per `--colors`) are marked `▸`, off-color tagged
`(off)`. Columns: `CARD CLR R MV GIHWR IWD ALSA N tier`.

## Flags / config

| flag | env | default | meaning |
|---|---|---|---|
| `--set` | `MTG_SET` | `SOS` | 17Lands expansion code |
| `--fmt` | `MTG_FMT` | `QuickDraft` | PremierDraft / QuickDraft / TradDraft / Sealed |
| `--colors` | `MTG_COLORS` | (none) | mark these colors on-color, e.g. `UR` |
| `--days` | `MTG_DAYS` | `120` | 17Lands lookback window |
| `--refresh` | | | force re-fetch of cached 17Lands data |
| | `MTG_SSH` | `albertngo@100.111.228.115` | laptop SSH target |
| | `MTG_SSH_KEY` | `~/.ssh/wc3_reverse_play` | SSH key |
| | `MTG_LOG` | `~/Library/.../MTGA/Player.log` | remote Player.log path |

**New set each season:** change `--set` / `--fmt`. The current event's set code is in the log
(`"EventName":"QuickDraft_<SET>_<date>"`).

## How it works

1. `pull` SSHes the laptop and greps the last `DraftPack` array out of `Player.log`.
2. Arena IDs → card data via Scryfall `cards/arena/<id>` (cached in `cache/`, needs an
   `Accept: application/json` header or Scryfall 400s).
3. 17Lands `card_ratings/data` for the set+format (cached 24h in `cache/`).
4. Joins by name, sorts by GIH WR, prints the table.

CGB / external-grade cross-reference is intentionally not scripted (fragile page scrape) — the
coaching agent does that step with WebFetch per `AGENTS.md`.

## Requirements

- Python 3 (stdlib only — no pip installs).
- SSH access to the laptop with `~/.ssh/wc3_reverse_play` (for `pull`).
- Outbound HTTPS to `api.scryfall.com` and `www.17lands.com`.
