// Writes v2/audio/cues.json from the picture's own timing (window.soundCues in scene.html).
// Usage: node v2/export_cues.mjs [music.wav]
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
const { chromium } = createRequire(import.meta.url)(process.env.PW || '/opt/node22/lib/node_modules/playwright');
const here = path.dirname(new URL(import.meta.url).pathname);
const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const page = await browser.newPage();
await page.goto('file://' + path.join(here, 'scene.html'));
const cues = await page.evaluate(async () => { await window.ready; return window.soundCues(); });
await browser.close();
const sheet = {
  fps: 60, duration_s: 15.0, energy: 'punchy', kit: 'audio/kit',
  music: { file: process.argv[2] || 'audio/music.wav', start_s: 0, loop: true, fade_out_s: 0.6 },
  cues,
};
fs.mkdirSync(path.join(here, 'audio'), { recursive: true });
fs.writeFileSync(path.join(here, 'audio', 'cues.json'), JSON.stringify(sheet, null, 1));
console.log(`audio/cues.json: ${cues.length} cues, ${cues.filter(c => c.weight === 'hero').length} heroes`);
