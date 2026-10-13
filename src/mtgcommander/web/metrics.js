// Draws the metric groups from the one item shape the server sends every metric in:
//   {id, label, value, unit, target: {min, target, max} | null, status: short | inside | over | null,
//    why: [..], cards: [..], base?, change?}
// Any item is a row: its label, its value with its unit, how far it moved from the base deck (and what it was there), how
// it sits in the bracket's band, and its `why` behind a tap. A few families of items are folded into one picture (the
// mana curve, the answers to each threat, the playstyle shares), but an item the pages have never heard of is still
// drawn, as a row, with no page code.
//
// Nothing here works out a number. A bar's length is its value against the largest value in its picture (layout); how far
// a value moved from its base is the `change` the server sent.

import * as ui from "./ui.js";

const { h } = ui;

/** The item with this id from a deck's metrics, or null. */
export function findItem(measured, id) {
  for (const group of measured.groups) {
    for (const item of group.items) if (item.id === id) return item;
  }
  return null;
}

// What is open: the rows whose "why" shows, and the groups the compact panel has opened up. Kept here so that a redraw
// after a change does not close what the person was reading.
const openRows = new Set();
const openGroups = new Set();

const NUMBER = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const hasBand = (item) => item.target !== null && item.target !== undefined;
const isChecked = (item) => hasBand(item) || (item.status !== null && item.status !== undefined);

/** "want 2–4", "at least 1", "at most 8": the bracket's usual range for a number. */
function bandText(target) {
  if (!target) return "";
  const { min, max } = target;
  const low = min !== null && min !== undefined;
  const high = max !== null && max !== undefined;
  if (low && high) return min === max ? `want ${NUMBER.format(min)}` : `want ${NUMBER.format(min)}–${NUMBER.format(max)}`;
  if (low) return `want ${NUMBER.format(min)} or more`;
  if (high) return `at most ${NUMBER.format(max)}`;
  return "";
}

/** The mark for where a value sits in its band: a green check inside it, "short" in red, "over" in gold. */
export function statusMark(status) {
  if (status === "inside") return h("span", { class: "is-inside" }, "✓", h("span", { class: "sr-only", text: " inside the range" }));
  if (status === "short") return h("span", { class: "is-short", text: "short" });
  if (status === "over") return h("span", { class: "is-over", text: "over" });
  return null;
}

/** The right-hand side of a row: 36 −2 from 38 · want 34–36 ✓ */
function valueBlock(item) {
  const parts = [h("span", { text: ui.valueText(item.value, item.unit) })];
  const moved = ui.delta(item);
  if (moved) parts.push(" ", moved);
  const band = bandText(item.target);
  if (band && ui.isNumber(item.value)) parts.push(h("span", { class: "metric__band", text: ` · ${band}` }));
  const mark = ui.isNumber(item.value) ? statusMark(item.status) : null;
  if (mark) parts.push(" ", mark);
  return parts;
}

/** What a row says when it is opened: the `why` lines, then the cards it counts as links to their sheets. */
function whyPanel(item, ctx) {
  const panel = h("div", { class: "metric__why", id: `why-${item.id}` }, item.why.map((line) => h("p", { text: line })));
  if (item.cards.length && ctx) {
    const list = h("p", { class: "metric__cards" });
    item.cards.forEach((name, i) => list.append(i ? ", " : "", h("a", { href: ctx.link(name), text: name })));
    panel.append(list);
  }
  return panel;
}

const hasDetail = (item) => item.why.length > 0 || item.cards.length > 0;

/** An opener and the panel it shows: the button toggles the panel and remembers it. */
function disclosure(item, ctx, button) {
  const panel = whyPanel(item, ctx);
  const isOpen = openRows.has(item.id);
  panel.hidden = !isOpen;
  button.setAttribute("aria-expanded", String(isOpen));
  button.setAttribute("aria-controls", panel.id);
  button.addEventListener("click", () => {
    const now = panel.hidden;
    panel.hidden = !now;
    if (now) openRows.add(item.id);
    else openRows.delete(item.id);
    button.setAttribute("aria-expanded", String(now));
  });
  return panel;
}

function itemRow(item, ctx) {
  const label = h("span", { class: "metric__label" }, dotFor(item), item.label);
  const value = h("span", { class: "metric__value" }, valueBlock(item));
  if (!hasDetail(item)) return h("div", { class: "metric" }, h("div", { class: "metric__row" }, label, value));
  const button = h("button", { type: "button", class: "metric__row" }, label, value);
  return h("div", { class: "metric" }, button, disclosure(item, ctx, button));
}

const SOURCE_COLORS = { white: "w", blue: "u", black: "b", red: "r", green: "g" };

/** A colored dot before "Green sources": the color is the last word of the id (sources_green). */
function dotFor(item) {
  const match = /^sources_(\w+)$/.exec(item.id);
  const color = match && SOURCE_COLORS[match[1]];
  return color ? h("span", { class: `mana-${color}`, "aria-hidden": "true", text: "● " }) : null;
}

// ------------------------------------------------------------------------------------------------ folded pictures

const isCurve = (item) => /^curve_\d+$/.test(item.id);
const isAnswer = (item) => /^answers_\w+$/.test(item.id);
const isStyle = (item) => /^style_\w+$/.test(item.id);

/** The mana curve: one column for each mana value, as tall as its count is against the biggest count. */
function curveChart(items) {
  const shown = items.filter((item) => !(item.value === 0 && item.id === "curve_0"));
  const most = Math.max(1, ...shown.map((item) => (ui.isNumber(item.value) ? item.value : 0)));
  const word = (item) => (/ or more$/.test(item.label) ? `${item.id.slice(6)}+` : item.id.slice(6));
  const columns = { gridTemplateColumns: `repeat(${shown.length}, minmax(0, 1fr))` };
  return h("div", { class: "metric metric--chart" },
    h("div", { class: "metric__row metric__row--static" }, h("span", { class: "metric__label", text: "Mana curve" }),
      h("span", { class: "metric__value metric__band", text: "cards by mana value" })),
    h("div", {
      class: "curve", style: columns, role: "img",
      "aria-label": `Mana curve: ${shown.map((item) => `${word(item)} mana ${ui.valueText(item.value)}`).join(", ")}`,
    }, shown.map((item) => h("div", { class: "curve__col" },
      h("span", { class: "curve__n", text: ui.valueText(item.value) }),
      h("span", { class: "curve__bar", style: { height: `${Math.round(100 * (ui.isNumber(item.value) ? item.value : 0) / most * 0.72)}%` } })))),
    h("div", { class: "curve__labels", style: columns, "aria-hidden": "true" }, shown.map((item) => h("span", { text: word(item) }))));
}

// A cell is about 58 px wide, so the long words get a place to break (as the artboard does by hand).
const SOFT_HYPHENS = { enchantments: "enchant\u00adments", planeswalkers: "planes\u00adwalkers", graveyards: "grave\u00adyards" };
const softHyphens = (word) => SOFT_HYPHENS[word.toLowerCase()] || word;

/** The answers to each kind of threat, as cells: the count, what it answers, and the count in the base deck. */
function answerCells(items, ctx) {
  const detail = h("div", {});
  const cells = h("div", { class: "cells", role: "group", "aria-label": "Answers to each threat" });
  for (const item of items) {
    const panel = whyPanel(item, ctx);
    panel.hidden = true;
    const short = item.status === "short";
    const word = softHyphens(item.label.replace(/^Answers to /, ""));
    const moved = ui.hasMoved(item);
    const cell = h("button", { type: "button", class: short ? "cell is-short" : "cell", "aria-expanded": "false", "aria-controls": panel.id },
      h("span", { class: "cell__n", text: ui.valueText(item.value, item.unit) }),
      h("span", { class: "cell__l", text: ui.capitalize(word) + (short ? " · short" : "") }),
      moved ? h("span", { class: "cell__b", text: `(${ui.valueText(item.base, item.unit)})` }) : null);
    cell.addEventListener("click", () => {
      const opening = panel.hidden;
      for (const other of detail.children) other.hidden = true;
      for (const other of cells.children) other.setAttribute("aria-expanded", "false");
      panel.hidden = !opening;
      cell.setAttribute("aria-expanded", String(opening));
    });
    detail.append(panel);
    cells.append(cell);
  }
  return h("div", { class: "metric metric--cells" },
    h("div", { class: "metric__row metric__row--static" }, h("span", { class: "metric__label", text: "Answers to each threat" })), cells, detail);
}

/** The playstyle shares, strongest first, each as a bar as long as its share of the nonland cards. */
function styleBars(items, ctx, chosen) {
  const sorted = [...items].sort((a, b) => (ui.isNumber(b.value) ? b.value : -1) - (ui.isNumber(a.value) ? a.value : -1));
  const rows = sorted.map((item) => {
    const mine = chosen && item.id === `style_${String(chosen).replace(/-/g, "_")}`;
    const fill = h("span", { class: "bar__fill", style: { width: `${Math.max(0, Math.min(100, ui.isNumber(item.value) ? item.value : 0))}%` } });
    const line = h("span", { class: "bar" },
      h("span", { class: mine ? "bar__label is-mine" : "bar__label", text: mine ? `${item.label} (your pick)` : item.label }),
      h("span", { class: "bar__track", "aria-hidden": "true" }, fill),
      h("span", { class: "bar__v", text: ui.valueText(item.value, item.unit) }));
    if (!hasDetail(item)) return h("div", { class: "metric" }, h("div", { class: "metric__row" }, line));
    const button = h("button", { type: "button", class: "metric__row" }, line);
    return h("div", { class: "metric" }, button, disclosure(item, ctx, button));
  });
  return h("div", { class: "metric metric--bars" },
    h("div", { class: "metric__row metric__row--static" }, h("span", { class: "metric__label", text: "How much of each playstyle" }),
      h("span", { class: "metric__value metric__band", text: "share of nonland cards" })), rows);
}

/** Rows for the items of a group, with each consecutive run of one family folded into its picture. */
function drawItems(items, ctx, chosen) {
  const out = [];
  for (let i = 0; i < items.length;) {
    const item = items[i];
    const family = isCurve(item) ? isCurve : isAnswer(item) ? isAnswer : isStyle(item) ? isStyle : null;
    if (!family) {
      out.push(itemRow(item, ctx));
      i += 1;
      continue;
    }
    let end = i;
    while (end < items.length && family(items[end])) end += 1;
    const run = items.slice(i, end);
    out.push(family === isCurve ? curveChart(run) : family === isAnswer ? answerCells(run, ctx) : styleBars(run, ctx, chosen));
    i = end;
  }
  return out;
}

// ----------------------------------------------------------------------------------------------------------- groups

/**
 * One group as a card: its title, its first item as a summary on the right, and its items. `compact` (the panel beside
 * the cards on a desktop) shows only the items that have a band, or the first three when none has, and a button for
 * the rest.
 */
function groupCard(group, ctx, { compact = false, chosen } = {}) {
  const lead = group.items[0];
  const body = h("div", { class: "mgroup__items" });
  const all = group.items;
  let subset = all;
  if (compact) {
    subset = all.filter(isChecked);
    if (!subset.length) subset = all.slice(0, 3);
  }
  const more = compact && subset.length < all.length;
  const draw = () => {
    const expanded = !compact || openGroups.has(group.id);
    body.replaceChildren(...drawItems(expanded ? all : subset, ctx, chosen));
    toggle.hidden = !more;
    toggle.textContent = expanded ? "Show fewer" : `Show all ${all.length} numbers`;
    toggle.setAttribute("aria-expanded", String(expanded));
  };
  const toggle = h("button", {
    type: "button", class: "more",
    onclick: () => { if (openGroups.has(group.id)) openGroups.delete(group.id); else openGroups.add(group.id); draw(); },
  });
  const card = h("section", { class: "mgroup", "aria-label": group.label },
    h("div", { class: "mgroup__head" }, h("h2", { class: "mgroup__title", text: group.label }),
      lead && ui.isNumber(lead.value) ? h("span", { class: "mgroup__key", text: `${lead.label.toLowerCase()} ${ui.valueText(lead.value, lead.unit)}` }) : null),
    body, toggle);
  draw();
  return card;
}

function context(app, deck) {
  return { link: (name) => app.link.card(deck.player, deck.id, name) };
}

/** The Metrics tab: every group in full, then a way into the changes from the base deck. */
export function metricsTab(app, deck) {
  const data = deck.data;
  const ctx = context(app, deck);
  const groups = data.metrics.groups.filter((g) => g.id !== "changes");
  const changes = data.metrics.groups.find((g) => g.id === "changes");
  const added = changes && changes.items.find((item) => item.id === "changes_added");
  const cut = changes && changes.items.find((item) => item.id === "changes_cut");
  const wrap = h("div", { class: app.saving ? "groups is-faded" : "groups" },
    h("p", { class: "muted small", text: `Numbers after “from” and grey numbers in brackets are the base deck, ${data.base.name}.` }),
    groups.map((group) => groupCard(group, ctx, { chosen: data.spec.playstyle })));
  if (changes) {
    wrap.append(h("a", { class: "linkcard", href: app.link.deck(deck.player, deck.id, "changes") },
      h("span", { class: "linkcard__title", text: "Changes from the base deck" }),
      added && cut ? h("span", { class: "linkcard__v", text: `+${ui.valueText(added.value)} −${ui.valueText(cut.value)} ›` }) : null));
  }
  return wrap;
}

/** The panel beside the cards on a desktop: every group, compact. */
export function aside(app, deck) {
  const data = deck.data;
  const ctx = context(app, deck);
  const groups = data.metrics.groups.filter((g) => g.id !== "changes");
  return h("aside", { class: app.saving ? "aside is-faded" : "aside", "aria-label": "Metrics" },
    groups.map((group) => groupCard(group, ctx, { compact: true, chosen: data.spec.playstyle })),
    h("a", { class: "more", href: app.link.deck(deck.player, deck.id, "metrics"), text: "All metrics" }));
}
