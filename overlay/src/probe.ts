// Headless smoke test for the overlay's data layer — no Electron, no GUI.
// Prints the render payload buildPack() would push, so you can verify the
// current.json -> tiles join (GIH, grade, wheel, tags, AI take) end-to-end.
//
//   npx tsx src/probe.ts               # uses <ROOT>/data/drafts/current.json
//   MTG_CURRENT=/path/to.json npx tsx src/probe.ts
// (or after `npm run build`:  node dist/probe.js)
import * as path from 'path';
import { makeLoader, buildPack } from './pack';

// tsx runs this from src/ (ROOT two up); compiled it runs from dist/ (also two up).
const ROOT = process.env.MTG_ROOT || path.resolve(__dirname, '..', '..');
const CURRENT = process.env.MTG_CURRENT || path.join(ROOT, 'data', 'drafts', 'current.json');

const pack = buildPack(CURRENT, makeLoader(ROOT));
if (!pack) {
  console.error(`No live pack in ${CURRENT}`);
  process.exit(1);
}

console.log(`${pack.set} ${pack.fmt} · P${pack.pack}P${pack.pick} · ${pack.n} cards\n`);
for (const t of pack.tiles) {
  const gih = t.gih == null ? '  —  ' : (t.gih * 100).toFixed(1) + '%';
  const grade = t.ds ? ` ${t.ds}` : '';
  const wheel = t.wheel ? ' 🎡' : '';
  console.log(`${gih}${grade.padEnd(4)}  ${t.name}${wheel}  [${(t.tags || []).join(', ')}]`);
  if (t.take) console.log(`         🤖 ${t.take}`);
}
