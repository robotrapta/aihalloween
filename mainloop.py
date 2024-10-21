#!/usr/bin/env -S poetry run python

from functools import lru_cache
import datetime
import json
import logging
import os
import random
import signal
import sys
import time
import yaml
from pathlib import Path

from timebudget import timebudget


# Framegrab bug makes me initialize logging before it's imported
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(process)d %(levelname)s - %(message)s')

from PIL import Image
from framegrab import FrameGrabber, MotionDetector
from groundlight import Groundlight
from imgcat import imgcat
import cv2
import numpy as np

from fps import FpsDisplay
from simple_tts import make_mp3_text, play_mp3

logger = logging.getLogger(__name__)


class Debouncer:
    """Prevents events from firing too quickly.  Works across processes by using a filesystem semaphore."""
    def __init__(self, name: str, delay: float = 1.0):
        self.name = name
        self.lock_file = Path(f"/tmp/debounce-{name}")
        self.delay = delay

    def is_ready(self) -> bool:
        """Public method to check if the debouncer is ready to fire again.  Will only return True if 
        nothing else has gotten True in the last (delay) seconds."""
        if self._check_ready():
            logger.debug(f"Touching {self.lock_file}")
            # Touch the file to update its last modified time
            self.lock_file.touch()
            return True
        return False

    def _check_ready(self) -> bool:
        """Checks if the debouncer is ready to fire again based on the lock file timestamp."""
        if not self.lock_file.exists():
            logger.debug(f"Lock file {self.lock_file} does not exist")
            return True
        
        last_modified = self.lock_file.stat().st_mtime
        elapsed = time.time() - last_modified  # Use time.time() instead of time.monotonic()
        logger.debug(f"Lock file {self.lock_file} last modified {last_modified} - {elapsed}s ago")
        return elapsed > self.delay


class HalloweenDetector():
    """Creates a Groundlight detector for the given query, and whenever the detector triggers, it 
    will play a soundfile or text-to-speech message.
    """

    def __init__(self,
                 name: str,
                 query: str,
                 trigger_callback: callable = None,
                 messages: list[str] = None,
                 soundfile_dir: str = "",
                 volume: int = 100,
                 debounce_time: float = 3.0):
        self.name = name
        self.query = query
        self.trigger_callback = trigger_callback
        self.tts_choices = messages
        self.soundfile_dir = soundfile_dir
        self.volume = volume
        self.debounce_time = debounce_time

        if self.tts_choices and self.soundfile_dir:
            raise ValueError(f"Error in configuration for detector {self.name}: Cannot configure both 'messages' and 'soundfile_dir'. Please choose one.")

        self.gl = Groundlight()
        self.detector = self.gl.get_or_create_detector(
            name=self.name,
            query=self.query,
        )
        logger.info(f"Using detector {self.detector}")
        self.debouncer = Debouncer("trigger", delay=debounce_time)

    def tts_trigger(self):
        text_choices = self.tts_choices
        if not text_choices:
            logger.info("No text configured - skipping trigger")
            return
        chosen_text = random.choice(text_choices)
        logger.info(f"TTS speaking: '{chosen_text}'. Triggered by {self.detector.name}")
        audiofile = make_mp3_text(chosen_text)
        play_mp3(audiofile, volume=self.volume)

    def pick_and_play_soundfile(self, soundfile_dir: str):
        soundfiles = [f for f in os.listdir(soundfile_dir) if f.endswith('.mp3')]
        soundfile = os.path.join(soundfile_dir, random.choice(soundfiles))
        logger.info(f"Playing {soundfile}")
        play_mp3(soundfile, volume=self.volume)

    def do_trigger(self):
        if not self.debouncer.is_ready():
            logger.info(f"Debouncer is not ready - skipping trigger")
            return
        if self.trigger_callback:
            self.trigger_callback()
        elif self.soundfile_dir:
            self.pick_and_play_soundfile(self.soundfile_dir)
        else:
            self.tts_trigger()

    def process_image(self, frame: bytes | np.ndarray) -> bool:
        start_time = time.monotonic()
        iq = self.gl.ask_ml(self.detector, frame)
        elased = time.monotonic() - start_time
        logger.info(f"{self.name} got {iq.result.label} ({iq.result.confidence:.2f}) after {elased:.2f}s iq={iq.id}")
        if iq.result.label == "YES":
            self.do_trigger()
            return True
        return False

    def __str__(self):
        return f"HalloweenDetector(name={self.name}, query={self.detector.query})"

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

class Config:
    def __init__(self, file_path: str):
        with open(file_path, 'r') as file:
            self.config = yaml.safe_load(file)

    def get_motdet_params(self):
        return self.config.get('motdet_pct', 1.5), self.config.get('motdet_val', 50)

    def get_resize_dimensions(self):
        return self.config.get('resize_width', 800), self.config.get('resize_height', 600)

    def get_detectors(self):
        return self.config.get('detectors', [])

    def get_debounce_time(self):
        return self.config.get('debounce_time', 3.0)

def load_detectors_from_yaml(config: Config) -> list[HalloweenDetector]:
    detectors = []
    base_volume = config.config.get('base_volume', 100)
    debounce_time = config.get_debounce_time()  # Get debounce time from config
    for detector_config in config.get_detectors():
        # Calculate volume based on base_volume and detector-specific volume
        detector_config['volume'] = base_volume * (detector_config.get('volume', 100) / 100)
        detector_config['debounce_time'] = debounce_time  # Add debounce time to the config
        detector = HalloweenDetector(**detector_config)
        logger.info(f"Created {detector}")
        detectors.append(detector)
    return detectors

def process_detector(detector: HalloweenDetector, jpeg_bytes: bytes, grab_time: float):
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

def mainloop(config_file: str):
    logger.info(f"Loading configuration from {config_file}")
    config = Config(config_file)
    motdet_pct, motdet_val = config.get_motdet_params()
    resize_width, resize_height = config.get_resize_dimensions()

    logger.info("Initializing camera")
    grabber = FrameGrabber.from_yaml("camera.yaml")[0]
    first_frame = grabber.grab()
    save_jpeg("first-frame", first_frame)
    logger.info("Camera initialized")
    motdet = MotionDetector(motdet_pct, motdet_val)

    detectors = load_detectors_from_yaml(config)
    # A special non-configurable detector that looks for people.
    any_people = HalloweenDetector(
        "any-people", 
        "Are there any people on the sidewalk?", 
        volume=config.config.get('base_volume', 100)  # Use base_volume directly for this detector
    )

    fps_display = FpsDisplay(catch_exceptions=True, status_file=Path("status/media/fps.json"))

    while True:
        with fps_display:  # prints fps once per second
            # Get the image
            frame = grabber.grab()
            grab_time = time.monotonic()
            if frame is None:
                logger.warning("No frame captured!")
                continue
            # Resize down to configured dimensions to speed everything up
            frame = cv2.resize(frame, (resize_width, resize_height))
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
                            try:
                                process_detector(detector, jpeg_bytes, grab_time)
                            finally:
                                # Don't leak the child process back into the main loop
                                os._exit(0)

def reap_children(signum, frame):
    """Reap child processes to prevent zombies."""
    while True:
        try:
            # Wait for any child process to terminate
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
            logger.debug(f"Reaped child process with PID: {pid} status={status}")
        except ChildProcessError:
            break

if __name__ == "__main__":
    signal.signal(signal.SIGCHLD, reap_children)

    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "halloween.yaml"
    mainloop(config_file=config_file)
