// Self-starting capture: spawn mtg-draft's log-tailer so `npm start` is the only
// thing you launch (no separate `python3 src/mtg-draft.py pull`). The daemon is
// idempotent — only one ever runs, and it detaches/reparents itself — so calling
// this on every launch is safe. It keeps data/drafts/current.json fresh each pick.
//
// Env:
//   MTG_NO_CAPTURE=1   don't auto-start (you manage the daemon yourself, e.g. the
//                      SSH/remote-read setup) — the overlay just polls current.json
//   MTG_PYTHON         python executable (default: python3)
import { spawn } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

export function ensureCapture(ROOT: string): void {
  if (process.env.MTG_NO_CAPTURE) {
    console.log('[capture] MTG_NO_CAPTURE set — not starting the daemon; polling current.json only');
    return;
  }
  const script = path.join(ROOT, 'src', 'mtg-draft.py');
  if (!fs.existsSync(script)) {
    console.warn(`[capture] ${script} not found — start the daemon yourself: python3 src/mtg-draft.py capture`);
    return;
  }
  const py = process.env.MTG_PYTHON || 'python3';
  console.log(`[capture] ensuring capture daemon: ${py} ${script} capture`);
  // `capture` starts the detached follower (which reparents to launchd/PID 1) and
  // the launcher itself exits promptly — so this child going away is expected.
  const child = spawn(py, [script, 'capture'], { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
  child.stdout.on('data', (d: Buffer) => process.stdout.write(`[capture] ${d}`));
  child.stderr.on('data', (d: Buffer) => process.stderr.write(`[capture] ${d}`));
  child.on('error', (e: Error) => console.warn(`[capture] couldn't start (${e.message}) — start it manually`));
  child.on('exit', () => console.log('[capture] launcher done; daemon runs detached and refreshes current.json each pick'));
}
