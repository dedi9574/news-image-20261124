#!/usr/bin/env python3
"""Front page of THE WORLD TODAY for Tuesday, 24 November 2026.

Builds a one-page newspaper front page (1024 x 1024 PNG) with Pillow:
a masthead and dateline, a hand-drawn sunset scene of tankers in a
strait, the lead story on the US-Iran blockade standoff, six short
stories in a two-column grid, and a sport strip at the foot.

All text and all geometry are fixed constants, so the output is fully
deterministic: running the script twice yields byte-identical PNG data.
No clock, no randomness, no network access.
"""

import os
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- page setup

PAGE_W = 1024
PAGE_H = 1024
EDGE = 30                        # outer margin on both sides
INNER_W = PAGE_W - 2 * EDGE      # usable width between the margins

PAPER = (251, 250, 246)          # warm off-white newsprint
INK = (20, 20, 20)              # near-black for text and rules
FAINT = (74, 74, 74)            # grey for the photo caption

# ---------------------------------------------------------------- fonts

FONT_PATHS = {
    "serif_bold": [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ],
    "serif": [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ],
    "serif_italic": [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ],
    "sans_bold": [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
}


def pick_font(kind, size):
    """Return the first usable font file for kind, else Pillow's default."""
    for path in FONT_PATHS[kind]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


# ---------------------------------------------------------------- text tools

def wrap_text(canvas, text, font, max_width):
    """Greedy word wrap: split text into lines no wider than max_width."""
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if canvas.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def paint_lines(canvas, lines, font, x, y, leading, fill=INK):
    """Draw lines top to bottom, returning the y just below the last one."""
    for line in lines:
        canvas.text((x, y), line, font=font, fill=fill)
        y += leading
    return y


def rule(canvas, y, weight=1):
    """A solid horizontal rule spanning the content width."""
    canvas.rectangle([EDGE, y, PAGE_W - EDGE, y + weight - 1], fill=INK)


# ---------------------------------------------------------------- hero picture

def _lerp(a, b, t):
    """Blend two RGB colours by factor t (0..1)."""
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _tanker(canvas, cx, water_y, scale, hull, deck):
    """Draw one tanker silhouette centred on cx, floating on water_y."""
    hull_w = int(150 * scale)
    hull_h = int(26 * scale)
    bow = int(26 * scale)
    x0 = cx - hull_w // 2
    x1 = cx + hull_w // 2
    # Hull: a long body with a tapered bow on the right.
    canvas.polygon(
        [
            (x0, water_y - hull_h),
            (x1 - bow, water_y - hull_h),
            (x1, water_y - hull_h // 2),
            (x1, water_y),
            (x0, water_y),
        ],
        fill=hull,
    )
    # White superstructure block and bridge near the stern.
    sup_w = int(34 * scale)
    sup_h = int(22 * scale)
    canvas.rectangle(
        [x0 + int(16 * scale), water_y - hull_h - sup_h,
         x0 + int(16 * scale) + sup_w, water_y - hull_h],
        fill=deck,
    )
    canvas.rectangle(
        [x0 + int(20 * scale), water_y - hull_h - sup_h - int(8 * scale),
         x0 + int(20 * scale) + int(26 * scale),
         water_y - hull_h - sup_h],
        fill=deck,
    )
    # Funnel with a dark red band, plus a thin mast and a wisp of smoke.
    fx = x0 + int(64 * scale)
    canvas.rectangle(
        [fx, water_y - hull_h - int(20 * scale),
         fx + int(10 * scale), water_y - hull_h],
        fill=(140, 47, 38),
    )
    canvas.line(
        [cx + hull_w // 2 - int(30 * scale), water_y - hull_h,
         cx + hull_w // 2 - int(30 * scale),
         water_y - hull_h - int(34 * scale)],
        fill=hull, width=max(1, int(2 * scale)),
    )
    for k, (dx, dy, r) in enumerate(((0, -6, 7), (9, -14, 9), (20, -22, 11))):
        canvas.ellipse(
            [fx + dx - r, water_y - hull_h - int(20 * scale) + dy - r,
             fx + dx + r, water_y - hull_h - int(20 * scale) + dy + r],
            fill=(168, 160, 152),
        )


def paint_strait(canvas, box):
    """Paint the hero scene: dusk sky, sun, sea, cliffs, three tankers."""
    x0, y0, x1, y1 = box
    width = x1 - x0
    horizon = y0 + int((y1 - y0) * 0.58)

    # Sky: warm orange at the top fading into a dusky mauve at the sea.
    sky_top = (233, 166, 106)
    sky_low = (146, 104, 118)
    for yy in range(y0, horizon):
        t = (yy - y0) / max(1, horizon - y0)
        canvas.line([(x0, yy), (x1, yy)], fill=_lerp(sky_top, sky_low, t))

    # Low sun with a soft glow, sitting just above the horizon.
    sun_cx, sun_cy = x0 + int(width * 0.66), horizon - 46
    canvas.ellipse(
        [sun_cx - 42, sun_cy - 42, sun_cx + 42, sun_cy + 42],
        fill=(240, 190, 128),
    )
    canvas.ellipse(
        [sun_cx - 26, sun_cy - 26, sun_cx + 26, sun_cy + 26],
        fill=(246, 216, 152),
    )

    # Sea: dark blue-grey with a few pale, flat wave streaks.
    canvas.rectangle([x0, horizon, x1, y1], fill=(61, 76, 94))
    streaks = [
        (0.10, 0.05, 0.30), (0.22, 0.55, 0.28), (0.30, 0.20, 0.42),
        (0.42, 0.62, 0.30), (0.52, 0.08, 0.36), (0.63, 0.45, 0.40),
        (0.74, 0.25, 0.30), (0.85, 0.58, 0.34), (0.94, 0.12, 0.26),
    ]
    sea_h = y1 - horizon
    for frac, start, length in streaks:
        yy = horizon + int(sea_h * frac)
        sx = x0 + int(width * start)
        ex = sx + int(width * length)
        canvas.line([(sx, yy), (ex, yy)], fill=(96, 112, 130), width=2)

    # Rocky headlands left and right, closing the strait.
    canvas.polygon(
        [(x0, y1), (x0, y0 + 30), (x0 + 150, y0 + 96),
         (x0 + 210, y0 + 150), (x0 + 170, y1)],
        fill=(46, 42, 40),
    )
    canvas.polygon(
        [(x1, y1), (x1, y0 + 64), (x1 - 120, y0 + 118),
         (x1 - 190, y0 + 168), (x1 - 150, y1)],
        fill=(40, 37, 35),
    )

    # Three tankers: one distant near the horizon, two closer in.
    _tanker(canvas, x0 + int(width * 0.52), horizon + 26, 0.42,
            (24, 24, 30), (150, 154, 158))
    _tanker(canvas, x0 + int(width * 0.72), horizon + 78, 0.72,
            (22, 22, 28), (196, 199, 203))
    _tanker(canvas, x0 + int(width * 0.38), y1 - 18, 1.05,
            (18, 18, 24), (207, 210, 214))

    # Two gulls high in the sky.
    for gx, gy in ((x0 + 120, y0 + 42), (x0 + 210, y0 + 66)):
        canvas.line([(gx - 10, gy), (gx, gy - 6), (gx + 10, gy)],
                    fill=(60, 52, 48), width=2)

    # Thin black frame around the picture.
    canvas.rectangle([x0, y0, x1 - 1, y1 - 1], outline=INK, width=2)


# ---------------------------------------------------------------- story cells

def story_cell(canvas, x, y, width, headline, body, head_font, body_font):
    """One grid item: bold headline, then a short body paragraph."""
    y = paint_lines(
        canvas, wrap_text(canvas, headline, head_font, width),
        head_font, x, y, 27,
    )
    y += 4
    y = paint_lines(
        canvas, wrap_text(canvas, body, body_font, width),
        body_font, x, y, 21,
    )
    return y


# ---------------------------------------------------------------- the page

LEAD_HEADLINE = "TRUMP DARES IRAN: 'AT THE BOTTOM OF THE SEA'"
LEAD_DECK = (
    "US president warns Iranian tankers that test the naval blockade will "
    "be sunk; Tehran shows off an underground 'missile city' and readies a "
    "14-tanker convoy as strikes may resume in the new year."
)
PHOTO_CAPTION = (
    "Tankers gather near Kharg Island as Iran threatens to test the US blockade."
)

GRID_STORIES = [
    ("BANTEN FIRE TOLL 24",
     "A blaze at a candy factory in Serang, Indonesia, kills 24; about 30 "
     "workers still missing as rescuers search the wreckage."),
    ("HOLY CITIES BY RAIL",
     "Modi and Nepal PM Balendra Shah flag off the Saryu-Kamala Express; "
     "the first train reaches Janakpur this morning."),
    ("COP31 IN RUINS",
     "Climate talks in Antalya collapse with no deal after record "
     "overtime; the draft never even mentioned fossil fuels."),
    ("153 DRONES OVERNIGHT",
     "Russia fires 153 drones at Ukraine, 60 of them jet-powered; Kyiv "
     "region counts its dead after a block of flats collapses."),
    ("COURT: MYANMAR GUILTY",
     "The World Court finds Myanmar committed genocide against the "
     "Rohingya \u2014 the first state ever held responsible \u2014 and orders "
     "reparations."),
    ("VERSTAPPEN WINS VEGAS",
     "Max Verstappen takes a chaotic Las Vegas GP \u2014 35 lead changes, "
     "352 overtakes \u2014 beating Norris by 0.639 seconds."),
]

SPORT_TEXT = (
    "New Zealand bat out the final day to draw the Wellington Test; India "
    "declared on 720/9, Pant 128, but Mitchell and Phillips hold firm at 239/5."
)


def build_front_page():
    """Assemble the whole front page and return the Pillow image."""
    page = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    canvas = ImageDraw.Draw(page)

    masthead = pick_font("serif_bold", 84)
    dateline = pick_font("sans_bold", 23)
    caption_font = pick_font("serif_italic", 19)
    lead_font = pick_font("serif_bold", 48)
    deck_font = pick_font("serif", 20)
    cell_head = pick_font("serif_bold", 22)
    cell_body = pick_font("serif", 16)
    sport_tag = pick_font("sans_bold", 20)
    sport_body = pick_font("serif", 17)

    y = 12
    canvas.text((PAGE_W // 2, y), "THE WORLD TODAY", font=masthead,
                anchor="ma", fill=INK)
    y = 102
    canvas.text((PAGE_W // 2, y), "TUESDAY, 24 NOVEMBER 2026",
                font=dateline, anchor="ma", fill=INK)

    rule(canvas, 136, weight=3)
    rule(canvas, 142, weight=1)

    # Hero picture and its caption. The picture is 280 tall so the page
    # fills the frame instead of leaving dead space at the foot.
    paint_strait(canvas, (EDGE, 150, PAGE_W - EDGE, 430))
    canvas.text((PAGE_W // 2, 438), PHOTO_CAPTION, font=caption_font,
                anchor="ma", fill=FAINT)

    # Lead story: big headline, then the deck paragraph.
    y = 466
    y = paint_lines(canvas, wrap_text(canvas, LEAD_HEADLINE, lead_font, INNER_W),
                    lead_font, EDGE, y, 54)
    y += 8
    y = paint_lines(canvas, wrap_text(canvas, LEAD_DECK, deck_font, INNER_W),
                    deck_font, EDGE, y, 26)
    y += 12
    rule(canvas, y)

    # Two-column grid of six short stories, three rows.
    col_w = (INNER_W - 28) // 2
    col_x = [EDGE, EDGE + col_w + 28]
    grid_top = y + 16
    for row in range(3):
        row_y = grid_top + row * 100
        for col in range(2):
            headline, body = GRID_STORIES[row * 2 + col]
            story_cell(canvas, col_x[col], row_y, col_w,
                       headline, body, cell_head, cell_body)

    # Sport strip along the bottom.
    sport_y = grid_top + 3 * 100 + 8
    rule(canvas, sport_y)
    sport_y += 10
    canvas.text((EDGE, sport_y), "SPORT", font=sport_tag, fill=INK)
    paint_lines(
        canvas,
        wrap_text(canvas, SPORT_TEXT, sport_body, INNER_W - 96),
        sport_body, EDGE + 96, sport_y, 23,
    )

    return page


def main():
    """Render the page and save it next to this script."""
    page = build_front_page()
    here = Path(__file__).resolve().parent
    target = here / "entry.png"
    page.save(target, format="PNG")
    print(f"wrote {target}")

    extra_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if extra_dir:
        dest = Path(extra_dir) / "entry.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, dest)
        print(f"also copied to {dest}")


if __name__ == "__main__":
    main()
