from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class WorkbenchStatus(str, Enum):
    """Status of a workbench entry in base-config.yaml."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class WorkbenchFilter(str, Enum):
    """Filter mode for workbench listing."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ALL = "all"


class WorkbenchEntry(BaseModel):
    """A workbench entry as stored in base-config.yaml under the `workbenches` list."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    source: str
    git_branch: str = Field(alias="git-branch")
    status: WorkbenchStatus = WorkbenchStatus.ACTIVE
