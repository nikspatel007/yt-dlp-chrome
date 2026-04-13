# yt-dlp Chrome Extension — Audio Downloader

One-click MP3 download from YouTube videos. Adds a download button directly to YouTube pages.

## Quick Start

### 1. Run Setup

**macOS:**

```bash
./setup.sh
```

**Windows:**

```batch
setup.bat
```

This installs uv, yt-dlp, ffmpeg, and creates the download folder.

### 2. Load the Extension

1. Open `chrome://extensions` in Chrome
2. Enable **Developer mode** (toggle in top right)
3. Click **Load unpacked**
4. Select the `extension/` folder from this project

### 3. Start the Server

```bash
cd yt-dlp-chrome
uv run python server.py
```

### 4. Download Audio

1. Go to any YouTube video
2. Click the **MP3** button next to the like/share buttons
3. Wait for it to say **Done!**
4. Find your file in `~/Downloads/yt-dlp-audio/`

## How It Works

- The Chrome extension adds a download button to YouTube pages
- When clicked, it sends the video URL to a local Python server (`localhost:8765`)
- The server uses yt-dlp (as a Python library) to download and convert to 320kbps MP3
- The MP3 file is saved to your Downloads folder

## Troubleshooting

**Button doesn't appear:** Refresh the YouTube page. If it still doesn't appear, check that the extension is enabled in `chrome://extensions`.

**"Server not running" error:** Click the extension icon in the toolbar to see the server status. Start the server with `uv run python server.py`.

**Download fails:** Make sure ffmpeg is installed (`ffmpeg -version`). Re-run the setup script if needed.

## Requirements

- [uv](https://docs.astral.sh/uv/) (installed by setup script)
- ffmpeg
- Google Chrome
