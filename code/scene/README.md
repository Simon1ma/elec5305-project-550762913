# Noise analysis and scene identification

Fresh GitHub download: run `START_PROJECT('classification')` for the bundled MATLAB centroid demo. For frozen advanced-model scoring, install the documented Python dependencies, run `python code/scene/configure_runtime.py`, then `python code/scene/evaluate_scene_holdout.py`. Public model copies are staged into ignored local folders without refitting. The personal-recording GUI and raw-feature rebuild instructions below require the original private recordings.

## Current evaluation status

The 04-06 archive has now been evaluated using the stored models, with no
refitting or development/test hash overlap. The predeclared dual-scale fusion
scores 8/9 on both original new recordings and white20 probes. The full-recording
RBF SVM, which scored 9/9 during development, scores 5/9 on the original new
recordings. See `results/scene_holdout/README.md` for all routes and failures.

The three new readings and three new bottle sources also form 27 enhancement
mixtures. `results/scene_bridge/README.md` records this connection to the original
causal processors and the initial-noise-estimate failure observed on these files.
`launch_scene_demo` now lists all 18 recordings and links to
`launch_final_demo('personal')`, where any of the three readings can be selected.
The sections below retain the development history and initial acquisition plan.

This extension adds a sound-analysis module before the existing enhancement
system. The user-selected classes are **plastic bottle pressing**, **alarm** and
**spoken reading**. Classification uses a separately captured scene recording.
The previous steady/keyboard/mixed plan remains an optional recorder profile.

## Advanced routes

The module now includes MATLAB MFCC/delta/delta-delta and periodicity features,
linear/RBF SVM, ExtraTrees, 1.5/3-second multi-scale voting, late fusion and
training-side noise augmentation. Eleven fixed development routes are compared
on the same source-held-out folds, including component ablations and controlled
gain/white-noise probes. Exact definitions and measured results are in
`results/scene_advanced/README.md`.

```matlab
addpath(fullfile(pwd,'code','scene'));
extract_scene_advanced();
```

```text
python -m pip install -r code/scene/requirements-advanced.txt
python code/scene/scene_advanced.py develop
```

Running `launch_scene_demo` then enables method selection and a temporal-vote
tab, while retaining the original classifier. Python runtime information is
written locally during development; it is not hard-coded into the app.

## Current development module

Nine unique phone recordings have been imported: three per class. The three
01 takes are the original pilot files, so the dataset contains nine, not twelve,
unique sources. The author confirmed that the pressed object is a plastic bottle.

```text
python code/scene/import_scene_development.py --folder PATH_TO_NINE_M4AS
```

The folder contains `鐡跺瓙01.m4a` through `鐡跺瓙03.m4a`, `闂归挓01.m4a` through
`闂归挓03.m4a`, and `鍙よ瘲01.m4a` through `鍙よ瘲03.m4a`. The importer preserves raw
files and rejects duplicates, decodes without normalisation and records hashes.
Python import dependencies are numpy, soundfile and imageio-ffmpeg.

```matlab
addpath(fullfile(pwd,'code','scene'));
extract_scene_development();
evaluate_scene_development();
launch_scene_demo();
```

Three-fold development evaluation holds out one entire recording per class in
each fold. Standardisation is fitted on the remaining six sources. Nearest
centroid and nearest neighbour, each with/without absolute RMS, obtain 8/9
correct and macro-F1 0.88571. The primary prototype is nearest centroid without
absolute RMS, selected before score inspection. Scores and the misclassification
are documented in `results/scene_development/README.md`.

The app supports selecting development examples, importing recordings, original
playback, waveform/spectrogram display, feature inspection and predicted class.
Recordings 01/02/03 are takes; they are not confirmed independent physical
sessions. The subsequent nine-recording frozen-model test is complete; see results/scene_holdout/README.md. Broader session/device generalisation remains untested.

## Original three-file phone pilot

Three M4A files have been imported to ignored `data/local/scene/pilot/`.
Originals and SHA256 hashes are preserved. `import_scene_pilot.py --container PATH
--alarm PATH --speech PATH` decodes them to mono 48 kHz PCM24 without gain
normalisation. On 7 November 2026, the author confirmed personally recording all
three clips using a phone and personally performing the spoken reading. Use
`--self-recorded` when reimporting this confirmed set.

```matlab
addpath(fullfile(pwd,'code','scene'));
analyse_scene_pilot();
```

The pilot exports complete-recording features and waveform/spectrogram plots
to `results/scene_pilot/`. Its three labels are supplied labels, not predictions.
One source per class is sufficient to exercise the pipeline; classifier
performance requires additional independent recordings.

## Record personal data

In MATLAB, with the repository as Current Folder:

```matlab
addpath(fullfile(pwd,'code','scene'));
check_scene_features();
record_scene_session('session01','train','bottle_alarm_speech');
```

The recorder requests permission through a Record button for each clip. Each
session contains three eight-second recordings per class (nine clips total).
It plays each clip back and lets the operator accept or retry. Use a moderate,
fixed microphone gain. Follow the class-specific prompts; spoken reading belongs
only in the speech class. Record alarm playback acoustically from another device.
Phone recordings can also be imported with source/session labels retained.

Collect two more physically separate sessions:

```matlab
record_scene_session('session02','validation','bottle_alarm_speech');
record_scene_session('session03','test','bottle_alarm_speech');
```

Between sessions, reposition the microphone/source and vary pressing/reading rhythm while
keeping class definitions. Preserve all three classes in each session. Record
the final test session after model choices are fixed. Never move clips or
windows from the same recording/session across splits. The minimum pilot has
27 recordings, 216 seconds of captured sound, with nine clips per split. It
evaluates this user's sources and recording conditions.

Files and the manifest stay under ignored `data/local/scene/`. Existing report
results and the submission archive are unchanged by these recording commands.

## Acoustic features

`scene_features(audio, fs)` accepts a mono recording, resamples to 16 kHz,
and extracts 25 ms Hann frames with 10 ms hops. It produces one row per source
recording: RMS level and variation, burst ratio, zero-crossing rate, centroid
and variability, flatness, entropy, positive spectral flux and variability,
low/high-frequency energy fractions and 85% rolloff. Full-scale and silence
flags accompany the features. Frame observations are aggregated within clips.

```matlab
[x,fs]=audioread('path_to_noise.wav');
[features,quality]=scene_features(x,fs);
disp(features); disp(quality);
```

## Independent evaluation after development

The first new-recording evaluation is complete. To reproduce it:

```text
python code/scene/import_scene_holdout.py --archive PATH_TO_Untitled_Message.zip
```

```matlab
extract_scene_holdout();
```

```text
python code/scene/evaluate_scene_holdout.py
```

The development classifiers are implemented. Further feature/setting changes
must use development/validation sources before freezing the model. Evaluate
the frozen model once on new held-out recordings and keep their source/session
groups separate. Do not fit feature standardisation on final test recordings.

Report a recording-level confusion matrix, accuracy, per-class precision and
recall, macro-F1 and feature/runtime summaries. Inspect misclassified clips and
speech-versus-bottle confusions. The first new-recording test is complete; see results/scene_holdout/README.md. Additional recording conditions are future validation.

The first integration displays the predicted scene and a processing suggestion.
Any automatic choice of enhancement method requires a separate comparison
against fixed processing, using the existing paired speech evaluation.
