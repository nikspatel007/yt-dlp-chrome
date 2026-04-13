#!/bin/bash
set -e

echo "=== yt-dlp Chrome Extension Setup (macOS) ==="
echo ""

# Check/install uv
echo "[1/4] Checking uv..."
if ! command -v uv &> /dev/null; then
    echo "       Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "       uv already installed."
fi

# Install dependencies via uv
echo "[2/4] Installing yt-dlp..."
uv sync

# Install ffmpeg
echo "[3/4] Installing ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "       ffmpeg already installed."
else
    if command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "ERROR: ffmpeg not found and Homebrew is not installed."
        echo "Install Homebrew from https://brew.sh then re-run this script."
        exit 1
    fi
fi

# Create download directory
echo "[4/4] Creating download directory..."
mkdir -p "$HOME/Downloads/yt-dlp-audio"

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Open chrome://extensions in Chrome"
echo "  2. Enable 'Developer mode' (toggle in top right)"
echo "  3. Click 'Load unpacked' and select the extension/ folder"
echo "  4. Start the server: uv run python server.py"
echo "  5. Go to any YouTube video and click the MP3 button!"
echo ""
echo "Downloads will be saved to: $HOME/Downloads/yt-dlp-audio/"
