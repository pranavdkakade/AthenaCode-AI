import os
from typing import List, Dict

# tree-sitter language bindings
try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjs

    PY_LANGUAGE = Language(tspython.language())
    JS_LANGUAGE = Language(tsjs.language())
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

# File extensions mapped to language labels
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".php": "php",
}

MAX_FILE_SIZE_BYTES = 500_000  # 500 KB — skip very large generated files
MAX_SOURCE_FILES = int(os.environ.get("CODEATLAS_MAX_SOURCE_FILES", "250"))
MAX_PARSED_BLOCKS = int(os.environ.get("CODEATLAS_MAX_PARSED_BLOCKS", "800"))
SKIP_PATH_PARTS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "coverage",
    "target",
    "vendor",
    ".next",
}


def parse_repository(repo_path: str) -> List[Dict]:
    """
    Walks the repository and extracts function/class/method blocks.

    Returns:
        List of dicts with keys: file_path, function_name, code, language.
    """
    results = []
    scanned_files = 0

    for root, dirs, files in os.walk(repo_path):
        # Skip hidden and bulky directories that do not help code understanding.
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_PATH_PARTS]

        for filename in files:
            if scanned_files >= MAX_SOURCE_FILES or len(results) >= MAX_PARSED_BLOCKS:
                return results

            ext = os.path.splitext(filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            if filename.endswith(".min.js") or filename.endswith(".bundle.js"):
                continue

            full_path = os.path.join(root, filename)
            if os.path.getsize(full_path) > MAX_FILE_SIZE_BYTES:
                continue

            scanned_files += 1

            language = SUPPORTED_EXTENSIONS[ext]
            relative_path = os.path.relpath(full_path, repo_path).replace("\\", "/")

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
            except OSError:
                continue

            if TREE_SITTER_AVAILABLE and language == "python":
                functions = _extract_python_functions(source, relative_path)
            else:
                # Fallback: treat the whole file as a single chunk
                functions = [
                    {
                        "file_path": relative_path,
                        "function_name": filename,
                        "code": source,
                        "language": language,
                    }
                ]

            results.extend(functions)
            if len(results) >= MAX_PARSED_BLOCKS:
                return results

    return results


def _extract_python_functions(source: str, file_path: str) -> List[Dict]:
    """Uses tree-sitter to extract individual Python functions and classes."""
    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(bytes(source, "utf8"))
    root_node = tree.root_node

    blocks = []
    _walk_tree(root_node, source, file_path, blocks)
    return blocks


def _walk_tree(node, source: str, file_path: str, blocks: list) -> None:
    """Recursively walks AST nodes collecting function and class definitions."""
    if node.type in ("function_definition", "class_definition"):
        name_node = node.child_by_field_name("name")
        func_name = name_node.text.decode("utf8") if name_node else "unknown"
        code_snippet = source[node.start_byte: node.end_byte]
        blocks.append(
            {
                "file_path": file_path,
                "function_name": func_name,
                "code": code_snippet,
                "language": "python",
            }
        )
        return  # Don't recurse into nested functions here — they'll appear as separate chunks

    for child in node.children:
        _walk_tree(child, source, file_path, blocks)
