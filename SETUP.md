# Spotify Playlist Updater Setup Guide

This script automatically adds songs from the Kiss 108 Top Songs chart to your Spotify playlist.

## Prerequisites

- Python 3.10 or higher
- A Spotify account (free or premium)

## Step 1: Install Dependencies

```bash
cd /Users/jeffmuller/Documents/Spotify-Playlist-Update
pip3 install -r requirements.txt
```

## Step 2: Create a Spotify Developer App

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **Create App**
4. Fill in the details:
   - **App name**: Kiss 108 Playlist Updater
   - **App description**: Automatically adds Kiss 108 top songs to my playlist
   - **Redirect URI**: `http://localhost:8888/callback`
   - Check the boxes for Web API access
5. Click **Create**
6. On your app's page, click **Settings**
7. Note your **Client ID** and **Client Secret**

## Step 3: Configure Credentials

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:
   ```
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   SPOTIFY_PLAYLIST_ID=3nJHpvaovScI9N9VIgh7Qq
   ```

## Step 4: First Run (Authorization)

Run the script once to authorize with Spotify:

```bash
python3 update_playlist.py
```

This will:
1. Open your browser to the Spotify login page
2. Ask you to authorize the app
3. Redirect to `localhost:8888/callback`
4. Save the authorization token locally (in `.spotify_cache`)

After authorization, the script will scrape Kiss 108 and add songs to your playlist.

## Step 5: Schedule Weekly Updates (Optional)

To run automatically every Sunday at 10 AM, add a cron job:

```bash
crontab -e
```

Add this line:
```
0 10 * * 0 cd /Users/jeffmuller/Documents/Spotify-Playlist-Update && /usr/bin/python3 update_playlist.py >> playlist_update.log 2>&1
```

## Usage

### Manual Run
```bash
cd /Users/jeffmuller/Documents/Spotify-Playlist-Update
python3 update_playlist.py
```

### Check Logs
If running via cron:
```bash
tail -f playlist_update.log
```

### View Added Songs History
```bash
cat added_songs.json | python3 -m json.tool
```

## Troubleshooting

### "Missing required environment variables"
Make sure you've created `.env` from `.env.example` and filled in your Spotify credentials.

### "Cannot access the specified playlist"
- Verify the playlist ID is correct
- Make sure you own the playlist or it's collaborative
- Try re-authorizing by deleting `.spotify_cache` and running again

### "No songs found on Kiss 108 page"
The website structure may have changed. Check if the site is accessible and report the issue.

### Authorization Expired
Delete `.spotify_cache` and run the script again to re-authorize.

## Files

| File | Purpose |
|------|---------|
| `update_playlist.py` | Main script |
| `scraper.py` | Fetches songs from Kiss 108 |
| `spotify_client.py` | Spotify API wrapper |
| `config.py` | Configuration loading |
| `.env` | Your credentials (not in git) |
| `added_songs.json` | Tracks which songs have been processed |
| `.spotify_cache` | Spotify authorization token |
