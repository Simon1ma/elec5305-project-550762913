"""Evaluate all stored models on new sources without fitting or selection."""
from pathlib import Path
import hashlib
import json

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from scene_advanced import CLASSES, LOCAL, ROOT, read_features, predict, write_csv

OUT = ROOT / 'results/scene_holdout'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    definition = json.loads((ROOT / 'results/scene_advanced/model_definition.json').read_text())
    model_path = LOCAL / 'advanced_models.joblib'
    before = sha(model_path)
    assert before == definition['model_sha256']
    for name, digest in definition['code_sha256'].items():
        assert sha(ROOT / 'code/scene' / name) == digest, f'Frozen code changed: {name}'
    bundle = joblib.load(model_path)
    rows, names, X = read_features(OUT / 'multiscale_features.csv')
    sources = {r['SourceSHA256'] for r in rows}
    assert len(sources) == 9 and sources.isdisjoint(set(definition['source_sha256']))
    cases = sorted({r['CaseID'] for r in rows})
    predictions = []
    timelines = []
    summary = []
    for route, model in bundle['models'].items():
        assert sources.isdisjoint(set(model['training_hashes']))
        for condition in ['clean', 'gain_minus6', 'white20']:
            true, predicted, review = [], [], []
            for case in cases:
                idx = [i for i, r in enumerate(rows) if r['CaseID'] == case and r['Condition'] == condition]
                label = rows[idx[0]]['Label']
                # Ground-truth labels stay outside the prediction interface.
                query = [{key: value for key, value in rows[i].items() if key not in
                          ['Label', 'CaseID', 'SourceSHA256', 'Condition']} for i in idx]
                result = predict(model, query, names, X[idx])
                true.append(label)
                predicted.append(result['label'])
                review.append(result['needs_review'])
                predictions.append({'Route': route, 'Condition': condition, 'CaseID': case,
                                    'TrueLabel': label, 'Prediction': result['label'],
                                    'Correct': label == result['label'], 'VoteGap': result['vote_gap'],
                                    'NeedsReview': result['needs_review']})
                if route == bundle['default_route'] and condition == 'clean':
                    timelines.extend([{'CaseID': case, **item} for item in result['timeline']])
            matrix = confusion_matrix(true, predicted, labels=CLASSES)
            write_csv(OUT / f'{route}_{condition}_confusion.csv',
                      [{'TrueLabel': c, **dict(zip(CLASSES, matrix[i].tolist()))} for i, c in enumerate(CLASSES)])
            summary.append({'Route': route, 'Condition': condition, 'SourceRecordings': 9,
                            'Correct': sum(a == b for a, b in zip(true, predicted)),
                            'Accuracy': accuracy_score(true, predicted),
                            'MacroF1': f1_score(true, predicted, labels=CLASSES, average='macro', zero_division=0),
                            'ReviewCount': sum(review)})
    write_csv(OUT / 'test_predictions.csv', predictions)
    write_csv(OUT / 'test_summary.csv', summary)
    write_csv(OUT / 'primary_window_decisions.csv', timelines)
    evidence = {'model_sha256_before': before, 'model_sha256_after': sha(model_path),
                'new_sources': 9, 'development_sources': 9, 'hash_overlap': 0,
                'fitting_performed': False, 'primary_route_frozen_before_test': bundle['default_route'],
                'scoring_unit': 'new source recording; perturbations share that source',
                'test_feature_sha256': sha(OUT / 'multiscale_features.csv')}
    assert evidence['model_sha256_before'] == evidence['model_sha256_after']
    (OUT / 'test_audit.json').write_text(json.dumps(evidence, indent=2) + '\n')
    plot_results(summary, predictions, bundle['default_route'])
    for row in summary:
        if row['Condition'] == 'clean':
            print(row['Route'], f"{row['Correct']}/9", f"F1={row['MacroF1']:.3f}", flush=True)
    print('PASS: frozen-model new-recording test complete; no fitting or model changes.')


def plot_results(summary, predictions, primary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    routes = list(dict.fromkeys(r['Route'] for r in summary))
    fig, ax = plt.subplots(figsize=(12, 7))
    for j, condition in enumerate(['clean', 'gain_minus6', 'white20']):
        scores = [next(r['MacroF1'] for r in summary if r['Route'] == route and r['Condition'] == condition) for route in routes]
        ax.barh(np.arange(len(routes)) + (j - 1) * .24, scores, height=.23, label=condition)
    ax.set_yticks(np.arange(len(routes)), [r.replace('rich_', '').replace('_', ' ') for r in routes])
    ax.set_xlim(0, 1.04)
    ax.invert_yaxis()
    ax.set_xlabel('Macro-F1 on 9 new recordings (same phone, bedroom, at most 0.5 m)')
    ax.set_title('Frozen-model test: original recordings and controlled probes', pad=45)
    ax.legend(loc='lower center', bbox_to_anchor=(.5, 1.01), ncol=3)
    fig.tight_layout()
    fig.savefig(OUT / 'test_route_comparison.png', dpi=160)
    plt.close(fig)
    selected = [r for r in predictions if r['Route'] == primary and r['Condition'] == 'clean']
    matrix = confusion_matrix([r['TrueLabel'] for r in selected], [r['Prediction'] for r in selected], labels=CLASSES)
    fig, ax = plt.subplots(figsize=(6.8, 5.5))
    ax.imshow(matrix, vmin=0, vmax=3)
    names = ['Alarm', 'Plastic bottle', 'Speech']
    ax.set_xticks(range(3), names)
    ax.set_yticks(range(3), names)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, str(matrix[i, j]), ha='center', va='center', fontsize=18,
                    color='black' if matrix[i, j] >= 2 else 'white')
    ax.set_xlabel('Predicted')
    ax.set_ylabel('Recorded class')
    ax.set_title('Predeclared fusion route: new-recording test')
    fig.tight_layout()
    fig.savefig(OUT / 'primary_test_confusion.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    main()
