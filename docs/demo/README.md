# Demonstration — le bulletin en cartes

Ce dossier contient un vrai rendu, produit a partir de depeches reelles relevees le
5 novembre 2026 (BBC, France 24, Le Monde, Al Jazeera, DW, Hespress).

| Fichier | Contenu |
|---|---|
| `bulletin.mp4` | 1080x1920, 30 fps, ~62 s, 10 cartes, piste de sous-titres francaise |
| `contact.png` | les 10 cartes en planche contact |
| `poster.png` | une image d'illustration extraite de la video |
| `cards/card01..10.png` | les cartes a l'unite, 1080x1920 |
| `bulletin.vtt` / `bulletin.srt` | les sous-titres derives du storyboard |
| `storyboard.json` | numero, kicker, titre, duree, instant de debut, texte parle |
| `segments.json` | le texte a synthetiser par la voix |

## Ce qui a ete fait a la main

Les 10 cartes et les 6 titres. C'est le travail editorial qu'on ne confie pas
encore au LLM : choisir l'evenement, le reduire a trois a six mots, decider ou
couper la ligne. Le pipeline ne genere pour l'instant que les images et le timing.

## La voix

La synthese vocale n'a pas pu etre produite sur cette machine : SAPI repond une
erreur COM sur les deux interfaces (SpVoice et System.Speech), alors que la voix
francaise Hortense est bien installee. La piste audio du MP4 est donc **muette**,
et le timing de chaque carte suit la longueur du texte parle (~17 caracteres par
seconde), ce qui donne le rythme reel du bulletin.

Sur une machine ou le TTS fonctionne, remplacer l'etape 3 par la synthese des
segments de `segments.json` dans `audio/seg01.wav..seg10.wav` : le script
reprend les durees mesurees automatiquement.

## Le son

Trois emplacements, tous optionnels, tous détectés automatiquement :

| Dossier | Contenu | Effet |
|---|---|---|
| `music/` | **un** fichier (`piste.mp3`, `ambiance.m4a`, `theme.wav`…) | bouclé sur la durée du bulletin, fondu entrée 1 s et sortie 2 s, **12 % du volume** |
| `audio/` | `seg01.wav` … `seg10.wav` | la voix, mélangée par-dessus la musique |
| *(rien)* | — | piste silencieuse, la vidéo reste valide |

Une seule commande assemble le tout :

```powershell
powershell -ExecutionPolicy Bypass -File tools/demo_build.ps1
```

Elle enchaîne : cartes → vidéo muette → audio (musique et/ou voix) → mixage →
sous-titres → planche contact. Le script affiche ce qu'il a trouvé, donc on sait
toujours pourquoi la vidéo sonne comme elle sonne.

`music/README.md` détaille les règles de droits : une musique sans licence fait
retirer la vidéo, pas la musique.

## Les images de fond

Déposer une image dans `backgrounds/` sous le nom `card01.jpg`, `card02.jpg`, …
(`.png` accepté). Le rendu la détecte, la recadre pour couvrir le cadre 1080×1920,
applique un voile (plus dense à gauche, là où le texte se trouve) et garde le
texte au premier plan. Aucun code à modifier.

Sans fichier, la carte garde son dégradé de couleur — le rendu ne casse jamais.

Dans la vidéo livrée, seule la carte 2 a un fond : une image abstraite générée
pour la démonstration, pas une photo de presse. Les autres attendent les
vôtres.

`tools/geo_silhouette.py` et `sources/geo/` permettent aussi de dessiner la
silhouette d'un pays (Natural Earth, domaine public). Le rendu obtenu n'était
pas convaincant : la fonctionnalité est désactivée, le code est conservé.

## Reconstruire

```
python tools/demo_deck.py --emit                 # ecrit segments.json
powershell tools/demo_tts.ps1                    # (optionnel) synthese vocale
python tools/demo_deck.py --render               # cartes + listes + sous-titres
cd docs/demo
ffmpeg -y -f concat -safe 0 -i concat.txt -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 `
  -r 30 -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest -movflags +faststart bulletin.mp4
ffmpeg -y -i bulletin.mp4 -i bulletin.vtt -c copy -c:s mov_text -metadata:s:s:0 language=fra bulletin2.mp4
```
