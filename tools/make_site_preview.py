#!/usr/bin/env python3
"""Rendu haute fidelite de la page d'accueil du site (desktop 1440).

Contenu reel : depeches du 5 novembre 2026. Aucune photo tierce : les vignettes
sont des aplats typographiques, comme dans les cartes video.

Sortie : docs/site.png
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1440, 2040
FONT = Path(r"C:\Windows\Fonts")
SANS = FONT / "segoeui.ttf"
SANS_B = FONT / "segoeuib.ttf"
SANS_SB = FONT / "seguisb.ttf" if (FONT / "seguisb.ttf").exists() else FONT / "segoeuib.ttf"
SERIF = FONT / "georgia.ttf"
SERIF_B = FONT / "georgiab.ttf"

# Deux jeux de jetons. Le passage a un theme ne change aucune geometrie :
# seules les couleurs bougent, donc les deux rendus restent superposables.
THEMES = {
    "light": dict(
        bg="#FBFAF7", surface="white", ink="#17181A", muted="#6B6F76",
        line="#E6E3DD", accent="#9F1239", soft="#F3F1EC", dark="#121316",
        sub="#3F4147", faint="#9A9EA6", src="#4B4E55",
        ad_bg="#FFFBEB", ad_border="#F59E0B", ad_ink="#92400E", ad_ink2="#B45309",
        band_muted="#A8AFB8", band_chip="#1E2126", band_chip_border="#2E333A",
        band_chip_ink="#D5DAE1", band_border="#2A3B3F",
    ),
    "dark": dict(
        bg="#0D0E10", surface="#16181C", ink="#F4F3F0", muted="#9198A1",
        line="#262A30", accent="#FB7185", soft="#1B1E23", dark="#08090B",
        sub="#B9BFC8", faint="#6E757E", src="#AEB5BE",
        ad_bg="#241C0B", ad_border="#B45309", ad_ink="#FCD34D", ad_ink2="#F59E0B",
        band_muted="#9AA3AD", band_chip="#22262C", band_chip_border="#2F353D",
        band_chip_ink="#D7DCE3", band_border="#2C3238",
    ),
}
THEME = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--theme=")), "light")
C = THEMES[THEME]
BG, INK, MUTED = C["bg"], C["ink"], C["muted"]
LINE, ACCENT, SOFT, DARK = C["line"], C["accent"], C["soft"], C["dark"]

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
_f: dict = {}


def font(size, path=SANS):
    k = (size, path)
    if k not in _f:
        _f[k] = ImageFont.truetype(str(path), int(size))
    return _f[k]


def text(x, y, s, size=14, path=SANS, color=INK, anchor="la"):
    d.text((x, y), s, font=font(size, path), fill=color, anchor=anchor)


def wrap(x, y, s, size, maxw, path=SANS, color=INK, lead=1.32, maxlines=3):
    f = font(size, path)
    words, lines, cur = s.split(), [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if f.getlength(cand) <= maxw or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > maxlines:
        lines = lines[:maxlines]
        while f.getlength(lines[-1] + "…") > maxw and len(lines[-1]) > 4:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    for i, ln in enumerate(lines):
        text(x, y + i * size * lead, ln, size, path, color)
    return y + len(lines) * size * lead


def rrect(x, y, w, h, fill, stroke=None, r=10, sw=1):
    d.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=fill, outline=stroke, width=sw)


def hline(x, y, w, color=LINE):
    d.line([(x, y), (x + w, y)], fill=color, width=1)


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def thumb(x, y, w, h, hue, code, r=8, corners=(True, True, True, True)):
    """Vignette typographique : degrade + code pays en filigrane.

    Construite à part puis collée avec un masque arrondi : dessiner le dégradé
    directement sur la page écrasait les coins arrondis de la carte.
    """
    base = hex2rgb(hue)
    tile = Image.new("RGB", (w, h))
    td = ImageDraw.Draw(tile)
    for i in range(h):
        t = i / max(1, h - 1)
        c = tuple(int(base[k] * (0.55 + 0.45 * t)) for k in range(3))
        td.line([(0, i), (w, i)], fill=c)
    size = min(120, h * 0.58)
    f = font(size, SERIF_B)
    while f.getlength(code) > w * 0.78 and size > 18:
        size -= 3
        f = font(size, SERIF_B)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).text((w / 2, h / 2), code, font=f,
                                 fill=(255, 255, 255, 64), anchor="mm")
    tile = Image.alpha_composite(tile.convert("RGBA"), overlay).convert("RGB")

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=r,
                                           fill=255, corners=corners)
    img.paste(tile, (x, y), mask)


def chip(x, y, label, active=False, h=30):
    f = font(12.5, SANS_SB)
    w = int(f.getlength(label) + 28)
    if active:
        rrect(x, y, w, h, INK, None, h // 2)
        text(x + 14, y + h / 2, label, 12.5, SANS_SB, C["bg"], anchor="lm")
    else:
        rrect(x, y, w, h, C["surface"], LINE, h // 2)
        text(x + 14, y + h / 2, label, 12.5, SANS_SB, MUTED, anchor="lm")
    return w


def badge(x, y, label, fill, fg, size=11):
    f = font(size, SANS_SB)
    w = int(f.getlength(label) + 20)
    rrect(x, y, w, 22, fill, None, 11)
    text(x + 10, y + 11, label, size, SANS_SB, fg, anchor="lm")
    return w


M = 72           # marge
CW = W - 2 * M   # largeur utile = 1296

# ═══════════════════════════════════════════════════════════════════════════
# En-tete
# ═══════════════════════════════════════════════════════════════════════════
text(M, 30, "Le Fil", 26, SERIF_B, INK)
d.rectangle([M + 78, 34, M + 79, 58], fill=ACCENT)
text(M + 90, 40, "l'actualité mondiale, source par source", 12.5, SANS, MUTED)

navx = 520
for item, act in (("Fil", True), ("Carte", False), ("Résumé", False),
                  ("Vidéos", False), ("Suivre", False)):
    text(navx, 40, item, 14, SANS_SB if act else SANS, INK if act else MUTED)
    if act:
        d.rectangle([navx, 61, navx + 18, 63], fill=ACCENT)
    navx += int(font(14, SANS).getlength(item)) + 34

rrect(W - M - 318, 30, 248, 34, C["surface"], LINE, 17)
text(W - M - 300, 47, "Rechercher un pays, un thème…", 12, SANS, C["faint"], anchor="lm")

lx = W - M - 62
rrect(lx, 30, 62, 34, SOFT, LINE, 17)
text(lx + 14, 47, "FR", 12.5, SANS_SB, INK, anchor="lm")
d.polygon([(lx + 40, 44), (lx + 50, 44), (lx + 45, 50)], fill=MUTED)

hline(M, 84, CW)
text(M, 96, "Jeudi 5 novembre 2026", 12, SANS_SB, MUTED)
text(M + 170, 96, "·", 12, SANS, MUTED)
text(M + 186, 96, "fil mis à jour il y a 2 min", 12, SANS, MUTED)
text(W - M, 96, "4 812 événements suivis · 65 rédactions", 12, SANS, MUTED, anchor="ra")

# ═══════════════════════════════════════════════════════════════════════════
# La une
# ═══════════════════════════════════════════════════════════════════════════
HY = 140
big_w = 830
HERO_H = 460
rrect(M, HY, big_w, HERO_H, C["surface"], LINE, 12)

# visuel de une
TH = 236
thumb(M + 1, HY + 1, big_w - 2, TH, "#1D4ED8", "FR", 11, (True, True, False, False))
badge(M + 18, HY + 18, "À LA UNE", ACCENT, "#FFFFFF", 10.5)
badge(M + big_w - 210, HY + 18, "épinglé · expire dans 6 h", C["ad_bg"], C["ad_ink"], 10.5)

text(M + 24, HY + TH + 18, "FRANCE", 11.5, SANS_SB, ACCENT)
y = wrap(M + 24, HY + TH + 40,
         "Grève du 5 novembre : les syndicats rejoignent le mouvement",
         31, big_w - 48, SERIF_B, INK, 1.24, 2)
y = wrap(M + 24, y + 10,
         "Entre 575 000 et 1,6 million de manifestants selon les sources. "
         "Quatre rédactions, quatre chiffres : voilà pourquoi on les affiche côte à côte.",
         14.5, big_w - 220, SANS, C["sub"], 1.45, 2)
text(M + 24, HY + HERO_H - 34, "Le Monde · France 24 · BBC · DW", 12, SANS_SB, MUTED)
text(M + big_w - 24, HY + HERO_H - 34, "il y a 12 min", 12, SANS, MUTED, anchor="ra")

# deux secondaires
sx = M + big_w + 26
sw = CW - big_w - 26
for i, (kicker, titre, hue, code, n, quand) in enumerate([
    ("EUROPE", "Le ciel européen en alerte après des menaces", "#0F766E", "EU", 3, "il y a 26 min"),
    ("ÉTATS-UNIS", "Midterms : la carte politique rebattue", "#4338CA", "US", 3, "il y a 1 h"),
]):
    cy = HY + i * 240
    rrect(sx, cy, sw, 220, C["surface"], LINE, 12)
    thumb(sx + 1, cy + 1, 150, 218, hue, code, 11, (True, False, False, True))
    tx = sx + 170
    text(tx, cy + 22, kicker, 10.5, SANS_SB, hex2rgb(hue))
    wrap(tx, cy + 42, titre, 17.5, sw - 190, SERIF_B, INK, 1.28, 3)
    text(tx, cy + 186, f"{n} rédactions · {quand}", 11.5, SANS, MUTED)

# ═══════════════════════════════════════════════════════════════════════════
# Le Resume du jour
# ═══════════════════════════════════════════════════════════════════════════
RY = 640
rrect(M, RY, CW, 196, DARK, C["band_border"], 14)
text(M + 28, RY + 24, "LE RÉSUMÉ DU JOUR", 11, SANS_SB, "#5EEAD4")

# poster 16:9
pw, ph = 268, 151
px, py = M + 28, RY + 46
for i in range(ph):
    t = i / ph
    d.line([(px, py + i), (px + pw, py + i)],
           fill=(int(11 + 10 * t), int(44 + 14 * t), int(48 + 18 * t)))
rrect(px, py, pw, ph, None, C["band_border"], 8)
d.ellipse([px + pw / 2 - 22, py + ph / 2 - 22, px + pw / 2 + 22, py + ph / 2 + 22], fill=(94, 234, 212))
d.polygon([(px + pw / 2 - 6, py + ph / 2 - 10), (px + pw / 2 - 6, py + ph / 2 + 10),
           (px + pw / 2 + 11, py + ph / 2)], fill=DARK)
text(px + pw - 10, py + ph - 10, "4 min 12", 10.5, SANS_SB, "#CBD5E1", anchor="rb")

tx = px + pw + 28
wrap(tx, RY + 52, "Ce qui s'est passé dans le monde aujourd'hui",
     22, 620, SERIF_B, "#FFFFFF", 1.25, 2)
text(tx, RY + 118, "Six événements, quatre langues de sources, une voix.", 13, SANS, C["band_muted"])

chx = tx
for c in ("France", "Europe", "États-Unis", "+3"):
    f = font(11.5, SANS_SB)
    cw = int(f.getlength(c) + 22)
    rrect(chx, RY + 146, cw, 26, C["band_chip"], C["band_chip_border"], 13)
    text(chx + 11, RY + 159, c, 11.5, SANS_SB, C["band_chip_ink"], anchor="lm")
    chx += cw + 8

rrect(W - M - 168, RY + 132, 140, 40, "#FFFFFF", None, 20)
text(W - M - 98, RY + 152, "Écouter", 13.5, SANS_SB, DARK, anchor="mm")

# ═══════════════════════════════════════════════════════════════════════════
# Filtres
# ═══════════════════════════════════════════════════════════════════════════
FY = 866
text(M, FY + 8, "Le fil du monde", 21, SERIF_B, INK)
text(M + 178, FY + 13, "· 1 284 événements sur 48 h", 12.5, SANS, MUTED)

cx = M
for c in ("Monde", "Afrique", "Maghreb", "Europe", "Asie", "Amériques", "+ tous les thèmes"):
    cx += chip(cx, FY + 44, c, active=(c == "Monde")) + 8

# ═══════════════════════════════════════════════════════════════════════════
# Le fil : cartes
# ═══════════════════════════════════════════════════════════════════════════
CARDS = [
    ("MAROC", "Vigilance face à la menace terroriste", "#9F1239", "MA",
     ["Hespress"], "il y a 22 min"),
    ("PARAGUAY", "Le président Peña démissionne après un scandale bancaire", C["ad_ink2"], "PY",
     ["France 24"], "il y a 1 h"),
    ("COP31", "Le financement de l'adaptation jugé « ahurissant » par l'ONU", "#15803D", "COP",
     ["France 24"], "il y a 2 h"),
    ("CALIFORNIE", "548 peines de mort commuées par le gouverneur", "#4338CA", "US",
     ["BBC", "DW"], "il y a 25 min"),
    ("FRANCE", "Grève du 5 novembre : la mobilisation en chiffres", "#1D4ED8", "FR",
     ["Le Monde", "BBC", "France 24"], "il y a 3 h"),
    ("PROCHE-ORIENT", "Démolitions à Biddu : plus de 100 déplacés", "#0F766E", "ME",
     ["Al Jazeera"], "il y a 40 min"),
]

col_w = (CW - 2 * 27) // 3
CH = 344
for i, (kicker, titre, hue, code, srcs, quand) in enumerate(CARDS):
    row, col = divmod(i, 3)
    gx = M + col * (col_w + 27)
    gy = 970 + row * (CH + 27)
    rrect(gx, gy, col_w, CH, C["surface"], LINE, 12)
    thumb(gx + 1, gy + 1, col_w - 2, 168, hue, code, 11, (True, True, False, False))
    text(gx + 18, gy + 186, kicker, 10.5, SANS_SB, hex2rgb(hue))
    y = wrap(gx + 18, gy + 206, titre, 17, col_w - 36, SERIF_B, INK, 1.3, 3)
    text(gx + 18, gy + CH - 46, " · ".join(srcs), 11.5, SANS_SB, C["src"])
    text(gx + col_w - 18, gy + CH - 46, quand, 11.5, SANS, MUTED, anchor="ra")
    n = len(srcs)
    label = "1 rédaction" if n == 1 else f"{n} rédactions"
    bw2 = badge(gx + col_w - 18 - 96, gy + 182, label, SOFT, MUTED, 10)

# ═══════════════════════════════════════════════════════════════════════════
# Emplacement publicitaire
# ═══════════════════════════════════════════════════════════════════════════
AY = 970 + 2 * (CH + 27) + 6
rrect(M, AY, CW, 132, C["ad_bg"], C["ad_border"], 10, 1)
text(W / 2, AY + 52, "PUBLICITÉ · 970 × 250", 15, SANS_SB, C["ad_ink"], anchor="ma")
text(W / 2, AY + 76, "hauteur réservée · se remplit sans décaler la page",
     11.5, SANS, C["ad_ink2"], anchor="ma")

# ═══════════════════════════════════════════════════════════════════════════
# Pied
# ═══════════════════════════════════════════════════════════════════════════
PY = AY + 168
hline(M, PY, CW)
text(M, PY + 22, "Le Fil", 17, SERIF_B, INK)
text(M, PY + 50, "Agrégateur d'actualité mondiale — FR · EN · DE · ES · IT", 11.5, SANS, MUTED)
text(M, PY + 70, "Les sources arabophones sont reformulées, jamais traduites mot à mot.", 11.5, SANS, MUTED)

for i, (t, links) in enumerate([
    ("Le site", ["Fil", "Carte", "Résumé", "Vidéos"]),
    ("À propos", ["Éthique", "Corrections", "Financement", "Retrait"]),
    ("Légal", ["CGU", "Confidentialité", "Cookies", "ads.txt"]),
]):
    lx2 = M + 640 + i * 230
    text(lx2, PY + 22, t, 11.5, SANS_SB, INK)
    for j, l in enumerate(links):
        text(lx2, PY + 44 + j * 19, l, 11.5, SANS, MUTED)

out = Path("docs")
out.mkdir(exist_ok=True)
name = "site-dark.png" if THEME == "dark" else "site.png"
tmp = out / ("_tmp-" + name)
img.save(tmp)
try:
    tmp.replace(out / name)
    written = name
except OSError:
    # le fichier est ouvert dans un lecteur : on ecrit a cote plutot que d'echouer
    alt = name.replace(".png", "-v2.png")
    tmp.replace(out / alt)
    written = alt
print(f"ecrit: docs/{written}", img.size)
