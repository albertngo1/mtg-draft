// mtg-draft overlay — Electron main process.
//
// Draws a transparent, always-on-top, click-through window over MTG Arena and
// renders the CURRENT draft pack. All game-reading is already done by mtg-draft's
// capture daemon, which refreshes data/drafts/current.json every pick — this app
// only polls that file, joins two local lookups (AI take + oracle/guide), and draws.
//
// Nothing here talks to the network or an LLM: the AI takes are pre-baked into
// card-reference/ai_takes_<SET>.json, so per-pick rendering is instant and offline.
//
// Env overrides:
//   MTG_ROOT     repo root (default: parent of the compiled dist/ folder)
//   MTG_CURRENT  path to current.json (default: <ROOT>/data/drafts/current.json)
//   MTG_POLL_MS  poll interval in ms (default: 500)
import { app, BrowserWindow, ipcMain, globalShortcut, screen } from 'electron';
import * as path from 'path';
import { makeLoader, buildPack } from './pack';
import { ensureCapture } from './capture';

// At runtime this file lives in dist/, so the repo root is two levels up.
const ROOT = process.env.MTG_ROOT || path.resolve(__dirname, '..', '..');
const CURRENT = process.env.MTG_CURRENT || path.join(ROOT, 'data', 'drafts', 'current.json');
const POLL_MS = Number(process.env.MTG_POLL_MS || 500);
const loader = makeLoader(ROOT);

let win: BrowserWindow | null = null;
let interactive = false; // false = click-through (glance); true = catches mouse (hover/drag)
let expandAll = false; // show every tile's AI take inline
let lastKey = ''; // dedupe renders: set|pack|pick|n

function tick(): void {
  const pack = buildPack(CURRENT, loader);
  if (!pack || pack.key === lastKey) return;
  lastKey = pack.key;
  if (win) win.webContents.send('pack', pack);
}

function pushState(): void {
  if (win) win.webContents.send('state', { interactive, expandAll } as OverlayState);
}

function setInteractive(v: boolean): void {
  interactive = v;
  if (!win) return;
  // Passive: whole window ignores the mouse so clicks reach Arena. `forward` still
  // delivers move events so hover works the moment you flip to interactive.
  win.setIgnoreMouseEvents(!interactive, { forward: true });
  win.setFocusable(interactive);
  pushState();
}

function createWindow(): void {
  const wa = screen.getPrimaryDisplay().workArea;
  win = new BrowserWindow({
    x: wa.x + wa.width - 360,
    y: wa.y + 40,
    width: 340,
    height: wa.height - 120,
    frame: false,
    transparent: true,
    hasShadow: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: true,
    movable: true,
    fullscreenable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.setAlwaysOnTop(true, 'screen-saver');
  // Survive Spaces / a fullscreen game on its own Space (requires windowed Arena to
  // actually draw over it — exclusive fullscreen refuses all overlays).
  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  win.loadFile(path.join(__dirname, 'index.html'));
  win.webContents.on('did-finish-load', () => {
    pushState();
    tick();
  });
  setInteractive(false); // start in glance (click-through) mode
  setInterval(tick, POLL_MS);
}

app.whenReady().then(() => {
  ensureCapture(ROOT); // spawn the log-tailer so current.json stays fresh — zero extra setup
  createWindow();
  // Toggle click-through (grab it to move/hover, then let go).
  globalShortcut.register('CommandOrControl+Shift+O', () => setInteractive(!interactive));
  // Toggle showing every AI take inline (works in glance mode too).
  globalShortcut.register('CommandOrControl+Shift+E', () => {
    expandAll = !expandAll;
    pushState();
  });
  // Hide / show the overlay entirely.
  globalShortcut.register('CommandOrControl+Shift+H', () => {
    if (!win) return;
    if (win.isVisible()) win.hide();
    else win.show();
  });
});

app.on('will-quit', () => globalShortcut.unregisterAll());
app.on('window-all-closed', () => app.quit());

// Renderer asks to (un)capture the mouse for a hovered region — lets the overlay
// stay click-through globally yet grab the mouse only over an interactive element.
ipcMain.on('set-ignore', (_e, ignore: boolean) => {
  if (win && !interactive) win.setIgnoreMouseEvents(!!ignore, { forward: true });
});
