"""
Record AirPods motion to CSV. Run via AirpodsPosture.app. 

  - CLI: --label (good/slouch/dynamic), --duration, --output
  - open CSV with motion columns (time_ns, pitch, roll, yaw, accel, gyro, gravity)
  - stream samples from HeadphoneMotionReader into rows
  - print progress; stop on Ctrl+C or duration
  - main() entrypoint
"""

