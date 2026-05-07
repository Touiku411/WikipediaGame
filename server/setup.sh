#!/usr/bin/fish

if [ -d ".venv" ]; then
    rm -rf .venv
fi

# Create the virtual environment
python3.10 -m venv .venv

# Activate the virtual environment
source venv/bin/activate

# Install the dependencies
pip install -r requirements.txt
