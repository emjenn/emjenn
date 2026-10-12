"""Original 15s electro-house track, 120 BPM, D minor. Fully synthesized.
  0 intro (14->spark ticks), 2.0 drop, 3.5-12.0 one lead note per tip (17), 12 wall, 13 outro hit.
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


# progression in D minor: Dm - Bb - F - C   (bass root, chord voicing)
DM = (38, [57, 60, 62, 65, 69])
BB = (34, [58, 62, 65, 69, 70])
FF = (41, [57, 60, 65, 69, 72])
CC = (36, [55, 60, 64, 67, 72])
prog = [DM, DM, BB, FF, CC, DM, BB, DM]

kick_s, clap_s = kick(), clap()
kick_times = []

# ---- intro (bar 0): 14 ticks converge, riser, roll ----
add(supersaw(DM[1], BAR + 0.1, cutoff=650, attack=1.0, release=0.2, voices=5), 0, 0.5)
add(riser(BAR), 0, 0.45)
for i in range(14):
    add(blip(74 + (i * 5) % 14, 0.09), 0.1 + i * 0.075, 0.12, pan=-0.7 + i * 0.1)
for i in range(8):
    add(snare_hit(), BAR - BEAT * 2 + i * BEAT / 4, 0.1 + 0.05 * i)
for i in range(4):
    add(snare_hit(), BAR - BEAT / 2 + i * BEAT / 8, 0.45)


def groove_bar(b, start_beat=0, end_beat=4, arp=False):
    bt = b * BAR
    root, ch = prog[b]
    for k in range(start_beat, end_beat):
        kt = bt + k * BEAT
        kick_times.append(kt)
        add(kick_s, kt, 0.95)
        add(hat(), kt + BEAT / 2, 0.2, pan=0.25)
        add(hat(open_=True), kt + BEAT / 2, 0.07, pan=-0.25)
        if k in (1, 3):
            add(clap_s, kt, 0.5, pan=0.05)
        add(supersaw([n + 12 for n in ch], BEAT * 0.42, cutoff=3000, release=0.06),
            kt + BEAT / 2, 0.3, pan=0.18 if k % 2 else -0.18)
        add(sub(root, BEAT * 0.45), kt + BEAT / 2, 0.55)
        add(sub(root + 12, BEAT * 0.2), kt + BEAT * 0.75, 0.25)
        for s in range(4):
            add(hat(0.025), kt + s * BEAT / 4, 0.04 + 0.025 * (s % 2), pan=-0.35)


# ---- drop at 2.0, tips 3.5 - 12.0 (one lead note per tip, 17 total) ----
add(impact(), BAR, 0.9)
groove_bar(1)
for i in range(4):
    add(snare_hit(), 3.25 + i * BEAT / 8, 0.25 + 0.08 * i)
add(impact(1.2), 3.5, 0.45)
mel = [74, 77, 81, 79, 77, 74, 72, 74, 77, 81, 84, 81, 79, 77, 81, 84, 86]
for i in range(17):
    t0 = 3.5 + i * BEAT
    add(pluck(mel[i] + 12, 0.32, 7000), t0, 0.2, pan=0.3 * (-1) ** i)
    add(pluck(mel[i], 0.4, 3000), t0, 0.12)
    add(whoosh(0.18), t0 - 0.09, 0.08, pan=0.4 * (-1) ** i)
for b in range(2, 6):
    groove_bar(b)
for i in range(8):
    add(snare_hit(), 11.5 + i * BEAT / 8, 0.15 + 0.06 * i)
add(riser(BEAT * 1.5, 500, 11000), 11.25, 0.35)

# ---- wall 12 - 13 ----
add(impact(1.2), 12.0, 0.6)
add(kick_s, 12.0, 0.95); kick_times.append(12.0)
add(kick_s, 12.5, 0.9); kick_times.append(12.5); add(clap_s, 12.5, 0.4)
for i in range(17):
    add(blip(86 - (i % 7) * 2, 0.06), 12.05 + i * 0.04, 0.08, pan=-0.7 + i * 0.08)
for i in range(8):
    add(snare_hit(), 12.75 + i * BEAT / 16, 0.2 + 0.05 * i)

# ---- outro hit at 13.0 ----
ot = 13.0
add(impact(2.0), ot, 0.85)
add(kick_s, ot, 1.0)
kick_times.append(ot)
add(supersaw([n + 12 for n in DM[1]] + [62 + 12], 1.9, cutoff=3200, release=1.4), ot, 0.6)
add(sub(26, 1.6), ot, 0.55)
for i, n in enumerate([86, 81, 77, 74, 69, 65]):
    add(pluck(n, 0.5, 4000), ot + BEAT + i * BEAT / 4, 0.13 * (1 - i / 8), pan=0.5 * (-1) ** i)

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

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mx * 32767).astype("<i2").tobytes())
print("wrote", out)
