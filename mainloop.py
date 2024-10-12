#!/usr/bin/env -S poetry run python

from functools import lru_cache
import datetime
import json
import logging
import os
import random
import time

from timebudget import timebudget


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


class HalloweenDetector():
    """Creates a Groundlight detector for the given query, and whenever the detector triggers, it 
    will play a soundfile or text-to-speech message.
    """

    def __init__(self, 
                 query_name: str, 
                 query_text: str, 
                 trigger_callback: callable = None, 
                 messages: list[str] = None, 
                 soundfile_dir: str = ""):
        self.gl = Groundlight()
        self.name = query_name
        self.detector = self.gl.get_or_create_detector(
            name=query_name,
            query=query_text,
        )
        logger.info(f"Using detector {self.detector}")
        self.trigger_callback = trigger_callback
        if not messages:
            self.tts_choices = []
        else:
            self.tts_choices = messages
        self.soundfile_dir = soundfile_dir


    def tts_trigger(self):
        text_choices = self.tts_choices
        if not text_choices:
            logger.info("No text configured - skipping trigger")
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

    def do_trigger(self):
        if self.trigger_callback:
            self.trigger_callback()
        elif self.soundfile_dir:
            self.pick_and_play_soundfile(self.soundfile_dir)
        else:
            self.tts_trigger()

    def process_image(self, frame: np.ndarray) -> bool:
        start_time = time.monotonic()
        iq = self.gl.ask_ml(self.detector, frame)
        elased = time.monotonic() - start_time
        logger.info(f"{self.name} got {iq.result.label} ({iq.result.confidence:.2f}) after {elased:.2f}s iq={iq.id}")
        if iq.result.label == "YES":
            self.do_trigger()
            return True
        return False

def save_jpeg(filename_base:str, image:bytes | np.ndarray, metadata:dict={}):
    image_filename = f"status/media/{filename_base}.jpg"
    if isinstance(image, np.ndarray):
        image = cv2.imencode('.jpg', image)[1].tobytes()
    with open(image_filename, "wb") as f:
        f.write(image)
    # save a .json status file with the filename, creation time, and md5sum of the image    
    status_filename = f"status/media/{filename_base}.json"
    with open(status_filename, "w") as f:
        doc = {
            "filename": image_filename,
            "created": datetime.datetime.now().isoformat(),
        }
        doc.update(metadata)
        json.dump(doc, f)

def mainloop(motdet_pct:float=1.5, motdet_val:int=50):
    logger.info("Initializing camera")
    grabber = FrameGrabber.from_yaml("camera.yaml")[0]
    first_frame = grabber.grab()
    save_jpeg("first-frame", first_frame)
    logger.info("Camera initialized")
    motdet = MotionDetector(motdet_pct, motdet_val)

    any_people = HalloweenDetector("any-people", "Are there any people on the sidewalk?")

    detectors = [
        HalloweenDetector("doggie", "Can you see a dog?", soundfile_dir="media/dog"),
        HalloweenDetector("baby-stroller", "Is there a baby stroller in view?", soundfile_dir="media/baby"),
        HalloweenDetector("taking-photo", "Is someone holding a camera or cellphone towards the camera?",
                        messages=[
                            "How do I look? Spooky?",
                            "My hashtag is A.I. Halloween",
                        ]),
        HalloweenDetector("pointing-at-me", "Is someone pointing at the camera?",
                        messages=[
                            "Don't point that at me!",
                            "I will rip that finger right off of you!",
                        ]),
        HalloweenDetector("staring", "Is anybody looking straight at the camera?",
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
            # Resize down to 800x600 to speed everything up
            frame = cv2.resize(frame, (800, 600))
            motion = motdet.motion_detected(frame)
            if motion:
                jpeg_bytes = cv2.imencode('.jpg', frame)[1].tobytes()  # Jpeg compress once for everything downstream
                save_jpeg("latest-motion", jpeg_bytes)
                if any_people.process_image(jpeg_bytes):
                    save_jpeg("latest-person", jpeg_bytes)
                    logger.info("Motion:Found people.  Checking alerts.  grab_latency={time.monotonic() - grab_time:.2f}s")
                    for detector in detectors:
                        if os.fork() == 0:
                            # Using os.fork here is a blunt hammer, but effective.
                            # We're getting some HTTP errors I think from this.  But the sub-processes just die.
                            # So it lowers recall, but doesn't break the system.
                            if detector.process_image(jpeg_bytes):
                                answer = "YES"
                                md = {
                                    "triggered_by": detector.name,
                                }
                                save_jpeg(f"latest-triggered-{detector.name}", jpeg_bytes, metadata=md)
                                save_jpeg("latest-triggered", jpeg_bytes, metadata=md)
                            else:
                                answer = "NO"
                            logger.info(f"Final {detector.name} {answer} grab_latency={time.monotonic() - grab_time:.2f}s")
                            os._exit(0)


if __name__ == "__main__":
    mainloop()
