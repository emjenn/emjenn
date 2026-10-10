"""Procedural 15 s soundtrack: 120 BPM synthwave/electronic in A minor.
Beat-locked to the visual timeline (scene cuts on 4.0, 5.5, 7.0, 8.5, 9.5, 12.0 s)."""
import numpy as np, wave, sys

SR = 48000
DUR = 15.0
N = int(SR * DUR)
BPM = 120
BEAT = 60 / BPM
rng = np.random.default_rng(7)
t = np.arange(N) / SR

def midi(m): return 440.0 * 2 ** ((m - 69) / 12)

def onepole_lp(x, fc):
    """One-pole low-pass; fc may be scalar or per-sample array."""
    fc = np.broadcast_to(np.asarray(fc, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x); s = 0.0
    xl, al = x.tolist(), a.tolist()
    for i in range(len(xl)):
        s += al[i] * (xl[i] - s); y[i] = s
    return y

def lp2(x, fc): return onepole_lp(onepole_lp(x, fc), fc)
def hp(x, fc): return x - onepole_lp(x, fc)

def place(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf): return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n] * gain

def env_ad(n, a, d):
    tt = np.arange(n) / SR
    return np.minimum(1, tt / max(a, 1e-4)) * np.exp(-tt / d)

# ---------------- drums ----------------
def kick():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    f = 45 + 120 * np.exp(-tt / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tt / 0.28)
    click = rng.standard_normal(n) * np.exp(-tt / 0.003) * 0.35
    return np.tanh((body + click) * 1.6)

def clap():
    n = int(0.4 * SR); tt = np.arange(n) / SR
    nz = hp(rng.standard_normal(n), 900); nz = lp2(nz, 6000)
    e = np.zeros(n)
    for k, off in enumerate([0, 0.011, 0.022]):
        e += np.where(tt >= off, np.exp(-(tt - off) / 0.008), 0) * (0.7 if k < 2 else 0)
    e += np.where(tt >= 0.022, np.exp(-(tt - 0.022) / 0.13), 0)
    return nz * e * 1.4

def hat(open_=False):
    n = int((0.35 if open_ else 0.08) * SR); tt = np.arange(n) / SR
    nz = hp(hp(rng.standard_normal(n), 7000), 7000)
    return nz * np.exp(-tt / (0.11 if open_ else 0.018))

def crash():
    n = int(2.8 * SR); tt = np.arange(n) / SR
    nz = hp(rng.standard_normal(n), 4000)
    return nz * np.exp(-tt / 0.9) * 0.6

def impact():
    n = int(2.5 * SR); tt = np.arange(n) / SR
    f = 32 + 90 * np.exp(-tt / 0.08)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.9)
    nz = lp2(rng.standard_normal(n), 900) * np.exp(-tt / 0.25) * 0.8
    return np.tanh((boom + nz) * 1.8)

def whoosh(length=0.5, up=True):
    n = int(length * SR); tt = np.arange(n) / SR
    p = tt / length
    fc = 300 + 7000 * (p ** 2 if up else (1 - p) ** 2)
    nz = onepole_lp(rng.standard_normal(n), fc)
    nz = hp(nz, 200)
    e = np.sin(np.pi * p) ** 2
    return nz * e

def riser(length):
    n = int(length * SR); tt = np.arange(n) / SR; p = tt / length
    nz = onepole_lp(rng.standard_normal(n), 200 + 9000 * p ** 3)
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * p ** 2) / SR) * 0.25
    return (hp(nz, 300) + tone) * p ** 2

# ---------------- synths ----------------
def saw(freq, n, phase0=0.0):
    ph = (phase0 + np.cumsum(np.full(n, freq) / SR)) % 1.0
    return 2 * ph - 1

def supersaw(freqs, n, voices=5, detune=0.012):
    out = np.zeros(n)
    for f in freqs:
        for v in range(voices):
            d = 1 + detune * (v - (voices - 1) / 2) / ((voices - 1) / 2)
            out += saw(f * d, n, rng.random())
    return out / (len(freqs) * voices)

CHORDS = {  # (root midi, voicing)
    'Am': (45, [57, 60, 64, 69]),
    'F':  (41, [57, 60, 65, 69]),
    'C':  (48, [55, 60, 64, 67]),
    'G':  (43, [55, 59, 62, 67]),
    'Em': (40, [55, 59, 64, 67]),
}
# bar index -> chord  (bar = 2 s)
PROG = ['Am', 'Am', 'F', 'C', 'G', 'Am', 'F', 'Am']

# sidechain envelope from kick positions
kick_times = [b * BEAT for b in range(int(2 / BEAT), int(11.5 / BEAT))] + \
             [b * BEAT for b in range(int(12 / BEAT), int(14 / BEAT))] + [14.0]
side = np.ones(N)
for kt in kick_times:
    i = int(kt * SR); n = min(int(0.45 * SR), N - i)
    tt = np.arange(n) / SR
    side[i:i + n] = np.minimum(side[i:i + n], 1 - 0.75 * np.exp(-tt / 0.11))

mixL = np.zeros(N); mixR = np.zeros(N)
def add(sig, at, g=1.0, pan=0.0):
    place(mixL, sig, at, g * np.sqrt(0.5 * (1 - pan)) * 1.414)
    place(mixR, sig, at, g * np.sqrt(0.5 * (1 + pan)) * 1.414)

# --- pads (supersaw chords) ---
pad = np.zeros(N)
for bar, ch in enumerate(PROG):
    start = bar * 2.0
    length = 2.0 if bar < 7 else 1.0
    if bar == 7: start = 14.0
    n = int((length + 0.05) * SR)
    s = supersaw([midi(m) for m in CHORDS[ch][1]], n)
    e = np.minimum(1, np.arange(n) / (0.02 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.04 * SR))
    place(pad, s * e, start)
# final chord ring out 14 -> 15
cut = 300 + 3200 * np.clip((t - 0.2) / 1.8, 0, 1) ** 2   # intro filter sweep
cut = np.where(t >= 2.0, 4200, cut)
cut = np.where((t >= 11.5) & (t < 12.0), 4200 - 3000 * (t - 11.5) / 0.5, cut)
cut = np.where(t >= 12.0, 5200, cut)
cut = np.where(t >= 14.0, 5200 * np.exp(-(t - 14.0) / 0.6) + 400, cut)
pad = lp2(pad, cut)
padL = pad * side; padR = np.roll(pad, int(0.012 * SR)) * side   # Haas width
mixL += padL * 0.55; mixR += padR * 0.55

# --- bass: octave-pumping 8ths ---
bass = np.zeros(N)
for bar, ch in enumerate(PROG):
    if bar == 0: continue
    root = CHORDS[ch][0]
    for k in range(8):
        at = bar * 2.0 + k * BEAT / 2
        if 11.5 <= at < 12.0 or at >= 14.0: continue
        m = root + (12 if k % 2 else 0)
        n = int(BEAT / 2 * SR * 0.95)
        tt = np.arange(n) / SR
        sq = np.sign(np.sin(2 * np.pi * midi(m) * tt)) * 0.5 + saw(midi(m), n) * 0.5
        place(bass, sq * np.exp(-tt / 0.18) * np.minimum(1, tt / 0.003), at)
bass = lp2(bass, 900)
bass_sub = np.zeros(N)
for bar, ch in enumerate(PROG):
    if bar == 0: continue
    n = int(2.0 * SR); tt = np.arange(n) / SR
    place(bass_sub, np.sin(2 * np.pi * midi(CHORDS[ch][0]) * tt), bar * 2.0)
bass_sub[int(11.5 * SR):int(12 * SR)] = 0
bass_sub *= np.where(t >= 14.0, np.exp(-(t - 14.0) / 0.4), 1)
bass = (bass * 0.5 + bass_sub * 0.35) * side
mixL += bass; mixR += bass

# --- pluck arp (16ths) ---
arp = np.zeros(N)
pattern = [0, 2, 1, 3, 2, 1, 3, 2]
for bar, ch in enumerate(PROG):
    notes = CHORDS[ch][1]
    for k in range(16):
        at = bar * 2.0 + k * (2.0 / 16)
        if at >= 15: break
        m = notes[pattern[k % 8]] + 12 + (12 if (k // 8) % 2 and bar >= 3 else 0)
        n = int(0.25 * SR); tt = np.arange(n) / SR
        tone = saw(midi(m), n) * 0.6 + np.sin(2 * np.pi * midi(m) * 2 * tt) * 0.25
        g = 0.55 if bar == 0 else (0.9 if k % 4 == 0 else 0.7)
        place(arp, tone * np.exp(-tt / 0.07) * g, at)
arp = lp2(arp, np.where(t < 2, 1200 + 2500 * t / 2, 4500))
# ping-pong delay (dotted 8th)
d = int(0.75 * BEAT * SR)
arpL = arp.copy(); arpR = np.zeros(N)
arpR[d:] += arp[:-d] * 0.45; arpL[2 * d:] += arp[:-2 * d] * 0.25; arpR[3 * d:] += arp[:-3 * d] * 0.12
mixL += arpL * 0.32; mixR += arpR * 0.32 + arp * 0.12

# --- lead hook in the finale (12 -> 15) ---
lead = np.zeros(N)
hook = [(12.0, 76, .25), (12.25, 74, .25), (12.5, 72, .5), (13.0, 69, .25), (13.25, 72, .25),
        (13.5, 74, .5), (14.0, 76, 1.0)]
for at, m, ln in hook:
    n = int((ln + 0.3) * SR); tt = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * tt) * np.clip(tt / 0.3, 0, 1)
    s = sum(saw(midi(m) * vib[0] * dd, n, rng.random()) for dd in (0.995, 1.0, 1.006)) / 3
    e = np.minimum(1, tt / 0.01) * np.where(tt < ln, 1, np.exp(-(tt - ln) / 0.12))
    place(lead, s * e, at)
lead = lp2(lead, 3800)
mixL += lead * 0.22; mixR += np.roll(lead, int(0.008 * SR)) * 0.22

# --- drums ---
K, C, HC, HO = kick(), clap(), hat(), hat(True)
for kt in kick_times:
    add(K, kt, 0.95)
for b in range(int(2 / BEAT), int(14 / BEAT)):
    at = b * BEAT
    if 11.5 <= at < 12.0: continue
    if b % 2 == 1: add(C, at, 0.55, 0.05)
    add(HO, at + BEAT / 2, 0.16, 0.25)
    for s16 in (0.25, 0.75):
        add(HC, at + s16 * BEAT, 0.12, -0.3)
# snare roll build 11.5 -> 12
for i in range(16):
    at = 11.5 + i * 0.5 / 16
    add(C, at, 0.15 + 0.4 * i / 16, 0.0)
# intro ticks
for i in range(8):
    add(HC, i * 0.25, 0.05 + 0.08 * i / 8, 0.3 if i % 2 else -0.3)

# --- FX ---
add(impact(), 0.0, 0.55)
add(riser(1.85), 0.1, 0.30)
add(impact(), 2.0, 0.65); add(crash(), 2.0, 0.35)
for at in (4.0, 5.5, 7.0, 8.5, 9.5):
    add(whoosh(0.45), at - 0.3, 0.30, 0.4 if at % 3 else -0.4)
add(riser(0.5), 11.5, 0.35)
add(impact(), 12.0, 0.7); add(crash(), 12.0, 0.4)
add(impact(), 14.0, 0.45); add(crash(), 14.0, 0.25)

# --- reverb (vectorised Schroeder combs) on a send ---
def comb(x, D, g):
    y = x.copy()
    for k in range(1, len(x) // D + 1):
        a, b = k * D, min((k + 1) * D, len(x))
        y[a:b] += g * y[a - D:b - D]
    return y
def verb(x):
    out = sum(comb(x, int(SR * dt), g) for dt, g in ((.0297, .80), (.0371, .78), (.0411, .76), (.0437, .74)))
    return lp2(out / 4, 5000)
wetL = verb(mixL * 0.25); wetR = verb(mixR * 0.25)
L = mixL + wetL * 0.35; R = mixR + np.roll(wetR, 331) * 0.35

# master: soft clip, fade
fade = np.clip((DUR - t) / 0.6, 0, 1)
L = np.tanh(L * 1.2) * fade; R = np.tanh(R * 1.2) * fade
peak = max(np.abs(L).max(), np.abs(R).max())
L, R = L / peak * 0.89, R / peak * 0.89
pcm = (np.stack([L, R], 1) * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', peak)
