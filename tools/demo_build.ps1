# Assemble le bulletin : cartes -> video -> audio -> sous-titres.
#
#   powershell -ExecutionPolicy Bypass -File tools/demo_build.ps1
#
# Detecte automatiquement :
#   docs/demo/backgrounds/cardNN.jpg   fonds d'images (optionnels)
#   docs/demo/audio/segNN.wav          voix (optionnelle)
#   docs/demo/music/<un fichier>       musique de fond (optionnelle)
#
# Sans aucun media, la video sort quand meme : cartes + piste silencieuse.

$ErrorActionPreference = "Stop"
# lance depuis la racine du depot ; fonctionne aussi en Invoke-Expression
$root = if ($MyInvocation.MyCommand.Path) {
    Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
} else {
    (Get-Location).Path
}
$demo = Join-Path $root "docs\demo"
Push-Location $root
try {
    # Python avec Pillow : DEMO_PYTHON, sinon python du PATH, sinon le runtime
    # embarque par l'outil (l'environnement de developpement local).
    function Resolve-Python {
        if ($env:DEMO_PYTHON) { return $env:DEMO_PYTHON }
        $cands = @("python")
        $dsh = Join-Path $env:USERPROFILE ".dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
        if (Test-Path $dsh) { $cands += $dsh }
        foreach ($c in $cands) {
            # EAP local : un echec de sonde ne doit pas interrompre le script
            $prev = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            & $c -c "import PIL" 2>$null
            $ok = ($LASTEXITCODE -eq 0)
            $ErrorActionPreference = $prev
            if ($ok) { return $c }
        }
        throw "aucun Python avec Pillow (definir DEMO_PYTHON)"
    }
    $py = Resolve-Python
    Write-Output "== python : $py"

    Write-Output "== cartes et storyboard"
    & $py tools/demo_deck.py --render
    if ($LASTEXITCODE -ne 0) { throw "rendu des cartes en echec" }

    Push-Location $demo
    try {
        Write-Output "== video muette"
        ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i concat.txt `
            -r 30 -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p silent.mp4
        if ($LASTEXITCODE -ne 0) { throw "encodage video en echec" }

        $dur = [double](ffprobe -v error -show_entries format=duration -of csv=p=0 silent.mp4)
        Write-Output ("   duree : {0:N1} s" -f $dur)

        # ── voix ────────────────────────────────────────────────────────────
        $segs = Get-ChildItem "audio\seg*.wav" -ErrorAction SilentlyContinue | Sort-Object Name
        $voice = $null
        if ($segs -and $segs.Count -gt 0) {
            Write-Output "== voix : $($segs.Count) segment(s)"
            $list = $segs | ForEach-Object { "file 'audio/$($_.Name)'" }
            Set-Content -Path voice.txt -Value $list -Encoding ASCII
            ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i voice.txt -c copy voice.wav
            $voice = "voice.wav"
        } else {
            Write-Output "== voix : aucune (audio/ vide)"
        }

        # ── musique ─────────────────────────────────────────────────────────
        $music = $null
        foreach ($ext in @("mp3", "m4a", "wav", "aac", "ogg")) {
            $f = Get-ChildItem "music\*.$ext" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($f) { $music = $f; break }
        }

        if ($music) {
            Write-Output "== musique : $($music.Name) (bouclee, 12 % du volume)"
            # formatage invariant : en fr-FR, "$fadeOut" produirait "59,73" et
            # la virgule casserait la chaine de filtres ffmpeg
            $inv = [System.Globalization.CultureInfo]::InvariantCulture
            $durStr = $dur.ToString("0.###", $inv)
            $fadeStr = ([Math]::Max(0, $dur - 2)).ToString("0.###", $inv)
            $chain = "volume=0.12,afade=t=in:st=0:d=1,afade=t=out:st=$fadeStr`:d=2"
            ffmpeg -y -hide_banner -loglevel error -stream_loop -1 -i "music\$($music.Name)" `
                -t $durStr -af $chain -c:a aac -b:a 160k music.m4a
            if ($LASTEXITCODE -ne 0) { throw "preparation de la musique en echec" }
        } else {
            Write-Output "== musique : aucune (music/ vide)"
        }

        # ── mixage ──────────────────────────────────────────────────────────
        if ($voice -and $music) {
            Write-Output "== mixage voix + musique"
            ffmpeg -y -hide_banner -loglevel error -i $voice -i music.m4a `
                -filter_complex "[0:a]apad[v];[v][1:a]amix=inputs=2:duration=first:dropout_transition=0[a]" `
                -map "[a]" -c:a aac -b:a 160k mix.m4a
            $audio = "mix.m4a"
        }
        elseif ($voice) { $audio = $voice }
        elseif ($music) { $audio = "music.m4a" }
        else {
            Write-Output "== audio : piste silencieuse"
            ffmpeg -y -hide_banner -loglevel error -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 `
                -t $dur -c:a aac -b:a 96k silence.m4a
            $audio = "silence.m4a"
        }

        # ── assemblage final ────────────────────────────────────────────────
        Write-Output "== assemblage + sous-titres"
        ffmpeg -y -hide_banner -loglevel error -i silent.mp4 -i $audio -i bulletin.vtt `
            -map 0:v -map 1:a -map 2:s -c:v copy -c:a copy -c:s mov_text `
            -metadata:s:s:0 language=fra -shortest -movflags +faststart bulletin_new.mp4
        if ($LASTEXITCODE -ne 0) { throw "assemblage final en echec" }

        Move-Item -Force bulletin_new.mp4 bulletin.mp4
        Remove-Item silent.mp4, silence.m4a, music.m4a, mix.m4a -ErrorAction SilentlyContinue

        ffmpeg -y -hide_banner -loglevel error -i cards/card%02d.png `
            -vf "scale=270:480,tile=5x2:padding=10:margin=10:color=white" -frames:v 1 contact.png
        ffmpeg -y -hide_banner -loglevel error -ss 9 -i bulletin.mp4 -frames:v 1 poster.png

        $size = [Math]::Round((Get-Item bulletin.mp4).Length / 1KB, 1)
        Write-Output ("== OK  bulletin.mp4  {0} Ko  {1:N1} s" -f $size, $dur)
    }
    finally { Pop-Location }
}
finally { Pop-Location }
