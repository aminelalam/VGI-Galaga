@echo off
setlocal
rem ExecutionPolicy applies only to this child process, never to Windows settings.
if "%~1"=="" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build-demo.ps1" -Configuration Release -Verify -Package
) else (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build-demo.ps1" %*
)
exit /b %errorlevel%
