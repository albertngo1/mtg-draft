// The shared pieces, one copy of each: the card tile, chip, stat, toast, banner, sheet and button, plus the few small
// helpers they need (building elements, icons, mana symbols, number and date formatting). Every screen draws these and
// none draws its own, so a change to how a card or a button looks is made once, here and in styles.css.
//
// Nothing here ever puts server text into markup: elements are built with textContent, never innerHTML, so a card
// or a deck called "<img onerror=...>" is shown as text.
import { TIMEOUT_MS } from "./api.js";
const SVG_NS = "http://www.w3.org/2000/svg";
/** h("div", {class: "x", onclick: fn}, child, "text", [more children]) -> an element. */
export function h(tag, props, ...children) {
    const el = document.createElement(tag);
    for (const [key, value] of Object.entries(props || {})) {
        if (value === undefined || value === null)
            continue;
        if (key === "class")
            el.className = value;
        else if (key === "text")
            el.textContent = value;
        else if (key === "dataset")
            Object.assign(el.dataset, value);
        else if (key === "style") {
            for (const [name, v] of Object.entries(value)) {
                if (name.startsWith("--"))
                    el.style.setProperty(name, v);
                else
                    el.style[name] = v;
            }
        }
        else if (key.startsWith("on") && typeof value === "function")
            el.addEventListener(key.slice(2).toLowerCase(), value);
        else if (key === "value" || key === "checked" || key === "disabled" || key === "hidden" || key === "open")
            el[key] = value;
        else if (value === false) {
            if (key.startsWith("aria-"))
                el.setAttribute(key, "false");
        }
        else if (value === true)
            el.setAttribute(key, key.startsWith("aria-") ? "true" : "");
        else
            el.setAttribute(key, String(value));
    }
    append(el, children);
    return el;
}
/** Add children (nodes, text, numbers, or nested arrays of them; null and false are skipped). */
export function append(parent, children) {
    for (const child of children.flat(Infinity)) {
        if (child === null || child === undefined || child === false)
            continue;
        parent.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return parent;
}
const ICONS = {
    back: ["M15 18l-6-6 6-6"],
    plus: ["M12 5v14M5 12h14"],
    close: ["M6 6l12 12M18 6L6 18"],
    chevron: ["M6 9l6 6 6-6"],
    search: ["M4 11a7 7 0 1 0 14 0a7 7 0 1 0 -14 0", "M20 20l-3.5-3.5"],
    flip: ["M3 12a9 9 0 0 1 15.5-6.2L21 8", "M21 3v5h-5", "M21 12a9 9 0 0 1-15.5 6.2L3 16", "M3 21v-5h5"],
};
/** A small stroke icon. Icons are decoration: the button that holds one carries the label. */
export function icon(name, size = 20) {
    const svg = document.createElementNS(SVG_NS, "svg");
    for (const [key, value] of Object.entries({
        width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": 2,
        "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true", focusable: "false",
    }))
        svg.setAttribute(key, String(value));
    for (const d of ICONS[name] || []) {
        const path = document.createElementNS(SVG_NS, "path");
        path.setAttribute("d", d);
        svg.append(path);
    }
    return svg;
}
/** The small gold diamond of the brand. */
export function pip(size = 12) {
    const svg = document.createElementNS(SVG_NS, "svg");
    for (const [key, value] of Object.entries({ width: size, height: size, viewBox: "0 0 12 12", "aria-hidden": "true" })) {
        svg.setAttribute(key, String(value));
    }
    svg.setAttribute("class", "brand__pip");
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", "M6 0l6 6-6 6-6-6z");
    path.setAttribute("fill", "currentColor");
    svg.append(path);
    return svg;
}
// ------------------------------------------------------------------------------------------------- numbers and dates
const NUMBER = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const NUMBER_1 = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
export const isNumber = (value) => typeof value === "number" && Number.isFinite(value);
/** 12.5 -> "$12.50", 2211.9 -> "$2,211.90". */
export function money(value) {
    return isNumber(value) ? `$${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";
}
/** 185.43 -> "$185". */
export function moneyWhole(value) {
    return isNumber(value) ? `$${Math.round(value).toLocaleString("en-US")}` : "—";
}
/** An amount a person chose, as they would write it: 25 -> "$25", 12.5 -> "$12.50". */
export function dollars(value) {
    return Number.isInteger(value) ? moneyWhole(value) : money(value);
}
/** A card's price as the pages show it: "price unknown" when nothing prices it. */
export function priceText(card) {
    return isNumber(card && card.price) ? money(card.price) : "price unknown";
}
/** A metric's value with its unit ("%", "$" or none); "—" when the server could not work it out. */
export function valueText(value, unit) {
    if (!isNumber(value))
        return "—";
    if (unit === "%")
        return `${NUMBER_1.format(value)}%`;
    if (unit === "$")
        return money(value);
    return NUMBER.format(value);
}
/**
 * A change with its sign and unit: 14 -> "+14", -2 -> "−2" (the real minus sign), 4.5 with "%" -> "+4.5%", 12.5 with "$" ->
 * "+$12.50". Its size is written the way `valueText` writes a value, or the way `format` does when the number beside it is
 * written another way. A change of zero has no sign, and "—" stands for no number.
 */
export function signedValue(change, unit, format = valueText) {
    if (!isNumber(change))
        return "—";
    return `${change > 0 ? "+" : change < 0 ? "−" : ""}${format(Math.abs(change), unit)}`;
}
/** A number with a sign, for a change: 0.74 -> "+0.74". */
export function signed(value) {
    return signedValue(value, null);
}
export function oneDecimal(value) {
    return isNumber(value) ? NUMBER_1.format(value) : "—";
}
/** "today", "yesterday", "3 days ago", or a date for anything older than a month. */
export function when(iso, now = new Date()) {
    const then = new Date(iso);
    if (Number.isNaN(then.getTime()))
        return "";
    const day = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
    const days = Math.round((day(now) - day(then)) / 86400000);
    if (days <= 0)
        return "today";
    if (days === 1)
        return "yesterday";
    if (days < 30)
        return `${days} days ago`;
    return then.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}
/** "Oct 11" from an ISO time. */
export function shortDate(iso) {
    const then = new Date(iso);
    return Number.isNaN(then.getTime()) ? "" : then.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
export const capitalize = (text) => (text ? text[0].toUpperCase() + text.slice(1) : text);
/**
 * Where a free card comes from, from the server's `owned_from`: ["Peace Offering"] -> "from Peace Offering", two boxes ->
 * "from Peace Offering or Family Matters", more -> "from Peace Offering, Family Matters or 3 more"; "" for none. The same
 * words as the terminal's report (render.boxes_text).
 */
export function fromBoxes(names) {
    const boxes = names || [];
    if (!boxes.length)
        return "";
    if (boxes.length <= 2)
        return `from ${boxes.join(" or ")}`;
    return `from ${boxes[0]}, ${boxes[1]} or ${boxes.length - 2} more`;
}
/** The last two folders of a path: "/Users/andy/mtg-draft/commander/decks" -> "commander/decks". */
export function pathTail(path) {
    return String(path || "").split(/[\\/]/).filter(Boolean).slice(-2).join("/");
}
// ---------------------------------------------------------------------------------------------- mana and colors
const COLOR_ORDER = "WUBRG";
// Scryfall draws every symbol as a picture in SYMBOL_FOLDER, named <FILE>.svg, where FILE is the symbol with its braces
// and slashes left out ({W/U} is WU, {2/W} is 2W, {G/P} is GP) except for two: {½} is HALF and {∞} is INFINITY. These are
// the 84 symbols of the list Scryfall publishes for its symbols (read 2026-10-12). A symbol that is not in it is not drawn
// as a picture, so a new one shows as text until it is added here.
const SYMBOL_FOLDER = "https://svgs.scryfall.io/card-symbols/";
const SYMBOL_FILE = { "½": "HALF", "∞": "INFINITY" };
const SYMBOLS = new Set([
    "W U B R G C S L D X Y Z H HW HR T Q E P PW CHAOS A TK", // mana, and what stands beside it
    "0 ½ 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 100 1000000 ∞", // generic mana
    "W/U W/B B/R B/G U/B U/R R/G R/W G/W G/U C/W C/U C/B C/R C/G 2/W 2/U 2/B 2/R 2/G", // hybrid
    "W/P U/P B/P R/P G/P C/P B/G/P B/R/P G/U/P G/W/P R/G/P R/W/P U/B/P U/R/P W/B/P W/U/P", // Phyrexian: pay 2 life instead
].join(" ").split(" "));
/** The address of the picture of a symbol such as "{W/U}", or null when Scryfall's list has no such symbol. */
export function symbolUrl(symbol) {
    const name = (/^\{([^{}]+)\}$/.exec(symbol) || [])[1];
    if (name === undefined || !SYMBOLS.has(name))
        return null;
    return `${SYMBOL_FOLDER}${SYMBOL_FILE[name] || name.replace(/\//g, "")}.svg`;
}
/** A symbol as text, the way the pages drew every symbol before the pictures: its braces, a color's letter in its color. */
function symbolAsText(symbol) {
    const name = symbol.slice(1, -1);
    return h("span", { class: "mana-text" }, "{", h("span", { class: /^[WUBRG]$/.test(name) ? `mana-${name.toLowerCase()}` : null, text: name }), "}");
}
/**
 * One symbol, "{B}", as Scryfall's picture of it: the symbol is its alt text and the picture is as tall as the text it
 * sits in (styles.css). When the picture does not load (offline, blocked) or the symbol is not in the list, it is the text.
 */
export function manaSymbol(symbol) {
    const src = symbolUrl(symbol);
    if (!src)
        return symbolAsText(symbol);
    const img = h("img", { class: "mana-sym", src, alt: symbol });
    img.addEventListener("error", () => img.replaceWith(symbolAsText(symbol)));
    return img;
}
/** Text with symbols in it ("{T}: Add {G}.") -> its words and a symbol for each {...}, as a list of nodes for an element. */
export function symbolText(text) {
    const parts = String(text || "").split(/(\{[^{}]*\})/); // words and symbols alternate: the symbols sit at odd places
    return parts.map((part, i) => (i % 2 ? manaSymbol(part) : part)).filter((part) => part !== "");
}
/** "{2}{B}{G}" -> the cost drawn with Scryfall's symbols. A two-faced card's "{1}{G} // {2}{W}" keeps its slashes. */
export function manaCost(cost) {
    const faces = String(cost || "").split(" // ");
    return h("span", { class: "mana" }, faces.map((face, i) => [i ? " // " : null, symbolText(face)]));
}
/** "BG" or ["G", "B"] -> the letters in WUBRG order, each in its color. */
export function colorLetters(ci) {
    const letters = [...new Set(Array.isArray(ci) ? ci.join("") : String(ci || ""))]
        .filter((c) => COLOR_ORDER.includes(c)).sort((a, b) => COLOR_ORDER.indexOf(a) - COLOR_ORDER.indexOf(b));
    if (!letters.length)
        return h("span", { class: "mono", text: "colorless" });
    return h("span", { class: "mono" }, letters.map((c) => h("span", { class: `mana-${c.toLowerCase()}`, text: c })));
}
/** The color identity of a list of cards (commanders): the letters of all of them. */
export function colorsOf(cards) {
    return [...new Set(cards.map((c) => c.ci || "").join(""))].join("");
}
const COLOR_WORDS = { W: "white", U: "blue", B: "black", R: "red", G: "green" };
/** "BG" -> "black and green". */
export function colorWords(ci) {
    const words = [...COLOR_ORDER].filter((c) => String(ci || "").includes(c)).map((c) => COLOR_WORDS[c]);
    if (!words.length)
        return "no colors";
    return words.length === 1 ? words[0] : `${words.slice(0, -1).join(", ")} and ${words[words.length - 1]}`;
}
/** "Legendary Creature — Squirrel Warlock" -> "Legendary Creature". */
export function mainType(typeLine) {
    return String(typeLine || "").split(" — ")[0].split(" // ")[0];
}
/** Cost, type and price of a card on one line: {2}{B}{G} · Instant · $0.97. */
export function typeLine(card) {
    const bits = [];
    if (card.cost)
        bits.push(manaCost(card.cost));
    if (card.type)
        bits.push(mainType(card.type));
    bits.push(priceText(card));
    const out = h("span", { class: "cardrow__type" });
    bits.forEach((bit, i) => out.append(i ? " · " : "", bit));
    return out;
}
/**
 * A button, or a link when `href` is given. kind: primary (gold fill), gold (gold outline), danger (red outline),
 * quiet (text only) or outline (the default). It is always at least 44 px tall. `busy` shows a spinner and ignores taps.
 */
export function button({ label, kind = "outline", size, icon: iconName, href, onClick, ariaLabel, busy = false, disabled = false, focusKey, title, className, type = "button", external = false } = {}) {
    const el = h(href ? "a" : "button", {
        class: ["btn", `btn--${kind}`, size ? `btn--${size}` : "", busy ? "is-busy" : "", className || ""].filter(Boolean).join(" "),
        href, type: href ? undefined : type, "aria-label": ariaLabel, title, "data-focus-key": focusKey,
        target: href && external ? "_blank" : undefined, rel: href && external ? "noopener noreferrer" : undefined,
        disabled: !href && (disabled || busy) ? true : undefined,
        "aria-disabled": href && disabled ? "true" : undefined,
        "aria-busy": busy ? "true" : undefined,
    }, iconName ? icon(iconName, 16) : null, label !== undefined ? h("span", { text: label }) : null);
    if (onClick)
        el.addEventListener("click", onClick);
    return el;
}
/** A round 44 px button that holds only an icon; `label` is what a screen reader says. */
export function iconButton({ icon: iconName, label, href, onClick, focusKey }) {
    const el = h(href ? "a" : "button", {
        class: "iconbtn", href, type: href ? undefined : "button", "aria-label": label, title: label, "data-focus-key": focusKey,
    }, icon(iconName));
    if (onClick)
        el.addEventListener("click", onClick);
    return el;
}
// ------------------------------------------------------------------------------------------- chips, tags and stats
/**
 * A pill: a filter chip that is pressed or not (with an optional count beside the label), or, given `href`, a link that
 * looks the same (close names to try instead of a name that was not found).
 */
export function chip({ label, count, pressed = false, onClick, disabled, title, focusKey, href }) {
    return h(href ? "a" : "button", {
        type: href ? undefined : "button", class: "chip", href, "aria-pressed": href ? undefined : pressed, onclick: onClick, disabled, title,
        "data-focus-key": focusKey,
    }, label, count !== undefined ? h("b", { text: String(count) }) : null);
}
/** The small gold label ("NEW", "NEW · OWNED"); laid over a tile's corner when `overlay` is set. */
export function badge(text, { overlay = false } = {}) {
    return h("span", { class: overlay ? "badge tile__badge" : "badge", "aria-hidden": overlay ? "true" : undefined, text });
}
/** A small monospace tag; `on` outlines it in gold. */
export function tag(text, { on = false } = {}) {
    return h("span", { class: on ? "tag on" : "tag", text });
}
/** One headline number with its label: stat({value: "93.8", label: "Score", mark: delta(...)}). */
export function stat({ value, label, mark, title, tone, className }) {
    return h("div", { class: ["stat", mark ? "stat--marked" : "", className || ""].join(" ").trim(), title }, h("span", { class: ["stat__n", tone ? `is-${tone}` : ""].join(" ").trim(), text: value }), h("span", { class: "stat__k" }, label, mark ? " " : null, mark));
}
/** True when a metric item moved from the base deck's value: the server sent a `change`, and it is not zero. */
export function hasMoved(item) {
    return isNumber(item.change) && item.change !== 0;
}
/**
 * How far a metric item moved from the base deck's value: "+3.4", or with `showBase` "−2 from 38". The size is the
 * server's own `change`; the pages never subtract. `format` writes the size when the number beside it has its own style
 * (the stat line's one decimal). A screen reader hears "down 2 from 38" in its place. Null when the item did not move.
 */
export function delta(item, { showBase = true, format = valueText } = {}) {
    if (!hasMoved(item))
        return null;
    const change = item.change;
    const was = valueText(item.base, item.unit);
    return h("span", { class: "delta" }, h("span", { "aria-hidden": "true" }, signedValue(change, item.unit, format), showBase ? h("span", { class: "delta__was", text: ` from ${was}` }) : null), h("span", { class: "sr-only", text: `${change > 0 ? "up" : "down"} ${format(Math.abs(change), item.unit)} from ${was}` }));
}
/** A small uppercase heading with a line after it ("Versions", "Creatures · 29"). */
export function sectionLabel(text, { tight = false } = {}) {
    return h("h2", { class: tight ? "section-label section-label--tight" : "section-label", text });
}
/** The same, a size smaller, for the parts of a sheet ("Why it's here"). */
export function subheading(text) {
    return h("h2", { class: "k", text });
}
/**
 * A banner. tone: info, warn (gold border) or bad (red border). `text` may be a string or an array of strings and
 * nodes; `actions` are [{label, kind, onClick}] buttons on its right.
 */
export function banner({ tone = "info", title, text, children, actions = [], role } = {}) {
    const body = h("div", { class: "banner__body" });
    if (title || text) {
        body.append(h("p", {}, title ? h("span", { class: "banner__title", text: title }) : null, title && text ? " " : null, ...[].concat(text || [])));
    }
    for (const child of [].concat(children || []))
        body.append(child);
    const el = h("div", { class: tone === "info" ? "banner" : `banner banner--${tone}`, role: role || (tone === "bad" ? "alert" : "status") }, body);
    if (actions.length) {
        el.append(h("div", { class: "banner__actions" }, actions.map((a) => button({
            label: a.label, kind: a.kind || "outline", size: "small", onClick: a.onClick, busy: a.busy,
        }))));
    }
    return el;
}
/**
 * The banner for a request that failed (an ApiError from api.js). When the server never answered it names what to check:
 * `mtg-commander serve`, and Tailscale when the page was opened from another device. Any other failure shows the server's
 * own words. `retry` adds a Retry button, `note` is extra text ("Your cut of X wasn't saved."), `actions` more buttons.
 */
export function failureBanner(error, { retry, note, actions = [] } = {}) {
    const buttons = [...(retry ? [{ label: "Retry", kind: "primary", onClick: retry }] : []), ...actions];
    if (error.cannotReach) {
        const local = ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname);
        return banner({
            tone: "bad", title: "Can't reach your computer.",
            text: ["Is ", h("code", { text: "mtg-commander serve" }), local ? " still running?" : " running, and is Tailscale on?",
                error.kind === "timeout" ? ` It did not answer within ${Math.round(TIMEOUT_MS / 1000)} seconds.` : "", note ? ` ${note}` : ""],
            actions: buttons,
        });
    }
    return banner({ tone: "bad", title: "The server reported an error:", text: [error.message, note ? ` ${note}` : ""], actions: buttons });
}
/** A line with a spinner: "Finding swaps…". */
export function working(text) {
    return h("div", { class: "working", role: "status" }, h("span", { class: "spinner", "aria-hidden": "true" }), h("span", { text }));
}
/** The first-open panel: what the server is doing, a moving bar, and how many web requests it has made so far. */
export function waitingBanner(progress) {
    const requests = progress && progress.requests;
    return h("div", { class: "banner banner--wait", role: "status" }, h("p", { text: (progress && progress.message) || "Getting the deck ready" }), h("div", { class: "progress", "aria-hidden": "true" }, h("span")), requests ? h("span", { class: "progress__text", text: `${requests} web ${requests === 1 ? "request" : "requests"} so far` }) : null);
}
/** A dashed box that says there is nothing here yet and what to do. */
export function emptyState({ title, text, action } = {}) {
    return h("div", { class: "empty" }, title ? h("div", { class: "empty__title", text: title }) : null, text ? h("p", { text }) : null, action || null);
}
// --------------------------------------------------------------------------------------------------------------- toast
let toastTimer;
/** A short message at the bottom of the screen with an optional action ("Undo"). One at a time; it fades after 8 s. */
export function toast(message, { action, duration = 8000 } = {}) {
    const layer = document.getElementById("toast-layer");
    clearTimeout(toastTimer);
    const el = h("div", { class: "toast" }, h("span", { class: "toast__text", text: message }), action ? button({ label: action.label, kind: "quiet", onClick: () => { dismissToast(); action.onClick(); } }) : null);
    layer.replaceChildren(el);
    const start = () => { clearTimeout(toastTimer); toastTimer = setTimeout(dismissToast, duration); };
    const hold = () => clearTimeout(toastTimer);
    el.addEventListener("pointerenter", hold);
    el.addEventListener("focusin", hold);
    el.addEventListener("pointerleave", start);
    start();
}
export function dismissToast() {
    clearTimeout(toastTimer);
    const layer = document.getElementById("toast-layer");
    if (layer && !layer.querySelector(".noticebox"))
        layer.replaceChildren();
}
/**
 * Put a banner at the bottom of the screen, where it stays until it is dismissed or acted on. This is for the result of
 * a change that failed ("Can't reach your computer", "changed on another device"): a banner inside the page could be
 * scrolled out of sight, and a failure must not be missed. It replaces any toast.
 */
export function postNotice(node) {
    clearTimeout(toastTimer);
    document.getElementById("toast-layer").replaceChildren(h("div", { class: "noticebox" }, node));
}
export function clearNotice() {
    const layer = document.getElementById("toast-layer");
    if (layer && layer.querySelector(".noticebox"))
        layer.replaceChildren();
}
let current = null;
const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
/**
 * A sheet: a dialog over the deck (full height on a phone, centered on a desktop). Esc, the close button and a tap
 * outside call `onDismiss`; the owner then calls `destroy()`. While it is open the page behind it is inert, Tab stays
 * inside it, and on `destroy()` focus goes back to `returnFocus` (an element, or a function that finds it, since the
 * page behind may have been redrawn). Opening a sheet closes any sheet that is already open.
 * `onDestroy` runs when it goes away. Returns {body, setTitle, setSub, setBadge, dismiss, destroy, focus}.
 */
export function openSheet({ onDismiss, onDestroy, returnFocus } = {}) {
    if (current)
        current.destroy({ restoreFocus: false });
    const layer = document.getElementById("sheet-layer");
    const titleBox = h("h1", { class: "sheet__title", id: "sheet-title" });
    const subBox = h("div", { class: "sheet__sub" });
    const badgeBox = h("div", { class: "sheet__badge" });
    const body = h("div", { class: "sheet__body" });
    const closeButton = iconButton({ icon: "close", label: "Close", onClick: () => dismiss() });
    const panel = h("section", { class: "sheet", role: "dialog", "aria-modal": "true", "aria-labelledby": "sheet-title", tabindex: "-1" }, h("header", { class: "sheet__head" }, h("div", { class: "sheet__titles" }, titleBox, subBox), badgeBox, closeButton), body);
    const backdrop = h("div", { class: "sheet-backdrop" }, h("div", { class: "sheet-grip", "aria-hidden": "true" }, h("span")), panel);
    const dismiss = () => { if (onDismiss)
        onDismiss();
    else
        controller.destroy(); };
    backdrop.addEventListener("click", (e) => {
        if (e.target === backdrop || e.target.closest(".sheet-grip"))
            dismiss();
    });
    const onKey = (e) => {
        if (e.key === "Escape" && !e.defaultPrevented) {
            e.preventDefault();
            dismiss();
        }
        else if (e.key === "Tab") {
            const items = [...panel.querySelectorAll(FOCUSABLE)].filter((el) => !el.hidden && el.offsetParent !== null);
            if (!items.length) {
                e.preventDefault();
                panel.focus();
                return;
            }
            const first = items[0];
            const last = items[items.length - 1];
            const active = document.activeElement;
            if (e.shiftKey && (active === first || active === panel || !panel.contains(active))) {
                e.preventDefault();
                last.focus();
            }
            else if (!e.shiftKey && (active === last || !panel.contains(active))) {
                e.preventDefault();
                first.focus();
            }
        }
    };
    document.addEventListener("keydown", onKey);
    const controller = {
        body,
        setTitle(text) { titleBox.textContent = text; },
        setSub(...nodes) { subBox.replaceChildren(); append(subBox, nodes); },
        setBadge(node) { badgeBox.replaceChildren(); if (node)
            badgeBox.append(node); },
        dismiss,
        focus(el) { (el || panel).focus({ preventScroll: true }); },
        destroy({ restoreFocus = true } = {}) {
            if (current !== controller)
                return;
            current = null;
            if (onDestroy)
                onDestroy();
            document.removeEventListener("keydown", onKey);
            backdrop.remove();
            document.documentElement.classList.remove("has-sheet");
            for (const id of ["topbar", "main"]) {
                const el = document.getElementById(id);
                if (el)
                    el.inert = false;
            }
            const target = typeof returnFocus === "function" ? returnFocus() : returnFocus;
            if (restoreFocus && target && target.isConnected)
                target.focus({ preventScroll: true });
        },
    };
    current = controller;
    for (const id of ["topbar", "main"]) {
        const el = document.getElementById(id);
        if (el)
            el.inert = true;
    }
    document.documentElement.classList.add("has-sheet");
    layer.append(backdrop);
    panel.focus({ preventScroll: true });
    return controller;
}
export function sheetIsOpen() {
    return current !== null;
}
// -------------------------------------------------------------------------------------------------------- card tiles
function fallbackFor(card) {
    return h("div", { class: "tile__fallback" }, h("span", { class: "tile__fb-name", text: card.name }), card.cost ? h("span", { class: "tile__fb-cost" }, manaCost(card.cost)) : null, card.type ? h("span", { class: "tile__fb-type", text: card.type }) : null);
}
/**
 * The one card tile: the card's picture (loaded lazily), or a text tile with its name, cost and type when it has no
 * picture or the picture fails to load. It is a link when given `href`, a button when given `onClick`.
 *   size    tile (a grid cell, the default), thumb, mini, commander or large
 *   badge   text laid over the corner ("NEW", "NEW · OWNED")
 *   count   copies; shown as ×4 when more than one
 *   pending a word ("Cutting…") that dims the card while its change waits for the server
 *   back    show the back face of a two-faced card
 *   cut     show it dimmed, as a card that was cut
 */
export function cardTile(card, { size = "tile", href, onClick, badge: badgeText, count = 1, pending = "", cut = false, back = false, focusKey, lazy = true } = {}) {
    const words = [card.name, ...(badgeText ? badgeText.toLowerCase().split(" · ") : []), count > 1 ? `${count} copies` : ""].filter(Boolean);
    const tile = h(href ? "a" : onClick ? "button" : "div", {
        class: ["tile", size === "tile" ? "" : `tile--${size}`, pending ? "is-pending" : "", cut ? "is-cut" : ""].filter(Boolean).join(" "),
        href, type: !href && onClick ? "button" : undefined, "data-focus-key": focusKey, "aria-busy": pending ? "true" : undefined,
        "data-card": card.name,
    });
    if (onClick)
        tile.addEventListener("click", onClick);
    const source = back ? card.image_back : card.image;
    if (source) {
        const img = h("img", { src: source, alt: words.join(", "), loading: lazy ? "lazy" : "eager", decoding: "async", draggable: "false" });
        img.addEventListener("error", () => img.replaceWith(fallbackFor(card)));
        tile.append(img);
    }
    else {
        tile.append(fallbackFor(card));
    }
    if (badgeText)
        tile.append(badge(badgeText, { overlay: true }));
    if (count > 1)
        tile.append(h("span", { class: "tile__count", "aria-hidden": "true", text: `×${count}` }));
    if (pending)
        tile.append(h("span", { class: "tile__status", text: pending }));
    return tile;
}
/**
 * A row for a card in a list (search results, replacements, what a card replaces): its thumbnail, name, cost-type-price
 * line, optional `more` text and an `action` on the right. `keptOut` is the reason a card cannot be added, which greys
 * the row and replaces `more`. With `onPick` the whole row is one button.
 */
export function cardRow(card, { more, action, keptOut, onPick, focusKey, extraName } = {}) {
    const main = h("div", { class: "cardrow__main" }, h("div", { class: "cardrow__name" }, card.name, extraName ? h("span", { class: "muted", text: ` ${extraName}` }) : null), typeLine(card), keptOut ? h("div", { class: "cardrow__more" }, h("span", { class: "kept", text: "Kept out:" }), ` ${keptOut}`)
        : more ? h("div", { class: "cardrow__more" }, more) : null);
    const thumb = cardTile(card, { size: "thumb" });
    if (onPick) {
        return h("button", { type: "button", class: "cardrow cardrow--pick", onclick: onPick, "data-focus-key": focusKey }, thumb, main, action ? h("div", { class: "cardrow__action" }, action) : null);
    }
    return h("div", { class: keptOut ? "cardrow cardrow--kept-out" : "cardrow" }, thumb, main, action ? h("div", { class: "cardrow__action" }, action) : null);
}
// -------------------------------------------------------------------------------------------------------------- forms
/** A labelled form field; `control` is the input (give it the id the label points at). */
export function field({ id, label, control, hint, error }) {
    return h("div", { class: "field" }, label ? h("label", { class: "field__label", for: id, text: label }) : null, control, hint ? h("div", { class: "field__hint", id: id ? `${id}-hint` : undefined, text: hint }) : null, error ? h("div", { class: "field__error", role: "alert", text: error }) : null);
}
/** A search box with its icon and a label for screen readers. */
export function searchBox({ id, label, placeholder, value = "", onInput, big = false, autofocus = false }) {
    const input = h("input", {
        id, type: "search", placeholder, value, autocomplete: "off", autocapitalize: "off", spellcheck: "false", enterkeyhint: "search",
        oninput: onInput ? (e) => onInput(e.target.value, e) : undefined,
    });
    if (autofocus)
        input.autofocus = true;
    return {
        input,
        el: h("div", { class: big ? "search search--big" : "search" }, icon("search", 16), h("label", { class: "sr-only", for: id, text: label }), input),
    };
}
