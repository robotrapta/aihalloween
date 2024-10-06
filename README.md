# FaceScreamer - A Spooky Halloween Computer Vision Project

## System Setup

Install poetry if you haven't:

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/home/ubuntu/.local/bin:$PATH"
```

And if you're on Ubuntu, make sure you have the right prerequisites installed:

```bash
sudo apt install -y libgl1-mesa-glx ffmpeg tmux
```


Install dependencies

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
@reboot /home/ubuntu/facescreamer/onboot.sh
```

## Running

Get a [Groundlight API token](https://code.groundlight.ai/python-sdk/docs/getting-started/api-tokens)
and set it as an environment variable like

```bash
export GROUNDLIGHT_API_TOKEN=api_2Q...
```

Then run

```bash
poetry run python ./screamer.py
```

### What to do?

Try looking at the camera and sticking out your tongue.
