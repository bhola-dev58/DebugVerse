#!/bin/bash

# Configuration
BACKEND_LOG="backend.log"
FRONTEND_LOG="frontend.log"

echo "Cleaning up existing processes on ports 8000 and 3000..."
# Attempt to kill processes on ports 8000 (backend) and 3000 (frontend)
fuser -k 8000/tcp 2>/dev/null
fuser -k 3000/tcp 2>/dev/null

echo "Running project in dev mode..."

# 1. Start the backend in the background
echo "Starting backend..."
source ./venv/bin/activate
cd backend
PYTHONPATH=.. uvicorn main:app --reload --port 8000 > "../$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
cd ..

# 2. Start the frontend in the background
echo "Starting frontend..."
if [ -d "frontend" ]; then
    cd frontend
    # Use PORT=3000 to be explicit
    PORT=3000 npm start > "../$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    cd ..
else
    echo "Frontend directory not found. Skipping frontend startup."
fi

echo "Backend PID: $BACKEND_PID"
if [ ! -z "$FRONTEND_PID" ]; then
    echo "Frontend PID: $FRONTEND_PID"
fi

echo "--------------------------------------------------"
echo "Server output is being written to '$BACKEND_LOG' and '$FRONTEND_LOG'."
echo "To view server output, run: tail -f $BACKEND_LOG"
if [ ! -z "$FRONTEND_PID" ]; then
    echo "To view frontend output, run: tail -f $FRONTEND_LOG"
fi
echo "To stop servers, run: kill $BACKEND_PID"
if [ ! -z "$FRONTEND_PID" ]; then
    echo "To stop frontend, run: kill $FRONTEND_PID"
fi
echo "--------------------------------------------------"
