// Data layer, shared by main.ts (Electron) and probe.ts (headless smoke test).
// Reads mtg-draft's local files only — no network, no Electron dependency.
import * as fs from 'fs';
import * as path from 'path';

/** A card as it appears in current.json's `offered` list (loosely typed external JSON). */
interface OfferedCard {
  id: string;
  name: string;
  color?: string;
  rarity?: string;
  cmc?: number;
  mana?: string;
  type?: string;
  gih?: number | null;
  ds?: string | null;
  alsa?: number | null;
  iwd?: number | null;
  wheel?: boolean;
  tags?: string[];
  guide?: string | null;
  taken?: boolean;
}

/** A row from cards_<SET>.ndjson (oracle text + guide enrich). */
interface CardRow {
  id: string;
  text?: string | null;
  guide?: string | null;
  [k: string]: unknown;
}

export interface Loader {
  loadTakes(set: string): Record<string, string>;
  loadCards(set: string): Record<string, CardRow>;
}

export function makeLoader(ROOT: string): Loader {
  let takesCache: { set: string | null; map: Record<string, string> } = { set: null, map: {} };
  let cardsCache: { set: string | null; map: Record<string, CardRow> } = { set: null, map: {} };

  function loadTakes(set: string): Record<string, string> {
    if (takesCache.set === set) return takesCache.map;
    let map: Record<string, string> = {};
    try {
      map = JSON.parse(fs.readFileSync(path.join(ROOT, 'card-reference', `ai_takes_${set}.json`), 'utf8'));
    } catch {
      /* no takes for this set */
    }
    takesCache = { set, map };
    return map;
  }

  function loadCards(set: string): Record<string, CardRow> {
    if (cardsCache.set === set) return cardsCache.map;
    const map: Record<string, CardRow> = {};
    try {
      const raw = fs.readFileSync(path.join(ROOT, 'data', 'cache', `cards_${set}.ndjson`), 'utf8');
      for (const line of raw.split('\n')) {
        if (!line.trim()) continue;
        try {
          const r = JSON.parse(line) as CardRow;
          if (r && r.id != null) map[String(r.id)] = r;
        } catch {
          /* skip bad line (e.g. the _meta header) */
        }
      }
    } catch {
      /* not warmed for this set */
    }
    cardsCache = { set, map };
    return map;
  }

  return { loadTakes, loadCards };
}

/** Build the render payload from current.json. Returns null if there's no live pack. */
export function buildPack(currentPath: string, loader: Loader): Pack | null {
  let d: { set?: string; fmt?: string; picks?: Array<{ pack: number; pick: number; offered?: OfferedCard[] }> };
  try {
    d = JSON.parse(fs.readFileSync(currentPath, 'utf8'));
  } catch {
    return null;
  }
  const set = d.set || '';
  const picks = d.picks || [];
  if (!picks.length) return null;

  const last = picks[picks.length - 1];
  const offered = (last.offered || []).filter((c) => !c.taken);
  if (!offered.length) return null;

  const takes = loader.loadTakes(set);
  const cards = loader.loadCards(set);

  const tiles: Tile[] = offered
    .map((c): Tile => {
      const x = cards[String(c.id)] || ({} as CardRow);
      return {
        id: c.id,
        name: c.name,
        color: c.color || 'C',
        rarity: c.rarity,
        cmc: c.cmc,
        mana: c.mana,
        type: c.type,
        gih: c.gih ?? null,
        ds: c.ds ?? null,
        alsa: c.alsa ?? null,
        iwd: c.iwd ?? null,
        wheel: !!c.wheel,
        tags: (c.tags || []).slice(0, 4),
        take: takes[c.name] || null,
        guide: c.guide || x.guide || null,
        text: (x.text as string) || null,
      };
    })
    .sort((a, b) => (b.gih == null ? -1 : b.gih) - (a.gih == null ? -1 : a.gih));

  return {
    set,
    fmt: d.fmt,
    pack: last.pack,
    pick: last.pick,
    n: tiles.length,
    tiles,
    key: `${set}|${last.pack}|${last.pick}|${offered.length}`,
  };
}
