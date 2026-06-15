__doc__ = 'MTGA live draft coach — resolve a pack\'s Arena card IDs to a ranked 17Lands table.\n\nThe pipeline this automates (previously run by hand every pick):\n  1. read the current pack\'s Arena card IDs from MTGA\'s Player.log\n  2. map IDs -> card names/cost via the Scryfall Arena endpoint\n  3. pull 17Lands GIH WR / IWD / ALSA for the set+format\n  4. print a ranked table (highest GIH WR first)\n\nBy default the log is read LOCALLY — run this on the same machine where MTG Arena is\ninstalled (Windows or macOS). The log path is auto-detected per OS; override with MTG_LOG.\nReading the log from another machine over SSH is an optional advanced mode (see below).\n\nRequires MTGA "Detailed Logs (Plugin Support)" to be enabled: in Arena, go to\nSettings -> Account -> check "Detailed Logs (Plugin Support)", then restart Arena. Without\nit the draft pack entries this reads (Quick `DraftPack` / Premier `Draft.Notify`) never appear in Player.log.\n\nCGB / external-grade cross-reference is NOT scripted (it\'s a fragile scrape) — the\ncoaching agent does that step with WebFetch. See AGENTS.md.\n\nOutput: a table ranked by GIH WR, PLUS a "what each card does" section (oracle text +\nP/T) so picks are read for fit, not just stats. Use --brief to drop the text section.\n\nRun `warm` once per set: it pre-caches the whole set\'s card text + mana value, so every\nlater `pull`/`rank` makes ZERO live queries (17Lands itself is cached 24h). The pack→stats\njoin is by mtga_id, which 17Lands provides — so Scryfall is only needed for cost/text.\n\nUsage (Windows: use `python mtg-draft.py ...` or `mtg-draft.bat ...`):\n  python mtg-draft.py warm --set FIN     # pre-cache the whole set (text+MV) — run once per set\n  python mtg-draft.py cards --set FIN    # whole-set lean data as JSON — load into context once per draft\n  python mtg-draft.py pull               # read the current pack (Quick or Premier) from the local log, rank it\n  python mtg-draft.py pool               # audit your picks so far: creatures/spells/lands, curve, CABS\n  python mtg-draft.py watch              # stream: auto-print the table each time a new pack appears\n  python mtg-draft.py rank 102690 102462 # rank an explicit list of Arena card IDs\n  python mtg-draft.py resolve 102690 ... # print name|cmc|color|type for IDs\n  python mtg-draft.py capture            # show/Start the background log-capture; `capture stop` to end it\n  python mtg-draft.py draft              # parse the captured stream -> drafts/current.json + summary\n\n(On macOS/Linux you can also use the ./mtg-draft.sh wrapper.)\n\nSide-car capture: any draft command (pull/pool/watch) auto-starts a detached background\nprocess that mirrors the ENTIRE Player.log stream to logs/player_stream.log and keeps\nfollowing it (across Arena restarts) until you run `capture stop`. It\'s idempotent — only\none runs at a time. This gives a durable raw record of the whole draft so questions can be\nanswered from the saved stream instead of re-reading the noisy live log. The stream is\nbounded by a front-truncating cap (default 50MB; --cap-mb / MTG_CAP_MB) that drops the\noldest bytes first, so a draft in progress is never trimmed.\n\nCommon flags:\n  --set FIN           17Lands expansion code (pull/pool/watch auto-detect it from the live\n                      draft\'s EventName; otherwise defaults to $MTG_SET or FIN)\n  --fmt PremierDraft  PremierDraft | QuickDraft | TradDraft | Sealed (auto-detected like --set;\n                      a format with no win-rate data yet falls back to PremierDraft history)\n  --colors UR         mark these colors as on-color (OPTIONAL — auto-detected from your picks\n                      for pull/pool/watch; pass this only to override the guess)\n  --days 120          17Lands lookback window in days (default 120)\n  --brief             skip the oracle-text section (table only)\n  --poll N            watch poll interval in seconds (default 2)\n  --refresh           force re-fetch of the cached 17Lands dataset\n\nAdvanced — read the log from ANOTHER machine over SSH (e.g. Arena on a different PC):\n  --ssh user@host     SSH target whose Player.log to read (or set MTG_SSH)\n  --ssh-key PATH      SSH private key for that target (or set MTG_SSH_KEY)\n  --local             force local read (default; kept for back-compat)\n  When --ssh / MTG_SSH is set, set MTG_LOG to the log path ON THAT remote machine.\n\nConfig (env or flags):\n  MTG_SET, MTG_FMT, MTG_COLORS, MTG_DAYS\n  MTG_LOG    override the Player.log path (auto-detected per OS by default)\n  MTG_SSH, MTG_SSH_KEY    optional remote-read target + key (leave unset for local)\n'
import sys, os, re, json
from .config import CAP_MB_DEFAULT, DEFAULTS, HERE, STREAM
from .sources import resolve_ids, warm_set
from .logread import apply_event, infer_colors, pull_pack, pull_picked
from .capture import capture_status, ensure_capture, stop_capture, tail_follow
from .etl import refresh_current, export_cards
from .render import print_deck_state, print_draft_summary, print_pool, print_table, watch

def main():
    args = sys.argv[1:]

    # Internal: the detached background follower (started by ensure_capture). Not user-facing.
    if args and args[0] == "_tail":
        tail_follow(args[1])
        return

    cfg = dict(DEFAULTS)
    cfg["refresh"] = False
    cmd, ids = None, []
    cfg["brief"] = False
    cfg["force_local"] = bool(os.environ.get("MTG_LOCAL"))  # --local / MTG_LOCAL forces local read
    cfg["poll"] = 2
    cfg["colors_explicit"] = bool(cfg["colors"])  # MTG_COLORS env counts as explicit
    cfg["capture_action"] = "start"               # for the `capture` command: start|status|stop
    cfg["cap_mb"] = CAP_MB_DEFAULT                # captured-stream size cap (front-truncating)
    cfg["set_explicit"] = False                  # --set given? (else ETL auto-detects from EventName)
    cfg["fmt_explicit"] = False                  # --fmt given? (else ETL auto-detects from EventName)
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("pull", "rank", "resolve", "warm", "pool", "watch", "capture", "draft", "cards"):
            cmd = a
        elif a in ("stop", "status", "start") and cmd == "capture":
            cfg["capture_action"] = a
        elif a == "--local":
            cfg["force_local"] = True
        elif a == "--ssh":
            i += 1; cfg["ssh"] = args[i]
        elif a == "--ssh-key":
            i += 1; cfg["ssh_key"] = os.path.expanduser(args[i])
        elif a == "--poll":
            i += 1; cfg["poll"] = float(args[i])
        elif a == "--set":
            i += 1; cfg["set"] = args[i]; cfg["set_explicit"] = True
        elif a == "--fmt":
            i += 1; cfg["fmt"] = args[i]; cfg["fmt_explicit"] = True
        elif a == "--colors":
            i += 1; cfg["colors"] = args[i]; cfg["colors_explicit"] = True
        elif a == "--days":
            i += 1; cfg["days"] = int(args[i])
        elif a == "--cap-mb":
            i += 1; cfg["cap_mb"] = float(args[i])
        elif a == "--refresh":
            cfg["refresh"] = True
        elif a == "--brief":
            cfg["brief"] = True
        elif a in ("-h", "--help"):
            print(__doc__); return
        elif re.fullmatch(r"\d{5,7}", a):
            ids.append(a)
        else:
            print(f"unknown arg: {a}\n"); print(__doc__); return
        i += 1

    if cmd is None and ids:
        cmd = "rank"

    # Any live-draft command spins up the side-car capture (idempotent) so the full
    # Player.log stream is always being mirrored to logs/ — no extra step needed.
    if cmd in ("pull", "pool", "watch", "draft"):
        if ensure_capture(cfg):
            print(f"  (capture started → {os.path.relpath(STREAM, HERE)})")

    if cmd == "draft":
        out = refresh_current(cfg)
        if not out:
            raise SystemExit(
                "No draft found in the capture stream yet (logs/player_stream.log).\n"
                "Start/continue a draft in Arena (with Detailed Logs on) — `pull`/`capture` "
                "keep the stream recording — then run `draft` again.")
        state, n_drafts, path = out
        print_draft_summary(state, n_drafts, path)
    elif cmd == "capture":
        if cfg["capture_action"] == "stop":
            stop_capture()
        else:
            if cfg["capture_action"] != "status" and ensure_capture(cfg):
                print("  capture: started.")
            capture_status(cfg)
    elif cmd == "warm":
        warm_set(cfg)
    elif cmd == "watch":
        try:
            watch(cfg)
        except KeyboardInterrupt:
            print("\n  stopped.")
    elif cmd == "pool":
        picked, event = pull_picked(cfg)
        apply_event(cfg, event)
        if not cfg["colors_explicit"]:
            cfg["colors"] = infer_colors(picked, cfg)
        print_pool(picked, cfg)
    elif cmd == "pull":
        pack, pk, pi, picked, event = pull_pack(cfg)
        apply_event(cfg, event)          # set/fmt from the live draft's EventName, unless explicit
        if not cfg["colors_explicit"]:
            cfg["colors"] = infer_colors(picked, cfg)
        label = (f"Pack {pk+1} Pick {pi+1}" if pk >= 0 else "current pack")
        auto = "" if cfg["colors_explicit"] else f", colors auto: {cfg['colors'] or '—'}"
        print(f"\n  >> {label}  ({len(picked)} cards already taken{auto})")
        try:
            refresh_current(cfg)                  # update current.json from the live stream first
        except Exception:
            pass
        print_deck_state()                        # LEAD with the deck-state dashboard every pick
        print_table(pack, cfg, show_text=not cfg["brief"])
    elif cmd == "rank":
        if not ids:
            raise SystemExit("rank: give Arena card IDs, e.g. rank 102690 102462")
        print_table(ids, cfg, show_text=not cfg["brief"])
    elif cmd == "resolve":
        for cid, rec in resolve_ids(ids).items():
            print(f"{cid}|{rec['name']}|{rec['cmc']}|{rec['color']}|"
                  f"{rec.get('type_line') or rec.get('type','')}")
    elif cmd == "cards":
        recs, rfmt = export_cards(cfg)                # whole-set lean data — load once at draft start
        print(json.dumps({"set": cfg["set"], "fmt": cfg["fmt"], "ratings_fmt": rfmt,
                          "n": len(recs), "cards": recs}, ensure_ascii=False))
    else:
        print(__doc__)
