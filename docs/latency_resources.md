# Literature and Resource Map for the Revised Project

Checked: 28 October 2026. A resource or a paper is not evidence that its model has already been run in this project.

## Classical Spectral Enhancement

P. Scalart and J. V. Filho, "Speech enhancement based on a priori signal to noise estimation," ICASSP, 1996. [DOI](https://doi.org/10.1109/ICASSP.1996.543199).

Role: decision-directed a priori SNR estimation for the classical Wiener baseline. The current implementation is a simple baseline and does not claim to reproduce TSNR or HRNR systems.

## Full-Band Real-Time Enhancement

H. Schroter, A. N. Escalante-B., T. Rosenkranz, and A. Maier, "DeepFilterNet2: Towards Real-Time Speech Enhancement on Embedded Devices for Full-Band Audio," 2022. [Author manuscript](https://arxiv.org/abs/2205.05474).

H. Schroter, T. Rosenkranz, A. N. Escalante-B., and A. Maier, "DeepFilterNet: Perceptually Motivated Real-Time Speech Enhancement," 2023. [Author manuscript](https://arxiv.org/abs/2305.08227).

Role: modern low-complexity full-band enhancement and pretrained reference context. Published RTF values belong to the authors' configurations and hardware; they must not be copied into this project's measured comparison table. Inspect the selected model's configuration, frame buffering, lookahead, and streaming code before reporting its latency.

[Official DeepFilterNet code and models](https://github.com/Rikorose/DeepFilterNet).

## Objective Evaluation

J. Le Roux, S. Wisdom, H. Erdogan, and J. R. Hershey, "SDR - half-baked or well done?," author manuscript, 2018. [Paper](https://arxiv.org/abs/1811.02508).

Role: scale-invariant SDR as a projection-based waveform measure. The implemented score removes the mean and uses a scalar projection, not an arbitrary distortion filter or a lag search.

C. H. Taal, R. C. Hendriks, R. Heusdens, and J. Jensen, "An algorithm for intelligibility prediction of time-frequency weighted noisy speech," IEEE Transactions on Audio, Speech, and Language Processing, 19(7), 2125-2136, 2011. [DOI](https://doi.org/10.1109/TASL.2011.2114881).

[pystoi implementation](https://github.com/mpariente/pystoi). Role: intrusive intelligibility estimate from paired clean and degraded signals, not direct human listening accuracy.

## Datasets and Evaluation Context

- [University of Edinburgh VoiceBank+DEMAND](https://doi.org/10.7488/ds/2117): official 48 kHz paired clean/noisy speech. The current controlled experiment uses only one clean utterance and creates its own mixture.
- [DEMAND](https://zenodo.org/records/1227121): recorded environmental noise. Current recording is DWASHING channel 1; do not relabel it as fan or keyboard noise.
- [Microsoft DNS Challenge](https://github.com/microsoft/DNS-Challenge): real-time enhancement datasets, synthesis, and evaluation context. Exact challenge/version constraints must be stated before adopting its latency rules.

The intended literature progression is classical spectral estimation, causal/latency-constrained processing, then pretrained low-latency enhancement and multi-metric evaluation. The current milestone establishes only the classical streaming experiment; the modern-reference investigation remains work in progress.
