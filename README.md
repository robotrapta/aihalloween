# AI Halloween - A Spooky Computer Vision Project

This is Jacqueline.  She watches everybody walking by, and if she seems something interesting, she'll react.

![Jacqueline](media/jacqueline.jpeg)

It's super simple to adjust what she reacts to, but currently she's programmed to react to:

- **Dogs** - She'll make a snarky comment, or maybe play some animal noises.
- **Baby Strollers** - She'll say something slightly menacing like "Ooooh a baby!"
- **People taking photos** - She will make a snarky comment.
- **People pointing at her** - She will make a snarky comment.
- **People staring at her** - She will say Hi.

Last year if she got really riled up she'd blast you with a fog machine (DMX-controlled) but it seems I forgot to push that code to github after halloween, so it's lost on some micro-SD card somewhere in my house.  I'll just rewrite it.

## YAML Configuration

The behavior of Jacqueline is configured using a YAML file. Each detector is defined with a set of properties that determine what it reacts to and how it responds. Below is the format of the YAML configuration:

```
base_volume: 400  # Turn up volume for everything to 400%

detectors:
  - name: "doggie"
    query: "Are there any dogs in view?"
    soundfile_dir: "sounds/dogs"
    volume: 60   # Turn down volume for dog noises.

  - name: "baby-stroller"
    query: "Is there a baby stroller in view?"
    soundfile_dir: "sounds/babies"
    # No specific volume, uses base_volume

  - name: "taking-photo"
    query: "Is someone taking a photo?"
    messages:
      - "Say cheese!"
      - "My hashtag is A.I. Halloween"
    volume: 200  # Turn up volume for taking voice
```

### YAML Fields

System-wide:
- **base_volume**: A global volume setting that scales the volume for all detectors. It is a 100-based scale, where "100" means normal volume, "150" means 1.5 times the normal volume, etc.
- **motdet_pct**: The percentage threshold for motion detection sensitivity. This value is used to determine how much of the frame must change to trigger motion detection.
- **motdet_val**: The value threshold for motion detection. This is used to determine the intensity of change required to trigger motion detection.
- **resize_width**: The width to which frames are resized for processing. This helps in speeding up the processing by reducing the frame size.
- **resize_height**: The height to which frames are resized for processing.


Per-detector:
- **name**: A descriptive name for the detector.
- **query**: The query text used to identify the object or action in the frame.
- **soundfile_dir**: The directory path where sound files related to the detector are stored. If provided, Jacqueline will randomly choose one of the files in the directory to play when the detector is triggered.
- **messages**: A list of messages that Jacqueline can say when the detector is triggered. These will be rendered as a voice. Messages are only used if there is no `soundfile_dir`.
- **volume**: (Optional) A specific volume setting for the detector, which multiplies on top of the `base_volume`. It is also a 100-based scale.

## System Setup

Install poetry if you haven't:

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

Make sure you have the right prerequisites installed.  For Ubuntu:

```bash
sudo apt install -y libgl1-mesa-glx ffmpeg tmux
```

Install python dependencies

```bash
poetry install
```

### Camera setup

Create a default camera config and confirm that it works.

```
poetry run framegrab autodiscover > camera.yaml
poetry run framegrab preview ./camera.yaml
```

### Running automatically

Add something like this to your crontab:
(Update the directory to be what you think it should be.)

```
@reboot $HOME/aihalloween/onboot.sh
```

Cron can be tricky.  You likely want a line like this to set the `PATH` correctly: 
(Update the username if you're not using `ubuntu`) 

```
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/home/ubuntu/.local/bin/
```

## Running

Get a [Groundlight API token](https://code.groundlight.ai/python-sdk/docs/getting-started/api-tokens)
and set it as an environment variable like

```bash
export GROUNDLIGHT_API_TOKEN=api_2Q...
```

Then run

```bash
poetry run python ./mainloop.py ./halloween.yaml
```

### What to do?

Try taking a picture of the camera, or pointing at it, or just staring.

## Monitoring

There's a simple web server running on the machine that will show you the latest images.  Just open a web browser and go to http://your-machine-ip:8000/

It will show you the most recent images of various categories (triggered, motion detection, person) and if things are working properly, automatically reload them as new images come in.

<img src="media/web-monitor.jpg" alt="Web Monitoring Interface" style="max-width: 600px;">


