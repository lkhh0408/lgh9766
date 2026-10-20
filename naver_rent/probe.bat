@echo off
chcp 65001 > nul
cd /d "%~dp0"
set PYTHONUTF8=1
echo Folder: %CD%

rem ---- Find Python: py launcher, python command, then common install folders ----
set "PYEXE="
for /f "delims=" %%i in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do set "PYEXE=%%i"
if not defined PYEXE for /f "delims=" %%i in ('python -c "import sys;print(sys.executable)" 2^>nul') do set "PYEXE=%%i"
if not defined PYEXE for /d %%D in ("%LocalAppData%\Programs\Python\Python3*" "%ProgramFiles%\Python3*" "%LocalAppData%\Python\pythoncore-3*" "C:\Python3*") do if exist "%%~D\python.exe" set "PYEXE=%%~D\python.exe"

if not defined PYEXE (
  echo.
  echo Python was not found. Please send a screenshot of this window.
  echo ---- where py ----
  where py
  echo ---- where python ----
  where python
  echo ---- folders ----
  dir /b "%LocalAppData%\Programs\Python" 2>NUL
  dir /b "%LocalAppData%\Python" 2>NUL
  dir /b "%ProgramFiles%" 2>NUL | findstr /i python
  echo.
  pause
  exit /b 1
)
echo Python: %PYEXE%

echo [1/3] Installing packages...
"%PYEXE%" -m pip install --quiet --upgrade playwright openpyxl
if errorlevel 1 (
  echo Package install failed. Please send a screenshot of this window.
  pause
  exit /b 1
)
echo [2/3] Installing browser (first run only, may take a few minutes)...
"%PYEXE%" -m playwright install chromium
echo [3/3] Starting probe...
"%PYEXE%" probe.py
echo.
pause
