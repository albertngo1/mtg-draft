#!/usr/bin/env python3
"""Sealed pool -> best 40, calibrated on 17Lands trophy decks.

Two signals, deliberately unequal:

  1. sealed GIH WR      (whole 17Lands population)  -- how good the card is
  2. trophy maindeck rate (100 trophy pools)        -- what 7-win players BUILD

They correlate at r=0.82, so trophy rate is mostly redundant. It is therefore not
averaged in; only its *residual* against the rate GIH predicts is used, shrunk
toward zero by sample size. A card that winners play more often than its GIH
implies gets a small bump; one they leave in the sideboard gets a small cut.

Pair choice uses a FRONT-LOADED mean of the pair's top 23 playables (weight
1/(i+4)): in sealed the bombs decide the colour, the 23rd playable does not.

Measured by leave-one-out over the 100 HOB ArenaDirect_Sealed trophy decks:
  colour pair, top-1 ........ 47%   (always-guess-BR baseline: 42%)
  colour pair, top-2 ........ 72%   (with --pair-prior 0.003)
  cards, when pair matches .. 86%   of the algorithm's 23 were in the real 40

Usage:
  python3 src/sealed_algo.py --set HOB --pool mypool.txt
  python3 src/sealed_algo.py --set HOB --pool mypool.txt --json
  python3 src/sealed_algo.py --set HOB --validate
Pool file: one card per line, "2x Name" / "2 Name" / "Name" all work; blanks and
# comments ignored. Basics are ignored.
"""
import argparse, collections, json, math, os, re, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "cache")
WUBRG = "WUBRG"
BASIC = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}
PAIRS = [a + b for i, a in enumerate(WUBRG) for b in WUBRG[i + 1:]]

K_SHRINK = 10.0      # pseudo-observations of the GIH-implied play rate
LAMBDA = 0.060       # WR points per unit of play-rate residual
PAIR_PRIOR = 0.003   # WR points per z of format pair frequency (0 = ignore format)
N_SPELLS = 23
CREATURE_FLOOR = 13  # p25 of trophy decks; below this the deck stops functioning
SPLASH_MAX = 2
N_LANDS = 17         # 77 of 93 forty-card trophy decks; 16 only for a very low curve
UTIL_LAND_MIN = 0.50 # shrunk trophy play rate a utility land must clear to take a slot
UTIL_LAND_MAX = 3

# ---------------------------------------------------------------- mana costs
def pips(mana_cost):
    """({hard colour pips}, [{hybrid halves}, ...]) from a {..}{..} cost string."""
    hard, hybrid = set(), []
    for s in re.findall(r"\{([^}]+)\}", mana_cost or ""):
        if "/" in s:
            parts = {p for p in s.split("/") if p in WUBRG}
            if parts:
                hybrid.append(parts)
        elif s in WUBRG:
            hard.add(s)
    return hard, hybrid


def castable(card, pair):
    """Hybrid pips count as either half, so {B/R} cards are mono-pair, not gold."""
    hard, hybrid = pips(card.get("mana_cost", ""))
    return hard.issubset(pair) and all(h & pair for h in hybrid)


def off_colour_pips(card, pair):
    hard, hybrid = pips(card.get("mana_cost", ""))
    return len(hard - pair) + sum(1 for h in hybrid if not (h & pair))


def is_creature(c): return any("Creature" in t for t in c.get("types", []))
def is_land(c):     return any("Land" in t for t in c.get("types", []))

# ---------------------------------------------------------------- scoring
def _fit(rows):
    xs = [r[0] for r in rows]; ys = [r[1] for r in rows]
    mx, my = st.mean(xs), st.mean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return my - b * mx, b


def build_scores(db, trophy_cards):
    """trophy_cards: [{card, n_pool, n_main}] -> {name: {score, gih, ...}}"""
    tro = {r["card"]: r for r in trophy_cards}
    fit = [(db[n]["gih"], r["n_main"] / r["n_pool"]) for n, r in tro.items()
           if r["n_pool"] >= 8 and db.get(n, {}).get("gih")]
    a, b = _fit(fit)
    rmed = collections.defaultdict(list)
    for v in db.values():
        if v.get("gih"):
            rmed[v["rarity"]].append(v["gih"])
    rmed = {k: st.median(v) for k, v in rmed.items()}

    out = {}
    for n, c in db.items():
        if n in BASIC:
            continue
        r = tro.get(n)
        gih, src = c.get("gih"), "gih"
        if gih is None:
            # No sealed sample at all is itself evidence: nobody plays it.
            if r and r["n_pool"] >= 6 and b:
                gih = max(0.44, min(0.62, (r["n_main"] / r["n_pool"] - a) / b))
                src = "est-play"
            else:
                gih = rmed.get(c.get("rarity", "common"), 0.552) - 0.010
                src = "est-rarity"
        hat = a + b * gih
        p_obs, n_obs = ((r["n_main"] / r["n_pool"], r["n_pool"]) if r and r["n_pool"] else (hat, 0))
        p_adj = (n_obs * p_obs + K_SHRINK * hat) / (n_obs + K_SHRINK)
        out[n] = {"score": gih + LAMBDA * (p_adj - hat), "gih": gih,
                  "play_adj": p_adj, "play_hat": hat, "n_pool": n_obs, "src": src}
    return out, (a, b)


def pair_priors(pairs, total):
    vals = {p: math.log((pairs.get(p, 0) + 1) / (total + 10)) for p in PAIRS}
    m, s = st.mean(vals.values()), st.pstdev(vals.values()) or 1.0
    return {p: (v - m) / s for p, v in vals.items()}

# ---------------------------------------------------------------- build
def evaluate_pair(pool, db, sc, pair):
    P = set(pair)
    cands = sorted(((sc[n]["score"], n) for n in pool
                    if n not in BASIC and n in sc
                    and castable(db[n], P) and not is_land(db[n])), reverse=True)
    top = cands[:N_SPELLS]
    if len(top) < N_SPELLS:
        return None
    w = [1.0 / (i + 4) for i in range(len(top))]
    return sum(s * wi for (s, _), wi in zip(top, w)) / sum(w), top, cands


def build(pool, db, sc, priors, pair_prior=None):
    pp = PAIR_PRIOR if pair_prior is None else pair_prior
    results = []
    for p in PAIRS:
        r = evaluate_pair(pool, db, sc, p)
        if r:
            results.append((r[0] + pp * priors[p], r[0], p, r[1], r[2]))
    if not results:
        raise ValueError("no colour pair has 23 castable non-land cards in this pool")
    results.sort(reverse=True)
    _, mean, pair, top, cands = results[0]
    names = [n for _, n in top]

    creatures = sum(1 for n in names if is_creature(db[n]))
    if creatures < CREATURE_FLOOR:
        spare = [(s, n) for s, n in cands[N_SPELLS:] if is_creature(db[n])]
        weakest = sorted((sc[n]["score"], n) for n in names if not is_creature(db[n]))
        while creatures < CREATURE_FLOOR and spare and weakest:
            _, add = spare.pop(0)
            _, drop = weakest.pop(0)
            names.remove(drop); names.append(add); creatures += 1

    # Utility lands compete with basics, not with the 23 spells: trophy decks run
    # ~2 of them inside a 17-land mana base (Hobbit Hole is played 87% of the time).
    P = set(pair)
    util = sorted(((sc[n]["score"], n) for n in pool
                   if n not in BASIC and n in sc and is_land(db[n])
                   and castable(db[n], P) and sc[n]["play_adj"] >= UTIL_LAND_MIN),
                  reverse=True)[:UTIL_LAND_MAX]

    cut = min(sc[n]["score"] for n in names)
    splash = sorted(((sc[n]["score"], n) for n in set(pool)
                     if n in sc and not is_land(db[n]) and not castable(db[n], set(pair))
                     and off_colour_pips(db[n], set(pair)) == 1 and sc[n]["score"] > cut),
                    reverse=True)[:SPLASH_MAX]
    avg_cmc = st.mean(db[n].get("cmc", 0) for n in names)
    lands = N_LANDS if avg_cmc >= 2.90 else N_LANDS - 1
    util_names = [n for _, n in util]
    basics = lands - len(util_names)
    wpips = collections.Counter()
    for n in names:
        for c in pips(db[n].get("mana_cost", ""))[0]:
            wpips[c] += 1
    split = {c: round(basics * wpips[c] / max(sum(wpips[k] for k in pair), 1))
             for c in pair}
    return {"pair": pair, "mean_score": round(mean, 4),
            "pair_scores": [(round(m, 4), p) for _, m, p, _, _ in results],
            "spells": sorted(names, key=lambda n: -sc[n]["score"]),
            "splash": [n for _, n in splash],
            "creatures": creatures, "avg_cmc": round(avg_cmc, 2),
            "lands": lands, "utility_lands": util_names, "basics": split,
            "cut": [n for _, n in cands[N_SPELLS:]][:12]}

# ---------------------------------------------------------------- io
def read_pool(src):
    """Accept a path or an already-read blob. '2x Name', '2 Name', 'Name', and
    MTGA's own export line ('2 Name (HOB) 123') all parse."""
    text = src if "\n" in src or not os.path.exists(src) else open(src).read()
    pool = []
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line or line.lower() in ("deck", "sideboard", "commander"):
            continue
        line = re.sub(r"\s*\([A-Z0-9]{3,5}\)\s*\d*\s*$", "", line)  # MTGA export suffix
        m = re.match(r"^(\d+)\s*x?\s+(.*)$", line)
        n, name = (int(m.group(1)), m.group(2).strip()) if m else (1, line)
        pool += [name] * n
    return pool


def load(expansion, fmt):
    db = json.load(open(os.path.join(CACHE, f"carddb_{expansion}.json")))
    tro = json.load(open(os.path.join(CACHE, f"trophy_{expansion}_{fmt}.json")))
    return db, tro


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="expansion", required=True)
    ap.add_argument("--format", default="ArenaDirect_Sealed")
    ap.add_argument("--pool", help="pool file, or - for stdin")
    ap.add_argument("--pair-prior", type=float, default=PAIR_PRIOR)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--catalog", action="store_true",
                    help="dump every card's score/GIH/trophy play rate as JSON")
    a = ap.parse_args()
    db, tro = load(a.expansion, a.format)
    if a.validate:
        return validate(a.expansion, a.format, db, a.pair_prior)
    if a.catalog:
        sc, (fa, fb) = build_scores(db, tro["cards"])
        rows = []
        for n, s in sc.items():
            c = db[n]
            rows.append({"name": n, "score": s["score"], "gih": s["gih"],
                         "play": s["play_adj"], "play_hat": s["play_hat"],
                         "n_pool": s["n_pool"], "src": s["src"],
                         "delta": s["play_adj"] - s["play_hat"],
                         "img": c.get("img", ""), "mana_cost": c.get("mana_cost", ""),
                         "cmc": c.get("cmc", 0), "rarity": c.get("rarity", ""),
                         "types": c.get("types", []),
                         "colors": sorted(pips(c.get("mana_cost", ""))[0])
                                   or sorted({x for h in pips(c.get("mana_cost", ""))[1] for x in h}),
                         "is_land": is_land(c), "is_creature": is_creature(c)})
        rows.sort(key=lambda r: -r["score"])
        print(json.dumps({"expansion": a.expansion, "format": a.format,
                          "n_decks": tro["n_decks"], "pairs": tro["pairs"],
                          "shapes": tro["shapes"], "creatures": tro["creatures"],
                          "lands": tro["lands"], "fit": [fa, fb], "cards": rows}))
        return 0
    if not a.pool:
        ap.error("--pool or --validate required")
    pool = read_pool(sys.stdin.read() if a.pool == "-" else a.pool)
    unknown = sorted({n for n in pool if n not in db and n not in BASIC})
    if unknown:
        msg = {"error": "unknown card names", "unknown": unknown}
        print(json.dumps(msg) if a.json else
              "unknown card names (check spelling): " + ", ".join(unknown))
        return 1
    sc, _ = build_scores(db, tro["cards"])
    r = build(pool, db, sc, pair_priors(tro["pairs"], tro["n_decks"]), a.pair_prior)
    if a.json:
        r["cards"] = {n: sc[n] | {"img": db[n].get("img", ""),
                                  "mana_cost": db[n].get("mana_cost", ""),
                                  "cmc": db[n].get("cmc", 0),
                                  "rarity": db[n].get("rarity", ""),
                                  "types": db[n].get("types", [])}
                      for n in set(r["spells"] + r["splash"] + r["cut"] + r["utility_lands"])}
        r["trophy_pairs"] = tro["pairs"]
        r["n_trophy_decks"] = tro["n_decks"]
        print(json.dumps(r, indent=1)); return 0

    print(f"POOL {len(pool)} cards | format {a.expansion} {a.format} "
          f"({tro['n_decks']} trophy decks)")
    print("\npair ranking (front-loaded top-23 score):")
    for m, p in r["pair_scores"]:
        star = " <=" if p == r["pair"] else ""
        print(f"  {p}  {m:.4f}  (trophy share {tro['pairs'].get(p,0)}/{tro['n_decks']}){star}")
    mana = ", ".join(f"{v} {n}" for n, v in
                     zip([{"W":"Plains","U":"Island","B":"Swamp","R":"Mountain","G":"Forest"}[c]
                          for c in r["pair"]], r["basics"].values()))
    print(f"\nBUILD {r['pair']} — {len(r['spells'])} spells, {r['creatures']} creatures, "
          f"{r['lands']} lands, avg MV {r['avg_cmc']}")
    print(f"  mana: {mana}" + (f" + {', '.join(r['utility_lands'])}" if r["utility_lands"] else ""))
    print(f"{'':2}{'card':<34}{'score':>7}{'sealGIH':>9}{'trophy play':>13}")
    for n in r["spells"]:
        s = sc[n]
        pr = f"{s['play_adj']*100:.0f}% (n={s['n_pool']})" if s["n_pool"] else "-"
        print(f"  {n:<34}{s['score']:>7.4f}{s['gih']:>9.3f}{pr:>13}")
    if r["splash"]:
        print("\nsplash candidates (single off-colour pip, better than your worst include):")
        for n in r["splash"]:
            print(f"  {n:<34}{sc[n]['score']:>7.4f}  needs {sorted(pips(db[n]['mana_cost'])[0]-set(r['pair']))}")
    print("\nfirst cards below the line:", ", ".join(r["cut"][:8]))
    return 0


def validate(expansion, fmt, db, pair_prior):
    """Leave-one-out over the cached trophy events.

    TRAIN on everything, but SCORE only on the unbiased subset (the unfiltered
    100-most-recent query). The rest of the corpus comes from a colour-stratified
    sweep, so using it as the test set measures the algorithm against a colour mix
    that isn't the format's — WU decks are over-represented there roughly 30x."""
    import glob
    d = os.path.join(CACHE, "trophies", f"{expansion}_{fmt}")
    try:
        unbiased = set(json.load(open(os.path.join(
            CACHE, f"trophy_index_{expansion}_{fmt}.json")))["unbiased"])
    except Exception:
        unbiased = set()
    decks = []
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        aid = os.path.basename(f).split("_")[0]
        e = json.load(open(f)); cards = e["cards"]
        nm = lambda i: cards[str(i)]["name"]
        main = [nm(i) for i in e["decks"][0]["groups"][0]["cards"] if nm(i) not in BASIC]
        pool = [nm(i) for i in e["pool"]]
        cs = collections.Counter()
        for n in set(main):
            for c in pips(db[n].get("mana_cost", ""))[0]:
                cs[c] += 1
        # Train on the same decks the shipped aggregate was built from. The cache also holds
        # colour-swept decks; feeding those in raw trains on a colour mix that isn't the
        # format's, which is a different (worse) model than the one actually being served.
        decks.append({"pool": pool, "main": main, "test": (not unbiased) or aid in unbiased,
                      "pair": "".join(sorted((c for c, _ in cs.most_common(2)), key=WUBRG.index))})
    def weights_for(ds):
        """Post-stratification weights, same formula fetch_trophies.derive uses: a deck's
        colour pair's TRUE share (from the unbiased subset) over its share of this sample."""
        samp = collections.Counter(d["pair"] for d in ds)
        truth = collections.Counter(d["pair"] for d in ds if d["test"])
        if not truth or samp == truth:
            return {}
        ns, nt = sum(samp.values()), sum(truth.values())
        return {k: (min(10.0, max(0.1, (truth.get(k, 0) / nt) / (v / ns)))
                    if truth.get(k) else 0.1)
                for k, v in samp.items()}

    def rows(ds):
        w = weights_for(ds)
        pc, mc, w2 = collections.Counter(), collections.Counter(), collections.Counter()
        for x in ds:
            wx = w.get(x["pair"], 1.0)
            for n in set(x["pool"]):
                if n not in BASIC:
                    pc[n] += wx
                    w2[n] += wx * wx
            for n in set(x["main"]):
                mc[n] += wx
        out = []
        for n, raw in pc.items():
            if raw <= 0:
                continue
            n_eff = raw ** 2 / w2[n] if w2[n] else 0      # Kish effective sample size
            out.append({"card": n, "n_pool": n_eff,
                        "n_main": mc.get(n, 0) / raw * n_eff})
        return out
    meta = json.load(open(os.path.join(CACHE, f"trophy_{expansion}_{fmt}.json")))
    train_pool = [d for d in decks if d["test"]] if meta["n_decks"] == meta["n_unbiased"] else decks
    h1 = h2 = 0; ov = []; ovc = []
    for i, x in enumerate(decks):
        if not x["test"]:
            continue
        rest = [d for d in train_pool if d is not x]
        sc, _ = build_scores(db, rows(rest))
        pc = collections.Counter(y["pair"] for y in rest if len(y["pair"]) == 2)
        r = build(x["pool"], db, sc, pair_priors(pc, len(rest)), pair_prior)
        ok = r["pair"] == x["pair"]; h1 += ok
        h2 += x["pair"] in [p for _, p in r["pair_scores"][:2]]
        ca, cb = collections.Counter(x["main"]), collections.Counter(r["spells"])
        o = sum(min(ca[k], cb[k]) for k in cb) / len(r["spells"])
        ov.append(o); ok and ovc.append(o)
    n = len(ov)
    print(f"leave-one-out: trained on {len(train_pool)} decks, scored on the {n} unbiased ones "
          f"(pair-prior {pair_prior})")
    print(f"  pair top-1 {100*h1/n:.0f}%  top-2 {100*h2/n:.0f}%")
    print(f"  cards in the real 40: {100*st.mean(ov):.0f}% overall, "
          f"{100*st.mean(ovc):.0f}% when the pair matches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
