#!/bin/bash

export PATH="$PATH:/home/ubuntu/.local/bin/poetry"

cd "$(dirname "$0")"

# Set up configuration
if [ -f ~/.groundlight/endpoint ]; then
    source ~/.groundlight/endpoint
fi
source ~/.groundlight/api-token

# Run
poetry run python screamer.py &
poetry run python baby.py &
poetry run python dog.py &
