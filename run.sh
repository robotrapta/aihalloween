#!/bin/bash

cd "$(dirname "$0")"

# Set up configuration
if [ -f ~/.groundlight/endpoint ]; then
    source ~/.groundlight/endpoint
fi
source ~/.groundlight/api-token

# Run
poetry run python screamer.py
