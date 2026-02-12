from enum import Enum

from pydantic import BaseModel


class FileStatus(str, Enum):
    """Git file change statuses."""

    MODIFIED = "modified"
    ADDED = "added"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"
    UNTRACKED = "untracked"
    TYPE_CHANGED = "type_changed"
    UNMERGED = "unmerged"


class GitFileChange(BaseModel):
    """A single file change entry from git status."""

    path: str
    status: FileStatus
    staged: bool


class GitStatus(BaseModel):
    """Parsed output of git status for a repository."""

    branch: str | None  # None if HEAD is detached
    files: list[GitFileChange]  # Tracked file changes (staged and unstaged)
    untracked: list[str]  # Untracked file paths
