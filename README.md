# elec5305-project-550762913

## Speech Noise Reduction Using STFT-Based Wiener Filtering in Python

This repository contains the ELEC5305 project proposal and future implementation files for a Python-based speech noise reduction system.

The proposed project uses short-time Fourier transform (STFT), Wiener filtering, and inverse STFT overlap-add reconstruction to reduce additive background noise in speech recordings. The final implementation will compare clean, noisy, and enhanced speech using waveform plots, spectrograms, and SNR improvement.

## Project Information

- Course: ELEC5305
- Student Name: Yixiang Ma
- Student ID: 550762913
- GitHub Username: Simon1ma
- Repository: https://github.com/Simon1ma/elec5305-project-550762913.git
- Project Website: https://simon1ma.github.io/elec5305-project-550762913/
- Topic: Speech enhancement and noise reduction
- Main tools: Python, NumPy, SciPy, librosa or soundfile, matplotlib

## Proposal

The current project proposal is provided in:

- `ELEC5305_Project_Proposal_Yixiang_Ma_550762913.pdf`
- `ELEC5305_Project_Proposal_STFT_Wiener_Filtering.md`

The proposal describes the project motivation, STFT-based methodology, expected outcomes, timeline, and academic references.

## Planned Repository Contents

- Project proposal PDF
- Python implementation scripts or notebooks
- Example speech/noise samples or data-loading instructions
- Spectrogram and waveform comparison figures
- Evaluation results and final report

## Planned Method

1. Mix clean speech with background noise at controlled SNR levels.
2. Convert the noisy signal to the time-frequency domain using STFT.
3. Estimate the noise spectrum from low-energy or noise-only frames.
4. Apply a Wiener filtering gain to reduce noise-dominated frequency bins.
5. Reconstruct the enhanced speech signal using inverse STFT and overlap-add.
6. Evaluate the result using SNR improvement and spectrogram comparisons.

## GitHub Pages

The intended GitHub Pages URL is:

https://simon1ma.github.io/elec5305-project-550762913/

If GitHub displays a different Pages URL after enabling Pages in repository settings, the displayed URL should be used as the final project website link.
