import datetime
from enum import Enum

from pydantic import BaseModel


class TaskConfig(BaseModel):
    """Schema for a task's task.yaml metadata file."""

    name: str
    completed: str | None = None


class TaskFilter(str, Enum):
    """Filter mode for task listing."""

    OPEN = "open"
    COMPLETED = "completed"
    ALL = "all"


class TaskEntry(BaseModel):
    """A single task entry enriched with metadata for list display."""

    name: str
    folder_name: str
    created_date: datetime.date
    completed: str | None = None
    has_spec: bool = False
    has_impl: bool = False
    has_files: bool = False
