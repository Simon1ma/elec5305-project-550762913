ELEC5305 AUDIO PROCESSING REPORT 2
Yixiang Ma | 550762913

Topic: Temporal Modulation Filtering and Wavelet Analysis of Recorded Speech

Open "Report2 YixiangMa.mlx" in MATLAB and select Run All. The PDF is exported
from that executed Live Script, not assembled independently. All required input
audio and custom helpers are included. No network, Python, Rust, pretrained
model, microphone, or external project repository is needed to run the report.

Requirements: MATLAB R2026a Update 5 (tested), Signal Processing Toolbox,
and Wavelet Toolbox. resample and hann require Signal Processing Toolbox;
cwt requires Wavelet Toolbox. The Live Script checks these functions at startup.
The companion run_report2.m contains the same executable sections without
rich-text formatting, for non-Live-Editor checks.
Run check_report2() for additional reconstruction and odd/even-grid tests.

Run from this folder. Generated figures, full-precision metrics, analysis MAT,
and common-gain listening WAV files are written to generated/. The entire
generated/ directory can be regenerated. Listen using the same playback volume;
do not independently normalise clips when comparing them.

Input attribution and SHA256 are documented in AUDIO_SOURCE.txt. The input
is an existing public recording, not a recording made by the student. Source
speech is also used in separate project development; this report performs a
different modulation-filtering/CWT experiment and does not reuse old FIR or
Wiener results as new evidence.

Scope: an offline educational analysis of one utterance. Reference-to-error SNR
measures distortion against clean speech, not noise-reduction gain. There is
no human intelligibility test, neural training, or real-time claim.
