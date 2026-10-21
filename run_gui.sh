#!/usr/bin/env bash
set -e

# Configuration variables
VENV_NAME=".venv"

echo "=== SteamForgeLib Environment Setup & Launch ==="

# 1. Create a new virtual environment if it doesn't already exist
if [ ! -d "$VENV_NAME" ]; then
    echo "[1/4] Creating new virtual environment in '$VENV_NAME'..."
    python3 -m venv "$VENV_NAME"
else
    echo "[1/4] Virtual environment '$VENV_NAME' already exists. Skipping creation."
fi

# 2. Activate the virtual environment
echo "[2/4] Activating virtual environment..."
source "$VENV_NAME/bin/activate"

# 3. Upgrade pip and install dependencies
echo "[3/4] Upgrading pip and installing dependencies (PySide6, vdf, psutil)..."
pip install --upgrade pip
pip install PySide6 vdf psutil

# 4. Run the GUI application
echo "[4/4] Launching SteamForgeLibGUI.py..."
if [ -f "SteamForgeLibGUI.py" ]; then
    python3 SteamForgeLibGUI.py
else
    echo "Error: SteamForgeLibGUI.py not found in the current directory!"
    exit 1
fi