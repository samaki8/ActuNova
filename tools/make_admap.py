#!/usr/bin/env python3
"""Carte des emplacements publicitaires (wireframe desktop + mobile).

Montre ou sont reserves les trous dans la maquette, avant toute integration
de regie. Sortie : docs/ad-slots.png (2x).

Usage: python tools/make_admap.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, S = 1400, 1000, 2
FONT_DIR = Path(r"C:\Windows\Fonts")
REG, BOLD = FONT_DIR / "segoeui.ttf", FONT_DIR / "segoeuib.ttf"

INK, MUTED, LINE = "#1c1917", "#78716c", "#e7e5e4"
CONTENT_F, CONTENT_S = "#f8fafc", "#e2e8f0"
AD_F, AD_S, AD_T = "#fffbeb", "#f59e0b", "#92400e"
FRAME = "#d6d3d1"

img = Image.new("RGB", (W * S, H * S), "#ffffff")
d = ImageDraw.Draw(img)
_cache: dict = {}


def font(size: float, bold: bool = False):
    key = (size, bold)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(str(BOLD if bold else REG), int(size * S))
    return _cache[key]


def text(x, y, s, size=11, bold=False, color=INK, anchor="la"):
    d.text((x * S, y * S), s, font=font(size, bold), fill=color, anchor=anchor)


def rect(x, y, w, h, fill, stroke, r=6, sw=1.2, dash=False):
    box = [x * S, y * S, (x + w) * S, (y + h) * S]
    if dash:
        # contour pointille : emplacement desactive par defaut
        d.rounded_rectangle(box, radius=r * S, fill=fill)
        step = 7
        for i in range(int(x), int(x + w), step):
            d.line([(i * S, y * S), (min(i + 4, x + w) * S, y * S)], fill=stroke, width=int(sw * S))
            d.line([(i * S, (y + h) * S), (min(i + 4, x + w) * S, (y + h) * S)], fill=stroke, width=int(sw * S))
        return
    d.rounded_rectangle(box, radius=r * S, fill=fill, outline=stroke, width=max(1, int(sw * S)))


def ad(x, y, w, h, dims, slot, dashed=False):
    rect(x, y, w, h, AD_F, AD_S, 5, 1.4, dash=dashed)
    text(x + w / 2, y + h / 2 - 13, f"PUB · {dims}", 10.5, True, AD_T, anchor="ma")
    text(x + w / 2, y + h / 2 + 3, slot, 9.5, False, "#b45309", anchor="ma")


def card(x, y, w, h, label):
    rect(x, y, w, h, CONTENT_F, CONTENT_S, 5, 1)
    text(x + 10, y + 9, label, 9, False, MUTED)


# --- titres -----------------------------------------------------------------
text(56, 34, "Emplacements publicitaires", 20, True)
text(56, 64, "Réservation dans la maquette, avant toute intégration de régie — un trou non réservé coûte un CLS.", 11, False, MUTED)

# --- cadre desktop ----------------------------------------------------------
rect(56, 112, 700, 800, "#ffffff", FRAME, 10, 1.6)
text(72, 124, "DESKTOP 1440", 9, True, MUTED)

X0, XW = 72, 668
rect(X0, 142, XW, 34, "#f1f5f9", "#e2e8f0", 5, 1)
text(X0 + 12, 152, "Navigation · FR/EN · recherche", 9, False, MUTED)

ad(X0, 186, XW, 96, "970×250", "header-billboard · pages article et vidéo")

LW, RX = 404, 488
for i, y in enumerate([294, 378, 462]):
    card(X0, y, LW, 74, f"Story {i + 1} · titre + 14 sources + âge")
ad(X0, 546, LW, 104, "300×250", "feed-inline-1")
for i, y in enumerate([660, 744]):
    card(X0, y, LW, 74, f"Story {i + 4} · titre + sources")

ad(RX, 294, 252, 320, "300×600", "article-sidebar · sticky")
text(RX, 624, "Sticky : suit le scroll,", 9, False, MUTED)
text(RX, 638, "s'arrête avant le footer.", 9, False, MUTED)
card(RX, 664, 252, 154, "« Le bulletin du jour »\nvidéo 16:9 + script")

ad(X0, 834, XW, 40, "728×90", "article-end · fin de page")

# --- cadre mobile -----------------------------------------------------------
MX, MW = 820, 340
rect(MX, 112, MW, 800, "#ffffff", FRAME, 10, 1.6)
text(MX + 16, 124, "MOBILE 390", 9, True, MUTED)

IX, IW = 836, 308
rect(IX, 142, IW, 34, "#f1f5f9", "#e2e8f0", 5, 1)
text(IX + 12, 152, "Navigation · sélecteur FR/EN", 9, False, MUTED)

for i, y in enumerate([186, 250, 314]):
    card(IX, y, IW, 56, f"Story {i + 1}")
ad(IX, 378, IW, 110, "300×250", "feed-inline-1 · après la 3ᵉ story")
for i, y in enumerate([496, 560, 624, 688]):
    card(IX, y, IW, 56, f"Story {i + 4}")

text(IX, 762, "Aucune pub dans les 600 premiers pixels.", 9, False, MUTED)
ad(IX, 828, IW, 44, "320×50", "mobile-anchor · désactivé par défaut", dashed=True)

# --- legende ----------------------------------------------------------------
LY = 946
rect(56, LY, 16, 16, AD_F, AD_S, 4, 1.4)
text(80, LY + 1, "Emplacement réservé (hauteur fixe, même vide)", 9.5, False, MUTED)
rect(390, LY, 16, 16, CONTENT_F, CONTENT_S, 4, 1)
text(414, LY + 1, "Contenu éditorial", 9.5, False, MUTED)
rect(560, LY, 16, 16, AD_F, AD_S, 4, 1.4, dash=True)
text(584, LY + 1, "Slot présent mais désactivé par défaut", 9.5, False, MUTED)

out = Path("docs")
out.mkdir(exist_ok=True)
img.resize((W * 2, H * 2), Image.LANCZOS).save(out / "ad-slots.png")
print("ecrit: docs/ad-slots.png")
