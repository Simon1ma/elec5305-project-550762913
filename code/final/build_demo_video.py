"""Create a captioned walkthrough of actual MATLAB app results and fixed-gain audio.

Optional authoring packages: pillow and imageio-ffmpeg. The displayed app images
are exported after actual reruns in launch_final_demo, not invented UI mockups.
"""
from pathlib import Path
import csv,hashlib,json,subprocess,textwrap
import numpy as np
import soundfile as sf
from scipy.io import loadmat
from PIL import Image,ImageDraw,ImageFont,ImageOps
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/final_external';LOCAL=ROOT/'data/local/final_external'
W,H=1600,1100

def main():
    work=ROOT/'tmp/video';work.mkdir(parents=True,exist_ok=True)
    submission=ROOT/'submissions';submission.mkdir(exist_ok=True)
    font=lambda size,bold=False:ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size)
    manifest=json.loads((OUT/'input_manifest.json').read_text());first=manifest['cases'][0]['speech_id']
    secondary=json.loads((ROOT/'results/final/input_manifest.json').read_text())
    cohorts=[]
    for label,source in [('Primary: LibriSpeech test-clean',manifest),('Secondary: VoiceBank / VCTK',secondary)]:
        speakers={c['speaker'] for c in source['cases']}
        utterances={(c['speaker'],c['speech_id']) for c in source['cases']}
        assert len(speakers)==6 and len(utterances)==12 and len(source['cases'])==144
        assert all(sum(s==speaker for s,_ in utterances)==2 for speaker in speakers)
        cohorts.append({'label':label,'speakers':len(speakers),'utterances':len(utterances),'mixtures':len(source['cases'])})
    case=next(c for c in manifest['cases'] if c['speech_id']==first and c['noise_class']=='keyboard_typing' and c['input_snr_db']==0)
    d=loadmat(LOCAL/'wiener'/(case['case_id']+'.mat'),simplify_cells=True);P=manifest['prefix_samples'];N=manifest['speech_samples'];fs=manifest['fs']
    raw,rate=sf.read(LOCAL/'reference'/(case['case_id']+'.wav'));assert rate==fs
    signals={'Clean':d['clean'],'Noisy':d['noisy'],**{f'Wiener{window}':d['outputs'][:,i] for i,window in enumerate([10,20,40,80])},'DeepFilterNet3':raw[1440+P:1440+P+N]}
    gain=.95/max(1,max(np.max(np.abs(y)) for y in signals.values()))
    audio_dir=OUT/'audio';audio_dir.mkdir(exist_ok=True)
    for method,y in signals.items():sf.write(audio_dir/(method+'.wav'),y*gain,fs,subtype='PCM_24')
    rows=list(csv.DictReader((OUT/'metrics.csv').open()));case_scores={r['Method']:r for r in rows if r['CaseID']==case['case_id']}
    def card(title,lines,name,code=False):
        im=Image.new('RGB',(W,H),'#f6f9fb');draw=ImageDraw.Draw(im);draw.rectangle((0,0,W,18),fill='#176b87')
        draw.text((90,90),title,font=font(52,True),fill='#163c50')
        y=215
        for line in lines:
            chosen=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',33) if code else font(37)
            for part in textwrap.wrap(line,width=64 if not code else 72,break_long_words=False):
                draw.text((92,y),part,font=chosen,fill='#233b46');y+=53
            y+=27
        draw.text((90,H-85),'Yixiang Ma | ELEC5305 Final Project | SID 550762913',font=font(26),fill='#52656d')
        target=work/(name+'.png');im.save(target);return target
    def app_scene(image_name,title,caption,name):
        im=Image.new('RGB',(W,H),'#f6f9fb');draw=ImageDraw.Draw(im)
        draw.text((65,26),title,font=font(35,True),fill='#163c50')
        shot=ImageOps.contain(Image.open(OUT/'figures'/image_name).convert('RGB'),(1500,950));im.paste(shot,((W-shot.width)//2,84))
        draw.rectangle((0,H-84,W,H),fill='#163c50');draw.text((65,H-64),caption,font=font(28),fill='white')
        target=work/(name+'.png');im.save(target);return target
    scenes=[]
    def add(path,duration,audio=None):scenes.append({'image':path,'seconds':duration,'audio':audio})
    add(card('Causal speech enhancement: latency and quality',[
        'Question: what quality does a causal enhancer retain as its output waiting time changes?',
        'Stateful MATLAB Wiener: 10 / 20 / 40 / 80 ms windows.',
        'Official pretrained DeepFilterNet3: compare at the same 40 ms ready delay.',
        'This captioned walkthrough uses actual app exports and evaluated audio. Recorded files; no live microphone latency claim.'
    ],'01_title'),10)
    im=Image.new('RGB',(W,H),'#f6f9fb');draw=ImageDraw.Draw(im)
    draw.rectangle((0,0,W,18),fill='#176b87')
    draw.text((90,80),'Evaluation design: two speech cohorts',font=font(48,True),fill='#163c50')
    for cohort,y,detail in zip(cohorts,[195,445],[
        '16 kHz originals resampled to 48 kHz for processing',
        'Native 48 kHz recordings; secondary engineering comparison']):
        draw.rounded_rectangle((80,y,1520,y+220),radius=18,fill='white',outline='#d3e0e7',width=2)
        draw.text((110,y+25),cohort['label'],font=font(40,True),fill='#176b87')
        draw.text((110,y+85),'6 speakers x 2 utterances = 12 speech clips',font=font(36),fill='#233b46')
        draw.text((110,y+145),detail,font=font(30),fill='#52656d')
    lines=[
        'Each cohort: 12 clips x 4 noise recordings x 3 SNRs = 144 mixtures',
        'Noise: 2 washing-machine + 2 keyboard recordings | SNR: 0 / 5 / 10 dB',
        'Scoring: noisy + Wiener10/20/40/80 + DeepFilterNet3 = 6 conditions',
        'Combined: 288 mixtures and 1,728 quality-score rows',
        'The listening demo below illustrates one case from this larger evaluation.'
    ]
    for i,line in enumerate(lines):
        draw.text((90,715+58*i),line,font=font(30,i==3),fill='#163c50' if i==3 else '#233b46')
    draw.text((90,H-65),'Yixiang Ma | ELEC5305 Final Project | SID 550762913',font=font(26),fill='#52656d')
    cohortpath=work/'01b_evaluation_design.png';im.save(cohortpath);add(cohortpath,18)
    add(card('Run the code and audition the result',[
        "addpath(fullfile(pwd,'code','final'));",
        "launch_final_demo('external');",
        'Choose noise, input SNR and method; click Run processor.',
        'The app reruns the actual processor and checks agreement with its evaluated output. Clean / noisy / processed playback uses the same gain.'
    ],'02_commands',code=True),10)
    firstshot='demo_keyboard10.png'
    add(app_scene(firstshot,'Listen 1 / 5: clean reference','Audio: clean speech | Same fixed keyboard case for every listening segment','03_clean'),7,'Clean')
    add(app_scene(firstshot,'Listen 2 / 5: noisy mixture, 0 dB SNR','Audio: noisy input | Keyboard source 53501 | No independent loudness normalisation','04_noisy'),7,'Noisy')
    for index,method,shot in [(3,'Wiener10','demo_keyboard10.png'),(4,'Wiener80','demo_keyboard80.png'),(5,'DeepFilterNet3','demo_deepfilter.png')]:
        score=case_scores[method];ready=int(score['ReadyDelay_ms']);snr=float(score['OutputSNR_dB']);stoi=float(score['STOI'])
        add(app_scene(shot,f'Listen {index} / 5: {method}',f'Audio: {method} | Ready {ready} ms | This clip SNR {snr:.2f} dB, STOI {stoi:.4f}',f'0{index+2}_{method}'),8,method)
    chart=Image.open(OUT/'figures/quality_latency.png').convert('RGB');im=Image.new('RGB',(W,H),'#f6f9fb');draw=ImageDraw.Draw(im)
    draw.text((65,35),'Across speakers: quality versus ready delay',font=font(42,True),fill='#163c50');chart=ImageOps.contain(chart,(1490,850));im.paste(chart,((W-chart.width)//2,130))
    draw.text((65,980),'External keyboard, 0 dB: STOI noisy 0.7336 | Wiener40 0.6953 | DFNet3 0.8998',font=font(30),fill='#163c50')
    draw.text((65,1030),'6 speakers, 144 paired mixtures; intervals resample speakers, conditional on four noises.',font=font(27),fill='#52656d');chartpath=work/'08_results.png';im.save(chartpath);add(chartpath,12)
    add(card('What the measurements establish',[
        'Noise reduction and speech preservation can disagree: Wiener improves keyboard SNR while reducing STOI.',
        '40 ms ready delay is separate from the 30 ms DFNet3 transport shift and from CPU/device time.',
        '25,718 profiled Wiener calls met their hop budgets on this PC. This is not a hard real-time guarantee.',
        'LibriSpeech has 16 kHz source bandwidth. VCTK results are secondary because of upstream training-overlap risk.'
    ],'09_limits'),12)
    add(card('Sources and reproducibility',[
        'Speech: LibriSpeech test-clean, OpenSLR SLR12 (Panayotov et al., CC BY 4.0). Recording 1089-134686-0000; first 4.5 s, resampled and mixed.',
        'Keyboard: ESC-50 1-53501-A, derived from typing.wav by jennypendel, Freesound 53501 (CC Sampling+; ESC-50 CC BY-NC). Resampled/scaled; mixed and enhanced.',
        'Enhancer: official DeepFilterNet3 v0.5.6 runtime, pinned model. No training or fine-tuning.',
        'Code, full report, exact metrics, provenance and run instructions: github.com/Simon1ma/elec5305-project-550762913'
    ],'10_sources'),12)
    audio=np.zeros((round(sum(s['seconds'] for s in scenes)*fs),),dtype=np.float64);offset=0
    for scene in scenes:
        if scene['audio']:
            y=signals[scene['audio']]*gain;begin=round((offset+1)*fs);audio[begin:begin+N]=y
        offset+=scene['seconds']
    soundtrack=work/'soundtrack.wav';sf.write(soundtrack,audio,fs,subtype='PCM_24')
    listing=work/'scenes.txt'
    listing.write_text(''.join(f"file '{s['image'].as_posix()}'\nduration {s['seconds']}\n" for s in scenes)+f"file '{scenes[-1]['image'].as_posix()}'\n")
    video=submission/'Final_Project_Demo.mp4'
    command=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-f','concat','-safe','0','-i',str(listing),'-i',str(soundtrack),'-r','24','-c:v','libx264','-preset','medium','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-t',str(offset),'-movflags','+faststart',str(video)]
    subprocess.run(command,check=True,stdout=subprocess.DEVNULL,stderr=(work/'encoding.log').open('w'))
    evidence={'case_id':case['case_id'],'selection':'First external utterance, first keyboard source at 0 dB; not selected by scores.',
        'duration_seconds':offset,'video_style':'Captioned walkthrough using actual MATLAB app exports after processor reruns; no simulated live cursor or microphone capture.',
        'common_audio_gain':gain,'sample_rate':fs,'listening_order':['Clean','Noisy','Wiener10','Wiener80','DeepFilterNet3'],
        'evaluation_cohorts':cohorts,
        'clip_metrics':case_scores,'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
        'app_export_sha256':{name:hashlib.sha256((OUT/'figures'/name).read_bytes()).hexdigest() for name in ['demo_keyboard10.png','demo_keyboard80.png','demo_deepfilter.png']},
        'scenes':[{'start_seconds':sum(x['seconds'] for x in scenes[:i]),'seconds':s['seconds'],'audio':s['audio']} for i,s in enumerate(scenes)]}
    (OUT/'video_manifest.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('Created',video,'duration',offset,'seconds',flush=True)

if __name__=='__main__':main()
