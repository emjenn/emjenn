// Shared data, timeline and helpers for the three "39 AI resources" videos.
const W = 1920, H = 1080, DUR = 20, BEAT = 0.5;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');

// ---------- the 39 resources ----------
const CATS = [
  { name: 'VIDEOS', short: 'videos', items: [
    ['LLM Introduction', 'https://www.youtube.com/watch?v=zjkBMFhNj_g'],
    ['LLMs from Scratch', 'https://www.youtube.com/watch?v=9vM4p9NN0Ts'],
    ['Agentic AI Overview (Stanford)', 'https://www.youtube.com/watch?v=kJLiOGle3Lw'],
    ['Building & Evaluating Agents', 'https://www.youtube.com/watch?v=d5EltXhbcfA'],
    ['Building Effective Agents', 'https://www.youtube.com/watch?v=D7_ipDqhtwk'],
    ['Building Agents with MCP', 'https://www.youtube.com/watch?v=kQmXtrmQ5Zg'],
    ['Building an Agent from Scratch', 'https://www.youtube.com/watch?v=xzXdLRUyjUg'],
    ['Philo Agents', 'https://www.youtube.com/playlist?list=PLacQJwuclt_sV-tfZmpT1Ov6jldHl30NR'],
  ]},
  { name: 'GITHUB REPOS', short: 'repos', items: [
    ['GenAI Agents', 'https://github.com/NirDiamant/GenAI_Agents'],
    ['Microsoft AI Agents for Beginners', 'https://github.com/microsoft/ai-agents-for-beginners'],
    ['Prompt Engineering Guide', 'https://github.com/dair-ai/Prompt-Engineering-Guide'],
    ['Hands-On Large Language Models', 'https://github.com/HandsOnLLM/Hands-On-Large-Language-Models'],
    ['Made with ML', 'https://github.com/GokuMohandas/Made-With-ML'],
    ['Hands-On AI Engineering', 'https://github.com/Sumanth077/Hands-On-AI-Engineering'],
    ['Awesome Generative AI Guide', 'https://github.com/aishwaryanr/awesome-generative-ai-guide'],
    ['Designing Machine Learning Systems', 'https://github.com/chiphuyen/dmls-book'],
    ['Machine Learning for Beginners', 'https://github.com/microsoft/ML-For-Beginners'],
    ['LLM Course', 'https://github.com/mlabonne/llm-course'],
  ]},
  { name: 'GUIDES', short: 'guides', items: [
    ['Google’s Agent Whitepaper', 'https://www.kaggle.com/whitepaper-agents'],
    ['Google’s Agent Companion', 'https://www.kaggle.com/whitepaper-agent-companion'],
    ['Building Effective Agents by Anthropic', 'https://www.anthropic.com/engineering/building-effective-agents'],
    ['Claude Code Agentic Coding Practices', 'https://code.claude.com/docs/en/best-practices'],
    ['OpenAI’s Practical Guide to Building Agents', 'https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf'],
  ]},
  { name: 'BOOKS', short: 'books', items: [
    ['Understanding Deep Learning', 'https://udlbook.github.io/udlbook/'],
    ['Building an LLM from Scratch', 'https://www.manning.com/books/build-a-large-language-model-from-scratch'],
    ['The LLM Engineering Handbook', 'https://www.oreilly.com/library/view/llm-engineers-handbook/9781836200079/'],
    ['AI Agents: The Definitive Guide', 'https://www.oreilly.com/library/view/ai-agents-the/0642572247775/'],
    ['Building Applications with AI Agents', 'https://www.oreilly.com/library/view/building-applications-with/9781098176495/'],
    ['AI Agents with MCP', 'https://www.oreilly.com/library/view/ai-agents-with/9798341639546/'],
    ['AI Engineering', 'https://www.oreilly.com/library/view/ai-engineering/9781098166298/'],
  ]},
  { name: 'RESEARCH PAPERS', short: 'papers', items: [
    ['ReAct', 'https://arxiv.org/abs/2210.03629'],
    ['Generative Agents', 'https://arxiv.org/abs/2304.03442'],
    ['Toolformer', 'https://proceedings.neurips.cc/paper_files/paper/2023/file/d842425e4bf79ba039352da0f658a906-Paper-Conference.pdf'],
    ['Chain-of-Thought Prompting', 'https://arxiv.org/pdf/2201.11903'],
  ]},
  { name: 'COURSES', short: 'courses', items: [
    ['Hugging Face Agent Course', 'https://huggingface.co/learn/agents-course/en/unit0/introduction'],
    ['MCP with Anthropic', 'https://www.deeplearning.ai/courses/mcp-build-rich-context-ai-apps-with-anthropic'],
    ['Building Vector Databases with Pinecone', 'https://www.deeplearning.ai/courses/building-applications-vector-databases'],
    ['Vector Databases: Embeddings to Apps', 'https://www.deeplearning.ai/courses/vector-databases-embeddings-applications'],
    ['Agent Memory', 'https://www.deeplearning.ai/courses/llms-as-operating-systems-agent-memory'],
  ]},
];
// category windows (seconds, all on the beat; music hits on every start)
const T_DROP = 2, T_CATS = 4, T_WALL = 17, T_OUT = 18.5;
const CAT_DUR = [2.5, 3.0, 2.0, 2.5, 1.5, 1.5];
let _t = T_CATS; CATS.forEach((c, i) => { c.t0 = _t; c.t1 = _t + CAT_DUR[i]; _t = c.t1; });
let _n = 0; CATS.forEach(c => { c.first = _n; _n += c.items.length; });
const TOTAL = _n; // 39

// short display url: no scheme / www, middle-truncated
function shortUrl(u, max = 52) {
  let s = u.replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/$/, '');
  if (s.length <= max) return s;
  const head = s.slice(0, Math.ceil(max * 0.55)), tail = s.slice(-Math.floor(max * 0.45) + 1);
  return head + '…' + tail;
}

// ---------- helpers ----------
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
function font(f) { ctx.font = f; }
function txt(s, x, y, c, al = 'left', base = 'alphabetic') { ctx.fillStyle = c; ctx.textAlign = al; ctx.textBaseline = base; ctx.fillText(s, x, y); }
function typed(s, p) { return s.slice(0, Math.round(s.length * clamp(p))); }
function fit(s, fam, size, maxW, min = 14) { font(`${size}px ${fam}`); while (ctx.measureText(s).width > maxW && size > min) { size -= 2; font(`${size}px ${fam}`); } return size; }
function roundRect(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
function maskRise(s, x, y, p, fill, size, al = 'left') {
  if (p <= 0) return; const w = ctx.measureText(s).width, x0 = al === 'left' ? x : al === 'center' ? x - w / 2 : x - w;
  ctx.save(); ctx.beginPath(); ctx.rect(x0 - 30, y - size, w + 60, size * 1.3); ctx.clip();
  ctx.fillStyle = fill; ctx.textAlign = al; ctx.textBaseline = 'alphabetic'; ctx.fillText(s, x, y + (1 - eOutExpo(p)) * size * 1.1); ctx.restore();
}
// beat hits: every beat from the drop to the wall, plus section starts
const HITS = []; for (let t = T_DROP; t < T_WALL; t += BEAT) HITS.push(t); HITS.push(T_WALL, T_OUT);
function pulseAt(t, d = 8) { let p = 0; for (const k of HITS) if (t >= k) p = Math.max(p, Math.exp(-(t - k) * d)); return p; }
function catAt(t) { for (let i = CATS.length - 1; i >= 0; i--) if (t >= CATS[i].t0) return i; return -1; }

const _rnd = mulberry(39);
const GRAINS = [];
for (let i = 0; i < 6; i++) {
  const g = document.createElement('canvas'); g.width = W / 2; g.height = H / 2;
  const gx = g.getContext('2d'); const im = gx.createImageData(g.width, g.height);
  for (let j = 0; j < im.data.length; j += 4) { const v = _rnd() * 255; im.data[j] = im.data[j + 1] = im.data[j + 2] = v; im.data[j + 3] = 14; }
  gx.putImageData(im, 0, 0); GRAINS.push(g);
}
function finish(t, frame, barFill) {
  const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.7)'); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  ctx.drawImage(GRAINS[frame % GRAINS.length], 0, 0, W, H);
  ctx.fillStyle = barFill; ctx.fillRect(0, H - 5, W * clamp(t / DUR), 5);
}
function watermark(rgb = '240,240,240') {
  const s = 'x.com/nrqa__';
  font('500 24px IDMed');
  txt(s, 56, 62, `rgba(${rgb},0.45)`, 'left', 'middle');
  txt(s, W - 56, H - 50, `rgba(${rgb},0.45)`, 'right', 'middle');
  font('500 30px IDMed');
  txt(s, W / 2, H / 2, `rgba(${rgb},0.16)`, 'center', 'middle');
}
function fadeOut(t) { const fo = prog(t, DUR - 0.3, DUR); if (fo > 0) { ctx.fillStyle = `rgba(0,0,0,${fo})`; ctx.fillRect(0, 0, W, H); } }
const FONTS_READY = Promise.all(['10px IDBlack', '10px IDBold', '10px IDMed', 'italic 10px NR', '600 10px JBM', '400 10px JBM'].map(f => document.fonts.load(f)));
