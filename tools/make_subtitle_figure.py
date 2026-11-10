#!/usr/bin/env python3
"""Schema de l'alignement des sous-titres : une voix, plusieurs pistes.

Montre que les blocs de sous-titres se calent sur les SEGMENTS du script (et non
sur les mots), et que le budget de caracteres depend de la duree du segment.
Sortie : docs/subtitles.png (2x)
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, S = 1060, 442, 2
FONT_DIR = Path(r"C:\Windows\Fonts")
REG, BOLD = FONT_DIR / "segoeui.ttf", FONT_DIR / "segoeuib.ttf"

INK, MUTED, LINE = "#1c1917", "#78716c", "#e7e5e4"
GUTTER = 150
X0, X1 = 150, 1010
TOTAL = 69.0
SEGS = [8, 12, 16, 9, 14, 10]
SCALE = (X1 - X0) / TOTAL

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


def r(x, y, w, h, fill, stroke=None, rad=4, sw=1.1):
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=rad * S,
                        fill=fill, outline=stroke, width=max(1, int(sw * S)))


def bounds():
    x, out = X0, []
    for dur in SEGS:
        out.append((x, x + dur * SCALE, dur))
        x += dur * SCALE
    return out


text(56, 26, "Une voix, cinq sous-titres — l'alignement se fait au segment", 18, True)
text(56, 54, "Une traduction ne dure pas le même temps que la voix : chaque bloc se cale sur la durée du plan, jamais sur les mots.", 10, False, MUTED)

# ── regle du temps ──────────────────────────────────────────────────────────
d.line([X0 * S, 108 * S, X1 * S, 108 * S], fill=LINE, width=int(1.2 * S))
t = 0
while t <= 60:
    x = X0 + t * SCALE
    d.line([x * S, 104 * S, x * S, 112 * S], fill=LINE, width=int(1.2 * S))
    text(x, 88, f"{t}s", 8, False, MUTED, anchor="ma")
    t += 10
text(56, 100, "TEMPS", 8.5, True, MUTED)

# ── piste audio ─────────────────────────────────────────────────────────────
AUD_Y = 124
text(56, AUD_Y + 6, "VOIX — FR", 9, True, "#0f766e")
for i, (a, b, dur) in enumerate(bounds()):
    r(a + 1, AUD_Y, b - a - 2, 26, "#ccfbf1", "#99f6e4", 4, 1)
    text((a + b) / 2, AUD_Y + 7, f"S{i + 1} · {dur}s", 8, True, "#0f766e", anchor="ma")

# ── pistes de sous-titres ───────────────────────────────────────────────────
# remplissage = part du budget de caracteres (duree x 15 car/s) reellement
# consommee. Meme boite pour toutes les langues : c'est la langue qui remplit
# plus ou moins, et l'allemand remplit presque tout.
ROWS = [
    ("SOUS-TITRES — FR", 176, "#f1f5f9", "#e2e8f0", "#64748b", 0.72),
    ("SOUS-TITRES — EN", 226, "#eff6ff", "#dbeafe", "#1d4ed8", 0.56),
    ("SOUS-TITRES — DE", 276, "#fffbeb", "#fde68a", "#b45309", 0.88),
]

for label, y, fill, stroke, color, factor in ROWS:
    text(56, y + 6, label, 9, True, color)
    for i, (a, b, dur) in enumerate(bounds()):
        bw = b - a - 2
        r(a + 1, y, bw, 26, fill, stroke, 4, 1)
        inner = bw - 12
        r(a + 6, y + 5, inner, 16, "#ffffff", None, 3)
        r(a + 6, y + 5, max(8, inner * factor), 16, color, None, 3)

# ── mise en evidence du segment 3 ───────────────────────────────────────────
a3, b3, d3 = bounds()[2]
budget = int(d3 * 15)
cy = 276
r(a3 + 1, cy - 4, b3 - a3 - 2, 34, None, "#b45309", 6, 2)
text(a3 + 4, cy - 24, f"{d3} s × 15 car/s = {budget} caractères max", 8.5, True, "#b45309")
text(X1 - 4, 320, "L'allemand reçoit ~30 % de caractères en plus à durée égale :", 8.5, False, MUTED, anchor="ra")
text(X1 - 4, 333, "c'est lui qui contraint le générateur.", 8.5, False, MUTED, anchor="ra")

# ── legende ─────────────────────────────────────────────────────────────────
text(56, 366, "Les barres figurent le texte affiché. Le budget de caractères dépend de la durée du segment,",
     9, False, MUTED)
text(56, 380, "pas de la longueur de la phrase d'origine : au-delà de 17 car/s, le spectateur saute le bloc.",
     9, False, MUTED)
text(56, 404, "FR = transcription fidèle (accessibilité) · EN / DE = résumés traduits, réécrits plus courts.",
     8.5, False, "#94a3b8")

Path("docs").mkdir(exist_ok=True)
img.resize((W * 2, H * 2), Image.LANCZOS).save("docs/subtitles.png")
print("ecrit: docs/subtitles.png")
