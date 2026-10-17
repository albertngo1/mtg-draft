// The Add a card sheet. Step one: search for a card (an empty box lists the best fits not in the deck; typing waits 250 ms
// after the last key before asking). Step two: "what does it replace?", with "add as an extra card" as one of the
// answers. Opened with a card to cut already chosen (from the card sheet's "Swap for…"), step two is skipped.

import { callReady, cardSearchPath } from "./api.js";
import type { ApiError } from "./api.js";
import * as ui from "./ui.js";
import type { AddRoute, App, DeckRoute } from "./app.js";
import type { Progress, SearchAnswer, SearchCard } from "./types.js";

const { h } = ui;
const PAUSE_MS = 250;

/** "in 44% of 1,125 Bracket 3 Hazel decks (...)" -> the same sentence with the first clause in gold. */
function evidenceLine(card: SearchCard): string | (string | Node)[] {
  if (!card.evidence) return "No list of this commander's decks mentions this card, so it has no score.";
  const match = /\d+% of [\d,]+ [^(;]*?decks/.exec(card.evidence);
  const text = ui.capitalize(card.evidence);
  const tail = [card.score !== null ? ` · score ${ui.valueText(card.score)}` : "", card.gain !== null ? ` · deck score ${ui.signed(card.gain)} if added` : ""].join("");
  if (!match) return [text, tail];
  const at = text.indexOf(match[0]);
  return [text.slice(0, at), h("b", { text: match[0] }), text.slice(at + match[0].length), tail];
}

/** Open the sheet. `route` is {kind: "add", cut, card}. Returns the sheet (see ui.openSheet). */
export function open(app: App, route: AddRoute, options: ui.SheetOptions): ui.Sheet {
  let closed = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const sheet = ui.openSheet({ ...options, onDestroy: () => { closed = true; clearTimeout(timer); } });
  const { player, id } = app.state.route as DeckRoute;           // a sheet only opens over a deck
  const data = () => app.state.deck && app.state.deck.data;
  const st: { query: string; status: "loading" | "ready" | "error"; cards: SearchCard[]; error: ApiError | null; progress: Progress | null; seq: number; want: string } =
    { query: "", status: "loading", cards: [], error: null, progress: null, seq: 0, want: route.card || "" };
  const swapping = route.cut || "";

  const resultsBox = h("div", { "aria-live": "polite" });
  const hint = h("p", { class: "muted small" });
  const searchBox = ui.searchBox({
    id: "card-search", label: "Search cards in the commander's colors", big: true, placeholder: "Card name",
    onInput: (value) => {
      st.query = value;
      clearTimeout(timer);
      timer = setTimeout(() => search(value), PAUSE_MS);          // wait for the typing to stop before asking
    },
  });

  // ---- step one: search
  function search(text: string): void {
    const mine = ++st.seq;
    st.status = "loading";
    st.error = null;
    drawResults();
    callReady<SearchAnswer>("GET", cardSearchPath(text, player, id), undefined, {
      onProgress: (progress) => { st.progress = progress; },
      keepGoing: () => !closed && mine === st.seq,
    }).then((answer) => {
      if (closed || mine !== st.seq || answer.status === 202) return;
      st.cards = answer.body.cards;
      st.status = "ready";
      const wanted = st.want && st.cards.find((c) => c.name === st.want);
      st.want = "";
      if (wanted && !wanted.flag) {
        choose(wanted);
        return;
      }
      drawResults();
    }).catch((e) => {
      if (closed || mine !== st.seq) return;
      st.status = "error";
      st.error = e;
      drawResults();
    });
  }

  /** The line under the search box and its placeholder say how many cards the deck has and which colors; the deck may load after the sheet opens. */
  function drawHint(): void {
    const deck = data();
    searchBox.input.placeholder = `Card name${deck ? `, in ${ui.colorWords(ui.colorsOf(deck.commanders))}` : ""}`;
    hint.textContent = swapping ? `Pick the card that takes the place of ${swapping}.`
      : `${deck ? `The deck has ${deck.card_count} cards. ` : ""}After you pick a card, you choose what it replaces.`;
  }

  function drawResults(): void {
    drawHint();
    const out: HTMLElement[] = [];
    const typed = st.query.trim();
    if (st.status === "error") {
      out.push(ui.failureBanner(st.error!, { retry: () => search(st.query) }));
    } else if (st.status === "loading" && !st.cards.length) {
      out.push(ui.working(st.progress && st.progress.message ? st.progress.message : "Searching…"));
    } else {
      out.push(ui.sectionLabel(typed ? `Results for “${typed}”` : "Best fits not in the deck", { tight: true }));
      if (!st.cards.length) {
        out.push(ui.emptyState({
          title: "No card matches", text: `Nothing legal in Commander has “${typed}” in its name. Try fewer letters, or another spelling.`,
        }));
      }
      const rows = h("div", { class: st.status === "loading" ? "is-faded" : null, "aria-busy": st.status === "loading" ? "true" : "false" },
        st.cards.map((card) => ui.cardRow(card, {
          more: evidenceLine(card), keptOut: card.flag ? card.flag.reason : null,
          action: card.flag ? null : ui.button({
            label: swapping ? "Swap" : "Add", kind: "gold", ariaLabel: `${swapping ? "Swap in" : "Add"} ${card.name}`, onClick: () => choose(card),
          }),
        })));
      out.push(rows);
      out.push(h("p", { class: "footnote", text: "Prices: Scryfall." }));
    }
    resultsBox.replaceChildren(...out);
  }

  function showSearch(): void {
    sheet.setTitle(swapping ? `Swap ${swapping}` : "Add a card");
    sheet.setSub("");
    drawHint();
    sheet.body.replaceChildren(searchBox.el, hint, resultsBox);
  }

  // ---- step two: what does it replace?
  function choose(card: SearchCard): void {
    if (swapping) {
      app.change({ op: "swap", cut: swapping, add: card.name });
      app.closeSheet();
      return;
    }
    showChooser(card);
  }

  function showChooser(card: SearchCard): void {
    sheet.setTitle(`Add ${card.name}`);
    sheet.setSub(ui.typeLine(card));
    const deck = data();
    const heading = h("h2", { class: "sheet__title", tabindex: "-1", text: "What does it replace?" });
    const filter = ui.searchBox({ id: "replace-search", label: "Search the deck for a card to replace", placeholder: "Search this deck", onInput: (value) => drawList(value) });
    const list = h("div", {});
    const over = deck && deck.card_count >= 100;
    const extra = h("button", {
      type: "button", class: "cardrow cardrow--pick",
      onclick: () => { app.change({ op: "add", card: card.name }); app.closeSheet(); },
    }, ui.cardTile(card, { size: "thumb" }),
    h("div", { class: "cardrow__main" }, h("div", { class: "cardrow__name", text: "Add as an extra card" }),
      h("div", { class: "cardrow__more", text: over ? "Keeps every card. The deck goes over 100 cards, and the deck page will say so." : "Keeps every card." })));

    const drawList = (text: string) => {
      const terms = String(text || "").toLowerCase().split(/\s+/).filter(Boolean);
      // weakest cards first (a basic land or an unscored card has no score, so it comes last): sorting is all the page does
      const cards = [...(deck ? deck.cards : [])]
        .filter((c) => terms.every((t) => `${c.name} ${c.type}`.toLowerCase().includes(t)))
        .sort((a, b) => Number(a.score === null) - Number(b.score === null) || (a.score || 0) - (b.score || 0));
      list.replaceChildren(...(cards.length ? cards.map((c) => ui.cardRow(c, {
        onPick: () => { app.change({ op: "swap", cut: c.name, add: card.name }); app.closeSheet(); },
        more: [c.count > 1 ? `${c.count} copies · ` : "", c.score === null ? "no score" : `score ${ui.valueText(c.score)}`, c.roles.length ? ` · ${c.roles.join(", ")}` : ""].join(""),
        focusKey: `replace:${c.name}`,
      })) : [ui.emptyState({ title: "No card matches", text: "Nothing in the deck matches that." })]));
    };
    drawList("");
    sheet.body.replaceChildren(
      ui.button({ label: "Back to the results", kind: "quiet", size: "small", icon: "back", onClick: () => { showSearch(); sheet.focus(searchBox.input); } }),
      heading, extra, ui.sectionLabel("Or swap it for", { tight: true }), filter.el, list);
    sheet.focus(heading);
  }

  showSearch();
  drawResults();
  if (st.want) {                                                   // opened for one card ("Add to the deck" on its sheet)
    st.query = st.want;
    searchBox.input.value = st.want;
  } else {
    sheet.focus(searchBox.input);
  }
  search(st.query);
  return sheet;
}
