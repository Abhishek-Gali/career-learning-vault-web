#!/usr/bin/env bash
# scripts/setup.sh — Linux / macOS Setup Script (Strictly self-contained in project root)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Setting up CLF-C02 Researcher in: $PROJECT_ROOT"

# Set local pip and playwright cache paths
export PIP_CACHE_DIR="$PROJECT_ROOT/.pip-cache"
export PLAYWRIGHT_BROWSERS_PATH="$PROJECT_ROOT/.playwright"

# 1. Create local virtual environment
VENV_PATH="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating Python virtual environment in $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
else
    echo "Virtual environment already exists."
fi

# 2. Activate virtual environment and install packages
source "$VENV_PATH/bin/activate"
echo "Installing dependencies into local virtual environment..."
pip install --cache-dir "$PIP_CACHE_DIR" --upgrade pip
pip install --cache-dir "$PIP_CACHE_DIR" -e "$PROJECT_ROOT[dev]"

# 3. Download HTMX locally
VENDOR_DIR="$PROJECT_ROOT/app/web/static/vendor"
mkdir -p "$VENDOR_DIR"
HTMX_FILE="$VENDOR_DIR/htmx.min.js"
if [ ! -f "$HTMX_FILE" ]; then
    echo "Downloading HTMX to $HTMX_FILE..."
    curl -sSL "https://unpkg.com/htmx.org@2.0.11/dist/htmx.min.js" -o "$HTMX_FILE" || echo "Warning: Could not download HTMX (offline)."
fi

# 4. Ensure data directories exist
mkdir -p "$PROJECT_ROOT/data/db" "$PROJECT_ROOT/data/cache/pages" "$PROJECT_ROOT/data/cache/curriculum" "$PROJECT_ROOT/data/exports" "$PROJECT_ROOT/data/logs"

echo "Setup completed successfully!"
echo "To activate run: source .venv/bin/activate"
echo "To check system health run: clf doctor"
