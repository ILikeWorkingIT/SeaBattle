@echo off
cd /d "%~dp0"
echo Starting Swagger UI and ReDoc for openapi.yaml
echo Open the printed URLs in Chrome or Edge, not Cursor Simple Browser.
echo Default ports: 8080 (Swagger) and 8081 (ReDoc). If busy, the next free ports are used.
echo.
python preview-openapi.py
if errorlevel 1 (
  echo.
  echo Python failed. Need Python 3.12+ on PATH.
  pause
)
