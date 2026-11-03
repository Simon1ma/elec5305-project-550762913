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
    p('How much speech quality does a causal enhancer gain by waiting for more audio? We test four STFT Wiener windows (10/20/40/80 ms) with a shared 100 ms decision-directed smoothing time constant and compare them with the official pretrained DeepFilterNet3 reference. The primary LibriSpeech test-clean evaluation contains 144 paired mixtures from twelve utterances, six speakers, four noise recordings and three input SNRs. A native-48-kHz VCTK-derived cohort provides a secondary engineering comparison. On LibriSpeech at 0 dB keyboard SNR, Wiener40 raises waveform SNR to 2.13 dB but lowers STOI from 0.7336 to 0.6953. At the same 40 ms oldest-sample block-ready delay, DeepFilterNet3 reaches 13.55 dB SNR and 0.8998 STOI. Longer Wiener windows improve mean STOI in this condition, although waveform SNR peaks earlier. All 25,718 profiled external Wiener calls fit within their hop budgets on the tested CPU.')
    h('1. Introduction and research question')
    p('A causal speech enhancer must choose what to suppress using only the audio that has arrived. A longer analysis window may reveal spectral structure more clearly, but it also makes the processor wait longer and groups events across a wider interval. Average processing time can hide a slow individual block. We therefore measure quality, output readiness and computation separately.')
    p('Research question: How does causal STFT scheduling delay affect Wiener enhancement quality, and how does this classical baseline compare with a pretrained enhancer at a reconciled delay budget? We examine single-channel speech mixed with recorded noise, using objective metrics and the official pretrained reference.')
    sub('1.1 Contribution and project continuity')
    p('The semester project began with an offline demonstration using synthetic signals, FIR filtering and Wiener filtering. We then built a stateful causal processor, added recorded keyboard noise to the tests and introduced a pretrained comparator. The final study retains these processors and extends the evaluation to more speakers, noise recordings and input SNRs. We vary the Wiener window, put both output schedules on the same delay basis, compare paired quality scores and examine one keyboard event.')
    p('The earlier single-utterance examples form the development stage. Code, protocol, source identifiers, checks, full result tables and an audition app accompany this report.','SmallR')
    page()

    h('2. Literature review and research rationale')
    sub('2.1 Statistical spectral enhancement')
    p('Ephraim and Malah [1] distinguish Wiener spectral estimation from MMSE short-time spectral-amplitude estimation. Their decision-directed estimate of a priori SNR combines the current observation with preceding enhanced power. We use that idea to compute a Wiener gain from the estimated noise PSD, retaining the noisy phase.')
    p('We estimate noise PSD from a noise-only startup interval and keep it fixed while processing the following speech frames. Every window uses the same estimation rule. Keyboard bursts arriving after calibration show how this fixed estimate responds when the noise statistics change.')
    sub('2.2 Learned multi-frame enhancement')
    p('Schroter et al. [2] combine coarse ERB-band envelope gains with complex multi-frame filtering of lower-frequency speech. The Wiener baseline instead applies a real gain to each frequency bin and retains noisy phase. This comparison places a learned temporal representation beside a processor that estimates its noise model during a short startup interval.')
    p('The paper describes a 48 kHz system with 20 ms windows, 10 ms hops and two frames of lookahead. We inspect the pinned runtime and configuration [3] to determine when output becomes available. The paper also reports DNS4 training with VCTK oversampling. We therefore use LibriSpeech for the primary analysis and treat the VCTK-derived cohort as a secondary engineering comparison.')
    sub('2.3 Complementary metrics and the gap addressed here')
    p('Taal et al. [4] provide an objective intelligibility predictor for time-frequency weighted speech. The standard pystoi implementation [5] correlates short-time one-third-octave envelopes after its prescribed preprocessing. Its envelope-based score complements the waveform-error metrics used here.')
    p('Le Roux et al. [6] motivate explicit separation-metric definitions and propose SI-SDR. We report zero-mean projection SI-SDR alongside ordinary reference-to-error SNR. SI-SDR tolerates an overall scale change; SNR penalises it. Both measures use the output at its original amplitude. STOI and fixed-gain audition provide additional views of quality.')
    table(['Literature / resource','Design consequence','Interpretation'],[
        ['Statistical estimation [1]','Frozen decision-directed baseline','Wiener gain with noisy phase'],
        ['Learned multi-frame method [2,3]','Pinned modern reference; reconcile lookahead','Pinned weights and runtime'],
        ['STOI and SI-SDR [4-6]','Complementary paired metrics','Objective predictor and waveform measures']], [123,184,180])
    caption('Table 1. Prior work informs the processor, reference and complementary quality measures used in this latency-quality comparison.')
    page()

    h('3. Methods: stateful causal enhancement')
    diagram=Drawing(487,64)
    labels=['Recorded clean + noise','Shared mixture + prefix','Arrived-hop processor','Aligned scoring / audio']
    for i,label in enumerate(labels):
        x=i*125;diagram.add(Rect(x,22,112,30,fillColor=colors.HexColor('#e7f0f4'),strokeColor=colors.HexColor('#176b87')))
        diagram.add(String(x+56,34,label,fontName='Helvetica',fontSize=7.2,textAnchor='middle'))
        if i<3:diagram.add(Line(x+112,37,x+123,37,strokeColor=colors.HexColor('#176b87')))
    story.append(diagram);caption('Figure 1. Clean speech is used only for mixture construction and evaluation. Enhancement receives arrived mixture samples; the clean reference enters scoring after processing.')
    sub('3.1 Causal framing and reconstruction')
    p('CausalWiener.step(arrived) carries pending input, past samples, overlap-add accumulators, calibration spectra and previous enhanced power across calls. For window length L and hop H=L/2, each frame combines the previous H samples with the newly arrived H samples. The processor applies a periodic Hann window, FFT, gain, inverse FFT and overlap-add with analysis-window weight normalisation. Past-only startup padding and an EOF zero flush handle the boundaries.')
    table(['Window / L (ms)','L (samples)','H (samples)','FFT length','Calibration frames'],[
        ['10','480','240','512','59'],['20','960','480','1024','29'],['40','1920','960','2048','14'],['80','3840','1920','4096','6']], [103,92,92,92,108])
    caption('Table 2. All methods run at 48 kHz. The number of complete calibration frames in the shared 300 ms prefix varies with L.')
    sub('3.2 Frozen Wiener rule')
    p('The processor averages complete noise-only frames as they arrive and then fixes the noise PSD D[k]. Let P[t,k]=|Y[t,k]|^2, Q[t-1,k] be the preceding enhanced power, and gamma=P/D. The decision-directed update and real gain are:')
    eq('alpha = exp(-H / (fs * 0.100))\nxi = alpha * Q_previous / D + (1-alpha) * max(gamma-1, 0)\nG = max(0.05, xi / (1+xi));  Q = G^2 * P')
    p('A PSD floor protects division. The 100 ms time constant keeps the physical smoothing time constant across all four hop settings. Changing the window and hop also changes observation support, frequency resolution, calibration averaging and output cadence. FFT zero-padding increases spectral sampling density.')
    sub('3.3 Pretrained reference')
    p('We run the official v0.5.6 Windows Rust/Tract executable with a pinned DeepFilterNet3 ONNX archive [3], checking binary and model SHA256 hashes before execution. The reference uses published pretrained weights and default inference thresholds. Both processors receive the same float32 mixture. Wiener produces double-precision output; the reference CLI writes PCM16. These are the implementations used for the quality and timing measurements.')
    page()

    h('4. Experimental design and data provenance')
    sub('4.1 Separate development, external and engineering cohorts')
    p('We fixed the final settings using the earlier p232_003 VoiceBank utterance, DEMAND washing-machine recording and ESC-50 keyboard source 137. For the primary external cohort, we take the first six lexicographically sorted LibriSpeech test-clean speaker IDs [7] and the first two sorted recordings per speaker lasting at least 4.5 s. We retain the first 4.5 s and resample once from 16 to 48 kHz using 3:1 polyphase conversion. The 16 kHz originals contain speech bandwidth up to 8 kHz. Resampling occurs before enhancement timing begins.')
    p('The secondary cohort uses twelve native-48-kHz utterances from the first six sorted speakers in the official VoiceBank clean training archive [8]. Because [2] reports VCTK in the reference model\'s training, this cohort supports an engineering comparison. We fixed the LibriSpeech selection rule and processor settings before external inference and report the two corpora separately.')
    table(['Cohort','Speakers','Speech recordings','Role'],[
        ['External: LibriSpeech test-clean','1089, 1188, 121, 1221, 1284, 1320','2 per speaker; 12 total','Primary; 16 kHz source'],
        ['Engineering: VoiceBank / VCTK','p226, p227, p228, p230, p231, p233','2 per speaker; 12 total','Secondary engineering comparison']], [119,161,99,108])
    caption('Table 3. Selection follows the stated deterministic source order. Manifests retain every recording ID, source URL and hash.')
    sub('4.2 Noise selection and controlled mixtures')
    p('Each cohort uses two ESC-50 washing-machine sources (21896, 23996) and two keyboard sources (53501, 61212) [9]. Sorted filenames and distinct original source IDs determine the selection; development source 137 is excluded. We resample the first 4.9 s of each 5 s clip once from 44.1 to 48 kHz and use a continuous segment for each mixture.')
    eq('mixture = clean + beta * noise\nbeta = sqrt(sum(clean^2) / (10^(inputSNR/10) * sum(noise^2)))')
    p('We set the noise scale using the scored speech interval. Each input begins with 300 ms of recorded noise and ends with a 100 ms noise tail. A common attenuation per cohort leaves 0.8 peak headroom before float32 storage (external 0.22420135; engineering 0.28328995). We apply it to clean references as well and score the output at its original amplitude. Each cohort has 12 utterances x 4 recordings x 3 SNRs (0/5/10 dB) = 144 paired mixtures. Six scored conditions produce 864 rows.')
    sub('4.3 Metrics and uncertainty')
    p('SNR is 10 log10(sum(clean^2)/sum((output-clean)^2)). SI-SDR removes means and projects output onto clean before taking the target-to-residual energy ratio. We use standard pystoi 0.4.1 with extended=False. After aligning each output by its measured processor shift, we score 4.5 s of speech and omit the prefix and tail. Within each noise/SNR group, we average the utterance/source outcomes for each speaker. We then draw 2,000 seed-5305 bootstrap resamples of the six speakers for exploratory 95% percentile intervals. Paired differences are calculated per speaker before resampling. These intervals reflect the six selected speakers and four fixed noise files.')
    page()

    h('5. Delay contract and validation')
    sub('5.1 Reconcile waveform shift with output availability')
    p('We measure two different delays. Transport shift is the displacement between equal-length input and output block arrays. Output readiness is the time when a block can actually be emitted. For Wiener, a block starting at sample s is ready after samples through s+L have arrived. Its oldest sample has waited L/fs; its newest sample has waited (L-H+1)/fs. Playback starting at that ready timestamp has an L/fs sample delay, with computation and devices measured separately.')
    table(['System','Transport shift (ms)','Oldest-sample ready (ms)','Evidence'],[
        ['Wiener 10/20/40/80','5 / 10 / 20 / 40','10 / 20 / 40 / 80','Impulse and per-block schedule'],
        ['DeepFilterNet3','30','40','Source/configuration + transport probe']], [115,115,126,131])
    caption('Table 4. The reference uses L=20 ms, H=10 ms and two lookahead frames, including the delay of both implemented lookahead paths.')
    p('For the reference, transport is L-H+2H=30 ms (1440 samples), and oldest-sample readiness is L+2H=40 ms. We therefore compare Wiener40 with DeepFilterNet3 at a shared 40 ms ready delay. The source shows persistent inference state and hop-based processing [3]; a near-identity probe measures the transport shift. Wiener uses a 300 ms noise-only prefix for calibration before steady-state processing. The reference receives the same prefix and follows its pretrained inference rule.')
    sub('5.2 Validation before interpretation')
    table(['Check','Measured result','Scope'],[
        ['Unit-gain reconstruction','Maximum external relative error 2.984e-16','All 144 mixtures x 4 windows'],
        ['Chunk and future invariance','Maximum differences 0','All four Wiener settings on development checks'],
        ['Reference delay / trimming','1440 samples; exact CLI trim agreement','Separate development probes'],
        ['Reference future / repeats','Future-prefix error 0; repeats bit-identical','Development probe + representative repeats'],
        ['Shared input / input SNR','WAV=MAT exactly; max SNR error 1.38e-8 dB','All external mixtures'],
        ['PCM16 full-scale flags','0 / 144 external outputs','PCM16 sample threshold check']], [137,182,168])
    caption('Table 5. Development causality probes were rerun on this PC; reconstruction and input checks cover the final mixtures.')
    p('Rerunning the development quality table gives a maximum absolute difference of 3.82e-14, consistent with the earlier processor and scoring results. Capturing diagnostic gains changes the selected final outputs by less than 1e-12. EOF flushing starts after the last recorded sample arrives.')
    sub('5.3 Compute measurement')
    p('We time each processor in sequential benchmark jobs, separate from quality scoring. After one unreported warm-up, seven repeats use the first utterance and first noise source of each class at 0 dB. Wiener RTF covers the sequential driver and EOF flush; construction, preallocation, I/O and metrics lie outside that timer. A full-hop step profile also records calibration and validation/timer overhead, with EOF flush outside recurring deadlines. The reference reports aggregate frame-loop time from its internal timer after setup. Each RTF therefore measures the stated implementation and timed operations.')
    page()

    h('6. Results: external intelligibility-predictor trade-off')
    figure('quality_latency.png','Figure 2. External speaker-mean STOI versus oldest-sample block-ready delay. Bars are 95% speaker-bootstrap intervals, conditional on the four fixed noises. Dashed lines are noisy-input means; the neural point is at 40 ms.',maxheight=268)
    table(['0 dB input noise','Method','SNR (dB)','SI-SDR (dB)','STOI'],[
        [noise.replace('_',' '),method.replace('DeepFilterNet3','DFNet3'),val(noise,0,method,'OutputSNR_dB',2),val(noise,0,method,'SI_SDR_dB',2),val(noise,0,method)]
        for noise in ['washing_machine','keyboard_typing'] for method in ['Noisy','Wiener40','DeepFilterNet3']], [134,105,81,89,78])
    caption('Table 6. Matched 40 ms ready-delay systems at 0 dB. Each row averages 24 mixtures from six speakers; full window/SNR tables are supplied as CSV.')
    p('At 0 dB washing noise, Wiener STOI rises from 0.6981 at 10 ms to 0.7463 at 80 ms, crossing the noisy mean of 0.7228. Under keyboard noise it rises from 0.6602 to 0.7065 but stays below the noisy mean of 0.7336. At 0 dB, Wiener10/20/40 lower STOI in all 24 keyboard mixtures, and Wiener80 lowers it in 23. DeepFilterNet3 lowers it in none of the 24.')
    p('Within these windows, extra waiting helps the Wiener envelope-correlation score, but keyboard-noise STOI remains below the noisy input. At 40 ms, DeepFilterNet3 obtains 0.8998 keyboard STOI versus 0.6953 for Wiener40. Even Wiener80 reaches only 0.7065 with twice that ready delay.')
    page()

    h('7. Results: error metrics and paired comparisons')
    figure('snr_latency.png','Figure 3. External output SNR on the same mixtures, alignment and speaker units as Figure 2. STOI and waveform SNR select different windows and methods in several conditions.',maxheight=268)
    table(['Noise','Input SNR','DFNet3 - Wiener40 STOI [95% CI]'],[
        [noise.replace('_',' '),str(snr),difference(noise,snr,'DeepFilterNet3')]
        for noise in ['washing_machine','keyboard_typing'] for snr in [0,5,10]], [145,73,269])
    caption('Table 7. Paired speaker-mean differences at the common 40 ms ready delay. Intervals resample the six speakers conditional on the selected noise recordings.')
    p('At 0 dB washing noise, output SNR climbs from 7.07 dB for Wiener10 to 8.71 dB for Wiener40, then drops to 8.26 dB for Wiener80. STOI continues to rise. The paired 80-minus-40 ms changes are -0.447 dB SNR [ -0.595, -0.303 ] and +0.00795 STOI [ +0.00410, +0.01161 ]. The two metrics therefore favour different windows in this condition.')
    p('At 10 dB washing input, Wiener40 reaches 16.60 dB SNR versus 14.25 dB for DeepFilterNet3. The reference-minus-Wiener difference is -2.355 dB [ -4.729, -0.628 ], while its STOI difference is +0.02008. SI-SDR also favours Wiener40 here (16.50 versus 14.50 dB). At 5 dB washing input, the SNR-difference interval includes zero. Keyboard noise reverses the SNR ordering: at 0 dB input, DeepFilterNet3 reaches 13.55 dB versus 2.13 dB for Wiener40. Across the selected keyboard recordings, the reference has higher mean SNR and STOI.')
    page()

    h('8. Keyboard event and secondary cohort')
    figure('keyboard_event.png',f"Figure 4. First external keyboard case, 0 dB. The event centre ({event['event_centre_s']:.3f} s) maximises 20 ms true-noise energy on a 10 ms grid, excluding 300 ms speech boundaries.",maxheight=380)
    eventrows=read(EXT/'event_metrics.csv')
    table(['Illustrative 400 ms event','Noisy','Wiener10','Wiener80','DFNet3'],[
        ['Reference-to-error SNR (dB)']+[f"{float(r['EventSNR_dB']):.2f}" for r in eventrows]], [171,79,79,79,79])
    p('The display STFT uses a 20 ms Hann window, 5 ms hop and FFT1024, giving all output spectrograms one grid. Gain maps retain their native frame resolutions and show the Wiener attenuation applied during processing. A PSD fixed from the prefix and a long decision-directed memory can miss later keyboard bursts; stronger attenuation can also weaken speech. This event motivates testing an adaptive noise estimator while keeping the other processor settings fixed.')
    sub('8.1 Secondary native-48-kHz engineering comparison')
    p('On the VCTK-derived cohort at 0 dB, washing STOI is 0.7169 noisy, 0.7254 Wiener40 and 0.8362 for the reference. Keyboard values are 0.7004, 0.6582 and 0.8805. The keyboard case again shows that waveform SNR can improve while STOI worsens. We report this cohort separately because it draws on VCTK-related speech used in reference training [2] and differs from LibriSpeech in bandwidth and level.')
    page()

    h('9. Runtime and evaluation conditions')
    figure('block_timing.png','Figure 5. External Wiener empirical distributions of step time divided by hop budget. Values below one fit the recurring input interval in these measured calls. Step timings include instrumentation overhead.',maxheight=178)
    table(['Noise','Window (ms)','RTF median','Step p99 (ms)','Step max (ms)','Hop (ms)'],[
        [r['Noise'].replace('_',' '),r['Window_ms'],f"{float(next(x for x in wb if x['Noise']==r['Noise'] and x['Window_ms']==r['Window_ms'])['RTF_median']):.4f}",f"{float(r['Step_p99_ms']):.3f}",f"{float(r['Step_max_ms']):.3f}",f"{float(r['HopBudget_ms']):.0f}"] for r in timing], [121,65,75,80,80,66])
    caption('Table 8. Seven repetitions per representative noise/window condition. Windows with longer hops can reduce per-second call overhead even when a single step takes longer.')
    p(f"All {validation['profiled_step_calls']:,} profiled external full-hop Wiener calls fit their hop budgets. DeepFilterNet3 median RTF is {float(rb[0]['RTF_median']):.4f} for washing and {float(rb[1]['RTF_median']):.4f} for keyboard. The computer has an Intel Core i7-14700HX (20 cores, 28 logical processors), approximately 31.8 GiB RAM and Windows 11 build 26200. Processing uses MATLAB R2026a Update 5 and Python 3.12.14; scoring uses numpy 2.4.6, scipy 1.17.1 and pystoi 0.4.1. The timings measure these implementations on this computer and input duration.")
    sub('9.1 Evaluation conditions')
    p('Each cohort samples six speakers and two recordings per noise class. The speaker bootstrap varies speakers while holding those noise recordings fixed. Controlled mixing provides clean references for scoring, and Wiener begins with 300 ms of noise-only calibration. The next evaluation stage would include room acoustics, microphone capture and calibration contaminated by speech.')
    p('The reference writes PCM16 output and Wiener retains double precision; they also use different compute backends. The reference sees 945 external 10 ms input blocks below its 1e-7 silence-power threshold, compared with 542 in the secondary cohort. We measure Wiener per-hop time and reference aggregate RTF. Device-loop timing and listener responses form the next measurements.')
    page()

    h('10. Discussion and conclusion')
    p('Across the tested 10-80 ms Wiener windows, mean STOI generally rises as the ready delay grows. Waveform SNR can reach its peak at a shorter window, while keyboard-noise STOI remains below the noisy input. At the shared 40 ms ready delay, DeepFilterNet3 has higher mean STOI in every external noise/SNR condition; all corresponding STOI paired intervals are positive. In the 10 dB washing condition, Wiener40 retains higher SNR and SI-SDR. Choosing a processor and window therefore depends on the relative importance of envelope correlation, waveform error and output delay.')
    p("The methods in [1-3] help interpret this pattern. Wiener uses a noise PSD fixed at startup and applies a real gain; DeepFilterNet3 uses learned multi-frame complex filtering. We relate these differences to measured output schedules and paired quality scores for two recorded noise classes. Public manifests, the mixture recipe and the scoring code define the sample population behind each comparison.")
    sub('Reproducible deliverables')
    p('The repository provides runnable processors, preparation and scoring scripts, manifests, exact CSV results, validation evidence and instructions. launch_final_demo reruns selected methods, checks their agreement with evaluated outputs and plays clean, noisy and processed recordings at one common gain. The short video shows the app results and includes those audio excerpts. Repository: https://github.com/Simon1ma/elec5305-project-550762913 .','SmallR')
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
