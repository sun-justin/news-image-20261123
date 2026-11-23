#!/usr/bin/env python3
"""THE WORLD TODAY - Monday 23 November 2026.

A pure-stdlib Python program that draws a dense newspaper front page
summing up the world news of Monday 23 November 2026 as a 1024x1024 PNG.

Everything is drawn from scratch in this file: a hand-built vector
serif font (strokes on a 9x16 grid, with serif ticks on vertical
stems), gradient skies, shaded illustrations, a world map, a markets
strip and 37 dated stories across 9 regions.

No network, no clock, no randomness: two runs write byte-identical
output.  Run with:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
The image is written to <MAKEFUN_OUTPUT_DIR>/entry.png.
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 242, 231)
INK = (22, 20, 17)
INK_SOFT = (58, 54, 48)
RED = (172, 32, 28)
BLUE = (28, 58, 108)
GOLD = (176, 132, 52)
GREY = (128, 122, 110)
RULE = (90, 82, 70)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.px[i], self.px[i + 1], self.px[i + 2] = c
                i += 3

    def vgrad(self, x, y, w, h, top, bot):
        for j in range(h):
            t = j / max(1, h - 1)
            c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
            self.rect(x, y + j, w, 1, c)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        # perpendicular offsets for thickness
        offs = []
        if t <= 1:
            offs = [(0, 0)]
        else:
            r = t // 2
            if abs(dx) >= abs(dy):
                offs = [(0, k) for k in range(-r, r + 1)]
            else:
                offs = [(k, 0) for k in range(-r, r + 1)]
        for s in range(steps + 1):
            px = x0 + dx * s // steps
            py = y0 + dy * s // steps
            for ox, oy in offs:
                self.set(px + ox, py + oy, c)

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def disc(self, cx, cy, r, c):
        self.circle(cx, cy, r, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        # scanline fill of a simple polygon
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.set(x, y, c)

    def frame(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)


def mix(a, b, t):
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


# ------------------------------------------------------- vector serif font
# Glyphs are strokes on a 9-wide, 16-tall grid: cap top y=0, x-height
# top y=5, baseline y=12, descenders to y=15.  Format per glyph:
# strokes separated by ';', points "x,y" separated by spaces.
# A stroke of one point is a dot.  Vertical stems get serif ticks
# at render time, which is what makes the face read as a serif.
FONT_RAW = {
    'A': "0,12 4,0 8,12;2,8 6,8",
    'B': "0,0 0,12;0,0 5,0 7,2 7,4 5,6 0,6;5,6 7,8 7,10 5,12 0,12",
    'C': "8,2 6,0 2,0 0,2 0,10 2,12 6,12 8,10",
    'D': "0,0 0,12;0,0 5,0 8,3 8,9 5,12 0,12",
    'E': "0,0 0,12;0,0 7,0;0,6 5,6;0,12 7,12",
    'F': "0,0 0,12;0,0 7,0;0,6 5,6",
    'G': "8,2 6,0 2,0 0,2 0,10 2,12 6,12 8,10 8,6;8,6 4,6",
    'H': "0,0 0,12;8,0 8,12;0,6 8,6",
    'I': "4,0 4,12;1,0 7,0;1,12 7,12",
    'J': "8,0 8,10 6,12 2,12 1,10;5,0 8,0",
    'K': "0,0 0,12;8,0 1,6;4,6 8,12",
    'L': "0,0 0,12;0,12 7,12",
    'M': "0,12 0,0 4,7 8,0 8,12",
    'N': "0,12 0,0 8,12 8,0",
    'O': "2,0 6,0 8,2 8,10 6,12 2,12 0,10 0,2 2,0",
    'P': "0,0 0,12;0,0 6,0 8,2 8,5 6,7 0,7",
    'Q': "2,0 6,0 8,2 8,10 6,12 2,12 0,10 0,2 2,0;5,8 8,12",
    'R': "0,0 0,12;0,0 6,0 8,2 8,5 6,7 0,7;4,7 8,12",
    'S': "7,2 5,0 2,0 1,2 1,4 3,5 7,6 8,8 8,10 6,12 3,12 1,10",
    'T': "0,0 8,0;4,0 4,12",
    'U': "0,0 0,10 2,12 6,12 8,10 8,0",
    'V': "0,0 4,12 8,0",
    'W': "0,0 2,12 4,5 6,12 8,0",
    'X': "0,0 8,12;8,0 0,12",
    'Y': "0,0 4,6 8,0;4,6 4,12",
    'Z': "0,0 8,0 0,12 8,12",
    '0': "2,0 6,0 8,2 8,10 6,12 2,12 0,10 0,2 2,0",
    '1': "4,0 4,12;1,3 4,0;1,12 7,12",
    '2': "1,2 3,0 6,0 8,2 8,5 0,12 8,12",
    '3': "1,1 3,0 6,0 8,2 8,5 6,6;6,6 8,7 8,10 6,12 3,12 1,11",
    '4': "6,0 0,8 8,8;6,0 6,12",
    '5': "8,0 0,0 0,6 6,6 8,8 8,10 6,12 2,12 0,10",
    '6': "7,1 5,0 2,1 1,3 1,9 2,12 5,12 8,10 8,7 6,5 3,5 1,7",
    '7': "0,0 8,0 4,12",
    '8': "3,0 6,0 8,2 8,5 6,6 2,6 0,5 0,2 2,0;2,6 0,7 0,10 2,12 6,12 8,10 8,7 6,6",
    '9': "1,4 2,1 5,0 7,1 8,3 8,9 7,12 4,12 2,11;1,4 3,6 6,6 8,4",
}

FONT_RAW.update({
    'a': "8,5 8,12;7,5 4,5 2,6 1,8 1,10 3,12 6,12 8,10",
    'b': "0,0 0,12;0,7 4,5 7,6 8,8 8,10 6,12 3,12 0,10",
    'c': "7,6 5,5 2,5 1,7 1,10 2,12 5,12 7,11",
    'd': "8,0 8,12;8,7 5,5 2,6 1,8 1,10 3,12 6,12 8,10",
    'e': "7,10 5,12 2,12 1,10 1,7 2,5 5,5 7,7 7,8 1,8",
    'f': "6,0 4,0 3,1 3,12;1,4 6,4",
    'g': "8,5 8,14;7,5 4,5 2,6 1,8 1,10 3,12 6,12 8,10;8,14 5,15 2,15 1,13",
    'h': "0,0 0,12;0,7 4,5 7,6 8,8 8,12",
    'i': "4,5 4,12;4,2",
    'j': "5,5 5,14;5,14 3,15 1,14;5,2",
    'k': "0,0 0,12;7,5 1,8;3,8 7,12",
    'l': "3,0 3,12;3,12 6,12",
    'm': "0,5 0,12;0,5 3,5 4,7 4,12;4,5 7,5 8,7 8,12",
    'n': "0,5 0,12;0,5 3,5 6,6 7,8 7,12",
    'o': "2,5 6,5 8,7 8,10 6,12 2,12 0,10 0,7 2,5",
    'p': "0,5 0,15;0,7 4,5 7,6 8,8 8,10 6,12 3,12 0,10",
    'q': "8,5 8,15;8,7 5,5 2,6 1,8 1,10 3,12 6,12 8,10",
    'r': "0,5 0,12;0,7 3,5 6,6 7,8",
    's': "7,6 5,5 2,5 1,6 1,8 3,9 7,10 8,11 6,12 3,12 1,11",
    't': "4,0 4,12;1,4 7,4;4,12 6,12",
    'u': "0,5 0,10 2,12 6,12 8,10 8,5",
    'v': "0,5 4,12 8,5",
    'w': "0,5 2,12 4,7 6,12 8,5",
    'x': "0,5 8,12;8,5 0,12",
    'y': "0,5 4,11 8,5;4,11 3,15 1,15",
    'z': "0,5 8,5 0,12 8,12",
    '.': "4,11 4,12",
    ',': "4,11 4,12;4,12 2,15",
    ':': "4,3 4,4;4,9 4,10",
    ';': "4,3 4,4;4,9 4,10;4,10 2,14",
    "'": "4,0 3,3",
    '"': "2,0 1,3;6,0 5,3",
    '!': "4,0 4,8;4,11 4,12",
    '?': "2,2 3,0 6,0 7,2 7,4 5,6 4,7 4,9;4,11 4,12",
    '-': "1,6 7,6",
    '(': "6,0 3,2 2,6 3,10 6,12",
    ')': "2,0 5,2 6,6 5,10 2,12",
    '/': "7,0 1,12",
    '%': "7,0 1,12;1,1 3,1 3,3 1,3 1,1;5,9 7,9 7,11 5,11 5,9",
    '$': "4,0 4,12;7,2 5,0 2,0 1,2 1,4 3,5 7,6 8,8 8,10 6,12 3,12 1,10",
    '+': "4,3 4,9;1,6 7,6",
    '=': "1,4 7,4;1,8 7,8",
    'x': "0,5 8,12;8,5 0,12",
    '&': "6,0 3,1 1,4 1,7 3,9 8,12;3,9 6,6 7,4 6,2",
    '*': "4,1 4,11;1,3 7,9;7,3 1,9",
    '#': "3,0 2,12;6,0 5,12;1,4 8,4;1,8 8,8",
})

GLYPHS = {}
for _ch, _raw in FONT_RAW.items():
    _strokes = []
    for _s in _raw.split(';'):
        _pts = []
        for _p in _s.strip().split():
            _a, _b = _p.split(',')
            _pts.append((int(_a), int(_b)))
        _strokes.append(_pts)
    GLYPHS[_ch] = _strokes

ADV = 9.0      # advance width in font units
LINE_H = 16.0  # line height in font units


def _serif_ticks(cv, x, y, s, c, t):
    # a short horizontal tick at a stem end: the serif
    half = max(1, int(round(1.1 * s)))
    cv.rect(x - half, y - t // 2, 2 * half + 1, max(1, t), c)


def draw_glyph(cv, ch, ox, oy, s, c, t):
    strokes = GLYPHS.get(ch)
    if not strokes:
        return
    for pts in strokes:
        if len(pts) == 1:
            px = ox + int(round(pts[0][0] * s))
            py = oy + int(round(pts[0][1] * s))
            cv.rect(px - t // 2, py - t // 2, max(1, t), max(1, t), c)
            continue
        for i in range(len(pts) - 1):
            x0 = ox + int(round(pts[i][0] * s))
            y0 = oy + int(round(pts[i][1] * s))
            x1 = ox + int(round(pts[i + 1][0] * s))
            y1 = oy + int(round(pts[i + 1][1] * s))
            cv.line(x0, y0, x1, y1, c, t)
        # serif ticks on near-vertical stems at cap top / baseline
        for (gx, gy) in (pts[0], pts[-1]):
            if gy in (0, 12):
                px = ox + int(round(gx * s))
                py = oy + int(round(gy * s))
                _serif_ticks(cv, px, py, s, c, t)


def text_w(text, s):
    return int(round(len(text) * ADV * s))


def draw_text(cv, x, y, s, c, text, bold=False):
    t = 1 if s < 1.4 else (2 if s < 2.6 else 3)
    if bold:
        t += 1
    cx = x
    for ch in text:
        if ch == ' ':
            cx += int(round(ADV * s))
            continue
        if bold:
            draw_glyph(cv, ch, cx, y, s, c, t)
            draw_glyph(cv, ch, cx + 1, y, s, c, t)
        else:
            draw_glyph(cv, ch, cx, y, s, c, t)
        cx += int(round(ADV * s))
    return cx


def wrap(text, s, maxw):
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_w(trial, s) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def para(cv, x, y, s, c, text, maxw, bold=False, leading=None):
    lh = int(round((leading or LINE_H) * s))
    for ln in wrap(text, s, maxw):
        draw_text(cv, x, y, s, c, ln, bold=bold)
        y += lh
    return y


def centered(cv, y, s, c, text, bold=False, cx=512):
    w = text_w(text, s)
    return draw_text(cv, cx - w // 2, y, s, c, text, bold=bold)


# ------------------------------------------------------------ illustrations
def shade_sun(cv, cx, cy, r):
    # a shaded sun: warm concentric discs, brightest at the centre
    for k in range(r, 0, -1):
        t = k / r
        c = mix((255, 236, 180), (214, 110, 40), t)
        cv.circle(cx, cy, k, c)


def smoke_plume(cv, x, y, w, h):
    # a rising smoke column built from overlapping shaded discs
    n = 7
    for i in range(n):
        t = i / (n - 1)
        cx = x + int(w * 0.5 + (i % 2 - 0.5) * w * 0.22)
        cy = y + int(h * (1 - t)) - 4
        r = int(w * (0.20 + 0.14 * t))
        g = int(70 + 90 * t)
        cv.circle(cx, cy, r, (g, g, g - 4))
        cv.circle(cx - r // 3, cy - r // 3, max(1, r * 2 // 3), (g + 26, g + 26, g + 22))


def building_windows(cv, x, y, w, h, lit, cols=6, rows=8):
    cw, ch = w // cols, h // rows
    for r in range(rows):
        for co in range(cols):
            wx = x + co * cw + cw // 4
            wy = y + r * ch + ch // 4
            ww, wh = cw // 2, ch // 2
            # checkerboard of lit and dark windows, fixed pattern
            if (r * 7 + co * 3) % 5 < 2:
                cv.rect(wx, wy, ww, wh, lit)
            else:
                cv.rect(wx, wy, ww, wh, (28, 30, 38))


def draw_cop31(cv, x, y, w, h):
    # Antalya dusk: gradient sky, shaded sun, conference hall, smoke
    cv.vgrad(x, y, w, h, (250, 196, 120), (214, 120, 62))
    shade_sun(cv, x + w - 52, y + 42, 30)
    cv.rect(x, y + h - 34, w, 34, (74, 58, 44))
    cv.rect(x, y + h - 30, w, 4, (40, 32, 26))
    # conference hall: wide low block with a sawtooth roof
    hx, hy, hw, hh = x + 18, y + h - 78, w - 36, 48
    cv.rect(hx, hy + 10, hw, hh - 10, (226, 214, 190))
    cv.poly([(hx, hy + 10), (hx + 20, hy), (hx + 44, hy + 10),
             (hx + 68, hy), (hx + 92, hy + 10), (hx + 116, hy),
             (hx + 140, hy + 10), (hx + hw, hy + 10),
             (hx + hw, hy + 38), (hx, hy + 38)], (196, 178, 148))
    building_windows(cv, hx + 8, hy + 14, hw - 16, 22, (255, 214, 120), 8, 2)
    smoke_plume(cv, x + 12, y + 30, 46, 48)
    cv.rect(x, y + h - 2, w, 2, (40, 32, 26))


def draw_hormuz(cv, x, y, w, h):
    # Strait of Hormuz at dusk: orange sky, dark sea, a tanker, smoke
    cv.vgrad(x, y, w, h * 3 // 5, (248, 176, 96), (206, 96, 52))
    shade_sun(cv, x + 58, y + 34, 24)
    sea_y = y + h * 3 // 5
    cv.vgrad(x, sea_y, w, h - h * 3 // 5, (26, 64, 96), (12, 30, 52))
    # tanker: hull, containers, bridge tower, funnel smoke
    tx, ty = x + 30, sea_y + 14
    cv.poly([(tx, ty), (tx + w - 70, ty), (tx + w - 84, ty + 26),
             (tx + 8, ty + 26)], (18, 20, 26))
    cv.rect(tx + 8, ty - 26, 96, 26, (150, 52, 40))
    cv.rect(tx + 108, ty - 26, 96, 26, (52, 96, 130))
    cv.rect(tx + 208, ty - 26, 60, 26, (176, 132, 52))
    cv.rect(tx + w - 96, ty - 46, 26, 46, (210, 204, 188))
    cv.rect(tx + w - 92, ty - 42, 18, 6, (255, 214, 120))
    cv.rect(tx + w - 92, ty - 32, 18, 6, (255, 214, 120))
    cv.rect(tx + 40, ty - 40, 8, 14, (30, 30, 34))
    smoke_plume(cv, tx + 22, ty - 52, 40, 36)
    # sea lanes
    for k in range(3):
        yy = sea_y + 34 + k * 12
        cv.hline(x + 10, yy, w - 20, mix((26, 64, 96), (255, 255, 255), 0.18))
    cv.rect(x, y + h - 2, w, 2, (40, 32, 26))


def draw_kyiv(cv, x, y, w, h):
    # Kyiv: cold grey-blue sky, an apartment block hit by a drone,
    # smoke above, fire glow at the broken corner
    cv.vgrad(x, y, w, h, (168, 182, 196), (108, 124, 142))
    cv.circle(x + w - 46, y + 26, 16, (226, 228, 224))
    bx, by, bw, bh = x + 26, y + 44, w - 90, h - 56
    cv.rect(bx, by, bw, bh, (148, 138, 122))
    cv.rect(bx, by, bw, 6, (110, 100, 86))
    building_windows(cv, bx + 8, by + 12, bw - 16, bh - 24, (255, 196, 110), 5, 6)
    # broken corner: dark jagged edge with orange fire glow
    cv.poly([(bx + bw - 34, by), (bx + bw, by), (bx + bw, by + 40),
             (bx + bw - 18, by + 30), (bx + bw - 34, by + 18)],
            (52, 46, 40))
    for k in range(5):
        cv.ellipse(bx + bw - 22 + k * 3, by + 26 + k * 5, 12 - k, 8 - k,
                   (240, 120 + k * 12, 30))
    smoke_plume(cv, bx + bw - 66, y + 28, 52, 20)
    cv.rect(x, y + h - 34, w, 34, (66, 60, 52))
    cv.rect(x, y + h - 2, w, 2, (40, 32, 26))


# ---------------------------------------------------------------- world map
# rough continent outlines in (lon, lat)
CONTINENTS = [
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-60, 60),
     (-55, 47), (-70, 42), (-75, 35), (-80, 26), (-90, 21), (-97, 16),
     (-105, 20), (-115, 30), (-125, 40), (-125, 49), (-140, 60), (-165, 60)],
    [(-58, 64), (-40, 70), (-25, 76), (-55, 80), (-68, 76)],
    [(-80, 10), (-60, 8), (-50, 0), (-35, -8), (-40, -20), (-48, -28),
     (-58, -35), (-65, -40), (-70, -52), (-73, -40), (-70, -20),
     (-77, -12), (-80, -3)],
    [(-10, 36), (-9, 43), (0, 46), (-2, 50), (3, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (28, 59), (30, 60), (25, 65), (30, 70), (40, 68),
     (45, 68), (40, 60), (35, 55), (30, 50), (28, 45), (23, 40), (19, 42),
     (12, 44), (8, 44), (3, 43), (-2, 37), (-9, 37)],
    [(-6, 35), (10, 37), (20, 32), (32, 31), (35, 28), (40, 15), (43, 11),
     (51, 11), (48, 2), (40, -5), (35, -18), (32, -28), (26, -34),
     (18, -35), (12, -18), (9, 4), (-8, 4), (-15, 11), (-17, 15),
     (-16, 25), (-10, 30)],
    [(40, 68), (55, 70), (70, 72), (90, 75), (110, 76), (130, 72),
     (160, 70), (178, 66), (170, 60), (162, 56), (158, 52), (142, 50),
     (140, 40), (130, 35), (127, 35), (122, 30), (120, 22), (110, 20),
     (105, 10), (100, 8), (98, 15), (95, 16), (90, 22), (88, 22),
     (80, 15), (77, 8), (73, 20), (66, 25), (60, 25), (57, 26), (52, 28),
     (48, 30), (44, 30), (40, 36), (36, 36), (35, 31)],
    [(130, 31), (133, 34), (137, 35), (140, 38), (141, 42), (143, 44),
     (141, 39), (139, 35), (132, 33)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (130, -32),
     (137, -35), (140, -38), (147, -39), (150, -37), (153, -27),
     (146, -19), (142, -11), (136, -12), (132, -11), (126, -14),
     (122, -17), (114, -22)],
]
# story locations on the map (lon, lat)
MAP_DOTS = [
    (36.9, 36.9), (50.5, 26.2), (30.5, 50.4), (-77.0, 38.9),
    (-0.1, 51.5), (174.8, -41.3), (127.0, 37.5), (106.8, -6.2),
    (32.5, 15.6), (31.6, 4.9), (15.3, -4.3), (-9.1, 38.7),
    (85.3, 27.7), (77.2, 28.6), (46.7, 24.6), (21.0, 52.2),
    (37.6, 55.7), (24.9, 60.2), (-115.1, 36.2), (149.1, -35.3),
]


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, (222, 230, 234))
    cv.frame(x, y, w, h, RULE, 1)
    # faint latitude lines
    for lat in (60, 30, 0, -30):
        yy = y + int((75 - lat) / 130 * h)
        cv.hline(x + 1, yy, w - 2, (198, 206, 214))
    for lon in (-120, -60, 0, 60, 120):
        xx = x + int((lon + 170) / 360 * w)
        cv.vline(xx, y + 1, h - 2, (198, 206, 214))

    def px(lon, lat):
        return (x + int((lon + 170) / 360 * w),
                y + int((75 - lat) / 130 * h))

    for cont in CONTINENTS:
        pts = [px(lo, la) for lo, la in cont]
        cv.poly(pts, (96, 116, 88))
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            cv.line(x0, y0, x1, y1, (58, 78, 54), 1)
    for lon, lat in MAP_DOTS:
        dx, dy = px(lon, lat)
        cv.circle(dx, dy, 5, RED)
        cv.circle(dx, dy, 2, (255, 255, 255))


# ---------------------------------------------------------------- PNG writer
def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------------- content
# 37 stories, 9 regions, all reported on Monday 23 November 2026.
LEADS = [
    ("CLIMATE - ANTALYA",
     "COP31 COLLAPSES: NO DEAL IN ANTALYA",
     "Climate talks in Antalya collapse as the EU rejects a draft that "
     "never mentions fossil fuels. After two days of overtime, no deal.",
     draw_cop31),
    ("MIDDLE EAST - THE GULF",
     "IRAN STRIKES US BASES AND TANKERS",
     "Iran hits US bases in Bahrain and two tankers in the Strait of "
     "Hormuz. A US blockade enters its 130th day; 25 tankers hit in "
     "a week.",
     draw_hormuz),
    ("EUROPE - UKRAINE",
     "DRONES KILL FOUR IN KYIV REGION",
     "Russian drones kill four near Kyiv and flatten a block in Dymer, "
     "where 14 are missing. 186 drones came overnight; 161 were shot down.",
     draw_kyiv),
]

BRIEFS = [
    ("EUROPE", "POLAND: RUSSIAN MISSILES CROSS BORDER IN PROVOCATION"),
    ("EUROPE", "UK AND EU REACH BREXIT RESET DEAL DESPITE FEES ROW"),
    ("EUROPE", "RUSSIA SUMMONS FINNISH DIPLOMAT OVER ATHLETE BAN"),
    ("EUROPE", "POLAND: RUSSIA TWICE TRIED TO KILL US RAPPER"),
    ("EUROPE", "RUSSIAN CARGO SHIP STILL BURNING OFF FINLAND"),
    ("EUROPE", "ZELENSKIY URGES US TO APPROVE PATRIOT TRANSFERS"),
    ("NORTH AMERICA", "DEMOCRATS CLINCH 258 HOUSE SEATS, MOST SINCE 1992"),
    ("NORTH AMERICA", "US SEEKS ANSWERS ON NVIDIA CHIP SALES TO CHINA"),
    ("NORTH AMERICA", "NVIDIA AIDE LINKED TO SECRET CHIP NETWORK TO CHINA"),
    ("NORTH AMERICA", "US ARMY TO DETONATE IOWA EXPLOSIVES DESPITE ORDER"),
    ("ASIA-PACIFIC", "SOUTH KOREA MINISTER RESIGNS OVER AI CHEATING SCANDAL"),
    ("ASIA-PACIFIC", "NEPAL PM SHAH HOLDS TALKS WITH MODI IN NEW DELHI"),
    ("ASIA-PACIFIC", "70% OF AUSTRALIAN MPS SAY POLITICS HARMED THEM"),
    ("ASIA-PACIFIC", "MYANMAR CALLS ASEAN DECISION UNFAIR AND IMBALANCED"),
    ("SOUTH ASIA", "INDONESIA FACTORY FIRE: 3 DEAD, 50 MISSING"),
    ("SOUTH ASIA", "AMIT SHAH LAUNCHES RS 4,000 CRORE PUSH IN ARUNACHAL"),
    ("SOUTH ASIA", "IFFI 2026 HOSTS BRICS FILM ROUNDTABLE"),
    ("SOUTH ASIA", "BJP MP RAMRAO WADKUTE DIES OF HEART ATTACK IN DELHI"),
    ("SOUTH ASIA", "NINE KILLED AS PILGRIMS VEHICLE RAMS TRUCK IN KOTA"),
    ("SOUTH ASIA", "ANUPAMA DEFENDS WORLD WOMEN SNOOKER TITLE"),
    ("AFRICA", "DRONE ATTACK HITS UN BUILDING IN KHARTOUM"),
    ("AFRICA", "SPLA-IO ATTACK LEAVES 24 CIVILIANS DEAD IN S. SUDAN"),
    ("AFRICA", "FIGHTING NEAR CONGO EBOLA OUTBREAK DISRUPTS RESPONSE"),
    ("AFRICA", "LIBYA: BLAST ON RUSSIAN SHIP FOLLOWED DRONE ATTACK"),
    ("MIDDLE EAST", "SAUDI-LED COALITION INTERCEPTS HOUTHI MISSILE"),
    ("MIDDLE EAST", "CHILDREN WITH DIABETES IN GAZA STRUGGLE FOR INSULIN"),
    ("MIDDLE EAST", "EISENKOT CALLS WEST BANK ARSON JEWISH TERRORISM"),
    ("MIDDLE EAST", "IRAN IMPOSES ROLLING POWER CUTS AS GRID IS DAMAGED"),
    ("MARKETS", "AI SELL-OFF: S&P 500 -3.70%, NASDAQ -5.28%"),
    ("MARKETS", "BITCOIN AND ETHER BOUNCE AHEAD OF MONDAY ETF TEST"),
    ("MARKETS", "TAIWAN BANS SHORT-SELLING AS ASIA CALMS MARKETS"),
    ("SPORT", "LIVERPOOL THRASH 10-MAN MAN UTD 4-0 AT ANFIELD"),
    ("SPORT", "INDIA POST RECORD 720/9 IN WELLINGTON TEST"),
    ("SPORT", "VERSTAPPEN WINS THIRD LAS VEGAS GP IN FOUR YEARS"),
]

STATS = [
    ("37", "STORIES ON ONE PAGE"),
    ("9", "REGIONS"),
    ("25", "TANKERS HIT IN 7 DAYS"),
    ("186", "DRONES OVER KYIV"),
    ("258", "HOUSE SEATS"),
    ("$92.57", "BRENT CRUDE"),
]

MARKETS = ("S&P 500 6,910.39 -3.70%  -  NASDAQ 22,617.73 -5.28%  -  "
           "DOW 48,147.33 -1.93%  -  VIX 35.89  -  BRENT $92.57  -  "
           "GOLD $3,515.40")


# -------------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)
    mx = 28
    cw = W - 2 * mx  # 968

    # masthead
    centered(cv, 14, 5.6, INK, "THE WORLD TODAY", bold=True)
    centered(cv, 90, 1.4, INK_SOFT,
             "MONDAY 23 NOVEMBER 2026  -  37 STORIES  -  9 REGIONS", bold=True)
    cv.rect(mx, 118, cw, 3, INK)
    cv.rect(mx, 123, cw, 1, INK)

    # stats strip
    bw = (cw - 5 * 4) // 6
    for i, (num, lab) in enumerate(STATS):
        bx = mx + i * (bw + 4)
        cv.rect(bx, 130, bw, 36, (238, 232, 216))
        cv.frame(bx, 130, bw, 36, RULE, 1)
        centered(cv, 132, 1.4, RED, num, bold=True, cx=bx + bw // 2)
        centered(cv, 153, 0.68, INK_SOFT, lab, cx=bx + bw // 2)

    # three lead stories
    colw = (cw - 2 * 16) // 3
    for i, (kick, head, deck, art) in enumerate(LEADS):
        lx = mx + i * (colw + 16)
        art(cv, lx, 172, colw, 100)
        draw_text(cv, lx, 280, 0.95, RED, kick, bold=True)
        para(cv, lx, 296, 1.6, INK, head, colw, bold=True, leading=17.0)
        para(cv, lx, 350, 0.9, INK_SOFT, deck, colw, leading=17.0)
        if i < 2:
            cv.vline(lx + colw + 8, 172, 236, RULE)

    # markets strip
    cv.rect(mx, 416, cw, 28, (30, 32, 38))
    draw_text(cv, mx + 10, 423, 1.0, (255, 214, 120), "MARKETS", bold=True)
    draw_text(cv, mx + 96, 423, 0.75, (232, 228, 220), MARKETS)

    # world map
    draw_text(cv, mx, 452, 1.1, INK, "WHERE THE DAY HAPPENED", bold=True)
    draw_text(cv, mx + 250, 452, 0.9, INK_SOFT,
              "20 PLACES MARKED, FROM ANTALYA TO WELLINGTON")
    draw_map(cv, mx, 470, cw, 94)

    # briefs grid: 4 columns, fill top to bottom
    draw_text(cv, mx, 574, 1.1, INK, "IN BRIEF - 34 MORE STORIES, 23 NOVEMBER 2026",
              bold=True)
    cv.rect(mx, 592, cw, 2, INK)
    col_xs = [mx, mx + 245, mx + 490, mx + 735]
    col_w = 233
    y_top, y_bot = 600, 1008
    col, y = 0, y_top
    for tag, head in BRIEFS:
        lines = wrap(head, 0.9, col_w)
        need = 10 + len(lines) * 15 + 3
        if y + need > y_bot:
            col += 1
            y = y_top
            if col > 3:
                raise SystemExit("briefs overflow the grid")
        draw_text(cv, col_xs[col], y, 0.8, RED, tag, bold=True)
        para(cv, col_xs[col], y + 10, 0.9, INK, head, col_w,
             bold=True, leading=17.0)
        y += need

    # footer
    cv.rect(mx, 1010, cw, 1, RULE)
    centered(cv, 1013, 0.7, INK_SOFT,
             "THE WORLD TODAY - MONDAY 23 NOVEMBER 2026 - "
             "SOURCES: REUTERS, AP, AL JAZEERA, UKMTO, BBC")
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    path = os.path.join(outdir, "entry.png")
    size = write_png(cv, path)
    import hashlib
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("wrote %s (%d bytes) sha256=%s" % (path, size, h))
    print("stories: %d (3 leads + %d briefs), regions: 9"
          % (3 + len(BRIEFS), len(BRIEFS)))


if __name__ == "__main__":
    main()
