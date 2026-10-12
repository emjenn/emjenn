// Shared timeline, content and helpers for the "agent memory" videos. Each option sets its own palette in C.
const W = 1920, H = 1080, DUR = 15, BEAT = 0.5;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const C = Object.assign({ white: '#FFFFFF', g1: '#C9C9C9', g2: '#8A8A8A', g3: '#3A3A3A', g4: '#161616', acc: '#FFFFFF' }, window.PALETTE || {});
const T_DROP = 2, T_R0 = 3.5, R_DUR = 0.45, N = 20, T_RECAP = 12.5, T_OUT = 13.2;
const SLOT_T = i => T_R0 + i * R_DUR;
const HITS = []; for (let t = 2; t < 13; t += BEAT) HITS.push(t); for (let i = 0; i < 20; i++) HITS.push(3.5 + i * 0.45); HITS.push(12.5, 13.2);

// text exactly as provided - nothing added
const TITLE = ['20 GitHub projects for building', 'a second brain', 'your AI agents can actually use'];
const RAW = [
  ['1).', 'Chubby Skills', 'https://github.com/chubbyguan/chubbyskills'],
  ['2).', 'OpenWiki', 'https://github.com/kdsz001/OpenWiki'],
  ['3).', 'Agent Second Brain', 'https://github.com/smixs/agent-second-brain'],
  ['4).', 'DocMason', 'https://github.com/JetXu-LLM/DocMason'],
  ['5).', 'DocsAgent', 'https://github.com/docsagent/docsagent'],
  ['6).', 'claude-obsidian', 'https://github.com/AgriciDaniel/claude-obsidian'],
  ['7).', 'SwarmVault', 'https://github.com/swarmclawai/swarmvault'],
  ['8).', 'sage-wiki', 'https://github.com/xoai/sage-wiki'],
  ['9).', 'Vault Curate', 'https://github.com/notoriouslab/vault-curate'],
  ['10).', 'COG Second Brain', 'https://github.com/huytieu/COG-second-brain'],
  ['11).', 'Hindsight', 'https://github.com/vectorize-io/hindsight'],
  ['12)', 'memU', 'https://github.com/NevaMind-AI/memU'],
  ['13).', 'TencentDB Agent Memory', 'https://github.com/TencentCloud/TencentDB-Agent-Memory'],
  ['14).', 'agentmemory', 'https://github.com/rohitg00/agentmemory'],
  ['15).', 'OpenViking', 'https://github.com/volcengine/OpenViking'],
  ['16).', 'Open Second Brain', 'https://github.com/itechmeat/open-second-brain'],
  ['17).', 'Second Brain Cloudflare', 'https://github.com/rahilp/second-brain-cloudflare'],
  ['18)', 'makerskills', 'https://github.com/coreyhaines31/makerskills'],
  ['19).', 'Row-Bot', 'https://github.com/siddsachar/row-bot'],
  ['20).', 'MateClaw', 'https://github.com/mateaix/mateclaw'],
];
const REPOS = RAW.map(([n, name, url]) => ({ n, name, url }));
const num = i => REPOS[i].n;

// GitHub mark (24x24 path)
const GH_PATH = new Path2D('M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12');
function ghMark(x, y, size, color = C.white, alpha = 1, rot = 0) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.globalAlpha *= alpha; const s = size / 24; ctx.scale(s, s); ctx.translate(-12, -12.3);
  ctx.fillStyle = color; ctx.fill(GH_PATH); ctx.restore();
}
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
  ctx.fillStyle = C.acc; ctx.fillRect(0, H - 5, W * clamp(t / DUR), 5);
  const s = 'x.com/nrqa__';
  font('500 24px IDMed'); txt(s, 56, 62, 'rgba(255,255,255,0.45)', 'left', 'middle'); txt(s, W - 56, H - 32, 'rgba(255,255,255,0.45)', 'right', 'middle');
  font('500 30px IDMed'); txt(s, W / 2, H / 2, 'rgba(255,255,255,0.16)', 'center', 'middle');
  const fo = prog(t, DUR - 0.3, DUR); if (fo > 0) { ctx.fillStyle = `rgba(0,0,0,${fo})`; ctx.fillRect(0, 0, W, H); }
}
function flashes(t, list) { for (const [h, c, a = 0.5] of list) { const p = prog(t, h, h + 0.25); if (p > 0 && p < 1) { ctx.fillStyle = `rgba(${c},${a * (1 - eOutCubic(p))})`; ctx.fillRect(0, 0, W, H); } } }
const FONTS_READY = Promise.all(['10px IDBlack', '10px IDBold', '10px IDMed', 'italic 10px NR', '600 10px JBM', '400 10px JBM'].map(f => document.fonts.load(f)));

// title card: the provided title, verbatim, three lines
function titleCard(t, X = 140, align = 'left') {
  const u = t - T_DROP, out = eInExpo(prog(t, T_R0 - 0.25, T_R0));
  if (u < 0 || out >= 1) return;
  ctx.save(); ctx.globalAlpha = 1 - out;
  ctx.fillStyle = 'rgba(0,0,0,0.88)'; ctx.fillRect(0, 250, W * eOutExpo(prog(u, 0, 0.25)), 560);
  font('70px IDBlack'); maskRise(TITLE[0], X, 390, prog(u, 0.05, 0.25), C.white, 70, align);
  font('170px IDBlack'); maskRise(TITLE[1], X, 560, prog(u, 0.2, 0.4), C.white, 104, align);
  font('70px IDBlack'); maskRise(TITLE[2], X, 680, prog(u, 0.35, 0.55), C.g1, 70, align);
  ctx.restore();
}
// big current-item readout: number, name, link (all as provided)
function readout(i, x, y, u, maxW = 1700, align = 'left', size = 96) {
  const r = REPOS[i];
  font('600 30px JBM'); txt(r.n, x, y, C.g2, align);
  const ns = fit(r.name, 'IDBlack', size, maxW, 40); maskRise(r.name, x, y + ns + 4, prog(u, 0, 0.14), C.white, ns, align);
  font('400 26px JBM'); txt(typed('↳ ' + r.url, prog(u, 0.03, 0.2)), x, y + ns + 58, C.g1, align);
}
