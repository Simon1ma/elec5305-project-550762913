# ELEC5305 Project Progress

**Name:** Yixiang Ma

**SID:** 550762913

**Project:** Comparative Evaluation of FIR and STFT-Domain Wiener Filtering for Speech Enhancement in MATLAB

**GitHub Project Site:** https://simon1ma.github.io/elec5305-project-550762913/

The project compares a fixed FIR low-pass baseline with STFT-domain Wiener filtering for speech enhancement. So far, a reproducible MATLAB pipeline has been implemented and tested using a three-second synthetic speech-like signal at 16 kHz. The signal is mixed with white Gaussian noise and 60/120 Hz hum at 5 dB input SNR. Both enhancement methods receive the same mixture.

The FIR baseline uses an order-96 Hamming-window filter with a 1200 Hz cutoff and forward-backward filtering. The Wiener method estimates noise power from an initial 0.3-second noise-only segment and applies decision-directed spectral gains before inverse STFT. The clean reference is used for evaluation, not by the enhancement algorithm.

In this preliminary example, FIR achieves 12.32 dB output SNR and Wiener achieves 17.04 dB, corresponding to improvements of 7.32 and 12.04 dB. Reconstruction and repeatability checks passed. The project site contains runnable code, metrics, waveform and spectrogram comparisons, audio examples, and limitations.

These results concern one synthetic example only. Next steps are evaluation on recorded speech and environmental noise, comparisons across input SNRs, and analysis of speech distortion and changing-noise conditions. Feedback will inform the experimental design and subsequent improvements.
