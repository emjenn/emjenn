"""Original 15s synthwave/house track, 128 BPM, A minor. Fully synthesized (no samples).

Timeline (1 bar = 1.875s, 8 bars = 15s):
  bar 0      intro: pad + riser + ticking hats
  bar 1      DROP: impact, four-on-the-floor, bass, clap
  bar 2      groove + snare fill into bar 3
  bars 3-6   course showcase: full groove + 16th arp
  bar 7      outro: final chord hit, half-time kick, reverb tail
"""
import numpy as np
import wave
import sys

SR = 44100
BPM = 128
BEAT = 60 / BPM
BAR = BEAT * 4
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(7)

L = np.zeros(N)
R = np.zeros(N)


def add(sig, t0, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if i0 >= N:
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
    """cutoff may be scalar or per-sample array"""
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
def kick(d=0.45):
    t = tvec(d)
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 7.5)
    click = rng.standard_normal(len(t)) * np.exp(-t * 400) * 0.35
    return np.tanh((body + click) * 1.8)


def clap(d=0.3):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    env = np.exp(-t * 22)
    for k in (0.0, 0.011, 0.022):
        env += (t >= k) * np.exp(-np.maximum(t - k, 0) * 140) * 0.8
    sig = hp(onepole_lp(n, 4500), 900) * env
    return sig * 0.9


def hat(d=0.06, open_=False):
    d = 0.22 if open_ else d
    t = tvec(d)
    n = rng.standard_normal(len(t))
    sig = hp(n, 7000) * np.exp(-t * (14 if open_ else 70))
    return sig


def snare_roll_hit(d=0.12):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    tone = np.sin(2 * np.pi * 190 * t) * 0.5
    return (hp(n, 1500) * 0.8 + tone) * np.exp(-t * 30)


# ---------- fx ----------
def riser(d, f0=200, f1=6000):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    cut = f0 * (f1 / f0) ** (t / d)
    sig = onepole_lp(n, cut) * (t / d) ** 2
    sweep = saw(110 * 2 ** (3 * t / d), t) * 0.15 * (t / d) ** 3
    return sig + onepole_lp(sweep, 3000)


def impact(d=2.5):
    t = tvec(d)
    f = 30 + 90 * np.exp(-t * 6)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    crash = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 2.8) * 0.35
    return np.tanh(boom * 1.5) + crash


def whoosh(d=0.6, rev=False):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    x = t / d
    env = np.sin(np.pi * x) ** 2
    cut = 400 + 7000 * (x if not rev else 1 - x)
    return onepole_lp(n, cut) * env


def downlifter(d=1.6):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    cut = 8000 * np.exp(-t * 3) + 200
    return onepole_lp(n, cut) * np.exp(-t * 1.8)


# ---------- tonal ----------
def supersaw(notes, d, cutoff=2400, voices=5, detune=0.12, attack=0.01, release=0.15):
    t = tvec(d)
    sig = np.zeros(len(t))
    for n in notes:
        for v in range(voices):
            cents = (v - (voices - 1) / 2) * detune * 2 / (voices - 1) * 100 / 10
            f = midi(n) * 2 ** (cents / 1200)
            sig += saw(f, t, phase=rng.random())
    sig /= voices * len(notes)
    env = np.minimum(t / attack, 1) * np.clip((d - t) / release, 0, 1)
    return onepole_lp(sig, cutoff) * env


def pluck(note, d=0.22, bright=5000):
    t = tvec(d)
    sig = saw(midi(note), t) * 0.6 + np.sign(np.sin(2 * np.pi * midi(note) * 1.005 * t)) * 0.3
    cut = 300 + bright * np.exp(-t * 18)
    return onepole_lp(sig, cut) * np.exp(-t * 9)


def bass(note, d):
    t = tvec(d)
    f = midi(note)
    sig = saw(f, t) * 0.7 + np.sin(2 * np.pi * f / 2 * t) * 0.6
    sig = onepole_lp(sig, 380 + 900 * np.exp(-t * 10))
    env = np.minimum(t / 0.005, 1) * np.clip((d - t) / 0.03, 0, 1)
    return np.tanh(sig * 1.6 * env)


# chord progression per bar: (bass root, chord notes)
AM = (45, [57, 60, 64, 71])  # Am(add9-ish)
F = (41, [57, 60, 65, 69])
C = (48, [55, 60, 64, 67])
G = (43, [55, 59, 62, 67])
prog = [AM, AM, F, C, G, AM, F, AM]

kick_s, clap_s = kick(), clap()

# ---- intro (bar 0) ----
add(supersaw(prog[0][1], BAR + 0.2, cutoff=900, attack=0.8, release=0.3), 0, 0.55)
add(riser(BAR), 0, 0.5)
for i in range(8):
    add(hat(), i * BEAT / 2 + BEAT / 2 * (i % 2), 0.08 + 0.02 * i, pan=0.3)
# snare build in last beat of intro
for i in range(8):
    add(snare_roll_hit(), BAR - BEAT * 2 + i * BEAT / 4, 0.12 + 0.05 * i, pan=-0.1)

# ---- drop at bar 1 ----
add(impact(), BAR, 0.9)
kick_times = []
for b in range(1, 7):
    bt = b * BAR
    for k in range(4):
        kt = bt + k * BEAT
        kick_times.append(kt)
        add(kick_s, kt, 0.95)
        add(hat(), kt + BEAT / 2, 0.22, pan=0.25)
        add(hat(open_=True), kt + BEAT / 2, 0.07, pan=-0.25)
        if k in (1, 3):
            add(clap_s, kt, 0.45, pan=0.05)
    for s in range(16):  # 16th shaker
        add(hat(0.03), bt + s * BEAT / 4, 0.05 + 0.03 * (s % 2), pan=-0.35)

# chords (offbeat stabs) + bass, sidechained later
pad = np.zeros(N)
padL = np.zeros(N)
for b in range(1, 7):
    root, ch = prog[b]
    bt = b * BAR
    for k in range(4):
        st = supersaw([n + 12 for n in ch], BEAT * 0.45, cutoff=3200 if b >= 3 else 2200, release=0.08)
        add(st, bt + k * BEAT + BEAT / 2, 0.32, pan=-0.2 if k % 2 else 0.2)
        # rolling bass on offbeat 8ths
        add(bass(root, BEAT / 2 * 0.9), bt + k * BEAT + BEAT / 2, 0.55)
        add(bass(root + 12, BEAT / 4 * 0.8), bt + k * BEAT + BEAT * 0.75, 0.28)

# arp for course showcase bars 3-6
arp_pat = [0, 2, 1, 3, 2, 1, 3, 2]
for b in range(3, 7):
    _, ch = prog[b]
    bt = b * BAR
    for s in range(16):
        n = ch[arp_pat[s % 8]] + 12 + (12 if s % 8 == 7 else 0)
        add(pluck(n), bt + s * BEAT / 4, 0.16, pan=0.45 * np.sin(s * 0.7))

# snare fill end of bar 2 -> into bar 3, plus whooshes at group changes
for i in range(8):
    add(snare_roll_hit(), 3 * BAR - BEAT * 2 + i * BEAT / 4, 0.08 + 0.04 * i)
for b in (3, 4, 5, 6):
    add(whoosh(0.5), b * BAR - 0.4, 0.25)
add(whoosh(0.7, rev=True), BAR * 0.25, 0.15)

# ---- outro (bar 7) ----
ot = 7 * BAR
add(impact(2.0), ot, 0.75)
add(kick_s, ot, 1.0)
add(kick_s, ot + BEAT * 2, 0.8)
add(supersaw([n + 12 for n in prog[7][1]] + [45 + 24], BAR, cutoff=3000, attack=0.005, release=1.2), ot, 0.6)
add(bass(33, BAR * 0.9), ot, 0.5)
add(downlifter(BAR), ot, 0.25)
for i, n in enumerate([76, 72, 69, 64, 60, 57]):
    add(pluck(n, 0.5, 3500), ot + BEAT * 2 + i * BEAT / 4, 0.14 * (1 - i / 8), pan=0.5 * (-1) ** i)

# ---- sidechain ducking from kicks ----
duck = np.ones(N)
for kt in kick_times + [ot]:
    i0 = int(kt * SR)
    t = tvec(BEAT)
    env = 1 - 0.65 * np.exp(-t * 9)
    seg = duck[i0 : i0 + len(env)]
    duck[i0 : i0 + len(env)] = np.minimum(seg, env[: len(seg)])

# simple stereo reverb (feedback delays)
def reverb(x, delays=(0.0297, 0.0371, 0.0411, 0.0437), fb=0.78, mix=0.22):
    out = np.zeros_like(x)
    for d in delays:
        D = int(d * SR)
        y = np.copy(x)
        for i in range(D, len(y), D):
            y[i : i + D] += y[i - D : i][: len(y[i : i + D])] * fb
        out += y
    return onepole_lp(out / len(delays), 5000) * mix

Ld, Rd = L * duck, R * duck
Lw = Ld + reverb(Ld, (0.0297, 0.0371, 0.0411, 0.0437))
Rw = Rd + reverb(Rd, (0.0313, 0.0353, 0.0423, 0.0459))

# master: fade out tail, soft limit
fade = np.clip((DUR - np.arange(N) / SR) / 0.35, 0, 1)
fade_in = np.clip(np.arange(N) / SR / 0.02, 0, 1)
mx = np.stack([Lw, Rw], 1) * (fade * fade_in)[:, None]
mx /= np.max(np.abs(mx)) + 1e-9
mx = np.tanh(mx * 1.6) / np.tanh(1.6) * 0.92

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mx * 32767).astype("<i2").tobytes())
print("wrote", out)
