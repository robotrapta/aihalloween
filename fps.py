import time
import logging

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

    def __init__(self, ema_alpha:float=0.1, display_every_secs:float=1.0):
        self.last_msg_time = time.monotonic()
        self.ema_fps = 0
        self.ema_alpha = ema_alpha
        self.display_every_secs = display_every_secs

    def __enter__(self):
        self.start_time = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        elapsed = time.monotonic() - self.start_time
        self.tick(elapsed)

    def tick(self, elapsed:float):
        current_fps = 1.0 / elapsed

        if self.ema_fps == 0:
            self.ema_fps = current_fps
        else:
            self.ema_fps = self.ema_alpha * current_fps + (1 - self.ema_alpha) * self.ema_fps

        if time.monotonic() - self.last_msg_time >= self.display_every_secs:
            logger.info(f"fps={self.ema_fps:.2f}")
            self.last_msg_time = time.monotonic()
