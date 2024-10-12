#!/bin/bash

echo "Starting Halloween services in tmux"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PATH=/usr/bin/:$HOME/.local/bin/poetry:$PATH

cd "$SCRIPT_DIR"
# Make sure the `cd` worked
if [ $? -ne 0 ]; then
    echo "Failed to cd to $SCRIPT_DIR"
    exit 1
fi

if [ -n "$REINSTALL" ]; then
    git pull origin main
    poetry install
fi

poetry run python check-audio.py
tmux new-session -d -s aihalloween "$SCRIPT_DIR/run.sh; bash"
tmux new-session -d -s psst "$SCRIPT_DIR/media/psst/soundloop.sh"
# Launch the web server
tmux new-session -d -s web "$SCRIPT_DIR/serve-status.sh"

