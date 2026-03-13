import { useState } from "react";

export default function SearchBar({ onSubmit, isLoading }) {
  const [question, setQuestion] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim() || isLoading) return;
    onSubmit(question.trim());
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) handleSubmit(e);
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <input
        className="search-bar__input"
        type="text"
        placeholder="How does authentication work?"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
        autoFocus
      />
      <button
        className="search-bar__btn"
        type="submit"
        disabled={isLoading || !question.trim()}
      >
        {isLoading ? "…" : "Ask"}
      </button>
    </form>
  );
}
