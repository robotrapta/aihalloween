from pathlib import Path
import datetime
import json
import logging
import os
import time

logger = logging.getLogger(__name__)

class FpsDisplay:
    """Context manager that displays an EMA average of the FPS periodically.
    Example usage:
        fps = FpsDisplay()
        while True:
            with fps:
                img = grabber.grab()
                process_image(img)
    """

    def __init__(self, ema_alpha:float=0.1, display_every_secs:float=1.0, catch_exceptions:bool=False, status_file:Path=None):
        self.last_msg_time = time.monotonic()
        self.ema_fps = 0
        self.ema_alpha = ema_alpha
        self.display_every_secs = display_every_secs
        self.catch_exceptions = catch_exceptions
        self.exception_delay = 5.0
        self.status_file = status_file

    def __enter__(self):
        self.start_time = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.catch_exceptions and exc_type is not None:
            if issubclass(exc_type, KeyboardInterrupt):
                raise
            logger.error(f"Exception {exc_type.__name__}: {exc_value}. Pausing for {self.exception_delay} seconds before continuing.", exc_info=(exc_type, exc_value, traceback))
            # TODO: Maybe some kind of backoff?
            time.sleep(self.exception_delay)
            return True  # Prevent the exception from being propagated
        elapsed = time.monotonic() - self.start_time
        self.tick(elapsed)

    def tick(self, elapsed:float):
        current_fps = 1.0 / elapsed

        if self.ema_fps == 0:
            self.ema_fps = current_fps
        else:
            self.ema_fps = self.ema_alpha * current_fps + (1 - self.ema_alpha) * self.ema_fps

        if time.monotonic() - self.last_msg_time >= self.display_every_secs:
            logger.info(f"average recent fps={self.ema_fps:.2f}")
            self.last_msg_time = time.monotonic()
            if self.status_file:
                doc = {
                    "fps": self.ema_fps,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "pid": os.getpid(),
                }
                self.status_file.write_text(json.dumps(doc))
