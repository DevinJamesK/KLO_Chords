@echo off
setlocal enabledelayedexpansion

REM ────────────────────────────────────────────────────────────
REM KLO Chords -run script (Windows)
REM ────────────────────────────────────────────────────────────

cd /d "%~dp0"

set ENV_NAME=klo_music
set REQUIREMENTS_FILE=requirements.txt

echo == KLO Chords Launcher ==

REM ── 1. Pick a Python interpreter ────────────────────────────

REM Prefer conda env if it exists
where conda >nul 2>nul
if %ERRORLEVEL% equ 0 (
    conda env list | findstr /C:"%ENV_NAME% " >nul
    if !ERRORLEVEL! equ 0 (
        echo [*] Conda environment '%ENV_NAME%' found.
    ) else (
        echo [!] Conda env '%ENV_NAME%' not found -creating it now...
        call conda env create -f environment.yml
        echo [*] Conda environment '%ENV_NAME%' created.
    )
    call conda activate "%ENV_NAME%"
    set PY=python
) else (
    echo [i] Conda not found -using system python.
    if exist ".venv\Scripts\activate.bat" (
        call .venv\Scripts\activate.bat
        echo [*] Activated local .venv
    )
    set PY=python
)

REM ── 2. Check Python version ─────────────────────────────────
%PY% -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>nul

REM ── 3. Install / verify dependencies ────────────────────────
echo [i] Checking dependencies...
%PY% -c "import dearpygui, sounddevice, numpy" >nul 2>nul
if !ERRORLEVEL! neq 0 (
    echo [i] Installing dependencies from %REQUIREMENTS_FILE%...
    %PY% -m pip install -r "%REQUIREMENTS_FILE%" --quiet
    echo [*] Dependencies installed.
) else (
    echo [*] Dependencies OK.
)

REM ── 4. Install the package in editable mode ─────────────────
echo [i] Installing klo-chords (editable)...
%PY% -m pip install -e . --quiet
echo [*] Package installed.

REM ── 5. Launch ───────────────────────────────────────────────
echo [i] Starting KLO Chords...
echo.
%PY% -m klo_chords

endlocal
