"""Source-grouped model comparison for MATLAB-extracted acoustic features.

Train-only scaling, recording-balanced window weights and recording-level scores.
Derived windows/perturbations never cross a source recording's development fold.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import sys
import time

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC, SVC

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/scene_advanced'
LOCAL = ROOT / 'data/local/scene/advanced'
META = ['CaseID', 'Label', 'Fold', 'SourceSHA256', 'Condition', 'Mode', 'StartSeconds', 'EndSeconds']
CLASSES = ['alarm', 'container_press', 'speech']
ROUTES = {
    'handcrafted_centroid_full': ('centroid', ['full'], 'handcrafted', False),
    'rich_centroid_full': ('centroid', ['full'], 'dynamic', False),
    'rich_linear_svm_full': ('linear', ['full'], 'dynamic', False),
    'rich_rbf_svm_full': ('rbf', ['full'], 'dynamic', False),
    'rich_extratrees_full': ('trees', ['full'], 'dynamic', False),
    'static_rbf_multiscale': ('rbf', ['w1.5', 'w3'], 'static', False),
    'rich_rbf_single_scale': ('rbf', ['w1.5'], 'dynamic', False),
    'rich_rbf_multiscale': ('rbf', ['w1.5', 'w3'], 'dynamic', False),
    'rich_extratrees_multiscale': ('trees', ['w1.5', 'w3'], 'dynamic', False),
    'rich_fusion_multiscale': ('fusion', ['w1.5', 'w3'], 'dynamic', False),
    'rich_rbf_augmented': ('rbf', ['w1.5', 'w3'], 'dynamic', True),
}
PRIMARY = 'rich_fusion_multiscale'


def read_features(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        names = [key for key in reader.fieldnames if key not in META]
        rows = list(reader)
    X = np.array([[float(row[name]) for name in names] for row in rows])
    assert np.isfinite(X).all() and len(names) == 69
    return rows, names, X


def balanced_weights(rows):
    """Each source sums to one; its conditions/scales receive equal total weight."""
    weights = np.zeros(len(rows))
    for case in sorted({row['CaseID'] for row in rows}):
        conditions = sorted({r['Condition'] for r in rows if r['CaseID'] == case})
        for condition in conditions:
            modes = sorted({r['Mode'] for r in rows if r['CaseID'] == case and r['Condition'] == condition})
            for mode in modes:
                idx = [i for i, row in enumerate(rows) if
                       (row['CaseID'], row['Condition'], row['Mode']) == (case, condition, mode)]
                weights[idx] = 1 / (len(conditions) * len(modes) * len(idx))
    assert np.isclose(weights.sum(), len({r['CaseID'] for r in rows}))
    return weights


def fit(rows, names, X, spec):
    kind, modes, subset, augment = spec
    allowed = ['clean', 'white20'] if augment else ['clean']
    indices = [i for i, r in enumerate(rows) if r['Mode'] in modes and r['Condition'] in allowed]
    selected = [rows[i] for i in indices]
    if subset == 'handcrafted':
        columns = list(range(12))
    else:
        columns = [i for i, name in enumerate(names) if subset == 'dynamic' or not name.startswith(('Delta_', 'Delta2_'))]
    y = np.array([r['Label'] for r in selected])
    weights = balanced_weights(selected)
    scaler = StandardScaler().fit(X[np.ix_(indices, columns)], sample_weight=weights)
    Z = scaler.transform(X[np.ix_(indices, columns)])
    components = []
    for component in (['rbf', 'trees'] if kind == 'fusion' else [kind]):
        if component == 'centroid':
            estimator = np.array([np.average(Z[y == c], axis=0, weights=weights[y == c]) for c in CLASSES])
        elif component == 'linear':
            estimator = LinearSVC(C=1, max_iter=10000, random_state=5305).fit(Z, y, sample_weight=weights)
        elif component == 'rbf':
            estimator = SVC(C=4, kernel='rbf', gamma='scale').fit(Z, y, sample_weight=weights)
        else:
            estimator = ExtraTreesClassifier(n_estimators=128, max_depth=6, min_samples_leaf=2,
                                            max_features='sqrt', random_state=5305, n_jobs=1)
            estimator.fit(Z, y, sample_weight=weights)
        components.append((component, estimator))
    return {'scaler': scaler, 'columns': columns, 'components': components, 'modes': modes,
            'names': names, 'feature_count': len(columns), 'spec': spec,
            'training_cases': sorted({r['CaseID'] for r in selected}),
            'training_hashes': sorted({r['SourceSHA256'] for r in selected})}


def predict(model, rows, names, X):
    assert names == model['names'], 'Query feature schema differs from training.'
    selected = [i for i, r in enumerate(rows) if r['Mode'] in model['modes']]
    assert selected
    Z = model['scaler'].transform(X[np.ix_(selected, model['columns'])])
    component_scores = []
    timeline = []
    for kind, estimator in model['components']:
        if kind == 'centroid':
            labels = np.array(CLASSES)[np.argmin(((Z[:, None, :] - estimator[None, :, :]) ** 2).sum(axis=2), axis=1)]
        else:
            labels = estimator.predict(Z)
        scale_scores = []
        for mode in model['modes']:
            mask = np.array([rows[i]['Mode'] == mode for i in selected])
            if mask.any():
                scale_scores.append(np.array([(labels[mask] == c).mean() for c in CLASSES]))
        component_scores.append(np.mean(scale_scores, axis=0))
        for idx, label in zip(selected, labels):
            timeline.append({'Component': kind, 'Mode': rows[idx]['Mode'],
                             'StartSeconds': float(rows[idx]['StartSeconds']),
                             'EndSeconds': float(rows[idx]['EndSeconds']), 'Prediction': str(label)})
    scores = np.mean(component_scores, axis=0)
    order = np.argsort(-scores, kind='stable')
    winner = CLASSES[order[0]]
    gap = float(scores[order[0]] - scores[order[1]])
    return {'label': winner, 'classes': CLASSES, 'vote_fractions': scores.tolist(),
            'vote_gap': gap, 'needs_review': bool(scores[order[0]] < .55 or gap < .15),
            'review_rule': 'Fixed low-vote-consensus flag, not an unknown-class detector',
            'timeline': timeline, 'feature_count': model['feature_count']}


def write_csv(path, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def develop():
    rows, names, X = read_features(OUT / 'multiscale_features.csv')
    LOCAL.mkdir(parents=True, exist_ok=True)
    assert len({r['CaseID'] for r in rows}) == 9
    assert len({r['SourceSHA256'] for r in rows}) == 9
    for source in {r['SourceSHA256'] for r in rows}:
        assert len({r['Fold'] for r in rows if r['SourceSHA256'] == source}) == 1
    predictions = []
    training_times = []
    for route, spec in ROUTES.items():
        for fold in ['1', '2', '3']:
            fit_idx = [i for i, r in enumerate(rows) if r['Fold'] != fold]
            fit_rows = [rows[i] for i in fit_idx]
            begin = time.perf_counter()
            model = fit(fit_rows, names, X[fit_idx], spec)
            training_times.append({'Route': route, 'Fold': fold, 'FitSeconds': time.perf_counter() - begin})
            held_cases = sorted({r['CaseID'] for r in rows if r['Fold'] == fold})
            for condition in ['clean', 'gain_minus6', 'white20']:
                for case in held_cases:
                    test_idx = [i for i, r in enumerate(rows) if r['CaseID'] == case and r['Condition'] == condition]
                    held_rows = [rows[i] for i in test_idx]
                    assert set(model['training_hashes']).isdisjoint({r['SourceSHA256'] for r in held_rows})
                    result = predict(model, held_rows, names, X[test_idx])
                    predictions.append({'Route': route, 'Condition': condition, 'CaseID': case, 'Fold': fold,
                                        'TrueLabel': held_rows[0]['Label'], 'Prediction': result['label'],
                                        'VoteGap': result['vote_gap'], 'NeedsReview': result['needs_review']})
        print('Evaluated', route, flush=True)
    summaries = []
    for route in ROUTES:
        for condition in ['clean', 'gain_minus6', 'white20']:
            subset = [r for r in predictions if r['Route'] == route and r['Condition'] == condition]
            true = [r['TrueLabel'] for r in subset]
            pred = [r['Prediction'] for r in subset]
            assert len(subset) == 9
            summaries.append({'Route': route, 'Condition': condition, 'SourceRecordings': 9,
                              'Correct': sum(a == b for a, b in zip(true, pred)),
                              'Accuracy': accuracy_score(true, pred),
                              'MacroF1': f1_score(true, pred, labels=CLASSES, average='macro', zero_division=0),
                              'ReviewCount': sum(r['NeedsReview'] for r in subset)})
            matrix = confusion_matrix(true, pred, labels=CLASSES)
            write_csv(OUT / f'{route}_{condition}_confusion.csv',
                      [{'TrueLabel': c, **dict(zip(CLASSES, matrix[i].tolist()))} for i, c in enumerate(CLASSES)])
    write_csv(OUT / 'route_summary.csv', summaries)
    write_csv(OUT / 'recording_predictions.csv', predictions)
    write_csv(OUT / 'fit_timings.csv', training_times)
    models = {route: fit(rows, names, X, spec) for route, spec in ROUTES.items()}
    model_path = LOCAL / 'advanced_models.joblib'
    joblib.dump({'models': models, 'default_route': PRIMARY, 'role': 'development; independent test pending'}, model_path)
    runtime = {'python': sys.executable, 'pythonpath': os.environ.get('PYTHONPATH', '')}
    (LOCAL / 'runtime.json').write_text(json.dumps(runtime, indent=2), encoding='utf-8')
    definition = {'default_route': PRIMARY, 'routes': ROUTES, 'classes': CLASSES,
                  'independent_sources': 9, 'feature_rows_with_probes': len(rows),
                  'feature_names': names, 'sklearn': sklearn.__version__,
                  'numpy': np.__version__, 'model_sha256': hashlib.sha256(model_path.read_bytes()).hexdigest(),
                  'score_unit': 'source recording; three development folds',
                  'consensus_rule': 'equal scale/model hard-vote fractions; no probability calibration',
                  'independent_test': 'pending'}
    definition['source_sha256'] = sorted({r['SourceSHA256'] for r in rows})
    definition['feature_csv_sha256'] = hashlib.sha256((OUT / 'multiscale_features.csv').read_bytes()).hexdigest()
    code_files = ['scene_features.m', 'scene_rich_features.m', 'scene_multiscale_features.m',
                  'extract_scene_advanced.m', 'scene_advanced.py']
    definition['code_sha256'] = {name: hashlib.sha256((ROOT / 'code/scene' / name).read_bytes()).hexdigest()
                                 for name in code_files}
    (OUT / 'model_definition.json').write_text(json.dumps(definition, indent=2) + '\n', encoding='utf-8')
    plot_results(summaries)
    for row in summaries:
        if row['Condition'] == 'clean':
            print(row['Route'], f"{row['Correct']}/9", f"F1={row['MacroF1']:.3f}", flush=True)


def plot_results(summaries):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels = list(ROUTES)
    fig, ax = plt.subplots(figsize=(12, 6.5))
    positions = np.arange(len(labels))
    for j, condition in enumerate(['clean', 'gain_minus6', 'white20']):
        values = [float(next(r['MacroF1'] for r in summaries if r['Route'] == route and r['Condition'] == condition)) for route in labels]
        ax.barh(positions + (j - 1) * .24, values, height=.23, label=condition)
    ax.set_yticks(positions, [label.replace('rich_', '').replace('_', ' ') for label in labels])
    ax.set_xlim(0, 1.04)
    ax.axvline(.885714285714286, color='black', linestyle='--', alpha=.65, label='Original baseline (clean)')
    ax.set_xlabel('Recording-level macro-F1 (9 development sources)')
    ax.set_title('Technical-route comparison and controlled robustness probes', pad=45)
    ax.invert_yaxis()
    ax.legend(loc='lower center', bbox_to_anchor=(.5, 1.01), ncol=4, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / 'route_comparison.png', dpi=160)
    plt.close(fig)


def infer(query, output, route):
    bundle = joblib.load(LOCAL / 'advanced_models.joblib')
    route = route or bundle['default_route']
    assert route in bundle['models']
    rows, names, X = read_features(query)
    begin = time.perf_counter()
    result = predict(bundle['models'][route], rows, names, X)
    result.update(route=route, prediction_seconds=time.perf_counter() - begin, model_role=bundle['role'])
    Path(output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['label'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['develop', 'infer'])
    parser.add_argument('--query', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--route', choices=list(ROUTES))
    args = parser.parse_args()
    if args.action == 'develop':
        develop()
    else:
        assert args.query and args.output
        infer(args.query, args.output, args.route)
