"""Original 15s phonk track, 120 BPM, C# minor. Fully synthesized (no samples).

  0.0  intro: filtered cowbell riff + riser
  2.0  DROP: 808s, cowbell lead, triplet hats; hard hits on 2.0/2.5/3.0/3.5/4.0 (headline cuts)
  4.5 - 11.5  one rim/chop accent per beat = one guide per beat (14)
  11.5 index: roll
  13.0 outro hit
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



def cowbell(note, d=0.22):
    t = tvec(d)
    f = midi(note)
    sq = np.sign(np.sin(2 * np.pi * f * t)) + np.sign(np.sin(2 * np.pi * f * 1.48 * t))
    sig = hp(onepole_lp(sq, 4200), 500)
    return sig * np.exp(-t * 11) * 0.5


def bass808(note, d=0.6, slide=0):
    t = tvec(d)
    f = midi(note) * 2 ** (slide * np.clip(1 - t / 0.12, 0, 1) / 12)
    f = f * (1 + 1.5 * np.exp(-t * 40))
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return np.tanh(sig * 2.5 * np.exp(-t * 2.2)) * np.clip((d - t) / 0.04, 0, 1)


def rim(d=0.06):
    t = tvec(d)
    return (np.sin(2 * np.pi * 1700 * t) * 0.6 + hp(rng.standard_normal(len(t)), 3000) * 0.5) * np.exp(-t * 70)


riff = [61, 64, 68, 66, 64, 61, 59, 61, 61, 64, 68, 71, 69, 68, 66, 64]
roots = [37, 37, 33, 35]  # C#, C#, A, B
kick_s, clap_s = kick(), clap()
kick_times = []

# intro: filtered cowbell riff + riser
for s in range(16):
    c = cowbell(riff[s] + 12, 0.2)
    add(onepole_lp(c, 900 + s * 150), s * BEAT / 4 + 0.0, 0.18 + s * 0.01, pan=0.2 * (-1) ** s)
add(riser(BAR), 0, 0.45)
for i in range(8):
    add(snare_hit(), BAR - BEAT * 2 + i * BEAT / 4, 0.1 + 0.05 * i)


def phonk_bar(t0, bar_idx, accent_beats=False):
    root = roots[bar_idx % 4]
    for k in (0.0, 1.5, 2.5):
        kt = t0 + k * BEAT
        kick_times.append(kt)
        add(kick_s, kt, 0.9)
        add(bass808(root, 0.7 if k < 2 else 0.45, slide=7 if k == 2.5 else 0), kt, 0.75)
    for k in (1, 3):
        add(clap_s, t0 + k * BEAT, 0.55)
    for s in range(12):  # triplet hats
        add(hat(0.03), t0 + s * BEAT / 3, 0.07 + 0.04 * (s % 3 == 0), pan=0.3)
    for s in range(8):
        n = riff[(bar_idx % 2) * 8 + s]
        add(cowbell(n + 12), t0 + s * BEAT / 2, 0.3, pan=-0.15)
    if accent_beats:
        for k in range(4):
            add(rim(), t0 + k * BEAT, 0.35, pan=0.4 * (-1) ** k)
            add(whoosh(0.16), t0 + k * BEAT - 0.08, 0.1)


add(impact(), 2.0, 0.9)
# headline: hard hits each beat 2.0 - 4.0
phonk_bar(2.0, 0, accent_beats=True)
phonk_bar(4.0, 1)
for k in range(5):
    add(impact(0.4), 2.0 + k * BEAT, 0.25)
add(impact(1.0), 4.5, 0.45)
# guides 4.5 - 11.5
for i in range(14):
    add(rim(), 4.5 + i * BEAT, 0.4, pan=0.4 * (-1) ** i)
    add(whoosh(0.16), 4.5 + i * BEAT - 0.08, 0.12)
for b in range(3, 6):
    phonk_bar(b * BAR, b)
# index 11.5 - 13: stripped + roll
for k in range(3):
    add(kick_s, 11.5 + k * BEAT, 0.85); kick_times.append(11.5 + k * BEAT)
    add(bass808(roots[3], 0.4), 11.5 + k * BEAT, 0.6)
for s in range(12):
    add(cowbell(riff[s] + 12, 0.12), 11.5 + s * BEAT / 4, 0.2)
for i in range(8):
    add(snare_hit(), 12.5 + i * BEAT / 8, 0.2 + 0.06 * i)
# outro
ot = 13.0
add(impact(2.0), ot, 0.85)
add(kick_s, ot, 1.0); kick_times.append(ot)
add(bass808(37, 1.8, slide=-5), ot, 0.8)
for i, n in enumerate([73, 68, 64, 61]):
    add(cowbell(n, 0.4), ot + BEAT + i * BEAT / 2, 0.22 * (1 - i / 6))

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
