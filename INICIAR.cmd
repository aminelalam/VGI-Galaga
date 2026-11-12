@echo off
setlocal
set "galagaNavesCarpeta=%~dp0"
if not exist "%galagaNavesCarpeta%Galaga3D.exe" set "galagaNavesCarpeta=%~dp0dist\Galaga3D-Anterior-Naves\"
if not exist "%galagaNavesCarpeta%Galaga3D.exe" (
    echo Ejecuta primero build-demo.cmd o descarga el paquete Windows y extraelo.
    pause
    exit /b 1
)
pushd "%galagaNavesCarpeta%"
start "" "%galagaNavesCarpeta%Galaga3D.exe"
popd
