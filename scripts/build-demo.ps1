param(
    [ValidateSet('Debug','Release')][string]$Configuration = 'Release',
    [switch]$Verify,
    [switch]$Package,
    [switch]$SoftwareRenderer
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repo 'Entrega_Amin_VGI\entornsGrafics'
if ($Package -and $Configuration -ne 'Release') { throw 'El paquete distribuible requiere Release.' }
$locator = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (!(Test-Path -LiteralPath $locator)) { throw 'Instala Visual Studio con C++ de escritorio, MFC y Windows SDK.' }
$installation = & $locator -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$installation) { throw 'No se encuentra Visual Studio con el compilador C++.' }
$vsVersion = & $locator -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationVersion
$toolset = if (([version]$vsVersion).Major -ge 18) { 'v145' } else { 'v143' }
$msbuild = Join-Path $installation 'MSBuild\Current\Bin\MSBuild.exe'
$solution = Join-Path $source 'Galaga3D.sln'
if ($SoftwareRenderer) { & (Join-Path $PSScriptRoot 'setup-mesa.ps1') -Deploy }
& $msbuild $solution /t:Build "/p:Configuration=$Configuration" /p:Platform=x64 "/p:PlatformToolset=$toolset" /p:PreferredToolArchitecture=x64 /m:1 /nodeReuse:false /p:BuildInParallel=false /verbosity:minimal /nologo
if ($LASTEXITCODE -ne 0) { throw 'La compilacion ha fallado.' }
$tests = Join-Path $source "bin\tests\$Configuration\Game3DTests.exe"
& $tests
if ($LASTEXITCODE -ne 0) { throw 'Han fallado las pruebas de logica.' }
$binary = Join-Path $source "bin\x64\$Configuration"
$executable = Join-Path $binary 'Galaga3D.exe'
if (!(Test-Path -LiteralPath $executable)) { throw "Falta el ejecutable esperado: $executable" }
# Una copia anterior de Mesa no debe sustituir al controlador al compilar sin la opcion.
$mesaRuntime = Join-Path $binary 'opengl32.dll'
if (!$SoftwareRenderer -and (Test-Path -LiteralPath $mesaRuntime)) { Remove-Item -LiteralPath $mesaRuntime -Force }
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
    if (Select-String -LiteralPath $report -Pattern '^FAIL ' -Quiet) { throw 'La comprobacion grafica ha detectado un error.' }
}
if ($Package) {
    $destination = Join-Path $repo 'dist\Galaga3D-Anterior-Naves'
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Copy-Item -LiteralPath $executable -Destination $destination -Force
    $packagedMesa = Join-Path $destination 'opengl32.dll'
    if ($SoftwareRenderer) { Copy-Item -LiteralPath $mesaRuntime -Destination $destination -Force }
    elseif (Test-Path -LiteralPath $packagedMesa) { Remove-Item -LiteralPath $packagedMesa -Force }
    foreach ($folder in @('Recursos_Galaga3D','shaders','textures')) {
        Copy-Item -LiteralPath (Join-Path $binary $folder) -Destination $destination -Recurse -Force
    }
    # App-local redistribution of the VS runtime; no system installation needed.
    $redist = Get-ChildItem -LiteralPath (Join-Path $installation 'VC\Redist\MSVC') -Directory |
        Where-Object { $_.Name -match '^14\.' } | Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1
    if (!$redist) { throw 'No se encuentran los redistribuibles de Visual C++.' }
    $components = Get-ChildItem -LiteralPath (Join-Path $redist.FullName 'x64') -Directory |
        Where-Object { $_.Name -match '^Microsoft\.VC\d+\.(CRT|MFC)$' }
    if (@($components).Count -lt 2) { throw 'Faltan los redistribuibles de Visual C++ CRT o MFC.' }
    foreach ($component in $components) {
        Get-ChildItem -LiteralPath $component.FullName -Filter '*.dll' | Copy-Item -Destination $destination -Force
    }
    $licenses = Join-Path $destination 'licenses'
    New-Item -ItemType Directory -Path $licenses -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $source 'third_party\glew\LICENSE.txt') -Destination (Join-Path $licenses 'GLEW.txt') -Force
    Copy-Item -LiteralPath (Join-Path $source 'third_party\soil2\LICENSE') -Destination (Join-Path $licenses 'SOIL2.txt') -Force
    # GLM 0.9.9.7: https://raw.githubusercontent.com/g-truc/glm/0.9.9.7/copying.txt
    Copy-Item -LiteralPath (Join-Path $source 'third_party\GLM-COPYING.txt') -Destination (Join-Path $licenses 'GLM.txt') -Force
    Copy-Item -LiteralPath (Join-Path $repo 'Recursos_Galaga3D\fonts\bitstream-vera-license.txt') -Destination $licenses -Force
    if ($SoftwareRenderer) {
        $mesaLicenses = Join-Path $licenses 'Mesa'
        New-Item -ItemType Directory -Path $mesaLicenses -Force | Out-Null
        Get-ChildItem -LiteralPath (Join-Path $source 'third_party\mesa\licenses') | Copy-Item -Destination $mesaLicenses -Recurse -Force
        Copy-Item -LiteralPath (Join-Path $source 'third_party\mesa\README.md') -Destination (Join-Path $licenses 'MESA-ORIGEN.md') -Force
    }
    Copy-Item -LiteralPath (Join-Path $repo 'README.md') -Destination (Join-Path $destination 'LEEME.md') -Force
    Copy-Item -LiteralPath (Join-Path $repo 'INICIAR.cmd') -Destination $destination -Force
    Write-Output "Demo lista: $destination\Galaga3D.exe"
}
