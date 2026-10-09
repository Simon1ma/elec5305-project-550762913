# ELEC5305 Project - Yixiang Ma (550762913)

## Comparative Evaluation of FIR and STFT-Domain Wiener Filtering for Speech Enhancement in MATLAB

**Project site:** https://simon1ma.github.io/elec5305-project-550762913/

**Progress updated:** 9 October 2026

This project compares a fixed FIR low-pass baseline with STFT-domain Wiener filtering. The initial Python proposal has evolved into a MATLAB implementation, extending the synthetic-signal work from Audio Processing Report 1. The previous proposal is retained as a historical planning document.

## Implemented and Verified

- A reproducible 3-second synthetic speech-like signal at 16 kHz.
- Controlled mixing with white Gaussian noise and 60/120 Hz hum at 5 dB input SNR.
- Order-96 FIR baseline, 1200 Hz cutoff, Hamming window, and offline forward-backward filtering.
- Decision-directed STFT-domain Wiener enhancement using an initial 0.3-second noise-only prefix.
- Signal reconstruction checks, shared-input comparison, plots, metrics, and audio examples.
- Reference-to-error SNR on unnormalised outputs, excluding the noise-only prefix.

| Method | Input SNR (dB) | Output SNR (dB) | Improvement (dB) |
| --- | --- | --- | --- |
| Unprocessed | 5.00 | 5.00 | 0.00 |
| FIR | 5.00 | 12.32 | 7.32 |
| Wiener | 5.00 | 17.04 | 12.04 |

These are measured results for one synthetic example. They do not establish performance on real speech or improved intelligibility. No LibriSpeech or DEMAND experiments have been completed yet.

[Detailed results and limitations](results/preliminary/README.md) | [Code and execution instructions](code/README.md) | [Brief progress submission](docs/project_progress_submission.md)

## Run in MATLAB

Requires MATLAB with Signal Processing Toolbox. From the repository root:

```matlab
addpath(fullfile(pwd, 'code'));
results = main_preliminary();
```

Run `check_preliminary()` for reconstruction, length, gain, prefix-selection, SNR-mixing, and repeatability checks. The tested MATLAB version is R2026a Update 5.

## Repository Contents

- `code/`: runnable MATLAB implementation, configuration, and checks.
- `results/preliminary/`: actual numerical outputs, English-labelled plots, audio examples, and unscaled signals in a MAT file.
- `docs/`: progress submission description.
- `index.md`: GitHub Pages project overview.

## Next Work

Collect a small subset of recorded speech from [LibriSpeech](https://www.openslr.org/12/) and environmental noise from [DEMAND](https://zenodo.org/records/1227121). Separate development and evaluation speakers, select parameters on development data, then evaluate fixed settings at 0, 5, and 10 dB. Add segmental SNR and investigate speech distortion and changing-noise failures.

Full source datasets will not be uploaded. Selected file IDs, channels, segment offsets, and seeds will be documented.
