#!/bin/bash

echo "Starting project setup..."

# 1. Create a Python virtual environment in the root directory
echo "Creating Python virtual environment 'venv' in root..."
python3 -m venv venv

if [ $? -eq 0 ]; then
    echo "Virtual environment created successfully."
else
    echo "ERROR: Failed to create virtual environment. Ensure you have 'python3-venv' installed."
    exit 1
fi

# 2. Activate the environment and install backend dependencies
echo "Installing backend dependencies using the root venv..."
./venv/bin/pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "Backend dependencies installed successfully."
else
    echo "ERROR: Failed to install backend dependencies."
    exit 1
fi

# 3. Setup frontend dependencies (optional, but makes it truly runnable)
echo "Setting up frontend dependencies..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    if [ $? -eq 0 ]; then
        echo "Frontend dependencies installed successfully."
    else
        echo "ERROR: Failed to install frontend dependencies. Ensure node/npm are installed."
        cd ..
        # We don't exit here as the backend part is already set up
    fi
    cd ..
else
    echo "Frontend directory not found. Skipping frontend installation."
fi

echo "--------------------------------------------------"
echo "Setup complete!"
echo "To run the backend: source venv/bin/activate && cd backend && uvicorn main:app --reload"
echo "To run the frontend: cd frontend && npm start"
echo "--------------------------------------------------"
