Latency-Quality Trade-offs in Real-Time Causal Speech Enhancement

ELEC5305 Final Project | Yixiang Ma | SID 550762913 | 2 November 2026

### Abstract

This project studies how a causal STFT Wiener enhancer trades waiting time for speech quality, and compares it with an official pretrained DeepFilterNet3 reference. Four Wiener windows, 10/20/40/80 ms, share a 100 ms decision-directed smoothing time constant. A separate LibriSpeech test-clean cohort supplies 144 paired mixtures: twelve utterances from six speakers, four noise recordings and three input SNRs. A second, native-48-kHz VCTK-derived cohort provides a secondary engineering comparison. On the external cohort at 0 dB keyboard SNR, Wiener40 raises waveform SNR to 2.13 dB but lowers STOI from 0.7336 to 0.6953. At the same 40 ms oldest-sample block-ready delay, DeepFilterNet3 obtains 13.55 dB and 0.8998. Longer Wiener windows improve mean STOI here, while waveform SNR peaks earlier. All 25,718 profiled external Wiener calls remain within their hop budgets on the tested CPU. The measured outcomes describe causal processing of recorded files on the tested computer.

## 1. Introduction and research question

Low-delay speech enhancement must decide what to suppress before much future context is available. A longer analysis window can make spectral structure easier to distinguish, while postponing output and combining speech events over a longer interval. A fast average implementation can still miss individual deadlines. These issues motivate measuring enhancement quality, sample availability and compute time as separate quantities.

Research question: How does causal STFT scheduling delay affect Wiener enhancement quality, and how does this classical baseline compare with a pretrained enhancer at a reconciled delay budget? The study concerns single-channel additive recorded noise. The evaluation uses objective metrics and the official pretrained reference.

### 1.1 Contribution and project continuity

The semester project progressed from an offline synthetic FIR/Wiener demonstration to a stateful causal processor, then to recorded keyboard noise and a pretrained reference. The final stage preserves those processors and expands the evaluation across speakers, noise sources and SNRs. Its contribution is the controlled window ablation, delay reconciliation, paired objective evaluation and failure analysis. Wiener filtering and DeepFilterNet provide established methods for the controlled comparison.

The earlier single-utterance examples form the development stage. Code, protocol, source identifiers, checks, full result tables and an audition app accompany this report.


---

## 2. Literature review and research rationale

### 2.1 Statistical spectral enhancement

Ephraim and Malah [1] distinguish Wiener spectral estimation from MMSE short-time spectral-amplitude estimation and introduce a decision-directed estimate of a priori SNR. This connects current observations with the preceding enhanced spectrum. Their statistical formulation motivates the noise PSD and spectral-gain estimates used here. The present baseline applies a decision-directed Wiener gain while retaining noisy phase.

For this investigation, a fixed noise estimate makes the assumptions inspectable. A noise-only startup interval supplies its PSD, and subsequent frames use the same estimate. This holds noise estimation fixed across window settings. Transient noise arriving after calibration tests the resulting estimator under a change in noise statistics.

### 2.2 Learned multi-frame enhancement

Schroter et al. [2] combine coarse ERB-band envelope gains with complex multi-frame filtering of lower-frequency speech. This differs from the baseline's real, binwise attenuation with noisy phase: a learned temporal representation can use speech structure beyond an initial noise PSD. It motivates a modern comparator, while also introducing dependence on pretrained data and inference implementation.

The paper describes a 48 kHz system with 20 ms windows, 10 ms hops and two frames of lookahead. The pinned runtime/configuration [3] is inspected separately before assigning its delay. The same paper reports DNS4 training with VCTK oversampling, which makes the VCTK-derived cohort a secondary engineering comparison. The primary analysis uses a separate LibriSpeech corpus; upstream file-level overlap remains unverified.

### 2.3 Complementary metrics and the gap addressed here

Taal et al. [4] provide an objective intelligibility predictor for time-frequency weighted speech. The standard pystoi implementation [5] correlates short-time one-third-octave envelopes after its prescribed preprocessing. It captures changes in speech-envelope structure alongside waveform-error metrics.

Le Roux et al. [6] show why separation metrics need explicit definitions and propose SI-SDR. This study reports zero-mean projection SI-SDR beside ordinary reference-to-error SNR: one tolerates an overall reference scale, while the other penalises it. The evaluation preserves output amplitude for both measures. STOI and fixed-gain audition complete the comparison across complementary quality objectives.

| Literature / resource | Design consequence | Interpretation |
| --- | --- | --- |
| Statistical estimation [1] | Frozen decision-directed baseline | Wiener gain with noisy phase |
| Learned multi-frame method [2,3] | Pinned modern reference; reconcile lookahead | Pinned weights and runtime |
| STOI and SI-SDR [4-6] | Complementary paired metrics | Objective predictor and waveform measures |

Table 1. The methodological gap is an auditable latency-quality comparison, using reproducible signal and delay measurements.


---

## 3. Methods: stateful causal enhancement

Figure 1. Clean speech is used only for mixture construction and evaluation. Enhancement receives arrived mixture samples; the clean reference enters scoring after processing.

### 3.1 Causal framing and reconstruction

CausalWiener.step(arrived) maintains pending input, past samples, overlap-add accumulators, calibration spectra and previous enhanced power across calls. With window length L and hop H=L/2, a frame contains the previous H samples and the newly arrived H samples. Periodic Hann analysis is followed by FFT, gain multiplication, inverse FFT and overlap-add divided by the sum of analysis-window weights. Reconstruction uses the analysis window with overlap-weight normalisation. Past-only startup padding and a labelled EOF zero flush handle boundaries.

| Window / L (ms) | L (samples) | H (samples) | FFT length | Calibration frames |
| --- | --- | --- | --- | --- |
| 10 | 480 | 240 | 512 | 59 |
| 20 | 960 | 480 | 1024 | 29 |
| 40 | 1920 | 960 | 2048 | 14 |
| 80 | 3840 | 1920 | 4096 | 6 |

Table 2. All methods run at 48 kHz. Calibration counts include complete frames within the same 300 ms prefix; this count necessarily varies with L.

### 3.2 Frozen Wiener rule

After averaging the complete, already-arrived noise-only calibration frames, the noise PSD D[k] remains fixed. Let P[t,k]=|Y[t,k]|^2, Q[t-1,k] be the preceding enhanced power, and gamma=P/D. The decision-directed update and real gain are:

```text
alpha = exp(-H / (fs * 0.100))
xi = alpha * Q_previous / D + (1-alpha) * max(gamma-1, 0)
G = max(0.05, xi / (1+xi));  Q = G^2 * P
```

A PSD floor protects division. The common 100 ms time constant sets the same physical smoothing time across the four hop settings. The window/hop ablation jointly changes observation support, frequency resolution, calibration averaging and output cadence. FFT zero-padding increases the spectral sampling density.

### 3.3 Pretrained reference

The official v0.5.6 Windows Rust/Tract executable runs the pinned DeepFilterNet3 ONNX archive [3]. Binary/model SHA256 checks precede execution. Default inference thresholds are retained; the project uses published pretrained weights. Both processors consume exactly the same float32 mixture. Wiener retains double output; the reference CLI writes PCM16. The quality and timing results therefore describe these specific implementations.


---

## 4. Experimental design and data provenance

### 4.1 Separate development, external and engineering cohorts

Development remains the earlier p232_003 VoiceBank utterance, DEMAND washing-machine recording and ESC-50 keyboard source 137. Final settings were fixed on development data. The primary external cohort uses LibriSpeech test-clean [7]: the first six lexicographically sorted speaker IDs and the first two sorted recordings per speaker lasting at least 4.5 s. The first 4.5 s are retained and resampled once from 16 to 48 kHz by a 3:1 polyphase conversion. The 16 kHz source limits speech bandwidth to 8 kHz; preparation resampling precedes enhancement timing.

The original final expansion used twelve native-48-kHz utterances from the first six sorted speakers in the official VoiceBank clean training archive [8]. The VCTK training reference in [2] places this cohort in the secondary engineering analysis. The LibriSpeech selection rule and processor settings were fixed before external inference. Upstream file-level overlap remains unverified. Results are reported by corpus.

| Cohort | Speakers | Speech recordings | Role |
| --- | --- | --- | --- |
| External: LibriSpeech test-clean | 1089, 1188, 121, 1221, 1284, 1320 | 2 per speaker; 12 total | Primary; 16 kHz source |
| Engineering: VoiceBank / VCTK | p226, p227, p228, p230, p231, p233 | 2 per speaker; 12 total | Secondary engineering comparison |

Table 3. Selection follows the stated deterministic source order. Manifests retain every recording ID, source URL and hash.

### 4.2 Noise selection and controlled mixtures

Each cohort uses two ESC-50 washing-machine sources (21896, 23996) and two keyboard sources (53501, 61212), selected by sorted filename with distinct original source IDs, excluding development source 137 [9]. The selected recording sources differ from the project development sources. The first 4.9 s of each 5 s clip is resampled once from 44.1 to 48 kHz. Each mixture uses a continuous segment of its source recording.

```text
mixture = clean + beta * noise
beta = sqrt(sum(clean^2) / (10^(inputSNR/10) * sum(noise^2)))
```

Scaling uses only the scored speech interval. Each input has 300 ms of preceding real noise and 100 ms of real-noise tail. One common attenuation per cohort provides 0.8 peak headroom before float32 storage (external 0.22420135; engineering 0.28328995). Clean references receive the same attenuation; scoring uses original output amplitudes. Each cohort contains 12 utterances x 4 recordings x 3 SNRs (0/5/10 dB) = 144 paired mixtures, each scored under six conditions, yielding 864 rows.

### 4.3 Metrics and uncertainty

SNR is 10 log10(sum(clean^2)/sum((output-clean)^2)). SI-SDR removes means and projects output onto clean before taking target-to-residual energy ratio. Standard pystoi 0.4.1 uses extended=False. Alignment removes the shifts established by the processor schedules. Prefix/tail are excluded from the 4.5 s score. Within each noise/SNR group, utterance/source outcomes are averaged per speaker; 2,000 seed-5305 bootstrap resamples of six speakers provide exploratory 95% percentile intervals. Paired differences are formed within each speaker before resampling. The intervals describe variation across six speakers conditional on the four selected noise files.


---

## 5. Delay contract and validation

### 5.1 Reconcile waveform shift with output availability

A transport shift is the displacement in equal-length input/output block arrays. Output readiness is defined separately from this array displacement. For Wiener, a logical output block starting at sample s is emitted after samples through s+L have arrived. The oldest-sample block-ready delay is therefore L/fs; the newest-sample age is (L-H+1)/fs. Starting playback at each ready timestamp gives a conservative L/fs sample delay, before computation or devices.

| System | Transport shift (ms) | Oldest-sample ready (ms) | Evidence |
| --- | --- | --- | --- |
| Wiener 10/20/40/80 | 5 / 10 / 20 / 40 | 10 / 20 / 40 / 80 | Impulse and per-block schedule |
| DeepFilterNet3 | 30 | 40 | Source/configuration + transport probe |

Table 4. The reference has L=20 ms, H=10 ms and two lookahead frames. The two lookahead paths contribute their implemented combined delay.

The reference transport is L-H+2H=30 ms (1440 samples), while oldest-sample readiness is L+2H=40 ms. Wiener40 and DeepFilterNet3 form the matched 40 ms ready-delay comparison. Source inspection identifies its persistent inference state and hop loop [3]; an independent near-identity probe confirms transport. Wiener's 300 ms noise-only calibration precedes steady-state processing. The reference receives the same prefix and applies its own pretrained inference rule.

### 5.2 Validation before interpretation

| Check | Measured result | Scope |
| --- | --- | --- |
| Unit-gain reconstruction | Maximum external relative error 2.984e-16 | All 144 mixtures x 4 windows |
| Chunk and future invariance | Maximum differences 0 | All four Wiener settings on development checks |
| Reference delay / trimming | 1440 samples; exact CLI trim agreement | Separate development probes |
| Reference future / repeats | Future-prefix error 0; repeats bit-identical | Development probe + representative repeats |
| Shared input / input SNR | WAV=MAT exactly; max SNR error 1.38e-8 dB | All external mixtures |
| PCM16 full-scale flags | 0 / 144 external outputs | PCM16 sample threshold check |

Table 5. Historical causality probes are rerun on this PC and are labelled development checks. Final per-mixture reconstruction/input checks supplement them.

The original development quality table reproduces to maximum absolute difference 3.82e-14. This confirms continuity of the existing processor and scoring code. Diagnostic gain capture also leaves its selected final outputs unchanged to below 1e-12. EOF flushing begins after the final recorded sample arrives.

### 5.3 Compute measurement

Timing is performed separately from quality, in sequential benchmark jobs: one omitted warm-up and seven repeats on the first utterance and first noise source of each class at 0 dB. Wiener RTF includes its sequential driver and EOF flush, excluding construction, preallocation, I/O and metrics. A separate full-hop step profile includes validation/timer overhead and calibration, and excludes EOF flush from recurring deadlines. Reference RTF comes from its internal frame-loop timer after setup; the official binary reports aggregate frame-loop timing. The RTF values describe each measured implementation and its stated timing scope.


---

## 6. Results: external intelligibility-predictor trade-off

Figure 2. External speaker-mean STOI versus oldest-sample block-ready delay. Bars are 95% speaker-bootstrap intervals, conditional on the four fixed noises. Dashed lines are noisy-input means; the neural point is at 40 ms.

![Figure 2. External speaker-mean STOI versus oldest-sample block-ready delay. Bars are 95% speaker-bootstrap intervals, conditional on the four fixed noises. Dashed lines are noisy-input means; the neural point is at 40 ms.](../../results/final_external/figures/quality_latency.png)

| 0 dB input noise | Method | SNR (dB) | SI-SDR (dB) | STOI |
| --- | --- | --- | --- | --- |
| washing machine | Noisy | 0.00 | 0.00 | 0.7228 |
| washing machine | Wiener40 | 8.71 | 7.99 | 0.7384 |
| washing machine | DFNet3 | 10.46 | 10.32 | 0.8345 |
| keyboard typing | Noisy | 0.00 | 0.00 | 0.7336 |
| keyboard typing | Wiener40 | 2.13 | 1.45 | 0.6953 |
| keyboard typing | DFNet3 | 13.55 | 13.52 | 0.8998 |

Table 6. Matched 40 ms ready-delay systems at 0 dB. Each row averages 24 mixtures from six speakers; full window/SNR tables are supplied as CSV.

At 0 dB washing noise, Wiener STOI rises from 0.6981 at 10 ms to 0.7463 at 80 ms, while the noisy mean is 0.7228. With keyboard noise it rises from 0.6602 to 0.7065, remaining below noisy speech (0.7336). At 0 dB, Wiener10/20/40 reduce STOI in all 24 keyboard cases; Wiener80 does so in 23. The reference reduces it in none of those 24 cases. These counts describe outcomes for the 24 paired mixtures in that condition.

Longer waiting therefore helps this baseline's envelope-correlation score within the tested range, while keyboard-noise STOI remains below the noisy input. The reference obtains 0.8998 keyboard STOI at 40 ms, versus 0.6953 for Wiener40 and 0.7065 for Wiener80. Since the latter uses twice the ready delay, the observed gap reflects differences between the complete enhancement systems at their stated ready delays.


---

## 7. Results: error metrics and paired comparisons

Figure 3. External output SNR on the same mixtures, alignment and speaker units as Figure 2. STOI and waveform SNR select different windows and methods in several conditions.

![Figure 3. External output SNR on the same mixtures, alignment and speaker units as Figure 2. STOI and waveform SNR select different windows and methods in several conditions.](../../results/final_external/figures/snr_latency.png)

| Noise | Input SNR | DFNet3 - Wiener40 STOI [95% CI] |
| --- | --- | --- |
| washing machine | 0 | +0.0962 [+0.0720, +0.1156] |
| washing machine | 5 | +0.0512 [+0.0372, +0.0667] |
| washing machine | 10 | +0.0201 [+0.0099, +0.0313] |
| keyboard typing | 0 | +0.2045 [+0.1764, +0.2283] |
| keyboard typing | 5 | +0.1479 [+0.1173, +0.1790] |
| keyboard typing | 10 | +0.0937 [+0.0670, +0.1232] |

Table 7. Paired speaker-mean differences at the common 40 ms ready delay. Intervals resample the six speakers conditional on the selected noise recordings.

At 0 dB washing noise, output SNR increases from 7.07 dB (Wiener10) to 8.71 dB (Wiener40), then falls to 8.26 dB (Wiener80), although STOI increases. The paired 80-minus-40 ms changes are -0.447 dB SNR [ -0.595, -0.303 ] and +0.00795 STOI [ +0.00410, +0.01161 ]. This quantifies the opposing changes in waveform SNR and STOI as the window length increases.

At 10 dB washing input, Wiener40 reaches 16.60 dB SNR versus 14.25 dB for the reference. The reference-minus-Wiener difference is -2.355 dB [ -4.729, -0.628 ], yet its STOI difference remains +0.02008. SI-SDR also favours Wiener40 here (16.50 versus 14.50 dB), reinforcing the waveform-error result. At 5 dB washing input, the SNR-difference interval includes zero. By contrast, at 0 dB keyboard input the reference SNR is 13.55 dB versus 2.13 dB for Wiener40. Across the selected keyboard recordings the reference has higher mean SNR and STOI, while the washing condition shows a metric-dependent ordering.


---

## 8. Keyboard event and secondary cohort

Figure 4. First external keyboard case, 0 dB. The event centre (1.520 s) maximises 20 ms true-noise energy on a 10 ms grid, excluding 300 ms speech boundaries. Selection uses true noise energy before outcome inspection. Waveforms and display STFTs share scales; native gain maps retain their own grids.

![Figure 4. First external keyboard case, 0 dB. The event centre (1.520 s) maximises 20 ms true-noise energy on a 10 ms grid, excluding 300 ms speech boundaries. Selection uses true noise energy before outcome inspection. Waveforms and display STFTs share scales; native gain maps retain their own grids.](../../results/final_external/figures/keyboard_event.png)

| Illustrative 400 ms event | Noisy | Wiener10 | Wiener80 | DFNet3 |
| --- | --- | --- | --- | --- |
| Reference-to-error SNR (dB) | -6.66 | -4.99 | -4.81 | 11.31 |

The shared display STFT uses a 20 ms Hann window, 5 ms hop and FFT1024; all outputs share a display grid while gains retain native frame resolutions. Native Wiener gains show the attenuation applied during processing. A fixed prefix PSD and long decision-directed memory can poorly represent later keyboard bursts, while attenuation can also weaken useful speech. The event motivates the proposed controlled test of an adaptive noise estimator.

### 8.1 Secondary native-48-kHz engineering comparison

On the VCTK-derived cohort at 0 dB, washing STOI is 0.7169 noisy, 0.7254 Wiener40 and 0.8362 reference; keyboard values are 0.7004, 0.6582 and 0.8805. This secondary engineering cohort repeats the keyboard metric conflict: waveform SNR improves while STOI can worsen. The published VCTK training connection shapes its interpretation; the corpora are analysed separately because speech bandwidth and levels also differ.


---

## 9. Runtime and experimental scope

Figure 5. External Wiener empirical distributions of step time divided by hop budget. Values below one fit the recurring input interval in these measured calls. Step timings include instrumentation overhead.

![Figure 5. External Wiener empirical distributions of step time divided by hop budget. Values below one fit the recurring input interval in these measured calls. Step timings include instrumentation overhead.](../../results/final_external/figures/block_timing.png)

| Noise | Window (ms) | RTF median | Step p99 (ms) | Step max (ms) | Hop (ms) |
| --- | --- | --- | --- | --- | --- |
| washing machine | 10 | 0.0080 | 0.131 | 1.734 | 5 |
| washing machine | 20 | 0.0057 | 0.167 | 1.889 | 10 |
| washing machine | 40 | 0.0035 | 0.183 | 0.301 | 20 |
| washing machine | 80 | 0.0034 | 0.368 | 1.777 | 40 |
| keyboard typing | 10 | 0.0075 | 0.117 | 1.728 | 5 |
| keyboard typing | 20 | 0.0053 | 0.184 | 1.808 | 10 |
| keyboard typing | 40 | 0.0041 | 0.225 | 0.694 | 20 |
| keyboard typing | 80 | 0.0030 | 0.364 | 1.501 | 40 |

Table 8. Seven repetitions per representative noise/window condition. Windows with longer hops can reduce per-second call overhead even when a single step takes longer.

All 25,718 profiled external full-hop calls are within budget. Reference median RTF is 0.0666 for washing and 0.0628 for keyboard. Tests run on an Intel Core i7-14700HX (20 cores, 28 logical processors), approximately 31.8 GiB RAM, Windows 11 build 26200, MATLAB R2026a Update 5 and Python 3.12.14. Scoring uses numpy 2.4.6, scipy 1.17.1 and pystoi 0.4.1. These values characterise the tested implementations on this computer and input duration.

### 9.1 Experimental scope

Each cohort samples six speakers and two recordings per noise class. The speaker bootstrap is conditional on these recordings. The synthetic mixing protocol supplies a clean reference for scoring, and the Wiener processor starts with 300 ms of noise-only calibration. Room acoustics, microphone capture and speech-contaminated calibration motivate the next evaluation stage.

The reference is quantised to PCM16 while Wiener retains double precision, and the compute backends differ. There are 945 external 10 ms input blocks below the reference's 1e-7 silence-power threshold (542 in the secondary cohort). The threshold count characterises low-energy inputs under the fixed headroom policy. The measurements include Wiener per-hop timing and reference aggregate RTF; live device timing and listener responses form separate experiments.


---

## 10. Discussion and conclusion

The results identify a quality-delay trade-off across the tested conditions. For the frozen Wiener design, spending more ready delay generally improves mean STOI across 10-80 ms, while its waveform-error optimum can occur earlier and keyboard-noise STOI remains below the noisy input. At a common 40 ms ready delay the pretrained reference has higher mean STOI in every tested external noise/SNR condition, with positive paired intervals. On the cleaner washing mixtures, the classical method can retain higher waveform SNR and SI-SDR. System choice therefore depends on the latency constraint and the quality objective.

These findings are consistent with the methodological distinction in [1-3]: a fixed-PSD, real-gain estimator and a learned multi-frame complex filter encode different information. The corpus selection, noise sources, mixture recipe and scoring population define this project's comparison. The contribution is an evidence chain connecting persistent causal state, validated output schedules, paired signals and multiple quality measures.

A next controlled experiment would replace only the fixed noise estimator with a causal adaptive estimator, holding windows, smoothing time and gain floor fixed, then test a speech-contaminated prefix and more source-disjoint transient noises. A separate device-loop experiment should measure capture, resampling, processing, output buffering and deadline tails together. A listening test would be needed to establish perceived benefit or word-recognition changes. These extensions address the measured transient-noise behaviour and extend the timing evidence to a device loop.

### Reproducible deliverables

The repository contains the runnable processors and preparation/scoring scripts, manifests, exact CSV results, validation evidence and instructions. launch_final_demo reruns selected methods, verifies agreement with evaluated outputs and plays clean/noisy/processed recordings at one common gain. The accompanying short video shows actual app results and those audio excerpts. Repository: https://github.com/Simon1ma/elec5305-project-550762913 .

### References

[1] Y. Ephraim and D. Malah, "Speech Enhancement Using a Minimum Mean-Square Error Short-Time Spectral Amplitude Estimator," IEEE Trans. ASSP, 32(6), 1109-1121, 1984. https://malah.net.technion.ac.il/files/2017/08/Ephraim_Speech_Enhancement_ASSP84.pdf

[2] H. Schroter et al., "DeepFilterNet: Perceptually Motivated Real-Time Speech Enhancement," arXiv:2305.08227, 2023. https://arxiv.org/abs/2305.08227

[3] Rikorose/DeepFilterNet, official v0.5.6 runtime and DeepFilterNet3 model; source commit 978576aa8400552a4ce9730838c635aa30db5e61. https://github.com/Rikorose/DeepFilterNet/tree/978576aa8400552a4ce9730838c635aa30db5e61

[4] C. H. Taal et al., "An Algorithm for Intelligibility Prediction of Time-Frequency Weighted Noisy Speech," IEEE Trans. ASLP, 19(7), 2125-2136, 2011. https://doi.org/10.1109/TASL.2011.2114881

[5] M. Pariente et al., pystoi, standard STOI implementation, version 0.4.1 used. https://github.com/mpariente/pystoi

[6] J. Le Roux, S. Wisdom, H. Erdogan and J. R. Hershey, "SDR - half-baked or well done?" ICASSP 2019; arXiv:1811.02508. https://arxiv.org/abs/1811.02508

[7] V. Panayotov, G. Chen, D. Povey and S. Khudanpur, "LibriSpeech: an ASR corpus based on public domain audio books," ICASSP 2015. Test-clean, OpenSLR SLR12, CC BY 4.0. https://www.openslr.org/12/

[8] C. Valentini-Botinhao, "Noisy speech database for training speech enhancement algorithms and TTS models," University of Edinburgh, 2017; clean training recordings, CC BY 4.0. https://doi.org/10.7488/ds/2117

[9] K. J. Piczak, "ESC: Dataset for Environmental Sound Classification," ACM Multimedia 2015. ESC-50 commit 33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6; CC BY-NC with individual clip attributions. https://github.com/karolpiczak/ESC-50
