// The screens that are not a deck: Decks (a player's versions and the base decks), New version (choose a base deck, then
// the settings) and New base deck (search the precons, or paste a list).
import { call } from "./api.js";
import * as ui from "./ui.js";
const { h } = ui;
const enc = encodeURIComponent;
/** A player's name as the server wants it for a folder: lowercase letters, digits and hyphens. */
export function playerId(text) {
    return String(text || "").trim().toLowerCase().replace(/['‘’`´]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}
let decksToken = 0;
/** Load the players, the player's versions, the base decks and the uncommitted files for the Decks screen. */
export async function load(app) {
    const { state } = app;
    const token = ++decksToken;
    const previous = state.decks;
    const loading = {
        status: "loading", error: null, player: state.player,
        players: previous ? previous.players : [], bases: previous ? previous.bases : [],
        versions: previous && previous.player === state.player ? previous.versions : [],
        files: [], filesNote: null, root: previous ? previous.root : "", warnings: [],
    };
    state.decks = loading;
    app.render();
    try {
        const [players, bases, status] = await Promise.all([
            call("GET", "/api/players"), call("GET", "/api/bases"),
            call("GET", "/api/status").catch(() => null),
        ]);
        let player = state.player;
        if (!player && players.body.players.length === 1) {
            player = players.body.players[0]; // one player on this computer: no need to ask who is playing
            app.rememberPlayer(player);
        }
        let versions = [];
        let warnings = bases.body.warnings || [];
        if (player && players.body.players.includes(player)) { // a player with no folder yet simply has no versions
            const listed = await call("GET", `/api/decks?player=${enc(player)}`);
            versions = listed.body.versions;
            warnings = warnings.concat(listed.body.warnings || []);
        }
        if (token !== decksToken)
            return;
        state.decks = {
            status: "ready", error: null, player, players: players.body.players, bases: bases.body.bases, versions, warnings,
            files: status ? status.body.uncommitted : [], filesNote: status ? status.body.uncommitted_note : null,
            root: status ? status.body.settings.decks : "",
        };
    }
    catch (e) {
        if (token !== decksToken)
            return;
        loading.status = "error";
        loading.error = e;
    }
    app.render();
}
function brand() {
    return h("a", { class: "brand", href: "#/" }, ui.pip(), "Commander decks");
}
function pluralize(n, one, many = `${one}s`) {
    return `${n} ${n === 1 ? one : many}`;
}
export function decksView(app) {
    const { state } = app;
    const data = state.decks || { status: "loading", error: null, player: null, players: [], versions: [], bases: [], files: [], filesNote: null, root: "", warnings: [] };
    const player = state.player;
    const pill = player ? h("button", {
        type: "button", class: "pill", "aria-haspopup": "dialog", "aria-label": `Player: ${player}. Change player`, "data-focus-key": "player",
        onclick: () => choosePlayer(app),
    }, player, ui.icon("chevron", 14)) : null;
    const topbar = h("div", { class: "topbar__row topbar__row--home" }, brand(), h("span", { class: "topbar__spacer", style: { flex: "1" } }), pill);
    const main = h("div", { class: "page page--list" });
    if (data.status === "error") {
        main.append(ui.failureBanner(data.error, { retry: () => load(app) }));
        return { title: "Decks", topbar, main };
    }
    if (!player) {
        if (data.status === "loading")
            main.append(ui.working("Looking for your decks…"));
        else
            main.append(whoIsPlaying(app, data.players));
        return { title: "Decks", topbar, main };
    }
    const versions = data.versions;
    main.append(h("div", {}, h("h1", { class: "title" }, "Your ", h("span", { class: "accent", text: "decks" })), h("p", { class: "lede", text: data.status === "loading" && !versions.length ? "Loading…" : `${pluralize(versions.length, "version")} · ${pluralize(data.bases.length, "base deck")}` })));
    main.append(h("div", { class: "btnrow" }, ui.button({ label: "New version", kind: "primary", size: "big", icon: "plus", href: app.link.newVersion(), className: "btn--block" }), ui.button({ label: "New base deck", kind: "outline", size: "big", href: app.link.newBase, className: "btn--block" })));
    for (const warning of data.warnings || [])
        main.append(ui.banner({ tone: "warn", text: warning }));
    main.append(h("section", {}, ui.sectionLabel("Versions", { tight: true }), versionsList(app, data)));
    main.append(h("section", {}, ui.sectionLabel("Base decks", { tight: true }), basesList(app, data)));
    main.append(filesLine(data, player));
    return { title: "Decks", topbar, main };
}
function whoIsPlaying(app, players) {
    const panel = h("section", { class: "stack" }, h("h1", { class: "title" }, "Who is ", h("span", { class: "accent", text: "playing" }), "?"), h("p", { class: "lede", text: players.length
            ? "Each player's decks are kept in their own folder. Pick yours, or add a name; this device will remember it."
            : "Nobody has saved a deck on this computer yet. Type a name: each player's decks are kept in their own folder, and this device will remember it." }));
    for (const name of players) {
        panel.append(ui.button({ label: name, kind: "outline", size: "big", onClick: () => app.setPlayer(name) }));
    }
    panel.append(newPlayerForm(app, { someoneNew: players.length > 0 }));
    return panel;
}
function newPlayerForm(app, { onDone, someoneNew = false } = {}) {
    const input = h("input", { id: "new-player", class: "input", type: "text", autocomplete: "off", autocapitalize: "off", spellcheck: "false", placeholder: "Your name" });
    const hint = h("div", { class: "field__hint" });
    const error = h("div", { class: "field__error", role: "alert" });
    const submit = () => {
        const id = playerId(input.value);
        if (!id) {
            error.textContent = "Type a name with at least one letter or number.";
            return;
        }
        if (onDone)
            onDone();
        app.setPlayer(id);
    };
    input.addEventListener("input", () => {
        const id = playerId(input.value);
        error.textContent = "";
        hint.textContent = id && id !== input.value.trim() ? `Saved as “${id}”.` : "";
    });
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") {
        e.preventDefault();
        submit();
    } });
    return h("div", { class: "field" }, h("label", { class: "field__label", for: "new-player", text: someoneNew ? "Someone new" : "Your name" }), h("div", { class: "btnrow" }, h("div", { style: { flex: "1", minWidth: "140px" } }, input), ui.button({ label: "Continue", kind: "primary", onClick: submit })), hint, error);
}
function choosePlayer(app) {
    const sheet = ui.openSheet({
        returnFocus: () => document.querySelector('[data-focus-key="player"]'),
        onDismiss: () => sheet.destroy(),
    });
    sheet.setTitle("Who is playing?");
    const players = (app.state.decks && app.state.decks.players) || [];
    const current = app.state.player;
    const names = !current || players.includes(current) ? players : [current, ...players];
    const list = h("div", { class: "stack", role: "listbox", "aria-label": "Players" });
    for (const name of names) {
        const selected = name === current;
        list.append(h("button", {
            type: "button", class: "baserow", role: "option", "aria-selected": selected,
            onclick: () => { sheet.destroy(); if (!selected)
                app.setPlayer(name); },
        }, h("span", { class: "baserow__main" }, h("span", { class: "baserow__name", text: name })), selected ? h("span", { class: "baserow__count", text: "this device" }) : null));
    }
    sheet.body.append(list, newPlayerForm(app, { onDone: () => sheet.destroy(), someoneNew: true }));
    sheet.focus();
}
function versionsList(app, data) {
    if (data.status === "loading" && !data.versions.length)
        return ui.working("Loading your versions…");
    if (!data.versions.length) {
        return ui.emptyState({
            title: `${app.state.player} has no versions yet`,
            text: data.bases.length ? "A version is your own copy of a base deck, with every change you make to it." : "Start with a base deck: a precon, or a list you paste in.",
            action: ui.button({ label: data.bases.length ? "New version" : "New base deck", kind: "primary", href: data.bases.length ? app.link.newVersion() : app.link.newBase }),
        });
    }
    return h("div", { class: "stack" }, data.versions.map((entry) => versionCard(app, data.player, entry)));
}
function versionCard(app, player, entry) {
    const lead = (entry.commanders || [])[0] || entry.name;
    const head = entry.headline;
    const settings = entry.settings || {};
    const bracket = head && head.bracket !== null && head.bracket !== undefined ? head.bracket : settings.bracket;
    const themes = [].concat(settings.themes || [], settings.playstyle ? [settings.playstyle] : []);
    const top = h("div", { class: "deckcard__top" }, entry.commander_image ? ui.cardTile({ name: lead, image: entry.commander_image, cost: "", type: "" }, { size: "commander" }) : null, h("div", { style: { flex: "1", minWidth: "0" } }, h("div", { class: "deckcard__name", text: entry.name }), h("div", { class: "deckcard__sub", text: entry.error ? "This version cannot be opened" : `${(entry.commanders || []).join(" & ")} · from ${entry.base_name}` })));
    const card = h("a", { class: "deckcard", href: app.link.deck(player, entry.id), "data-focus-key": `deck:${entry.id}` }, top);
    if (entry.error) {
        card.append(h("div", { class: "deckcard__note", text: entry.error }));
        return card;
    }
    card.append(h("div", { class: "deckcard__stats" }, ui.stat({ value: head ? ui.oneDecimal(head.score) : "—", label: "Score" }), ui.stat({ value: String(entry.swaps), label: "Swaps" }), ui.stat({ value: ui.moneyWhole(entry.spent), label: "Spent" })));
    if (!head)
        card.append(h("div", { class: "deckcard__note", text: "Open it to see its numbers: they are worked out from the commander's data." }));
    const tags = h("div", { class: "tags" });
    if (bracket !== undefined && bracket !== null)
        tags.append(ui.tag(`Bracket ${bracket}`, { on: true }));
    for (const word of themes)
        tags.append(ui.tag(word));
    tags.append(ui.tag(ui.when(entry.updated)));
    card.append(tags);
    return card;
}
function basesList(app, data) {
    if (!data.bases.length) {
        return ui.emptyState({
            title: "No base decks yet",
            text: "A base deck is where a version starts: a precon from the list, or a deck list you paste in. It is saved once and never changes.",
            action: ui.button({ label: "New base deck", kind: "primary", href: app.link.newBase }),
        });
    }
    const counts = {};
    for (const entry of data.versions)
        counts[entry.base] = (counts[entry.base] || 0) + 1;
    return h("div", {}, data.bases.map((base) => h("a", { class: "baserow", href: app.link.newVersion(base.id) }, h("div", { class: "baserow__main" }, h("div", { class: "baserow__name", text: base.name }), h("div", { class: "baserow__sub" }, `${(base.commanders || []).join(" & ")}`, base.ci ? " · " : "", base.ci ? ui.colorLetters(base.ci) : null)), h("span", { class: "baserow__count", text: counts[base.id] ? pluralize(counts[base.id], "version") : "no versions" }))));
}
function filesLine(data, player) {
    const folder = data.root ? `${ui.pathTail(data.root)}/${player}` : player;
    let text = folder;
    if (data.filesNote)
        text += ` · ${data.filesNote}`;
    else if (data.files.length)
        text += ` · ${pluralize(data.files.length, "file")} not committed to git yet`;
    else
        text += " · every saved deck file is committed to git";
    return h("p", { class: "footnote", text });
}
// ------------------------------------------------------------------------------------------ New version, New base deck
const BRACKET_NAMES = { 1: "Exhibition", 2: "Core", 3: "Upgraded", 4: "Optimized", 5: "cEDH" };
const PAUSE_MS = 250;
// What each form remembers while it is open. Typing updates these without redrawing, so a keystroke never loses the caret.
const version = { baseId: null, name: "", bracket: 3, budget: "", playstyle: "", themes: new Set(), owned: new Set(), ownedQuery: "", ownedResults: [], busy: false, errors: {}, notice: null };
const base = { mode: "precon", query: "", results: [], status: "idle", busy: false, name: "", list: "", commander: "", problems: [], errors: {}, notice: null, close: [], taken: null };
let formData = { status: "loading", bases: [], menu: null, error: null };
let formToken = 0;
let timer;
function resetVersion(baseId) {
    Object.assign(version, { baseId: baseId || null, name: "", bracket: 3, budget: "", playstyle: "", themes: new Set(), owned: new Set(), ownedQuery: "", ownedResults: [], busy: false, errors: {}, notice: null });
}
function resetBase() {
    Object.assign(base, { mode: "precon", query: "", results: [], status: "idle", busy: false, name: "", list: "", commander: "", problems: [], errors: {}, notice: null, close: [], taken: null });
}
/** Load what the two forms need: the base decks and the menu of playstyles and themes. */
export async function loadForm(app) {
    const route = app.state.route;
    const token = ++formToken;
    if (route.name === "new")
        resetVersion(route.query.base);
    else
        resetBase();
    formData = { status: "loading", bases: formData.bases, menu: formData.menu, error: null };
    app.render();
    try {
        const [bases, menu, players] = await Promise.all([call("GET", "/api/bases"), call("GET", "/api/menu"), call("GET", "/api/players")]);
        if (token !== formToken)
            return;
        formData = { status: "ready", bases: bases.body.bases, menu: menu.body, players: players.body.players, error: null };
        if (!app.state.player && players.body.players.length === 1)
            app.rememberPlayer(players.body.players[0]);
    }
    catch (e) {
        if (token !== formToken)
            return;
        formData = { status: "error", bases: [], menu: null, error: e };
    }
    app.render();
}
function formTopbar(app, title) {
    return h("div", { class: "topbar__row" }, ui.iconButton({ icon: "back", label: "Back to decks", href: app.link.decks }), h("div", { class: "topbar__title" }, h("div", { class: "topbar__name", text: title }))); // the page's own h1 is in the form
}
function formShell(app, title, build) {
    const main = h("div", { class: "page page--narrow" });
    if (formData.status === "error")
        main.append(ui.failureBanner(formData.error, { retry: () => loadForm(app) }));
    else if (formData.status === "loading")
        main.append(ui.working("Loading…"));
    else if (!app.state.player)
        main.append(whoIsPlaying(app, formData.players || []));
    else
        build(main);
    return { title, topbar: formTopbar(app, title), main };
}
const sleepThen = (fn) => { clearTimeout(timer); timer = setTimeout(fn, PAUSE_MS); };
/** A notice is a function that builds its banner, or null. */
function noticeBanner(notice) {
    return notice ? notice() : null;
}
const warning = (title, text) => () => ui.banner({ tone: "warn", title, text });
/** The banner for a form request that failed; Retry sends it again. */
function failureNotice(error, retry) {
    return () => ui.failureBanner(error, { retry });
}
// ---- New version
function chosenBase() {
    return formData.bases.find((b) => b.id === version.baseId) || null;
}
export function newVersionView(app) {
    return formShell(app, "New version", (main) => {
        main.append(h("div", {}, h("h1", { class: "title" }, "New ", h("span", { class: "accent", text: "version" })), h("p", { class: "lede", text: "A version is your own copy of a base deck, with every change you make to it." })));
        const chosen = chosenBase();
        if (!chosen) {
            main.append(basePicker(app));
            return;
        }
        main.append(versionForm(app, chosen));
    });
}
function basePicker(app) {
    const out = h("section", {}, ui.sectionLabel("Choose a base deck", { tight: true }));
    if (!formData.bases.length) {
        out.append(ui.emptyState({
            title: "No base decks yet", text: "A version starts from a base deck: a precon from the list, or a deck list you paste in.",
            action: ui.button({ label: "New base deck", kind: "primary", href: app.link.newBase }),
        }));
        return out;
    }
    for (const entry of formData.bases) {
        out.append(h("button", {
            type: "button", class: "baserow", "data-focus-key": `base:${entry.id}`,
            onclick: () => { version.baseId = entry.id; app.render(); },
        }, entry.commander_image ? ui.cardTile({ name: (entry.commanders || [])[0] || entry.name, image: entry.commander_image, cost: "", type: "" }, { size: "commander" }) : null, h("span", { class: "baserow__main" }, h("span", { class: "baserow__name", text: entry.name }), h("span", { class: "baserow__sub" }, `${(entry.commanders || []).join(" & ")}`, entry.ci ? " · " : "", entry.ci ? ui.colorLetters(entry.ci) : null)), h("span", { class: "baserow__count", text: `${entry.card_count} cards` })));
    }
    out.append(ui.button({ label: "New base deck", kind: "outline", href: app.link.newBase, className: "btn--block" }));
    return out;
}
function versionForm(app, chosen) {
    const menu = formData.menu;
    const form = h("form", { class: "form", novalidate: true });
    form.addEventListener("submit", (e) => { e.preventDefault(); submitVersion(app, chosen); });
    form.append(h("div", { class: "baserow", style: { borderBottom: "1px solid var(--line-soft)" } }, chosen.commander_image ? ui.cardTile({ name: (chosen.commanders || [])[0] || chosen.name, image: chosen.commander_image, cost: "", type: "" }, { size: "commander" }) : null, h("span", { class: "baserow__main" }, h("span", { class: "baserow__name", text: chosen.name }), h("span", { class: "baserow__sub", text: `${(chosen.commanders || []).join(" & ")} · ${chosen.card_count} cards` })), ui.button({ label: "Change", kind: "quiet", size: "small", onClick: () => { version.baseId = null; app.render(); } })));
    const name = h("input", { id: "version-name", class: "input", type: "text", value: version.name, placeholder: "For example, Squirrels go wide", autocomplete: "off", maxlength: "80" });
    name.addEventListener("input", () => { version.name = name.value; version.errors.name = ""; });
    form.append(ui.field({ id: "version-name", label: "Name", control: name, error: version.errors.name }));
    const brackets = h("div", { class: "seg", role: "group", "aria-label": "Bracket" }, [1, 2, 3, 4, 5].map((n) => ui.chip({
        label: `${n} ${BRACKET_NAMES[n]}`, pressed: version.bracket === n,
        onClick: () => { version.bracket = n; const style = version.playstyle ? playstyleOf(version.playstyle) : null; if (style && style.min_bracket > n)
            version.playstyle = ""; app.render(); },
    })));
    form.append(ui.field({ id: "bracket", label: "Bracket", control: brackets, hint: "How powerful the table expects the deck to be. The suggestions and the checks follow it.", error: version.errors.bracket }));
    const budget = h("input", { id: "version-budget", class: "input", type: "number", min: "0", step: "any", inputmode: "decimal", value: version.budget, placeholder: "No budget" });
    budget.addEventListener("input", () => { version.budget = budget.value; version.errors.budget = ""; });
    form.append(ui.field({ id: "version-budget", label: "Budget in dollars (optional)", control: budget, hint: "Suggestions stay inside it. Cards you own cost nothing.", error: version.errors.budget }));
    const playstyles = h("div", { class: "seg", role: "group", "aria-label": "Playstyle" }, menu.playstyles.map((p) => ui.chip({
        label: p.label, pressed: version.playstyle === p.slug, disabled: p.min_bracket > version.bracket, title: p.min_bracket > version.bracket ? `Needs Bracket ${p.min_bracket} or higher` : undefined,
        onClick: () => { version.playstyle = version.playstyle === p.slug ? "" : p.slug; app.render(); },
    })));
    const described = version.playstyle ? playstyleOf(version.playstyle) : null;
    form.append(ui.field({ id: "playstyle", label: "Playstyle (optional)", control: playstyles, hint: described ? described.description : "How you want the deck to win.", error: version.errors.playstyle }));
    const themes = h("div", { class: "seg", role: "group", "aria-label": "Themes" }, menu.themes.map((t) => ui.chip({
        label: t.label, pressed: version.themes.has(t.slug),
        onClick: () => { if (version.themes.has(t.slug))
            version.themes.delete(t.slug);
        else
            version.themes.add(t.slug); app.render(); },
    })));
    form.append(ui.field({ id: "themes", label: "Themes (optional)", control: themes, hint: "Each theme the commander has not been opened with makes the first open fetch one more page.", error: version.errors.themes }));
    form.append(ownedPrecons(app, chosen));
    ui.append(form, [noticeBanner(version.notice)]);
    form.append(ui.button({ label: "Create version", kind: "primary", size: "big", busy: version.busy, type: "submit", className: "btn--block" }));
    return form;
}
function playstyleOf(slug) {
    return formData.menu.playstyles.find((p) => p.slug === slug) || null;
}
function ownedPrecons(app, chosen) {
    const own = formData.bases.filter((b) => b.id !== chosen.id && b.source && b.source.type === "precon").map((b) => b.source.name);
    const searchBox = ui.searchBox({
        id: "owned-search", label: "Search the precons you own", placeholder: "Search the precons you own", value: version.ownedQuery,
        onInput: (value) => {
            version.ownedQuery = value;
            sleepThen(async () => {
                try {
                    const found = await call("GET", `/api/precons?q=${enc(value)}`);
                    version.ownedResults = found.body.precons;
                }
                catch (e) {
                    version.ownedResults = [];
                }
                app.render();
            });
        },
    });
    const options = [...new Set([...own, ...version.owned, ...version.ownedResults])];
    const chips = h("div", { class: "seg", role: "group", "aria-label": "Precons you own" }, options.map((n) => ui.chip({
        label: n, pressed: version.owned.has(n),
        onClick: () => { if (version.owned.has(n))
            version.owned.delete(n);
        else
            version.owned.add(n); app.render(); },
    })));
    return ui.field({
        id: "owned-search", label: "Precons you own (optional)",
        control: h("div", { class: "stack" }, searchBox.el, options.length ? chips : null),
        hint: "A card in a precon you own costs $0 in the suggestions. The base deck's own cards always do.", error: version.errors.owned_precons,
    });
}
async function submitVersion(app, chosen) {
    if (version.busy)
        return;
    const player = app.state.player;
    const name = version.name.trim();
    version.errors = {};
    version.notice = null;
    if (!name) {
        version.errors.name = "Give the version a name.";
        app.render();
        return;
    }
    const settings = { bracket: version.bracket };
    if (version.budget.trim() !== "") {
        const value = Number(version.budget);
        if (!Number.isFinite(value) || value < 0) {
            version.errors.budget = "Type an amount in dollars: zero or more, or leave it empty.";
            app.render();
            return;
        }
        settings.budget = value;
    }
    if (version.themes.size)
        settings.themes = [...version.themes];
    if (version.playstyle)
        settings.playstyle = version.playstyle;
    if (version.owned.size)
        settings.owned_precons = [...version.owned];
    version.busy = true;
    app.render();
    try {
        const made = await call("POST", "/api/decks", { player, name, base: chosen.id, settings });
        version.busy = false;
        app.go(app.link.deck(player, made.body.version.id));
    }
    catch (e) {
        const error = e;
        version.busy = false;
        if (error.kind === "conflict")
            version.errors.name = error.message;
        else if (error.kind === "invalid" && Array.isArray(error.details) && error.details.length) {
            for (const problem of error.details) {
                const key = problem.setting === "owned_precons" ? "owned_precons" : problem.setting;
                if (key)
                    version.errors[key] = problem.text;
            }
            if (!Object.keys(version.errors).length)
                version.notice = failureNotice(error);
        }
        else
            version.notice = failureNotice(error, () => submitVersion(app, chosen));
        app.render();
    }
}
// ---- New base deck
export function newBaseView(app) {
    return formShell(app, "New base deck", (main) => {
        main.append(h("div", {}, h("h1", { class: "title" }, "New ", h("span", { class: "accent", text: "base deck" })), h("p", { class: "lede", text: "A base deck is where a version starts: a precon, or a list you paste in. It is saved once and never changes." })));
        main.append(h("div", { class: "seg", role: "group", "aria-label": "How to make it" }, ui.chip({ label: "A precon", pressed: base.mode === "precon", onClick: () => { base.mode = "precon"; base.notice = null; app.render(); } }), ui.chip({ label: "Paste a list", pressed: base.mode === "paste", onClick: () => { base.mode = "paste"; base.notice = null; app.render(); } })));
        main.append(base.mode === "precon" ? preconPicker(app) : pasteForm(app));
    });
}
function preconPicker(app) {
    const out = h("div", { class: "stack" });
    const searchBox = ui.searchBox({
        id: "precon-search", label: "Search the precons", placeholder: "Search precons, for example squirreled", value: base.query, big: true,
        onInput: (value) => {
            base.query = value;
            base.status = value.trim() ? "typing" : "idle";
            base.close = [];
            sleepThen(async () => {
                if (!base.query.trim()) {
                    base.results = [];
                    base.status = "idle";
                    app.render();
                    return;
                }
                base.status = "loading";
                app.render();
                try {
                    const found = await call("GET", `/api/precons?q=${enc(base.query)}`);
                    base.results = found.body.precons;
                    base.status = "ready";
                }
                catch (e) {
                    base.status = "error";
                    base.notice = failureNotice(e, () => { base.query = base.query; app.render(); });
                }
                app.render();
            });
        },
    });
    out.append(searchBox.el);
    if (base.status === "loading")
        out.append(ui.working("Searching…"));
    else if (base.status === "ready" && !base.results.length) {
        out.append(ui.emptyState({ title: "No precon matches", text: `No precon has “${base.query.trim()}” in its name. Try fewer letters.` }));
    }
    else if (base.status === "idle") {
        out.append(h("p", { class: "muted small", text: "Type part of a precon's name. Every Commander precon Wizards of the Coast has printed is on the list." }));
    }
    out.append(h("div", {}, base.results.map((name) => h("button", {
        type: "button", class: "baserow", disabled: base.busy,
        onclick: () => createFromPrecon(app, name),
    }, h("span", { class: "baserow__main" }, h("span", { class: "baserow__name", text: name })), h("span", { class: "baserow__count", text: "Make it" })))));
    ui.append(out, [noticeBanner(base.notice)]);
    if (base.close.length) {
        out.append(h("div", { class: "stack" }, h("p", { class: "para", text: "Did you mean:" }), h("div", { class: "seg" }, base.close.map((name) => ui.chip({ label: name, onClick: () => createFromPrecon(app, name) })))));
    }
    if (base.taken) {
        out.append(ui.button({ label: `Make a version of ${base.taken.name}`, kind: "gold", href: app.link.newVersion(base.taken.id) }));
    }
    return out;
}
async function createFromPrecon(app, name) {
    if (base.busy)
        return;
    base.busy = true;
    base.notice = null;
    base.close = [];
    base.taken = null;
    app.render();
    try {
        const made = await call("POST", "/api/bases", { player: app.state.player, precon: name });
        base.busy = false;
        app.go(app.link.newVersion(made.body.base.id));
    }
    catch (e) {
        const error = e;
        base.busy = false;
        if (error.kind === "not_found") {
            base.close = (error.details && error.details.suggestions) || [];
            base.notice = () => ui.banner({ tone: "bad", title: "Not found:", text: error.message });
        }
        else if (error.kind === "conflict") {
            base.notice = warning("Already saved:", `${name} is already one of your base decks.`);
            base.taken = { name, id: playerId(name) };
        }
        else
            base.notice = failureNotice(error, () => createFromPrecon(app, name));
        app.render();
    }
}
/** Replace line `n` (1-based) of the pasted list with a card name (keeping its count), or drop it when `name` is null. */
function fixLine(n, name) {
    const lines = base.list.split("\n");
    const line = lines[n - 1] || "";
    const count = /^\s*(\d+)\s*x?\s+/i.exec(line);
    if (name === null)
        lines.splice(n - 1, 1);
    else
        lines[n - 1] = `${count ? count[1] : 1} ${name}`;
    base.list = lines.join("\n");
    // a dropped line moves the ones below it up; the problems that remain keep pointing at the right line
    base.problems = base.problems.filter((p) => p.line !== n).map((p) => (name === null && p.line > n ? { ...p, line: p.line - 1 } : p));
}
function pasteForm(app) {
    const form = h("form", { class: "form", novalidate: true });
    form.addEventListener("submit", (e) => { e.preventDefault(); createFromList(app); });
    const name = h("input", { id: "base-name", class: "input", type: "text", value: base.name, placeholder: "For example, My Hazel deck", autocomplete: "off", maxlength: "80" });
    name.addEventListener("input", () => { base.name = name.value; base.errors.name = ""; });
    form.append(ui.field({ id: "base-name", label: "Name", control: name, error: base.errors.name }));
    const list = h("textarea", { id: "base-list", class: "textarea", placeholder: "Commander\n1 Hazel of the Rootbloom\n\nDeck\n1 Sol Ring\n9 Forest\n…", spellcheck: "false", value: base.list });
    list.addEventListener("input", () => { base.list = list.value; base.errors.list = ""; });
    form.append(ui.field({
        id: "base-list", label: "The deck list", control: list, error: base.errors.list,
        hint: "One card on each line, with its count: “1 Sol Ring”. Mark the commander under a “Commander” heading, or name it below.",
    }));
    const commander = h("input", { id: "base-commander", class: "input", type: "text", value: base.commander, placeholder: "Only if the list does not mark it", autocomplete: "off" });
    commander.addEventListener("input", () => { base.commander = commander.value; });
    form.append(ui.field({ id: "base-commander", label: "Commander (optional)", control: commander }));
    if (base.problems.length) {
        form.append(h("section", { class: "stack" }, ui.sectionLabel(`${base.problems.length} ${base.problems.length === 1 ? "line" : "lines"} could not be read`, { tight: true }), h("ul", { class: "problems" }, base.problems.map((p) => h("li", {}, h("div", {}, h("span", { class: "mono", text: `Line ${p.line}: ` }), p.text), h("div", { class: "seg", style: { marginTop: "6px" } }, (p.suggestions || []).map((suggestion) => ui.chip({ label: suggestion, onClick: () => { fixLine(p.line, suggestion); app.render(); } })), ui.chip({ label: "Drop this line", onClick: () => { fixLine(p.line, null); app.render(); } })))))));
    }
    ui.append(form, [noticeBanner(base.notice)]);
    form.append(ui.button({ label: "Create base deck", kind: "primary", size: "big", busy: base.busy, type: "submit", className: "btn--block" }));
    return form;
}
async function createFromList(app) {
    if (base.busy)
        return;
    base.errors = {};
    base.notice = null;
    if (!base.name.trim())
        base.errors.name = "Give the base deck a name.";
    if (!base.list.trim())
        base.errors.list = "Paste the deck list.";
    if (Object.keys(base.errors).length) {
        app.render();
        return;
    }
    base.busy = true;
    app.render();
    try {
        const body = { player: app.state.player, name: base.name.trim(), list: base.list };
        if (base.commander.trim())
            body.commander = base.commander.trim();
        const made = await call("POST", "/api/bases", body);
        base.busy = false;
        app.go(app.link.newVersion(made.body.base.id));
    }
    catch (e) {
        const error = e;
        base.busy = false;
        if (error.kind === "invalid" && Array.isArray(error.details) && error.details.length && error.details[0].line !== undefined) {
            base.problems = error.details;
            base.notice = warning("Fix or drop these lines,", "then create the base deck again.");
        }
        else if (error.kind === "conflict")
            base.errors.name = error.message;
        else
            base.notice = failureNotice(error, () => createFromList(app));
        app.render();
    }
}
