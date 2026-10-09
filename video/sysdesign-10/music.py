"""Original 15s breakbeat / electro track, 128 BPM, D minor. Fully synthesized (no samples).

Timeline (1 bar = 1.875s, 8 bars = 15s):
  bar 0      intro: telemetry beeps as the architecture diagram builds, packet zips, riser, snare build
  bar 1      DROP: impact, broken-beat drums, sub bass, title stabs
  bars 2-6   10 repos (one every 2 beats): FM bell arp + a "packet" zip on every camera move
  bar 7      outro: final chord, half-time kick, downlifter, reverb tail
"""
import sys
import wave

import numpy as np
from scipy.signal import lfilter

SR = 44100
BPM = 128
BEAT = 60 / BPM
BAR = BEAT * 4
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(1010)

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


def lp(x, cutoff):
    """one-pole lowpass; cutoff scalar (fast) or per-sample array"""
    if np.isscalar(cutoff):
        a = 1 - np.exp(-2 * np.pi * cutoff / SR)
        return lfilter([a], [1, a - 1], x)
    a = 1 - np.exp(-2 * np.pi * np.asarray(cutoff) / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def lp2(x, cutoff):
    return lp(lp(x, cutoff), cutoff)


def hp(x, cutoff):
    return x - lp(x, cutoff)


def saw(f, t, phase=0.0):
    ph = np.cumsum(np.broadcast_to(f, t.shape)) / SR + phase
    return 2 * (ph % 1.0) - 1


def sq(f, t, phase=0.0, pw=0.5):
    ph = np.cumsum(np.broadcast_to(f, t.shape)) / SR + phase
    return np.where(ph % 1.0 < pw, 1.0, -1.0)


# ---------- drums ----------
def kick(d=0.42):
    t = tvec(d)
    f = 48 + 140 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    click = hp(rng.standard_normal(len(t)), 2000) * np.exp(-t * 500) * 0.5
    return np.tanh((body + click) * 2.2)


def clap(d=0.32):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    env = np.exp(-t * 18)
    for k in (0.0, 0.009, 0.019, 0.028):
        env += (t >= k) * np.exp(-np.maximum(t - k, 0) * 160) * 0.9
    return hp(lp(n, 6000), 1100) * env * 0.85


def hat(d=0.05, open_=False):
    d = 0.24 if open_ else d
    t = tvec(d)
    metal = sum(sq(f, t) for f in (3140, 4270, 5310, 6880, 8190)) / 5
    sig = hp(metal * 0.6 + rng.standard_normal(len(t)) * 0.5, 7500)
    return sig * np.exp(-t * (13 if open_ else 80))


def rim(d=0.08):
    t = tvec(d)
    return (np.sin(2 * np.pi * 1700 * t) * 0.6 + hp(rng.standard_normal(len(t)), 3000) * 0.4) * np.exp(-t * 60)


def snare(d=0.14):
    t = tvec(d)
    tone = np.sin(2 * np.pi * (180 + 60 * np.exp(-t * 40)) * t) * 0.6
    return (hp(rng.standard_normal(len(t)), 1800) * 0.8 + tone) * np.exp(-t * 26)


def key_click():
    t = tvec(0.03)
    return hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 300) + np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 200) * 0.3


# ---------- fx ----------
def riser(d, f0=150, f1=9000):
    t = tvec(d)
    x = t / d
    cut = f0 * (f1 / f0) ** x
    noise = lp(rng.standard_normal(len(t)), cut) * x ** 2
    tone = lp(saw(80 * 2 ** (4 * x), t), 4000) * 0.18 * x ** 3
    return noise + tone


def impact(d=2.4):
    t = tvec(d)
    f = 28 + 110 * np.exp(-t * 7)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.0)
    crash = hp(rng.standard_normal(len(t)), 3500) * np.exp(-t * 2.6) * 0.32
    return np.tanh(boom * 1.7) + crash


def whoosh(d=0.5):
    t = tvec(d)
    x = t / d
    return lp(rng.standard_normal(len(t)), 300 + 8000 * x) * np.sin(np.pi * x) ** 2


def downlifter(d=1.8):
    t = tvec(d)
    return lp(rng.standard_normal(len(t)), 9000 * np.exp(-t * 3) + 150) * np.exp(-t * 1.6)


def blip(note, d=0.16):
    """'commit' blip: FM bell with a fast pitch drop"""
    t = tvec(d)
    f = midi(note) * (1 + 0.5 * np.exp(-t * 60))
    mod = np.sin(2 * np.pi * np.cumsum(f * 2.0) / SR) * 2.2 * np.exp(-t * 25)
    car = np.sin(2 * np.pi * np.cumsum(f) / SR + mod)
    return car * np.exp(-t * 22)


def glitch(d=0.06, f=900):
    t = tvec(d)
    return sq(f * (1 + 3 * t / d), t, pw=0.3) * np.exp(-t * 30) * 0.5


# ---------- tonal ----------
def supersaw(notes, d, cutoff=2400, voices=7, spread=0.25, attack=0.01, release=0.15):
    t = tvec(d)
    sig = np.zeros(len(t))
    for n in notes:
        for v in range(voices):
            cents = (v - (voices - 1) / 2) / ((voices - 1) / 2) * spread * 100
            sig += saw(midi(n) * 2 ** (cents / 1200), t, phase=rng.random())
    sig /= voices * len(notes)
    env = np.minimum(t / attack, 1) * np.clip((d - t) / release, 0, 1)
    return lp2(sig, cutoff) * env


def pluck(note, d=0.2, bright=6000):
    t = tvec(d)
    f = midi(note)
    sig = sq(f, t, pw=0.25) * 0.5 + saw(f * 1.003, t) * 0.5
    return lp(sig, 250 + bright * np.exp(-t * 20)) * np.exp(-t * 11)


def reese(note, d, bright=600):
    t = tvec(d)
    f = midi(note)
    sig = saw(f * 0.995, t) + saw(f * 1.005, t, 0.3) + np.sin(2 * np.pi * f / 2 * t) * 1.2
    sig = lp2(sig, bright)
    env = np.minimum(t / 0.004, 1) * np.clip((d - t) / 0.025, 0, 1)
    return np.tanh(sig * 1.4 * env)



def sub(note, d):
    t = tvec(d)
    f = midi(note)
    sig = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    env = np.minimum(t / 0.006, 1) * np.clip((d - t) / 0.03, 0, 1)
    return np.tanh(sig * 1.5 * env)


def bell(note, d=0.35, idx=3.0):
    t = tvec(d)
    f = midi(note)
    mod = np.sin(2 * np.pi * f * 3.5 * t) * idx * np.exp(-t * 9)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 7)


def zip_(d=0.22, up=True):
    """data-packet zip: fast sine chirp with a tiny noise tail"""
    t = tvec(d)
    x = t / d
    f = 300 * 2 ** ((5 * x) if up else (5 * (1 - x)))
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * x) ** 1.5
    return sig + hp(rng.standard_normal(len(t)), 5000) * 0.12 * np.sin(np.pi * x)


def beep(note, d=0.07):
    t = tvec(d)
    return sq(midi(note), t, pw=0.5) * np.exp(-t * 35) * 0.5


# D minor: Dm, Bb, F, C
DM = (38, [57, 62, 65, 69])
BB = (34, [58, 62, 65, 70])
FF = (41, [57, 60, 65, 69])
CC = (36, [55, 60, 64, 67])
prog = [DM, DM, BB, FF, CC, DM, BB, DM]
kick_s, clap_s = kick(), clap()
kick_times = []

# ---- intro (bar 0) ----
for s in range(14):  # telemetry beeps as nodes pop in
    add(beep([74, 81, 77, 86][s % 4], 0.06), 0.05 + s * BEAT / 4, 0.16, pan=0.6 * np.sin(s * 1.3))
add(supersaw(DM[1], BAR + 0.1, cutoff=800, attack=0.9, release=0.2), 0, 0.38)
add(sub(26, BAR), 0, 0.25)
add(riser(BAR), 0, 0.45)
for k in range(4):
    add(zip_(0.25), BAR * 0.32 + k * BEAT * 0.75, 0.13, pan=-0.5 + k * 0.33)
for i in range(8):
    add(snare(), BAR - BEAT * 2 + i * BEAT / 4, 0.1 + 0.05 * i)
add(glitch(0.12, 500), BAR - 0.13, 0.25)

# ---- drop + title (bar 1) ----
add(impact(), BAR, 0.95)
for k in range(4):
    add(supersaw([n + 12 for n in DM[1]], BEAT * 0.5, cutoff=1600 + 1000 * k, release=0.1), BAR + k * BEAT, 0.38)
    add(bell(DM[1][k] + 24, 0.4), BAR + k * BEAT, 0.12, pan=0.4 * (-1) ** k)

# ---- broken-beat groove (bars 1-6) ----
# kick on 1, the "and" of 2, and 3.5 / snare on 2 and 4
KPAT = [0, 1.5, 2.5]
for b in range(1, 7):
    bt = b * BAR
    root, ch = prog[b]
    for kb in KPAT:
        kick_times.append(bt + kb * BEAT)
        add(kick_s, bt + kb * BEAT, 0.95)
    for sb in (1, 3):
        add(clap_s, bt + sb * BEAT, 0.42, pan=0.05)
        add(snare(), bt + sb * BEAT, 0.3)
    add(snare(0.08), bt + 3.75 * BEAT, 0.12, pan=0.3)
    for s in range(16):
        add(hat(0.03), bt + s * BEAT / 4, (0.1 if s % 4 == 2 else 0.05), pan=-0.3)
    add(hat(open_=True), bt + 1.5 * BEAT, 0.07, pan=0.3)
    add(hat(open_=True), bt + 3.5 * BEAT, 0.07, pan=0.3)
    # sub bass following the kicks + reese stab
    for kb, dur in zip(KPAT, (1.4, 0.9, 1.4)):
        add(sub(root, BEAT * dur), bt + kb * BEAT, 0.55)
    add(reese(root + 12, BEAT * 0.4, 900), bt + 3.5 * BEAT, 0.22)

# FM bell arp + pad through the repo section
arp_pat = [0, 1, 2, 3, 2, 1, 3, 0]
for b in range(2, 7):
    _, ch = prog[b]
    bt = b * BAR
    for s in range(16):
        n = ch[arp_pat[s % 8]] + 12 + (12 if s % 8 in (3, 6) else 0)
        add(bell(n, 0.25, 2.0), bt + s * BEAT / 4, 0.09, pan=0.5 * np.sin(s * 0.9))
    add(supersaw(ch, BAR, cutoff=1200, attack=0.3, release=0.3), bt, 0.16)

# packet zip on every camera move between repos, alternating direction
for i in range(10):
    t0 = 2 * BAR + i * 2 * BEAT
    if i:
        add(zip_(0.3, up=i % 2 == 0), t0 - 0.24, 0.2, pan=0.5 * (-1) ** i)
    add(beep(86 + (i % 3) * 2, 0.08), t0 + 0.05, 0.12, pan=-0.4 * (-1) ** i)
    add(blip(74 + [0, 3, 5, 7, 10, 12, 15, 17, 19, 22][i], 0.2), t0 + BEAT, 0.12, pan=0.2)

for i in range(6):
    add(glitch(0.04, 600 + 220 * i), 5 * BAR - BEAT + i * BEAT / 6, 0.14)
for i in range(8):
    add(snare(), 7 * BAR - BEAT * 2 + i * BEAT / 4, 0.06 + 0.04 * i)

# ---- outro (bar 7) ----
ot = 7 * BAR
add(impact(2.0), ot, 0.8)
add(kick_s, ot, 1.0)
add(kick_s, ot + BEAT * 2, 0.8)
kick_times += [ot, ot + BEAT * 2]
add(supersaw([n + 12 for n in DM[1]] + [38 + 24], BAR, cutoff=3000, attack=0.005, release=1.3), ot, 0.55)
add(sub(26, BAR * 0.9), ot, 0.55)
add(downlifter(BAR), ot, 0.22)
for i, n in enumerate([86, 81, 77, 74, 69, 65]):
    add(bell(n, 0.5), ot + BEAT * 2 + i * BEAT / 4, 0.14 * (1 - i / 8), pan=0.5 * (-1) ** i)

# ---- sidechain ----
duck = np.ones(N)
for kt in kick_times:
    i0 = int(kt * SR)
    env = 1 - 0.7 * np.exp(-tvec(BEAT) * 9)
    seg = duck[i0 : i0 + len(env)]
    duck[i0 : i0 + len(env)] = np.minimum(seg, env[: len(seg)])


def reverb(x, delays, fb=0.76, mix=0.2):
    out = np.zeros_like(x)
    for d in delays:
        D = int(d * SR)
        out += lfilter([1.0], np.r_[1.0, np.zeros(D - 1), -fb], x)
    return lp(out / len(delays), 5000) * mix


Ld, Rd = L * duck, R * duck
Lw = Ld + reverb(Ld, (0.0297, 0.0371, 0.0411, 0.0437))
Rw = Rd + reverb(Rd, (0.0313, 0.0353, 0.0423, 0.0459))

fade = np.clip((DUR - np.arange(N) / SR) / 0.35, 0, 1)
fade_in = np.clip(np.arange(N) / SR / 0.02, 0, 1)
mx = np.stack([Lw, Rw], 1) * (fade * fade_in)[:, None]
mx /= np.max(np.abs(mx)) + 1e-9
mx = np.tanh(mx * 1.7) / np.tanh(1.7) * 0.93

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mx * 32767).astype("<i2").tobytes())
print("wrote", out)
