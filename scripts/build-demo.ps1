param(
    [ValidateSet('Debug','Release')][string]$Configuration = 'Release',
    [switch]$Verify,
    [switch]$Package
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repo 'Entrega_Amin_VGI\entornsGrafics'
if ($Package -and $Configuration -ne 'Release') { throw 'El paquete distribuible requiere Release.' }
$locator = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (!(Test-Path -LiteralPath $locator)) { throw 'Instala Visual Studio 2022 con C++ de escritorio y MFC v143.' }
$installation = & $locator -latest -version '[17.0,18.0)' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$installation) { throw 'No se encuentra Visual Studio 2022 con el compilador C++.' }
$msbuild = Join-Path $installation 'MSBuild\Current\Bin\MSBuild.exe'
$solution = Join-Path $source 'Galaga3D.sln'
& (Join-Path $PSScriptRoot 'setup-mesa.ps1') -Deploy
& $msbuild $solution /t:Build "/p:Configuration=$Configuration" /p:Platform=x64 /verbosity:minimal /nologo
if ($LASTEXITCODE -ne 0) { throw 'La compilacion ha fallado.' }
$tests = Join-Path $source "bin\tests\$Configuration\Game3DTests.exe"
& $tests
if ($LASTEXITCODE -ne 0) { throw 'Han fallado las pruebas de logica.' }
$binary = Join-Path $source "bin\x64\$Configuration"
$executable = Join-Path $binary 'Galaga3D.exe'
if (!(Test-Path -LiteralPath $executable)) { throw "Falta el ejecutable esperado: $executable" }
if ($Verify) {
    $report = Join-Path $binary 'verification\render-report.txt'
    if (Test-Path -LiteralPath $report) { Remove-Item -LiteralPath $report -Force }
    $process = Start-Process -FilePath $executable -ArgumentList '/verify-render' -WorkingDirectory $binary -WindowStyle Hidden -PassThru
    if (!$process.WaitForExit(60000)) {
        Stop-Process -Id $process.Id -ErrorAction SilentlyContinue
        throw 'La verificacion grafica ha superado 60 segundos. Consulta startup.log y context.log.'
    }
    $process.Refresh()
    if ($process.ExitCode -ne 0 -or !(Test-Path -LiteralPath $report)) { throw 'Ha fallado la verificacion grafica. Consulta startup.log y context.log junto al ejecutable.' }
    Get-Content -LiteralPath $report
}
if ($Package) {
    $destination = Join-Path $repo 'dist\Galaga3D'
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Copy-Item -LiteralPath $executable -Destination $destination -Force
    Copy-Item -LiteralPath (Join-Path $binary 'opengl32.dll') -Destination $destination -Force
    foreach ($folder in @('Recursos_Galaga3D','shaders','textures')) {
        Copy-Item -LiteralPath (Join-Path $binary $folder) -Destination $destination -Recurse -Force
    }
    # App-local redistribution of the VS runtime; no system installation needed.
    $redist = Get-ChildItem -LiteralPath (Join-Path $installation 'VC\Redist\MSVC') -Directory |
        Where-Object { $_.Name -match '^14\.' } | Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1
    if (!$redist) { throw 'No se encuentran los redistribuibles de Visual C++.' }
    foreach ($component in @('Microsoft.VC143.CRT','Microsoft.VC143.MFC')) {
        $folder = Join-Path $redist.FullName "x64\$component"
        if (!(Test-Path -LiteralPath $folder)) { throw "Falta el redistribuible $component." }
        Get-ChildItem -LiteralPath $folder -Filter '*.dll' | Copy-Item -Destination $destination -Force
    }
    $licenses = Join-Path $destination 'licenses'
    New-Item -ItemType Directory -Path $licenses -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $source 'third_party\glew\LICENSE.txt') -Destination (Join-Path $licenses 'GLEW.txt') -Force
    Copy-Item -LiteralPath (Join-Path $source 'third_party\soil2\LICENSE') -Destination (Join-Path $licenses 'SOIL2.txt') -Force
    # GLM 0.9.9.7: https://raw.githubusercontent.com/g-truc/glm/0.9.9.7/copying.txt
    Copy-Item -LiteralPath (Join-Path $source 'third_party\GLM-COPYING.txt') -Destination (Join-Path $licenses 'GLM.txt') -Force
    $mesaLicenses = Join-Path $licenses 'Mesa'
    New-Item -ItemType Directory -Path $mesaLicenses -Force | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $source 'third_party\mesa\licenses') | Copy-Item -Destination $mesaLicenses -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $source 'third_party\mesa\README.md') -Destination (Join-Path $licenses 'MESA-ORIGEN.md') -Force
    Copy-Item -LiteralPath (Join-Path $repo 'DEMO_3D.md') -Destination (Join-Path $destination 'LEEME.md') -Force
    Write-Output "Demo lista: $destination\Galaga3D.exe"
}
