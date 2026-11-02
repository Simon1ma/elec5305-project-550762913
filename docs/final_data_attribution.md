# Final-project source and excerpt attribution

The public result tables and report describe derived signals. Raw third-party
archives, model weights and the executable are retrieved locally and are not
included in Git. The short demonstration uses one 4.5-second derived mixture and
its clean, noisy and enhanced versions at a shared playback gain.

## Speech

- Primary cohort: LibriSpeech **test-clean**, OpenSLR SLR12, 16 kHz, CC BY 4.0.
  V. Panayotov, G. Chen, D. Povey and S. Khudanpur, *LibriSpeech: an ASR corpus
  based on public domain audio books*, ICASSP 2015.
  https://www.openslr.org/12/
- Video excerpt: recording `1089-134686-0000.flac`, first 4.5 seconds, resampled
  16 to 48 kHz, globally attenuated and mixed. Original member and SHA256 are
  recorded in `results/final_external/input_manifest.json`.
- Secondary engineering cohort: VoiceBank clean training recordings from the
  University of Edinburgh dataset, DOI 10.7488/ds/2117, CC BY 4.0.
  Source-member IDs and SHA256 hashes are in `results/final/input_manifest.json`.

## Noise and transformations

Four selected ESC-50 source clips are attributed in its pinned official LICENSE:
https://github.com/karolpiczak/ESC-50/blob/33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6/LICENSE .
The dataset license is CC BY-NC 3.0, with original clip terms also listed there.
The preparation scripts retain original clip bytes and the full license locally.

| ESC-50 filename | Original Freesound recording | Creator | Original label in ESC-50 LICENSE |
| --- | --- | --- | --- |
| `1-21896-A-35.wav` | [file0100washingmachine.mp3](https://www.freesound.org/people/ulcered/sounds/21896/) | ulcered | CC-Sampling+ |
| `1-23996-A-35.wav` | [WashingMachine1.flac](https://www.freesound.org/people/acclivity/sounds/23996/) | acclivity | CC-BY-NC |
| `1-53501-A-32.wav` | [typing.wav](https://www.freesound.org/people/jennypendel/sounds/53501/) | jennypendel | CC-Sampling+ |
| `1-61212-A-32.wav` | [00428 keyboard writing 1.wav](https://www.freesound.org/people/Robinhood76/sounds/61212/) | Robinhood76 | CC-BY-NC |

The video uses `1-53501-A-32.wav`, derived from jennypendel's `typing.wav`.
Noise is resampled once from 44.1 to 48 kHz, shortened to 4.9 seconds, scaled
for a specified input SNR, and mixed with speech. The displayed/app audio is
then processed by the evaluated enhancers. No isolated ESC-50 source audio is
republished. Educational use retains the original attribution and terms.

## Pretrained reference

The reference is the official DeepFilterNet v0.5.6 runtime with the pinned
DeepFilterNet3 ONNX model and source commit
`978576aa8400552a4ce9730838c635aa30db5e61`:
https://github.com/Rikorose/DeepFilterNet . Binary and model SHA256 values are
verified by the scripts. No training or fine-tuning is performed here.
