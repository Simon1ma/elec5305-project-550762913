# Speech Noise Reduction Using STFT-Based Wiener Filtering in Python

## Student Information

- Full Name: Yixiang Ma
- Student ID (SID): 550762913
- GitHub Username: Simon1ma
- GitHub Project Link: https://github.com/Simon1ma/elec5305-project-550762913.git
- GitHub Pages Link: https://simon1ma.github.io/elec5305-project-550762913/

## Project Overview

In this project, I plan to build a Python-based speech noise reduction system using short-time Fourier transform (STFT) analysis and Wiener filtering. The problem I want to study is what happens when speech is mixed with everyday background noise, such as fan noise, traffic noise, keyboard noise, or room ambience. This is practical because noisy speech can make online meetings, mobile calls, hearing-assistive devices, and speech-processing systems harder to use.

My proposed solution is to transform noisy speech into the time-frequency domain using STFT, estimate the noise spectrum, apply a Wiener filtering gain to reduce noisy frequency components, and reconstruct the enhanced signal using inverse STFT and overlap-add synthesis. I will use Python because it is convenient for audio experiments, plotting, and sharing reproducible code through GitHub.

## Background and Motivation

I chose speech enhancement because it is a signal processing problem that can be heard and visualised, not only calculated. In many real-world situations, a microphone records both the desired speech and unwanted acoustic noise. A simple time-domain filter is often not flexible enough because speech and noise change over time and frequency. Time-frequency methods are more suitable because they process short frames and apply different attenuation in different frequency bins.

This topic also connects directly with the ELEC5305 Week 4 tutorial on STFT, ISTFT, Hann windows, overlap-add, and perfect reconstruction. Before working through this material, I mainly thought about filtering as a time-domain operation. The tutorial made me more interested in how a signal can be changed in the time-frequency domain and then reconstructed back into a waveform. STFT divides a signal into overlapping windowed frames, applies the Fourier transform, and represents the signal as a spectrogram. The inverse process reconstructs the time-domain signal using overlap-add.

I chose Wiener filtering because it is a well-established and feasible baseline method for single-channel speech enhancement. Compared with a large neural-network model, it is easier to implement, explain, and evaluate within one semester. It still has enough technical depth because I need to consider windowing, spectral magnitude estimation, noise power estimation, filtering gains, and objective evaluation metrics. A challenge will be choosing suitable STFT parameters, because a longer window gives better frequency resolution but poorer time resolution.

## Proposed Methodology

I will implement the project in Python using NumPy, SciPy, librosa or soundfile, and matplotlib. I plan to begin with short speech clips and simple background noises, such as fan noise, keyboard noise, or traffic noise, rather than a very large dataset. Clean speech will be mixed with noise at selected input signal-to-noise ratio (SNR) levels, such as 0 dB, 5 dB, and 10 dB, to create reproducible noisy test signals.

The first stage will implement STFT analysis. The noisy speech will be divided into overlapping frames using a Hann or square-root Hann window. I will test a practical frame length, such as 1024 samples, and a hop size such as 512 samples, following the course discussion of time-frequency resolution and reconstruction.

The second stage will estimate the noise power spectrum from leading low-energy frames or from a known noise-only segment. The Wiener gain will then be calculated from the estimated speech and noise spectra. This gain should reduce frequency bins dominated by noise while keeping bins more likely to contain speech. I will reuse the noisy phase for reconstruction, which is a common starting point in classical speech enhancement.

The third stage will perform inverse STFT and overlap-add synthesis to reconstruct the enhanced waveform. I will compare the clean, noisy, and enhanced signals using waveform plots, spectrograms, and objective measures. The main evaluation metric will be SNR improvement. If time permits, I may also explore segmental SNR or perceptual speech quality scores.

## Expected Outcomes

The expected outcome is a working Python prototype that demonstrates STFT-based speech enhancement on noisy speech examples. I expect to produce clean, noisy, and enhanced audio files, along with spectrogram plots showing how the Wiener filter changes noise-dominated regions. The report will explain how STFT parameters, window functions, overlap, and reconstruction affect the results.

I expect the method to improve SNR in simple noise conditions, although it may not work well when the noise changes quickly. I will also discuss limitations such as musical noise, speech distortion, and sensitivity to the noise estimate. The GitHub repository will provide documented Python code, example outputs, and a concise demonstration so that the method can be reproduced.

## Timeline

| Week | Task |
| --- | --- |
| 1-2 | Select and refine the speech enhancement topic; create GitHub repository |
| 3-5 | Review literature on STFT, Wiener filtering, and speech enhancement; collect speech and noise samples |
| 6-9 | Implement STFT, noise mixing, Wiener filtering, ISTFT, and initial tests in Python |
| 10-11 | Evaluate SNR improvement, tune parameters, and generate waveform/spectrogram comparisons |
| 12-13 | Finalise report, clean up GitHub documentation, and prepare demonstration |

## References

1. P. C. Loizou, *Speech Enhancement: Theory and Practice*, 2nd ed. Boca Raton, FL, USA: CRC Press, 2013.
2. Y. Ephraim and D. Malah, "Speech enhancement using a minimum mean-square error short-time spectral amplitude estimator," *IEEE Transactions on Acoustics, Speech, and Signal Processing*, vol. 32, no. 6, pp. 1109-1121, 1984.
3. P. Scalart and J. V. Filho, "Speech enhancement based on a priori signal to noise estimation," in *Proceedings of the 1996 IEEE International Conference on Acoustics, Speech, and Signal Processing*, 1996, pp. 629-632.
4. C. K. A. Reddy et al., "The INTERSPEECH 2021 Deep Noise Suppression Challenge," in *Proceedings of INTERSPEECH*, 2021.
5. S. F. Boll, "Suppression of acoustic noise in speech using spectral subtraction," *IEEE Transactions on Acoustics, Speech, and Signal Processing*, vol. 27, no. 2, pp. 113-120, 1979.
6. J. S. Lim and A. V. Oppenheim, "Enhancement and bandwidth compression of noisy speech," *Proceedings of the IEEE*, vol. 67, no. 12, pp. 1586-1604, 1979.
