import subprocess
from pathlib import Path

from bench.model.git import FileStatus, GitFileChange, GitStatus


GIT_EXECUTABLE: str = "git"

_STATUS_CODE_MAP: dict[str, FileStatus] = {
    "M": FileStatus.MODIFIED,
    "A": FileStatus.ADDED,
    "D": FileStatus.DELETED,
    "R": FileStatus.RENAMED,
    "C": FileStatus.COPIED,
    "T": FileStatus.TYPE_CHANGED,
}


def _run_git(args: list[str], repo_path: Path) -> subprocess.CompletedProcess[str]:
    """Execute a git command in the given repository directory.

    Args:
        args: Git subcommand and arguments (e.g., ["status", "--porcelain=v2"]).
        repo_path: Path to the git repository working directory.

    Returns:
        The completed subprocess result with captured stdout and stderr.

    Raises:
        RuntimeError: If git is not installed, repo_path is not a directory,
                      or the git command exits with a non-zero status.
    """
    if not repo_path.is_dir():
        raise RuntimeError(f"Not a directory: {repo_path}")

    try:
        result = subprocess.run(
            [GIT_EXECUTABLE, *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise RuntimeError(
            f"Git is not installed or not found on PATH (tried: {GIT_EXECUTABLE})"
        )

    if result.returncode != 0:
        cmd_str = " ".join([GIT_EXECUTABLE, *args])
        raise RuntimeError(
            f"Git command failed: {cmd_str}\n"
            f"Return code: {result.returncode}\n"
            f"stderr: {result.stderr.strip()}"
        )

    return result


def _parse_porcelain_status_code(code: str) -> FileStatus:
    """Map a single porcelain v2 status character to a FileStatus enum value.

    Args:
        code: A single character status code from git porcelain v2 output.

    Returns:
        The corresponding FileStatus enum value.

    Raises:
        ValueError: If the status code is not recognized.
    """
    status = _STATUS_CODE_MAP.get(code)
    if status is None:
        raise ValueError(f"Unrecognized git status code: {code!r}")
    return status


def git_status(repo_path: Path) -> GitStatus:
    """Get the parsed git status of a repository.

    Args:
        repo_path: Path to the git repository working directory.

    Returns:
        A GitStatus model with branch, file changes, and untracked files.

    Raises:
        RuntimeError: If the directory is not a git repo or git is unavailable.
    """
    result = _run_git(["status", "--porcelain=v2", "--branch"], repo_path)

    branch: str | None = None
    files: list[GitFileChange] = []
    untracked: list[str] = []

    for line in result.stdout.splitlines():
        if line.startswith("# branch.head "):
            head_value = line[len("# branch.head ") :]
            branch = None if head_value == "(detached)" else head_value

        elif line.startswith("1 "):
            # Ordinary changed entry: 1 <XY> <sub> <mH> <mI> <mW> <hH> <hI> <path>
            parts = line.split(" ", 8)
            xy = parts[1]
            path = parts[8]

            staged_code = xy[0]
            unstaged_code = xy[1]

            if staged_code != ".":
                files.append(
                    GitFileChange(
                        path=path,
                        status=_parse_porcelain_status_code(staged_code),
                        staged=True,
                    )
                )
            if unstaged_code != ".":
                files.append(
                    GitFileChange(
                        path=path,
                        status=_parse_porcelain_status_code(unstaged_code),
                        staged=False,
                    )
                )

        elif line.startswith("2 "):
            # Renamed/copied entry: 2 <XY> <sub> <mH> <mI> <mW> <hH> <hI> <X><score> <path>\t<origPath>
            parts = line.split(" ", 9)
            xy = parts[1]
            path_with_orig = parts[9]
            path = path_with_orig.split("\t")[0]

            staged_code = xy[0]
            unstaged_code = xy[1]

            if staged_code != ".":
                files.append(
                    GitFileChange(
                        path=path,
                        status=_parse_porcelain_status_code(staged_code),
                        staged=True,
                    )
                )
            if unstaged_code != ".":
                files.append(
                    GitFileChange(
                        path=path,
                        status=_parse_porcelain_status_code(unstaged_code),
                        staged=False,
                    )
                )

        elif line.startswith("u "):
            # Unmerged entry: u <XY> <sub> <m1> <m2> <m3> <mW> <h1> <h2> <h3> <path>
            parts = line.split(" ", 10)
            path = parts[10]
            files.append(
                GitFileChange(
                    path=path,
                    status=FileStatus.UNMERGED,
                    staged=False,
                )
            )

        elif line.startswith("? "):
            # Untracked entry: ? <path>
            untracked_path = line[2:]
            untracked.append(untracked_path)

    return GitStatus(branch=branch, files=files, untracked=untracked)


def is_git_repository(path: Path) -> bool:
    """Check if a directory is a git repository (or git worktree).

    Args:
        path: Path to check.

    Returns:
        True if the path is a git repository, False otherwise.
    """
    if not path.is_dir():
        return False
    try:
        _run_git(["rev-parse", "--git-dir"], path)
        return True
    except RuntimeError:
        return False


def list_local_branches(repo_path: Path) -> list[str]:
    """List all local branch names in a repository.

    Args:
        repo_path: Path to the git repository working directory.

    Returns:
        A list of local branch names.

    Raises:
        RuntimeError: If the directory is not a git repo or git is unavailable.
    """
    result = _run_git(["branch", "--format=%(refname:short)"], repo_path)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def create_branch(branch_name: str, repo_path: Path) -> None:
    """Create a new git branch without checking it out.

    Args:
        branch_name: Name of the branch to create.
        repo_path: Path to the git repository working directory.

    Raises:
        RuntimeError: If the branch already exists, the directory is not a
                      git repo, or git is unavailable.
    """
    _run_git(["branch", branch_name], repo_path)


def add_worktree(
    repo_path: Path,
    worktree_path: Path,
    branch_name: str,
    start_point: str | None = None,
    create_branch: bool = False,
) -> None:
    """Add a git worktree for a repository.

    When create_branch is True, creates a new branch starting from start_point:
        git worktree add -b <branch_name> <worktree_path> <start_point>

    When create_branch is False, checks out an existing branch:
        git worktree add <worktree_path> <branch_name>

    Args:
        repo_path: Path to the main git repository.
        worktree_path: Absolute path where the worktree should be created.
        branch_name: Name of the branch to checkout/create in the worktree.
        start_point: The commit/branch to start from (required when create_branch=True).
        create_branch: If True, create a new branch with -b flag.

    Raises:
        RuntimeError: If the git command fails.
        ValueError: If create_branch is True but start_point is None.
    """
    if create_branch:
        if start_point is None:
            raise ValueError("start_point is required when create_branch is True")
        args = [
            "worktree",
            "add",
            "-b",
            branch_name,
            str(worktree_path),
            start_point,
        ]
    else:
        args = ["worktree", "add", str(worktree_path), branch_name]
    _run_git(args, repo_path)


def remove_worktree(repo_path: Path, worktree_path: Path) -> None:
    """Remove a git worktree.

    Runs `git worktree remove <worktree_path>` from the main repository.
    Does NOT use --force; will fail if the worktree has uncommitted changes.

    Args:
        repo_path: Path to the main git repository.
        worktree_path: Absolute path of the worktree to remove.

    Raises:
        RuntimeError: If the git command fails (e.g., dirty worktree).
    """
    _run_git(["worktree", "remove", str(worktree_path)], repo_path)


def prune_worktrees(repo_path: Path) -> None:
    """Prune stale worktree references in a repository.

    Runs `git worktree prune` to clean up worktree administrative data
    for worktrees whose directories have been removed.

    Args:
        repo_path: Path to the main git repository.

    Raises:
        RuntimeError: If the git command fails.
    """
    _run_git(["worktree", "prune"], repo_path)


def branch_exists(branch_name: str, repo_path: Path) -> bool:
    """Check if a local branch exists in the repository.

    Args:
        branch_name: Name of the branch to check.
        repo_path: Path to the git repository.

    Returns:
        True if the branch exists locally, False otherwise.

    Raises:
        RuntimeError: If the directory is not a git repo or git is unavailable.
    """
    branches = list_local_branches(repo_path)
    return branch_name in branches


def delete_branch(branch_name: str, repo_path: Path) -> None:
    """Delete a local git branch.

    Runs `git branch -d <branch_name>` in the given repo directory.

    Args:
        branch_name: Name of the branch to delete.
        repo_path: Path to the git repository working directory.

    Raises:
        RuntimeError: If the git command fails (e.g., branch not found,
                      unmerged changes).
    """
    _run_git(["branch", "-d", branch_name], repo_path)


def _has_upstream(branch_name: str, repo_path: Path) -> bool:
    """Check if a branch has an upstream tracking branch configured.

    Args:
        branch_name: Name of the branch to check.
        repo_path: Path to the git repository working directory.

    Returns:
        True if the branch has an upstream configured, False otherwise.
    """
    try:
        _run_git(["config", "--get", f"branch.{branch_name}.remote"], repo_path)
        return True
    except RuntimeError:
        return False


def push_branch(branch_name: str, repo_path: Path) -> None:
    """Push a branch to origin with smart upstream tracking.

    Sets upstream (-u) on first push if no upstream is configured.
    Uses plain push if upstream is already set.

    Args:
        branch_name: Name of the branch to push.
        repo_path: Path to the git repository working directory.

    Raises:
        RuntimeError: If the push is rejected or fails for any reason.
    """
    if _has_upstream(branch_name, repo_path):
        _run_git(["push", "origin", branch_name], repo_path)
    else:
        _run_git(["push", "-u", "origin", branch_name], repo_path)
