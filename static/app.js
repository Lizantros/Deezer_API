document.addEventListener('DOMContentLoaded', () => {
    // State
    let currentSongs = []; // From Parse
    let preparedResults = []; // From Match

    const elements = {
        authOverlay: document.getElementById('authOverlay'),
        arlInput: document.getElementById('arlInput'),
        btnConnect: document.getElementById('btnConnect'),
        authError: document.getElementById('authError'),
        connectionStatus: document.getElementById('connectionStatus'),

        descriptionInput: document.getElementById('descriptionInput'),
        btnParse: document.getElementById('btnParse'),
        btnMatch: document.getElementById('btnMatch'),

        songList: document.getElementById('songList'),
        songsCount: document.getElementById('songsCount'),

        playlistName: document.getElementById('playlistName'),
        btnCreate: document.getElementById('btnCreate'),
    };

    // Load saved ARL if any
    let storedArl = localStorage.getItem('deezer_arl');

    // --- Auth Functions ---
    async function checkConnection(arl) {
        elements.connectionStatus.textContent = "Connecting...";
        try {
            const res = await fetch('/api/auth/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ arl: arl })
            });
            const data = await res.json();

            if (data.status === 'ok') {
                elements.connectionStatus.textContent = "Connected";
                elements.connectionStatus.classList.remove('error');
                elements.authOverlay.classList.remove('active');
                localStorage.setItem('deezer_arl', arl);
                return true;
            } else {
                throw new Error(data.message);
            }
        } catch (e) {
            elements.connectionStatus.textContent = "Disconnected";
            elements.connectionStatus.classList.add('error');
            elements.authOverlay.classList.add('active'); // Show login
            if (elements.authError.style.display === 'block') {
                elements.authError.textContent = "Connection failed. Please check your ARL.";
            }
            return false;
        }
    }

    elements.btnConnect.addEventListener('click', async () => {
        const arl = elements.arlInput.value.trim();
        if (!arl) return;

        elements.btnConnect.textContent = "Verifying...";
        elements.authError.style.display = 'none';

        if (await checkConnection(arl)) {
            storedArl = arl;
        } else {
            elements.authError.style.display = 'block';
            elements.btnConnect.textContent = "Connect";
        }
    });

    // --- Parsing Functions ---
    elements.btnParse.addEventListener('click', async () => {
        const text = elements.descriptionInput.value;
        if (!text.trim()) return;

        elements.btnParse.textContent = "Parsing...";

        try {
            const res = await fetch('/api/parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            const data = await res.json();

            currentSongs = data.songs;
            preparedResults = []; // Reset matches
            renderSongsState('parsed'); // Render just text list
            elements.btnParse.textContent = "1. Parse Songs";
        } catch (e) {
            alert("Error parsing text");
            elements.btnParse.textContent = "1. Parse Songs";
        }
    });

    // --- Matching Functions ---
    elements.btnMatch.addEventListener('click', async () => {
        if (!currentSongs.length) return alert("Parse songs first!");

        elements.btnMatch.textContent = "Searching...";
        elements.btnMatch.disabled = true;

        try {
            const res = await fetch('/api/prepare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    arl: storedArl,
                    songs: currentSongs
                })
            });
            const data = await res.json();
            if (data.results) {
                preparedResults = data.results;
                renderSongsState('matched');
            } else {
                alert("Error fetching matches");
            }
        } catch (e) {
            alert("Network error: " + e);
        } finally {
            elements.btnMatch.textContent = "2. Find Matches";
            elements.btnMatch.disabled = false;
        }
    });


    function renderSongsState(state) {
        // state = 'parsed' (show simple list from currentSongs)
        // state = 'matched' (show complex list from preparedResults)

        elements.songList.innerHTML = '';

        if (state === 'parsed') {
            elements.songsCount.textContent = `Review Songs (${currentSongs.length})`;
            currentSongs.forEach(song => {
                const item = document.createElement('div');
                item.className = 'song-item';
                item.innerHTML = `
                    <div class="song-status" style="background:#555"></div>
                    <div class="song-info">
                        <div class="song-title">${song.title}</div>
                        <div class="song-artist">${song.artist || '(No Artist)'}</div>
                    </div>
                `;
                elements.songList.appendChild(item);
            });
        } else if (state === 'matched') {
            elements.songsCount.textContent = `Matches Found (${preparedResults.length})`;

            preparedResults.forEach((res, idx) => {
                const item = document.createElement('div');
                item.className = 'song-item';

                let content = '';
                let statusClass = '';

                if (res.status === 'found') {
                    statusClass = 'found';
                    content = `
                        <div class="song-info">
                            <div class="song-title">${res.title}</div>
                            <div class="song-artist" style="color:#00ff88">Found: ${res.artist}</div>
                        </div>
                        <input type="hidden" class="track-id" value="${res.id}">
                    `;
                } else if (res.status === 'missing') {
                    statusClass = 'missing';
                    content = `
                        <div class="song-info">
                            <div class="song-title">${res.title}</div>
                            <div class="song-artist" style="color:#ff3b3b">Not Found</div>
                            <div class="refine-container" style="display:flex; gap:5px; margin-top:5px;">
                                <input type="text" class="refine-input" placeholder="Refine search..." value="${res.artist} ${res.title}">
                                <button class="small-btn refine-btn" data-index="${idx}">Search</button>
                            </div>
                            <select class="candidate-select" style="width:100%; margin-top:5px; display:none;">
                            </select>
                        </div>
                    `;
                } else if (res.status === 'ambiguous') {
                    statusClass = 'ambiguous'; // yellow?
                    // Create Dropdown
                    let options = res.candidates.map(c =>
                        `<option value="${c.id}">${c.artist} - ${c.title} (${c.album})</option>`
                    ).join('');

                    content = `
                        <div class="song-info">
                            <div class="song-title" style="color:#ffd700">${res.title} (Choose Match)</div>
                            <div class="refine-container" style="display:flex; gap:5px; margin-top:5px;">
                                <input type="text" class="refine-input" placeholder="Refine search..." value="${res.title}">
                                <button class="small-btn refine-btn" data-index="${idx}">Search</button>
                            </div>
                            <select class="candidate-select" style="width:100%; margin-top:5px; font-size:0.8rem; padding:6px;">
                                ${options}
                            </select>
                        </div>
                     `;
                }

                item.innerHTML = `<div class="song-status ${statusClass}" style="${res.status === 'ambiguous' ? 'background:#ffd700' : ''}"></div>` + content;
                elements.songList.appendChild(item);
            });

            // Attach Refine Events
            document.querySelectorAll('.refine-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const idx = e.target.getAttribute('data-index');
                    const parent = e.target.closest('.song-info');
                    const input = parent.querySelector('.refine-input');
                    const select = parent.querySelector('.candidate-select');

                    const query = input.value;
                    if (!query) return;

                    e.target.textContent = "...";

                    try {
                        const res = await fetch('/api/search_candidates', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ arl: storedArl, query: query })
                        });
                        const data = await res.json();

                        if (data.candidates && data.candidates.length > 0) {
                            select.innerHTML = data.candidates.map(c =>
                                `<option value="${c.id}">${c.artist} - ${c.title} (${c.album})</option>`
                            ).join('');
                            select.style.display = 'block';

                            // Update status color if it was missing
                            const statusDot = parent.parentElement.querySelector('.song-status');
                            if (statusDot) statusDot.style.background = '#ffd700'; // Turn yellow
                        } else {
                            alert("No matches found for that query");
                        }
                    } catch (err) {
                        alert("Search failed: " + err);
                    } finally {
                        e.target.textContent = "Search";
                    }
                });
            });
        }
    }

    // --- Creation Functions ---
    elements.btnCreate.addEventListener('click', async () => {
        if (!preparedResults.length) return alert("Please click 'Find Matches' first!");

        const playlistName = elements.playlistName.value.trim();
        if (!playlistName) return alert("Enter a playlist name!");

        // Collect IDs
        const trackIds = [];
        const items = elements.songList.querySelectorAll('.song-item');

        items.forEach(item => {
            // Check for hidden input
            const hidden = item.querySelector('.track-id');
            if (hidden) {
                trackIds.push(parseInt(hidden.value));
            } else {
                // Check for select
                const select = item.querySelector('select');
                if (select) {
                    trackIds.push(parseInt(select.value));
                }
            }
        });

        if (trackIds.length === 0) return alert("No valid tracks selected to add.");

        elements.btnCreate.textContent = "Creating...";
        elements.btnCreate.disabled = true;

        try {
            const res = await fetch('/api/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    arl: storedArl,
                    playlist_name: playlistName,
                    track_ids: trackIds
                })
            });
            const data = await res.json();

            if (data.status === 'success') {
                alert(data.message);
            } else {
                alert("Error: " + data.message);
            }
        } catch (e) {
            alert("Network error: " + e);
        } finally {
            elements.btnCreate.textContent = "Create Playlist";
            elements.btnCreate.disabled = false;
        }
    });

    // Init
    if (storedArl) {
        checkConnection(storedArl);
    } else {
        elements.authOverlay.classList.add('active'); // Force login if no storage
    }
});
