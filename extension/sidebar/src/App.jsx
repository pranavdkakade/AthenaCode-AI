import { useState, useEffect } from "react";
import icon from "./public/icon.png";
import SearchBar from "./components/SearchBar";
import ResultPanel from "./components/ResultPanel";
import RepoHeader from "./components/RepoHeader";
import ApiKeySettings from "./components/ApiKeySettings";

const BACKEND_BASE = "http://localhost:8000/api";

export default function App() {
  const [repo, setRepo] = useState(null);
  const [apiKey, setApiKey] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [analyzeError, setAnalyzeError] = useState("");
  const [queryResult, setQueryResult] = useState(null);
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryError, setQueryError] = useState("");

  // Read current repo from Chrome storage (set by content.js) and load API key
  useEffect(() => {
    if (typeof chrome !== "undefined" && chrome.storage) {
      // Load repository
      chrome.storage.local.get("currentRepo", (data) => {
        if (data.currentRepo) setRepo(data.currentRepo);
      });

      // Load API key
      chrome.storage.local.get("gpt_api_key", (data) => {
        if (data.gpt_api_key) setApiKey(data.gpt_api_key);
      });

      const listener = (changes) => {
        if (changes.currentRepo?.newValue) {
          setRepo(changes.currentRepo.newValue);
          setIsAnalyzed(false);
          setQueryResult(null);
        }
        if (changes.gpt_api_key?.newValue) {
          setApiKey(changes.gpt_api_key.newValue);
        }
      };
      chrome.storage.onChanged.addListener(listener);
      return () => chrome.storage.onChanged.removeListener(listener);
    }
  }, []);

  async function handleAnalyze() {
    if (!repo) return;
    setIsAnalyzing(true);
    setAnalyzeError("");
    try {
      const res = await fetch(`${BACKEND_BASE}/analyze_repo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repo.repoUrl }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed.");
      setIsAnalyzed(true);
    } catch (err) {
      setAnalyzeError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleQuery(question) {
    if (!question.trim() || !repo) return;
    setIsQuerying(true);
    setQueryError("");
    setQueryResult(null);
    try {
      const repoName = `${repo.owner}__${repo.repo}`;
      const res = await fetch(`${BACKEND_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, repo_name: repoName, top_k: 5 }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Query failed.");
      setQueryResult(data);
    } catch (err) {
      setQueryError(err.message);
    } finally {
      setIsQuerying(false);
    }
  }

  return (
    <div className="codeatlas-root">
      <header className="codeatlas-header">
        <img src={icon} alt="AthenaCode AI Logo" className="codeatlas-logo" style={{ width: 32, height: 32, marginRight: 8 }} />
        <h1 className="codeatlas-title">AthenaCode AI</h1>
      </header>

      <main className="codeatlas-main">
        <ApiKeySettings />

        {!repo ? (
          <p className="codeatlas-hint">
            Navigate to a GitHub repository to get started.
          </p>
        ) : (
          <>
            <RepoHeader
              repo={repo}
              isAnalyzed={isAnalyzed}
              isAnalyzing={isAnalyzing}
              onAnalyze={handleAnalyze}
              error={analyzeError}
            />

            {isAnalyzed && (
              <>
                <SearchBar onSubmit={handleQuery} isLoading={isQuerying} />
                {queryError && (
                  <p className="codeatlas-error">{queryError}</p>
                )}
                {queryResult && <ResultPanel result={queryResult} />}
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
