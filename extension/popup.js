(function () {
  const statusEl = document.getElementById('status');
  const statusText = document.getElementById('status-text');
  const helpEl = document.getElementById('help');
  const downloadSection = document.getElementById('download-section');
  const downloadBtn = document.getElementById('download-btn');
  const notYoutube = document.getElementById('not-youtube');
  const downloadsSection = document.getElementById('downloads-section');
  const historyList = document.getElementById('history-list');
  const djViewBtn = document.getElementById('dj-view-btn');

  let currentUrl = null;

  const YOUTUBE_RE = /^https?:\/\/(www\.|m\.)?(youtube\.com\/watch\?|youtu\.be\/)/;

  function timeAgo(timestamp) {
    const seconds = Math.floor(Date.now() / 1000 - timestamp);
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
    return Math.floor(seconds / 86400) + 'd ago';
  }

  function renderWaveform(waveform) {
    if (!waveform || waveform.length === 0) return '';
    const targetBars = 60;
    const step = Math.max(1, Math.floor(waveform.length / targetBars));
    let bars = '';
    for (let i = 0; i < waveform.length; i += step) {
      const height = Math.max(2, Math.round(waveform[i] * 100));
      bars += '<div class="waveform-bar" style="height:' + height + '%"></div>';
    }
    return '<div class="waveform">' + bars + '</div>';
  }

  function renderHistory(data) {
    downloadsSection.style.display = 'block';

    if (data.history && data.history.length > 0) {
      historyList.innerHTML = data.history
        .map(function(item) {
          var isError = item.status === 'error';
          var cls = isError ? 'error' : 'done';
          var subtitle = isError
            ? (item.error || 'Download failed')
            : timeAgo(item.timestamp);

          var dataAttr = (!isError && item.filename)
            ? ' data-filename="' + item.filename.replace(/"/g, '&quot;') + '"'
            : '';

          var badges = (!isError && item.bpm)
            ? '<div class="track-badges">' +
                '<span class="badge-bpm">' + item.bpm + ' BPM</span>' +
                '<span class="badge-key">' + (item.key || '?') + '</span>' +
              '</div>'
            : '';

          var waveform = (!isError && item.waveform)
            ? renderWaveform(item.waveform)
            : '';

          return '<div class="download-item ' + cls + '"' + dataAttr + '>' +
              '<div class="track-header">' +
                '<div class="track-title">' + (isError ? '❌ ' : '') + item.title + '</div>' +
                '<div class="track-time">' + subtitle + '</div>' +
              '</div>' +
              badges +
              waveform +
            '</div>';
        }).join('');

      historyList.querySelectorAll('.download-item.done').forEach(function(el) {
        el.addEventListener('click', function() {
          var filename = el.dataset.filename;
          if (filename) {
            chrome.runtime.sendMessage({ action: 'reveal', filename: filename });
          }
        });
      });
    } else {
      historyList.innerHTML = '<div class="empty">No downloads yet</div>';
    }
  }

  function loadDownloads() {
    chrome.runtime.sendMessage({ action: 'getDownloads' }, function(response) {
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

    setButtonState('downloading', 'Downloading & Analyzing...');

    chrome.runtime.sendMessage(
      { action: 'download', url: currentUrl },
      function(response) {
        if (!response || response.status === 'error') {
          setButtonState('error', (response && response.message) || 'Download failed');
          setTimeout(function() { setButtonState('ready', 'Download MP3 (320kbps)'); }, 5000);
        } else {
          var info = response.bpm ? ' (' + response.bpm + ' BPM, ' + response.key + ')' : '';
          setButtonState('done', '✓ ' + response.title + info);
          loadDownloads();
          setTimeout(function() { setButtonState('ready', 'Download MP3 (320kbps)'); }, 4000);
        }
      }
    );
  }

  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
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

  djViewBtn.addEventListener('click', function() {
    chrome.runtime.sendMessage({ action: 'openDjView' });
  });

  chrome.runtime.sendMessage({ action: 'healthCheck' }, function(response) {
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

  setInterval(loadDownloads, 3000);
})();
