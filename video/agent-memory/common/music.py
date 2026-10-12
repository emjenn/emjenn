"""Original 15s soundtracks for the "agent memory" videos, 120 BPM, A minor. Fully synthesized.
usage: python3 music.py funk|pop|hard out.wav
  0 intro, 2.0 drop, repos at 3.5 + 0.75i (10), 11.0 recap, 13 outro hit.
"""
import numpy as np
import wave
import sys

SR = 44100
BPM = 120
BEAT = 60 / BPM
BAR = BEAT * 4
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(11)

L = np.zeros(N)
R = np.zeros(N)


def add(sig, t0, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if i0 >= N or i0 < 0:
        return
    sig = sig[: N - i0]
    gl = gain * np.cos((pan + 1) * np.pi / 4)
    gr = gain * np.sin((pan + 1) * np.pi / 4)
    L[i0 : i0 + len(sig)] += sig * gl
    R[i0 : i0 + len(sig)] += sig * gr


def tvec(d):
    return np.arange(int(d * SR)) / SR


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def onepole_lp(x, cutoff):
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def hp(x, cutoff):
    return x - onepole_lp(x, cutoff)


def saw(f, t, phase=0.0):
    ph = np.cumsum(np.broadcast_to(f, t.shape)) / SR + phase
    return 2 * (ph % 1.0) - 1


# ---------- drums ----------
def kick(d=0.5):
    t = tvec(d)
    f = 42 + 140 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
    click = rng.standard_normal(len(t)) * np.exp(-t * 500) * 0.4
    return np.tanh((body + click) * 2.2)


def clap(d=0.35):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    env = np.exp(-t * 18)
    for k in (0.0, 0.009, 0.019, 0.028):
        env += (t >= k) * np.exp(-np.maximum(t - k, 0) * 160) * 0.8
    snare_tone = np.sin(2 * np.pi * 210 * t) * np.exp(-t * 35) * 0.6
    return hp(onepole_lp(n, 5200), 800) * env * 0.9 + snare_tone


def hat(d=0.05, open_=False):
    d = 0.25 if open_ else d
    t = tvec(d)
    return hp(rng.standard_normal(len(t)), 7500) * np.exp(-t * (12 if open_ else 80))


def snare_hit(d=0.12):
    t = tvec(d)
    tone = np.sin(2 * np.pi * 200 * t) * 0.5
    return (hp(rng.standard_normal(len(t)), 1500) * 0.8 + tone) * np.exp(-t * 32)


# ---------- fx ----------
def riser(d, f0=250, f1=9000):
    t = tvec(d)
    cut = f0 * (f1 / f0) ** (t / d)
    sig = onepole_lp(rng.standard_normal(len(t)), cut) * (t / d) ** 2
    sweep = saw(130 * 2 ** (3 * t / d), t) * 0.14 * (t / d) ** 3
    return sig + onepole_lp(sweep, 3500)


def impact(d=2.5):
    t = tvec(d)
    f = 28 + 100 * np.exp(-t * 5)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.0)
    crash = hp(rng.standard_normal(len(t)), 3500) * np.exp(-t * 2.6) * 0.32
    return np.tanh(boom * 1.6) + crash


def whoosh(d=0.6, rev=False):
    t = tvec(d)
    x = t / d
    env = np.sin(np.pi * x) ** 2
    cut = 500 + 8000 * (x if not rev else 1 - x)
    return onepole_lp(rng.standard_normal(len(t)), cut) * env


def blip(note, d=0.14):
    t = tvec(d)
    f = midi(note) * (1 + 0.5 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22)


# ---------- tonal ----------
def supersaw(notes, d, cutoff=2600, voices=7, detune=0.2, attack=0.006, release=0.12, wob=0.0):
    t = tvec(d)
    sig = np.zeros(len(t))
    for n in notes:
        for v in range(voices):
            cents = (v - (voices - 1) / 2) / ((voices - 1) / 2) * detune * 100
            sig += saw(midi(n) * 2 ** (cents / 1200), t, phase=rng.random())
    sig /= voices * len(notes)
    env = np.minimum(t / attack, 1) * np.clip((d - t) / release, 0, 1)
    if wob:  # future-bass volume wobble
        env *= 0.55 + 0.45 * np.cos(2 * np.pi * wob * t)
    return onepole_lp(sig, cutoff) * env


def pluck(note, d=0.2, bright=6000):
    t = tvec(d)
    f = midi(note)
    sig = saw(f, t) * 0.5 + np.sign(np.sin(2 * np.pi * f * 1.004 * t)) * 0.35
    return onepole_lp(sig, 300 + bright * np.exp(-t * 20)) * np.exp(-t * 10)


def sub(note, d):
    t = tvec(d)
    f = midi(note)
    sig = np.sin(2 * np.pi * f * t) + 0.35 * saw(f, t)
    sig = onepole_lp(sig, 260 + 700 * np.exp(-t * 12))
    env = np.minimum(t / 0.004, 1) * np.clip((d - t) / 0.03, 0, 1)
    return np.tanh(sig * 1.8 * env)



STYLE = sys.argv[1]
SLOTS = [3.5 + 0.75 * i for i in range(10)]
T_RECAP, T_OUT = 11.0, 13.0
kick_s, clap_s = kick(), clap()
kick_times = []


def b808(note, d=0.7, slide=0):
    t = tvec(d)
    f = midi(note) * 2 ** (slide * np.clip(1 - t / 0.15, 0, 1) / 12) * (1 + 1.2 * np.exp(-t * 40))
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * 2.8 * np.exp(-t * 1.8)) * np.clip((d - t) / 0.04, 0, 1)


def crush(x, bits=5, hold=6):
    y = np.repeat(x[::hold], hold)[: len(x)]
    q = 2 ** bits
    return np.round(y * q) / q


def stabm(notes, d=0.2, cut=2500):  # dark minor stab
    return supersaw(notes, d, cutoff=cut, attack=0.002, release=0.06, voices=5, detune=0.1)


def bell(note, d=0.6):
    t = tvec(d); f = midi(note)
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 8)) * np.exp(-t * 5)


AM = [57, 60, 64]; FM = [53, 57, 60]; GM = [55, 59, 62]; EM = [52, 55, 59]
PROG = [(45, AM), (41, FM), (43, GM), (40, EM)]

# ---------------- intro 0-2 ----------------
add(riser(2.0, 150, 9000), 0, 0.42)
if STYLE == 'spy':
    for s in range(16): add(hat(0.02), s * BEAT / 4, 0.05 + 0.04 * (s % 4 == 0), pan=0.3)  # clock tick
    for s in range(8): add(sub(45 + [0, 0, 3, 0, 6, 0, 3, 1][s], BEAT / 2 * 0.8), s * BEAT / 2, 0.35)
    add(supersaw([57, 60, 63], 2.0, cutoff=500, attack=1.2, release=0.2), 0, 0.35)
elif STYLE == 'pop':
    for s in range(16): add(pluck([60, 64, 67, 72][s % 4] + 12, 0.15, 1500 + s * 300), s * BEAT / 4, 0.07 + s * 0.004)
    add(supersaw([60, 64, 67, 71], 2.0, cutoff=900, attack=1.0, release=0.2), 0, 0.4)
elif STYLE == 'funk':
    for s in range(20): add(hp(rng.standard_normal(int(0.012 * SR)), 2000) * 0.5, 0.2 + s * 0.06, 0.12, pan=0.3)  # printer feed
    add(supersaw([55, 59, 62, 66], 2.0, cutoff=900, attack=0.8, release=0.2), 0, 0.35)
else:
    add(supersaw([45, 52, 57, 60], 2.0, cutoff=600, attack=1.2, release=0.2), 0, 0.5)
    for i in range(6): add(hat(0.03), 1.25 + i * BEAT / 8, 0.08)
for i in range(8):
    add(snare_hit(), 2.0 - BEAT * 2 + i * BEAT / 4, 0.08 + 0.05 * i)
add(impact(), 2.0, 0.9)

# ---------------- groove 2-13 ----------------
def bar_pop(b):
    t0 = b * BAR
    PP = [(48, [60, 64, 67, 71]), (45, [57, 60, 64, 67]), (41, [57, 60, 65, 69]), (43, [55, 59, 62, 67])]
    root, ch = PP[b % 4]
    for k in range(4):
        kt = t0 + k * BEAT; kick_times.append(kt); add(kick_s, kt, 0.9)
        if k in (1, 3): add(clap_s, kt, 0.45)
        add(hat(), kt + BEAT / 2, 0.14, pan=0.3)
        for e in range(2): add(sub(root + 12 * e, BEAT / 2 * 0.85), kt + e * BEAT / 2, 0.4)
    arp = [0, 1, 2, 3, 2, 1, 3, 2]
    for s in range(16): add(pluck(ch[arp[s % 8]] + 12, 0.16, 6500), t0 + s * BEAT / 4, 0.11, pan=0.5 * np.sin(s * 0.9))
    add(supersaw([n + 12 for n in ch], BAR, cutoff=2000, attack=0.05, release=0.3, voices=5), t0, 0.14)


def bar_spy(b):
    t0 = b * BAR
    for k in range(4):
        kt = t0 + k * BEAT; kick_times.append(kt); add(onepole_lp(kick_s, 3000), kt, 0.85)
        if k in (1, 3): add(snare_hit(0.15), kt, 0.35)
    for s in range(16): add(hat(0.02), t0 + s * BEAT / 4, 0.05 + 0.03 * (s % 4 == 0), pan=0.3)
    line = [0, 0, 3, 0, 6, 0, 3, 1]
    for s in range(8): add(sub(45 + line[s], BEAT / 2 * 0.8), t0 + s * BEAT / 2, 0.45)
    add(supersaw([57 + 12, 60 + 12, 63 + 12], BAR, cutoff=1200, attack=0.3, release=0.3, voices=5), t0, 0.12)


def bar_funk(b):
    t0 = b * BAR; root, ch = PROG[b % 4]
    for pos in (0.0, 0.75, 2.0, 2.5):
        kt = t0 + pos * BEAT; kick_times.append(kt); add(kick_s, kt, 0.85)
    for k in (1, 3): add(clap_s, t0 + k * BEAT, 0.5); add(snare_hit(0.12), t0 + k * BEAT, 0.3)
    for s in range(16): add(hat(0.025), t0 + s * BEAT / 4 + (0.03 if s % 2 else 0), 0.06 + 0.03 * (s % 2 == 0), pan=0.3)
    for pos, oct_ in ((0, 0), (0.5, 12), (1.25, 0), (1.75, 12), (2.5, 0), (3.0, 7), (3.5, 12)):
        add(np.tanh(pluck(root + oct_, 0.18, 1800) * 2), t0 + pos * BEAT, 0.4)
    for pos in (0.5, 2.25): add(stabm([n + 12 for n in ch], 0.1, 3500), t0 + pos * BEAT, 0.25, pan=-0.2)


def bar_techno(b):
    t0 = b * BAR; root, ch = PROG[b % 4]
    for k in range(4):
        kt = t0 + k * BEAT; kick_times.append(kt); add(kick_s, kt, 0.95)
        add(hat(open_=True), kt + BEAT / 2, 0.13, pan=0.25)
        if k in (1, 3): add(clap_s, kt, 0.35)
        add(sub(root, BEAT * 0.4), kt + BEAT / 2, 0.5)
    for s in range(16): add(hat(0.02), t0 + s * BEAT / 4, 0.04 + 0.03 * (s % 2), pan=-0.3)
    for pos in (0.75, 1.75, 3.25): add(stabm([n + 12 for n in ch], 0.12, 1800 + b * 200), t0 + pos * BEAT, 0.3, pan=0.2)


def bar_glitch(b):
    t0 = b * BAR; root, ch = PROG[b % 4]
    for pos in (0.0, 0.75, 2.5): kt = t0 + pos * BEAT; kick_times.append(kt); add(kick_s, kt, 0.9)
    for k in (1, 3): add(crush(clap_s, 6, 3), t0 + k * BEAT, 0.55)
    for s in range(16):
        if (s * 7 + b) % 5 == 0:
            for r in range(3): add(crush(hat(0.015), 4, 3), t0 + s * BEAT / 4 + r * BEAT / 12, 0.07, pan=0.4)
        else: add(hat(0.025), t0 + s * BEAT / 4, 0.05, pan=-0.3)
    add(crush(sub(root, BAR * 0.9), 6, 2), t0, 0.35)
    for s in range(8): add(crush(pluck(ch[s % 3] + 24, 0.1, 5000), 5, 4), t0 + s * BEAT / 2 + (BEAT / 4 if s % 3 == 2 else 0), 0.1, pan=0.4 * np.sin(s))


def bar_hard(b):
    t0 = b * BAR; root, ch = PROG[b % 4]
    for pos in (0.0, 1.5, 2.75):
        kt = t0 + pos * BEAT; kick_times.append(kt); add(kick_s, kt, 0.85)
        add(b808(root - 12 + 12, 0.8 if pos == 0 else 0.5, slide=-5 if pos == 2.75 else 0), kt, 0.75)
    add(clap_s, t0 + 2 * BEAT, 0.65); add(snare_hit(0.2), t0 + 2 * BEAT, 0.45)
    for s in range(16):
        if s in (6, 7, 14, 15):
            for r in range(3): add(hat(0.015), t0 + s * BEAT / 4 + r * BEAT / 12, 0.07, pan=0.3)
        else: add(hat(0.03), t0 + s * BEAT / 4, 0.09 if s % 2 == 0 else 0.05, pan=0.3)
    for k, n in enumerate([ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12]): add(bell(n, 0.4), t0 + k * BEAT + BEAT / 2, 0.06, pan=-0.3)


FN = {'pop': bar_pop, 'funk': bar_funk, 'hard': bar_hard}[STYLE]
for b in range(1, 7):
    FN(b)

# repo punctuation every 1.5s
for i, ts in enumerate(SLOTS):
    add(whoosh(0.3), ts - 0.22, 0.15)
    add(impact(0.5), ts, 0.22)
    if STYLE == 'pop': add(bell(84 + (i % 5) * 2, 0.4), ts, 0.14); add(blip(96, 0.05), ts, 0.1)
    elif STYLE == 'funk':
        add(thock_ := blip(100, 0.03), ts, 0.2)
        for r in range(0): add(hp(rng.standard_normal(int(0.01 * SR)), 2500) * 0.6, ts + r * 0.035, 0.18)
    else: add(b808(33, 0.6, slide=7), ts, 0.4)

# recap 11.5 - 13
add(riser(1.5, 500, 12000), T_RECAP, 0.35)
add(impact(1.2), T_RECAP, 0.5)
for i in range(10): add(blip(81 + (i % 5) * 2, 0.06), T_RECAP + 0.1 + i * 0.06, 0.08)
if STYLE == 'funk':
    for i, n in enumerate([88, 93]): add(bell(n, 0.8), T_OUT + i * 0.09, 0.25)  # ka-ching
ot = T_OUT
L[int(ot * SR):] *= 0.0; R[int(ot * SR):] *= 0.0
add(impact(2.0), ot, 0.85)
add(kick_s, ot, 1.0); kick_times.append(ot)
add(supersaw([57, 60, 64, 69], 1.9, cutoff=2600, release=1.4), ot, 0.5)
add(sub(33, 1.6), ot, 0.55)
for i, n in enumerate([88, 84, 81, 76, 72]):
    add(bell(n, 0.6), ot + BEAT + i * BEAT / 4, 0.08 * (1 - i / 7), pan=0.5 * (-1) ** i)

# ---- sidechain ----
duck = np.ones(N)
for kt in kick_times:
    i0 = int(kt * SR)
    env = 1 - 0.7 * np.exp(-tvec(BEAT) * 8)
    seg = duck[i0 : i0 + len(env)]
    duck[i0 : i0 + len(env)] = np.minimum(seg, env[: len(seg)])


def reverb(x, delays, fb=0.78, mix=0.22):
    out = np.zeros_like(x)
    for d in delays:
        D = int(d * SR)
        y = np.copy(x)
        for i in range(D, len(y), D):
            y[i : i + D] += y[i - D : i][: len(y[i : i + D])] * fb
        out += y
    return onepole_lp(out / len(delays), 5500) * mix


Ld, Rd = L * duck, R * duck
Lw = Ld + reverb(Ld, (0.0297, 0.0371, 0.0411, 0.0437))
Rw = Rd + reverb(Rd, (0.0313, 0.0353, 0.0423, 0.0459))

fade = np.clip((DUR - np.arange(N) / SR) / 0.4, 0, 1)
fade_in = np.clip(np.arange(N) / SR / 0.02, 0, 1)
mx = np.stack([Lw, Rw], 1) * (fade * fade_in)[:, None]
mx /= np.max(np.abs(mx)) + 1e-9
mx = np.tanh(mx * 1.7) / np.tanh(1.7) * 0.92

out = sys.argv[2]
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mx * 32767).astype("<i2").tobytes())
print("wrote", out)
