# Kiss 108 Playlist Updater

A web app that automatically adds songs from the Kiss 108 Top Songs chart to your Spotify playlist.

![Dashboard Preview](https://img.shields.io/badge/Flask-Web%20App-blue) ![Deploy with Vercel](https://img.shields.io/badge/Vercel-Deployed-black)

## Features

- 🎵 Scrapes current top songs from Kiss 108
- 🔍 Searches and matches songs on Spotify
- ➕ Adds new songs to your playlist automatically
- 🚫 Skips duplicates already in your playlist
- 📊 Dashboard to view and manage updates

## Deploy to Vercel

### 1. Fork or Clone This Repository

```bash
git clone https://github.com/YOUR_USERNAME/spotify-playlist-updater.git
```

### 2. Create a Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **Create App**
3. Set **Redirect URI** to: `https://your-vercel-app.vercel.app/callback`
4. Note your **Client ID** and **Client Secret**

### 3. Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **New Project** and import this repository
3. Add environment variables:

| Variable | Value |
|----------|-------|
| `SPOTIFY_CLIENT_ID` | Your Spotify Client ID |
| `SPOTIFY_CLIENT_SECRET` | Your Spotify Client Secret |
| `SPOTIFY_REDIRECT_URI` | `https://your-app.vercel.app/callback` |
| `SPOTIFY_PLAYLIST_ID` | Your target playlist ID |
| `FLASK_SECRET_KEY` | Random string (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |

4. Click **Deploy**

### 4. Update Spotify App

After deployment, update your Spotify app's Redirect URI to match your Vercel URL:
`https://your-app.vercel.app/callback`

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# Run locally
python api/index.py
```

Visit `http://localhost:5000`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/login` | GET | Spotify OAuth login |
| `/callback` | GET | OAuth callback |
| `/api/scrape` | GET | Preview Kiss 108 songs |
| `/api/playlist` | GET | Get current playlist tracks |
| `/api/update` | POST | Scrape and add new songs |

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Vanilla HTML/CSS/JS
- **APIs**: Spotify Web API, Kiss 108 website
- **Hosting**: Vercel Serverless Functions

## License

MIT
