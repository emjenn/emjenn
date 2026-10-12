// Shared palette, timeline, content and helpers for the Opus 5.5 cheatsheet options.
const W = 1920, H = 1080, DUR = 15, BEAT = 0.5;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const C = { orange: '#D97757', deep: '#C15F3C', cream: '#F0EEE6', dim: '#8A877F' };
const T_DROP = 2, T_TIP0 = 3.5, TIP_DUR = 1.5, N = 6, T_FULL = 12.5, T_OUT = 13;
const TIP_T = i => T_TIP0 + i * TIP_DUR;
const HITS = []; for (let t = 2; t < 13; t += BEAT) HITS.push(t); HITS.push(13);

const TIPS = [
  ['Default to medium effort', 'Medium on 5.5 already outperforms high on Opus 5, at a lower cost. Maxing it out by habit just burns tokens.'],
  ['Drop “think step by step”', 'Reasoning is built in now. The model decides how much thinking a task needs, so asking it to think harder adds nothing.'],
  ['A check-in isn’t a finish line', 'On long runs, it sends progress updates along the way. If it stops to report, tell it to keep going.'],
  ['Fence off anything you paste', 'Put emails, docs, and web text in clearly labeled sections or tags. That way it can tell your instructions apart from the material it’s working on.'],
  ['Retire your image workarounds', 'Those custom chart readers and OCR steps you built are probably dead weight. It reads screenshots, diagrams, and charts accurately on its own.'],
  ['For design work, name what you don’t want', '“Make it unique” gets you generic. “No purple gradients, no centered hero, no emoji icons” gets you something different. It follows specific bans much better than vague direction.'],
];

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, p) => a + (b - a) * p;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const eOutExpo = p => p >= 1 ? 1 : 1 - Math.pow(2, -10 * p);
const eInExpo = p => p <= 0 ? 0 : Math.pow(2, 10 * p - 10);
const eOutCubic = p => 1 - Math.pow(1 - p, 3);
const eInOutCubic = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
const eOutBack = (p, s = 1.7) => 1 + (s + 1) * Math.pow(p - 1, 3) + s * Math.pow(p - 1, 2);
const hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const pad2 = n => String(n).padStart(2, '0');
const rgba = (hex, a) => { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; };
function pulseAt(t, d = 8) { let p = 0; for (const k of HITS) if (t >= k) p = Math.max(p, Math.exp(-(t - k) * d)); return p; }
function font(f) { ctx.font = f; }
function txt(s, x, y, c, al = 'left', base = 'alphabetic') { ctx.fillStyle = c; ctx.textAlign = al; ctx.textBaseline = base; ctx.fillText(s, x, y); }
function typed(s, p) { return s.slice(0, Math.round(s.length * clamp(p))); }
function fit(s, fam, size, maxW, min = 16) { font(`${size}px ${fam}`); while (ctx.measureText(s).width > maxW && size > min) { size -= 2; font(`${size}px ${fam}`); } return size; }
function wrap(s, maxW) { const out = ['']; for (const w of s.split(' ')) { const tr = (out[out.length - 1] + ' ' + w).trim(); if (ctx.measureText(tr).width > maxW && out[out.length - 1]) out.push(w); else out[out.length - 1] = tr; } return out; }
function roundRect(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
function maskRise(s, x, y, p, fill, size, al = 'left') {
  if (p <= 0) return; const w = ctx.measureText(s).width, x0 = al === 'left' ? x : al === 'center' ? x - w / 2 : x - w;
  ctx.save(); ctx.beginPath(); ctx.rect(x0 - 20, y - size, w + 40, size * 1.32); ctx.clip();
  ctx.fillStyle = fill; ctx.textAlign = al; ctx.textBaseline = 'alphabetic'; ctx.fillText(s, x, y + (1 - eOutExpo(p)) * size * 1.1); ctx.restore();
}

// the brand spark: 12 chunky rays
const RAY_L = [1, .74, .93, .7, .98, .79, .9, .72, 1, .77, .87, .73];
const RAY_J = RAY_L.map((_, i) => Math.sin(i * 12.9898) * 0.07);
function spark(x, y, r, p, rot, color = C.orange, alpha = 1, rayScale = null) {
  if (p <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.globalAlpha *= alpha; ctx.fillStyle = color;
  for (let i = 0; i < 12; i++) {
    const pi = clamp((p - i * 0.035) / 0.55); if (pi <= 0) continue;
    const len = r * RAY_L[i] * eOutBack(pi, 1.4) * (rayScale ? rayScale(i) : 1), a = i * Math.PI / 6 + RAY_J[i];
    const w0 = r * 0.1, w1 = r * 0.065, ca = Math.cos(a), sa = Math.sin(a), px = -sa, py = ca;
    ctx.beginPath(); ctx.moveTo(px * w0, py * w0); ctx.lineTo(ca * len + px * w1, sa * len + py * w1);
    ctx.arc(ca * len, sa * len, w1, a + Math.PI / 2, a - Math.PI / 2, true); ctx.lineTo(-px * w0, -py * w0); ctx.closePath(); ctx.fill();
  }
  ctx.beginPath(); ctx.arc(0, 0, r * 0.2 * clamp(p * 3), 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

const _rnd = mulberry(5);
const GRAINS = [];
for (let i = 0; i < 6; i++) {
  const g = document.createElement('canvas'); g.width = W / 2; g.height = H / 2;
  const gx = g.getContext('2d'); const im = gx.createImageData(g.width, g.height);
  for (let j = 0; j < im.data.length; j += 4) { const v = _rnd() * 255; im.data[j] = im.data[j + 1] = im.data[j + 2] = v; im.data[j + 3] = 14; }
  gx.putImageData(im, 0, 0); GRAINS.push(g);
}
function finish(t, frame) {
  const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.4, W / 2, H / 2, H); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.65)'); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  ctx.drawImage(GRAINS[frame % GRAINS.length], 0, 0, W, H);
  ctx.fillStyle = C.orange; ctx.fillRect(0, H - 5, W * clamp(t / DUR), 5);
  const s = 'x.com/nrqa__';
  font('500 24px IDMed'); txt(s, 56, 62, 'rgba(240,238,230,0.45)', 'left', 'middle'); txt(s, W - 56, H - 32, 'rgba(240,238,230,0.45)', 'right', 'middle');
  font('500 30px IDMed'); txt(s, W / 2, H / 2, 'rgba(240,238,230,0.16)', 'center', 'middle');
  const fo = prog(t, DUR - 0.3, DUR); if (fo > 0) { ctx.fillStyle = `rgba(0,0,0,${fo})`; ctx.fillRect(0, 0, W, H); }
}
function flashes(t, list) { for (const [h, c, a = 0.5] of list) { const p = prog(t, h, h + 0.25); if (p > 0 && p < 1) { ctx.fillStyle = `rgba(${c},${a * (1 - eOutCubic(p))})`; ctx.fillRect(0, 0, W, H); } } }
const FONTS_READY = Promise.all(['10px IDBlack', '10px IDBold', '10px IDMed', 'italic 10px NR', '600 10px JBM', '400 10px JBM'].map(f => document.fonts.load(f)));
