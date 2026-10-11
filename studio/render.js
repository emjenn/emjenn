// Renders principles.html frame-by-frame in headless Chromium.
//   node render.js stills 0 69 105 ...      → build/still_XXX.png
//   node render.js audio                     → build/score_raw.wav (48 kHz stereo, float)
//   node render.js video [start] [end]       → build/frames/f_XXX.png
// three.js 0.160.0 and Geist Mono are served from local copies when the CDN is unreachable.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname, BUILD = path.join(ROOT, 'build'), VENDOR = path.join(BUILD, 'vendor');

function wav(L, R, sr) {
  const n = L.length, b = Buffer.alloc(44 + n * 8);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 8, 4); b.write('WAVE', 8);
  b.write('fmt ', 12); b.writeUInt32LE(16, 16); b.writeUInt16LE(3, 20); b.writeUInt16LE(2, 22);
  b.writeUInt32LE(sr, 24); b.writeUInt32LE(sr * 8, 28); b.writeUInt16LE(8, 32); b.writeUInt16LE(32, 34);
  b.write('data', 36); b.writeUInt32LE(n * 8, 40);
  for (let i = 0; i < n; i++) { b.writeFloatLE(L[i], 44 + i * 8); b.writeFloatLE(R[i], 48 + i * 8); }
  return b;
}

(async () => {
  const [mode, ...args] = process.argv.slice(2);
  const browser = await chromium.launch({
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl'],
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1080 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('page:', m.text()));
  page.on('pageerror', e => { console.error('PAGEERR', e); process.exit(1); });

  await page.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', route => {
    const rel = route.request().url().split('three@0.160.0/')[1];
    route.fulfill({ path: path.join(VENDOR, 'package', rel), contentType: 'text/javascript' });
  });
  await page.route('https://fonts.googleapis.com/**', route =>
    route.fulfill({ path: path.join(VENDOR, 'geist.css'), contentType: 'text/css' }));
  await page.route('https://fonts.gstatic.com/**', route =>
    route.fulfill({ path: path.join(VENDOR, 'geist-latin.woff2'), contentType: 'font/woff2' }));

  await page.goto('file://' + path.join(ROOT, 'principles.html') + '?render');
  await page.evaluate(() => window.ready);
  const stage = await page.$('#stage');

  if (mode === 'stills') {
    for (const f of args) {
      await page.evaluate(f => window.renderAt(f / 60), +f);
      await stage.screenshot({ path: path.join(BUILD, `still_${String(f).padStart(3, '0')}.png`) });
      console.log('still', f);
    }
  } else if (mode === 'audio') {
    const [L, R] = await page.evaluate(() => window.renderAudio(48000));
    fs.writeFileSync(path.join(BUILD, 'score_raw.wav'), wav(L, R, 48000));
    console.log('audio', L.length, 'samples');
  } else if (mode === 'video') {
    const a = +(args[0] || 0), b = +(args[1] || 480);
    fs.mkdirSync(path.join(BUILD, 'frames'), { recursive: true });
    const t0 = Date.now();
    for (let f = a; f < b; f++) {
      await page.evaluate(f => window.renderAt(f / 60), f);
      await stage.screenshot({ path: path.join(BUILD, 'frames', `f_${String(f).padStart(3, '0')}.png`) });
      if (f % 20 === 0) console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
  }
  await browser.close();
})();
