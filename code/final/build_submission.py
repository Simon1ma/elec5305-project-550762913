"""Build and verify a compact final-project submission archive."""
from pathlib import Path
import hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[2]
FINAL=ROOT/'submissions/Final_Project_Submission.zip'

def files():
    fixed=[ROOT/'README.md',ROOT/'index.md',ROOT/'output/pdf/Final_Project_Yixiang_Ma.pdf',
        ROOT/'output/pdf/Final_Project_Yixiang_Ma.md',ROOT/'submissions/Final_Project_Demo.mp4',
        ROOT/'docs/final_experiment_protocol.md',ROOT/'docs/pretraining_overlap_audit.md',
        ROOT/'docs/final_data_attribution.md']
    latency=['CausalWiener.m','latency_config.m','run_causal_stream.m','check_causal.m',
        'prepare_data.py','prepare_transient_reference.py','evaluate_latency.py']
    fixed += [ROOT/'code/latency'/n for n in latency]
    fixed += sorted(x for x in (ROOT/'code/final').iterdir() if x.is_file())
    for cohort in ['final','final_external']:
        base=ROOT/'results'/cohort
        fixed += sorted(x for x in base.iterdir() if x.is_file() and x.suffix in ['.csv','.json','.md'])
        for subtree in ['figures','development_reproduction','audio']:
            folder=base/subtree
            if folder.exists():fixed += sorted(x for x in folder.rglob('*') if x.is_file() and x.suffix in ['.csv','.json','.png','.wav'])
    assert all(p.is_file() for p in fixed)
    return sorted(set(fixed),key=lambda p:p.relative_to(ROOT).as_posix())

def main():
    paths=files();checks={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    readme=(
        '# ELEC5305 final project submission\n\n'
        'Research report: output/pdf/Final_Project_Yixiang_Ma.pdf (10 pages).\n'
        'Code-and-audio demonstration: submissions/Final_Project_Demo.mp4 (94 seconds).\n'
        'Runnable implementation: code/final/README.md; shared causal helpers are in code/latency/.\n'
        'Primary exact results: results/final_external/README.md.\n'
        'Secondary engineering comparison: results/final/README.md.\n'
        'Attribution, protocol and training-overlap audit: docs/.\n\n'
        'Original speech/noise archives, reference executable and pretrained weights are not '
        'redistributed. The documented scripts retrieve and verify them locally. '
        'The report explains the data, methods, results and limitations. '
        'Manifest.sha256.json checks every included file.\n'
    )
    FINAL.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(FINAL,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('SUBMISSION_README.md',readme)
        z.writestr('MANIFEST.sha256.json',json.dumps(checks,indent=2)+'\n')
        for path in paths:z.write(path,path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(FINAL) as z:
        assert z.testzip() is None
        actual=json.loads(z.read('MANIFEST.sha256.json'))
        assert set(actual)==set(z.namelist())-{'MANIFEST.sha256.json','SUBMISSION_README.md'}
        for name,digest in actual.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
        assert all(not name.startswith('data/local/') and 'Report2' not in name for name in z.namelist())
    print('PASS:',len(paths),'files;',FINAL.stat().st_size,'bytes;',FINAL)

if __name__=='__main__':main()
