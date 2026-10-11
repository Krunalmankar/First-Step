"""Lay every narration unit, pause, chapter card and scene on one timeline."""
import json
from pathlib import Path

import script_data

HERE = Path(__file__).parent

# base timings in seconds at tempo 1.0 (script.txt "!tempo" divides them)
_GAP_SENTENCE = 0.30
_GAP_PARAGRAPH = 0.62
_GAP_SCENE = 0.55
_PAUSE = 1.4
_CARD = 3.6
_TITLE = 5.5
_END = 6.0


def build(backend="kokoro"):
    tts = json.loads((HERE / "build" / f"tts_{backend}.json").read_text())
    clips = {m["idx"]: m for m in tts["units"]}
    sc = script_data.load()
    chap_titles = {c.num: c.title for c in sc.chapters}
    T = sc.tempo                                  # every gap, pause and card tightens with the tempo
    GAP_SENTENCE, GAP_PARAGRAPH, GAP_SCENE, PAUSE, CARD, TITLE, END = (
        x / T for x in (_GAP_SENTENCE, _GAP_PARAGRAPH, _GAP_SCENE, _PAUSE, _CARD, _TITLE, _END))

    units, segs, pauses = [], [], []
    t = 0.9 / T
    cur = {"name": "title40", "start": 0.0, "chapter": 0, "units": [], "extra": {}}
    chapter = 0
    prev_kind = None

    def close(at):
        cur["end"] = at
        segs.append(cur)

    for u in sc.units:
        if u.chapter != chapter:
            chapter = u.chapter
            t += 0.5 / T
            close(t)
            if chapter == 1:
                segs.append({"name": "_title", "start": t, "end": t + TITLE, "chapter": 0, "units": [], "extra": {}})
                t += TITLE
            if 1 <= chapter <= 6:
                segs.append({"name": "_chapter", "start": t, "end": t + CARD, "chapter": chapter, "units": [],
                             "extra": {"num": chapter, "title": chap_titles[chapter]}})
                t += CARD
            cur = None
        if u.kind == "pause":
            pauses.append((t, t + PAUSE))
            t += PAUSE
            prev_kind = "pause"
            continue
        if cur is None or u.scene != cur["name"]:
            gap = GAP_SCENE + (0.25 / T if u.para_break else 0) if cur is not None else 0.6 / T
            if prev_kind == "title":
                gap += 0.6 / T
            if cur is not None:
                close(t + gap * 0.45)
                start = t + gap * 0.45
            else:
                start = t
            cur = {"name": u.scene, "start": start, "chapter": u.chapter, "units": [], "extra": {}}
        else:
            gap = GAP_PARAGRAPH if u.para_break else GAP_SENTENCE
            if prev_kind == "title":
                gap += 0.6 / T
        if u.kind == "title":
            gap += 0.25 / T
        gap += u.pre_gap / T                 # deliberate beat before a reveal
        s = t + gap
        clip = clips[u.idx]
        e = s + clip["dur"]
        units.append({"idx": u.idx, "kind": u.kind, "text": u.text, "spoken": clip["spoken"], "speed": u.speed,
                      "emotion": clip.get("emotion", "neutral"), "marked": u.marked, "rise": u.rise,
                      "new": u.new,
                      "chapter": u.chapter, "scene": u.scene, "start": round(s, 3), "end": round(e, 3),
                      "file": clip["file"]})
        cur["units"].append(u.idx)
        t = e
        prev_kind = u.kind
    t += 1.2 / T
    close(t)
    segs.append({"name": "_end", "start": t, "end": t + END, "chapter": 7, "units": [], "extra": {}})
    t += END
    tl = {"duration": round(t, 3), "voice": tts["voice"], "backend": backend, "tempo": T, "units": units,
          "segments": [{**s, "start": round(s["start"], 3), "end": round(s["end"], 3)} for s in segs],
          "pauses": [(round(a, 3), round(b, 3)) for a, b in pauses],
          "chapters": [{"num": c.num, "title": c.title} for c in sc.chapters]}
    (HERE / "build" / "timeline.json").write_text(json.dumps(tl, indent=1))
    return tl


if __name__ == "__main__":
    tl = build()
    print("duration", tl["duration"], "s,", len(tl["segments"]), "segments")
