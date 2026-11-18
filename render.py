#!/usr/bin/env python3
"""Draw the fixed 17 November 2026 front page, offline and deterministically.

All artwork is made from Pillow primitives. Render at 2048 square, then
downsample to 1024 square. The grader uses the finished PNG, not this script.
"""

from functools import lru_cache
from hashlib import sha256
from math import cos, pi, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SCALE = 2
SIZE = 1024
PAPER = "#F7F4ED"
INK = "#202B31"
MUTED = "#61686A"
RULE = "#C9C8BF"
RUST = "#A74B3C"
BLUE = "#315A72"
OLIVE = "#637448"
RUST_PALE = "#F0E2DB"
BLUE_PALE = "#E7EDF0"
OLIVE_PALE = "#E8ECDD"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

canvas = Image.new("RGB", (SIZE * SCALE, SIZE * SCALE), PAPER)
draw = ImageDraw.Draw(canvas)
text_records = []


def box(coords):
    return tuple(round(v * SCALE) for v in coords)


def rect(coords, fill, outline=None, width=1):
    draw.rectangle(box(coords), fill=fill, outline=outline, width=round(width * SCALE))


def rounded(coords, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(
        box(coords), radius=round(radius * SCALE), fill=fill,
        outline=outline, width=round(width * SCALE),
    )


def line(points, fill=INK, width=1):
    draw.line(
        [(round(x * SCALE), round(y * SCALE)) for x, y in points],
        fill=fill, width=max(1, round(width * SCALE)), joint="curve",
    )


def polygon(points, fill, outline=None, width=1):
    points = [(round(x * SCALE), round(y * SCALE)) for x, y in points]
    draw.polygon(points, fill=fill)
    if outline:
        draw.line(points + [points[0]], fill=outline, width=round(width * SCALE), joint="curve")


def ellipse(coords, fill=None, outline=None, width=1):
    draw.ellipse(box(coords), fill=fill, outline=outline, width=round(width * SCALE))


def arc(coords, start, end, fill, width=1):
    draw.arc(box(coords), start, end, fill=fill, width=round(width * SCALE))


@lru_cache(maxsize=None)
def font(size, style="regular"):
    names = {
        "regular": "DejaVuSans.ttf",
        "bold": "DejaVuSans-Bold.ttf",
        "serif": "DejaVuSerif-Bold.ttf",
    }
    return ImageFont.truetype(str(FONT_DIR / names[style]), round(size * SCALE))


def text(x, y, value, size, fill=INK, style="regular", align="left", max_width=None):
    assert "\n" not in value, "Use separate, positioned lines."
    face = font(size, style)
    width = draw.textlength(value, font=face) / SCALE
    if max_width is not None:
        assert width <= max_width, f"Text overflow: {value!r} ({width:.1f} > {max_width})"
    if align == "center":
        x -= width / 2
    elif align == "right":
        x -= width
    coords = (round(x * SCALE), round(y * SCALE))
    bounds = draw.textbbox(coords, value, font=face, anchor="lt")
    assert 0 <= bounds[0] and bounds[2] <= SIZE * SCALE, value
    assert 0 <= bounds[1] and bounds[3] <= SIZE * SCALE, value
    draw.text(coords, value, font=face, fill=fill, anchor="lt")
    text_records.append((value, tuple(v / SCALE for v in bounds)))


def burst(x, y, radius, color, points=10):
    polygon([
        (
            x + cos(-pi / 2 + i * pi / points) * (radius if i % 2 == 0 else radius * 0.48),
            y + sin(-pi / 2 + i * pi / points) * (radius if i % 2 == 0 else radius * 0.48),
        )
        for i in range(points * 2)
    ], color)


def arrow(points, color, width=2, head=6):
    line(points, color, width)
    x, y = points[-1]
    px, py = points[-2]
    dx, dy = x - px, y - py
    norm = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / norm, dy / norm
    polygon([
        (x, y),
        (x - ux * head - uy * head / 2, y - uy * head + ux * head / 2),
        (x - ux * head + uy * head / 2, y - uy * head - ux * head / 2),
    ], color)


def us_flag(x, y, w=52, h=31):
    rect((x, y, x + w, y + h), PAPER)
    for i in range(0, 13, 2):
        rect((x, y + i * h / 13, x + w, y + (i + 1) * h / 13), RUST)
    rect((x, y, x + w * 0.42, y + h * 7 / 13), BLUE)
    for row in range(5):
        for col in range(5):
            cx = x + 2.5 + col * 4
            cy = y + 2 + row * 3.1
            ellipse((cx, cy, cx + 0.9, cy + 0.9), PAPER)
    rect((x, y, x + w, y + h), None, INK, 0.7)


def philippines_flag(x, y, w=52, h=31):
    rect((x, y, x + w, y + h / 2), BLUE)
    rect((x, y + h / 2, x + w, y + h), RUST)
    polygon([(x, y), (x + w * 0.43, y + h / 2), (x, y + h)], PAPER)
    ellipse((x + 6, y + 12, x + 12, y + 18), "#B69751")
    for cx, cy in [(x + 3, y + 4), (x + 3, y + h - 4), (x + 18, y + h / 2)]:
        burst(cx, cy, 1.5, "#B69751", 5)
    rect((x, y, x + w, y + h), None, INK, 0.7)


def kerch_art(x, y):
    """Broken road span, falling into the strait between labeled endpoints."""
    rect((x, y, x + 468, y + 184), RUST_PALE)
    text(x + 14, y + 12, "KERCH STRAIT · OVERNIGHT", 11.5, RUST, "bold")
    text(x + 20, y + 42, "RUSSIA", 13, INK, "bold")
    text(x + 448, y + 42, "OCCUPIED CRIMEA", 13, INK, "bold", "right")
    rect((x, y + 139, x + 468, y + 184), "#E3CFC3")
    for row, offset in [(149, 0)]:
        for start in range(10 + offset, 445, 59):
            line([(x + start, y + row), (x + start + 35, y + row)], RUST, 0.7)
    # Road deck, parapets and piers. The middle section is missing.
    for left, right in [(18, 187), (286, 450)]:
        rect((x + left, y + 103, x + right, y + 115), INK)
        line([(x + left, y + 98), (x + right, y + 98)], INK, 2)
        for rail in range(left + 4, right, 17):
            line([(x + rail, y + 98), (x + rail, y + 104)], INK, 1)
        for stripe in range(left + 8, right - 9, 27):
            line([(x + stripe, y + 109), (x + stripe + 13, y + 109)], PAPER, 1)
    for pier in [44, 142, 316, 417]:
        rect((x + pier, y + 115, x + pier + 9, y + 151), INK)
        rect((x + pier - 4, y + 147, x + pier + 13, y + 153), INK)
    arc((x + 41, y + 65, x + 158, y + 141), 180, 360, INK, 3)
    arc((x + 308, y + 65, x + 428, y + 141), 180, 360, INK, 3)
    for support in [58, 77, 98, 120, 142, 325, 344, 366, 388, 410]:
        relative = support - (99 if support < 200 else 368)
        arch_y = 67 + (relative / 58) ** 2 * 23
        line([(x + support, y + arch_y), (x + support, y + 103)], INK, 1)
    # A tilted section and small pieces fall into the water.
    polygon([(x + 205, y + 114), (x + 259, y + 142), (x + 254, y + 154), (x + 200, y + 125)], RUST)
    line([(x + 207, y + 120), (x + 249, y + 142)], PAPER, 1.6)
    polygon([(x + 278, y + 119), (x + 284, y + 122), (x + 282, y + 128)], INK)
    polygon([(x + 194, y + 132), (x + 199, y + 135), (x + 193, y + 140)], INK)
    burst(x + 238, y + 85, 22, RUST, 8)
    ellipse((x + 231, y + 78, x + 245, y + 92), RUST_PALE)
    line([(x + 215, y + 151), (x + 211, y + 143)], RUST, 2)
    line([(x + 260, y + 158), (x + 269, y + 151)], RUST, 2)
    rect((x, y + 160, x + 468, y + 184), RUST_PALE)
    line([(x + 20, y + 158), (x + 448, y + 158)], RUST, 0.8)
    text(x + 20, y + 168, "ZELENSKY: UNPRECEDENTED OPERATION", 11.5, RUST, "bold", max_width=428)


def manila_art(x, y):
    """US/Philippines flags, an arriving plane, and a compact summit route."""
    rect((x, y, x + 468, y + 184), BLUE_PALE)
    text(x + 14, y + 12, "DIPLOMACY · PHILIPPINES", 11.5, BLUE, "bold")
    us_flag(x + 20, y + 45)
    philippines_flag(x + 82, y + 45)
    text(x + 20, y + 86, "US", 10.5, BLUE, "bold")
    text(x + 82, y + 86, "PHILIPPINES", 10.5, BLUE, "bold")
    # Airliner in profile; no external assets or font icons.
    polygon([
        (x + 166, y + 57), (x + 354, y + 57), (x + 383, y + 66),
        (x + 399, y + 77), (x + 389, y + 85), (x + 187, y + 85),
        (x + 165, y + 76), (x + 154, y + 39), (x + 168, y + 39),
        (x + 189, y + 57),
    ], PAPER, BLUE, 1.8)
    polygon([(x + 242, y + 69), (x + 293, y + 37), (x + 309, y + 37), (x + 280, y + 72)], BLUE)
    polygon([(x + 253, y + 73), (x + 304, y + 101), (x + 325, y + 101), (x + 287, y + 74)], BLUE)
    for wx in range(197, 366, 13):
        rounded((x + wx, y + 62, x + wx + 5, y + 67), 1, BLUE)
    line([(x + 375, y + 65), (x + 385, y + 70)], BLUE, 2)
    line([(x + 187, y + 79), (x + 378, y + 79)], BLUE, 1)
    arrow([(x + 380, y + 96), (x + 413, y + 112), (x + 413, y + 136)], BLUE, 1.5, 5)
    text(x + 20, y + 113, "MANILA", 29, BLUE, "bold")
    text(x + 185, y + 111, "ASEAN SUMMIT + QUAD", 15, INK, "bold")
    text(x + 185, y + 136, "India · Japan · Australia", 12.5, INK)
    line([(x + 20, y + 158), (x + 448, y + 158)], BLUE, 0.8)
    text(x + 20, y + 168, "NEXT: XI JINPING + VLADIMIR PUTIN · SHENZHEN · THURSDAY", 11, BLUE, "bold", max_width=428)


def kyiv_icon(x, y):
    rounded((x, y, x + 120, y + 104), 3, RUST_PALE)
    rect((x, y + 80, x + 120, y + 104), "#E3CFC3")
    # Two bridge decks, with a ballistic missile and a burst overhead.
    for bridge_y in [61, 76]:
        rect((x + 12, y + bridge_y, x + 106, y + bridge_y + 4), INK)
        for pier in [23, 49, 78, 99]:
            line([(x + pier, y + bridge_y + 4), (x + pier, y + 91)], INK, 2)
        arc((x + 22, y + bridge_y - 15, x + 79, y + bridge_y + 15), 180, 360, INK, 1.5)
    polygon([(x + 75, y + 15), (x + 88, y + 26), (x + 60, y + 53), (x + 58, y + 40)], RUST)
    polygon([(x + 58, y + 38), (x + 49, y + 35), (x + 57, y + 49)], RUST)
    polygon([(x + 68, y + 48), (x + 70, y + 60), (x + 58, y + 51)], RUST)
    line([(x + 90, y + 12), (x + 98, y + 4)], RUST, 1.5)
    line([(x + 99, y + 23), (x + 108, y + 14)], RUST, 1.5)
    burst(x + 49, y + 58, 17, RUST, 8)
    ellipse((x + 44, y + 53, x + 54, y + 63), RUST_PALE)
    for wave in [13, 49, 84]:
        line([(x + wave, y + 97), (x + wave + 22, y + 97)], RUST, 0.7)


def bahrain_icon(x, y):
    rounded((x, y, x + 120, y + 104), 3, BLUE_PALE)
    # Quadcopter above a protected radar dish.
    line([(x + 19, y + 22), (x + 54, y + 44)], INK, 2)
    line([(x + 19, y + 44), (x + 54, y + 22)], INK, 2)
    rounded((x + 29, y + 27, x + 44, y + 39), 3, INK)
    for cx, cy in [(18, 22), (54, 22), (18, 44), (54, 44)]:
        ellipse((x + cx - 7, y + cy - 3, x + cx + 7, y + cy + 3), PAPER, INK, 1.2)
    for start in [60, 72]:
        line([(x + start, y + 36), (x + start + 5, y + 39)], BLUE, 1.3)
    # A shield denotes interception, without claiming an interception weapon.
    polygon([(x + 91, y + 25), (x + 106, y + 31), (x + 104, y + 49), (x + 91, y + 61), (x + 78, y + 49), (x + 76, y + 31)], PAPER, BLUE, 2)
    line([(x + 84, y + 42), (x + 89, y + 47), (x + 99, y + 35)], BLUE, 2.3)
    line([(x + 64, y + 72), (x + 64, y + 96)], INK, 3)
    line([(x + 45, y + 96), (x + 81, y + 96)], INK, 3)
    polygon([(x + 44, y + 65), (x + 73, y + 79), (x + 86, y + 59)], BLUE)
    arc((x + 44, y + 43, x + 87, y + 79), 15, 145, PAPER, 2)
    line([(x + 68, y + 62), (x + 77, y + 48)], BLUE, 1.5)
    ellipse((x + 74, y + 45, x + 79, y + 50), BLUE)
    line([(x + 12, y + 100), (x + 108, y + 100)], BLUE, 0.8)


def nvidia_icon(x, y):
    rounded((x, y, x + 120, y + 104), 3, OLIVE_PALE)
    for pin in range(28, 95, 11):
        line([(x + pin, y + 13), (x + pin, y + 23)], OLIVE, 3)
        line([(x + pin, y + 82), (x + pin, y + 93)], OLIVE, 3)
    for pin in range(30, 79, 12):
        line([(x + 10, y + pin), (x + 20, y + pin)], OLIVE, 3)
        line([(x + 100, y + pin), (x + 110, y + pin)], OLIVE, 3)
    rounded((x + 20, y + 23, x + 100, y + 82), 4, INK)
    rounded((x + 25, y + 28, x + 95, y + 77), 2, OLIVE)
    text(x + 60, y + 34, "NVIDIA", 11.5, PAPER, "bold", "center")
    text(x + 60, y + 51, "CEO", 23, PAPER, "bold", "center")
    arrow([(x + 89, y + 86), (x + 112, y + 86)], INK, 2.5, 7)


def rwanda_icon(x, y):
    rounded((x, y, x + 120, y + 104), 3, OLIVE_PALE)
    # Simplified Africa silhouette with a pin at Rwanda's approximate location.
    polygon([
        (x + 39, y + 12), (x + 56, y + 9), (x + 68, y + 13),
        (x + 76, y + 27), (x + 91, y + 36), (x + 104, y + 35),
        (x + 96, y + 49), (x + 83, y + 56), (x + 81, y + 72),
        (x + 73, y + 87), (x + 64, y + 94), (x + 54, y + 81),
        (x + 49, y + 65), (x + 39, y + 55), (x + 27, y + 50),
        (x + 21, y + 39), (x + 24, y + 26),
    ], OLIVE, PAPER, 1)
    ellipse((x + 95, y + 70, x + 100, y + 87), OLIVE)
    ellipse((x + 63, y + 49, x + 79, y + 65), PAPER, INK, 1)
    polygon([(x + 64, y + 60), (x + 78, y + 60), (x + 71, y + 73)], PAPER, INK, 1)
    ellipse((x + 68, y + 54, x + 74, y + 60), OLIVE)
    arrow([(x + 12, y + 15), (x + 12, y + 65), (x + 56, y + 65)], INK, 1.4, 5)
    text(x + 10, y + 82, "RWANDA", 10, INK, "bold")


def lead_story(x, art, title_lines, summary, accent):
    rect((x, 210, x + 468, 214), accent)
    art(x, 220)
    for i, value in enumerate(title_lines):
        text(x + 12, 419 + 39 * i, value, 33, INK, "bold", max_width=444)
    text(x + 12, 509, summary, 17, max_width=444)
    line([(x, 550), (x + 468, 550)], RULE, 1)


def small_story(x, y, icon, accent, title_lines, summary, labels, title_size=25):
    rect((x, y, x + 468, y + 3), accent)
    icon(x + 12, y + 18)
    for i, value in enumerate(title_lines):
        text(x + 148, y + 20 + 31 * i, value, title_size, INK, "bold", max_width=308)
    for i, value in enumerate(labels):
        text(x + 148, y + 89 + 15 * i, value, 11.5, accent, "bold", max_width=308)
    text(x + 12, y + 138, summary, 16, max_width=444)
    line([(x, y + 160), (x + 468, y + 160)], RULE, 1)


def render():
    # Typography is literal, placed as separate checked lines; no text engines.
    text(512, 24, "WORLD NEWS", 114, INK, "serif", "center", max_width=960)
    rect((32, 126, 992, 191), INK)
    text(512, 139, "TUESDAY 17 NOVEMBER 2026", 55, PAPER, "bold", "center", max_width=934)
    line([(32, 200), (992, 200)], INK, 1)

    lead_story(
        32, kerch_art, ["KERCH BRIDGE", "SPAN COLLAPSES"],
        "Ukraine strikes; traffic halted; 2 killed in Crimea.", RUST,
    )
    lead_story(
        524, manila_art, ["TRUMP ARRIVES", "IN MANILA"],
        "ASEAN + Quad talks; about 1,500 protesters rally.", BLUE,
    )
    small_story(
        32, 572, kyiv_icon, RUST, ["KYIV BRIDGES", "HIT BY MISSILES"],
        "Russian missiles cut heat to hundreds of buildings.",
        ["SOUTH + NORTH BRIDGES · DNIPRO", "BALLISTIC MISSILE STRIKES"],
    )
    small_story(
        524, 572, bahrain_icon, BLUE, ["BAHRAIN DRONES", "INTERCEPTED"],
        "Iran targets US radar; no casualties or damage.",
        ["SHEIKH ISA AIR BASE", "IRAN'S REVOLUTIONARY GUARD"],
    )
    small_story(
        32, 750, nvidia_icon, OLIVE, ["NVIDIA CEO", "JENSEN HUANG QUITS"],
        "Reported affair with alleged Chinese-recruited spy.",
        ["BOARD RULES OUT REINSTATEMENT", "US INTELLIGENCE ALLEGES SPY LINK"],
        title_size=24,
    )
    small_story(
        524, 750, rwanda_icon, OLIVE, ["EU PLANS RWANDA", "MIGRANT HUB"],
        "5 countries plan 2027 pilot for about 100 people.",
        ["REJECTED ASYLUM SEEKERS", "Austria · Denmark · Germany", "Greece · Netherlands"],
    )

    # Small three-column quick-news strip, then the dated closing line.
    rect((32, 928, 992, 930), INK)
    footer = [
        (32, "BRITAIN · SANCTIONS", "8 Israeli construction firms", "Over West Bank settlements"),
        (361, "MONGOLIA · PRESIDENT RESIGNS", "Ukhnaagiin Khurelsukh", "Amid a corruption scandal"),
        (690, "CULTURE · NEXT JAMES BOND", "Robert Pattinson", "Directed by Denis Villeneuve"),
    ]
    for x, title, first, second in footer:
        text(x, 940, title, 11.2, INK, "bold", max_width=302)
        text(x, 958, first, 12.5, INK, max_width=302)
        text(x, 975, second, 12.5, MUTED, max_width=302)
    for x in [345, 674]:
        line([(x, 940), (x, 986)], RULE, 1)
    text(512, 1001, "17 November 2026 — the day in one image", 13, MUTED, align="center")

    # Guard every text line against collisions with other text lines.
    for i, (first, a) in enumerate(text_records):
        for second, b in text_records[i + 1:]:
            overlaps = a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]
            assert not overlaps, f"Overlapping text: {first!r} / {second!r}"

    output = canvas.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    path = ROOT / "entry.png"
    output.save(path, format="PNG", optimize=True, compress_level=9)
    with Image.open(path) as check:
        assert check.format == "PNG" and check.size == (1024, 1024)
        check.verify()
    data = path.read_bytes()
    assert len(data) <= 1048576, f"PNG exceeds 1 MiB: {len(data)}"
    print(f"entry.png: {len(data)} bytes; 1024x1024; valid PNG")
    print(f"sha256: {sha256(data).hexdigest()}")


if __name__ == "__main__":
    render()
