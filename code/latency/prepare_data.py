"""Download two official archives and retain a documented single-clip example."""
from pathlib import Path
import hashlib
import io
import json
import shutil
import urllib.request
import zipfile

import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "data/local/latency"
SPEECH_URL = "https://datashare.ed.ac.uk/server/api/core/bitstreams/dec213d3-bf57-4777-9663-c24bdce92d5e/content"
NOISE_URL = "https://zenodo.org/api/records/1227121/files/DWASHING_48k.zip/content"


class RemoteZip(io.RawIOBase):
    """Seekable HTTP ranges let zipfile retrieve just one noise channel."""
    def __init__(self, url):
        self.url = url
        self.position = 0
        request = urllib.request.Request(url, headers={"Range":"bytes=0-0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            assert response.status == 206
            self.length = int(response.headers["Content-Range"].split("/")[-1])

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = (0 if whence == 0 else self.position if whence == 1 else self.length)+offset
        return self.position

    def read(self, size=-1):
        size = self.length-self.position if size < 0 else min(size,self.length-self.position)
        pieces = []
        while size > 0:
            take = min(size,1024*1024)
            start = self.position
            stop = start+take-1
            request = urllib.request.Request(self.url,headers={"Range":f"bytes={start}-{stop}"})
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(request,timeout=30) as response:
                        assert response.status == 206
                        assert response.headers["Content-Range"].startswith(f"bytes {start}-{stop}/")
                        payload = response.read()
                    assert len(payload) == take
                    break
                except Exception:
                    if attempt == 2:
                        raise
            pieces.append(payload)
            self.position += take
            size -= take
        return b"".join(pieces)


def download(url, path):
    if path.exists() and zipfile.is_zipfile(path):
        return
    temporary = path.with_suffix(".partial")
    print(f"Downloading {path.name}", flush=True)
    with urllib.request.urlopen(url, timeout=90) as response, temporary.open("wb") as stream:
        shutil.copyfileobj(response, stream, length=1024*1024)
    assert zipfile.is_zipfile(temporary), "Download is not a valid ZIP archive"
    temporary.replace(path)


def main():
    LOCAL.mkdir(parents=True, exist_ok=True)
    speech_archive = LOCAL / "clean_testset_wav.zip"
    download(SPEECH_URL, speech_archive)
    with zipfile.ZipFile(speech_archive) as archive:
        for name in sorted(archive.namelist()):
            if not Path(name).name.startswith("p232_") or not name.endswith(".wav"):
                continue
            payload = archive.read(name)
            info = sf.info(io.BytesIO(payload))
            if info.samplerate == 48000 and info.duration >= 4:
                speech, fs = sf.read(io.BytesIO(payload), dtype="float64")
                speech_name = name
                break
        else:
            raise RuntimeError("No suitable p232 speech utterance found")
    channel_cache = LOCAL / "DWASHING_ch01.wav"
    if not channel_cache.exists():
        print("Retrieving only channel 1 from the official DEMAND archive",flush=True)
        with zipfile.ZipFile(RemoteZip(NOISE_URL)) as archive:
            noise_name = next(name for name in sorted(archive.namelist())
                              if Path(name).name.lower() == "ch01.wav")
            payload = archive.read(noise_name)  # zipfile checks the member CRC.
            channel_cache.write_bytes(payload)
            (LOCAL / "noise_member.txt").write_text(noise_name)
    noise_name = (LOCAL / "noise_member.txt").read_text()
    noise, noise_fs = sf.read(channel_cache,dtype="float64")
    assert fs == noise_fs == 48000 and speech.ndim == noise.ndim == 1
    speech = speech[:8*fs]
    noise_offset_seconds = 10
    noise = noise[noise_offset_seconds*fs:noise_offset_seconds*fs+len(speech)+fs]
    assert len(noise) >= len(speech)+round(.3*fs)
    sf.write(LOCAL / "clean.wav", speech, fs, subtype="DOUBLE")
    sf.write(LOCAL / "noise.wav", noise, fs, subtype="DOUBLE")
    manifest = {
        "speech_source": "https://doi.org/10.7488/ds/2117",
        "speech_archive_url": SPEECH_URL,
        "speech_file": speech_name,
        "speech_speaker": "p232",
        "speech_segment_start_seconds": 0,
        "speech_samples": len(speech),
        "noise_source": "https://zenodo.org/records/1227121",
        "noise_archive_url": NOISE_URL,
        "noise_archive_md5": "ecf765f12b8d3ada7ef0ec664b8f8d73",
        "noise_integrity": "ZIP member CRC verified; published whole-archive MD5 recorded but not verified because only channel 1 is fetched",
        "noise_file": noise_name,
        "noise_segment_start_seconds": noise_offset_seconds,
        "noise_label": "DEMAND washing-machine recording; not fan or keyboard noise",
        "sample_rate": fs,
        "resampling": "None: both sources are native 48 kHz",
        "selection_rule": "First lexicographically sorted p232 utterance with duration >=4 s; retain at most 8 s",
        "role": "Single-utterance engineering/development example; not held-out benchmark evidence",
        "speech_license": "CC BY 4.0 per the University of Edinburgh dataset End-user Licence",
        "noise_license": "CC BY-SA 3.0 according to DEMAND dataset description",
    }
    for filename in ("clean.wav", "noise.wav"):
        manifest[filename+"_sha256"] = hashlib.sha256((LOCAL/filename).read_bytes()).hexdigest()
    result_dir = ROOT / "results/latency_milestone1"
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "data_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
