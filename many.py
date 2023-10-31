#!/usr/bin/env -S poetry run python

from functools import lru_cache
import random
import time

from framegrab import FrameGrabber, MotionDetector
from groundlight import Groundlight
from imgcat import imgcat
import numpy as np
from PIL import Image
import typer

from simple_tts import make_mp3_text, play_mp3

cli_app = typer.Typer(no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]})


class VisualHalloween():

    def __init__(self, query_name:str, query_text:str, scream_callback:callable=None, messages:list[str]=None):
        self.gl = Groundlight()
        self.name = query_name
        self.detector = self.gl.get_or_create_detector(
                    name=query_name,
                    query=query_text,
                )
        print(f"Using detector {self.detector}")
        self.scream_callback = scream_callback
        if not messages:
            self.tts_choices = ["Oh no!"]
        else:
            self.tts_choices = messages

    def tts_scream(self):
        text_choices = self.tts_choices
        chosen_text = random.choice(text_choices)
        print("\n\n\nSCREAMING!!!  {chosen_text}\n\n\n")
        audiofile = make_mp3_text(chosen_text)
        play_mp3(audiofile)

    def do_scream(self):
        if self.scream_callback:
            self.scream_callback()
        else:
            self.tts_scream()

    def process_image(self, frame: np.ndarray) -> bool:
        start_time = time.monotonic()
        iq = self.gl.ask_ml(self.detector, frame)
        elased = time.monotonic() - start_time
        print(f"Got {iq.result} for {self.name} after {elased:.2f}s on image of size {frame.shape} with {iq.id}")
        if iq.result.label == "YES":
            self.do_scream()
            return True
        return False


def mainloop(motdet_pct:float=1.5, motdet_val:int=50):
    grabber = FrameGrabber.from_yaml("camera.yaml")[0]
    motdet = MotionDetector(motdet_pct, motdet_val)

    screamers = [
        VisualHalloween("doggie", "Can you see a dog?", messages=[
            "bark bark bark",
            "I like to eat dogs",
            "woof woof bark woof",
        ]),
        VisualHalloween("baby-stroller", "Is there a baby stroller in view?", messages=[
            "oooh that's a cute baby. she looks delicious.",
            "don't you think it's dangerous taking a baby out on halloween?"
            "I like to eat babies",
            "Aren't you worried a monster might jump out of the bushes and grab your baby?"
        ]),
        VisualHalloween("tongue-sticking","Is there a person facing the camera and sticking out their tongue?", messages=[
            "I will rip that tongue right out of you.",
            "Hey that's rude!",
            "Cut it out, or I'll cut that tongue out of you.",
            "Are you trying to make me angry?",
        ]),
    ]

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
            for screamer in screamers:
                screamer.process_image(frame)
        if time.monotonic() - last_fps_message > 1:
            last_fps_message = time.monotonic()
            print(f"fps={ema_fps:.2f}")


if __name__ == "__main__":
    mainloop()
