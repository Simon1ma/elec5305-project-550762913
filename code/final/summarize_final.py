"""Summarise measured timing, validation, and a fixed keyboard event."""
from pathlib import Path
import argparse,csv,json,platform
import numpy as np
from scipy.io import loadmat
from scipy.signal import spectrogram
import soundfile as sf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]

def read(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))

def write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser();p.add_argument('--cohort',choices=['voicebank','external'],default='external');args=p.parse_args()
    suffix='final_external' if args.cohort=='external' else 'final'
    out=ROOT/'results'/suffix;local=ROOT/'data/local'/suffix
    manifest=json.loads((out/'input_manifest.json').read_text());metrics=read(out/'metrics.csv')
    blocks=read(out/'wiener_block_timings.csv');timings=[]
    for noise in ['washing_machine','keyboard_typing']:
        for window in [10,20,40,80]:
            selected=[r for r in blocks if r['Noise']==noise and int(r['Window_ms'])==window]
            ms=np.array([float(r['StepSeconds'])*1000 for r in selected]);budget=window/2
            timings.append({'Noise':noise,'Window_ms':window,'Calls':len(ms),'HopBudget_ms':budget,
                'Step_p50_ms':float(np.quantile(ms,.5)),'Step_p95_ms':float(np.quantile(ms,.95)),
                'Step_p99_ms':float(np.quantile(ms,.99)),'Step_max_ms':float(ms.max()),
                'OverHopBudgetCalls':int(np.sum(ms>budget)),'OverHopBudgetFraction':float(np.mean(ms>budget))})
    write(out/'block_timing_summary.csv',timings)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':240})
    fig,axes=plt.subplots(1,2,figsize=(10,3.4))
    for ax,noise in zip(axes,['washing_machine','keyboard_typing']):
        for window in [10,20,40,80]:
            values=np.sort([float(r['StepSeconds'])/(window/2000) for r in blocks if r['Noise']==noise and int(r['Window_ms'])==window])
            ax.plot(values,np.arange(1,len(values)+1)/len(values),label=f'{window} ms window')
        ax.axvline(1,color='#b3532b',ls='--',label='Hop budget');ax.set_xscale('log');ax.set_ylim(0,1.02)
        ax.set_xlabel('Step time / hop budget (log scale)');ax.set_ylabel('Empirical cumulative fraction')
        ax.set_title(noise.replace('_',' '));ax.grid(alpha=.2)
    axes[0].legend(fontsize=8,frameon=False);fig.tight_layout();fig.savefig(out/'figures/block_timing.png');plt.close(fig)
    noisy={r['CaseID']:r for r in metrics if r['Method']=='Noisy'}
    harmed=[]
    for method in ['Wiener10','Wiener20','Wiener40','Wiener80','DeepFilterNet3']:
        for noise in ['washing_machine','keyboard_typing']:
            for snr in ['0','5','10']:
                rows=[r for r in metrics if r['Method']==method and r['NoiseClass']==noise and r['InputSNR_dB']==snr]
                harmed.append({'Method':method,'Noise':noise,'InputSNR_dB':int(snr),'Cases':len(rows),
                    'STOI_lower_than_noisy':sum(float(r['STOI'])<float(noisy[r['CaseID']]['STOI']) for r in rows)})
    write(out/'stoi_decrease_counts.csv',harmed)
    checks=read(out/'wiener_checks.csv');ref=read(out/'reference_checks.csv')
    validation={'cases':len(manifest['cases']),'quality_rows':len(metrics),'reconstruction_max_relative_error':max(float(r['ReconstructionRelativeError']) for r in checks),
        'reference_full_scale_flags':sum(r['PCM16ClippingDetected'].lower()=='true' for r in ref),
        'ten_ms_input_blocks_below_reference_silence_power_threshold':sum(c['blocks_below_reference_silence_threshold'] for c in manifest['cases']),
        'silence_threshold_note':'Input power <1e-7 flags possible official silence branch; internal model branch decisions are not logged.',
        'profiled_step_calls':len(blocks),'over_hop_budget_calls':sum(r['OverHopBudget'].lower() in ['1','true'] for r in blocks),
        'profiled_calls_note':'Includes calibration calls and timer/validation overhead; excludes EOF flush. Not a hard real-time guarantee.',
        'cpu':'Intel Core i7-14700HX (20 cores, 28 logical processors)','platform':platform.platform()}
    (out/'validation_summary.json').write_text(json.dumps(validation,indent=2)+'\n')
    path=local/'event_diagnostics.mat'
    if path.exists():event_plot(out,local,manifest,loadmat(path,simplify_cells=True))
    print(json.dumps(validation,indent=2))

def event_plot(out,local,manifest,d):
    fs=int(d['fs']);N=int(d['N']);P=int(d['P']);noise=d['trueNoise'];case_id=d['caseID']
    # Peak 20 ms true-noise energy; select before examining any method output.
    starts=np.arange(int(.3*fs),N-int(.3*fs)-960,480)
    energies=np.array([np.mean(noise[s:s+960]**2) for s in starts]);peak=int(starts[np.argmax(energies)]+480)
    a=peak-int(.2*fs);b=peak+int(.2*fs);centre=peak/fs
    saved=loadmat(local/'wiener'/(case_id+'.mat'),simplify_cells=True)
    raw,rate=sf.read(local/'reference'/(case_id+'.wav'));assert rate==fs
    signals=[d['clean'],d['noisy'],saved['outputs'][:,0],saved['outputs'][:,3],raw[1440+P:1440+P+N]]
    labels=['Clean','Noisy','Wiener 10 ms','Wiener 80 ms','DeepFilterNet3 (40 ms ready)']
    fig=plt.figure(figsize=(11,8.2));grid=fig.add_gridspec(5,3,width_ratios=[1.1,1.35,1.1],hspace=.55,wspace=.4)
    freqs,times,reference=spectrogram(signals[0],fs,window='hann',nperseg=960,noverlap=720,nfft=1024,mode='magnitude',scaling='spectrum')
    vmax=20*np.log10(reference.max()+1e-30);vmin=vmax-70;amplitude=max(np.max(np.abs(s[a:b])) for s in signals)*1.08
    summaries=[]
    for i,(signal,label) in enumerate(zip(signals,labels)):
        ax=fig.add_subplot(grid[i,0]);ax.plot(np.arange(a,b)/fs,signal[a:b],lw=.55,color='#176b87');ax.set_ylim(-amplitude,amplitude);ax.set_xlim(a/fs,b/fs);ax.set_ylabel(label,fontsize=8);ax.tick_params(labelsize=8)
        f,t,S=spectrogram(signal,fs,window='hann',nperseg=960,noverlap=720,nfft=1024,mode='magnitude',scaling='spectrum')
        ax=fig.add_subplot(grid[i,1]);ax.pcolormesh(t,f/1000,20*np.log10(np.maximum(S,1e-30)),shading='auto',vmin=vmin,vmax=vmax,cmap='magma');ax.set_xlim(a/fs,b/fs);ax.set_ylim(0,8);ax.tick_params(labelsize=8)
        if i==0:ax.set_title('Shared 20 ms display STFT',fontsize=9)
        if i==4:ax.set_xlabel('Time in speech (s)')
        if i>0:summaries.append({'Method':label,'EventSNR_dB':float(10*np.log10(np.sum(signals[0][a:b]**2)/np.sum((signal[a:b]-signals[0][a:b])**2)))})
    for row,window in [(0,10),(2,80)]:
        g=d['diagnostics'][f'window{window}'];ax=fig.add_subplot(grid[row:row+2,2])
        im=ax.pcolormesh(g['frameCentreSeconds'],g['frequency']/1000,g['gain'],shading='auto',vmin=0,vmax=1,cmap='viridis');ax.set_xlim(a/fs,b/fs);ax.set_ylim(0,8);ax.set_title(f'Native gain: {window} ms window',fontsize=9);ax.set_ylabel('kHz');fig.colorbar(im,ax=ax,label='Linear gain',fraction=.04)
    ax=fig.add_subplot(grid[4,2]);ax.axis('off');ax.text(0,.9,f'Peak-noise event at {centre:.3f} s\nFixed first keyboard case, 0 dB\nCommon waveform and spectral scales\nGain grids retain native resolution',fontsize=8,va='top')
    fig.suptitle('Keyboard event inspection | '+case_id,fontsize=10);fig.savefig(out/'figures/keyboard_event.png',bbox_inches='tight');plt.close(fig)
    write(out/'event_metrics.csv',summaries)
    (out/'event_selection.json').write_text(json.dumps({'case_id':case_id,'event_centre_s':centre,'interval_s':[a/fs,b/fs],
        'selection':'Maximum 20 ms true-noise energy, 10 ms grid, excluding 300 ms speech boundaries; no enhancement outcomes used.',
        'display_stft':'20 ms periodic Hann, 5 ms display hop, FFT1024; gain grids remain native.'},indent=2)+'\n')

if __name__=='__main__':main()
