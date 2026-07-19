#!/bin/bash

# Configuration
REPO_DIR="/home/cy/ntfy-self-hosted"
VENV_DIR="$REPO_DIR/venv"

echo "Deploying ntfy-self-hosted monitors..."

# Ensure directory exists (Assuming code is already copied or cloned here)
mkdir -p "$REPO_DIR"

# Navigate to project directory
cd "$REPO_DIR" || exit

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Install requirements
echo "Installing requirements..."
"$VENV_DIR/bin/pip" install -r requirements.txt

# Setup Cron Jobs dynamically using setup_cron.py
echo "Configuring cron jobs..."
"$VENV_DIR/bin/python" setup_cron.py

echo "Deployment complete! Scrapers are now scheduled with a 10-minute offset."
