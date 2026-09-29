#!/usr/bin/env python3
"""
Spotify Playlist Updater

Scrapes Kiss 108 Top Songs and adds new songs to a Spotify playlist.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from config import validate_config, SPOTIFY_PLAYLIST_ID, ADDED_SONGS_FILE
from scraper import fetch_top_songs
from spotify_client import SpotifyClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def load_added_songs() -> dict:
    """Load the record of previously added songs."""
    if ADDED_SONGS_FILE.exists():
        try:
            with open(ADDED_SONGS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load added songs file: {e}")
    return {"songs": {}, "last_updated": None}


def save_added_songs(data: dict) -> None:
    """Save the record of added songs."""
    data["last_updated"] = datetime.now().isoformat()
    with open(ADDED_SONGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def make_song_key(title: str, artist: str) -> str:
    """Create a normalized key for a song."""
    return f"{title.lower().strip()}|{artist.lower().strip()}"


def main():
    """Main entry point for the playlist updater."""
    logger.info("=" * 50)
    logger.info("Starting Spotify Playlist Updater")
    logger.info("=" * 50)

    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Load state
    added_songs_data = load_added_songs()
    added_songs = added_songs_data.get("songs", {})

    # Fetch songs from Kiss 108
    try:
        scraped_songs = fetch_top_songs()
    except Exception as e:
        logger.error(f"Failed to scrape songs: {e}")
        sys.exit(1)

    if not scraped_songs:
        logger.warning("No songs found on Kiss 108 page")
        sys.exit(0)

    logger.info(f"Scraped {len(scraped_songs)} songs from Kiss 108")

    # Initialize Spotify client
    try:
        spotify = SpotifyClient()
    except Exception as e:
        logger.error(f"Failed to initialize Spotify client: {e}")
        sys.exit(1)

    # Verify playlist access
    if not spotify.verify_playlist_access(SPOTIFY_PLAYLIST_ID):
        logger.error("Cannot access the specified playlist")
        sys.exit(1)

    # Get existing playlist tracks
    existing_tracks = spotify.get_playlist_tracks(SPOTIFY_PLAYLIST_ID)

    # Process each scraped song
    new_tracks_to_add = []
    songs_processed = []

    for title, artist in scraped_songs:
        song_key = make_song_key(title, artist)

        # Skip if already processed
        if song_key in added_songs:
            logger.debug(f"Skipping (already processed): {title} - {artist}")
            continue

        # Search on Spotify
        track_uri = spotify.search_track(title, artist)

        if track_uri:
            # Check if already in playlist
            if track_uri in existing_tracks:
                logger.info(f"Already in playlist: {title} - {artist}")
                added_songs[song_key] = {
                    "title": title,
                    "artist": artist,
                    "track_uri": track_uri,
                    "status": "already_in_playlist",
                    "date": datetime.now().isoformat()
                }
            else:
                logger.info(f"New song to add: {title} - {artist}")
                new_tracks_to_add.append(track_uri)
                songs_processed.append((title, artist, track_uri))
        else:
            logger.warning(f"Not found on Spotify: {title} - {artist}")
            added_songs[song_key] = {
                "title": title,
                "artist": artist,
                "track_uri": None,
                "status": "not_found",
                "date": datetime.now().isoformat()
            }

    # Add new tracks to playlist
    if new_tracks_to_add:
        added_count = spotify.add_tracks_to_playlist(SPOTIFY_PLAYLIST_ID, new_tracks_to_add)
        logger.info(f"Successfully added {added_count} new tracks to playlist")

        # Update state for successfully added songs
        for title, artist, track_uri in songs_processed:
            song_key = make_song_key(title, artist)
            added_songs[song_key] = {
                "title": title,
                "artist": artist,
                "track_uri": track_uri,
                "status": "added",
                "date": datetime.now().isoformat()
            }
    else:
        logger.info("No new tracks to add")

    # Save state
    added_songs_data["songs"] = added_songs
    save_added_songs(added_songs_data)

    # Summary
    logger.info("=" * 50)
    logger.info("Summary:")
    logger.info(f"  Songs scraped: {len(scraped_songs)}")
    logger.info(f"  New songs added: {len(new_tracks_to_add)}")
    logger.info(f"  Total songs tracked: {len(added_songs)}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
