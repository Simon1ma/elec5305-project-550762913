"""Score delay-aligned MATLAB outputs; make a measured latency-quality plot."""
from pathlib import Path
import csv
import json
import platform

import numpy as np
from scipy.io import loadmat
import scipy
from pystoi import stoi
import pystoi
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/latency_milestone1"


def snr(clean, output):
    return float(10*np.log10(np.sum(clean**2)/np.sum((output-clean)**2)))


def si_sdr(clean, output):
    reference = clean-clean.mean()
    estimate = output-output.mean()
    projection = np.dot(estimate,reference)/np.dot(reference,reference)*reference
    error = estimate-projection
    return float(10*np.log10(np.sum(projection**2)/max(np.sum(error**2),np.finfo(float).tiny)))


def evaluate():
    data = loadmat(OUT / "experiment.mat", squeeze_me=True)
    clean, noisy, outputs = data["clean"], data["noisy"], data["outputs"]
    fs = int(data["fs"])
    assert fs == 48000 and abs(snr(clean,noisy)) < 1e-8
    assert abs(stoi(clean,clean,fs,extended=False)-1) < 1e-6
    assert abs(si_sdr(clean,noisy)-si_sdr(clean,2*noisy)) < 1e-8
    with (OUT / "benchmark.csv").open() as stream:
        benchmark = list(csv.DictReader(stream))
    noisy_metrics = {"SNR_dB":snr(clean,noisy), "SI_SDR_dB":si_sdr(clean,noisy),
                     "STOI":float(stoi(clean,noisy,fs,extended=False))}
    rows = []
    for k, base in enumerate(benchmark):
        assert np.isfinite(outputs[:,k]).all() and len(outputs[:,k]) == len(clean)
        row = {**base, "Method":"Causal Wiener", "InputSNR_dB":noisy_metrics["SNR_dB"],
               "OutputSNR_dB":snr(clean,outputs[:,k]), "SI_SDR_dB":si_sdr(clean,outputs[:,k]),
               "STOI":float(stoi(clean,outputs[:,k],fs,extended=False))}
        row["Improvement_dB"] = row["OutputSNR_dB"]-row["InputSNR_dB"]
        rows.append(row)
    with (OUT / "metrics.csv").open("w",newline="",encoding="utf-8") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (OUT / "noisy_metrics.json").write_text(json.dumps(noisy_metrics,indent=2)+"\n")
    package_info = {"python":platform.python_version(),"numpy":np.__version__,
                    "scipy":scipy.__version__,"pystoi":pystoi.__version__,
                    "matplotlib":matplotlib.__version__}
    (OUT / "metric_environment.json").write_text(json.dumps(package_info,indent=2)+"\n")
    print("Noisy:",noisy_metrics)
    for row in rows:
        print({key:row[key] for key in ["Window_ms","OldestSampleReadyDelay_ms","OutputSNR_dB","SI_SDR_dB","STOI","RTF_median"]})
    return rows,noisy_metrics


def draw(rows, baseline):
    matplotlib.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Arial","DejaVu Sans"],
        "font.size":9,"axes.titlesize":10,"axes.labelsize":9,"xtick.labelsize":8,
        "ytick.labelsize":8,"legend.fontsize":8,"pdf.fonttype":42,"svg.fonttype":"none",
        "axes.spines.top":False,"axes.spines.right":False,"axes.linewidth":0.8})
    figure_dir = OUT / "figures"; figure_dir.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1,2,figsize=(183/25.4,85/25.4))
    fig.subplots_adjust(left=.085,right=.98,bottom=.27,top=.88,wspace=.32)
    delays = [float(row["OldestSampleReadyDelay_ms"]) for row in rows]
    for ax,key,title,ylabel in zip(axes,["STOI","SI_SDR_dB"],
                                  ["a  Intelligibility estimate","b  Waveform fidelity"],
                                  ["STOI","SI-SDR (dB)"]):
        ax.plot(delays,[row[key] for row in rows],"o-",color="#176b87",lw=1.4,ms=4,label="Causal Wiener")
        ax.axhline(baseline[key],color="#777777",ls="--",lw=1,label="Noisy reference")
        ax.set_title(title,loc="left",pad=9)
        ax.set_xlabel("Oldest-sample block-ready delay (ms)")
        ax.set_ylabel(ylabel)
        ax.set_xticks(delays)
        ax.set_xlim(5,85)
        ax.grid(axis="y",color="#dddddd",lw=.5)
        if key == "STOI":
            low = min(baseline[key],*(row[key] for row in rows))
            high = max(baseline[key],*(row[key] for row in rows))
            ax.set_ylim(max(0,low-.025),min(1,high+.025))
    handles,labels = axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",bbox_to_anchor=(.5,.01),ncol=2,frameon=False)
    # Both panels share the same four observations and form one quantitative grid.
    prefix = figure_dir / "latency_quality"
    fig.canvas.draw()
    rectangles = [ax.get_position().bounds for ax in axes]
    assert abs(rectangles[0][2]-rectangles[1][2])*fig.get_figwidth()*72 < 1.5
    assert abs(rectangles[0][3]-rectangles[1][3])*fig.get_figheight()*72 < 1.5
    try:
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        # Optional authoring audit; the experiment has no dependency on it.
        (figure_dir / "layout_rectangles.json").write_text(json.dumps(rectangles))
    else:
        require_matplotlib_panel_alignment(fig,json_out=str(prefix)+".alignment.json",
            overlay_svg=str(prefix)+".alignment.svg",tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    fig.savefig(str(prefix)+".png",dpi=300)
    fig.savefig(str(prefix)+".svg")
    fig.savefig(str(prefix)+".pdf")
    plt.close(fig)
    contract = {
        "question":"How does the measured block-ready delay relate to intelligibility and fidelity in this one recorded-speech mixture?",
        "scope":"One utterance, one noise recording segment, four configurations; no population inference",
        "archetype":"quantitative grid", "backend":"Python/matplotlib",
        "panels":{"a":"STOI; intelligibility estimate, not a listening-test result",
                  "b":"SI-SDR; scale-invariant waveform distortion"},
        "source_data":"metrics.csv; noisy_metrics.json",
        "uncertainty":"None for quality: n=1 utterance. Timing variation is reported separately in benchmark.csv.",
        "exclusions":"No measured configurations excluded. Noisy is a horizontal quality reference, not a latency-matched enhancer.",
        "delay_definition":"Oldest logical sample age when its H-sample output block is ready; includes capture packet, excludes compute/device/OS/network delays",
        "line_interpretation":"Lines connect four observed configurations as guides; no interpolation model was fitted",
    }
    (OUT / "figure_contract.json").write_text(json.dumps(contract,indent=2)+"\n")


if __name__ == "__main__":
    observations,noisy_baseline = evaluate()
    draw(observations,noisy_baseline)
