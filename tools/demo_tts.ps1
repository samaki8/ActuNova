# Synthese vocale des segments du bulletin (SAPI, voix francaise Hortense).
# Sortie : docs/demo/audio/seg01.wav ... seg10.wav
$ErrorActionPreference = "Stop"

$root = (Get-Location).Path
$demo = Join-Path $root "docs\demo"
$audio = Join-Path $demo "audio"
New-Item -ItemType Directory -Force -Path $audio | Out-Null

$segments = Get-Content -Raw -Encoding UTF8 (Join-Path $demo "segments.json") | ConvertFrom-Json
Write-Output "segments: $($segments.Count)"

$voice = New-Object -ComObject SAPI.SpVoice
$list = $voice.GetVoices()
for ($i = 0; $i -lt $list.Count; $i++) {
    $desc = $list.Item($i).GetDescription()
    if ($desc -match 'Hortense') { $voice.Voice = $list.Item($i); Write-Output "voix: $desc" }
}
$voice.Rate = -1
$voice.Volume = 100

for ($i = 0; $i -lt $segments.Count; $i++) {
    $n = $i + 1
    $path = Join-Path $audio ("seg{0:D2}.wav" -f $n)
    $voice.SetOutputToWaveFile($path)
    $voice.Speak([string]$segments[$i])
    $voice.SetOutputToNull()
    $size = (Get-Item $path).Length
    Write-Output ("seg{0:D2}.wav  {1,7} octets" -f $n, $size)
}
Write-Output "termine"
