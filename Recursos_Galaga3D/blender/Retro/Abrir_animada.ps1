$ErrorActionPreference = 'Stop'
$retroProgramRoot = Join-Path $env:ProgramFiles 'Blender Foundation'
$retroExe = Get-ChildItem -LiteralPath $retroProgramRoot -Filter 'blender-launcher.exe' -File -Recurse | Sort-Object FullName -Descending | Select-Object -First 1
if (-not $retroExe) {
    $retroExe = Get-ChildItem -LiteralPath $retroProgramRoot -Filter 'blender.exe' -File -Recurse | Sort-Object FullName -Descending | Select-Object -First 1
}
if (-not $retroExe) { throw 'No se encuentra Blender instalado.' }
$retroBlend = Join-Path $PSScriptRoot 'Galaga3D_Retro_Animada.blend'
$retroScript = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) 'scripts\interfaz_retro_interactiva.py'
# Abre la versión animada con el controlador de botones.
Start-Process -FilePath $retroExe.FullName -ArgumentList @('"' + $retroBlend + '"','--python','"' + $retroScript + '"') -WindowStyle Normal
