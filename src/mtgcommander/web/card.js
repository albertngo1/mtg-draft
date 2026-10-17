// The card sheet: one card over the deck, with the tool's numbers for it. It asks the server for the sheet
// (GET /api/cards/NAME?deck=PLAYER/ID) and draws what comes back: the picture (with a flip for two-faced cards), the
// rules text, why the card is in the deck, how its removal power is made, what cutting it would change, the best
// cards to put in its place, and the Cut and Swap buttons.
import { callReady, cardSheetPath } from "./api.js";
import * as ui from "./ui.js";
import { statusMark } from "./metrics.js";
const { h } = ui;
/** The name of the change that put a card in the deck, from the change log: {n, label, replaced} or null. */
function addedBy(name, changes) {
    for (const change of [...changes].reverse()) {
        if (change.op === "undo" || change.undone)
            continue;
        const items = change.op === "group" ? change.items || [] : [change];
        for (const item of [...items].reverse()) {
            if ((item.op === "add" || item.op === "swap") && item.add === name) {
                return { n: change.n, label: change.op === "group" ? change.label ?? null : null, replaced: item.op === "swap" ? item.cut ?? null : null };
            }
        }
    }
    return null;
}
/** "in 39% of 1,125 Bracket 3 Hazel decks (...)" -> the same sentence with the first clause in gold. */
function evidenceSentence(text) {
    const match = /\d+% of [\d,]+ [^(;]*?decks/.exec(text);
    const sentence = ui.capitalize(text);
    if (!match)
        return [sentence];
    const at = sentence.indexOf(match[0]);
    return [sentence.slice(0, at), h("b", { text: match[0] }), sentence.slice(at + match[0].length)];
}
/** Open the sheet for the card called `name`. Returns the sheet (see ui.openSheet). */
export function open(app, name, options) {
    let closed = false;
    const sheet = ui.openSheet({ ...options, onDestroy: () => { closed = true; } });
    const { player, id } = app.state.route; // a sheet only opens over a deck
    const st = { back: false, answer: null, error: null, progress: null, quiet: false };
    sheet.setTitle(name);
    const known = () => {
        const data = app.state.deck && app.state.deck.data;
        return data ? [...data.commanders, ...data.cards, ...data.cut_cards].find((c) => c.name === name) : null;
    };
    async function load() {
        st.error = null;
        st.answer = null;
        draw();
        try {
            const answer = await callReady("GET", cardSheetPath(name, player, id), undefined, {
                onProgress: (progress) => { st.progress = progress; if (!closed)
                    draw(); },
                keepGoing: () => !closed,
            });
            if (closed || answer.status === 202)
                return;
            st.answer = answer.body;
        }
        catch (e) {
            if (closed)
                return;
            st.error = e;
        }
        draw();
    }
    function draw() {
        const keep = sheet.body.scrollTop;
        const a = st.answer;
        const card = a ? a.card : known();
        sheet.setTitle(card ? card.name : name);
        sheet.setSub(card ? ui.typeLine(card) : "");
        const data = app.state.deck && app.state.deck.data;
        const fresh = data && data.cards.find((c) => c.name === (card ? card.name : name));
        sheet.setBadge(fresh && fresh.new ? ui.badge("NEW") : null);
        const parts = [];
        if (card)
            parts.push(imageBlock(card));
        if (st.error)
            parts.push(failure(st.error));
        else if (!a)
            parts.push(ui.waitingBanner(st.progress && st.progress.message ? st.progress : { message: "Loading the card" }));
        else
            parts.push(...details(a, data));
        sheet.body.replaceChildren(...parts);
        sheet.body.scrollTop = keep;
    }
    function imageBlock(card) {
        const flip = card.image_back ? ui.button({
            label: "Flip card", kind: "outline", size: "small", icon: "flip",
            ariaLabel: st.back ? "Show the front face" : "Show the back face",
            onClick: () => { st.back = !st.back; draw(); },
        }) : null;
        return h("div", { class: "cardsheet__image" }, ui.cardTile(card, { size: "large", back: st.back, lazy: false }), flip);
    }
    function failure(error) {
        if (error.kind === "not_found") {
            const close = (error.details && error.details.suggestions) || [];
            return ui.banner({
                tone: "bad", title: "No such card.", text: error.message,
                children: close.length ? [h("div", { class: "chips chips--wrap" }, close.map((n) => ui.chip({ label: n, href: app.link.card(player, id, n) })))] : [],
            });
        }
        return ui.failureBanner(error, { retry: load });
    }
    function details(a, data) {
        const card = a.card;
        const out = [];
        if (a.flag) {
            out.push(ui.banner({ tone: "warn", title: "Kept out:", text: a.flag.reason }));
        }
        if (card.text || card.power) {
            const lines = [card.text, card.power !== null && card.power !== undefined && card.power !== "" ? `${card.power}/${card.toughness}` : ""].filter(Boolean);
            out.push(h("p", { class: "rules" }, ui.symbolText(lines.join("\n"))));
        }
        const tags = h("div", { class: "tags" });
        for (const role of a.roles)
            tags.append(ui.tag(ui.capitalize(role), { on: true }));
        if (a.gc)
            tags.append(ui.tag("Game Changer", { on: true }));
        if (card.owned)
            tags.append(ui.tag("You own it"));
        if (a.salt !== null && a.salt !== undefined)
            tags.append(ui.tag(`Salt ${ui.valueText(a.salt)}`));
        if (a.copies > 1)
            tags.append(ui.tag(`${a.copies} copies in the deck`));
        if (tags.children.length)
            out.push(tags);
        out.push(whySection(a, data));
        if (a.removal)
            out.push(removalSection(a.removal));
        if (a.answers.length)
            out.push(answersSection(a));
        const combos = comboSection(a);
        if (combos)
            out.push(combos);
        if (a.if_cut)
            out.push(ifCutSection(a.if_cut));
        if (a.replacements.length)
            out.push(replacementsSection(a));
        out.push(actions(a));
        out.push(h("p", { class: "footnote", style: { textAlign: "center" }, text: "Card image and text: Scryfall" }));
        if (card.scryfall_uri)
            out.push(ui.button({ label: "Open it on Scryfall", kind: "quiet", size: "small", href: card.scryfall_uri, external: true, className: "btn--block" }));
        return out;
    }
    function whySection(a, data) {
        const section = h("section", {}, ui.subheading("Why it's here"));
        if (a.commander) {
            section.append(h("p", { class: "para", text: "This is the commander. A score says how often other decks play a card, which says nothing about the deck's own commander, so it has none." }));
            return section;
        }
        if (!a.score) {
            section.append(h("p", { class: "para", text: "No score for this card." }));
            return section;
        }
        section.append(h("p", { class: "para" }, evidenceSentence(a.score.evidence)));
        const parts = a.score.parts;
        const mono = h("p", { class: "mono-line" }, "score ", h("b", { text: ui.valueText(a.score.value) }));
        mono.append(` · base ${ui.valueText(parts.base)}`);
        if (Math.abs(parts.resid) >= 0.005)
            mono.append(` · adjustment ${ui.signed(parts.resid)}`);
        mono.append(` · theme ${ui.signed(parts.theme)} · salt ${ui.valueText(parts.salt)}`);
        section.append(mono);
        const by = a.copies > 0 && data ? addedBy(a.card.name, data.version.changes || []) : null;
        if (by) {
            section.append(h("p", { class: "para muted small", text: `Added in change ${by.n}${by.label ? ` (“${by.label}”)` : ""}${by.replaced ? `, replacing ${by.replaced}` : ""}.` }));
        }
        return section;
    }
    function removalSection(removal) {
        const w = removal.weights;
        const k = removal.kinds;
        const factors = [
            [ui.capitalize(k.speed), w.speed], [ui.capitalize(k.reach), w.reach], [ui.capitalize(k.permanence), w.permanence], [k.cost, w.cost],
        ];
        if (k.repeatable)
            factors.push(["Repeats", w.repeatable]);
        return h("section", {}, ui.subheading(`${removal.role === "wipe" ? "Board wipe" : "Removal"} power ${ui.valueText(removal.value)}`), h("div", { class: "factors" }, factors.map(([word, weight]) => h("span", { class: "factor" }, word, h("i", { text: `×${ui.valueText(weight)}` })))), h("p", { class: "mono-line muted", text: removal.line }));
    }
    function answersSection(a) {
        return h("section", {}, ui.subheading("Answers"), h("div", { class: "factors" }, a.answers.map((word) => h("span", { class: "factor on", text: ui.capitalize(word) }))));
    }
    function comboSection(a) {
        if (!a.combos)
            return null;
        const lines = (list, lead) => list.map((combo) => h("p", { class: "para" }, h("b", { text: `${lead}: ` }), `${combo.cards.join(" + ")} → ${combo.produces.join(", ")} (${combo.min_bracket > 1 ? `Bracket ${combo.min_bracket} and up` : "any bracket"})`));
        const rows = [...lines(a.combos.in_deck, "In the deck"), ...lines(a.combos.would_complete, "Would complete")];
        return rows.length ? h("section", {}, ui.subheading("Combos"), rows) : null;
    }
    function ifCutSection(cut) {
        // Cutting one card moves many numbers a little (every share has one card fewer to divide by), so lead with the deck
        // score and the numbers whose status changes, and fold the rest behind a tap.
        const score = cut.items.find((item) => item.id === "score");
        const changed = cut.items.filter((item) => item.id !== "score" && item.status_before !== item.status);
        const quiet = cut.items.filter((item) => item.id !== "score" && item.status_before === item.status);
        const section = h("section", {}, ui.subheading("If you cut it"));
        const grid = h("div", { class: "ifcut" });
        if (score || cut.score_change !== null) {
            grid.append(h("span", { text: "Deck score" }), h("span", { class: "mono" }, score ? `${ui.valueText(score.before)} → ${ui.valueText(score.after)}` : "", cut.score_change !== null ? ` (${ui.signed(cut.score_change)})` : ""));
        }
        for (const item of changed)
            grid.append(...movedRow(item, true));
        if (grid.children.length)
            section.append(grid);
        if (!changed.length)
            section.append(h("p", { class: "para muted small", text: "No number leaves the range it is in." }));
        if (quiet.length) {
            const more = h("div", { class: "ifcut" }, quiet.map((item) => movedRow(item, false)));
            more.hidden = !st.quiet;
            const toggle = ui.button({
                label: `${quiet.length} other ${quiet.length === 1 ? "number moves" : "numbers move"} slightly`, kind: "quiet", size: "small",
                onClick: () => { st.quiet = !st.quiet; more.hidden = !st.quiet; toggle.setAttribute("aria-expanded", String(st.quiet)); },
            });
            toggle.setAttribute("aria-expanded", String(st.quiet));
            section.append(toggle, more);
        }
        return section;
    }
    /** One line of "if you cut it": the label, then before → after, the after in its status color. */
    function movedRow(item, showStatus) {
        const after = h("b", { class: item.status === "short" ? "is-short" : item.status === "over" ? "is-over" : null, text: ui.valueText(item.after, item.unit) });
        const right = h("span", { class: "mono" }, `${ui.valueText(item.before, item.unit)} → `, after);
        const mark = showStatus ? statusMark(item.status) : null;
        if (mark)
            right.append(" ", mark);
        return [h("span", { text: item.label }), right];
    }
    function replacementsSection(a) {
        const cardName = a.card.name;
        return h("section", {}, ui.subheading("Best replacements"), a.replacements.map((r) => ui.cardRow(r.card, {
            more: `deck score ${ui.signed(r.gain)} · ${r.evidence}`,
            action: ui.button({
                label: "Swap", kind: "gold", size: "small", ariaLabel: `Swap ${cardName} for ${r.card.name}`,
                onClick: () => { app.change({ op: "swap", cut: cardName, add: r.card.name }); app.closeSheet(); },
            }),
        })));
    }
    function actions(a) {
        const cardName = a.card.name;
        if (a.commander)
            return h("p", { class: "para muted", text: "The commander cannot be cut." });
        if (a.copies > 0) {
            return h("div", { class: "stack" }, a.copies > 1 ? h("p", { class: "para muted small", text: `You have ${a.copies} copies. Cut removes one of them.` }) : null, h("div", { class: "btnrow" }, 
            // one sheet replaces the other in the history, so Back and Esc from the Add sheet return to the deck
            ui.button({ label: "Swap for…", kind: "gold", size: "big", onClick: () => app.replace(app.link.add(player, id, { cut: cardName })), className: "btn--block" }), ui.button({
                label: "Cut", kind: "danger", size: "big", className: "btn--block", ariaLabel: `Cut ${cardName}`,
                onClick: () => { app.change({ op: "cut", card: cardName }); app.closeSheet(); },
            })));
        }
        if (a.flag)
            return h("p", { class: "para muted", text: "This card cannot be added to the deck." });
        return ui.button({ label: "Add to the deck", kind: "primary", size: "big", icon: "plus", onClick: () => app.replace(app.link.add(player, id, { card: cardName })) });
    }
    load();
    return sheet;
}
