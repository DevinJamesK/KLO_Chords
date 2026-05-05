#!/usr/bin/env bash
set -euo pipefail

# ────────────────────────────────────────────────────────────
# KLO Chords — run script (macOS / Linux)
# ────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_NAME="klo_music"
REQUIREMENTS_FILE="requirements.txt"

# ── 1. Pick a Python interpreter ────────────────────────────
echo "== KLO Chords Launcher =="

# Prefer conda env if it exists
if command -v conda &>/dev/null; then
    if conda env list | grep -q "^${ENV_NAME} "; then
        echo "[✓] Conda environment '${ENV_NAME}' found."
    else
        echo "[!] Conda env '${ENV_NAME}' not found — creating it now..."
        conda env create -f environment.yml
        echo "[✓] Conda environment '${ENV_NAME}' created."
    fi
    conda activate "${ENV_NAME}" 2>/dev/null || true
    PY="python"
else
    # Fall back to system python or venv
    echo "[i] Conda not found — using system python."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo "[✓] Activated local .venv"
    fi
    PY="python3"
fi

# ── 2. Check Python version ─────────────────────────────────
PY_VER="$($PY -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
echo "[i] Python ${PY_VER}"

# ── 3. Install / verify dependencies ────────────────────────
echo "[i] Checking dependencies..."
if ! $PY -c "import dearpygui, sounddevice, numpy" 2>/dev/null; then
    echo "[i] Installing dependencies from ${REQUIREMENTS_FILE}..."
    $PY -m pip install -r "${REQUIREMENTS_FILE}" --quiet
    echo "[✓] Dependencies installed."
else
    echo "[✓] Dependencies OK."
fi

# ── 4. Install the package in editable mode (so assets resolve) ──
echo "[i] Installing klo-chords (editable)..."
$PY -m pip install -e . --quiet
echo "[✓] Package installed."

# ── 5. Launch ───────────────────────────────────────────────
echo "[i] Starting KLO Chords..."
echo ""
$PY -m klo_chords
