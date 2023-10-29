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
                name="tongue-sticking",
                query="Is there a person facing the camera and sticking out their tongue?",
            )
    print(f"Using detector {detector}")
    return gl, detector


@lru_cache(maxsize=1)
def clown_image() -> Image.Image:
    clown_image = Image.open("./media/scary-clown.jpg")
    return clown_image


def do_scream():
    print("\n\n\nSCREAMING!!!\n\n\n")
    text_choices = [
        "I will rip that tongue right out of you.",
        "Hey that's rude!",
        "Cut it out, or I'll cut that tongue out of you.",
        "Are you trying to make me angry?",
    ]
    chosen_text = random.choice(text_choices)
    audiofile = make_mp3_text(chosen_text)
    play_mp3(audiofile)


def process_image(frame: np.ndarray) -> bool:
    gl, detector = init_gl()
    start_time = time.monotonic()
    iq = gl.ask_ml(detector, frame)
    elased = time.monotonic() - start_time
    print(f"Got {iq.result} after {elased:.2f}s on image of size {frame.shape}")
    if iq.result.label == "YES":
        do_scream()
        return True
    return False

def mainloop():
    grabber = FrameGrabber.from_yaml("camera.yaml")[0]
    motdet = MotionDetector()

    ema_fps = None
    last_fps_message = 0
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
            # reverse BGR for preview
            imgcat(frame[:, :, ::-1])
            process_image(frame)
        if time.monotonic() - last_fps_message > 1:
            last_fps_message = time.monotonic()
            print(f"fps={ema_fps:.2f}")


if __name__ == "__main__":
    mainloop()