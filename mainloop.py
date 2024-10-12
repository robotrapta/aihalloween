#!/usr/bin/env -S poetry run python

from functools import lru_cache
import logging
import os
import random
import time


# Framegrab bug makes me initialize logging before it's imported
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(process)d - %(levelname)s - %(message)s')

from PIL import Image
from framegrab import FrameGrabber, MotionDetector
from groundlight import Groundlight
from imgcat import imgcat
import cv2
import numpy as np
import typer

from fps import FpsDisplay
from simple_tts import make_mp3_text, play_mp3

logger = logging.getLogger(__name__)

cli_app = typer.Typer(no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]})


class VisualHalloween():
    """Creates a Groundlight detector for the given query, and whenever the detector triggers, it 
    will play a soundfile or text-to-speech message.
    """

    def __init__(self, query_name:str, query_text:str, scream_callback:callable=None, messages:list[str]=None, soundfile_dir:str=""):
        self.gl = Groundlight()
        self.name = query_name
        self.detector = self.gl.get_or_create_detector(
            name=query_name,
            query=query_text,
        )
        logger.info(f"Using detector {self.detector}")
        self.scream_callback = scream_callback
        if not messages:
            self.tts_choices = []
        else:
            self.tts_choices = messages
        self.soundfile_dir = soundfile_dir


    def tts_scream(self):
        text_choices = self.tts_choices
        if not text_choices:
            logger.info("No text configured - skipping scream")
            return
        chosen_text = random.choice(text_choices)
        logger.info(f"TTS speaking: '{chosen_text}'. Triggered by {self.detector.name}")
        audiofile = make_mp3_text(chosen_text)
        play_mp3(audiofile)

    def pick_and_play_soundfile(self, soundfile_dir:str):
        soundfiles = [f for f in os.listdir(soundfile_dir) if f.endswith('.mp3')]
        soundfile = os.path.join(soundfile_dir, random.choice(soundfiles))
        logger.info(f"Playing {soundfile}")
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
        logger.info(f"Got {iq.result} for {self.name} after {elased:.2f}s on image of size {frame.shape} with {iq.id}")
        if iq.result.label == "YES":
            self.do_scream()
            return True
        return False


def mainloop(motdet_pct:float=1.5, motdet_val:int=50):
    logger.info("Initializing camera")
    grabber = FrameGrabber.from_yaml("camera.yaml")[0]
    logger.info("Camera initialized")
    motdet = MotionDetector(motdet_pct, motdet_val)

    first_pass = VisualHalloween("any-people", "Are there any people on the sidewalk?")

    screamers = [
        VisualHalloween("doggie", "Can you see a dog?", soundfile_dir="media/dog"),
        VisualHalloween("baby-stroller", "Is there a baby stroller in view?", soundfile_dir="media/baby"),
        VisualHalloween("taking-photo", "Is someone holding a camera or cellphone towards the camera?",
                        messages=[
                            "How do I look? Spooky?",
                            "My hashtag is A.I. Halloween",
                        ]),
        VisualHalloween("pointing-at-me", "Is someone pointing at the camera?",
                        messages=[
                            "Don't point that at me!",
                            "I will rip that finger right off of you!",
                        ]),
        VisualHalloween("staring", "Is anybody looking straight at the camera?",
                        messages=[
                            "Hi.",
                            "What's up?",
                            "Boo!",
                            "What are you looking at?",
                            "Trick or treat!",
                        ]),
    ]

    fps_display = FpsDisplay(catch_exceptions=True)

    while True:
        with fps_display:  # prints fps once per second
            # Get the image
            frame = grabber.grab()
            grab_time = time.monotonic()
            if frame is None:
                logger.warning("No frame captured!")
                continue
            # Resize down to 800x600
            frame = cv2.resize(frame, (800, 600))

            # Process the image
            motion = motdet.motion_detected(frame)
            if motion:
                logger.info("Motion detected - checking first pass")
                if first_pass.process_image(frame):
                    # Fetch a fresh frame for the next step
                    frame = grabber.grab()
                    # reverse BGR for preview
                    imgcat(frame[:, :, ::-1])
                    cv2.imwrite("latest.jpg", frame)
                    logger.info("Found people - checking screamers")
                    for screamer in screamers:
                        if os.fork() == 0:
                            screamer.process_image(frame)
                            elapsed = time.monotonic() - grab_time
                            logger.info(f"Screamer {screamer.name} total response time: {elapsed:.2f}s")
                            os._exit(0)


if __name__ == "__main__":
    mainloop()
