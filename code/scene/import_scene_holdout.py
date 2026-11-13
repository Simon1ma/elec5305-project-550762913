"""Read the nine 04-06 recordings from an archive; preserve frozen-model provenance."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import zipfile

import imageio_ffmpeg
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / 'data/local/scene/holdout'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    definition = json.loads((ROOT / 'results/scene_advanced/model_definition.json').read_text())
    model = ROOT / 'data/local/scene/advanced/advanced_models.joblib'
    assert sha(model) == definition['model_sha256'], 'Frozen model has changed.'
    for name, digest in definition['code_sha256'].items():
        assert sha(ROOT / 'code/scene' / name) == digest, f'Frozen feature/model code changed: {name}'
    development = json.loads((ROOT / 'data/local/scene/development/development_manifest.json').read_text(encoding='utf-8'))
    old_source = {c['source_sha256'] for c in development['cases']}
    old_audio = {c['wav_sha256'] for c in development['cases']}
    originals = LOCAL / 'originals'
    decoded = LOCAL / 'wav'
    originals.mkdir(parents=True, exist_ok=True)
    decoded.mkdir(parents=True, exist_ok=True)
    cases = []
    with zipfile.ZipFile(args.archive) as archive:
        assert archive.testzip() is None
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            # Read members only; never extract archive paths onto the filesystem.
            name = Path(entry.filename.replace('\\', '/')).name
            match = re.fullmatch(r'(瓶子|闹钟|朗读|古诗)(0[456])\.m4a', name, re.IGNORECASE)
            assert match and entry.file_size < 100_000_000, f'Unexpected archive member: {name}'
            label = {'瓶子': 'container_press', '闹钟': 'alarm', '朗读': 'speech', '古诗': 'speech'}[match[1]]
            take = int(match[2])
            case_id = f'{label}_{take:02}'
            payload = archive.read(entry)
            original = originals / (case_id + '.m4a')
            if original.exists():
                assert original.read_bytes() == payload, 'Do not overwrite another source.'
            else:
                original.write_bytes(payload)
            target = decoded / (case_id + '.wav')
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-y', '-i', str(original),
                            '-map', '0:a:0', '-vn', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le', str(target)],
                           check=True, capture_output=True)
            x, fs = sf.read(target)
            assert fs == 48000 and x.ndim == 1 and np.isfinite(x).all() and len(x) > fs / 2
            assert sha(original) not in old_source, 'A development source was resubmitted as test.'
            assert sha(target) not in old_audio, 'Decoded audio duplicates a development recording.'
            cases.append({'case_id': case_id, 'label': label, 'take': take, 'source_filename': name,
                          'source_sha256': sha(original), 'wav_sha256': sha(target),
                          'wav': target.relative_to(ROOT).as_posix(), 'sample_rate': fs,
                          'duration_seconds': len(x) / fs, 'peak': float(np.max(np.abs(x))),
                          'rms_dbfs': float(20 * np.log10(max(np.sqrt(np.mean(x**2)), 1e-12))),
                          'full_scale_samples': int(np.sum(np.abs(x) >= 1 - 1 / 32768)),
                          'role': 'holdout', 'recorded_by': 'project author'})
    expected = {(label, take) for label in ['alarm', 'container_press', 'speech'] for take in [4, 5, 6]}
    assert {(c['label'], c['take']) for c in cases} == expected and len(cases) == 9
    assert len({c['source_sha256'] for c in cases}) == len({c['wav_sha256'] for c in cases}) == 9
    cases.sort(key=lambda c: (c['label'], c['take']))
    manifest = {
        'role': 'new-recording holdout; frozen models only',
        'archive_sha256': sha(args.archive), 'frozen_model_sha256': sha(model),
        'acquisition': {'recorded_by': 'project author', 'same_phone_as_development': True,
                        'room': 'bedroom', 'distance': 'at most 0.5 m',
                        'alarm_content': 'one previous tone retained; other content changed',
                        'physical_bottle_identity': 'not separately specified',
                        'notes_source': 'author confirmation, 7 November 2026'},
        'cases': cases,
    }
    (LOCAL / 'holdout_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for case in cases:
        print(case['case_id'], f"{case['duration_seconds']:.2f}s", f"peak={case['peak']:.3f}")
    print('PASS: nine unique test sources, disjoint from development; frozen model/code unchanged.')


if __name__ == '__main__':
    main()
