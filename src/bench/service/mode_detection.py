from pathlib import Path

from bench.model.config import BaseConfig, WorkbenchConfig
from bench.model.context import BenchContext
from bench.model.mode import BenchMode
from bench.repository.filesystem import (
    BASE_CONFIG_FILENAME,
    find_bench_root,
    find_workbench_marker,
    load_yaml_file,
)


def _load_base_config(root_path: Path, bench_dir_name: str) -> BaseConfig:
    """Load and validate the base config from a project root."""
    config_path = root_path / bench_dir_name / BASE_CONFIG_FILENAME
    data = load_yaml_file(config_path)
    return BaseConfig(**data)


def _load_workbench_config(config_path: Path) -> WorkbenchConfig:
    """Load and validate the workbench config."""
    data = load_yaml_file(config_path)
    return WorkbenchConfig(**data)


def detect_mode(cwd: Path) -> BenchContext:
    """Detect the current bench mode based on the working directory.

    Algorithm:
    1. Check if CWD is a workbench (has workbench-config.yaml)
    2. Check if CWD is a project root (has base-config.yaml)
    3. Search upward from CWD for a project root
    4. If nothing found, return UNINITIALIZED

    The workbench check comes first because a workbench directory contains
    a .bench folder with workbench-config.yaml, and we need to distinguish
    it from a root which has base-config.yaml.
    """
    resolved_cwd = cwd.resolve()

    # 1. Check if CWD is a workbench
    workbench_result = find_workbench_marker(resolved_cwd)
    if workbench_result is not None:
        wb_config_path, wb_dir_name = workbench_result
        workbench_config = _load_workbench_config(wb_config_path)

        # Also search upward for the project root (start from parent to skip CWD itself)
        base_config: BaseConfig | None = None
        root_path: Path | None = None
        bench_dir_name: str = wb_dir_name

        root_result = find_bench_root(resolved_cwd.parent)
        if root_result is not None:
            root_path, bench_dir_name = root_result
            base_config = _load_base_config(root_path, bench_dir_name)

        return BenchContext(
            mode=BenchMode.WORKBENCH,
            cwd=resolved_cwd,
            root_path=root_path,
            bench_dir_name=wb_dir_name,
            base_config=base_config,
            workbench_config=workbench_config,
        )

    # 2. Check if CWD is a project root
    root_result = find_bench_root(resolved_cwd)
    if root_result is not None:
        root_path, bench_dir_name = root_result

        if root_path == resolved_cwd:
            # CWD is the project root itself
            base_config = _load_base_config(root_path, bench_dir_name)
            return BenchContext(
                mode=BenchMode.ROOT,
                cwd=resolved_cwd,
                root_path=root_path,
                bench_dir_name=bench_dir_name,
                base_config=base_config,
            )

        # 3. CWD is inside a project root
        base_config = _load_base_config(root_path, bench_dir_name)
        return BenchContext(
            mode=BenchMode.WITHIN_ROOT,
            cwd=resolved_cwd,
            root_path=root_path,
            bench_dir_name=bench_dir_name,
            base_config=base_config,
        )

    # 4. Nothing found
    return BenchContext(
        mode=BenchMode.UNINITIALIZED,
        cwd=resolved_cwd,
    )
