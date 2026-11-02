"""Create a predeclared speaker/source-disjoint causal evaluation subset."""
from pathlib import Path
import csv
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
import numpy as np
import soundfile as sf
from scipy.io import savemat
from scipy.signal import resample_poly

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'code/latency'))
from prepare_data import RemoteZip

LOCAL=ROOT/'data/local/final';OUT=ROOT/'results/final'
TRAIN_URL='https://datashare.ed.ac.uk/server/api/core/bitstreams/245452b6-6235-44b6-a6f9-e7eb19797769/content'
ESC='https://raw.githubusercontent.com/karolpiczak/ESC-50/33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6/'


def get(url):
    with urllib.request.urlopen(url,timeout=60) as response:return response.read()


def main():
    LOCAL.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    speech_dir=LOCAL/'speech';speech_dir.mkdir(exist_ok=True)
    noise_dir=LOCAL/'noise';noise_dir.mkdir(exist_ok=True)
    fs=48000;N=216000;P=14400;T=4800;total=P+N+T
    speech=[]
    with zipfile.ZipFile(RemoteZip(TRAIN_URL)) as z:
        names=sorted(n for n in z.namelist() if n.endswith('.wav'))
        speakers=sorted({Path(n).stem.split('_')[0] for n in names})[:6]
        assert 'p232' not in speakers and 'p257' not in speakers
        for speaker in speakers:
            selected=0
            for name in names:
                if not Path(name).name.startswith(speaker+'_'):continue
                target=speech_dir/Path(name).name
                raw=target.read_bytes() if target.exists() else z.read(name)
                info=sf.info(io.BytesIO(raw))
                if info.duration<4.5 or info.samplerate!=fs:continue
                target.write_bytes(raw)
                x,rate=sf.read(io.BytesIO(raw),dtype='float64');assert x.ndim==1 and rate==fs
                speech.append({'id':target.stem,'speaker':speaker,'audio':x[:N],
                    'source_member':name,'source_sha256':hashlib.sha256(raw).hexdigest()})
                selected+=1
                if selected==2:break
            assert selected==2
            print('Selected evaluation speaker',speaker,flush=True)
    metadata=list(csv.DictReader(io.StringIO(get(ESC+'meta/esc50.csv').decode())))
    (noise_dir/'ESC50_LICENSE.txt').write_bytes(get(ESC+'LICENSE'))
    noises=[]
    for category in ['washing_machine','keyboard_typing']:
        seen=set()
        for record in sorted((r for r in metadata if r['category']==category),key=lambda r:r['filename']):
            source=record['src_file']
            if source in seen or source=='137':continue
            target=noise_dir/record['filename']
            raw=target.read_bytes() if target.exists() else get(ESC+'audio/'+record['filename'])
            target.write_bytes(raw)
            n,rate=sf.read(io.BytesIO(raw),dtype='float64');assert rate==44100 and n.ndim==1
            n=resample_poly(n,160,147);assert len(n)>=total
            noises.append({**record,'audio':n[:total],'source_sha256':hashlib.sha256(raw).hexdigest(),
                'source_url':ESC+'audio/'+record['filename']})
            seen.add(source)
            if len(seen)==2:break
        assert len(seen)==2
    raw_cases=[];peak=0
    for s in speech:
        for noise in noises:
            for snr_db in [0,5,10]:
                factor=np.sqrt(np.sum(s['audio']**2)/(10**(snr_db/10)*np.sum(noise['audio'][P:P+N]**2)))
                mix=noise['audio']*factor;mix[P:P+N]+=s['audio']
                peak=max(peak,float(np.max(np.abs(mix))),float(np.max(np.abs(s['audio']))))
                raw_cases.append((s,noise,snr_db,mix))
    scale=min(1,.8/peak)
    cases=[];case_dir=LOCAL/'cases';case_dir.mkdir(exist_ok=True)
    for s,noise,snr_db,mix in raw_cases:
        case_id=f"{s['id']}__{noise['category']}_{noise['src_file']}__snr{snr_db}"
        shared=(mix*scale).astype(np.float32);clean=s['audio']*scale
        actual=10*np.log10(np.sum(clean**2)/np.sum((shared[P:P+N].astype(float)-clean)**2))
        assert abs(actual-snr_db)<1e-5
        input_path=case_dir/(case_id+'.wav');sf.write(input_path,shared,fs,subtype='FLOAT')
        mat_path=case_dir/(case_id+'.mat')
        savemat(mat_path,{'input':shared.astype(float)[:,None],'clean':clean[:,None],
            'fs':fs,'prefixSamples':P,'speechSamples':N,'tailSamples':T},do_compression=True)
        block_power=shared.reshape(-1,480).astype(float)**2
        cases.append({'case_id':case_id,'speaker':s['speaker'],'speech_id':s['id'],
            'noise_class':noise['category'],'noise_source':noise['src_file'],'noise_file':noise['filename'],
            'input_snr_db':snr_db,'actual_input_snr_db':float(actual),
            'input_wav':input_path.relative_to(ROOT).as_posix(),'input_mat':mat_path.relative_to(ROOT).as_posix(),
            'shared_input_sha256':hashlib.sha256(input_path.read_bytes()).hexdigest(),
            'blocks_below_reference_silence_threshold':int(np.sum(block_power.mean(axis=1)<1e-7))})
    manifest={'research_question':'Latency-quality trade-offs in causal speech enhancement',
        'fs':fs,'prefix_samples':P,'speech_samples':N,'tail_samples':T,'common_input_attenuation':scale,
        'development_speaker':'p232','development_keyboard_source':'137',
        'evaluation_speakers':speakers,'speaker_disjoint_from_project_development':True,
        'noise_source_disjoint_from_project_development':True,
        'pretrained_training_overlap':'Not independently ruled out; project split does not establish upstream model independence.',
        'speech_archive':TRAIN_URL,'speech_doi':'10.7488/ds/2117','speech_licence':'CC BY 4.0',
        'noise_dataset':'ESC-50 pinned commit 33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6',
        'noise_licence':'ESC-50 CC BY-NC; original clip attribution retained in local ESC50_LICENSE.txt',
        'selection_rule':'First six sorted training-archive speakers; first two sorted >=4.5 s utterances each; first two distinct noise source IDs per category, excluding 137.',
        'speech_sources':[{k:v for k,v in s.items() if k!='audio'} for s in speech],
        'noise_sources':[{k:v for k,v in n.items() if k!='audio'} for n in noises],
        'cases':cases}
    (OUT/'input_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    with (OUT/'case_manifest.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(cases[0]));writer.writeheader();writer.writerows(cases)
    print('Prepared',len(cases),'shared mixtures from',len(speech),'utterances and',len(noises),'noise sources.',flush=True)


if __name__=='__main__':main()
