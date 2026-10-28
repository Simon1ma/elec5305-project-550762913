# Final Project: Second Progress Stage - Working Description

Yixiang Ma | SID 550762913

Project site: https://simon1ma.github.io/elec5305-project-550762913/

Following feedback, the project now investigates latency-quality trade-offs in causal speech enhancement. Wiener filtering is treated as a classical baseline rather than a novel contribution.

The first revised milestone implements a stateful sequential-block MATLAB processor with left-aligned Hann analysis, decision-directed Wiener gains, and overlap-add reconstruction. One recorded 48 kHz VoiceBank utterance is mixed with DEMAND washing-machine noise at 0 dB input SNR. The same mixture is evaluated with 10, 20, 40, and 80 ms windows. Reconstruction, arbitrary-chunk consistency, future-input invariance, impulse transport shift, and output scheduling checks passed.

Output SNRs are 3.12, 2.83, 1.92, and 1.28 dB; corresponding STOI values are 0.9273, 0.9295, 0.9307, and 0.9330. The unprocessed STOI is 0.9310, illustrating why SNR improvement alone is insufficient. SI-SDR and repeated-run RTF are also reported. Quality scoring removes only the known transport shift, without lag optimisation or output peak normalisation.

Delay conventions, the separate 300 ms calibration requirement, timing exclusions, source provenance, code, and limitations are documented. These results concern one development example. Actual keyboard/transient experiments, broader speaker-disjoint evaluation, and a pretrained DeepFilterNet comparison remain incomplete. This working description should be updated as those milestones are completed and checked against the current Canvas instructions before submission.
