@echo off
chcp 65001 > nul
cd /d "%~dp0"
set PYTHONUTF8=1

where py > /dev/null 2>&1 && (set PY=py) || (set PY=python)
%PY% --version > /dev/null 2>&1
if errorlevel 1 (
  echo Python is not installed. See README.md, step 1.
  pause
  exit /b 1
)

echo [1/3] Installing packages...
%PY% -m pip install --quiet --upgrade playwright openpyxl
echo [2/3] Installing browser (first run only, may take a few minutes)...
%PY% -m playwright install chromium
echo [3/3] Collecting listings...
%PY% naver_rent.py
echo.
pause
