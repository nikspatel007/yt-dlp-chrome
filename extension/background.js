const SERVER_URL = 'http://localhost:8765';

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'download') {
    fetch(`${SERVER_URL}/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: message.url }),
    })
      .then(res => res.json())
      .then(data => sendResponse(data))
      .catch(() =>
        sendResponse({
          status: 'error',
          message: 'Cannot connect to server. Run: python server.py',
        })
      );
    // Return true to indicate async sendResponse
    return true;
  }

  if (message.action === 'healthCheck') {
    fetch(`${SERVER_URL}/health`)
      .then(res => res.json())
      .then(data => sendResponse(data))
      .catch(() => sendResponse({ status: 'offline' }));
    return true;
  }

  if (message.action === 'getDownloads') {
    fetch(`${SERVER_URL}/downloads`)
      .then(res => res.json())
      .then(data => sendResponse(data))
      .catch(() => sendResponse({ active: [], history: [] }));
    return true;
  }

  if (message.action === 'reveal') {
    fetch(`${SERVER_URL}/reveal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: message.filename }),
    })
      .then(res => res.json())
      .then(data => sendResponse(data))
      .catch(() => sendResponse({ status: 'error' }));
    return true;
  }

  if (message.action === 'openDjView') {
    chrome.tabs.create({ url: `${SERVER_URL}/dj` });
    sendResponse({ status: 'ok' });
    return true;
  }
});
