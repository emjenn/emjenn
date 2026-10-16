// shared bits for the three "7 job interview prompts" motion options
const W = 1920, H = 1080, DUR = 15;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');

// ---------- copy (verbatim) ----------
const TITLE = 'Copy these 7 prompts before your next job interview';
const PROMPTS = [
  ['1).', 'Resume Transformer', '↳ Transform my resume [paste resume] for [target position] into an ATS-optimized document that highlights achievements and incorporates industry keywords.'],
  ['2).', 'Cover Letter Creator', '↳ Write a personalized cover letter for [position] at [company] that connects my experience to their needs and demonstrates why I\'m an ideal fit.'],
  ['3).', 'Interview Answer Builder', '↳ Create a STAR response for "[interview question]" using my experience with [example], making it concise and impressive.'],
  ['4).', 'Job Description Decoder', '↳ Analyze this job listing [paste listing] to identify key requirements, hidden expectations, and phrases to include in my application.'],
  ['5).', 'LinkedIn Optimizer', '↳ Improve my LinkedIn profile [paste sections] to attract recruiters for [desired role], with compelling achievements and keywords.'],
  ['6).', 'Salary Negotiator', '↳ Create a negotiation script for my offer from [company/role] [paste details] to maximize compensation while maintaining relationship.'],
  ['7).', 'Interview Question Generator', '↳ Prepare me for my [company/position] interview with likely questions based on this job description [paste description].'],
].map(([n, title, body]) => ({ n, title, body }));

// ---------- palette: Nelly coffee ladder on black ----------
const C = {
  bg: '#000000', cream: '#F6EFE7', light: '#DEC5A8', latte: '#C9A27C', caramel: '#B07D4F',
  caramelDeep: '#8A5E38', mocha: '#6F4A32', esp: '#3B2A20', espDeep: '#2A1D15', gold: '#D9A441', muted: '#C9AE94',
};
const rgba = (hex, a) => {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`;
};

// ---------- math / easing ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, p) => a + (b - a) * p;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const eOutExpo = p => p >= 1 ? 1 : 1 - Math.pow(2, -10 * p);
const eInExpo = p => p <= 0 ? 0 : Math.pow(2, 10 * p - 10);
const eOutCubic = p => 1 - Math.pow(1 - p, 3);
const eInCubic = p => p * p * p;
const eInOutCubic = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
const eOutBack = (p, s = 1.7) => 1 + (s + 1) * Math.pow(p - 1, 3) + s * Math.pow(p - 1, 2);
const eInOutExpo = p => p <= 0 ? 0 : p >= 1 ? 1 : p < .5 ? Math.pow(2, 20 * p - 10) / 2 : (2 - Math.pow(2, -20 * p + 10)) / 2;
const eOutElastic = p => p <= 0 ? 0 : p >= 1 ? 1 : Math.pow(2, -10 * p) * Math.sin((p * 10 - .75) * (2 * Math.PI) / 3) + 1;
function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

function pulseAt(t, hits, decay = 7) {
  let p = 0;
  for (const k of hits) if (t >= k) p = Math.max(p, Math.exp(-(t - k) * decay));
  return p;
}

// ---------- drawing helpers ----------
function font(f) { ctx.font = f; }
function txt(s, x, y, color, align = 'left', base = 'alphabetic') {
  ctx.fillStyle = color; ctx.textAlign = align; ctx.textBaseline = base; ctx.fillText(s, x, y);
}
function rrect(x, y, w, h, r) {
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r);
}
function sparklePath(x, y, r, pinch = 0.0) {
  ctx.beginPath();
  ctx.moveTo(x, y - r);
  ctx.quadraticCurveTo(x + pinch * r, y - pinch * r, x + r, y);
  ctx.quadraticCurveTo(x + pinch * r, y + pinch * r, x, y + r);
  ctx.quadraticCurveTo(x - pinch * r, y + pinch * r, x - r, y);
  ctx.quadraticCurveTo(x - pinch * r, y - pinch * r, x, y - r);
  ctx.closePath();
}
function sparkle(x, y, r, color, rot = 0) {
  if (r <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  sparklePath(0, 0, r, 0.08); ctx.fillStyle = color; ctx.fill();
  ctx.restore();
}

// rich text: words, with [bracketed] runs highlighted
function layoutRich(text, fontStr, maxW) {
  font(fontStr);
  const sp = ctx.measureText(' ').width;
  const words = text.split(' ');
  let inB = false;
  const toks = words.map(w => {
    const runs = []; let cur = '', curHl = inB;
    for (const ch of w) {
      if (ch === '[') { if (cur) runs.push({ s: cur, hl: curHl }); cur = ch; curHl = true; inB = true; continue; }
      cur += ch;
      if (ch === ']') { runs.push({ s: cur, hl: true }); cur = ''; curHl = false; inB = false; }
    }
    if (cur) runs.push({ s: cur, hl: curHl });
    runs.forEach(r => r.w = ctx.measureText(r.s).width);
    return { runs, w: runs.reduce((a, r) => a + r.w, 0), endHl: inB };
  });
  const lines = []; let line = [], lw = 0;
  for (const tk of toks) {
    const add = (line.length ? sp : 0) + tk.w;
    if (line.length && lw + add > maxW) { lines.push({ toks: line, w: lw }); line = []; lw = 0; }
    line.push(tk); lw += (line.length > 1 ? sp : 0) + tk.w;
  }
  if (line.length) lines.push({ toks: line, w: lw });
  let count = 0; lines.forEach(l => l.toks.forEach(tk => tk.i = count++));
  return { lines, sp, font: fontStr, count, chars: text.length };
}

// mode 'rise': words rise+fade with stagger; mode 'type': characters appear
function drawRich(L, x, y, lineH, reveal, o = {}) {
  const color = o.color || C.cream, hlColor = o.hlColor || C.gold, hlBg = o.hlBg || rgba(C.caramel, .22);
  const size = o.size || 40, align = o.align || 'left', mode = o.mode || 'rise', spread = o.spread || 6;
  font(L.font); ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
  let charBudget = mode === 'type' ? Math.floor(reveal * L.chars) : Infinity;
  let caret = null;
  L.lines.forEach((ln, li) => {
    let cx = align === 'center' ? x - ln.w / 2 : x;
    const cy = y + li * lineH;
    ln.toks.forEach((tk, ti) => {
      let p = 1;
      if (mode === 'rise') p = eOutCubic(clamp(reveal * (L.count + spread) - tk.i, 0, spread) / spread);
      if (p <= 0 || charBudget <= 0) { cx += tk.w + L.sp; return; }
      const dy = (1 - p) * size * 0.7;
      ctx.globalAlpha = p * (o.alpha ?? 1);
      let rx = cx;
      tk.runs.forEach((r, ri) => {
        let s = r.s;
        if (charBudget < s.length) s = s.slice(0, charBudget);
        charBudget -= s.length;
        const w = s === r.s ? r.w : ctx.measureText(s).width;
        if (r.hl && s.length) {
          const nextTok = ln.toks[ti + 1];
          const joins = ri === tk.runs.length - 1 && s === r.s && nextTok && nextTok.runs[0].hl && tk.endHl;
          ctx.fillStyle = hlBg;
          rrect(rx - 6, cy + dy - size * 0.82, w + 12 + (joins ? L.sp - 12 : 0), size * 1.08, 8); ctx.fill();
        }
        ctx.fillStyle = r.hl ? hlColor : color;
        ctx.fillText(s, rx, cy + dy);
        rx += w;
        caret = [rx, cy];
      });
      if (charBudget > 0) charBudget -= 1; // the space
      cx += tk.w + L.sp;
    });
  });
  ctx.globalAlpha = 1;
  return caret;
}

// text revealed from a clip mask (rises from below a baseline)
function maskRise(s, x, y, p, color, size, align = 'left', dist = 1.1) {
  if (p <= 0) return;
  const w = ctx.measureText(s).width;
  const x0 = align === 'left' ? x : align === 'center' ? x - w / 2 : x - w;
  ctx.save();
  ctx.beginPath(); ctx.rect(x0 - 30, y - size * 1.1, w + 60, size * 1.45); ctx.clip();
  txt(s, x, y + (1 - p) * size * dist, color, align);
  ctx.restore();
}

// ---------- watermark (always on top, every frame) ----------
function watermark() {
  ctx.save();
  font('600 22px IDSemi');
  ctx.textBaseline = 'middle';
  const s = 'x.com/nrqa__';
  // top-left
  ctx.globalAlpha = 0.42; txt(s, 44, 44, C.cream, 'left', 'middle');
  // bottom-right
  txt(s, W - 44, H - 42, C.cream, 'right', 'middle');
  // center
  ctx.globalAlpha = 0.2; txt(s, W / 2, H / 2, C.cream, 'center', 'middle');
  ctx.restore();
}

// film grain + vignette for depth on black
const grainCanvas = document.createElement('canvas');
grainCanvas.width = 512; grainCanvas.height = 512;
{
  const g = grainCanvas.getContext('2d'), id = g.createImageData(512, 512), r = mulberry(5);
  for (let i = 0; i < id.data.length; i += 4) { const v = r() * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
  g.putImageData(id, 0, 0);
}
function grain(f, amt = 0.045) {
  ctx.save();
  ctx.globalAlpha = amt; ctx.globalCompositeOperation = 'overlay';
  const ox = (f * 137) % 512, oy = (f * 251) % 512;
  ctx.translate(-ox, -oy);
  ctx.fillStyle = ctx.createPattern(grainCanvas, 'repeat');
  ctx.fillRect(0, 0, W + 512, H + 512);
  ctx.restore();
}
function vignette(a = 0.6) {
  const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${a})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function clear() { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = C.bg; ctx.fillRect(0, 0, W, H); }

window.ready = document.fonts.ready.then(() => Promise.all(
  ['IDBlack', 'IDBold', 'IDSemi', 'IDMed', 'Sora', 'SoraB', 'SoraR', 'FrB', 'FrI', 'JBM'].map(f => document.fonts.load(`40px ${f}`))
));
