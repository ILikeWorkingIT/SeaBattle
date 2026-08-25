@echo off
cd /d "%~dp0"
set PYTHONPATH=%CD%
python -m frontend
if errorlevel 1 (
  echo.
  echo If the window did not open, check that Python 3.12 and PySide6 are installed.
  pause
)
