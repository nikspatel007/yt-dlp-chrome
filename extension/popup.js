(function () {
  const statusEl = document.getElementById('status');
  const statusText = document.getElementById('status-text');
  const helpEl = document.getElementById('help');
  const downloadSection = document.getElementById('download-section');
  const downloadBtn = document.getElementById('download-btn');
  const notYoutube = document.getElementById('not-youtube');
  const downloadsSection = document.getElementById('downloads-section');
  const historyList = document.getElementById('history-list');

  let currentUrl = null;

  const YOUTUBE_RE = /^https?:\/\/(www\.|m\.)?(youtube\.com\/watch\?|youtu\.be\/)/;

  function timeAgo(timestamp) {
    const seconds = Math.floor(Date.now() / 1000 - timestamp);
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
    return Math.floor(seconds / 86400) + 'd ago';
  }

  function renderHistory(data) {
    downloadsSection.style.display = 'block';

    if (data.history && data.history.length > 0) {
      historyList.innerHTML = data.history
        .map((item, i) => {
          const isError = item.status === 'error';
          const cls = isError ? 'error' : 'done clickable';
          const icon = isError ? '❌' : '✅';
          const subtitle = isError
            ? (item.error || 'Download failed')
            : timeAgo(item.timestamp);
          const dataAttr = (!isError && item.filename)
            ? ` data-filename="${item.filename.replace(/"/g, '&quot;')}" data-idx="${i}"`
            : '';
          return `
            <div class="download-item ${cls}"${dataAttr}>
              <span class="icon">${icon}</span>
              <div class="info">
                <div class="title">${item.title}</div>
                <div class="time">${subtitle}</div>
              </div>
            </div>
          `;
        }).join('');

      // Add click handlers to reveal files in Finder
      historyList.querySelectorAll('.download-item.clickable').forEach(el => {
        el.addEventListener('click', () => {
          const filename = el.dataset.filename;
          if (filename) {
            chrome.runtime.sendMessage({ action: 'reveal', filename });
          }
        });
      });
    } else {
      historyList.innerHTML = '<div class="empty">No downloads yet</div>';
    }
  }

  function loadDownloads() {
    chrome.runtime.sendMessage({ action: 'getDownloads' }, (response) => {
      if (response) renderHistory(response);
    });
  }

  function setButtonState(state, text) {
    downloadBtn.className = 'download-btn ' + state;
    downloadBtn.textContent = text;
    downloadBtn.disabled = (state !== 'ready');
  }

  function handleDownload() {
    if (!currentUrl) return;

    setButtonState('downloading', 'Downloading...');

    chrome.runtime.sendMessage(
      { action: 'download', url: currentUrl },
      (response) => {
        if (!response || response.status === 'error') {
          setButtonState('error', (response && response.message) || 'Download failed');
          setTimeout(() => setButtonState('ready', 'Download MP3 (320kbps)'), 5000);
        } else {
          setButtonState('done', '✓ Downloaded: ' + response.title);
          loadDownloads();
          setTimeout(() => setButtonState('ready', 'Download MP3 (320kbps)'), 3000);
        }
      }
    );
  }

  // Get current tab URL
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0] && tabs[0].url && YOUTUBE_RE.test(tabs[0].url)) {
      currentUrl = tabs[0].url;
      downloadSection.style.display = 'block';
      notYoutube.style.display = 'none';
    } else {
      downloadSection.style.display = 'none';
      notYoutube.style.display = 'block';
    }
  });

  downloadBtn.addEventListener('click', handleDownload);

  // Check server status
  chrome.runtime.sendMessage({ action: 'healthCheck' }, (response) => {
    if (response && response.status === 'ok') {
      statusEl.className = 'status online';
      statusText.textContent = 'Server is running';
      helpEl.style.display = 'none';
      downloadBtn.disabled = false;
      loadDownloads();
    } else {
      statusEl.className = 'status offline';
      statusText.textContent = 'Server is not running';
      helpEl.style.display = 'block';
      helpEl.innerHTML =
        'Start the server by running:<br><br>' +
        '<code>uv run python server.py</code><br><br>' +
        'from the <code>yt-dlp-chrome</code> directory.';
      downloadBtn.disabled = true;
    }
  });

  // Refresh history every 3 seconds
  setInterval(loadDownloads, 3000);
})();
