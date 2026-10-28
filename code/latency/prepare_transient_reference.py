"""Prepare a real keyboard clip and the official pretrained Windows runtime."""
from pathlib import Path
import configparser
import csv
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
import urllib.request

import numpy as np
from scipy.signal import resample_poly
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "data/local/latency2"
OUT = ROOT / "results/latency_milestone2"
VERSION = "v0.5.6"
ASSET = "deep-filter-0.5.6-x86_64-pc-windows-msvc.exe"
ESC_COMMIT = "33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6"
DF_COMMIT = "978576aa8400552a4ce9730838c635aa30db5e61"
EXPECTED_BINARY_SHA256 = "75e11fa16445f560cb6b021521ddb89e89270d13b83089705d98776f58fd7915"
EXPECTED_MODEL_SHA256 = "c94d91f70911001c946e0fabb4aa9adc37045f45a03b56008cb0c8244cb63616"


def get(url):
    with urllib.request.urlopen(url,timeout=45) as response:
        return response.read()


def download(url,path):
    if not path.exists():
        print("Downloading",path.name,flush=True)
        temporary = path.with_suffix(path.suffix+".partial")
        with urllib.request.urlopen(url,timeout=60) as response, temporary.open("wb") as stream:
            shutil.copyfileobj(response,stream,1024*1024)
        temporary.replace(path)


def main():
    LOCAL.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    esc_sha = ESC_COMMIT
    base = f"https://raw.githubusercontent.com/karolpiczak/ESC-50/{esc_sha}/"
    metadata = list(csv.DictReader(io.StringIO(get(base+"meta/esc50.csv").decode())))
    record = sorted((r for r in metadata if r["category"] == "keyboard_typing"),key=lambda r:r["filename"])[0]
    clip_url = base+"audio/"+record["filename"]
    clip_path = LOCAL / record["filename"]
    download(clip_url,clip_path)
    license_text = get(base+"LICENSE").decode()
    (LOCAL / "ESC50_LICENSE.txt").write_text(license_text,encoding="utf-8")
    keyboard,source_fs = sf.read(clip_path,dtype="float64")
    assert source_fs == 44100 and keyboard.ndim == 1
    keyboard = resample_poly(keyboard,160,147)
    sf.write(LOCAL/"keyboard_48k.wav",keyboard,48000,subtype="DOUBLE")

    release = json.loads(get(f"https://api.github.com/repos/Rikorose/DeepFilterNet/releases/tags/{VERSION}"))
    asset = next(a for a in release["assets"] if a["name"] == ASSET)
    executable = LOCAL / "deep-filter.exe"
    download(asset["browser_download_url"],executable)
    assert executable.read_bytes()[:2] == b"MZ"
    assert hashlib.sha256(executable.read_bytes()).hexdigest() == EXPECTED_BINARY_SHA256
    source_sha = DF_COMMIT
    source_base = f"https://raw.githubusercontent.com/Rikorose/DeepFilterNet/{source_sha}/"
    model_url = source_base+"models/DeepFilterNet3_onnx.tar.gz"
    model_path = LOCAL / "DeepFilterNet3_onnx.tar.gz"
    download(model_url,model_path)
    assert hashlib.sha256(model_path.read_bytes()).hexdigest() == EXPECTED_MODEL_SHA256
    with tarfile.open(model_path) as archive:
        config_member = next(m for m in archive.getmembers() if m.name.endswith("config.ini"))
        model_config = archive.extractfile(config_member).read().decode()
    (OUT / "deepfilternet_model_config.ini").write_text(model_config,encoding="utf-8")
    config = configparser.ConfigParser(); config.read_string(model_config)
    model_section = "deepfilternet"
    L = config.getint("DF","fft_size") if config.has_section("DF") else config.getint("df","fft_size")
    df_section = "DF" if config.has_section("DF") else "df"
    H = config.getint(df_section,"hop_size"); fs = config.getint(df_section,"sr")
    convolution_lookahead = config.getint(model_section,"conv_lookahead")
    filtering_lookahead = config.getint(df_section,"df_lookahead")
    lookahead = max(convolution_lookahead,filtering_lookahead)
    source_urls = {}
    for name in ("enhance_wav.rs","tract.rs","wav_utils.rs"):
        relative = "libDF/src/"+("bin/" if name=="enhance_wav.rs" else "")+name
        url = source_base+relative
        (LOCAL / name).write_bytes(get(url))
        source_urls[name] = url
    version = subprocess.run([str(executable),"--version"],capture_output=True,text=True,check=True).stdout.strip()
    (LOCAL / "deepfilter_help.txt").write_text(subprocess.run([str(executable),"--help"],capture_output=True,text=True,check=True).stdout)
    manifest = {
        "keyboard":{**record,"url":clip_url,"repository_commit":esc_sha,
            "original_author":"Anton", "original_recording":"keyboard-typing.wav",
            "original_source_url":"https://freesound.org/people/Anton/sounds/137/",
            "original_clip_license_label":"CC-BY as listed in the ESC-50 LICENSE",
            "original_sample_rate":source_fs,"sample_rate_after_preparation":48000,
            "resampling":"scipy.signal.resample_poly, up=160, down=147, once before creating shared mixtures",
            "selection":"First filename in lexicographic order labelled keyboard_typing; independent of enhancement output",
            "license":"ESC-50 CC BY-NC; clip attribution retained locally from the official LICENSE",
            "source_sha256":hashlib.sha256(clip_path.read_bytes()).hexdigest()},
        "reference":{"version":version,"binary_url":asset["browser_download_url"],
            "binary_sha256":hashlib.sha256(executable.read_bytes()).hexdigest(),
            "model":"DeepFilterNet3","model_url":model_url,
            "model_sha256":hashlib.sha256(model_path.read_bytes()).hexdigest(),
            "source_commit":source_sha,"source_urls":source_urls,
            "sample_rate":fs,"fft_size":L,"hop_size":H,
            "conv_lookahead_frames":convolution_lookahead,"df_lookahead_frames":filtering_lookahead,
            "combined_lookahead_frames":lookahead,
            "documented_transport_shift_samples":L-H+lookahead*H,
            "conservative_oldest_block_ready_delay_ms":1000*(L+lookahead*H)/fs,
            "output_format":"Official CLI writes 16-bit PCM; this quantisation is included in quality scores",
            "training":"Official pretrained weights only; no training or fine-tuning"},
        "experiment":{"speech":"Same VoiceBank p232_003 development utterance, first 4.5 seconds",
            "noise_types":["DEMAND washing-machine","ESC-50 keyboard typing"],
            "duration_seconds":4.5,"prefix_seconds":0.3,"target_snr_db":0,
            "calibration":"Same 300 ms initial noise-only policy for Wiener; reference receives identical input",
            "limitation":"One development utterance and one recording per noise type, no generalisation claim"}}
    (OUT / "data_and_model_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2),flush=True)


if __name__ == "__main__":
    main()
