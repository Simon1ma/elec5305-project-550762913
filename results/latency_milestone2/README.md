# Second Causal Milestone: Transient Noise and Pretrained Reference

Yixiang Ma | SID 550762913 | ELEC5305 | 28 October 2026

## Scope and Shared Inputs

This development experiment studies the latency-quality trade-off of a classical causal Wiener baseline and an official pretrained DeepFilterNet3 reference. It is not a new enhancement algorithm or a held-out benchmark.

- Speech: first 4.5 seconds of VoiceBank `p232_003.wav`, native 48 kHz, CC BY 4.0. [Official source](https://doi.org/10.7488/ds/2117).
- Relatively steady noise: DEMAND DWASHING channel 1, segment beginning at 10 seconds, native 48 kHz, CC BY-SA 3.0. This is washing-machine noise, not fan noise. [Official source](https://zenodo.org/records/1227121).
- Transient noise: ESC-50 `1-137-A-32.wav`, the first filename in sorted `keyboard_typing` entries. Its original 44.1 kHz recording is resampled once to 48 kHz by polyphase resampling (160/147). No looping is used. [Pinned dataset](https://github.com/karolpiczak/ESC-50/tree/33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6). ESC-50 is distributed under CC BY-NC; its LICENSE attributes this particular clip to Anton's [keyboard-typing.wav](https://freesound.org/people/Anton/sounds/137/) as CC-BY. The preparation script retains the original license.
- Each noise is scaled to 0 dB SNR over the speech. A 300 ms real-noise prefix supplies Wiener calibration; a 100 ms real-noise tail allows delayed output to emerge. Total input duration is 4.9 seconds. Both methods receive exactly the same float32 input WAV for each case, with one common attenuation across all inputs and clean references.
- Quality excludes prefix and tail. Outputs are aligned only by their known transport shift. There is no lag optimisation or independent output normalisation. The clean reference is never supplied to the enhancement processors.

Only one speech utterance and one recording per noise type are used. These examples are development data. The pretrained model's training overlap has not been independently established. No speaker-generalisation or statistical-significance claim is supported. The first milestone used a longer speech segment and a different timing scope; its scores must not be treated as a directly comparable baseline for improvement.

## Measured Results

Window duration and oldest-sample block-ready delay are separate columns. DeepFilterNet3's 20 ms window does not imply 20 ms block-ready delay.

| Noise | Method | Window (ms) | Ready delay (ms) | Output SNR (dB) | SI-SDR (dB) | STOI | Median RTF |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Washing machine | Noisy | N/A | N/A | 0.00 | -0.02 | 0.9263 | N/A |
| Washing machine | Wiener | 10 | 10 | 3.70 | 3.25 | 0.9215 | 0.0447 |
| Washing machine | Wiener | 20 | 20 | 3.28 | 3.23 | 0.9225 | 0.0226 |
| Washing machine | Wiener | 40 | 40 | 2.27 | 2.22 | 0.9239 | 0.0170 |
| Washing machine | Wiener | 80 | 80 | 1.55 | 1.51 | 0.9281 | 0.0122 |
| Washing machine | DeepFilterNet3 | 20 | 40 | 18.90 | 18.97 | 0.9641 | 0.2113 |
| Keyboard | Noisy | N/A | N/A | 0.00 | -0.07 | 0.7280 | N/A |
| Keyboard | Wiener | 10 | 10 | 2.12 | 1.26 | 0.6764 | 0.0308 |
| Keyboard | Wiener | 20 | 20 | 2.09 | 1.69 | 0.6936 | 0.0844 |
| Keyboard | Wiener | 40 | 40 | 2.02 | 1.68 | 0.7020 | 0.2192 |
| Keyboard | Wiener | 80 | 80 | 2.00 | 1.67 | 0.7185 | 0.1649 |
| Keyboard | DeepFilterNet3 | 20 | 40 | 12.93 | 12.78 | 0.9092 | 0.2088 |

[Exact metrics](metrics.csv) | [Wiener timing and reconstruction](wiener_benchmark.csv) | [Reference timing](reference_benchmark.csv)

![STOI versus block-ready delay](figures/quality_latency.png)

**Figure 1.** STOI versus the oldest-sample output-block-ready delay. Blue points vary the Wiener window and hop together at 50% overlap; the diamond is one fixed pretrained configuration. Dashed lines show each unprocessed mixture. Quality has one utterance per condition, so timing repeats do not provide quality error bars.

## Interpretation and Event Inspection

Wiener improves SNR in both examples, but all four keyboard STOI values are below the noisy input's 0.7280. Its fixed noise PSD is estimated only from the initial prefix and cannot follow subsequent changes. DeepFilterNet3 obtains higher SNR and STOI in both examples, including keyboard STOI 0.9092 at the same 40 ms ready-delay convention as the 40 ms Wiener branch. This is a result for these particular mixtures, not proof of general superiority.

![Recorded keyboard event: 10 ms and 80 ms Wiener settings](figures/keyboard_event.png)

**Figure 2.** A keyboard event is selected by the maximum 20 ms true-noise mean-square energy, excluding the first and last 350 ms of scored speech; the view extends 300 ms either side. Selection does not use output quality. Columns compare 10 ms and 80 ms Wiener windows. Rows show waveforms, enhanced spectrograms, and native Wiener gains. Display spectrograms share a 20 ms Hann window, 5 ms hop, 1024-point FFT, and -90 to -20 dB colour limits. Gain maps use each processor's native frame/frequency grid, with identical 0-1 limits. The long-window gain grid is temporally coarser, and bursts can pass high gains. One event does not isolate a causal mechanism or establish that shorter windows are always better.

[Vector quality figure](figures/quality_latency.pdf) | [Vector event figure](figures/keyboard_event.pdf) | [Event selection](event_selection.json) | [Figure settings](figure_contract.json)

## Algorithm and Latency Definitions

The Wiener implementation uses a periodic Hann analysis window with 50% overlap, FFT lengths 512/1024/2048/4096, decision-directed gains with a common 100 ms smoothing time constant, and minimum gain 0.05. The noise PSD averages complete already-arrived calibration frames and remains fixed thereafter. The processor retains history and overlap-add state across calls. Zero flushing occurs only after end-of-file. See the [implementation](https://github.com/Simon1ma/elec5305-project-550762913/tree/main/code/latency).

For Wiener, transport shifts are 5/10/20/40 ms, verified by impulse tests. Output schedules verify oldest-sample block-ready delays of 10/20/40/80 ms. This convention includes input-packet collection but excludes CPU, device, operating-system, and network delays.

The reference uses the official Windows x64 Rust/Tract executable v0.5.6 and pinned DeepFilterNet3 ONNX weights. It processes 480-sample hops with persistent state, a 960-sample window, and two frames of combined lookahead at 48 kHz. No training, fine-tuning, or optional postfilter is used. Source/configuration imply a transport shift of `(960 - 480) + 2*480 = 1440` samples (30 ms). Under the oldest-sample block-ready convention, this is `960 + 2*480 = 1920` samples (40 ms), including one capture hop. The two lookahead settings combine as their maximum, not their sum.

The transport shift was independently measured with a non-silent near-identity probe. The 40 ms ready delay is source/configuration-derived and reconciled with that probe, not measured on audio hardware. The CLI's delay-compensation option was checked against exact trimming; it was not used as a substitute for delayed-output handling. Both methods receive the same real-noise tail. The reference's low-energy skip threshold is not triggered by any 10 ms input block in either mixture.

The 300 ms noise-only calibration is a separate startup requirement for the Wiener method, not part of the steady-state 10-80 ms delay. This experiment simulates streaming from recordings; it does not include audio-device latency or establish a hard real-time guarantee.

## Scoring and Compute Timing

SNR is clean-reference energy divided by total output-error energy, including residual noise and speech distortion. SI-SDR uses zero-mean scalar projection. STOI is the standard `pystoi` implementation, not extended STOI. Its standard internal resampling belongs to the metric, not a method-specific preprocessing advantage.

The official reference CLI writes PCM16, so its quantisation is included in the reported scores. Wiener outputs remain double precision; shared inputs are float32. These implementation/precision differences are disclosed, not presented as a strictly precision-matched ablation.

RTF is processing time divided by the full 4.9-second input duration. Each condition has seven timing repetitions after one omitted warm-up. Wiener timing starts after processor construction and preallocation and includes the block loop and final flush; it excludes diagnostic capture, alignment, metrics, plotting, and file I/O. DeepFilterNet timing uses the official internal frame-loop timer, excluding model setup and input/output file I/O. Each reference repeat starts a fresh process and has no state carryover. MATLAB and Rust/Tract are different execution backends, and their boundary handling differs; these RTFs are implementation measurements, not intrinsic algorithm-complexity comparisons.

Keyboard Wiener timing varied noticeably: for example, the 40 ms window's RTF ranged from 0.1808 to 0.2914, unlike its washing-machine result. The observed variability is retained rather than smoothed away. All median RTFs are below one on this machine, but no per-block deadline or worst-case execution guarantee has been established. First-milestone timing included setup, so its RTFs are not merged into this table.

## Verification and Provenance

- Unit-gain Wiener reconstruction passed for all eight noise/window cases (relative error below 1e-10).
- The shared processor's reconstruction, arbitrary-chunk, emitted-prefix future-invariance, impulse-shift, and scheduling tests passed for all four window settings.
- Capturing native Wiener gains did not change the enhanced signal (maximum absolute difference below 1e-12).
- DeepFilterNet's measured transport shift is 1440 samples. The near-identity probe relative error, including PCM16, is 0.0004602.
- Replacing all input after sample 96000 left reference output already emitted before that sample unchanged (maximum difference zero).
- The reference CLI's compensated output exactly matches trimming 1440 samples from its uncompensated output. Seven repeated outputs are bit-identical. No PCM16 output clipping was detected.
- Figure alignment and text-collision checks passed; vector figures retain readable text.

[Reference checks](reference_checks.json) | [Data/model versions, checksums, source links](data_and_model_manifest.json) | [Speech/washing-machine source hashes](../latency_milestone1/data_manifest.json) | [Shared-input hashes and mixing](shared_input_manifest.json) | [Model configuration](deepfilternet_model_config.ini) | [Measured environment](environment.txt)

Raw recordings, executable binaries, model weights, and intermediate MAT/audio files are excluded from the repository. Scripts retrieve the documented official resources and check pinned runtime/model hashes. [Reproduction instructions](https://github.com/Simon1ma/elec5305-project-550762913/blob/main/code/latency/README.md).

## Remaining Work

Expand the speech and noise source sets, separate development and evaluation sources before segmenting or mixing, freeze parameters on development data, and evaluate several SNRs. Establish model-training overlap where possible. Collect per-block execution-time distributions and, if a live-audio claim is needed, measure actual device latency. The present evidence supports a second progress submission, not a completed final-project benchmark.
