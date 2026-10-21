#!/usr/bin/env bash
set -e

# Configuration variables
VENV_NAME=".venv"

echo "=== SteamForgeLib Environment Cleanup & Uninstall ==="

# 1. Remove virtual environment directory if it exists
if [ -d "$VENV_NAME" ]; then
    echo "Removing virtual environment directory ('$VENV_NAME')..."
    rm -rf "$VENV_NAME"
    echo "Virtual environment successfully removed."
else
    echo "No virtual environment found at '$VENV_NAME'."
fi

# 2. Clean up Python cache files (__pycache__, .pyc files)
echo "Cleaning up local Python cache files..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "Uninstall and cleanup completed successfully."