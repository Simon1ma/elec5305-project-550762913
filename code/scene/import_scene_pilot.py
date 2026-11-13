"""Preserve and decode three user-provided pilot recordings without gain changes."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

import imageio_ffmpeg
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / 'data/local/scene/pilot'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--container', '--can', dest='can', type=Path, required=True)
    parser.add_argument('--alarm', type=Path, required=True)
    parser.add_argument('--speech', type=Path, required=True)
    parser.add_argument('--self-recorded', action='store_true',
                        help='The project author confirms personally capturing all three recordings.')
    args = parser.parse_args()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    originals = LOCAL / 'originals'
    decoded = LOCAL / 'wav'
    originals.mkdir(parents=True, exist_ok=True)
    decoded.mkdir(parents=True, exist_ok=True)
    cases = []
    for key, label, source in [('can_press', 'container_press', args.can),
                               ('alarm', 'alarm', args.alarm), ('speech', 'speech', args.speech)]:
        assert source.is_file(), source
        original = originals / (key + source.suffix.lower())
        if original.exists():
            assert sha256(original) == sha256(source), 'Use a new pilot folder for a different source.'
        else:
            shutil.copy2(source, original)
        probe = subprocess.run([ffmpeg, '-hide_banner', '-i', str(original)],
                               capture_output=True, text=True, encoding='utf-8', errors='replace')
        (originals / (key + '_metadata.txt')).write_text(probe.stderr, encoding='utf-8')
        target = decoded / (key + '.wav')
        subprocess.run([ffmpeg, '-v', 'error', '-y', '-i', str(original), '-map', '0:a:0',
                        '-vn', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le', str(target)],
                       check=True, capture_output=True)
        audio, fs = sf.read(target, dtype='float64')
        assert fs == 48000 and audio.ndim == 1 and np.isfinite(audio).all()
        cases.append({
            'case_id': 'pilot_' + key, 'label': label,
            'original_filename': source.name,
            'source_sha256': sha256(original),
            'wav': target.relative_to(ROOT).as_posix(), 'wav_sha256': sha256(target),
            'sample_rate': fs, 'duration_seconds': len(audio) / fs,
            'peak': float(np.max(np.abs(audio))),
            'rms_dbfs': float(20 * np.log10(max(np.sqrt(np.mean(audio**2)), 1e-12))),
            'full_scale_samples': int(np.sum(np.abs(audio) >= 1 - 1 / 32768)),
            'split': 'pilot',
            'recording_origin': ('Author-recorded using a phone; spoken reading performed by the author'
                                 if args.self_recorded else
                                 'User-provided; capture provenance pending confirmation'),
        })
    manifest = {
        'purpose': 'Feature and import pilot; no training/test classification claim',
        'processing': 'First audio stream, mono downmix, 48 kHz PCM24; no gain normalisation',
        'cases': cases,
    }
    path = LOCAL / 'pilot_manifest.json'
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for c in cases:
        print(f"{c['label']}: {c['duration_seconds']:.2f} s, peak {c['peak']:.4f}, "
              f"RMS {c['rms_dbfs']:.2f} dBFS, full-scale samples {c['full_scale_samples']}")
    print('Manifest:', path)


if __name__ == '__main__':
    main()
