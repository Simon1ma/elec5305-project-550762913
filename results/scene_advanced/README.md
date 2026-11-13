# Multi-route acoustic scene classification

Subsequent new-recording evaluation is complete in
`results/scene_holdout/README.md`. The results below are the earlier development
comparisons; development 9/9 is not the later test score. Enhancement on the new
personal sources is documented in `results/scene_bridge/README.md`.

Implemented and evaluated 7 November 2026 on the existing nine author-recorded
development sources: plastic-bottle pressing, alarms and spoken Chinese reading.
These remain nine independent source recordings; windows and perturbations do
not increase the number of independent sources.

## Feature and temporal design

MATLAB Audio Toolbox supplies MFCC and first/second temporal differences.
At 16 kHz, analysis uses 25 ms Hann frames, 10 ms hops and FFT512. Fourteen
cepstral coefficients are requested; C0 is discarded, retaining C1-C13.

The full vector has **69 descriptors**:

- 12 original level-relative acoustic features.
- 26 MFCC mean/standard-deviation values.
- 26 delta/delta-delta standard-deviation values.
- 5 periodicity/envelope descriptors: autocorrelation strength mean and SD,
  strongly periodic frame fraction, pitch variability and envelope recurrence.

Full-recording classification is compared with 1.5-second and 3-second windows,
each with 50% overlap. A window is retained when its RMS is at least 15% of the
maximum window RMS within that source/scale; a fallback retains one window.
This is a label-independent activity heuristic. Each source's training weights
sum to one, divided equally over conditions and scales and then over windows.
Standardisation is fitted on training sources with those weights.

## Technical routes and fixed settings

The comparison includes original 12-feature centroid, rich-feature centroid,
linear SVM, RBF SVM, extra-randomised tree ensemble, static-feature ablation,
single-scale SVM, dual-scale SVM, dual-scale trees, SVM/tree late fusion, and
noise-augmented dual-scale SVM.

Linear SVM uses C=1. RBF SVM uses C=4 and gamma=scale. ExtraTrees uses 128 trees,
maximum depth 6, minimum leaf size 2, sqrt feature sampling and seed 5305.
Late fusion averages hard-vote fractions equally over scales and model branches.
These vote fractions are agreement scores, not calibrated class probabilities.
The pre-evaluation primary experiment is the dual-scale fusion; all routes are
available for development comparison. No result has yet selected an independent
test winner.

## Source-level development protocol

Keep the existing three folds: hold out take 01/02/03 across all classes, fitting
on six sources and predicting three. Every window and transformation inherits
its source fold. Source hashes are checked for fitting/held-out disjointness.

Each held-out source is evaluated in three conditions:

- Original recording.
- Amplitude multiplied by 0.5 (approximately -6 dB).
- Added seeded Gaussian white noise at 20 dB recording-level SNR.

The augmentation route uses original and white20 versions of fitting sources;
held-out source transformations never enter training. Feature extraction yields
507 rows including probes, from nine original recordings. Evaluation metrics
are always calculated per source recording, not per window.

## Selected results: correct recordings / 9

| Route | Original | Half gain | White noise, 20 dB |
| --- | ---: | ---: | ---: |
| Original 12-feature centroid | 8 | 8 | 4 |
| Rich-feature centroid | 8 | 8 | 5 |
| Rich-feature linear SVM | 8 | 8 | 5 |
| Rich-feature RBF SVM, full recording | 9 | 9 | 6 |
| Rich-feature ExtraTrees, full recording | 9 | 9 | 5 |
| Dual-scale RBF SVM | 8 | 8 | 8 |
| Dual-scale SVM/tree fusion | 8 | 8 | 8 |
| Noise-augmented dual-scale RBF SVM | 8 | 8 | 9 |

Full-recording nonlinear models correct the original clean-development error.
Dual-scale and augmented routes show better results under the specified white
noise probe, while their original-recording result remains 8/9. Removing delta
descriptors gives the same dual-scale RBF decisions here, so these development
recordings do not establish a benefit from the delta block. Fusion does not
outperform its RBF branch in this probe. Results support different trade-offs,
not a claim that adding every component improves classification.

These comparisons use a very small, single-author development set. The subsequent nine-recording frozen-model evaluation is reported separately in results/scene_holdout/README.md, and the Gaussian probe is a controlled noise
condition rather than a general environmental robustness result.

## Reproduce and demonstrate

```matlab
addpath(fullfile(pwd,'code','scene'));
extract_scene_advanced();
```

```text
python -m pip install -r code/scene/requirements-advanced.txt
python code/scene/scene_advanced.py develop
```

```matlab
launch_scene_demo();
```

The app's method selector compares the original baseline with MFCC classifiers,
multi-scale fusion and augmented SVM. Tabs display rich features and per-window
decisions. Runtime configuration and models stay in ignored
`data/local/scene/advanced/`; running development writes the current Python path
for the MATLAB bridge. Inference launches Python directly through Java
ProcessBuilder without shell command interpolation. Its displayed analysis time
includes feature extraction and Python startup/model loading.

`route_summary.csv` and `recording_predictions.csv` contain all outcomes;
`*_confusion.csv` and `route_comparison.png` provide comparisons. Fit timings
are observations of these jobs and do not establish a device latency budget.

## Primary documentation

- MATLAB MFCC and deltas: https://www.mathworks.com/help/audio/ref/mfcc.html
- SVM: https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html
- ExtraTrees: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html
- Grouped validation: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html
