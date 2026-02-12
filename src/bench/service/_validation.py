from pathlib import Path

from bench.repository import is_git_repository, list_local_branches


def parse_repo_arg(repo_arg: str) -> tuple[str, str]:
    """Parse a --add-repo argument into (directory_name, branch_name).

    Args:
        repo_arg: The raw value, expected format 'directory-name:branch-name'.

    Returns:
        A tuple of (directory_name, branch_name).

    Raises:
        ValueError: If the format is invalid.
    """
    parts = repo_arg.split(":")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f'Invalid --add-repo format "{repo_arg}". '
            f"Expected format: directory-name:branch-name"
        )
    return parts[0], parts[1]


def validate_repo(dir_name: str, branch_name: str, root_path: Path) -> None:
    """Validate that a repo directory exists, is a git repo, and the branch exists.

    Args:
        dir_name: Name of the directory in the project root.
        branch_name: Name of the local git branch.
        root_path: Path to the project root.

    Raises:
        ValueError: If validation fails.
    """
    repo_path = root_path / dir_name

    if not repo_path.is_dir():
        raise ValueError(
            f'Repository directory "{dir_name}" does not exist '
            f"in project root: {root_path}"
        )

    if not is_git_repository(repo_path):
        raise ValueError(f'Directory "{dir_name}" is not a git repository')

    branches = list_local_branches(repo_path)
    if branch_name not in branches:
        available = ", ".join(branches) if branches else "(none)"
        raise ValueError(
            f'Branch "{branch_name}" does not exist in repository "{dir_name}". '
            f"Available local branches: {available}"
        )
