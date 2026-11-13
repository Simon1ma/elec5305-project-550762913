# Exploratory online noise-estimation comparison

Read PROTOCOL.md before interpreting results. This post-test experiment uses the original 27 personal mixtures and an unconditional 0.5 s exponential noise-power update at 40 ms window length. Original processors, classifiers and saved results are unchanged. No additional independent recording was acquired.

Reproduce from repository root:

```matlab
addpath(fullfile(pwd,'code','scene'));
run_adaptive_comparison();
```

```text
python code/scene/evaluate_adaptive_comparison.py
```

metrics.csv contains all per-case SNR/SI-SDR/STOI and paired changes. summary.csv gives means and STOI decrease counts. checks.csv records exact baseline reproduction; audit.json records validation status. This simple speech-unaware update can suppress speech. New recordings with a development-frozen estimator are needed for independent validation. See report Section 12.

## Measured outcome

At 0 dB, mean output SNR is 2.6948 dB (+2.6945 vs fixed Wiener40), while STOI falls to 0.4037 (-0.0589). At 5 dB changes are +0.5431 dB / -0.0614 STOI; at 10 dB they are -3.0292 dB / -0.0659. STOI falls below noisy input in all 27 mixtures. This comparator is not recommended as an improved enhancer.
