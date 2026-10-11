"""Parse script.txt into chapters, scenes and narration units."""
import re
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).parent
TAG = re.compile(r"\s*\{([a-z])=([^}]*)\}")


@dataclass
class Unit:
    idx: int            # narration unit number (0-based); -1 for pauses
    kind: str           # "say" | "title" | "pause"
    text: str           # exact on-screen / subtitle text (no markup)
    speed: float
    chapter: int
    scene: str
    para_break: bool = False   # a blank line preceded this unit
    marked: str = ""           # text with *emphasis* markup, for the voice
    emotion: str = "neutral"   # expressive.py preset
    rise: bool = False         # question that lifts at the end
    pre_gap: float = 0.0       # extra silence before the line (s)
    para_pos: int = 0          # 1 = first sentence of a paragraph, 2 = last, 0 = otherwise / single
    new: bool = False          # added after the approved script (documented in SCRIPT_CHANGES.md)
    base_speed: float = 1.0    # delivery speed before the global tempo


@dataclass
class Chapter:
    num: int
    title: str
    speed: float
    emotion: str = "neutral"


@dataclass
class Script:
    chapters: list = field(default_factory=list)
    units: list = field(default_factory=list)
    tempo: float = 1.0         # global pace ("!tempo 1.15"): narration speed, pauses and animation


def load(path=HERE / "script.txt") -> Script:
    sc = Script()
    chap = scene = None
    blank = False
    n = 0
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if line.startswith("## "):
            num, title, spd, *emo = [p.strip() for p in line[3:].split("|")]
            chap = Chapter(int(num), title, float(spd), emo[0] if emo else "neutral")
            sc.chapters.append(chap)
            blank = False
            continue
        if not line:
            blank = True
            continue
        if line.startswith("!tempo"):
            sc.tempo = float(line.split()[1])
            continue
        if line.startswith("#"):
            continue
        if line.startswith("@ "):
            scene = line[2:].strip()
            continue
        if line == "[pause]":
            sc.units.append(Unit(-1, "pause", "", 0, chap.num, scene))
            blank = False
            continue
        kind = "say"
        if line.startswith("~ "):
            kind, line = "title", line[2:]
        tags = dict(TAG.findall(line))
        marked = TAG.sub("", line).strip()
        base = float(tags.get("s", chap.speed))
        sc.units.append(Unit(n, kind, marked.replace("*", ""), base * sc.tempo, chap.num, scene,
                             blank, marked, tags.get("e", chap.emotion), tags.get("q") == "rise",
                             float(tags.get("g", 0)), new="n" in tags, base_speed=base))
        n += 1
        blank = False
    # paragraph position: a paragraph starts after a blank line, a scene change or a chapter change
    says = [u for u in sc.units if u.kind != "pause"]
    starts = [i == 0 or u.para_break or u.scene != says[i - 1].scene or u.chapter != says[i - 1].chapter
              for i, u in enumerate(says)]
    for i, u in enumerate(says):
        first, last = starts[i], i + 1 == len(says) or starts[i + 1]
        u.para_pos = 0 if first and last else 1 if first else 2 if last else 0
    return sc


if __name__ == "__main__":
    s = load()
    print(len(s.chapters), "chapters,", sum(u.kind != "pause" for u in s.units), "narration units,",
          sum(u.kind == "pause" for u in s.units), "pauses,", len({u.scene for u in s.units}), "scenes")
    print("tempo", s.tempo, ";", sum(u.new for u in s.units), "added lines;",
          sum(len(u.text.split()) for u in s.units), "words;", sum(u.marked.count("*") // 2 for u in s.units if u.marked),
          "emphasis marks; emotions:", sorted({u.emotion for u in s.units if u.kind != "pause"}))
