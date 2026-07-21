// Renderer: draw the current pack. Pure DOM, no Node access (sandboxed).
// This file has no imports/exports, so it stays a classic browser script.
const root = document.getElementById('root') as HTMLDivElement;
const head = document.getElementById('head') as HTMLSpanElement;
let state: OverlayState = { interactive: false, expandAll: false };
let lastPack: Pack | null = null;

const COLORS: Record<string, string> = {
  W: '#e9e2c4', U: '#5aa9f7', B: '#8b8f99', R: '#f26d6d', G: '#4ade80', C: '#9ca3af', M: '#f5b942',
};
function accent(c: string): string {
  if (!c) return COLORS.C;
  if (c.length > 1) return COLORS.M; // gold / multicolor
  return COLORS[c] || COLORS.C;
}
function gih(v: number | null): string {
  return v == null ? '' : `<span class="gih">${(v * 100).toFixed(1)}%</span>`;
}
function esc(s: unknown): string {
  return String(s).replace(/[&<>]/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[m] as string));
}

function tileEl(t: Tile): HTMLDivElement {
  const el = document.createElement('div');
  el.className = 'tile' + (state.expandAll ? '' : ' collapsed');
  el.style.borderLeftColor = accent(t.color);
  const ds = t.ds ? `<span class="grade">${esc(t.ds)}</span>` : '';
  const alsa = t.alsa != null ? `<span class="alsa">L${t.alsa}</span>` : '';
  const wheel = t.wheel ? '<span class="wheel" title="wheeled back to you">🎡</span>' : '';
  const tags = (t.tags || []).map((x) => `<span class="tag">${esc(x)}</span>`).join('');
  el.innerHTML =
    `<div class="row"><span class="name">${esc(t.name)}</span>${gih(t.gih)}${ds}${alsa}${wheel}</div>` +
    `<div class="sub">${esc(t.mana || '')} ${esc(t.type || '')}</div>` +
    (tags ? `<div class="tags">${tags}</div>` : '') +
    (t.take ? `<div class="take">🤖 ${esc(t.take)}</div>` : '') +
    (t.guide ? `<div class="guide">📘 ${esc(t.guide)}</div>` : '');
  // Hover-to-expand (only meaningful when the window is interactive / ⌘⇧O).
  el.addEventListener('mouseenter', () => el.classList.add('hover'));
  el.addEventListener('mouseleave', () => el.classList.remove('hover'));
  return el;
}

function render(pack: Pack): void {
  lastPack = pack;
  head.textContent = `${pack.set} · P${pack.pack}P${pack.pick} · ${pack.n} cards`;
  root.innerHTML = '';
  for (const t of pack.tiles) root.appendChild(tileEl(t));
}

function applyState(): void {
  document.body.classList.toggle('interactive', state.interactive);
  document.body.classList.toggle('expandall', state.expandAll);
}

window.overlay.onPack(render);
window.overlay.onState((s) => {
  state = s;
  applyState();
  if (lastPack) render(lastPack);
});
applyState();
