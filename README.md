# CodeAtlas AI

> LLM-Powered GitHub Codebase Mapping and Documentation Extension

CodeAtlas AI is a Chrome extension + FastAPI backend that lets developers ask plain-English questions about any GitHub repository and instantly receive accurate, file-referenced explanations powered by **Groq LLaMA 3** and vector search over the codebase.

---

## System Architecture

```
User opens GitHub repository
        ↓
Chrome Extension (content.js) detects repo
        ↓
User clicks "Analyze Repository" in sidebar
        ↓
Backend clones repository (git clone --depth 1)
        ↓
Code parsing with Tree-sitter (functions / classes)
        ↓
CodeBERT embedding generation
        ↓
FAISS vector index stored on disk
        ↓
User types question in sidebar
        ↓
Question embedding → FAISS semantic search
        ↓
Top chunks passed to Groq LLaMA 3 (RAG)
        ↓
Explanation + file references displayed in sidebar
```

---

## Folder Structure

```
codeatlas-ai/
├── extension/                  # Chrome extension
│   ├── manifest.json           # MV3 manifest
│   ├── content.js              # GitHub page detector
│   ├── background.js           # Service worker
│   └── sidebar/                # React sidebar (Vite)
│       ├── index.html
│       ├── vite.config.js
│       ├── package.json
│       └── src/
│           ├── main.jsx
│           ├── App.jsx
│           ├── App.css
│           └── components/
│               ├── RepoHeader.jsx
│               ├── SearchBar.jsx
│               └── ResultPanel.jsx
│
├── backend/                    # FastAPI backend
│   ├── main.py
│   ├── routes/
│   │   ├── repo_routes.py      # POST /api/analyze_repo
│   │   └── query_routes.py     # POST /api/query
│   └── services/
│       ├── repo_cloner.py      # git clone + cleanup
│       ├── repo_parser.py      # Tree-sitter AST parsing
│       └── code_explainer.py   # Groq LLM explanation
│
├── ai_pipeline/
│   ├── chunking/
│   │   └── code_chunker.py     # Function → chunk with metadata
│   ├── embeddings/
│   │   └── embedder.py         # CodeBERT embeddings
│   ├── vector_db/
│   │   └── faiss_index.py      # FAISS store + search
│   └── rag/
│       ├── retriever.py        # Post-process search results
│       └── generator.py        # Groq RAG generation
│
├── data/
│   └── cloned_repos/           # Temporary cloned repos
│
├── venv/                       # Python virtual environment
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- A [Groq API key](https://console.groq.com)

---

### 1 — Backend Setup

```bash
# Activate the virtual environment
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set your Groq API key
copy .env.example .env
# Edit .env and set GROQ_API_KEY=your_key_here

# Start the backend
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

### 2 — Extension Setup (React sidebar)

```bash
cd extension/sidebar
npm install
npm run build
```

This outputs the built React app into `extension/sidebar/dist/`.

---

### 3 — Load the Extension in Chrome

1. Open `chrome://extensions`
2. Enable **Developer Mode** (top right)
3. Click **Load unpacked**
4. Select the `extension/` folder
5. The **CodeAtlas AI** icon appears in the toolbar

---

## Usage

1. Navigate to any GitHub repository (e.g. `https://github.com/tiangolo/fastapi`)
2. Click the CodeAtlas AI toolbar icon → side panel opens
3. Click **Analyze Repository** — wait for indexing to complete
4. Type a question:
   - *"How does authentication work?"*
   - *"Where is the payment logic?"*
   - *"Which file generates the JWT token?"*
5. View the AI explanation with clickable file references

---

## Security

- Keep your `GROQ_API_KEY` in `.env` only. Never hardcode it in source files.
- Do not commit `.env` to Git. Add `.env` to `.gitignore` if not already present.
- Rotate API keys immediately if exposed in screenshots, logs, or commits.
- The extension UI stores user-entered API key data in `chrome.storage.local` (local browser storage only).
- `chrome.storage.local` is local to the user profile and is not synced to your backend automatically.
- Current backend LLM calls use `GROQ_API_KEY` from environment variables.

---

## Major Points

- Backend must be running before using the extension (`http://localhost:8000`).
- Clone + parse are optimized for source code and skip heavy folders (`.git`, `node_modules`, `venv`, `alphaenv`, etc.).
- FAISS indexes persist in `data/vector_indexes/` and can be reused across restarts.
- Repository analysis is limited by parser caps for speed:
  - `CODEATLAS_MAX_SOURCE_FILES` (default `250`)
  - `CODEATLAS_MAX_PARSED_BLOCKS` (default `800`)
- Windows-specific clone safeguards are enabled:
  - Git long paths enabled (`core.longpaths=true`)
  - Defensive clone directory cleanup
  - Unique work directory per clone run to avoid stale-folder conflicts


## API Reference

### `POST /api/analyze_repo`

```json
{
  "repo_url": "https://github.com/owner/repo"
}
```

**Response:**
```json
{
  "status": "success",
  "repo_name": "owner__repo",
  "total_chunks": 142,
  "message": "Repository 'owner__repo' analyzed and indexed successfully."
}
```

---

### `POST /api/query`

```json
{
  "question": "How does authentication work?",
  "repo_name": "owner__repo",
  "top_k": 5
}
```

**Response:**
```json
{
  "question": "How does authentication work?",
  "answer": "Authentication starts in routes/auth_controller.py ...",
  "references": [
    {
      "file_path": "services/auth_service.py",
      "function_name": "login_user",
      "language": "python",
      "snippet": "def login_user(...):"
    }
  ]
}
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq — LLaMA 3 70B |
| Embeddings | Microsoft CodeBERT (HuggingFace) |
| Vector DB | FAISS (faiss-cpu) |
| Backend | FastAPI + Uvicorn |
| Code Parsing | Tree-sitter |
| Extension | Chrome MV3 |
| Sidebar UI | React 18 + Vite |

---

## Development Notes

- The backend must be running on `http://localhost:8000` for the extension to work.
- `GROQ_API_KEY` must be set as an environment variable before starting the backend.
- Repository size is capped — extremely large monorepos may take longer to index.
- FAISS indexes are stored in `data/vector_indexes/` and survive server restarts.
