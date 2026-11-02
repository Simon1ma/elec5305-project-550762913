# Pretraining overlap audit and external-cohort amendment

Checked 2 November 2026 against the author manuscript and pinned implementation.

## Specific evidence

Schroter et al., *DeepFilterNet: Perceptually Motivated Real-Time Speech Enhancement* (2023), section 4, state that the model is trained on the multilingual DNS4 data while oversampling high-quality PTDB and VCTK data. Source: https://arxiv.org/html/2305.08227v1 .

The initial final-project expansion selected twelve utterances from six speakers in the VoiceBank clean training archive. These are project-development-disjoint speakers, but their VCTK provenance creates a concrete risk of upstream pretraining overlap. They must not be described as unseen speakers for DeepFilterNet3 or used to claim leakage-free model generalisation.

## Amendment

Retain every VoiceBank result as a secondary in-domain engineering comparison. Add a separate external cohort from the official LibriSpeech **test-clean** partition, with six deterministically selected speakers and two utterances each. Freeze the source-selection rule and all processing settings before running that cohort. Do not tune any parameter in response to either cohort's quality scores.

This amendment follows literature inspection, not a search for favourable model outcomes. The VoiceBank run preceded the amendment; it is not presented as a prospectively verified unseen-model benchmark.

External selection: first six lexicographically sorted speaker IDs in the official test-clean archive; first two sorted FLAC files per speaker lasting at least 4.5 s. Use the first 4.5 s. Resample 16 kHz speech to the processors' 48 kHz input rate once using a 3:1 polyphase conversion. Use exactly the same four evaluation noise sources, SNRs, prefix/tail, shared-input precision, and frozen model settings as the VoiceBank cohort.

## Remaining limits

- The selected files come from an official test partition, but complete per-file training manifests for the supplied model are not available in the checked resources. No absolute guarantee against upstream exposure is claimed for LibriSpeech either.
- LibriSpeech is 16 kHz audiobook speech. Upsampling does not create speech content above 8 kHz. It is an external band-limited-speech test of 48 kHz processors, not native full-band speech evidence.
- Resampling occurs before shared mixture creation. Its processing cost and filter delay are outside the reported enhancement-ready delays. A deployed resampler/device chain would require separate latency measurement.
- The four noise files remain a small fixed set and may also have appeared in broad upstream noise corpora. Speaker bootstrap intervals condition on these files.
- No training or fine-tuning occurs in this project.
