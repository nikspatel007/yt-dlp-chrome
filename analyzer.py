"""Audio analysis module: BPM, key, waveform, and phrase detection."""

import numpy as np
import librosa


# Camelot wheel mapping: (pitch_class_index, mode) -> camelot notation
# pitch_class_index: 0=C, 1=C#, 2=D, ..., 11=B
# mode: 'minor' or 'major'
CAMELOT_MAP = {
    (8, 'minor'): '1A',   (11, 'major'): '1B',
    (3, 'minor'): '2A',   (6, 'major'): '2B',
    (10, 'minor'): '3A',  (1, 'major'): '3B',
    (5, 'minor'): '4A',   (8, 'major'): '4B',
    (0, 'minor'): '5A',   (3, 'major'): '5B',
    (7, 'minor'): '6A',   (10, 'major'): '6B',
    (2, 'minor'): '7A',   (5, 'major'): '7B',
    (9, 'minor'): '8A',   (0, 'major'): '8B',
    (4, 'minor'): '9A',   (7, 'major'): '9B',
    (11, 'minor'): '10A', (2, 'major'): '10B',
    (6, 'minor'): '11A',  (9, 'major'): '11B',
    (1, 'minor'): '12A',  (4, 'major'): '12B',
}

PHRASE_COLORS = {
    'intro': '#1565c0',
    'outro': '#1565c0',
    'verse': '#7b1fa2',
    'build': '#e65100',
    'chorus': '#2e7d32',
    'breakdown': '#c62828',
}


def detect_bpm(y, sr):
    """Detect BPM using librosa beat tracking."""
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    if hasattr(tempo, '__len__'):
        return round(float(tempo[0]))
    return round(float(tempo))


def detect_key(y, sr):
    """Detect musical key and return Camelot notation."""
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    pitch_class = int(np.argmax(chroma_mean))
    major_third = (pitch_class + 4) % 12
    minor_third = (pitch_class + 3) % 12
    if chroma_mean[major_third] >= chroma_mean[minor_third]:
        mode = 'major'
    else:
        mode = 'minor'
    return CAMELOT_MAP.get((pitch_class, mode), '?')


def compute_waveform(y, num_points=200):
    """Compute normalized RMS waveform downsampled to num_points."""
    chunk_size = len(y) // num_points
    if chunk_size == 0:
        return [0.0] * num_points
    rms_values = []
    for i in range(num_points):
        start = i * chunk_size
        end = start + chunk_size
        chunk = y[start:end]
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        rms_values.append(rms)
    max_rms = max(rms_values) if rms_values else 1.0
    if max_rms == 0:
        return [0.0] * num_points
    return [round(v / max_rms, 3) for v in rms_values]


def detect_phrases(y, sr, duration):
    """Detect song structure phrases using energy-based segmentation."""
    rms = librosa.feature.rms(y=y)[0]
    if len(rms) == 0 or duration == 0:
        return [{'type': 'verse', 'start': 0.0, 'end': duration}]
    kernel_size = min(50, len(rms) // 4)
    if kernel_size > 1:
        kernel = np.ones(kernel_size) / kernel_size
        rms_smooth = np.convolve(rms, kernel, mode='same')
    else:
        rms_smooth = rms
    num_segments = min(10, max(4, int(duration / 30)))
    try:
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=12)
        bounds = librosa.segment.agglomerative(mfcc, k=num_segments)
        bound_times = librosa.frames_to_time(bounds, sr=sr)
    except Exception:
        bound_times = np.linspace(0, duration, num_segments + 1)[1:-1]
    all_boundaries = [0.0] + sorted(bound_times.tolist()) + [duration]
    segments = []
    for i in range(len(all_boundaries) - 1):
        start = all_boundaries[i]
        end = all_boundaries[i + 1]
        start_frame = int(start / duration * len(rms_smooth))
        end_frame = int(end / duration * len(rms_smooth))
        start_frame = max(0, min(start_frame, len(rms_smooth) - 1))
        end_frame = max(start_frame + 1, min(end_frame, len(rms_smooth)))
        seg_energy = float(np.mean(rms_smooth[start_frame:end_frame]))
        segments.append({'start': round(start, 1), 'end': round(end, 1), 'energy': seg_energy})
    if not segments:
        return [{'type': 'verse', 'start': 0.0, 'end': duration}]
    energies = [s['energy'] for s in segments]
    max_energy = max(energies) if energies else 1.0
    if max_energy == 0:
        max_energy = 1.0
    phrases = []
    for i, seg in enumerate(segments):
        rel_energy = seg['energy'] / max_energy
        is_first = (i == 0)
        is_last = (i == len(segments) - 1)
        is_build = False
        if i < len(segments) - 1:
            next_energy = segments[i + 1]['energy'] / max_energy
            if next_energy - rel_energy > 0.2 and rel_energy < 0.8:
                is_build = True
        if is_first and rel_energy < 0.6:
            phrase_type = 'intro'
        elif is_last and rel_energy < 0.6:
            phrase_type = 'outro'
        elif is_build:
            phrase_type = 'build'
        elif rel_energy >= 0.75:
            phrase_type = 'chorus'
        elif rel_energy < 0.4 and not is_first and not is_last:
            phrase_type = 'breakdown'
        else:
            phrase_type = 'verse'
        phrases.append({'type': phrase_type, 'start': seg['start'], 'end': seg['end']})
    return phrases


def analyze_mp3(filepath):
    """Run full analysis on an MP3 file. Returns dict with bpm, key, waveform, phrases, duration."""
    print(f'  🎵 Analyzing: {filepath}', flush=True)
    y, sr = librosa.load(filepath, sr=22050, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))
    bpm = detect_bpm(y, sr)
    key = detect_key(y, sr)
    waveform = compute_waveform(y)
    phrases = detect_phrases(y, sr, duration)
    print(f'  🎵 Analysis complete: {bpm} BPM, key {key}, {len(phrases)} phrases', flush=True)
    return {
        'bpm': bpm,
        'key': key,
        'waveform': waveform,
        'phrases': phrases,
        'duration': round(duration, 1),
    }
