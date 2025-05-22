#!/bin/bash
cd ~/tmp
cp error.png saturday.png
cp error.png sunday.png

MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    python3 ~/bin/get_weather_mountain.py -dw
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        break
    else
        RETRY_COUNT=$((RETRY_COUNT+1))
        echo "retry...$RETRY_COUNT/$MAX_RETRIES"
        sleep 1
    fi
done
