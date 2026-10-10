"""v2 soundtrack: 15s future-bass / trap, 96 BPM, A minor. Fully synthesized, no samples.

1 bar = 2.5s, 6 bars = 15s
  bar 0  (0.0-2.5)   intro: filtered supersaw swell, riser, accelerating snare roll, gap before drop
  bar 1  (2.5-5.0)   DROP: 808 + kick, half-time clap, rolling hats, pumping supersaw chords
  bars 2-4 (5-12.5)  course run: groove + one pluck per course on every 8th (5.0 -> 11.25), fill into 12.5
  bar 5  (12.5-15)   outro: impact, final chord, long reverb tail
"""
import sys
import wave

import numpy as np

SR = 44100
BPM = 96
BEAT = 60 / BPM
BAR = BEAT * 4
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(42)

L = np.zeros(N)
R = np.zeros(N)
SC = np.ones(N)  # sidechain gain curve


def tvec(d):
    return np.arange(int(d * SR)) / SR


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def add(sig, t0, gain=1.0, pan=0.0, bus=None):
    i0 = int(round(t0 * SR))
    if i0 >= N or i0 < 0:
        return
    sig = sig[: N - i0]
    gl = gain * np.cos((pan + 1) * np.pi / 4)
    gr = gain * np.sin((pan + 1) * np.pi / 4)
    (bus or (L, R))[0][i0 : i0 + len(sig)] += sig * gl
    (bus or (L, R))[1][i0 : i0 + len(sig)] += sig * gr


def fftconv(x, h):
    n = len(x) + len(h) - 1
    m = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(h, m), m)[:n]


def lowpass_fir(x, fc, taps=255):
    k = np.arange(taps) - (taps - 1) / 2
    h = np.sinc(2 * fc / SR * k) * np.hamming(taps)
    h /= h.sum()
    return fftconv(x, h)[(taps - 1) // 2 : (taps - 1) // 2 + len(x)]


def svf_lp(x, cutoff, q=0.7):
    """time-varying state-variable lowpass (chunked control rate for speed)"""
    cutoff = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    y = np.zeros_like(x)
    lp = bp = 0.0
    blk = 64
    for s in range(0, len(x), blk):
        f = 2 * np.sin(np.pi * min(cutoff[s], SR / 6) / SR)
        damp = 1 / q
        for i in range(s, min(s + blk, len(x))):
            hp = x[i] - lp - damp * bp
            bp += f * hp
            lp += f * bp
            y[i] = lp
    return y


def blep_saw(freq, t, phase0=0.0):
    dt = np.broadcast_to(freq, t.shape) / SR
    p = (np.cumsum(dt) + phase0) % 1.0
    s = 2 * p - 1
    m1 = p < dt
    x = p[m1] / dt[m1]
    s[m1] -= x + x - x * x - 1
    m2 = p > 1 - dt
    x = (p[m2] - 1) / dt[m2]
    s[m2] -= x * x + x + x + 1
    return s


def supersaw(notes, d, detune=0.22, voices=7):
    t = tvec(d)
    l = np.zeros(len(t))
    r = np.zeros(len(t))
    for n in notes:
        for v in range(voices):
            off = (v - (voices - 1) / 2) / ((voices - 1) / 2)
            f = midi(n + off * detune)
            s = blep_saw(np.full(len(t), f), t, rng.random())
            pan = off * 0.8
            l += s * np.cos((pan + 1) * np.pi / 4)
            r += s * np.sin((pan + 1) * np.pi / 4)
    k = 1 / (len(notes) * voices) ** 0.5
    return l * k, r * k


# ---------------- drums ----------------
def kick():
    t = tvec(0.5)
    f = 48 + 160 * np.exp(-t * 35)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    click = rng.standard_normal(len(t)) * np.exp(-t * 500) * 0.4
    return np.tanh((body + click) * 2.2)


def bass808(note, d, glide_from=None):
    t = tvec(d)
    f0 = midi(note)
    f = np.full(len(t), f0)
    if glide_from is not None:
        f = midi(glide_from) + (f0 - midi(glide_from)) * (1 - np.exp(-t * 18))
    f = f * (1 + 0.6 * np.exp(-t * 40))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    env = np.minimum(1, t / 0.004) * np.exp(-t * 1.1)
    rel = np.minimum(1, (d - t) / 0.03)
    return np.tanh(s * env * rel * 2.6) * 0.8


def clap():
    t = tvec(0.45)
    n = rng.standard_normal(len(t))
    env = np.zeros(len(t))
    for k in (0.0, 0.009, 0.018, 0.027):
        env += (t >= k) * np.exp(-np.maximum(t - k, 0) * (90 if k < 0.027 else 16))
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.5
    x = n * env
    x = x - lowpass_fir(x, 900, 101)
    return np.tanh((x + tone) * 1.3) * 0.7


def snare(gain=1.0):
    t = tvec(0.18)
    n = rng.standard_normal(len(t))
    n = n - lowpass_fir(n, 1500, 61)
    tone = np.sin(2 * np.pi * (220 + 80 * np.exp(-t * 60)) * t)
    return (n * 0.7 + tone * 0.5) * np.exp(-t * 28) * gain


def hat(open_=False):
    t = tvec(0.35 if open_ else 0.05)
    n = rng.standard_normal(len(t))
    n = n - lowpass_fir(n, 7000, 61)
    return n * np.exp(-t * (9 if open_ else 90)) * 0.5


def pluck(note, d=0.5, bright=1.0):
    t = tvec(d)
    s = blep_saw(np.full(len(t), midi(note)), t) * 0.6 + np.sign(np.sin(2 * np.pi * midi(note + 12) * t)) * 0.25
    s = lowpass_fir(s, 2500 + 4000 * bright, 63)
    return s * np.exp(-t * 9) * np.minimum(1, t / 0.002)


def reverb_ir(seconds, decay, seed):
    r = np.random.default_rng(seed)
    t = tvec(seconds)
    ir = r.standard_normal(len(t)) * np.exp(-t * decay)
    ir = lowpass_fir(ir, 6000, 63)
    return ir / np.sqrt(np.sum(ir ** 2))


def sidechain_at(t0, depth=0.85, rel=7.0):
    i0 = int(t0 * SR)
    t = tvec(BEAT)
    g = 1 - depth * np.exp(-t * rel) * np.minimum(1, (t + 0.0) / 0.003 + 0.3)
    i1 = min(N, i0 + len(g))
    SC[i0:i1] = np.minimum(SC[i0:i1], g[: i1 - i0])


# ---------------- arrangement ----------------
T_DROP = BAR
T_OUT = BAR * 5
# Am - F - C - G  (one chord per bar for the drop bars), voiced around A3-E5
CHORDS = [
    [57, 60, 64, 69, 72],  # Am
    [53, 57, 60, 65, 69],  # F
    [48, 55, 60, 64, 67],  # C
    [55, 59, 62, 67, 71],  # G
]
ROOTS = [33, 29, 36, 31]  # 808 roots (A1, F1, C2, G1)

pad_bus = (np.zeros(N), np.zeros(N))  # gets sidechained
dry_bus = (np.zeros(N), np.zeros(N))

# --- intro swell: filtered supersaw Am(add9), cutoff opening over the bar
l, r = supersaw([57, 64, 69, 71, 76], BAR - 0.16)
cut = 300 * (40 ** (tvec(BAR - 0.16) / (BAR - 0.16)))
env = np.minimum(1, tvec(BAR - 0.16) / 0.8)
add(svf_lp(l, cut, 1.4) * env, 0, 0.55, -0.2, pad_bus)
add(svf_lp(r, cut, 1.4) * env, 0, 0.55, 0.2, pad_bus)

# riser (noise sweep)
t = tvec(BAR - 0.16)
noise = rng.standard_normal(len(t))
riser = svf_lp(noise, 400 * (25 ** (t / t[-1])), 2.5) * (t / t[-1]) ** 2
add(riser, 0, 0.35, 0, dry_bus)

# accelerating snare roll into the drop (8ths, 16ths, 32nds) with crescendo
roll = [i * BEAT / 2 for i in range(4)] + [2 * BEAT + i * BEAT / 4 for i in range(4)] + [3 * BEAT + i * BEAT / 8 for i in range(6)]
for k, tt in enumerate(roll):
    add(snare(0.25 + 0.75 * k / len(roll)), tt, 0.55, 0, dry_bus)
# ticking hats in intro
for i in range(8):
    add(hat(), i * BEAT / 2 + BEAT / 4, 0.25, 0.3, dry_bus)

# --- impacts
def impact(t0, gain=1.0):
    t = tvec(2.0)
    boom = np.sin(2 * np.pi * np.cumsum(38 + 90 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.2)
    nz = rng.standard_normal(len(t)) * np.exp(-t * 5)
    nz = lowpass_fir(nz, 3000, 63)
    add(np.tanh(boom * 1.5 + nz * 0.4), t0, 0.7 * gain, 0, dry_bus)


impact(T_DROP)
impact(T_OUT, 1.1)

# --- drop + course run groove (bars 1-4)
for b in range(1, 5):
    t0 = b * BAR
    ch = CHORDS[(b - 1) % 4]
    # pumping supersaw chord for the whole bar
    l, r = supersaw(ch, BAR)
    l = lowpass_fir(l, 5200, 63)
    r = lowpass_fir(r, 5200, 63)
    add(l, t0, 0.45, -0.1, pad_bus)
    add(r, t0, 0.45, 0.1, pad_bus)
    # kick pattern (trap): 1, the "and" of 2, 3+ (bar 4 gets a variation)
    kicks = [0, 1.5, 2.75] if b != 4 else [0, 1.5, 2.25, 2.75, 3.5]
    for k in kicks:
        add(kick(), t0 + k * BEAT, 0.9, 0, dry_bus)
        sidechain_at(t0 + k * BEAT)
    # 808: root on 1, re-hit on beat 2.5 with glide
    root = ROOTS[(b - 1) % 4]
    add(bass808(root, BEAT * 1.5), t0, 0.85, 0, dry_bus)
    add(bass808(root + 12 if b % 2 else root, BEAT * 2.5, glide_from=root), t0 + 1.5 * BEAT, 0.75, 0, dry_bus)
    # half-time clap on beat 3
    add(clap(), t0 + 2 * BEAT, 0.75, 0, dry_bus)
    # hats: 8ths with 16th/triplet rolls
    for i in range(8):
        add(hat(), t0 + i * BEAT / 2, 0.32, 0.25, dry_bus)
    if b in (2, 4):
        for i in range(6):
            add(hat(), t0 + 3 * BEAT + i * BEAT / 6, 0.22 + 0.04 * i, -0.2, dry_bus)
    else:
        for i in range(4):
            add(hat(), t0 + 1 * BEAT + i * BEAT / 4, 0.2, -0.25, dry_bus)
    add(hat(True), t0 + 3.5 * BEAT, 0.22, 0.4, dry_bus)

# --- course plucks: 20 notes on 8ths from 5.0s, A-minor pentatonic climbing melody
PENTA = [57, 60, 62, 64, 67, 69, 72, 74, 76, 79, 81]
mel = [0, 2, 4, 3, 5, 4, 6, 5, 3, 5, 7, 6, 5, 7, 8, 7, 8, 9, 8, 10]
pluck_bus = (np.zeros(N), np.zeros(N))
for i, m in enumerate(mel):
    tt = 2 * BAR + i * BEAT / 2
    add(pluck(PENTA[m], 0.5, 0.4 + 0.6 * i / 19), tt, 0.32, -0.35 if i % 2 else 0.35, pluck_bus)
    add(pluck(PENTA[m] + 12, 0.25, 0.5), tt, 0.1, 0.35 if i % 2 else -0.35, pluck_bus)
# chord stab on "20/20 unlocked" (11.25)
for n in (69, 72, 76, 81):
    add(pluck(n, 1.0, 1.0), 2 * BAR + 20 * BEAT / 2, 0.22, 0, pluck_bus)

# fill into outro: snare 16ths + riser over the last 1.25s of bar 4
fill_t0 = T_OUT - 2 * BEAT
for i in range(8):
    add(snare(0.3 + 0.7 * i / 8), fill_t0 + i * BEAT / 4, 0.45, 0, dry_bus)
t = tvec(2 * BEAT - 0.08)
noise = rng.standard_normal(len(t))
add(svf_lp(noise, 800 * (12 ** (t / t[-1])), 2.0) * (t / t[-1]) ** 2, fill_t0, 0.3, 0, dry_bus)

# --- outro: big final chord (Am add9) with slow fade + 808 sustain
l, r = supersaw([45, 57, 64, 69, 71, 76], DUR - T_OUT)
t = tvec(DUR - T_OUT)
fade = np.exp(-t * 0.9) * np.minimum(1, (DUR - T_OUT - t) / 0.4)
add(lowpass_fir(l, 4500, 63) * fade, T_OUT, 0.55, -0.15, dry_bus)
add(lowpass_fir(r, 4500, 63) * fade, T_OUT, 0.55, 0.15, dry_bus)
add(bass808(33, 2.2), T_OUT, 0.8, 0, dry_bus)
add(kick(), T_OUT, 1.0, 0, dry_bus)
add(clap(), T_OUT, 0.6, 0, dry_bus)
# sparkle arp in outro
for i, n in enumerate([81, 76, 72, 69, 76, 72, 69, 64]):
    add(pluck(n, 0.6, 0.7), T_OUT + 0.3 + i * BEAT / 2, 0.14 * (1 - i / 9), -0.5 + i / 8, pluck_bus)

# ---------------- mix ----------------
mixL = pad_bus[0] * SC + dry_bus[0] + pluck_bus[0]
mixR = pad_bus[1] * SC + dry_bus[1] + pluck_bus[1]

# reverb send (pads + plucks + claps)
send_l = pad_bus[0] * SC * 0.35 + pluck_bus[0] * 0.6 + dry_bus[0] * 0.08
send_r = pad_bus[1] * SC * 0.35 + pluck_bus[1] * 0.6 + dry_bus[1] * 0.08
wl = fftconv(send_l, reverb_ir(2.8, 2.2, 1))[:N]
wr = fftconv(send_r, reverb_ir(2.8, 2.2, 2))[:N]
mixL += wl * 0.28
mixR += wr * 0.28

# gap before the drop (classic "breath")
gap0, gap1 = int((T_DROP - 0.16) * SR), int(T_DROP * SR)
g = np.ones(N)
g[gap0:gap1] = np.linspace(1, 0.05, gap1 - gap0) ** 3
mixL *= g
mixR *= g

# master: gentle glue + soft clip + limiter-ish normalize
for ch in (mixL, mixR):
    ch -= np.mean(ch)
peak = max(np.max(np.abs(mixL)), np.max(np.abs(mixR)))
mixL = np.tanh(mixL / peak * 1.6) / np.tanh(1.6)
mixR = np.tanh(mixR / peak * 1.6) / np.tanh(1.6)
# fade in/out edges
fi = int(0.01 * SR)
fo = int(0.35 * SR)
for ch in (mixL, mixR):
    ch[:fi] *= np.linspace(0, 1, fi)
    ch[-fo:] *= np.linspace(1, 0, fo)
out = np.stack([mixL, mixR], 1) * 0.92

path = sys.argv[1] if len(sys.argv) > 1 else "build/music.wav"
with wave.open(path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((out * 32767).astype("<i2").tobytes())
print("wrote", path)
