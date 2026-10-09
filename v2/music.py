"""Procedural 15 s soundtrack #2: 128 BPM tech-house / electro in F minor.
Organ-style chord stabs, resonant acid bassline, shuffled hats, zaps on every company cut.
Beat grid: 0.46875 s. Drop @1.875 (beat 4), company cuts every 2 beats, outro drop @11.25, last hit @14.0625."""
import numpy as np, wave, sys

SR, DUR = 48000, 15.0
N = int(SR * DUR); t = np.arange(N) / SR
BEAT = 60 / 128; S16 = BEAT / 4; BAR = BEAT * 4
rng = np.random.default_rng(2026)
midi = lambda m: 440.0 * 2 ** ((m - 69) / 12)

def svf(x, fc, q=0.7, mode='lp'):
    """Chamberlin state-variable filter; fc scalar or per-sample."""
    fc = np.broadcast_to(np.asarray(fc, float), x.shape)
    f = (2 * np.sin(np.pi * np.clip(fc, 20, SR / 6) / SR)).tolist()
    damp = 1 / q; lp = bp = 0.0; out = [0.0] * len(x); xs = x.tolist()
    for i in range(len(xs)):
        hp = xs[i] - lp - damp * bp
        bp += f[i] * hp; lp += f[i] * bp
        out[i] = lp if mode == 'lp' else (hp if mode == 'hp' else bp)
    return np.array(out)

def onepole(x, fc):
    a = 1 - np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x.tolist()): s += a * (v - s); y[i] = s
    return y
hpf = lambda x, fc: x - onepole(x, fc)

L = np.zeros(N); R = np.zeros(N)
def add(sig, at, g=1.0, pan=0.0):
    i = int(round(at * SR))
    if i >= N or i < 0: return
    n = min(len(sig), N - i)
    L[i:i + n] += sig[:n] * g * np.sqrt(1 - pan) ; R[i:i + n] += sig[:n] * g * np.sqrt(1 + pan)

# ---------------- instruments ----------------
def kick():
    n = int(0.42 * SR); tt = np.arange(n) / SR
    f = 50 + 190 * np.exp(-tt / 0.022)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.22)
    click = hpf(rng.standard_normal(n), 2000) * np.exp(-tt / 0.002) * 0.5
    return np.tanh((body + click) * 2.2) * 0.9

def clap():
    n = int(0.35 * SR); tt = np.arange(n) / SR
    nz = svf(rng.standard_normal(n), 1600, 1.2, 'bp')
    e = sum(np.where(tt >= o, np.exp(-(tt - o) / 0.006), 0) for o in (0, .009, .018)) * 0.6
    e += np.where(tt >= .027, np.exp(-(tt - .027) / 0.11), 0)
    return nz * e * 2.2

def rim():
    n = int(0.08 * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1700 * tt) * 0.6 + svf(rng.standard_normal(n), 3500, 2, 'bp')) * np.exp(-tt / 0.012)

def hat(open_=False):
    n = int((0.3 if open_ else 0.06) * SR); tt = np.arange(n) / SR
    # metallic: sum of square partials (808-ish) + noise
    sq = sum(np.sign(np.sin(2 * np.pi * f * tt)) for f in (205.3, 304.4, 369.6, 522.7, 540, 800))
    sig = hpf(hpf(sq * 0.3 + rng.standard_normal(n) * 0.7, 7500), 7500)
    return sig * np.exp(-tt / (0.09 if open_ else 0.014))

def shaker():
    n = int(0.05 * SR); tt = np.arange(n) / SR
    return hpf(rng.standard_normal(n), 5000) * np.sin(np.pi * tt / tt[-1]) ** 2

def stab(notes, length=0.16, bright=1.0):
    n = int((length + 0.25) * SR); tt = np.arange(n) / SR
    s = np.zeros(n)
    for m in notes:
        f = midi(m)
        for h, a in ((1, 1), (2, .55), (3, .3), (4, .22), (6, .12), (8, .06)):   # organ drawbars
            s += a * np.sin(2 * np.pi * f * h * tt + rng.random() * 6.28)
        s += 0.35 * (2 * ((f * 1.004 * tt) % 1) - 1)                          # a little saw bite
    env = np.minimum(1, tt / 0.003) * np.where(tt < length, np.exp(-tt / 0.18), np.exp(-length / 0.18) * np.exp(-(tt - length) / 0.05))
    s = svf(s * env / len(notes), 900 + 4200 * bright * np.exp(-tt / 0.09), 1.4)
    return s

def zap(f0=2400, f1=90, length=0.18):
    n = int(length * SR); tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt / (length / 5))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (length / 2.5))

def impact():
    n = int(2.2 * SR); tt = np.arange(n) / SR
    f = 30 + 110 * np.exp(-tt / 0.06)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.7)
    return np.tanh((boom + onepole(rng.standard_normal(n), 700) * np.exp(-tt / 0.2)) * 2)

def crash(length=2.4):
    n = int(length * SR); tt = np.arange(n) / SR
    return hpf(rng.standard_normal(n), 5000) * np.exp(-tt / 0.75) * 0.7

def riser(length, f0=300, f1=8000):
    n = int(length * SR); p = np.arange(n) / n
    nz = svf(rng.standard_normal(n), f0 + (f1 - f0) * p ** 2.5, 3.0, 'bp')
    return nz * p ** 1.6

def reverse_cymbal(length):
    return crash(length)[::-1] * np.linspace(0, 1, int(length * SR)) ** 2

# ---------------- arrangement ----------------
# bar -> chord (F minor). bar = 1.875 s
CH = {'Fm': [53, 56, 60, 63], 'Db': [53, 56, 60, 61], 'Eb': [55, 58, 63, 67], 'Cm': [55, 58, 60, 63], 'Bbm': [53, 58, 61, 65]}
BASS = {'Fm': 29, 'Db': 25, 'Eb': 27, 'Cm': 24, 'Bbm': 22}
PROG = ['Fm', 'Fm', 'Db', 'Eb', 'Cm', 'Fm', 'Db', 'Eb']
chord_at = lambda tm: PROG[min(int(tm / BAR), 7)]
DROP, OUTRO, END_HIT = BAR, 6 * BAR, 30 * BEAT

# drums ----------------------------------------------------------------
K, CL, RM, HC, HO, SH = kick(), clap(), rim(), hat(), hat(True), shaker()
for b in range(32):
    tb = b * BEAT
    groove = DROP <= tb < END_HIT and not (OUTRO - BEAT <= tb < OUTRO)   # tiny break before the outro drop
    if groove or tb == END_HIT:
        add(K, tb, 0.8)
    if groove:
        if b % 2 == 1: add(CL, tb, 0.5, 0.05)
        add(HO, tb + BEAT / 2, 0.26, 0.3)
        for s in range(4):
            sw = 0.012 if s % 2 else 0                 # light swing on the off-16ths
            vel = (0.22, 0.12, 0.17, 0.12)[s]
            add(HC, tb + s * S16 + sw, vel, -0.35)
        add(SH, tb + 3 * S16 + 0.01, 0.06, 0.5)
        if b % 4 == 3: add(RM, tb + 3 * S16, 0.18, -0.2)
# intro: accelerating snare/clap roll into the drop
for i, tm in enumerate(np.concatenate([np.arange(0, BEAT * 2, S16 * 2), np.arange(BEAT * 2, BAR, S16)])):
    add(CL, tm, 0.06 + 0.32 * (tm / BAR) ** 1.5, 0.0)
# break roll before outro
for i in range(8):
    add(CL, OUTRO - BEAT + i * BEAT / 8, 0.15 + 0.03 * i)

# sidechain from the kick
side = np.ones(N)
for b in range(32):
    tb = b * BEAT
    if DROP <= tb <= END_HIT:
        i = int(tb * SR); n = min(int(0.4 * SR), N - i); tt = np.arange(n) / SR
        side[i:i + n] = np.minimum(side[i:i + n], 1 - 0.7 * np.exp(-tt / 0.09))

# chord stabs: syncopated house pattern (16th positions within a bar)
music = np.zeros(N)
STAB_POS = [0, 3, 6, 10, 12, 14]
for bar in range(8):
    ch = CH[PROG[bar]]
    for p in STAB_POS:
        tm = bar * BAR + p * S16
        if tm >= END_HIT + 0.01: break
        if OUTRO - BEAT <= tm < OUTRO: continue
        bright = 0.25 + 0.75 * (tm / BAR) if bar == 0 else 1.0
        sig = stab([m + 12 for m in ch], 0.11 if p % 4 else 0.16, bright)
        i = int(tm * SR); n = min(len(sig), N - i); music[i:i + n] += sig[:n] * (0.5 if bar == 0 else 0.62)
# the final stab rings out
sig = stab([m + 12 for m in CH['Fm']] + [65 + 12], 0.7, 1.0)
i = int(END_HIT * SR); n = min(len(sig), N - i); music[i:i + n] += sig[:n] * 0.75

# acid bass: rolling 16ths, resonant filter with per-note envelope
bass = np.zeros(N); cut = np.full(N, 200.0)
BASS_PAT = [0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1]   # 1 = octave up
for s in range(int(DROP / S16), int(END_HIT / S16)):
    tm = s * S16
    if OUTRO - BEAT <= tm < OUTRO: continue
    if s % 4 == 0: continue                                    # leave the kick alone
    root = BASS[chord_at(tm)] + 12 * BASS_PAT[s % 16] + 12
    n = int(S16 * SR * 0.92); tt = np.arange(n) / SR
    ph = (midi(root) * tt) % 1
    note = (2 * ph - 1) * 0.8 + np.sign(np.sin(2 * np.pi * midi(root) * tt)) * 0.2
    i = int(tm * SR); n = min(n, N - i)
    bass[i:i + n] += note[:n] * np.exp(-tt[:n] / 0.09)
    accent = 1.0 if s % 16 in (2, 7, 10, 14) else 0.55
    cut[i:i + n] = np.maximum(cut[i:i + n], 300 + 2600 * accent * np.exp(-tt[:n] / 0.05))
# filter opens more across the run of companies
cut *= np.where(t < OUTRO, 0.75 + 0.5 * np.clip((t - DROP) / (OUTRO - DROP), 0, 1), 1.25)
bass = np.tanh(svf(bass, cut, 4.5) * 1.8) * 0.55
sub = np.zeros(N)
for s in range(int(DROP / BEAT), int(END_HIT / BEAT) + 1):
    tm = s * BEAT
    if OUTRO - BEAT <= tm < OUTRO: continue
    n = int(BEAT * SR * (0.95 if tm < END_HIT else 2)); tt = np.arange(n) / SR
    f = midi(BASS[chord_at(tm)] + 12)
    note = np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / 0.004) * np.exp(-tt / (0.5 if tm < END_HIT else 0.35))
    i = int(tm * SR); n = min(n, N - i); sub[i:i + n] += note[:n]
music = music * side
bassmix = (bass * 1.3 + sub * 0.22) * side

# bell motif across the company run (call & response)
bell = np.zeros(N)
MOTIF = [(0, 72), (3, 75), (6, 77), (8, 79), (11, 77), (14, 75)]
for bar in range(1, 8):
    if bar == 6: continue
    for pos, m in MOTIF:
        tm = bar * BAR + pos * S16
        if tm >= END_HIT: break
        n = int(0.6 * SR); tt = np.arange(n) / SR; f = midi(m + (0 if PROG[bar] in ('Fm', 'Db') else 2) - (2 if PROG[bar] == 'Cm' else 0))
        tone = (np.sin(2 * np.pi * f * tt + 1.8 * np.sin(2 * np.pi * f * 3.5 * tt) * np.exp(-tt / 0.08))) * np.exp(-tt / 0.22)
        i = int(tm * SR); n = min(n, N - i); bell[i:i + n] += tone[:n]
d = int(BEAT * 0.75 * SR)
bellL = bell.copy(); bellR = np.zeros(N); bellR[d:] += bell[:-d] * 0.5; bellL[2 * d:] += bell[:-2 * d] * 0.25

L += music * 1.6 + bassmix + bellL * 0.16; R += np.roll(music, int(0.01 * SR)) * 1.6 + bassmix + bellR * 0.16 + bell * 0.04

# FX ------------------------------------------------------------------
add(riser(BAR, 400, 9000), 0.0, 0.28)
add(impact(), DROP, 0.75); add(crash(), DROP, 0.35)
for k in range(10):                                   # a zap on every company cut
    cut_t = DROP + k * 2 * BEAT
    add(zap(2600 - 120 * k, 110, 0.16), cut_t, 0.22, -0.4 if k % 2 else 0.4)
add(reverse_cymbal(0.9), OUTRO - 0.9, 0.35)
add(riser(BEAT, 800, 10000), OUTRO - BEAT, 0.3)
add(impact(), OUTRO, 0.85); add(crash(), OUTRO, 0.4)
add(impact(), END_HIT, 0.55); add(crash(3.0), END_HIT, 0.3)

# reverb send ----------------------------------------------------------
def comb(x, D, g):
    y = x.copy()
    for k in range(1, len(x) // D + 1):
        a, b = k * D, min((k + 1) * D, len(x)); y[a:b] += g * y[a - D:b - D]
    return y
def verb(x):
    return onepole(sum(comb(x, int(SR * dt), g) for dt, g in ((.0253, .82), (.0313, .80), (.0367, .78), (.0419, .76))) / 4, 4500)
wl, wr = verb((music + bellL) * 0.2), verb((np.roll(music, 97) + bellR) * 0.2)
L += wl * 0.4; R += np.roll(wr, 401) * 0.4

fade = np.clip((DUR - t) / 0.5, 0, 1)
L = np.tanh(L * 1.1) * fade; R = np.tanh(R * 1.1) * fade
pk = max(abs(L).max(), abs(R).max()); L, R = L / pk * 0.9, R / pk * 0.9
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([L, R], 1) * 32767).astype(np.int16).tobytes())
print('ok')
