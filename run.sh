#!/bin/bash

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

BACKEND_LOG="$PROJECT_DIR/backend.log"
FRONTEND_LOG="$PROJECT_DIR/frontend.log"
PID_FILE="$PROJECT_DIR/.pids"

# Function to check if a port is in use
is_port_in_use() {
    nc -z 127.0.0.1 "$1" 2>/dev/null || (echo > /dev/tcp/127.0.0.1/"$1") 2>/dev/null
}

# Determine Backend Port
if [ -n "$BACKEND_PORT" ]; then
    B_PORT="$BACKEND_PORT"
elif is_port_in_use 8000; then
    echo "Notice: Port 8000 is currently occupied. Using port 8001 for Backend."
    B_PORT=8001
else
    B_PORT=8000
fi

# Determine Frontend Port
if [ -n "$FRONTEND_PORT" ]; then
    F_PORT="$FRONTEND_PORT"
elif is_port_in_use 3000; then
    echo "Notice: Port 3000 is currently occupied. Using port 3001 for Frontend."
    F_PORT=3001
else
    F_PORT=3000
fi

echo "Cleaning up any old DebugVerse background processes..."
if [ -f "$PID_FILE" ]; then
    while read -r p; do
        [ -n "$p" ] && kill "$p" 2>/dev/null
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi

echo "Starting DebugVerse in development mode..."
echo "  Backend port  : $B_PORT"
echo "  Frontend port : $F_PORT"
echo "  Backend API   : http://localhost:$B_PORT"

# 1. Start the backend
echo "Starting backend..."
source ./venv/bin/activate
env PORT="$B_PORT" PYTHONPATH=. ./venv/bin/uvicorn backend.main:app --reload --port "$B_PORT" --host 0.0.0.0 > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" >> "$PID_FILE"

# 2. Start the frontend
if [ -d "frontend" ]; then
    echo "Starting frontend..."
    cd frontend || exit 1
    env BROWSER=none PORT="$F_PORT" REACT_APP_API_URL="http://localhost:$B_PORT" npm start > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    cd "$PROJECT_DIR" || exit 1
    echo "$FRONTEND_PID" >> "$PID_FILE"
else
    echo "Frontend directory not found. Skipping frontend startup."
fi

echo ""
echo "=================================================="
echo " DebugVerse is running!"
echo "   Frontend UI : http://localhost:$F_PORT"
echo "   Backend API : http://localhost:$B_PORT"
echo "   Backend Docs: http://localhost:$B_PORT/docs"
echo "=================================================="
echo "Logs are being written to:"
echo "   Backend  : tail -f backend.log"
if [ -n "$FRONTEND_PID" ]; then
    echo "   Frontend : tail -f frontend.log"
fi
echo "=================================================="

# Check for background flag
if [ "$1" = "--background" ] || [ "$1" = "-d" ]; then
    echo "Servers running in background mode."
    echo "To stop DebugVerse, run: ./kill_ports.sh"
else
    echo "Press Ctrl+C to stop both servers..."
    trap 'echo ""; echo "Shutting down DebugVerse..."; kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null; rm -f "$PID_FILE"; exit 0' INT TERM
    wait
fi
