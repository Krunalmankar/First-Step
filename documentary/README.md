# SimpleMoney documentary: "Could the United States Collapse Because of Its Debt?"

A complete, reproducible production of the documentary in the master prompt (12 min 33 s). Code generates
everything: the narration, the original score and sound design, every motion graphic and chart, the subtitles,
the production sheet and the YouTube description. Edit the script or a number, run one command, and the whole
film re-times itself to the new narration.

## Deliverables

| # | Deliverable (from the brief) | File |
|---|---|---|
| 1 | Final documentary: 1920×1080, 24 fps, H.264 + AAC 256 kb/s, -14 LUFS / -1.4 dBTP, English subtitle track | `output/Could the United States Collapse Because of Its Debt.mp4` |
| 2 | Complete voiceover, timed to picture | `output/voiceover_narration.mp3` |
| 3 | Synchronised subtitles | `output/Could the United States Collapse Because of Its Debt.en.srt` |
| 4 | Editable project / timeline | `script.txt` (script plus markup), `output/timeline.json` (every sentence, scene and pause with timecodes), and the Python sources |
| 5 | Sentence-by-sentence production sheet | `output/production_sheet.csv` |
| 6 | Research sources with dates and links | `SOURCES.md`; description-ready copy in `output/youtube_description.txt` |
| 7 | Asset register with licence information | `ASSET_REGISTER.md` |
| 8 | Original graphics and audio assets | `output/graphics/` (one still per scene), `output/music_sfx_stem.mp3` (score + SFX, timed to picture) |

## How it works

```
script.txt ──► script_data.py ──► tts.py ──► timeline.py ──► audio.py ──► render.py ──► build.py
 (approved    (chapters, scenes,  (one clip   (gaps, pauses,  (score, SFX,  (one scene    (mux, SRT, sheet,
  script +     sentences, speed)   per        chapter cards,  ducking,      per segment,  description)
  markup)                          sentence)  scene bounds)   mastering)    in parallel)
```

- **`script.txt`**: the approved script, one sentence per line, verbatim. `@ scene` lines assign visuals,
  `{s=0.9}` sets per-sentence delivery speed, `[pause]` is a 1.4 s silent beat that is never spoken, and `~`
  marks the narrated sub-chapter titles ("Door number one…").
- **`normalize.py`** turns figures into natural speech: "$1.14 trillion" → "one point one four trillion
  dollars", "£45 billion" → "forty-five billion pounds", "5.31%" → "five point three one percent", plus dates and
  years.
- **`scenes.py`**: one renderer per scene. Every build is keyed to the moment its words are spoken.
  **`gfx.py`** holds the visual identity (charcoal / white / muted blue, one vermilion accent; Inter typeface).
- **`data.py`**: every on-screen figure and its source line.
- **`audio.py`**: the original score (per-scene cues following the brief's music direction), synthesised SFX,
  ducking under narration, near-silence on `[pause]`, a hard cut on "Not quite.", and the narration chain
  (anti-imaging low-pass, 3:1 compression, true-peak limiting), mastered to -14 LUFS.
- **`qa.py`**: the brief's final checks. Narration vs the approved script word for word
  (`approved_script.txt`, extracted from the brief PDF), timeline integrity, streams, duration, black frames,
  silences and loudness.

## Rebuild

```bash
pip install kokoro-onnx soundfile scipy numpy pillow pyloudnorm edge-tts
# Kokoro model files (Apache-2.0) go in build/models/ (or set KOKORO_MODELS):
#   https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
#   https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
python3 build.py                               # full build, ~15-20 min on 4 cores
python3 build.py --skip-tts                    # reuse cached narration clips
python3 build.py --skip-tts --reuse-video      # re-mix and re-mux only
python3 render.py stills 0.9                   # review PNGs of every scene at 90% of its duration
python3 qa.py                                  # run the checks
```

### Switching to the Andrew voice (as specified in the brief)

The brief asks for Microsoft Neural TTS **en-US-AndrewNeural**. This build environment's network policy
blocked the speech service (`speech.platform.bing.com`), so the narration here uses the offline neural model
**Kokoro-82M (voice `am_michael`)**. The pipeline already supports Andrew:

```bash
python3 build.py --backend edge   # synthesises every sentence with en-US-AndrewNeural and re-times the film
```

Pacing, pauses, chapter-specific speed, subtitles and the full picture edit re-time automatically from the new
clip lengths. Kokoro has no emotion or style controls, so chapter delivery is shaped through per-sentence speed
and timing. For a monetised channel, render Andrew through your own Azure AI Speech resource (see
`ASSET_REGISTER.md`).

## Before publishing

1. Re-verify the figures flagged in `SOURCES.md` (this sandbox could not reach Treasury, CBO, FRED or IMF to
   re-check them), including the "every auction has found buyers" line.
2. Optionally swap in the Andrew voice (above).
3. Tick YouTube's altered/synthetic-content disclosure for the AI narration.

## Format notes

- 1920×1080 at 24 fps. I didn't render 4K here because of the compute budget. `W, H` in `gfx.py` set the
  canvas, but the layout coordinates are in 1080p pixels, so a 4K master needs a scale factor added to `gfx.py`.
- Every number graphic carries its source and period. Scenarios, projections and estimates are tagged on
  screen (SCENARIO, PROJECTION, ESTIMATE, "A POSSIBLE PATH — NOT A PREDICTION").
- The cut uses no third-party footage, photos, music or logos. See `ASSET_REGISTER.md` for verified
  public-domain visuals an editor could add.
