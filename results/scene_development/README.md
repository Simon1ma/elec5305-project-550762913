# Personal sound-scene development experiment

Nine author-recorded phone clips, supplied 7 November 2026: three plastic-bottle
pressing recordings, three alarms and three spoken Chinese readings. The author
confirmed plastic bottle as the object, correcting the first file's can wording.
The three 01 recordings match the earlier pilot; there are nine unique sources,
not twelve. Total decoded duration is 87.9573 seconds. No full-scale samples were
found in these decodes. Raw recordings remain under ignored `data/local/scene/`.

## Development protocol

Use one feature vector per complete recording. The 13 pre-existing features are
extracted at 16 kHz with 25 ms frames and 10 ms hops. Frame windows are aggregated
within their source, not randomly divided into training and evaluation sets.

Each of three folds holds out take 01, 02 or 03 from every class: six recordings
for fitting and three for prediction. Feature means/scales are fitted only on
the six fitting recordings in each fold. Source and decoded hashes must be
disjoint across folds. Take number denotes a fold, not an independently verified
physical recording session.

Four fixed development comparisons: nearest centroid or nearest neighbour,
with all 13 features or 12 features excluding absolute RMS level. The primary
prototype is nearest centroid with the 12 relative features, specified before
the first score inspection. No deep model is used in this classification module.

## Results

All four comparisons give 8/9 correct (88.89%) and macro-F1 0.88571.

| Supplied class | Correct | Recall |
| --- | ---: | ---: |
| Alarm | 3/3 | 1.000 |
| Plastic bottle pressing | 2/3 | 0.667 |
| Speech | 3/3 | 1.000 |

The single error is `container_press_01` predicted as speech. Its mean spectral
centroid is approximately 675 Hz, versus 1879 and 2384 Hz for the other bottle
takes. The first reading's centroid is approximately 674 Hz. This describes a
feature overlap; a causal explanation needs further recording-level inspection.
All feature sets give the same decisions here, so these nine recordings show no
classification benefit from including absolute RMS or switching classifiers.

This is exploratory recording-held-out development performance. Independent
recordings/sessions are still needed for final testing. It is not a population
accuracy estimate or a test result on multiple speakers/devices.

## Outputs and demonstration

- `features.csv`, `quality.csv`: one row per unique source.
- `development_predictions.csv`: every held-out decision and fold assignment.
- `development_summary.csv`, `*_per_class.csv`, `*_confusion.csv`: exact scores.
- `development_confusions.png`: all four comparisons.
- `demo_speech.png`: actual MATLAB app export after analysing speech take 02.

Run `launch_scene_demo` to choose a development clip or import another recording,
inspect the waveform, spectrogram and features, view the predicted best-match
class and audition the original recording. Suggestions are informational; no
automatic enhancement routing has been evaluated.
