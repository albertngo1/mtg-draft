#!/usr/bin/env python3
"""Ingest Untapped.gg limited card data into grades/untapped_<SET>.json.

Untapped tiers cards by "In-Hand WR" — the same metric as 17Lands GIH WR
(empirically: rho=0.955, mean |dWR|=1.8pts vs 17Lands same-format; see AGENTS.md).
So this is a *second empirical sample*, not a new signal — useful as a small-N
consensus check, not an independent lens. (Draftsim is the orthogonal/theory source.)

Input: a captured network artifact. Untapped's own page never exposes card NAMES
in its stats API (everything is keyed by an internal `title_id`); the name map lives
in the Next.js page-data blob `.../card-data.json`. So this reads either:
  - a HAR file that contains a (non-empty) card-data.json response, OR
  - that card-data.json saved directly (recommended; see "Refresh" below).

The artifact carries three pieces we join:
  minifiedMtgaJsonData.cardData  rows: [arena_grpId, title_id, ...]   (col0, col1)
  minifiedMtgaJsonData.localeData      [title_id, "Card Name"]        -> names
  limitedCardStatsResp.data.data[title_id].ALL.{b,s,g,p} -> stat arrays
Stat array schema (metadata.fields): group[1] = [available_games, available_wins];
In-Hand WR = sum(available_wins)/sum(available_games) over rank brackets.

Refresh (when card-data.json in a HAR is a cached 304/empty, fetch it once — this is a
single JSON API call, not browser scraping):
  curl -s 'https://mtga.untapped.gg/_next/data/<BUILD_ID>/limited/draft/<set-slug>/card-data.json' -o cd.json
The <BUILD_ID> is in any HAR's _next/data URLs (e.g. njRUYt-sxok7uweDzfOYb).

Usage:
  python3 ingest_untapped.py <card-data.json | something.har> [--set SOS]
"""
import json
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _extract_pageprops(raw):
    """Return the ssrProps dict from either a card-data.json or a HAR."""
    obj = json.loads(raw)
    # direct card-data.json
    if isinstance(obj, dict) and obj.get("pageProps", {}).get("ssrProps"):
        return obj["pageProps"]["ssrProps"]
    # HAR: find an entry whose body parses to a card-data.json with names
    if isinstance(obj, dict) and "log" in obj:
        for e in obj["log"]["entries"]:
            if "card-data.json" not in e["request"]["url"]:
                continue
            txt = e["response"]["content"].get("text") or ""
            if len(txt) < 1000:
                continue  # cached 304 / empty
            sp = json.loads(txt).get("pageProps", {}).get("ssrProps")
            if sp and sp.get("minifiedMtgaJsonData", {}).get("localeData"):
                return sp
    raise SystemExit(
        "No usable card-data.json found. If you passed a HAR whose card-data.json "
        "was a cached 304 (empty), fetch it fresh — see the 'Refresh' note in this file's docstring."
    )


def ihwr(rec):
    """In-Hand WR from a stats record: avail_wins/avail_games over rank brackets."""
    ag = aw = 0
    for _agg, brackets in rec.items():          # _agg == "ALL"
        for _rank, groups in brackets.items():  # b/s/g/p
            if len(groups) > 1 and len(groups[1]) >= 2:
                ag += groups[1][0]
                aw += groups[1][1]
    return (aw / ag * 100.0, ag) if ag else (None, 0)


def main():
    args = [a for a in sys.argv[1:]]
    set_code = "SOS"
    if "--set" in args:
        i = args.index("--set")
        set_code = args[i + 1]
        del args[i:i + 2]
    if not args:
        raise SystemExit(__doc__)
    src = args[0]

    with open(src) as f:
        sp = _extract_pageprops(f.read())

    cd = sp["minifiedMtgaJsonData"]["cardData"]
    loc = dict(sp["minifiedMtgaJsonData"]["localeData"])
    stats = sp["limitedCardStatsResp"]["data"]["data"]
    fmt = sp.get("clientProps", {}).get("limitedFormat") or \
        sp.get("limitedCardStatsRespUrl", "")

    out = {}
    for row in cd:
        arena, title_id = row[0], row[1]
        name = loc.get(title_id)
        key = str(title_id)
        if key in stats and name:
            wr, n = ihwr(stats[key])
            if wr and n >= 200:          # drop ultra-thin samples
                out[name] = round(wr, 1)

    payload = {
        "_source": (
            "Untapped.gg limited card-data (In-Hand WR, Premier Draft). "
            "Empirically redundant with 17Lands GIH WR (rho=0.955); kept as a "
            "second-sample consensus check. Value = In-Hand WR %%. Ingested from %s."
            % os.path.basename(src)
        ),
        "_format": str(fmt),
    }
    payload.update(dict(sorted(out.items())))

    dst = os.path.join(HERE, "grades", "untapped_%s.json" % set_code)
    with open(dst, "w") as f:
        json.dump(payload, f, indent=0)
    print("wrote %d cards -> %s" % (len(out), dst))


if __name__ == "__main__":
    main()
