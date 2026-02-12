from pathlib import Path

from pydantic import BaseModel

from bench.model.config import BaseConfig, WorkbenchConfig
from bench.model.mode import BenchMode


class BenchContext(BaseModel):
    """The resolved runtime context for bench."""

    mode: BenchMode
    cwd: Path
    root_path: Path | None = None  # path to the project root (if found)
    bench_dir_name: str | None = None  # ".bench" or "bench" (whichever was found)
    base_config: BaseConfig | None = (
        None  # loaded root config (if in root/workbench/within_root)
    )
    workbench_config: WorkbenchConfig | None = (
        None  # loaded workbench config (if in workbench mode)
    )
