import { useState, useEffect } from "react";
import "./ApiKeySettings.css";

export default function ApiKeySettings() {
  const [apiKey, setApiKey] = useState("");
  const [tempApiKey, setTempApiKey] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Load API key from chrome.storage.local on mount
  useEffect(() => {
    if (typeof chrome !== "undefined" && chrome.storage) {
      chrome.storage.local.get("gpt_api_key", (data) => {
        if (data.gpt_api_key) {
          setApiKey(data.gpt_api_key);
          setTempApiKey(data.gpt_api_key);
        }
      });
    }
  }, []);

  // Save API key to chrome.storage.local
  function handleSaveApiKey() {
    if (!tempApiKey.trim()) {
      setMessage("API key cannot be empty");
      return;
    }

    setIsLoading(true);
    setMessage("");

    if (typeof chrome !== "undefined" && chrome.storage) {
      chrome.storage.local.set(
        { gpt_api_key: tempApiKey },
        () => {
          setApiKey(tempApiKey);
          setMessage("✓ API key saved successfully!");
          setShowForm(false);

          // Clear message after 3 seconds
          setTimeout(() => setMessage(""), 3000);
          setIsLoading(false);
        }
      );
    } else {
      setMessage("Chrome storage not available");
      setIsLoading(false);
    }
  }

  // Handle clearing/removing API key
  function handleClearApiKey() {
    if (typeof chrome !== "undefined" && chrome.storage) {
      chrome.storage.local.remove("gpt_api_key", () => {
        setApiKey("");
        setTempApiKey("");
        setShowForm(false);
        setMessage("✓ API key removed");
        setTimeout(() => setMessage(""), 2000);
      });
    }
  }

  return (
    <div className="api-key-settings">
      <div className="api-key-header">
        <h3 className="api-key-title">LLM API Key</h3>
        {apiKey && <span className="api-key-status">✓ Saved</span>}
      </div>

      {!showForm ? (
        <div className="api-key-buttons">
          <button
            className="api-key-btn api-key-btn-primary"
            onClick={() => setShowForm(true)}
          >
            {apiKey ? "Change API Key" : "Set API Key"}
          </button>
          {apiKey && (
            <button
              className="api-key-btn api-key-btn-secondary"
              onClick={handleClearApiKey}
            >
              Remove
            </button>
          )}
        </div>
      ) : (
        <div className="api-key-form">
          <label className="api-key-label" htmlFor="api-key-input">
            Enter your LLM API Key (Groq, OpenAI, etc.):
          </label>
          <input
            id="api-key-input"
            type="password"
            className="api-key-input"
            placeholder="Paste your API key here..."
            value={tempApiKey}
            onChange={(e) => setTempApiKey(e.target.value)}
          />
          <p className="api-key-info">
            📌 Your API key is stored locally in your browser. Never shared with anyone.
          </p>
          <div className="api-key-form-buttons">
            <button
              className="api-key-btn api-key-btn-primary"
              onClick={handleSaveApiKey}
              disabled={isLoading}
            >
              {isLoading ? "Saving..." : "Save"}
            </button>
            <button
              className="api-key-btn api-key-btn-tertiary"
              onClick={() => {
                setShowForm(false);
                setTempApiKey(apiKey);
                setMessage("");
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {message && <p className="api-key-message">{message}</p>}
    </div>
  );
}
