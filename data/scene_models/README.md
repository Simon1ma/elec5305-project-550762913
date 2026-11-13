# Frozen scene-model assets

The centroid MAT and advanced joblib bundle are unchanged copies of the fitted models, not refitted on new recordings. START_PROJECT('classification') stages the MATLAB model locally. python code/scene/configure_runtime.py stages both models and records the active Python environment. Frozen model/feature/code fingerprints and test results are in results/scene_advanced/model_definition.json and results/scene_holdout/. Raw phone audio is not included.
