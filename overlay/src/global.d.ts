// Shared ambient types — visible to both the Node side (pack/main/probe) and the
// browser renderer without imports, so nothing has to become a module.

interface Tile {
  id: string;
  name: string;
  color: string;
  rarity?: string;
  cmc?: number;
  mana?: string;
  type?: string;
  gih: number | null;
  ds: string | null;
  alsa: number | null;
  iwd: number | null;
  wheel: boolean;
  tags: string[];
  take: string | null;
  guide: string | null;
  text: string | null;
}

interface Pack {
  set: string;
  fmt?: string;
  pack: number;
  pick: number;
  n: number;
  tiles: Tile[];
  key: string;
}

interface OverlayState {
  interactive: boolean;
  expandAll: boolean;
}

interface OverlayAPI {
  onPack(cb: (pack: Pack) => void): void;
  onState(cb: (state: OverlayState) => void): void;
  setIgnore(ignore: boolean): void;
}

interface Window {
  overlay: OverlayAPI;
}
