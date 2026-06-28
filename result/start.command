#!/bin/bash
# Gaokao Data Query Server — macOS launcher
# Double-click this file to run

cd "$(dirname "$0")"

echo "========================================"
echo "  Gaokao Data Query Server"
echo "========================================"
echo ""

# ── Check for Python 3 ──
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo "Python 3 not found. Attempting automatic install..."
    echo ""

    # Try Homebrew (most common on macOS)
    if command -v brew &>/dev/null; then
        echo "Installing Python via Homebrew..."
        brew install python3
        if command -v python3 &>/dev/null; then
            PY=python3
            echo "Done."
        fi
    fi

    # Try Xcode Command Line Tools (ships python3)
    if [ -z "$PY" ] && command -v xcode-select &>/dev/null; then
        echo "Trying Xcode Command Line Tools..."
        xcode-select --install 2>/dev/null
        # xcode-select opens a GUI dialog; python3 won't be available immediately
    fi

    if [ -z "$PY" ]; then
        echo ""
        echo "Automatic install failed. Please install Python 3 manually:"
        echo "  https://www.python.org/downloads/"
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

URL="http://localhost:8765"
echo "$URL" | pbcopy 2>/dev/null && echo "📋 URL copied to clipboard: $URL" || echo "   URL: $URL"
echo ""
echo "The browser will open automatically."
echo "Press Ctrl+C to stop."
echo "========================================"
echo ""

(sleep 0.5 && open "$URL") &
$PY serve.py --port 8765

read -p "Press Enter to exit..."
