"""Library persistence: read/write library.json in the download folder."""

import json
import os
import threading


class Library:
    """Thread-safe library backed by a JSON file."""

    def __init__(self, download_dir):
        self.filepath = os.path.join(download_dir, 'library.json')
        self.tracks = []
        self.lock = threading.Lock()
        self._load()

    def _load(self):
        """Load library from disk if it exists."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                self.tracks = data.get('tracks', [])
                print(f'  📚 Loaded {len(self.tracks)} tracks from library.json')
            except (json.JSONDecodeError, IOError) as e:
                print(f'  ⚠ Failed to load library.json: {e}')
                self.tracks = []
        else:
            print('  📚 No library.json found, starting fresh')

    def _save(self):
        """Write library to disk. Must be called with lock held."""
        try:
            with open(self.filepath, 'w') as f:
                json.dump({'tracks': self.tracks}, f, indent=2)
        except IOError as e:
            print(f'  ⚠ Failed to save library.json: {e}')

    def add_track(self, track_data):
        """Add a track to the library and save to disk."""
        with self.lock:
            self.tracks = [t for t in self.tracks if t.get('url') != track_data.get('url')]
            self.tracks.insert(0, track_data)
            self._save()

    def get_tracks(self):
        """Return a copy of all tracks."""
        with self.lock:
            return list(self.tracks)

    def get_history_for_api(self):
        """Return tracks formatted for the /downloads API response."""
        with self.lock:
            return [
                {
                    'title': t.get('title', 'Unknown'),
                    'filename': t.get('filename', ''),
                    'status': t.get('status', 'ok'),
                    'error': t.get('error', ''),
                    'timestamp': t.get('downloaded_at', 0),
                    'bpm': t.get('bpm'),
                    'key': t.get('key'),
                    'waveform': t.get('waveform'),
                    'phrases': t.get('phrases'),
                    'duration': t.get('duration'),
                    'url': t.get('url', ''),
                }
                for t in self.tracks
            ]
