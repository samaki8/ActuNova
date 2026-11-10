#!/usr/bin/env python3
"""Demonstration : un bulletin de 10 cartes a partir de depeches reelles.

Etape 1  python tools/demo_deck.py --emit      -> ecrit docs/demo/segments.json
Etape 2  (PowerShell) synthese vocale des segments -> WAV
Etape 3  python tools/demo_deck.py --render    -> cartes PNG + listes de concat
Etape 4  (ffmpeg) assemblage

Les titres sont reels (BBC, France 24, Le Monde, Al Jazeera, DW, Hespress,
releves le 5 novembre 2026). Les cartes sont ecrites a la main : c'est le travail
editorial qu'on ne confie pas encore au LLM.
"""
from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import geo_silhouette as geo

W, H, S = 1080, 1920, 1
OUT = Path("docs/demo")
FONT_DIR = Path(r"C:\Windows\Fonts")
REG = FONT_DIR / "segoeui.ttf"
BOLD = FONT_DIR / "segoeuib.ttf"
SEMI = FONT_DIR / "seguisb.ttf"
if not SEMI.exists():
    SEMI = BOLD

WHITE = "#ffffff"
DIM = "#94a3b8"

_d: dict = {}


def font(size, path=BOLD):
    k = (size, path)
    if k not in _d:
        _d[k] = ImageFont.truetype(str(path), int(size))
    return _d[k]


# ── le plateau ──────────────────────────────────────────────────────────────
# hue = teinte de fond par evenement ; accent = couleur du kicker
DECK = [
    dict(kind="text", hue="#0e7490", accent="#67e8f9",
         kicker="LE RÉSUMÉ",
         lines=["Jeudi 5", "novembre 2026"],
         source="6 événements · 1 min",
         say="Le résumé de l'actualité mondiale du jeudi cinq novembre."),

    dict(kind="text", hue="#1d4ed8", accent="#93c5fd",
         kicker="FRANCE",
         lines=["Grève : les", "syndicats", "rejoignent"],
         source="Le Monde · France 24 · BBC",
         say="En France, la grève prend de l'ampleur. Les syndicats ont rejoint le mouvement."),

    dict(kind="number", hue="#1d4ed8", accent="#93c5fd",
         kicker="FRANCE",
         number="575 000",
         label="manifestants, selon la CGT",
         source="Le Monde · France 24",
         say="Entre cinq cent soixante-quinze mille et un million six cent mille manifestants, selon les sources."),

    dict(kind="text", hue="#0f766e", accent="#5eead4",
         kicker="EUROPE",
         lines=["Vingt vols visés", "par des alertes"],
         source="BBC · Le Monde · France 24",
         say="En Europe, une vingtaine de vols commerciaux ont été visés par des alertes à la bombe."),

    dict(kind="text", hue="#4338ca", accent="#a5b4fc",
         kicker="ÉTATS-UNIS",
         lines=["Midterms : la", "carte politique", "rebattue"],
         source="Al Jazeera · DW",
         say="Aux États-Unis, les élections de mi-mandat rebattent la carte politique."),

    dict(kind="number", hue="#4338ca", accent="#a5b4fc",
         kicker="CALIFORNIE",
         number="548",
         label="peines de mort commuées",
         source="BBC · DW",
         say="En Californie, le gouverneur a commué cinq cent quarante-huit peines de mort."),

    dict(kind="text", hue="#b45309", accent="#fcd34d",
         kicker="PARAGUAY",
         lines=["Le président", "démissionne"],
         source="France 24",
         say="Au Paraguay, le président Santiago Peña démissionne après un scandale bancaire."),

    dict(kind="text", hue="#15803d", accent="#86efac",
         kicker="COP31",
         lines=["Le financement", "de l'adaptation", "manque"],
         source="France 24",
         say="À la COP trente et un, l'ONU juge le déficit de financement de l'adaptation ahurissant."),

    dict(kind="text", hue="#9f1239", accent="#fda4af",
         kicker="MAROC",
         lines=["Vigilance face", "à la menace"],
         source="Hespress",
         say="Au Maroc, le ministère de l'Intérieur appelle à la vigilance face à la menace terroriste."),

    dict(kind="text", hue="#334155", accent="#cbd5e1",
         kicker="LE FIL",
         lines=["Chaque événement,", "source par source"],
         source="lefil.example",
         say="C'était le résumé. Chaque événement, source par source, sur le site."),
]


# Fond par defaut : le degrade. La silhouette de pays n'est pas activee (le
# rendu obtenu n'etait pas convaincant). Des qu'une image est deposee dans
# docs/demo/backgrounds/cardNN.jpg, elle est utilisee a la place — et c'est le
# chemin normal : les visuels se choisissent a la main.
GEO_MAP = {i: (None, None) for i in range(1, 11)}
for _i, _c in enumerate(DECK, 1):
    _c["geo"], _c["geo_bbox"] = GEO_MAP[_i]


def hex2rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def darken(rgb, f: float):
    return tuple(int(c * f) for c in rgb)


def gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return img


def cover(img: Image.Image, size) -> Image.Image:
    """Recadre l'image pour couvrir exactement la taille demandee."""
    w, h = img.size
    W2, H2 = size
    s = max(W2 / w, H2 / h)
    img = img.resize((int(w * s) + 1, int(h * s) + 1), Image.LANCZOS)
    left, top = (img.width - W2) // 2, (img.height - H2) // 2
    return img.crop((left, top, left + W2, top + H2))


def draw_card(card: dict, index: int, total: int) -> Image.Image:
    hue = hex2rgb(card["hue"])

    # ── fond : image si elle existe, sinon degrade ─────────────────────────
    bg_file = next(
        (p for p in (OUT / "backgrounds" / f"card{index + 1:02d}.jpg",
                     OUT / "backgrounds" / f"card{index + 1:02d}.png") if p.exists()),
        None,
    )
    if bg_file:
        img = cover(Image.open(bg_file).convert("RGB"), (W, H))
        # voile : assombrit uniformement, puis degrade vers la droite pour que
        # le texte reste lisible quel que soit le cliche
        veil = Image.new("RGBA", (W, H), (8, 10, 14, 120))
        for x in range(0, W):
            a = int(150 * (1 - x / W) ** 1.1)
            ImageDraw.Draw(veil).line([(x, 0), (x, H)], fill=(6, 9, 13, a))
        img = Image.alpha_composite(img.convert("RGBA"), veil).convert("RGB")
    else:
        img = gradient((W, H), (10, 12, 16), darken(hue, 0.55))

    d = ImageDraw.Draw(img)

    # barre de progression, tout en haut (hors zone utile)
    seg = W / total
    d.rectangle([0, 0, W, 8], fill=(255, 255, 255, 26))
    d.rectangle([index * seg, 0, (index + 1) * seg, 8], fill=hex2rgb(card["accent"]))

    # filet vertical d'accent : dessine apres le contenu, pour qu'il s'arrete
    # avec le bloc de texte et ne flotte pas dans le vide

    x = 104
    kicker_f = font(38, SEMI)
    d.text((x, 520), card["kicker"], font=kicker_f, fill=hex2rgb(card["accent"]))

    if card["kind"] == "number":
        num_f = font(190, BOLD)
        d.text((x, 600), card["number"], font=num_f, fill=WHITE)
        d.text((x, 600 + 210), card["label"], font=font(44, REG), fill=DIM)
        y_src = 600 + 210 + 90
    else:
        f = font(92, BOLD)
        y = 620
        for line in card["lines"]:
            d.text((x, y), line, font=f, fill=WHITE)
            y += 112
        y_src = y + 26

    d.text((x, y_src), card["source"], font=font(34, REG), fill=DIM)
    d.rectangle([56, 496, 62, y_src + 46], fill=darken(hue, 1.5))

    # signature discrete sous le bloc (dans la zone utile)
    d.text((x, 1500), "Le Fil", font=font(28, SEMI), fill=darken(hex2rgb(card["accent"]), 0.75))
    return img


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--render"
    OUT.mkdir(parents=True, exist_ok=True)

    if mode == "--emit":
        segs = [c["say"] for c in DECK]
        (OUT / "segments.json").write_text(
            json.dumps(segs, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"ecrit: {OUT/'segments.json'} ({len(segs)} segments)")
        return

    cards_dir = OUT / "cards"
    cards_dir.mkdir(exist_ok=True)
    audio_dir = OUT / "audio"

    if not audio_dir.exists():
        audio_dir.mkdir(parents=True, exist_ok=True)
        print("note : pas d'audio synthetise, le timing suit la longueur du texte")

    total = len(DECK)
    concat, storyboard = [], []
    t = 0.0
    for i, card in enumerate(DECK):
        img = draw_card(card, i, total)
        p = cards_dir / f"card{i + 1:02d}.png"
        img.save(p)

        # la duree suit la longueur du texte parle (~15 caracteres/seconde),
        # et non l'audio : la synthese vocale n'est pas disponible ici.
        wav = audio_dir / f"seg{i + 1:02d}.wav"
        if wav.exists():
            dur = wav_duration(wav) + 0.35
        else:
            dur = min(7.5, max(2.0, 0.9 + len(card["say"]) / 17.0))
        card_dur = round(dur, 2)
        concat.append(f"file 'cards/card{i + 1:02d}.png'\nduration {card_dur}")
        storyboard.append({"n": i + 1, "kicker": card["kicker"],
                           "headline": card.get("number") or " ".join(card["lines"]),
                           "dur": card_dur, "start": round(t, 2),
                           "say": card["say"]})
        t += card_dur

    concat.append(f"file 'cards/card{total:02d}.png'")   # derniere image maintenue
    (OUT / "concat.txt").write_text("\n".join(concat) + "\n", encoding="utf-8")
    (OUT / "storyboard.json").write_text(
        json.dumps(storyboard, ensure_ascii=False, indent=1), encoding="utf-8")

    # sous-titres derives du storyboard : c'est ce que le site servira en WebVTT
    def ts(sec: float, comma: bool = False) -> str:
        h, m, s = int(sec // 3600), int(sec % 3600 // 60), sec % 60
        sep = "," if comma else "."
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", sep)

    vtt = ["WEBVTT", ""]
    srt = []
    for i, s in enumerate(storyboard):
        a, b = s["start"], s["start"] + s["dur"]
        vtt += [f"{i + 1}", f"{ts(a)} --> {ts(b)}", s["say"], ""]
        srt += [f"{i + 1}", f"{ts(a, True)} --> {ts(b, True)}", s["say"], ""]
    (OUT / "bulletin.vtt").write_text("\n".join(vtt), encoding="utf-8")
    (OUT / "bulletin.srt").write_text("\n".join(srt), encoding="utf-8")

    print(f"{total} cartes + 1 contact, duree estimee {t:.1f} s")
    for s in storyboard:
        print(f"  {s['n']:>2}. {s['kicker']:<12} {s['headline'][:38]:<40} {s['dur']:>5} s")


if __name__ == "__main__":
    main()
