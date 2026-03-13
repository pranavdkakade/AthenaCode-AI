/**
 * background.js  (Manifest V3 service worker)
 *
 * Responsibilities:
 *  - Listen for REPO_DETECTED messages from content scripts.
 *  - Open / focus the side panel when the action button is clicked.
 *  - Relay analyze-repo requests from the sidebar to the backend.
 */

"use strict";

const BACKEND_BASE = "http://localhost:8000/api";

// Open the side panel when the toolbar button is clicked
chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ tabId: tab.id });
});

// Handle messages from content.js and sidebar.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case "REPO_DETECTED":
      handleRepoDetected(message.payload, sender.tab);
      sendResponse({ ok: true });
      break;

    case "ANALYZE_REPO":
      analyzeRepo(message.payload.repoUrl)
        .then((result) => sendResponse({ ok: true, data: result }))
        .catch((err) => sendResponse({ ok: false, error: err.message }));
      return true; // keep message channel open for async response

    default:
      break;
  }
});

/**
 * Called when content.js detects a GitHub repository.
 * Updates the extension badge to show CodeAtlas is active.
 */
function handleRepoDetected(repoInfo, tab) {
  if (!tab) return;
  chrome.action.setBadgeText({ text: "AI", tabId: tab.id });
  chrome.action.setBadgeBackgroundColor({ color: "#6366f1", tabId: tab.id });
}

/**
 * Sends a POST /analyze_repo request to the FastAPI backend.
 */
async function analyzeRepo(repoUrl) {
  const response = await fetch(`${BACKEND_BASE}/analyze_repo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }

  return response.json();
}
