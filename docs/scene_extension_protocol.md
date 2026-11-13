# Noise-scene extension: plan fixed 6 November 2026

## New-recording test and personal bridge, 7 November 2026

The author supplied takes 04-06 after the v2 models had been stored. The archive
contains nine new sources (no development hash overlap), captured on the same
phone in a bedroom at at most 0.5 m. One alarm tone is repeated; other contents
changed. Score all 11 models without refitting; preserve predeclared fusion as
the primary route. Detailed test protocol, frozen-model audit and measured
outcomes are in `results/scene_holdout/README.md`.

Before enhancement output inspection, specify a bridge using the three new
readings and three new bottle sources: first 8 s reading, first 8.4 s continuous
bottle recording, natural first 300 ms calibration, 100 ms tail, 0/5/10 dB,
and all six existing quality conditions. This yields 27 controlled mixtures and
162 scores with unchanged enhancers. No event-based calibration selection,
estimator retuning or clean-reference input to enhancement. Separate source
classification links the recordings to scene analysis; no mixture classifier or
automatic routing benefit is assumed. See `results/scene_bridge/README.md`.

## Multi-route amendment after baseline development, 7 November 2026

At the user's request, expand the nine-recording development work beyond the
nearest-centroid prototype. Add MFCC/delta/delta-delta, autocorrelation/envelope
features, linear/RBF SVM, ExtraTrees, single/dual-scale temporal voting,
late fusion and fitting-only Gaussian noise augmentation. Keep all derived
windows/conditions grouped with their source recording and use training-only
weighted standardisation. Compare component ablations and controlled gain/noise
probes. The fusion route is specified as the primary advanced experiment before
its first evaluation, while the original centroid remains the historical
baseline. Detailed parameters and actual outcomes are in
`results/scene_advanced/README.md`. Independent recordings remain reserved for
the subsequent test stage. The earlier v1 model freeze remains historical;
this amendment opens a new development version before independent testing.

## User-selected amendment, 7 November 2026

The user supplied three phone/audio files representing container pressing, an alarm
and a spoken Chinese poem. These replace the initial steady/keyboard/mixed
classes for the first pilot. The current operational labels are `container_press`,
`alarm` and `speech`. Chinese speech is suitable because this module analyses
acoustics rather than transcribing words. On 7 November 2026, the author confirmed
personally capturing all three recordings using a phone and personally reading
the poem. Originals remain local with hashes and unnormalised WAV decodes.
The author clarified that the object is a plastic bottle, correcting the initial
can wording. The legacy pilot ID is retained only for provenance continuity.

## Nine-recording development implementation, 7 November 2026

The newly supplied 01/02/03 files contain three takes per class. Hash checks show
that all three 01 files match the previous pilot, leaving nine unique sources.
Total duration is 87.9573 seconds. All nine are development data.

Use three fixed take-index folds, each holding out one full source per class.
Fit standardisation only within each six-recording fitting set. Compare fixed
nearest-centroid/nearest-neighbour classifiers with 13 features or 12 features
excluding absolute RMS. The primary prototype is centroid with 12 relative
features, specified before the first score inspection. These are development
comparisons; the take-based split does not establish separate physical sessions.

All four give 8/9 and macro-F1 0.88571. Bottle take 01 is misclassified as speech.
Freeze further choices before independent test capture/evaluation. Preserve
session/source grouping for any future segments or augmentations.

The remaining paragraphs document the initial collection plan and its context.

The first three files are pipeline-development examples, one source per class.
Use them to inspect acoustic features; reserve independent recording sessions
for validation and test evaluation. All segments or transformations of a source
remain in its original split. Do not report a three-file fitting score as
classification accuracy on unseen recordings.

The proposed independent-session design, training-only feature standardisation,
recording-level metrics and class-balanced comparisons below still apply, with
the new labels replacing the initial classes. Alarm is a potentially useful
warning sound; a scene label alone does not imply that it should be suppressed.
The initial plan below is retained to document the scope change.

## Research question

Can interpretable short-time acoustic features distinguish steady mechanical,
keyboard-transient and mixed noise in independently recorded sessions, and
provide useful context for the existing causal speech enhancer?

## Scope and project continuity

The previous Wiener/DeepFilterNet3 latency-quality study remains the enhancement
baseline. This extension introduces personal noise acquisition, feature design,
scene classification and recording-session evaluation. ASR integration is not
part of this selected first extension.

The analysis input is a separate noise-only recording, not a speech/noise
mixture. Initial recording duration is eight seconds. Classification acquisition
time is separate from the previous enhancer's 10-80 ms output-ready schedules.

## Data and split

- Three classes: steady mechanical, keyboard, mixed steady-plus-keyboard.
- Three separately captured sessions, three recordings per class per session.
- Session 1 is training; session 2 is validation; session 3 is held-out testing.
- Keep microphone gain fixed and vary distance/placement and typing rhythm
  between sessions. Log the physical source, device and conditions.
- Each source recording is one observation. Internal windows are aggregated.
- Use only training recordings for feature standardisation and classifier fit.
- Choose feature sets and classifier settings using validation recordings.
- Capture/evaluate the final session after freezing the selected configuration.
- More sessions are preferable if time allows; group them by physical session.

## Features, baselines and outputs

Implement time-domain level/burst features and frequency-domain shape/change
features. Compare simple classifiers before increasing complexity. Assess the
effect of removing absolute level, since microphone gain can dominate RMS.
Labels, filenames and split identifiers are not classifier features.

Deliver a source manifest, a feature-definition table, labelled feature plots,
recording-level predictions, confusion matrix, macro-F1, accuracy and failure
examples. Demonstrate record/import -> analyse -> scene label -> processing
suggestion -> existing enhancement/audition.

## Schedule

6-7 November: recording tool, feature extraction and training/validation capture.
8-9 November: classifiers, development comparisons and configuration freeze.
10 November: held-out capture, evaluation and scene/processing integration.
11-12 November: report, video and reproducible package.
13 November: final submission checks.

## Current implementation status

Recording tool and acoustic feature extractor are implemented. Signal-level
checks verify the feature extractor. Classifier fitting, held-out accuracy and
enhancement-routing benefit require the planned recording data; no performance
claim is made by the implementation checks.
