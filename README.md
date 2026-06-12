# mtg-draft

**A draft coach for MTG Arena that lives in your terminal.**

While you draft, it reads the pack you're looking at straight out of Arena's log, ranks every card by
real [17Lands](https://www.17lands.com/) win-rate data, and shows you what each card does — so every
pick is backed by data instead of a gut read.

No account login. No screen overlay. No browser extension. Just a Python script reading the log file
Arena already writes on your own machine.

```
  MKM PremierDraft  (on-color = WB)

   CARD                    CLR  R  MV GIHWR   IWD    ALSA  N     CGB   tier
  -----------------------------------------------------------------------------
   Enlisted Wurm           WG   U  6  60.6%   +4.9   3.7   5396  B+    🔥bomb  (off)
   Krosan Tusker           G    C  7  56.5%   +4.1   4.6   4002  C+    excellent  (off)
  ▸Putrid Warrior          WB   C  2  55.5%   +0.0   6.8   934   C-    excellent
   Kuldotha Rebirth        R    C  1  50.0%   -0.6   6.2   856   C     filler  (off)
   ...
```

Cards in your colors are marked `▸`; off-color picks are tagged `(off)`. Below the table (not shown)
the tool prints the mana cost, stats, and oracle text for every card in the pack, so you're judging
on *fit*, not just the win-rate column.

## Why this exists

Good limited players already do this loop by hand every pick: read the pack, look up each card's
17Lands numbers, weigh them against the archetypes that are open. This tool just does it for you,
instantly, without leaving the game — and it's careful about *how* it reads the numbers. The key idea
baked in: a card's win rate is the win rate of **the decks that drafted it**, not a context-free
score. A payoff card looks amazing because the deck built around it wins — that doesn't mean it's good
in *your* pile. The tool surfaces that distinction instead of hiding it behind a single number.

## Quick start

You'll need **Python 3.8+** and a one-time Arena setting:

> In MTG Arena: **Settings → Account → check "Detailed Logs (Plugin Support)"**, then restart Arena.
> Without this, the draft packs this tool reads never get written to the log.

```bash
git clone https://github.com/albertngo1/mtg-draft && cd mtg-draft

# Once per set: pre-cache card text + data so live picks make zero network calls.
# Use the set's 17Lands code (e.g. FIN, DSK, MKM).
python3 src/mtg-draft.py warm --set FIN

# During the draft: read the current pack and rank it. Set, format, and your
# colors are all auto-detected from the live draft.
python3 src/mtg-draft.py pull
```

On **Windows**, use `python` and the `mtg-draft.bat` wrapper (`mtg-draft.bat pull`). On macOS/Linux
there's a `./mtg-draft.sh` wrapper too. Nothing to `pip install` — it's standard library only.

Want it to update on its own? Run **`watch`** in a side pane and it reprints the ranked table every
time a new pack appears.

## Two ways to use it

**🧍 Solo — no AI, no API key.** The whole ranking engine is plain Python over cached 17Lands +
Scryfall data. `warm` once, keep `watch` running beside Arena, and draft straight off the live
ranked overlay. Nothing leaves your machine.

**🤖 Coached — add an AI agent.** Point an LLM agent (e.g. Claude Code) at
[`AGENTS.md`](./AGENTS.md) and it drives the same loop but adds *judgment*: reading open lanes,
cross-referencing expert set guides, mana-curve warnings, and adapting when you take an off-meta
pick. It's a second opinion layered on top — the solo tool works fine without it. If you use
[Claude Code](https://claude.com/claude-code), the repo ships a `/mtg-draft` skill (in
[`.claude/skills/`](./.claude/skills/mtg-draft/)) that wires this up — just open the repo and type
`/mtg-draft`.

Either way, the 17Lands data is the source of truth and the AI is decorrelated expert color, never
the other way around.

## Learn more

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — the full reference: every command and flag, how the
  log-reading and caching work, the draft-history reconstruction, repo layout, and more.
- **[AGENTS.md](./AGENTS.md)** — the operating manual for the AI coaching layer: universal limited
  theory plus how to drive this tool pick-by-pick.

## Credits

- **[17Lands](https://www.17lands.com/)** — draft win-rate statistics (queried at runtime).
- **[Scryfall](https://scryfall.com/)** — card names, mana costs, and oracle text (queried at
  runtime, not redistributed; please respect their [API guidelines](https://scryfall.com/docs/api)).

Magic: The Gathering is © Wizards of the Coast. This is an unofficial fan tool, not affiliated with
or endorsed by Wizards of the Coast.

## License

[MIT](./LICENSE)
