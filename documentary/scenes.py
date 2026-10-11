"""One renderer per scene. Each draws a single frame at local time c.t.

Scene timing comes from the narration: c.cues[i] = (start, end) of the i-th narrated unit
inside the scene, so every build is locked to the words it illustrates.
"""
import math

from PIL import Image, ImageDraw

import data as D
from gfx import *  # noqa: F401,F403

SCENES = {}
HEADERS = {0: "", 1: "Part 1 · The borrowing machine", 2: "Part 2 · Warning signs", 3: "Part 3 · Three doors",
           4: "Part 4 · Why it hasn't happened", 5: "Part 5 · Like Rome?", 6: "Conclusion", 7: ""}


class Ctx:
    def __init__(self, t, dur, cues, texts, chapter, extra=None):
        self.t, self.dur, self.cues, self.texts, self.chapter = t, dur, cues, texts, chapter
        self.extra = extra or {}

    def start(self, i):
        return self.cues[i][0] if i < len(self.cues) else self.dur

    def p(self, i, d=0.6, delay=0.0):
        """Eased 0..1 progress that begins when unit i starts."""
        return ease_out((self.t - self.start(i) - delay) / d)

    def at(self, i, sub):
        """Approximate time the substring `sub` is spoken inside unit i."""
        s, e = self.cues[i]
        txt = self.texts[i]
        k = txt.find(sub)
        return s + (e - s) * (max(k, 0) / max(1, len(txt)))

    def pa(self, i, sub, d=0.6):
        return ease_out((self.t - self.at(i, sub)) / d)

    def since(self, i):
        return self.t - self.start(i)


def scene(name):
    def deco(fn):
        SCENES[name] = fn
        return fn
    return deco


def hdr(d, c):
    h = HEADERS.get(c.chapter, "")
    if h:
        header(d, h, ease(c.t / 0.8))


# ======================================================================= cards
@scene("_chapter")
def s_chapter(d, fr, c):
    num, title = c.extra["num"], c.extra["title"]
    a = ease(c.t / 0.7) * ease((c.dur - c.t) / 0.5)
    label = "" if num == 6 else f"PART {num}"
    text(d, (W / 2, H / 2 - 92), label, 26, ACCENT, a, "SemiBold", "mm", spacing=8)
    w = 260 * ease_out((c.t - 0.2) / 1.2)
    d.line((W / 2 - w / 2, H / 2 - 50, W / 2 + w / 2, H / 2 - 50), fill=mix(DIM, a), width=2)
    if True:
        for i, ln in enumerate(wrap(title, 76, 1400, "SemiBold", True)):
            text(d, (W / 2, H / 2 + 20 + i * 92), ln, 76, WHITE, a * ease((c.t - 0.3) / 0.8), "SemiBold", "mm", True)


@scene("_title")
def s_title(d, fr, c):
    a = ease(c.t / 1.0) * ease((c.dur - c.t) / 0.6)
    text(d, (W / 2, 300), "SIMPLEMONEY", 22, GREY, a, "SemiBold", "mm", spacing=10)
    lines = ["Could the United States", "Collapse Because of Its Debt?"]
    for i, ln in enumerate(lines):
        text(d, (W / 2, 470 + i * 112), ln, 96, WHITE, a * ease((c.t - 0.4 - i * 0.3) / 0.9), "Bold", "mm", True)
    w = 520 * ease_out((c.t - 1.2) / 1.4)
    d.line((W / 2 - w / 2, 690, W / 2 + w / 2, 690), fill=mix(ACCENT, a), width=3)
    text(d, (W / 2, 760), D.AS_OF, 22, GREY, a * ease((c.t - 1.6) / 0.8), "Regular", "mm")


@scene("_end")
def s_end(d, fr, c):
    a = ease(c.t / 0.8) * ease((c.dur - c.t) / 1.2)
    text(d, (W / 2, H / 2 - 30), "SIMPLEMONEY", 54, WHITE, a, "Bold", "mm", True, spacing=14)
    d.line((W / 2 - 60, H / 2 + 26, W / 2 + 60, H / 2 + 26), fill=mix(ACCENT, a), width=3)
    text(d, (W / 2, H / 2 + 80), "Research sources are listed in the description.", 24, GREY, a, "Regular", "mm")
    text(d, (W / 2, H - 90), "Narrated with a synthetic (AI) voice · Graphics are original · "
         "Scenarios and projections are labelled", 20, GREY, a, "Regular", "mm")


# ======================================================================= cold open
@scene("title40")
def s_title40(d, fr, c):
    p = ease_out(c.since(0) / 1.6)
    val = int(round(40 * p))
    text(d, (W / 2, H / 2 - 40), f"${val}", 260, WHITE, ease(c.t / 0.4), "Bold", "mm", True)
    text(d, (W / 2, H / 2 + 130), "TRILLION", 54, ACCENT, ease((c.t - 1.1) / 0.6), "SemiBold", "mm", spacing=22)
    text(d, (W / 2, H - 70), D.AS_OF, 20, GREY, 0.8 * ease((c.t - 2.2) / 1.0), "Regular", "mm")


@scene("owes")
def s_owes(d, fr, c):
    rate = D.DEFICIT_B * 1e9 / (365 * 86400)
    v = D.DEBT_TOTAL_T * 1e12 + rate * c.t
    text(d, (W / 2, 330), "WHAT THE US GOVERNMENT OWES", 26, GREY, ease(c.t / 0.6), "SemiBold", "mm", spacing=6)
    text(d, (W / 2, 500), money(v), 128, WHITE, ease(c.t / 0.6), "SemiBold", "mm", True)
    a = c.p(1, 0.8)
    text(d, (W / 2, 640), "and still climbing", 44, ACCENT, a, "Medium", "mm")
    arrow(d, (W / 2 + 230, 660), (W / 2 + 290, 610), ACCENT, a, 4, 16)
    source(d, D.SRC_DTP + ". Counter rate illustrative (FY2026 average deficit).", ease(c.t / 1.0))


@scene("milestones")
def s_milestones(d, fr, c):
    hdr(d, c)
    x0, x1, y = 300, 1620, 560
    xs = [x0, x0 + (x1 - x0) * 5 / 10, x1]   # Oct 2025 -> Mar 2026 -> Aug 2026: five months apart each
    hline(d, x0 - 80, x0 - 80 + (x1 - x0 + 160) * ease_out(c.t / 1.2), y, LINE, 1, 3)
    shows = [ease((c.t - 0.3) / 0.6), ease((c.t - 0.8) / 0.6), c.pa(0, "crossed", 0.7)]
    for i, ((amt, when), x, a) in enumerate(zip(D.DEBT_MILESTONES, xs, shows)):
        col = ACCENT if i == 2 else WHITE
        dot(d, (x, y), 12 if i == 2 else 9, col, a)
        text(d, (x, y - 70), amt, 84 if i == 2 else 64, col, a, "SemiBold", "mm", True)
        text(d, (x, y + 56), when, 30, GREY, a, "Regular", "mm")
    a = c.p(1, 0.8)
    if a > 0:
        yb = y + 130
        d.line((xs[1], yb, xs[1] + (xs[2] - xs[1]) * a, yb), fill=mix(BLUE, a), width=3)
        d.line((xs[1], yb - 12, xs[1], yb + 12), fill=mix(BLUE, a), width=3)
        d.line((xs[2], yb - 12, xs[2], yb + 12), fill=mix(BLUE, a * ease(a * 3 - 2)), width=3)
        text(d, ((xs[1] + xs[2]) / 2, yb + 44), "+$1 trillion in about five months", 32, BLUE, a, "Medium", "mm")
    source(d, "Source: US Treasury, Debt to the Penny (total public debt outstanding)", ease(c.t))


@scene("outlays")
def s_outlays(d, fr, c):
    text(d, (MX, 190), "Federal spending, fiscal year 2026", 44, WHITE, ease(c.t / 0.6), "SemiBold", display=True)
    text(d, (MX, 250), "Outlays, $ billions", 26, GREY, ease(c.t / 0.6))
    order = {"Net interest": 1, "Defense": 2, "Medicare": 3, "Social Security": 4}
    x0, maxw, y0, rh = 470, 1180, 350, 140
    for k, (name, v) in enumerate(D.OUTLAYS):
        cue = order[name]
        a = c.p(cue, 0.5) if cue < len(c.cues) else 0
        g = ease_out((c.t - c.start(cue)) / 1.1) if cue < len(c.cues) else 0
        y = y0 + k * rh
        col = ACCENT if name == "Net interest" else (BLUE if name != "Social Security" else GREY)
        text(d, (x0 - 30, y + 30), name, 34, WHITE if a else DIM, max(a, 0.35), "Medium", "rm")
        d.rectangle((x0, y + 6, x0 + maxw, y + 56), fill=mix(PANEL, 0.6))
        if g > 0:
            d.rectangle((x0, y + 6, x0 + maxw * v / 1700 * g, y + 56), fill=mix(col, a))
            text(d, (x0 + maxw * v / 1700 * g + 18, y + 31), f"{int(v * g):,}", 34, col, a, "SemiBold", "lm")
    source(d, D.SRC_MBR, ease(c.t))


@scene("interest_counter")
def s_interest_counter(d, fr, c):
    v = D.INTEREST_PER_SEC * c.t
    text(d, (W / 2, 250), "INTEREST PAID SINCE THIS SHOT BEGAN", 24, GREY, ease(c.t / 0.6), "SemiBold", "mm", spacing=5)
    text(d, (W / 2, 390), money(v), 150, ACCENT, ease(c.t / 0.5), "SemiBold", "mm", True)
    text(d, (W / 2, 500), "≈ $36,000 every second · FY2026 average", 32, WHITE, ease((c.t - 0.6) / 0.6), "Regular", "mm")
    words = [("ROADS", 1), ("SCHOOLS", 2)]
    for j, (w, cue) in enumerate(words):
        if cue >= len(c.cues):
            continue
        a = c.p(cue, 0.4)
        x = W / 2 + (j - 1) * 420
        text(d, (x, 700), w, 60, GREY, a, "SemiBold", "mm", spacing=6)
        s = c.p(cue, 0.5, 0.35)
        hw = text_width(w, 60, "SemiBold") / 2 + 30
        if s > 0:
            d.line((x - hw, 702, x - hw + 2 * hw * s, 702), fill=mix(ACCENT, a), width=5)
    if len(c.cues) > 3:
        text(d, (W / 2 + 420, 700), "INTEREST", 60, ACCENT, c.p(3, 0.5), "Bold", "mm", spacing=6)
    source(d, "Source: CBO, Monthly Budget Review (net interest $1,143B in FY2026 ÷ seconds in a year)", ease(c.t))


@scene("question")
def s_question(d, fr, c):
    word_reveal(d, (W / 2, 430), c.texts[0], 64, c.since(0), 1.2, WHITE, "SemiBold", display=True)
    if len(c.cues) > 1:
        word_reveal(d, (W / 2, 530), c.texts[1], 52, c.since(1), 1.6, GREY, "Medium", display=True)
    if len(c.cues) > 2:
        text(d, (W / 2, 720), "Stay with me.", 40, ACCENT, c.p(2, 0.8), "Medium", "mm")


# ======================================================================= part 1
@scene("spend_list")
def s_spend_list(d, fr, c):
    hdr(d, c)
    text(d, (W / 2, 250), "Where the money goes, every year", 54, WHITE, c.p(1, 0.6) if len(c.cues) > 1 else 0,
         "SemiBold", "mm", True)
    items = ["Social Security", "Medicare", "defence", "roads", "schools", "interest"]
    labels = ["Social Security", "Medicare", "Defense", "Roads", "Schools", "Interest on the debt"]
    cw, ch, gx, gy = 480, 150, 40, 40
    x0 = (W - (3 * cw + 2 * gx)) / 2
    for k, (it, lab) in enumerate(zip(items, labels)):
        a = c.pa(1, it, 0.5) if len(c.cues) > 1 else 0
        r, col = divmod(k, 3)
        x, y = x0 + col * (cw + gx), 380 + r * (ch + gy)
        accent = k == 5
        d.rounded_rectangle((x, y, x + cw, y + ch), radius=14, fill=mix(PANEL, a),
                            outline=mix(ACCENT if accent else LINE, a), width=3 if accent else 2)
        text(d, (x + cw / 2, y + ch / 2), lab, 40, ACCENT if accent else WHITE, a, "Medium", "mm")


@scene("spend_vs")
def s_spend_vs(d, fr, c):
    hdr(d, c)
    text(d, (MX, 200), "Fiscal year 2026", 48, WHITE, ease(c.t / 0.6), "SemiBold", display=True)
    x0, maxw = 420, 1240
    a1 = ease_out(c.since(0) / 1.0)
    tb = c.at(0, "But")
    a2 = ease_out((c.t - tb) / 1.0)
    for k, (lab, v, a, col) in enumerate([("Spent", D.SPENT_T, a1, WHITE), ("Collected", D.COLLECTED_T, a2, BLUE)]):
        y = 380 + k * 190
        text(d, (x0 - 34, y + 50), lab, 44, GREY, max(a, 0.3), "Medium", "rm")
        if a > 0:
            d.rectangle((x0, y, x0 + maxw * v / 7.6 * a, y + 100), fill=mix(col, a))
            text(d, (x0 + maxw * v / 7.6 * a - 24, y + 50), f"${v * a:.1f}T", 48, INK, a, "Bold", "rm", True,
                 base=col)
    g = ease((c.t - tb - 1.4) / 0.8)
    if g > 0:
        xa, xb = x0 + maxw * D.COLLECTED_T / 7.6, x0 + maxw * D.SPENT_T / 7.6
        for yy in range(570, 670, 14):
            d.line((xa, yy, xb, yy), fill=mix(ACCENT, g * 0.7), width=2)
        d.rectangle((xa, 570, xb, 670), outline=mix(ACCENT, g), width=3)
        text(d, ((xa + xb) / 2, 730), "the gap: ≈ $2.0T", 38, ACCENT, g, "SemiBold", "mm")
    source(d, D.SRC_MBR, ease(c.t))


@scene("hundred")
def s_hundred(d, fr, c):
    hdr(d, c)
    n_fill = int(73 * ease_out(c.since(1) / 2.2)) if len(c.cues) > 1 else 0
    show = ease(c.t / 0.8)
    s, g = 48, 12
    gx = 760 - (10 * s + 9 * g) / 2
    gy = 540 - (10 * s + 9 * g) / 2
    for k in range(100):
        r, q = divmod(k, 10)
        x, y = gx + q * (s + g), gy + (9 - r) * (s + g)
        if k < n_fill:
            d.rectangle((x, y, x + s, y + s), fill=mix(BLUE, show))
        elif k >= 73 and n_fill >= 73:
            d.rectangle((x, y, x + s, y + s), outline=mix(ACCENT, show), width=3)
        else:
            d.rectangle((x, y, x + s, y + s), outline=mix(LINE, show), width=2)
    tx = 1240
    text(d, (tx, 380), "For every", 36, GREY, show)
    text(d, (tx, 420), "$100 spent", 76, WHITE, show, "SemiBold", display=True)
    a = c.p(1, 0.6, 1.0) if len(c.cues) > 1 else 0
    text(d, (tx, 560), "only", 36, GREY, a)
    text(d, (tx, 600), f"${n_fill}", 110, BLUE, a, "SemiBold", display=True)
    text(d, (tx, 740), "collected", 36, GREY, a)
    source(d, D.SRC_MBR + " ($5.4T revenue ÷ $7.4T outlays)", ease(c.t))


@scene("deficit")
def s_deficit(d, fr, c):
    hdr(d, c)
    text(d, (W / 2, 300), "BORROWED IN FISCAL YEAR 2026", 26, GREY, ease(c.t / 0.6), "SemiBold", "mm", spacing=6)
    p = ease_out(c.since(1) / 1.8) if len(c.cues) > 1 else 0
    text(d, (W / 2, 450), f"${D.DEFICIT_B * p:,.0f} billion", 130, WHITE, ease(c.t / 0.6), "SemiBold", "mm", True)
    if len(c.cues) > 2:
        a = c.p(2, 0.7)
        text(d, (W / 2, 640), "≈ $5.5 billion", 84, ACCENT, a, "SemiBold", "mm", True)
        text(d, (W / 2, 720), "every single day", 36, GREY, a, "Medium", "mm")
    source(d, D.SRC_MBR + " (deficit $1,993B ÷ 365 days)", ease(c.t))


@scene("bonds")
def s_bonds(d, fr, c):
    hdr(d, c)
    tint_layer(fr, guilloche(), BLUE_D, 0.22 * ease(c.t / 1.5), (W / 2, H / 2 + 20), 0.9, c.t * 1.2)
    a = ease(c.t / 0.8)
    L, R, y = (330, 450, 790, 650), (1130, 450, 1590, 650), 550
    for box, lab, sub in [(L, "US Treasury", "the borrower"), (R, "Investors", "around the world")]:
        d.rounded_rectangle(box, radius=18, fill=mix(PANEL, a), outline=mix(LINE, a), width=2)
        text(d, ((box[0] + box[2]) / 2, y - 22), lab, 46, WHITE, a, "SemiBold", "mm", True, base=PANEL)
        text(d, ((box[0] + box[2]) / 2, y + 34), sub, 28, GREY, a, "Regular", "mm", base=PANEL)
    pb = c.pa(0, "Treasury bonds", 0.8)
    pc = c.pa(0, "lend", 0.8)
    arrow(d, (820, 500), (820 + 280 * pb, 500), WHITE, pb, 4, 18) if pb > 0.02 else None
    text(d, (960, 455), "Treasury bonds", 30, WHITE, pb, "Medium", "mm")
    arrow(d, (1100, 600), (1100 - 280 * pc, 600), BLUE, pc, 4, 18) if pc > 0.02 else None
    text(d, (960, 645), "cash (a loan)", 30, BLUE, pc, "Medium", "mm")
    if len(c.cues) > 1:
        text(d, (W / 2, 840), "Countries borrow all the time.", 40, GREY, c.pa(1, "Countries", 0.6), "Medium", "mm")


LOOP_NODES = [("Deficit", "spending > revenue"), ("Borrowing", "sell new bonds"), ("More debt", ""),
              ("More interest", "")]


def draw_loop(d, c, cx, cy, R, lit, extra_a=0.0, orbit=None, base_a=1.0):
    pos = [(cx - R, cy), (cx, cy - R * 0.72), (cx + R, cy), (cx, cy + R * 0.72)]
    for i in range(4):
        a0 = math.pi + i * math.pi / 2
        pts = [(cx + R * math.cos(a0 + k / 30 * math.pi / 2),
                cy + R * 0.72 * math.sin(a0 + k / 30 * math.pi / 2)) for k in range(4, 27)]
        on = lit[i] if i < len(lit) else 0
        polyline(d, pts, LINE, base_a, 3)
        if on > 0:
            polyline(d, partial(pts, on), ACCENT if i == 3 else BLUE, base_a, 5)
            if on >= 1:
                arrow(d, pts[-2], pts[-1], ACCENT if i == 3 else BLUE, base_a, 5, 18)
    if orbit is not None:
        for k in range(3):
            ang = orbit + k * 2 * math.pi / 3
            dot(d, (cx + R * math.cos(ang), cy + R * 0.72 * math.sin(ang)), 9, ACCENT, base_a)
    for i, ((lab, sub), (x, y)) in enumerate(zip(LOOP_NODES, pos)):
        hot = (lit[i - 1] if i > 0 and i - 1 < len(lit) else 0) or (i == 0)
        col = ACCENT if i == 3 and hot else WHITE
        w = max(text_width(lab, 38, "SemiBold"), text_width(sub, 24)) / 2 + 36
        d.rounded_rectangle((x - w, y - 50, x + w, y + 50), radius=14, fill=mix(PANEL, base_a),
                            outline=mix(col if hot else LINE, base_a), width=2)
        text(d, (x, y - (12 if sub else 0)), lab, 38, col, base_a, "SemiBold", "mm", base=PANEL)
        if sub:
            text(d, (x, y + 26), sub, 24, GREY, base_a, "Regular", "mm", base=PANEL)
    if extra_a > 0:
        x, y = pos[1][0] - 520, pos[1][1] - 40
        d.rounded_rectangle((x - 190, y - 50, x + 190, y + 50), radius=14, fill=mix(PANEL, extra_a),
                            outline=mix(BLUE, extra_a), width=2)
        text(d, (x, y - 12), "Old bonds come due", 32, WHITE, extra_a, "SemiBold", "mm", base=PANEL)
        text(d, (x, y + 24), "repaid with new borrowing", 22, GREY, extra_a, "Regular", "mm", base=PANEL)
        arrow(d, (x + 194, y + 10), (pos[1][0] - 150, pos[1][1] + 6), BLUE, extra_a, 4, 16)
    return pos


@scene("machine")
def s_machine(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    lit = [c.p(1, 1.0) if n > 1 else 0,            # borrowing -> more debt
           c.p(2, 1.0) if n > 2 else 0,            # more debt -> more interest
           c.p(4, 1.0) if n > 4 else 0,            # more interest -> deficit
           c.p(4, 1.0, 0.8) if n > 4 else 0]       # deficit -> borrowing
    lit = [lit[3], lit[0], lit[1], lit[2]]
    pos = draw_loop(d, c, W / 2 + 120, 560, 470, lit, c.p(5, 0.8) if n > 5 else 0, base_a=ease(c.t / 0.8))
    if n > 3:
        a = c.p(3, 0.6)
        x, y = pos[3][0] + 290, pos[3][1] + 10
        text(d, (x, y - 20), "+$115B", 64, ACCENT, a, "Bold", "lm", True)
        text(d, (x, y + 30), "interest bill, in one year", 26, GREY, a, "Regular", "lm")
    source(d, D.SRC_MBR, ease(c.t))


@scene("one_in_five")
def s_one_in_five(d, fr, c):
    hdr(d, c)
    a = ease(c.t / 0.6)
    bw, bh, g = 250, 120, 40
    x0 = (W - (5 * bw + 4 * g)) / 2
    hot = c.pa(0, "goes straight", 0.7)
    for k in range(5):
        x = x0 + k * (bw + g)
        ak = ease((c.t - 0.2 - k * 0.15) / 0.5)
        y = 420 - (40 * hot if k == 0 else 0)
        col = ACCENT if k == 0 and hot > 0 else BLUE
        d.rounded_rectangle((x, y, x + bw, y + bh), radius=10, outline=mix(col, ak), width=3)
        text(d, (x + bw / 2, y + bh / 2), "$", 60, col, ak, "SemiBold", "mm", True)
    text(d, (x0 + bw / 2, 600), "→ interest", 36, ACCENT, hot, "SemiBold", "mm")
    text(d, (W / 2, 760), "More than 1 in 5 tax dollars", 60, WHITE, a, "SemiBold", "mm", True)
    text(d, (W / 2, 830), "Net interest $1.14T ÷ revenue $5.4T ≈ 21% (FY2026)", 30, GREY, a, "Regular", "mm")
    source(d, D.SRC_MBR, a)


@scene("per_person")
def s_per_person(d, fr, c):
    hdr(d, c)
    p = ease_out(c.since(0) / 3.0)
    text(d, (W / 2, 320), "SPLIT EVENLY", 26, GREY, ease(c.t / 0.6), "SemiBold", "mm", spacing=6)
    text(d, (W / 2, 480), f"{money(D.PER_PERSON * p)}+", 170, WHITE, ease(c.t / 0.5), "SemiBold", "mm", True)
    text(d, (W / 2, 640), "for every man, woman and child", 44, ACCENT, c.pa(0, "every man", 0.7), "Medium", "mm")
    source(d, "Source: US Treasury, Debt to the Penny ($40.31T) ÷ US Census Bureau resident population estimate",
           ease(c.t))


@scene("spin")
def s_spin(d, fr, c):
    hdr(d, c)
    t = c.t
    orbit = 0.6 * t + 0.09 * t * t          # accelerating
    draw_loop(d, c, W / 2, 560, 470, [1, 1, 1, 1], 0, orbit, base_a=ease(t / 0.6) * 0.9)
    if len(c.cues) > 1:
        text(d, (W / 2, 560), "The faster it spins,", 40, WHITE, c.p(1, 0.6), "Medium", "mm")
        text(d, (W / 2, 610), "the harder it is to stop.", 40, ACCENT, c.pa(1, "the harder", 0.6), "Medium", "mm")
    else:
        text(d, (W / 2, 580), "A machine that feeds itself", 40, WHITE, ease(t / 0.8), "Medium", "mm")


# ======================================================================= part 2
@scene("nobody")
def s_nobody(d, fr, c):
    hdr(d, c)
    text(d, (W / 2, 330), "“", 200, DIM, ease(c.t / 0.6), "Bold", "mm", True)
    word_reveal(d, (W / 2, 450), "Come on. It's America.", 64, c.t - c.at(0, "Come"), 0.9, WHITE, "SemiBold",
                display=True)
    word_reveal(d, (W / 2, 540), "Nobody seriously doubts America.", 64, c.t - c.at(0, "Nobody"), 1.2, WHITE,
                "SemiBold", display=True)
    if len(c.cues) > 1:
        text(d, (W / 2, 720), "Except… they already have.", 56, ACCENT, c.p(1, 0.6), "SemiBold", "mm", True)


@scene("downgrades")
def s_downgrades(d, fr, c):
    hdr(d, c)
    text(d, (MX, 190), "The United States loses its top credit ratings", 46, WHITE, ease(c.t / 0.6), "SemiBold",
         display=True)
    x0, x1, y = 300, 1620, 560
    hline(d, x0 - 100, x0 - 100 + (x1 - x0 + 200) * ease_out(c.t / 1.6), y, LINE, 1, 3)
    dctx = c.pa(0, "August 2011", 0.6)
    ev = [("Aug 2011", "S&P", "AAA → AA+", c.pa(0, "S&P", 0.6)),
          ("Aug 2023", "Fitch", "AAA → AA+", c.p(1, 0.6) if len(c.cues) > 1 else 0),
          ("May 2025", "Moody's", "Aaa → Aa1", c.p(2, 0.6) if len(c.cues) > 2 else 0)]
    for k, (when, who, what, a) in enumerate(ev):
        x = lerp(x0, x1, k / 2)
        dot(d, (x, y), 12, ACCENT, a)
        if k == 0:
            dot(d, (x, y), 9, GREY, dctx * (1 - a))
            text(d, (x, y - 110), when, 34, GREY, dctx, "Medium", "mm")
            text(d, (x, y + 130), "Debt-ceiling standoff", 28, GREY, dctx * (0.5 + 0.5 * (1 - a)), "Regular", "mm")
            if dctx > 0 and a <= 0:
                continue
        text(d, (x, y - 110), when, 34, GREY, a, "Medium", "mm")
        text(d, (x, y - 60), who, 54, WHITE, a, "SemiBold", "mm", True)
        text(d, (x, y + 70), what, 44, ACCENT, a, "SemiBold", "mm", True)
    if len(c.cues) > 2:
        text(d, (lerp(x0, x1, 1), y + 130), "Aaa since 1917", 28, GREY, c.pa(2, "more than a century", 0.6),
             "Regular", "mm")
    source(d, D.SRC_RATINGS, ease(c.t))


@scene("none_perfect")
def s_none_perfect(d, fr, c):
    hdr(d, c)
    a = ease(c.t / 0.6)
    cols = [("S&P Global Ratings", "AA+"), ("Fitch Ratings", "AA+"), ("Moody's Ratings", "Aa1")]
    for k, (who, r) in enumerate(cols):
        x = W / 2 + (k - 1) * 480
        ak = ease((c.t - 0.3 * k) / 0.6)
        d.rounded_rectangle((x - 200, 330, x + 200, 640), radius=18, fill=mix(PANEL, ak), outline=mix(LINE, ak), width=2)
        text(d, (x, 400), who, 32, GREY, ak, "Medium", "mm", base=PANEL)
        text(d, (x, 520), r, 110, WHITE, ak, "SemiBold", "mm", True, base=PANEL)
    p = c.pa(0, "not one", 0.8)
    text(d, (W / 2, 770), "Not one perfect score.", 64, ACCENT, p, "SemiBold", "mm", True)
    source(d, D.SRC_RATINGS, a)


def chart_axes(d, box, xr, yr, a, xticks, yticks, yfmt="{:.0f}%", xfmt="{}"):
    x0, y0, x1, y1 = box

    def X(v):
        return x0 + (v - xr[0]) / (xr[1] - xr[0]) * (x1 - x0)

    def Y(v):
        return y1 - (v - yr[0]) / (yr[1] - yr[0]) * (y1 - y0)

    for v in yticks:
        hline(d, x0, x1, Y(v), LINE, a * 0.8, 1)
        text(d, (x0 - 16, Y(v)), yfmt.format(v), 24, GREY, a, "Regular", "rm")
    for v in xticks:
        text(d, (X(v), y1 + 30), xfmt.format(v), 24, GREY, a, "Regular", "mm")
    return X, Y


@scene("yield")
def s_yield(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    a = ease(c.t / 0.8)
    text(d, (MX, 170), "30-year US Treasury yield", 46, WHITE, a, "SemiBold", display=True)
    text(d, (MX, 228), "Annual averages 2007–2025, then the August 2026 close", 26, GREY, a)
    X, Y = chart_axes(d, (230, 320, 1560, 900), (2006.5, 2027), (1, 6), a, range(2007, 2027, 3), [1, 2, 3, 4, 5, 6])
    pts = [(X(x + 0.5), Y(v)) for x, v in D.YIELD_30Y] + [(X(2026.6), Y(D.YIELD_AUG26_CLOSE))]
    p = ease_out((c.t - (c.start(1) if n > 1 else 0) + 0.8) / 3.2) if n > 1 else 0.35 * ease(c.t / 1.5)
    polyline(d, partial(pts, p), BLUE, a, 5)
    if p >= 1:
        dot(d, pts[-1], 11, ACCENT, a)
        text(d, (pts[-1][0] - 20, pts[-1][1] - 44), "5.31%", 48, ACCENT, a, "Bold", "rm", True)
    if n > 2:
        h = c.p(2, 1.4)
        y = Y(D.YIELD_AUG26_CLOSE)
        dashed(d, (pts[-1][0], y), (pts[-1][0] - (pts[-1][0] - X(2007)) * h, y), ACCENT, h * 0.8, 2)
        text(d, (X(2007) + 10, y - 28), "Highest close since 2007", 28, ACCENT, ease(h * 2 - 1), "Medium", "lm")
    if n > 3:
        b = c.p(3, 0.7)
        d.rounded_rectangle((560, 760, 990, 880), radius=12, fill=mix(PANEL, b), outline=mix(ACCENT, b), width=2)
        text(d, (585, 795), "Aug 2026 auction: 5.22%", 30, WHITE, b, "SemiBold", "lm", base=PANEL)
        text(d, (585, 845), "highest at a 30-year auction since 2001", 22, GREY, b, "Regular", "lm", base=PANEL)
    source(d, D.SRC_YIELD + " · 2007–2025 annual averages approximate", a)


@scene("charging")
def s_charging(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    out = ease((c.start(1) - c.t) / 0.4) if n > 1 else 1
    text(d, (W / 2, 450), "The world is still lending.", 66, WHITE, c.p(0, 0.6) * out, "SemiBold", "mm", True)
    text(d, (W / 2, 560), "But it's charging more.", 66, ACCENT, c.pa(0, "But", 0.6) * out, "SemiBold", "mm", True)
    if n > 1:
        text(d, (W / 2, 450), "Not collapse tomorrow.", 60, GREY, c.p(1, 0.6), "SemiBold", "mm", True)
        text(d, (W / 2, 560), "But the people who judge risk", 60, WHITE, c.pa(1, "But it does", 0.6), "SemiBold", "mm", True)
        text(d, (W / 2, 650), "are getting nervous.", 60, ACCENT, c.pa(1, "getting", 0.5), "SemiBold", "mm", True)


# ======================================================================= part 3
def draw_doors(d, focus=None, opened=0.0, a=1.0, ys=300, appear=(1, 1, 1)):
    dw, dh, g = 260, 470, 120
    x0 = (W - (3 * dw + 2 * g)) / 2
    for k in range(3):
        ak = a * appear[k]
        if ak <= 0:
            continue
        x = x0 + k * (dw + g)
        dim = focus is not None and focus != k
        col = DIM if dim else WHITE
        d.rectangle((x - 10, ys - 10, x + dw + 10, ys + dh), outline=mix(LINE, ak), width=2)
        if focus == k and opened > 0:
            # the door swings open (shown as a narrowing panel) revealing light
            d.rectangle((x, ys, x + dw, ys + dh), fill=mix(ACCENT, ak * 0.18 * opened))
            pw = dw * (1 - 0.82 * opened)
            d.polygon([(x, ys), (x + pw, ys + 24 * opened), (x + pw, ys + dh - 24 * opened), (x, ys + dh)],
                      fill=mix(PANEL, ak), outline=mix(ACCENT, ak))
        else:
            d.rectangle((x, ys, x + dw, ys + dh), fill=mix(PANEL, ak), outline=mix(col, ak * (0.5 if dim else 1)), width=2)
            dot(d, (x + dw - 36, ys + dh / 2), 7, col, ak * (0.5 if dim else 1))
        text(d, (x + dw / 2, ys + dh + 60), str(k + 1), 48, ACCENT if focus == k else col, ak, "SemiBold", "mm", True)


@scene("doors")
def s_doors(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    app = [ease((c.t - c.at(1, "three") - k * 0.25) / 0.5) if n > 1 else 0 for k in range(3)]
    text(d, (W / 2, 190), "How would a real crisis start?", 50, WHITE, c.p(0, 0.6), "SemiBold", "mm", True)
    draw_doors(d, a=1.0, appear=app, ys=310)
    tag(d, "SCENARIOS, NOT PREDICTIONS", ease((c.t - 1.0) / 0.6))


def door_title(d, c, k, title):
    hdr(d, c)
    o = ease_out((c.t - 0.2) / 1.6)
    draw_doors(d, focus=k, opened=o, a=1.0, ys=250)
    text(d, (W / 2, 880), title, 56, WHITE, c.p(0, 0.6, 0.3), "SemiBold", "mm", True)
    tag(d, "SCENARIO", ease(c.t / 0.6))


@scene("door1")
def s_door1(d, fr, c):
    door_title(d, c, 0, "Door 1 · The investors walk away")


@scene("door2")
def s_door2(d, fr, c):
    door_title(d, c, 1, "Door 2 · The dollar slowly melts")


@scene("door3")
def s_door3(d, fr, c):
    door_title(d, c, 2, "Door 3 · America defaults… on purpose")


@scene("door1_quote")
def s_door1_quote(d, fr, c):
    header(d, "Door 1 · The investors walk away", ease(c.t / 0.6))
    tag(d, "SCENARIO", 1)
    text(d, (W / 2, 330), "“", 200, DIM, ease(c.t / 0.6), "Bold", "mm", True)
    word_reveal(d, (W / 2, 470), "We'll still lend you money…", 64, c.t - c.at(0, "We'll"), 1.2, WHITE, "SemiBold",
                display=True)
    word_reveal(d, (W / 2, 570), "but only at much higher interest rates.", 64, c.t - c.at(0, "but only"), 1.6,
                WHITE, "SemiBold", display=True, highlight=("higher",))


@scene("door1_chain")
def s_door1_chain(d, fr, c):
    header(d, "Door 1 · The investors walk away", ease(c.t / 0.6))
    tag(d, "SCENARIO", 1)
    n = len(c.cues)
    a0 = c.p(0, 0.5)
    a1 = c.p(1, 0.5) if n > 1 else 0
    # see-saw: bond prices and yields move in opposite directions
    cx, cy = W / 2, 400
    tilt = 0.24 * max(a0, 0)
    L = 420
    p0 = (cx - L * math.cos(tilt), cy + L * math.sin(tilt))
    p1 = (cx + L * math.cos(tilt), cy - L * math.sin(tilt))
    k = ease(c.t / 0.6)
    d.polygon([(cx, cy + 8), (cx - 30, cy + 60), (cx + 30, cy + 60)], fill=mix(DIM, k))
    d.line((*p0, *p1), fill=mix(WHITE, k), width=5)
    text(d, (p0[0], p0[1] + 50), "Bond prices ↓", 44, WHITE, a0, "SemiBold", "mm")
    text(d, (p1[0], p1[1] - 50), "Yields ↑", 44, ACCENT, a1, "SemiBold", "mm")
    if n > 2:
        items = [("Every dollar borrowed", "borrows"), ("Every dollar refinanced", "refinances"),
                 ("Mortgages", "mortgages"), ("Car loans", "car loans"), ("Business loans", "business loans")]
        for j, (lab, key) in enumerate(items):
            a = c.pa(2, key, 0.5)
            x = W / 2 + (j - 2) * 340
            d.rounded_rectangle((x - 155, 640, x + 155, 760), radius=12, fill=mix(PANEL, a), outline=mix(LINE, a), width=2)
            for ln_i, ln in enumerate(wrap(lab, 28, 260, "Medium")):
                text(d, (x, 680 + ln_i * 34), ln, 28, WHITE, a, "Medium", "mm", base=PANEL)
            text(d, (x, 810), "costs more ↑", 26, ACCENT, a, "Medium", "mm")


@scene("door1_cbo")
def s_door1_cbo(d, fr, c):
    header(d, "Door 1 · The investors walk away", ease(c.t / 0.6))
    n = len(c.cues)
    text(d, (MX, 190), "Net interest: already the 2nd-largest bill", 46, WHITE, c.p(0, 0.6), "SemiBold", display=True)
    text(d, (MX, 248), "after Social Security (FY2026)", 28, GREY, c.p(0, 0.6))
    base, maxh = 850, 470
    bars = [("FY2026", "actual", 1.14, c.p(0, 0.8, 0.6)), ("2036", "CBO projection", D.NET_INTEREST_2036_T,
                                                         c.p(1, 1.2) if n > 1 else 0)]
    for k, (lab, kind, v, a) in enumerate(bars):
        x = 760 + k * 420
        h = maxh * v / 2.2 * a
        if a > 0:
            if k == 0:
                d.rectangle((x - 110, base - h, x + 110, base), fill=mix(ACCENT, a))
            else:
                d.rectangle((x - 110, base - h, x + 110, base), outline=mix(ACCENT, a), width=4)
                for yy in range(int(base - h) + 10, base, 18):
                    d.line((x - 106, yy, x + 106, yy), fill=mix(ACCENT, a * 0.35), width=2)
            text(d, (x, base - h - 46), f"${v:.2f}T" if k == 0 else f"${v:.1f}T", 54, ACCENT, a, "Bold", "mm", True)
        text(d, (x, base + 40), lab, 32, WHITE, max(a, 0.3), "SemiBold", "mm")
        text(d, (x, base + 80), kind, 24, GREY, max(a, 0.3), "Regular", "mm")
    hline(d, 560, 1380, base, DIM, 1, 2)
    if n > 1:
        tag(d, "PROJECTION", c.p(1, 0.6))
        text(d, (1500, 520), "even without", 32, GREY, c.pa(1, "even without", 0.6), "Regular", "lm")
        text(d, (1500, 562), "a panic", 32, GREY, c.pa(1, "even without", 0.6), "Regular", "lm")
    source(d, D.SRC_MBR + "; " + D.SRC_BEO.replace("Source: ", ""), ease(c.t))


@scene("uk_intro")
def s_uk_intro(d, fr, c):
    hdr(d, c)
    text(d, (W / 2, 420), "Far-fetched?", 70, WHITE, c.p(0, 0.6), "SemiBold", "mm", True)
    a = c.pa(0, "In 2022", 0.7)
    text(d, (W / 2, 560), "UNITED KINGDOM", 40, ACCENT, a, "SemiBold", "mm", spacing=10)
    text(d, (W / 2, 640), "2022", 110, WHITE, a, "Bold", "mm", True)


@scene("uk")
def s_uk(d, fr, c):
    header(d, "Part 3 · The UK gilt crisis, 2022", ease(c.t / 0.6))
    n = len(c.cues)
    x0, x1, ty = 260, 1660, 800
    # real dates: 23 Sep, 28 Sep, 20 Oct -> positions by day number
    knots = [(21, x0), (23, 420), (28, 900), (33, 1100), (50, x1)]   # piecewise: the first week is stretched

    def X(day):
        for (da, xa), (db, xb) in zip(knots, knots[1:]):
            if day <= db:
                return xa + (day - da) / (db - da) * (xb - xa)
        return x1
    days = {"23 Sep": 23, "28 Sep": 28, "20 Oct": 50}
    hline(d, x0 - 40, x1 + 40, ty, LINE, ease(c.t / 0.8), 3)
    ev = [("23 Sep", "Mini-budget:", "£45bn unfunded tax cuts", c.p(0, 0.6)),
          ("28 Sep", "Bank of England pledges", "up to £65bn for gilts", c.pa(4, "Bank of England", 0.6) if n > 4 else 0),
          ("20 Oct", "Prime Minister", "Liz Truss resigns", c.p(5, 0.6) if n > 5 else 0)]
    for when, l1, l2, a in ev:
        x = X(days[when])
        x = min(x, x1)
        dot(d, (x, ty), 11, ACCENT if when == "20 Oct" else WHITE, a)
        text(d, (x, ty + 44), when + " 2022", 26, GREY, a, "Medium", "mm")
        text(d, (x, ty + 88), l1, 28, WHITE, a, "SemiBold", "mm")
        text(d, (x, ty + 124), l2, 26, WHITE, a, "Regular", "mm")
    # schematic long-dated gilt yield path (shape only, not to scale)
    shape = [(21, 0.10), (22, 0.14), (23, 0.32), (26, 0.62), (27, 0.92), (28, 0.40), (30, 0.48), (33, 0.52),
             (38, 0.62), (41, 0.80), (44, 0.52), (50, 0.30)]
    top, bot = 290, 660
    pts = [(X(dd), bot - v * (bot - top)) for dd, v in shape]
    p = 0.0
    if n > 1:
        p = 0.28 * ease((c.t - c.start(1)) / 1.0)
    if n > 3:
        p = max(p, 0.28 + 0.2 * ease((c.t - c.start(3)) / 1.2))
    if n > 4:
        p = max(p, 0.48 + 0.18 * ease((c.t - c.at(4, "Bank of England")) / 1.0))
    if n > 5:
        p = max(p, 0.66 + 0.34 * ease((c.t - c.start(5)) / 1.6))
    if p > 0:
        polyline(d, partial(pts, p), ACCENT, 1, 5)
        text(d, (x0 - 20, top - 40), "Long-dated gilt yields: schematic shape, not to scale", 24, GREY,
             ease(p * 4), "Regular", "la")
    if n > 2:
        a = c.p(2, 0.6)
        d.rounded_rectangle((1180, 668, 1660, 760), radius=12, fill=mix(PANEL, a), outline=mix(LINE, a), width=2)
        text(d, (1205, 698), "Pound: record low vs dollar", 28, WHITE, a, "SemiBold", "lm", base=PANEL)
        text(d, (1205, 736), "26 September 2022", 22, GREY, a, "Regular", "lm", base=PANEL)
    source(d, D.SRC_BOE, ease(c.t))


@scene("uk_imagine")
def s_uk_imagine(d, fr, c):
    hdr(d, c)
    a0 = c.p(0, 0.6)
    text(d, (W / 2, 380), "That was Britain.", 58, GREY, a0, "SemiBold", "mm", True)
    if len(c.cues) > 1:
        a = c.p(1, 0.8)
        text(d, (W / 2, 520), "Now imagine the country whose bonds", 58, WHITE, a, "SemiBold", "mm", True)
        text(d, (W / 2, 600), "the entire world depends on.", 58, ACCENT, c.pa(1, "the entire", 0.7), "SemiBold", "mm",
             True)


@scene("door2_print")
def s_door2_print(d, fr, c):
    header(d, "Door 2 · The dollar slowly melts", ease(c.t / 0.6))
    tag(d, "SCENARIO", 1)
    n = len(c.cues)
    melt = ease((c.t - c.at(0, "quietly")) / 6.0)
    s = 1 - 0.35 * melt
    cx, cy = 560, 470
    bw, bh = 520 * s, 240 * s
    a = ease(c.t / 0.6)
    d.rounded_rectangle((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), radius=12,
                        outline=mix(BLUE, a * (1 - 0.5 * melt)), width=3)
    d.rounded_rectangle((cx - bw / 2 + 16, cy - bh / 2 + 16, cx + bw / 2 - 16, cy + bh / 2 - 16), radius=8,
                        outline=mix(BLUE_D, a * (1 - 0.5 * melt)), width=1)
    text(d, (cx, cy), "$1", 110 * s, BLUE, a * (1 - 0.5 * melt), "SemiBold", "mm", True)
    text(d, (cx, cy + 200), "what a dollar buys", 28, GREY, a, "Regular", "mm")
    items = [("Prices ↑", 1, ACCENT), ("Savings ↓", 2, BLUE)]
    for j, (lab, cue, col) in enumerate(items):
        if cue < n:
            text(d, (1300, 360 + j * 130), lab, 64, col, c.p(cue, 0.5), "SemiBold", "mm", True)
    if n > 3:
        a3 = c.pa(3, "Why", 0.7)
        text(d, (W / 2, 820), "“Why are we holding so many dollars?”", 50, WHITE, a3, "Medium", "mm")


@scene("door2_creep")
def s_door2_creep(d, fr, c):
    header(d, "Door 2 · The dollar slowly melts", ease(c.t / 0.6))
    tag(d, "SCENARIO", 1)
    # a slow, quiet line that drifts down: no crash, just erosion
    p = ease(c.t / max(1, c.dur - 0.5))
    pts = [(260 + i * 14, 400 + (i * 14) ** 1.25 * 0.06 + 6 * math.sin(i * 0.4)) for i in range(101)]
    polyline(d, partial(pts, p), BLUE, ease(c.t / 0.5), 4)
    text(d, (W / 2, 260), "No crash.", 54, GREY, c.p(0, 0.6), "SemiBold", "mm", True)
    text(d, (W / 2, 860), "It creeps in.", 60, WHITE, c.pa(0, "It creeps", 0.8), "SemiBold", "mm", True)


@scene("door2_reserve")
def s_door2_reserve(d, fr, c):
    header(d, "Door 2 · The dollar slowly melts", ease(c.t / 0.6))
    n = len(c.cues)
    a = ease(c.t / 0.8)
    text(d, (MX, 170), "Share of world FX reserves held in US dollars", 46, WHITE, a, "SemiBold", display=True)
    text(d, (MX, 228), "Allocated official foreign-exchange reserves", 26, GREY, a)
    X, Y = chart_axes(d, (230, 320, 1560, 880), (1999.5, 2027.5), (50, 75), a, range(2000, 2027, 5), [50, 55, 60, 65, 70, 75])
    pts = [(X(x), Y(v)) for x, v in D.USD_SHARE]
    if n > 1:
        p1 = ease((c.t - c.at(1, "more than 70%")) / 0.6)
        dot(d, pts[0], 10, WHITE, p1)
        text(d, (pts[0][0] + 22, pts[0][1] - 26), "71% (2000)", 32, WHITE, p1, "SemiBold", "lm")
    if n > 2:
        p2 = ease_out((c.t - c.start(2)) / 2.8)
        polyline(d, partial(pts, p2), BLUE, 1, 5)
        if p2 >= 1:
            dot(d, pts[-1], 11, ACCENT)
            text(d, (pts[-1][0] - 10, pts[-1][1] + 54), "56.7%", 54, ACCENT, 1, "Bold", "rm", True)
            text(d, (pts[-1][0] - 10, pts[-1][1] + 100), "Q2 2026", 24, GREY, 1, "Regular", "rm")
    source(d, D.SRC_COFER + " · earlier years approximate", a)


@scene("door3_strange")
def s_door3_strange(d, fr, c):
    header(d, "Door 3 · America defaults… on purpose", ease(c.t / 0.6))
    tag(d, "SCENARIO", 1)
    n = len(c.cues)
    out = ease((c.start(2) - c.t) / 0.4) if n > 2 else 1
    if n > 1:
        text(d, (W / 2 - 300, 470), "Has the money", 52, WHITE, c.p(1, 0.6) * out, "SemiBold", "mm", True)
        text(d, (W / 2 + 300, 470), "Fails to pay", 52, ACCENT, c.pa(1, "still fail", 0.6) * out, "SemiBold", "mm", True)
        text(d, (W / 2, 470), "≠", 70, GREY, c.pa(1, "still fail", 0.6) * out, "Regular", "mm")
    else:
        text(d, (W / 2, 470), "The strangest one", 56, WHITE, c.p(0, 0.6), "SemiBold", "mm", True)
    if n > 2:
        text(d, (W / 2, 430), "How?", 64, GREY, c.p(2, 0.4), "SemiBold", "mm", True)
    if n > 3:
        text(d, (W / 2, 560), "POLITICS", 110, ACCENT, c.p(3, 0.4), "Bold", "mm", True, spacing=10)


@scene("door3_limit")
def s_door3_limit(d, fr, c):
    header(d, "Door 3 · America defaults… on purpose", ease(c.t / 0.6))
    n = len(c.cues)
    a = ease(c.t / 0.6)
    text(d, (MX, 190), "The debt limit", 50, WHITE, a, "SemiBold", display=True)
    cx, cy, R = W / 2, 700, 380
    lo, hi = 30.0, D.DEBT_LIMIT_T
    for k in range(0, 61):
        ang = math.pi + k / 60 * math.pi
        r0, r1 = R - (24 if k % 10 == 0 else 12), R
        col = ACCENT if k >= 57 else LINE
        d.line((cx + r0 * math.cos(ang), cy + r0 * math.sin(ang), cx + r1 * math.cos(ang), cy + r1 * math.sin(ang)),
               fill=mix(col, a), width=3)
    pl = c.p(1, 0.8) if n > 1 else 0
    text(d, (cx + R + 20, cy - 10), "Limit", 26, GREY, pl, "Medium", "lm")
    text(d, (cx + R + 20, cy + 26), "$41.1T", 44, ACCENT, pl, "Bold", "lm", True)
    text(d, (cx - R - 20, cy + 26), "$30T", 26, GREY, pl, "Regular", "rm")
    pn = c.p(2, 1.8) if n > 2 else 0
    v = lo + (D.DEBT_TOTAL_T - lo) * pn
    ang = math.pi + (v - lo) / (hi - lo) * math.pi
    if pn > 0:
        d.line((cx, cy, cx + (R - 50) * math.cos(ang), cy + (R - 50) * math.sin(ang)), fill=WHITE, width=5)
        dot(d, (cx, cy), 14, WHITE)
        text(d, (cx, cy - 130), f"${v:.2f}T", 96, WHITE, pn, "SemiBold", "mm", True)
        text(d, (cx, cy - 60), "owed now (total public debt)", 26, GREY, pn, "Regular", "mm")
    if n > 3:
        b = c.p(3, 0.6)
        tag(d, "ESTIMATE", b)
        text(d, (cx, cy + 90), "Limit could be hit: 2027 (estimated)", 40, ACCENT, b, "SemiBold", "mm")
    source(d, D.SRC_NTUF + " · Debt subject to limit differs slightly from total debt", a)


@scene("door3_panic")
def s_door3_panic(d, fr, c):
    header(d, "Door 3 · America defaults… on purpose", ease(c.t / 0.6))
    tag(d, "SCENARIO", 1)
    n = len(c.cues)
    out = ease((c.start(3) - c.t) / 0.4) if n > 3 else 1
    k = ease(c.t / 0.6) * out
    pays = [("Social Security", "Social Security"), ("Military pay", "military"), ("Veterans' benefits", "veterans"),
            ("Contractors", None), ("Bond interest", None)]
    unsure = c.pa(0, "payments could be delayed", 0.5)
    for j, (lab, key) in enumerate(pays):
        x = W / 2 + (j - 2) * 300
        named = c.pa(1, key, 0.4) if (key and n > 1) else 0
        missed = c.p(2, 0.5) if (j == 4 and n > 2) else 0
        col = ACCENT if (named or missed) else BLUE
        a = k * ease((c.t - j * 0.15) / 0.5)
        d.rounded_rectangle((x - 130, 360, x + 130, 560), radius=14, outline=mix(col, a), width=3)
        mark = "×" if missed else ("?" if unsure > 0.5 else "✓")
        text(d, (x, 430), mark, 60, col, a, "SemiBold", "mm")
        for i, ln in enumerate(wrap(lab, 26, 230, "Medium")):
            text(d, (x, 500 + i * 30), ln, 26, WHITE, a, "Medium", "mm")
        if named and not missed:
            text(d, (x, 600), "delayed?", 24, ACCENT, a * named, "Medium", "mm")
    if n > 2:
        text(d, (W / 2, 700), "The world's “safest” asset misses a payment", 44, WHITE, c.p(2, 0.6) * out, "Medium", "mm")
    if n > 3:
        text(d, (W / 2, 470), "Not because America is broke.", 58, GREY, c.p(3, 0.5), "SemiBold", "mm", True)
    if n > 4:
        text(d, (W / 2, 590), "Because it chose to stumble.", 58, ACCENT, c.p(4, 0.5), "SemiBold", "mm", True)


@scene("crisis_collapse")
def s_crisis_collapse(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    a = c.p(1, 0.7) if n > 1 else 0
    text(d, (W / 2 - 330, 430), "CRISIS", 110, WHITE, a, "Bold", "mm", True, spacing=6)
    text(d, (W / 2, 430), "≠", 110, ACCENT, a, "Regular", "mm")
    text(d, (W / 2 + 360, 430), "COLLAPSE", 110, GREY, a, "Bold", "mm", True, spacing=6)
    if n > 2:
        text(d, (W / 2, 580), "A country can take a brutal shock and survive.", 40, GREY, c.p(2, 0.6), "Regular", "mm")
    if n > 3:
        b = c.p(3, 0.8)
        d.rounded_rectangle((360, 680, 1560, 860), radius=16, fill=mix(PANEL, b), outline=mix(LINE, b), width=2)
        text(d, (400, 720), "CBO WARNING", 22, ACCENT, b, "SemiBold", spacing=4, base=PANEL)
        paragraph(d, (400, 760), "Rising debt raises the risk of a fiscal crisis and leaves less room to respond "
                  "to the next emergency.", 34, 1120, WHITE, b, "Regular", 1.3)
    source(d, D.SRC_BEO, ease(c.t))


# ======================================================================= part 4
CARD_LABELS = ["The dollar is king", "A giant economy", "Borrows in its own currency", "The world's safe asset"]


def draw_cards(d, active=-1, flipped=(0, 0, 0, 0), a=1.0, y=170, h=150, small=True, appear=(1, 1, 1, 1)):
    cw, g = 380, 36
    x0 = (W - (4 * cw + 3 * g)) / 2
    for k in range(4):
        ak = a * appear[k]
        if ak <= 0:
            continue
        x = x0 + k * (cw + g)
        f = flipped[k]
        hot = k == active
        if f < 0.5:
            sx = 1 - 2 * f
            xc = x + cw / 2
            d.rounded_rectangle((xc - cw / 2 * sx, y, xc + cw / 2 * sx, y + h), radius=14, fill=mix(BLUE_D, ak),
                                outline=mix(BLUE, ak), width=2)
        else:
            sx = 2 * f - 1
            xc = x + cw / 2
            d.rounded_rectangle((xc - cw / 2 * sx, y, xc + cw / 2 * sx, y + h), radius=14, fill=mix(PANEL, ak),
                                outline=mix(ACCENT if hot else LINE, ak), width=3 if hot else 2)
            if sx > 0.6:
                text(d, (xc, y + 44), f"{k + 1}", 34, ACCENT if hot else GREY, ak, "Bold", "mm", True, base=PANEL)
                for i, ln in enumerate(wrap(CARD_LABELS[k], 28, cw - 40, "Medium")):
                    text(d, (xc, y + 92 + i * 34), ln, 28, WHITE if hot else GREY, ak, "Medium", "mm", base=PANEL)


@scene("cards")
def s_cards(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    text(d, (W / 2, 330), "Why is America still standing?", 60, WHITE, c.pa(0, "If all", 0.6), "SemiBold", "mm", True)
    app = [ease((c.t - c.start(1) - k * 0.2) / 0.5) if n > 1 else 0 for k in range(4)]
    draw_cards(d, appear=app, y=520, h=230)


def adv(d, c, k):
    hdr(d, c)
    fl = [1.0 if j < k else (ease(c.t / 0.8) if j == k else 0) for j in range(4)]
    draw_cards(d, active=k, flipped=fl, y=150)


@scene("adv1")
def s_adv1(d, fr, c):
    adv(d, c, 0)
    n = len(c.cues)
    a = c.p(1, 0.6) if n > 1 else 0
    text(d, (MX, 420), "Share of world FX reserves, Q2 2026", 36, WHITE, a, "SemiBold")
    x0, x1, y = MX, W - MX, 500
    tot = 0
    cols = [BLUE, GREY, DIM]
    for j, (lab, v) in enumerate(D.RESERVES_Q2_2026):
        cue = j + 1                                   # each share grows as its sentence begins
        g = c.p(cue, 1.0, 0.5 if j == 0 else 0.0) if cue < n else 0
        xa = x0 + (x1 - x0) * tot / 100
        xb = xa + (x1 - x0) * v / 100 * g
        if g > 0:
            d.rectangle((xa, y, xb - 4, y + 120), fill=mix(cols[j], g))
            text(d, (xa + 24, y + 60), f"{v}%", 50, INK if j < 2 else WHITE, g, "Bold", "lm", True, base=cols[j])
            text(d, (xa + 4, y + 170), lab, 32, WHITE, g, "Medium", "la")
        tot += v
    source(d, D.SRC_COFER, ease(c.t))


@scene("adv2")
def s_adv2(d, fr, c):
    adv(d, c, 1)
    n = len(c.cues)
    a = c.pa(0, "worth", 0.6)
    text(d, (W / 2 - 400, 560), "$30T+", 130, WHITE, a, "SemiBold", "mm", True)
    text(d, (W / 2 - 400, 660), "economy (GDP) per year", 30, GREY, a, "Regular", "mm")
    if n > 1:
        b = c.p(1, 0.6)
        text(d, (W / 2 + 400, 560), "+$169B", 130, BLUE, b, "SemiBold", "mm", True)
        text(d, (W / 2 + 400, 660), "rise in tax revenue, FY2026", 30, GREY, b, "Regular", "mm")
    source(d, "Source: US Bureau of Economic Analysis (GDP); " + D.SRC_MBR.replace("Source: ", ""), ease(c.t))


@scene("adv3")
def s_adv3(d, fr, c):
    adv(d, c, 2)
    n = len(c.cues)
    a = c.p(0, 0.6, 0.4)
    for j, (lab, x) in enumerate([("Borrows in", W / 2 - 380), ("Repays in", W / 2 + 380)]):
        text(d, (x, 520), lab, 34, GREY, a, "Medium", "mm")
        text(d, (x, 620), "$", 130, BLUE, a, "SemiBold", "mm", True)
    arrow(d, (W / 2 - 220, 620), (W / 2 + 220, 620), BLUE, a, 4, 18)
    if n > 2:
        text(d, (W / 2, 800), "No foreign-currency trap", 48, WHITE, c.p(2, 0.6), "SemiBold", "mm", True)


@scene("adv4")
def s_adv4(d, fr, c):
    adv(d, c, 3)
    n = len(c.cues)
    users = [("Banks", "Banks"), ("Governments", "governments"), ("Funds", "funds")]
    for j, (lab, key) in enumerate(users):
        x = W / 2 + (j - 1) * 360
        aj = c.pa(1, key, 0.5) if n > 1 else 0
        d.rounded_rectangle((x - 140, 420, x + 140, 510), radius=12, outline=mix(LINE, aj), width=2)
        text(d, (x, 465), lab, 34, WHITE, aj, "Medium", "mm")
        arrow(d, (x, 515), (W / 2 + (x - W / 2) * 0.3, 610), DIM, aj, 2, 12)
    k = ease(c.t / 0.6)
    d.rounded_rectangle((W / 2 - 230, 615, W / 2 + 230, 715), radius=14, fill=mix(PANEL, k), outline=mix(BLUE, k), width=3)
    text(d, (W / 2, 665), "US Treasuries", 44, WHITE, k, "SemiBold", "mm", True, base=PANEL)
    if n > 2:
        text(d, (W / 2, 830), "So far, every auction has found buyers", 42, BLUE, c.p(2, 0.6), "Medium", "mm")


@scene("safe")
def s_safe(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    out = ease((c.start(1) - c.t) / 0.15) if n > 1 else 1
    text(d, (W / 2, H / 2), "So America is safe, right?", 70, WHITE, c.p(0, 0.6) * out, "SemiBold", "mm", True)
    if n > 1:
        text(d, (W / 2, H / 2), "Not quite.", 110, ACCENT, ease(c.since(1) / 0.15), "Bold", "mm", True)


@scene("trust")
def s_trust(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    a = ease(c.t / 0.6)
    crack = ease((c.t - c.at(2, "all at once") + 0.1) / 0.25) if n > 2 else 0
    fall = clamp((c.t - c.at(2, "all at once") - 0.3) / 1.6) if n > 2 else 0
    lines_a = a * (1 - crack)
    draw_cards(d, flipped=(1, 1, 1, 1), y=160, h=150, a=lines_a)
    cw, g = 380, 36
    x0 = (W - (4 * cw + 3 * g)) / 2
    tp = c.pa(0, "trust", 0.8)
    for k in range(4):
        xc = x0 + k * (cw + g) + cw / 2
        if tp > 0:
            polyline(d, partial([(xc, 315), (W / 2, 520)], tp), BLUE, lines_a, 2)
    # TRUST as a separate layer so it can crack into pieces
    size = 230
    txt = Image.new("L", (1200, 360), 0)
    ImageDraw.Draw(txt).text((600, 180), "TRUST", font=font(size, "Bold", True), fill=255, anchor="mm", )
    if fall <= 0:
        m = txt.point(lambda v: int(v * tp))
        fr.paste(Image.new("RGB", txt.size, WHITE), (W // 2 - 600, 640 - 180), m)
        if crack > 0:
            pts = [(W / 2 - 60, 470), (W / 2 + 10, 560), (W / 2 - 40, 640), (W / 2 + 40, 720), (W / 2 - 10, 810)]
            polyline(d, partial(pts, crack), INK, 1, 9)
            pts2 = [(W / 2 + 10, 560), (W / 2 + 160, 600), (W / 2 + 240, 590)]
            polyline(d, partial(pts2, crack), INK, 1, 6)
    else:
        # split along a jagged vertical crack; halves drift apart, tilt and fade
        mask = Image.new("L", txt.size, 0)
        md = ImageDraw.Draw(mask)
        poly = [(0, 0), (540, 0), (610, 90), (560, 180), (640, 260), (590, 360), (0, 360)]
        md.polygon(poly, fill=255)
        from PIL import ImageChops
        left = ImageChops.multiply(txt, mask)
        right = ImageChops.multiply(txt, ImageChops.invert(mask))
        fe = fall * fall
        for piece, dx, rot in ((left, -1, 1), (right, 1, -1)):
            p = piece.rotate(rot * 9 * fe, resample=Image.BILINEAR, center=(600, 180))
            p = p.point(lambda v: int(v * (1 - fall)))
            fr.paste(Image.new("RGB", p.size, mix(WHITE, 1 - 0.4 * fall)),
                     (int(W // 2 - 600 + dx * (5 + 120 * fe)), int(640 - 180 + 260 * fe)), p)


# ======================================================================= part 5
@scene("rome")
def s_rome(d, fr, c):
    hdr(d, c)
    a = ease(c.t / 1.5)
    tint_layer(fr, columns_drawing(), WHITE, 0.75 * a, (W / 2, 560), 0.9 + 0.03 * c.t / max(1, c.dur))
    text(d, (W / 2, 1000), "Original illustration", 18, DIM, a, "Regular", "mm")


@scene("chain_intro")
def s_chain_intro(d, fr, c):
    hdr(d, c)
    a = ease(c.t / 1.0) * (1 - 0.7 * c.pa(0, "It would", 1.0))
    tint_layer(fr, columns_drawing(), GREY, 0.35 * a, (W / 2, 560), 0.93)
    text(d, (W / 2, 420), "Not barbarians at the gates.", 62, GREY, c.p(0, 0.6), "SemiBold", "mm", True)
    text(d, (W / 2, 560), "A slow chain reaction.", 70, WHITE, c.pa(0, "It would", 0.6), "SemiBold", "mm", True)


CHAIN = ["Deficits that never stop", "Interest rates keep climbing", "Impossible political choices",
         "Slower growth, stubborn inflation, investor doubt", "Superpower status slips away"]


def draw_chain(d, lit, a=1.0, y=330, faded=0.0):
    n = len(CHAIN)
    bw, g = 300, 40
    x0 = (W - (n * bw + (n - 1) * g)) / 2
    for k in range(n):
        lk = lit[k]
        x = x0 + k * (bw + g)
        col = ACCENT if k == n - 1 else BLUE
        out_a = a * (1 - faded)
        d.rounded_rectangle((x, y, x + bw, y + 214), radius=14, fill=mix(PANEL, out_a),
                            outline=mix(col if lk > 0 else LINE, out_a * max(lk, 0.6)), width=3 if lk > 0 else 2)
        text(d, (x + 24, y + 34), f"{k + 1}", 30, col if lk > 0 else DIM, out_a, "Bold", "la", True, base=PANEL)
        for i, ln in enumerate(wrap(CHAIN[k], 28, bw - 48, "Medium")):
            text(d, (x + 24, y + 86 + i * 34), ln, 28, WHITE if lk > 0 else DIM, out_a * max(lk, 0.7), "Medium",
                 base=PANEL)
        if k < n - 1:
            arrow(d, (x + bw + 6, y + 107), (x + bw + g - 6, y + 107), BLUE if lit[k + 1] > 0 else LINE, out_a, 3, 10)


@scene("chain")
def s_chain(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    tag(d, "A POSSIBLE PATH — NOT A PREDICTION", ease(c.t / 0.6))
    lit = [c.p(0, 0.5), c.p(2, 0.5) if n > 2 else 0, c.p(3, 0.5) if n > 3 else 0, c.p(4, 0.5) if n > 4 else 0, 0]
    draw_chain(d, lit, ease(c.t / 0.6), y=230)
    # inset: deficit actual vs projected (sentence 2)
    if n > 1:
        ina = c.p(1, 0.6) * ease((c.start(2) - c.t + 0.3) / 0.5) if n > 2 else c.p(1, 0.6)
        base = 900
        for k, (lab, v, kind) in enumerate([("FY2026", 1.993, "actual"), ("2036", D.DEFICIT_2036_T, "CBO projection")]):
            x = W / 2 - 200 + k * 400
            h = 300 * v / 3.2 * ease_out((c.t - c.start(1) - k * 0.6) / 1.0)
            if k == 0:
                d.rectangle((x - 90, base - h, x + 90, base), fill=mix(BLUE, ina))
            else:
                d.rectangle((x - 90, base - h, x + 90, base), outline=mix(BLUE, ina), width=4)
            text(d, (x, base - h - 36), f"${v:.1f}T" if k else "≈ $2.0T", 42, WHITE, ina, "Bold", "mm", True)
            text(d, (x + 120, base - 40), f"{lab}", 28, WHITE, ina, "SemiBold", "lm")
            text(d, (x + 120, base - 8), kind, 22, GREY, ina, "Regular", "lm")
        text(d, (W / 2, 520), "Annual deficit", 32, GREY, ina, "Medium", "mm")
    if n > 3:
        ch = c.p(3, 0.6) * (ease((c.start(4) - c.t + 0.3) / 0.5) if n > 4 else 1)
        for j, (lab, key) in enumerate([("Raise taxes", "raise"), ("Cut benefits", "cut"), ("Borrow even more", "borrow")]):
            x = W / 2 + (j - 1) * 420
            aj = ch * c.pa(3, key, 0.4)
            d.rounded_rectangle((x - 180, 620, x + 180, 720), radius=12, outline=mix(GREY, aj), width=2)
            text(d, (x, 670), lab, 36, WHITE, aj, "Medium", "mm")
    if n > 4:
        items = [("Slower growth", 4), ("Stubborn inflation", 5), ("Investors losing faith", 6)]
        for j, (lab, cue) in enumerate(items):
            if cue < n:
                text(d, (W / 2 + (j - 1) * 480, 700), lab, 40, WHITE, c.p(cue, 0.5), "SemiBold", "mm")
    source(d, D.SRC_BEO, ease(c.t))


@scene("record2030")
def s_record2030(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    big = ease(c.since(0) / 0.6) * (1 - ease((c.t - c.start(1)) / 0.5)) if n > 1 else ease(c.since(0) / 0.6)
    text(d, (W / 2, H / 2), "2030", 260, ACCENT, big, "Bold", "mm", True)
    if n > 1:
        a = c.p(1, 0.8)
        text(d, (MX, 170), "Debt held by the public, % of GDP", 46, WHITE, a, "SemiBold", display=True)
        X, Y = chart_axes(d, (230, 300, 1640, 880), (1938, 2038), (0, 130), a, range(1940, 2040, 10), [0, 25, 50, 75, 100, 125])
        hist = [(X(x), Y(v)) for x, v in D.DEBT_GDP_HIST]
        proj = [(X(x), Y(v)) for x, v in D.DEBT_GDP_PROJ]
        p = ease_out((c.t - c.start(1)) / 2.5)
        polyline(d, partial(hist, p), BLUE, a, 5)
        y106 = Y(106)
        dashed(d, (X(1946), y106), (X(2037), y106), GREY, a * 0.8, 2)
        dot(d, (X(1946), y106), 9, WHITE, a)
        text(d, (X(1946) + 18, y106 - 30), "1946 record: 106%", 28, WHITE, a, "SemiBold", "lm")
        q = ease_out((c.t - c.start(1) - 2.3) / 1.6)
        if q > 0:
            for i in range(len(proj) - 1):
                seg = partial(proj, q)
                for j in range(len(seg) - 1):
                    dashed(d, seg[j], seg[j + 1], ACCENT, 1, 5, 14, 9)
            if q >= 1:
                dot(d, (X(2030), Y(D.DEBT_GDP_PROJ[1][1])), 11, ACCENT)
                text(d, (X(2030) - 20, Y(D.DEBT_GDP_PROJ[1][1]) - 60), "2030: record broken", 32, ACCENT, 1,
                     "SemiBold", "rm")
                tag(d, "CBO PROJECTION", 1)
        source(d, D.SRC_BEO + " · history approximate; projection simplified to CBO anchor points", a)


@scene("slipping")
def s_slipping(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    tag(d, "A POSSIBLE PATH — NOT A PREDICTION", ease(c.t / 0.6))
    lit = [1, 1, 1, 1, c.p(1, 0.8) if n > 1 else 0]
    fade = ease((c.t - c.start(3)) / 4.5) if n > 3 else 0
    draw_chain(d, lit, ease(c.t / 0.6), y=330, faded=fade * 0.85)
    if n > 2:
        text(d, (W / 2, 700), "Not in a day.", 48, GREY, c.p(2, 0.6) * (1 - fade), "SemiBold", "mm", True)
    if n > 3:
        text(d, (W / 2, 700), "Year by year.", 48, WHITE, c.p(3, 0.6) * (1 - 0.5 * fade) * ease(fade * 5), "SemiBold",
             "mm", True)


@scene("window")
def s_window(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    close = ease((c.t - (c.start(2) if n > 2 else c.dur)) / 5.0)
    gap = 780 * (1 - 0.45 * close)
    a = ease(c.t / 0.8)
    d.rectangle((W / 2 - gap / 2, 220, W / 2 + gap / 2, 860), fill=mix(BLUE_D, a * 0.55))
    d.line((W / 2 - gap / 2, 220, W / 2 - gap / 2, 860), fill=mix(BLUE, a), width=3)
    d.line((W / 2 + gap / 2, 220, W / 2 + gap / 2, 860), fill=mix(BLUE, a), width=3)
    text(d, (W / 2, 380), "Guaranteed?", 60, WHITE, c.p(0, 0.5), "SemiBold", "mm", True)
    text(d, (W / 2, 470), "No.", 80, ACCENT, c.pa(0, "No", 0.4), "Bold", "mm", True)
    if n > 1:
        for j, (lab, key) in enumerate([("Smart reforms", "Smart"), ("Stronger growth", "stronger"),
                                        ("Tough decisions", "tough")]):
            text(d, (W / 2, 600 + j * 60), lab, 36, WHITE, c.pa(1, key, 0.5), "Medium", "mm")
    if n > 2:
        text(d, (W / 2, 950), "the window gets a little smaller", 30, GREY, c.pa(2, "the window", 0.6), "Regular", "mm")


# ======================================================================= conclusion
@scene("conc_q")
def s_conc_q(d, fr, c):
    hdr(d, c)
    word_reveal(d, (W / 2, H / 2), "Will America collapse because of its debt?", 70, c.since(0) - 0.3, 1.8, WHITE,
                "SemiBold", display=True)


@scene("futures")
def s_futures(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    if n > 1:
        text(d, (W / 2, H / 2), "The honest answer", 60, WHITE, c.p(0, 0.5) * ease((c.start(1) - c.t) / 0.4),
             "SemiBold", "mm", True)
    futs = [("Bankruptcy", "bankrupt", "UNLIKELY", GREY, 2), ("A painful crisis", "painful", "POSSIBLE", BLUE, 3),
            ("Losing the crown", "losing its crown", "WORTH WATCHING", ACCENT, 5)]
    for k, (lab, key, verdict, col, cue) in enumerate(futs):
        x = W / 2 + (k - 1) * 520
        a = c.pa(1, key, 0.6) if n > 1 else 0
        d.rounded_rectangle((x - 230, 320, x + 230, 620), radius=18, fill=mix(PANEL, a), outline=mix(LINE, a), width=2)
        text(d, (x, 380), f"FUTURE {k + 1}", 22, GREY, a, "SemiBold", "mm", spacing=4, base=PANEL)
        text(d, (x, 480), lab, 44, WHITE, a, "SemiBold", "mm", True, base=PANEL)
        v = c.p(cue, 0.5) if cue < n else 0
        if k == 2 and n > 4:
            v = c.p(5, 0.5) if n > 5 else 0
        text(d, (x, 720), verdict, 40, col, v, "Bold", "mm", spacing=4)
        if v > 0:
            d.rounded_rectangle((x - 230, 320, x + 230, 620), radius=18, outline=mix(col, v), width=3)


@scene("conc_cbo")
def s_conc_cbo(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    a = ease(c.t / 0.6)
    tag(d, "CBO PROJECTION", a)
    text(d, (MX, 190), "Debt held by the public, % of GDP", 46, WHITE, a, "SemiBold", display=True)
    p = ease_out((c.t - c.at(0, "rising")) / 2.2)
    for k, (lab, v) in enumerate([("2026", D.DEBT_GDP_2026), ("2036", D.DEBT_GDP_2036)]):
        x = 520 + k * 520
        h = 460 * v / 125 * (p if k else ease_out(c.t / 1.0))
        if k == 0:
            d.rectangle((x - 120, 860 - h, x + 120, 860), fill=mix(BLUE, a))
        else:
            d.rectangle((x - 120, 860 - h, x + 120, 860), outline=mix(ACCENT, a), width=4)
        text(d, (x, 860 - h - 46), f"{v}%", 64, ACCENT if k else WHITE, a if k == 0 else p, "Bold", "mm", True)
        text(d, (x, 900), lab, 32, GREY, a, "SemiBold", "mm")
    y106 = 860 - 460 * 106 / 125
    dashed(d, (360, y106), (1260, y106), GREY, a * 0.8, 2)
    text(d, (345, y106), "1946 record 106%", 24, GREY, a, "Regular", "rm")
    if n > 1:
        b = c.p(1, 0.6)
        text(d, (1400, 330), "Net interest", 30, GREY, b, "Medium", "lm")
        text(d, (1400, 390), "$1.14T → $2.1T", 48, ACCENT, b, "Bold", "lm", True)
        text(d, (1400, 445), "per year by 2036", 26, GREY, b, "Regular", "lm")
    if n > 3:
        text(d, (1400, 720), "Direction: clear ↑", 40, WHITE, c.p(3, 0.5), "SemiBold", "lm")
    source(d, D.SRC_BEO, a)


@scene("final")
def s_final(d, fr, c):
    n = len(c.cues)
    text(d, (W / 2, 450), "The real question isn't whether America can borrow.", 54, GREY, c.p(0, 0.8), "SemiBold",
         "mm", True)
    if n > 1:
        text(d, (W / 2, 580), "It's how long the world will keep believing it should.", 58, WHITE, c.p(1, 1.2),
             "SemiBold", "mm", True)


@scene("outro")
def s_outro(d, fr, c):
    n = len(c.cues)
    out = ease((c.start(3) - c.t) / 0.4) if n > 3 else 1
    text(d, (W / 2, 330), "What do you think?", 66, WHITE, c.p(0, 0.6) * out, "SemiBold", "mm", True)
    if n > 1:
        text(d, (W / 2 - 330, 500), "Ticking time bomb", 48, ACCENT, c.pa(1, "ticking", 0.6) * out, "SemiBold", "mm", True)
        text(d, (W / 2, 500), "or", 40, GREY, c.pa(1, "or a problem", 0.6) * out, "Regular", "mm")
        text(d, (W / 2 + 330, 500), "Fixed in time", 48, BLUE, c.pa(1, "fix", 0.6) * out, "SemiBold", "mm", True)
    if n > 2:
        text(d, (W / 2, 660), "Drop your answer in the comments", 38, GREY, c.p(2, 0.6) * out, "Medium", "mm")
    if n > 3:
        for k, (lab, key) in enumerate([("Who actually owns all this debt?", "who actually"),
                                        ("Could the dollar lose its throne?", "whether the dollar")]):
            x = W / 2 + (k - 0.5) * 680
            a = c.pa(3, key, 0.6)
            d.rounded_rectangle((x - 310, 400, x + 310, 640), radius=18, fill=mix(PANEL, a), outline=mix(LINE, a), width=2)
            text(d, (x, 450), "NEXT?", 22, ACCENT, a, "SemiBold", "mm", spacing=5, base=PANEL)
            for i, ln in enumerate(wrap(lab, 44, 540, "SemiBold", True)):
                text(d, (x, 520 + i * 54), ln, 44, WHITE, a, "SemiBold", "mm", True, base=PANEL)
    if n > 4:
        text(d, (W / 2, 780), "That story is even scarier.", 40, GREY, c.p(4, 0.6), "Medium", "mm")


# ======================================================================= cold open: the Roman mirror
SILVER, BRONZE = (214, 218, 225), (146, 104, 70)


def draw_coin(d, cx, cy, R, metal, a, label=""):
    """Original coin drawing: rim, beaded border, laurel wreath, value in the centre."""
    if a <= 0.01:
        return
    rim = tuple(int(c * 0.62) for c in metal)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=mix(metal, a), outline=mix(rim, a), width=5)
    for i in range(84):
        ang = 2 * math.pi * i / 84
        r = R - 17
        dot(d, (cx + r * math.cos(ang), cy + r * math.sin(ang)), 3.4, rim, a)
    d.ellipse((cx - R + 34, cy - R + 34, cx + R - 34, cy + R - 34), outline=mix(rim, a), width=2)
    for side in (-1, 1):                                    # laurel: leaves along two arcs
        for j in range(11):
            ang = math.pi / 2 + side * (0.35 + j * 0.2)
            r = R - 58
            x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
            lx, ly = 13 * math.cos(ang + side * 1.1), 13 * math.sin(ang + side * 1.1)
            d.polygon([(x - lx, y - ly), (x + ly * 0.45, y - lx * 0.45), (x + lx, y + ly),
                       (x - ly * 0.45, y + lx * 0.45)], fill=mix(rim, a))
    if label:
        text(d, (cx, cy - 6), label, int(R * 0.42), rim, a, "Bold", "mm", True, base=metal)
        text(d, (cx, cy + R * 0.32), "SILVER", int(R * 0.12), rim, a, "SemiBold", "mm", spacing=6, base=metal)


@scene("rome_intro")
def s_rome_intro(d, fr, c):
    n = len(c.cues)
    out = ease((c.start(1) - c.t) / 0.4) if n > 1 else 1
    if out > 0.98:
        word_reveal(d, (W / 2, H / 2), "This has happened before.", 76, c.since(0), 1.0, WHITE, "SemiBold",
                    display=True)
    else:
        text(d, (W / 2, H / 2), "This has happened before.", 76, WHITE, out, "SemiBold", "mm", True)
    if n > 1:
        a = c.p(1, 1.2)
        tint_layer(fr, columns_drawing(), WHITE, 0.5 * a, (W / 2, 600), 0.74 + 0.02 * c.p(1, 8.0))
        text(d, (W / 2, 190), "ROME · THIRD CENTURY AD", 30, ACCENT, a, "SemiBold", "mm", spacing=10)
        text(d, (W / 2, 1000), "Original illustration", 18, DIM, a, "Regular", "mm")


@scene("rome_coin")
def s_rome_coin(d, fr, c):
    n = len(c.cues)
    a = ease(c.t / 0.7)
    deb = ease((c.t - c.at(1, "went from")) / 4.0) if n > 1 else 0.0       # debasement progress
    metal = tuple(int(lerp(SILVER[i], BRONZE[i], deb)) for i in range(3))
    pct = round(lerp(95, 5, deb))
    draw_coin(d, 520, 560, 250, metal, a, f"~{pct}%")
    text(d, (520, 870), "Rome's main silver coin", 28, GREY, a, "Medium", "mm")
    if n > 0:
        text(d, (1000, 210), "To pay soldiers and fund wars, Rome watered down its money", 30, WHITE,
             c.pa(0, "watered", 0.6), "Medium", "la")
    x0, base, hmax = 1080, 820, 470
    keys = ["almost pure", "went from", "only a few"]
    for k, (when, who, v) in enumerate(D.ROME_SILVER):
        x = x0 + k * 250
        g = c.pa(1, keys[k], 0.9) if n > 1 else 0
        if g <= 0:
            continue
        h = hmax * v / 100 * g
        col = tuple(int(lerp(SILVER[i], BRONZE[i], k / 2)) for i in range(3))
        d.rectangle((x - 70, base - h, x + 70, base), fill=mix(col, g))
        text(d, (x, base - h - 36), f"~{v}%", 44, WHITE, g, "Bold", "mm", True)
        text(d, (x, base + 36), when, 26, WHITE, g, "SemiBold", "mm")
        text(d, (x, base + 70), who, 22, GREY, g, "Regular", "mm")
    hline(d, x0 - 110, x0 + 610, base, DIM, a, 2)
    source(d, D.SRC_ROME, a)


@scene("rome_edict")
def s_rome_edict(d, fr, c):
    n = len(c.cues)
    a = ease(c.t / 0.6)
    p = ease_out(c.since(0) / 2.4)
    pts = [(170 + i * 7, 760 - (i / 100) ** 2.6 * 430 - 6 * math.sin(i * 0.5)) for i in range(101)]
    polyline(d, partial(pts, p), ACCENT, a, 5)
    hline(d, 160, 880, 772, DIM, a, 2)
    text(d, (170, 300), "Prices", 34, WHITE, a, "SemiBold", "la")
    text(d, (170, 344), "schematic, not to scale", 20, GREY, a, "Regular", "la")
    text(d, (250, 430), "trust in the money ↓", 30, ACCENT, c.pa(0, "trust", 0.6), "Medium", "la")
    if n > 1:
        b = c.p(1, 0.7) * (1 - 0.45 * (c.p(2, 0.5) if n > 2 else 0))
        x0, y0, x1, y1 = 1050, 280, 1700, 740
        d.rounded_rectangle((x0, y0, x1, y1), radius=16, fill=mix(PANEL, b), outline=mix(LINE, b), width=2)
        text(d, (x0 + 40, y0 + 70), "301 AD", 64, WHITE, b, "Bold", "lm", True, base=PANEL)
        text(d, (x0 + 40, y0 + 140), "EDICT ON MAXIMUM PRICES", 26, ACCENT, b, "SemiBold", "lm", spacing=3, base=PANEL)
        text(d, (x0 + 40, y0 + 186), "Emperor Diocletian caps prices by decree", 26, GREY, b, "Regular", "lm",
             base=PANEL)
        for i in range(5):                                  # decorative rows (not legible text)
            w = [520, 470, 540, 380, 450][i]
            d.rounded_rectangle((x0 + 40, y0 + 250 + i * 34, x0 + 40 + w, y0 + 262 + i * 34), radius=6,
                                fill=mix(LINE, b, base=PANEL))
    if n > 2:
        text(d, (1375, 820), "It didn't work.", 60, ACCENT, c.p(2, 0.5), "Bold", "mm", True)


@scene("rome_fall")
def s_rome_fall(d, fr, c):
    n = len(c.cues)
    a = ease(c.t / 0.8)
    tint_layer(fr, columns_drawing(), GREY, 0.22 * a, (W / 2, 560), 0.8)
    x0, x1, y = 260, 1660, 560
    hline(d, x0 - 40, x0 - 40 + (x1 - x0 + 80) * ease_out(c.t / 1.6), y, LINE, 1, 3)

    def X(year):
        return x0 + (year - 265) / (476 - 265) * (x1 - x0)

    ev = [(265, "c. 265 AD", "coins ~5% silver", ease((c.t - 0.3) / 0.6), GREY),
          (301, "301 AD", "price edict fails", ease((c.t - 0.7) / 0.6), GREY),
          (476, "476 AD", "Western Empire falls", c.pa(0, "476", 0.6), ACCENT)]
    for k, (yr, when, what, ak, col) in enumerate(ev):
        x = X(yr)
        dot(d, (x, y), 11 if yr == 476 else 9, col if yr == 476 else WHITE, ak)
        up = k == 1
        text(d, (x, y - 70 if not up else y + 60), when, 34, WHITE, ak, "SemiBold", "mm")
        text(d, (x, y - 30 if not up else y + 100), what, 24, col if yr == 476 else GREY, ak, "Regular", "mm")
    if n > 0:
        text(d, (X(380), y - 150), "almost two more centuries", 28, GREY, c.pa(0, "two more", 0.8), "Medium", "mm")
    if n > 1:
        b = c.p(1, 0.8)
        text(d, (W / 2, 800), "It weakened slowly.", 58, WHITE, b, "SemiBold", "mm", True)
        text(d, (W / 2, 870), "costs outran income · the money lost people's trust", 30, GREY,
             c.pa(1, "as its costs", 0.8), "Regular", "mm")


@scene("rome_us")
def s_rome_us(d, fr, c):
    n = len(c.cues)
    lift = ease((c.t - c.start(1)) / 0.6) if n > 1 else 0
    text(d, (W / 2, lerp(H / 2, 190, lift)), "America is not Rome.", lerp(80, 50, lift), WHITE, c.p(0, 0.6),
         "SemiBold", "mm", True)
    if n > 1:
        rows = [("Debased its coins", "Borrows by selling Treasury bonds", "debasing"),
                ("An ancient empire", "The world's largest economy", "largest")]
        xl, xr = W / 2 - 400, W / 2 + 400
        h = c.p(1, 0.6)
        text(d, (xl, 300), "ROME", 30, GREY, h, "SemiBold", "mm", spacing=8)
        text(d, (xr, 300), "AMERICA", 30, BLUE, h, "SemiBold", "mm", spacing=8)
        hline(d, W / 2 - 700, W / 2 + 700, 335, LINE, h, 2)
        for j, (rome, us, key) in enumerate(rows):
            g = c.pa(1, key, 0.6) if j else c.pa(1, "borrows", 0.6)
            y = 410 + j * 110
            text(d, (xl, y), rome, 36, WHITE, g, "Medium", "mm")
            text(d, (xr, y), us, 36, WHITE, g, "Medium", "mm")
    if n > 2:
        text(d, (W / 2, 720), "Different tools. Same question:", 40, GREY, c.p(2, 0.6), "Medium", "mm")
        word_reveal(d, (W / 2, 800), "How long will the world keep trusting the money?", 50,
                    c.t - c.at(2, "how long"), 1.6, WHITE, "SemiBold", display=True, highlight=("trusting",))


# ======================================================================= household impact
@scene("door1_mortgage")
def s_door1_mortgage(d, fr, c):
    header(d, "Door 1 · What it means at home", ease(c.t / 0.6))
    tag(d, "ILLUSTRATION", ease(c.t / 0.6), color=BLUE)
    n = len(c.cues)
    text(d, (W / 2, 200), "For families, this isn't abstract.", 46, GREY, c.p(0, 0.6), "Medium", "mm")
    if n > 1:
        a = c.p(1, 0.6)
        text(d, (W / 2 - 230, 320), "Treasury yields ↑", 42, WHITE, a, "SemiBold", "mm")
        arrow(d, (W / 2 - 20, 320), (W / 2 + 60, 320), BLUE, c.p(1, 0.6, 0.3), 4, 16)
        text(d, (W / 2 + 270, 320), "Mortgage rates ↑", 42, ACCENT, c.p(1, 0.6, 0.5), "SemiBold", "mm")
    if n > 2:
        p_, r1, r2 = D.MORTGAGE
        m1, m2 = D.mortgage_payment(p_, r1), D.mortgage_payment(p_, r2)
        b = c.p(2, 0.7)
        x0, y0, x1, y1 = 520, 420, 1400, 880
        d.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=mix(PANEL, b), outline=mix(LINE, b), width=2)
        text(d, (x0 + 50, y0 + 60), f"30-year mortgage · ${p_:,.0f}", 34, WHITE, b, "SemiBold", "lm", base=PANEL)
        for j, (r, m) in enumerate([(r1, m1), (r2, m2)]):
            g = c.pa(2, "every extra", 0.6) if j else b
            text(d, (x0 + 50, y0 + 150 + j * 80), f"At {r * 100:.0f}%", 34, GREY, g, "Medium", "lm", base=PANEL)
            text(d, (x1 - 50, y0 + 150 + j * 80), f"${m:,.0f} a month", 40, WHITE, g, "SemiBold", "rm", True,
                 base=PANEL)
        k = c.pa(2, "roughly", 0.6)
        hline(d, x0 + 50, x1 - 50, y0 + 300, LINE, k, 2)
        text(d, (x0 + 50, y0 + 370), f"+${m2 - m1:,.0f} a month", 60, ACCENT, k, "Bold", "lm", True, base=PANEL)
        text(d, (x1 - 50, y0 + 370), f"≈ ${12 * (m2 - m1):,.0f} a year", 32, GREY, k, "Regular", "rm", base=PANEL)
    source(d, "Standard fixed-rate amortisation; illustrative rates of 6% and 7%", ease(c.t))


@scene("door2_imports")
def s_door2_imports(d, fr, c):
    header(d, "Door 2 · What it means at home", ease(c.t / 0.6))
    tag(d, "SCENARIO", 1)
    n = len(c.cues)
    text(d, (W / 2, 210), "Weaker dollar → pricier imports", 52, WHITE, c.p(0, 0.6), "SemiBold", "mm", True)
    if n > 1:
        items = [("Phones", "phones"), ("Cars", "cars"), ("Clothes", "clothes"), ("Coffee", "coffee")]
        for j, (lab, key) in enumerate(items):
            g = c.pa(1, key, 0.5)
            x = W / 2 + (j - 1.5) * 330
            d.rounded_rectangle((x - 140, 330, x + 140, 520), radius=16, fill=mix(PANEL, g), outline=mix(LINE, g),
                                width=2)
            text(d, (x, 400), lab, 44, WHITE, g, "SemiBold", "mm", True, base=PANEL)
            text(d, (x, 466), "price ↑", 30, ACCENT, g, "Medium", "mm", base=PANEL)
        text(d, (W / 2, 590), "Foreign sellers want more dollars for the same goods", 28, GREY,
             c.pa(1, "Foreign", 0.6), "Regular", "mm")
    if n > 2:
        g = c.p(2, 0.6)
        shrink = ease((c.t - c.at(2, "buys less")) / 2.0)
        text(d, (560, 720), "Same paycheck", 40, WHITE, g, "SemiBold", "mm")
        d.rounded_rectangle((420, 760, 700, 820), radius=10, outline=mix(BLUE, g), width=3)
        text(d, (560, 790), "$", 34, BLUE, g, "Bold", "mm", True)
        arrow(d, (760, 790), (880, 790), DIM, g, 3, 14)
        text(d, (1120, 720), "What it buys", 40, WHITE, g, "SemiBold", "mm")
        w = 520 * (1 - 0.22 * shrink)
        d.rectangle((940, 765, 940 + w, 815), fill=mix(BLUE, g))
        d.rectangle((940 + w, 765, 1460, 815), outline=mix(ACCENT, g * shrink), width=2)
        text(d, (1200, 860), "illustrative", 20, DIM, g, "Regular", "mm")


@scene("wallet")
def s_wallet(d, fr, c):
    hdr(d, c)
    n = len(c.cues)
    a = c.p(0, 0.6)
    text(d, (W / 2, 250), "Not a headline about collapse.", 56, GREY, a, "SemiBold", "mm", True)
    if n > 1:
        text(d, (W / 2, 330), "A quiet squeeze on household budgets", 34, WHITE, c.pa(1, "quietly", 0.6), "Medium", "mm")
        cards = [("Pricier loans", "mortgages · car loans · credit cards", "loans"),
                 ("Pricier imports", "if the dollar weakens", "imports"),
                 ("Less room in the budget", "as interest takes a bigger share", "less room")]
        for j, (title, sub, key) in enumerate(cards):
            g = c.pa(1, key, 0.6)
            x = W / 2 + (j - 1) * 560
            d.rounded_rectangle((x - 250, 440, x + 250, 700), radius=18, fill=mix(PANEL, g),
                                outline=mix(ACCENT if j == 0 else LINE, g), width=2)
            text(d, (x, 530), title, 42, WHITE, g, "SemiBold", "mm", True, base=PANEL)
            text(d, (x, 610), sub, 26, GREY, g, "Regular", "mm", base=PANEL)
