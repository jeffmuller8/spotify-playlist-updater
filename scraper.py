"""Web scraper for Kiss 108 Top Songs page."""

import logging
import requests
from bs4 import BeautifulSoup
from config import KISS108_URL

logger = logging.getLogger(__name__)


def fetch_top_songs() -> list[tuple[str, str]]:
    """
    Fetch the top songs from Kiss 108's website.

    Returns:
        List of (song_title, artist_name) tuples
    """
    logger.info(f"Fetching top songs from {KISS108_URL}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        response = requests.get(KISS108_URL, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Kiss 108 page: {e}")
        raise

    soup = BeautifulSoup(response.text, "html.parser")
    songs = []

    # Look for song entries - iHeart uses various structures
    # Try multiple selectors to find song/artist pairs

    # Pattern 1: Look for track list items
    track_items = soup.select('[class*="track"], [class*="song"], [class*="playlist-item"]')

    for item in track_items:
        song_title = None
        artist_name = None

        # Try to find title
        title_elem = item.select_one('[class*="title"], [class*="song-name"], h3, h4')
        if title_elem:
            song_title = title_elem.get_text(strip=True)

        # Try to find artist
        artist_elem = item.select_one('[class*="artist"], [class*="subtitle"], span')
        if artist_elem and artist_elem != title_elem:
            artist_name = artist_elem.get_text(strip=True)

        if song_title and artist_name:
            songs.append((song_title, artist_name))

    # Pattern 2: Look for structured data with specific iHeart patterns
    if not songs:
        # Try finding links with song info
        for link in soup.select('a[href*="/artist/"], a[href*="/song/"]'):
            text = link.get_text(strip=True)
            if " - " in text:
                parts = text.split(" - ", 1)
                if len(parts) == 2:
                    songs.append((parts[0].strip(), parts[1].strip()))

    # Pattern 3: Generic pattern for lists
    if not songs:
        for item in soup.select('li, div.item, article'):
            texts = [t.strip() for t in item.stripped_strings]
            if len(texts) >= 2:
                # Heuristic: first text is usually song, second is artist
                potential_song = texts[0]
                potential_artist = texts[1]
                # Skip if they look like navigation or other elements
                if len(potential_song) > 2 and len(potential_artist) > 2:
                    if not any(x in potential_song.lower() for x in ['menu', 'home', 'search', 'login']):
                        songs.append((potential_song, potential_artist))

    # Deduplicate while preserving order
    seen = set()
    unique_songs = []
    for song in songs:
        key = (song[0].lower(), song[1].lower())
        if key not in seen:
            seen.add(key)
            unique_songs.append(song)

    logger.info(f"Found {len(unique_songs)} songs")
    return unique_songs


if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    songs = fetch_top_songs()
    for i, (title, artist) in enumerate(songs[:10], 1):
        print(f"{i}. {title} - {artist}")
