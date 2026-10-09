# Preliminary Synthetic-Signal Results

These results were generated in MATLAB R2026a Update 5 on 2026-10-09 using `code/main_preliminary.m`. They demonstrate a working FIR and STFT-domain Wiener pipeline, not a completed real-speech evaluation.

## Achieved So Far

- Reproduced the earlier 3-second synthetic speech-like signal at 16 kHz.
- Generated one shared mixture of white Gaussian noise and 60/120 Hz hum at 5 dB input SNR, with random seed 7.
- Removed independent output peak normalisation from metric calculation.
- Implemented the order-96, 1200 Hz Hamming FIR baseline with forward-backward filtering.
- Implemented decision-directed Wiener gains using only 0.3 seconds of initial noise.
- Used MATLAB STFT and ISTFT with explicit padding and checked reconstruction.
- Exported numerical metrics, English-labelled plots, and shared-scale listening examples.

## Measured Results

| Method | Input SNR (dB) | Output SNR (dB) | Improvement (dB) |
| --- | --- | --- | --- |
| Unprocessed | 5.00 | 5.00 | 0.00 |
| FIR | 5.00 | 12.32 | 7.32 |
| Wiener | 5.00 | 17.04 | 12.04 |

Output SNR is `10*log10(sum(clean.^2)/sum((output-clean).^2))`. Metrics exclude the 4800-sample noise-only prefix, use the unscaled outputs, and include both speech distortion and residual noise. The clean reference is used only for mixture generation and scoring, not by `wiener_enhancement`.

The Wiener method has 4.72 dB higher output SNR than FIR in this single example. The plots show that FIR suppresses frequencies above its cutoff, whereas Wiener preserves the low-frequency harmonic pattern and attenuates noise in the inactive intervals. The abrupt syllable gate also produces genuine broadband transients in the clean synthetic signal; these should not be interpreted as recording noise.

This result does not establish improved intelligibility or superiority across real speech, different input SNRs, or nonstationary environmental noises.

## Files

- [Exact metrics](metrics.csv)
- [Execution details](run_summary.txt)
- [Waveforms](figures/waveforms.png)
- [Spectrogram comparison](figures/spectrograms.png)
- [SNR and effective FIR response](figures/snr_and_fir_response.png)
- [Clean audio](audio/clean.wav)
- [Noisy audio](audio/noisy.wav)
- [FIR audio](audio/fir.wav)
- [Wiener audio](audio/wiener.wav)

`experiment.mat` contains unscaled signals, coefficients, configuration, gains, and noise estimates. Audio examples use the same playback attenuation (0.584012533) to prevent clipping, preserving relative levels across methods.

## Verification

`code/check_preliminary.m` passed checks for non-hop-aligned signal lengths, gain bounds, complete prefix-only noise frames, exact 0/5/10 dB mixing, SNR identities, and repeated-run metric equality. Unit-gain reconstruction relative error in the demonstration was approximately 2e-16.

## Remaining Work

Recorded speech and DEMAND noise have not been evaluated. Next steps are speaker-separated development/evaluation subsets, fixed-parameter evaluation at 0/5/10 dB, segmental SNR, and analysis of noise-estimation errors and speech distortion. Current alpha 0.98 and gain floor 0.05 are initial settings, not optimised final parameters.
