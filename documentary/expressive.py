"""Expressive narration on top of Kokoro: emotion presets, word emphasis and intonation shaping.

Two passes per sentence through the prosody-enabled graph (see prosody_model.py):
  1. synthesise with duration shaping only, and read back the model's own pitch (F0), energy (N)
     and per-token durations;
  2. reshape those contours, then synthesise again. The vocoder renders the new contours natively.

Shaping per sentence (all in semitones on the model's own contour, so the voice stays itself):
  * register shift and pitch-range expansion around the sentence median (the "ups and downs"),
    computed on the smoothed macro contour so natural micro-prosody is kept, not exaggerated;
  * gentle declination across the sentence, and a pitch reset at paragraph starts;
  * emphasis bumps (pitch + energy + slight lengthening) on words marked *like this* (or **strong**);
  * a settled fall at the end of statements, a lift on questions, suspension on trailing clauses;
  * longer beats on commas, colons and ellipses.
Markup lives in script.txt; the on-screen text never shows it.
"""
import re
from dataclasses import dataclass

import numpy as np

from normalize import normalize

PRESETS = {
    #                shift  range  decl  emph  fall  rise  energy  emph_dur  beat
    "neutral":       (0.0, 1.16, 1.0, 2.1, 1.2, 1.6, 0.0, 1.10, 1.30),
    "intrigue":      (-1.0, 1.18, 1.0, 2.4, 1.6, 1.8, -0.4, 1.14, 1.45),
    "pointed":       (-1.4, 0.95, 0.6, 2.2, 2.2, 1.0, -1.0, 1.18, 1.50),
    "curious":       (0.3, 1.27, 0.6, 2.3, 1.0, 2.4, 0.2, 1.10, 1.30),
    "conversational": (0.2, 1.24, 1.0, 2.3, 1.2, 2.0, 0.2, 1.10, 1.25),
    "tight":         (-0.4, 1.15, 0.8, 2.7, 1.6, 1.6, 0.3, 1.14, 1.35),
    "measured":      (-0.3, 1.12, 0.9, 2.3, 1.5, 1.6, 0.0, 1.10, 1.35),
    "heavy":         (-1.3, 1.00, 0.8, 2.3, 2.2, 1.2, -0.3, 1.22, 1.55),
    "analytical":    (-0.2, 1.16, 0.9, 2.4, 1.4, 1.8, 0.0, 1.10, 1.30),
    "urgent":        (0.6, 1.26, 0.6, 2.5, 1.0, 1.8, 0.6, 1.06, 1.15),
    "creeping":      (-0.9, 0.88, 0.5, 1.8, 1.6, 1.4, -1.0, 1.12, 1.50),
    "puzzled":       (0.4, 1.30, 0.5, 2.5, 1.0, 3.0, 0.2, 1.12, 1.40),
    "grave":         (-1.5, 0.95, 0.8, 2.3, 2.4, 1.2, -0.5, 1.20, 1.55),
    "reassuring":    (0.4, 1.25, 1.0, 2.3, 1.2, 2.0, 0.3, 1.10, 1.25),
    "reflective":    (-0.8, 1.06, 0.8, 2.0, 1.8, 1.6, -0.6, 1.14, 1.50),
    "hopeful":       (0.3, 1.26, 0.8, 2.4, 1.1, 2.2, 0.2, 1.12, 1.35),
    "decisive":      (-0.2, 1.20, 0.9, 2.6, 1.9, 1.8, 0.2, 1.16, 1.40),
    "warm":          (0.7, 1.28, 0.8, 2.3, 1.1, 2.4, 0.4, 1.10, 1.25),
}
FIELDS = ("shift", "range", "decl", "emph", "fall", "rise", "energy", "emph_dur", "beat")
VERSION = "expr-6"   # bump to invalidate cached clips when the shaping changes

PUNCT_BEATS = {",": 1.0, ";": 1.0, ":": 1.15, "—": 1.15, "…": 1.6}   # multiplied by the preset's beat


@dataclass
class Plan:
    phonemes: str
    tokens: list
    dur_scale: np.ndarray        # [S+2]
    spans: list                  # (tok_start, tok_end, strength) for emphasised segments (padded indices)
    last_word: tuple             # (tok_start, tok_end) padded indices
    ending: str                  # "." "?" "," or ""
    rise: bool = False           # question that should lift at the end (yes/no, tag, elliptical)


def preset(name):
    return dict(zip(FIELDS, PRESETS.get(name, PRESETS["neutral"])))


def strip_markup(s):
    return s.replace("**", "").replace("*", "")


def segments(marked):
    """Split '... *word* ... **phrase** ...' into (text, strength) pieces."""
    out, pos = [], 0
    for m in re.finditer(r"\*\*[^*]+\*\*|\*[^*]+\*", marked):
        if m.start() > pos:
            out.append((marked[pos:m.start()], 0))
        tok = m.group(0)
        out.append((tok[2:-2], 2) if tok.startswith("**") else (tok[1:-1], 1))
        pos = m.end()
    if pos < len(marked):
        out.append((marked[pos:], 0))
    return out


def plan(marked, tokenizer, fixes, p, rise=False):
    """Phonemise segment by segment, keeping track of which tokens each emphasis covers."""
    parts = []                                   # [phonemes, strength, length of the word part]
    for text, strength in segments(marked):
        t = normalize(text).strip()
        lead = re.match(r"^([,.;:!?…\"”’)\]]+)\s*", t)
        if lead and parts:                       # punctuation that belongs to the previous word
            parts[-1][0] += lead.group(1)        # (kept out of that word's emphasis span)
            t = t[lead.end():]
        if not t:
            continue
        ph = tokenizer.phonemize(t, "en-us").strip()
        for a, b in fixes:
            ph = ph.replace(a, b)
        core = len(ph.rstrip(".,!?;:…\"”’"))
        parts.append([ph, strength, core])
    frag, frag_spans = "", []
    for ph, strength, core in parts:
        if frag:
            frag += " "
        frag_spans.append((len(frag), len(frag) + core, strength))
        frag += ph
    # Speak the sentence phonemised in one piece (natural reductions: "a" -> ɐ, "to" -> tə), and project the
    # emphasis spans found on the fragment-wise string onto it with a character alignment.
    phon = tokenizer.phonemize(normalize(strip_markup(marked)), "en-us").strip()
    for a, b in fixes:
        phon = phon.replace(a, b)
    char_spans = [(_project(frag, phon, a), _project(frag, phon, b - 1) + 1, st) for a, b, st in frag_spans]
    vocab = tokenizer.vocab
    tok_of_char, tokens = [], []
    for ch in phon:
        tok_of_char.append(len(tokens) if ch in vocab else -1)
        if ch in vocab:
            tokens.append(vocab[ch])

    def tok_range(a, b):
        idx = [tok_of_char[i] for i in range(a, b) if tok_of_char[i] >= 0]
        return (idx[0] + 1, idx[-1] + 2) if idx else (1, 1)   # +1 for the leading pad token

    dur = np.ones(len(tokens) + 2, np.float32)
    spans = []
    for a, b, strength in char_spans:
        if strength:
            s, e = tok_range(a, b)
            spans.append((s, e, strength))
            dur[s:e] *= p["emph_dur"] ** strength
    body = phon.rstrip(" .!?\"”’")
    for i, ch in enumerate(phon[:len(body)]):            # beats on internal punctuation only
        if ch in PUNCT_BEATS and tok_of_char[i] >= 0:
            dur[tok_of_char[i] + 1] *= 1 + (p["beat"] - 1) * PUNCT_BEATS[ch]
    if "..." in phon[:len(body)]:
        for m in re.finditer(r"\.\.\.", phon[:len(body)]):
            for i in range(m.start(), m.end()):
                if tok_of_char[i] >= 0:
                    dur[tok_of_char[i] + 1] *= 1 + (p["beat"] - 1) * PUNCT_BEATS["…"]
    words = [m for m in re.finditer(r"[^\s]+", phon) if re.search(r"[^\W\d_]", m.group(0))]
    last = tok_range(words[-1].start(), words[-1].start() + len(words[-1].group(0).rstrip(".,!?;:…\"”’")))\
        if words else (1, 1)
    end_ch = phon.rstrip(" \"”’")[-1:] if phon else ""
    ending = "?" if end_ch == "?" else "," if end_ch in ",…;:" or phon.rstrip().endswith("...") else \
        "." if end_ch in ".!" else ""
    return Plan(phon, tokens, dur, spans, last, ending, rise and ending == "?")


def _project(src, dst, i):
    """Map character index i of src onto dst (strings that differ only slightly)."""
    import difflib
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, src, dst, autojunk=False).get_opcodes():
        if i1 <= i < i2:
            if tag == "equal":
                return j1 + (i - i1)
            return min(j2 - 1, j1 + int((i - i1) * (j2 - j1) / max(1, i2 - i1))) if j2 > j1 else max(0, j1 - 1)
    return len(dst) - 1


def _smooth(x, n):
    if n <= 1:
        return x
    w = np.hanning(n + 2)[1:-1]
    w /= w.sum()
    pad = np.pad(x, (n, n), mode="edge")
    return np.convolve(pad, w, mode="same")[n:-n]


def contours(pl, durations, f0, n_pred, p, para_pos=0, energy_extra=0.0):
    """Return (f0_mul, n_add) for pass 2. All pitch maths in semitones."""
    F = f0.shape[0]
    cum = np.concatenate([[0], np.cumsum(durations)]).astype(int) * 2      # token -> F0-frame boundaries

    voiced = f0 > 50

    def frames(tok_a, tok_b):
        """Frame span of tokens, tightened to its voiced part (the model parks trailing silence
        on the final phoneme, which would otherwise stretch the last word)."""
        a, b = cum[tok_a], cum[tok_b]
        v = np.where(voiced[a:b])[0]
        return (a + v[0], a + v[-1] + 1) if len(v) else (a, b)

    off = np.zeros(F)
    nadd = np.zeros(F) + p["energy"] + energy_extra
    if voiced.sum() > 8:
        st = np.zeros(F)
        st[voiced] = 12 * np.log2(f0[voiced] / 100.0)
        idx = np.arange(F)
        st_i = np.interp(idx, idx[voiced], st[voiced])                    # bridge unvoiced gaps
        macro = _smooth(st_i, 13)                                          # ~160 ms: phrase-level contour
        med = np.median(st[voiced])
        off += (p["range"] - 1.0) * (macro - med)                          # ups and downs
        first, last_v = idx[voiced][0], idx[voiced][-1]
        tn = np.clip((idx - first) / max(1, last_v - first), 0, 1)
        off += p["decl"] * (0.5 - tn)                                      # natural declination
    off += p["shift"] + {0: 0.0, 1: 0.6, 2: -0.35}.get(para_pos, 0.0)     # paragraph start reset / end settle
    for a, b, strength in pl.spans:                                        # word emphasis
        fa, fb = frames(a, b)
        width = max(fb - fa, 6)
        centre = fa + 0.42 * width
        half = 0.8 * width
        x = np.arange(F)
        w = np.clip(1 - np.abs(x - centre) / half, 0, 1)
        w = 0.5 - 0.5 * np.cos(np.pi * w)
        amp = p["emph"] * (1.0 if strength == 1 else 1.3)
        off += amp * w
        nadd += 0.9 * strength * w
    la, lb = frames(*pl.last_word)                                         # phrase-final contour
    if lb > la:
        x = np.arange(F)
        ramp = np.clip((x - la) / max(1, lb - la), 0, 1)
        ramp[x >= lb] = 1.0
        if pl.rise and voiced.sum() > 8:
            # hold the pitch reached at the start of the last word, then lift (instead of the model's fall)
            held = macro[min(la, F - 1)] - macro
            up = p["rise"] * np.clip((x - (la + 0.2 * (lb - la))) / max(1, 0.8 * (lb - la)), 0, 1)
            region = x >= la
            off[region] = (off[min(la, F - 1)] + held + up)[region]
        elif pl.ending == "?":
            pass                                            # wh-questions: keep the model's natural fall
        elif pl.ending == ".":
            off -= p["fall"] * ramp
            nadd -= 0.7 * ramp
        elif pl.ending == ",":
            off += 0.8 * ramp
    off = _smooth(off, 7)
    return (2.0 ** (off / 12.0)).astype(np.float32), nadd.astype(np.float32)


def exact_frames(target):
    """Round fractional frame counts so the running total never drifts (error diffusion), min 1 frame."""
    out, acc, done = np.zeros(len(target), np.float32), 0.0, 0
    for i, t in enumerate(target):
        acc += float(t)
        n = max(1, int(round(acc)) - done)
        out[i] = n
        done += n
    return out


def synthesise(sess, tokenizer, voice_pack, marked, speed, preset_name, fixes, para_pos=0, energy_extra=0.0,
               rise=False):
    """Three-pass expressive synthesis. Returns (audio float32 @24 kHz, info dict).
    1) read the model's unrounded durations; 2) fix exact frame counts (tempo + emphasis + beats, error-diffused)
    and read the pitch/energy predicted for that timing; 3) render with the reshaped contours."""
    p = preset(preset_name)
    pl = plan(marked, tokenizer, fixes, p, rise)
    if len(pl.tokens) > 508:
        raise ValueError("sentence too long for one Kokoro window; split it in script.txt")
    style = np.asarray(voice_pack[len(pl.tokens) - 1], np.float32).reshape(1, 256)
    feeds = {"tokens": np.array([[0, *pl.tokens, 0]], np.int64), "style": style,
             "speed": np.array([speed], np.float32)}
    neutral = {"f0_mul": np.ones((1, 1), np.float32), "n_add": np.zeros((1, 1), np.float32)}
    S = len(pl.tokens) + 2
    *_, dur_pred = sess.run(None, {**feeds, **neutral, "dur_scale": np.ones((1, S), np.float32)})
    want = exact_frames(dur_pred[0] * pl.dur_scale)
    scale = (want / np.maximum(dur_pred[0], 1e-4) * (1 + 1e-5)).astype(np.float32)[None, :]
    _, dur, f0, nn, _ = sess.run(None, {**feeds, **neutral, "dur_scale": scale})
    assert np.array_equal(dur[0], want), "exact frame counts not honoured"
    f0_mul, n_add = contours(pl, dur[0], f0[0], nn[0], p, para_pos, energy_extra)
    audio, dur2, *_ = sess.run(None, {**feeds, "dur_scale": scale, "f0_mul": f0_mul[None, :],
                                      "n_add": n_add[None, :]})
    assert np.array_equal(dur2, dur), "durations changed between passes"
    return np.asarray(audio, np.float32).ravel(), {"f0_before": f0[0], "f0_after": f0[0] * f0_mul,
                                                  "durations": dur[0], "plan": pl}
