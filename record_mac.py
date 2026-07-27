"""
Record AirPods motion to CSV. Run via AirpodsPosture.app.

  - CLI: --label (neutral/forward/dynamic), --duration, --output
  - open CSV with motion columns (time_ns, pitch, roll, yaw, accel, gyro, gravity)
  - stream samples from HeadphoneMotionReader into rows
  - print progress; stop on Ctrl+C or duration
  - main() entrypoint
"""

import argparse
import csv
import sys
import time
from pathlib import Path

from airpods_motion import HeadphoneMotionReader
from config import CLASS_PREFIX_TO_ID, DATA_DIR


def main():
    parser = argparse.ArgumentParser(
        prog="AirPods posture recorder",
        description="Record labeled motion CSVs (neutral / forward / dynamic).",
    )
    parser.add_argument("--label", required=True, choices=list(CLASS_PREFIX_TO_ID))
    parser.add_argument("--duration", type=float, default=300.0)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()


    DATA_DIR.mkdir(exist_ok=True)
    if args.output is not None:
        output = args.output

    else:
        n = 1
        while True:
            output = DATA_DIR / f"{args.label}_{n:02d}.csv"
            if not output.exists():
                break
            n += 1
    print(f"Recording {args.label} for {args.duration:.0f}s -> {output}")
    return 0



if __name__ == "__main__":
    sys.exit(main())
