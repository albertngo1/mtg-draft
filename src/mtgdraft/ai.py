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
- WEIGH THE RUNNING DECK COMPOSITION: every take must judge the pick against the `deck_going_in` state at
  THAT point — creatures / spells / removal / two_drops / five_plus counts, the curve, themes, and the
  stated `needs`. A card's value is RELATIVE to what the deck already has: credit a pick that fills a real
  gap (creatures below ~15-18, two_drops below ~5-7, removal below ~3-4, an empty curve slot, or a listed
  `need`), and ding one that stacks an already-full slot (a 6th two-drop, a 5th card at 5+ MV, the 5th
  removal) or ignores the `needs`. Say which gap it fills or which glut it worsens.
- Judge EACH pick at decision-time using ONLY the `deck_going_in` state given. NEVER use hindsight about
  how the draft ended (you'll see the final colors, but a pick made at P1P4 didn't know them).
Give a GENUINE take: endorse a good pick briefly, or push back when it was a mistake and name the specific
better card. 1-2 sentences, concrete (cite the card / number / signal). No fluff, never just restate the table."""

# Appended to DOCTRINE only when the draft's event name flags a "cascade emblem" event
# (e.g. QuickDraftEmblem_SOS / MWM_SOS_Cascade). Without this, takes wrongly assume normal SOS.
CASCADE_NOTE = """

CASCADE-EMBLEM EVENT (auto-detected from the event name): this draft was played under the SOS "cascade
emblem" — you cascade ONCE PER TURN, on the FIRST spell cast that turn (NOT every spell, and it does not
chain). Adjust takes accordingly, but keep the guide/archetype read as the lead:
- It is a MODEST ~1-card/turn value bump, NOT a snowball. Do NOT credit "cascade value" as a reason to go
  removal-light or to overvalue raw card advantage.
- Value a FEW high-MV cards as turn-openers (the spell you lead a turn with gets the one cascade), but do
  NOT reward OVER-drafting top-end — only one fires per turn and a 2nd expensive spell that turn does
  nothing. A pile of 5+ drops is still the trap; a low curve with a few openers is correct.
- Cheap cards are GOOD cascade hits (what the one cascade flips into); don't penalize cheap on-plan cards
  as "bad in cascade." A normal aggressive curve is still what you want.
- Net: the emblem barely changes correct draft picks vs normal SOS — it rewards a coherent low-curve deck
  with a few bombs/openers, which is the normal good-deck shape. Do not invoke cascade to justify greedy
  top-end or thin removal."""

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
        curve = run.get("curve", {}) or {}
        five_plus = sum(v for k, v in curve.items() if str(k).isdigit() and int(k) >= 5)
        payload.append({
            "pick": f"P{p['pack']}P{p['pick']}",
            "deck_going_in": {"n": run.get("n", 0), "colors": run.get("colors", ""),
                              "creatures": run.get("creatures", 0), "spells": run.get("spells", 0),
                              "removal": run.get("removal_est", 0), "two_drops": run.get("two_drops", 0),
                              "five_plus": five_plus, "curve": curve,
                              "themes": run.get("themes", {}),
                              "needs": run.get("needs_readable") or run.get("needs", []),
                              "premiums_passed": run.get("premiums_passed_readable", "")},
            "took": _slim(_enrich(tk)) if tk else None,
            "options": [_slim(_enrich(c)) for c in p.get("offered", [])[:top]],
        })
        prev = p.get("running") or prev
    ev = (draft.get("event_name") or draft.get("event") or "").lower()
    is_cascade = "cascade" in ev or "emblem" in ev
    doctrine = DOCTRINE + (CASCADE_NOTE if is_cascade else "")
    user = (f"Set/format: {draft.get('set')} {draft.get('fmt')} (ratings source: "
            f"{draft.get('ratings_fmt')}){' — CASCADE-EMBLEM EVENT' if is_cascade else ''}. "
            f"Final deck colors: {draft.get('analysis', {}).get('colors')}.\nFor EACH pick below give "
            f"your take. Output ONLY a JSON object mapping the pick label to the take string — nothing else.\n\n"
            + json.dumps(payload))
    try:
        r = subprocess.run([claude, "-p", doctrine + "\n\n" + user],
                           env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": tok},
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=240)
        out = r.stdout.strip()
        s, e = out.find("{"), out.rfind("}")
        return json.loads(out[s:e + 1]) if s >= 0 else {}
    except Exception:
        return {}

def draft_summary(draft):
    """One more claude -p call → the CLOSING AUDIT (arc / what went right / marginal calls / final 40 /
    the lever / how-to-play) as a markdown string appended after the per-pick takes. '' on any failure."""
    from collections import Counter
    claude, tok = shutil.which("claude"), _token()
    if not claude or not tok:
        return ""
    gnotes = load_guide_notes(draft.get("set", ""))
    def _enrich(c):
        if c and not c.get("guide"):
            g = gnotes.get(c["name"].split("//")[0].strip().lower())
            if g:
                return {**c, "guide": g}
        return c
    picks = [{"pick": f"P{p['pack']}P{p['pick']}", "took": (p["taken"]["name"] if p.get("taken") else None)}
             for p in draft.get("picks", [])]
    names = Counter(c["name"] for c in draft.get("pool", []))
    seen, pool = set(), []
    for c in draft.get("pool", []):
        if c["name"] in seen:
            continue
        seen.add(c["name"])
        pool.append({"n": names[c["name"]], **_slim(_enrich(c)), "cmc": c.get("cmc"), "type": c.get("type")})
    a = draft.get("analysis", {}) or {}
    final = next((p["running"] for p in reversed(draft.get("picks", [])) if p.get("running")), {})
    ev = (draft.get("event_name") or draft.get("event") or "").lower()
    doctrine = DOCTRINE + (CASCADE_NOTE if ("cascade" in ev or "emblem" in ev) else "")
    instr = (
        "The draft is COMPLETE. Write a CLOSING AUDIT in GitHub-flavored markdown with EXACTLY these "
        "sections, using the '## ' headers verbatim and in this order:\n\n"
        "## \U0001F3C1 The arc\n2-4 sentences: how the draft developed — what the P1P1 set up, when and "
        "why the colors locked, the open lane you read.\n\n"
        "## ✅ What went right\n3-5 bullets, each citing a specific pick label + card.\n\n"
        "## ⚠️ Marginal calls\n2-4 bullets on the questionable/close picks, each citing the pick "
        "label and naming the better alternative if there was one. If the draft was clean, say so and list "
        "the 1-2 closest spots.\n\n"
        "## \U0001F0CF Final 40\nThe recommended 40-card build from the POOL ONLY (target ~17 lands, ~23 "
        "nonland, 15-18 creatures, 5-7 two-drops, 3-4+ removal, cap ~5-6 cards at 5+ MV; remember disguise "
        "cards deploy at 3 so they don't bloat the top end). List lands (count + split), creatures by mana "
        "value, then spells. End with a one-line 'Cuts:' on the notable sideboard cards and why.\n\n"
        "## \U0001F3AF The lever\n1-2 sentences: the single most important decision that shaped this deck.\n\n"
        "## ▶️ How to play it\n3-5 bullets: the deck's role/plan, mulligan guidance, a key "
        "sequencing note, and matchup context (when you're the beatdown vs. the control). Build the 40 ONLY "
        "from cards in the pool. Be concrete and concise — this is a post-draft review the player learns from."
    )
    user = (f"Set/format: {draft.get('set')} {draft.get('fmt')}. Final colors: {a.get('colors')}. "
            f"Archetype lean: {a.get('archetype_lean') or a.get('archetype') or '—'}. "
            f"Final deck-state: creatures {final.get('creatures')}, spells {final.get('spells')}, "
            f"removal~{final.get('removal_est')}, two-drops {final.get('two_drops')}, "
            f"curve {final.get('curve')}.\n\nPICKS (in order):\n{json.dumps(picks)}\n\n"
            f"FINAL POOL (build the 40 from these; n = copies owned):\n{json.dumps(pool)}")
    try:
        r = subprocess.run([claude, "-p", doctrine + "\n\n" + instr + "\n\n" + user],
                           env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": tok},
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=240)
        return r.stdout.strip()
    except Exception:
        return ""
