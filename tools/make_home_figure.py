#!/usr/bin/env python3
"""Composition de la page d'accueil : une manuelle, Resume du jour, fil, carte.

Sortie : docs/home.png (2x)
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, S = 1100, 862, 2
FONT_DIR = Path(r"C:\Windows\Fonts")
REG, BOLD = FONT_DIR / "segoeui.ttf", FONT_DIR / "segoeuib.ttf"

INK, MUTED = "#1c1917", "#78716c"
LINE, SOFT = "#e7e5e4", "#f8fafc"
GOLD, GOLD_S, GOLD_D = "#f59e0b", "#fffbeb", "#92400e"
TEAL, TEAL_S, TEAL_D = "#0d9488", "#f0fdfa", "#0f766e"
SLATE, SLATE_S = "#64748b", "#f1f5f9"

img = Image.new("RGB", (W * S, H * S), "#ffffff")
d = ImageDraw.Draw(img)
_cache: dict = {}


def font(size, bold=False):
    k = (size, bold)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(str(BOLD if bold else REG), int(size * S))
    return _cache[k]


def text(x, y, s, size=10, bold=False, color=INK, anchor="la"):
    d.text((x * S, y * S), s, font=font(size, bold), fill=color, anchor=anchor)


def r(x, y, w, h, fill, stroke=None, rad=6, sw=1.1):
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=rad * S,
                        fill=fill, outline=stroke, width=max(1, int(sw * S)))


def bar(x, y, w, h=8, fill="#cbd5e1"):
    r(x, y, w, h, fill, None, 3)


def num(x, y, n, color):
    d.ellipse([x * S, y * S, (x + 17) * S, (y + 17) * S], fill=color)
    text(x + 8.5, y + 3.5, str(n), 8.5, True, "#ffffff", anchor="ma")


text(56, 26, "La page d'accueil, de haut en bas", 19, True)
text(56, 56, "Une éditoriale qui expire, un Résumé quotidien, le fil, puis la carte — jamais l'inverse.", 10, False, MUTED)

FX, FY, FW, FH = 56, 96, 988, 676
r(FX, FY, FW, FH, "#ffffff", LINE, 12, 1.6)
IX, IW = FX + 16, FW - 32

# ── 1. barre de navigation ─────────────────────────────────────────────────
r(IX, FY + 16, IW, 34, SLATE_S, "#e2e8f0", 6, 1)
r(IX + 12, FY + 24, 22, 18, TEAL_S, None, 4)
text(IX + 42, FY + 27, "Fil", 9, True, INK)
text(IX + 76, FY + 27, "Carte", 9, False, MUTED)
text(IX + 122, FY + 27, "Résumé", 9, False, MUTED)
text(IX + 176, FY + 27, "Suivre", 9, False, MUTED)
r(IX + IW - 74, FY + 22, 62, 22, "#ffffff", "#cbd5e1", 11, 1)
text(IX + IW - 62, FY + 27, "FR", 9, True, INK)
tri = IX + IW - 26
d.polygon([(tri * S, (FY + 30) * S), ((tri + 8) * S, (FY + 30) * S), ((tri + 4) * S, (FY + 36) * S)],
          fill=MUTED)

# ── 2. la une ──────────────────────────────────────────────────────────────
HY = FY + 62
r(IX, HY, 520, 188, "#ffffff", LINE, 8, 1)
r(IX + 1, HY + 1, 518, 96, GOLD_S, None, 8)
r(IX + 13, HY + 13, 62, 17, GOLD, None, 8)
text(IX + 44, HY + 16, "À LA UNE", 7.5, True, "#ffffff", anchor="ma")
text(IX + 14, HY + 108, "Grève des transports au Maroc :", 12.5, True, INK)
text(IX + 14, HY + 126, "ce que disent 14 rédactions", 12.5, True, INK)
text(IX + 14, HY + 150, "14 rédactions · mis à jour il y a 12 min", 8.5, False, MUTED)
r(IX + 352, HY + 104, 156, 20, GOLD_S, GOLD, 10, 1)
text(IX + 430, HY + 110, "épinglé · expire dans 6 h", 7.5, True, GOLD_D, anchor="ma")
num(FX - 26, HY + 4, 1, GOLD)

SX = IX + 536
for i, (ty, n) in enumerate([(HY, 8), (HY + 97, 5)]):
    r(SX, ty, 392, 91, "#ffffff", LINE, 8, 1)
    r(SX + 1, ty + 1, 120, 89, SLATE_S, None, 8)
    bar(SX + 136, ty + 18, 224, 10, "#334155")
    bar(SX + 136, ty + 36, 180, 10, "#334155")
    text(SX + 136, ty + 60, f"{n} rédactions · il y a 3 h", 8.5, False, MUTED)

# ── 3. le resume du jour ───────────────────────────────────────────────────
RY = HY + 202
r(IX, RY, IW, 88, TEAL_S, "#99f6e4", 8, 1.2)
r(IX + 12, RY + 12, 112, 64, "#134e4a", None, 6)
d.polygon([((IX + 60) * S, (RY + 34) * S), ((IX + 60) * S, (RY + 54) * S), ((IX + 74) * S, (RY + 44) * S)],
          fill="#5eead4")
text(IX + 138, RY + 14, "Le Résumé du jour", 11.5, True, TEAL_D)
text(IX + 138, RY + 32, "4 min 12 · 5 événements · français et anglais", 8.5, False, "#0f766e")
chips = ["Mali", "Budget 2027", "Sommet UE", "+2"]
cx = IX + 138
for c in chips:
    w = 8 + len(c) * 5.2
    r(cx, RY + 54, w, 18, "#ffffff", "#99f6e4", 9, 1)
    text(cx + w / 2, RY + 59, c, 7.5, False, TEAL_D, anchor="ma")
    cx += w + 6
num(FX - 26, RY + 4, 2, TEAL)

# ── 4. le fil ──────────────────────────────────────────────────────────────
FY2 = RY + 100
for i, y in enumerate([FY2, FY2 + 84]):
    r(IX, y, IW, 76, "#ffffff", LINE, 8, 1)
    r(IX + 1, y + 1, 104, 74, SLATE_S, None, 8)
    bar(IX + 118, y + 14, 360, 10, "#334155")
    bar(IX + 118, y + 32, 260, 10, "#334155")
    text(IX + 118, y + 54, f"{[9, 4][i]} rédactions · il y a {[1, 5][i]} h", 8.5, False, MUTED)
num(FX - 26, FY2 + 4, 3, SLATE)

# emplacement publicitaire
ADY = FY2 + 172
r(IX, ADY, IW, 74, GOLD_S, GOLD, 6, 1.4)
text(IX + IW / 2, ADY + 26, "PUB · 728×90", 10, True, GOLD_D, anchor="ma")
text(IX + IW / 2, ADY + 42, "feed-inline · hauteur réservée, jamais de trou", 8, False, "#b45309", anchor="ma")

# ── 5. la carte ────────────────────────────────────────────────────────────
MY = ADY + 84
r(IX, MY, IW, 42, "#f1f5f9", "#e2e8f0", 6, 1)
text(IX + 14, MY + 13, "Explorer la carte du monde", 9.5, True, "#334155")
text(IX + IW - 14, MY + 13, "chargée au clic →", 8.5, False, MUTED, anchor="ra")
num(FX - 26, MY + 12, 4, "#475569")

# ── legende ────────────────────────────────────────────────────────────────
text(56, 818, "1 · une choisie à la main, avec expiration   ·   2 · le Résumé quotidien, chapitré   ·   "
              "3 · le fil algorithmique   ·   4 · la carte, chargée seulement au clic",
     9, False, MUTED)

Path("docs").mkdir(exist_ok=True)
img.resize((W * 2, H * 2), Image.LANCZOS).save("docs/home.png")
print("ecrit: docs/home.png")
