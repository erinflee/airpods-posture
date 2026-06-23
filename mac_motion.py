"""
Read AirPods head motion from macOS Core Motion (CMHeadphoneMotionManager).

Run motion scripts through AirpodsPosture.app (not bare python3) so macOS
grants Motion & Fitness permission.
"""

from CoreMotion import CMHeadphoneMotionManager
from Foundation import NSDate, NSDefaultRunLoopMode, NSOperationQueue, NSRunLoop


def _motion_to_sample(motion):
    """Convert one Core Motion sample to a plain dict (matches CSV columns)."""
    attitude = motion.attitude()
    accel = motion.userAcceleration()
    gyro = motion.rotationRate()
    gravity = motion.gravity()
    return {
        "time_ns": int(motion.timestamp() * 1e9),
        "pitch": attitude.pitch(), # chin up/down movement
        "roll": attitude.roll(), # ear to shoulder
        "yaw": attitude.yaw(), # face look side 
        "accelerationX": accel.x, # sudden linear movement
        "accelerationY": accel.y,
        "accelerationZ": accel.z,
        "rotationRateX": gyro.x, # how fast is rotation
        "rotationRateY": gyro.y,
        "rotationRateZ": gyro.z,
        "gravityX": gravity.x, # helps us understand which way is down
        "gravityY": gravity.y,
        "gravityZ": gravity.z,
    }


class HeadphoneMotionReader:
    """Stream AirPods motion and pass each sample to a callback as a dict."""

    def __init__(self):
        """Create the Core Motion manager and set initial state."""
        self._manager = CMHeadphoneMotionManager.alloc().init()
        self._on_sample = None
        self._running = False

    def available(self):
        """Return True if AirPods motion can be read on this Mac right now."""
        return bool(self._manager.isDeviceMotionAvailable())

    def start(self, on_sample):
        """Begin streaming -> call on_sample once per motion dict."""
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
        """Stop motion updates and signal run_until_stopped() to exit."""
        self._running = False
        self._manager.stopDeviceMotionUpdates()

    def run_until_stopped(self):
        """Block until stop() is called so Core Motion callbacks can fire."""
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
