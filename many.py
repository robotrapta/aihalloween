#!/usr/bin/env -S poetry run python

from functools import lru_cache
import random
import time
import os
import random

import cv2
from framegrab import FrameGrabber, MotionDetector
from groundlight import Groundlight
from imgcat import imgcat
import numpy as np
from PIL import Image
import typer

from simple_tts import make_mp3_text, play_mp3

cli_app = typer.Typer(no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]})


class VisualHalloween():

    def __init__(self, query_name:str, query_text:str, scream_callback:callable=None, messages:list[str]=None, soundfile_dir:str=""):
        self.gl = Groundlight()
        self.name = query_name
        self.detector = self.gl.get_or_create_detector(
                    name=query_name,
                    query=query_text,
                )
        print(f"Using detector {self.detector}")
        self.scream_callback = scream_callback
        if not messages:
            self.tts_choices = []
        else:
            self.tts_choices = messages
        self.soundfile_dir = soundfile_dir


    def tts_scream(self):
        text_choices = self.tts_choices
        if not text_choices:
            print(f"No text configured - skipping scream")
            return
        chosen_text = random.choice(text_choices)
        print(f"\n\n\nTTS SCREAMING!!!  {chosen_text}\nTriggered by {self.detector.name}\n\n")
        audiofile = make_mp3_text(chosen_text)
        play_mp3(audiofile)

    def pick_and_play_soundfile(self, soundfile_dir:str):
        soundfiles = os.listdir(soundfile_dir)
        soundfile = soundfile_dir + "/" + random.choice(soundfiles)
        print(f"Playing {soundfile}")
        play_mp3(soundfile)

    def do_scream(self):
        if self.scream_callback:
            self.scream_callback()
        elif self.soundfile_dir:
            self.pick_and_play_soundfile(self.soundfile_dir)
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

    first_pass = VisualHalloween("any-people", "Are there any people on the sidewalk?")

    screamers = [
        VisualHalloween("doggie", "Can you see a dog?", soundfile_dir="media/dog"),
        VisualHalloween("baby-stroller", "Is there a baby stroller in view?", soundfile_dir="media/baby"),
        VisualHalloween("taking-photo", "Is someone holding a camera or cellphone towards the camera?",
                        messages=[
            "Take a picture, it will last longer.",
            "My hashtag is A.I. Halloween",
        ]),
        VisualHalloween("pointing-at-me", "Is someone pointing at the camera?",
                        messages=[
            "Don't point that at me!",
            "I will rip that finger off of you!",
        ]),
    ]

    ema_fps = None
    last_fps_message = 0
    while True:
        start_time = time.monotonic()

        # Get the image
        frame = grabber.grab()
        if frame is None:
            print("No frame captured!")
            continue

        # Process the image
        motion = motdet.motion_detected(frame)
        if motion:
            print("Motion detected - checking first pass")
            if first_pass.process_image(frame):
                # reverse BGR for preview
                imgcat(frame[:, :, ::-1])
                cv2.imwrite("latest.jpg", frame)
                print("Found people - checking screamers")
                for screamer in screamers:
                    screamer.process_image(frame)
        
        # Timing summary.
        elapsed = time.monotonic() - start_time
        current_fps = 1.0 / elapsed
        if ema_fps is None:
            ema_fps = current_fps
        else:
            ema_fps = 0.9 * ema_fps + 0.1 * current_fps
        if time.monotonic() - last_fps_message > 1:
            last_fps_message = time.monotonic()
            print(f"fps={ema_fps:.2f}")


if __name__ == "__main__":
    mainloop()
