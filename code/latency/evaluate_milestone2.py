"""Evaluate two recorded noises and one official pretrained streaming reference."""
from pathlib import Path
import csv
import json

import numpy as np
from scipy.io import loadmat
from scipy.signal import spectrogram, convolve
import soundfile as sf
from pystoi import stoi
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from evaluate_latency import snr, si_sdr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/latency_milestone2"
LOCAL = ROOT / "data/local/latency2"


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def score(clean,output,fs):
    assert clean.shape == output.shape and np.isfinite(output).all()
    return {"OutputSNR_dB":snr(clean,output),"SI_SDR_dB":si_sdr(clean,output),
            "STOI":float(stoi(clean,output,fs,extended=False))}


def evaluate(data):
    fs = int(data["fs"]); clean = data["clean"]; rows = []
    wiener_timing = read_csv(OUT/"wiener_benchmark.csv")
    reference_timing = read_csv(OUT/"reference_benchmark.csv")
    for c,noise in enumerate(("washing","keyboard")):
        baseline = score(clean,data["noisy"][:,c],fs)
        assert abs(baseline["OutputSNR_dB"]) < 1e-5
        rows.append({"Noise":noise,"Method":"Noisy","Window_ms":"", "OldestSampleReadyDelay_ms":"",
            "TransportShift_ms":"","RTF_median":"","RTF_min":"","RTF_max":"",**baseline})
        for k,window in enumerate((10,20,40,80)):
            timing = wiener_timing[c*4+k]
            scores = score(clean,data["outputs"][:,k,c],fs)
            rows.append({"Noise":noise,"Method":"Causal Wiener","Window_ms":window,
                **{key:float(timing[key]) for key in ("OldestSampleReadyDelay_ms","TransportShift_ms","RTF_median","RTF_min","RTF_max")},**scores})
        reference,reference_fs = sf.read(LOCAL/f"{noise}_reference_aligned.wav")
        assert reference_fs == fs
        timing = reference_timing[c]
        rows.append({"Noise":noise,"Method":"DeepFilterNet3","Window_ms":20,
            **{key:float(timing[key]) for key in ("OldestSampleReadyDelay_ms","TransportShift_ms","RTF_median","RTF_min","RTF_max")},
            **score(clean,reference,fs)})
    with (OUT/"metrics.csv").open("w",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps(rows,indent=2))
    return rows


def export(fig,name,axes):
    directory = OUT/"figures"; directory.mkdir(exist_ok=True)
    prefix = directory/name
    fig.canvas.draw()
    try:
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        rectangles = [ax.get_position().bounds for ax in axes]
        (directory/f"{name}.layout.json").write_text(json.dumps(rectangles))
    else:
        require_matplotlib_panel_alignment(fig,axes=axes,
            json_out=str(prefix)+".alignment.json",overlay_svg=str(prefix)+".alignment.svg",
            tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    fig.savefig(str(prefix)+".png",dpi=300)
    fig.savefig(str(prefix)+".pdf")
    fig.savefig(str(prefix)+".svg")
    plt.close(fig)


def quality_plot(rows):
    fig,axes = plt.subplots(1,2,figsize=(183/25.4,88/25.4))
    fig.subplots_adjust(left=.085,right=.98,top=.87,bottom=.29,wspace=.32)
    for ax,noise,title in zip(axes,("washing","keyboard"),("a  Mechanical noise","b  Keyboard typing")):
        selected = [r for r in rows if r["Noise"] == noise]
        baseline = selected[0]; wiener = selected[1:5]; reference = selected[5]
        ax.plot([r["OldestSampleReadyDelay_ms"] for r in wiener],[r["STOI"] for r in wiener],
            "o-",color="#176b87",lw=1.3,ms=4,label="Causal Wiener")
        ax.scatter([reference["OldestSampleReadyDelay_ms"]],[reference["STOI"]],
            color="#aa4c2b",marker="D",s=30,zorder=3,label="DeepFilterNet3")
        ax.axhline(baseline["STOI"],color="#777777",ls="--",lw=1,label="Noisy reference")
        ax.set_title(title,loc="left",pad=9); ax.set_xlabel("Oldest-sample block-ready delay (ms)")
        ax.set_ylabel("STOI"); ax.set_xlim(5,85); ax.set_xticks([10,20,40,80])
        low = min(r["STOI"] for r in selected); high = max(r["STOI"] for r in selected)
        ax.set_ylim(max(0,low-.025),min(1,high+.025)); ax.grid(axis="y",color="#dddddd",lw=.5)
    handles,labels = axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",bbox_to_anchor=(.5,.01),ncol=3,frameon=False)
    export(fig,"quality_latency",list(axes))


def event_plot(data):
    fs = int(data["fs"]); n = len(data["clean"])
    noise = data["trueNoise"][:,1]
    energy = convolve(noise**2,np.ones(960)/960,mode="same")
    margin = int(.35*fs)
    peak = margin+int(np.argmax(energy[margin:-margin]))
    centre = peak/fs; start = centre-.3; stop = centre+.3
    event = {"centre_seconds":centre,"range_seconds":[start,stop],
        "selection":"Maximum 20 ms mean-square true keyboard noise, excluding the first/last 350 ms; independent of enhancement output",
        "display_spectrogram":"Common 20 ms Hann, 5 ms hop, FFT 1024 for both enhanced signals",
        "display_gain":"Native enhancement time/frequency grids, range 0-1",
        "scope":"One event in the same development clip, not an independent replicate"}
    (OUT/"event_selection.json").write_text(json.dumps(event,indent=2)+"\n")
    fig,axes = plt.subplots(3,2,figsize=(183/25.4,190/25.4))
    fig.subplots_adjust(left=.085,right=.87,bottom=.13,top=.94,hspace=.64,wspace=.36)
    time = np.arange(n)/fs
    mask = (time>=start)&(time<=stop)
    amp = np.max(np.abs(np.column_stack([data["clean"][mask],data["noisy"][mask,1],data["outputs"][mask,0,1],data["outputs"][mask,3,1]])))*1.05
    labels = ["a","b","c","d","e","f"]
    spectrum_image = gain_image = None
    for col,(k,window) in enumerate(((0,10),(3,80))):
        output = data["outputs"][:,k,1]
        ax = axes[0,col]
        ax.plot(time[mask],data["noisy"][mask,1],color="#aaaaaa",lw=.55,label="Noisy")
        ax.plot(time[mask],output[mask],color="#176b87",lw=.65,label="Enhanced")
        ax.plot(time[mask],data["clean"][mask],color="#222222",lw=.5,label="Clean")
        ax.set_ylim(-amp,amp); ax.set_ylabel("Amplitude")
        ax.set_title(f"{labels[col]}  {window} ms: waveform",loc="left",pad=8)
        frequency,tt,magnitude = spectrogram(output,fs=fs,window="hann",nperseg=960,noverlap=720,
            nfft=1024,detrend=False,scaling="spectrum",mode="magnitude")
        ax = axes[1,col]
        spectrum_image = ax.pcolormesh(tt,frequency/1000,20*np.log10(np.maximum(magnitude,1e-8)),
            shading="auto",vmin=-90,vmax=-20,cmap="viridis",rasterized=True)
        ax.set_ylim(0,8); ax.set_ylabel("Frequency (kHz)")
        ax.set_title(f"{labels[2+col]}  Enhanced spectrum",loc="left",pad=8)
        detail = getattr(data["diagnostics"],f"window{window}")
        ax = axes[2,col]
        gain_image = ax.pcolormesh(detail.frameCentreSeconds,detail.frequency/1000,detail.gain,
            shading="auto",vmin=0,vmax=1,cmap="viridis",rasterized=True)
        ax.set_ylim(0,8); ax.set_ylabel("Frequency (kHz)")
        ax.set_title(f"{labels[4+col]}  Native Wiener gain",loc="left",pad=8)
        for row in range(3):
            axes[row,col].set_xlim(start,stop)
            axes[row,col].set_xlabel("Time in speech segment (s)")
    spectrum_box = axes[1,1].get_position()
    gain_box = axes[2,1].get_position()
    spectrum_bar = fig.add_axes([.89,spectrum_box.y0,.018,spectrum_box.height])
    gain_bar = fig.add_axes([.89,gain_box.y0,.018,gain_box.height])
    cb = fig.colorbar(spectrum_image,cax=spectrum_bar); cb.set_label("STFT magnitude (dB)")
    cb = fig.colorbar(gain_image,cax=gain_bar); cb.set_label("Gain")
    handles,legend = axes[0,0].get_legend_handles_labels()
    fig.legend(handles,legend,loc="lower center",bbox_to_anchor=(.47,.015),ncol=3,frameon=False)
    export(fig,"keyboard_event",list(axes.flat))


def main():
    matplotlib.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Arial","DejaVu Sans"],
        "font.size":8,"axes.titlesize":9,"axes.labelsize":8,"xtick.labelsize":7,"ytick.labelsize":7,
        "legend.fontsize":8,"pdf.fonttype":42,"svg.fonttype":"none", "axes.linewidth":.8,
        "axes.spines.top":False,"axes.spines.right":False})
    data = loadmat(OUT/"experiment.mat",squeeze_me=True,struct_as_record=False)
    rows = evaluate(data)
    quality_plot(rows); event_plot(data)
    contract = {"backend":"Python/matplotlib","data":"metrics.csv; experiment.mat diagnostics; event_selection.json",
        "quality_figure":"Two-panel quantitative grid: noise type stratifies the same latency-quality question",
        "event_figure":"Three-row quantitative/image composite: waveform, common-resolution output spectra, native gains",
        "replication":"One 4.5 s development utterance; two recordings are conditions, not speech replicates",
        "uncertainty":"No quality error bars for n=1; seven-repeat timing ranges are in benchmark CSV files",
        "exclusions":"All four Wiener settings and reference retained for each noise; event crop rule declared separately",
        "reference_delay":"40 ms from pinned source/config; 30 ms transport verified by an independent near-identity probe",
        "limits":"No hard real-time or end-to-end device measurement; no neural training; runtime implementation and output precision differ",
        "style_adaptation":"Typography and method-family colours reused from the earlier project figure; new data mapping and event layout"}
    (OUT/"figure_contract.json").write_text(json.dumps(contract,indent=2)+"\n")


if __name__ == "__main__":
    main()
