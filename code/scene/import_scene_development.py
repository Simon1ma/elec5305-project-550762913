"""Import nine independent recording takes as a development-only scene dataset."""
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
LOCAL = ROOT / 'data/local/scene/development'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=Path, required=True)
    args = parser.parse_args()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    originals = LOCAL / 'originals'
    decoded = LOCAL / 'wav'
    originals.mkdir(parents=True, exist_ok=True)
    decoded.mkdir(parents=True, exist_ok=True)
    pilot_path = ROOT / 'data/local/scene/pilot/pilot_manifest.json'
    pilot = json.loads(pilot_path.read_text(encoding='utf-8'))['cases'] if pilot_path.exists() else []
    cases = []
    for label, prefix in [('container_press', '瓶子'), ('alarm', '闹钟'), ('speech', '古诗')]:
        for take in [1, 2, 3]:
            source = args.folder / f'{prefix}{take:02}.m4a'
            assert source.is_file(), source
            case_id = f'{label}_{take:02}'
            original = originals / (case_id + '.m4a')
            if original.exists():
                assert sha(original) == sha(source), 'Do not overwrite a different source.'
            else:
                shutil.copy2(source, original)
            target = decoded / (case_id + '.wav')
            subprocess.run([ffmpeg, '-v', 'error', '-y', '-i', str(original), '-map', '0:a:0',
                            '-vn', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le', str(target)],
                           check=True, capture_output=True)
            x, fs = sf.read(target, dtype='float64')
            assert x.ndim == 1 and fs == 48000 and np.isfinite(x).all() and len(x) > fs / 2
            source_hash = sha(original)
            wav_hash = sha(target)
            matches = [c['case_id'] for c in pilot if
                       c['source_sha256'] == source_hash or c['wav_sha256'] == wav_hash]
            cases.append({
                'case_id': case_id, 'label': label, 'take': take, 'development_fold': take,
                'source_filename': source.name, 'source_sha256': source_hash,
                'wav': target.relative_to(ROOT).as_posix(), 'wav_sha256': wav_hash,
                'matches_previous_pilot': matches,
                'duration_seconds': len(x) / fs, 'sample_rate': fs,
                'peak': float(np.max(np.abs(x))),
                'rms_dbfs': float(20 * np.log10(max(np.sqrt(np.mean(x**2)), 1e-12))),
                'full_scale_samples': int(np.sum(np.abs(x) >= 1 - 1 / 32768)),
                'role': 'development', 'recorded_by': 'project author',
            })
    assert len({c['source_sha256'] for c in cases}) == 9, 'Duplicate source files within development set.'
    assert len({c['wav_sha256'] for c in cases}) == 9, 'Duplicate decoded recordings within development set.'
    manifest = {
        'classes': ['container_press', 'alarm', 'speech'],
        'role': 'development only; independent test recordings pending',
        'fold_design': 'Three recording-level folds: hold out take 01, 02 or 03 from every class',
        'physical_sessions': 'Not yet established; take index does not certify session independence',
        'processing': 'Mono 48 kHz PCM24 without gain normalisation; originals retained',
        'cases': cases,
    }
    (LOCAL / 'development_manifest.json').write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for c in cases:
        print(f"{c['case_id']}: {c['duration_seconds']:.2f} s; peak {c['peak']:.3f}; "
              f"pilot matches: {','.join(c['matches_previous_pilot']) or 'none'}")
    print(f"Unique recordings: 9; total duration: {sum(c['duration_seconds'] for c in cases):.2f} seconds")


if __name__ == '__main__':
    main()
