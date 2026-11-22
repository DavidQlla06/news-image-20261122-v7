#!/usr/bin/env python3
"""Render the 22 November 2026 front page (news-image-20261122 v7).

Map-led broadsheet: masthead, world map with 13 numbered markers beside
a lead-story column, 12 illustrated story cards with numbered badges,
a two-column briefs panel and a ticker bar. Fully deterministic.
"""
import json
import math
import os
import random
import textwrap

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W = H = 1024

PAPER = (247, 243, 233)
INK = (22, 20, 18)
FAINT = (105, 100, 92)
RULE = (60, 56, 50)
RED = (178, 34, 34)
OCEAN_TOP = (168, 205, 228)
OCEAN_BOT = (120, 172, 210)
LAND = (232, 214, 170)
LAND_EDGE = (150, 128, 84)

REGION_COLORS = {
    "EUROPE": (43, 108, 176),
    "AMERICAS": (156, 66, 161),
    "ASIA-PACIFIC": (38, 140, 110),
    "AFRICA": (196, 120, 30),
    "MIDDLE EAST & GULF": (190, 45, 45),
    "CLIMATE & PLANET": (46, 150, 80),
    "BUSINESS · TECH · SPORT": (90, 90, 170),
}

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_R = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def vgradient(img, box, top, bot):
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0)
    d = ImageDraw.Draw(img)
    for i in range(h):
        t = i / h
        c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)


def speckle(img, box, n, seed, alpha=26):
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for _ in range(n):
        x = rng.randint(x0, x1)
        y = rng.randint(y0, y1)
        v = rng.choice([(0, 0, 0), (255, 255, 255)])
        d.point((x, y), fill=v + (alpha,))
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"), (0, 0))


# Simplified continent outlines as (lon, lat) polygons, drawn by hand.
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-80, 62), (-78, 58), (-76, 50), (-70, 46), (-66, 44), (-70, 42),
     (-74, 39), (-76, 35), (-80, 31), (-81, 25), (-84, 30), (-89, 30),
     (-94, 29), (-97, 26), (-97, 22), (-94, 18), (-90, 15), (-86, 13),
     (-83, 9), (-79, 9), (-81, 13), (-84, 16), (-88, 18), (-91, 19),
     (-97, 16), (-102, 18), (-105, 20), (-108, 23), (-110, 24),
     (-114, 29), (-117, 33), (-122, 37), (-124, 42), (-124, 47),
     (-128, 51), (-133, 56), (-140, 60), (-152, 60), (-158, 56),
     (-162, 58), (-166, 61)],
    # South America
    [(-79, 9), (-75, 11), (-72, 12), (-64, 10), (-60, 8), (-52, 5),
     (-50, 0), (-44, -3), (-35, -8), (-39, -13), (-40, -21), (-48, -26),
     (-52, -33), (-58, -39), (-62, -41), (-65, -45), (-67, -50),
     (-68, -54), (-71, -54), (-74, -50), (-74, -44), (-73, -37),
     (-71, -30), (-70, -20), (-70, -18), (-75, -15), (-77, -12),
     (-79, -8), (-81, -4), (-80, 1), (-78, 4), (-77, 7)],
    # Africa
    [(-6, 35), (0, 36), (10, 37), (11, 34), (20, 32), (30, 31), (32, 31),
     (35, 28), (38, 22), (40, 15), (43, 12), (48, 11), (51, 12),
     (50, 15), (48, 11), (44, 11), (42, 15), (40, 20), (38, 24),
     (35, 28), (33, 27), (32, 31), (30, 31), (22, 33), (15, 32),
     (10, 34), (10, 37), (5, 37), (0, 36), (-2, 35), (-6, 35),
     (-10, 31), (-15, 25), (-17, 20), (-17, 15), (-15, 11), (-13, 8),
     (-8, 5), (-4, 5), (2, 6), (6, 4), (9, 4), (13, -1), (12, -6),
     (13, -12), (14, -18), (16, -28), (18, -33), (20, -35), (26, -34),
     (31, -29), (32, -26), (35, -24), (36, -20), (38, -15), (40, -11),
     (40, -5), (41, -2), (46, 5), (51, 11), (48, 11), (43, 12),
     (40, 15), (38, 20), (36, 24), (34, 27), (32, 31)],
    # Eurasia (Europe + Asia as one landmass)
    [(-9, 43), (-2, 44), (-1, 46), (-5, 48), (0, 49), (2, 51), (5, 53),
     (8, 55), (8, 57), (10, 59), (5, 60), (5, 62), (10, 64), (14, 67),
     (18, 69), (25, 71), (31, 70), (40, 68), (50, 69), (60, 69),
     (70, 72), (80, 73), (90, 75), (100, 77), (110, 74), (120, 73),
     (130, 72), (140, 72), (150, 70), (160, 69), (170, 66), (178, 65),
     (170, 60), (162, 58), (158, 52), (156, 50), (150, 59), (143, 54),
     (142, 50), (140, 46), (135, 45), (132, 43), (129, 40), (127, 40),
     (126, 38), (122, 38), (120, 34), (121, 31), (119, 26), (114, 22),
     (110, 20), (108, 17), (109, 13), (106, 9), (104, 8), (103, 2),
     (100, 6), (98, 10), (97, 15), (94, 17), (92, 16), (89, 22),
     (86, 20), (80, 15), (77, 8), (76, 10), (72, 19), (70, 22),
     (66, 25), (61, 25), (57, 26), (56, 27), (52, 25), (50, 29),
     (48, 30), (50, 26), (54, 24), (56, 24), (58, 23), (59, 22),
     (55, 17), (52, 15), (45, 12), (43, 12), (42, 15), (39, 21),
     (36, 28), (34, 28), (36, 36), (30, 36), (27, 37), (23, 36),
     (19, 40), (15, 38), (16, 40), (14, 42), (12, 44), (8, 44),
     (6, 43), (3, 42), (0, 39), (-2, 37), (-2, 37), (-6, 36),
     (-9, 37), (-9, 39), (-9, 43)],
    # SE Asia islands (Borneo-ish blob)
    [(109, 1), (113, 4), (117, 6), (119, 2), (118, -2), (114, -3),
     (110, -2), (109, 0)],
    # Indonesia / New Guinea
    [(95, 5), (100, 0), (105, -6), (110, -7), (115, -8), (120, -9),
     (125, -9), (131, -4), (136, -2), (141, -3), (146, -6), (150, -9),
     (147, -9), (142, -8), (137, -7), (132, -4), (128, -3), (123, -10),
     (118, -9), (112, -7), (106, -6), (100, -1), (96, 3)],
    # Australia
    [(113, -22), (114, -28), (115, -34), (118, -35), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -30), (153, -26), (151, -24),
     (149, -20), (146, -19), (145, -15), (142, -11), (142, -14),
     (141, -17), (139, -17), (136, -15), (135, -12), (132, -11),
     (130, -12), (126, -14), (122, -17), (118, -20), (114, -22)],
    # Greenland
    [(-45, 60), (-42, 65), (-40, 70), (-32, 68), (-22, 70), (-20, 76),
     (-25, 80), (-35, 82), (-50, 80), (-55, 76), (-53, 70), (-52, 64),
     (-48, 60)],
    # Britain
    [(-5, 50), (-3, 53), (-5, 55), (-3, 57), (-5, 58), (-7, 58),
     (-8, 55), (-6, 52), (-5, 50)],
    # Japan
    [(130, 31), (133, 34), (137, 35), (140, 36), (141, 40), (141, 43),
     (140, 42), (139, 38), (136, 35), (133, 34), (131, 32)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24), (45, -25),
     (44, -22), (43, -18)],
    # New Zealand
    [(167, -46), (170, -44), (172, -41), (174, -39), (176, -38),
     (178, -37), (176, -37), (174, -39), (173, -42), (170, -44),
     (168, -46)],
]


def lonlat_to_xy(lon, lat, box):
    x0, y0, x1, y1 = box
    x = x0 + (lon + 180) / 360.0 * (x1 - x0)
    y = y0 + (75 - lat) / 135.0 * (y1 - y0)
    return x, y


def draw_map(img, box, markers):
    """markers: list of (number, lon, lat, color)."""
    x0, y0, x1, y1 = box
    vgradient(img, box, OCEAN_TOP, OCEAN_BOT)
    d = ImageDraw.Draw(img)
    # graticule
    for lon in range(-150, 181, 30):
        gx, _ = lonlat_to_xy(lon, 0, box)
        d.line([(gx, y0), (gx, y1)], fill=(140, 180, 205), width=1)
    for lat in range(-60, 76, 30):
        _, gy = lonlat_to_xy(0, lat, box)
        d.line([(x0, gy), (x1, gy)], fill=(140, 180, 205), width=1)
    for poly in CONTINENTS:
        pts = [lonlat_to_xy(lon, lat, box) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_EDGE)
    # equator + tropics labels
    d.text((x0 + 4, y1 - 13), "PACIFIC", font=font(SANS, 9), fill=(70, 110, 140))
    d.text((x1 - 52, y1 - 13), "ATLANTIC", font=font(SANS, 9), fill=(70, 110, 140))
    for num, lon, lat, color in markers:
        cx, cy = lonlat_to_xy(lon, lat, box)
        r = 9
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color,
                  outline=(255, 255, 255), width=2)
        t = str(num)
        tw = d.textlength(t, font=font(SANS_B, 11))
        d.text((cx - tw / 2, cy - 6), t, font=font(SANS_B, 11), fill=(255, 255, 255))
    d.rectangle(box, outline=RULE, width=2)


def scene_sky(img, box, top, bot):
    vgradient(img, box, top, bot)


def draw_scene(img, box, kind):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d = ImageDraw.Draw(img)
    if kind == "summit":
        scene_sky(img, box, (96, 150, 200), (190, 215, 235))
        d = ImageDraw.Draw(img)
        # conference table + flags + gavel
        d.rectangle([x0 + 14, y1 - 20, x1 - 14, y1 - 10], fill=(120, 84, 50))
        for i, c in enumerate([(200, 40, 40), (40, 90, 200), (40, 160, 80), (230, 180, 40)]):
            fx = x0 + 26 + i * 52
            d.line([(fx, y1 - 20), (fx, y0 + 12)], fill=(60, 60, 60), width=2)
            d.polygon([(fx, y0 + 12), (fx + 26, y0 + 18), (fx, y0 + 24)], fill=c)
        d.line([(x0 + w - 46, y0 + 16), (x0 + w - 24, y0 + 38)], fill=(90, 60, 30), width=5)
        d.rectangle([x0 + w - 52, y0 + 8, x0 + w - 36, y0 + 22], fill=(90, 60, 30))
        d.line([(x0 + 10, y1 - 8), (x1 - 10, y1 - 8)], fill=RED, width=3)
    elif kind == "f1car":
        scene_sky(img, box, (30, 30, 60), (90, 70, 120))
        d = ImageDraw.Draw(img)
        d.rectangle([x0, y1 - 14, x1, y1], fill=(40, 40, 44))
        for i in range(8):
            d.rectangle([x0 + 8 + i * 30, y1 - 9, x0 + 20 + i * 30, y1 - 5], fill=(240, 240, 240))
        # car body
        cy = y1 - 22
        d.polygon([(x0 + 30, cy), (x0 + 70, cy - 8), (x0 + 120, cy - 9),
                   (x0 + 150, cy - 4), (x0 + 205, cy), (x0 + 205, cy + 6),
                   (x0 + 30, cy + 6)], fill=(210, 30, 40))
        d.rectangle([x0 + 96, cy - 15, x0 + 112, cy - 8], fill=(210, 30, 40))
        d.rectangle([x0 + 22, cy - 6, x0 + 40, cy + 2], fill=(30, 30, 30))
        for wx in (x0 + 58, x0 + 168):
            d.ellipse([wx - 10, cy - 3, wx + 10, cy + 13], fill=(15, 15, 15))
            d.ellipse([wx - 4, cy + 2, wx + 4, cy + 9], fill=(200, 200, 200))
        d.text((x0 + 8, y0 + 6), "LAS VEGAS", font=font(SANS_B, 12), fill=(255, 220, 90))
    elif kind == "missiles":
        scene_sky(img, box, (70, 80, 110), (150, 140, 130))
        d = ImageDraw.Draw(img)
        # skyline
        rng = random.Random(7)
        bx = x0 + 6
        while bx < x1 - 20:
            bw = rng.randint(16, 30)
            bh = rng.randint(18, 34)
            d.rectangle([bx, y1 - bh, bx + bw, y1], fill=(52, 52, 60))
            bx += bw + 4
        # missile trails + bursts
        for (mx, my) in [(x0 + 60, y0 + 16), (x0 + 120, y0 + 10), (x0 + 175, y0 + 20)]:
            d.line([(mx - 26, my - 8), (mx, my)], fill=(255, 180, 60), width=3)
            d.polygon([(mx, my), (mx - 8, my - 3), (mx - 8, my + 3)], fill=(255, 220, 120))
            for a in range(0, 360, 45):
                ex = mx + 11 * math.cos(math.radians(a))
                ey = my + 11 * math.sin(math.radians(a))
                d.line([(mx, my), (ex, ey)], fill=(255, 120, 40), width=2)
        d.ellipse([x0 + 100, y1 - 26, x0 + 140, y1 - 6], fill=(240, 110, 30))
    elif kind == "building":
        scene_sky(img, box, (120, 150, 185), (200, 210, 220))
        d = ImageDraw.Draw(img)
        # apartment block, part collapsed
        d.rectangle([x0 + 40, y0 + 4, x0 + 140, y1 - 3], fill=(205, 190, 165), outline=(120, 105, 80))
        for r in range(2):
            for c in range(4):
                wx = x0 + 48 + c * 23
                wy = y0 + 8 + r * 14
                d.rectangle([wx, wy, wx + 13, wy + 9], fill=(70, 85, 105))
        d.polygon([(x0 + 140, y0 + 4), (x0 + 205, y1 - 3), (x0 + 140, y1 - 3)], fill=(170, 155, 130))
        for i in range(6):
            rx = x0 + 150 + i * 10
            d.polygon([(rx, y1 - 3), (rx + 8, y1 - 3), (rx + 4, y1 - 12 - (i % 3) * 3)], fill=(130, 115, 90))
        d.ellipse([x0 + 150, y0 + 3, x0 + 186, y0 + 15], fill=(90, 90, 95))
    elif kind == "shipfire":
        scene_sky(img, box, (80, 120, 165), (170, 195, 215))
        d = ImageDraw.Draw(img)
        d.rectangle([x0, y1 - 16, x1, y1], fill=(50, 95, 140))
        # hull
        d.polygon([(x0 + 24, y1 - 26), (x1 - 30, y1 - 26), (x1 - 46, y1 - 14),
                   (x0 + 40, y1 - 14)], fill=(45, 45, 52))
        d.rectangle([x0 + 60, y1 - 34, x0 + 96, y1 - 26], fill=(70, 70, 80))
        d.rectangle([x0 + 150, y1 - 32, x0 + 176, y1 - 26], fill=(70, 70, 80))
        # flames + smoke
        for fx in (x0 + 84, x0 + 112, x0 + 160):
            d.polygon([(fx - 9, y1 - 26), (fx, y1 - 38), (fx + 9, y1 - 26)], fill=(240, 110, 25))
            d.polygon([(fx - 4, y1 - 26), (fx, y1 - 33), (fx + 4, y1 - 26)], fill=(255, 190, 60))
        for (sx, sy, sr) in [(x0 + 90, y0 + 8, 11), (x0 + 118, y0 + 5, 13), (x0 + 150, y0 + 7, 10)]:
            d.ellipse([sx - sr, sy - sr // 2, sx + sr, sy + sr // 2], fill=(60, 60, 66))
    elif kind == "crash":
        scene_sky(img, box, (35, 35, 45), (70, 70, 85))
        d = ImageDraw.Draw(img)
        d.text((x0 + 8, y0 + 3), "-5.3%", font=font(SANS_B, 18), fill=(255, 80, 80))
        pts = [(x0 + 10, y0 + 28), (x0 + 55, y0 + 22), (x0 + 95, y0 + 32),
               (x0 + 135, y0 + 26), (x0 + 175, y0 + 36), (x0 + 215, y0 + 40)]
        d.line(pts, fill=(255, 70, 70), width=4)
        d.polygon([(x0 + 215, y0 + 40), (x0 + 200, y0 + 37), (x0 + 208, y0 + 30)], fill=(255, 70, 70))
        for gx in range(x0 + 10, x1 - 6, 24):
            d.line([(gx, y0 + 20), (gx, y1 - 4)], fill=(90, 90, 105), width=1)
    elif kind == "bars":
        scene_sky(img, box, (60, 60, 70), (110, 105, 100))
        d = ImageDraw.Draw(img)
        for i in range(7):
            bx = x0 + 18 + i * 30
            d.rectangle([bx, y0 + 6, bx + 7, y1 - 6], fill=(25, 25, 28))
        d.rectangle([x0 + 10, y0 + 10, x1 - 10, y0 + 16], fill=(25, 25, 28))
        d.rectangle([x0 + 10, y1 - 16, x1 - 10, y1 - 10], fill=(25, 25, 28))
        # silhouette behind bars
        cx = x0 + w // 2
        d.ellipse([cx - 9, y0 + 8, cx + 9, y0 + 26], fill=(15, 15, 18))
        d.rectangle([cx - 15, y0 + 26, cx + 15, y1 - 5], fill=(15, 15, 18))
    elif kind == "quake":
        scene_sky(img, box, (150, 180, 205), (215, 225, 230))
        d = ImageDraw.Draw(img)
        # mountains + cracked ground
        d.polygon([(x0 + 6, y1 - 18), (x0 + 60, y0 + 14), (x0 + 110, y1 - 18)], fill=(140, 125, 105))
        d.polygon([(x0 + 70, y1 - 18), (x0 + 130, y0 + 8), (x0 + 195, y1 - 18)], fill=(120, 105, 88))
        d.polygon([(x0 + 120, y0 + 8), (x0 + 130, y0 + 8), (x0 + 125, y0 + 20)], fill=(245, 245, 245))
        d.rectangle([x0, y1 - 18, x1, y1], fill=(165, 140, 100))
        crack = [(x0 + 90, y1 - 18), (x0 + 105, y1 - 10), (x0 + 98, y1 - 4), (x0 + 112, y1)]
        d.line(crack, fill=(40, 32, 24), width=3)
        d.text((x0 + 8, y0 + 5), "M6.7", font=font(SANS_B, 18), fill=(160, 40, 30))
    elif kind == "factory":
        scene_sky(img, box, (140, 150, 170), (200, 195, 185))
        d = ImageDraw.Draw(img)
        d.rectangle([x0 + 20, y1 - 26, x0 + 180, y1 - 6], fill=(150, 120, 95))
        d.polygon([(x0 + 20, y1 - 26), (x0 + 60, y1 - 36), (x0 + 100, y1 - 26),
                   (x0 + 140, y1 - 36), (x0 + 180, y1 - 26)], fill=(110, 85, 65))
        d.rectangle([x0 + 185, y0 + 10, x0 + 200, y1 - 6], fill=(120, 95, 75))
        for fx in (x0 + 55, x0 + 95, x0 + 140):
            d.polygon([(fx - 10, y1 - 28), (fx, y1 - 38), (fx + 10, y1 - 28)], fill=(240, 110, 25))
            d.polygon([(fx - 4, y1 - 28), (fx, y1 - 34), (fx + 4, y1 - 28)], fill=(255, 195, 70))
        d.ellipse([x0 + 60, y0 + 4, x0 + 110, y0 + 20], fill=(70, 70, 76))
        d.ellipse([x0 + 120, y0 + 2, x0 + 175, y0 + 18], fill=(85, 85, 92))
    elif kind == "vial":
        scene_sky(img, box, (200, 225, 240), (240, 248, 250))
        d = ImageDraw.Draw(img)
        cx = x0 + w // 2
        d.rectangle([cx - 16, y0 + 14, cx + 16, y1 - 5], fill=(225, 240, 248), outline=(90, 130, 160), width=2)
        d.rectangle([cx - 16, y0 + 28, cx + 16, y1 - 5], fill=(200, 60, 60))
        d.rectangle([cx - 9, y0 + 6, cx + 9, y0 + 14], fill=(90, 130, 160))
        d.rectangle([cx - 3, y0 + 31, cx + 3, y0 + 41], fill=(255, 255, 255))
        d.rectangle([cx - 8, y0 + 33, cx + 8, y0 + 39], fill=(255, 255, 255))
        # virus dots
        rng = random.Random(3)
        for _ in range(7):
            vx = rng.randint(x0 + 12, x1 - 16)
            vy = rng.randint(y0 + 8, y1 - 14)
            if abs(vx - cx) < 30:
                continue
            d.ellipse([vx, vy, vx + 8, vy + 8], fill=(200, 60, 60))
    elif kind == "bottle":
        scene_sky(img, box, (215, 200, 170), (240, 230, 205))
        d = ImageDraw.Draw(img)
        cx = x0 + w // 2
        d.polygon([(cx - 8, y0 + 8), (cx + 8, y0 + 8), (cx + 8, y0 + 22),
                   (cx + 18, y0 + 34), (cx + 18, y1 - 8), (cx - 18, y1 - 8),
                   (cx - 18, y0 + 34), (cx - 8, y0 + 22)], fill=(90, 60, 35))
        d.rectangle([cx - 18, y0 + 48, cx + 18, y0 + 68], fill=(245, 240, 225))
        d.line([(cx - 9, y0 + 52), (cx + 9, y0 + 64)], fill=RED, width=3)
        d.line([(cx + 9, y0 + 52), (cx - 9, y0 + 64)], fill=RED, width=3)
        d.ellipse([cx - 5, y0 + 54, cx + 5, y0 + 62], outline=(40, 40, 40), width=2)
    elif kind == "plane":
        scene_sky(img, box, (120, 170, 215), (200, 225, 242))
        d = ImageDraw.Draw(img)
        d.ellipse([x0 + 16, y0 + 8, x0 + 52, y0 + 20], fill=(255, 255, 255))
        d.ellipse([x0 + 150, y0 + 12, x0 + 192, y0 + 24], fill=(255, 255, 255))
        # jet silhouette
        cy = y0 + 18
        d.polygon([(x0 + 26, cy), (x0 + 80, cy - 6), (x0 + 150, cy - 5),
                   (x0 + 196, cy), (x0 + 150, cy + 6), (x0 + 80, cy + 5)], fill=(60, 70, 90))
        d.polygon([(x0 + 96, cy + 3), (x0 + 128, cy + 16), (x0 + 142, cy + 16), (x0 + 120, cy + 3)], fill=(60, 70, 90))
        d.polygon([(x0 + 30, cy - 2), (x0 + 19, cy - 11), (x0 + 34, cy - 10), (x0 + 42, cy - 3)], fill=(60, 70, 90))
        for i in range(6):
            wx = x0 + 96 + i * 14
            d.ellipse([wx, cy - 3, wx + 5, cy + 2], fill=(220, 235, 248))
        d.rectangle([x0, y1 - 10, x1, y1], fill=(110, 160, 110))
    d.rectangle(box, outline=RULE, width=1)


def badge(draw, cx, cy, num, color):
    r = 10
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color,
                 outline=(255, 255, 255), width=2)
    t = str(num)
    tw = draw.textlength(t, font=font(SANS_B, 12))
    draw.text((cx - tw / 2, cy - 7), t, font=font(SANS_B, 12), fill=(255, 255, 255))


def render(data):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    margin = 24
    right = W - margin

    # ---- masthead ----
    mast = data["masthead"]
    f_mast = font(SERIF, 58)
    tw = d.textlength(mast, font=f_mast)
    d.text(((W - tw) / 2, 8), mast, font=f_mast, fill=INK)
    f_date = font(SERIF, 26)
    tw = d.textlength(data["date"], font=f_date)
    d.text(((W - tw) / 2, 74), data["date"], font=f_date, fill=RED)
    d.line([(margin, 108), (right, 108)], fill=INK, width=3)
    d.line([(margin, 113), (right, 113)], fill=INK, width=1)

    # ---- map + lead ----
    map_box = (margin, 122, 582, 348)
    lead = data["lead"]
    markers = [(1, lead["lon"], lead["lat"], RED)]
    for i, c in enumerate(data["cards"], start=2):
        markers.append((i, c["lon"], c["lat"], REGION_COLORS[c["region"]]))
    draw_map(img, map_box, markers)
    d = ImageDraw.Draw(img)
    d.text((margin, 352), "Numbers match the story cards below.",
           font=font(SANS, 11), fill=FAINT)

    lx = 598
    lw = right - lx
    # kicker chip
    kick = lead["kicker"]
    f_kick = font(SANS_B, 15)
    kw = d.textlength(kick, font=f_kick) + 16
    d.rectangle([lx, 122, lx + kw, 146], fill=RED)
    d.text((lx + 8, 126), kick, font=f_kick, fill=(255, 255, 255))
    badge(d, right - 12, 134, 1, RED)
    f_lead = font(SERIF, 26)
    y = 154
    for line in wrap(d, lead["headline"], f_lead, lw):
        d.text((lx, y), line, font=f_lead, fill=INK)
        y += 31
    f_sum = font(SERIF_R, 14)
    y += 2
    for line in wrap(d, lead["summary"], f_sum, lw):
        d.text((lx, y), line, font=f_sum, fill=(55, 52, 48))
        y += 18
    y += 4
    f_bul = font(SANS, 13)
    for b in lead["bullets"]:
        d.polygon([(lx, y + 3), (lx + 8, y + 7), (lx, y + 11)], fill=RED)
        for j, line in enumerate(wrap(d, b, f_bul, lw - 14)):
            d.text((lx + 14, y), line, font=f_bul, fill=INK)
            y += 16
        y += 2

    # ---- cards grid 4 x 3 ----
    cards = data["cards"]
    grid_top = 378
    cols, rows = 4, 3
    gap = 8
    cw = (right - margin - gap * (cols - 1)) // cols
    ch = 112
    scene_h = 40
    for idx, card in enumerate(cards):
        r, c = divmod(idx, cols)
        cx0 = margin + c * (cw + gap)
        cy0 = grid_top + r * (ch + gap)
        cx1, cy1 = cx0 + cw, cy0 + ch
        d.rectangle([cx0, cy0, cx1, cy1], fill=(252, 250, 244), outline=RULE, width=1)
        draw_scene(img, (cx0 + 1, cy0 + 1, cx1 - 1, cy0 + scene_h), card["scene"])
        d = ImageDraw.Draw(img)
        color = REGION_COLORS[card["region"]]
        badge(d, cx0 + 13, cy0 + scene_h + 10, idx + 2, color)
        f_reg = font(SANS_B, 10)
        d.text((cx0 + 28, cy0 + scene_h + 4), card["region"], font=f_reg, fill=color)
        f_head = font(SERIF, 13)
        head_lines = wrap(d, card["headline"], f_head, cw - 10)[:2]
        hy = cy0 + scene_h + 17
        for line in head_lines:
            d.text((cx0 + 5, hy), line, font=f_head, fill=INK)
            hy += 15
        f_body = font(SANS, 10)
        body_lines = wrap(d, card["summary"], f_body, cw - 10)[:2]
        for line in body_lines:
            d.text((cx0 + 5, hy + 1), line, font=f_body, fill=(70, 66, 60))
            hy += 12

    # ---- briefs panel ----
    briefs_top = grid_top + rows * (ch + gap) + 6
    d.text((margin, briefs_top), "ALSO TODAY — AROUND THE WORLD",
           font=font(SANS_B, 15), fill=INK)
    d.line([(margin, briefs_top + 22), (right, briefs_top + 22)], fill=RULE, width=1)
    items = data["textlist"]
    col_w = (right - margin - 24) // 2
    f_bh = font(SANS_B, 12)
    f_bs = font(SANS, 11)
    for i, item in enumerate(items):
        col = 0 if i < 6 else 1
        row = i % 6
        bx = margin + col * (col_w + 24)
        by = briefs_top + 28 + row * 31
        color = REGION_COLORS[item["region"]]
        d.rectangle([bx, by + 2, bx + 4, by + 24], fill=color)
        for j, line in enumerate(wrap(d, item["headline"], f_bh, col_w - 12)[:1]):
            d.text((bx + 10, by), line, font=f_bh, fill=INK)
        for j, line in enumerate(wrap(d, item["summary"], f_bs, col_w - 12)[:1]):
            d.text((bx + 10, by + 15), line, font=f_bs, fill=(80, 76, 70))

    # ---- ticker ----
    tick_top = briefs_top + 28 + 6 * 31 + 6
    d.rectangle([margin, tick_top, right, tick_top + 40], fill=(25, 23, 22))
    f_tick = font(SANS, 11)
    tick_text = "  •  ".join(data["ticker"])
    lines = wrap(d, tick_text, f_tick, right - margin - 16)
    ty = tick_top + 5
    for line in lines[:2]:
        d.text((margin + 8, ty), line, font=f_tick, fill=(240, 238, 232))
        ty += 15

    # ---- footer ----
    foot = data["footer"]
    f_foot = font(SANS, 11)
    tw = d.textlength(foot, font=f_foot)
    d.text(((W - tw) / 2, tick_top + 44), foot, font=f_foot, fill=FAINT)

    speckle(img, (0, 0, W - 1, H - 1), 2600, seed=42, alpha=14)
    return img


def main():
    with open(os.path.join(HERE, "stories.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    img = render(data)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", HERE)
    os.makedirs(out_dir, exist_ok=True)
    img.save(os.path.join(out_dir, "entry.png"), optimize=True)
    print("wrote", os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
