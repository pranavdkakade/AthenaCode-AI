/**
 * content.js
 * Injected into every github.com/* page.
 * Detects GitHub repository pages, extracts owner/repo info,
 * and notifies the background service worker.
 */

(function () {
  "use strict";

  /**
   * Returns { owner, repo, repoUrl } if the current page is a GitHub
   * repository root or any sub-page within one, otherwise null.
   */
  function detectRepo() {
    const { hostname, pathname } = window.location;
    if (hostname !== "github.com") return null;

    // GitHub repo paths look like: /owner/repo[/...]
    const parts = pathname.replace(/^\//, "").split("/");
    if (parts.length < 2 || !parts[0] || !parts[1]) return null;

    // Exclude GitHub non-repo paths (settings, marketplace, etc.)
    const NON_REPO_ROOTS = new Set([
      "settings", "marketplace", "explore", "notifications",
      "trending", "issues", "pulls", "sponsors", "login", "join",
    ]);
    if (NON_REPO_ROOTS.has(parts[0])) return null;

    const owner = parts[0];
    const repo = parts[1];
    const repoUrl = `https://github.com/${owner}/${repo}`;

    return { owner, repo, repoUrl };
  }

  const repoInfo = detectRepo();

  if (repoInfo) {
    // Persist in extension storage so the sidebar can read it
    chrome.storage.local.set({ currentRepo: repoInfo });

    // Also message the background worker (e.g. to update badge)
    chrome.runtime.sendMessage({
      type: "REPO_DETECTED",
      payload: repoInfo,
    });
  } else {
    // Clear stale data if navigating away from a repo
    chrome.storage.local.remove("currentRepo");
  }
})();
