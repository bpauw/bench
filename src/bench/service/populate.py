from pathlib import Path

from bench.model.config import BaseConfig
from bench.model.mode import BenchMode
from bench.repository.filesystem import (
    BASE_CONFIG_FILENAME,
    BENCH_DIR_NAME_DEFAULT,
    DIRECTORIES_PLACEHOLDER,
    POPULATE_AGENTS_PROMPT_FILENAME,
    PROMPT_SEED_FILES,
    PROMPTS_DIR_NAME,
    list_repo_directories,
    list_sibling_directories,
    load_yaml_file,
    read_prompt_file,
)
from bench.repository.opencode import run_command
from bench.service.mode_detection import detect_mode


def populate_agents_md(
    cwd: Path, model: str | None = None, repos: list[str] | None = None
) -> None:
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
        repos: Optional list of repository names to include. If None or empty, all
               discovered repositories are included. Each name is validated against
               discovered directories.

    Raises:
        ValueError: If mode is UNINITIALIZED or WITHIN_ROOT, or if any repo name
                    in repos is not found among discovered directories.
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

    # Phase 3.5: Filter directories by requested repos (if specified)
    if repos is not None and len(repos) > 0:
        # Validate: all requested repos must exist in discovered directories
        available_dirs = set(directories)
        requested_dirs = set(repos)
        unknown_dirs = requested_dirs - available_dirs

        if unknown_dirs:
            unknown_list = ", ".join(sorted(unknown_dirs))
            available_list = ", ".join(sorted(directories))
            raise ValueError(
                f"Unknown repositories: {unknown_list}. Available: {available_list}"
            )

        # Filter: keep only requested directories, preserve sorted order
        directories = [d for d in directories if d in requested_dirs]

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


def populate_prompts(cwd: Path) -> dict[str, object]:
    """Synchronize on-disk prompt files with the canonical PROMPT_SEED_FILES templates.

    Compares each prompt file defined in PROMPT_SEED_FILES against its on-disk
    counterpart. Missing files are created, differing files are overwritten, and
    matching files are left untouched.

    Adapts behavior based on detected mode:
    - ROOT: Prompts directory is <root>/<bench_dir>/prompts/
    - WORKBENCH: Prompts directory is <cwd>/<bench_dir>/prompts/

    Args:
        cwd: The current working directory.

    Returns:
        A dict with per-file results and aggregate counts:
        - "results": list of dicts with "filename" and "status" keys
        - "created": count of newly created files
        - "updated": count of overwritten files
        - "up_to_date": count of files already matching their template

    Raises:
        ValueError: If mode is UNINITIALIZED or WITHIN_ROOT, or if the
                    prompts directory does not exist.
    """
    # Phase 1: Detect mode and validate
    context = detect_mode(cwd)

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError("Not inside a bench project. Run 'bench init' first.")
    if context.mode == BenchMode.WITHIN_ROOT:
        raise ValueError(
            "Cannot populate prompts from inside the project tree. "
            "Run this command from the project root or a workbench directory."
        )

    # Phase 2: Resolve prompts directory path
    if context.mode == BenchMode.ROOT:
        assert context.root_path is not None
        assert context.bench_dir_name is not None
        prompts_dir = context.root_path / context.bench_dir_name / PROMPTS_DIR_NAME
    else:
        # WORKBENCH mode
        assert context.bench_dir_name is not None
        prompts_dir = cwd / context.bench_dir_name / PROMPTS_DIR_NAME

    if not prompts_dir.is_dir():
        raise ValueError(
            f"Prompts directory not found: {prompts_dir}. "
            "The project may not be properly initialized."
        )

    # Phase 3: Compare and synchronize files
    results: list[dict[str, str]] = []

    for filename, template_content in PROMPT_SEED_FILES.items():
        file_path = prompts_dir / filename

        if not file_path.exists():
            # File missing -- create it
            file_path.write_text(template_content)
            results.append({"filename": filename, "status": "created"})
        else:
            # File exists -- compare trimmed content
            on_disk_content = file_path.read_text()
            if on_disk_content.rstrip() == template_content.rstrip():
                results.append({"filename": filename, "status": "up_to_date"})
            else:
                # Content differs -- overwrite
                file_path.write_text(template_content)
                results.append({"filename": filename, "status": "updated"})

    # Phase 4: Build and return summary dict
    created_count = sum(1 for r in results if r["status"] == "created")
    updated_count = sum(1 for r in results if r["status"] == "updated")
    up_to_date_count = sum(1 for r in results if r["status"] == "up_to_date")

    return {
        "results": results,
        "created": created_count,
        "updated": updated_count,
        "up_to_date": up_to_date_count,
    }
