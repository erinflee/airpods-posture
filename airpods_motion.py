"""
Read AirPods head motion via Core Motion (CMHeadphoneMotionManager).

Run through AirpodsPosture.app, not bare python3, so macOS grants Motion &
Fitness permission.
"""

from CoreMotion import CMHeadphoneMotionManager
from Foundation import NSDate, NSDefaultRunLoopMode, NSOperationQueue, NSRunLoop


def _motion_to_sample(motion):
    """One Core Motion sample -> plain dict matching the CSV columns."""
    attitude = motion.attitude()
    accel = motion.userAcceleration()
    gyro = motion.rotationRate()
    gravity = motion.gravity()
    return {
        "time_ns": int(motion.timestamp() * 1e9),
        "pitch": attitude.pitch(), # chin up/down (rad)
        "roll": attitude.roll(), # ear-to-shoulder
        "yaw": attitude.yaw(), # head turn
        "accelerationX": accel.x, # linear movement
        "accelerationY": accel.y,
        "accelerationZ": accel.z,
        "rotationRateX": gyro.x, # rotation speed
        "rotationRateY": gyro.y,
        "rotationRateZ": gyro.z,
        "gravityX": gravity.x, # down vector
        "gravityY": gravity.y,
        "gravityZ": gravity.z,
    }


class HeadphoneMotionReader:
    """Stream AirPods motion, passing each sample dict to a callback."""

    def __init__(self):
        self._manager = CMHeadphoneMotionManager.alloc().init()
        self._on_sample = None
        self._running = False

    def available(self):
        """True if AirPods motion can be read right now."""
        return bool(self._manager.isDeviceMotionAvailable())

    def start(self, on_sample):
        """Start streaming; call on_sample once per sample dict."""
        self._on_sample = on_sample
        self._running = True

        def handler(motion, error):
            if error is not None or motion is None:
                return
            if self._on_sample is not None:
                self._on_sample(_motion_to_sample(motion))

        queue = NSOperationQueue.mainQueue()
        self._manager.startDeviceMotionUpdatesToQueue_withHandler_(queue, handler)

    def stop(self):
        """Stop updates and let run_until_stopped() exit."""
        self._running = False
        self._manager.stopDeviceMotionUpdates()

    def run_until_stopped(self):
        """Block until stop() is called, pumping the run loop so callbacks fire."""
        while self._running:
            NSRunLoop.currentRunLoop().runMode_beforeDate_(
                NSDefaultRunLoopMode,
                NSDate.dateWithTimeIntervalSinceNow_(0.1),
            )


if __name__ == "__main__":
    reader = HeadphoneMotionReader()
    print("available:", reader.available())
    if not reader.available():
        raise SystemExit("AirPods motion not available — connect AirPods to this Mac.")

    state = {"count": 0}

    def on_sample(sample):
        state["count"] += 1
        if state["count"] <= 3 or state["count"] % 25 == 0:
            print(f"pitch={sample['pitch']:.3f}  samples={state['count']}")
        if state["count"] >= 75:
            reader.stop()

    print("Streaming ~3 s — nod your head to see pitch change…")
    reader.start(on_sample)
    reader.run_until_stopped()
    print(f"done ({state['count']} samples)")
