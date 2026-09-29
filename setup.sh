#!/bin/bash
# Setup script for Spotify Playlist Updater

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================="
echo "Spotify Playlist Updater Setup"
echo "=================================="
echo

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Install dependencies
echo
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env with your Spotify credentials"
    echo
    echo "To get your credentials:"
    echo "1. Go to https://developer.spotify.com/dashboard"
    echo "2. Create a new app"
    echo "3. Set redirect URI to: http://localhost:8888/callback"
    echo "4. Copy Client ID and Client Secret to .env"
else
    echo
    echo ".env file already exists"
fi

# Make main script executable
chmod +x update_playlist.py

echo
echo "=================================="
echo "Setup complete!"
echo "=================================="
echo
echo "Next steps:"
echo "1. Edit .env with your Spotify credentials"
echo "2. Run: python3 update_playlist.py"
echo "3. Authorize the app in your browser"
echo
echo "See SETUP.md for detailed instructions."
