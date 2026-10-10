// Usage: node render.mjs stills <outdir> t1 t2 ...   |   node render.mjs video <out.mp4> [fps]
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)(process.env.PW || '/opt/node22/lib/node_modules/playwright');
import { spawn } from 'node:child_process';
import path from 'node:path';
const [mode, out, ...rest] = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--font-render-hinting=none'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto('file://' + path.resolve(new URL('.', import.meta.url).pathname, 'scene.html'));
await page.evaluate(async () => { await window.ready; await document.fonts.ready; });
const shot = () => page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1920, height: 1080 } });
if (mode === 'stills') {
  for (const s of rest) { const t = +s; await page.evaluate(([t]) => renderFrame(t, Math.round(t * 60)), [t]);
    await page.screenshot({ path: `${out}/f_${s}.png` }); }
} else {
  const fps = +(rest[0] || 60), total = 15 * fps;
  const ff = spawn('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < total; f++) {
    await page.evaluate(([t, f]) => renderFrame(t, f), [f / fps, f]);
    const buf = await shot();
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 120 === 0) console.log('frame', f, '/', total);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
await browser.close();
