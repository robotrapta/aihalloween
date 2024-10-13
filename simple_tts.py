import os

from gtts import gTTS

AUDIO_DIR = "./audio/"

def make_mp3_text(text:str) -> str:
    fn = "".join([c if c.isalnum() else "_" for c in text]) + ".mp3"
    fn = os.path.join(AUDIO_DIR, fn)

    try:  # check if the file already exists
        with open(fn, "r") as f:
            return fn
    except FileNotFoundError:
        pass
    tts = gTTS(text)
    print(f"Generating {fn} to say '{text}'")
    tts.save(fn)
    return fn

def play_mp3(fn: str, volume: int = 100) -> None:
    # Use the -af option to apply a volume filter
    os.system(f"ffplay -autoexit -nodisp -af 'volume={volume/100.0}' {fn}")
