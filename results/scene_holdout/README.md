# Frozen-model evaluation on nine new recordings

The author supplied takes 04-06 in `Untitled_Message.zip`, 7 November 2026.
There are three new plastic-bottle clips, three alarms and three Chinese readings,
totalling 105.4293 seconds. Acquisition: same phone as development, bedroom,
at most 0.5 m from the source. One earlier alarm tone was retained and other
content changed; exact bottle identity was not separately specified.

All source and decoded hashes differ from the nine development sources. There
are no decoded full-scale samples. The 11 stored models, preprocessing, feature
code and weights match the pre-test fingerprints. No fitting was performed.
The model SHA256 before and after is recorded in `test_audit.json`.

## Results: correct recordings / 9

| Route | Original new recordings | Half gain | White noise, 20 dB |
| --- | ---: | ---: | ---: |
| 12-feature centroid | 8 | 8 | 4 |
| Rich-feature centroid | 8 | 8 | 6 |
| Full-recording linear SVM | 8 | 8 | 4 |
| Full-recording RBF SVM | 5 | 5 | 5 |
| Full-recording ExtraTrees | 6 | 6 | 6 |
| Static-feature dual-scale SVM | 6 | 6 | 5 |
| Rich single-scale SVM | 8 | 8 | 8 |
| Rich dual-scale SVM | 8 | 8 | 8 |
| Rich dual-scale ExtraTrees | 8 | 8 | 8 |
| **Predeclared dual-scale fusion** | **8** | **8** | **8** |
| Noise-augmented dual-scale SVM | 6 | 6 | 8 |

The predeclared fusion has accuracy 88.89% and macro-F1 0.88571 in each condition.
For the original recordings, all three bottle clips and all three readings are
correct; alarm 05 is predicted as container pressing. No route classifies alarm
05 correctly. In the white-noise probe the fusion also misclassifies alarm 05.

## Interpretation

The full-recording RBF SVM's development 9/9 becomes 5/9 on new recordings: all
three new readings are predicted as alarm, in addition to the alarm 05 error.
The temporal fusion retains 8/9 and correctly identifies all new readings.
This directly distinguishes promising development scores from held-out behaviour.

Alarm 05 has mean active-frame periodicity strength 0.5326, versus 0.7559 and
0.8694 for alarms 04 and 06, and a higher mean spectral flatness (0.0120 versus
0.0051 and 0.0047). These descriptors identify an acoustic difference to inspect;
they do not establish a single-feature cause for the multi-feature error.

Removing temporal differences reduces dual-scale SVM performance to 6/9 original
and 5/9 white20, compared with 8/9 in both conditions for the dynamic feature set.
Fusion matches its SVM branch here; it has not shown a gain over that branch.
The original centroid matches the fusion on unperturbed recordings but drops to
4/9 under white20, while temporal routes retain 8/9.

The test assesses new recordings from the same author/phone environment. The
gain/noise probes are derived from those same nine sources, not additional
independent recordings. Models are retained unchanged for reproducibility.

## Reproduce

```text
python code/scene/import_scene_holdout.py --archive PATH_TO_Untitled_Message.zip
```

```matlab
addpath(fullfile(pwd,'code','scene'));
extract_scene_holdout();
```

```text
python code/scene/evaluate_scene_holdout.py
```

Read `test_summary.csv`, `test_predictions.csv`, `*_confusion.csv` and
`primary_window_decisions.csv` for every outcome. Plots are
`test_route_comparison.png` and `primary_test_confusion.png`. The evaluator
removes ground-truth labels from the prediction interface and checks that model
bytes remain unchanged before and after evaluation.
