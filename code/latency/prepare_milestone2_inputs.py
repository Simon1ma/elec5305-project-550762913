"""Build identical, headroom-safe stationary/keyboard inputs for both runtimes."""
from pathlib import Path
import json
import hashlib

import numpy as np
from scipy.io import savemat
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "data/local/latency2"
OUT = ROOT / "results/latency_milestone2"


def main():
    fs = 48000; prefix = 14400; length = 216000; tail = 4800
    clean, sr = sf.read(ROOT / "data/local/latency/clean.wav")
    washing, sr_w = sf.read(ROOT / "data/local/latency/noise.wav")
    keyboard, sr_k = sf.read(LOCAL / "keyboard_48k.wav")
    assert sr == sr_w == sr_k == fs
    clean = clean[:length]
    noises = [washing[:prefix+length+tail], keyboard[:prefix+length+tail]]
    mixtures = []; scaled_noises = []
    for noise in noises:
        assert len(noise) == prefix+length+tail
        scale = np.sqrt(np.mean(clean**2)/np.mean(noise[prefix:prefix+length]**2))
        scaled = noise*scale
        mixed = scaled.copy(); mixed[prefix:prefix+length] += clean
        mixtures.append(mixed); scaled_noises.append(scaled)
    common_scale = .8/max(np.max(np.abs(mixtures)),np.max(np.abs(clean)))
    clean = clean*common_scale
    inputs = (np.column_stack(mixtures)*common_scale).astype(np.float32)
    scaled_noises = np.column_stack(scaled_noises)*common_scale
    for k,name in enumerate(("washing","keyboard")):
        sf.write(LOCAL/f"{name}_input.wav",inputs[:,k],fs,subtype="FLOAT")
    savemat(LOCAL/"inputs.mat",{"clean":clean[:,None],"inputs":inputs.astype(float),
        "trueNoise":scaled_noises,"fs":fs,"prefixSamples":prefix,"speechSamples":length,
        "tailSamples":tail},do_compression=True)
    block_energy = (inputs.T.reshape(2,-1,480)**2).mean(axis=2)
    info = {"sample_rate":fs,"speech_seconds":length/fs,"calibration_seconds":prefix/fs,
        "recorded_noise_tail_seconds":tail/fs,"full_input_seconds":inputs.shape[0]/fs,
        "common_input_attenuation":float(common_scale),"maximum_input_amplitude":float(np.max(np.abs(inputs))),
        "input_quantisation":"Shared float32 WAV inputs for MATLAB and official DeepFilterNet CLI",
        "reference_speech_quantisation":"Double-precision scaled clean reference; no per-output peak normalisation",
        "noise_tail":"100 ms of the same actual recording, added after speech to drain delayed output; no loop or artificial keyboard join",
        "deepfilter_silence_skip_threshold_power":1e-7,
        "blocks_below_reference_silence_threshold":{name:int(np.sum(block_energy[k]<1e-7)) for k,name in enumerate(("washing","keyboard"))},
        "files":{name:hashlib.sha256((LOCAL/name).read_bytes()).hexdigest() for name in ("washing_input.wav","keyboard_input.wav")}}
    (OUT/"shared_input_manifest.json").write_text(json.dumps(info,indent=2)+"\n")
    print(json.dumps(info,indent=2))


if __name__ == "__main__":
    main()
