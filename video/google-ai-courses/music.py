"""Original 15s future-bass track, 120 BPM, F minor. Fully synthesized (no samples).

Timeline (1 bar = 2.0s):
  0.0 - 2.0   intro: filtered chord pad, 4 "dot" blips, riser, snare roll
  2.0         DROP: impact, kick/clap groove, wobbling supersaw stabs, sub
  4.5 - 6.0   glitch stutter + tape-stop into the counter, re-drop at 6.0
  6.0 - 12.0  course showcase: full groove + 16th arp, whoosh per group
  12.0 - 13.0 wall: hat roll + riser
  13.0        outro: final chord hit, reverb tail
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


# progression in F minor: Fm - Db - Ab - Eb   (bass root, chord voicing)
FM = (41, [56, 60, 63, 65, 68])
DB = (37, [56, 61, 65, 68, 72])
AB = (44, [56, 60, 63, 68, 72])
EB = (39, [55, 58, 63, 67, 70])
prog = [FM, FM, DB, FM, DB, AB, EB, FM]

kick_s, clap_s = kick(), clap()
kick_times = []

# ---- intro (bar 0) ----
add(supersaw(FM[1], BAR + 0.1, cutoff=700, attack=1.0, release=0.2, voices=5), 0, 0.5)
add(riser(BAR), 0, 0.45)
for i, n in enumerate([84, 79, 80, 75]):  # four "dot" blips, matched to visuals
    add(blip(n), 0.12 + i * 0.25, 0.22, pan=-0.6 + i * 0.4)
for i in range(4):
    add(hat(), BEAT * 2 + i * BEAT / 2, 0.06 + 0.03 * i, pan=0.3)
for i in range(8):
    add(snare_hit(), BAR - BEAT * 2 + i * BEAT / 4, 0.1 + 0.05 * i)
for i in range(4):
    add(snare_hit(), BAR - BEAT / 2 + i * BEAT / 8, 0.45)


def groove_bar(b, stutter=False):
    bt = b * BAR
    root, ch = prog[b]
    for k in range(4):
        kt = bt + k * BEAT
        if stutter and k >= 1:
            continue
        kick_times.append(kt)
        add(kick_s, kt, 0.95)
        add(hat(), kt + BEAT / 2, 0.2, pan=0.25)
        add(hat(open_=True), kt + BEAT / 2, 0.06, pan=-0.25)
        if k in (1, 3):
            add(clap_s, kt, 0.5, pan=0.05)
        # wobbling chord on every beat + sub
        add(supersaw([n + 12 for n in ch], BEAT * 0.95, cutoff=3400 if b >= 3 else 2600, wob=1 / (BEAT / 3)),
            kt, 0.3, pan=0.15 if k % 2 else -0.15)
        add(sub(root, BEAT * 0.9), kt, 0.6)
    for s in range(16):
        if stutter and s >= 4:
            break
        add(hat(0.025), bt + s * BEAT / 4, 0.04 + 0.025 * (s % 2), pan=-0.35)


# ---- drop (bar 1) and bar 2 (with stutter from 4.5s) ----
add(impact(), BAR, 0.9)
groove_bar(1)
groove_bar(2, stutter=True)

# glitch stutter 4.5 - 5.5: chopped chord, accelerating
st = 2 * BAR + BEAT
chop = supersaw([n + 12 for n in DB[1]], 0.07, cutoff=4000, release=0.02)
t = st
step = BEAT / 4
while t < st + BEAT * 2:
    add(chop, t, 0.35, pan=0.4 * np.sin(t * 9))
    add(blip(84 + int((t - st) * 6)), t, 0.08)
    t += step
    step = max(BEAT / 16, step * 0.86)
# tape-stop downsweep on last beat before re-drop
ts = tvec(BEAT)
f = midi(53) * (1 - ts / BEAT) ** 1.5 + 20
add(np.tanh(saw(f, ts) * 0.7) * (1 - ts / BEAT), 3 * BAR - BEAT, 0.25)
add(riser(BEAT * 2, 800, 12000), 3 * BAR - BEAT * 2, 0.3)

# ---- showcase bars 3-5 ----
add(impact(1.8), 3 * BAR, 0.7)
arp = [0, 2, 1, 3, 4, 2, 3, 1]
for b in range(3, 6):
    groove_bar(b)
    _, ch = prog[b]
    for s in range(16):
        n = ch[arp[s % 8]] + 12 + (12 if s % 8 == 4 else 0)
        add(pluck(n), b * BAR + s * BEAT / 4, 0.13, pan=0.5 * np.sin(s * 0.8))
    add(whoosh(0.5), b * BAR - 0.35, 0.22)

# ---- wall (bar 6, first half) : roll + riser ----
groove_bar(6, stutter=True)
for i in range(16):
    add(snare_hit(), 6 * BAR + BEAT + i * BEAT / 8 * (1 - i / 40), 0.12 + 0.03 * i)
for i in range(12):
    add(hat(0.02), 6 * BAR + i * BEAT / 6, 0.1, pan=0.4 * (-1) ** i)
add(riser(BEAT * 2, 400, 11000), 6 * BAR, 0.4)
_, ch6 = prog[6]
for s in range(8):
    add(pluck(ch6[arp[s]] + 24, 0.15), 6 * BAR + s * BEAT / 4, 0.12, pan=0.5 * np.sin(s))

# ---- outro hit at 13.0 ----
ot = 6.5 * BAR
add(impact(2.0), ot, 0.85)
add(kick_s, ot, 1.0)
kick_times.append(ot)
add(supersaw([n + 12 for n in FM[1]] + [65 + 12], 1.9, cutoff=3200, release=1.4), ot, 0.6)
add(sub(29, 1.6), ot, 0.55)
for i, n in enumerate([84, 80, 77, 72, 68, 65]):
    add(pluck(n, 0.5, 4000), ot + BEAT + i * BEAT / 4, 0.13 * (1 - i / 8), pan=0.5 * (-1) ** i)
for i, n in enumerate([84, 79, 80, 75]):
    add(blip(n, 0.2), ot + BEAT * 3 + i * 0.12, 0.12, pan=-0.6 + i * 0.4)

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
