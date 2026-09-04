#!/usr/bin/env python3
"""Fetch 17Lands trophy decks for a set+format and derive sealed build statistics.

A "trophy deck" won the max matches for its event (7 wins in Bo1 Arena Direct Sealed).
17Lands exposes, per trophy, the FULL 84-card sealed pool AND the registered 40 — i.e.
100 labelled (pool -> deck) pairs. That is the only public source of *build* decisions
(what winners left in the sideboard), as opposed to card power (GIH WR).

Outputs (all under data/cache/, which is gitignored):
  trophies/<SET>_<FORMAT>/<id>.json     raw per-event payloads
  trophy_<SET>_<FORMAT>.json            derived aggregate consumed by sealed_algo.py
  carddb_<SET>.json                     name -> mana_cost/cmc/types/rarity/gih

17Lands data is licensed for use on 17lands.com; keep everything this writes local
(data/ is gitignored) and do not redistribute the raw payloads.

Usage:
  python3 src/ingest/fetch_trophies.py --set HOB --format ArenaDirect_Sealed
"""
import argparse, collections, itertools, json, os, statistics as st, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "data", "cache")
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.17lands.com/trophy_decks"}
BASIC = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}


def _get(url, data=None):
    req = urllib.request.Request(url, headers=dict(UA))
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def unbiased_list(expansion, fmt):
    """The unfiltered query: the 100 most recent trophies, no colour filter. This is the
    only UNBIASED sample the endpoint gives — the colour sweep below is stratified, so its
    colour mix reflects how many ids each filter returned, not the format's real mix."""
    return _get("https://www.17lands.com/api/trophies/",
                {"expansion": expansion, "event_type": fmt,
                 "card_names": [], "ranks": [], "deck_colors": []})["data"]


def trophy_list(expansion, fmt, delay=1.0):
    """POST /api/trophies/ is what www.17lands.com/trophy_decks calls. It returns only the
    100 most recent decks — but the deck_colors filter is applied BEFORE that cap, so each
    colour combination has its own 100. Sweeping every 1-, 2- and 3-colour combination turns
    the 100-deck ceiling into ~1,100 for a busy format, reaching weeks further back. Combos
    that come back full (100) are themselves truncated; slice those further if you need more."""
    seen, capped = {}, []
    combos = [[]] + [["".join(c)] for n in (1, 2, 3)
                     for c in itertools.combinations("WUBRG", n)]
    for c in combos:
        try:
            d = _get("https://www.17lands.com/api/trophies/",
                     {"expansion": expansion, "event_type": fmt,
                      "card_names": [], "ranks": [], "deck_colors": c})["data"]
        except Exception as e:
            print(f"  colour {c or 'any'}: {e}")
            time.sleep(3)
            continue
        for x in d:
            seen[x["aggregate_id"]] = x
        if len(d) >= 100:
            capped.append("".join(c) or "any")
        time.sleep(delay)
    if capped:
        print(f"  hit the 100 cap (more available) for: {', '.join(capped)}")
    return list(seen.values())


def load_cached(expansion, fmt, entries):
    d = os.path.join(CACHE, "trophies", f"{expansion}_{fmt}")
    out = []
    for e in entries:
        p = os.path.join(d, f"{e['aggregate_id']}_{e['deck_index']}.json")
        if os.path.exists(p):
            try:
                out.append((e, json.load(open(p))))
            except Exception:
                pass
    return out


def fetch_events(expansion, fmt, entries, delay=2.0):
    d = os.path.join(CACHE, "trophies", f"{expansion}_{fmt}")
    os.makedirs(d, exist_ok=True)
    out, backoff, done = [], 60, 0
    for e in entries:
        p = os.path.join(d, f"{e['aggregate_id']}_{e['deck_index']}.json")
        if not os.path.exists(p):
            try:
                body = _get("https://www.17lands.com/data/event_preview"
                            f"?draft_id={e['aggregate_id']}&deck_index={e['deck_index']}")
            except Exception as ex:
                # 17Lands IP-bans on bursts (~200 requests in a couple of minutes gets a
                # plain 403 on every GET, including card_ratings — FlareSolverr does NOT
                # get around it). One long backoff, then give up for this run; everything
                # already on disk is reused, so re-running resumes where it stopped.
                print(f"  {ex} at {e['aggregate_id']} — backing off {backoff}s")
                if backoff >= 900:
                    print("  still blocked; stopping. Re-run later to resume.")
                    break
                time.sleep(backoff)
                backoff *= 4
                continue
            json.dump(body, open(p, "w"))
            done += 1
            if done % 100 == 0:
                print(f"  fetched {done} new ({len(out) + 1}/{len(entries)})")
            time.sleep(delay)
        try:
            out.append((e, json.load(open(p))))
        except Exception:
            os.remove(p)          # truncated write from an interrupted run
    return out


def derive(expansion, fmt, events, sealed_stats, unbiased_ids=frozenset()):
    """Aggregate the fetched events.

    The colour sweep is a STRATIFIED sample, not a random one: a combo that returns 100 ids
    contributes 100 decks whether or not that colour pair is common. Counting it raw makes
    WU look like the format's best pair simply because the WU filter filled its quota. So:

      * pair frequencies come only from `unbiased_ids` (the unfiltered 100-most-recent query);
      * every other statistic is POST-STRATIFIED — each deck is weighted by its colour pair's
        true share divided by its share of the fetched sample, weights clipped to [0.1, 10].

    With no unbiased ids supplied (a plain unfiltered fetch) every weight is 1 and this is a
    straight count."""
    pool_ct, main_ct = collections.Counter(), collections.Counter()
    pool_cp, main_cp = collections.Counter(), collections.Counter()
    pool_w2 = collections.Counter()      # sum of w^2, for Kish effective sample size
    pairs, creatures, lands, shapes = collections.Counter(), [], [], collections.Counter()
    carddb = {}

    def upper_pair(colors):
        return "".join(sorted((c for c in colors if c.isupper()), key="WUBRG".index))

    sample = collections.Counter(upper_pair(e["colors"]) for e, _ in events)
    truth = collections.Counter(upper_pair(e["colors"]) for e, _ in events
                                if e["aggregate_id"] in unbiased_ids)
    weight = {}
    if truth:
        ns, nt = sum(sample.values()), sum(truth.values())
        for k, v in sample.items():
            w = (truth.get(k, 0) / nt) / (v / ns) if v else 1.0
            weight[k] = min(10.0, max(0.1, w)) if truth.get(k) else 0.1
    for e, d in events:
        w = weight.get(upper_pair(e["colors"]), 1.0)
        cards = d["cards"]
        nm = lambda i: cards[str(i)]["name"]
        for k, v in cards.items():
            carddb.setdefault(v["name"], {
                "name": v["name"], "mana_cost": v.get("mana_cost", ""),
                "cmc": v.get("cmc", 0), "types": v.get("types", []),
                "rarity": v.get("rarity", ""), "mtga_id": v["id"],
                "img": v.get("image_url", "")})
        pool = [nm(i) for i in d["pool"] if nm(i) not in BASIC]
        main_all = [nm(i) for i in d["decks"][0]["groups"][0]["cards"]]
        main = [m for m in main_all if m not in BASIC]
        for n in set(pool):
            pool_ct[n] += w
            pool_w2[n] += w * w
        for n in set(main): main_ct[n] += w
        for n, c in collections.Counter(pool).items(): pool_cp[n] += c * w
        for n, c in collections.Counter(main).items(): main_cp[n] += c * w
        lands.append(len(main_all) - len(main))
        creatures.append(sum(1 for m in main if any("Creature" in t for t in carddb[m]["types"])))
        up = upper_pair(e["colors"])
        # Pair frequency: unbiased sample only. Everything else is reweighted above.
        if len(up) == 2 and (not unbiased_ids or e["aggregate_id"] in unbiased_ids):
            pairs[up] += 1
        shapes["pure2c" if (len(e["colors"]) == 2) else
               "splash" if len(up) == 2 else "3c+"] += 1
    for n, s in sealed_stats.items():
        c = carddb.setdefault(n, {"name": n, "mana_cost": "", "cmc": 0,
                                  "types": s["types"], "rarity": s["rarity"],
                                  "mtga_id": s["mtga_id"]})
        c["gih"] = s["ever_drawn_win_rate"]
        c["gih_n"] = s["ever_drawn_game_count"]
        c["rarity"] = s["rarity"]
        c.setdefault("img", "")
        c["img"] = c["img"] or s.get("url", "")
    # Kish effective n: (sum w)^2 / sum w^2. Equals the raw count when every weight is 1,
    # and collapses toward the count of the decks that actually carry weight when they are
    # not. sealed_algo shrinks by n_pool, so handing it the raw weighted sum would make it
    # trust a heavily-reweighted sample far more than it should.
    cards = []
    for n, raw in pool_ct.items():
        if raw <= 0:
            continue
        n_eff = raw ** 2 / pool_w2[n] if pool_w2[n] else 0
        rate = main_ct.get(n, 0) / raw                 # the weighted play rate
        cards.append({"card": n,
                      "n_pool": round(n_eff, 2),       # effective, for shrinkage
                      "n_pool_weighted": round(raw, 2),
                      "n_main": round(rate * n_eff, 2),  # same scale, so n_main/n_pool == rate
                      "copies_pool": round(pool_cp[n], 2),
                      "copies_main": round(main_cp.get(n, 0), 2)})
    cards.sort(key=lambda r: (-(r["n_main"] / r["n_pool"]), -r["n_pool"]))
    return carddb, {
        "expansion": expansion, "format": fmt, "n_decks": len(events),
        "n_unbiased": sum(1 for e, _ in events if e["aggregate_id"] in unbiased_ids),
        "n_effective": round(sum(weight.get(upper_pair(e["colors"]), 1.0) for e, _ in events) ** 2
                             / max(sum(weight.get(upper_pair(e["colors"]), 1.0) ** 2
                                       for e, _ in events), 1e-9), 1) if weight else len(events),
        "stratified": bool(truth),
        "weights": {k: round(v, 3) for k, v in sorted(weight.items())},
        "pairs": dict(pairs.most_common()), "shapes": dict(shapes),
        "creatures": {"mean": round(st.mean(creatures), 2), "median": st.median(creatures),
                      "dist": dict(sorted(collections.Counter(creatures).items()))},
        "lands": {"median": st.median(lands),
                  "dist": dict(sorted(collections.Counter(lands).items()))},
        "cards": cards}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", dest="expansion", required=True)
    ap.add_argument("--format", default="ArenaDirect_Sealed")
    ap.add_argument("--stats-format", default="Sealed", help="17Lands card-stats format to join on")
    ap.add_argument("--days", default="120")
    # DEFAULT, not an opt-in. A plain run rewrote the shipped aggregate on the swept
    # corpus twice before this flipped: the sweep is stratified, so aggregating it
    # silently biases every published frequency, and post-stratification buys back so
    # little that it lost a head-to-head against the unbiased 100 (pair@2 68% vs 77%).
    # The swept decks are still fetched and still browsable — they just do not vote.
    ap.add_argument("--include-swept", action="store_true",
                    help="aggregate the colour-swept decks too, post-stratified. Off by "
                         "default: measured worse than the unbiased sample alone.")
    ap.add_argument("--offline", action="store_true",
                    help="re-derive from cached events + the saved index; no network at all")
    ap.add_argument("--delay", type=float, default=2.0,
                    help="seconds between event fetches; below ~1.5 risks an IP ban")
    a = ap.parse_args()
    sp = os.path.join(CACHE, f"17lands_{a.expansion}_{a.stats_format}_{a.days}d.json")
    if not os.path.exists(sp):
        raise SystemExit(f"missing {sp} — run: python3 src/mtg-draft.py warm --set {a.expansion}")
    sealed = {c["name"]: c for c in json.load(open(sp))}
    index_path = os.path.join(CACHE, f"trophy_index_{a.expansion}_{a.format}.json")
    if a.offline:
        idx = json.load(open(index_path))
        unbiased, entries = set(idx["unbiased"]), idx["entries"]
        print(f"offline: {len(entries)} indexed decks, {len(unbiased)} unbiased")
    else:
        unbiased = {e["aggregate_id"] for e in unbiased_list(a.expansion, a.format)}
        entries = trophy_list(a.expansion, a.format)
        json.dump({"unbiased": sorted(unbiased), "entries": entries}, open(index_path, "w"))
        print(f"{len(entries)} unique trophy decks after the colour sweep "
              f"({len(unbiased)} of them from the unbiased unfiltered query)")
    fetch_list = entries
    if not a.include_swept:
        entries = [e for e in entries if e["aggregate_id"] in unbiased]
    # Fetch everything (the extra decks are browsable via sealed_algo --decks), but
    # aggregate only what `entries` was narrowed to above.
    if not a.offline:
        fetch_events(a.expansion, a.format, fetch_list, a.delay)
    events = load_cached(a.expansion, a.format, entries)
    carddb, agg = derive(a.expansion, a.format, events, sealed, unbiased)
    json.dump(carddb, open(os.path.join(CACHE, f"carddb_{a.expansion}.json"), "w"), indent=1)
    json.dump(agg, open(os.path.join(CACHE, f"trophy_{a.expansion}_{a.format}.json"), "w"), indent=1)
    print(f"decks={agg['n_decks']} (unbiased {agg['n_unbiased']}) shapes={agg['shapes']} "
          f"top pairs={list(agg['pairs'].items())[:3]} "
          f"creatures~{agg['creatures']['median']} lands~{agg['lands']['median']}")


if __name__ == "__main__":
    main()
