from pydantic import BaseModel, ConfigDict, Field

from bench.model.source import Source, SourceRepo
from bench.model.workbench import WorkbenchEntry


class Models(BaseModel):
    """AI model configuration for coding agent tasks."""

    task: str = "anthropic/claude-opus-4-6"
    discuss: str = "anthropic/claude-opus-4-6"


class ImplementationStep(BaseModel):
    """A single step in the implementation workflow pipeline."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    prompt: str
    required_files: list[str] = Field(alias="required-files", default_factory=list)
    output_files: list[str] = Field(alias="output-files", default_factory=list)


class BaseConfig(BaseModel):
    """Schema for .bench/base-config.yaml (project root config)."""

    model_config = ConfigDict(populate_by_name=True)

    sources: list[Source] = []
    workbenches: list[WorkbenchEntry] = []
    models: Models = Field(default_factory=Models)
    implementation_flow_template: list[ImplementationStep] = Field(
        alias="implementation-flow-template", default_factory=list
    )


class WorkbenchConfig(BaseModel):
    """Schema for .bench/workbench-config.yaml (workbench-specific config)."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    source: str
    git_branch: str = Field(alias="git-branch")
    repos: list[SourceRepo] = []
    implementation_flow: list[ImplementationStep] = Field(
        alias="implementation-flow", default_factory=list
    )
