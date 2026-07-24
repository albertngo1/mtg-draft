#!/usr/bin/env python3
"""Deterministic prep + merge for the AI-takes generation pass (see AI_TAKES_PLAYBOOK.md).

The *creative* step — writing each card's take — is done by fanning the chunks out to
parallel analyst agents under a per-set doctrine. This script handles only the mechanical
ends so they are byte-for-byte identical across sets:

  prep  <SET> <out_dir> [N]   dump per-card context (stats + grade + all guide notes),
                              split into N chunks (default 12) at <out_dir>/chunk_NN.json
  merge <SET> <results_dir>   merge <results_dir>/chunk_*.json into
                              card-reference/ai_takes_<SET>.json, keyed + ordered to the
                              real card list; reports any missing / extra names.

Usage:
  python3 gen_ai_takes.py prep  MSH /path/to/scratch/chunks 12
  # ...fan chunks out to analyst agents, each writes /path/to/scratch/results/chunk_NN.json...
  python3 gen_ai_takes.py merge MSH /path/to/scratch/results
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.split("//")[0].lower())

# ---- guide parsing: identical to build_card_reference.py --------------------
# Card name in bold, optionally linked, optionally followed by one-or-more parentheticals
# (scryfall link AND a mana/reminder gloss — LoL's `[**Card**](url) (4WW: …) — note` form),
# then the note. Separator optional so Numot's `**Card:** note` (colon inside bold) parses too.
BULLET = re.compile(r"^\s*-\s*\[?\*\*(.+?):?\*\*\]?(?:\s*\([^)]*\))*\s*[—–:-]?\s*(.+?)\s*$")
TABLE  = re.compile(r"^\s*\|\s*\[?\*\*(.+?)\*\*\]?[^|]*\|\s*(.+?)\s*\|")
def parse_guide(path):
    notes = {}
    if not os.path.exists(path):
        return notes
    insec = False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            insec = ("card tip" in line.lower()) or ("card note" in line.lower())
            continue
        if not insec:
            continue
        m = BULLET.match(line) or TABLE.match(line)
        if not m:
            continue
        raw, note = m.group(1), m.group(2).strip()
        names = [raw.split("(")[0]] + re.findall(r"\(([^)]+)\)", raw)
        if not note:
            continue
        for nm in names:
            k = norm(nm)
            if k and k not in notes:
                notes[k] = note
    return notes

# guide dir, filename pattern, label — keep in sync with build_card_reference.py
GUIDES = [
    ("LoL",   "lords-of-limited",  "{SET}-draft-guide.md"),
    ("Numot", "numot",             "{SET}.md"),
    ("LR",    "limited-resources", "{SET}.md"),
    ("LLU",   "limited-level-ups", "{SET}.md"),
]

def load_cards(SET):
    return json.load(open(f"{ROOT}/data/cache/17lands_{SET}_PremierDraft_1200d.json"))

def load_scry():
    """Scryfall cache keyed by mtga_id (string) — carries oracle `text`, `pt`, `mana`, `type_line`.
    Joined into the prep record so the analyst agents READ what each card does, not just its stats."""
    p = f"{ROOT}/data/cache/scryfall_arena.json"
    return json.load(open(p)) if os.path.exists(p) else {}

def load_grades(SET):
    for src in ("draftsim", "cardgamebase"):
        p = f"{ROOT}/grades/{src}_{SET}.json"
        if os.path.exists(p):
            label = "DS" if src == "draftsim" else "CGB"
            return label, {norm(k): v for k, v in json.load(open(p)).items()
                           if not k.startswith("_")}
    return "", {}

def pct(x):    return f"{x*100:.1f}%" if x else None
def signed(x): return f"{x*100:+.1f}" if x else None

def prep(SET, out_dir, N):
    cards = load_cards(SET)
    glabel, grades = load_grades(SET)
    scry = load_scry()
    guides = [(lab, parse_guide(f"{ROOT}/draft-guides/{d}/{f.format(SET=SET)}"))
              for lab, d, f in GUIDES]
    out = []
    for c in cards:
        k = norm(c["name"])
        meta = scry.get(str(c.get("mtga_id")), {})
        rec = {
            "name": c["name"],
            "color": c["color"] or "C",
            "rarity": c["rarity"],
            "mana": meta.get("mana") or None,               # mana cost, e.g. "{2}{U}"
            "type_line": meta.get("type_line") or None,
            "types": c.get("types"),
            "pt": meta.get("pt") or None,                   # power/toughness for creatures
            "text": (meta.get("text") or "").strip() or None,  # ORACLE TEXT — read what the card DOES
            "gih_wr": pct(c.get("ever_drawn_win_rate")),
            "iwd": signed(c.get("drawn_improvement_win_rate")),
            "alsa": round(c["avg_seen"], 1) if c.get("avg_seen") else None,
            "oh_wr": pct(c.get("opening_hand_win_rate")),
            "gd_wr": pct(c.get("drawn_win_rate")),
            "play_rate": pct(c.get("play_rate")),
            f"{glabel.lower()}_grade": grades.get(k),
            "notes": {lab: g[k] for lab, g in guides if g.get(k)},
        }
        out.append(rec)
    os.makedirs(out_dir, exist_ok=True)
    chunks = [[] for _ in range(N)]
    for i, r in enumerate(out):
        chunks[i % N].append(r)
    for i, ch in enumerate(chunks):
        json.dump(ch, open(f"{out_dir}/chunk_{i:02d}.json", "w"),
                  ensure_ascii=False, indent=1)
    print(f"prep {SET}: {len(out)} cards | grade={glabel} "
          f"({sum(1 for r in out if r.get(glabel.lower()+'_grade'))}) "
          f"| GIH WR ({sum(1 for r in out if r['gih_wr'])}) "
          f"| oracle text ({sum(1 for r in out if r['text'])}) "
          f"| >=1 note ({sum(1 for r in out if r['notes'])}) "
          f"| {N} chunks -> {out_dir}")

def merge(SET, results_dir):
    import glob
    merged = {}
    for f in sorted(glob.glob(f"{results_dir}/chunk_*.json")):
        merged.update(json.load(open(f)))
    names = [c["name"] for c in load_cards(SET)]
    missing = [n for n in names if n not in merged]
    extra   = [k for k in merged if k not in set(names)]
    out = {n: merged[n] for n in names if n in merged}
    dest = f"{HERE}/ai_takes_{SET}.json"
    json.dump(out, open(dest, "w"), ensure_ascii=False, indent=1)
    avg = round(sum(len(v.split()) for v in out.values()) / max(len(out), 1), 1)
    print(f"merge {SET}: wrote {len(out)}/{len(names)} takes -> {dest} | avg {avg} words")
    if missing: print(f"  MISSING ({len(missing)}): {missing}")
    if extra:   print(f"  EXTRA (dropped, not draftable) ({len(extra)}): {extra[:10]}")
    if missing: sys.exit(1)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "prep":
        prep(sys.argv[2].upper(), sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 12)
    elif cmd == "merge":
        merge(sys.argv[2].upper(), sys.argv[3])
    else:
        print(__doc__); sys.exit(1)
