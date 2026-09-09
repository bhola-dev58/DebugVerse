#!/bin/bash

echo "Stopping DebugVerse..."

# 1. Kill tracked PIDs
if [ -f .pids ]; then
    while read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "Killing tracked process $pid..."
            kill "$pid" 2>/dev/null
        fi
    done < .pids
    rm -f .pids
fi

# 2. Kill by port if any linger
for port in 8000 8001 3000 3001; do
    fuser -k "${port}/tcp" 2>/dev/null
done

# 3. Clean up log files
rm -f backend.log frontend.log

echo "DebugVerse stopped and cleaned up."
