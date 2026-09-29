"""Flask app for Spotify Playlist Updater - Vercel serverless function."""

import os
from flask import Flask, redirect, request, session, jsonify, make_response
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

# Spotify configuration
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:5000/callback")
SPOTIFY_PLAYLIST_ID = os.environ.get("SPOTIFY_PLAYLIST_ID", "3nJHpvaovScI9N9VIgh7Qq")
SPOTIFY_SCOPES = "playlist-modify-public playlist-modify-private playlist-read-private"
KISS108_URL = "https://kiss108.iheart.com/music/top-songs/"


def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        cache_handler=None,
        show_dialog=True
    )


def get_spotify_client():
    token_info = session.get("token_info")
    if not token_info:
        return None
    sp_oauth = get_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
        session["token_info"] = token_info
    return spotipy.Spotify(auth=token_info["access_token"])


def fetch_kiss108_songs():
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    response = requests.get(KISS108_URL, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    songs = []

    track_items = soup.select('[class*="track"], [class*="song"], [class*="playlist-item"]')
    for item in track_items:
        title_elem = item.select_one('[class*="title"], [class*="song-name"], h3, h4')
        artist_elem = item.select_one('[class*="artist"], [class*="subtitle"], span')
        if title_elem and artist_elem and title_elem != artist_elem:
            song_title = title_elem.get_text(strip=True)
            artist_name = artist_elem.get_text(strip=True)
            if song_title and artist_name:
                songs.append({"title": song_title, "artist": artist_name})

    if not songs:
        for link in soup.select('a[href*="/artist/"], a[href*="/song/"]'):
            text = link.get_text(strip=True)
            if " - " in text:
                parts = text.split(" - ", 1)
                if len(parts) == 2:
                    songs.append({"title": parts[0].strip(), "artist": parts[1].strip()})

    seen = set()
    unique = []
    for song in songs:
        key = (song["title"].lower(), song["artist"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(song)
    return unique


def render_page(content, title="Kiss 108 Playlist Updater"):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: #fff; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 2rem; }}
        header {{ text-align: center; margin-bottom: 2rem; }}
        header h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #888; font-size: 1rem; }}
        .card {{ background: rgba(255,255,255,0.05); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid rgba(255,255,255,0.1); }}
        .login-card {{ text-align: center; padding: 3rem; }}
        .login-card p {{ color: #888; margin-bottom: 1.5rem; }}
        .btn {{ display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1.5rem; border-radius: 50px; font-size: 1rem; font-weight: 600; text-decoration: none; border: none; cursor: pointer; transition: transform 0.2s; }}
        .btn:hover {{ transform: translateY(-2px); }}
        .btn-spotify {{ background: #1DB954; color: #fff; }}
        .btn-primary {{ background: #4a6cf7; color: #fff; }}
        .btn-success {{ background: #1DB954; color: #fff; }}
        .btn-small {{ padding: 0.5rem 1rem; font-size: 0.875rem; }}
        .user-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 12px; }}
        .user-info {{ display: flex; align-items: center; gap: 0.75rem; }}
        .avatar {{ width: 40px; height: 40px; border-radius: 50%; }}
        .playlist-info {{ display: flex; gap: 1.5rem; align-items: center; }}
        .playlist-cover {{ width: 100px; height: 100px; border-radius: 8px; }}
        .playlist-info h3 {{ margin-bottom: 0.25rem; }}
        .playlist-info p {{ color: #888; margin-bottom: 0.75rem; }}
        .actions {{ display: flex; gap: 1rem; justify-content: center; margin-bottom: 1.5rem; flex-wrap: wrap; }}
        .results-panel {{ background: rgba(255,255,255,0.05); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1); }}
        .hidden {{ display: none !important; }}
        .song-list {{ list-style: none; max-height: 400px; overflow-y: auto; }}
        .song-item {{ display: flex; align-items: center; gap: 1rem; padding: 0.75rem; border-radius: 8px; }}
        .song-item:hover {{ background: rgba(255,255,255,0.05); }}
        .song-details {{ flex: 1; }}
        .song-title {{ font-weight: 500; }}
        .song-artist {{ color: #888; font-size: 0.875rem; }}
        .badge {{ padding: 0.25rem 0.75rem; border-radius: 50px; font-size: 0.75rem; font-weight: 600; }}
        .badge-added {{ background: rgba(29,185,84,0.2); color: #1DB954; }}
        .badge-exists {{ background: rgba(255,193,7,0.2); color: #ffc107; }}
        .badge-notfound {{ background: rgba(255,82,82,0.2); color: #ff5252; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }}
        .summary-item {{ text-align: center; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; }}
        .summary-item .number {{ font-size: 2rem; font-weight: 700; }}
        .summary-item .label {{ color: #888; font-size: 0.875rem; }}
        .loading {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 1000; }}
        .spinner {{ width: 50px; height: 50px; border: 3px solid rgba(255,255,255,0.1); border-top-color: #1DB954; border-radius: 50%; animation: spin 1s linear infinite; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .section-title {{ margin: 1.5rem 0 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.1); }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Kiss 108 Playlist Updater</h1>
            <p class="subtitle">Automatically add top songs to your Spotify playlist</p>
        </header>
        {content}
    </div>
    <div id="loading" class="loading hidden">
        <div class="spinner"></div>
        <p id="loadingText" style="margin-top:1rem">Loading...</p>
    </div>
    <script>
        function showLoading(text) {{
            document.getElementById('loadingText').textContent = text;
            document.getElementById('loading').classList.remove('hidden');
        }}
        function hideLoading() {{
            document.getElementById('loading').classList.add('hidden');
        }}
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        const scrapeBtn = document.getElementById('scrapeBtn');
        const updateBtn = document.getElementById('updateBtn');
        const resultsPanel = document.getElementById('results');

        if (scrapeBtn) {{
            scrapeBtn.addEventListener('click', async () => {{
                showLoading('Fetching Kiss 108 top songs...');
                try {{
                    const response = await fetch('/api/scrape');
                    const data = await response.json();
                    hideLoading();
                    if (data.success) {{
                        let html = '<p style="margin-bottom:1rem;color:#888;">Found ' + data.count + ' songs</p><ul class="song-list">';
                        data.songs.forEach((song, i) => {{
                            html += '<li class="song-item"><span style="color:#888;width:24px;">' + (i+1) + '</span><div class="song-details"><div class="song-title">' + escapeHtml(song.title) + '</div><div class="song-artist">' + escapeHtml(song.artist) + '</div></div></li>';
                        }});
                        html += '</ul>';
                        resultsPanel.innerHTML = '<h2>Kiss 108 Top Songs</h2>' + html;
                        resultsPanel.classList.remove('hidden');
                    }} else {{
                        alert('Error: ' + data.error);
                    }}
                }} catch (err) {{
                    hideLoading();
                    alert('Failed: ' + err.message);
                }}
            }});
        }}

        if (updateBtn) {{
            updateBtn.addEventListener('click', async () => {{
                showLoading('Updating playlist...');
                try {{
                    const response = await fetch('/api/update', {{ method: 'POST' }});
                    const data = await response.json();
                    hideLoading();
                    if (data.success) {{
                        let html = '<div class="summary">';
                        html += '<div class="summary-item"><div class="number">' + data.summary.scraped + '</div><div class="label">Scraped</div></div>';
                        html += '<div class="summary-item"><div class="number" style="color:#1DB954">' + data.summary.added + '</div><div class="label">Added</div></div>';
                        html += '<div class="summary-item"><div class="number" style="color:#ffc107">' + data.summary.already_exists + '</div><div class="label">Exists</div></div>';
                        html += '<div class="summary-item"><div class="number" style="color:#ff5252">' + data.summary.not_found + '</div><div class="label">Not Found</div></div>';
                        html += '</div>';
                        if (data.added.length > 0) {{
                            html += '<h3 class="section-title">Added</h3><ul class="song-list">';
                            data.added.forEach(s => {{
                                html += '<li class="song-item"><div class="song-details"><div class="song-title">' + escapeHtml(s.spotify_name) + '</div><div class="song-artist">' + escapeHtml(s.artist) + '</div></div><span class="badge badge-added">Added</span></li>';
                            }});
                            html += '</ul>';
                        }}
                        resultsPanel.innerHTML = '<h2>Update Complete</h2>' + html;
                        resultsPanel.classList.remove('hidden');
                    }} else {{
                        alert('Error: ' + data.error);
                    }}
                }} catch (err) {{
                    hideLoading();
                    alert('Failed: ' + err.message);
                }}
            }});
        }}
    </script>
</body>
</html>'''


@app.route("/")
def index():
    sp = get_spotify_client()

    if not sp:
        content = '''
        <div class="card login-card">
            <h2>Connect Your Spotify</h2>
            <p>Link your Spotify account to get started</p>
            <a href="/login" class="btn btn-spotify">Login with Spotify</a>
        </div>
        '''
        return render_page(content)

    try:
        user = sp.current_user()
        playlist = sp.playlist(SPOTIFY_PLAYLIST_ID, fields="name,images,tracks(total)")

        avatar = f'<img src="{user["images"][0]["url"]}" class="avatar">' if user.get("images") else ""
        cover = f'<img src="{playlist["images"][0]["url"]}" class="playlist-cover">' if playlist.get("images") else ""

        content = f'''
        <div class="user-bar">
            <div class="user-info">{avatar}<span>{user["display_name"]}</span></div>
            <a href="/logout" class="btn btn-small">Logout</a>
        </div>
        <div class="card">
            <h2>Target Playlist</h2>
            <div class="playlist-info">
                {cover}
                <div>
                    <h3>{playlist["name"]}</h3>
                    <p>{playlist["tracks"]["total"]} tracks</p>
                    <a href="https://open.spotify.com/playlist/{SPOTIFY_PLAYLIST_ID}" target="_blank" class="btn btn-small">Open in Spotify</a>
                </div>
            </div>
        </div>
        <div class="actions">
            <button id="scrapeBtn" class="btn btn-primary">Preview Kiss 108 Songs</button>
            <button id="updateBtn" class="btn btn-success">Update Playlist</button>
        </div>
        <div id="results" class="results-panel hidden"></div>
        '''
        return render_page(content)

    except Exception as e:
        session.clear()
        return redirect("/")


@app.route("/login")
def login():
    sp_oauth = get_spotify_oauth()
    return redirect(sp_oauth.get_authorize_url())


@app.route("/callback")
def callback():
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return render_page(f'<div class="card"><h2>Error</h2><p>{error}</p><a href="/" class="btn btn-primary">Go Back</a></div>')

    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/api/scrape")
def api_scrape():
    try:
        songs = fetch_kiss108_songs()
        return jsonify({"success": True, "songs": songs, "count": len(songs)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/update", methods=["POST"])
def api_update():
    sp = get_spotify_client()
    if not sp:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    try:
        scraped = fetch_kiss108_songs()

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

        added = []
        not_found = []
        already_exists = []

        for song in scraped:
            query = f"track:{song['title']} artist:{song['artist']}"
            results = sp.search(q=query, type="track", limit=3)
            tracks = results.get("tracks", {}).get("items", [])

            if not tracks:
                query = f"{song['title']} {song['artist']}"
                results = sp.search(q=query, type="track", limit=3)
                tracks = results.get("tracks", {}).get("items", [])

            if tracks:
                track = tracks[0]
                if track["uri"] in existing_uris:
                    already_exists.append({"title": song["title"], "artist": song["artist"], "spotify_name": track["name"]})
                else:
                    sp.playlist_add_items(SPOTIFY_PLAYLIST_ID, [track["uri"]])
                    existing_uris.add(track["uri"])
                    added.append({"title": song["title"], "artist": song["artist"], "spotify_name": track["name"], "uri": track["uri"]})
            else:
                not_found.append(song)

        return jsonify({
            "success": True,
            "added": added,
            "already_exists": already_exists,
            "not_found": not_found,
            "summary": {"scraped": len(scraped), "added": len(added), "already_exists": len(already_exists), "not_found": len(not_found)}
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
