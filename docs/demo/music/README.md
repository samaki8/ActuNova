# Musique et sons

Dépose ici **un seul fichier** : `piste.mp3`, `ambiance.m4a`, `theme.wav`... peu
importe le nom, le premier trouvé est utilisé (ordre de préférence : mp3, m4a,
wav, aac, ogg).

Le script `tools/demo_build.ps1` :

- boucle la piste sur toute la durée du bulletin et la coupe à la fin ;
- applique un fondu d'entrée de 1 s et un fondu de sortie de 2 s ;
- la passe à **12 % du volume**, pour qu'elle reste sous la voix ;
- si des segments de voix existent dans `audio/`, les mélange à la musique ;
- s'il n'y a ni musique ni voix, laisse une piste silencieuse (la vidéo reste
  valide).

## Deux règles

**La musique ne doit pas couvrir la voix.** 12 % est un point de départ ; sur une
piste très dense (percussions, saturation), il faut descendre à 8 %.

**Une musique sans droits fait retirer la vidéo, pas la musique.** Sur YouTube,
la revendication automatique transfère la monétisation au ayant droit ; sur
TikTok, le son est coupé ou la vidéo supprimée. Les seules sources sûres :

1. la bibliothèque audio de la plateforme (elle couvre la revendication pour
   cette plateforme, et seulement pour elle) ;
2. une banque sous licence écrite (Artlist, Epidemic Sound, Musicbed) ;
3. du CC0 explicite (Free Music Archive en filtre CC0, pas CC-BY).

Une musique « trouvée sur internet » n'entre dans aucune des trois.

## Pour tester sans musique

Le dossier vide est un état valide : la vidéo sort avec une piste silencieuse.
