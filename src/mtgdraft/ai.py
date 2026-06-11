"""Optional AI commentary for the replay — one batched `claude -p` call returns a 1-line take per
pick. Off unless the caller asks for it (replay.py --ai). Best-effort: any failure (no token, 401,
bad JSON) returns {} so the deterministic replay is unaffected. Needs the long-lived
CLAUDE_CODE_OAUTH_TOKEN (env or a gitignored claude-token.txt at the repo root) — the
~/.claude/.credentials.json token 401s in a spawned subprocess."""
import os, json, shutil, subprocess
from .config import ROOT
from .grades import load_guide_notes

# Distilled from AGENTS.md so the takes reflect THIS tool's doctrine, not generic MTG opinion.
DOCTRINE = """You are a sharp MTG Limited draft coach. For each pick of a COMPLETED draft (under review),
give a one-line take. Principles to apply:
- LEAD WITH THE GUIDE: the set's archetypes, which color pairs are strongest, and the card's role
  in the open archetype drive the pick. The `guide` field (expert per-card note) is your lead lens.
- CORE: every GIH WR is ARCHETYPE-CONDITIONAL — it's the win rate of the decks that actually drafted
  the card, not a context-free measure. Decode what it's conditioned on and ask if THIS deck matches.
  * Low archetype concentration (colorless / mono-pip / generically-good two-color) → WR transfers →
    strong primary input, near co-equal with the guide.
  * High concentration (Converge/X-cost payoffs, build-arounds, multicolor synergy) → the number is
    the SOUP/payoff deck's result, not yours → discount hard unless you're that deck. (Snarl Song's
    60.7% is soup at X=4-5; in 2-color GW it's two 2/2s for 6. Substitute your real X/support first.)
  * The guide LEADS not because it's unbiased (it's archetype tiers too) but because it DECODES the
    stat — "A in soup, C in 2-color" surfaces the hidden conditioning. Guide tells you which
    archetype's number you're reading.
  * ALSA is the exception: draft BEHAVIOR (contention/openness), not an outcome, so not
    archetype-conditioned — the one reliably orthogonal signal.
  * IWD = win-rate delta → same conditioning + extra variance → MORE skeptical than GIH; a flag only.
  * NAME THE MECHANISM (honesty guardrail): to discount a card's WR you must name the concrete reason
    the conditioning fails for THIS deck (X=color count, off-color pips, needs graveyard/go-wide/a
    payoff not drafted). No nameable mechanism = the WR transfers, don't override it — that's
    rationalizing, not decoding. And only do this work on the high-conditioning minority (payoffs/
    Converge/multicolor/build-arounds); for vanilla commons the number transfers, trust it.
  Format matters only via concentration: SOS buries decks into invisible soup (distrust the column);
  MKM's clean two-color guilds concentrate less (more cards transfer). Judge the CARD — cost, role, fit.
- GIH is INFLATED for payoff / Converge / build-around cards (flagged `inflated`): the win rate reflects
  decks built to abuse them, so discount them hard for a plain 2-color deck.
- BREAD priority: bombs > premium removal > evasion > efficient creatures > filler. Threats beat answers;
  stop taking removal past ~3-4. Bias toward proactive threats and a real closer (evasion), not a 9th answer.
- Deck shape (Be Boring / CABS): ~15-18 creatures, 5-7 two-drops, 3-4 removal, cap ~5-6 at 5+ MV;
  consistency beats raw power; all else equal take the cheaper card.
- Signals: stay open early, lock colors ~P1P8-9, last clean pivot is P2P1-3. ALSA = contention
  (low = take now, won't wheel) — the primary 17Lands read. 8-seat pod: a card returns at pick N+8.
  Wheeling cards = that lane is open.
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
    d = {"name": c["name"], "clr": c.get("color")}
    if c.get("guide"):     d["guide"] = c["guide"]       # lead lens: expert per-card note
    if c.get("alsa"):      d["alsa"] = round(c["alsa"], 1)
    if c.get("iwd") is not None: d["iwd"] = round(c["iwd"] * 100, 1)
    if c.get("ds"):        d["grade"] = c["ds"]
    if c.get("gih"):       d["gih"] = c["gih"]            # tiebreaker only — listed last
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
    # Backfill the expert guide note at take-time so a store built before the guide existed (or before
    # its notes were parseable, e.g. SOS's table format) still feeds the lead-lens note to the model.
    gnotes = load_guide_notes(draft.get("set", ""))
    def _enrich(c):
        if c and not c.get("guide"):
            g = gnotes.get(c["name"].split("//")[0].strip().lower())
            if g:
                return {**c, "guide": g}
        return c
    payload, prev = [], None
    for p in draft.get("picks", []):
        run = prev or {}
        tk = p.get("taken")
        payload.append({
            "pick": f"P{p['pack']}P{p['pick']}",
            "deck_going_in": {"n": run.get("n", 0), "colors": run.get("colors", ""),
                              "curve": run.get("curve", {}), "needs": run.get("needs", []),
                              "premiums_passed": run.get("premiums_passed_readable", "")},
            "took": _slim(_enrich(tk)) if tk else None,
            "options": [_slim(_enrich(c)) for c in p.get("offered", [])[:top]],
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
