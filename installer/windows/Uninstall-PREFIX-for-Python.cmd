@echo off
setlocal
rem Windows PowerShell must not load inherited PowerShell 7 modules.
set "PSModulePath="
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Uninstall-PREFIX-for-Python.ps1" %*
set "PREFIX_EXIT=%ERRORLEVEL%"
if not "%PREFIX_EXIT%"=="0" pause
exit /b %PREFIX_EXIT%
