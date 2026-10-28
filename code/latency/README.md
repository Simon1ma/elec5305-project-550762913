# Causal Speech Enhancement: Experiment Reproduction

This directory contains two causal recorded-speech milestones after teacher feedback. The previous `code/main_preliminary.m` remains an offline synthetic-signal demonstration and must not be described as a causal real-time experiment.

## Research Question

How does the analysis-window and output-scheduling latency trade off against enhancement quality in a causal Wiener baseline?

The second milestone includes real keyboard noise and an official pretrained DeepFilterNet3 reference. No neural model is trained or fine-tuned. [Current measured results](../../results/latency_milestone2/README.md).

## Reproduce Milestone 2 (Current)

Tested on Windows x64, MATLAB R2026a Update 5 with Signal Processing Toolbox, and Python 3.11.9. From the repository root:

```text
python -m pip install -r code/latency/requirements.txt
python code/latency/prepare_data.py
python code/latency/prepare_transient_reference.py
python code/latency/prepare_milestone2_inputs.py
```

`prepare_data.py` retrieves the original speech/washing-machine inputs if needed. `prepare_transient_reference.py` downloads a pinned ESC-50 keyboard recording, official v0.5.6 Windows runtime, and pinned DeepFilterNet3 ONNX weights. Runtime/model SHA256 values are checked. Files and licenses stay under ignored `data/local/`; do not upload them. No PyTorch, torchaudio, or Python deepfilternet package is required. Other operating systems have not been tested in this project.

In MATLAB, with the repository as the current folder:

```matlab
addpath(fullfile(pwd,'code','latency'));
check_causal();
main_latency_milestone2();
```

After MATLAB finishes, run these commands outside MATLAB:

```text
python code/latency/run_deepfilter_reference.py
python code/latency/evaluate_milestone2.py
```

Run benchmarks sequentially without other benchmark jobs. The outputs include full metrics, reconstruction checks, reference delay/future-invariance checks, manifests, timing CSVs, and two figures under `results/latency_milestone2/`. The intermediate MAT file and audio are excluded from Git. The figure script optionally runs additional layout audits when the author's audit helper is installed; it does not require that helper for reproduction.

This milestone uses a 4.5-second development speech segment, 300 ms real-noise prefix, and 100 ms real-noise tail at 48 kHz. Quality excludes prefix/tail and removes only known transport shifts. Both methods consume identical float32 inputs, with no output normalisation. The CLI reference writes PCM16; Wiener retains double precision. Read the result page before comparing precision, timing, or latency.

### Current Timing and Delay Contract

Wiener ready delays are 10/20/40/80 ms; transport shifts are half those values. DeepFilterNet3 has a 20 ms window, 10 ms hop, and two combined lookahead frames: transport is 30 ms, oldest-sample block-ready delay is 40 ms. Source/configuration derive the ready delay; a separate probe confirms transport. This is not a device latency test. The 300 ms Wiener calibration is a separate startup requirement.

Each RTF is a seven-repeat median after one omitted warm-up, divided by the entire 4.9-second input. Current Wiener timing excludes construction/preallocation and includes the sequential loop and end flush, without diagnostics. Reference timing uses its internal frame-loop timer after model/file setup and before file writing. Each reference repeat launches a fresh process. Different backends and precision mean these are measured implementation costs, not pure algorithm-complexity rankings. RTF below one does not guarantee every block meets its deadline.

`run_deepfilter_reference.py` additionally checks a near-identity transport probe, emitted-prefix invariance to future input, exact delay-compensation trimming, deterministic repeated output, and PCM16 clipping. `main_latency_milestone2.m` checks reconstruction for all conditions and verifies gain-diagnostic capture leaves output unchanged.

## Reproduce Milestone 1 (Historical)

From the repository root, prepare the official single-clip inputs:

```text
python -m pip install -r code/latency/requirements.txt
python code/latency/prepare_data.py
```

In MATLAB R2026a with Signal Processing Toolbox:

```matlab
addpath(fullfile(pwd,'code','latency'));
check_causal();
main_latency_milestone1();
```

Then compute STOI and SI-SDR and generate the figure:

```text
python code/latency/evaluate_latency.py
```

Generated outputs are in `results/latency_milestone1/`. Local source recordings and archives are in `data/local/latency/` and are not committed. The initial speech download is about 147 MB; only one channel is retrieved from the official noise ZIP using HTTP ranges. ZIP member CRC and retained-file SHA256 hashes support integrity checking. Recorded whole-archive noise MD5 is source metadata, not a claim of verifying an un-downloaded archive.

## Milestone 1: Data and Experimental Unit

- Speech: University of Edinburgh VoiceBank+DEMAND clean test archive, first lexicographically sorted p232 utterance lasting at least 4 seconds, capped at 8 seconds. Source: https://doi.org/10.7488/ds/2117. The source recording is CC BY 4.0 per its End-user Licence.
- Noise: DEMAND DWASHING, channel 1, segment beginning at 10 seconds. Source: https://zenodo.org/records/1227121, CC BY-SA 3.0 per dataset description. This is washing-machine noise, **not fan or keyboard noise**. It is a preliminary relatively steady mechanical-noise example, not a claim that every part of the recording is stationary.
- Both sources are native 48 kHz. No resampling is performed before enhancement.
- Noise is scaled to exactly 0 dB SNR over the scored utterance. A preceding 300 ms noise-only segment is used for causal calibration.
- This is one engineering/development example, not held-out statistical evidence. It must not later be relabelled as an untouched evaluation example. No speaker-generalisation claim is supported.

The exact selected filenames, sample counts, segments, and hashes are saved in `data_manifest.json`.

## Streaming Design

`CausalWiener.step(arrived)` only receives samples that have arrived. It maintains history, unprocessed samples, overlap-add state, the calibration PSD, and previous enhanced spectral power across calls. It never receives a clean reference or the rest of the file. The driver feeds one hop at a time and performs a labelled zero flush only after end-of-file.

The analysis window is periodic Hann with 50 percent overlap. Analysis windowing is followed by FFT, gains, inverse FFT, and overlap-add divided by accumulated analysis-window weights; there is no second synthesis window. Past-only initial padding and explicit end flushing cover boundaries. Reconstruction is checked for every configuration.

| Window (ms) | Window samples | Hop samples | FFT length |
| --- | --- | --- | --- |
| 10 | 480 | 240 | 512 |
| 20 | 960 | 480 | 1024 |
| 40 | 1920 | 960 | 2048 |
| 80 | 3840 | 1920 | 4096 |

Zero-padding changes the frequency sampling grid, not the observation's resolving power. The noise estimator averages only complete, already-arrived frames within the 300 ms calibration. This introduces different frame counts at different window lengths; the same calibration duration and estimator rule are used. After calibration, the PSD remains fixed. Decision-directed smoothing uses a common 100 ms time constant (`alpha=exp(-hopSeconds/0.1)`), rather than the same per-frame alpha at different hops. Minimum gain is 0.05. These initial settings are not optimised on the selected utterance.

## Delay Definitions

All timings below exclude CPU compute, audio-device, operating-system, and network delay unless explicitly described as measured compute time.

- **Transport shift:** the unit-gain impulse test measures `H` samples in equal-length block-output arrays. This is the waveform shift removed for quality scoring.
- **Capture packet:** each input call gathers `H` new samples before processing.
- **Oldest-sample block-ready delay:** for each valid logical output block starting at sample `s`, the required input has arrived through sample `s+L`. Its oldest sample is therefore available after `L/fs` seconds. This is verified from per-block schedule traces, not inferred from window size alone.
- **Newest-sample block-ready delay:** `(L-H+1)/fs` seconds under the same sample-index convention. Different samples in one ready block have different ages.
- **Playback interpretation:** starting output playback at each block-ready timestamp gives a conservative fixed sample delay of `L/fs`. Some libraries quote `L-H` as STFT transport latency and account for capture buffering separately. Do not compare these conventions without reconciling them.
- **Calibration:** a separate 300 ms initial noise-only phase. It is excluded from speech quality scoring and must be stated as a startup requirement, not hidden in steady-state latency.

This is a causal recorded-file simulation, not a microphone/device latency experiment or a hard real-time guarantee. Mean/median RTF below one does not prove that every processing block meets its deadline.

## Milestone 1: Metrics and Timing

SNR includes all output error against clean speech. SI-SDR is zero-mean reference projection followed by target-to-residual energy ratio. STOI uses `pystoi.stoi(..., extended=False)`; its internal standardised resampling is part of the metric, not method-specific enhancement preprocessing. Original output amplitudes are preserved.

All outputs remove only the known H-sample transport shift and the 300 ms prefix before scoring. No lag search or independent peak normalisation is used.

RTF is processing time divided by full input duration including calibration. Seven repeated runs follow one warm-up for each configuration. Timed calls include processor construction, sequential processing, and final flush; exclude file I/O, plotting, and metric calculation. Hardware and software are recorded. Timing repeats are not independent speech examples; quality has n=1 utterance and no inferential error bars.

## Checks

`check_causal.m` tests all four configurations for near-perfect unit-gain reconstruction, equal output for irregular input chunks, invariance of already-emitted output to changed future input, impulse transport shift, and output-block readiness scheduling.

## Next Stages

The transient-noise and pretrained-reference steps are complete for one development utterance in milestone 2. Broader evaluation requires speaker/source-disjoint selection before segmenting and mixing, multiple SNRs, model-training-overlap checks, and per-block deadline measurements. Do not relabel existing development examples as untouched evaluation data.

## Resources

- [VoiceBank+DEMAND](https://doi.org/10.7488/ds/2117)
- [DEMAND](https://zenodo.org/records/1227121)
- [STOI implementation](https://github.com/mpariente/pystoi)
- [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet)
- [DNS Challenge](https://github.com/microsoft/DNS-Challenge)
