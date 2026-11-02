"""Prepare the prospectively specified LibriSpeech test-clean external cohort."""
from pathlib import Path
import argparse,csv,hashlib,io,json,tarfile,urllib.request
import numpy as np
import soundfile as sf
from scipy.io import savemat
from scipy.signal import resample_poly

ROOT=Path(__file__).resolve().parents[2];LOCAL=ROOT/'data/local/final_external';OUT=ROOT/'results/final_external'
URL='https://openslr.trmal.net/resources/12/test-clean.tar.gz'


def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,default=LOCAL/'test-clean.tar.gz');args=p.parse_args()
    LOCAL.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    if not args.archive.exists():urllib.request.urlretrieve(URL,args.archive)
    with urllib.request.urlopen('https://openslr.trmal.net/resources/12/md5sum.txt',timeout=60) as response:checks=response.read().decode()
    expected=next(line.split()[0] for line in checks.splitlines() if line.split()[-1].endswith('test-clean.tar.gz'))
    actual=hashlib.md5(args.archive.read_bytes()).hexdigest();assert actual==expected
    speech=[]
    with tarfile.open(args.archive) as archive:
        names=sorted(m.name for m in archive.getmembers() if m.name.endswith('.flac'))
        speakers=sorted({Path(n).name.split('-')[0] for n in names})[:6]
    # Stream a second time instead of repeatedly seeking inside a gzip file.
    payloads={speaker:[] for speaker in speakers}
    with tarfile.open(args.archive,mode='r|gz') as archive:
        for member in archive:
            if not member.name.endswith('.flac'):continue
            speaker=Path(member.name).name.split('-')[0]
            if speaker not in payloads:continue
            raw=archive.extractfile(member).read()
            if sf.info(io.BytesIO(raw)).duration>=4.5:payloads[speaker].append((member.name,raw))
    for speaker in speakers:
        selected=sorted(payloads[speaker],key=lambda item:item[0])[:2];assert len(selected)==2
        for name,raw in selected:
            x,rate=sf.read(io.BytesIO(raw),dtype='float64');assert rate==16000 and x.ndim==1
            x=resample_poly(x[:72000],3,1)
            speech.append({'id':Path(name).stem,'speaker':speaker,'audio':x,'source_member':name,'source_sha256':hashlib.sha256(raw).hexdigest()})
    earlier=json.loads((ROOT/'results/final/input_manifest.json').read_text());noises=[]
    for entry in earlier['noise_sources']:
        path=ROOT/'data/local/final/noise'/entry['filename'];raw=path.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==entry['source_sha256']
        n,rate=sf.read(io.BytesIO(raw));assert rate==44100
        noises.append({**entry,'audio':resample_poly(n,160,147)[:235200]})
    raw_cases=[];peak=0;P=14400;N=216000;T=4800;fs=48000
    for s in speech:
        for noise in noises:
            for snr_db in [0,5,10]:
                factor=np.sqrt(np.sum(s['audio']**2)/(10**(snr_db/10)*np.sum(noise['audio'][P:P+N]**2)))
                mix=noise['audio']*factor;mix[P:P+N]+=s['audio'];peak=max(peak,float(np.max(np.abs(mix))),float(np.max(np.abs(s['audio']))))
                raw_cases.append((s,noise,snr_db,mix))
    scale=min(1,.8/peak);cases=[];case_dir=LOCAL/'cases';case_dir.mkdir(exist_ok=True)
    for s,noise,snr_db,mix in raw_cases:
        case_id=f"{s['id']}__{noise['category']}_{noise['src_file']}__snr{snr_db}"
        shared=(mix*scale).astype(np.float32);clean=s['audio']*scale
        actual=10*np.log10(np.sum(clean**2)/np.sum((shared[P:P+N].astype(float)-clean)**2));assert abs(actual-snr_db)<1e-5
        wav=case_dir/(case_id+'.wav');mat=case_dir/(case_id+'.mat');sf.write(wav,shared,fs,subtype='FLOAT')
        savemat(mat,{'input':shared.astype(float)[:,None],'clean':clean[:,None],'fs':fs,'prefixSamples':P,'speechSamples':N,'tailSamples':T},do_compression=True)
        cases.append({'case_id':case_id,'speaker':s['speaker'],'speech_id':s['id'],'noise_class':noise['category'],'noise_source':noise['src_file'],'noise_file':noise['filename'],
            'input_snr_db':snr_db,'actual_input_snr_db':float(actual),'input_wav':wav.relative_to(ROOT).as_posix(),'input_mat':mat.relative_to(ROOT).as_posix(),
            'shared_input_sha256':hashlib.sha256(wav.read_bytes()).hexdigest(),'blocks_below_reference_silence_threshold':int(np.sum((shared.reshape(-1,480).astype(float)**2).mean(axis=1)<1e-7))})
    manifest={**{k:v for k,v in earlier.items() if k not in ['cases','speech_sources','evaluation_speakers','common_input_attenuation','speech_archive','speech_doi']},
        'cohort':'External LibriSpeech test-clean','speech_archive':URL,'speech_archive_md5_verified':expected,
        'selection_rule':'First six lexicographic test-clean speakers; first two sorted >=4.5 s FLACs each; first 4.5 s.',
        'speech_resampling':'16 to 48 kHz, polyphase up=3; no added speech bandwidth; preparation outside measured enhancement latency.',
        'evaluation_speakers':speakers,'common_input_attenuation':scale,'speech_sources':[{k:v for k,v in s.items() if k!='audio'} for s in speech],'cases':cases}
    manifest.pop('speech_doi',None)
    (OUT/'input_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with (OUT/'case_manifest.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
    print('Prepared external cohort:',len(cases),'mixtures; speakers',speakers,flush=True)


if __name__=='__main__':main()
