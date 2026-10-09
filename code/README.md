# Preliminary MATLAB Experiment

Run in MATLAB from the repository root:

```matlab
addpath(fullfile(pwd, 'code'));
results = main_preliminary();
```

Or select `code` as MATLAB's current folder and enter `main_preliminary`.

Requires MATLAB with Signal Processing Toolbox (`fir1`, `filtfilt`, `stft`, `istft`, and `spectrogram`). Tested environment and output are recorded in `results/preliminary/run_summary.txt` after execution.

## What It Implements

- Reuses the synthetic speech-like signal from Report 1.
- Mixes white Gaussian noise plus 60/120 Hz hum at exactly 5 dB reference-to-error input SNR.
- Prepends 0.3 seconds of noise for both methods; excludes this prefix from evaluation.
- FIR: order 96, 1200 Hz cutoff, Hamming window, offline forward-backward filtering.
- Wiener: 512-sample periodic Hann, 256-sample hop, 1024-point FFT, initial prefix-only noise estimate, decision-directed alpha 0.98, minimum gain 0.05.
- Uses MATLAB STFT/ISTFT with explicit padding and verifies unit-gain reconstruction before enhancement.
- Does not give the clean reference or ground-truth noise to the Wiener function.
- Calculates SNR before playback scaling. Output error includes speech distortion and residual noise.

`calculate_snr(clean, estimate)` uses a reference signal and an estimated signal; its second argument is **not** a noise vector, unlike the old Report 1 helper with the same name. These functions are in a separate directory from the old report.

## Output

`results/preliminary/` contains `metrics.csv`, `experiment.mat`, a run summary, English-labelled figures, and four WAV files. All WAV files receive the same attenuation to prevent clipping; their playback scale is recorded. Unscaled metric signals are in the MAT file.

The synthetic example is a pipeline demonstration, not evidence of real-speech intelligibility or performance on LibriSpeech/DEMAND. Initial parameters are not tuned on evaluation data. A fixed initial noise estimate may fail on changing noise. No superiority of Wiener over FIR is assumed.

## Verification

```matlab
check_preliminary();
```

This checks multiple non-hop-aligned lengths, reconstruction error, gain bounds, prefix-frame selection, controlled SNR mixing, scoring identities, and repeated-run metrics.

## Implementation References

- [MathWorks STFT](https://www.mathworks.com/help/signal/ref/stft.html)
- [MathWorks ISTFT](https://www.mathworks.com/help/signal/ref/istft.html)
- P. Scalart and J. V. Filho, "Speech enhancement based on a priori signal to noise estimation," ICASSP, 1996, DOI: 10.1109/ICASSP.1996.543199.

The code implements a decision-directed Wiener baseline; it does not implement the full MMSE-STSA estimator.
