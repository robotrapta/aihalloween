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

