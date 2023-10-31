#!/usr/bin/env -S poetry run python
from functools import lru_cache
import random
import time

from framegrab import FrameGrabber, MotionDetector
from groundlight import Groundlight
from imgcat import imgcat
import numpy as np
from PIL import Image

from simple_tts import make_mp3_text, play_mp3


@lru_cache(maxsize=1)
def init_gl() -> tuple[Groundlight, "Detector"]:
    gl = Groundlight()
    detector = gl.get_or_create_detector(
                name="doggie",
                query="Can you see a dog?",
            )
    print(f"Using detector {detector}")
    return gl, detector


def do_scream():
    print("\n\n\nSCREAMING!!!\n\n\n")
    text_choices = [
        "Here kitty kitty kitty kitty",
        "Woof woof",
        "I'm a helpless squirrel stuck in this hedge, I hope that dog doesn't see me",
    ]
    chosen_text = random.choice(text_choices)
    audiofile = make_mp3_text(chosen_text)
    play_mp3(audiofile)


def process_image(frame: np.ndarray) -> bool:
    gl, detector = init_gl()
    start_time = time.monotonic()
    iq = gl.ask_ml(detector, frame)
    elased = time.monotonic() - start_time
    print(f"Got {iq.result} after {elased:.2f}s on image of size {frame.shape} with {iq.id}")
    if iq.result.label == "YES":
        do_scream()
        return True
    return False

def mainloop():
    grabber = FrameGrabber.from_yaml("camera.yaml")[0]
    motdet = MotionDetector(pct_threshold=1.5, val_threshold=20)

    ema_fps = None
    last_fps_message = 0
    while True:
        start_time = time.monotonic()
        frame = grabber.grab()
        if frame is None:
            print("No frame captured!")
            continue
        # invert the frame by 180 degrees
        frame = np.rot90(frame, 2)

        motion = motdet.motion_detected(frame)
        elapsed = time.monotonic() - start_time
        current_fps = 1.0 / elapsed
        if ema_fps is None:
            ema_fps = current_fps
        else:
            ema_fps = 0.9 * ema_fps + 0.1 * current_fps
        if motion:
            # reverse BGR for preview
            imgcat(frame[:, :, ::-1])
            process_image(frame)
        if time.monotonic() - last_fps_message > 1:
            last_fps_message = time.monotonic()
            print(f"fps={ema_fps:.2f}")


if __name__ == "__main__":
    mainloop()
