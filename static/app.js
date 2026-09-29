// Kiss 108 Playlist Updater - Frontend JavaScript

const scrapeBtn = document.getElementById('scrapeBtn');
const updateBtn = document.getElementById('updateBtn');
const resultsPanel = document.getElementById('results');
const resultsTitle = document.getElementById('resultsTitle');
const resultsContent = document.getElementById('resultsContent');
const closeResults = document.getElementById('closeResults');
const loading = document.getElementById('loading');
const loadingText = document.getElementById('loadingText');

function showLoading(text) {
    loadingText.textContent = text;
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

function showResults(title, content) {
    resultsTitle.textContent = title;
    resultsContent.innerHTML = content;
    resultsPanel.classList.remove('hidden');
}

function hideResults() {
    resultsPanel.classList.add('hidden');
}

if (closeResults) {
    closeResults.addEventListener('click', hideResults);
}

// Preview Kiss 108 Songs
if (scrapeBtn) {
    scrapeBtn.addEventListener('click', async () => {
        showLoading('Fetching Kiss 108 top songs...');

        try {
            const response = await fetch('/api/scrape');
            const data = await response.json();
            hideLoading();

            if (data.success) {
                let html = `<p style="margin-bottom: 1rem; color: #888;">Found ${data.count} songs on Kiss 108</p>`;
                html += '<ul class="song-list">';

                data.songs.forEach((song, index) => {
                    html += `
                        <li class="song-item">
                            <span style="color: #888; width: 24px;">${index + 1}</span>
                            <div class="song-details">
                                <div class="song-title">${escapeHtml(song.title)}</div>
                                <div class="song-artist">${escapeHtml(song.artist)}</div>
                            </div>
                        </li>
                    `;
                });

                html += '</ul>';
                showResults('Kiss 108 Top Songs', html);
            } else {
                showResults('Error', `<p class="error">${escapeHtml(data.error)}</p>`);
            }
        } catch (err) {
            hideLoading();
            showResults('Error', `<p class="error">Failed to fetch songs: ${escapeHtml(err.message)}</p>`);
        }
    });
}

// Update Playlist
if (updateBtn) {
    updateBtn.addEventListener('click', async () => {
        showLoading('Updating playlist... This may take a moment.');

        try {
            const response = await fetch('/api/update', { method: 'POST' });
            const data = await response.json();
            hideLoading();

            if (data.success) {
                let html = `
                    <div class="summary">
                        <div class="summary-item">
                            <div class="number">${data.summary.scraped}</div>
                            <div class="label">Scraped</div>
                        </div>
                        <div class="summary-item">
                            <div class="number" style="color: #1DB954;">${data.summary.added}</div>
                            <div class="label">Added</div>
                        </div>
                        <div class="summary-item">
                            <div class="number" style="color: #ffc107;">${data.summary.already_exists}</div>
                            <div class="label">Already Exist</div>
                        </div>
                        <div class="summary-item">
                            <div class="number" style="color: #ff5252;">${data.summary.not_found}</div>
                            <div class="label">Not Found</div>
                        </div>
                    </div>
                `;

                if (data.added.length > 0) {
                    html += '<h3 class="section-title">Added to Playlist</h3>';
                    html += '<ul class="song-list">';
                    data.added.forEach(song => {
                        html += `
                            <li class="song-item">
                                <div class="song-details">
                                    <div class="song-title">${escapeHtml(song.spotify_name)}</div>
                                    <div class="song-artist">${escapeHtml(song.artist)}</div>
                                </div>
                                <span class="badge badge-added">Added</span>
                            </li>
                        `;
                    });
                    html += '</ul>';
                }

                if (data.not_found.length > 0) {
                    html += '<h3 class="section-title">Not Found on Spotify</h3>';
                    html += '<ul class="song-list">';
                    data.not_found.forEach(song => {
                        html += `
                            <li class="song-item">
                                <div class="song-details">
                                    <div class="song-title">${escapeHtml(song.title)}</div>
                                    <div class="song-artist">${escapeHtml(song.artist)}</div>
                                </div>
                                <span class="badge badge-notfound">Not Found</span>
                            </li>
                        `;
                    });
                    html += '</ul>';
                }

                showResults('Update Complete', html);

                // Reload page after a delay to refresh playlist count
                setTimeout(() => location.reload(), 3000);
            } else {
                showResults('Error', `<p class="error">${escapeHtml(data.error)}</p>`);
            }
        } catch (err) {
            hideLoading();
            showResults('Error', `<p class="error">Failed to update playlist: ${escapeHtml(err.message)}</p>`);
        }
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
