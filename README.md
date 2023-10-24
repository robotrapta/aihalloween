# FaceScream - a spooky halloween vision project

## Setup

Install poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Install dependencies

```bash
poetry install
```

### Camera setup

Check the default camera configuration.

```
framegrab preview ./camera.yaml
```

If that doesn't work, try `framegrab autodiscover` to find the camera and update `camera.yaml`

## Running

