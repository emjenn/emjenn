// Option C: "Orbit" - 20 projects orbit the mark on two rings; each in turn pulls into focus.
const OX = 960, OY = 520;
const ORB = i => ({ ring: i % 2, rx: i % 2 ? 860 : 560, ry: i % 2 ? 400 : 260, ph: (Math.floor(i / 2) / 10) * 6.283 + (i % 2) * 0.31 });
function orbXY(i, t) { const o = ORB(i), a = o.ph + t * (o.ring ? 0.18 : -0.26); return { x: OX + Math.cos(a) * o.rx, y: OY + Math.sin(a) * o.ry, z: Math.sin(a) }; }
const cur = t => (t >= T_R0 && t < T_RECAP) ? clamp(Math.floor((t - T_R0) / R_DUR), 0, N - 1) : -1;
const shown = (t, i) => t >= T_RECAP ? 1 : prog(t, SLOT_T(i), SLOT_T(i) + 0.15);

function background(t) {
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  const g = ctx.createRadialGradient(OX, OY, 0, OX, OY, 900);
  g.addColorStop(0, `rgba(255,255,255,${0.07 + pulseAt(t, 6) * 0.04})`); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function rings(t, a) {
  ctx.save(); ctx.globalAlpha = a; ctx.lineWidth = 1.5;
  [[560, 260], [860, 400]].forEach(([rx, ry], k) => { const p = eOutCubic(prog(t, 0.2 + k * 0.2, 0.9 + k * 0.2)); ctx.strokeStyle = 'rgba(255,255,255,0.18)'; ctx.setLineDash([6, 10]); ctx.lineDashOffset = -t * 30 * (k ? 1 : -1); ctx.beginPath(); ctx.ellipse(OX, OY, rx, ry, 0, 0, 6.283 * p); ctx.stroke(); });
  ctx.setLineDash([]); ctx.restore();
}
function satellites(t, a) {
  const c = cur(t);
  const order = [...Array(N).keys()].sort((i, j) => orbXY(i, t).z - orbXY(j, t).z);
  ctx.save(); ctx.globalAlpha = a;
  for (const i of order) {
    if (i === c) continue;
    const s = shown(t, i), { x, y, z } = orbXY(i, t), sc = 0.75 + 0.25 * (z + 1) / 2;
    if (s <= 0) { ctx.fillStyle = 'rgba(255,255,255,0.15)'; ctx.beginPath(); ctx.arc(x, y, 5, 0, 6.283); ctx.fill(); continue; }
    ctx.save(); ctx.globalAlpha *= (0.45 + 0.55 * (z + 1) / 2) * clamp(s * 2);
    ctx.fillStyle = C.white; ctx.beginPath(); ctx.arc(x, y, 7 * sc, 0, 6.283); ctx.fill();
    font(`${Math.round(22 * sc)}px IDBold`); txt(REPOS[i].name, x + 14, y + 7, C.white);
    ctx.restore();
  }
  ctx.restore();
}
function focusItem(t) {
  const c = cur(t); if (c < 0) return;
  const u = t - SLOT_T(c), r = REPOS[c], o = orbXY(c, t);
  const pin = eOutBack(prog(u, 0, 0.16), 1.4), back = eInExpo(prog(u, 0.36, 0.45));
  const k = pin * (1 - back);
  const x = lerp(o.x, OX, k), y = lerp(o.y, OY + 330, k);
  // tether line from orbit slot to focus
  ctx.strokeStyle = `rgba(255,255,255,${0.5 * k})`; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(o.x, o.y); ctx.lineTo(x, y - 60); ctx.stroke();
  ctx.save(); ctx.translate(x, y); ctx.scale(lerp(0.3, 1, k), lerp(0.3, 1, k)); ctx.globalAlpha = clamp(k * 1.5);
  ctx.fillStyle = 'rgba(0,0,0,0.85)'; roundRect(-760, -120, 1520, 210, 20); ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 2; ctx.stroke();
  font('600 28px JBM'); txt(r.n, 0, -72, C.g2, 'center');
  const ns = fit(r.name, 'IDBlack', 84, 1440, 40); txt(r.name, 0, -72 + ns + 4, C.white, 'center');
  font('400 24px JBM'); txt('↳ ' + r.url, 0, 64, C.g1, 'center');
  ctx.restore();
}
function core(t) {
  const p = eOutBack(prog(t, 0.6, 1.2), 1.8), pk = pulseAt(t, 8);
  ghMark(OX, OY, 190 * p * (1 + pk * 0.05), C.white);
  ctx.strokeStyle = 'rgba(255,255,255,0.3)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(OX, OY, 130 * p + pk * 20, 0, 6.283); ctx.stroke();
}
function closing(t) {
  // no text: satellites spiral into the core, mark grows with a shockwave
  const u = t - T_OUT, p = eInOutCubic(prog(u, 0.05, 0.7));
  for (let i = 0; i < N; i++) {
    const { x, y } = orbXY(i, t + p * 3); const xx = lerp(x, OX, p), yy = lerp(y, OY, p);
    ctx.fillStyle = `rgba(255,255,255,${1 - p})`; ctx.beginPath(); ctx.arc(xx, yy, 7, 0, 6.283); ctx.fill();
  }
  const m = lerp(1, 1.8, eOutBack(prog(u, 0.6, 1.05), 1.8)); ghMark(OX, OY, 190 * m, C.white);
  const rp = prog(u, 0.65, 1.4); if (rp > 0 && rp < 1) { ctx.strokeStyle = `rgba(255,255,255,${1 - rp})`; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(OX, OY, 220 + rp * 700, 0, 6.283); ctx.stroke(); }
}
function render(t, frame) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
  background(t);
  let shake = 0; for (const h of [T_DROP, T_OUT]) if (t >= h) shake = Math.max(shake, Math.exp(-(t - h) * 8));
  ctx.save(); ctx.translate((hash(frame) - 0.5) * 16 * shake, (hash(frame + 5) - 0.5) * 16 * shake);
  if (t < T_OUT) {
    const dim = t >= T_DROP && t < T_R0 ? 0.3 : 1;
    rings(t, dim); satellites(t, dim); core(t); focusItem(t);
    titleCard(t, W / 2, 'center');
  } else closing(t);
  ctx.restore();
  flashes(t, [[T_DROP, '255,255,255', 0.45], [T_RECAP, '255,255,255', 0.2], [T_OUT, '255,255,255', 0.45]]);
  finish(t, frame);
}
window.ready = FONTS_READY.then(() => render(0, 0));
