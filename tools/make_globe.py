#!/usr/bin/env python3
"""Rendu de la page Carte : un globe (projection orthographique) au lieu d'un plan.

Le globe est calcule par projection inverse : pour chaque pixel du disque, on
retrouve le point de la sphere, puis le pays, sur un masque equirectangulaire
construit a partir de Natural Earth (domaine public).

Un point n'apparait que s'il est sur la face visible : pas de point « a travers »
la Terre, ce qui est le premier truc qui trahit un faux globe en 2D.

Sortie : docs/globe.png
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import geo_silhouette as geo

W, H = 1440, 1080
FONT = Path(r"C:\Windows\Fonts")
SANS = FONT / "segoeui.ttf"
SANS_SB = FONT / "seguisb.ttf" if (FONT / "seguisb.ttf").exists() else FONT / "segoeuib.ttf"
SERIF_B = FONT / "georgiab.ttf"

BG = "#080A0C"
SURFACE = "#12161B"
INK = "#F4F3F0"
MUTED = "#8C949E"
LINE = "#232A32"
ACCENT = "#FB7185"
OCEAN = np.array([15, 29, 43], dtype=float)
LAND = np.array([58, 74, 90], dtype=float)

CX, CY, R = 500.0, 540.0, 392.0
LAM0, PHI0 = math.radians(12.0), math.radians(16.0)   # europe / afrique de l'ouest

img = Image.new("RGB", (W, H), BG)
_f: dict = {}


def font(size, path=SANS):
    k = (size, path)
    if k not in _f:
        _f[k] = ImageFont.truetype(str(path), int(size))
    return _f[k]


def text(x, y, s, size=13, path=SANS, color=INK, anchor="la"):
    ImageDraw.Draw(img).text((x, y), s, font=font(size, path), fill=color, anchor=anchor)


def rrect(x, y, w, h, fill, stroke=None, r=10, sw=1):
    ImageDraw.Draw(img).rounded_rectangle([x, y, x + w, y + h], radius=r,
                                          fill=fill, outline=stroke, width=sw)


# ── masque equirectangulaire des terres ─────────────────────────────────────
MW, MH = 2048, 1024
mask = Image.new("L", (MW, MH), 0)
dm = ImageDraw.Draw(mask)
for ring in geo.world_rings():
    lons = [p[0] for p in ring]
    if max(lons) - min(lons) > 180:      # anneau a cheval sur l'antimeridien
        continue
    for shift in (0, 360, -360):
        pts = [((lon + shift + 180) * MW / 360.0, (90 - lat) * MH / 180.0) for lon, lat in ring]
        dm.polygon(pts, fill=255)
mask_np = np.asarray(mask, dtype=np.uint8)

# ── projection inverse, vectorisee ──────────────────────────────────────────
# On amene le point (lat0, lon0) au centre du disque : rotation autour de Z par
# -lon0, puis autour de Y par -(90-lat0). Une rotation autour de X centrerait le
# globe sur le pole, pas sur le point voulu.
xs = (np.arange(W) - CX) / R
ys = -(np.arange(H) - CY) / R
gx, gy = np.meshgrid(xs, ys)
rr = gx * gx + gy * gy
inside = rr <= 1.0
z2 = np.sqrt(np.clip(1.0 - rr, 0.0, None))

sl, cl = math.sin(PHI0), math.cos(PHI0)
so, co = math.sin(LAM0), math.cos(LAM0)

# base de vue : droite = est (Y1), haut = nord (u), profondeur = axe de visee (d)
y1 = gx
x1 = -gy * sl + z2 * cl
z1 = gy * cl + z2 * sl
xw = x1 * co - y1 * so
yw = x1 * so + y1 * co
zw = z1

lat = np.degrees(np.arcsin(np.clip(zw, -1, 1)))
lon = np.degrees(np.arctan2(yw, xw))

u = ((lon + 180.0) / 360.0 * MW).astype(np.int32) % MW
v = np.clip(((90.0 - lat) / 180.0 * MH).astype(np.int32), 0, MH - 1)
is_land = (mask_np[v, u] > 127) & inside

# ── eclairage ───────────────────────────────────────────────────────────────
L = np.array([-0.42, 0.50, 0.76])
L = L / np.linalg.norm(L)
shade = np.clip(gx * L[0] + gy * L[1] + z2 * L[2], 0.0, 1.0)
shade = 0.44 + 0.56 * shade ** 0.85

face = np.where(is_land[..., None], LAND, OCEAN) * shade[..., None]

# limbe : leger halo bleute sur le bord
rim = np.clip((rr - 0.90) / 0.10, 0.0, 1.0)[..., None]
face = face * (1 - rim * 0.55) + np.array([90, 150, 200]) * rim * 0.55

rgb = np.zeros((H, W, 3), dtype=float)
rgb[inside] = face[inside]
globe = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))

# halo atmospherique
halo = Image.new("RGB", (W, H), BG)
dh = ImageDraw.Draw(halo)
for i in range(26, 0, -1):
    a = int(6 + (26 - i) * 1.1)
    dh.ellipse([CX - R - i, CY - R - i, CX + R + i, CY + R + i],
               outline=(a // 3, a // 2, a))
img = Image.blend(img, halo.filter(ImageFilter.GaussianBlur(18)), 0.55)
img.paste(globe, (0, 0), Image.fromarray((inside * 255).astype(np.uint8)))

d = ImageDraw.Draw(img)


# ── graticule ───────────────────────────────────────────────────────────────
def project(lon_d, lat_d):
    lam, phi = math.radians(lon_d), math.radians(lat_d)
    x = math.cos(phi) * math.cos(lam)
    y = math.cos(phi) * math.sin(lam)
    z = math.sin(phi)
    x1_ = x * math.cos(LAM0) + y * math.sin(LAM0)
    y1_ = -x * math.sin(LAM0) + y * math.cos(LAM0)
    depth = x1_ * math.cos(PHI0) + z * math.sin(PHI0)          # axe de visee
    up = -x1_ * math.sin(PHI0) + z * math.cos(PHI0)            # nord
    return CX + R * y1_, CY - R * up, depth                    # droite = est


def arc(points, color, width=1):
    for (a, b) in zip(points, points[1:]):
        if a[2] > 0.02 and b[2] > 0.02:
            d.line([(a[0], a[1]), (b[0], b[1])], fill=color, width=width)


for lat_d in range(-60, 90, 30):
    arc([project(lon_d, lat_d) for lon_d in range(-180, 181, 4)], (28, 42, 56))
for lon_d in range(-180, 180, 30):
    arc([project(lon_d, lat_d) for lat_d in range(-85, 86, 4)], (28, 42, 56))
arc([project(lon_d, 0) for lon_d in range(-180, 181, 4)], (52, 76, 96))

# ── evenements ──────────────────────────────────────────────────────────────
EVENTS = [
    ("FRANCE", "Grève du 5 novembre", 2.35, 48.85, 3, (29, 78, 216), True),
    ("ÉTATS-UNIS", "Midterms", -95.0, 38.0, 3, (67, 56, 202), False),
    ("CALIFORNIE", "548 peines commuées", -119.4, 36.7, 2, (67, 56, 202), False),
    ("MAROC", "Vigilance terroriste", -6.85, 34.0, 1, (190, 24, 93), False),
    ("PARAGUAY", "Le président démissionne", -57.6, -25.3, 1, (180, 83, 9), False),
    ("COP31", "Financement de l'adaptation", -48.5, -1.45, 1, (21, 128, 61), False),
    ("PROCHE-ORIENT", "Démolitions à Biddu", 35.1, 31.9, 1, (13, 148, 136), False),
]

glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dg = ImageDraw.Draw(glow)
for kicker, titre, lon, lat_d, n, col, sel in EVENTS:
    px, py, depth = project(lon, lat_d)
    if depth <= 0.15:
        continue
    rad = 5 + n * 2.6
    col_rgba = col + (150,)
    dg.ellipse([px - rad * 3, py - rad * 3, px + rad * 3, py + rad * 3], fill=col_rgba)
img.paste(Image.alpha_composite(img.convert("RGBA"),
                                glow.filter(ImageFilter.GaussianBlur(20))).convert("RGB"), (0, 0))
d = ImageDraw.Draw(img)

dot_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dd = ImageDraw.Draw(dot_layer)
for kicker, titre, lon, lat_d, n, col, sel in EVENTS:
    px, py, depth = project(lon, lat_d)
    if depth <= 0.10:
        continue
    # un point proche du limbe s'efface : sur une vraie sphere, il est de biais
    a = int(255 * min(1.0, (depth - 0.10) / 0.28))
    rad = 6 + n * 3.2
    dd.ellipse([px - rad, py - rad, px + rad, py + rad],
               fill=col + (a,), outline=(10, 16, 22, a), width=2)
img = Image.alpha_composite(img.convert("RGBA"), dot_layer).convert("RGB")
d = ImageDraw.Draw(img)

for kicker, titre, lon, lat_d, n, col, sel in EVENTS:
    px, py, depth = project(lon, lat_d)
    if sel and depth > 0.10:
        rad = 6 + n * 3.2
        d.ellipse([px - rad - 11, py - rad - 11, px + rad + 11, py + rad + 11],
                  outline=ACCENT, width=2)

# etiquette
px, py, _ = project(2.35, 48.85)
lbl = "France · 3 rédactions"
fw = font(12, SANS_SB).getlength(lbl) + 26
rrect(px + 30, py - 40, fw, 30, "#0B1116", "#33414D", 8)
text(px + 43, py - 25, lbl, 12, SANS_SB, INK, anchor="lm")

# ── habillage ───────────────────────────────────────────────────────────────
text(72, 60, "Carte du monde", 21, SERIF_B, INK)
text(72, 92, "glisser pour tourner · double-clic pour zoomer · un point par événement",
     12.5, SANS, MUTED)

rrect(72, H - 92, 470, 44, "#0B1116", LINE, 10)
text(90, H - 78, "● 1 rédaction", 10.5, SANS, MUTED)
text(186, H - 78, "● 2", 10.5, SANS, MUTED)
text(226, H - 78, "● 3 et plus", 10.5, SANS, MUTED)
text(320, H - 78, "taille = couverture", 10.5, SANS, "#5C656F")

# ── panneau lateral ─────────────────────────────────────────────────────────
PX, PY, PW, PH = 1040, 148, 328, 784
rrect(PX, PY, PW, PH, SURFACE, LINE, 12)
text(PX + 22, PY + 20, "ÉVÉNEMENT SÉLECTIONNÉ", 10, SANS_SB, ACCENT)
text(PX + 22, PY + 42, "il y a 12 min · 3 rédactions", 11, SANS, MUTED)

y = PY + 72
for ln in ("Grève du 5 novembre :", "les syndicats", "rejoignent le", "mouvement"):
    text(PX + 22, y, ln, 23, SERIF_B, INK)
    y += 30
y += 10
for ln in ("Le Monde, France 24 et BBC", "confirment la reprise du", "mouvement ; les chiffres",
           "divergent selon les sources."):
    text(PX + 22, y, ln, 12.5, SANS, "#AEB5BE")
    y += 19

y += 18
d.line([PX + 22, y, PX + PW - 22, y], fill=LINE)
y += 16
text(PX + 22, y, "CHIFFRES DIVERGENTS", 10, SANS_SB, MUTED)
for val, src in [("575 000", "Le Monde"), ("1,6 M", "France 24"), ("non communiqué", "BBC")]:
    y += 22
    text(PX + 22, y, val, 13, SANS_SB, INK)
    text(PX + PW - 22, y, src, 11, SANS, MUTED, anchor="ra")

y += 34
d.line([PX + 22, y, PX + PW - 22, y], fill=LINE)
y += 16
text(PX + 22, y, "SUR LA MÊME FACE DU GLOBE", 10, SANS_SB, MUTED)
for k, t, n in [("MAROC", "Vigilance face à la menace", 1),
                ("PROCHE-ORIENT", "Démolitions à Biddu", 1)]:
    y += 26
    text(PX + 22, y, k, 9.5, SANS_SB, "#5C656F")
    text(PX + 22, y + 14, t, 12, SANS_SB, INK)
    text(PX + PW - 22, y + 14, str(n), 11, SANS, MUTED, anchor="ra")
    y += 30

by = PY + PH - 56
rrect(PX + 22, by, PW - 44, 36, ACCENT, None, 18)
text(PX + 22 + (PW - 44) / 2, by + 18, "Voir l'événement", 12.5, SANS_SB, "#1A0A0D", anchor="mm")

Path("docs").mkdir(exist_ok=True)
img.save("docs/globe.png")
print("ecrit: docs/globe.png", img.size)
