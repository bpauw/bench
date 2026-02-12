from pydantic import BaseModel


class OpenCodeResult(BaseModel):
    """Result of an opencode CLI execution."""

    stdout: str
    stderr: str
    return_code: int
