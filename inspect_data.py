"""
Plot and summarize CSV recordings before training

  - summarize_file(path): sample count, pitch/roll mean/std
  - plot_file(path, out_dir): save pitch/roll vs time PNG to results/
  - main(): loop data/*.csv, print stats, optional --plot
"""

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from statistics import fmean, pstdev
from config import BASELINE_PATH, DATA_DIR, CLASS_PREFIX_TO_ID

def load_csv(csv_path):
    with open(csv_path, 'r', newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def label_from_filename(path):
    filename = Path(path).stem # neutral_01.csv -> cuts .csv and returns neutral_01
    prefix = filename.split("_")[0]
    if prefix in CLASS_PREFIX_TO_ID.keys():
        return prefix
    raise ValueError("invalid file name")
    

def summarize_file(path, baseline):
    rows = load_csv(path)
    prefix = label_from_filename(path)
    baseline_mean_pitch = baseline["mean"]["pitch"]
    data = {
        "pitch": [],
        "roll": [], 
        "delta_pitch": []
    }

    for row in rows: 
        data["pitch"].append(float(row["pitch"]))
        data["roll"].append(float(row["roll"]))
        data["delta_pitch"].append(float(row["pitch"]) - baseline_mean_pitch)

    stats = {
        "sample_count": len(rows),
        "label": prefix,
        "pitch_mean": fmean(data["pitch"]),
        "roll_mean": fmean(data["roll"]),
        "delta_pitch_mean": fmean(data["delta_pitch"]),
        "pitch_std": pstdev(data["pitch"]),
        "roll_std": pstdev(data["roll"]),
        "delta_pitch_std": pstdev(data["delta_pitch"]),
    }
    return stats


def plot_file(path, baseline, out_dir):
    rows = load_csv(path)
    baseline_mean_pitch = baseline["mean"]["pitch"]

    pitch = [float(row["pitch"]) for row in rows]
    roll = [float(row["roll"]) for row in rows]
    delta_pitch = [p - baseline_mean_pitch for p in pitch]
    x = list(range(len(rows)))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    stem = Path(path).stem

    axes[0].plot(x, delta_pitch)
    axes[0].set_ylabel("delta pitch (rad)")
    axes[0].set_title(stem)

    axes[1].plot(x, pitch)
    axes[1].set_ylabel("pitch (rad)")

    axes[2].plot(x, roll)
    axes[2].set_ylabel("roll (rad)")
    axes[2].set_xlabel("sample index")

    fig.tight_layout()
    fig.savefig(out_dir / f"{stem}.png")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Summarize and plot posture CSV recordings")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--plot", action="store_true", help="Save pitch/roll PNGs to results/")
    args = parser.parse_args()

    baseline = load_baseline(args.baseline)
    csv_files = sorted(args.data_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files in {args.data_dir}", file=sys.stderr)
        return 1

    delta_pitch_by_label = {}
    for csv_path in csv_files:
        stats = summarize_file(csv_path, baseline)
        print(
            f"{csv_path.name}: "
            f"samples={stats['sample_count']} label={stats['label']} "
            f"pitch_mean={stats['pitch_mean']:.4f} roll_mean={stats['roll_mean']:.4f} "
            f"delta_pitch_mean={stats['delta_pitch_mean']:.4f} "
            f"pitch_std={stats['pitch_std']:.4f} roll_std={stats['roll_std']:.4f}"
        )
        delta_pitch_by_label[stats["label"]] = stats["delta_pitch_mean"]
        if args.plot:
            plot_file(csv_path, baseline, ROOT / "results")

    if "forward" in delta_pitch_by_label and "neutral" in delta_pitch_by_label:
        ok = delta_pitch_by_label["forward"] < delta_pitch_by_label["neutral"]
        print(f"sanity: forward delta_pitch mean more negative than neutral? {ok}")

    return 0


