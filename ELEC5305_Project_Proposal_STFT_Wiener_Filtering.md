# Speech Noise Reduction Using STFT-Based Wiener Filtering in Python

## Student Information

- Full Name: Yixiang Ma
- Student ID (SID): 550762913
- GitHub Username: Simon1ma
- GitHub Project Link: https://github.com/Simon1ma/elec5305-project-550762913.git
- GitHub Pages Link: https://simon1ma.github.io/elec5305-project-550762913/

## Project Overview

This project proposes to develop a Python-based speech noise reduction system using short-time Fourier transform (STFT) analysis and Wiener filtering. The main problem addressed is the degradation of speech quality when a speech signal is mixed with background noise, such as fan noise, traffic noise, keyboard noise, or room ambience. This problem is important because noisy speech reduces intelligibility in online meetings, mobile communication, hearing-assistive devices, and automatic speech-processing applications.

The proposed solution is to transform noisy speech into the time-frequency domain using STFT, estimate the noise spectrum, apply a Wiener filtering gain to reduce noisy frequency components, and reconstruct the enhanced signal using inverse STFT and overlap-add synthesis. The project will be implemented in Python so that the full workflow can be reproduced, documented, and demonstrated through a GitHub repository.

## Background and Motivation

Speech enhancement is a classic digital signal processing problem. In many real-world situations, a microphone records both the desired speech and unwanted acoustic noise. Traditional time-domain filtering is often not flexible enough because speech and noise vary over time and frequency. Time-frequency methods are more suitable because they process short frames and apply different attenuation in different frequency bins.

The ELEC5305 tutorial material on STFT, ISTFT, Hann windows, overlap-add, and perfect reconstruction provides the technical foundation for this project. STFT divides a signal into overlapping windowed frames, applies the Fourier transform, and represents the signal as a spectrogram. The inverse process reconstructs the time-domain signal using overlap-add. Correct choice of window and hop size is important because poor reconstruction can introduce distortion before noise reduction is applied.

Wiener filtering is selected because it is a well-established and feasible baseline method for single-channel speech enhancement. Compared with a large neural-network model, it is easier to implement, explain, and evaluate within one semester. It also provides enough technical depth because the project must consider windowing, spectral magnitude estimation, noise power estimation, filtering gains, and objective evaluation metrics.

## Proposed Methodology

The project will be implemented in Python using NumPy, SciPy, librosa or soundfile, and matplotlib. The input data will consist of clean speech recordings and noise recordings. Clean speech will be mixed with noise at selected input signal-to-noise ratio (SNR) levels, such as 0 dB, 5 dB, and 10 dB, to create reproducible noisy test signals.

The first stage will implement STFT analysis. The noisy speech will be divided into overlapping frames using a Hann or square-root Hann window. The project will test a practical frame length, such as 1024 samples, and a hop size such as 512 samples, following the course discussion of time-frequency resolution and reconstruction.

The second stage will estimate the noise power spectrum from leading low-energy frames or from a known noise-only segment. The Wiener gain will then be calculated from the estimated speech and noise spectra. This gain will attenuate frequency bins dominated by noise while keeping bins more likely to contain speech. The noisy phase will be reused for reconstruction, which is common in classical speech enhancement systems.

The third stage will perform inverse STFT and overlap-add synthesis to reconstruct the enhanced waveform. The project will compare the clean, noisy, and enhanced signals using waveform plots, spectrograms, and objective measures. The main evaluation metric will be SNR improvement. If time permits, segmental SNR or perceptual speech quality scores may also be explored.

## Expected Outcomes

The expected outcome is a working Python prototype that demonstrates STFT-based speech enhancement on noisy speech examples. The project should produce clean, noisy, and enhanced audio files, along with spectrogram plots showing how the Wiener filter reduces noise-dominated regions. The report will explain how STFT parameters, window functions, overlap, and reconstruction affect the results.

The project is expected to show measurable SNR improvement for at least some test conditions. It will also identify limitations, such as musical noise, speech distortion, sensitivity to noise estimation, and reduced performance when noise changes rapidly. The GitHub repository will provide documented Python code, example outputs, and a concise demonstration so that the method can be reproduced.

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
