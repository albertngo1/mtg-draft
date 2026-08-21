#!/usr/bin/env python3
"""Build the static GitHub Pages site from the card-reference Markdown files.

Reads every ``card-reference/<SET>-card-reference.md`` on disk at build time and
emits a browsable site into ``docs/`` (the GitHub Pages source):

    docs/index.html          landing page — one card per set
    docs/sets/<SET>.html     that set's full reference
    docs/assets/site.css     styles  (copied from card-reference/site/)
    docs/assets/site.js      search + filters (copied from card-reference/site/)

Nothing is transcribed into this script: the Markdown is the single source of
truth, so re-running the build picks up any edit to those files.

    python3 card-reference/build_site.py            # -> ./docs
    python3 card-reference/build_site.py --out /tmp/preview

Standard library only, matching the rest of the repo.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REF_DIR = REPO / "card-reference"
GUIDE_DIR = REPO / "draft-guides" / "lords-of-limited"
TEMPLATE_DIR = REF_DIR / "site"

SITE_TITLE = "MTG Card Reference"
SITE_TAGLINE = (
    "Every draftable card in a set as a tile — the card image, its 17Lands "
    "win-rate numbers, an expert letter grade, notes distilled from the draft "
    "guides, and an AI take."
)
REPO_URL = "https://github.com/albertngo1/mtg-draft"

# Colour section -> CSS custom property used for the dot / accent.
SECTION_DOT = {
    "white": "var(--w)",
    "blue": "var(--u)",
    "black": "var(--b)",
    "red": "var(--r)",
    "green": "var(--g)",
    "multicolor": "var(--m)",
    "multicolour": "var(--m)",
    "colorless": "var(--c)",
    "colourless": "var(--c)",
    "lands": "var(--l)",
}
SECTION_ORDER = ["white", "blue", "black", "red", "green",
                 "multicolor", "colorless", "lands"]


# --------------------------------------------------------------------------
# Markdown -> HTML.  A deliberately small renderer for the exact subset that
# build_card_reference.py emits: ATX headings, paragraphs, blockquotes, GFM
# pipe tables, bullet/ordered lists, and raw HTML blocks passed straight
# through (that is how the card tiles arrive).
# --------------------------------------------------------------------------

def slug(text: str) -> str:
    """GitHub-style heading slug, so the file's own '#white' anchors work."""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text.strip())


_CODE_RE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)
_EM_RE = re.compile(r"(?<![\*\w])\*([^*\n]+?)\*(?!\*)")


def inline(text: str) -> str:
    """Inline markdown. Raw HTML in the source is intentionally left alone."""
    stash: list[str] = []

    def keep(match: re.Match) -> str:
        stash.append("<code>%s</code>" % html.escape(match.group(1), quote=False))
        return "\x00%d\x00" % (len(stash) - 1)

    text = _CODE_RE.sub(keep, text)
    text = _LINK_RE.sub(
        lambda m: '<a href="%s">%s</a>' % (html.escape(m.group(2), quote=True), m.group(1)),
        text,
    )
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = _EM_RE.sub(r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)


_DELIM_RE = re.compile(r"^\|?[\s:|-]+\|[\s:|-]*$")
_ITEM_RE = re.compile(r"^(\s*)(?:[-*+]|(\d+)\.)\s+(.*)$")


def _row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def render_markdown(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        # Raw HTML block: everything up to the next blank line, verbatim.
        if line.lstrip().startswith("<"):
            buf = []
            while i < n and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl, txt = len(m.group(1)), m.group(2).strip()
            out.append('<h%d id="%s">%s</h%d>' % (lvl, slug(txt), inline(txt), lvl))
            i += 1
            continue

        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % render_markdown("\n".join(buf)))
            continue

        # GFM pipe table: header row followed by a |---|---| delimiter.
        if line.lstrip().startswith("|") and i + 1 < n and _DELIM_RE.match(lines[i + 1].strip()):
            header = _row(line)
            i += 2
            body = []
            while i < n and lines[i].lstrip().startswith("|"):
                body.append(_row(lines[i]))
                i += 1
            cells = "".join("<th>%s</th>" % inline(c) for c in header)
            rows = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in body
            )
            out.append(
                '<div class="tablescroll"><table><thead><tr>%s</tr></thead>'
                "<tbody>%s</tbody></table></div>" % (cells, rows)
            )
            continue

        # List: consecutive item lines plus their lazy continuation lines.
        m = _ITEM_RE.match(line)
        if m:
            ordered = m.group(2) is not None
            items: list[list[str]] = []
            while i < n and lines[i].strip():
                mm = _ITEM_RE.match(lines[i])
                if mm:
                    items.append([mm.group(3)])
                elif items:
                    items[-1].append(lines[i].strip())
                else:
                    break
                i += 1
            tag = "ol" if ordered else "ul"
            body = "".join("<li>%s</li>" % inline(" ".join(p)) for p in items)
            out.append("<%s>%s</%s>" % (tag, body, tag))
            continue

        # Paragraph.
        buf = []
        while i < n and lines[i].strip() and not lines[i].lstrip().startswith(("#", ">", "|", "<")):
            buf.append(lines[i].strip())
            i += 1
        if not buf:                       # defensive: never spin on one line
            buf.append(lines[i].strip())
            i += 1
        text = " ".join(buf)
        cls = ' class="lede"' if text.startswith("*") and text.endswith("*") else ""
        out.append("<p%s>%s</p>" % (cls, inline(text)))

    return "\n".join(out)


# --------------------------------------------------------------------------
# Card tiles.  The Markdown holds them as a raw 3-per-row <table> of <td>
# cells; we re-emit each cell as a real element in a responsive CSS grid so
# the page can filter, search and reflow it.
# --------------------------------------------------------------------------

TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
TILE_RE = re.compile(
    r'^<img\s+src="([^"]+)"[^>]*alt="([^"]*)"[^>]*>(?:<br>)?'
    r"<b>(.*?)</b><br><sub>(.*?)</sub>(.*)$",
    re.S,
)
SUB_RE = re.compile(r"<sub>(.*?)</sub>", re.S)
STAT_KEYS = ("GIH", "OH", "IWD", "ALSA", "Play", "GD")


def _stat_chips(raw: str, primary: bool) -> str:
    chips = []
    for tok in raw.split("·"):
        tok = re.sub(r"<[^>]+>", "", tok).strip()
        if not tok or tok in {"—", "-"}:
            continue
        key, _, val = tok.partition(" ")
        if not val:
            key, val = "", tok
        cls = " class=\"gih\"" if key == "GIH" else ""
        chips.append(
            "<li%s><span class=\"k\">%s</span><span class=\"v\">%s</span></li>"
            % (cls, html.escape(key), html.escape(val))
        )
    if not chips:
        return ""
    return '<ul class="stats%s">%s</ul>' % ("" if primary else " sub", "".join(chips))


def render_tile(cell: str) -> str:
    m = TILE_RE.match(cell.strip())
    if not m:                       # unknown shape: keep the content, lose nothing
        return '<article class="tile"><div class="body">%s</div></article>' % cell

    img, alt, name, meta, rest = m.groups()

    parts = [p.strip() for p in meta.split("·")]
    colors = parts[0] if parts else ""
    rarity = parts[-1] if len(parts) > 1 else ""

    subs = list(SUB_RE.finditer(rest))
    stats, notes, ai_from = [], [], 0
    for idx, sub in enumerate(subs):
        text = sub.group(1)
        if not notes and text.split(" ")[0].strip("<b>") in STAT_KEYS:
            stats.append(text)
            ai_from = sub.end()
        else:
            notes.append(text)
    ai_to = subs[len(stats)].start() if len(subs) > len(stats) else len(rest)
    ai = rest[ai_from:ai_to].strip()
    ai = re.sub(r"^(?:<br>\s*)+", "", ai)
    ai = re.sub(r"(?:<br>\s*)+$", "", ai)

    pips = "".join(
        '<span class="pip pip-%s">%s</span>' % (c, c)
        for c in colors if c in "WUBRGC"
    )

    bits = ['<article class="tile" data-rarity="%s" data-name="%s">'
            % (html.escape(rarity.lower(), quote=True),
               html.escape(html.unescape(name).lower(), quote=True))]
    bits.append(
        '<a class="art" href="%s" target="_blank" rel="noopener">'
        '<img src="%s" alt="%s" loading="lazy" decoding="async"></a>'
        % (html.escape(img, quote=True), html.escape(img, quote=True), alt)
    )
    bits.append('<div class="body">')
    bits.append('<h3 class="cname">%s</h3>' % name)
    bits.append(
        '<p class="cmeta"><span class="pips">%s</span>'
        '<span class="rar rar-%s">%s</span></p>'
        % (pips, html.escape(rarity, quote=True), html.escape(rarity))
    )
    for idx, raw in enumerate(stats):
        bits.append(_stat_chips(raw, primary=(idx == 0)))
    if ai:
        bits.append('<p class="ai">%s</p>' % ai)
    if notes:
        label = "%d expert note%s" % (len(notes), "" if len(notes) == 1 else "s")
        bits.append(
            '<details class="notes"><summary>%s</summary>%s</details>'
            % (label, "".join('<p class="note">%s</p>' % t for t in notes))
        )
    bits.append("</div></article>")
    return "".join(bits)


def render_grid(block: str) -> tuple[str, int]:
    cells = TD_RE.findall(block)
    tiles = "".join(render_tile(c) for c in cells)
    return '<div class="grid">%s</div>' % tiles, len(cells)


# --------------------------------------------------------------------------
# Parsing one <SET>-card-reference.md into the pieces the page needs.
# --------------------------------------------------------------------------

def set_display_name(code: str) -> str:
    """Full set name, read out of the Lords of Limited draft guide if present."""
    guide = GUIDE_DIR / ("%s-draft-guide.md" % code)
    if not guide.exists():
        return ""
    first = guide.read_text(encoding="utf-8").split("\n", 1)[0].lstrip("# ").strip()
    m = re.match(r"^(.+?)\s*\(%s\)" % re.escape(code), first)
    if m:
        return m.group(1).strip()
    m = re.match(r"^%s\s*[—:-]\s*(.+?)(?:\s*\(.*)?$" % re.escape(code), first)
    if m:
        return m.group(1).strip()
    return ""


def parse_set(path: Path) -> dict:
    code = path.name.split("-")[0]
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")

    title = lines[0].lstrip("# ").strip() if lines else code

    # Split: front matter (up to '## Contents') / sections (after it).
    contents_at = next(
        (i for i, l in enumerate(lines) if l.strip().lower().startswith("## contents")),
        None,
    )
    if contents_at is None:
        contents_at = next((i for i, l in enumerate(lines) if re.match(r"^## \w", l)), len(lines))
    front = lines[1:contents_at]
    # Skip the Contents list itself; sections start at the next '## '.
    rest_start = next(
        (i for i in range(contents_at + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    body = lines[rest_start:]

    # Front matter splits again at its first sub-heading: everything before is
    # the page lede/caveat, everything after is the (collapsible) format brief.
    brief_at = next((i for i, l in enumerate(front) if re.match(r"^#{2,3} \w", l)), len(front))
    hero_md = "\n".join(front[:brief_at]).strip()
    brief_md = "\n".join(front[brief_at:]).strip()
    # Not every set has the long-form "## Format brief" essay; some only carry
    # the archetype table. Label the section for what is actually there.
    has_brief = any(l.lower().startswith("## format brief") for l in front)

    # Sections: '## Name' followed by the raw card-tile <table>.
    sections = []
    cur_name, cur_buf = None, []

    def flush():
        if cur_name is None:
            return
        chunk = "\n".join(cur_buf)
        grid, count = render_grid(chunk)
        sections.append({
            "name": cur_name,
            "id": slug(cur_name),
            "html": grid,
            "count": count,
            "dot": SECTION_DOT.get(cur_name.lower(), "var(--text-3)"),
        })

    for line in body:
        if line.startswith("## "):
            flush()
            cur_name, cur_buf = line[3:].strip(), []
        elif cur_name is not None:
            cur_buf.append(line)
    flush()

    total = sum(s["count"] for s in sections)

    # Cheap facts for the landing page, all pulled out of the file itself.
    lede = next((l for l in front if l.strip().startswith("*") and "draftable" in l), "")
    grade_src = ""
    m = re.search(r"17Lands ratings,\s*(.+?),\s*expert-guide notes", lede)
    if m:
        grade_src = m.group(1).strip()
    legend = next((l for l in front if l.strip().startswith("**Legend**")), "")
    guides = re.findall(r"[·—]\s*(?:\S{1,2}\s+)?((?:[A-Z][\w.\-']*\s?)+)", legend.split(".")[-1])
    guides = [g.strip() for g in guides if g.strip() and g.strip() != "AI"]

    return {
        "code": code,
        "name": set_display_name(code),
        "title": title,
        "hero_html": render_markdown(hero_md),
        "brief_html": render_markdown(brief_md),
        "brief_words": len(brief_md.split()),
        "has_brief": has_brief,
        "sections": sections,
        "total": total,
        "grade_src": grade_src,
        "guides": guides,
        "mtime": dt.datetime.fromtimestamp(path.stat().st_mtime),
        "bytes": path.stat().st_size,
    }


# --------------------------------------------------------------------------
# Page templates.
# --------------------------------------------------------------------------

SEARCH_SVG = ('<svg width="13" height="13" viewBox="0 0 16 16" fill="none" '
              'stroke="currentColor" stroke-width="1.8" aria-hidden="true">'
              '<circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5 14.5 14.5"/></svg>')


def shell(title: str, head_extra: str, body: str, depth: int) -> str:
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(SITE_TAGLINE)}">
<meta name="color-scheme" content="dark">
<link rel="stylesheet" href="{up}assets/site.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22><rect width=%2216%22 height=%2216%22 rx=%223%22 fill=%22%230a0c10%22/><rect x=%224%22 y=%223%22 width=%228%22 height=%2210%22 rx=%221.5%22 fill=%22%23d8b46a%22/></svg>">
{head_extra}</head>
<body>
{body}
<a class="totop" href="#top" aria-label="Back to top">&uarr;</a>
<script src="{up}assets/site.js" defer></script>
</body>
</html>
"""


def footer(depth: int) -> str:
    up = "../" * depth
    return f"""<footer class="foot"><div class="wrap">
<p>Generated from the Markdown in <a href="{REPO_URL}/tree/main/card-reference"><code>card-reference/</code></a>
by <code>build_site.py</code> — rebuild with <code>python3 card-reference/build_site.py</code>.</p>
<p>Card images are hotlinked from <a href="https://scryfall.com/">Scryfall</a> and TCGplayer; win-rate data from
<a href="https://www.17lands.com/">17Lands</a>. Magic: The Gathering is &copy; Wizards of the Coast — an
unofficial fan project, not affiliated with or endorsed by Wizards.</p>
<p><a href="{up}index.html">All sets</a> &middot; <a href="{REPO_URL}">mtg-draft on GitHub</a></p>
</div></footer>"""


def render_index(sets: list[dict]) -> str:
    total_cards = sum(s["total"] for s in sets)
    briefs = sum(1 for s in sets if s["has_brief"])

    cards = []
    for s in sets:
        by = {sec["id"]: sec for sec in s["sections"]}
        segs, key = [], []
        for name in SECTION_ORDER:
            sec = by.get(name)
            if not sec or not sec["count"]:
                continue
            pct = 100.0 * sec["count"] / max(s["total"], 1)
            segs.append('<span style="width:%.2f%%;background:%s"></span>' % (pct, sec["dot"]))
        tags = []
        if s["grade_src"]:
            tags.append('<span class="tag">%s</span>' % html.escape(s["grade_src"]))
        if s["has_brief"]:
            tags.append('<span class="tag on">Format brief</span>')
        elif s["brief_html"]:
            tags.append('<span class="tag">Archetype guide</span>')
        tags.append('<span class="tag">%d sections</span>' % len(s["sections"]))

        cards.append(f"""<a class="setcard" href="sets/{s['code']}.html">
  <div class="row"><span class="code">{s['code']}</span><span class="cards">{s['total']} cards</span></div>
  <p class="sub">{html.escape(s['name'] or 'Draft set reference')}</p>
  <div class="bar">{''.join(segs)}</div>
  <div class="tags">{''.join(tags)}</div>
</a>""")

    body = f"""<header class="topbar" id="top"><div class="wrap">
  <span class="brand"><span class="pipmark">&#9670;</span>{SITE_TITLE}</span>
  <div class="toolbar"><a class="crumb" href="{REPO_URL}">GitHub &#8599;</a></div>
</div></header>

<main class="wrap">
  <section class="hero">
    <h1>Every card in the set,<br><span class="accent">ranked and annotated.</span></h1>
    <p class="lede">{SITE_TAGLINE}</p>
    <div class="statline">
      <div><span class="n">{len(sets)}</span><span class="k">sets</span></div>
      <div><span class="n">{total_cards:,}</span><span class="k">card tiles</span></div>
      <div><span class="n">{briefs}</span><span class="k">format briefs</span></div>
    </div>
  </section>

  <p class="section-label">Choose a set</p>
  <div class="setgrid">{''.join(cards)}</div>

  <p class="section-label">How to read a tile</p>
  <div class="prose">
    <p><strong>GIH</strong> — games-in-hand win rate, the primary signal.
       <strong>IWD</strong> — improvement when drawn, in percentage points.
       <strong>ALSA</strong> — average last seen at, so lower means the card is taken earlier.
       <strong>OH / GD</strong> — opening-hand and drawn win rates. <strong>Play</strong> — play rate.
       The letter grade beside them comes from a pre-data expert review, so where a grade and a win
       rate disagree, the win rate is the result and the grade was the prediction.</p>
    <p>A win rate is the win rate of <em>the decks that drafted the card</em>, not a context-free
       score — build-around payoffs post their deck's number. The AI take and the expert notes on
       each tile exist to say which deck a number belongs to.</p>
    <p>On a set page, type to search across names, stats and every note; <kbd>/</kbd> focuses the
       box and <kbd>Esc</kbd> clears it.</p>
  </div>
</main>
{footer(0)}"""
    return shell(SITE_TITLE, "", body, depth=0)


def render_set(s: dict) -> str:
    jump = "".join(
        '<a href="#%s" data-c="1" style="--dot:%s">%s<b>%d</b></a>'
        % (sec["id"], sec["dot"], html.escape(sec["name"]), sec["count"])
        for sec in s["sections"]
    )
    brief_title = ("Format brief &mdash; archetypes, draft plan, deckbuilding"
                   if s["has_brief"] else "Archetypes &amp; format notes")
    if s["brief_html"]:
        jump = '<a href="#brief">%s</a>' % ("Format brief" if s["has_brief"] else "Archetypes") + jump

    sections = "".join(
        f"""<section class="cardsection" id="{sec['id']}" data-total="{sec['count']}" style="--dot:{sec['dot']}">
  <h2 id="{sec['id']}-h">{html.escape(sec['name'])}<span class="n">{sec['count']}</span></h2>
  {sec['html']}
</section>"""
        for sec in s["sections"]
    )

    brief = ""
    if s["brief_html"]:
        brief = f"""<details class="brief" id="brief">
  <summary>{brief_title}
    <span class="hint">{s['brief_words']:,} words</span></summary>
  <div class="briefbody prose">{s['brief_html']}</div>
</details>"""

    chips = "".join(
        '<button class="chip" data-rarity="%s" aria-pressed="false">%s</button>' % (r.lower(), r)
        for r in ("Common", "Uncommon", "Rare", "Mythic")
    )

    name = s["name"] or ""
    body = f"""<header class="topbar" id="top"><div class="wrap">
  <span class="brand"><a href="../index.html"><span class="pipmark">&#9670;</span>{SITE_TITLE}</a></span>
  <span class="setbadge">{s['code']}</span>
  <div class="toolbar">
    <label class="search">{SEARCH_SVG}<input id="q" type="search" placeholder="Search cards, stats, notes&hellip;" autocomplete="off" spellcheck="false"></label>
    <div class="chips">{chips}</div>
    <span class="count" id="count">{s['total']} cards</span>
  </div>
</div></header>
<nav class="jump"><div class="wrap">{jump}</div></nav>

<main class="wrap">
  <section class="sethead">
    <h1>{s['code']}{' &middot; ' + html.escape(name) if name else ''}</h1>
    <div class="prose">{s['hero_html']}</div>
    {brief}
  </section>
  {sections}
  <p class="empty">No cards match that search.</p>
</main>
{footer(1)}"""
    title = "%s — %s" % (s["code"], SITE_TITLE)
    return shell(title, "", body, depth=1)


# --------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(REPO / "docs"), help="output directory (default ./docs)")
    ap.add_argument("--ref-dir", default=str(REF_DIR), help="folder holding *-card-reference.md")
    args = ap.parse_args()

    ref_dir = Path(args.ref_dir)
    out = Path(args.out)
    files = sorted(ref_dir.glob("*-card-reference.md"))
    if not files:
        raise SystemExit("no *-card-reference.md files in %s" % ref_dir)

    (out / "sets").mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    for asset in ("site.css", "site.js"):
        shutil.copyfile(TEMPLATE_DIR / asset, out / "assets" / asset)
    # Serve the files as-is: no Jekyll pass, no underscore-folder surprises.
    (out / ".nojekyll").write_text("", encoding="utf-8")

    sets = []
    for path in files:
        s = parse_set(path)
        (out / "sets" / ("%s.html" % s["code"])).write_text(render_set(s), encoding="utf-8")
        sets.append(s)
        print("  %-4s %3d cards, %d sections -> sets/%s.html"
              % (s["code"], s["total"], len(s["sections"]), s["code"]))

    (out / "index.html").write_text(render_index(sets), encoding="utf-8")
    print("built %d sets, %d card tiles -> %s"
          % (len(sets), sum(s["total"] for s in sets), out))


if __name__ == "__main__":
    main()
