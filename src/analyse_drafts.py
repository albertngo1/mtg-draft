#!/usr/bin/env python3
"""Pick-order analysis over 17Lands trophy drafts.

17Lands hides WHICH card a non-owner took (`pick` is null) but publishes every PACK and
the final pool. That is enough: assign each pick to one pool card drawn from its own
pack so the whole assignment is a perfect matching, and any edge present in EVERY
perfect matching is provably the real pick. Typically ~2/3 of picks resolve, and the
early picks — the informative ones — resolve almost always, because a large pack
intersected with a 42-card pool leaves little slack.

What that buys, which a sealed pool cannot answer:

  wheeling     a card seen at pick n and still there at n+8 went around the table.
               Measured off the packs alone, so it needs no pick recovery at all —
               this is the cleanest read of what the field systematically underrates.
  commitment   on-colour rate by pick number, against the deck they registered. Read
               this with care: the final colours ARE largely chosen by the early picks,
               so a high early number is partly circular. The informative parts are the
               DIPS — a pick they took off-colour is a speculative or hate pick — and
               the late-pack collapse, where picks are throwaways.
  passed       for a determined pick, the best card left behind. Mythic players' own
               errors, at scale.

Usage:
  python3 src/analyse_drafts.py --set HOB --format PremierDraft --rank mythic
"""
import argparse, collections, glob, json, os, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "cache")
sys.path.insert(0, os.path.join(ROOT, "src"))
import sealed_algo as A          # noqa: E402  (pips/castable/is_land/BASIC)

POD = 8                          # seats, so a card wheels 8 picks later


def load(expansion, fmt, rank):
    d = os.path.join(CACHE, "drafts", f"{expansion}_{fmt}_{rank}")
    for f in sorted(glob.glob(os.path.join(d, "*.draft.json"))):
        aid = os.path.basename(f).split(".")[0]
        deck = glob.glob(os.path.join(d, f"{aid}_*.deck.json"))
        if not deck:
            continue
        try:
            dr, ev = json.load(open(f)), json.load(open(deck[0]))
        except Exception:
            continue
        if not dr.get("picks") or not ev.get("pool"):
            continue
        yield aid, dr, ev


def reconstruct(dr, ev):
    """{pick index: card name} for every pick that is provably determined."""
    cards = ev["cards"]
    pool = [cards[str(i)]["name"] for i in ev["pool"] if str(i) in cards]
    picks = dr["picks"]
    if len(pool) != len(picks):
        return {}
    slots, idx = [], {}
    for name, q in collections.Counter(pool).items():
        for k in range(q):
            idx[(name, k)] = len(slots)
            slots.append((name, k))
    adj = [[idx[s] for s in slots if s[0] in {c["name"] for c in x["available"]}]
           for x in picks]
    n = len(picks)

    def match(skip=None):
        to = [-1] * len(slots)

        def aug(u, seen):
            for v in adj[u]:
                if skip == (u, v) or v in seen:
                    continue
                seen.add(v)
                if to[v] == -1 or aug(to[v], seen):
                    to[v] = u
                    return True
            return False
        return sum(aug(u, set()) for u in range(n)), to

    size, to = match()
    if size < n:
        return {}
    out = {}
    for v, u in enumerate(to):
        if u != -1 and match(skip=(u, v))[0] < n:
            out[u] = slots[v][0]     # this edge is in every perfect matching
    return out


def deck_colors_of(ev, db, text):
    cards = ev["cards"]
    md = [cards[str(i)]["name"] for i in ev["decks"][0]["groups"][0]["cards"]
          if str(i) in cards]
    return A.deck_colors(md, db, text) if len(md) == 40 else (set(), set())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="expansion", required=True)
    ap.add_argument("--format", default="PremierDraft")
    ap.add_argument("--rank", default="mythic")
    a = ap.parse_args()
    db = json.load(open(os.path.join(CACHE, f"carddb_{a.expansion}.json")))
    text = A._oracle(a.expansion)
    # Card power for a DRAFT must come from draft data — the sealed trophy scores are
    # a different format with a different metagame. 17Lands' own PremierDraft file is
    # the right source, and /data/draft even ships card_performance_data inline.
    stat_fmt = a.format if a.format in ("PremierDraft", "TradDraft", "QuickDraft") else "Sealed"
    gih = {}
    for days in ("120d", "1200d"):
        f = os.path.join(CACHE, f"17lands_{a.expansion}_{stat_fmt}_{days}.json")
        if os.path.exists(f):
            for c in json.load(open(f)):
                if c.get("ever_drawn_win_rate"):
                    gih.setdefault(c["name"], c["ever_drawn_win_rate"])
            break
    sc = {k: {"gih": v} for k, v in gih.items()}
    print(f"card win rates from 17lands_{a.expansion}_{stat_fmt} ({len(sc)} cards)")

    seen_early = collections.Counter()   # card offered at pick <= 5
    wheeled = collections.Counter()      # ...and still there 8 picks later
    oncolour = collections.defaultdict(lambda: [0, 0])   # pick -> [on, total]
    passed_best = []
    ndrafts = det_tot = pick_tot = 0
    for aid, dr, ev in load(a.expansion, a.format, a.rank):
        ndrafts += 1
        picks = dr["picks"]
        det = reconstruct(dr, ev)
        det_tot += len(det)
        pick_tot += len(picks)
        by_pp = {(x["pack_number"], x["pick_number"]): i for i, x in enumerate(picks)}
        for i, x in enumerate(picks):
            p, k = x["pack_number"], x["pick_number"]
            names = [c["name"] for c in x["available"]]
            if k <= 5:
                later = by_pp.get((p, k + POD))
                if later is not None:
                    back = {c["name"] for c in picks[later]["available"]}
                    for nm in set(names):
                        if nm in A.BASIC:
                            continue          # basics always wheel; they are not a signal
                        seen_early[nm] += 1
                        if nm in back:
                            wheeled[nm] += 1
        main_c, _ = deck_colors_of(ev, db, text)
        if main_c:
            for i, nm in det.items():
                x = picks[i]
                if nm in A.BASIC or nm not in db:
                    continue
                slot = x["pack_number"] * 14 + x["pick_number"]
                oncolour[slot][1] += 1
                if A.castable(db[nm], main_c):
                    oncolour[slot][0] += 1
                # best on-colour card left behind
                left = [c["name"] for c in x["available"] if c["name"] != nm
                        and c["name"] in sc and c["name"] in db
                        and A.castable(db[c["name"]], main_c)]
                if left and nm in sc:
                    best = max(left, key=lambda c: sc[c]["gih"])
                    if sc[best]["gih"] - sc[nm]["gih"] > 0.02:
                        passed_best.append((sc[best]["gih"] - sc[nm]["gih"], best, nm))

    print(f"=== {ndrafts} {a.rank} {a.expansion} {a.format} trophy drafts ===")
    if not ndrafts:
        return 1
    print(f"picks provably recovered: {det_tot}/{pick_tot} ({100*det_tot/pick_tot:.0f}%)\n")

    floor = max(20, ndrafts // 4)     # scale the sample floor with the corpus
    rows = [(wheeled[c] / v, v, c, sc.get(c, {}).get("gih"),
             db.get(c, {}).get("rarity", "common"))
            for c, v in seen_early.items() if v >= floor]
    rows = [r for r in rows if r[3]]
    rows.sort(reverse=True)
    print(f"WHEELING — offered by pick 6, still there {POD} picks later "
          f"({len(rows)} cards, n>={floor})")
    # Wheel rate mostly just tracks card quality, which tells you nothing you did not
    # already know. The signal is the RESIDUAL: cards that wheel more or less often than
    # they should. But it MUST be fitted within rarity — drafters take rares early
    # regardless of win rate, so a single pooled fit just rediscovers rarity: every card
    # it flags as "underrated" comes out a common and every "correctly taken" one a rare.
    fits = {}
    for rar in {r[4] for r in rows}:
        grp = [r for r in rows if r[4] == rar]
        if len(grp) < 8:                      # too few to fit; fall back to the pooled line
            continue
        xs = [g[3] for g in grp]; ys = [g[0] for g in grp]
        mx, my = st.mean(xs), st.mean(ys)
        b = (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
             / max(sum((x - mx) ** 2 for x in xs), 1e-9))
        fits[rar] = (my - b * mx, b, len(grp))
    xs = [r[3] for r in rows]; ys = [r[0] for r in rows]
    mx, my = st.mean(xs), st.mean(ys)
    pb = (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
          / max(sum((x - mx) ** 2 for x in xs), 1e-9))
    pooled = (my - pb * mx, pb, len(rows))
    def pred(r):
        a_, b_, _ = fits.get(r[4], pooled)
        return a_ + b_ * r[3]
    res = sorted((r[0] - pred(r), r) for r in rows)
    print("  fitted WITHIN rarity — a pooled fit just rediscovers that rares go early:")
    for rar in ("common", "uncommon", "rare", "mythic"):
        if rar in fits:
            a_, b_, k = fits[rar]
            print(f"    {rar:<9} n={k:<4} mean wheel "
                  f"{100*st.mean([r[0] for r in rows if r[4]==rar]):>3.0f}%  "
                  f"slope {b_:+.2f}/GIH point")
    print()
    def show(lst, head):
        print(f"  {head}")
        print(f"    {'card':<32}{'wheel%':>8}{'GIH':>8}{'vs pred':>9}{'n':>5}  rarity")
        for d, (r, v, c, g, rar) in lst:
            print(f"    {c:<32}{r*100:>7.0f}%{g:>8.3f}{d*100:>+8.0f}%{v:>5}  {rar}")
    show(res[:6], "PASSED LESS than the win rate predicts — the field is on to these")
    print()
    show(res[-6:][::-1], "WHEELS MORE than it should — the field's blind spot")

    print("\nCOMMITMENT — share of determined picks castable in the FINAL colours")
    print("  (partly circular early on: the final colours are chosen by these picks."
          " Read the dips.)")
    for lo in range(0, 42, 3):
        on = sum(oncolour[s][0] for s in range(lo, lo + 3))
        tot = sum(oncolour[s][1] for s in range(lo, lo + 3))
        if tot:
            bar = "#" * round(on / tot * 30)
            print(f"  picks {lo+1:>2}-{lo+3:<2} {100*on/tot:>4.0f}%  n={tot:<5} {bar}")

    print("\nPASSED — biggest on-colour win rate given up on a determined pick")
    passed_best.sort(reverse=True)
    # Aggregate by the card GIVEN UP, not by the pair — pairs are nearly all unique.
    agg = collections.Counter(b for _, b, _ in passed_best)
    gap = collections.defaultdict(list)
    for d, b, _ in passed_best:
        gap[b].append(d)
    print(f"  {len(passed_best)} of {pick_tot and det_tot} determined picks gave up win rate")
    print(f"    {'card passed over':<32}{'times':>7}{'median gap':>12}")
    for k, v in agg.most_common(8):
        print(f"    {k:<32}{v:>7}{st.median(gap[k]):>+12.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
