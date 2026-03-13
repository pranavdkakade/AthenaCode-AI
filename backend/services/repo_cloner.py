import os
import shutil
import subprocess
from urllib.parse import urlparse

# Maximum repository size allowed (in MB)
MAX_REPO_SIZE_MB = 500

# Directories to remove after cloning (irrelevant to code understanding)
IGNORED_DIRS = ["node_modules", ".git", "build", "dist", "__pycache__", ".next", "venv", ".venv"]

CLONE_BASE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cloned_repos")


def clone_repository(repo_url: str) -> tuple[str, str]:
    """
    Clones a public GitHub repository to the local data directory.

    Args:
        repo_url: Full GitHub repository URL.

    Returns:
        Tuple of (local_repo_path, repo_name).

    Raises:
        ValueError: For invalid URLs.
        RuntimeError: If cloning fails.
    """
    repo_name = extract_repo_name(repo_url)
    clone_dir = os.path.abspath(os.path.join(CLONE_BASE, repo_name))

    # Remove existing clone to ensure fresh state
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)

    os.makedirs(clone_dir, exist_ok=True)

    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, clone_dir],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"git clone failed: {result.stderr.strip()}")

    _cleanup_ignored_dirs(clone_dir)

    return clone_dir, repo_name


def extract_repo_name(repo_url: str) -> str:
    """Extracts 'owner__repo' from a GitHub URL for use as a directory name."""
    parsed = urlparse(repo_url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError(f"Cannot parse repository name from URL: {repo_url}")
    owner, repo = parts[0], parts[1].replace(".git", "")
    return f"{owner}__{repo}"


def _cleanup_ignored_dirs(base_path: str) -> None:
    """Recursively removes directories that are irrelevant to code analysis."""
    for root, dirs, _ in os.walk(base_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for d in list(dirs):
            full_path = os.path.join(root, d)
            if d in IGNORED_DIRS and os.path.exists(full_path):
                shutil.rmtree(full_path)
                dirs.remove(d)
