import os
import shutil
import stat
import subprocess
import platform
from uuid import uuid4
from urllib.parse import urlparse

# Maximum repository size allowed (in MB)
MAX_REPO_SIZE_MB = 500

# Directories to remove after cloning (irrelevant to code understanding)
IGNORED_DIRS = ["node_modules", ".git", "build", "dist", "__pycache__", ".next", "venv", ".venv", "alphaenv", "env", ".env"]

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
    os.makedirs(CLONE_BASE, exist_ok=True)
    clone_dir = os.path.abspath(
        os.path.join(CLONE_BASE, f"{repo_name}__work_{os.getpid()}_{uuid4().hex[:8]}")
    )

    # Enable long paths for Windows (git config core.longpaths true)
    # This allows cloning repositories with deep directory structures
    env = os.environ.copy()
    
    # Try to set git config to allow long paths
    subprocess.run(
        ["git", "config", "--global", "core.longpaths", "true"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Don't fail if config fails, just proceed with clone

    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, clone_dir],
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
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


def _force_remove_directory(dir_path: str) -> None:
    """
    Aggressively removes a directory, especially useful for removing 
    Windows-locked .git folders.
    """
    if not os.path.exists(dir_path):
        return
    
    # Try Python's shutil first with permission handling
    def on_error(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            func(path)
        except Exception:
            pass
    
    try:
        # Change all permissions first
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                try:
                    os.chmod(os.path.join(root, file), stat.S_IWRITE | stat.S_IREAD)
                except Exception:
                    pass
            for dir_name in dirs:
                try:
                    os.chmod(os.path.join(root, dir_name), stat.S_IWRITE | stat.S_IREAD)
                except Exception:
                    pass
        
        # Then remove
        shutil.rmtree(dir_path, onerror=on_error)
        return
    except Exception:
        pass
    
    # If Python fails and we're on Windows, try Windows command
    if platform.system() == "Windows":
        try:
            subprocess.run(
                ["cmd", "/c", "rmdir", "/s", "/q", dir_path],
                timeout=10,
                capture_output=True,
            )
            return
        except Exception:
            pass
    
    # If all else fails, at least try to rename (move to temp)
    try:
        temp_name = f"{dir_path}_to_delete_{os.getpid()}"
        os.rename(dir_path, temp_name)
    except Exception:
        # Give up but don't crash - directory will be handled by skip filters
        pass


def _cleanup_ignored_dirs(base_path: str) -> None:
    """Recursively removes directories that are irrelevant to code analysis."""
    
    # Priority order - remove largest/most problematic first
    priority_dirs = [".git", "venv", "alphaenv", "env", ".venv"]
    
    def remove_readonly(func, path, exc_info):
        """Windows error handler - remove read-only attribute before deletion."""
        try:
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            func(path)
        except Exception:
            pass
    
    def force_remove_dir(dir_path):
        """Aggressively remove directory on Windows."""
        try:
            # Change all file permissions first
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                    except Exception:
                        pass
                for dir_name in dirs:
                    try:
                        dir_file_path = os.path.join(root, dir_name)
                        os.chmod(dir_file_path, stat.S_IWRITE | stat.S_IREAD)
                    except Exception:
                        pass
            
            # Remove the directory
            shutil.rmtree(dir_path, onerror=remove_readonly)
            return True
        except Exception:
            pass
        
        # Try Windows command as fallback
        if platform.system() == "Windows":
            try:
                subprocess.run(
                    ["cmd", "/c", "rmdir", "/s", "/q", dir_path],
                    timeout=10,
                    capture_output=True,
                )
                return True
            except Exception:
                pass
        
        return False
    
    # First pass: remove priority (large/problematic) directories
    for root, dirs, _ in os.walk(base_path, topdown=True):
        for d in priority_dirs:
            if d in dirs:
                full_path = os.path.join(root, d)
                if os.path.exists(full_path):
                    force_remove_dir(full_path)
                    try:
                        dirs.remove(d)
                    except ValueError:
                        pass
    
    # Second pass: remove other ignored directories
    for root, dirs, _ in os.walk(base_path, topdown=True):
        for d in list(dirs):
            full_path = os.path.join(root, d)
            if d in IGNORED_DIRS and os.path.exists(full_path):
                force_remove_dir(full_path)
                try:
                    dirs.remove(d)
                except ValueError:
                    pass
