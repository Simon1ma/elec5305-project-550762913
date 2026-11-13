"""Connect held-out personal speech/bottle sources to the frozen enhancement study."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys

import numpy as np
import soundfile as sf
from scipy.io import loadmat, savemat

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/scene_bridge'
LOCAL = ROOT / 'data/local/scene_bridge'
sys.path.insert(0, str(ROOT / 'code/final'))
sys.path.insert(0, str(ROOT / 'code/latency'))
from run_final_reference import execute, EXE, MODEL
from evaluate_latency import snr, si_sdr


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = LOCAL / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    sources = json.loads((ROOT / 'data/local/scene/holdout/holdout_manifest.json').read_text(encoding='utf-8'))['cases']
    speeches = [c for c in sources if c['label'] == 'speech']
    noises = [c for c in sources if c['label'] == 'container_press']
    assert len(speeches) == len(noises) == 3
    fs = 48000
    P, N, T = 14400, 384000, 4800
    signals = []
    peak = 0
    for speech in speeches:
        clean, rate = sf.read(ROOT / speech['wav'])
        assert rate == fs and len(clean) >= N
        clean = clean[:N]
        for noise in noises:
            disturbance, rate = sf.read(ROOT / noise['wav'])
            assert rate == fs and len(disturbance) >= P + N + T
            disturbance = disturbance[:P + N + T]
            for snr_db in [0, 5, 10]:
                beta = np.sqrt(np.sum(clean**2) / (10**(snr_db / 10) * np.sum(disturbance[P:P + N]**2)))
                mixture = beta * disturbance
                mixture[P:P + N] += clean
                peak = max(peak, float(np.max(np.abs(mixture))), float(np.max(np.abs(clean))))
                signals.append((speech, noise, snr_db, beta, mixture, clean))
    attenuation = min(1., .8 / peak)
    cases = []
    for speech, noise, snr_db, beta, mixture, clean in signals:
        case_id = f"{speech['case_id']}__{noise['case_id']}__snr{snr_db}"
        x = (mixture * attenuation).astype(np.float32)
        reference = clean * attenuation
        wav = inputs / (case_id + '.wav')
        mat = inputs / (case_id + '.mat')
        sf.write(wav, x, fs, subtype='FLOAT')
        savemat(mat, {'input': x[:, None], 'clean': reference[:, None], 'fs': fs,
                      'prefixSamples': P, 'speechSamples': N,
                      'scaledNoise': (mixture[P:P + N] - clean)[:, None] * attenuation})
        cases.append({'case_id': case_id, 'speech_id': speech['case_id'], 'speaker': 'project_author',
                      'noise_class': 'plastic_bottle', 'noise_source': noise['case_id'],
                      'input_snr_db': snr_db, 'input_wav': wav.relative_to(ROOT).as_posix(),
                      'input_mat': mat.relative_to(ROOT).as_posix(), 'shared_input_sha256': sha(wav),
                      'speech_source_sha256': speech['source_sha256'], 'noise_source_sha256': noise['source_sha256'],
                      'noise_scale': float(beta)})
    manifest = {
        'purpose': 'Personal held-out recordings connect scene analysis to unchanged causal enhancement',
        'fs': fs, 'prefix_samples': P, 'speech_samples': N, 'tail_samples': T,
        'selection': 'First 8 s speech; first 8.4 s continuous bottle source; first 300 ms calibrates Wiener',
        'speech_reference': 'Quiet phone recording, including its original room/microphone background',
        'common_input_attenuation': attenuation, 'speaker_count': 1,
        'classification': 'Separate source recording; no claim of classifying overlapping mixtures',
        'cases': cases,
    }
    assert len(cases) == 27
    (OUT / 'input_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Prepared 27 mixtures from three held-out readings and three bottle recordings; attenuation', attenuation, flush=True)


def reference():
    assert sha(EXE) == '75e11fa16445f560cb6b021521ddb89e89270d13b83089705d98776f58fd7915'
    assert sha(MODEL) == 'c94d91f70911001c946e0fabb4aa9adc37045f45a03b56008cb0c8244cb63616'
    manifest = json.loads((OUT / 'input_manifest.json').read_text())
    destination = LOCAL / 'reference'
    destination.mkdir(parents=True, exist_ok=True)
    checks = []
    for i, case in enumerate(manifest['cases']):
        source = ROOT / case['input_wav']
        assert sha(source) == case['shared_input_sha256']
        result, _, log = execute(source, destination)
        start = 1440 + manifest['prefix_samples']
        assert len(result) >= start + manifest['speech_samples']
        checks.append({'CaseID': case['case_id'], 'TransportShiftSamples': 1440,
                       'FullScaleFlag': bool(np.any(np.abs(result) >= 32767 / 32768)),
                       'OutputSamples': len(result)})
        if (i + 1) % 9 == 0:
            print('Personal reference', i + 1, '/27', flush=True)
    write_csv(OUT / 'reference_checks.csv', checks)


def evaluate():
    from pystoi import stoi
    manifest = json.loads((OUT / 'input_manifest.json').read_text())
    fs, P, N = manifest['fs'], manifest['prefix_samples'], manifest['speech_samples']
    methods = ['Noisy', 'Wiener10', 'Wiener20', 'Wiener40', 'Wiener80', 'DeepFilterNet3']
    rows = []
    for i, case in enumerate(manifest['cases']):
        source = ROOT / case['input_wav']
        assert sha(source) == case['shared_input_sha256']
        x, rate = sf.read(source)
        original = loadmat(ROOT / case['input_mat'], squeeze_me=True)
        assert rate == fs and np.array_equal(x, original['input'])
        result = loadmat(LOCAL / 'wiener' / (case['case_id'] + '.mat'), squeeze_me=True)
        reference, rate = sf.read(LOCAL / 'reference' / source.name)
        assert rate == fs
        neural = reference[1440 + P:1440 + P + N]
        clean = result['clean']
        signals = [x[P:P + N], *[result['outputs'][:, k] for k in range(4)], neural]
        for method, y in zip(methods, signals):
            assert len(y) == N and np.isfinite(y).all()
            rows.append({'CaseID': case['case_id'], 'SpeechID': case['speech_id'],
                         'NoiseSource': case['noise_source'], 'InputSNR_dB': case['input_snr_db'],
                         'Method': method, 'OutputSNR_dB': snr(clean, y), 'SI_SDR_dB': si_sdr(clean, y),
                         'STOI': float(stoi(clean, y, fs, extended=False))})
        if i == 0:
            demo = LOCAL / 'demo'
            demo.mkdir(exist_ok=True)
            gain = .85 / max(np.max(np.abs(y)) for y in [clean, *signals])
            for method, y in zip(['Clean', *methods], [clean, *signals]):
                sf.write(demo / (method + '.wav'), y * gain, fs, subtype='PCM_24')
            (OUT / 'demo_selection.json').write_text(json.dumps({
                'case_id': case['case_id'], 'selection': 'First manifest case, set before outputs',
                'common_playback_gain': float(gain), 'scoring_uses_original_amplitudes': True}, indent=2) + '\n')
    assert len(rows) == 162
    write_csv(OUT / 'metrics.csv', rows)
    summaries = []
    baseline = {r['CaseID']: r for r in rows if r['Method'] == 'Noisy'}
    for snr_db in [0, 5, 10]:
        for method in methods:
            selected = [r for r in rows if r['Method'] == method and r['InputSNR_dB'] == snr_db]
            summaries.append({'InputSNR_dB': snr_db, 'Method': method, 'Mixtures': len(selected),
                              'OutputSNR_dB': float(np.mean([r['OutputSNR_dB'] for r in selected])),
                              'SI_SDR_dB': float(np.mean([r['SI_SDR_dB'] for r in selected])),
                              'STOI': float(np.mean([r['STOI'] for r in selected])),
                              'STOI_lower_than_noisy': sum(r['STOI'] < baseline[r['CaseID']]['STOI'] for r in selected)})
    write_csv(OUT / 'summary_by_snr.csv', summaries)
    error = max(abs(r['OutputSNR_dB'] - r['InputSNR_dB']) for r in rows if r['Method'] == 'Noisy')
    assert error < 1e-5
    (OUT / 'quality_verification.json').write_text(json.dumps({
        'cases': 27, 'metric_rows': 162, 'new_speakers': 1, 'speech_sources': 3, 'bottle_sources': 3,
        'input_snr_max_abs_error_db': error, 'shared_wav_mat_arrays_equal': True,
        'calibration': 'Natural first 300 ms, no event-based selection or calibration retuning',
        'scoring_interval_seconds': 8}, indent=2) + '\n')
    plot_results(summaries)
    for row in summaries:
        if row['InputSNR_dB'] == 0:
            print(row['Method'], f"SNR={row['OutputSNR_dB']:.2f}, STOI={row['STOI']:.4f}", flush=True)
    print('PASS: 162 paired scores; unchanged enhancement methods and exact shared inputs.')


def plot_results(summaries):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, metric in zip(axes, ['OutputSNR_dB', 'STOI']):
        for method in ['Noisy', 'Wiener40', 'Wiener80', 'DeepFilterNet3']:
            group = [r for r in summaries if r['Method'] == method]
            ax.plot([r['InputSNR_dB'] for r in group], [r[metric] for r in group], marker='o', label=method)
        ax.set_xticks([0, 5, 10])
        ax.set_xlabel('Controlled input SNR (dB)')
        ax.set_ylabel('Output SNR (dB)' if metric == 'OutputSNR_dB' else 'STOI')
        ax.grid(alpha=.25)
    axes[0].legend(fontsize=8)
    fig.suptitle('Personal-recording bridge: 3 readings x 3 bottle sources x 3 SNRs')
    fig.tight_layout()
    fig.savefig(OUT / 'personal_enhancement.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'reference', 'evaluate'])
    args = parser.parse_args()
    {'prepare': prepare, 'reference': reference, 'evaluate': evaluate}[args.action]()
