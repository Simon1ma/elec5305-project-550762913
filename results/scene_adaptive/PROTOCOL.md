# Exploratory online-estimation comparison, 13 November 2026

Specified before running this new variant, after inspection of the existing bridge results. This is post-test exploration, not a new held-out evaluation. No parameter search or model refitting.

Use the same 27 personal mixtures, 40 ms window / 20 ms hop, 300 ms calibration, 100 ms decision-directed smoothing, 0.05 gain floor and known 20 ms transport shift. Only the noise PSD rule changes: after computing each enhanced frame, update D = beta D + (1-beta) P, beta=exp(-H/(fs*0.5)). The next frame uses this estimate. This deliberately simple unconditional EMA can absorb speech; it is a diagnostic comparator, not an implementation of a published speech-presence estimator. No clean signal, source labels or future samples enter processing. Report every case, SNR, SI-SDR and STOI, plus paired differences against fixed Wiener40 and decrease counts. Reuse the existing reference scores. Mixtures share three readings and three bottle sources, so do not treat 27 cases as independent speakers. No new runtime claim.

Validation: fixed output rerun must match saved baseline; bypass reconstruction, variable chunk equivalence and future-input invariance checked on first case. Models and original processor remain unchanged.
