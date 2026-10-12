"""Original 15s soundtracks for the GitHub top-5 videos, 120 BPM, A minor. Fully synthesized.
usage: python3 music.py techno|glitch|hard out.wav
  0 intro, 2.0 drop, repos at 4.0 + 1.5i (5), 11.5 recap, 13 outro hit.
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
SLOTS = [4.0 + 1.5 * i for i in range(5)]
T_RECAP, T_OUT = 11.5, 13.0
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
if STYLE == 'techno':
    for s in range(8): add(blip(69 + (s % 2) * 12, 0.08), s * BEAT / 2, 0.08 + s * 0.01)
    add(supersaw(AM, 2.0, cutoff=500, attack=1.0, release=0.2), 0, 0.45)
elif STYLE == 'glitch':
    for s in range(24):
        add(crush(blip(76 + (s * 5) % 12, 0.05), 4, 4), 0.1 + s * 0.075, 0.1, pan=np.sin(s))
    add(crush(supersaw(EM, 2.0, cutoff=900, attack=0.8, release=0.2)), 0, 0.3)
else:
    add(supersaw([45, 52, 57, 60], 2.0, cutoff=600, attack=1.2, release=0.2), 0, 0.5)
    for i in range(6): add(hat(0.03), 1.25 + i * BEAT / 8, 0.08)
for i in range(8):
    add(snare_hit(), 2.0 - BEAT * 2 + i * BEAT / 4, 0.08 + 0.05 * i)
add(impact(), 2.0, 0.9)

# ---------------- groove 2-13 ----------------
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


FN = {'techno': bar_techno, 'glitch': bar_glitch, 'hard': bar_hard}[STYLE]
for b in range(1, 7):
    FN(b)

# repo punctuation every 1.5s
for i, ts in enumerate(SLOTS):
    add(whoosh(0.35), ts - 0.28, 0.22)
    add(impact(0.8), ts, 0.38)
    if STYLE == 'techno': add(stabm([69, 72, 76], 0.25, 4000), ts, 0.3)
    elif STYLE == 'glitch':
        for r in range(4): add(crush(stabm([64, 67, 71], 0.06, 4000), 4, 5), ts + r * 0.06, 0.25)
    else: add(b808(33, 0.8, slide=7), ts, 0.45)

# recap 11.5 - 13
add(riser(1.5, 500, 12000), T_RECAP, 0.35)
add(impact(1.2), T_RECAP, 0.5)
for i in range(5): add(blip(81 + i * 2, 0.08), T_RECAP + 0.1 + i * 0.07, 0.1)
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
