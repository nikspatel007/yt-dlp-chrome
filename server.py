#!/usr/bin/env python3
"""Local HTTP server for yt-dlp Chrome extension.

Listens on localhost:8765. Accepts download requests from the Chrome extension
and uses yt-dlp as a library to download YouTube audio as 320kbps MP3.

Usage: python server.py
"""

import json
import os
import platform
import re
import subprocess
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path

import yt_dlp


def get_download_dir():
    """Return platform-appropriate download directory."""
    if platform.system() == 'Windows':
        base = Path(os.environ.get('USERPROFILE', Path.home()))
    else:
        base = Path.home()
    dl_dir = base / 'Downloads' / 'yt-dlp-audio'
    dl_dir.mkdir(parents=True, exist_ok=True)
    return str(dl_dir)


# Track active downloads to prevent duplicates
active_downloads = set()
active_downloads_lock = threading.Lock()

# Download history: list of {title, filename, status, timestamp, url}
download_history = []
download_history_lock = threading.Lock()
MAX_HISTORY = 50

YOUTUBE_URL_RE = re.compile(
    r'^https?://(www\.|m\.)?(youtube\.com/watch\?|youtu\.be/)'
)


def download_audio(url):
    """Download audio from URL as 320kbps MP3 using yt-dlp library."""
    def progress_hook(d):
        if d['status'] == 'downloading':
            pct = d.get('_percent_str', '?').strip()
            speed = d.get('_speed_str', '?').strip()
            print(f'  ↓ {pct} at {speed}', flush=True)
        elif d['status'] == 'finished':
            print(f'  ↓ Download complete, converting to MP3...', flush=True)

    ydl_opts = {
        'format': 'ba/b',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'paths': {'home': get_download_dir()},
        'outtmpl': '%(title)s.%(ext)s',
        'cookiesfrombrowser': ('chrome',),
        'noplaylist': True,
        'progress_hooks': [progress_hook],
    }

    print(f'⬇ Starting download: {url}', flush=True)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'Unknown')
        filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
        print(f'✓ Done: {title}', flush=True)
        print(f'  Saved to: {filename}', flush=True)
        return {
            'status': 'ok',
            'title': title,
            'filename': filename,
        }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self._send_json({})

    def do_GET(self):
        if self.path == '/health':
            with active_downloads_lock:
                downloading = list(active_downloads)
            self._send_json({'status': 'ok', 'active': len(downloading)})
        elif self.path == '/downloads':
            with download_history_lock:
                history = list(download_history)
            with active_downloads_lock:
                active = list(active_downloads)
            self._send_json({'active': active, 'history': history})
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        if self.path == '/reveal':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length))
                filepath = body.get('filename', '')
                if filepath and os.path.exists(filepath):
                    if platform.system() == 'Darwin':
                        subprocess.Popen(['open', '-R', filepath])
                    elif platform.system() == 'Windows':
                        subprocess.Popen(['explorer', '/select,', filepath])
                    self._send_json({'status': 'ok'})
                else:
                    self._send_json({'status': 'error', 'message': 'File not found'}, 404)
            except Exception as e:
                self._send_json({'status': 'error', 'message': str(e)}, 500)
            return

        if self.path != '/download':
            self._send_json({'error': 'Not found'}, 404)
            return

        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            self._send_json({'status': 'error', 'message': 'Invalid JSON'}, 400)
            return

        url = body.get('url', '').strip()
        if not url:
            self._send_json({'status': 'error', 'message': 'No URL provided'}, 400)
            return

        if not YOUTUBE_URL_RE.match(url):
            self._send_json({'status': 'error', 'message': 'Not a valid YouTube URL'}, 400)
            return

        with active_downloads_lock:
            if url in active_downloads:
                self._send_json({'status': 'error', 'message': 'Already downloading this URL'}, 409)
                return
            active_downloads.add(url)

        try:
            result = download_audio(url)
            with download_history_lock:
                download_history.insert(0, {
                    'title': result.get('title', 'Unknown'),
                    'filename': result.get('filename', ''),
                    'status': 'ok',
                    'timestamp': time.time(),
                })
                del download_history[MAX_HISTORY:]
            self._send_json(result)
        except Exception as e:
            print(f'✗ Error: {e}', flush=True)
            with download_history_lock:
                download_history.insert(0, {
                    'title': url,
                    'filename': '',
                    'status': 'error',
                    'error': str(e),
                    'timestamp': time.time(),
                })
                del download_history[MAX_HISTORY:]
            self._send_json({'status': 'error', 'message': str(e)}, 500)
        finally:
            with active_downloads_lock:
                active_downloads.discard(url)

    def log_message(self, format, *args):
        """Suppress default request logging."""
        pass


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def check_dependencies():
    """Check that required dependencies are installed before starting."""
    ok = True

    # Check yt-dlp
    try:
        import yt_dlp
        print(f'  yt-dlp {yt_dlp.version.__version__}')
    except ImportError:
        print('  yt-dlp ............ NOT FOUND')
        print('    Install with: uv add yt-dlp')
        ok = False

    # Check ffmpeg
    import shutil
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        print(f'  ffmpeg ............ {ffmpeg_path}')
    else:
        print('  ffmpeg ............ NOT FOUND')
        if platform.system() == 'Darwin':
            print('    Install with: brew install ffmpeg')
        elif platform.system() == 'Windows':
            print('    Install with: choco install ffmpeg')
        else:
            print('    Install ffmpeg from https://ffmpeg.org/download.html')
        ok = False

    # Check ffprobe
    ffprobe_path = shutil.which('ffprobe')
    if ffprobe_path:
        print(f'  ffprobe ........... {ffprobe_path}')
    else:
        print('  ffprobe ........... NOT FOUND (usually installed with ffmpeg)')
        ok = False

    return ok


def main():
    print('Checking dependencies...')
    if not check_dependencies():
        print('\nMissing dependencies. Please install them and try again.')
        return

    print()
    host = '127.0.0.1'
    port = 8765
    server = ThreadedHTTPServer((host, port), Handler)
    print(f'yt-dlp server running on http://{host}:{port}')
    print(f'Downloads will be saved to: {get_download_dir()}')
    print('Press Ctrl+C to stop\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
        server.server_close()


if __name__ == '__main__':
    main()
