#!/usr/bin/env python3
"""THE WORLD TODAY - Monday 23 November 2026.

Draws a one-page newspaper front page summing up the world's news of
Monday 23 November 2026 as a 1024x1024 PNG.

Pure Python 3 standard library only: no network, no clock, no randomness,
no third-party modules. Every pixel is drawn by this file - a small
stroke font with serif feet, shaded illustrations, a dotted world map -
and the image is rendered at 2x and downsampled for clean anti-aliased
edges, so two runs write byte-identical output.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes: <MAKEFUN_OUTPUT_DIR>/entry.png (1024x1024, under 1 MiB)
"""

import os
import struct
import zlib

W, H = 1024, 1024
SS = 2                      # supersampling factor
CW, CH = W * SS, H * SS

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)
INK = (22, 22, 22)
INK_SOFT = (58, 54, 48)
RED = (163, 18, 18)
BLUE = (31, 78, 121)
TEAL = (14, 92, 92)
GOLD = (176, 132, 30)
GREY = (128, 122, 112)
RULE = (150, 142, 128)
LIGHT_LINE = (205, 196, 180)

# ------------------------------------------------------- stroke font data
# Glyphs on a 9-wide grid: cap top y=0, baseline y=10, descender y=13.
# Each value is a list of strokes; a stroke is "x,y x,y ..." points.
FONT = {
    "A": ["0,10 4,0 8,10", "2,7 6,7"],
    "B": ["0,0 0,10", "0,0 5,0 7,2 5,5 0,5", "0,5 6,5 7,7 5,10 0,10"],
    "C": ["8,2 6,0 2,0 0,3 0,7 2,10 6,10 8,8"],
    "D": ["0,0 0,10", "0,0 5,0 8,3 8,7 5,10 0,10"],
    "E": ["7,0 0,0 0,10 7,10", "0,5 5,5"],
    "F": ["7,0 0,0 0,10", "0,5 5,5"],
    "G": ["8,2 6,0 2,0 0,3 0,7 2,10 6,10 8,8 8,5", "5,5 8,5"],
    "H": ["0,0 0,10", "8,0 8,10", "0,5 8,5"],
    "I": ["4,0 4,10", "1,0 7,0", "1,10 7,10"],
    "J": ["7,0 7,8 5,10 2,10 0,8"],
    "K": ["0,0 0,10", "7,0 0,5 8,10"],
    "L": ["0,0 0,10 7,10"],
    "M": ["0,10 0,0 4,6 8,0 8,10"],
    "N": ["0,10 0,0 8,10 8,0"],
    "O": ["2,0 6,0 8,2 8,8 6,10 2,10 0,8 0,2 2,0"],
    "P": ["0,10 0,0 5,0 7,2 5,5 0,5"],
    "Q": ["2,0 6,0 8,2 8,8 6,10 2,10 0,8 0,2 2,0", "5,7 8,10"],
    "R": ["0,10 0,0 5,0 7,2 5,5 0,5", "4,5 8,10"],
    "S": ["7,1 5,0 2,0 0,2 0,4 2,5 6,5 8,6 8,8 6,10 3,10 1,9"],
    "T": ["0,0 8,0", "4,0 4,10"],
    "U": ["0,0 0,8 2,10 6,10 8,8 8,0"],
    "V": ["0,0 4,10 8,0"],
    "W": ["0,0 2,10 4,5 6,10 8,0"],
    "X": ["0,0 8,10", "8,0 0,10"],
    "Y": ["0,0 4,5 8,0", "4,5 4,10"],
    "Z": ["0,0 8,0 0,10 8,10"],
    "a": ["7,4 7,10", "7,4 3,4 1,6 1,8 3,10 6,10"],
    "b": ["1,0 1,10", "1,7 2,5 4,4 6,6 6,8 4,10 1,10"],
    "c": ["7,5 5,4 2,4 1,6 1,8 2,10 5,10 7,9"],
    "d": ["7,0 7,10", "7,10 4,10 1,8 1,6 3,4 6,4 7,5"],
    "e": ["1,8 6,8", "6,8 6,6 5,4 2,4 1,6 1,8 2,10 5,10 7,8"],
    "f": ["6,1 4,0 3,1 3,10", "1,4 5,4"],
    "g": ["7,4 3,4 1,6 1,8 3,10 6,10 7,8", "7,8 7,12 5,13 3,13 1,12"],
    "h": ["1,0 1,10", "1,7 3,5 5,4 7,5 7,10"],
    "i": ["4,4 4,10", "3,0 5,0", "3,2 5,2"],
    "j": ["5,4 5,12 3,13 1,12", "4,0 6,0", "4,2 6,2"],
    "k": ["1,0 1,10", "6,4 1,7 7,10"],
    "l": ["4,0 4,10"],
    "m": ["1,10 1,4 3,4 4,6 5,4 7,4 7,10", "4,6 4,10"],
    "n": ["1,10 1,4 4,4 6,5 7,7 7,10"],
    "o": ["2,4 5,4 7,6 7,8 5,10 2,10 1,8 1,6 2,4"],
    "p": ["1,4 1,13", "1,10 4,10 6,8 6,6 4,4 1,4"],
    "q": ["7,4 7,13", "7,10 4,10 2,8 2,6 4,4 7,4"],
    "r": ["1,10 1,4 4,4 6,5 7,7"],
    "s": ["7,5 5,4 2,4 1,6 2,8 5,8 7,9 6,10 3,10 1,9"],
    "t": ["3,1 3,10 5,10", "1,4 5,4"],
    "u": ["1,4 1,8 2,10 5,10 7,8 7,4"],
    "v": ["1,4 4,10 7,4"],
    "w": ["1,4 2,10 4,6 6,10 7,4"],
    "x": ["1,4 7,10", "7,4 1,10"],
    "y": ["1,4 4,10 7,4", "7,4 7,12 5,13 3,13"],
    "z": ["1,4 7,4 1,10 7,10"],
    "0": ["2,0 6,0 8,2 8,8 6,10 2,10 0,8 0,2 2,0"],
    "1": ["2,2 4,0 4,10", "1,10 7,10"],
    "2": ["1,2 3,0 6,0 8,2 8,4 6,6 0,10 8,10"],
    "3": ["1,1 3,0 6,0 8,2 7,4 5,5", "5,5 7,6 8,8 6,10 3,10 1,9"],
    "4": ["6,0 6,10", "0,7 7,7", "2,0 0,7"],
    "5": ["8,0 0,0 0,5 5,5 7,6 7,8 5,10 1,10"],
    "6": ["7,1 5,0 2,0 0,3 0,7 2,10 6,10 8,8 8,6 6,4 3,4 1,6"],
    "7": ["0,0 8,0 4,10"],
    "8": ["3,0 5,0 7,2 7,4 5,5 3,5 1,4 1,2 3,0", "3,5 1,6 1,8 3,10 5,10 7,8 7,6 5,5"],
    "9": ["2,0 6,0 8,2 8,10", "2,0 1,2 1,5 3,7 6,7 8,5"],
    ".": ["4,9 4,10"],
    ",": ["4,9 4,11 3,13"],
    ":": ["4,2 4,3", "4,8 4,9"],
    ";": ["4,2 4,3", "4,8 4,11 3,13"],
    "!": ["4,0 4,7", "4,9 4,10"],
    "?": ["1,2 3,0 6,0 8,2 8,4 6,6 4,7 4,8", "4,9 4,10"],
    "'": ["4,0 4,3"],
    '"': ["2,0 2,3", "6,0 6,3"],
    "-": ["1,5 7,5"],
    "(": ["6,0 3,2 3,8 6,10"],
    ")": ["2,0 5,2 5,8 2,10"],
    "[": ["6,0 2,0 2,10 6,10"],
    "]": ["2,0 6,0 6,10 2,10"],
    "/": ["1,10 7,0"],
    "%": ["0,10 8,0", "1,0 3,0 3,2 1,2 1,0", "5,8 7,8 7,10 5,10 5,8"],
    "&": ["7,1 5,0 2,1 1,3 2,5 5,6 7,7 7,9 5,10 2,10 1,9", "2,5 8,10"],
    "$": ["4,-1 4,11", "7,1 5,0 2,0 0,2 0,4 2,5 6,5 8,6 8,8 6,10 3,10 1,9"],
    "#": ["2,0 2,10", "6,0 6,10", "0,3 8,3", "0,7 8,7"],
    "*": ["4,0 4,10", "0,3 8,7", "8,3 0,7"],
    "+": ["4,1 4,9", "1,5 7,5"],
    "=": ["1,3 7,3", "1,7 7,7"],
    "<": ["7,1 1,5 7,9"],
    ">": ["1,1 7,5 1,9"],
    "_": ["0,12 8,12"],
    "~": ["1,6 3,4 5,6 7,4"],
    "^": ["0,6 4,1 8,6"],
    "|": ["4,0 4,10"],
}

# Parse font once: char -> (advance_units, [ [(x, y), ...], ... ])
def _parse_font():
    out = {}
    for ch, strokes in FONT.items():
        parsed = []
        maxx = 0
        for st in strokes:
            pts = []
            for tok in st.split():
                x, y = tok.split(",")
                x, y = int(x), int(y)
                maxx = max(maxx, x)
                pts.append((x, y))
            parsed.append(pts)
        adv = maxx + 5
        if ch == " ":
            adv = 6
        out[ch] = (adv, parsed)
    out[" "] = (5, [])
    return out

_GLYPHS = _parse_font()


def glyph_advance(ch, scale):
    """Advance width in final pixels for one character at given scale
    (scale = final pixels per font unit)."""
    adv, _ = _GLYPHS.get(ch, _GLYPHS["?"])
    return adv * scale


def text_width(text, scale):
    return sum(glyph_advance(c, scale) for c in text)


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self):
        self.buf = bytearray(CW * CH * 3)
        self.fill_rect(0, 0, W, H, PAPER)

    def _idx(self, x, y):
        return (y * CW + x) * 3

    def px(self, x, y, col):
        if 0 <= x < CW and 0 <= y < CH:
            i = self._idx(x, y)
            self.buf[i] = col[0]
            self.buf[i + 1] = col[1]
            self.buf[i + 2] = col[2]

    def blend_px(self, x, y, col, alpha):
        """alpha 0..1 over existing pixel."""
        if 0 <= x < CW and 0 <= y < CH:
            i = self._idx(x, y)
            a = alpha
            self.buf[i] = int(col[0] * a + self.buf[i] * (1 - a))
            self.buf[i + 1] = int(col[1] * a + self.buf[i + 1] * (1 - a))
            self.buf[i + 2] = int(col[2] * a + self.buf[i + 2] * (1 - a))

    def fill_rect(self, x, y, w, h, col):
        """Final-pixel coordinates."""
        x0, y0 = max(0, int(x * SS)), max(0, int(y * SS))
        x1, y1 = min(CW, int((x + w) * SS)), min(CH, int((y + h) * SS))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(col) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * CW + x0) * 3
            self.buf[i:i + len(row)] = row

    def vgrad_rect(self, x, y, w, h, top, bottom):
        """Vertical gradient, final-pixel coordinates."""
        x0, y0 = max(0, int(x * SS)), max(0, int(y * SS))
        x1, y1 = min(CW, int((x + w) * SS)), min(CH, int((y + h) * SS))
        if x1 <= x0 or y1 <= y0:
            return
        span = max(1, y1 - y0 - 1)
        for yy in range(y0, y1):
            t = (yy - y0) / span
            col = tuple(int(top[c] * (1 - t) + bottom[c] * t) for c in range(3))
            row = bytes(col) * (x1 - x0)
            i = (yy * CW + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, col, thick=1):
        self.fill_rect(x, y, w, thick, col)

    def vline(self, x, y, h, col, thick=1):
        self.fill_rect(x, y, thick, h, col)

    def _stamp(self, cx, cy, r, col):
        """Square brush stamp centred at supersampled coords."""
        x0, y0 = int(cx - r), int(cy - r)
        x1, y1 = int(cx + r) + 1, int(cy + r) + 1
        for yy in range(max(0, y0), min(CH, y1)):
            base = (yy * CW + max(0, x0)) * 3
            n = min(CW, x1) - max(0, x0)
            if n > 0:
                self.buf[base:base + n * 3] = bytes(col) * n

    def line(self, x0, y0, x1, y1, col, thick=1):
        """Thick line, final-pixel coordinates, square brush."""
        ax, ay = x0 * SS, y0 * SS
        bx, by = x1 * SS, y1 * SS
        r = max(1.0, thick * SS / 2.0)
        steps = int(max(abs(bx - ax), abs(by - ay)) * 2) + 1
        for i in range(steps + 1):
            t = i / steps if steps else 0
            self._stamp(ax + (bx - ax) * t, ay + (by - ay) * t, r, col)

    def circle(self, cx, cy, rad, col):
        """Filled circle, final-pixel coordinates."""
        cx, cy, rad = cx * SS, cy * SS, rad * SS
        r2 = rad * rad
        y0, y1 = int(cy - rad), int(cy + rad) + 1
        for yy in range(max(0, y0), min(CH, y1)):
            dy = yy - cy
            dx = int((r2 - dy * dy) ** 0.5) if r2 - dy * dy > 0 else 0
            x0 = max(0, int(cx - dx))
            x1 = min(CW, int(cx + dx) + 1)
            if x1 > x0:
                i = (yy * CW + x0) * 3
                self.buf[i:i + (x1 - x0) * 3] = bytes(col) * (x1 - x0)

    def circle_shaded(self, cx, cy, rad, light, dark, lx, ly):
        """Sphere shading: light direction (lx, ly) unit-ish vector."""
        cx, cy, rad = cx * SS, cy * SS, rad * SS
        r2 = rad * rad
        y0, y1 = int(cy - rad), int(cy + rad) + 1
        for yy in range(max(0, y0), min(CH, y1)):
            dy = yy - cy
            rem = r2 - dy * dy
            if rem <= 0:
                continue
            dx = int(rem ** 0.5)
            for xx in range(max(0, int(cx - dx)), min(CW, int(cx + dx) + 1)):
                ddx = xx - cx
                # brightness from facing the light
                t = (ddx * lx + dy * ly) / (rad * 1.4) + 0.55
                t = max(0.0, min(1.0, t))
                col = tuple(int(dark[c] + (light[c] - dark[c]) * t)
                            for c in range(3))
                self.px(xx, yy, col)

    def polygon(self, pts, col):
        """Filled polygon, final-pixel coordinates."""
        pts = [(x * SS, y * SS) for x, y in pts]
        ys = [p[1] for p in pts]
        y0, y1 = int(min(ys)), int(max(ys)) + 1
        n = len(pts)
        for yy in range(max(0, y0), min(CH, y1)):
            xs = []
            for i in range(n):
                x0, ya = pts[i]
                x1, yb = pts[(i + 1) % n]
                if ya == yb:
                    continue
                if (ya <= yy < yb) or (yb <= yy < ya):
                    xs.append(x0 + (yy - ya) * (x1 - x0) / (yb - ya))
            if len(xs) < 2:
                continue
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa, xb = int(xs[k]), int(xs[k + 1]) + 1
                xa = max(0, xa)
                xb = min(CW, xb)
                if xb > xa:
                    i = (yy * CW + xa) * 3
                    self.buf[i:i + (xb - xa) * 3] = bytes(col) * (xb - xa)

    # ------------------------------------------------------------ text
    def _draw_stroke(self, pts, ox, oy, scale, col, thick):
        """One polyline in font units, offset by (ox, oy) in final px."""
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            self.line(ox + x0 * scale, oy + y0 * scale,
                      ox + x1 * scale, oy + y1 * scale, col, thick)
        # serif feet: a near-vertical stroke ending at the cap line,
        # the baseline or a descender gets a small horizontal foot.
        for (ex, ey), (nx, ny) in ((pts[0], pts[1]), (pts[-1], pts[-2])):
            dx, dy = ex - nx, ey - ny
            if abs(dy) > 0 and abs(dx) <= 0.35 * abs(dy):
                if ey <= 0.6 or ey >= 9.4 or ey >= 12.4:
                    half = 0.55 * scale
                    self.line(ox + ex * scale - half, oy + ey * scale,
                              ox + ex * scale + half, oy + ey * scale,
                              col, thick)

    def text(self, x, y, s, txt, col, thick=None, align="left"):
        """Draw text; (x, y) is the top-left of the cap line (final px).
        s = cap height in final pixels. Returns width drawn."""
        if thick is None:
            thick = max(1.0, s * 0.12)
        scale = s / 10.0
        total = text_width(txt, scale)
        if align == "center":
            x -= total / 2
        elif align == "right":
            x -= total
        cx = x
        for ch in txt:
            adv, strokes = _GLYPHS.get(ch, _GLYPHS["?"])
            for pts in strokes:
                self._draw_stroke(pts, cx, y, scale, col, thick)
            cx += adv * scale
        return total

    def wrap(self, txt, s, maxw):
        """Greedy word wrap; returns list of lines."""
        scale = s / 10.0
        lines = []
        for para in txt.split("\n"):
            words = para.split(" ")
            cur = ""
            for w in words:
                trial = (cur + " " + w).strip()
                if text_width(trial, scale) <= maxw or not cur:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
        return lines

    def para(self, x, y, s, txt, col, maxw, leading=None):
        """Draw wrapped paragraph; returns y after the last line."""
        if leading is None:
            leading = s * 1.32
        for ln in self.wrap(txt, s, maxw):
            self.text(x, y, s, ln, col)
            y += leading
        return y

    # ------------------------------------------------------- downsample
    def to_png_bytes(self):
        """Average each 2x2 block down to 1024x1024 and encode a PNG."""
        raw = bytearray()
        for yy in range(H):
            raw.append(0)  # filter: none
            for xx in range(W):
                for c in range(3):
                    i00 = ((2 * yy) * CW + 2 * xx) * 3 + c
                    i01 = i00 + 3
                    i10 = ((2 * yy + 1) * CW + 2 * xx) * 3 + c
                    i11 = i10 + 3
                    raw.append((self.buf[i00] + self.buf[i01]
                                + self.buf[i10] + self.buf[i11] + 2) // 4)
        return encode_png(bytes(raw), W, H)


def _chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data +
            struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))


def encode_png(raw, w, h):
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b""))


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    img = build_image()
    data = img.to_png_bytes()
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote", path, len(data), "bytes")


# ------------------------------------------------------------ illustrations
def draw_cop31(cv, x, y, w, h):
    """COP31 conference hall at dusk, Antalya: gradient sky, lit hall,
    a row of flags, a low sun."""
    cv.vgrad_rect(x, y, w, h, (44, 62, 96), (214, 132, 74))
    cv.circle(x + w * 0.78, y + h * 0.30, 13, (250, 214, 140))
    cv.circle(x + w * 0.78, y + h * 0.30, 20, (244, 190, 110))
    # distant hills
    cv.polygon([(x, y + h * 0.62), (x + w * 0.30, y + h * 0.50),
                (x + w * 0.62, y + h * 0.64), (x + w, y + h * 0.52),
                (x + w, y + h), (x, y + h)], (58, 52, 66))
    # hall
    hx, hy, hw, hh = x + w * 0.10, y + h * 0.34, w * 0.80, h * 0.52
    cv.vgrad_rect(hx, hy, hw, hh, (96, 104, 124), (52, 54, 66))
    cv.polygon([(hx - 6, hy), (hx + hw * 0.5, hy - 16),
                (hx + hw + 6, hy), (hx + hw, hy + 6),
                (hx, hy + 6)], (38, 40, 52))
    # lit windows, two rows
    for r in range(2):
        for c in range(9):
            wx = hx + 10 + c * (hw - 20) / 9
            wy = hy + 12 + r * 22
            warm = (250, 206, 110) if (r + c) % 3 else (190, 205, 220)
            cv.fill_rect(wx, wy, (hw - 20) / 9 - 6, 12, warm)
    # flags in front
    cols = [(163, 18, 18), (31, 78, 121), (14, 92, 92), (176, 132, 30),
            (90, 60, 120), (40, 110, 60)]
    for i in range(6):
        fx = x + w * 0.08 + i * w * 0.15
        cv.vline(fx, y + h * 0.72, h * 0.20, INK, 1.5)
        cv.fill_rect(fx, y + h * 0.72, 16, 10, cols[i % len(cols)])


def draw_tanker(cv, x, y, w, h):
    """Strait of Hormuz at dawn: tanker under a smoke plume, burning sea."""
    cv.vgrad_rect(x, y, w, h, (232, 176, 110), (120, 70, 60))
    cv.circle(x + w * 0.20, y + h * 0.30, 12, (252, 226, 160))
    # smoke plume: a cluster of solid grey discs, darker at the core
    for (sx, sy, sr, col) in [(0.66, 0.30, 24, (86, 84, 82)),
                              (0.70, 0.20, 30, (104, 102, 100)),
                              (0.75, 0.13, 22, (120, 118, 116)),
                              (0.62, 0.16, 17, (110, 108, 106)),
                              (0.79, 0.26, 15, (96, 94, 92)),
                              (0.70, 0.32, 18, (76, 74, 72))]:
        cv.circle(x + w * sx, y + h * sy, sr, col)
    # sea
    cv.vgrad_rect(x, y + h * 0.62, w, h * 0.38, (46, 84, 106), (18, 40, 58))
    for i in range(5):
        wy = y + h * (0.66 + i * 0.065)
        cv.line(x + 6 + i * 8, wy, x + w - 10 - i * 6, wy,
                (150, 180, 195), 1)
    # tanker hull and superstructure
    cv.polygon([(x + w * 0.06, y + h * 0.66), (x + w * 0.94, y + h * 0.66),
                (x + w * 0.88, y + h * 0.86), (x + w * 0.12, y + h * 0.86)],
               (30, 26, 24))
    cv.fill_rect(x + w * 0.06, y + h * 0.66, w * 0.88, 4, (120, 52, 36))
    cv.fill_rect(x + w * 0.68, y + h * 0.44, w * 0.16, h * 0.22,
                 (226, 222, 210))
    for r in range(2):
        for c in range(3):
            cv.fill_rect(x + w * (0.70 + c * 0.05), y + h * (0.47 + r * 0.09),
                         8, 6, (40, 60, 80))
    cv.vline(x + w * 0.30, y + h * 0.50, h * 0.16, (30, 26, 24), 2)
    cv.vline(x + w * 0.52, y + h * 0.54, h * 0.12, (30, 26, 24), 2)
    # orange reflection streak on the water under the hull
    cv.fill_rect(x + w * 0.30, y + h * 0.90, w * 0.40, 3, (214, 128, 54))


def draw_dymer(cv, x, y, w, h):
    """A five-storey block in Dymer after a drone strike: dusk sky,
    broken windows, smoke, rubble and a searchlight."""
    cv.vgrad_rect(x, y, w, h, (58, 52, 88), (196, 120, 74))
    cv.circle(x + w * 0.16, y + h * 0.26, 10, (248, 220, 160))
    # searchlight beam
    cv.polygon([(x + w * 0.86, y + h), (x + w * 0.58, y + h * 0.18),
                (x + w * 0.66, y + h * 0.18), (x + w * 0.94, y + h)],
               (240, 230, 190))
    # block
    bx, by, bw, bh = x + w * 0.14, y + h * 0.30, w * 0.56, h * 0.58
    cv.vgrad_rect(bx, by, bw, bh, (122, 108, 92), (74, 64, 56))
    for r in range(5):
        for c in range(4):
            wx = bx + 8 + c * (bw - 16) / 4
            wy = by + 8 + r * (bh - 16) / 5
            lit = (r * 4 + c) % 4 == 0
            dark = (r == 1 and c == 2) or (r == 2 and c == 1)
            col = (40, 34, 30) if dark else (
                (250, 206, 110) if lit else (52, 58, 70))
            cv.fill_rect(wx, wy, (bw - 16) / 4 - 7, (bh - 16) / 5 - 7, col)
    # broken corner and smoke
    cv.polygon([(bx + bw * 0.62, by), (bx + bw, by),
                (bx + bw, by + bh * 0.30), (bx + bw * 0.78, by + bh * 0.16)],
               (52, 46, 42))
    for (sx, sy, sr, col) in [(0.72, 0.22, 15, (110, 102, 94)),
                              (0.78, 0.13, 19, (128, 120, 112)),
                              (0.66, 0.11, 12, (118, 110, 102)),
                              (0.80, 0.24, 11, (100, 92, 86))]:
        cv.circle(x + w * sx, y + h * sy, sr, col)
    # rubble at the base
    cv.polygon([(bx - 6, y + h * 0.88), (bx + bw * 0.35, y + h * 0.80),
                (bx + bw * 0.62, y + h * 0.88), (bx + bw + 10, y + h * 0.84),
                (bx + bw + 16, y + h * 0.94), (bx - 10, y + h * 0.94)],
               (88, 78, 66))
    cv.fill_rect(x, y + h * 0.94, w, h * 0.06, (52, 48, 44))


def draw_mercury(cv, x, y, w, h):
    """BepiColombo at Mercury: black sky, stars, a shaded cratered disc."""
    cv.fill_rect(x, y, w, h, (10, 10, 16))
    stars = [(0.08, 0.12), (0.22, 0.08), (0.35, 0.2), (0.52, 0.08),
             (0.68, 0.14), (0.82, 0.07), (0.9, 0.24), (0.12, 0.42),
             (0.86, 0.5), (0.3, 0.82), (0.62, 0.86), (0.92, 0.82),
             (0.06, 0.72), (0.46, 0.92)]
    for sx, sy in stars:
        cv.circle(x + w * sx, y + h * sy, 1.2, (235, 235, 245))
    cx, cy, r = x + w * 0.5, y + h * 0.52, min(w, h) * 0.36
    cv.circle_shaded(cx, cy, r, (214, 196, 172), (58, 50, 44), -0.7, -0.7)
    # craters
    for (kx, ky, kr, sh) in [(0.42, 0.42, 7, 0.55), (0.60, 0.55, 9, 0.5),
                             (0.52, 0.68, 5, 0.6), (0.66, 0.38, 5, 0.55),
                             (0.38, 0.62, 4, 0.6)]:
        cv.circle(x + w * kx, y + h * ky, kr, (96, 86, 74))
        cv.circle(x + w * kx - 1, y + h * ky - 1, kr * 0.7, (150, 138, 120))
    # small spacecraft
    cv.fill_rect(x + w * 0.78, y + h * 0.16, 14, 5, (200, 200, 210))
    cv.fill_rect(x + w * 0.74, y + h * 0.17, 4, 3, (31, 78, 121))
    cv.fill_rect(x + w * 0.84, y + h * 0.17, 4, 3, (176, 132, 30))


# Dotted world map: land spans per row on a 72 x 30 grid.
# Equirectangular, lon -180..180, lat 78..-58 (5 deg per column).
MAP_SPANS = {
    0: [(10, 13), (26, 29), (40, 68)],
    1: [(7, 15), (26, 31), (36, 69)],
    2: [(5, 17), (26, 30), (35, 69)],
    3: [(4, 17), (27, 29), (36, 68)],
    4: [(5, 16), (27, 27), (36, 49), (52, 67)],
    5: [(6, 15), (37, 48), (52, 68)],
    6: [(7, 15), (26, 29), (36, 48), (53, 67)],
    7: [(8, 15), (26, 31), (36, 49), (54, 66)],
    8: [(9, 14), (28, 33), (38, 49), (56, 66)],
    9: [(10, 14), (28, 33), (38, 47), (56, 64)],
    10: [(11, 14), (29, 32), (38, 46), (48, 51), (56, 62)],
    11: [(12, 14), (29, 32), (39, 45), (48, 51), (55, 61)],
    12: [(13, 14), (30, 32), (40, 44), (48, 51), (55, 60)],
    13: [(14, 14), (23, 25), (36, 44), (49, 51), (56, 60)],
    14: [(22, 25), (36, 44), (57, 63)],
    15: [(22, 25), (37, 43), (57, 63)],
    16: [(23, 25), (37, 43), (58, 62)],
    17: [(23, 25), (38, 42)],
    18: [(24, 25), (38, 42)],
    19: [(24, 25), (38, 41)],
    20: [(25, 26), (38, 41)],
    21: [(25, 26), (38, 41), (58, 64)],
    22: [(26, 26), (38, 40), (58, 66)],
    23: [(26, 26), (39, 40), (58, 67)],
    24: [(26, 26), (39, 40), (59, 66)],
    25: [(59, 64)],
}

MARKERS = [  # (lon, lat, label, dx, dy, align) - label offset in final px
    # from the dot; align "l" = label starts at dot+dx, "r" = label ends
    # at dot+dx. Offsets spread the crowded Europe / Gulf / S. Asia
    # cluster (KYIV, ANTALYA, BAHRAIN, DELHI, NAIROBI) apart.
    (-100, 24, "SINALOA", 8, -4, "l"),
    (-9, 39, "LISBON", -8, 12, "r"),
    (31, 50, "KYIV", 8, -16, "l"),
    (31, 37, "ANTALYA", -8, -14, "r"),
    (50, 26, "BAHRAIN", -38, 12, "l"),
    (77, 28, "DELHI", 8, -4, "l"),
    (36, -1, "NAIROBI", 8, 12, "l"),
    (106, -6, "BANTEN", 8, -4, "l"),
    (127, 37, "SEOUL", 8, -4, "l"),
    (151, -34, "SYDNEY", -8, -4, "r"),
]


def draw_map(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (232, 238, 240))
    cols, rows = 72, 30
    cw, chh = w / cols, h / rows
    dot_r = max(1.0, min(cw, chh) * 0.36)
    for r, spans in MAP_SPANS.items():
        for c0, c1 in spans:
            for c in range(c0, c1 + 1):
                cv.circle(x + (c + 0.5) * cw, y + (r + 0.5) * chh,
                          dot_r, (96, 116, 134))
    # graticule
    for gx in range(1, 6):
        cv.vline(x + w * gx / 6, y, h, (210, 216, 220), 0.6)
    for gy in range(1, 3):
        cv.hline(x, y + h * gy / 3, w, (210, 216, 220), 0.6)
    # markers
    for lon, lat, lab, dx, dy, align in MARKERS:
        mx = x + (lon + 180) / 360 * w
        my = y + (78 - lat) / 136 * h
        lx = mx + dx
        ly = my + dy
        # leader line from the dot to a spread-out label
        if abs(dx) > 20 or abs(dy) > 10:
            ax, ay = lx, ly + 3.5
            vx, vy = ax - mx, ay - my
            vl = (vx * vx + vy * vy) ** 0.5 or 1
            cv.line(mx + 5 * vx / vl, my + 5 * vy / vl, ax, ay, RED, 0.8)
        cv.circle(mx, my, 4.5, RED)
        cv.circle(mx, my, 2, (255, 255, 255))
        if align == "r":
            cv.text(lx, ly, 7, lab, RED, thick=1.1, align="right")
        else:
            cv.text(lx, ly, 7, lab, RED, thick=1.1)


# ------------------------------------------------------------------ stories
# All stories were reported on Monday 23 November 2026 (or, for the
# Friday market closes, in the weekend editions leading into it).
# Sources checked: Reuters, AP, AFP, UKMTO, ESA, national wires.
LEADS = [
    ("CLIMATE & UN", "COP31 collapses: EU rejects draft with no fossil fuels",
     "Nearly 200 nations leave Antalya empty-handed; the final text "
     "never mentions fossil fuels.",
     draw_cop31),
    ("MIDDLE EAST", "Iran strikes Bahrain base; two tankers hit in Hormuz",
     "Tehran says it hit US facilities; two are wounded as Gulf states "
     "condemn the tanker attacks.",
     draw_tanker),
    ("EUROPE", "Drone hits flats near Kyiv: 2 killed, 14 missing",
     "A Russian drone hits a five-storey block in Dymer; rescuers dig "
     "for survivors in the rubble.",
     draw_dymer),
]

# (region tag, headline) - 34 briefs; 3 leads + 34 = 37 stories.
BRIEFS = [
    ("MARKETS", "AI sell-off deepens; S&P 500 in correction"),
    ("AMERICAS", "Mexico captures 'El Chapo Isidro'; 11 killed"),
    ("ASIA-PACIFIC", "Indonesia factory fire: 3 dead, 50 missing"),
    ("SCIENCE & TECH", "BepiColombo reaches Mercury after 8 years"),
    ("CLIMATE & UN", "UN states keep talking on AI weapons; no rules"),
    ("EUROPE", "NATO to meet Monday over missiles hitting Poland"),
    ("EUROPE", "Russian ship Sparta II still burning off Finland"),
    ("MIDDLE EAST", "Settlers torch 12 vehicles in West Bank villages"),
    ("ASIA-PACIFIC", "Nepal PM Shah meets Modi in Delhi"),
    ("ASIA-PACIFIC", "S. Korea education minister quits in AI scandal"),
    ("SPORT", "India post record 720/9 in Wellington Test"),
    ("CLIMATE & UN", "Australian PM blames COP31 failure on geopolitics"),
    ("EUROPE", "UK to build Ukrainian drones in new deal"),
    ("AFRICA", "South Sudan: 24 civilians killed in new violence"),
    ("AFRICA", "Nigeria: 35 Fulani killed in revenge attacks"),
    ("AFRICA", "Sudan drones hit homes, UN building in Khartoum"),
    ("ASIA-PACIFIC", "Kim: North Korea seeks security, not supremacy"),
    ("AMERICAS", "Bolsonaro stable in intensive care in Brazil"),
    ("MIDDLE EAST", "Netanyahu-Eisenkot coalition talks fail"),
    ("MIDDLE EAST", "Saudi coalition intercepts Houthi missile"),
    ("AFRICA", "WHO chief pleads for peace in Ebola-hit Congo"),
    ("ASIA-PACIFIC", "Myanmar junta calls ASEAN decision unfair"),
    ("EUROPE", "Thousands march in Lisbon over living costs"),
    ("EUROPE", "Turkey seizes last major independent TV channel"),
    ("EUROPE", "UK and EU strike new deals; May rebukes Burnham"),
    ("MIDDLE EAST", "Iran starts rationing electricity as war strains grid"),
    ("MIDDLE EAST", "Houthis fire ballistic missile at Saudi Arabia"),
    ("MIDDLE EAST", "Iran: enriched uranium stays in country"),
    ("AMERICAS", "Trump: no worries about regime change in Iran"),
    ("AMERICAS", "US to build nuclear plant in Saudi Arabia"),
    ("MARKETS", "Flash PMIs due Monday; Fed's Williams speaks"),
    ("ASIA-PACIFIC", "India: Shah launches Rs 4,000-crore projects"),
    ("ASIA-PACIFIC", "Malaysia to act with UN after ICJ Myanmar ruling"),
    ("SCIENCE & TECH", "Nvidia row: aide linked to AI-chip smuggling ring"),
]

STATS = [
    ("2", "tankers hit in the Strait of Hormuz"),
    ("14", "missing after drone hits flats in Dymer"),
    ("11", "killed in the Sinaloa raid"),
    ("50", "missing in the Banten factory fire"),
    ("720/9", "India's record Test total in Wellington"),
]

MARKET_LINES = [
    "MARKETS - FRI CLOSE:   S&P 500 6,910  -3.7%    |    "
    "Nasdaq 22,618  -5.3%",
    "Dow 48,147  -1.9%    |    Brent $92.57    |    Gold $3,538    |    "
    "VIX 35.89",
]


def draw_brief(cv, x, y, w, tag, headline, size=11):
    """Region tag in red caps, then a headline wrapped to two lines."""
    scale = size / 10.0
    tag_txt = tag + "  "
    tw = text_width(tag_txt, size / 10.0 * 0.82)
    cv.text(x, y, size * 0.82, tag_txt, RED, thick=1.1)
    # first line fits beside the tag, second line uses the full width
    words = headline.split(" ")
    lines = []
    cur = ""
    limit = w - tw
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_width(trial, scale) <= limit or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
            limit = w
    if cur:
        lines.append(cur)
    if len(lines) > 2:  # keep the block to two lines
        lines = lines[:2]
        while text_width(lines[1] + "...", scale) > w and " " in lines[1]:
            lines[1] = lines[1].rsplit(" ", 1)[0]
        lines[1] += "..."
    cv.text(x + tw, y, size, lines[0], INK)
    if len(lines) > 1:
        cv.text(x, y + size * 1.45, size, lines[1], INK)


def build_image():
    cv = Canvas()
    M = 26
    CWID = W - 2 * M

    # ---------------------------------------------------------- masthead
    cv.hline(M, 22, CWID, INK, 2)
    cv.text(W / 2, 32, 50, "THE WORLD TODAY", INK, align="center")
    cv.text(M, 98, 14, "MONDAY, 23 NOVEMBER 2026", INK)
    cv.text(W - M, 98, 14, "37 STORIES - 9 REGIONS", RED, align="right")
    cv.hline(M, 118, CWID, INK, 2)
    cv.hline(M, 122, CWID, RULE, 1)

    # -------------------------------------------------------- stats strip
    # Number on its own row, label below with a clear gap.
    y = 130
    bw = (CWID - 4 * 6) / 5
    for i, (val, lab) in enumerate(STATS):
        bx = M + i * (bw + 6)
        cv.fill_rect(bx, y, bw, 48, (255, 255, 255))
        cv.hline(bx, y, bw, RULE, 1)
        cv.hline(bx, y + 47, bw, RULE, 1)
        cv.text(bx + 8, y + 3, 13, val, RED)
        ly = y + 24
        for ln in cv.wrap(lab, 8, bw - 16)[:2]:
            cv.text(bx + 8, ly, 8, ln, INK_SOFT)
            ly += 11.5

    # ------------------------------------------------------------ 3 leads
    y = 184
    colw = (CWID - 2 * 30) / 3
    for i, (tag, head, body, illo) in enumerate(LEADS):
        cx = M + i * (colw + 30)
        cv.text(cx, y, 10, tag, RED)
        illo(cv, cx, y + 16, colw, 112)
        hy = y + 136
        hy = cv.para(cx, hy, 13.5, head, INK, colw, leading=18.5)
        cv.para(cx, hy + 5, 9, body, INK_SOFT, colw, leading=12.5)
        if i < 2:
            cv.vline(cx + colw + 15, y, 250, LIGHT_LINE, 1)

    # ------------------------------------------------ map + Mercury feature
    y = 440
    map_w = 620
    cv.text(M, y, 10, "WHERE IT HAPPENED", RED)
    draw_map(cv, M, y + 16, map_w, 108)
    cv.text(M, y + 128, 9, "Red dots mark the day's datelines, from Sinaloa to Sydney.",
            INK_SOFT)
    fx = M + map_w + 24
    fw = W - M - fx
    cv.text(fx, y, 10, "SCIENCE & TECH", RED)
    draw_mercury(cv, fx, y + 16, fw, 66)
    cv.para(fx, y + 88, 10.5,
            "BepiColombo enters orbit around Mercury after an eight-year "
            "voyage; ESA reports a thruster glitch, the craft is safe.",
            INK_SOFT, fw, leading=13.5)

    # ------------------------------------------------------- briefs grid
    y = 586
    cv.text(M, y, 12, "THE DAY IN BRIEF", INK)
    cv.hline(M, y + 18, CWID, INK, 2)
    y += 26
    colw = (CWID - 2 * 24) / 3
    per_col = [12, 11, 11]
    idx = 0
    for c in range(3):
        cx = M + c * (colw + 24)
        by = y
        for _ in range(per_col[c]):
            tag, head = BRIEFS[idx]
            idx += 1
            draw_brief(cv, cx, by, colw, tag, head, size=8.5)
            by += 26
        if c < 2:
            cv.vline(cx + colw + 12, y - 4, 12 * 26, LIGHT_LINE, 1)

    # ------------------------------------------------------ markets strip
    y = 928
    cv.hline(M, y, CWID, INK, 2)
    cv.hline(M, y + 3, CWID, RULE, 1)
    cv.text(W / 2, y + 10, 9.5, MARKET_LINES[0], INK, align="center")
    cv.text(W / 2, y + 24, 9.5, MARKET_LINES[1], INK, align="center")
    cv.hline(M, y + 40, CWID, RULE, 1)

    # ------------------------------------------------------------- footer
    cv.text(W / 2, 978, 9,
            "Sources: Reuters, AP, AFP, UKMTO, ESA. All stories reported "
            "Monday 23 November 2026.", INK_SOFT, align="center")
    return cv


if __name__ == "__main__":
    main()
