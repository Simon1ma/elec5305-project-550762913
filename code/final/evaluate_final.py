"""Score the frozen causal comparison and speaker-cluster uncertainty."""
from pathlib import Path
import csv
import hashlib
import json
import platform
import sys
import numpy as np
from scipy.io import loadmat
import scipy
import soundfile as sf
from pystoi import stoi
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/final';LOCAL=ROOT/'data/local/final'
sys.path.insert(0,str(ROOT/'code/latency'))
from evaluate_latency import snr,si_sdr
METHODS=['Noisy','Wiener10','Wiener20','Wiener40','Wiener80','DeepFilterNet3']


def save_csv(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def score(clean,y,fs):
    assert clean.shape==y.shape and np.isfinite(y).all()
    return {'OutputSNR_dB':snr(clean,y),'SI_SDR_dB':si_sdr(clean,y),'STOI':float(stoi(clean,y,fs,extended=False))}


def interval(values,rng):
    x=np.asarray(values,dtype=float);draws=x[rng.integers(0,len(x),(2000,len(x)))].mean(axis=1)
    return np.quantile(draws,[.025,.975])


def main():
    manifest=json.loads((OUT/'input_manifest.json').read_text());cases=manifest['cases'];rows=[]
    assert len(cases)==144 and len(manifest['evaluation_speakers'])==6
    P=manifest['prefix_samples'];N=manifest['speech_samples'];fs=manifest['fs']
    for i,case in enumerate(cases):
        source=ROOT/case['input_wav'];assert hashlib.sha256(source.read_bytes()).hexdigest()==case['shared_input_sha256']
        shared,rate=sf.read(source);original=loadmat(ROOT/case['input_mat'],squeeze_me=True)
        assert rate==fs and np.array_equal(shared,original['input'])
        data=loadmat(LOCAL/'wiener'/(case['case_id']+'.mat'),squeeze_me=True)
        clean=data['clean'];noisy=shared[P:P+N]
        assert np.array_equal(noisy,data['noisy'])
        raw,reference_fs=sf.read(LOCAL/'reference'/source.name);assert reference_fs==fs
        enhanced=raw[1440+P:1440+P+N];assert len(enhanced)==N
        signals=[noisy,*[data['outputs'][:,k] for k in range(4)],enhanced]
        for method,signal in zip(METHODS,signals):
            measurements=score(clean,signal,fs)
            rows.append({'CaseID':case['case_id'],'Speaker':case['speaker'],'SpeechID':case['speech_id'],
                         'NoiseClass':case['noise_class'],'NoiseSource':case['noise_source'],'InputSNR_dB':case['input_snr_db'],
                         'Method':method,'Window_ms':20 if method=='DeepFilterNet3' else int(method[6:]) if method.startswith('Wiener') else 0,
                         'ReadyDelay_ms':40 if method=='DeepFilterNet3' else int(method[6:]) if method.startswith('Wiener') else 0,
                         **measurements})
        if i==0:
            demo=LOCAL/'demo';demo.mkdir(exist_ok=True)
            common=.95/max(1,max(np.max(np.abs(s)) for s in [clean,*signals]))
            sf.write(demo/'Clean.wav',clean*common,fs,subtype='PCM_24')
            for method,signal in zip(METHODS,signals):sf.write(demo/(method+'.wav'),signal*common,fs,subtype='PCM_24')
            (OUT/'demo_selection.json').write_text(json.dumps({'case':case,'selection':'First manifest case, fixed before evaluation outcomes; not best-performing case.','common_playback_attenuation':common},indent=2)+'\n')
        if (i+1)%24==0:print('Scored',i+1,'/ 144 mixtures.',flush=True)
    save_csv(OUT/'metrics.csv',rows)
    rng=np.random.default_rng(5305);speakers=sorted(manifest['evaluation_speakers']);summaries=[];paired=[]
    baseline={(r['CaseID'],r['Method']):r for r in rows}
    for noise in ['washing_machine','keyboard_typing']:
        for snr_db in [0,5,10]:
            for method in METHODS:
                selected=[r for r in rows if r['NoiseClass']==noise and r['InputSNR_dB']==snr_db and r['Method']==method]
                item={'NoiseClass':noise,'InputSNR_dB':snr_db,'Method':method,'ReadyDelay_ms':selected[0]['ReadyDelay_ms'],'Cases':len(selected),'Speakers':6}
                for metric in ['OutputSNR_dB','SI_SDR_dB','STOI']:
                    means=[np.mean([r[metric] for r in selected if r['Speaker']==speaker]) for speaker in speakers]
                    low,high=interval(means,rng)
                    item[metric]=float(np.mean(means));item[metric+'_CI_low']=float(low);item[metric+'_CI_high']=float(high)
                    differences=[np.mean([r[metric]-baseline[(r['CaseID'],'Wiener40')][metric] for r in selected if r['Speaker']==speaker]) for speaker in speakers]
                    low,high=interval(differences,rng)
                    paired.append({'NoiseClass':noise,'InputSNR_dB':snr_db,'Method':method,'Reference':'Wiener40','Metric':metric,
                                   'MeanDifference':float(np.mean(differences)),'CI_low':float(low),'CI_high':float(high),'SpeakerClusters':6})
                summaries.append(item)
    save_csv(OUT/'summary_by_condition.csv',summaries);save_csv(OUT/'paired_vs_wiener40.csv',paired)
    figures=OUT/'figures';figures.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':240})
    for metric,label,name in [('STOI','STOI (objective predictor)','quality_latency'),('OutputSNR_dB','Output SNR (dB)','snr_latency')]:
        fig,axes=plt.subplots(2,3,figsize=(12,6.3),sharex=True)
        for i,noise in enumerate(['washing_machine','keyboard_typing']):
            for j,input_snr in enumerate([0,5,10]):
                ax=axes[i,j];group=[r for r in summaries if r['NoiseClass']==noise and r['InputSNR_dB']==input_snr]
                w=[next(r for r in group if r['Method']==m) for m in METHODS[1:5]];reference=next(r for r in group if r['Method']=='DeepFilterNet3');noisy=next(r for r in group if r['Method']=='Noisy')
                means=np.array([r[metric] for r in w]);low=np.array([r[metric+'_CI_low'] for r in w]);high=np.array([r[metric+'_CI_high'] for r in w])
                ax.errorbar([10,20,40,80],means,yerr=np.maximum(np.vstack([means-low,high-means]),0),marker='o',capsize=3,color='#176b87',label='Causal Wiener')
                ax.errorbar([40],[reference[metric]],yerr=[[max(0,reference[metric]-reference[metric+'_CI_low'])],[max(0,reference[metric+'_CI_high']-reference[metric])]],fmt='D',capsize=4,color='#b3532b',label='DeepFilterNet3')
                ax.axhline(noisy[metric],ls='--',color='#777',label='Noisy');ax.set_title(f'{noise.replace("_"," ")} | {input_snr} dB input',fontsize=10)
                ax.set_xticks([10,20,40,80]);ax.grid(alpha=.2);ax.set_ylabel(label)
                if i==1:ax.set_xlabel('Oldest-sample block-ready delay (ms)')
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,frameon=False)
        fig.tight_layout(rect=[0,.055,1,1]);fig.savefig(figures/(name+'.png'));fig.savefig(figures/(name+'.pdf'));plt.close(fig)
    verification={'cases':len(cases),'metric_rows':len(rows),'speaker_clusters':6,'shared_wav_mat_arrays_equal':True,
                  'input_snr_max_abs_error':max(abs(r['OutputSNR_dB']-r['InputSNR_dB']) for r in rows if r['Method']=='Noisy'),
                  'resampling_unit':'Speaker; 2000 replicates, conditional on the four noise recordings','bootstrap_seed':5305,
                  'upstream_pretraining_overlap':'Not independently ruled out','python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform()}
    (OUT/'quality_verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print('PASS: 864 paired quality rows, identical shared inputs, and speaker-cluster intervals.',flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--cohort',choices=['voicebank','external'],default='voicebank');args=parser.parse_args()
    if args.cohort=='external':OUT=ROOT/'results/final_external';LOCAL=ROOT/'data/local/final_external'
    main()
