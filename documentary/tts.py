"""Generate one narration clip per script unit.

Backends:
  kokoro  Kokoro-82M (Apache-2.0), voice am_michael, runs offline, with expressive prosody:
          emotion presets, word emphasis and intonation shaping (expressive.py, prosody_model.py).
          --flat renders the model's default delivery instead (for A/B comparison).
  edge    Microsoft Neural TTS, en-US-AndrewNeural (the voice the brief asks for). Needs network access
          to speech.platform.bing.com. Emotion presets map to its rate/pitch controls; word emphasis is
          not available through that service.

Usage: python3 tts.py [--backend kokoro|edge] [--flat]
Clips are cached in build/tts/<backend>/ keyed by everything that affects the sound.
"""
import argparse
import asyncio
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

import expressive
import script_data
from normalize import normalize

HERE = Path(__file__).parent
SR = 48000
MODELS = Path(__import__("os").environ.get("KOKORO_MODELS", HERE / "build" / "models"))

# Phoneme-level fixes for words the Kokoro G2P gets wrong.
PHONEME_FIXES = [("tɹˈɪpəl ɐ", "tɹˈɪpəl ˈeɪ"),          # triple-A
                 ("pɹˈɑːdʒɛkts", "pɹədʒˈɛkts"),         # "projects" as a verb
                 ("dɪəklˈɛʃən", "dˌaɪəklˈiːʃən")]       # Diocletian

# Delivery level per emotion (dB after per-clip peak normalisation): quiet lines sit back, urgent ones lean in.
LEVEL_DB = {"pointed": -2.0, "creeping": -1.5, "grave": -1.0, "reflective": -1.0, "heavy": -0.5,
            "urgent": 0.8, "warm": 0.3}


def key(*parts):
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:16]


def resample(x, sr_in):
    """Band-limited polyphase resampling (no imaging above the source Nyquist)."""
    if sr_in == SR:
        return x
    from math import gcd
    g = gcd(SR, sr_in)
    from scipy.signal import resample_poly
    return resample_poly(x, SR // g, sr_in // g).astype(np.float32)


def trim(x, thresh=0.004):
    idx = np.where(np.abs(x) > thresh)[0]
    if not len(idx):
        return x
    a = max(0, idx[0] - int(0.02 * SR))
    b = min(len(x), idx[-1] + int(0.06 * SR))
    return x[a:b]


class KokoroBackend:
    name = "kokoro"
    voice = "am_michael"

    def __init__(self, flat=False):
        import onnxruntime as ort
        from kokoro_onnx import Kokoro
        self.flat = flat
        self.k = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
        self.pack = self.k.get_voice_style(self.voice)
        model = MODELS / "kokoro-v1.0-prosody.onnx"
        if not model.exists():
            import prosody_model
            prosody_model.build()
        self.sess = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])

    def cache_key(self, u):
        if self.flat:
            return key("flat", normalize(u.text), f"{u.speed:.3f}")
        return key(expressive.VERSION, u.marked, f"{u.speed:.3f}", u.emotion, u.rise, u.para_pos)

    def synth(self, u, out):
        if self.flat:
            ph = self.k.tokenizer.phonemize(normalize(u.text), "en-us")
            for a, b in PHONEME_FIXES:
                ph = ph.replace(a, b)
            audio, sr = self.k.create(ph, voice=self.voice, speed=u.speed, is_phonemes=True)
        else:
            audio, _ = expressive.synthesise(self.sess, self.k.tokenizer, self.pack, u.marked, u.speed, u.emotion,
                                             PHONEME_FIXES, u.para_pos, rise=u.rise)
            sr = 24000
        sf.write(out, resample(audio.astype(np.float32), sr), SR)


class EdgeBackend:
    name = "edge"
    voice = "en-US-AndrewNeural"
    flat = False

    def cache_key(self, u):
        return key(normalize(u.text), f"{u.speed:.3f}", u.emotion)

    def synth(self, u, out):
        import edge_tts
        mp3 = str(out) + ".mp3"
        p = expressive.preset(u.emotion)
        rate = f"{round((u.speed - 1) * 100):+d}%"
        pitch = f"{round(p['shift'] * 6):+d}Hz"          # ~6 Hz per semitone around this voice's register
        asyncio.run(edge_tts.Communicate(normalize(u.text), self.voice, rate=rate, pitch=pitch).save(mp3))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp3, "-ac", "1", "-ar", str(SR), str(out)], check=True)
        Path(mp3).unlink()


def run(backend_name, flat=False):
    be = EdgeBackend() if backend_name == "edge" else KokoroBackend(flat)
    outdir = HERE / "build" / "tts" / be.name
    outdir.mkdir(parents=True, exist_ok=True)
    sc = script_data.load()
    manifest = []
    for u in sc.units:
        if u.kind == "pause":
            continue
        k = be.cache_key(u)
        raw = outdir / f"{k}.raw.wav"
        clip = outdir / f"{k}.wav"
        if not clip.exists():
            be.synth(u, raw)
            x, _ = sf.read(raw, dtype="float32")
            x = trim(x)
            gain = 0.89 * 10 ** (0 if be.flat else LEVEL_DB.get(u.emotion, 0.0) / 20)
            x = x / (np.max(np.abs(x)) + 1e-9) * gain
            sf.write(clip, x, SR)
            raw.unlink()
            print(f"[{u.idx:03d}] {len(x)/SR:5.2f}s  {u.emotion:14s} {u.text[:60]}", flush=True)
        manifest.append({"idx": u.idx, "text": u.text, "spoken": normalize(u.text), "speed": u.speed,
                         "emotion": "flat" if be.flat else u.emotion, "marked": u.marked, "rise": u.rise,
                         "file": str(clip.relative_to(HERE)), "dur": sf.info(clip).duration})
    meta = {"voice": be.voice, "expressive": not be.flat, "units": manifest}
    (HERE / "build" / f"tts_{be.name}.json").write_text(json.dumps(meta, indent=1))
    print("total speech", round(sum(m["dur"] for m in manifest), 1), "s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="kokoro", choices=["edge", "kokoro"])
    ap.add_argument("--flat", action="store_true", help="model's default delivery (no expressive shaping)")
    a = ap.parse_args()
    run(a.backend, a.flat)
