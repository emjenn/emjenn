"""Original 15s electro / future-house track, 128 BPM, D minor (FullEnrich cut). Fully synthesized (no samples).

Timeline (1 bar = 1.875s, 8 bars = 15s):
  bar 0      intro: tape-start pad, riser, accelerating snare roll
  bar 1      DROP: impact, four-on-the-floor, 808 sub + growl bass, clap
  bars 2-4   6 prompts, one every 2 beats: chord stab + climbing bell + whoosh
  bars 5-6   3 proof stats on a syncopated 11/16 grid, glitch stutters
  bar 7      outro: final chord hit, half-time kick, downlifter, reverb tail
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




def bell(note, d=0.9):
    t = tvec(d)
    f = midi(note)
    mod = np.sin(2 * np.pi * f * 3.5 * t) * 2.2 * np.exp(-t * 6)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 4.5)


def sub808(note, d, glide_from=None):
    t = tvec(d)
    f = np.full(len(t), midi(note))
    if glide_from is not None:
        f = midi(note) + (midi(glide_from) - midi(note)) * np.exp(-t * 25)
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = np.minimum(t / 0.004, 1) * np.clip((d - t) / 0.04, 0, 1) * (0.55 + 0.45 * np.exp(-t * 3))
    return np.tanh(sig * 2.2) * env


def growl(note, d):
    t = tvec(d)
    f = midi(note)
    sig = saw(f, t) + saw(f * 1.008, t, 0.3) + 0.5 * np.sign(np.sin(2 * np.pi * f * 0.5 * t))
    wob = 500 + 2200 * (0.5 + 0.5 * np.sin(2 * np.pi * (1 / BEAT) * 2 * t - np.pi / 2))
    sig = onepole_lp(onepole_lp(sig, wob), wob)
    env = np.minimum(t / 0.004, 1) * np.clip((d - t) / 0.03, 0, 1)
    return np.tanh(sig * 1.4 * env) * 0.7


DM = (38, [62, 65, 69, 72])
BB = (34, [62, 65, 70, 74])
F_ = (41, [60, 65, 69, 72])
C_ = (36, [60, 64, 67, 72])
prog = [DM, DM, BB, F_, C_, BB, F_, DM]

kick_s, clap_s = kick(), clap()

# ---- intro (bar 0): tape-start pad + riser + snare roll ----
t0 = tvec(BAR + 0.2)
pad = supersaw([n - 12 for n in prog[0][1]], BAR + 0.2, cutoff=700, attack=0.6, release=0.3)
pad = onepole_lp(pad, 400 + 3200 * (t0 / BAR) ** 2)
add(pad, 0, 0.6)
add(riser(BAR, 150, 9000), 0, 0.55)
for i in range(4):
    add(kick_s, i * BEAT, 0.35 * (i + 1) / 4)
roll = [0.0]
while roll[-1] < BAR - 0.02:  # accelerating roll
    roll.append(roll[-1] + max(0.035, 0.22 * (1 - roll[-1] / BAR) ** 1.4))
for k, rt in enumerate(roll[:-1]):
    add(snare_roll_hit(), rt, 0.04 + 0.22 * (rt / BAR) ** 2, pan=0.15 * (-1) ** k)

# ---- drop: bars 1-6 groove ----
add(impact(), BAR, 1.0)
kick_times = []
for b in range(1, 7):
    bt = b * BAR
    root, ch = prog[b]
    for k in range(4):
        kt = bt + k * BEAT
        kick_times.append(kt)
        add(kick_s, kt, 1.0)
        add(hat(), kt + BEAT / 2, 0.24, pan=0.25)
        add(hat(open_=True), kt + BEAT / 2, 0.08, pan=-0.25)
        if k in (1, 3):
            add(clap_s, kt, 0.5, pan=0.05)
        # bass: 808 on the beat, growl on offbeats
        prev = prog[b - 1][0] if k == 0 else None
        add(sub808(root, BEAT * 0.48, glide_from=prev + 12 if prev else None), kt, 0.55)
        add(growl(root + 12, BEAT * 0.45), kt + BEAT / 2, 0.30)
    for s in range(16):
        add(hat(0.03), bt + s * BEAT / 4, 0.05 + 0.035 * (s % 2), pan=-0.35)
    # offbeat chord stabs
    for k in range(4):
        st = supersaw([n + 12 for n in ch], BEAT * 0.42, cutoff=3400 if b >= 2 else 2400, release=0.07)
        add(st, bt + k * BEAT + BEAT / 2, 0.26, pan=-0.25 if k % 2 else 0.25)

# ---- 6 prompt hits every 2 beats from bar 2, then 3 syncopated stat hits ----
penta = [62, 65, 67, 69, 72, 74, 77, 79, 81]
hits = [2 * BAR + i * BEAT * 2 for i in range(6)] + [5 * BAR + j * BEAT * 2.75 for j in range(3)]
for i, ct in enumerate(hits):
    root, ch = prog[min(7, int(ct / BAR + 1e-6))]
    add(supersaw(ch, BEAT * 0.9, cutoff=4200, attack=0.003, release=0.25), ct, 0.38)
    add(bell(penta[i]), ct, 0.22, pan=0.35 * (-1) ** i)
    add(bell(penta[i] + 12, 0.5), ct + BEAT, 0.08, pan=-0.35 * (-1) ** i)
    add(whoosh(0.35), ct - 0.3, 0.22, pan=0.5 * (-1) ** i)
# data-glitch stutters during the stats
for j in range(3):
    st = 5 * BAR + j * BEAT * 2.75 + BEAT * 1.5
    for q in range(6):
        add(pluck(86 - q * 2, 0.05, 7000), st + q * BEAT / 8, 0.09, pan=0.6 * (-1) ** q)

# 16th arp across the showcase
arp_pat = [0, 2, 1, 3, 2, 1, 3, 2]
for b in range(2, 7):
    _, ch = prog[b]
    bt = b * BAR
    for s in range(16):
        n = ch[arp_pat[s % 8]] + 12 + (12 if s % 8 == 7 else 0)
        add(pluck(n, 0.18, 4500), bt + s * BEAT / 4, 0.12 + 0.03 * (b - 2) / 4, pan=0.45 * np.sin(s * 0.7))
add(whoosh(0.7, rev=True), BAR * 0.2, 0.15)
add(riser(BAR * 0.5, 400, 8000), 6.5 * BAR, 0.3)

# ---- outro (bar 7) ----
ot = 7 * BAR
add(impact(2.0), ot, 0.8)
add(kick_s, ot, 1.0)
add(kick_s, ot + BEAT * 2, 0.8)
add(supersaw([n + 12 for n in prog[7][1]] + [62 + 12], BAR, cutoff=3200, attack=0.005, release=1.2), ot, 0.6)
add(sub808(26, BAR * 0.9, glide_from=38), ot, 0.55)
add(downlifter(BAR), ot, 0.25)
for i, n in enumerate([86, 84, 81, 79, 77, 74, 72, 69]):
    add(bell(n, 0.6), ot + BEAT * 1.5 + i * BEAT / 4, 0.1 * (1 - i / 10), pan=0.5 * (-1) ** i)

# ---- sidechain ----
duck = np.ones(N)
for kt in kick_times + [ot]:
    i0 = int(kt * SR)
    t = tvec(BEAT)
    env = 1 - 0.6 * np.exp(-t * 9)
    seg = duck[i0 : i0 + len(env)]
    duck[i0 : i0 + len(env)] = np.minimum(seg, env[: len(seg)])


def reverb(x, delays, fb=0.78, mix=0.2):
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
