export default function ResultPanel({ result }) {
  const { question, answer, references } = result;

  function openFile(filePath) {
    // Could link to the GitHub file URL if repo context is added later
    navigator.clipboard.writeText(filePath).catch(() => {});
  }

  return (
    <div className="result-panel">
      <p className="result-panel__question">"{question}"</p>

      <div className="result-panel__answer">{answer}</div>

      {references && references.length > 0 && (
        <>
          <p className="result-panel__refs-title">
            Referenced Files ({references.length})
          </p>
          <div className="result-panel__refs">
            {references.map((ref, i) => (
              <div
                key={i}
                className="file-ref"
                onClick={() => openFile(ref.file_path)}
                title="Click to copy path"
              >
                <p className="file-ref__path">📄 {ref.file_path}</p>
                <p className="file-ref__func">⚙️ {ref.function_name}</p>
                {ref.snippet && (
                  <pre className="file-ref__snippet">{ref.snippet}</pre>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
