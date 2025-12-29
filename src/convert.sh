#!/bin/bash
# Simple wrapper for convert_to_dzi.py
# Usage: ./convert.sh image.jpg [output_name]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${SCRIPT_DIR}/env/bin/python3"

if [ ! -f "$PYTHON" ]; then
    echo "❌ Python environment not found. Run: make setup"
    exit 1
fi

"$PYTHON" "${SCRIPT_DIR}/convert_to_dzi.py" "$@"
