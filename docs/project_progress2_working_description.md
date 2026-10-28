# Final Project: Second Progress Description

Yixiang Ma | SID 550762913 | ELEC5305 | 28 October 2026

Project site: https://simon1ma.github.io/elec5305-project-550762913/

Detailed results: https://simon1ma.github.io/elec5305-project-550762913/results/latency_milestone2/

Following feedback, my project investigates latency-quality trade-offs in causal speech enhancement. Wiener filtering is an established baseline rather than a new algorithm.

I implemented a stateful sequential-block MATLAB processor and compared 10, 20, 40, and 80 ms windows. The current development experiment uses 4.5 seconds of one recorded 48 kHz VoiceBank utterance mixed separately with DEMAND washing-machine and ESC-50 keyboard noise at 0 dB SNR. The same inputs, 300 ms noise-only prefix, and 100 ms recorded-noise tail are supplied to every method. Reconstruction, arbitrary-chunk consistency, future-input invariance, transport shift, and output scheduling have been checked.

I added the official pretrained DeepFilterNet3 reference without training or fine-tuning. Its stateful Rust frame loop and lookahead were inspected. A probe confirmed its 30 ms transport shift; under a common oldest-sample block-ready convention its delay is 40 ms. At that ready delay, the 40 ms Wiener branch achieves keyboard SNR 2.02 dB and STOI 0.7020, compared with DeepFilterNet3's 12.93 dB and 0.9092. Noisy keyboard STOI is 0.7280, showing that Wiener SNR improvement alone does not establish an intelligibility benefit. Event-level waveforms, spectrograms, and gains help inspect this failure case.

The site includes SNR, SI-SDR, STOI, repeated-run RTF, source provenance, checks, and runnable code. It distinguishes algorithmic delay from compute/device latency and discloses backend and output-precision differences. Results concern one development utterance, not held-out generalisation. More speakers, source-disjoint evaluation, multiple SNRs, and per-block deadline measurements remain next steps.
