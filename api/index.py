"""Flask app for Spotify Playlist Updater - Vercel serverless function."""

import json
import os
from datetime import datetime
from flask import Flask, render_template, redirect, request, session, url_for, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# Spotify configuration
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:5000/callback")
SPOTIFY_PLAYLIST_ID = os.environ.get("SPOTIFY_PLAYLIST_ID", "3nJHpvaovScI9N9VIgh7Qq")
SPOTIFY_SCOPES = "playlist-modify-public playlist-modify-private playlist-read-private"
KISS108_URL = "https://kiss108.iheart.com/music/top-songs/"


def get_spotify_oauth():
    """Create SpotifyOAuth instance."""
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        cache_handler=None,
        show_dialog=True
    )


def get_spotify_client():
    """Get authenticated Spotify client from session."""
    token_info = session.get("token_info")
    if not token_info:
        return None

    sp_oauth = get_spotify_oauth()

    # Check if token needs refresh
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
        session["token_info"] = token_info

    return spotipy.Spotify(auth=token_info["access_token"])


def fetch_kiss108_songs():
    """Scrape top songs from Kiss 108."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    response = requests.get(KISS108_URL, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    songs = []

    # Try multiple selectors
    track_items = soup.select('[class*="track"], [class*="song"], [class*="playlist-item"]')

    for item in track_items:
        title_elem = item.select_one('[class*="title"], [class*="song-name"], h3, h4')
        artist_elem = item.select_one('[class*="artist"], [class*="subtitle"], span')

        if title_elem and artist_elem and title_elem != artist_elem:
            song_title = title_elem.get_text(strip=True)
            artist_name = artist_elem.get_text(strip=True)
            if song_title and artist_name:
                songs.append({"title": song_title, "artist": artist_name})

    # Fallback patterns
    if not songs:
        for link in soup.select('a[href*="/artist/"], a[href*="/song/"]'):
            text = link.get_text(strip=True)
            if " - " in text:
                parts = text.split(" - ", 1)
                if len(parts) == 2:
                    songs.append({"title": parts[0].strip(), "artist": parts[1].strip()})

    # Deduplicate
    seen = set()
    unique = []
    for song in songs:
        key = (song["title"].lower(), song["artist"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(song)

    return unique


@app.route("/")
def index():
    """Dashboard home page."""
    sp = get_spotify_client()
    logged_in = sp is not None
    user_info = None
    playlist_info = None

    if logged_in:
        try:
            user_info = sp.current_user()
            playlist_info = sp.playlist(SPOTIFY_PLAYLIST_ID, fields="name,images,tracks(total)")
        except Exception:
            logged_in = False
            session.clear()

    return render_template(
        "index.html",
        logged_in=logged_in,
        user=user_info,
        playlist=playlist_info,
        playlist_id=SPOTIFY_PLAYLIST_ID
    )


@app.route("/login")
def login():
    """Redirect to Spotify login."""
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """Handle Spotify OAuth callback."""
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return render_template("error.html", message=f"Authorization failed: {error}")

    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info

    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    """Clear session and logout."""
    session.clear()
    return redirect(url_for("index"))


@app.route("/api/scrape")
def api_scrape():
    """API endpoint to fetch Kiss 108 songs."""
    try:
        songs = fetch_kiss108_songs()
        return jsonify({"success": True, "songs": songs, "count": len(songs)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/playlist")
def api_playlist():
    """Get current playlist tracks."""
    sp = get_spotify_client()
    if not sp:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    try:
        tracks = []
        offset = 0

        while True:
            results = sp.playlist_tracks(
                SPOTIFY_PLAYLIST_ID,
                offset=offset,
                limit=50,
                fields="items(track(name,artists,uri,album(images))),next"
            )

            for item in results.get("items", []):
                track = item.get("track")
                if track:
                    tracks.append({
                        "name": track["name"],
                        "artist": track["artists"][0]["name"] if track["artists"] else "Unknown",
                        "uri": track["uri"],
                        "image": track["album"]["images"][-1]["url"] if track["album"]["images"] else None
                    })

            if not results.get("next"):
                break
            offset += 50

        return jsonify({"success": True, "tracks": tracks, "count": len(tracks)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/update", methods=["POST"])
def api_update():
    """Scrape Kiss 108 and add new songs to playlist."""
    sp = get_spotify_client()
    if not sp:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    try:
        # Fetch scraped songs
        scraped = fetch_kiss108_songs()

        # Get existing playlist tracks
        existing_uris = set()
        offset = 0
        while True:
            results = sp.playlist_tracks(SPOTIFY_PLAYLIST_ID, offset=offset, limit=100, fields="items(track(uri)),next")
            for item in results.get("items", []):
                if item.get("track"):
                    existing_uris.add(item["track"]["uri"])
            if not results.get("next"):
                break
            offset += 100

        # Search and add new songs
        added = []
        not_found = []
        already_exists = []

        for song in scraped:
            query = f"track:{song['title']} artist:{song['artist']}"
            results = sp.search(q=query, type="track", limit=3)
            tracks = results.get("tracks", {}).get("items", [])

            if not tracks:
                # Relaxed search
                query = f"{song['title']} {song['artist']}"
                results = sp.search(q=query, type="track", limit=3)
                tracks = results.get("tracks", {}).get("items", [])

            if tracks:
                track = tracks[0]
                if track["uri"] in existing_uris:
                    already_exists.append({
                        "title": song["title"],
                        "artist": song["artist"],
                        "spotify_name": track["name"]
                    })
                else:
                    sp.playlist_add_items(SPOTIFY_PLAYLIST_ID, [track["uri"]])
                    existing_uris.add(track["uri"])
                    added.append({
                        "title": song["title"],
                        "artist": song["artist"],
                        "spotify_name": track["name"],
                        "uri": track["uri"]
                    })
            else:
                not_found.append(song)

        return jsonify({
            "success": True,
            "added": added,
            "already_exists": already_exists,
            "not_found": not_found,
            "summary": {
                "scraped": len(scraped),
                "added": len(added),
                "already_exists": len(already_exists),
                "not_found": len(not_found)
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# For local development
if __name__ == "__main__":
    app.run(debug=True, port=5000)
