#!/usr/bin/env -S poetry run python
from simple_tts import *

if __name__ == "__main__":
    hello_world = make_mp3_text("Good evening girls and ghouls!")
    play_mp3(hello_world)
