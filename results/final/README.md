# Secondary native-48-kHz engineering cohort

This cohort uses six selected speakers and twelve utterances from the official
VoiceBank clean training archive, combined with the same four ESC-50 noise
recordings and 0/5/10 dB input SNRs as the external experiment. It contains
144 paired mixtures and 864 quality rows. The DeepFilterNet author paper states
that VCTK was oversampled in model training; because the clean archive is
VCTK-derived, these results **do not establish upstream-unseen generalisation**.
The completed cohort is preserved as an engineering comparison. The separate
[LibriSpeech test-clean results](../final_external/README.md) are the primary
external evaluation. See the dated [audit and amendment](../../docs/pretraining_overlap_audit.md).

At 0 dB input, washing-machine STOI is 0.7169 noisy, 0.7254 Wiener40, and
0.8362 DeepFilterNet3. Keyboard STOI is 0.7004 noisy, 0.6582 Wiener40, and
0.8805 reference. Those figures are speaker means, conditional on the four
fixed recordings, not a claim of unseen-model test performance.

The [manifest](input_manifest.json), [full metrics](metrics.csv),
[conditional means and intervals](summary_by_condition.csv),
[paired differences](paired_vs_wiener40.csv), [Wiener checks](wiener_checks.csv),
[reference checks](reference_checks.csv), [timing CSVs](wiener_benchmark.csv),
and [validation summary](validation_summary.json) give the exact data.
The [current-PC reproduction](development_reproduction/reproduction_check.json)
of the original development milestone matched its quality values to maximum
absolute difference 3.82e-14. Development recordings are not extra evaluation
speakers.

Full run instructions and timing/precision limits are in
[code/final/README.md](../../code/final/README.md). The analysis is stated in
the [research report](../../output/pdf/Final_Project_Yixiang_Ma.pdf).
