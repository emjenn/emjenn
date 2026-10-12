"""Original 20s soundtracks for the 39 AI resources videos, 120 BPM. Fully synthesized.
usage: python3 music.py techno|breaks|future out.wav
  0-2 intro, 2 drop, 2-17 groove with hits at each category start, 17 wall breakdown, 18.5 outro hit.
"""
import numpy as np
import wave
import sys

SR = 44100
BPM = 120
BEAT = 60 / BPM
BAR = BEAT * 4
DUR = 20.0
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
CAT_STARTS = [4.0, 6.5, 9.5, 11.5, 14.0, 15.5]
T_WALL, T_OUT = 17.0, 18.5
kick_s, clap_s = kick(), clap()
kick_times = []


def acid(note, d, cut):
    t = tvec(d)
    f = midi(note)
    sig = saw(f, t)
    env_cut = cut * (0.35 + 0.65 * np.exp(-t * 18))
    y = onepole_lp(onepole_lp(sig, env_cut), env_cut * 1.2)
    return np.tanh(y * 3) * np.clip((d - t) / 0.01, 0, 1)


def stab(notes, d=0.25, cut=3500):
    return supersaw(notes, d, cutoff=cut, attack=0.003, release=0.08, voices=5, detune=0.12)


def bass808(note, d=0.6, slide=0):
    t = tvec(d)
    f = midi(note) * 2 ** (slide * np.clip(1 - t / 0.12, 0, 1) / 12) * (1 + 1.5 * np.exp(-t * 40))
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * 2.5 * np.exp(-t * 2.2)) * np.clip((d - t) / 0.04, 0, 1)


# ---------------- intro (0 - 2) ----------------
add(riser(2.0), 0, 0.45)
for i in range(8):
    add(snare_hit(), 2.0 - BEAT * 2 + i * BEAT / 4, 0.1 + 0.05 * i)

if STYLE == 'techno':
    KEY = 45  # A
    line = [0, 0, 12, 0, 3, 0, 15, 0, 0, 7, 0, 12, 10, 0, 3, 5]
    for s in range(16):  # filtered acid tease
        add(acid(KEY + line[s], BEAT / 4 * 0.9, 300 + s * 90), s * BEAT / 4, 0.25)
    for s in range(8):
        add(blip(81 + (s % 2) * 7, 0.06), s * BEAT / 2, 0.08)
elif STYLE == 'breaks':
    KEY = 43  # G
    add(supersaw([55, 58, 62, 65], 2.0, cutoff=800, attack=1.0, release=0.2), 0, 0.45)
    for s in range(4):
        add(whoosh(0.25, rev=s % 2 == 1), s * BEAT, 0.12)
else:
    KEY = 46  # Bb
    add(supersaw([58, 61, 65, 68, 72], 2.0, cutoff=700, attack=1.0, release=0.2), 0, 0.5)
    for i, n in enumerate([82, 85, 89, 87, 85, 82, 80, 77]):
        add(pluck(n, 0.2, 3000 + i * 400), i * BEAT / 2, 0.1)

add(impact(), 2.0, 0.9)

# ---------------- groove (2 - 17) ----------------
def bar_techno(t0, b):
    line = [0, 0, 12, 0, 3, 0, 15, 0, 0, 7, 0, 12, 10, 0, 3, 5]
    sweep = 500 + 2600 * (0.5 + 0.5 * np.sin(b * 0.9))
    for k in range(4):
        kt = t0 + k * BEAT
        kick_times.append(kt); add(kick_s, kt, 0.95)
        add(hat(open_=True), kt + BEAT / 2, 0.12, pan=0.2)
        if k in (1, 3): add(clap_s, kt, 0.4)
    for s in range(16):
        add(acid(KEY + line[s] + (12 if b % 4 == 3 and s > 11 else 0), BEAT / 4 * 0.9, sweep + 400 * (s % 3 == 0)), t0 + s * BEAT / 4, 0.24, pan=0.15 * np.sin(s))
        add(hat(0.025), t0 + s * BEAT / 4, 0.05 + 0.03 * (s % 2), pan=-0.3)
    add(sub(KEY - 12, BAR * 0.95), t0, 0.25)


def bar_breaks(t0, b):
    # classic break: K . . . S . . K | . K K . S . . .
    pat = [(0, 'k'), (1, 's'), (1.75, 'k'), (2.5, 'k'), (3, 's'), (3.75, 'g'), (2.25, 'g')]
    for pos, kind in pat:
        tt = t0 + pos * BEAT
        if kind == 'k': kick_times.append(tt); add(kick_s, tt, 0.9)
        elif kind == 's': add(clap_s, tt, 0.6); add(snare_hit(0.18), tt, 0.4)
        else: add(snare_hit(0.08), tt, 0.15)
    for s in range(8):
        add(hat(0.04), t0 + s * BEAT / 2, 0.12 if s % 2 else 0.07, pan=0.3)
    roots = [0, 0, -2, -4]
    r = KEY + roots[b % 4]
    for pos in (0, 0.75, 1.5, 2.5, 3.25):
        add(bass808(r, BEAT * 0.7, slide=5 if pos == 2.5 else 0), t0 + pos * BEAT, 0.55)
    ch = [[55, 58, 62], [55, 58, 62], [53, 57, 60], [51, 55, 58]][b % 4]
    for pos in (0.5, 2.0):
        add(stab([n + 12 for n in ch], 0.18), t0 + pos * BEAT, 0.28, pan=0.3 * (-1) ** int(pos))


def bar_future(t0, b):
    prog_ = [(34, [58, 61, 65, 68, 72]), (30, [58, 61, 66, 70, 73]), (37, [56, 61, 65, 68, 73]), (32, [56, 60, 63, 68, 72])]
    root, ch = prog_[b % 4]
    for k in range(4):
        kt = t0 + k * BEAT
        kick_times.append(kt); add(kick_s, kt, 0.9)
        if k in (1, 3): add(clap_s, kt, 0.5)
        add(hat(), kt + BEAT / 2, 0.18, pan=0.25)
        add(supersaw([n + 12 for n in ch], BEAT * 0.95, cutoff=3000, wob=1 / (BEAT / 3)), kt, 0.28, pan=0.15 * (-1) ** k)
        add(sub(root, BEAT * 0.9), kt, 0.55)
    arp = [0, 2, 1, 3, 4, 2, 3, 1]
    for s in range(16):
        add(pluck(ch[arp[s % 8]] + 12, 0.18, 6000), t0 + s * BEAT / 4, 0.11, pan=0.5 * np.sin(s * 0.8))


BAR_FN = {'techno': bar_techno, 'breaks': bar_breaks, 'future': bar_future}[STYLE]
for b in range(1, 8):
    BAR_FN(b * BAR, b)
BAR_FN(8 * BAR, 8)  # 16 - 18 bar, cut at the wall below

# category punctuation
for i, ts in enumerate(CAT_STARTS):
    add(impact(0.9), ts, 0.4)
    add(whoosh(0.45), ts - 0.4, 0.22)
    if STYLE == 'breaks':
        add(stab([62, 67, 70, 74], 0.35, 4500), ts, 0.35)
    elif STYLE == 'techno':
        add(blip(93, 0.12), ts, 0.15)
    else:
        add(supersaw([70, 73, 77, 82], 0.3, cutoff=5000, release=0.15), ts, 0.25)

# ---------------- wall (17 - 18.5): strip back, roll + riser ----------------
mute0, mute1 = int(T_WALL * SR), int(T_OUT * SR)
L[mute0:mute1] *= np.linspace(1, 0.15, mute1 - mute0)
R[mute0:mute1] *= np.linspace(1, 0.15, mute1 - mute0)
kick_times = [k for k in kick_times if not (T_WALL <= k < T_OUT)]
add(impact(1.2), T_WALL, 0.5)
add(riser(1.5, 400, 12000), T_WALL, 0.45)
for i in range(12):
    add(snare_hit(), T_OUT - 0.75 + i * BEAT / 8, 0.15 + 0.05 * i)
for i in range(39 // 3):
    add(blip(84 + (i % 5) * 2, 0.05), T_WALL + 0.05 + i * 0.06, 0.07, pan=-0.6 + i * 0.1)

# ---------------- outro hit ----------------
ot = T_OUT
L[int(ot * SR):] = 0; R[int(ot * SR):] = 0
add(impact(2.0), ot, 0.85)
add(kick_s, ot, 1.0); kick_times.append(ot)
fin = {'techno': [57, 60, 64, 69], 'breaks': [55, 58, 62, 67], 'future': [58, 61, 65, 70]}[STYLE]
add(supersaw([n + 12 for n in fin], 1.4, cutoff=3200, release=1.0), ot, 0.55)
add(sub(KEY - 12, 1.3), ot, 0.5)
for i, n in enumerate(sorted(fin, reverse=True)):
    add(pluck(n + 24, 0.45, 4000), ot + BEAT + i * BEAT / 4, 0.12)

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
