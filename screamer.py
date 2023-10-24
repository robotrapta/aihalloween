#!/usr/bin/env -S poetry run python
import time

from framegrab import FrameGrabber, MotionDetector
from imgcat import imgcat


def mainloop():
    grabber = FrameGrabber.from_yaml("camera.yaml")[0]
    motdet = MotionDetector()

    ema_fps = None
    while True:
        start_time = time.monotonic()
        frame = grabber.grab()
        if frame is None:
            print("No frame captured!")
            continue

        motion = motdet.motion_detected(frame)
        elapsed = time.monotonic() - start_time
        current_fps = 1.0 / elapsed
        if ema_fps is None:
            ema_fps = current_fps
        else:
            ema_fps = 0.9 * ema_fps + 0.1 * current_fps
        if motion:
            print(f"Motion detected!")
            imgcat(frame)
        print(f"fps={ema_fps:.2f}")


if __name__ == "__main__":
    mainloop()