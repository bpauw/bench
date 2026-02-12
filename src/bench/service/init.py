from pathlib import Path

from bench.model.mode import BenchMode
from bench.repository.filesystem import create_bench_scaffold
from bench.service.mode_detection import detect_mode


def initialize_project(cwd: Path) -> list[str]:
    """Initialize a new bench project in the given directory.

    Args:
        cwd: The directory to initialize as a bench project root.

    Returns:
        A list of relative paths of created items.

    Raises:
        ValueError: If the directory is already part of a bench project.
    """
    context = detect_mode(cwd)

    if context.mode == BenchMode.ROOT:
        raise ValueError("This directory is already a bench project root.")
    elif context.mode == BenchMode.WORKBENCH:
        raise ValueError("Cannot initialize inside a workbench directory.")
    elif context.mode == BenchMode.WITHIN_ROOT:
        raise ValueError(
            f"Cannot initialize inside an existing bench project. "
            f"Project root is at: {context.root_path}"
        )

    return create_bench_scaffold(cwd)
