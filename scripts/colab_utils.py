"""Colab notebook helpers: clone, run, publish artifacts back to GitHub.

See scaffold/colab/README.md for setup and PAT instructions.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_URL = "https://github.com/jonasneves/aipi590-challenge-3.git"
DEFAULT_REPO_DIR = Path("/content/aipi590-challenge-3")
TOKEN_SECRET_NAME = "GITHUB_TOKEN_AIPI590_CHALLENGE_3"


def prepare_notebook(
    repo_dir: str | Path = DEFAULT_REPO_DIR,
    branch: str = "main",
) -> Path:
    """Clone the repo into Colab workspace if needed. Returns repo root."""
    repo_path = Path(repo_dir)
    if not repo_path.exists():
        env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
        subprocess.run(
            ["git", "clone", "--depth=1", "--branch", branch, REPO_URL, str(repo_path)],
            check=True, env=env,
        )

    if str(repo_path) not in sys.path:
        sys.path.insert(0, str(repo_path))

    os.chdir(repo_path)
    return repo_path


def publish_artifacts(
    paths: Iterable[str | Path],
    message: str,
    repo_dir: str | Path = DEFAULT_REPO_DIR,
    branch: str = "main",
) -> bool:
    """Commit and push generated artifacts from Colab back to GitHub.

    Requires a Colab secret named GITHUB_TOKEN_AIPI590_CHALLENGE_3 with repo
    write access scoped to jonasneves (not personal account). Returns True when
    a commit was created and pushed.
    """
    try:
        from google.colab import userdata
    except ImportError as exc:
        raise RuntimeError("publish_artifacts only works from Google Colab.") from exc

    token = userdata.get(TOKEN_SECRET_NAME)
    if not token:
        raise RuntimeError(
            f"Missing Colab secret {TOKEN_SECRET_NAME}. "
            "Add it in Colab: key icon (left sidebar) → Add secret."
        )

    repo_path = Path(repo_dir)
    rel_paths = [str(Path(p)) for p in paths]

    missing = [p for p in rel_paths if not (repo_path / p).exists()]
    if missing:
        raise FileNotFoundError(f"Cannot publish — files not found: {', '.join(missing)}")

    repo_url_parts = REPO_URL.replace("https://", "").rstrip(".git")
    authed_url = f"https://x-access-token:{token}@{repo_url_parts}.git"

    subprocess.run(["git", "config", "user.email", "colab-bot@scaffold"], check=True, cwd=repo_path)
    subprocess.run(["git", "config", "user.name", "Colab Bot"], check=True, cwd=repo_path)
    subprocess.run(["git", "remote", "set-url", "origin", authed_url], check=True, cwd=repo_path)

    if (repo_path / ".git" / "shallow").exists():
        subprocess.run(["git", "fetch", "--unshallow", "origin", branch], check=True, cwd=repo_path)

    subprocess.run(["git", "add", "--", *rel_paths], check=True, cwd=repo_path)

    diff = subprocess.run(["git", "diff", "--cached", "--quiet", "--", *rel_paths], cwd=repo_path)
    if diff.returncode == 0:
        print("No artifact changes to commit.")
        return False

    subprocess.run(["git", "commit", "-m", f"{message} [skip ci]"], check=True, cwd=repo_path)
    subprocess.run(["git", "push", "origin", branch], check=True, cwd=repo_path)
    print(f"Pushed: {', '.join(rel_paths)}")
    return True
