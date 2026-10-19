// The shapes of the server's answers (serve.py; see "The deck server" in ARCHITECTURE.md). Types only: nothing here is
// compiled, so the pages still hold exactly the eight modules. A field the server may leave out is optional; one it
// sends as null is `| null`.

/** What a 202 says while a deck is being prepared: how many web requests so far, and what the server is doing. */
export interface Progress {
  requests?: number;
  message?: string;
}

export interface Preparing {
  status: "preparing";
  progress?: Progress | null;
  revision?: number;
}

// ------------------------------------------------------------------------------------------------------------ cards

/** What a card tile needs: a name, and a picture or the text to draw in its place. */
export interface CardFace {
  name: string;
  image?: string | null;
  image_back?: string | null;
  cost?: string;
  type?: string;
  price?: number | null;
}

/** A card object: every card the server names comes as one. */
export interface Card extends CardFace {
  front?: string;
  scryfall_uri?: string;
  cmc?: number;
  ci?: string;
  owned?: boolean;
  /** The precons a free card came in ("you own it, from Peace Offering"); empty when it is owned another way. */
  owned_from?: string[];
  text?: string;
  power?: string | null;
  toughness?: string | null;
}

/** A card in a deck's list. */
export interface DeckCard extends Card {
  count: number;
  section: string;
  new: boolean;
  score: number | null;
  roles: string[];
  gc?: boolean;
}

/** Why a card cannot be added. */
export interface Flag {
  kind: "illegal" | "colors" | "in_deck" | "bracket";
  reason: string;
}

/** A card the Add sheet offers. */
export interface SearchCard extends Card {
  score: number | null;
  evidence: string | null;
  gain: number | null;
  flag: Flag | null;
}

export interface SearchAnswer {
  cards: SearchCard[];
}

// ---------------------------------------------------------------------------------------------------------- metrics

export type Unit = "%" | "$" | null | undefined;
export type Status = "short" | "inside" | "over";

export interface Band {
  min?: number | null;
  target?: number | null;
  max?: number | null;
}

/** The one item shape every metric comes in (metrics.ts). */
export interface MetricItem {
  id: string;
  label: string;
  value: number | null;
  unit?: Unit;
  target?: Band | null;
  status?: Status | null;
  why: string[];
  cards: string[];
  base?: number | null;
  change?: number | null;
}

export interface MetricGroup {
  id: string;
  label: string;
  items: MetricItem[];
}

export interface Headline {
  score: number | null;
  bracket: number | null;
  bracket_ok: boolean | null;
  removal_power: number | null;
  lands: number | null;
  price: number | null;
}

export interface Metrics {
  headline: Headline;
  groups: MetricGroup[];
}

// ------------------------------------------------------------------------------------------------------------- decks

export interface Settings {
  bracket?: number;
  budget?: number | null;
  themes?: string[];
  playstyle?: string;
  owned_precons?: string[];
}

/** One change of the change log, as a deck file keeps it. */
export interface LoggedChange {
  n: number;
  op: "cut" | "add" | "swap" | "group" | "undo" | "settings";
  card?: string;
  cut?: string;
  add?: string;
  label?: string;
  of?: number;
  items?: LoggedChange[];
  undone?: boolean;
  source?: "manual" | "suggested";
  at?: string;
}

export interface Version {
  id: string;
  name: string;
  revision: number;
  created?: string;
  settings: Settings;
  changes?: LoggedChange[];
}

export interface Spec {
  bracket?: number;
  themes?: string[];
  playstyle?: string;
}

export interface SourceInfo {
  cache?: string;
  fetched?: string;
}

/** GET /api/decks/PLAYER/ID, and the answer to every change. */
export interface DeckAnswer {
  version: Version;
  base: { id?: string; name: string };
  spec: Spec;
  commanders: Card[];
  cards: DeckCard[];
  cut_cards: DeckCard[];
  card_count: number;
  /** The precons the player owns besides the base deck's own: the version's setting, then the player's collection. */
  other_owned_precons?: string[];
  diff: { added: [number, string][]; cut: [number, string][] };
  metrics: Metrics;
  warnings?: string[];
  sources: Record<string, SourceInfo>;
  result?: { changed: boolean; message?: string };
}

/** A version on the Decks screen. */
export interface VersionEntry {
  id: string;
  name: string;
  base: string;
  base_name: string;
  commanders?: string[];
  commander_image?: string | null;
  headline: Headline | null;
  settings?: Settings;
  swaps: number;
  spent: number | null;
  updated: string;
  error?: string;
}

export interface BaseEntry {
  id: string;
  name: string;
  commanders?: string[];
  commander_image?: string | null;
  ci?: string;
  card_count: number;
  source?: { type: string; name: string };
}

export interface Playstyle {
  slug: string;
  label: string;
  min_bracket: number;
  description: string;
}

export interface Menu {
  playstyles: Playstyle[];
  themes: { slug: string; label: string }[];
}

export interface StatusAnswer {
  settings: { decks: string };
  uncommitted: string[];
  uncommitted_note: string | null;
}

/** A problem with a request: a setting that is wrong, or a line of a pasted list (null: a name on no one line, such as
 *  a card of a pasted JSON deck, or a misspelled commander). */
export interface Problem {
  setting?: string;
  line?: number | null;
  text: string;
  suggestions?: string[];
}

// ------------------------------------------------------------------------------------------------- the card sheet

export interface Combo {
  cards: string[];
  produces: string[];
  min_bracket: number;
}

export interface IfCutItem {
  id: string;
  label: string;
  unit?: Unit;
  before: number | null;
  after: number | null;
  status?: Status | null;
  status_before?: Status | null;
}

export interface CardSheet {
  card: Card;
  flag: Flag | null;
  commander: boolean;
  copies: number;
  roles: string[];
  gc: boolean;
  salt: number | null;
  answers: string[];
  score: { value: number; evidence: string; parts: { base: number; resid: number; theme: number; salt: number } } | null;
  removal: {
    role: string;
    value: number;
    line: string;
    weights: { speed: number; reach: number; permanence: number; cost: number; repeatable: number };
    kinds: { speed: string; reach: string; permanence: string; cost: string; repeatable: boolean };
  } | null;
  combos: { in_deck: Combo[]; would_complete: Combo[] } | null;
  if_cut: { items: IfCutItem[]; score_change: number | null } | null;
  replacements: { card: Card; gain: number; evidence: string }[];
}

// -------------------------------------------------------------------------------------------------------- suggestions

export interface Swap {
  cut: string;
  add: string;
  gain: number;
  price?: number | null;
  owned?: boolean;
  owned_from?: string[];
  forced?: boolean;
  fills?: string[];
}

export interface PricePoint {
  budget: number;
  spent: number;
  value: number;
  change?: number | null;
  swaps: number;
  weakens?: { label: string; before: number; after: number; target: number }[];
}

export interface SuggestAnswer {
  revision: number;
  bracket: number;
  budget: number | null;
  spent: number | null;
  left: number | null;
  over: number | null;
  value_before: number;
  swaps: Swap[];
  price_points: PricePoint[];
  cheap_adds: { card: string; price: number; gain: number }[];
  blocked: { card: string; reason: string }[];
  warnings: string[];
  cards: Record<string, Card>;
  changes_kept?: { added?: number; cut?: number };
}
