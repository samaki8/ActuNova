#!/usr/bin/env python3
"""Genere le schema d'architecture cible (PNG @2x + SVG) depuis une seule
description de layout. Deux backends de dessin partagent les memes primitives.

Usage: python tools/make_diagram.py
Sortie: docs/pipeline.png, docs/pipeline.svg
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1240, 800
S = 2  # supersampling

FONT_DIR = Path(r"C:\Windows\Fonts")
REG = FONT_DIR / "segoeui.ttf"
BOLD = FONT_DIR / "segoeuib.ttf"
if not REG.exists():
    REG, BOLD = FONT_DIR / "arial.ttf", FONT_DIR / "arialbd.ttf"

C_INK = "#0f172a"
C_MUTED = "#64748b"
C_LABEL = "#94a3b8"
C_LINE = "#94a3b8"
C_BG = "#ffffff"

THEMES = {
    "collect": ("#eff6ff", "#bfdbfe", "#1d4ed8"),
    "process": ("#f5f3ff", "#ddd6fe", "#6d28d9"),
    "site": ("#ecfdf5", "#a7f3d0", "#047857"),
    "video": ("#fdf2f8", "#fbcfe8", "#be185d"),
    "store": ("#f8fafc", "#e2e8f0", "#334155"),
}


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float
    title: str
    sub: str = ""
    theme: str = "process"


@dataclass
class Layout:
    boxes: list = field(default_factory=list)
    lines: list = field(default_factory=list)   # (points, arrow_end)
    labels: list = field(default_factory=list)  # (x, y, text)
    pills: list = field(default_factory=list)
    titles: list = field(default_factory=list)


def wrap(text: str, font, max_w: float) -> list[str]:
    words, out, cur = text.split(), [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if font.getlength(cand) <= max_w or not cur:
            cur = cand
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


class Base:
    def __init__(self):
        self.reset()

    def reset(self):
        raise NotImplementedError

    def rrect(self, x, y, w, h, r, fill, stroke, sw=1.5):
        raise NotImplementedError

    def line(self, pts, color=C_LINE, sw=1.6, arrow=True):
        raise NotImplementedError

    def text(self, x, y, s, size, bold=False, color=C_INK, anchor="la", max_w=None):
        raise NotImplementedError


class PILBackend(Base):
    def reset(self):
        self.img = Image.new("RGB", (W * S, H * S), C_BG)
        self.d = ImageDraw.Draw(self.img)
        self._fonts = {}

    def font(self, size, bold):
        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype(str(BOLD if bold else REG), int(size * S))
        return self._fonts[key]

    def rrect(self, x, y, w, h, r, fill, stroke, sw=1.5):
        self.d.rounded_rectangle(
            [x * S, y * S, (x + w) * S, (y + h) * S],
            radius=r * S, fill=fill, outline=stroke, width=max(1, int(sw * S)),
        )

    def line(self, pts, color=C_LINE, sw=1.6, arrow=True):
        p = [(px * S, py * S) for px, py in pts]
        self.d.line(p, fill=color, width=max(1, int(sw * S)), joint="curve")
        if arrow:
            (x1, y1), (x2, y2) = p[-2], p[-1]
            a = math.atan2(y2 - y1, x2 - x1)
            L, wd = 9 * S, 4.2 * S
            tip = (x2, y2)
            b1 = (x2 - L * math.cos(a) + wd * math.sin(a), y2 - L * math.sin(a) - wd * math.cos(a))
            b2 = (x2 - L * math.cos(a) - wd * math.sin(a), y2 - L * math.sin(a) + wd * math.cos(a))
            self.d.polygon([tip, b1, b2], fill=color)

    def text(self, x, y, s, size, bold=False, color=C_INK, anchor="la", max_w=None):
        f = self.font(size, bold)
        if max_w:
            lines = wrap(s, f, max_w * S)
            for i, ln in enumerate(lines):
                self.d.text((x * S, (y + i * size * 1.28) * S), ln, font=f, fill=color, anchor=anchor)
            return len(lines)
        self.d.text((x * S, y * S), s, font=f, fill=color, anchor=anchor)
        return 1

    def save(self, path):
        self.img.resize((W * 2, H * 2), Image.LANCZOS).save(path)


class SVGBackend(Base):
    def reset(self):
        self.parts = []

    def rrect(self, x, y, w, h, r, fill, stroke, sw=1.5):
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def line(self, pts, color=C_LINE, sw=1.6, arrow=True):
        d = " ".join(("M" if i == 0 else "L") + f"{px},{py}" for i, (px, py) in enumerate(pts))
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
                          f'stroke-linejoin="round"/>')
        if arrow:
            self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
                              f'marker-end="url(#ah)"/>')

    def text(self, x, y, s, size, bold=False, color=C_INK, anchor="la", max_w=None):
        weight = ' font-weight="600"' if bold else ""
        ta = ' text-anchor="middle"' if str(anchor).startswith("m") else ""
        if max_w:
            n = max(8, int(max_w / (size * 0.52)))
            words, lines, cur = s.split(), [], ""
            for w in words:
                cand = f"{cur} {w}".strip()
                if len(cand) <= n or not cur:
                    cur = cand
                else:
                    lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            for i, ln in enumerate(lines):
                self.parts.append(
                    f'<text x="{x}" y="{y + i * size * 1.28 + size * 0.8:.1f}" font-size="{size}" '
                    f'fill="{color}"{weight}{ta} font-family="Segoe UI, Inter, system-ui, sans-serif">{ln}</text>'
                )
            return len(lines)
        self.parts.append(
            f'<text x="{x}" y="{y + size * 0.8:.1f}" font-size="{size}" fill="{color}"{weight}{ta} '
            f'font-family="Segoe UI, Inter, system-ui, sans-serif">{s}</text>'
        )
        return 1

    def save(self, path):
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="{C_BG}"/>'
            "<defs><marker id=\"ah\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" "
            "markerWidth=\"7\" markerHeight=\"7\" orient=\"auto-start-reverse\">"
            f'<path d="M0,0 L10,5 L0,10 z" fill="{C_LINE}"/></marker></defs>'
        )
        Path(path).write_text(head + "".join(self.parts) + "</svg>", encoding="utf-8")


def build() -> Layout:
    L = Layout()

    L.titles = [
        (40, 30, "Plateforme d'actualité mondiale", 21, True),
        (40, 62, "Architecture cible · du flux RSS à la vidéo publiée · interface bilingue FR/EN", 12, False),
    ]

    # --- rangee 1 : collecte & traitement --------------------------------
    y1, h1 = 132, 76
    x1 = [68, 292, 516, 740, 964]
    row1 = [
        ("Sources", "30+ flux RSS · Atom · RDF", "collect"),
        ("Ingestion", "ETag · backoff · 1 requête/domaine", "collect"),
        ("Normalisation", "URL canonique · langue · UTC · 150 car.", "process"),
        ("Déduplication + clustering", "simhash · cosine 0,82 · fenêtre 72 h", "process"),
        ("Ranking", "fraîcheur · étendue · autorité", "process"),
    ]
    for x, (t, s, th) in zip(x1, row1):
        L.boxes.append(Box(x, y1, 196, h1, t, s, th))
    for i in range(len(x1) - 1):
        L.lines.append(([(x1[i] + 196, y1 + h1 / 2), (x1[i + 1] - 6, y1 + h1 / 2)], True))

    L.labels.append((56, 112, "1 · COLLECTE & TRAITEMENT", 10, True))

    # --- bus de distribution (le ranking alimente les deux branches) -----
    bus_x = 36
    rank_cx = x1[-1] + 196 / 2
    L.lines.append(([(rank_cx, y1 + h1), (rank_cx, 222), (bus_x, 222), (bus_x, 368)], False))
    L.lines.append(([(bus_x, 368), (66, 368)], True))
    L.lines.append(([(bus_x, 368), (bus_x, 538), (66, 538)], True))

    # --- rangee 2 : site public -----------------------------------------
    y2, h2 = 330, 76
    x2 = x1
    w2 = 196
    row2 = [
        ("API /v1", "REST · curseur · cache 60 s", "site"),
        ("Web Next.js", "carte + fil · FR/EN", "site"),
        ("Section vidéo", "16:9 · sous-titres · sources", "site"),
        ("Comptes", "régions · thèmes suivis", "site"),
        ("Newsletter", "digest quotidien bilingue", "site"),
    ]
    for x, (t, s, th) in zip(x2, row2):
        L.boxes.append(Box(x, y2, w2, h2, t, s, th))
    for i in range(len(x2) - 1):
        L.lines.append(([(x2[i] + w2, y2 + h2 / 2), (x2[i + 1] - 6, y2 + h2 / 2)], True))
    L.labels.append((56, 306, "2 · SITE PUBLIC", 10, True))

    # --- rangee 3 : usine video -----------------------------------------
    y3, h3 = 500, 76
    row3 = [
        ("Sélection", "3-5 événements/jour", "video"),
        ("Script", "LLM contraint · claims sourcés", "video"),
        ("Voix", "TTS neural · timings par mot", "video"),
        ("Rendu", "Remotion · 1080x1920 · 30 fps", "video"),
        ("Publication", "idempotent · 1 état/plateforme", "video"),
    ]
    for x, (t, s, th) in zip(x1, row3):
        L.boxes.append(Box(x, y3, 196, h3, t, s, th))
    for i in range(len(x1) - 1):
        L.lines.append(([(x1[i] + 196, y3 + h3 / 2), (x1[i + 1] - 6, y3 + h3 / 2)], True))
    L.labels.append((56, 476, "3 · USINE VIDÉO", 10, True))

    # la meme video alimente la rubrique du site (rendu 16:9)
    L.lines.append(([(x1[3] + 98, y3), (x1[3] + 98, 452), (x1[2] + 98, 452),
                     (x1[2] + 98, y2 + h2 + 4)], True))

    # --- plateformes ----------------------------------------------------
    py, ph, pw, gap = 648, 32, 132, 10
    px0 = 1160 - (4 * pw + 3 * gap)
    centers = []
    for i, name in enumerate(["YouTube Shorts", "TikTok", "Instagram Reels", "X"]):
        x = px0 + i * (pw + gap)
        L.pills.append((x, py, pw, ph, name))
        centers.append(x + pw / 2)
    pub_cx = x1[-1] + 196 / 2
    L.lines.append(([(pub_cx, y3 + h3), (pub_cx, 622), (centers[0], 622)], False))
    L.lines.append(([(centers[0], 622), (centers[-1], 622)], False))
    for cx in centers:
        L.lines.append(([(cx, 622), (cx, py - 4)], True))

    return L


def render(b: Base) -> None:
    L = build()

    for x, y, s, size, bold in L.titles:
        b.text(x, y, s, size, bold, C_INK if bold else C_MUTED)

    for x, y, s, size, bold in L.labels:
        b.text(x, y, s, size, True, C_LABEL)

    for ln in L.lines:
        pts, arrow = ln
        b.line(pts, C_LINE, 1.6, arrow)

    for box in L.boxes:
        fill, stroke, title_c = THEMES[box.theme]
        b.rrect(box.x, box.y, box.w, box.h, 10, fill, stroke, 1.4)
        b.text(box.x + 14, box.y + 13, box.title, 12.5, True, title_c, max_w=box.w - 26)
        b.text(box.x + 14, box.y + 39, box.sub, 9.6, False, C_MUTED, max_w=box.w - 26)

    for x, y, w, h, name in L.pills:
        b.rrect(x, y, w, h, 16, "#ffffff", "#e2e8f0", 1.2)
        b.text(x + w / 2, y + 10, name, 9.5, True, C_INK, anchor="ma" if False else "ma")

    # bandeau stockage
    b.rrect(68, 712, 1104, 52, 10, THEMES["store"][0], THEMES["store"][1], 1.2)
    b.text(88, 722, "État partagé", 10.5, True, THEMES["store"][2])
    b.text(88, 739, "PostgreSQL 16 + pgvector (relationnel · vecteurs · plein texte)   ·   Redis (cache, verrous)   ·   S3/R2 (vidéos, sauvegardes)", 9.8, False, C_MUTED)


def main() -> None:
    Path("docs").mkdir(exist_ok=True)
    pil = PILBackend()
    render(pil)
    pil.save("docs/pipeline.png")

    svg = SVGBackend()
    render(svg)
    svg.save("docs/pipeline.svg")
    print("ecrit: docs/pipeline.png, docs/pipeline.svg")


if __name__ == "__main__":
    main()
