"""Run the unchanged official streaming reference on all final shared WAVs."""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/final';LOCAL=ROOT/'data/local/final'
EXE=ROOT/'data/local/latency2/deep-filter.exe'
MODEL=ROOT/'data/local/latency2/DeepFilterNet3_onnx.tar.gz'


def execute(source,destination):
    process=subprocess.run([str(EXE),'--model',str(MODEL),'--output-dir',str(destination),'-v',str(source)],capture_output=True,text=True,check=True)
    log=process.stdout+process.stderr;match=re.search(r'RTF: ([0-9.eE+-]+)',log)
    assert match,'No official frame-loop timing found'
    result,fs=sf.read(destination/source.name,dtype='float64')
    assert fs==48000 and np.isfinite(result).all()
    return result,float(match[1]),log


def main():
    assert hashlib.sha256(EXE.read_bytes()).hexdigest()=='75e11fa16445f560cb6b021521ddb89e89270d13b83089705d98776f58fd7915'
    assert hashlib.sha256(MODEL.read_bytes()).hexdigest()=='c94d91f70911001c946e0fabb4aa9adc37045f45a03b56008cb0c8244cb63616'
    manifest=json.loads((OUT/'input_manifest.json').read_text());cases=manifest['cases']
    destination=LOCAL/'reference';destination.mkdir(exist_ok=True)
    checks=[]
    for i,case in enumerate(cases):
        source=ROOT/case['input_wav'];assert hashlib.sha256(source.read_bytes()).hexdigest()==case['shared_input_sha256']
        result,_,log=execute(source,destination)
        start=1440+manifest['prefix_samples'];stop=start+manifest['speech_samples']
        assert len(result)>=stop
        clipped=bool(np.any(np.abs(result)>=32767/32768))
        checks.append({'CaseID':case['case_id'],'TransportShift_samples':1440,'OldestSampleReadyDelay_ms':40,
                       'OutputSamples':len(result),'PCM16ClippingDetected':clipped,
                       'AlignedSamples':len(result[start:stop])})
        if (i+1)%12==0 or i+1==len(cases):print('Final DeepFilterNet3:',i+1,'/',len(cases),flush=True)
    with (OUT/'reference_checks.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)


def benchmark():
    manifest=json.loads((OUT/'input_manifest.json').read_text());cases=manifest['cases'];rows=[]
    for category in ['washing_machine','keyboard_typing']:
        case=next(c for c in cases if c['speech_id']==cases[0]['speech_id'] and c['noise_class']==category and c['input_snr_db']==0)
        source=ROOT/case['input_wav'];destination=LOCAL/'reference_timing';destination.mkdir(exist_ok=True)
        execute(source,destination);rtfs=[];previous=None
        for repeat in range(7):
            result,rtf,_=execute(source,destination)
            assert previous is None or np.array_equal(previous,result)
            previous=result.copy();rtfs.append(rtf)
        rows.append({'CaseID':case['case_id'],'Noise':category,'Method':'DeepFilterNet3','OldestSampleReadyDelay_ms':40,
                     'RTF_median':float(np.median(rtfs)),'RTF_min':min(rtfs),'RTF_max':max(rtfs),'Repeats':7})
        print('Reference repeated timing complete:',category,flush=True)
    with (OUT/'reference_benchmark.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--benchmark',action='store_true');p.add_argument('--cohort',choices=['voicebank','external'],default='voicebank');args=p.parse_args()
    if args.cohort=='external':OUT=ROOT/'results/final_external';LOCAL=ROOT/'data/local/final_external'
    benchmark() if args.benchmark else main()
