"""Three original 15s tracks, fully synthesized (no samples), one per video option.

  A  "slam"    128 BPM  F minor house / electro. title 8 beats, prompts every 3 beats.
  B  "console" 140 BPM  dark trap, 808 slides, hat rolls. title 6 beats, prompts every 3.5 beats.
  C  "orbit"   160 BPM  liquid drum & bass, reese + pads. title 6 beats, prompts every 4 beats.

Each prompt change gets a hit/whoosh so the cuts in the video land on the music.
usage: python3 music.py A|B|C out.wav
"""
import sys
import wave

import numpy as np
from scipy.signal import lfilter

SR = 44100
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(11)

STYLE = sys.argv[1]
OUT = sys.argv[2]

L = np.zeros(N)
R = np.zeros(N)


def add(sig, t0, gain=1.0, pan=0.0, bus=None):
    i0 = int(round(t0 * SR))
    if i0 >= N or i0 < 0:
        return
    sig = sig[: N - i0]
    gl = gain * np.cos((pan + 1) * np.pi / 4)
    gr = gain * np.sin((pan + 1) * np.pi / 4)
    bl, br = bus if bus is not None else (L, R)
    bl[i0 : i0 + len(sig)] += sig * gl
    br[i0 : i0 + len(sig)] += sig * gr


def tvec(d):
    return np.arange(int(d * SR)) / SR


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lp(x, cutoff):
    """one-pole lowpass; cutoff scalar or per-sample (processed in 64-sample blocks)"""
    if np.isscalar(cutoff):
        a = 1 - np.exp(-2 * np.pi * cutoff / SR)
        return lfilter([a], [1, a - 1], x)
    y = np.empty_like(x)
    zi = np.zeros(1)
    for s in range(0, len(x), 64):
        a = 1 - np.exp(-2 * np.pi * cutoff[s] / SR)
        y[s : s + 64], zi = lfilter([a], [1, a - 1], x[s : s + 64], zi=zi)
    return y


def lp2(x, cutoff):
    return lp(lp(x, cutoff), cutoff)


def hp(x, cutoff):
    return x - lp(x, cutoff)


def osc_saw(f, t, phase=0.0):
    ph = np.cumsum(np.broadcast_to(f, t.shape)) / SR + phase
    return 2 * (ph % 1.0) - 1


def osc_sin(f, t, phase=0.0):
    return np.sin(2 * np.pi * (np.cumsum(np.broadcast_to(f, t.shape)) / SR + phase))


def env_ar(t, d, a=0.005, r=0.05):
    return np.minimum(t / a, 1) * np.clip((d - t) / r, 0, 1)


# ---------------- drums ----------------
def kick(d=0.45, f0=48, punch=120, drive=1.8):
    t = tvec(d)
    f = f0 + punch * np.exp(-t * 30)
    body = osc_sin(f, t) * np.exp(-t * 7)
    click = rng.standard_normal(len(t)) * np.exp(-t * 450) * 0.3
    return np.tanh((body + click) * drive)


def k808(note, d, glide_to=None):
    t = tvec(d)
    f0 = midi(note)
    f = np.full(len(t), f0)
    if glide_to is not None:
        f = f0 * (midi(glide_to) / f0) ** np.clip((t - d * 0.45) / (d * 0.3), 0, 1)
    f = f * (1 + 1.6 * np.exp(-t * 40))
    s = osc_sin(f, t) * np.exp(-t * 1.6) * env_ar(t, d, 0.002, 0.04)
    return np.tanh(s * 2.2) * 0.9


def clap(d=0.3, bright=4500):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    env = np.exp(-t * 22)
    for k in (0.0, 0.011, 0.022):
        env += (t >= k) * np.exp(-np.maximum(t - k, 0) * 140) * 0.8
    return hp(lp(n, bright), 900) * env


def snare(d=0.25, tone=185, crack=1.0):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    body = osc_sin(tone * (1 + 0.5 * np.exp(-t * 60)), t) * np.exp(-t * 25)
    noise = hp(lp(n, 7000), 1200) * np.exp(-t * 16) * crack
    return np.tanh((body * 0.8 + noise) * 1.4)


def hat(d=0.05, open_=False, hpf=7500):
    d = 0.24 if open_ else d
    t = tvec(d)
    return hp(rng.standard_normal(len(t)), hpf) * np.exp(-t * (13 if open_ else 75))


def rim(d=0.06):
    t = tvec(d)
    return (osc_sin(1700, t) * 0.6 + hp(rng.standard_normal(len(t)), 3000) * 0.5) * np.exp(-t * 70)


# ---------------- fx ----------------
def riser(d, f0=200, f1=7000):
    t = tvec(d)
    x = t / d
    n = lp(rng.standard_normal(len(t)), f0 * (f1 / f0) ** x) * x**2
    sweep = lp(osc_saw(110 * 2 ** (3 * x), t), 3000) * 0.15 * x**3
    return n + sweep


def impact(d=2.5, f0=30):
    t = tvec(d)
    boom = osc_sin(f0 + 90 * np.exp(-t * 6), t) * np.exp(-t * 2.2)
    crash = hp(rng.standard_normal(len(t)), 3500) * np.exp(-t * 2.6) * 0.33
    return np.tanh(boom * 1.5) + crash


def whoosh(d=0.5, rev=False):
    t = tvec(d)
    x = t / d
    cut = 400 + 7500 * (x if not rev else 1 - x)
    return lp(rng.standard_normal(len(t)), cut) * np.sin(np.pi * x) ** 2


def zap(d=0.18, f0=2400, f1=120):
    t = tvec(d)
    return osc_sin(f0 * (f1 / f0) ** (t / d), t) * np.exp(-t * 14)


def glitch(d=0.12):
    t = tvec(d)
    sq = np.sign(osc_sin(80 + rng.random() * 900, t))
    return sq * (np.floor(t * 120) % 2) * np.exp(-t * 18) * 0.6


def downlifter(d=1.6):
    t = tvec(d)
    return lp(rng.standard_normal(len(t)), 8000 * np.exp(-t * 3) + 200) * np.exp(-t * 1.8)


# ---------------- tonal ----------------
def supersaw(notes, d, cutoff=2400, voices=7, detune=0.18, attack=0.01, release=0.15):
    t = tvec(d)
    sig = np.zeros(len(t))
    for n in notes:
        for v in range(voices):
            cents = (v - (voices - 1) / 2) / ((voices - 1) / 2) * detune * 100
            sig += osc_saw(midi(n) * 2 ** (cents / 1200), t, phase=rng.random())
    sig /= voices * len(notes)
    return lp2(sig, cutoff) * env_ar(t, d, attack, release)


def pluck(note, d=0.22, bright=5000, decay=9):
    t = tvec(d)
    sig = osc_saw(midi(note), t) * 0.6 + np.sign(osc_sin(midi(note) * 1.005, t)) * 0.3
    return lp(sig, 300 + bright * np.exp(-t * 18)) * np.exp(-t * decay)


def bell(note, d=0.9):
    t = tvec(d)
    f = midi(note)
    mod = osc_sin(f * 3.5, t) * 2.2 * np.exp(-t * 5)
    car = np.sin(2 * np.pi * f * t + mod)
    return car * np.exp(-t * 3.2) * env_ar(t, d, 0.002, 0.1)


def bass_house(note, d):
    t = tvec(d)
    f = midi(note)
    sig = osc_saw(f, t) * 0.7 + osc_sin(f / 2, t) * 0.6
    return np.tanh(lp(sig, 380 + 1100 * np.exp(-t * 10)) * 1.7 * env_ar(t, d, 0.004, 0.03))


def reese(note, d, cutoff=700):
    t = tvec(d)
    f = midi(note)
    sig = osc_saw(f * 0.995, t) + osc_saw(f * 1.005, t, 0.3) + osc_sin(f / 2, t) * 0.8
    wob = cutoff * (1 + 0.6 * np.sin(2 * np.pi * 2.1 * t))
    return np.tanh(lp2(sig, wob) * 1.5) * env_ar(t, d, 0.01, 0.06)


def pad(notes, d, cutoff=1800, attack=0.6, release=0.8):
    return supersaw(notes, d, cutoff=cutoff, voices=5, detune=0.12, attack=attack, release=release)


# ---------------- mix helpers ----------------
def reverb(x, delays, fb=0.78, mix=0.22):
    out = np.zeros_like(x)
    for d in delays:
        D = int(d * SR)
        y = np.copy(x)
        for i in range(D, len(y), D):
            y[i : i + D] += y[i - D : i][: len(y[i : i + D])] * fb
        out += y
    return lp(out / len(delays), 5000) * mix


def duck_curve(times, length, depth=0.65, speed=9):
    duck = np.ones(N)
    t = tvec(length)
    env = 1 - depth * np.exp(-t * speed)
    for kt in times:
        i0 = int(kt * SR)
        if i0 >= N:
            continue
        seg = duck[i0 : i0 + len(env)]
        duck[i0 : i0 + len(env)] = np.minimum(seg, env[: len(seg)])
    return duck


# music bus (gets sidechained) vs drum bus
ML, MR = np.zeros(N), np.zeros(N)
MUS = (ML, MR)
duck_times = []

# =====================================================================
if STYLE == "A":
    # 128 BPM, F minor. title 0..8 beats (drop at beat 4), prompts every 3 beats from beat 8
    BPM = 128
    B = 60 / BPM
    T_DROP = 4 * B
    T_P = [8 * B + i * 3 * B for i in range(7)]
    T_OUT = T_P[-1] + 3 * B
    Fm = (41, [56, 60, 63, 65 + 2])
    Db = (37, [56, 61, 65, 68])
    Ab = (44, [56, 60, 63, 68])
    Eb = (39, [55, 58, 63, 67])
    prog = [Fm, Db, Ab, Eb]
    kk = kick()
    # intro: filtered pad, riser, accelerating hats, 4 title slams
    add(pad(Fm[1], T_DROP + 0.2, cutoff=1000, attack=0.4), 0, 0.5, bus=MUS)
    add(riser(T_DROP), 0, 0.45)
    for i in range(4):
        add(kick(0.3, f0=55, punch=200), i * B, 0.55)
        add(zap(0.25, 3000, 200), i * B, 0.12, pan=(-0.4, 0.4, -0.2, 0.2)[i])
    for i in range(16):
        add(hat(), i * B / 4, 0.04 + 0.012 * i, pan=0.3)
    for i in range(8):
        add(snare(0.12), T_DROP - B + i * B / 8, 0.05 + 0.03 * i)
    add(impact(), T_DROP, 0.85)
    add(supersaw([n + 12 for n in Fm[1]], B * 2, cutoff=4500, release=0.6), T_DROP, 0.35, bus=MUS)
    # groove from drop to outro
    t = T_DROP
    beat_i = 0
    while t < T_OUT - 1e-6:
        root, ch = prog[(beat_i // 4) % 4]
        duck_times.append(t)
        add(kk, t, 0.95)
        add(hat(), t + B / 2, 0.2, pan=0.25)
        add(hat(open_=True), t + B / 2, 0.06, pan=-0.25)
        if beat_i % 2 == 1:
            add(clap(), t, 0.42, pan=0.05)
        for s in range(4):
            add(hat(0.03), t + s * B / 4, 0.035 + 0.025 * (s % 2), pan=-0.35)
        add(supersaw([n + 12 for n in ch], B * 0.42, cutoff=3400, release=0.07), t + B / 2, 0.28, pan=0.2 * (-1) ** beat_i, bus=MUS)
        add(bass_house(root, B / 2 * 0.9), t + B / 2, 0.55, bus=MUS)
        add(bass_house(root + 12, B / 4 * 0.8), t + B * 0.75, 0.25, bus=MUS)
        if t >= T_P[0]:
            arp = [0, 2, 1, 3]
            for s in range(4):
                add(pluck(ch[arp[(beat_i + s) % 4]] + 12, 0.2), t + s * B / 4, 0.12, pan=0.45 * np.sin(beat_i + s))
        t += B
        beat_i += 1
    for i, tp in enumerate(T_P):
        add(whoosh(0.45), tp - 0.32, 0.22, pan=(-1) ** i * 0.3)
        add(zap(0.16, 1800 + 200 * i, 150), tp, 0.10)
    add(impact(2.0), T_OUT, 0.8)
    add(kk, T_OUT, 1.0)
    add(supersaw([n + 12 for n in Fm[1]] + [65], DUR - T_OUT, cutoff=3200, attack=0.005, release=1.0), T_OUT, 0.55, bus=MUS)
    add(bass_house(29, 1.2), T_OUT, 0.5, bus=MUS)
    add(downlifter(1.4), T_OUT, 0.22)
    duck_times.append(T_OUT)
    duck_len = B
    rv = ((0.0297, 0.0371, 0.0411, 0.0437), (0.0313, 0.0353, 0.0423, 0.0459))

# =====================================================================
elif STYLE == "B":
    # 140 BPM dark trap, C# minor. title 6 beats, prompts every 3.5 beats
    BPM = 140
    B = 60 / BPM
    T_P = [6 * B + i * 3.5 * B for i in range(7)]
    T_OUT = T_P[-1] + 3.5 * B
    # bell melody over whole track, intro filtered
    mel = [73, 76, 80, 78, 76, 73, 71, 73]
    for i in range(int(DUR / (B / 2))):
        tt = i * B / 2
        if tt > T_OUT + B * 2:
            break
        n = mel[i % 8] - (12 if (i // 8) % 2 else 0)
        g = 0.11 if tt < T_P[0] else 0.13
        add(bell(n, 0.8), tt, g, pan=0.35 * np.sin(i * 0.9), bus=MUS)
    add(pad([61, 64, 68, 71], T_OUT + 0.5, cutoff=1400, attack=1.0), 0, 0.34, bus=MUS)
    add(riser(T_P[0]), 0, 0.35)
    # intro: rim ticks + glitches building to the drop
    for i in range(6):
        add(rim(), i * B, 0.18, pan=0.2)
        add(glitch(), i * B + B / 2, 0.06, pan=-0.3)
    for i in range(12):
        add(hat(0.03), T_P[0] - B * 1.5 + i * B / 8, 0.05 + 0.012 * i, pan=0.25)
    add(impact(2.2, 26), T_P[0], 0.85)
    # half-time groove: kick+808 pattern, snare on beat 3 of each bar, hat rolls
    bars = int((T_OUT - T_P[0]) / (4 * B)) + 1
    kpat = [0, 1.5, 2.75, 3.5]  # in beats within a bar
    bassnotes = [37, 37, 40, 35]
    for b in range(bars):
        bt = T_P[0] + b * 4 * B
        for j, kb in enumerate(kpat):
            kt = bt + kb * B
            if kt >= T_OUT:
                continue
            nxt = kpat[j + 1] if j + 1 < len(kpat) else 4
            d = (nxt - kb) * B * 0.95
            gl = bassnotes[(j + 1) % 4] if j == 3 and b % 2 else None
            add(k808(bassnotes[(b + j) % 4] - 12, d, glide_to=(gl - 12) if gl else None), kt, 0.75)
            add(kick(0.18, f0=60, punch=160, drive=1.2), kt, 0.45)
            duck_times.append(kt)
        st = bt + 2 * B
        if st < T_OUT:
            add(snare(0.3, 200), st, 0.55)
            add(clap(0.3, 6000), st, 0.3)
        # hats: 8ths with triplet / 32nd rolls on bar end
        for s in range(8):
            ht = bt + s * B / 2
            if ht < T_OUT:
                add(hat(0.035), ht, 0.13, pan=0.3)
        roll_t = bt + 3 * B
        steps = 6 if b % 2 else 8
        for s in range(steps):
            ht = roll_t + s * B / steps
            if ht < T_OUT:
                add(hat(0.025), ht, 0.06 + 0.012 * s, pan=-0.2 + 0.07 * s)
    for i, tp in enumerate(T_P[1:]):
        add(whoosh(0.4), tp - 0.3, 0.2, pan=(-1) ** i * 0.3)
        add(glitch(0.1), tp, 0.08)
    add(impact(2.0, 24), T_OUT, 0.8)
    add(k808(25, DUR - T_OUT), T_OUT, 0.8)
    add(bell(73, 1.8), T_OUT, 0.18, bus=MUS)
    add(bell(80, 1.8), T_OUT + B / 2, 0.12, pan=0.4, bus=MUS)
    add(bell(85, 1.8), T_OUT + B, 0.09, pan=-0.4, bus=MUS)
    add(downlifter(1.6), T_OUT, 0.2)
    duck_times.append(T_OUT)
    duck_len = B * 0.9
    rv = ((0.0337, 0.0391, 0.0451, 0.0497), (0.0353, 0.0413, 0.0473, 0.0519))

# =====================================================================
else:
    # 160 BPM liquid DnB, D minor. title 6 beats, prompts every 4 beats (1 bar)
    BPM = 160
    B = 60 / BPM
    T_P = [6 * B + i * 4 * B for i in range(7)]
    T_OUT = T_P[-1] + 4 * B
    chords = [(38, [62, 65, 69, 72]), (34, [62, 65, 70, 74]), (41, [60, 65, 69, 72]), (36, [60, 64, 67, 72])]
    # airy intro: pad + falling plucks + riser
    add(pad(chords[0][1], T_P[0] + 0.3, cutoff=1600, attack=0.3), 0, 0.42, bus=MUS)
    add(riser(T_P[0], 300, 9000), 0, 0.38)
    for i in range(12):
        add(pluck([86, 81, 77, 74][i % 4], 0.35, 4000, 6), i * B / 2, 0.07 + 0.006 * i, pan=0.5 * (-1) ** i, bus=MUS)
    add(impact(2.4), T_P[0], 0.75)
    # two-step DnB: K . . . S . . K | K . S . . . . .  (8ths over 2 beats... use 16ths per bar)
    kpos = [0, 10]
    spos = [4, 12]
    gpos = [7, 15]  # ghost snares
    for bi in range(8):
        bt = T_P[0] + bi * 4 * B
        if bt >= T_OUT:
            break
        root, ch = chords[bi % 4]
        step = B / 4
        for s in kpos:
            add(kick(0.3, f0=52, punch=140), bt + s * step, 0.85)
            duck_times.append(bt + s * step)
        for s in spos:
            add(snare(0.28, 210, 1.1), bt + s * step, 0.6)
        for s in gpos:
            add(snare(0.08, 230, 0.6), bt + s * step, 0.12)
        for s in range(16):
            add(hat(0.028 if s % 2 else 0.04), bt + s * step, 0.07 if s % 2 else 0.12, pan=0.3)
        add(hat(open_=True), bt + 6 * step, 0.08, pan=-0.3)
        add(hat(open_=True), bt + 14 * step, 0.08, pan=-0.3)
        add(reese(root, 4 * B * 0.98, 600 + 80 * bi), bt, 0.42, bus=MUS)
        add(pad([n + 12 for n in ch], 4 * B + 0.1, cutoff=2600, attack=0.05, release=0.3), bt, 0.22, bus=MUS)
        arp = [0, 1, 2, 3, 2, 1, 3, 2]
        for s in range(8):
            add(pluck(ch[arp[s]] + 12, 0.25, 4500, 8), bt + s * B / 2, 0.08, pan=0.5 * np.sin(s + bi), bus=MUS)
    for i, tp in enumerate(T_P[1:]):
        add(whoosh(0.5), tp - 0.36, 0.2, pan=(-1) ** i * 0.3)
        add(zap(0.22, 900, 3000), tp, 0.05, pan=(-1) ** i * 0.5)
    add(impact(2.4), T_OUT, 0.8)
    add(kick(0.5), T_OUT, 0.9)
    add(pad([62, 65, 69, 72, 76], DUR - T_OUT, cutoff=2800, attack=0.01, release=1.4), T_OUT, 0.42, bus=MUS)
    add(reese(26, 1.6, 500), T_OUT, 0.35, bus=MUS)
    for i, n in enumerate([86, 81, 77, 74, 69, 65]):
        add(pluck(n, 0.6, 3500, 5), T_OUT + B + i * B / 2, 0.1 * (1 - i / 8), pan=0.5 * (-1) ** i, bus=MUS)
    duck_times.append(T_OUT)
    duck_len = B
    rv = ((0.0277, 0.0351, 0.0391, 0.0457), (0.0293, 0.0373, 0.0413, 0.0479))

# ---------------- master ----------------
duck = duck_curve(duck_times, duck_len)
ML *= duck
MR *= duck
L += ML
R += MR
Lw = L + reverb(L, rv[0])
Rw = R + reverb(R, rv[1])
fade = np.clip((DUR - np.arange(N) / SR) / 0.4, 0, 1)
fade_in = np.clip(np.arange(N) / SR / 0.01, 0, 1)
mx = np.stack([Lw, Rw], 1) * (fade * fade_in)[:, None]
mx /= np.max(np.abs(mx)) + 1e-9
mx = np.tanh(mx * 1.7) / np.tanh(1.7) * 0.93
with wave.open(OUT, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mx * 32767).astype("<i2").tobytes())
print("wrote", OUT, "prompt times:", [round(x, 3) for x in T_P], "outro:", round(T_OUT, 3))
