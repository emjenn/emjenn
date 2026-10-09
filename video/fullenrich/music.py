"""Original 15s dark phonk / half-time trap track, 128 BPM (felt at 64), C# Phrygian.
Fully synthesized (no samples). Deliberately unlike the house tracks used in the other videos:
distorted 808 slides, phonk cowbell lead, half-time snare, triplet hat rolls, tape stop ending.

Timeline (1 bar = 1.875s, 8 bars = 15s):
  bar 0      intro: dark detuned choir pad, vinyl crackle, filtered cowbell teaser, reverse swell
  bar 1      DROP: 808 + kick pattern, half-time snare on beat 3, cowbell riff opens up
  bars 2-4   6 prompts: orchestral stab on every prompt cut (kick + snare positions)
  bars 5-6   3 proof stats: stabs on an 11/16 grid, beat chops + stutters
  bar 7      outro: final stab + long 808 slide, tape stop into the reverb tail

Drum grid (16th steps per bar) — mirrored in motion.html for the beat pulses:
  kick  0, 6, 10      snare 8
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




# ---------- phonk voices ----------
def cowbell(note, d=0.16):
    t = tvec(d)
    f = midi(note)
    sig = np.sign(np.sin(2 * np.pi * f * t)) + np.sign(np.sin(2 * np.pi * f * 1.483 * t)) * 0.8
    sig = onepole_lp(hp(sig, 700), 5200)
    return sig * np.exp(-t * 16) * 0.6


def b808(note, d, glide_from=None, drive=3.0):
    t = tvec(d)
    f = np.full(len(t), midi(note))
    if glide_from is not None:
        f = midi(note) + (midi(glide_from) - midi(note)) * np.exp(-t * 18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    click = np.sin(2 * np.pi * np.cumsum(f * (1 + 2 * np.exp(-t * 60))) / SR) * np.exp(-t * 40) * 0.5
    env = np.minimum(t / 0.003, 1) * np.clip((d - t) / 0.05, 0, 1) * (0.45 + 0.55 * np.exp(-t * 1.6))
    return np.tanh((np.sin(ph) + click) * drive) * env / np.tanh(drive)


def snare(d=0.35):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    body = np.sin(2 * np.pi * (175 + 60 * np.exp(-t * 40)) * t) * np.exp(-t * 18)
    noise = hp(onepole_lp(n, 7000), 1200) * np.exp(-t * 11)
    return np.tanh((body * 0.9 + noise * 0.9) * 1.6) * 0.8


def choir(notes, d, cutoff=1500):
    t = tvec(d)
    sig = np.zeros(len(t))
    for n in notes:
        for v in range(4):
            vib = 1 + 0.004 * np.sin(2 * np.pi * (4.5 + v * 0.3) * t + v)
            sig += saw(midi(n) * vib * 2 ** ((v - 1.5) * 0.12 / 12), t, rng.random())
    sig = onepole_lp(onepole_lp(sig, cutoff), cutoff * 1.4) / (4 * len(notes))
    env = np.minimum(t / 0.5, 1) * np.clip((d - t) / 0.4, 0, 1)
    return sig * env


def stab(notes, d=0.5):
    t = tvec(d)
    sig = np.zeros(len(t))
    for n in notes:
        sig += saw(midi(n), t, rng.random()) + saw(midi(n) * 1.006, t, rng.random())
    sig = onepole_lp(sig / (2 * len(notes)), 1800 + 5000 * np.exp(-t * 9)) * np.exp(-t * 4)
    burst = hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 30) * 0.4
    low = np.sin(2 * np.pi * midi(notes[0] - 24) * t) * np.exp(-t * 7)
    return np.tanh((sig * 1.4 + burst + low * 0.6) * 1.3)


def crackle(d):
    n = int(d * SR)
    x = np.zeros(n)
    idx = rng.integers(0, n, int(d * 60))
    x[idx] = rng.standard_normal(len(idx)) * rng.random(len(idx))
    return onepole_lp(x, 6000) + hp(rng.standard_normal(n), 3000) * 0.004


def rev_swell(d=1.2):
    t = tvec(d)
    n = rng.standard_normal(len(t))
    return hp(n, 2000) * (t / d) ** 3


# C# Phrygian: C# D E F# G# A B
CS = 37
riff = [  # 16 steps of the cowbell riff (midi or None)
    73, None, 73, 74, None, 73, None, 68, 73, None, 76, None, 74, 73, None, 68,
]
riff_b = [
    73, None, 73, 74, None, 73, None, 68, 76, None, 78, None, 76, 74, None, 73,
]
bass_roots = [CS, CS, CS - 4, CS + 1, CS, CS - 4, CS + 1, CS]  # per bar (C#, A, D)
S16 = BEAT / 4
kick_s = kick(0.4)
snare_s = snare()

# ---- intro (bar 0) ----
add(choir([61, 64, 68, 73], BAR + 0.3, cutoff=900), 0, 0.7)
add(rev_swell(BAR), 0, 0.35)
add(riser(BAR, 150, 5000), 0, 0.25)
for s in range(16):
    n = riff[s]
    if n is not None:
        add(onepole_lp(cowbell(n), 900 + 3000 * s / 16), s * S16, 0.18 + 0.2 * s / 16, pan=0.2)
for s in (12, 13, 14, 15):
    add(snare_s[: int(0.12 * SR)], s * S16, 0.15 + 0.08 * (s - 12))

# ---- groove bars 1-6 ----
add(impact(), BAR, 0.75)
pulses = []
for b in range(1, 7):
    bt = b * BAR
    root = bass_roots[b]
    chop = b == 6  # last stats bar: half-bar dropout chop
    for st in (0, 6, 10):
        if chop and st == 6:
            continue
        add(kick_s, bt + st * S16, 0.9)
        pulses.append(bt + st * S16)
    # 808 line: follows the kicks, slides on step 10
    prev = bass_roots[b - 1]
    add(b808(root, S16 * 6 * 0.95, glide_from=prev if prev != root else None), bt, 0.75)
    if not chop:
        add(b808(root, S16 * 4 * 0.95), bt + 6 * S16, 0.65)
    add(b808(root + 12 if b % 2 else root + 7, S16 * 6 * 0.95, glide_from=root), bt + 10 * S16, 0.6)
    add(snare_s, bt + 8 * S16, 0.75)
    pulses.append(bt + 8 * S16)
    # hats: 16ths with accents, triplet roll at the end of odd bars
    for s in range(16):
        if chop and 4 <= s < 8:
            continue
        add(hat(0.04), bt + s * S16, (0.16 if s % 4 == 2 else 0.09) * (0.7 if s % 2 else 1), pan=0.3)
    if b % 2:
        for q in range(6):
            add(hat(0.03), bt + 12 * S16 + q * (4 * S16 / 6), 0.07 + 0.02 * q, pan=-0.3)
    add(hat(open_=True), bt + 14 * S16, 0.08, pan=-0.2)
    # cowbell riff
    rf = riff if b % 2 else riff_b
    for s in range(16):
        n = rf[s]
        if n is None or (chop and 4 <= s < 8):
            continue
        add(cowbell(n), bt + s * S16, 0.42, pan=0.15 * (-1) ** s)
        add(cowbell(n + 12, 0.08), bt + s * S16 + S16 * 0.5, 0.08, pan=-0.4)  # echo
    # dark pad under it
    add(choir([61, 64, 68] if root == CS else [57, 61, 64] if root == CS - 4 else [62, 66, 69], BAR, cutoff=1100), bt, 0.22)
    if chop:  # stutter fill into the outro
        for q in range(8):
            add(snare_s[: int(0.05 * SR)], bt + 12 * S16 + q * S16 / 2, 0.12 + 0.05 * q)
add(crackle(15.0), 0, 0.5)

# ---- prompt + stat hits ----
hits = [2 * BAR + i * BEAT * 2 for i in range(6)] + [5 * BAR + j * S16 * 11 for j in range(3)]
stab_ch = [[61, 64, 68], [62, 66, 69], [61, 64, 68], [57, 61, 64], [62, 66, 69], [64, 68, 71],
           [61, 64, 68], [62, 66, 69], [64, 68, 73]]
for i, ht in enumerate(hits):
    add(stab([n + 12 for n in stab_ch[i]]), ht, 0.42, pan=0.25 * (-1) ** i)
    add(whoosh(0.3), ht - 0.27, 0.18, pan=-0.4 * (-1) ** i)

# ---- outro (bar 7) ----
ot = 7 * BAR
add(impact(2.0), ot, 0.8)
add(kick_s, ot, 1.0)
add(stab([73, 76, 80, 85], 1.2), ot, 0.5)
add(b808(CS - 12 + 12, BAR * 0.95, glide_from=CS + 12, drive=4), ot, 0.8)
add(choir([61, 64, 68, 73], BAR, cutoff=1600), ot, 0.35)
for i, n in enumerate([85, 80, 76, 73, 68]):
    add(cowbell(n, 0.25), ot + BEAT * 1.5 + i * S16, 0.25 * (1 - i / 7), pan=0.5 * (-1) ** i)
pulses.append(ot)

# ---- sidechain (kick + 808 pump) ----
duck = np.ones(N)
for kt in pulses:
    i0 = int(kt * SR)
    t = tvec(BEAT)
    env = 1 - 0.45 * np.exp(-t * 10)
    seg = duck[i0: i0 + len(env)]
    duck[i0: i0 + len(env)] = np.minimum(seg, env[: len(seg)])


def reverb(x, delays, fb=0.75, mix=0.18):
    out = np.zeros_like(x)
    for d in delays:
        D = int(d * SR)
        y = np.copy(x)
        for i in range(D, len(y), D):
            y[i: i + D] += y[i - D: i][: len(y[i: i + D])] * fb
        out += y
    return onepole_lp(out / len(delays), 4500) * mix


Ld, Rd = L * duck, R * duck
Lw = Ld + reverb(Ld, (0.0297, 0.0371, 0.0411, 0.0437))
Rw = Rd + reverb(Rd, (0.0313, 0.0353, 0.0423, 0.0459))
mx = np.stack([Lw, Rw], 1)


# ---- tape stop over the last 0.9s ----
def tape_stop(x, t0, dur):
    i0, n = int(t0 * SR), int(dur * SR)
    seg = x[i0:]
    rate = np.clip(1 - np.arange(len(seg)) / n, 0, 1) ** 1.5
    pos = np.cumsum(rate)
    pos = pos[pos < len(seg) - 1]
    out = np.zeros_like(seg)
    for c in range(seg.shape[1]):
        out[: len(pos), c] = np.interp(pos, np.arange(len(seg)), seg[:, c])
    out[: len(pos)] *= np.linspace(1, 0.3, len(pos))[:, None]
    x[i0:] = out
    return x


mx = tape_stop(mx, 14.05, 0.9)
fade = np.clip((DUR - np.arange(N) / SR) / 0.25, 0, 1)
fade_in = np.clip(np.arange(N) / SR / 0.02, 0, 1)
mx *= (fade * fade_in)[:, None]
mx /= np.max(np.abs(mx)) + 1e-9
mx = np.tanh(mx * 1.7) / np.tanh(1.7) * 0.92

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mx * 32767).astype("<i2").tobytes())
print("wrote", out)
