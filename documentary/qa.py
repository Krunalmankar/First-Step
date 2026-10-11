"""Quality checks from section 13 of the brief.

    python3 qa.py [path/to/approved_script.txt]   (defaults to the copy extracted from the brief PDF)

1. Narration vs approved script: the narrated units in script.txt, joined in order, must reproduce the
   approved script word for word (headings and the production note excluded; [pause] beats included).
2. Timeline integrity: every unit has audio, no overlaps, pauses never voiced, scenes cover the whole
   running time without gaps, chapters in order.
3. Output checks (if the MP4 exists): streams, duration, black frames, long silences, loudness.
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

import script_data

HERE = Path(__file__).parent
OUT = HERE / "output"
MP4 = OUT / "Could the United States Collapse Because of Its Debt.mp4"
ok = True


def fail(msg):
    global ok
    ok = False
    print("  FAIL:", msg)


def norm(s):
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'").replace("…", "...")
    return re.sub(r"\s+", " ", s).strip()


def tokens(s):
    s = norm(s).replace("[pause]", " PAUSE ")
    return s.split()


def check_script(src_path):
    print("1. Narration vs approved script")
    sc = script_data.load()
    src = norm(Path(src_path).read_text())
    start = src.find("30 September 2026.")
    src = src[start + len("30 September 2026."):]
    heads = []
    for c in sc.chapters:
        heads.append("Cold open" if c.num == 0 else "Conclusion" if c.num == 6 else "Outro" if c.num == 7
                     else f"Part {c.num}: {c.title}")
    for h in heads:
        if h not in src:
            fail(f"heading not found in source: {h!r}")
        src = src.replace(h, " ", 1)
    # approved sentences must match the brief exactly; lines added later are tracked separately
    ours = " ".join("[pause]" if u.kind == "pause" else u.text for u in sc.units if not u.new)
    a, b = tokens(src), tokens(ours)
    diffs = [op for op in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if op[0] != "equal"]
    for tag, i1, i2, j1, j2 in diffs:
        fail(f"{tag}: source {' '.join(a[i1:i2])!r} vs narration {' '.join(b[j1:j2])!r}")
    for u in sc.units:
        if u.kind != "pause" and re.search(r"[*{}]", u.text):
            fail(f"delivery markup leaked into on-screen text of unit {u.idx}: {u.text!r}")
        if u.kind != "pause" and u.marked.replace("*", "") != u.text:
            fail(f"emphasis markup changes the words of unit {u.idx}")
    added = [u for u in sc.units if u.new]
    log = (HERE / "SCRIPT_CHANGES.md").read_text() if (HERE / "SCRIPT_CHANGES.md").exists() else ""
    for u in added:
        if u.text not in log:
            fail(f"added line {u.idx} is not documented in SCRIPT_CHANGES.md: {u.text!r}")
    n_sent = len(re.findall(r"[.?!](?=\s|$|\")", re.sub(r"\.\.\.", "…", ours)))
    print(f"  {len(a)} source tokens, {len(b)} narration tokens, {len(diffs)} differences; "
          f"{sum(u.kind != 'pause' for u in sc.units)} narration units (~{n_sent} sentences), "
          f"{a.count('PAUSE')} [pause] beats in source / {b.count('PAUSE')} in timeline; "
          f"{len(added)} added lines, all documented" + ("" if ok else " (see failures)"))


def check_timeline():
    print("2. Timeline integrity")
    tl = json.loads((HERE / "build" / "timeline.json").read_text())
    us = tl["units"]
    for u in us:
        if not (HERE / u["file"]).exists():
            fail(f"missing audio for unit {u['idx']}")
        if "pause" in u["spoken"].lower() and "[" in u["spoken"]:
            fail(f"pause marker would be spoken in unit {u['idx']}")
    for x, y in zip(us, us[1:]):
        if y["start"] < x["end"]:
            fail(f"overlap between units {x['idx']} and {y['idx']}")
    segs = tl["segments"]
    if abs(segs[0]["start"]) > 1e-6 or abs(segs[-1]["end"] - tl["duration"]) > 1e-3:
        fail("segments do not span the full running time")
    for x, y in zip(segs, segs[1:]):
        if abs(x["end"] - y["start"]) > 1e-3:
            fail(f"gap/overlap between scenes {x['name']} and {y['name']}")
        if y["end"] <= y["start"]:
            fail(f"empty scene {y['name']}")
    chs = [u["chapter"] for u in us]
    if chs != sorted(chs):
        fail("chapters out of order")
    for a, b in tl["pauses"]:
        for u in us:
            if u["start"] < b and u["end"] > a:
                fail(f"narration overlaps a [pause] at {a:.1f}s")
    print(f"  {len(us)} units, {len(segs)} scenes, {len(tl['pauses'])} pauses, running time {tl['duration']:.1f}s "
          f"({int(tl['duration'] // 60)}:{tl['duration'] % 60:04.1f})")


def check_output():
    print("3. Output file")
    if not MP4.exists():
        print("  (no MP4 yet — skipped)")
        return
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", MP4],
                                   capture_output=True, text=True).stdout)
    kinds = {s["codec_type"]: s for s in pr["streams"]}
    v = kinds.get("video")
    print(f"  streams: {', '.join(s['codec_type'] + ':' + s['codec_name'] for s in pr['streams'])}")
    if not v or (v["width"], v["height"]) != (1920, 1080) or v["r_frame_rate"] != "24/1":
        fail("video stream is not 1920x1080 @ 24 fps")
    if "audio" not in kinds or "subtitle" not in kinds:
        fail("audio or subtitle stream missing")
    dur = float(pr["format"]["duration"])
    tl = json.loads((HERE / "build" / "timeline.json").read_text())
    if abs(dur - tl["duration"]) > 0.5:
        fail(f"duration {dur:.2f}s differs from timeline {tl['duration']:.2f}s")
    print(f"  duration {dur:.2f}s, size {MP4.stat().st_size / 1e6:.1f} MB")
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", MP4, "-vf", "blackdetect=d=0.1:pix_th=0.03",
                          "-af", "silencedetect=n=-55dB:d=2.5,ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    blacks = re.findall(r"black_start:\S+ black_end:\S+", log)
    sil = re.findall(r"silence_start: \S+", log)
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)
    print(f"  black segments: {len(blacks)}; silences >2.5s below -55 dB: {len(sil)}; "
          f"integrated loudness {I[-1] if I else '?'} LUFS; true peak {tp[-1] if tp else '?'} dBFS")
    if blacks:
        fail(f"black frames: {blacks[:3]}")
    if sil:
        fail(f"long silences at {sil[:3]}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else HERE / "approved_script.txt"
    check_script(src)
    check_timeline()
    check_output()
    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    sys.exit(0 if ok else 1)
