from pathlib import Path

from bench.model.config import BaseConfig
from bench.model.mode import BenchMode
from bench.repository.filesystem import (
    BASE_CONFIG_FILENAME,
    BENCH_DIR_NAME_DEFAULT,
    DIRECTORIES_PLACEHOLDER,
    POPULATE_AGENTS_PROMPT_FILENAME,
    PROMPTS_DIR_NAME,
    create_bench_scaffold,
    list_sibling_directories,
    load_yaml_file,
    read_prompt_file,
)
from bench.repository.opencode import run_command
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


def populate_agents_md(cwd: Path, model: str | None = None) -> None:
    """Populate .bench/AGENTS.md by running an AI agent to scan sibling directories.

    Args:
        cwd: The project root directory (where .bench/ lives).
        model: Optional model override. Falls back to models.task from base-config.yaml.

    Raises:
        RuntimeError: If opencode is not installed or returns a non-zero exit code.
    """
    # Phase 1: Detect directories
    directories = list_sibling_directories(cwd)
    if not directories:
        return

    # Phase 2: Load config for default model
    config_path = cwd / BENCH_DIR_NAME_DEFAULT / BASE_CONFIG_FILENAME
    raw_config = load_yaml_file(config_path)
    base_config = BaseConfig(**raw_config)
    resolved_model = model if model is not None else base_config.models.task

    # Phase 3: Build prompt
    prompt_path = (
        cwd
        / BENCH_DIR_NAME_DEFAULT
        / PROMPTS_DIR_NAME
        / POPULATE_AGENTS_PROMPT_FILENAME
    )
    raw_prompt = read_prompt_file(prompt_path)
    directory_lines = "\n".join(f"./{d}" for d in directories)
    prompt = raw_prompt.replace(DIRECTORIES_PLACEHOLDER, directory_lines)

    # Phase 4: Run agent
    exit_code = run_command(prompt, resolved_model, cwd)
    if exit_code != 0:
        raise RuntimeError(
            f"opencode exited with code {exit_code} during AGENTS.md population"
        )
