# FaceScream - a spooky halloween vision project

## System Setup

Install poetry if you haven't:

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/home/ubuntu/.local/bin:$PATH"
```

And if you're on Ubuntu, make sure you have `libGL.so` the right prerequisites installed:

```bash
sudo apt install libgl1-mesa-glx ffmpeg
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

### Troubleshooting

If poetry is getting stuck, try

```
export PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring
```

([ref](https://github.com/python-poetry/poetry/issues/1917))

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
