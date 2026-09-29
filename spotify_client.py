"""Spotify API client wrapper using spotipy."""

import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    SPOTIFY_SCOPES,
    CACHE_PATH,
)

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Wrapper for Spotify API operations."""

    def __init__(self):
        """Initialize the Spotify client with OAuth authentication."""
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=SPOTIFY_SCOPES,
                cache_path=str(CACHE_PATH),
            )
        )
        self._user_id = None

    @property
    def user_id(self) -> str:
        """Get the current user's Spotify ID."""
        if self._user_id is None:
            self._user_id = self.sp.current_user()["id"]
        return self._user_id

    def search_track(self, song_title: str, artist_name: str) -> str | None:
        """
        Search for a track on Spotify.

        Args:
            song_title: The song title to search for
            artist_name: The artist name to search for

        Returns:
            Spotify track URI if found, None otherwise
        """
        # Clean up search terms
        query = f"track:{song_title} artist:{artist_name}"

        try:
            results = self.sp.search(q=query, type="track", limit=5)
            tracks = results.get("tracks", {}).get("items", [])

            if not tracks:
                # Try a more relaxed search
                query = f"{song_title} {artist_name}"
                results = self.sp.search(q=query, type="track", limit=5)
                tracks = results.get("tracks", {}).get("items", [])

            if tracks:
                # Return the first match
                track = tracks[0]
                logger.debug(f"Found: {track['name']} by {track['artists'][0]['name']}")
                return track["uri"]

            logger.warning(f"No match found for: {song_title} - {artist_name}")
            return None

        except Exception as e:
            logger.error(f"Error searching for {song_title} - {artist_name}: {e}")
            return None

    def get_playlist_tracks(self, playlist_id: str) -> set[str]:
        """
        Get all track URIs currently in a playlist.

        Args:
            playlist_id: The Spotify playlist ID

        Returns:
            Set of track URIs in the playlist
        """
        track_uris = set()
        offset = 0
        limit = 100

        while True:
            try:
                results = self.sp.playlist_tracks(
                    playlist_id,
                    offset=offset,
                    limit=limit,
                    fields="items(track(uri)),next"
                )

                items = results.get("items", [])
                for item in items:
                    track = item.get("track")
                    if track and track.get("uri"):
                        track_uris.add(track["uri"])

                if not results.get("next"):
                    break

                offset += limit

            except Exception as e:
                logger.error(f"Error fetching playlist tracks: {e}")
                break

        logger.info(f"Playlist contains {len(track_uris)} tracks")
        return track_uris

    def add_tracks_to_playlist(self, playlist_id: str, track_uris: list[str]) -> int:
        """
        Add tracks to a playlist.

        Args:
            playlist_id: The Spotify playlist ID
            track_uris: List of track URIs to add

        Returns:
            Number of tracks successfully added
        """
        if not track_uris:
            return 0

        added_count = 0
        # Spotify API limits to 100 tracks per request
        batch_size = 100

        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i + batch_size]
            try:
                self.sp.playlist_add_items(playlist_id, batch)
                added_count += len(batch)
                logger.info(f"Added {len(batch)} tracks to playlist")
            except Exception as e:
                logger.error(f"Error adding tracks to playlist: {e}")

        return added_count

    def verify_playlist_access(self, playlist_id: str) -> bool:
        """
        Verify that we have access to modify the playlist.

        Args:
            playlist_id: The Spotify playlist ID

        Returns:
            True if we have access, False otherwise
        """
        try:
            playlist = self.sp.playlist(playlist_id, fields="id,name,owner(id)")
            owner_id = playlist.get("owner", {}).get("id")

            if owner_id == self.user_id:
                logger.info(f"Verified access to playlist: {playlist.get('name')}")
                return True

            # Check if it's a collaborative playlist
            playlist_full = self.sp.playlist(playlist_id, fields="collaborative")
            if playlist_full.get("collaborative"):
                logger.info(f"Access to collaborative playlist: {playlist.get('name')}")
                return True

            logger.warning(f"No write access to playlist owned by {owner_id}")
            return False

        except Exception as e:
            logger.error(f"Error verifying playlist access: {e}")
            return False
