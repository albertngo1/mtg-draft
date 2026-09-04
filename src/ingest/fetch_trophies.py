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
import argparse, collections, json, os, statistics as st, time, urllib.request

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


def trophy_list(expansion, fmt):
    # POST /api/trophies/ is what www.17lands.com/trophy_decks calls; max 100 most recent.
    r = _get("https://www.17lands.com/api/trophies/",
             {"expansion": expansion, "event_type": fmt,
              "card_names": [], "ranks": [], "deck_colors": []})
    return r["data"]


def fetch_events(expansion, fmt, entries, delay=1.5):
    d = os.path.join(CACHE, "trophies", f"{expansion}_{fmt}")
    os.makedirs(d, exist_ok=True)
    out = []
    for e in entries:
        p = os.path.join(d, f"{e['aggregate_id']}_{e['deck_index']}.json")
        if not os.path.exists(p):
            try:
                body = _get("https://www.17lands.com/data/event_preview"
                            f"?draft_id={e['aggregate_id']}&deck_index={e['deck_index']}")
            except Exception as ex:
                # 17Lands rate-limits event_preview aggressively; back off and stop
                # rather than burning through the remaining ids on 403s.
                print("  stop at", e["aggregate_id"], ex)
                print("  (already-cached events below are still used; re-run later to resume)")
                break
            json.dump(body, open(p, "w"))
            time.sleep(delay)
        out.append((e, json.load(open(p))))
    return out


def derive(expansion, fmt, events, sealed_stats):
    pool_ct, main_ct = collections.Counter(), collections.Counter()
    pool_cp, main_cp = collections.Counter(), collections.Counter()
    pairs, creatures, lands, shapes = collections.Counter(), [], [], collections.Counter()
    carddb = {}
    for e, d in events:
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
        for n in set(pool): pool_ct[n] += 1
        for n in set(main): main_ct[n] += 1
        for n, c in collections.Counter(pool).items(): pool_cp[n] += c
        for n, c in collections.Counter(main).items(): main_cp[n] += c
        lands.append(len(main_all) - len(main))
        creatures.append(sum(1 for m in main if any("Creature" in t for t in carddb[m]["types"])))
        up = "".join(sorted((c for c in e["colors"] if c.isupper()), key="WUBRG".index))
        if len(up) == 2: pairs[up] += 1
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
    cards = [{"card": n, "n_pool": pool_ct[n], "n_main": main_ct.get(n, 0),
              "copies_pool": pool_cp[n], "copies_main": main_cp.get(n, 0)}
             for n in pool_ct]
    cards.sort(key=lambda r: (-(r["n_main"] / r["n_pool"]), -r["n_pool"]))
    return carddb, {
        "expansion": expansion, "format": fmt, "n_decks": len(events),
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
    a = ap.parse_args()
    sp = os.path.join(CACHE, f"17lands_{a.expansion}_{a.stats_format}_{a.days}d.json")
    if not os.path.exists(sp):
        raise SystemExit(f"missing {sp} — run: python3 src/mtg-draft.py warm --set {a.expansion}")
    sealed = {c["name"]: c for c in json.load(open(sp))}
    entries = trophy_list(a.expansion, a.format)
    print(f"{len(entries)} trophy decks")
    events = fetch_events(a.expansion, a.format, entries)
    carddb, agg = derive(a.expansion, a.format, events, sealed)
    json.dump(carddb, open(os.path.join(CACHE, f"carddb_{a.expansion}.json"), "w"), indent=1)
    json.dump(agg, open(os.path.join(CACHE, f"trophy_{a.expansion}_{a.format}.json"), "w"), indent=1)
    print(f"decks={agg['n_decks']} shapes={agg['shapes']} "
          f"top pairs={list(agg['pairs'].items())[:3]} "
          f"creatures~{agg['creatures']['median']} lands~{agg['lands']['median']}")


if __name__ == "__main__":
    main()
