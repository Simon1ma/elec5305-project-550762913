"""Typeset the final research report directly from verified experiment tables.

Optional authoring dependency: reportlab. Processing/scoring does not need it.
"""
from pathlib import Path
import csv,json
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
from reportlab.graphics.shapes import Drawing,Rect,String,Line,Polygon

ROOT=Path(__file__).resolve().parents[2];EXT=ROOT/'results/final_external';SECOND=ROOT/'results/final'

def read(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
    output=ROOT/'output/pdf';output.mkdir(parents=True,exist_ok=True)
    summary=read(EXT/'summary_by_condition.csv');paired=read(EXT/'paired_vs_wiener40.csv')
    secondary=read(SECOND/'summary_by_condition.csv');timing=read(EXT/'block_timing_summary.csv')
    wb=read(EXT/'wiener_benchmark.csv');rb=read(EXT/'reference_benchmark.csv')
    validation=json.loads((EXT/'validation_summary.json').read_text());event=json.loads((EXT/'event_selection.json').read_text())
    def row(noise,snr,method,source=summary):return next(r for r in source if r['NoiseClass']==noise and int(r['InputSNR_dB'])==snr and r['Method']==method)
    def val(noise,snr,method,metric='STOI',digits=4,source=summary):
        number=float(row(noise,snr,method,source)[metric])
        if abs(number)<.5*10**(-digits):number=0.0
        return f"{number:.{digits}f}"
    def difference(noise,snr,method,metric='STOI',digits=4):
        r=next(r for r in paired if r['NoiseClass']==noise and int(r['InputSNR_dB'])==snr and r['Method']==method and r['Metric']==metric)
        return f"{float(r['MeanDifference']):+.{digits}f} [{float(r['CI_low']):+.{digits}f}, {float(r['CI_high']):+.{digits}f}]"
    styles=getSampleStyleSheet()
    for name,size,leading in [('BodyR',10,14),('SmallR',8.5,11),('CellR',8.2,10.3),('CaptionR',8.4,10.6)]:
        styles.add(ParagraphStyle(name=name,fontName='Helvetica',fontSize=size,leading=leading,spaceAfter=7))
    styles.add(ParagraphStyle(name='TitleR',fontName='Helvetica-Bold',fontSize=22,leading=26,spaceAfter=12,textColor=colors.HexColor('#163c50')))
    styles.add(ParagraphStyle(name='HeadR',fontName='Helvetica-Bold',fontSize=14,leading=18,spaceAfter=9,textColor=colors.HexColor('#163c50')))
    styles.add(ParagraphStyle(name='SubR',fontName='Helvetica-Bold',fontSize=10.8,leading=14,spaceBefore=5,spaceAfter=5))
    styles.add(ParagraphStyle(name='EquationR',fontName='Courier',fontSize=8.6,leading=12,spaceAfter=8,leftIndent=8))
    story=[];md=[]
    def p(text,style='BodyR'):
        story.append(Paragraph(escape(text),styles[style]));md.append(text+'\n')
    def h(text):p(text,'HeadR');md[-1]='## '+text+'\n'
    def sub(text):p(text,'SubR');md[-1]='### '+text+'\n'
    def eq(text):
        story.append(Paragraph(escape(text).replace('\n','<br/>'),styles['EquationR']));md.append('```text\n'+text+'\n```\n')
    def page():story.append(PageBreak());md.append('\n---\n')
    def caption(text):p(text,'CaptionR')
    def figure(name,caption_text,width=487,maxheight=300):
        path=EXT/'figures'/name;w,hh=ImageReader(str(path)).getSize();height=width*hh/w
        if height>maxheight:width*=maxheight/height;height=maxheight
        im=Image(str(path),width=width,height=height);im.hAlign='CENTER';story.append(im);caption(caption_text)
        md.append(f'![{caption_text}](../../results/final_external/figures/{name})\n')
    def table(headers,rows,widths):
        cells=[[Paragraph(escape(str(c)),styles['CellR']) for c in line] for line in [headers]+rows]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f0f4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#176b87')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#d3dce0')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        story.append(t);story.append(Spacer(1,6))
        md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n')

    p('Latency-Quality Trade-offs in\nReal-Time Causal Speech Enhancement'.replace('\n',' '),'TitleR')
    p('ELEC5305 Final Project | Yixiang Ma | SID 550762913 | 2 November 2026','SmallR')
    sub('Abstract')
    p('This project studies how a causal STFT Wiener enhancer trades waiting time for speech quality, and compares it with an official pretrained DeepFilterNet3 reference. Four Wiener windows, 10/20/40/80 ms, share a 100 ms decision-directed smoothing time constant. A separate LibriSpeech test-clean cohort supplies 144 paired mixtures: twelve utterances from six speakers, four noise recordings and three input SNRs. A second, native-48-kHz VCTK-derived cohort provides an engineering comparison with disclosed pretraining-overlap risk. On the external cohort at 0 dB keyboard SNR, Wiener40 raises waveform SNR to 2.13 dB but lowers STOI from 0.7336 to 0.6953. At the same 40 ms oldest-sample block-ready delay, DeepFilterNet3 obtains 13.55 dB and 0.8998. Longer Wiener windows improve mean STOI here, but do not monotonically improve waveform SNR. All 25,718 profiled external Wiener calls remain within their hop budgets on the tested CPU. These are causal recorded-file measurements, not device latency or a hard real-time guarantee.')
    h('1. Introduction and research question')
    p('Low-delay speech enhancement must decide what to suppress before much future context is available. A longer analysis window can make spectral structure easier to distinguish, while postponing output and combining speech events over a longer interval. A fast average implementation can still miss individual deadlines. These issues motivate measuring enhancement quality, sample availability and compute time as separate quantities.')
    p('Research question: How does causal STFT scheduling delay affect Wiener enhancement quality, and how does this classical baseline compare with a pretrained enhancer at a reconciled delay budget? The study concerns single-channel additive recorded noise. It does not train a neural model or measure human word recognition.')
    sub('1.1 Contribution and project continuity')
    p('The semester project progressed from an offline synthetic FIR/Wiener demonstration to a stateful causal processor, then to recorded keyboard noise and a pretrained reference. The final stage preserves those processors and expands the evaluation across speakers, noise sources and SNRs. Its contribution is the controlled window ablation, delay reconciliation, paired objective evaluation and failure analysis. Wiener filtering and DeepFilterNet are established methods; neither is claimed as a new algorithm.')
    p('The earlier single-utterance examples remain development evidence. Audio Processing Report 2 is separate coursework and supplies no final-project performance claim. Code, protocol, source identifiers, checks, full result tables and an audition app accompany this report.','SmallR')
    page()

    h('2. Literature review and research rationale')
    sub('2.1 Statistical spectral enhancement')
    p('Ephraim and Malah [1] distinguish Wiener spectral estimation from MMSE short-time spectral-amplitude estimation and introduce a decision-directed estimate of a priori SNR. This connects current observations with the preceding enhanced spectrum. Their formulation explains why a spectral estimator needs assumptions about speech and noise, rather than simply deleting all high-frequency energy. The present baseline uses a decision-directed Wiener gain with noisy phase; it does not implement their MMSE-STSA amplitude estimator.')
    p('For this investigation, a fixed noise estimate makes the assumptions inspectable. A noise-only startup interval supplies its PSD, and subsequent frames use the same estimate. This avoids an additional adaptation mechanism changing with window size, but deliberately exposes a weakness when transient noise differs from the initial sample. The resulting comparison is of this particular fixed-calibration baseline, not every possible classical Wiener system.')
    sub('2.2 Learned multi-frame enhancement')
    p('Schroter et al. [2] combine coarse ERB-band envelope gains with complex multi-frame filtering of lower-frequency speech. This differs from the baseline\'s real, binwise attenuation with noisy phase: a learned temporal representation can use speech structure beyond an initial noise PSD. It motivates a modern comparator, while also introducing dependence on pretrained data and inference implementation.')
    p('The paper describes a 48 kHz system with 20 ms windows, 10 ms hops and two frames of lookahead. The pinned runtime/configuration [3] is inspected separately before assigning its delay. The same paper reports DNS4 training with VCTK oversampling, so a new project speaker split alone cannot establish model-training independence. This finding changes the interpretation of the VCTK cohort and motivates a separate external corpus; it is not concealed by calling all new mixtures held out.')
    sub('2.3 Complementary metrics and the gap addressed here')
    p('Taal et al. [4] provide an objective intelligibility predictor for time-frequency weighted speech. The standard pystoi implementation [5] correlates short-time one-third-octave envelopes after its prescribed preprocessing. It is useful for detecting changes that waveform error alone may miss, but its score is not a percentage of words understood or a listening-test result.')
    p('Le Roux et al. [6] show why separation metrics need explicit definitions and propose SI-SDR. This study reports zero-mean projection SI-SDR beside ordinary reference-to-error SNR: one tolerates an overall reference scale, while the other penalises it. Neither score licenses output normalisation before comparison. Together with STOI and fixed-gain audition, they expose competing objectives rather than reducing quality to a single number.')
    table(['Literature / resource','Design consequence','Limitation retained'],[
        ['Statistical estimation [1]','Frozen decision-directed baseline','No claim to reproduce MMSE-STSA'],
        ['Learned multi-frame method [2,3]','Pinned modern reference; reconcile lookahead','Pretraining and backend dependence'],
        ['STOI and SI-SDR [4-6]','Complementary paired metrics','No human intelligibility evidence']], [123,184,180])
    caption('Table 1. The methodological gap is an auditable latency-quality comparison, rather than a claim to advance state-of-the-art enhancement.')
    page()

    h('3. Methods: stateful causal enhancement')
    diagram=Drawing(487,64)
    labels=['Recorded clean + noise','Shared mixture + prefix','Arrived-hop processor','Aligned scoring / audio']
    for i,label in enumerate(labels):
        x=i*125;diagram.add(Rect(x,22,112,30,fillColor=colors.HexColor('#e7f0f4'),strokeColor=colors.HexColor('#176b87')))
        diagram.add(String(x+56,34,label,fontName='Helvetica',fontSize=7.2,textAnchor='middle'))
        if i<3:diagram.add(Line(x+112,37,x+123,37,strokeColor=colors.HexColor('#176b87')))
    story.append(diagram);caption('Figure 1. Clean speech is used only for mixture construction and evaluation. Enhancement receives the arrived mixture samples, with no access to the clean reference.')
    sub('3.1 Causal framing and reconstruction')
    p('CausalWiener.step(arrived) maintains pending input, past samples, overlap-add accumulators, calibration spectra and previous enhanced power across calls. With window length L and hop H=L/2, a frame contains the previous H samples and the newly arrived H samples. Periodic Hann analysis is followed by FFT, gain multiplication, inverse FFT and overlap-add divided by the sum of analysis-window weights. There is no additional synthesis window. Past-only startup padding and a labelled EOF zero flush handle boundaries.')
    table(['Window / L (ms)','L (samples)','H (samples)','FFT length','Calibration frames'],[
        ['10','480','240','512','59'],['20','960','480','1024','29'],['40','1920','960','2048','14'],['80','3840','1920','4096','6']], [103,92,92,92,108])
    caption('Table 2. All methods run at 48 kHz. Calibration counts include complete frames within the same 300 ms prefix; this count necessarily varies with L.')
    sub('3.2 Frozen Wiener rule')
    p('After averaging the complete, already-arrived noise-only calibration frames, the noise PSD D[k] remains fixed. Let P[t,k]=|Y[t,k]|^2, Q[t-1,k] be the preceding enhanced power, and gamma=P/D. The decision-directed update and real gain are:')
    eq('alpha = exp(-H / (fs * 0.100))\nxi = alpha * Q_previous / D + (1-alpha) * max(gamma-1, 0)\nG = max(0.05, xi / (1+xi));  Q = G^2 * P')
    p('A PSD floor protects division. The common 100 ms time constant avoids giving the same per-frame alpha a different physical memory at each hop. Changing L still changes observation support, frequency resolution, calibration averaging and update cadence. Thus the experiment is a practical window/hop ablation, not an isolation of latency from every other signal-processing change. FFT zero-padding samples the spectrum more densely but adds no physical resolving power.')
    sub('3.3 Pretrained reference')
    p('The official v0.5.6 Windows Rust/Tract executable runs the pinned DeepFilterNet3 ONNX archive [3]. Binary/model SHA256 checks precede execution. Default inference thresholds are retained, with no postfilter, training or fine-tuning. Both processors consume exactly the same float32 mixture. Wiener retains double output; the reference CLI writes PCM16. This precision/backend difference is part of the evaluated systems and a limit on claims about algorithms alone.')
    page()

    h('4. Experimental design and data provenance')
    sub('4.1 Separate development, external and engineering cohorts')
    p('Development remains the earlier p232_003 VoiceBank utterance, DEMAND washing-machine recording and ESC-50 keyboard source 137. No final setting is selected from the final outcomes. The primary external cohort uses LibriSpeech test-clean [7]: the first six lexicographically sorted speaker IDs and the first two sorted recordings per speaker lasting at least 4.5 s. The first 4.5 s are retained and resampled once from 16 to 48 kHz by a 3:1 polyphase conversion. Upsampling adds no speech content above 8 kHz; resampling cost/delay is outside enhancement timing.')
    p('The original final expansion used twelve native-48-kHz utterances from the first six sorted speakers in the official VoiceBank clean training archive [8]. It completed before the training-data audit. After identifying VCTK in [2], all its results are retained as a secondary engineering cohort and the external selection rule is fixed before external inference. No parameters are retuned. Neither corpus certifies absence of upstream exposure because a complete model per-file training manifest is unavailable. The two corpora are analysed separately.')
    table(['Cohort','Speakers','Speech recordings','Role'],[
        ['External: LibriSpeech test-clean','1089, 1188, 121, 1221, 1284, 1320','2 per speaker; 12 total','Primary; 16 kHz source'],
        ['Engineering: VoiceBank / VCTK','p226, p227, p228, p230, p231, p233','2 per speaker; 12 total','Secondary; upstream overlap risk']], [119,161,99,108])
    caption('Table 3. Selection is deterministic rather than based on enhancement scores. Manifests retain every recording ID, source URL and hash.')
    sub('4.2 Noise selection and controlled mixtures')
    p('Each cohort uses two ESC-50 washing-machine sources (21896, 23996) and two keyboard sources (53501, 61212), selected by sorted filename with distinct original source IDs, excluding development source 137 [9]. These are recording-source-disjoint from project development, not proof that a pretrained model has never heard related noise. The first 4.9 s of each 5 s clip is resampled once from 44.1 to 48 kHz. No noise is looped.')
    eq('mixture = clean + beta * noise\nbeta = sqrt(sum(clean^2) / (10^(inputSNR/10) * sum(noise^2)))')
    p('Scaling uses only the scored speech interval. Each input has 300 ms of preceding real noise and 100 ms of real-noise tail. One common attenuation per cohort provides 0.8 peak headroom before float32 storage (external 0.22420135; engineering 0.28328995). Clean references receive the same attenuation; outputs are never independently normalised for scoring. Each cohort contains 12 utterances x 4 recordings x 3 SNRs (0/5/10 dB) = 144 paired mixtures, each scored under six conditions, yielding 864 rows.')
    sub('4.3 Metrics and uncertainty')
    p('SNR is 10 log10(sum(clean^2)/sum((output-clean)^2)). SI-SDR removes means and projects output onto clean before taking target-to-residual energy ratio. Standard pystoi 0.4.1 uses extended=False. Only known transport shifts are removed; no lag search optimises quality. Prefix/tail are excluded from the 4.5 s score. Within each noise/SNR group, utterance/source outcomes are averaged per speaker; 2,000 seed-5305 bootstrap resamples of six speakers provide exploratory 95% percentile intervals. Paired differences are formed within each speaker before resampling. The intervals condition on the four fixed noise files and do not turn 144 mixtures into 144 independent speakers.')
    page()

    h('5. Delay contract and validation')
    sub('5.1 Reconcile waveform shift with output availability')
    p('A transport shift is the displacement in equal-length input/output block arrays. It is not the age of an output sample when the block becomes available. For Wiener, a logical output block starting at sample s is emitted after samples through s+L have arrived. The oldest-sample block-ready delay is therefore L/fs; the newest-sample age is (L-H+1)/fs. Starting playback at each ready timestamp gives a conservative L/fs sample delay, before computation or devices.')
    table(['System','Transport shift (ms)','Oldest-sample ready (ms)','Evidence'],[
        ['Wiener 10/20/40/80','5 / 10 / 20 / 40','10 / 20 / 40 / 80','Impulse and per-block schedule'],
        ['DeepFilterNet3','30','40','Source/configuration + transport probe']], [115,115,126,131])
    caption('Table 4. The reference has L=20 ms, H=10 ms and two lookahead frames. Lookahead contributions combine as implemented, rather than being added twice.')
    p('The reference transport is L-H+2H=30 ms (1440 samples), while oldest-sample readiness is L+2H=40 ms. Hence Wiener40 is the matched-delay comparison, not Wiener20. Source inspection identifies its persistent inference state and hop loop [3]; an independent near-identity probe confirms transport. Wiener\'s 300 ms noise-only calibration remains a separate startup requirement. The reference receives the same prefix but does not use the baseline\'s fixed calibration rule.')
    sub('5.2 Validation before interpretation')
    table(['Check','Measured result','Scope'],[
        ['Unit-gain reconstruction','Maximum external relative error 2.984e-16','All 144 mixtures x 4 windows'],
        ['Chunk and future invariance','Maximum differences 0','All four Wiener settings on development checks'],
        ['Reference delay / trimming','1440 samples; exact CLI trim agreement','Separate development probes'],
        ['Reference future / repeats','Future-prefix error 0; repeats bit-identical','Development probe + representative repeats'],
        ['Shared input / input SNR','WAV=MAT exactly; max SNR error 1.38e-8 dB','All external mixtures'],
        ['PCM16 full-scale flags','0 / 144 external outputs','Threshold flag; not a perceptual clipping test']], [137,182,168])
    caption('Table 5. Historical causality probes are rerun on this PC and are labelled development checks. Final per-mixture reconstruction/input checks supplement them.')
    p('The original development quality table reproduces to maximum absolute difference 3.82e-14. This establishes continuity of the existing code, not new generalisation evidence. Diagnostic gain capture also leaves its selected final outputs unchanged to below 1e-12. End flushing occurs only after the real file ends; it is never described as steady-state access to future samples.')
    sub('5.3 Compute measurement')
    p('Timing is performed separately from quality, with no concurrent benchmark jobs: one omitted warm-up and seven repeats on the first utterance and first noise source of each class at 0 dB. Wiener RTF includes its sequential driver and EOF flush, excluding construction, preallocation, I/O and metrics. A separate full-hop step profile includes validation/timer overhead and calibration, and excludes EOF flush from recurring deadlines. Reference RTF comes from its internal frame-loop timer after setup; the binary does not expose per-hop timings. These differing scopes prevent an implementation-independent complexity ranking.')
    page()

    h('6. Results: external intelligibility-predictor trade-off')
    figure('quality_latency.png','Figure 2. External speaker-mean STOI versus oldest-sample block-ready delay. Bars are 95% speaker-bootstrap intervals, conditional on the four fixed noises. Dashed lines are noisy-input means; the neural point is at 40 ms.',maxheight=268)
    table(['0 dB input noise','Method','SNR (dB)','SI-SDR (dB)','STOI'],[
        [noise.replace('_',' '),method.replace('DeepFilterNet3','DFNet3'),val(noise,0,method,'OutputSNR_dB',2),val(noise,0,method,'SI_SDR_dB',2),val(noise,0,method)]
        for noise in ['washing_machine','keyboard_typing'] for method in ['Noisy','Wiener40','DeepFilterNet3']], [134,105,81,89,78])
    caption('Table 6. Matched 40 ms ready-delay systems at 0 dB. Each row averages 24 mixtures from six speakers; full window/SNR tables are supplied as CSV.')
    p('At 0 dB washing noise, Wiener STOI rises from 0.6981 at 10 ms to 0.7463 at 80 ms, while the noisy mean is 0.7228. With keyboard noise it rises from 0.6602 to 0.7065, remaining below noisy speech (0.7336). At 0 dB, Wiener10/20/40 reduce STOI in all 24 keyboard cases; Wiener80 does so in 23. The reference reduces it in none of those 24 cases. These counts are paired case descriptions, not independent statistical replications.')
    p('Longer waiting therefore helps this baseline\'s envelope-correlation score within the tested range, but does not resolve its transient-noise weakness. The reference obtains 0.8998 keyboard STOI at 40 ms, versus 0.6953 for Wiener40 and 0.7065 for Wiener80. Since the latter uses twice the ready delay, its smaller score cannot be explained simply by giving the reference more future context. Learned priors and estimator design differ as well; this experiment does not isolate which reference component causes the advantage.')
    page()

    h('7. Results: error metrics and paired comparisons')
    figure('snr_latency.png','Figure 3. External output SNR on the same mixtures, alignment and speaker units as Figure 2. Improvements in STOI and waveform SNR do not always select the same window or method.',maxheight=268)
    table(['Noise','Input SNR','DFNet3 - Wiener40 STOI [95% CI]'],[
        [noise.replace('_',' '),str(snr),difference(noise,snr,'DeepFilterNet3')]
        for noise in ['washing_machine','keyboard_typing'] for snr in [0,5,10]], [145,73,269])
    caption('Table 7. Paired speaker-mean differences at the common 40 ms ready delay. These exploratory intervals do not account for a wider population of noise recordings or multiple comparisons.')
    p('At 0 dB washing noise, output SNR increases from 7.07 dB (Wiener10) to 8.71 dB (Wiener40), then falls to 8.26 dB (Wiener80), although STOI increases. The paired 80-minus-40 ms changes are -0.447 dB SNR [ -0.595, -0.303 ] and +0.00795 STOI [ +0.00410, +0.01161 ]. This is a measured trade-off, not a monotonic benefit from waiting longer.')
    p('At 10 dB washing input, Wiener40 reaches 16.60 dB SNR versus 14.25 dB for the reference. The reference-minus-Wiener difference is -2.355 dB [ -4.729, -0.628 ], yet its STOI difference remains +0.02008. SI-SDR also favours Wiener40 here (16.50 versus 14.50 dB), so reference scaling alone does not explain the ordering. At 5 dB washing input, the SNR-difference interval includes zero. By contrast, at 0 dB keyboard input the reference SNR is 13.55 dB versus 2.13 dB for Wiener40. The evidence supports a strong transient-noise advantage in these recordings, not universal superiority in every metric.')
    page()

    h('8. Keyboard event and secondary cohort')
    figure('keyboard_event.png',f"Figure 4. First external keyboard case, 0 dB. The event centre ({event['event_centre_s']:.3f} s) maximises 20 ms true-noise energy on a 10 ms grid, excluding 300 ms speech boundaries. It is selected without enhancement scores. Waveforms and display STFTs share scales; native gain maps retain their own grids.",maxheight=380)
    eventrows=read(EXT/'event_metrics.csv')
    table(['Illustrative 400 ms event','Noisy','Wiener10','Wiener80','DFNet3'],[
        ['Reference-to-error SNR (dB)']+[f"{float(r['EventSNR_dB']):.2f}" for r in eventrows]], [171,79,79,79,79])
    p('The shared display STFT uses a 20 ms Hann window, 5 ms hop and FFT1024; a coarser native gain grid is therefore not confused with a different display setting. Native Wiener gains demonstrate the actual attenuation applied rather than a spectrogram-derived proxy. A fixed prefix PSD and long decision-directed memory can poorly represent later keyboard bursts, while attenuation can also weaken useful speech. This is a plausible interpretation of the event and whole-clip metrics, not proof from a noise-estimator ablation. No short-event STOI or phoneme-recognition claim is made.')
    sub('8.1 Secondary native-48-kHz engineering comparison')
    p('On the VCTK-derived cohort at 0 dB, washing STOI is 0.7169 noisy, 0.7254 Wiener40 and 0.8362 reference; keyboard values are 0.7004, 0.6582 and 0.8805. This broadly repeats the metric conflict seen externally: waveform SNR improves while keyboard STOI can worsen. It is corroborating engineering evidence only. Because VCTK occurs in the published training description, these numbers cannot establish unseen-speaker neural generalisation. Its native bandwidth and different speech levels also prevent treating cross-corpus score differences as an isolated bandwidth effect.')
    page()

    h('9. Runtime, deployment interpretation and limitations')
    figure('block_timing.png','Figure 5. External Wiener empirical distributions of step time divided by hop budget. Values below one fit the recurring input interval in these measured calls. Timings include instrumentation overhead and are not a device-latency measurement.',maxheight=178)
    table(['Noise','Window (ms)','RTF median','Step p99 (ms)','Step max (ms)','Hop (ms)'],[
        [r['Noise'].replace('_',' '),r['Window_ms'],f"{float(next(x for x in wb if x['Noise']==r['Noise'] and x['Window_ms']==r['Window_ms'])['RTF_median']):.4f}",f"{float(r['Step_p99_ms']):.3f}",f"{float(r['Step_max_ms']):.3f}",f"{float(r['HopBudget_ms']):.0f}"] for r in timing], [121,65,75,80,80,66])
    caption('Table 8. Seven repetitions per representative noise/window condition. Windows with longer hops can reduce per-second call overhead even when a single step takes longer.')
    p(f"All {validation['profiled_step_calls']:,} profiled external full-hop calls are within budget. Reference median RTF is {float(rb[0]['RTF_median']):.4f} for washing and {float(rb[1]['RTF_median']):.4f} for keyboard. Tests run on an Intel Core i7-14700HX (20 cores, 28 logical processors), approximately 31.8 GiB RAM, Windows 11 build 26200, MATLAB R2026a Update 5 and Python 3.12.14. Scoring uses numpy 2.4.6, scipy 1.17.1 and pystoi 0.4.1. These are measured backend costs on short recordings; they do not predict battery use, worst-case scheduling or embedded performance.")
    sub('9.1 What remains uncertain')
    p('Only six speakers per cohort and two recordings per noise class are sampled. The bootstrap captures speaker variation conditional on those files, not uncertainty across realistic rooms, microphones, reverberation or all noise types. The clean reference and known mixture recipe permit objective scoring but are unavailable to a deployed enhancer. Known noise-only startup is an advantage and a constraint of the baseline; a speech-contaminated prefix is not tested.')
    p('The reference is quantised to PCM16 while Wiener retains double precision, and the compute backends differ. There are 945 external 10 ms input blocks below the reference\'s 1e-7 silence-power threshold (542 in the secondary cohort). These are possible branch-trigger indicators, not logged internal decisions. Levels/thresholds are not changed after observing results; the global headroom policy can affect this pretrained system. No complete upstream file-overlap audit, live device loop, listening panel or reference per-hop deadline measurement is available. RTF below one and finite no-miss runs cannot establish a hard real-time guarantee.')
    page()

    h('10. Discussion and conclusion')
    p('The research question has a conditional answer. For the frozen Wiener design, spending more ready delay generally improves mean STOI across 10-80 ms, but its waveform-error optimum can occur earlier, and extra context alone does not repair keyboard-noise performance. At a common 40 ms ready delay the pretrained reference has higher mean STOI in every tested external noise/SNR condition, with positive paired intervals. On the cleaner washing mixtures, the classical method can retain higher waveform SNR and SI-SDR. Selecting a system therefore requires a latency constraint and an explicit quality objective rather than a single global ranking.')
    p('These findings are consistent with the methodological distinction in [1-3]: a fixed-PSD, real-gain estimator and a learned multi-frame complex filter encode different information. They do not reproduce the published benchmark numbers, because the corpus selection, noises, SNR recipe, precision and scoring population differ. The strongest contribution is the evidence chain connecting persistent causal state, validated output schedules, paired signals and multiple quality measures. It avoids interpreting a fast whole-file command as a complete real-time system.')
    p('A next controlled experiment would replace only the fixed noise estimator with a causal adaptive estimator, holding windows, smoothing time and gain floor fixed, then test a speech-contaminated prefix and more source-disjoint transient noises. A separate device-loop experiment should measure capture, resampling, processing, output buffering and deadline tails together. A listening test would be needed to establish perceived benefit or word-recognition changes. These extensions follow directly from the observed failure and measurement limits; they are not claimed as completed work.')
    sub('Reproducible deliverables')
    p('The repository contains the runnable processors and preparation/scoring scripts, manifests, exact CSV results, validation evidence and instructions. launch_final_demo reruns selected methods, verifies agreement with evaluated outputs and plays clean/noisy/processed recordings at one common gain. The accompanying short video shows actual app results and those audio excerpts. Repository: https://github.com/Simon1ma/elec5305-project-550762913 .','SmallR')
    sub('References')
    references=[
        ('[1] Y. Ephraim and D. Malah, "Speech Enhancement Using a Minimum Mean-Square Error Short-Time Spectral Amplitude Estimator," IEEE Trans. ASSP, 32(6), 1109-1121, 1984.','https://malah.net.technion.ac.il/files/2017/08/Ephraim_Speech_Enhancement_ASSP84.pdf'),
        ('[2] H. Schroter et al., "DeepFilterNet: Perceptually Motivated Real-Time Speech Enhancement," arXiv:2305.08227, 2023.','https://arxiv.org/abs/2305.08227'),
        ('[3] Rikorose/DeepFilterNet, official v0.5.6 runtime and DeepFilterNet3 model; source commit 978576aa8400552a4ce9730838c635aa30db5e61.','https://github.com/Rikorose/DeepFilterNet/tree/978576aa8400552a4ce9730838c635aa30db5e61'),
        ('[4] C. H. Taal et al., "An Algorithm for Intelligibility Prediction of Time-Frequency Weighted Noisy Speech," IEEE Trans. ASLP, 19(7), 2125-2136, 2011.','https://doi.org/10.1109/TASL.2011.2114881'),
        ('[5] M. Pariente et al., pystoi, standard STOI implementation, version 0.4.1 used.','https://github.com/mpariente/pystoi'),
        ('[6] J. Le Roux, S. Wisdom, H. Erdogan and J. R. Hershey, "SDR - half-baked or well done?" ICASSP 2019; arXiv:1811.02508.','https://arxiv.org/abs/1811.02508'),
        ('[7] V. Panayotov, G. Chen, D. Povey and S. Khudanpur, "LibriSpeech: an ASR corpus based on public domain audio books," ICASSP 2015. Test-clean, OpenSLR SLR12, CC BY 4.0.','https://www.openslr.org/12/'),
        ('[8] C. Valentini-Botinhao, "Noisy speech database for training speech enhancement algorithms and TTS models," University of Edinburgh, 2017; clean training recordings, CC BY 4.0.','https://doi.org/10.7488/ds/2117'),
        ('[9] K. J. Piczak, "ESC: Dataset for Environmental Sound Classification," ACM Multimedia 2015. ESC-50 commit 33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6; CC BY-NC with individual clip attributions.','https://github.com/karolpiczak/ESC-50')]
    for text,url in references:
        story.append(Paragraph(escape(text)+f' <link href="{escape(url)}" color="#176b87">[source]</link>',styles['SmallR']));md.append(text+' '+url+'\n')
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#c9d7dd'));canvas.line(54,38,541,38);canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#52656d'));canvas.drawString(54,26,'ELEC5305 | Yixiang Ma | Final research project');canvas.drawRightString(541,26,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(str(output/'Final_Project_Yixiang_Ma.pdf'),pagesize=(595.28,841.89),leftMargin=54,rightMargin=54,topMargin=43,bottomMargin=49,title='Latency-Quality Trade-offs in Real-Time Causal Speech Enhancement',author='Yixiang Ma')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    (output/'Final_Project_Yixiang_Ma.md').write_text('\n'.join(md),encoding='utf-8')
    print('Created',output/'Final_Project_Yixiang_Ma.pdf')

if __name__=='__main__':main()
