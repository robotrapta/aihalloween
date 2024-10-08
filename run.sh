#!/bin/bash

export PATH="$PATH:$HOME/.local/bin/poetry"

cd "$(dirname "$0")"

# Set up configuration
if [ -f ~/.groundlight/endpoint ]; then
    source ~/.groundlight/endpoint
fi
if [ -f ~/.groundlight/api-token ]; then
    source ~/.groundlight/api-token
fi

poetry run groundlight whoami
if [ $? -ne 0 ]; then
    echo "Failed to get Groundlight API token"
    exit 1
fi

# Run
poetry run python mainloop.py
