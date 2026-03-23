export default function RepoHeader({ repo, isAnalyzed, isAnalyzing, onAnalyze, error }) {
  return (
    <div className="repo-header">
      <p className="repo-header__name">
        <a href={repo.repoUrl} target="_blank" rel="noreferrer">
          {repo.owner}/{repo.repo}
        </a>
      </p>

      {!isAnalyzed ? (
        <>
          <button
            className="btn-analyze"
            onClick={onAnalyze}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? "Analyzing repository…" : "Analyze Repository"}
          </button>
          {error && <p className="codeatlas-error" style={{ marginTop: 8 }}>{error}</p>}
        </>
      ) : (
        <p className="repo-header__success">✅ Repository analyzed — ask anything below!</p>
      )}
    </div>
  );
}
