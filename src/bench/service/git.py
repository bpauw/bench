from pathlib import Path

from bench.model.git import GitStatus
from bench.repository.git import (
    create_branch,
    git_status,
    push_branch,
)


def get_git_status(repo_path: Path) -> GitStatus:
    """Get the git status of a repository.

    Args:
        repo_path: Path to the git repository working directory.

    Returns:
        A GitStatus model with branch, file changes, and untracked files.

    Raises:
        RuntimeError: If the directory is not a git repo or git is unavailable.
    """
    return git_status(repo_path)


def create_git_branch(branch_name: str, repo_path: Path) -> None:
    """Create a new git branch without switching to it.

    Args:
        branch_name: Name of the branch to create.
        repo_path: Path to the git repository working directory.

    Raises:
        RuntimeError: If the branch already exists or git fails.
    """
    create_branch(branch_name, repo_path)


def push_git_branch(branch_name: str, repo_path: Path) -> None:
    """Push a branch to origin with smart upstream tracking.

    Args:
        branch_name: Name of the branch to push.
        repo_path: Path to the git repository working directory.

    Raises:
        RuntimeError: If the push is rejected or fails.
    """
    push_branch(branch_name, repo_path)
