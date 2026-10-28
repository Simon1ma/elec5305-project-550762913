# ELEC5305 Project - Yixiang Ma (550762913)

## Latency-Quality Trade-offs in Real-Time Causal Speech Enhancement

**Project site:** https://simon1ma.github.io/elec5305-project-550762913/

**Progress updated:** 28 October 2026

Following teacher feedback, the research focus is the latency-quality trade-off of causal enhancement. Wiener filtering is the classical baseline, not a novel algorithm. The second revised milestone adds real keyboard noise, event-level inspection, and an official pretrained DeepFilterNet3 reference to the stateful MATLAB experiment.

[Current results and limitations](results/latency_milestone2/README.md) | [Run the experiment](code/latency/README.md) | [Brief progress description](docs/project_progress2_working_description.md) | [Earlier causal milestone](results/latency_milestone1/README.md)

Both methods receive the same 48 kHz mixtures: 4.5 seconds from one VoiceBank development utterance, either DEMAND washing-machine or ESC-50 keyboard noise at 0 dB SNR, a 300 ms noise-only prefix, and a 100 ms recorded-noise tail. Four Wiener windows (10/20/40/80 ms) are compared. At a comparable 40 ms oldest-sample block-ready delay:

| Noise | Method | Output SNR (dB) | SI-SDR (dB) | STOI |
| --- | --- | --- | --- | --- |
| Washing machine | Noisy | 0.00 | -0.02 | 0.9263 |
| Washing machine | Wiener, 40 ms window | 2.27 | 2.22 | 0.9239 |
| Washing machine | DeepFilterNet3, 20 ms window | 18.90 | 18.97 | 0.9641 |
| Keyboard | Noisy | 0.00 | -0.07 | 0.7280 |
| Keyboard | Wiener, 40 ms window | 2.02 | 1.68 | 0.7020 |
| Keyboard | DeepFilterNet3, 20 ms window | 12.93 | 12.78 | 0.9092 |

These are measured development examples, not a held-out benchmark. No training or fine-tuning was performed. Source inspection, delay probes, and future-input tests support the reference's streaming interpretation; the quoted delay is not measured microphone-to-speaker latency. Backend and output-precision differences are disclosed in the detailed results. The main next step is broader speaker/source-disjoint evaluation at several SNRs.

## Historical Offline Progress (9 October 2026)

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

These were measured results for one synthetic example as of 9 October. They did not establish performance on real speech or improved intelligibility. Later recorded-speech experiments are documented separately above.

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

## Separate Coursework: Audio Processing Report 2

**Temporal Modulation Filtering and Wavelet Analysis of Recorded Speech**

This is an independent MATLAB Live Script report, not the Final Project final submission. It examines 4/8/16 Hz temporal modulation masks, reconstruction fidelity, and continuous wavelet analysis of one recorded speech utterance.

[Report folder](<Report2 YixiangMa/>) | [PDF](<Report2 YixiangMa/Report2 YixiangMa.pdf>) | [MATLAB Live Script](<Report2 YixiangMa/Report2 YixiangMa.mlx>) | [Submission ZIP](<submissions/Report2 YixiangMa.zip>) | [Verification](docs/audio_processing_report2_verification.md)

MATLAB R2026a Update 5 with Signal Processing Toolbox and Wavelet Toolbox was tested. Extract the ZIP, set MATLAB's Current Folder to `Report2 YixiangMa`, open the Live Script, and run all sections. The input audio, source attribution, licence, and custom helpers are included. Generated outputs are recreated locally rather than committed.

## Next Work

Expand beyond the current single development utterance. Separate development and evaluation speakers and noise source recordings before segmenting or mixing, freeze settings on development data, then evaluate at 0, 5, and 10 dB. Examine speech distortion, transient-noise failures, and per-block deadlines. Do not reuse this development utterance as untouched evaluation data.

Full source datasets will not be uploaded. Selected file IDs, channels, segment offsets, and seeds will be documented.
