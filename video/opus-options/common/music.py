"""Original 15s soundtracks for the Opus cheatsheet options, 120 BPM, D minor. Fully synthesized.
usage: python3 music.py trap|synth|lofi out.wav
  0 intro, 2.0 drop, tips at 3.5 + 1.5i (6), 12.5 recap, 13 outro hit.
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
TIPS = [3.5 + 1.5 * i for i in range(6)]
T_FULL, T_OUT = 12.5, 13.0
kick_s, clap_s = kick(), clap()
kick_times = []


def keys(notes, d, bright=2200):
    t = tvec(d)
    sig = np.zeros(len(t))
    for n in notes:
        f = midi(n)
        sig += np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) * np.exp(-t * 6)
    env = np.minimum(t / 0.004, 1) * np.exp(-t * 2.2) * np.clip((d - t) / 0.05, 0, 1)
    return onepole_lp(sig / len(notes), bright) * env


def bell(note, d=0.6):
    t = tvec(d)
    f = midi(note)
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 8)) * np.exp(-t * 5)


def b808(note, d=0.7, slide=0):
    t = tvec(d)
    f = midi(note) * 2 ** (slide * np.clip(1 - t / 0.15, 0, 1) / 12) * (1 + 1.2 * np.exp(-t * 40))
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * 2.6 * np.exp(-t * 1.8)) * np.clip((d - t) / 0.04, 0, 1)


def thock(d=0.08):  # keyboard key
    t = tvec(d)
    return (np.sin(2 * np.pi * (600 + 400 * np.exp(-t * 80)) * t) * 0.5 + hp(rng.standard_normal(len(t)), 2500) * 0.4) * np.exp(-t * 90)


CH = [(38, [57, 60, 62, 65, 69]), (34, [57, 58, 62, 65, 69]), (41, [57, 60, 64, 65, 69]), (36, [55, 60, 64, 67, 72])]  # Dm Bb F C

# ---------------- intro 0-2 ----------------
add(riser(2.0), 0, 0.4)
if STYLE == 'trap':
    add(supersaw([50, 53, 57, 62], 2.0, cutoff=700, attack=1.0, release=0.2), 0, 0.45)
    for i in range(8): add(hat(0.03), 1.0 + i * BEAT / 4, 0.06 + 0.02 * i)
elif STYLE == 'synth':
    add(supersaw(CH[0][1], 2.0, cutoff=800, attack=1.2, release=0.2), 0, 0.5)
    for s in range(16): add(pluck(CH[0][1][s % 5] + 12, 0.15, 1200 + s * 250), s * BEAT / 4, 0.08 + s * 0.004)
else:
    add(keys(CH[0][1], 2.0, 1200), 0, 0.5)
    for i in range(24): add(thock(), 0.15 + i * 0.06 + 0.02 * np.sin(i * 7), 0.12)
for i in range(8):
    add(snare_hit(), 2.0 - BEAT * 2 + i * BEAT / 4, 0.08 + 0.05 * i)
add(impact(), 2.0, 0.85)

# ---------------- groove 2-13 ----------------
def bar_trap(b):
    t0 = b * BAR
    root = CH[b % 4][0]
    for pos in (0.0, 1.5, 2.75):
        kt = t0 + pos * BEAT; kick_times.append(kt); add(kick_s, kt, 0.85)
        add(b808(root, 0.8 if pos == 0 else 0.5, slide=5 if pos == 2.75 else 0), kt, 0.7)
    add(clap_s, t0 + 2 * BEAT, 0.6); add(snare_hit(0.2), t0 + 2 * BEAT, 0.4)
    for s in range(16):
        if s in (13, 14, 15):
            for r in range(2): add(hat(0.02), t0 + s * BEAT / 4 + r * BEAT / 8, 0.07, pan=0.3)
        else: add(hat(0.03), t0 + s * BEAT / 4, 0.09 if s % 2 == 0 else 0.05, pan=0.3)
    for k, n in enumerate([74, 77, 81, 77]):
        add(bell(n, 0.5), t0 + k * BEAT, 0.07, pan=-0.3)


def bar_synth(b):
    t0 = b * BAR
    root, ch = CH[b % 4]
    for k in range(4):
        kt = t0 + k * BEAT; kick_times.append(kt); add(kick_s, kt, 0.9)
        if k in (1, 3): add(clap_s, kt, 0.45)
        add(hat(), kt + BEAT / 2, 0.15, pan=0.3)
        for e in range(2): add(sub(root + 12 * e, BEAT / 2 * 0.85), kt + e * BEAT / 2, 0.42)
    arp = [0, 2, 4, 2, 1, 3, 4, 3]
    for s in range(16): add(pluck(ch[arp[s % 8]] + 12, 0.18, 6500), t0 + s * BEAT / 4, 0.12, pan=0.5 * np.sin(s * 0.9))
    add(supersaw([n + 12 for n in ch], BAR, cutoff=1800, attack=0.05, release=0.3, voices=5), t0, 0.15)


def bar_lofi(b):
    t0 = b * BAR
    root, ch = CH[b % 4]
    for pos in (0.0, 1.75, 2.5):
        kt = t0 + pos * BEAT; kick_times.append(kt); add(onepole_lp(kick_s, 2500), kt, 0.8)
    for k in (1, 3): add(onepole_lp(clap_s, 3000), t0 + k * BEAT, 0.45); add(snare_hit(0.15), t0 + k * BEAT, 0.25)
    for s in range(8):
        swing = 0.04 if s % 2 else 0
        add(onepole_lp(hat(0.04), 6000), t0 + s * BEAT / 2 + swing, 0.07, pan=0.25)
    add(keys([n for n in ch], BAR * 0.95, 1600), t0, 0.45)
    add(sub(root, BEAT * 1.8), t0, 0.4); add(sub(root, BEAT * 1.2), t0 + 2.5 * BEAT, 0.35)
    for i in range(10): add(thock(), t0 + 0.1 + i * 0.19 + 0.03 * np.sin(b * 3 + i), 0.05, pan=0.2 * np.sin(i))


FN = {'trap': bar_trap, 'synth': bar_synth, 'lofi': bar_lofi}[STYLE]
for b in range(1, 7):
    FN(b)

# tip punctuation
mel = [81, 84, 79, 77, 81, 86]
for i, ts in enumerate(TIPS):
    add(whoosh(0.4), ts - 0.3, 0.2)
    if STYLE == 'trap':
        add(impact(0.9), ts, 0.4); add(b808(38, 0.6, slide=7), ts, 0.4)
    elif STYLE == 'synth':
        add(impact(0.7), ts, 0.28); add(supersaw([mel[i], mel[i] + 7], 0.3, cutoff=5000, release=0.15), ts, 0.18)
    else:
        add(thock(0.12), ts, 0.4); add(bell(mel[i] - 12, 0.8), ts, 0.14)
    add(bell(mel[i]), ts, 0.13, pan=0.3 * (-1) ** i)

# recap + outro
add(riser(0.5, 800, 12000), 12.0, 0.3)
add(impact(1.2), T_FULL, 0.5)
ot = T_OUT
L[int(ot * SR):] *= 0.0; R[int(ot * SR):] *= 0.0
add(impact(2.0), ot, 0.75)
add(kick_s, ot, 1.0); kick_times.append(ot)
add(keys([n + 12 for n in CH[0][1]], 2.0, 3000), ot, 0.5)
add(supersaw([n + 12 for n in CH[0][1]], 1.9, cutoff=2400, release=1.4), ot, 0.3)
add(sub(26, 1.6), ot, 0.5)
for i, n in enumerate([93, 89, 86, 81, 77]):
    add(bell(n, 0.7), ot + BEAT + i * BEAT / 4, 0.08 * (1 - i / 7), pan=0.5 * (-1) ** i)

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
