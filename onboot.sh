#!/bin/bash

echo "Starting Halloween services in tmux"

export PATH=/usr/bin/:/home/ubuntu/.local/bin/poetry:$PATH

cd /home/ubuntu/hdev/facescreamer
git pull origin main
poetry install
poetry run python check-audio.py
tmux new-session -d -s facescreamer '/home/ubuntu/hdev/facescreamer/run.sh; bash'

