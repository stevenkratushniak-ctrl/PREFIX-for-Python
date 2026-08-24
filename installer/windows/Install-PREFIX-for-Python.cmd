@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-PREFIX-for-Python.ps1" %*
set "PREFIX_EXIT=%ERRORLEVEL%"
if not "%PREFIX_EXIT%"=="0" (
  echo.
  echo PREFIX for Python installation did not complete. Review the message above.
  pause
)
exit /b %PREFIX_EXIT%
