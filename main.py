#!/usr/bin/env python3
"""Front page of THE WORLD TODAY for Tuesday, 24 November 2026.

Renders a one-page newspaper front page (1024 x 1024 PNG) summing up
24 November 2026 world news: a masthead and dateline, a hand-drawn
sunset scene of tankers in a strait, the lead story on the US-Iran
blockade standoff, six short stories in a two-column grid, and a sport
strip at the foot.

STDLIB ONLY: the image is built pixel by pixel in a bytearray and
encoded as PNG by hand (zlib + struct). Text uses an embedded 5x7
bitmap font, so the program needs no Pillow, no font files, no network
and no clock. It runs in the grader's minimal python3.13 image and on
a read-only source tree: it writes entry.png to $MAKEFUN_OUTPUT_DIR
when that variable is set (the grader sets it to /output), and also
tries a copy next to this script, ignoring failures there.

Deterministic: fixed text, fixed geometry, fixed compression level, so
running the script twice yields byte-identical PNG data.
"""

import math
import os
import struct
import zlib
from pathlib import Path

# ---------------------------------------------------------------- page setup

PAGE_W = 1024
PAGE_H = 1024
EDGE = 30                        # outer margin on both sides
INNER_W = PAGE_W - 2 * EDGE      # usable width between the margins

PAPER = (251, 250, 246)          # warm off-white newsprint
INK = (20, 20, 20)              # near-black for text and rules
FAINT = (74, 74, 74)            # grey for captions and decks
RED = (178, 34, 34)             # accent for the lead kicker

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank. Only
# capitals are stored; lowercase input is uppercased on lookup.

GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#..", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...#.", "..#..", "..#..", "..#..", "..#..", "..#..", "...#."),
    ")": (".#...", "..#..", "..#..", "..#..", "..#..", "..#..", ".#..."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "/": ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "•": (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
}

# Characters that have no glyph of their own map to these.
ALIASES = {"–": "-", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"'}


def glyph_for(ch):
    """Return the 7-row bitmap for a character (uppercase lookup)."""
    ch = ALIASES.get(ch, ch)
    return GLYPHS.get(ch.upper(), GLYPHS[" "])


# ---------------------------------------------------------------- canvas

class Canvas:
    """An RGB pixel buffer with simple drawing primitives."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        r, g, b = colour
        self.buf = bytearray(bytes((r, g, b)) * (width * height))

    def fill_rect(self, x, y, w, h, colour):
        """Fill an axis-aligned rectangle (clipped to the page)."""
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(colour) * (x1 - x0)
        stride = self.width * 3
        for yy in range(y0, y1):
            off = yy * stride + x0 * 3
            self.buf[off:off + len(row)] = row

    def rule(self, x, y, w, thick=2, colour=INK):
        self.fill_rect(x, y, w, thick, colour)

    def set_px(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            off = (y * self.width + x) * 3
            self.buf[off:off + 3] = bytes(colour)

    def line(self, x0, y0, x1, y1, colour):
        """Bresenham line."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_px(x0, y0, colour)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, colour):
        for dy in range(-r, r + 1):
            dx = math.isqrt(r * r - dy * dy)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, colour)

    def fill_poly(self, points, colour):
        """Scanline fill of a simple polygon (even-odd rule)."""
        ys = [p[1] for p in points]
        y0, y1 = min(ys), max(ys)
        n = len(points)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, ya = points[i]
                x1, yb = points[(i + 1) % n]
                if ya == yb:
                    continue
                if (ya <= y < yb) or (yb <= y < ya):
                    xs.append(x0 + (y - ya) * (x1 - x0) / (yb - ya))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa = int(math.ceil(xs[i]))
                xb = int(math.floor(xs[i + 1]))
                if xb >= xa:
                    self.fill_rect(xa, y, xb - xa + 1, 1, colour)

    # -- text ------------------------------------------------------

    def text_width(self, text, scale):
        return len(text) * 6 * scale - scale

    def text(self, x, y, text, scale, colour):
        """Draw text left-aligned at (x, y); returns the width drawn."""
        cx = x
        for ch in text:
            glyph = glyph_for(ch)
            for gy, row in enumerate(glyph):
                for gx, cell in enumerate(row):
                    if cell == "#":
                        self.fill_rect(cx + gx * scale, y + gy * scale,
                                       scale, scale, colour)
            cx += 6 * scale
        return cx - x - scale

    def text_centred(self, cx, y, text, scale, colour):
        w = self.text_width(text, scale)
        self.text(cx - w // 2, y, text, scale, colour)

    def wrap(self, text, scale, max_width):
        """Word-wrap text to lines that fit max_width pixels."""
        lines = []
        for paragraph in text.split("\n"):
            line = ""
            for word in paragraph.split(" "):
                trial = word if not line else line + " " + word
                if self.text_width(trial, scale) <= max_width:
                    line = trial
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)
        return lines


# ---------------------------------------------------------------- PNG

def png_bytes(canvas):
    """Encode the canvas as a PNG (colour type 2, 8-bit, filter 0)."""
    w, h = canvas.width, canvas.height
    raw = bytearray()
    stride = w * 3
    buf = canvas.buf
    for y in range(h):
        raw.append(0)
        raw += buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- content

MASTHEAD = "THE WORLD TODAY"
DATELINE = "TUESDAY, 24 NOVEMBER 2026"

CAPTION = ("Tankers cross the strait at dusk as the US naval blockade "
           "tightens around Iran. (Illustration)")

KICKER = "US-IRAN STANDOFF"
LEAD_HEAD = ["TRUMP DARES IRAN", "TO TEST BLOCKADE"]
LEAD_DECK = ("They'll all be at the bottom of the sea, president warns, "
             "as Tehran readies a 14-tanker convoy and unveils an "
             "underground missile city.")

STORIES = [
    ("BANTEN FIRE TOLL 24",
     "A blaze at a candy factory in Serang, Indonesia, kills 24; about "
     "30 workers still missing."),
    ("HOLY CITIES BY RAIL",
     "Modi and Nepal PM Balendra Shah flag off the Saryu-Kamala Express; "
     "the first train reaches Janakpur today."),
    ("COP31 IN RUINS",
     "Climate talks in Antalya collapse with no deal after record "
     "overtime; the draft never mentioned fossil fuels."),
    ("153 DRONES OVERNIGHT",
     "Russia fires 153 drones at Ukraine, 60 of them jet-powered; Kyiv "
     "counts its dead after a block of flats collapses."),
    ("COURT: MYANMAR GUILTY",
     "The World Court finds Myanmar committed genocide against the "
     "Rohingya and orders reparations."),
    ("VERSTAPPEN WINS VEGAS",
     "Max Verstappen takes a chaotic Las Vegas Grand Prix, beating "
     "Norris by 0.639 seconds."),
]

SPORT = ("SPORT  New Zealand bat out the final day to draw the Wellington "
         "Test; India declared on 720/9, Pant 128.")


# ---------------------------------------------------------------- scene

def draw_sunset(canvas, x, y, w, h):
    """Sunset over a strait: banded sky, sun, sea, two tankers, birds."""
    horizon = y + int(h * 0.62)
    top = (255, 122, 42)
    mid = (255, 176, 88)
    low = (250, 222, 150)
    for yy in range(y, horizon):
        t = (yy - y) / max(1, horizon - y)
        if t < 0.55:
            a, b, f = top, mid, t / 0.55
        else:
            a, b, f = mid, low, (t - 0.55) / 0.45
        colour = tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))
        canvas.fill_rect(x, yy, w, 1, colour)

    # sun with a pale halo
    sun_x = x + int(w * 0.72)
    sun_y = y + int(h * 0.38)
    canvas.fill_circle(sun_x, sun_y, 52, (255, 214, 130))
    canvas.fill_circle(sun_x, sun_y, 40, (255, 232, 158))

    # birds
    for bx, by, s in ((x + 150, y + 52, 9), (x + 205, y + 74, 7),
                      (x + 250, y + 44, 8)):
        canvas.line(bx - s, by, bx, by + 5, INK)
        canvas.line(bx, by + 5, bx + s, by, INK)

    # sea
    canvas.fill_rect(x, horizon, w, y + h - horizon, (18, 62, 92))
    for yy in range(horizon + 14, y + h - 6, 16):
        for xx in range(x + 24, x + w - 60, 120):
            canvas.fill_rect(xx, yy, 54, 2, (70, 128, 158))

    # tanker silhouettes
    hull = (24, 24, 34)
    # big tanker, left
    canvas.fill_poly([(x + 70, horizon + 34), (x + 500, horizon + 34),
                      (x + 520, horizon + 52), (x + 500, horizon + 70),
                      (x + 70, horizon + 70)], hull)
    canvas.fill_rect(x + 380, horizon + 6, 62, 28, hull)     # deckhouse
    canvas.fill_rect(x + 452, horizon - 4, 18, 38, hull)     # funnel
    canvas.fill_rect(x + 130, horizon - 2, 4, 36, hull)      # mast
    # reflection streaks
    for xx in range(x + 90, x + 500, 46):
        canvas.fill_rect(xx, horizon + 74, 22, 3, (70, 128, 158))
    # small tanker, right
    canvas.fill_poly([(x + 590, horizon + 44), (x + 880, horizon + 44),
                      (x + 896, horizon + 58), (x + 880, horizon + 74),
                      (x + 590, horizon + 74)], hull)
    canvas.fill_rect(x + 780, horizon + 20, 46, 24, hull)
    canvas.fill_rect(x + 832, horizon + 12, 14, 32, hull)
    for xx in range(x + 610, x + 880, 52):
        canvas.fill_rect(xx, horizon + 78, 20, 3, (70, 128, 158))


# ---------------------------------------------------------------- layout

def build_front_page():
    page = Canvas(PAGE_W, PAGE_H, PAPER)
    y = 22
    page.rule(EDGE, y, INNER_W, 3)
    y += 12
    page.text_centred(PAGE_W // 2, y, MASTHEAD, 7, INK)
    y += 7 * 7 + 12
    page.rule(EDGE, y, INNER_W, 2)
    y += 10
    page.text_centred(PAGE_W // 2, y, DATELINE, 2, INK)
    y += 7 * 2 + 10
    page.rule(EDGE, y, INNER_W, 2)
    y += 12

    # hero illustration
    hero_h = 280
    page.rule(EDGE, y, INNER_W, 2)
    page.rule(EDGE, y + hero_h, INNER_W, 2)
    page.rule(EDGE, y, 2, hero_h)
    page.rule(EDGE + INNER_W - 2, y, 2, hero_h)
    draw_sunset(page, EDGE + 2, y + 2, INNER_W - 4, hero_h - 4)
    y += hero_h + 10
    for line in page.wrap(CAPTION, 2, INNER_W):
        page.text(EDGE, y, line, 2, FAINT)
        y += 7 * 2 + 5
    y += 8

    # lead story
    page.fill_rect(EDGE, y, 10, 14, RED)
    page.text(EDGE + 18, y, KICKER, 2, RED)
    y += 7 * 2 + 10
    for line in LEAD_HEAD:
        page.text(EDGE, y, line, 4, INK)
        y += 7 * 4 + 6
    y += 4
    for line in page.wrap(LEAD_DECK, 2, INNER_W):
        page.text(EDGE, y, line, 2, FAINT)
        y += 7 * 2 + 6
    y += 10
    page.rule(EDGE, y, INNER_W, 2)
    y += 14

    # six stories, two columns x three rows
    col_w = (INNER_W - 20) // 2
    row_h = 106
    for i, (head, body) in enumerate(STORIES):
        col = i % 2
        row = i // 2
        sx = EDGE + col * (col_w + 20)
        sy = y + row * row_h
        head_lines = page.wrap(head, 3, col_w)
        page.text(sx, sy, head_lines[0], 3, INK)
        by = sy + 7 * 3 + 8
        for line in page.wrap(body, 2, col_w)[:3]:
            page.text(sx, by, line, 2, INK)
            by += 7 * 2 + 6
    y += 3 * row_h + 6

    # sport strip
    page.rule(EDGE, y, INNER_W, 2)
    y += 12
    tag = "SPORT"
    tag_w = page.text_width(tag, 2) + 16
    page.fill_rect(EDGE, y, tag_w, 7 * 2 + 8, INK)
    page.text(EDGE + 8, y + 4, tag, 2, PAPER)
    sx = EDGE + tag_w + 12
    for line in page.wrap(SPORT[len("SPORT  "):], 2, INNER_W - tag_w - 12)[:2]:
        page.text(sx, y + 4, line, 2, INK)
        y += 7 * 2 + 6
    y += 14
    page.rule(EDGE, y, INNER_W, 3)

    return page


# ---------------------------------------------------------------- entry

def main():
    data = png_bytes(build_front_page())

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    targets = []
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        targets.append(Path(out_dir) / "entry.png")
    targets.append(Path(__file__).resolve().parent / "entry.png")

    wrote = False
    for target in targets:
        try:
            target.write_bytes(data)
            print(f"wrote {target} ({len(data)} bytes)")
            wrote = True
        except OSError as exc:
            # The grader mounts the repo read-only; the output dir is
            # the real destination, so a failed local copy is harmless.
            print(f"skip {target}: {exc}")
    if not wrote:
        raise SystemExit("could not write entry.png anywhere")


if __name__ == "__main__":
    main()
