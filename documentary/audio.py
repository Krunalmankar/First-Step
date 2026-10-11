"""Original score, sound design and final mix — all synthesised here, no external audio.

Music direction follows the brief chapter by chapter (tension pulse in the cold open, a build in
Part 1, darker tone and low hits in Part 2, propulsive UK sequence, thin ambience for the dollar,
cautious optimism then a hard cut on "Not quite.", reflective Part 5, controlled build to the
final line, warm outro). Music ducks under the narration and drops to near-silence on [pause].
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import butter, resample_poly, sosfilt, sosfiltfilt

HERE = Path(__file__).parent
SR = 48000
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


# ------------------------------------------------------------------ instruments
def pad(dur, chords, chord_len, cutoff=1400, bright=0.5):
    """Slow, warm pad: detuned additive voices with long crossfades between chords."""
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    t_all = np.arange(n) / SR
    xf = min(2.5, chord_len * 0.45)
    k = 0
    t0 = 0.0
    while t0 < dur:
        notes = chords[k % len(chords)]
        a, b = int(max(0, t0 - xf) * SR), int(min(dur, t0 + chord_len + xf) * SR)
        t = t_all[a:b]
        seg = np.zeros(b - a, np.float32)
        for m in notes:
            f = midi(m)
            for h, amp in ((1, 1.0), (2, 0.35 * bright), (3, 0.18 * bright), (4, 0.08 * bright)):
                for det in (-0.0018, 0.0018):
                    seg += amp * np.sin(2 * np.pi * f * h * (1 + det) * t + rng.uniform(0, 6.28))
        seg /= max(1, len(notes)) * 2.6
        # raised-cosine window over the chord with xf-second fades
        L = b - a
        w = np.ones(L, np.float32)
        fi = int(min(xf * SR, L // 2))
        if fi:
            ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fi))
            if t0 > 0:
                w[:fi] = ramp
            w[-fi:] = np.minimum(w[-fi:], ramp[::-1])
        out[a:b] += seg * w
        t0 += chord_len
        k += 1
    slow = 0.85 + 0.15 * np.sin(2 * np.pi * 0.07 * t_all + 1.3)
    return lp(out * slow, cutoff).astype(np.float32)


def kick(dur=0.6, f0=48, f1=110, decay=7.0):
    t = np.arange(int(dur * SR)) / SR
    ph = 2 * np.pi * (f0 * t + (f1 - f0) / 28 * (1 - np.exp(-28 * t)))
    return (np.sin(ph) * np.exp(-decay * t)).astype(np.float32)


def pulse(dur, bpm, gain_curve=None, f0=48):
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    k = kick(f0=f0)
    step = 60 / bpm
    t = 0.0
    while t < dur:
        i = int(t * SR)
        seg = k[: n - i]
        g = gain_curve(t / dur) if gain_curve else 1.0
        out[i:i + len(seg)] += seg * g
        t += step
    return out


def ticks(dur, bpm, level=0.12):
    """Soft filtered-noise ticks on eighth notes for propulsion."""
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    L = int(0.05 * SR)
    env = np.exp(-np.arange(L) / SR * 90).astype(np.float32)
    step = 60 / bpm / 2
    t, j = 0.0, 0
    while t < dur:
        i = int(t * SR)
        nz = rng.standard_normal(L).astype(np.float32) * env * (1.0 if j % 2 == 0 else 0.55)
        out[i:i + L] += nz[: n - i]
        t += step
        j += 1
    return (bp(out, 3000, 9000) * level).astype(np.float32)


def piano(dur, notes, spacing, level=0.3):
    """Sparse plucked notes (additive sine with fast decay), for reflective passages."""
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    L = int(4.0 * SR)
    t = np.arange(L) / SR
    k, x = 0, 0.4
    while x < dur - 0.5:
        f = midi(notes[k % len(notes)])
        tone = sum(a * np.sin(2 * np.pi * f * h * t) * np.exp(-t * (1.1 + 0.9 * h))
                   for h, a in ((1, 1), (2, 0.4), (3, 0.15), (4, 0.06)))
        tone *= np.minimum(1, t / 0.006)
        i = int(x * SR)
        out[i:i + L] += (tone[: n - i] * level).astype(np.float32)
        x += spacing
        k += 1
    return lp(out, 3500)


def thin(dur, level=0.18):
    """Thin, unsettling high ambience: two close high sines with slow tremolo plus faint air."""
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * midi(81) * t) + 0.8 * np.sin(2 * np.pi * midi(81) * 1.006 * t)
    s += 0.5 * np.sin(2 * np.pi * midi(88) * t + 1)
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * t)
    air = bp(rng.standard_normal(len(t)).astype(np.float32), 2000, 6000) * 0.25
    return ((s * trem / 2.3 + air) * level).astype(np.float32)


def drone(dur, note=38, level=0.4):
    t = np.arange(int(dur * SR)) / SR
    f = midi(note)
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t + 0.5) + 0.2 * np.sin(2 * np.pi * 3 * f * t)
    return (lp(s, 400) * level * (0.85 + 0.15 * np.sin(2 * np.pi * 0.11 * t))).astype(np.float32)


# ------------------------------------------------------------------ sound effects
def sfx_hit(level=0.9):
    """Low cinematic impact."""
    d = 3.2
    t = np.arange(int(d * SR)) / SR
    ph = 2 * np.pi * (36 * t + 60 / 6 * (1 - np.exp(-6 * t)))
    body = np.sin(ph) * np.exp(-1.6 * t)
    nz = lp(rng.standard_normal(len(t)), 700) * np.exp(-9 * t) * 0.6
    return ((body + nz) * level).astype(np.float32)


def sfx_riser(d=1.6, level=0.35):
    """Filtered-noise swell that resolves into the next chapter card."""
    n = int(d * SR)
    t = np.arange(n) / SR
    nz = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32)
    blk = 2048
    for i in range(0, n, blk):
        fc = 300 + 5000 * (i / n) ** 2
        out[i:i + blk] = lp(nz[i:i + blk], fc)
    env = (t / d) ** 2
    return (out * env * level).astype(np.float32)


def sfx_whoosh(d=0.9, level=0.28):
    n = int(d * SR)
    t = np.arange(n) / SR
    env = np.sin(np.pi * t / d) ** 2
    return (bp(rng.standard_normal(n), 250, 2200) * env * level).astype(np.float32)


def sfx_crack(level=0.7):
    d = 0.9
    n = int(d * SR)
    t = np.arange(n) / SR
    out = hp(rng.standard_normal(n), 1500) * np.exp(-14 * t) * 0.6
    for c in (0.0, 0.035, 0.08, 0.15):
        i = int(c * SR)
        L = int(0.012 * SR)
        out[i:i + L] += rng.standard_normal(L) * np.exp(-np.arange(L) / L * 5) * 1.3
    out += lp(rng.standard_normal(n), 200) * np.exp(-5 * t) * 0.8
    return (out * level).astype(np.float32)


def sfx_coin(level=0.35):
    """Small metallic 'ting': inharmonic partials with fast decay."""
    d = 1.2
    t = np.arange(int(d * SR)) / SR
    parts = [(2350, 1.0, 5.0), (3960, 0.6, 7.0), (5480, 0.4, 9.0), (7120, 0.25, 12.0)]
    sig = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-k * t) for f, a, k in parts)
    sig *= np.minimum(1, t / 0.002)
    return (sig * level / 2.3).astype(np.float32)


def sfx_tick(level=0.25):
    L = int(0.03 * SR)
    return (bp(rng.standard_normal(L), 2500, 7000) * np.exp(-np.arange(L) / SR * 160) * level).astype(np.float32)


# ------------------------------------------------------------------ score
Dm = [[50, 57, 62, 65], [46, 53, 62, 65], [53, 57, 60, 65], [48, 55, 60, 64]]          # Dm Bb F C
DARK = [[50, 57, 62, 65], [49, 56, 61, 65], [46, 53, 58, 62], [45, 52, 57, 61]]       # Dm, C#dim-ish, Bbm, A
OPT = [[53, 60, 65, 69], [48, 55, 64, 67], [50, 57, 62, 65], [46, 53, 62, 65]]        # F C Dm Bb
HOPE = [[46, 53, 62, 65], [53, 60, 65, 69], [48, 55, 64, 67], [53, 57, 60, 65]]       # Bb F C F
WARM = [[53, 60, 64, 69], [46, 58, 62, 65], [50, 57, 62, 65], [48, 55, 60, 64]]

# per-scene music parameters; scenes not listed inherit from the previous one
CUES = {
    "title40": dict(chords=DARK, cl=8, pad=0.32, cut=900, bpm=56, pulse=0.38),
    "milestones": dict(chords=DARK, cl=8, pad=0.36, cut=1000, bpm=60, pulse=0.42),
    "rome_intro": dict(chords=DARK, cl=10, pad=0.26, cut=800, bpm=0, pulse=0, piano=0.16),
    "rome_edict": dict(chords=DARK, cl=8, pad=0.30, cut=900, bpm=60, pulse=0.22),
    "rome_fall": dict(chords=DARK, cl=10, pad=0.26, cut=800, bpm=0, pulse=0, piano=0.14),
    "rome_us": dict(chords=DARK, cl=8, pad=0.30, cut=900, bpm=56, pulse=0.26),
    "question": dict(chords=DARK, cl=8, pad=0.30, cut=900, bpm=0, pulse=0),
    "_title": dict(chords=Dm, cl=6, pad=0.42, cut=1400, bpm=0, pulse=0),
    "spend_list": dict(chords=Dm, cl=8, pad=0.32, cut=1500, bpm=84, pulse=0.10),
    "bonds": dict(chords=Dm, cl=8, pad=0.34, cut=1600, bpm=84, pulse=0.18, tick=0.04),
    "machine": dict(chords=Dm, cl=6, pad=0.36, cut=1900, bpm=88, pulse=0.30, tick=0.08),
    "spin": dict(chords=Dm, cl=4, pad=0.38, cut=2200, bpm=96, pulse=0.38, tick=0.12),
    "_chapter2": dict(chords=DARK, cl=8, pad=0.36, cut=900, bpm=0, pulse=0),
    "nobody": dict(chords=DARK, cl=8, pad=0.30, cut=800, bpm=66, pulse=0.18),
    "none_perfect": dict(chords=DARK, cl=10, pad=0.18, cut=600, bpm=0, pulse=0),
    "yield": dict(chords=DARK, cl=8, pad=0.30, cut=900, bpm=66, pulse=0.24),
    "charging": dict(chords=DARK, cl=8, pad=0.28, cut=900, bpm=0, pulse=0),
    "_chapter3": dict(chords=DARK, cl=8, pad=0.34, cut=900, bpm=72, pulse=0.30),
    "door1_quote": dict(chords=DARK, cl=8, pad=0.30, cut=900, bpm=72, pulse=0.30),
    "door1_mortgage": dict(chords=DARK, cl=8, pad=0.28, cut=1000, bpm=72, pulse=0.18),
    "uk_intro": dict(chords=DARK, cl=4, pad=0.30, cut=1200, bpm=104, pulse=0.30, tick=0.08),
    "uk": dict(chords=DARK, cl=4, pad=0.36, cut=1600, bpm=108, pulse=0.46, tick=0.16),
    "uk_imagine": dict(chords=DARK, cl=8, pad=0.28, cut=800, bpm=0, pulse=0),
    "door2": dict(chords=DARK, cl=10, pad=0.10, cut=700, bpm=0, pulse=0, thin=0.22),
    "door3": dict(chords=DARK, cl=8, pad=0.30, cut=800, bpm=70, pulse=0.30),
    "crisis_collapse": dict(chords=Dm, cl=8, pad=0.30, cut=1000, bpm=0, pulse=0),
    "_chapter4": dict(chords=OPT, cl=6, pad=0.34, cut=1600, bpm=92, pulse=0.18),
    "adv1": dict(chords=OPT, cl=6, pad=0.36, cut=1800, bpm=92, pulse=0.24, tick=0.06),
    "safe": dict(chords=OPT, cl=6, pad=0.34, cut=1800, bpm=92, pulse=0.22, tick=0.05, cut_at=1),
    "trust": dict(chords=DARK, cl=10, pad=0.0, cut=600, bpm=0, pulse=0, drone=0.30),
    "_chapter5": dict(chords=Dm, cl=10, pad=0.30, cut=1000, bpm=0, pulse=0, piano=0.22),
    "chain": dict(chords=Dm, cl=8, pad=0.30, cut=1000, bpm=60, pulse=0.18, piano=0.16),
    "slipping": dict(chords=Dm, cl=10, pad=0.26, cut=900, bpm=0, pulse=0, piano=0.20),
    "window": dict(chords=HOPE, cl=6, pad=0.32, cut=1500, bpm=0, pulse=0, piano=0.18),
    "_chapter6": dict(chords=Dm, cl=8, pad=0.28, cut=1000, bpm=0, pulse=0),
    "futures": dict(chords=Dm, cl=6, pad=0.32, cut=1200, bpm=70, pulse=0.18),
    "conc_cbo": dict(chords=Dm, cl=6, pad=0.36, cut=1500, bpm=76, pulse=0.28),
    "final": dict(chords=[[50, 57, 62, 66], [45, 57, 61, 64], [50, 57, 62, 66]], cl=4, pad=0.42, cut=1800, bpm=0,
                  pulse=0),
    "outro": dict(chords=WARM, cl=6, pad=0.30, cut=1800, bpm=0, pulse=0, piano=0.16),
    "_end": dict(chords=WARM, cl=6, pad=0.26, cut=1600, bpm=0, pulse=0, piano=0.10),
}

PIANO_NOTES = [62, 65, 69, 72, 69, 65]


def seg_key(s):
    if s["name"] == "_chapter":
        return f"_chapter{s['chapter']}"
    return s["name"]


def render_music(tl):
    total = int((tl["duration"] + 1) * SR)
    mus = np.zeros(total, np.float32)
    segs = tl["segments"]
    units = {u["idx"]: u for u in tl["units"]}
    # merge consecutive segments sharing parameters into regions
    regions, cur = [], None
    for s in segs:
        p = CUES.get(seg_key(s))
        if p is not None or cur is None:
            p = p or CUES["title40"]
            cur = {"p": p, "start": s["start"], "end": s["end"], "segs": [s]}
            regions.append(cur)
        else:
            cur["end"] = s["end"]
            cur["segs"].append(s)
    XF = 1.2
    T = tl.get("tempo", 1.0)
    for r in regions:
        p = dict(r["p"])
        p["cl"] = p["cl"] / T
        if p.get("bpm"):
            p["bpm"] = p["bpm"] * T
        a0 = max(0.0, r["start"] - XF / 2)
        a1 = r["end"] + XF / 2
        d = a1 - a0
        x = np.zeros(int(d * SR), np.float32)
        if p.get("pad", 0):
            x += pad(d, p["chords"], p["cl"], p["cut"]) * p["pad"]
        if p.get("bpm") and p.get("pulse"):
            x[: int(d * SR)] += pulse(d, p["bpm"])[: len(x)] * p["pulse"]
        if p.get("tick"):
            x += ticks(d, p["bpm"] or 90, p["tick"])[: len(x)]
        if p.get("piano"):
            x += piano(d, PIANO_NOTES, 60 / 40 / T, p["piano"])[: len(x)]
        if p.get("thin"):
            x += thin(d, p["thin"])
        if p.get("drone"):
            x += drone(d, 38, p["drone"])
        if "cut_at" in p:
            # hard cut to silence when the given narration unit of the region's first segment begins
            seg = r["segs"][0]
            u = units[seg["units"][p["cut_at"]]]
            ci = int((u["start"] - 0.05 - a0) * SR)
            x[ci:] = 0
            pass
        fi = int(XF * SR)
        ramp = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
        if r["start"] > 0:
            x[:fi] *= ramp
        if "cut_at" not in p:
            x[-fi:] *= ramp[::-1]
        i0 = int(a0 * SR)
        mus[i0:i0 + len(x)] += x[: total - i0]
    # Part 1 build: gently raise the level across the chapter ("the faster it spins")
    ch = [s for s in segs if s["chapter"] == 1 and s["name"] != "_chapter"]
    if ch:
        a, b = int(ch[0]["start"] * SR), int(ch[-1]["end"] * SR)
        mus[a:b] *= np.linspace(0.8, 1.25, b - a).astype(np.float32)
    # Conclusion build into the final line
    ch = [s for s in segs if s["name"] in ("futures", "conc_cbo")]
    if ch:
        a, b = int(ch[0]["start"] * SR), int(ch[-1]["end"] * SR)
        mus[a:b] *= np.linspace(0.85, 1.3, b - a).astype(np.float32)
    return mus


def render_sfx(tl):
    total = int((tl["duration"] + 1) * SR)
    fx = np.zeros(total, np.float32)
    units = {u["idx"]: u for u in tl["units"]}

    def put(sig, t):
        i = int(t * SR)
        if i < 0:
            sig, i = sig[-i:], 0
        fx[i:i + len(sig)] += sig[: total - i]

    for s in tl["segments"]:
        n = s["name"]
        if n == "title40":
            put(sfx_hit(1.0), s["start"] + 0.9)
        if n in ("_chapter", "_title"):
            put(sfx_riser(), s["start"] - 1.5)
            put(sfx_hit(0.55), s["start"] + 0.05)
        if n in ("door1", "door2", "door3"):
            put(sfx_whoosh(), s["start"] + 0.15)
        if n == "downgrades":
            us = [units[i] for i in s["units"]]
            txt = us[0]["text"]
            put(sfx_hit(0.75), us[0]["start"] + (us[0]["end"] - us[0]["start"]) * txt.find("S&P") / len(txt))
            put(sfx_hit(0.75), us[1]["start"])
            put(sfx_hit(0.85), us[2]["start"])
        if n == "trust":
            u = units[s["units"][2]]
            put(sfx_crack(), u["start"] + (u["end"] - u["start"]) * u["text"].find("all at once") / len(u["text"]))
        if n == "safe":
            put(sfx_hit(0.6), units[s["units"][1]]["start"] - 0.02)
        if n in ("outlays",):
            for k in range(1, 5):
                put(sfx_tick(0.18), units[s["units"][k]]["start"])
        if n == "rome_coin":
            put(sfx_coin(), s["start"] + 0.25)
        if n == "rome_edict" and len(s["units"]) > 2:
            put(sfx_hit(0.45), units[s["units"][2]]["start"] - 0.02)
        if n == "record2030":
            put(sfx_hit(0.5), units[s["units"][0]]["start"] + 0.5)
        if n == "uk":
            put(sfx_hit(0.6), units[s["units"][5]]["start"])
    return fx


def narration(tl):
    total = int((tl["duration"] + 1) * SR)
    vo = np.zeros(total, np.float32)
    for u in tl["units"]:
        x, sr = sf.read(HERE / u["file"], dtype="float32")
        assert sr == SR
        i = int(u["start"] * SR)
        vo[i:i + len(x)] += x[: total - i]
    return vo


def envelope(x, win=0.05):
    # running means of squares can dip a hair below zero in silence; clamp before the root
    return np.sqrt(np.maximum(uniform_filter1d(x.astype(np.float64) ** 2, int(win * SR)), 0.0))


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-9))


def compress(x, thr_db, ratio, win=0.02, smooth=0.04):
    """RMS compressor with zero-latency smoothing (offline, so the gain can anticipate)."""
    level = db(envelope(x, win))
    gr = -np.maximum(0.0, level - thr_db) * (1 - 1 / ratio)
    gr = uniform_filter1d(gr, int(smooth * SR))
    return (x * 10 ** (gr / 20)).astype(np.float32)


def limit(x, ceiling, look=0.006, true_peak=False):
    """Look-ahead brickwall limiter: gain never exceeds what the loudest nearby sample needs.
    With true_peak, peaks are detected on a 4x oversampled signal (inter-sample peaks, BS.1770)."""
    n = int(look * SR)
    pk = np.abs(x)
    if true_peak:
        pk = np.abs(resample_poly(x.astype(np.float32), 4, 1)).reshape(-1, 4).max(axis=1)[: len(x)]
    g = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    g = minimum_filter1d(g, 2 * n + 1)
    g = uniform_filter1d(uniform_filter1d(g, n + 1), n + 1)   # stays below the needed gain at every peak
    return (x * g).astype(np.float32)


def voice_chain(vo):
    """Narration dynamics for consistent level on phones and laptops:
    anti-imaging low-pass (TTS clips were upsampled from 24 kHz), 3:1 compression above -24 dB,
    then ~6 dB of drive into a true-peak limiter (about 1 dB of reduction on the loudest 5% of speech)."""
    v = sosfiltfilt(butter(10, 11000, fs=SR, output="sos"), vo).astype(np.float32)
    v = compress(v / (np.max(np.abs(v)) + 1e-9), thr_db=-24, ratio=3, win=0.02, smooth=0.05)
    v = v / (np.max(np.abs(v)) + 1e-9)
    v = limit(v * 10 ** (6 / 20), 10 ** (-1 / 20), true_peak=True)
    return v / (np.max(np.abs(v)) + 1e-9) * 0.89


def master(x, target_lufs, ceiling_db=-1.5, tries=5):
    """Reach a target integrated loudness (EBU R128 / ITU-R BS.1770) under a peak ceiling:
    gain plus look-ahead limiting, re-measured until within 0.1 LU."""
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    ceiling = 10 ** (ceiling_db / 20)
    g = target_lufs - meter.integrated_loudness(x.astype(np.float64))
    y = x
    for _ in range(tries):
        y = limit(x * 10 ** (g / 20), ceiling, true_peak=True)
        L = meter.integrated_loudness(y.astype(np.float64))
        if abs(L - target_lufs) < 0.1:
            break
        g += target_lufs - L
    return y.astype(np.float32)


def mix(tl):
    vo_raw = narration(tl)
    vo = voice_chain(vo_raw)
    mus = render_music(tl)
    fx = render_sfx(tl)
    # ducking: music sits ~9 dB lower while the narrator speaks (smooth attack/release)
    env = (envelope(vo_raw) > 0.01).astype(np.float32)
    env = uniform_filter1d(uniform_filter1d(env, int(0.18 * SR)), int(0.18 * SR))
    duck = 1.0 - 0.62 * np.clip(env * 1.4, 0, 1)
    # [pause] beats: music falls to near-silence (cold open) or dips (elsewhere)
    gate = np.ones_like(mus)
    for a, b in tl["pauses"]:
        i, j = int(a * SR), int(b * SR)
        depth = 0.12 if a < 70 else 0.35
        r = int(0.25 * SR)
        g = np.full(j - i, depth, np.float32)
        g[:r] = np.linspace(1, depth, r)
        g[-r:] = np.linspace(depth, 1, r)
        gate[i:j] = np.minimum(gate[i:j], g)
    music_bus = mus * duck * gate * 0.55
    out = vo * 1.0 + music_bus + fx * 0.6
    out = hp(out, 30)
    # final safety limiter: catches SFX transients so loudness normalisation is not peak-bound
    out = out / (np.max(np.abs(vo)) + 1e-9) * 0.89
    out = limit(out, 0.89)
    return out.astype(np.float32), vo, (music_bus + fx * 0.6).astype(np.float32)


def write_all(tl):
    """Mix, master to -14 LUFS (YouTube reference), and write the deliverable stems."""
    out, vo, bed = mix(tl)
    for name, sig in (("mix", out), ("voice", vo), ("bed", bed)):
        if not np.all(np.isfinite(sig)):
            raise ValueError(f"non-finite samples in {name} bus")
    b = HERE / "build"
    sf.write(b / "mix_raw.wav", out, SR, subtype="FLOAT")
    sf.write(b / "mix_final.wav", master(out, -14.0), SR, subtype="FLOAT")
    sf.write(b / "voiceover.wav", master(vo, -16.0), SR, subtype="FLOAT")
    sf.write(b / "music_sfx_stem.wav", bed / (np.max(np.abs(bed)) + 1e-9) * 0.9, SR, subtype="FLOAT")
    return len(out) / SR


if __name__ == "__main__":
    tl = json.loads((HERE / "build" / "timeline.json").read_text())
    print("mixed", write_all(tl), "s")
