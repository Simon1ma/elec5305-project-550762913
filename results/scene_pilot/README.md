# Three-recording sound-scene pilot

Imported 7 November 2026. Labels are supplied by the user; no classifier has
predicted them. On 7 November 2026, the author confirmed personally capturing all
three recordings using a phone and personally performing the spoken reading.
The author subsequently clarified that the pressed object is a plastic bottle.
The legacy `pilot_can_press` identifier and original filename refer to that same
bottle recording; they do not represent an additional metal-can recording.

| Supplied label | Duration (s) | Decoded peak | Full-scale samples |
| --- | ---: | ---: | ---: |
| container_press (plastic bottle) | 12.5013 | 0.5210 | 0 |
| alarm | 7.8080 | 0.4428 | 0 |
| speech | 10.4533 | 0.3819 | 0 |

Original M4As, stream metadata, SHA256 hashes and mono 48 kHz PCM24 decodes
remain in ignored `data/local/scene/pilot/`. There is no gain normalisation.
The PCM full-scale check does not diagnose clipping before AAC encoding.

`features.csv` contains 13 acoustic features per complete source recording.
Feature extraction resamples once to 16 kHz; its RMS describes that signal.
`quality.csv` describes the decoded 48 kHz recordings. Waveform and spectrogram
panels use common display scales across the three sources.

The supplied alarm has lower mean spectral flatness (0.00397) than bottle pressing
(0.03887), consistent with concentrated tonal structure. Bottle pressing has higher
mean positive spectral flux (0.37115 versus 0.15997). Speech and bottle pressing
have similar mean spectral centroids in this pilot, demonstrating why a single
centroid threshold would not separate these particular examples well.

These descriptive differences guide feature design. Three source recordings
do not support a held-out classification accuracy or generalisation claim.
Next collect independent takes/sessions for each class, retaining a source-
recording/session split when creating any shorter examples.
