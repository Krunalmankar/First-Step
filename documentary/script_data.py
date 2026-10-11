"""Parse script.txt into chapters, scenes and narration units."""
import re
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).parent


@dataclass
class Unit:
    idx: int            # narration unit number (0-based); -1 for pauses
    kind: str           # "say" | "title" | "pause"
    text: str           # exact on-screen / subtitle text
    speed: float
    chapter: int
    scene: str
    para_break: bool = False   # a blank line preceded this unit


@dataclass
class Chapter:
    num: int
    title: str
    speed: float


@dataclass
class Script:
    chapters: list = field(default_factory=list)
    units: list = field(default_factory=list)


def load(path=HERE / "script.txt") -> Script:
    sc = Script()
    chap = scene = None
    blank = False
    n = 0
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if line.startswith("## "):
            num, title, spd = [p.strip() for p in line[3:].split("|")]
            chap = Chapter(int(num), title, float(spd))
            sc.chapters.append(chap)
            blank = False
            continue
        if not line:
            blank = True
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
        speed = chap.speed
        m = re.search(r"\s*\{s=([\d.]+)\}\s*$", line)
        if m:
            speed = float(m.group(1))     # per-sentence override replaces the chapter's base speed
            line = line[: m.start()]
        sc.units.append(Unit(n, kind, line, speed, chap.num, scene, blank))
        n += 1
        blank = False
    return sc


if __name__ == "__main__":
    s = load()
    print(len(s.chapters), "chapters,", sum(u.kind != "pause" for u in s.units), "narration units,",
          sum(u.kind == "pause" for u in s.units), "pauses,", len({u.scene for u in s.units}), "scenes")
    print(sum(len(u.text.split()) for u in s.units), "words")
