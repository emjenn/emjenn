"""Original 15s warm house track, 120 BPM, F major / D minor. Fully synthesized.
  0 intro (typing ticks), 2.0 drop, 3.5-12.5 a bell + whoosh every 1.5s (6 tips), 12.5 full sheet, 13 outro hit.
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



def keys(notes, d, bright=2200):
    """soft electric-piano-ish chord: sines + a little 2nd harmonic, gentle decay"""
    t = tvec(d)
    sig = np.zeros(len(t))
    for n in notes:
        f = midi(n)
        sig += np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6) + 0.08 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 9)
    sig /= len(notes)
    env = np.minimum(t / 0.004, 1) * np.exp(-t * 2.2) * np.clip((d - t) / 0.05, 0, 1)
    return onepole_lp(sig, bright) * env


def bell(note, d=0.6):
    t = tvec(d)
    f = midi(note)
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 8)) * np.exp(-t * 5)


# Fmaj7 - Am7 - Dm7 - Bbmaj7 (warm)
CH = [(41, [57, 60, 64, 65, 69]), (45, [55, 57, 60, 64, 67]), (38, [57, 60, 62, 65, 69]), (46, [57, 58, 62, 65, 69])]
kick_s, clap_s = kick(), clap()
kick_times = []
TIPS = [3.5 + 1.5 * i for i in range(6)]
T_FULL, T_OUT = 12.5, 13.0

# intro: keys + typing ticks + riser
add(keys(CH[0][1], 2.0, 1400), 0, 0.5)
for i in range(22):
    add(blip(88 + (i % 3) * 3, 0.03), 0.2 + i * 0.055, 0.05, pan=0.3 * np.sin(i))
add(riser(2.0), 0, 0.4)
for i in range(8):
    add(snare_hit(), 2.0 - BEAT * 2 + i * BEAT / 4, 0.08 + 0.05 * i)

def house_bar(b, chord_i):
    t0 = b * BAR
    root, ch = CH[chord_i % 4]
    for k in range(4):
        kt = t0 + k * BEAT
        kick_times.append(kt); add(kick_s, kt, 0.9)
        if k in (1, 3): add(clap_s, kt, 0.38)
        add(hat(open_=True), kt + BEAT / 2, 0.1, pan=0.25)
        for s in range(4):
            add(hat(0.02), kt + s * BEAT / 4, 0.035 + 0.02 * (s % 2), pan=-0.35)
        add(sub(root, BEAT * 0.4), kt + BEAT / 2, 0.45)
    for pos in (0.0, 0.75, 2.5, 3.25):  # syncopated keys stabs
        add(keys([n + 12 for n in ch], BEAT * 0.9, 2600), t0 + pos * BEAT, 0.35, pan=0.2 * (-1) ** int(pos * 4))

add(impact(), 2.0, 0.85)
for b in range(1, 7):
    house_bar(b, b - 1)
# tip punctuation: camera whoosh + bell note
mel = [81, 84, 79, 77, 81, 86]
for i, ts in enumerate(TIPS):
    add(whoosh(0.4), ts - 0.3, 0.22)
    add(impact(0.7), ts, 0.28)
    add(bell(mel[i]), ts, 0.16, pan=0.3 * (-1) ** i)
    add(bell(mel[i] + 7, 0.4), ts + BEAT, 0.08, pan=-0.3 * (-1) ** i)
# pull back to full sheet 12.5, outro 13
add(riser(0.5, 800, 12000), 12.0, 0.3)
add(impact(1.2), T_FULL, 0.5)
ot = T_OUT
add(impact(2.0), ot, 0.75)
add(kick_s, ot, 1.0); kick_times.append(ot)
add(keys([n + 12 for n in CH[0][1]], 2.0, 3000), ot, 0.6)
add(supersaw([n + 12 for n in CH[0][1]], 1.9, cutoff=2400, release=1.4), ot, 0.3)
add(sub(29, 1.6), ot, 0.5)
for i, n in enumerate([93, 89, 88, 84, 81]):
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

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mx * 32767).astype("<i2").tobytes())
print("wrote", out)
