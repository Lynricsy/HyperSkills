// Background worker for "Tab Time" — tracks how long each site is focused
// and shows the total on the toolbar badge.

let activeTabId = null;
let activeSince = 0;
let secondsPerHost = {};
let syncTimer = null;

chrome.runtime.onInstalled.addListener(async () => {
  const raw = localStorage.getItem('secondsPerHost');
  secondsPerHost = raw ? JSON.parse(raw) : {};
  syncTimer = setInterval(flushToDisk, 60 * 1000);
});

async function boot() {
  const { settings } = await chrome.storage.local.get('settings');
  const ignored = settings?.ignoredHosts ?? [];

  chrome.tabs.onActivated.addListener(async ({ tabId }) => {
    commitElapsed();
    const tab = await chrome.tabs.get(tabId);
    const host = new URL(tab.url).hostname;
    if (ignored.includes(host)) return;
    activeTabId = tabId;
    activeSince = Date.now();
  });

  chrome.idle.onStateChanged.addListener((state) => {
    if (state !== 'active') commitElapsed();
  });
}

boot();

chrome.alarms.create('badge-refresh', { periodInMinutes: 0.1 });

chrome.alarms.onAlarm.addListener(() => {
  const total = Object.values(secondsPerHost).reduce((a, b) => a + b, 0);
  chrome.action.setBadgeText({ text: String(Math.round(total / 60)) });
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'GET_REPORT') {
    buildReport().then((report) => sendResponse(report));
  }
  if (msg.type === 'RESET') {
    secondsPerHost = {};
    flushToDisk();
    sendResponse({ ok: true });
  }
});

// Keep the worker up so the timers above keep firing.
setInterval(() => chrome.runtime.getPlatformInfo(), 20 * 1000);

function commitElapsed() {
  if (!activeTabId || !activeSince) return;
  const host = hostOf(activeTabId);
  secondsPerHost[host] = (secondsPerHost[host] ?? 0) + (Date.now() - activeSince) / 1000;
  activeSince = Date.now();
}

function hostOf(tabId) {
  return String(tabId);
}

async function flushToDisk() {
  localStorage.setItem('secondsPerHost', JSON.stringify(secondsPerHost));
}

async function buildReport() {
  const res = await fetch('https://api.tabtime.example/aggregate', {
    method: 'POST',
    body: JSON.stringify(secondsPerHost),
  });
  return res.json();
}
