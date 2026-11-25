"""THE GLOBAL HERALD - front page of world news, Tuesday 24 November 2026.

Draws a 1024x1024 newspaper front page with pure-stdlib Python and writes
it to $MAKEFUN_OUTPUT_DIR/entry.png. No network, no randomness, no clock:
every run writes the same bytes.
"""

import math
import os
import struct
import zlib
from pathlib import Path

W, H = 1024, 1024

# ---------------------------------------------------------------- PNG output
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, width, height, rgb):
    """rgb: bytearray of width*height*3 bytes, row-major, filter 0."""
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _chunk(b"IEND", b""))
    Path(path).write_bytes(data)
    return len(data)


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.px[i] = c[0]
                self.px[i + 1] = c[1]
                self.px[i + 2] = c[2]
                i += 3

    def hline(self, x0, x1, y, c, t=1):
        if x0 > x1:
            x0, x1 = x1, x0
        for yy in range(y, y + t):
            for xx in range(x0, x1 + 1):
                self.set(xx, yy, c)

    def vline(self, x, y0, y1, c, t=1):
        if y0 > y1:
            y0, y1 = y1, y0
        for xx in range(x, x + t):
            for yy in range(y0, y1 + 1):
                self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            if fill:
                self.hline(cx - dx, cx + dx, cy + dy, c)
            else:
                self.set(cx - dx, cy + dy, c)
                self.set(cx + dx, cy + dy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for dy in range(-ry, ry + 1):
            dx = int(rx * math.sqrt(max(0.0, 1.0 - (dy * dy) / float(ry * ry))))
            self.hline(cx - dx, cx + dx, cy + dy, c)

    def poly(self, pts, c):
        """Scanline-filled polygon, pts = list of (x, y)."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0, y1 = min(ys), max(ys)
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, ya = pts[i]
                x1, yb = pts[(i + 1) % n]
                if ya == yb:
                    continue
                if (y >= min(ya, yb)) and (y < max(ya, yb)):
                    xs.append(x0 + (y - ya) * (x1 - x0) / (yb - ya))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.hline(int(xs[k]), int(xs[k + 1]), y, c)

    def vgrad(self, x, y, w, h, top, bot):
        for yy in range(h):
            f = yy / max(1, h - 1)
            c = (int(top[0] + (bot[0] - top[0]) * f),
                 int(top[1] + (bot[1] - top[1]) * f),
                 int(top[2] + (bot[2] - top[2]) * f))
            self.hline(x, x + w - 1, y + yy, c)


# --------------------------------------------------------------------- font
# 5x7 bitmap font, written out by hand. Each glyph is 7 rows; bit 4 is the
# leftmost column. Only the characters the page uses are defined.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
    "-": (0, 0, 0, 0x0E, 0, 0, 0),
    "—": (0, 0, 0, 0x1F, 0, 0, 0),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "+": (0, 0x04, 0x04, 0x0E, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    "•": (0, 0x04, 0x0E, 0x0E, 0x0E, 0x04, 0),
    "*": (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
    "#": (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    "@": (0x0E, 0x11, 0x17, 0x15, 0x16, 0x10, 0x0E),
    "<": (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    ">": (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
}


def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, scale, color, align="left"):
    """Draw text; y is the top. align left/center/right around x."""
    s = s.upper()
    if align == "center":
        x -= text_w(s, scale) // 2
    elif align == "right":
        x -= text_w(s, scale)
    for ch in s:
        g = FONT.get(ch, FONT["?"])
        for r in range(7):
            bits = g[r]
            for c in range(5):
                if bits & (1 << (4 - c)):
                    cv.rect(x + c * scale, y + r * scale, scale, scale, color)
        x += 6 * scale


def wrap(s, width, scale):
    """Greedy word wrap; returns list of lines fitting width pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ palette
PAPER = (252, 250, 243)
INK = (18, 18, 18)
RED = (163, 22, 33)
NAVY = (31, 58, 95)
GREY = (105, 105, 100)
BOX = (238, 236, 228)
SKY_TOP = (198, 224, 243)
SKY_BOT = (233, 241, 247)
SEA_TOP = (37, 99, 173)
SEA_BOT = (18, 52, 96)
SHIP = (96, 102, 112)
SHIP_DK = (58, 63, 72)
SMOKE = (88, 88, 84)
FIRE = (249, 115, 22)
FLAME = (251, 191, 36)
CHIP = (30, 41, 59)
GOLD = (217, 119, 6)
GREEN = (22, 163, 74)
SPACE = (15, 23, 42)
ROCKET = (226, 232, 240)


# ------------------------------------------------------------ illustrations
def draw_sea_scene(cv, x, y, w, h):
    """War at sea: sky, drones, a warship, explosion, waves."""
    horizon = y + int(h * 0.52)
    cv.vgrad(x, y, w, horizon - y, SKY_TOP, SKY_BOT)
    cv.vgrad(x, horizon, w, y + h - horizon, SEA_TOP, SEA_BOT)
    # clouds
    for cx, cy, rx, ry in ((x + 90, y + 34, 52, 12), (x + 300, y + 22, 60, 11),
                           (x + 520, y + 44, 46, 10)):
        cv.ellipse(cx, cy, rx, ry, (255, 255, 255))
    # drones: small quadcopters in the sky
    for dx, dy in ((x + 150, y + 62), (x + 430, y + 48), (x + 300, y + 84)):
        cv.rect(dx - 7, dy - 2, 14, 5, INK)
        cv.hline(dx - 13, dx + 13, dy - 6, INK, 2)
        cv.hline(dx - 13, dx + 13, dy + 4, INK, 2)
        cv.vline(dx - 5, dy + 3, dy + 9, INK)
        cv.vline(dx + 5, dy + 3, dy + 9, INK)
    # explosion starburst at the ship's bow
    ex, ey = x + w - 118, horizon - 26
    for r, c in ((46, (220, 60, 30)), (34, FIRE), (22, FLAME), (11, (253, 224, 71))):
        pts = []
        for k in range(16):
            ang = math.pi * k / 8.0
            rr = r if k % 2 == 0 else r * 0.45
            pts.append((int(ex + rr * math.cos(ang)),
                        int(ey + rr * math.sin(ang))))
        cv.poly(pts, c)
    # smoke plume above the explosion
    for sx, sy, sr in ((ex - 8, ey - 52, 15), (ex + 12, ey - 66, 18),
                       (ex + 2, ey - 82, 13), (ex - 18, ey - 40, 11)):
        cv.circle(sx, sy, sr, SMOKE)
    # warship: hull, superstructure, mast, funnel
    hx0, hx1 = x + 70, x + w - 190
    deck = horizon + 6
    cv.poly([(hx0, deck), (hx1, deck), (hx1 - 14, deck + 34),
             (hx0 + 34, deck + 34)], SHIP)
    cv.rect(hx0 + 8, deck + 34, hx1 - hx0 - 26, 5, SHIP_DK)
    cv.rect(hx0 + 90, deck - 34, 150, 34, SHIP)
    cv.rect(hx0 + 110, deck - 52, 60, 18, SHIP_DK)
    cv.vline(hx0 + 250, deck - 84, deck - 34, SHIP_DK, 5)
    cv.hline(hx0 + 236, hx0 + 264, deck - 84, SHIP_DK, 4)
    cv.rect(hx0 + 190, deck - 58, 26, 24, (150, 40, 40))
    for sx, sy, sr in ((hx0 + 203, deck - 72, 9), (hx0 + 210, deck - 86, 12),
                       (hx0 + 198, deck - 98, 8)):
        cv.circle(sx, sy, sr, SMOKE)
    # gun turret at the bow
    cv.rect(hx1 - 52, deck - 16, 44, 16, SHIP_DK)
    cv.line(hx1 - 12, deck - 10, hx1 + 34, deck - 22, SHIP_DK, 4)
    # wake foam and waves
    for wy in range(horizon + 42, y + h - 6, 16):
        for wx in range(x + 12, x + w - 12, 46):
            cv.hline(wx, wx + 22, wy, (220, 235, 245), 2)
    for fx in range(hx0 - 40, hx0 + 10, 12):
        cv.hline(fx, fx + 18, deck + 40, (235, 244, 250), 3)
    cv.rect(x, y, w, 2, INK)
    cv.rect(x, y + h - 2, w, 2, INK)
    cv.rect(x, y, 2, h, INK)
    cv.rect(x + w - 2, y, 2, h, INK)


def draw_chip(cv, x, y, w, h):
    """AI chip with pins and a rising trend arrow."""
    cv.rect(x, y, w, h, (219, 228, 238))
    cv.rect(x + 3, y + 3, w - 6, h - 6, INK)
    # pins
    for i in range(6):
        px = x + 24 + i * 42
        cv.rect(px, y - 2, 10, 8, GOLD)
        cv.rect(px, y + h - 6, 10, 8, GOLD)
    for i in range(3):
        py = y + 22 + i * 30
        cv.rect(x - 2, py, 8, 9, GOLD)
        cv.rect(x + w - 6, py, 8, 9, GOLD)
    # die
    cv.rect(x + 62, y + 24, w - 124, h - 48, CHIP)
    cv.rect(x + 62, y + 24, w - 124, 3, GOLD)
    cv.rect(x + 62, y + h - 27, w - 124, 3, GOLD)
    # rising arrow across the die, behind the label, behind the label
    pts = [(x + 74, y + h - 38), (x + 118, y + h - 62), (x + 150, y + h - 52),
           (x + 196, y + h - 84), (x + 232, y + h - 84)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], GREEN, 4)
    cv.poly([(x + 232, y + h - 84), (x + 214, y + h - 84),
             (x + 232, y + h - 66)], GREEN)
    # clear label plate so the arrow never crosses the letters
    cv.rect(x + w // 2 - 34, y + h // 2 - 18, 68, 36, CHIP)
    draw_text(cv, x + w // 2, y + h // 2 - 14, "AI", 4, (255, 255, 255),
              align="center")


def draw_scales(cv, x, y, w, h):
    """Scales of justice on a pale panel."""
    cv.rect(x, y, w, h, (233, 230, 218))
    cx = x + w // 2
    base = y + h - 16
    cv.rect(cx - 34, base, 68, 6, NAVY)
    cv.vline(cx, y + 18, base, NAVY, 5)
    cv.hline(cx - 74, cx + 74, y + 26, NAVY, 4)
    cv.circle(cx, y + 14, 7, GOLD)
    for sgn in (-1, 1):
        px = cx + sgn * 74
        cv.line(cx, y + 28, px - 16, y + 58, NAVY, 2)
        cv.line(cx, y + 28, px + 16, y + 58, NAVY, 2)
        cv.line(px - 16, y + 58, px + 16, y + 58, NAVY, 2)
        cv.poly([(px - 26, y + 58), (px + 26, y + 58), (px, y + 70)], GOLD)
    cv.rect(x, y, w, 2, INK)
    cv.rect(x, y + h - 2, w, 2, INK)
    cv.rect(x, y, 2, h, INK)
    cv.rect(x + w - 2, y, 2, h, INK)


def draw_rocket(cv, x, y, w, h):
    """Rocket climbing through a starry sky."""
    cv.rect(x, y, w, h, SPACE)
    for sx, sy, sr in ((x + 30, y + 24, 2), (x + 90, y + 60, 2),
                       (x + 150, y + 18, 3), (x + 230, y + 44, 2),
                       (x + 300, y + 20, 2), (x + 360, y + 70, 3),
                       (x + 420, y + 30, 2), (x + 260, y + 96, 2)):
        cv.circle(sx, sy, sr, (255, 255, 255))
    cx = x + w // 2
    top = y + 6
    cv.poly([(cx, top), (cx + 26, top + 34), (cx - 26, top + 34)], (185, 28, 28))
    cv.rect(cx - 26, top + 34, 52, 46, ROCKET)
    cv.ellipse(cx, top + 58, 11, 11, (147, 197, 253))
    cv.ellipse(cx, top + 58, 7, 7, (30, 64, 175))
    cv.poly([(cx - 26, top + 80), (cx - 52, top + 94), (cx - 26, top + 70)],
            (185, 28, 28))
    cv.poly([(cx + 26, top + 80), (cx + 52, top + 94), (cx + 26, top + 70)],
            (185, 28, 28))
    cv.poly([(cx - 13, top + 80), (cx + 13, top + 80), (cx, top + 106)],
            FLAME)
    cv.poly([(cx - 6, top + 80), (cx + 6, top + 80), (cx, top + 96)],
            (253, 224, 71))
    for sx, sy, sr in ((cx - 12, top + 108, 4), (cx + 10, top + 110, 5)):
        cv.circle(sx, sy, sr, (148, 163, 184))
    cv.rect(x, y, w, 2, INK)
    cv.rect(x, y + h - 2, w, 2, INK)
    cv.rect(x, y, 2, h, INK)
    cv.rect(x + w - 2, y, 2, h, INK)


def draw_ship(cv, x, y, w, h):
    """Container ship at sea, stacked boxes in bright colours."""
    cv.vgrad(x, y, w, h, (214, 230, 242), (238, 242, 247))
    cv.ellipse(x + 60, y + 22, 40, 9, (255, 255, 255))
    cv.ellipse(x + w - 90, y + 34, 48, 10, (255, 255, 255))
    sea = y + int(h * 0.62)
    cv.rect(x, sea, w, y + h - sea, SEA_TOP)
    for wy in range(sea + 10, y + h - 4, 14):
        for wx in range(x + 10, x + w - 10, 52):
            cv.hline(wx, wx + 24, wy, (200, 222, 240), 2)
    # stacked containers
    cols = [(220, 38, 38), (37, 99, 235), (22, 163, 74), (234, 179, 8),
            (220, 38, 38), (37, 99, 235)]
    bx, bw, bh = x + 66, 56, 20
    for row in range(3):
        for col in range(6):
            cx0 = bx + col * (bw + 4)
            cy0 = sea - (row + 1) * (bh + 3)
            cv.rect(cx0, cy0, bw, bh, cols[(col + row) % 6])
            cv.rect(cx0, cy0, bw, 2, INK)
    # hull
    cv.poly([(x + 30, sea - 6), (x + w - 30, sea - 6), (x + w - 66, sea + 34),
             (x + 66, sea + 34)], (40, 40, 44))
    cv.rect(x + 30, sea - 6, w - 60, 4, (185, 28, 28))
    # bridge tower
    cv.rect(x + w - 150, sea - 70, 46, 64, (240, 240, 235))
    cv.rect(x + w - 150, sea - 70, 46, 12, NAVY)
    for wy in range(sea - 52, sea - 12, 16):
        cv.rect(x + w - 142, wy, 30, 8, NAVY)
    cv.rect(x, y, w, 2, INK)
    cv.rect(x, y + h - 2, w, 2, INK)
    cv.rect(x, y, 2, h, INK)
    cv.rect(x + w - 2, y, 2, h, INK)


# ------------------------------------------------------------------- layout
M = 28            # page margin
R = 996           # right edge (1024 - 28)


def rule(cv, y, x0=M, x1=R, t=2, c=INK):
    cv.hline(x0, x1, y, c, t)


def build(cv):
    # ---- masthead ------------------------------------------------------
    cv.hline(M, R, 20, INK, 2)
    draw_text(cv, W // 2, 30, "THE GLOBAL HERALD", 7, INK, align="center")
    cv.hline(M, R, 88, INK, 3)
    cv.hline(M, R, 94, INK, 1)
    draw_text(cv, M, 102, "TUESDAY, 24 NOVEMBER 2026", 2, INK)
    draw_text(cv, R, 102, "GLOBAL EDITION", 2, INK, align="right")
    rule(cv, 124)

    # ---- zone A: lead + right column -----------------------------------
    draw_sea_scene(cv, M, 136, 632, 230)
    cv.vline(674, 136, 556, GREY, 1)
    draw_text(cv, M, 378, "WAR AT SEA", 2, RED)
    for i, ln in enumerate(("UKRAINE SINKS", "RUSSIAN WARSHIP", "OFF LIBYA")):
        draw_text(cv, M, 398 + i * 34, ln, 4, INK)
    deck = ("Naval drones sink a Russian corvette off Benghazi and destroy "
            "a helicopter, widening the war.")
    for i, ln in enumerate(wrap(deck, 632, 2)):
        draw_text(cv, M, 504 + i * 20, ln, 2, INK)

    # story 2: Nvidia
    draw_chip(cv, 688, 136, 308, 88)
    for i, ln in enumerate(("HUANG BACK AT", "NVIDIA")):
        draw_text(cv, 688, 232 + i * 27, ln, 3, INK)
    deck2 = ("Trump steps in to restore the chief; shares soar and "
             "Nasdaq jumps 6.5%.")
    for i, ln in enumerate(wrap(deck2, 308, 2)):
        draw_text(cv, 688, 287 + i * 20, ln, 2, INK)
    cv.hline(688, R, 347, GREY, 1)

    # story 3: ICJ / Rohingya
    draw_scales(cv, 688, 353, 308, 88)
    for i, ln in enumerate(("14 NATIONS BACK", "ICJ RULING")):
        draw_text(cv, 688, 449 + i * 27, ln, 3, INK)
    deck3 = ("UK, Canada, Australia affirm the ICJ genocide ruling "
             "on the Rohingya.")
    for i, ln in enumerate(wrap(deck3, 308, 2)):
        draw_text(cv, 688, 504 + i * 20, ln, 2, INK)

    # ---- zone B: space + trade -----------------------------------------
    rule(cv, 568)
    draw_rocket(cv, M, 580, 472, 118)
    cv.vline(512, 580, 796, GREY, 1)
    for i, ln in enumerate(("CHINA LAUNCHES", "SHENZHOU 24")):
        draw_text(cv, M, 706 + i * 27, ln, 3, INK)
    deck4 = "First Pakistani astronaut boards the Tiangong space station."
    for i, ln in enumerate(wrap(deck4, 472, 2)):
        draw_text(cv, M, 761 + i * 20, ln, 2, INK)

    draw_ship(cv, 524, 580, 472, 118)
    for i, ln in enumerate(("US READIES TARIFFS", "ON CHINA AND EU")):
        draw_text(cv, 524, 706 + i * 27, ln, 3, INK)
    deck5 = "Washington targets subsidised output, AP sources say."
    for i, ln in enumerate(wrap(deck5, 472, 2)):
        draw_text(cv, 524, 761 + i * 20, ln, 2, INK)

    # ---- zone C: markets -----------------------------------------------
    rule(cv, 812)
    cv.rect(M, 820, R - M, 42, BOX)
    items = "S&P 500 +4.7%  •  NASDAQ +6.5%  •  GOLD $3,620  •  BRENT $86.7"
    total = text_w("MARKETS: ", 2) + text_w(items, 2)
    sx = (W - total) // 2
    draw_text(cv, sx, 833, "MARKETS:", 2, RED)
    draw_text(cv, sx + text_w("MARKETS: ", 2), 833, items, 2, INK)

    # ---- zone D: in brief ----------------------------------------------
    rule(cv, 876)
    draw_text(cv, M, 886, "IN BRIEF", 2, RED)
    briefs = ("Russian strike kills 2 in Odesa. Oxfam calls Gaza a "
              "'toxic land'. N. Korea orders Swiss envoy out. Nepal quake "
              "5.6. UN chief urges AI rules within a year. Arsenal held "
              "by Dortmund.")
    for i, ln in enumerate(wrap(briefs, R - M, 2)):
        draw_text(cv, M, 908 + i * 20, ln, 2, INK)

    # ---- footer ---------------------------------------------------------
    rule(cv, 970, t=1, c=GREY)
    draw_text(cv, W // 2, 976,
              "THE GLOBAL HERALD • TUESDAY, 24 NOVEMBER 2026 • PAGE 1",
              2, GREY, align="center")


# --------------------------------------------------------------------- main
def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    os.makedirs(outdir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    build(cv)
    path = os.path.join(outdir, "entry.png")
    n = write_png(path, W, H, cv.px)
    print("wrote %s (%d bytes)" % (path, n))
    try:
        Path("entry.png").write_bytes(Path(path).read_bytes())
    except Exception:
        pass


if __name__ == "__main__":
    main()
