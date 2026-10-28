"""Run the official stateful Rust reference and verify its delay convention."""
from pathlib import Path
import csv
import json
import re
import subprocess

import numpy as np
from scipy.signal import correlate, correlation_lags
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "data/local/latency2"
OUT = ROOT / "results/latency_milestone2"
EXE = LOCAL / "deep-filter.exe"
MODEL = LOCAL / "DeepFilterNet3_onnx.tar.gz"


def execute(source, output_dir, extra=()):
    command = [str(EXE),"--model",str(MODEL),"--output-dir",str(output_dir),"-v",*extra,str(source)]
    process = subprocess.run(command,capture_output=True,text=True,check=True)
    log = process.stdout+process.stderr
    match = re.search(r"RTF: ([0-9.eE+-]+)",log)
    assert match, log
    samples,fs = sf.read(output_dir/source.name,dtype="float64")
    assert fs == 48000 and np.isfinite(samples).all()
    return samples,float(match[1]),log


def main():
    config = json.loads((OUT/"data_and_model_manifest.json").read_text())["reference"]
    shift = config["documented_transport_shift_samples"]
    fs = 48000; prefix = 14400; length = 216000
    benchmark = []; saved = {}
    for name in ("washing","keyboard"):
        source = LOCAL / f"{name}_input.wav"
        execute(source,LOCAL/"warmup")
        runtimes = []
        previous = None
        for repeat in range(7):
            raw,rtf,log = execute(source,LOCAL/f"reference_{name}")
            assert previous is None or np.array_equal(raw,previous), "Repeated output differs"
            previous = raw.copy(); runtimes.append(rtf)
            (LOCAL/f"{name}_repeat{repeat}.log").write_text(log)
        assert np.max(np.abs(raw)) < .999, "Reference PCM16 output may be clipped"
        aligned = raw[shift+prefix:shift+prefix+length]
        assert len(aligned) == length
        sf.write(LOCAL/f"{name}_reference_aligned.wav",aligned,fs,subtype="DOUBLE")
        saved[name] = raw
        benchmark.append({"Noise":name,"Method":"DeepFilterNet3", "TransportShift_ms":shift/fs*1000,
            "OldestSampleReadyDelay_ms":config["conservative_oldest_block_ready_delay_ms"],
            "DelayEvidence":"Source/config derived block-ready delay; transport independently probed",
            "RTF_median":float(np.median(runtimes)),"RTF_min":min(runtimes),"RTF_max":max(runtimes),
            "Repeats":7,"Timing":"Official internal frame-loop timer; excludes setup and file I/O",
            "RTF_values":json.dumps(runtimes)})

    # Test passthrough STFT + lookahead using a separate non-silent probe.
    rng = np.random.default_rng(927)
    probe = .04*rng.standard_normal(96000)
    probe_path = LOCAL/"delay_probe.wav"
    sf.write(probe_path,probe,fs,subtype="FLOAT")
    bypass = ("--min-db-thresh=-100","--max-db-erb-thresh=-100","--max-db-df-thresh=-100")
    probe_out,_,_ = execute(probe_path,LOCAL/"probe_output",bypass)
    correlations = correlate(probe_out,probe,mode="full",method="fft")
    measured_shift = int(correlation_lags(len(probe_out),len(probe),mode="full")[np.argmax(correlations)])
    assert measured_shift == shift, (measured_shift,shift)
    retained_probe = probe[:len(probe_out)-shift]
    probe_error = float(np.linalg.norm(probe_out[shift:]-retained_probe)/np.linalg.norm(retained_probe))
    assert probe_error < .002, "Passthrough delay probe is not a near-identity transform"

    # Changing future samples must leave output emitted before that input unchanged.
    original,_ = sf.read(LOCAL/"keyboard_input.wav",dtype="float64")
    cutoff = 96000
    changed = original.copy(); changed[cutoff:] = .05*rng.standard_normal(len(changed)-cutoff)
    changed_path = LOCAL/"keyboard_future_changed.wav"
    sf.write(changed_path,changed,fs,subtype="FLOAT")
    changed_output,_,_ = execute(changed_path,LOCAL/"future_output")
    future_error = float(np.max(np.abs(changed_output[:cutoff]-saved["keyboard"][:cutoff])))
    assert future_error == 0, "Reference emitted output depends on future input"
    compensated,_,_ = execute(LOCAL/"keyboard_input.wav",LOCAL/"compensated",("--compensate-delay",))
    assert np.array_equal(compensated,saved["keyboard"][shift:])
    checks = {"documented_transport_samples":shift,"probe_measured_transport_samples":measured_shift,
        "probe_relative_error_including_pcm16":probe_error,
        "future_perturbation_cutoff_samples":cutoff,"future_invariance_max_error":future_error,
        "cli_compensate_delay_matches_exact_shift":True,
        "repeat_output_bit_identical":True,"pcm16_output_clipping_detected":False,
        "causality_evidence":"Source inspection of DfTract::process hop loop plus emitted-prefix invariance",
        "block_ready_delay_evidence":"Frame schedule derived from source/config and confirmed transport; not hardware latency measurement"}
    with (OUT/"reference_benchmark.csv").open("w",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(benchmark[0])); writer.writeheader(); writer.writerows(benchmark)
    (OUT/"reference_checks.json").write_text(json.dumps(checks,indent=2)+"\n")
    print(json.dumps({"benchmark":benchmark,"checks":checks},indent=2),flush=True)


if __name__ == "__main__":
    main()
