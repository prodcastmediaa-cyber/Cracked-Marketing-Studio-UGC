#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/bot.log"
PID_FILE="$DIR/.bot.pid"

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Bot is already running (PID $OLD_PID). Use stop_bot.sh first."
        exit 1
    fi
fi

echo "Starting UGC bot..."
nohup python3 "$DIR/bot.py" >> "$LOG" 2>&1 &
echo $! > "$PID_FILE"
echo "Bot started (PID $(cat "$PID_FILE")). Logs: tail -f $LOG"
