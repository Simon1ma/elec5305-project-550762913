from pathlib import Path
import csv,json,sys,hashlib
import numpy as np
from scipy.io import loadmat
from pystoi import stoi
r=Path(__file__).resolve().parents[2];out=r/'results/scene_adaptive'
sys.path.insert(0,str(r/'code/latency'))
from evaluate_latency import snr,si_sdr
m=json.loads((r/'results/scene_bridge/input_manifest.json').read_text())
old=list(csv.DictReader((r/'results/scene_bridge/metrics.csv').open()))
print(old[0].keys())
rows=[]
for c in m['cases']:
 d=loadmat(r/c['input_mat'],simplify_cells=True);clean=d['clean'];y=loadmat(r/'data/local/scene_adaptive'/(c['case_id']+'.mat'),simplify_cells=True)['output']
 base=next(v for v in old if v['CaseID']==c['case_id'] and v['Method']=='Wiener40')
 noisy=d['input'][m['prefix_samples']:m['prefix_samples']+m['speech_samples']]
 a=float(stoi(clean,y,m['fs'],extended=False));s=float(snr(clean,y));si=float(si_sdr(clean,y))
 rows.append(dict(CaseID=c['case_id'],InputSNR_dB=c['input_snr_db'],OutputSNR_dB=s,SI_SDR_dB=si,STOI=a,DeltaSNR_vs_fixed=s-float(base['OutputSNR_dB']),DeltaSTOI_vs_fixed=a-float(base['STOI']),STOI_lower_than_noisy=int(a<float(stoi(clean,noisy,m['fs'],extended=False)))))
def write(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
write(out/'metrics.csv',rows)
summary=[]
for level in [0,5,10]:
 group=[v for v in rows if v['InputSNR_dB']==level]
 summary.append(dict(InputSNR_dB=level,Mixtures=9,**{key:float(np.mean([v[key] for v in group])) for key in ['OutputSNR_dB','SI_SDR_dB','STOI','DeltaSNR_vs_fixed','DeltaSTOI_vs_fixed']},STOI_lower_than_noisy=sum(v['STOI_lower_than_noisy'] for v in group)))
write(out/'summary.csv',summary)
print(json.dumps(summary,indent=2))
(out/'audit.json').write_text(json.dumps({'cases':len(rows),'status':'exploratory post-test comparison','protocol_sha256':hashlib.sha256((out/'PROTOCOL.md').read_bytes()).hexdigest(),'matlab_checks':'27 baseline matches; first-case bypass reconstruction, chunk invariance, future invariance passed'},indent=2))
