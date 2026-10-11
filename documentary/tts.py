"""Generate one narration clip per script unit.

Backends:
  edge    Microsoft Neural TTS, en-US-AndrewNeural (the voice the brief asks for).
          Needs network access to speech.platform.bing.com.
  kokoro  Kokoro-82M (Apache-2.0), voice am_michael, runs offline. Used when Andrew is unreachable.

Usage: python3 tts.py [--backend edge|kokoro]
Clips are cached in build/tts/<backend>/ keyed by text+speed, so re-runs only synthesise changes.
"""
import argparse
import asyncio
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

import script_data
from normalize import normalize

HERE = Path(__file__).parent
SR = 48000
MODELS = Path(__import__("os").environ.get("KOKORO_MODELS", HERE / "build" / "models"))

# Phoneme-level fixes for words the Kokoro G2P gets wrong.
PHONEME_FIXES = [("tɹˈɪpəl ɐ", "tɹˈɪpəl ˈeɪ"), ("pɹˈɑːdʒɛkts", "pɹədʒˈɛkts")]  # triple-A; "projects" as a verb


def key(text, speed):
    return hashlib.sha1(f"{text}|{speed:.3f}".encode()).hexdigest()[:16]


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

    def __init__(self):
        from kokoro_onnx import Kokoro
        self.k = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))

    def synth(self, text, speed, out):
        ph = self.k.tokenizer.phonemize(text, "en-us")
        for a, b in PHONEME_FIXES:
            ph = ph.replace(a, b)
        audio, sr = self.k.create(ph, voice=self.voice, speed=speed, is_phonemes=True)
        sf.write(out, resample(audio.astype(np.float32), sr), SR)


class EdgeBackend:
    name = "edge"
    voice = "en-US-AndrewNeural"

    def synth(self, text, speed, out):
        import edge_tts
        mp3 = str(out) + ".mp3"
        rate = f"{round((speed - 1) * 100):+d}%"
        asyncio.run(edge_tts.Communicate(text, self.voice, rate=rate).save(mp3))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp3, "-ac", "1", "-ar", str(SR), str(out)], check=True)
        Path(mp3).unlink()


def run(backend_name):
    be = EdgeBackend() if backend_name == "edge" else KokoroBackend()
    outdir = HERE / "build" / "tts" / be.name
    outdir.mkdir(parents=True, exist_ok=True)
    sc = script_data.load()
    manifest = []
    for u in sc.units:
        if u.kind == "pause":
            continue
        spoken = normalize(u.text)
        k = key(spoken, u.speed)
        raw = outdir / f"{k}.raw.wav"
        clip = outdir / f"{k}.wav"
        if not clip.exists():
            be.synth(spoken, u.speed, raw)
            x, _ = sf.read(raw, dtype="float32")
            x = trim(x)
            x = x / (np.max(np.abs(x)) + 1e-9) * 0.89  # consistent peak level per clip
            sf.write(clip, x, SR)
            raw.unlink()
            print(f"[{u.idx:03d}] {len(x)/SR:5.2f}s  {u.text[:70]}")
        manifest.append({"idx": u.idx, "text": u.text, "spoken": spoken, "speed": u.speed,
                         "file": str(clip.relative_to(HERE)), "dur": sf.info(clip).duration})
    (HERE / "build" / f"tts_{be.name}.json").write_text(json.dumps({"voice": be.voice, "units": manifest}, indent=1))
    print("total speech", round(sum(m["dur"] for m in manifest), 1), "s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="kokoro", choices=["edge", "kokoro"])
    run(ap.parse_args().backend)
