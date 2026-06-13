#!/usr/bin/env python3
"""Render a captured draft (drafts/<...>.json) into a readable, coached pick-by-pick markdown
replay. Pure post-hoc narration over the structured ETL data — every number/grade/oracle detail
is read from the draft JSON + the scryfall/grades caches, never invented.

Usage:  python3 src/replay.py [draft.json] [out.md] [--ai]
        --ai adds a model-written "🤖 Take" per pick (one claude -p call; needs CLAUDE_CODE_OAUTH_TOKEN).
"""
import json, os, sys, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root (this file is in src/)
SRC = os.path.join(HERE, "src")
DATA = os.path.join(HERE, "data")
sys.path.insert(0, SRC)
from mtgdraft.grades import load_grades_any
from mtgdraft.analysis import COLOR_NAMES

AI = "--ai" in sys.argv                                            # opt-in model commentary per pick
argv = [a for a in sys.argv[1:] if a != "--ai"]
PATH = argv[0] if argv else os.path.join(DATA, "drafts", "current.json")
draft = json.load(open(PATH))
scry = json.load(open(os.path.join(DATA, "cache", "scryfall_arena.json")))
grades, glabel = load_grades_any(draft.get("set", ""))
takes = {}
if AI:
    from mtgdraft.ai import pick_takes
    takes = pick_takes(draft)

COLORS = draft.get("analysis", {}).get("colors", "") or ""        # deck's final colors, e.g. "WB"

def oncolor(c, colors=None):
    """On-color relative to `colors` — by default the deck's FINAL colors, but the replay passes the
    colors committed AT THAT POINT (from the running data store) so each pick is audited against the
    deck as it actually stood, not in hindsight. Empty colors (nothing committed yet) = all open."""
    colors = COLORS if colors is None else colors
    col = c.get("color") or "C"
    if col in ("C", "") or not colors:                           # colorless / nothing committed = open
        return True
    return all(ch in colors for ch in col if ch in "WUBRG")

def g(c):                                                        # GIH as a %, or None
    return c["gih"] if c.get("gih") else None

def pct(v):
    return f"{v*100:.1f}%" if v else "n/a"

def grade_of(c):
    return grades.get(c["name"].lower(), "–")

def text_of(c):
    return (scry.get(str(c["id"]), {}).get("text", "") or "").replace("\n", " ").strip()

def image_of(c):
    """Front-face Scryfall image URL for `c`, or '' if cache is pre-v3 / lookup failed.
    Renders as a floated thumbnail next to each pick block — degrades cleanly to no-image."""
    return (scry.get(str(c["id"]), {}).get("image_url", "") or "").strip()

def mark(c, taken_id, colors):
    if c["id"] == taken_id: return "✅"
    return "▸" if oncolor(c, colors) else " "

def needs_read(run):
    """The deck's live needs — read straight from the running data store (the tool computes `needs`
    per pick now). Falls back to recomputing for older draft JSON that predates the field."""
    if not run:
        return []
    if "needs" in run:
        return run["needs"]
    n = run.get("n", 0)
    cre, two, rem = run.get("creatures", 0), run.get("two_drops", 0), run.get("removal_est", 0)
    frac = n / 42.0                                              # ~how far through the draft
    needs = []
    if two < round(6 * frac):  needs.append(f"2-drops ({two})")
    if rem < round(3.5 * frac): needs.append(f"removal (~{rem})")
    if cre < round(16 * frac):  needs.append(f"creatures ({cre})")
    five_plus = sum(v for k, v in (run.get("curve") or {}).items() if int(k) >= 5)
    if five_plus > 6:           needs.append(f"top-heavy ({five_plus} at 5+)")
    return needs

def build_note(p, prev):
    """Heuristic coaching note for one pick, audited against the deck-so-far (`prev` running block)."""
    tk = p["taken"]
    off = p["offered"]
    colors = (prev or {}).get("colors", "") or ""               # colors committed going INTO this pick
    if not tk:
        return "_(current pack — no pick recorded)_"
    best = off[0]                                                 # offered is pre-sorted by GIH desc
    on_off = [c for c in off if c["id"] != tk["id"] and oncolor(c, colors)]
    best_on = on_off[0] if on_off else None
    note = []
    early = p["pack"] == 1 and p["pick"] <= 5

    # On-color is audited against the colors committed GOING INTO this pick (from the running data
    # store), not the deck's final colors — so a red P1P4 pick is judged against the deck as it then
    # stood, not retconned into the WB deck it became. Empty `colors` (pack-1 open) = everything open.
    tk_tags = ", ".join(tk.get("tags", []) or []) or "—"
    tk_on = oncolor(tk, colors)
    best_off = not oncolor(best, colors)
    gap = (g(best) - g(tk)) if g(best) and g(tk) else None
    best_inflated = best.get("inflation")          # data store: GIH is selection-bias-inflated
    synergy_reach = bool(set(tk.get("tags", [])) & {"counters", "sacrifice", "tokens", "clues",
                                                    "spells-matter", "fractal", "converge"})
    color_tag = "on-color" if tk_on else f"{tk.get('color')}, off your {colors or 'colors'}"

    if tk["id"] == best["id"]:
        nxt = (g(best) - g(off[1])) if len(off) > 1 and g(best) and g(off[1]) else None
        lead = f"**Pick: {tk['name']}** ({pct(g(tk))}). Best card in the pack"
        lead += f", {nxt*100:.1f}% clear of the next — easy." if nxt and nxt > 0.03 else " — took it."
        note.append(lead)
    elif early:
        # colors aren't committed yet — judge on power, never on (final-color) fit
        lead = f"**Pick: {tk['name']}** ({pct(g(tk))}, {tk.get('color')} · {tk_tags})."
        if gap and gap > 0.04:
            kind = "synergy/build-around reach" if synergy_reach else "below-rate speculative pick"
            lead += (f" A {kind} on raw power — the pack's best was **{best['name']}** "
                     f"({pct(g(best))}) — but P{p['pack']}P{p['pick']} is still wide open, so it's a "
                     f"defensible flyer if the synergy comes together.")
        else:
            lead += f" Near the top of a still-open pack (best: {best['name']} {pct(g(best))})."
        note.append(lead)
    elif best_off and tk_on:
        # the genuine "bomb-but-off-archetype" case — took an on-color fit over an off-color headline
        extra = " (and its GIH is inflated — see below)" if best_inflated else ""
        note.append(f"**Pick: {tk['name']}** ({pct(g(tk))}, on-color · {tk_tags}). The headline number "
                    f"is **{best['name']}** ({pct(g(best))}, {best.get('color')}) — but it's off your "
                    f"{colors or 'colors'}{extra}. Taking the on-color fit.")
    elif best_off and not tk_on:
        note.append(f"**Pick: {tk['name']}** ({pct(g(tk))}, {tk.get('color')} — also off your "
                    f"{colors or 'colors'}). Nothing on-color near the top; best was **{best['name']}** "
                    f"({pct(g(best))}, {best.get('color')}). A speculative/splash pick.")
    elif gap and gap > 0.03:
        offc = "" if tk_on else ", and off-color"
        note.append(f"**Pick: {tk['name']}** ({pct(g(tk))}{offc}). ⚠ **{best['name']}** "
                    f"({pct(g(best))}, on-color) was {gap*100:.1f}% better and in your colors — "
                    f"the stronger pick here.")
    else:
        note.append(f"**Pick: {tk['name']}** ({pct(g(tk))}, {color_tag} · {tk_tags}) over "
                    f"**{best['name']}** ({pct(g(best))}) — close; defensible on fit/curve.")

    # passed an on-color premium (skip in pack 1 early — colors aren't locked, so "on-color" is moot)
    if not early and best_on and best_on["id"] != best["id"] and g(best_on) and g(best_on) >= 0.55:
        note.append(f"On-color premium also in the pack: {best_on['name']} ({pct(g(best_on))}).")

    # inflation caveat on the headline card, straight from the data store (the Snarl Song trap)
    if best_inflated and best["id"] != tk["id"]:
        note.append(f"⚠ **{best['name']}**'s {pct(g(best))} is inflated — {best_inflated['note']}")
    if tk.get("inflation"):
        note.append(f"⚠ Your pick's {pct(g(tk))} is inflated — {tk['inflation']['note']}")

    # expert note on the pick from the LoL set guide, if one exists
    if tk.get("guide"):
        note.append(f"📘 _Guide:_ {tk['guide']}")

    # deck-state audit, straight from the running data store: colors so far + what the deck still needs,
    # and whether this pick filled one of those needs.
    if prev:
        needs = needs_read(prev)
        state = f"_Deck going in: {prev.get('n')} cards, {prev.get('colors') or 'open'}"
        if needs:
            state += f" · still needs {', '.join(needs)}"
        state += "._"
        need_keys = " ".join(needs)
        filled = []
        if tk.get("cmc") == 2 and "2-drop" in need_keys:        filled.append("a 2-drop")
        if "removal" in (tk.get("tags") or []) and "removal" in need_keys: filled.append("removal")
        if filled:
            state += f"  ✓ Fills a need: {' & '.join(filled)}."
        note.append(state)

    # wheel callout — name the actual lane(s) flowing back, split into your colours vs a pivot signal
    wheels = [c for c in off if c.get("wheel")]
    if wheels:
        names = ", ".join(f"{c['name']} ({c.get('color') or 'C'})" for c in wheels)
        def lane(cols):
            return "/".join(COLOR_NAMES[ch] for ch in sorted(cols, key="WUBRG".index))
        wcols = {ch for c in wheels for ch in (c.get("color") or "") if ch in "WUBRG"}
        on_cols = {ch for ch in wcols if colors and ch in colors}
        off_cols = wcols - on_cols
        parts = []
        if on_cols:
            parts.append(f"**{lane(on_cols)}** (your colours) is coming back — your lane is open, keep mining it")
        if off_cols:
            where = f"open outside your {colors} — a pivot/splash signal" if colors \
                    else "open near you (nobody upstream is taking it)"
            parts.append(f"**{lane(off_cols)}** is {where}")
        if not wcols:
            parts.append("colourless/artifacts are flowing late — fine to pick up cheaply")
        note.append(f"🔄 Wheeled back (returned on the 8-seat lap): {names} — " + "; ".join(parts) + ".")

    return "  \n".join(note)

# ---- header ----
out = []
a = draft.get("analysis", {})
out.append(f"# Draft Replay — {draft.get('set')} {draft.get('fmt')}\n")
out.append(f"*Ratings source: {draft.get('ratings_fmt', draft.get('fmt'))}. "
           f"Grade column: {glabel or 'none'}. Reconstructed from `{os.path.relpath(PATH, HERE)}` — "
           f"all numbers/text are from the captured data, narration is post-hoc.*\n")
out.append(f"**Final deck: {COLORS or '—'}** · lean: {' · '.join(a.get('archetype_lean', []) or ['—'])}\n")
c = a.get("counts", {})
out.append(f"**Shape:** {c.get('creatures','?')} creatures · {c.get('spells','?')} spells · "
           f"~{a.get('removal_est','?')} removal · {a.get('two_drops','?')} two-drops · "
           f"curve {'  '.join(f'{k}:{v}' for k,v in (a.get('curve') or {}).items())}\n")
if a.get("flags"):
    out.append(f"**Flags:** {' · '.join(a['flags'])}\n")
out.append("\n*Each pick is audited against the deck **as it stood at that pick** (the per-pick "
           "`running` state), not in hindsight: `▸` = on-color vs the colors you'd committed by then "
           "(everything's open in pack 1), `✅` = your pick.*\n")
out.append("\n---\n")

# ---- per-pack, per-pick ----
last_pack = None
prev_run = None                                                  # running state from the PREVIOUS pick
for p in draft["picks"]:
    if p["pack"] != last_pack:
        out.append(f"\n## Pack {p['pack']}\n")
        last_pack = p["pack"]
    tk = p["taken"]
    colors_at = (prev_run or {}).get("colors", "") or ""         # colors committed going into this pick
    out.append(f"\n### P{p['pack']}P{p['pick']}" + (f" — took {tk['name']}" if tk else "") + "\n")
    # Float the taken-card image to the right of the pick block so the table flows next to it.
    # Falls back silently when the cache predates v3 (no `image_url`) — no image, no error.
    if tk:
        img = image_of(tk)
        if img:
            out.append(f'<img src="{img}" alt="{tk["name"]}" width="220" align="right">\n')
    # table of the pack (top cards) — always include the card actually taken, even if it ranks low
    rows = p["offered"][:8]
    if tk and not any(cc["id"] == tk["id"] for cc in rows):
        taken_card = next((cc for cc in p["offered"] if cc["id"] == tk["id"]), None)
        if taken_card:
            rows = rows + [taken_card]
    out.append(f"| | Card | Clr | GIH | IWD | ALSA | {glabel or 'Grade'} | Tags |")
    out.append("|---|---|---|---|---|---|---|---|")
    for cc in rows:
        iwd = f"{cc['iwd']*100:+.1f}" if cc.get("iwd") is not None else "—"
        alsa = f"{cc['alsa']:.1f}" if cc.get("alsa") else "—"
        tags = ", ".join(cc.get("tags", []) or [])
        if cc.get("inflation"): tags = "⚠infl · " + tags
        out.append(f"| {mark(cc, tk['id'] if tk else None, colors_at)} | {cc['name']} | {cc.get('color') or 'C'} "
                   f"| {pct(g(cc))} | {iwd} | {alsa} | {grade_of(cc)} | {tags} |")
    hidden = len(p["offered"]) - len(rows)
    if hidden > 0:
        out.append(f"| | _+{hidden} more_ | | | | | | |")
    out.append("")
    out.append(build_note(p, prev_run))
    take = takes.get(f"P{p['pack']}P{p['pick']}")               # opt-in model take (--ai)
    if take:
        out.append(f"\n🤖 **Take:** {take}")
    # what the taken card does
    if tk:
        t = text_of(tk)
        if t:
            out.append(f"\n> **{tk['name']}** — {t[:280]}")
    prev_run = p.get("running") or prev_run                      # carry forward for the next pick's audit

# ---- footer: running signal at end of each pack ----
out.append("\n\n---\n\n## Signal trail\n")
for pk in (1, 2, 3):
    picks = [p for p in draft["picks"] if p["pack"] == pk and p.get("running")]
    if picks:
        r = picks[-1]["running"]
        out.append(f"- **End of pack {pk}:** {r.get('n')} cards, {r.get('colors')} · "
                   f"premiums passed → {r.get('premiums_passed_readable') or '—'}")
if a.get("open_color_readable"):
    out.append(f"- **Open-color read (premiums flowing late):** {a['open_color_readable']}")

dest = argv[1] if len(argv) > 1 \
    else os.path.join(DATA, "drafts", f"{draft.get('set','draft')}-replay.md")
open(dest, "w").write("\n".join(out))
print("wrote", os.path.relpath(dest, HERE), f"({len(draft['picks'])} picks)")
