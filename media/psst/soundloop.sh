#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INITIAL_DELAY=${1:-10}
sleep $INITIAL_DELAY

REGULAR_DELAY=${2:-60}

while true; do
    echo "Say psst!"
    mpg123 "$SCRIPT_DIR/psst.mp3"
    echo "Sleeping $REGULAR_DELAY seconds"
    sleep $REGULAR_DELAY
done
