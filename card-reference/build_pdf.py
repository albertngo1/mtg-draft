#!/usr/bin/env python3
"""Render a <SET>-card-reference.md into a print-ready PDF via headless Chrome.
Usage: /tmp/venv/bin/python build_pdf.py SET [out_dir]
  (needs the `markdown` lib — run under the venv at /tmp/venv)
PDFs are written to out_dir (default ~/media) to avoid bloating the git repo with binaries.
"""
import sys, os, subprocess, markdown

SET = (sys.argv[1] if len(sys.argv) > 1 else "SOS").upper()
HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2 else "~/media")
SRC = os.path.join(HERE, f"{SET}-card-reference.md")
HTML = f"/tmp/{SET}-card-reference.html"
PDF = os.path.join(OUTDIR, f"{SET}-card-reference.pdf")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: letter landscape; margin: 0.4in; }
* { box-sizing: border-box; }
body { font-family: -apple-system, Helvetica, Arial, sans-serif; font-size: 11px; color:#111; line-height:1.35; }
h1 { font-size: 23px; margin: 0 0 6px; }
h2 { font-size: 17px; border-bottom: 2px solid #333; padding-bottom: 3px; margin: 22px 0 8px;
     page-break-after: avoid; }
p { margin: 4px 0; }
blockquote { background:#f5f5f5; border-left:3px solid #888; padding:4px 10px; margin:6px 0; }
ul { margin: 4px 0; columns: 3; }
table { width: 100%; border-collapse: collapse; margin: 6px 0; table-layout: fixed; }
td { width: 33.33%; border: 1px solid #ddd; padding: 7px; vertical-align: top;
     page-break-inside: avoid; }
tr { page-break-inside: avoid; }
img { width: 240px; max-width: 100%; height: auto; border-radius: 8px; }
sub { font-size: 10px; color: #333; line-height: 1.3; }
b { color:#000; }
a { color:#1a5; text-decoration: none; }
"""

body = markdown.markdown(open(SRC, encoding="utf-8").read(),
                         extensions=["tables", "sane_lists"])
html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
open(HTML, "w", encoding="utf-8").write(html)

os.makedirs(OUTDIR, exist_ok=True)
if os.path.exists(PDF):
    os.remove(PDF)
cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
       "--virtual-time-budget=180000", f"--print-to-pdf={PDF}", f"file://{HTML}"]
print("rendering", SET, "->", PDF, "(loading remote card images, ~3-5 min)...")
# Chrome --headless=new sometimes doesn't self-terminate after writing the PDF;
# it flushes the file near the end of virtual time, so we kill it once the PDF lands.
try:
    subprocess.run(cmd, capture_output=True, text=True, timeout=420)
except subprocess.TimeoutExpired:
    pass
if os.path.exists(PDF) and open(PDF, "rb").read()[-8:].rstrip().endswith(b"%%EOF"):
    print(f"OK  {PDF}  ({os.path.getsize(PDF)/1e6:.1f} MB)")
else:
    print(f"FAILED — PDF missing or truncated: {PDF}")
