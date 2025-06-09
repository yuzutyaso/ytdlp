// frontend/script.js
const API_BASE_URL = 'http://127.0.0.1:5000/api'; // FlaskサーバーのURL

const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const searchResultsDiv = document.getElementById('searchResults');
const videoDetailDiv = document.getElementById('videoDetail');
const playlistDetailDiv = document.getElementById('playlistDetail');
const backToListButton = document.getElementById('backToList');
const backToListFromPlaylistButton = document.getElementById('backToListFromPlaylist');

// 動画詳細表示要素
const youtubePlayer = document.getElementById('youtubePlayer');
const videoTitleElem = document.getElementById('videoTitle');
const videoUploaderElem = document.getElementById('videoUploader');
const videoDescriptionElem = document.getElementById('videoDescription');
const videoViewsElem = document.getElementById('videoViews');

// プレイリスト詳細表示要素
const playlistTitleElem = document.getElementById('playlistTitle');
const playlistDescriptionElem = document.getElementById('playlistDescription');
const playlistVideoCountElem = document.getElementById('playlistVideoCount');
const playlistVideosDiv = document.getElementById('playlistVideos');

searchButton.addEventListener('click', performSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch();
    }
});
backToListButton.addEventListener('click', showSearchResults);
backToListFromPlaylistButton.addEventListener('click', showSearchResults);

async function performSearch() {
    const query = searchInput.value.trim();
    if (!query) {
        alert('検索キーワードを入力してください。');
        return;
    }

    showLoading();
    try {
        const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        displaySearchResults(data);
    } catch (error) {
        console.error('検索中にエラーが発生しました:', error);
        searchResultsDiv.innerHTML = `<p class="error-message">検索結果の取得に失敗しました。サーバーが起動しているか確認してください。</p>`;
    } finally {
        hideLoading();
    }
}

function showLoading() {
    searchResultsDiv.innerHTML = '<p>検索中...</p>';
    videoDetailDiv.classList.add('hidden');
    playlistDetailDiv.classList.add('hidden');
    searchResultsDiv.classList.remove('hidden');
}

function hideLoading() {
    // 処理完了後にロード表示を消す（結果表示関数で上書きされるため、実質的には不要だが一応）
}

function displaySearchResults(results) {
    searchResultsDiv.innerHTML = '';
    videoDetailDiv.classList.add('hidden');
    playlistDetailDiv.classList.add('hidden');
    searchResultsDiv.classList.remove('hidden');

    if (results.length === 0) {
        searchResultsDiv.innerHTML = '<p>該当する結果はありませんでした。</p>';
        return;
    }

    results.forEach(item => {
        if (item.type === 'video') {
            const videoItem = document.createElement('div');
            videoItem.classList.add('video-item');
            videoItem.innerHTML = `
                <img src="${item.thumbnail}" alt="${item.title}">
                <div class="item-info">
                    <h3>${item.title}</h3>
                    <p>チャンネル: ${item.author}</p>
                    <p class="duration">長さ: ${formatDuration(item.duration)}</p>
                    <p class="views">再生回数: ${formatViews(item.views)}</p>
                </div>
            `;
            videoItem.addEventListener('click', () => showVideoDetail(item.url));
            searchResultsDiv.appendChild(videoItem);
        } else if (item.type === 'playlist') {
            const playlistItem = document.createElement('div');
            playlistItem.classList.add('playlist-item');
            playlistItem.innerHTML = `
                <img src="${item.thumbnail}" alt="${item.title}">
                <div class="item-info">
                    <h3>${item.title}</h3>
                    <p>チャンネル: ${item.author}</p>
                    <p class="video-count">動画数: ${item.video_count}</p>
                </div>
            `;
            playlistItem.addEventListener('click', () => showPlaylistDetail(item.url));
            searchResultsDiv.appendChild(playlistItem);
        }
    });
}

async function showVideoDetail(videoUrl) {
    searchResultsDiv.classList.add('hidden');
    playlistDetailDiv.classList.add('hidden');
    videoDetailDiv.classList.remove('hidden');

    // ローディング表示
    videoTitleElem.textContent = '動画情報を取得中...';
    youtubePlayer.src = ''; // 一度クリア

    try {
        const response = await fetch(`${API_BASE_URL}/video_info?url=${encodeURIComponent(videoUrl)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.error) {
            videoTitleElem.textContent = `エラー: ${data.error}`;
            return;
        }

        videoTitleElem.textContent = data.title;
        videoUploaderElem.textContent = `チャンネル: ${data.uploader}`;
        videoDescriptionElem.textContent = data.description ? data.description.substring(0, 200) + '...' : '説明なし';
        videoViewsElem.textContent = `再生回数: ${formatViews(data.view_count)}`;

        // YouTube埋め込みURLの構築
        // yt-dlpから取得したYouTube IDを使用する
        const youtubeEmbedId = data.id;
        youtubePlayer.src = `https://www.youtube.com/embed/${youtubeEmbedId}?autoplay=1`;

    } catch (error) {
        console.error('動画詳細の取得中にエラーが発生しました:', error);
        videoTitleElem.textContent = `動画情報の取得に失敗しました。`;
    }
}

async function showPlaylistDetail(playlistUrl) {
    searchResultsDiv.classList.add('hidden');
    videoDetailDiv.classList.add('hidden');
    playlistDetailDiv.classList.remove('hidden');

    // ローディング表示
    playlistTitleElem.textContent = 'プレイリスト情報を取得中...';
    playlistVideosDiv.innerHTML = '<p>動画を読み込み中...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/playlist_info?url=${encodeURIComponent(playlistUrl)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.error) {
            playlistTitleElem.textContent = `エラー: ${data.error}`;
            return;
        }

        playlistTitleElem.textContent = data.title;
        playlistDescriptionElem.textContent = data.description ? data.description.substring(0, 200) + '...' : '説明なし';
        playlistVideoCountElem.textContent = `動画数: ${data.video_count}`;

        playlistVideosDiv.innerHTML = ''; // クリア
        if (data.videos && data.videos.length > 0) {
            data.videos.forEach(video => {
                const videoItem = document.createElement('div');
                videoItem.classList.add('video-item');
                videoItem.innerHTML = `
                    <img src="${video.thumbnail_url}" alt="${video.title}">
                    <div class="item-info">
                        <h3>${video.title}</h3>
                        <p>チャンネル: ${video.author}</p>
                        <p class="duration">長さ: ${formatDuration(video.duration)}</p>
                    </div>
                `;
                videoItem.addEventListener('click', () => showVideoDetail(video.url));
                playlistVideosDiv.appendChild(videoItem);
            });
        } else {
            playlistVideosDiv.innerHTML = '<p>このプレイリストには動画がありません。</p>';
        }

    } catch (error) {
        console.error('プレイリスト詳細の取得中にエラーが発生しました:', error);
        playlistTitleElem.textContent = `プレイリスト情報の取得に失敗しました。`;
    }
}

function showSearchResults() {
    videoDetailDiv.classList.add('hidden');
    playlistDetailDiv.classList.add('hidden');
    searchResultsDiv.classList.remove('hidden');
    youtubePlayer.src = ''; // プレーヤーを停止
}

// ヘルパー関数: 再生時間を整形
function formatDuration(seconds) {
    if (typeof seconds !== 'number' || isNaN(seconds)) {
        return 'N/A';
    }
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    const parts = [];
    if (h > 0) parts.push(h);
    parts.push(m.toString().padStart(h > 0 ? 2 : 1, '0'));
    parts.push(s.toString().padStart(2, '0'));
    return parts.join(':');
}

// ヘルパー関数: 再生回数を整形
function formatViews(views) {
    if (typeof views !== 'number' || isNaN(views)) {
        return 'N/A';
    }
    return views.toLocaleString();
                                                 }
