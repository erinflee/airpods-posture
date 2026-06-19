"""
One-time ~10-second NEUTRAL calibration. Run via AirpodsPosture.app.

Sit in your natural, sustainable working posture — NOT a forced "perfect" pose
(calibrating to a pose you'd never hold makes normal sitting read as slouch ->
all-day alert spam). Keep working normally; hold roughly still.

Stores per-axis mean (μ) and std (σ) of orientation + gravity to baseline.json:
  - Tier 1 threshold reads μ (raw delta in radians)
  - Tiers 2-3 model reads μ and σ (z-score normalization)
"""

import argparse
import sys
import time

from baseline import mean_std_fields, save_baseline
from config import BASELINE_PATH
from mac_motion import HeadphoneMotionReader


def main():
    # Settings (override the defaults from the command line)
    parser = argparse.ArgumentParser(
        prog="Erin's Tech Neck Corrector",
        description="Will record data and calibrate to your normal posture"
    )

    # '--' makes it optional for user to change default setting
    parser.add_argument('--countdown', help='Countdown before recording', type=float, default=5.0)
    parser.add_argument('--duration', help='Duration of recording', type=float, default=10.0)
    parser.add_argument('--output', help='Baseline that gets recorded', default=BASELINE_PATH)
    args = parser.parse_args() # reads all the args i just wrote


    # Need a live AirPods stream, or there's nothing to calibrate
    reader = HeadphoneMotionReader()
    if not reader.available():
        print("Error: AirPods motion not available. Connect AirPods to this Mac and run through AirpodsPosture.app.")
        return 1

    # Let the user settle into their natural posture before recording
    print("Sit in your natural, sustainable working posture — not a forced 'perfect' pose.")
    print(f"Recording starts in {args.countdown:.0f} seconds...")
    time.sleep(args.countdown)
    print(f"Recording neutral posture for {args.duration:.0f} seconds — hold roughly still.")

    # Record samples until `duration` seconds have passed
    def on_sample(sample):
        if time.monotonic() - start >= args.duration:
            reader.stop()    
        samples.append(sample)
        
    samples = []
    start = time.monotonic()
    reader.start(on_sample)
    reader.run_until_stopped()

    # Need >=2 samples to compute std
    if len(samples) < 2:
        print(f"Error: only collected {len(samples)} samples — need at least 2 to compute std. Is the stream working?")
        return 1

    # Boil the samples down to μ/σ and save them to baseline.json
    means, stds = mean_std_fields(samples)
    save_baseline(means, stds, len(samples), args.duration, args.output)

    # Summary so you can see it worked
    hz = len(samples) / args.duration
    print(f"Saved baseline to {args.output}")
    print(f"  {len(samples)} samples over {args.duration:.0f}s (~{hz:.0f} Hz)")
    print(f"  pitch: mean={means['pitch']:.3f} rad, std={stds['pitch']:.3f} rad")
    return 0


if __name__ == "__main__":
    sys.exit(main())
