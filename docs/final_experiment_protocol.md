# Final causal latency-quality experiment protocol

Initial engineering protocol frozen before its evaluation mixtures, 2 November
2026. The external-cohort amendment below was fixed before running external
outputs; the original VoiceBank run had already completed.

## Research question and continuity

Continue the established project: how does causal STFT scheduling delay affect Wiener enhancement quality, and how does the classical baseline compare with the pinned pretrained DeepFilterNet3 reference under a reconciled delay convention?

Audio Processing Report 2 is independent coursework. Offline temporal modulation filtering is not a final-project method. Existing preliminary and causal milestones remain historical development evidence.

## Fixed methods

- Reuse `CausalWiener`, `latency_config`, and `run_causal_stream` without changing their enhancement rules.
- Windows 10/20/40/80 ms, 50% overlap, 48 kHz; a common 100 ms decision-directed smoothing time constant and gain floor 0.05.
- Fixed 300 ms noise-only calibration; no adaptation after calibration, no clean reference supplied to processors.
- DeepFilterNet3: official v0.5.6 Windows Rust/Tract executable and pinned model/source from milestone 2; no training, fine-tuning or postfilter.
- Wiener oldest-sample block-ready delays 10/20/40/80 ms; DeepFilterNet3 ready delay 40 ms and known transport shift 1440 samples. These exclude compute and device latency.
- No parameter selection from final evaluation outcomes.

## Split and experimental units

- Development speech remains p232_003; development noises remain DEMAND DWASHING and ESC-50 source 137.
- Final speech: the first six sorted speakers in the official clean 28-speaker archive, taking the first two sorted utterances per speaker lasting at least 4.5 seconds. Retain the first 4.5 seconds at native 48 kHz.
- Final noises: the first two sorted distinct source IDs in each of ESC-50 washing_machine and keyboard_typing, excluding keyboard source 137. Use 4.9 s from each original 5 s recording, resampling 44.1 to 48 kHz once.
- This is speaker-disjoint and noise-recording-source-disjoint relative to the project's development examples. It is not a guarantee that upstream model pretraining never encountered related source material.
- Input SNRs 0/5/10 dB, a 300 ms real-noise prefix, and 100 ms real-noise tail. Do not loop noise or invent future samples during streaming.
- Twelve utterances x four noise recordings x three SNRs = 144 paired mixtures. Six scored conditions per mixture: noisy, four Wiener windows, DeepFilterNet3.
- All methods consume identical float32 input files. One common input attenuation provides headroom. Clean references retain double precision; method outputs are not independently normalised.

## Measures and validation

- Reference-to-error SNR, zero-mean projection-based SI-SDR, and standard pystoi STOI on the original speech interval.
- Remove known transport shift only, with no quality-optimising delay search. Prefix and tail are not scored as speech.
- Repeat existing reconstruction, arbitrary-chunk, future-invariance, impulse-shift and schedule tests.
- Re-run the reference transport/future-invariance/compensated-trim checks and verify binary/model hashes.
- Keep quality and timing experiments separate. Run timed jobs sequentially, without concurrent benchmarks.
- Representative compute measurements: the first evaluation utterance, first source of each noise class, at 0 dB. One warm-up plus seven repetitions per Wiener window and reference condition.
- Wiener RTF includes the sequential driver and EOF flush, excludes construction/preallocation/I/O/metrics. Separate per-hop step timing reports p50/p95/p99/max and the fraction exceeding H/fs; label timer/validation overhead and exclude EOF flush from recurring deadlines.
- Reference RTF uses the official internal frame-loop timer. Do not fabricate per-frame reference timings when the binary does not expose them.
- Aggregate paired quality by speaker and resample the six speakers for uncertainty intervals, conditional on the four selected noise recordings. Repeated utterance/noise/SNR conditions are not independent speakers.
- Report backend, PCM16 versus double-output, data-source, pretraining-overlap and device-latency limitations.

## Pending supplementary source

The lecturer's audio materials have not been downloaded. They remain optional independent validation, not a prerequisite for the documented public-data final experiment.

## External-cohort amendment

Author-paper inspection identified VCTK in the model's training description.
Retain the original cohort as a secondary engineering comparison, with explicit
upstream exposure risk. The primary external test uses six lexicographically
selected LibriSpeech test-clean speaker IDs, the first two sorted recordings of
at least 4.5 seconds per speaker, and their first 4.5 seconds. Resample 16 to
48 kHz once before mixing; this does not create full-band speech or belong to
the reported enhancement delay. Reuse the same four noises, SNRs, mixture
duration, settings, precision policy, metrics, timing selection, and speaker
bootstrap. Do not pool the two speech corpora. No enhancement rule is retuned.
The reason, chronology, and remaining overlap uncertainty are documented in
`pretraining_overlap_audit.md`.
