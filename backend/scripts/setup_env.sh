#!/bin/bash

# Create and activate virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment based on OS
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please update the .env file with your Azure credentials."
fi

echo "Environment setup complete. Activate the virtual environment with:"
echo "source venv/bin/activate  # Linux/Mac"
echo "venv\\Scripts\\activate    # Windows"