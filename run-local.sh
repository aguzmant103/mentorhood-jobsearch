#!/bin/bash

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 is required but not found. Please install Python 3.11"
    exit 1
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment with Python 3.11..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 