# Final experiment: causal latency and speech enhancement quality

Run commands from the repository root. Tested on Windows 11 x64, Python 3.12.14,
MATLAB R2026a Update 5 with Signal Processing Toolbox, and the official
DeepFilterNet v0.5.6 Windows Rust/Tract runtime. No Python neural-network framework
or model training is required. Other operating systems are not validated here.

## 1. Prepare reproducible inputs and reference runtime

```text
python -m pip install -r code/final/requirements.txt
python code/latency/prepare_transient_reference.py
python code/final/prepare_final_inputs.py
python code/final/prepare_external_inputs.py
```

The reference preparer also retrieves a small historical keyboard clip and
recreates its historical manifest. The final mixture preparer reads selected
members of the official VoiceBank clean 28-speaker ZIP using HTTP ranges; it does
not download the whole archive. External preparation downloads the approximately
346 MB LibriSpeech test-clean archive and verifies its official MD5. An existing
archive can be supplied with `--archive PATH`. Both preparations keep raw data,
weights, binaries, and generated signal arrays under ignored `data/local/`.
The external preparer reuses the four noise files prepared by the preceding step.
Internet access and free local space (allow at least 4 GB) are required.

The historical milestone 2 probes can be reproduced using the separate
[milestone instructions](../latency/README.md). Their current-machine quality and
causality checks are retained in `results/final/development_reproduction/`.
These probes use development data and are not extra evaluation speakers.

## 2. Run the frozen processors

In MATLAB, with the repository as Current Folder:

```matlab
addpath(fullfile(pwd,'code','latency'));
addpath(fullfile(pwd,'code','final'));
check_causal();
main_final_wiener('external');
main_final_wiener('voicebank');
```

Outside MATLAB:

```text
python code/final/run_final_reference.py --cohort external
python code/final/evaluate_final.py --cohort external
python code/final/run_final_reference.py --cohort voicebank
python code/final/evaluate_final.py --cohort voicebank
```

Each cohort has 144 shared mixtures and 864 metric rows. Quality scoring uses
known transport shifts only. WAV and MAT input arrays must be exactly equal;
input hashes and reference binary/model hashes are checked. Rerunning preparation
is deterministic. Fixed source selection is specified in the input manifests.

## 3. Benchmark separately and inspect the keyboard event

Close other compute-heavy work and run benchmark commands **sequentially**.
Do not benchmark MATLAB and the reference concurrently.

```matlab
benchmark_final_wiener('external');
capture_final_event('external');
benchmark_final_wiener('voicebank');
```

Then, outside MATLAB:

```text
python code/final/run_final_reference.py --cohort external --benchmark
python code/final/run_final_reference.py --cohort voicebank --benchmark
python code/final/summarize_final.py --cohort external
python code/final/summarize_final.py --cohort voicebank
```

One warm-up is omitted and seven repeats are measured on the first utterance,
first noise source of each class, at 0 dB. Per-hop Wiener timings include timer
and input validation overhead, include calibration, and exclude EOF flush. The
reference exposes a frame-loop RTF but no per-hop timings. RTF is not hardware
latency and does not establish a hard real-time guarantee.

## 4. Interactive code demonstration and audition

```matlab
addpath(fullfile(pwd,'code','final'));
launch_final_demo('external');
```

Choose a recorded noise, SNR, and method, then click **Run processor**. The app
actually reruns the selected processor and asserts agreement with the evaluated
output. Play clean, noisy, and processed clips using a common gain; stop playback
before switching. The display reports the known ready delay, SNR, and the saved
canonical pystoi score. This is recorded-file processing, not live microphone
capture. The fixed first utterance is used throughout the demo.

## Outputs and interpretation

- `results/final_external/`: primary external LibriSpeech test-clean cohort.
- `results/final/`: secondary VCTK-derived engineering cohort and development
  reproduction. VCTK is mentioned in the model's training description.
- `output/pdf/Final_Project_Yixiang_Ma.pdf`: research report.
- `submissions/Final_Project_Demo.mp4`: short captioned app walkthrough with
  actual clean/noisy/enhanced audio and a common playback gain.

LibriSpeech is 16 kHz; resampling to 48 kHz adds no speech bandwidth. Neither
cohort certifies complete independence from upstream model training. Report
limits and the protocol amendment are in `docs/pretraining_overlap_audit.md`.
Full datasets, downloaded executables, and pretrained weights are not committed.
Audio excerpts in the deliverables are educational derivatives with attribution
in `docs/final_data_attribution.md`.
