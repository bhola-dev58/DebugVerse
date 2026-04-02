#!/bin/bash

# Build the sandbox image
echo "Building the sandbox image (debugverse-sandbox)..."
docker build -t debugverse-sandbox .

if [ $? -eq 0 ]; then
    echo "Sandbox image built successfully."
else
    echo "ERROR: Failed to build sandbox image. Make sure Docker is installed and running."
    exit 1
fi
