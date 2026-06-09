"""Optional AI commentary for the replay — one batched `claude -p` call returns a 1-line take per
pick. Off unless the caller asks for it (replay.py --ai). Best-effort: any failure (no token, 401,
bad JSON) returns {} so the deterministic replay is unaffected. Needs the long-lived
CLAUDE_CODE_OAUTH_TOKEN (env or a gitignored claude-token.txt at the repo root) — the
~/.claude/.credentials.json token 401s in a spawned subprocess."""
import os, json, shutil, subprocess
from .config import ROOT

# Distilled from AGENTS.md so the takes reflect THIS tool's doctrine, not generic MTG opinion.
DOCTRINE = """You are a sharp MTG Limited draft coach. For each pick of a COMPLETED draft (under review),
give a one-line take. Principles to apply:
- 17Lands GIH WR is the anchor, but judge the CARD — cost, evasion, role, curve fit — not just the number.
- GIH is INFLATED for payoff / Converge / build-around cards (flagged `inflated`): the win rate reflects
  decks built to abuse them, so discount them hard for a plain 2-color deck.
- BREAD priority: bombs > premium removal > evasion > efficient creatures > filler. Threats beat answers;
  stop taking removal past ~3-4. Bias toward proactive threats and a real closer (evasion), not a 9th answer.
- Deck shape (Be Boring / CABS): ~15-18 creatures, 5-7 two-drops, 3-4 removal, cap ~5-6 at 5+ MV;
  consistency beats raw power; all else equal take the cheaper card.
- Signals: stay open early, lock colors ~P1P8-9, last clean pivot is P2P1-3. ALSA = contention
  (low = take now, won't wheel). 8-seat pod: a card returns at pick N+8. Wheeling cards = that lane is open.
- Quick Draft is vs BOTS: hate-drafting does nothing; signals are softer and good cards wheel more.
- Judge EACH pick at decision-time using ONLY the `deck_going_in` state given. NEVER use hindsight about
  how the draft ended (you'll see the final colors, but a pick made at P1P4 didn't know them).
Give a GENUINE take: endorse a good pick briefly, or push back when it was a mistake and name the specific
better card. 1-2 sentences, concrete (cite the card / number / signal). No fluff, never just restate the table."""

def _token():
    t = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if t:
        return t.strip()
    try:
        return open(os.path.join(ROOT, "claude-token.txt")).read().strip()
    except Exception:
        return None

def _slim(c):
    """A compact card view — only what's decision-relevant, to keep the prompt small."""
    d = {"name": c["name"], "clr": c.get("color"), "gih": c.get("gih")}
    if c.get("alsa"):      d["alsa"] = round(c["alsa"], 1)
    if c.get("ds"):        d["grade"] = c["ds"]
    if c.get("tags"):      d["tags"] = c["tags"]
    if c.get("inflation"): d["inflated"] = c["inflation"]["kind"]
    if c.get("wheel"):     d["wheeled"] = True
    return d

def pick_takes(draft, top=6):
    """{pick_label: take} from one claude -p call, or {} if unavailable/failed. Each pick is sent with
    the deck state GOING INTO it (point-in-time, no hindsight) plus its top options."""
    claude, tok = shutil.which("claude"), _token()
    if not claude or not tok:
        return {}
    payload, prev = [], None
    for p in draft.get("picks", []):
        run = prev or {}
        tk = p.get("taken")
        payload.append({
            "pick": f"P{p['pack']}P{p['pick']}",
            "deck_going_in": {"n": run.get("n", 0), "colors": run.get("colors", ""),
                              "curve": run.get("curve", {}), "needs": run.get("needs", []),
                              "premiums_passed": run.get("premiums_passed_readable", "")},
            "took": _slim(tk) if tk else None,
            "options": [_slim(c) for c in p.get("offered", [])[:top]],
        })
        prev = p.get("running") or prev
    user = (f"Set/format: {draft.get('set')} {draft.get('fmt')} (ratings source: "
            f"{draft.get('ratings_fmt')}). Final deck colors: "
            f"{draft.get('analysis', {}).get('colors')}.\nFor EACH pick below give your take. "
            f"Output ONLY a JSON object mapping the pick label to the take string — nothing else.\n\n"
            + json.dumps(payload))
    try:
        r = subprocess.run([claude, "-p", DOCTRINE + "\n\n" + user],
                           env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": tok},
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=240)
        out = r.stdout.strip()
        s, e = out.find("{"), out.rfind("}")
        return json.loads(out[s:e + 1]) if s >= 0 else {}
    except Exception:
        return {}
