#!/bin/bash

# Kill processes on port 8000 (Backend)
echo "Killing processes on port 8000..."
fuser -k 8000/tcp || echo "No process on port 8000."

# Kill processes on port 3000 (Frontend)
echo "Killing processes on port 3000..."
fuser -k 3000/tcp || echo "No process on port 3000."

echo "Cleaning up log files..."
rm -f backend.log frontend.log

echo "Done!"
