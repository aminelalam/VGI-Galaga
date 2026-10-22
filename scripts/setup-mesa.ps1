param([switch]$Deploy)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repo 'Entrega_Amin_VGI\entornsGrafics'
$mesa = Join-Path $source 'third_party\mesa'
$cache = Join-Path $mesa 'cache'
$runtime = Join-Path $mesa 'bin'
$licenses = Join-Path $mesa 'licenses'
$version = '26.2.5'
$dllSha256 = '8ddc061ee752fff06ae682de0ac2e010926d76a93c1aecc4c206adee771856e1'

# TLS selection and downloaded files are local to this process/project.
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
foreach ($folder in @($cache, $runtime, $licenses)) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
}

function Get-VerifiedFile([string]$Url, [string]$Path, [string]$Sha256) {
    if ((Test-Path -LiteralPath $Path) -and
        (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -eq $Sha256) { return }
    $temporary = "$Path.download"
    Write-Output "Descargando $Url"
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $temporary
        if ((Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash -ne $Sha256) {
            throw "El SHA256 no coincide: $Url"
        }
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}

$dll = Join-Path $runtime 'opengl32.dll'
if (!(Test-Path -LiteralPath $dll) -or
    (Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash -ne $dllSha256) {
    $archive = Join-Path $cache "mesa-llvmpipe-x64-$version.7z"
    Get-VerifiedFile "https://github.com/mmozeiko/build-mesa/releases/download/$version/mesa-llvmpipe-x64-$version.7z" `
        $archive 'd1b713ca2a7fba47a50c058099f13c435ddb76a16a422c334e4d787f9755a31d'
    & tar.exe -xf $archive -C $runtime opengl32.dll
    if ($LASTEXITCODE -ne 0) { throw 'No se ha podido extraer Mesa con tar.exe.' }
    if ((Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash -ne $dllSha256) {
        throw 'El SHA256 de opengl32.dll no coincide con la version fijada.'
    }
}

# Notices are checked in. Restore them from pinned upstream sources if absent.
if (!(Test-Path -LiteralPath (Join-Path $licenses 'license.rst')) -or
    !(Test-Path -LiteralPath (Join-Path $licenses 'MIT'))) {
    $archive = Join-Path $cache "mesa-$version.tar.xz"
    Get-VerifiedFile "https://archive.mesa3d.org/mesa-$version.tar.xz" `
        $archive '794b3d1729075dae7ebd47c7283b7ca0cdb5dec668f7f11cc0a5d82f6138a0a5'
    & tar.exe -xf $archive -C $licenses --strip-components=2 "mesa-$version/docs/license.rst" "mesa-$version/licenses"
    if ($LASTEXITCODE -ne 0) { throw 'No se han podido extraer las licencias de Mesa.' }
}
Get-VerifiedFile 'https://raw.githubusercontent.com/llvm/llvm-project/llvmorg-23.1.3/LICENSE.TXT' `
    (Join-Path $licenses 'LLVM.txt') '8d85c1057d742e597985c7d4e6320b015a9139385cff4cbae06ffc0ebe89afee'

if ($Deploy) {
    foreach ($configuration in @('Debug', 'Release')) {
        $destination = Join-Path $source "bin\x64\$configuration"
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        $target = Join-Path $destination 'opengl32.dll'
        if (!(Test-Path -LiteralPath $target) -or
            (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $dllSha256) {
            Copy-Item -LiteralPath $dll -Destination $target -Force
        }
    }
}
Write-Output "Mesa $version LLVMpipe x64 listo (OpenGL local; sin cambiar controladores)."
