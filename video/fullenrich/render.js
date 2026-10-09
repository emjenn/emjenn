// usage: node render.js stills t1 t2 ...  |  node render.js video out.mp4 [fps]
const { chromium } = require('playwright');
const path = require('path');
const { spawn } = require('child_process');
(async () => {
  const [mode, ...args] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-web-security'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('page:', m.text()));
  page.on('pageerror', e => { console.error('PAGEERR', e); process.exit(1); });
  await page.goto('file://' + path.resolve(__dirname, 'motion.html'));
  await page.evaluate(() => window.ready);
  const canvas = await page.$('canvas');
  if (mode === 'stills') {
    for (const t of args) {
      await page.evaluate(t => render(t, Math.round(t * 60)), +t);
      await canvas.screenshot({ path: `build/still_${(+t).toFixed(2)}.png` });
    }
  } else {
    const fps = +(args[1] || 60), out = args[0], N = Math.round(15 * fps);
    const ff = spawn('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-i', 'build/music.wav', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
      '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = 0; f < N; f++) {
      await page.evaluate(([t, f]) => render(t, f), [f / fps, f]);
      const buf = await canvas.screenshot({ type: 'jpeg', quality: 97 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 60 === 0) console.log('frame', f, '/', N);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
