# Read-only inventory of the Patreon download folder on the Windows D: drive (not mounted in WSL).
# Run from WSL:  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(wslpath -w scripts/pdf_audit/manifest.ps1)" > manifest.json
# Output: UTF-8 JSON {songs:[{artist, song, link, files:[{name,size}]}], stray:[...]}. Change $root if the folder moved.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'SilentlyContinue'
$root = 'D:\מסמכים\python-downloads'
$items = foreach ($a in Get-ChildItem -LiteralPath $root -Directory) {
  foreach ($s in Get-ChildItem -LiteralPath $a.FullName -Directory) {
    $files = Get-ChildItem -LiteralPath $s.FullName -File
    $txt = $files | Where-Object { $_.Name -like '*video link.txt' } | Select-Object -First 1
    $link = if ($txt) { (Get-Content -LiteralPath $txt.FullName -Encoding UTF8 -Raw) } else { $null }
    [pscustomobject]@{
      artist = $a.Name; song = $s.Name; link = $link
      files = @($files | ForEach-Object { [pscustomobject]@{ name = $_.Name; size = $_.Length } })
    }
  }
}
# stray files directly under artist folders or the root
$stray = @(Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { $_.Directory.Parent.FullName -ne $root -and $_.Directory.Parent.Parent.FullName -ne $root } | Select-Object -First 50 -ExpandProperty FullName)
[pscustomobject]@{ songs = $items; stray = $stray } | ConvertTo-Json -Depth 5 -Compress
