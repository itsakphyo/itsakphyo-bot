#!/bin/bash

# Development start script
echo "Starting Itsakphyo Bot in development mode..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from example..."
    cp .env.example .env
    echo "Please edit .env with your bot token and configuration"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Start the application
echo "Starting application..."
python main.py
