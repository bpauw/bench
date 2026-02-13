from pathlib import Path

from bench.model.config import BaseConfig
from bench.model.mode import BenchMode
from bench.repository.filesystem import (
    BASE_CONFIG_FILENAME,
    BENCH_DIR_NAME_DEFAULT,
    DIRECTORIES_PLACEHOLDER,
    POPULATE_AGENTS_PROMPT_FILENAME,
    PROMPTS_DIR_NAME,
    list_repo_directories,
    list_sibling_directories,
    load_yaml_file,
    read_prompt_file,
)
from bench.repository.opencode import run_command
from bench.service.mode_detection import detect_mode


def populate_agents_md(cwd: Path, model: str | None = None) -> None:
    """Populate AGENTS.md by running an AI agent to scan relevant directories.

    Adapts behavior based on detected mode:
    - ROOT: Scans sibling directories, writes to <bench_dir>/AGENTS.md,
      reads prompt from <bench_dir>/prompts/, resolves config from root.
    - WORKBENCH: Scans repo/ subdirectories, writes to <bench_dir>/AGENTS.md
      (workbench's own bench dir), reads prompt from workbench's bench prompts/,
      resolves config from project root.

    Args:
        cwd: The current working directory.
        model: Optional model override. Falls back to models.task from base-config.yaml.

    Raises:
        ValueError: If mode is UNINITIALIZED or WITHIN_ROOT.
        RuntimeError: If opencode is not installed or returns a non-zero exit code.
    """
    # Phase 1: Detect mode and validate
    context = detect_mode(cwd)

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError("Not inside a bench project. Run 'bench init' first.")
    if context.mode == BenchMode.WITHIN_ROOT:
        raise ValueError(
            "Cannot populate AGENTS.md from inside the project tree. "
            "Run this command from the project root or a workbench directory."
        )

    # Phase 2: Resolve paths (AGENTS.md target, prompts dir, directories to scan)
    if context.mode == BenchMode.ROOT:
        assert context.root_path is not None
        assert context.bench_dir_name is not None
        bench_dir_name = context.bench_dir_name
        prompts_dir = context.root_path / bench_dir_name / PROMPTS_DIR_NAME
        opencode_cwd = context.root_path
    else:
        # WORKBENCH mode
        assert context.bench_dir_name is not None
        bench_dir_name = context.bench_dir_name
        prompts_dir = cwd / bench_dir_name / PROMPTS_DIR_NAME
        opencode_cwd = cwd

    # Phase 3: Discover directories
    if context.mode == BenchMode.ROOT:
        assert context.root_path is not None
        directories = list_sibling_directories(context.root_path)
    else:
        # WORKBENCH mode: list subdirectories of repo/
        directories = list_repo_directories(cwd)

    if not directories:
        return

    # Phase 4: Load config and resolve model
    if context.base_config is not None:
        base_config = context.base_config
    else:
        # Fallback: load config directly (should not happen for ROOT/WORKBENCH)
        assert context.root_path is not None
        config_path = context.root_path / BENCH_DIR_NAME_DEFAULT / BASE_CONFIG_FILENAME
        raw_config = load_yaml_file(config_path)
        base_config = BaseConfig(**raw_config)

    resolved_model = model if model is not None else base_config.models.task

    # Phase 5: Build prompt from template
    prompt_path = prompts_dir / POPULATE_AGENTS_PROMPT_FILENAME
    raw_prompt = read_prompt_file(prompt_path)
    directory_lines = "\n".join(f"./{d}" for d in directories)
    prompt = raw_prompt.replace(DIRECTORIES_PLACEHOLDER, directory_lines)

    # Phase 6: Run opencode agent
    exit_code = run_command(prompt, resolved_model, opencode_cwd)
    if exit_code != 0:
        raise RuntimeError(
            f"opencode exited with code {exit_code} during AGENTS.md population"
        )
