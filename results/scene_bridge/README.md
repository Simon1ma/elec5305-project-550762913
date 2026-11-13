# Personal-recording bridge to causal enhancement

This experiment connects the new sound-scene study to the existing enhancement
study using the same held-out personal recordings. Three readings (04-06) are
mixed with three plastic-bottle sources (04-06) at 0/5/10 dB, producing 27 mixtures
and 162 quality-score rows. The three bottle sources are correctly identified by
the frozen scene-fusion model in their separate source-recording test.

## Protocol fixed before enhancement output inspection

Use the first eight seconds of each quiet reading, and the first 8.4 seconds of
each continuous bottle recording. The first 300 ms is a natural noise-only
calibration prefix, followed by eight seconds scored speech and a 100 ms tail.
No event-based repositioning is applied. Noise scale is set on the scored
interval. Common attenuation is 1.0; both enhancers consume the exact same
float32 WAV/MAT samples. The quiet phone recording is the reference, retaining
its original room/microphone background.

Reuse all four unchanged causal Wiener settings and the pinned official
DeepFilterNet3 executable/model. Wiener has the existing 300 ms fixed noise
estimate; the reference receives the same prefix. Known transport shifts align
outputs before scoring. No clean reference is supplied to enhancement.

This is a one-author controlled-mixture engineering experiment. Three-by-three
source combinations do not provide 27 independent speakers. Scene analysis
classifies separate recordings; overlapping speech/noise classification and
automatic scene-based enhancement routing have not been established.

## Measured findings

At 0 dB input, noisy mean STOI is 0.4626. Wiener40 gives approximately 0.0003 dB
output SNR and 0.4626 STOI, effectively unchanged. DeepFilterNet3 gives 3.41 dB
SNR and 0.5688 STOI. At 10 dB input, noisy STOI is 0.6727; the reference gives
2.33 dB SNR and 0.5480 STOI, decreasing STOI in six of nine mixtures.

The natural initial prefix is much quieter than the later bottle events. The
unchanged fixed estimator consequently provides little waveform noise reduction.
`startup_diagnostics.csv` quantifies the prefix/event power gap;
`first_case_gain_diagnostics.csv` checks gains and output change on a fixed first
case. Diagnostics assert that enabling gain capture leaves scored output intact.
The three source power rises are 34.39, 53.87 and 53.53 dB. On the fixed first
case, the energy-weighted squared Wiener40 gain is approximately 0.9999 and
the output/input relative waveform difference is 0.00132. The unweighted mean
gain is 0.8978: attenuation in low-energy bins does not imply meaningful overall
noise reduction.
This is a startup-representativeness failure to analyse, not evidence that every
Wiener noise estimator would behave identically.

The bridge adds personal-recording evidence to the original public-data results:
quality depends on noise dynamics, startup conditions and processing method.
It does not show that the classifier improves enhancement quality by itself.

## Reproduce and audition

```text
python code/scene/personal_bridge.py prepare
```

```matlab
addpath(fullfile(pwd,'code','scene'));
run_personal_wiener();
```

```text
python code/scene/personal_bridge.py reference
python code/scene/personal_bridge.py evaluate
```

```matlab
diagnose_personal_bridge();
addpath(fullfile(pwd,'code','final'));
launch_final_demo('personal');
```

The app chooses any of three readings, three bottle sources, three SNRs and all
six conditions. It reruns enhancement and verifies agreement with saved outputs.
All audition clips use one common gain within the selected case; metrics retain
original amplitudes. The fixed audio-demo selection is the first manifest case,
chosen before scores. Inputs/outputs/audio remain under ignored
`data/local/scene_bridge/`. `metrics.csv`, `summary_by_snr.csv`, checks and figures
record the numerical results.
