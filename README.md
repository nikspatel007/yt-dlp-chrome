# yt-dlp Chrome Extension — Audio Downloader

One-click MP3 download from YouTube videos. A Chrome extension popup backed by a local Python server that uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) as a library.

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
2. Click the extension icon in Chrome's toolbar
3. Click **Download MP3 (320kbps)**
4. Find your file in `~/Downloads/yt-dlp-audio/`

Click any completed download in the history to reveal it in Finder.

## How It Works

- The Chrome extension detects when you're on a YouTube video page
- Click the extension icon to open the popup with a download button
- The popup sends the video URL to a local Python server (`localhost:8765`)
- The server uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) (as a Python library) to download and convert to 320kbps MP3
- The MP3 file is saved to your Downloads folder

## Troubleshooting

**"Server not running" error:** Click the extension icon in the toolbar to see the server status. Start the server with `uv run python server.py`.

**Download fails:** Make sure ffmpeg is installed (`ffmpeg -version`). Re-run the setup script if needed.

**YouTube bot detection:** The server uses your Chrome cookies for authentication. Make sure you're signed into YouTube in Chrome.

## Requirements

- [uv](https://docs.astral.sh/uv/) (installed by setup script)
- ffmpeg
- Google Chrome

## Acknowledgments

This project is a UI wrapper around the following open-source tools:

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** — Feature-rich command-line audio/video downloader. Licensed under the [Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE).
- **[yt-dlp-ejs](https://github.com/yt-dlp/ejs)** — JavaScript challenge solver for YouTube. Licensed under the [Unlicense](https://github.com/yt-dlp/ejs/blob/main/LICENSE).
- **[ffmpeg](https://ffmpeg.org)** — Audio/video processing toolkit. License [depends on the build](https://www.ffmpeg.org/legal.html).

## License

This project is released into the public domain under the [Unlicense](LICENSE), the same license used by yt-dlp.

See the [Unlicense](http://unlicense.org/) for details.

## Disclaimer

This tool is intended for downloading content you have the right to download. Respect copyright laws and YouTube's Terms of Service. The authors are not responsible for any misuse of this software.
