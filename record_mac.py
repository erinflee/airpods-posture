"""
Record AirPods motion to CSV. Run via AirpodsPosture.app.

  - CLI: --label (neutral/forward/dynamic), --duration, --output
  - open CSV with motion columns (time_ns, pitch, roll, yaw, accel, gyro, gravity)
  - stream samples from HeadphoneMotionReader into rows
  - print progress; stop on Ctrl+C or duration
  - main() entrypoint
"""

import csv
import sys
import time
import argparse
from airpods_motion import HeadphoneMotionReader
from config import DATA_DIR, CLASS_PREFIX_TO_ID






def main():
    parser = argparse.ArgumentParser(
        prog="AirPods posture recorder",
        description="Record labeled motion CSVs (neutral / forward / dynamic).",
    )
    parser.add_argument("--label", required=True, choices=list(CLASS_PREFIX_TO_ID))
    parser.add_argument("--duration", type=float, default=300.0)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    return 0



if __name__ == "__main__":
    sys.exit(main())
