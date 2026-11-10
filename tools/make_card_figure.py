#!/usr/bin/env python3
"""Anatomie d'une carte video (format diaporama 9:16) + rythme.

Sortie : docs/card.png (2x)
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, S = 1080, 800, 2
FONT_DIR = Path(r"C:\Windows\Fonts")
REG, BOLD = FONT_DIR / "segoeui.ttf", FONT_DIR / "segoeuib.ttf"

INK, MUTED = "#1c1917", "#78716c"
LINE, SOFT = "#e7e5e4", "#f8fafc"
WHITE = "#ffffff"
ACCENT = "#f59e0b"
DANGER = "#b91c1c"

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


def zone(x, y, w, h, label, color):
    """Zone interdite : hachures + libelle."""
    d.rectangle([x * S, y * S, (x + w) * S, (y + h) * S], fill=None)
    step = 9
    for i in range(int(x), int(x + w) + int(h), step):
        x1, y1 = max(x, i - h), min(x + w, i)
        if x1 < x + w and y1 > x:
            d.line([(x1 * S, (y + (x1 - (i - h))) * S), (y1 * S, (y + (y1 - (i - h))) * S)],
                   fill=color, width=1)
    text(x + 8, y + 6, label, 8, True, color)


# ── titre de la planche ─────────────────────────────────────────────────────
text(48, 24, "Anatomie d'une carte vidéo", 19, True)
text(48, 52, "Une image, trois à six mots. Tout le reste est une contrainte de placement.", 10, False, MUTED)

# ── cadre 9:16 ──────────────────────────────────────────────────────────────
FX, FY, FW, FH = 48, 96, 272, 484
for i in range(FH):                      # degrade de fond
    t = i / FH
    c = (int(11 + 18 * t), int(44 + 22 * t), int(58 + 30 * t))
    d.line([FX * S, (FY + i) * S, (FX + FW) * S, (FY + i) * S], fill=c, width=int(S))

d.rectangle([FX * S, FY * S, (FX + FW) * S, (FY + 64) * S], fill=(0, 0, 0))
d.rectangle([FX * S, (FY + 330) * S, (FX + FW) * S, (FY + FH) * S], fill=(0, 0, 0))
zone(FX, FY, FW, 64, "UI · 120 px", "#7f1d1d")
zone(FX, FY + 330, FW, FH - 330, "légende · 320 px", "#7f1d1d")

text(FX + 18, FY + 78, "MAROC", 9, True, ACCENT)
text(FX + 18, FY + 104, "Grève des", 25, True, WHITE)
text(FX + 18, FY + 140, "transports :", 25, True, WHITE)
text(FX + 18, FY + 176, "14 rédactions", 25, True, WHITE)
text(FX + 18, FY + 232, "Hespress · France 24", 8.5, False, "#94a3b8")

# ── annotations ─────────────────────────────────────────────────────────────
AX = 372
def note(y, title, body, color=INK):
    d.ellipse([(AX - 14) * S, (y + 3) * S, (AX - 6) * S, (y + 11) * S], fill=color)
    text(AX + 4, y - 1, title, 10.5, True, color)
    text(AX + 4, y + 14, body, 8.5, False, MUTED)

note(FY - 2, "Zone haute — 120 px", "Pseudo, son, bouton : le texte n'y entre jamais.", DANGER)
note(FY + 76, "Kicker — 2 mots", "Le pays ou la catégorie, en capitales. Il situe sans expliquer.", ACCENT)
note(FY + 112, "Titre — 3 à 6 mots", "96 px, 3 lignes maximum, coupure décidée à la main.", INK)
note(FY + 220, "Source — toujours visible", "Le nom de la rédaction, à 24 px. C'est l'attribution.", INK)
note(FY + 320, "Zone basse — 320 px", "Description, boutons, navigation : le texte s'arrête avant.", DANGER)

text(AX, FY + 396, "Contraste", 10.5, True, INK)
text(AX, FY + 411, "Texte blanc sur fond sombre, ratio ≥ 7:1.", 8.5, False, MUTED)
text(AX, FY + 434, "Un voile sombre derrière le texte garantit", 8.5, False, MUTED)
text(AX, FY + 447, "la lisibilité quelle que soit l'image.", 8.5, False, MUTED)

# ── bande de rythme ─────────────────────────────────────────────────────────
RY = 612
text(48, RY - 22, "Rythme : 1,2 à 2,5 s par carte", 10.5, True, INK)
durs = ["1,6 s", "2,2 s", "1,4 s"]
for i in range(3):
    x = 48 + i * 96
    r(x, RY, 80, 142, "#0b2c3a", None, 5)
    r(x, RY, 80, 14, "#000000", None, 5)
    r(x, RY + 100, 80, 42, "#000000", None, 5)
    bar_y = RY + 34 + i * 6
    r(x + 8, bar_y, 54, 6, "#e2e8f0", None, 3)
    r(x + 8, bar_y + 12, 40, 6, "#e2e8f0", None, 3)
    text(x + 40, RY + 152, durs[i], 8.5, True, MUTED, anchor="ma")

text(360, RY + 6, "10 à 14 cartes pour 20 à 35 secondes.", 9.5, True, INK)
text(360, RY + 24, "Au-delà de 40 s, le spectateur voit des images fixes :", 8.5, False, MUTED)
text(360, RY + 37, "il décroche. Le format court, c'est la contrainte,", 8.5, False, MUTED)
text(360, RY + 50, "pas un choix de goût.", 8.5, False, MUTED)

text(360, RY + 78, "Coupe franche entre les cartes.", 9.5, True, INK)
text(360, RY + 96, "Pas de transition animée : elle coûte du rendu", 8.5, False, MUTED)
text(360, RY + 109, "et fait « diaporama » plutôt que « natif ».", 8.5, False, MUTED)

Path("docs").mkdir(exist_ok=True)
img.resize((W * 2, H * 2), Image.LANCZOS).save("docs/card.png")
print("ecrit: docs/card.png")
