#!/usr/bin/env python3
"""Render a captured draft (drafts/<...>.json) into a readable, coached pick-by-pick markdown
replay. Pure post-hoc narration over the structured ETL data — every number/grade/oracle detail
is read from the draft JSON + the scryfall/grades caches, never invented.

Usage:  python3 scripts/replay.py [drafts/current.json] [> out.md]
"""
import json, os, sys, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root (this file is in src/)
SRC = os.path.join(HERE, "src")
DATA = os.path.join(HERE, "data")
sys.path.insert(0, SRC)
import importlib.util
spec = importlib.util.spec_from_file_location("mtg", os.path.join(SRC, "mtg-draft.py"))
mtg = importlib.util.module_from_spec(spec); spec.loader.exec_module(mtg)

PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA, "drafts", "current.json")
draft = json.load(open(PATH))
scry = json.load(open(os.path.join(DATA, "cache", "scryfall_arena.json")))
grades, glabel = mtg.load_grades_any(draft.get("set", ""))

COLORS = draft.get("analysis", {}).get("colors", "") or ""        # deck's final colors, e.g. "WB"
BOMB = 0.57                                                       # GIH WR bomb threshold

def oncolor(c):
    col = c.get("color") or "C"
    if col in ("C", ""):                                          # colorless = castable in any deck
        return True
    return all(ch in COLORS for ch in col if ch in "WUBRG")

def g(c):                                                        # GIH as a %, or None
    return c["gih"] if c.get("gih") else None

def pct(v):
    return f"{v*100:.1f}%" if v else "n/a"

def grade_of(c):
    return grades.get(c["name"].lower(), "–")

def text_of(c):
    return (scry.get(str(c["id"]), {}).get("text", "") or "").replace("\n", " ").strip()

def mark(c, taken_id):
    if c["id"] == taken_id: return "✅"
    return "▸" if oncolor(c) else " "

def build_note(p):
    """Heuristic coaching note for one pick, grounded in the card data."""
    tk = p["taken"]
    off = p["offered"]
    if not tk:
        return "_(current pack — no pick recorded)_"
    best = off[0]                                                 # offered is pre-sorted by GIH desc
    on_off = [c for c in off if c["id"] != tk["id"] and oncolor(c)]
    best_on = on_off[0] if on_off else None
    note = []
    pickno = (p["pack"] - 1) * 15 + p["pick"]
    early = p["pack"] == 1 and p["pick"] <= 5

    # framing of the card taken
    tk_tags = ", ".join(tk.get("tags", []) or []) or "—"
    if tk["id"] == best["id"]:
        gap = (g(best) - g(off[1])) if len(off) > 1 and g(best) and g(off[1]) else None
        lead = f"**Pick: {tk['name']}** ({pct(g(tk))}). Best card in the pack"
        lead += f", {gap*100:.1f}% clear of the next — easy." if gap and gap > 0.03 else " — took it."
        note.append(lead)
    else:
        gap = (g(best) - g(tk)) if g(best) and g(tk) else None
        payoff = bool(set(best.get("tags", [])) & {"counters", "sacrifice", "tokens", "spells-matter",
                                                   "converge", "fractal", "clues"})
        if not oncolor(best):
            # the "bomb-but-off-archetype" case
            why = "a build-around whose win rate rides on a shell you don't have" if payoff \
                  else f"off your {COLORS or 'colors'}"
            note.append(f"**Pick: {tk['name']}** ({pct(g(tk))}, on-color · {tk_tags}). The headline "
                        f"number is **{best['name']}** ({pct(g(best))}, {best.get('color')}) — but it's "
                        f"{why}. Taking the on-color fit.")
        elif gap and gap > 0.03:
            note.append(f"**Pick: {tk['name']}** ({pct(g(tk))}). ⚠ **{best['name']}** "
                        f"({pct(g(best))}, on-color) was {gap*100:.1f}% better and in your colors — "
                        f"the stronger pick here.")
        else:
            note.append(f"**Pick: {tk['name']}** ({pct(g(tk))}, {tk_tags}) over "
                        f"**{best['name']}** ({pct(g(best))}) — close; defensible on fit/curve.")

    if early and p["pick"] >= 3:
        note.append("_(Still open this early — taking power/color-flex, not committing.)_")

    # passed an on-color premium that wasn't the headline card
    if best_on and best_on["id"] != best["id"] and g(best_on) and g(best_on) >= 0.55:
        note.append(f"On-color premium also in the pack: {best_on['name']} ({pct(g(best_on))}).")

    # wheel callout
    wheels = [c["name"] for c in off if c.get("wheel")]
    if wheels:
        note.append(f"🔄 Wheeled back: {', '.join(wheels)} — confirms that lane is open near you.")

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
out.append("\n---\n")

# ---- per-pack, per-pick ----
last_pack = None
for p in draft["picks"]:
    if p["pack"] != last_pack:
        out.append(f"\n## Pack {p['pack']}\n")
        last_pack = p["pack"]
    tk = p["taken"]
    out.append(f"\n### P{p['pack']}P{p['pick']}" + (f" — took {tk['name']}" if tk else "") + "\n")
    # table of the pack (top cards)
    rows = p["offered"][:8]
    out.append(f"| | Card | Clr | GIH | IWD | ALSA | {glabel or 'Grade'} | Tags |")
    out.append("|---|---|---|---|---|---|---|---|")
    for cc in rows:
        iwd = f"{cc['iwd']*100:+.1f}" if cc.get("iwd") is not None else "—"
        alsa = f"{cc['alsa']:.1f}" if cc.get("alsa") else "—"
        tags = ", ".join(cc.get("tags", []) or [])
        out.append(f"| {mark(cc, tk['id'] if tk else None)} | {cc['name']} | {cc.get('color') or 'C'} "
                   f"| {pct(g(cc))} | {iwd} | {alsa} | {grade_of(cc)} | {tags} |")
    if len(p["offered"]) > 8:
        out.append(f"| | _+{len(p['offered'])-8} more_ | | | | | | |")
    out.append("")
    out.append(build_note(p))
    # what the taken card does
    if tk:
        t = text_of(tk)
        if t:
            out.append(f"\n> **{tk['name']}** — {t[:280]}")

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

dest = os.path.join(DATA, "drafts", f"{draft.get('set','draft')}-replay.md")
open(dest, "w").write("\n".join(out))
print("wrote", os.path.relpath(dest, HERE), f"({len(draft['picks'])} picks)")
