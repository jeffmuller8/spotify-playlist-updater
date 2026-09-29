"""Configuration loading for Spotify Playlist Updater."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
SPOTIFY_PLAYLIST_ID = os.getenv("SPOTIFY_PLAYLIST_ID", "3nJHpvaovScI9N9VIgh7Qq")

# Spotify API scopes needed
SPOTIFY_SCOPES = "playlist-modify-public playlist-modify-private playlist-read-private"

# Kiss 108 Top Songs URL
KISS108_URL = "https://kiss108.iheart.com/music/top-songs/"

# File paths
PROJECT_DIR = Path(__file__).parent
ADDED_SONGS_FILE = PROJECT_DIR / "added_songs.json"
CACHE_PATH = PROJECT_DIR / ".spotify_cache"


def validate_config():
    """Validate that required configuration is present."""
    missing = []
    if not SPOTIFY_CLIENT_ID:
        missing.append("SPOTIFY_CLIENT_ID")
    if not SPOTIFY_CLIENT_SECRET:
        missing.append("SPOTIFY_CLIENT_SECRET")

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please copy .env.example to .env and fill in your credentials."
        )
