"""Render the timeline to video: one H.264 segment per scene (in parallel), then a lossless concat."""
import json
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

from PIL import Image

import gfx
from gfx import FPS, H, W, ease
from scenes import SCENES, Ctx

HERE = Path(__file__).parent
SEGDIR = HERE / "build" / "segments"


def load():
    return json.loads((HERE / "build" / "timeline.json").read_text())


def make_ctx(seg, units_by_idx, t):
    us = [units_by_idx[i] for i in seg["units"]]
    cues = [(u["start"] - seg["start"], u["end"] - seg["start"]) for u in us]
    return Ctx(t, seg["end"] - seg["start"], cues, [u["text"] for u in us], seg["chapter"], seg.get("extra"))


def frame(seg, units_by_idx, t):
    bg = gfx.background()
    im = bg.copy()
    d = gfx.SDraw(im)
    c = make_ctx(seg, units_by_idx, t)
    SCENES[seg["name"]](d, im, c)
    dur = c.dur
    if not seg["name"].startswith("_"):
        z = 1 + 0.022 * (t / max(dur, 1))           # slow push-in
        cw, ch = W / z, H / z
        im = im.crop(((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).resize((W, H), Image.BILINEAR)
    a = ease(t / 0.32) * ease((dur - t) / 0.28)
    if seg["name"] == "title40":
        a = ease((dur - t) / 0.28)
    if a < 1:
        im = Image.blend(bg, im, a)
    return im


def frame_range(seg):
    return round(seg["start"] * FPS), round(seg["end"] * FPS)


def render_segment(args):
    k, seg, units_by_idx = args
    out = SEGDIR / f"{k:03d}_{seg['name']}.mp4"
    f0, f1 = frame_range(seg)
    if out.exists() and out.stat().st_size > 0:
        return str(out)
    tmp = out.with_suffix(".tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "17", "-tune", "animation", "-pix_fmt", "yuv420p", "-r", str(FPS), str(tmp)],
                         stdin=subprocess.PIPE)
    for f in range(f0, f1):
        t = f / FPS - seg["start"]
        p.stdin.write(frame(seg, units_by_idx, t).tobytes())
    p.stdin.close()
    p.wait()
    tmp.rename(out)
    return str(out)


def render_all(procs=4, only=None):
    tl = load()
    SEGDIR.mkdir(parents=True, exist_ok=True)
    ub = {u["idx"]: u for u in tl["units"]}
    jobs = [(k, s, ub) for k, s in enumerate(tl["segments"]) if only is None or s["name"] in only]
    jobs.sort(key=lambda j: -(j[1]["end"] - j[1]["start"]))     # longest first for better packing
    with Pool(procs) as pool:
        for i, path in enumerate(pool.imap_unordered(render_segment, jobs)):
            print(f"  [{i + 1}/{len(jobs)}] {Path(path).name}", flush=True)
    files = sorted(SEGDIR.glob("[0-9][0-9][0-9]_*.mp4"))
    files = [f for f in files if not f.name.endswith(".tmp.mp4")]
    (SEGDIR / "list.txt").write_text("".join(f"file '{f.name}'\n" for f in files))
    out = HERE / "build" / "video_only.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(SEGDIR / "list.txt"),
                    "-c", "copy", str(out)], check=True)
    return out


def export_graphics(outdir=HERE / "output" / "graphics"):
    """Deliverable: one high-quality JPEG still per scene, taken where the scene is fully built."""
    tl = load()
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("*.jpg"):
        old.unlink()
    ub = {u["idx"]: u for u in tl["units"]}
    frac = {"_chapter": 0.6, "_title": 0.7, "_end": 0.5, "trust": 0.55, "safe": 0.95, "title40": 0.6}
    for k, s in enumerate(tl["segments"]):
        name = s["name"].lstrip("_") + (f"_{s['chapter']}" if s["name"] == "_chapter" else "")
        img = frame(s, ub, (s["end"] - s["start"]) * frac.get(s["name"], 0.93))
        img.save(outdir / f"{k:02d}_{name}.jpg", quality=92, subsampling=0, optimize=True)


def stills(names=None, frac=0.85, outdir=HERE / "build" / "stills"):
    """Write a PNG per scene at a given fraction of its duration, for review."""
    tl = load()
    outdir.mkdir(parents=True, exist_ok=True)
    ub = {u["idx"]: u for u in tl["units"]}
    for k, s in enumerate(tl["segments"]):
        if names and s["name"] not in names:
            continue
        t = (s["end"] - s["start"]) * frac
        frame(s, ub, t).save(outdir / f"{k:03d}_{s['name']}.png")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stills":
        stills(sys.argv[3:] or None, float(sys.argv[2]) if len(sys.argv) > 2 else 0.85)
    else:
        render_all()
