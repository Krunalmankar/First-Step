"""Drawing primitives and the visual identity (charcoal / white / muted blue + one accent)."""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
FPS = 24
MX = 120  # horizontal safe margin

BG = (16, 20, 27)   # matches the centre of the background gradient
PANEL = (24, 29, 37)
INK = (10, 12, 17)    # dark text on coloured fills (distinct from BG, which SDraw treats as invisible)
WHITE = (236, 238, 241)
GREY = (140, 149, 164)
DIM = (66, 74, 88)
LINE = (44, 51, 63)
BLUE = (98, 136, 190)
BLUE_D = (50, 70, 102)
ACCENT = (235, 96, 60)

FONT_DIR = "/usr/share/fonts/opentype/inter/"


class SDraw(ImageDraw.ImageDraw):
    """ImageDraw that skips shapes whose colours have faded fully to the background colour,
    so invisible elements never leave flat patches on the background gradient."""

    @staticmethod
    def _gone(*cols):
        return all(c is None or c == BG for c in cols)

    def rectangle(self, xy, fill=None, outline=None, width=1):
        if not self._gone(fill, outline):
            super().rectangle(xy, fill, outline, width)

    def rounded_rectangle(self, xy, radius=0, fill=None, outline=None, width=1, **kw):
        if not self._gone(fill, outline):
            super().rounded_rectangle(xy, radius, fill, outline, width, **kw)

    def polygon(self, xy, fill=None, outline=None, width=1):
        if not self._gone(fill, outline):
            super().polygon(xy, fill, outline, width)

    def ellipse(self, xy, fill=None, outline=None, width=1):
        if not self._gone(fill, outline):
            super().ellipse(xy, fill, outline, width)

    def line(self, xy, fill=None, width=0, joint=None):
        if not self._gone(fill):
            super().line(xy, fill, width, joint)

    def text(self, xy, txt, fill=None, *a, **kw):
        if not self._gone(fill):
            super().text(xy, txt, fill, *a, **kw)


@lru_cache(maxsize=256)
def font(size, weight="Regular", display=False):
    fam = "InterDisplay" if display else "Inter"
    return ImageFont.truetype(f"{FONT_DIR}{fam}-{weight}.otf", int(size))


# ---------------------------------------------------------------- easing / timing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):  # smooth in-out
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c, a, base=BG):
    """Colour c at opacity a over the background colour."""
    a = clamp(a)
    return tuple(int(base[i] + (c[i] - base[i]) * a) for i in range(3))


# ---------------------------------------------------------------- background
@lru_cache(maxsize=1)
def background():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W * 0.5) / (W * 0.62)) ** 2 + ((y - H * 0.45) / (H * 0.75)) ** 2)
    v = np.clip(1.0 - 0.55 * r ** 2, 0.35, 1.0)
    base = np.array([17, 21, 28], np.float32)
    img = base[None, None, :] * v[..., None]
    img += np.array([2, 3, 6], np.float32) * (1 - y / H)[..., None]
    # tiny dither to stop banding in the gradient (not a grain effect)
    img += np.random.default_rng(1).uniform(-0.6, 0.6, img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- text
def text(d, xy, s, size, color=WHITE, a=1.0, weight="Regular", anchor="la", display=False, spacing=0, base=BG):
    if a <= 0.003:
        return
    f = font(size, weight, display)
    if spacing:
        tracked(d, xy, s, f, mix(color, a, base), spacing, anchor)
    else:
        d.text(xy, s, font=f, fill=mix(color, a, base), anchor=anchor)


def tracked(d, xy, s, f, fill, spacing, anchor):
    widths = [f.getlength(ch) for ch in s]
    total = sum(widths) + spacing * (len(s) - 1)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    for ch, w in zip(s, widths):
        d.text((x, y), ch, font=f, fill=fill, anchor="l" + anchor[1])
        x += w + spacing


def text_width(s, size, weight="Regular", display=False):
    return font(size, weight, display).getlength(s)


def wrap(s, size, maxw, weight="Regular", display=False):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_width(t, size, weight, display) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def paragraph(d, xy, s, size, maxw, color=WHITE, a=1.0, weight="Regular", lh=1.25, anchor="la", display=False):
    lines = wrap(s, size, maxw, weight, display)
    x, y = xy
    n = len(lines)
    if anchor[1] == "m":
        y -= (n - 1) * size * lh / 2
    for i, ln in enumerate(lines):
        text(d, (x, y + i * size * lh), ln, size, color, a, weight, anchor, display)
    return y + n * size * lh


def word_reveal(d, xy, s, size, t, dur, color=WHITE, weight="Regular", anchor="mm", display=False, highlight=()):
    """Words fade up one after another across dur seconds (local time t). Single line."""
    words = s.split()
    f = font(size, weight, display)
    sp = f.getlength(" ")
    widths = [f.getlength(w) for w in words]
    total = sum(widths) + sp * (len(words) - 1)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    for i, (w, wd) in enumerate(zip(words, widths)):
        a = ease((t - dur * i / max(1, len(words))) / 0.35)
        col = ACCENT if w.strip(".,?!:\"") in highlight else color
        d.text((x, y), w, font=f, fill=mix(col, a), anchor="l" + anchor[1])
        x += wd + sp


# ---------------------------------------------------------------- furniture
def header(d, label, a=1.0):
    """Small chapter label, top-left."""
    text(d, (MX, 70), label.upper(), 20, GREY, a * 0.9, "Medium", spacing=3)


def source(d, s, a=1.0):
    text(d, (MX, H - 62), s, 19, GREY, a * 0.85, "Regular")


def tag(d, s, a=1.0, xy=None, color=ACCENT):
    """Outlined pill label such as SCENARIO or PROJECTION (top-right by default)."""
    if a <= 0.003:
        return
    f = font(19, "SemiBold")
    w = sum(f.getlength(c) for c in s) + 2.5 * (len(s) - 1)
    x, y = xy or (W - MX - w - 36, 56)
    d.rounded_rectangle((x, y, x + w + 36, y + 38), radius=19, outline=mix(color, a), width=2)
    tracked(d, (x + 18, y + 19), s, f, mix(color, a), 2.5, "lm")


def hline(d, x0, x1, y, color=LINE, a=1.0, width=2):
    d.line((x0, y, x1, y), fill=mix(color, a), width=width)


def dashed(d, p0, p1, color, a=1.0, width=3, dash=14, gap=10):
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L == 0:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    s = 0
    while s < L:
        e = min(L, s + dash)
        d.line((x0 + ux * s, y0 + uy * s, x0 + ux * e, y0 + uy * e), fill=mix(color, a), width=width)
        s += dash + gap


def polyline(d, pts, color, a=1.0, width=4):
    if len(pts) >= 2:
        d.line(pts, fill=mix(color, a), width=width, joint="curve")


def dot(d, xy, r, color, a=1.0, outline=None):
    x, y = xy
    d.ellipse((x - r, y - r, x + r, y + r), fill=mix(color, a), outline=outline)


def arrow(d, p0, p1, color, a=1.0, width=3, head=14):
    d.line((*p0, *p1), fill=mix(color, a), width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    pts = [p1,
           (p1[0] - head * math.cos(ang - 0.45), p1[1] - head * math.sin(ang - 0.45)),
           (p1[0] - head * math.cos(ang + 0.45), p1[1] - head * math.sin(ang + 0.45))]
    d.polygon(pts, fill=mix(color, a))


def partial(pts, p):
    """First fraction p (0..1) of a polyline, by length."""
    if p >= 1 or len(pts) < 2:
        return list(pts)
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    target = sum(seg) * clamp(p)
    out = [pts[0]]
    for i, L in enumerate(seg):
        if target <= L:
            f = target / L if L else 0
            out.append((lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f)))
            return out
        target -= L
        out.append(pts[i + 1])
    return out


def money(v, dec=0):
    return f"${v:,.{dec}f}"


# ---------------------------------------------------------------- textures (original, procedural)
@lru_cache(maxsize=1)
def guilloche():
    """Engraved rosette lines reminiscent of a bond certificate. Purely procedural."""
    S = 1400
    img = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(img)
    c = S / 2
    for k in range(46):
        R, r, p = 520 - k * 2.2, 37 + (k % 5), 120 + k * 3
        pts = []
        for i in range(2400):
            t = i / 2400 * 2 * math.pi * 12
            x = (R - r) * math.cos(t) + p * math.cos((R - r) / r * t)
            y = (R - r) * math.sin(t) - p * math.sin((R - r) / r * t)
            pts.append((c + x * 0.98, c + y * 0.98))
        d.line(pts, fill=90 if k % 3 else 150, width=1)
    return img.filter(ImageFilter.GaussianBlur(0.4))


def tint_layer(frame, mask_l, color, a, center, scale=1.0, rot=0.0):
    """Composite a greyscale mask as a coloured, translucent layer onto frame."""
    m = mask_l
    if rot:
        m = m.rotate(rot, resample=Image.BILINEAR)
    if scale != 1.0:
        m = m.resize((int(m.width * scale), int(m.height * scale)), Image.BILINEAR)
    m = m.point(lambda v: int(v * clamp(a)))
    col = Image.new("RGB", m.size, color)
    frame.paste(col, (int(center[0] - m.width / 2), int(center[1] - m.height / 2)), m)


@lru_cache(maxsize=1)
def columns_drawing():
    """Minimal line drawing of a classical colonnade (original artwork)."""
    S_W, S_H = 1700, 820
    img = Image.new("L", (S_W, S_H), 0)
    d = ImageDraw.Draw(img)
    base_y, top_y = 740, 170
    d.line((40, base_y + 40, S_W - 40, base_y + 40), fill=200, width=3)
    d.line((70, base_y + 14, S_W - 70, base_y + 14), fill=160, width=2)
    d.polygon([(110, top_y - 40), (S_W / 2, 20), (S_W - 110, top_y - 40)], outline=170)
    d.line((110, top_y - 40, S_W - 110, top_y - 40), fill=170, width=2)
    d.line((100, top_y - 8, S_W - 100, top_y - 8), fill=170, width=2)
    n = 8
    for i in range(n):
        if i in (5,):           # one fallen column: the gap tells the story
            cx = 180 + i * (S_W - 360) / (n - 1)
            d.line((cx - 140, base_y + 6, cx + 120, base_y - 26), fill=110, width=2)
            d.line((cx - 140, base_y - 44, cx + 120, base_y - 76), fill=110, width=2)
            continue
        cx = 180 + i * (S_W - 360) / (n - 1)
        h = top_y if i != 6 else top_y + 260   # a broken one
        w = 46
        d.rectangle((cx - w - 12, h - 8, cx + w + 12, h + 8), outline=170)
        d.rectangle((cx - w - 12, base_y - 8, cx + w + 12, base_y + 8), outline=170)
        for f in range(-3, 4):
            x = cx + f * w / 3.4
            d.line((x, h + 8, x, base_y - 8), fill=120 if f else 180, width=2)
    return img
