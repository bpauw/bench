from pydantic import BaseModel, ConfigDict, Field


class SourceRepo(BaseModel):
    """A single repository-to-branch mapping within a source."""

    model_config = ConfigDict(populate_by_name=True)

    dir: str
    source_branch: str = Field(alias="source-branch")


class Source(BaseModel):
    """A named source: a collection of repository-to-branch mappings."""

    name: str
    repos: list[SourceRepo] = []
