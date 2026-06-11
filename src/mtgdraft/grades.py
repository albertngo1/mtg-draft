import os, json, re
from .config import GRADES, GUIDES

def load_grades(source, set_code):
    """External reviewer grades (e.g. draftsim) keyed by lowercased card name.
    Returns {} if the file doesn't exist. Files live in grades/<source>_<SET>.json."""
    try:
        with open(os.path.join(GRADES, f"{source}_{set_code}.json")) as f:
            d = json.load(f)
        out = {}
        for k, v in d.items():
            if k.startswith("_"):
                continue
            out[k.lower()] = v
            if "//" in k:                       # split/MDFC: also key by front face, the name the pool stores
                out[k.split("//")[0].strip().lower()] = v
        return out
    except Exception:
        return {}
_GRADE_SOURCES = [("draftsim", "DS"), ("cardgamebase", "CGB"), ("limitedgrades", "LG")]
def load_grades_any(set_code):
    """Load whichever reviewer-grade file exists for this set (first match wins).
    Returns (grades_dict, column_label). ({}, '') if none cached."""
    for source, label in _GRADE_SOURCES:
        g = load_grades(source, set_code)
        if g:
            return g, label
    return {}, ""
_GUIDE_NOTE_RX = re.compile(r"^\s*-\s*\*\*(.+?)\*\*\s*[—–-]\s*(.+?)\s*$")
# Table form `| **Card** (parenthetical) | take | source |` — col1 bolded name, col2 the note.
# (SOS and other guides put their Card-notes section in a per-color table, not bullets.)
_GUIDE_TABLE_RX = re.compile(r"^\s*\|\s*\*\*(.+?)\*\*[^|]*\|\s*(.+?)\s*\|")
def load_guide_notes(set_code):
    """Per-card expert notes from draft-guides/lords-of-limited/<SET>-draft-guide.md's '## Card notes' section.
    Reads BOTH bullet rows (`- **Card** — note`) and table rows (`| **Card** | note | … |`); a guide may
    use either format. Keyed by lowercased card name (+ split-card front face). Returns {} if no guide.
    Expert opinion — the lead lens that decodes archetype-conditional 17Lands WR (see AGENTS.md)."""
    notes = {}
    try:
        in_section = False
        with open(os.path.join(GUIDES, f"{set_code}-draft-guide.md"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("## "):
                    in_section = "card note" in line.lower()
                    continue
                if not in_section:
                    continue
                m = _GUIDE_NOTE_RX.match(line) or _GUIDE_TABLE_RX.match(line)
                if m:
                    name, note = m.group(1).split("(")[0].strip(), m.group(2).strip()
                    if not name or not note:
                        continue
                    notes[name.lower()] = note
                    if "//" in name:                    # split/MDFC: also key by front face
                        notes[name.split("//")[0].strip().lower()] = note
    except Exception:
        pass
    return notes
