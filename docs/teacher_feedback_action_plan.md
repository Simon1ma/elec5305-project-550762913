# Teacher Feedback: Research Revision and Implementation Audit

Reviewed: 28 October 2026

Status: final-project second progress submission confirmed. The first revised causal recorded-speech milestone has been implemented and measured. Existing offline results have not been relabelled as causal results. See `results/latency_milestone1/README.md` for the actual experiment and remaining scope.

## Revised Research Focus

Suggested title: **Latency-Quality Trade-offs in Real-Time Causal Speech Enhancement**.

Research question: How does algorithmic latency affect causal STFT-domain speech enhancement, and how does a classical Wiener baseline compare with one pretrained real-time enhancer under documented latency constraints?

The contribution is a controlled latency-quality investigation. Wiener filtering itself is an established baseline, not a new algorithm. The modern reference will be pretrained; no training or fine-tuning is planned.

## Existing Implementation Audit

| Existing component | What is reusable | Required change or limitation |
| --- | --- | --- |
| `code/mix_noise.m` | Controlled SNR mixing and reproducible input comparison | Extend to recorded speech and documented stationary/transient noise. |
| `code/calculate_snr.m` | Reference-to-error SNR without independent normalisation | Account for known processing delay consistently; add SI-SDR and STOI. |
| `code/generate_synthetic_signal.m` | Unit tests and controlled demonstrations | Synthetic harmonics are not a substitute for real speech or intelligibility evaluation. |
| `code/wiener_enhancement.m` | Noise PSD estimate, decision-directed gain, noisy-phase reuse | Current function computes a complete STFT before its frame loop; it is an offline implementation, not a demonstrated streaming system. |
| Noise-only prefix | A clearly specified initial estimator | Existing code estimates the PSD from the full prefix before processing. Streaming code must buffer/calibrate honestly and report calibration separately from steady-state delay. |
| `code/fir_baseline.m` | Historical offline comparison | `filtfilt` uses forward-backward filtering and is not a causal real-time comparator. |
| Reconstruction checks | Near-perfect reconstruction established for the old configuration | Repeat tests for every new window/hop combination and streaming boundary/flush behaviour. |
| `code/main_preliminary.m` | Existing result generation and unscaled metric signals | Plotting and file I/O must be excluded from compute timing; no runtime-to-latency equivalence. |
| Existing results | 5 dB synthetic example: FIR 12.32 dB, Wiener 17.04 dB | Historical offline evidence only; no claims about latency, STOI, recorded speech, or pretrained-model results. |

The old helper `calculate_snr(clean, estimate)` expects an estimated signal, not a noise vector.

## Minimum Experimental Design Suggested by the Feedback

1. Start with one recorded clean utterance plus stationary fan noise at 0 dB input SNR.
2. Process sequential input blocks using a causal Wiener implementation.
3. Compare analysis-window durations of 10, 20, 40, and 80 ms with a documented overlap ratio.
4. Verify reconstruction for each configuration before applying gains.
5. Report measured scheduling delay, RTF, output SNR, SI-SDR, and STOI.
6. Repeat with transient keyboard noise and inspect event-level waveform, spectrogram, and gain differences.
7. Evaluate the same mixtures using one pretrained real-time reference, preferably DeepFilterNet if feasible. Inspect its actual streaming path, lookahead, and configuration before making causal or latency claims.
8. Extend to speaker/source-disjoint development and evaluation subsets only after the first small experiment works.

## Initial Parameter Translation

If the core experiment uses 48 kHz, an initial 50-percent-overlap design is:

| Window duration | Window samples | Hop samples | Candidate FFT length |
| --- | --- | --- | --- |
| 10 ms | 480 | 240 | 512 |
| 20 ms | 960 | 480 | 1024 |
| 40 ms | 1920 | 960 | 2048 |
| 80 ms | 3840 | 1920 | 4096 |

These are proposed analysis settings, not measured algorithmic delays. FFT zero-padding changes the spectral sampling grid, not the observation window's physical resolving power. Actual delay depends on framing, output scheduling, overlap-add, buffering, and any model lookahead.

## Checks Needed Before Quality Claims

- Streaming state must persist across calls; the processor must not inspect the remaining file.
- A prefix-invariance test should show that changing future input does not change already-emitted output.
- Unit-gain reconstruction must be checked for all four configurations, including irregular input block lengths and end-of-stream flushing.
- Boundary padding and final flushing must not be described as future samples available during steady-state operation.
- Fixed calibration time must be reported separately from recurring frame latency.
- Use the same mixtures and documented latency alignment for every method. Do not optimise alignment independently to improve each score without reporting it.
- Benchmark with plotting and I/O disabled, warm-up separated, repeated runs, and hardware/software recorded.
- Report `RTF = processing seconds / audio seconds`; `RTF < 1` does not by itself establish a latency guarantee.
- Keep noise-estimation design fixed across the main experiment. Document whether decision-directed smoothing is held fixed per frame or converted to a common time constant; changing hop changes the time represented by one recursive update.
- Do not modify the pretrained model's advertised latency without validating its buffering and lookahead. A whole-file enhancement command alone is not proof of streaming operation.
- Record sample-rate handling, any resampling, and whether latency figures include resampling.

## Deliverable Ambiguity to Resolve

The supplied teacher feedback concerns the research project and its GitHub site. The locally available **Audio Processing Reports Instructions** separately covers Reports 1-2 and requires a MATLAB Live Script, its exported PDF, helper files/data, sections 2.1-2.8, and a reproducible ZIP.

The user confirmed the current task is the final project's second progress submission. The independent Audio Processing Report 2 is not the current deliverable. Previously considered alternatives were:

- the final project's second progress submission; or
- the independent Audio Processing Report 2.

Do not automatically impose the entire final-project minimum scope on Report 2, or submit a short project-site description in place of an MLX report. Scope and submission format must follow the current Canvas task.

## Work Not Yet Completed

A causal processor, one recorded-speech mechanical-noise experiment, SI-SDR/STOI scoring, scheduling-delay checks, and RTF measurements are now complete for the first revised milestone. Actual transient keyboard noise, broader evaluation, and pretrained-model streaming comparison remain incomplete. The selected speech utterance is development data and must not later be relabelled as untouched evaluation data.
