from pathlib import Path

from bench.model.config import BaseConfig
from bench.model.mode import BenchMode
from bench.repository.filesystem import (
    BASE_CONFIG_FILENAME,
    BENCH_DIR_NAME_DEFAULT,
    BENCH_SUBDIR_NAME,
    GITKEEP_FILENAME,
    MAPS_DIR_NAME,
    MAPS_LOCATION_PLACEHOLDER,
    MAP_INIT_PROMPT_FILENAME,
    MAP_UPDATE_PROMPT_FILENAME,
    METAMAP_FILENAME,
    PROMPTS_DIR_NAME,
    REPOSITORIES_PLACEHOLDER,
    list_repo_directories,
    list_sibling_directories,
    load_yaml_file,
    read_prompt_file,
    render_repositories_block,
)
from bench.repository.opencode import run_command
from bench.service.mode_detection import detect_mode


def init_maps(
    cwd: Path, model: str | None = None, only_repos: list[str] | None = None
) -> None:
    """Initialize maps for repositories.

    Args:
        cwd: The current working directory.
        model: Optional model override. Falls back to models.map from base-config.yaml.
        only_repos: Optional list of repo names to limit mapping to.

    Raises:
        ValueError: If mode is invalid, maps already initialized, or repo names invalid.
        RuntimeError: If opencode is not installed or returns non-zero.
    """
    # Phase 1: Detect mode and validate
    context = detect_mode(cwd)

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError("Not inside a bench project. Run 'bench init' first.")
    if context.mode == BenchMode.WITHIN_ROOT:
        raise ValueError(
            "Cannot initialize maps from inside the project tree. "
            "Run this command from the project root or a workbench directory."
        )

    # Phase 2: Resolve paths (maps dir, prompts dir, cwd for execution)
    if context.mode == BenchMode.ROOT:
        assert context.root_path is not None
        assert context.bench_dir_name is not None
        maps_dir = context.root_path / context.bench_dir_name / MAPS_DIR_NAME
        prompts_dir = context.root_path / context.bench_dir_name / PROMPTS_DIR_NAME
        opencode_cwd = context.root_path
        maps_location = f"{context.bench_dir_name}/{MAPS_DIR_NAME}"
    else:
        # WORKBENCH mode
        assert context.bench_dir_name is not None
        maps_dir = cwd / BENCH_SUBDIR_NAME / MAPS_DIR_NAME
        prompts_dir = cwd / BENCH_SUBDIR_NAME / PROMPTS_DIR_NAME
        opencode_cwd = cwd
        maps_location = f"{BENCH_SUBDIR_NAME}/{MAPS_DIR_NAME}"

    # Phase 3: Check maps not already initialized (metamap.md must NOT exist)
    metamap_path = maps_dir / METAMAP_FILENAME
    if metamap_path.exists():
        raise ValueError(
            "Maps are already initialized. Use 'bench map update' to update existing maps."
        )

    # Phase 4: Discover repos (mode-dependent) and filter by --only-repo
    if context.mode == BenchMode.ROOT:
        assert context.root_path is not None
        directories = list_sibling_directories(context.root_path)
    else:
        directories = list_repo_directories(cwd)

    if not directories:
        raise ValueError("No repositories found to map.")

    if only_repos is not None and len(only_repos) > 0:
        available_dirs = set(directories)
        requested_dirs = set(only_repos)
        unknown_dirs = requested_dirs - available_dirs

        if unknown_dirs:
            unknown_list = ", ".join(sorted(unknown_dirs))
            available_list = ", ".join(sorted(directories))
            raise ValueError(
                f"Unknown repositories: {unknown_list}. Available: {available_list}"
            )

        directories = [d for d in directories if d in requested_dirs]

    # Phase 5: Create repo subdirectories under maps/ with .gitkeep files
    for repo_name in directories:
        repo_map_dir = maps_dir / repo_name
        repo_map_dir.mkdir(parents=True, exist_ok=True)
        gitkeep = repo_map_dir / GITKEEP_FILENAME
        if not gitkeep.exists():
            gitkeep.touch()

    # Phase 6: Load config, resolve model (--model override or base_config.models.map)
    if context.base_config is not None:
        base_config = context.base_config
    else:
        assert context.root_path is not None
        config_path = context.root_path / BENCH_DIR_NAME_DEFAULT / BASE_CONFIG_FILENAME
        raw_config = load_yaml_file(config_path)
        base_config = BaseConfig(**raw_config)

    resolved_model = model if model is not None else base_config.models.map

    # Phase 7: Load and substitute prompt template
    prompt_path = prompts_dir / MAP_INIT_PROMPT_FILENAME
    raw_prompt = read_prompt_file(prompt_path)

    repos_block = render_repositories_block(directories)
    prompt = raw_prompt.replace(MAPS_LOCATION_PLACEHOLDER, maps_location)
    prompt = prompt.replace(REPOSITORIES_PLACEHOLDER, repos_block)

    # Phase 8: Execute headlessly via run_command()
    exit_code = run_command(prompt, resolved_model, opencode_cwd)
    if exit_code != 0:
        raise RuntimeError(
            f"opencode exited with code {exit_code} during map initialization"
        )


def update_maps(
    cwd: Path, model: str | None = None, only_repos: list[str] | None = None
) -> None:
    """Update existing maps for repositories.

    Args:
        cwd: The current working directory.
        model: Optional model override. Falls back to models.map from base-config.yaml.
        only_repos: Optional list of repo names to limit update to.

    Raises:
        ValueError: If mode is invalid, maps not initialized, repo names invalid,
                    or map directories missing.
        RuntimeError: If opencode is not installed or returns non-zero.
    """
    # Phase 1: Detect mode and validate
    context = detect_mode(cwd)

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError("Not inside a bench project. Run 'bench init' first.")
    if context.mode == BenchMode.WITHIN_ROOT:
        raise ValueError(
            "Cannot update maps from inside the project tree. "
            "Run this command from the project root or a workbench directory."
        )

    # Phase 2: Resolve paths
    if context.mode == BenchMode.ROOT:
        assert context.root_path is not None
        assert context.bench_dir_name is not None
        maps_dir = context.root_path / context.bench_dir_name / MAPS_DIR_NAME
        prompts_dir = context.root_path / context.bench_dir_name / PROMPTS_DIR_NAME
        opencode_cwd = context.root_path
        maps_location = f"{context.bench_dir_name}/{MAPS_DIR_NAME}"
    else:
        # WORKBENCH mode
        assert context.bench_dir_name is not None
        maps_dir = cwd / BENCH_SUBDIR_NAME / MAPS_DIR_NAME
        prompts_dir = cwd / BENCH_SUBDIR_NAME / PROMPTS_DIR_NAME
        opencode_cwd = cwd
        maps_location = f"{BENCH_SUBDIR_NAME}/{MAPS_DIR_NAME}"

    # Phase 3: Check maps ARE initialized (metamap.md must exist)
    metamap_path = maps_dir / METAMAP_FILENAME
    if not metamap_path.exists():
        raise ValueError("Maps have not been initialized. Run 'bench map init' first.")

    # Phase 4: Discover repos and filter by --only-repo
    if context.mode == BenchMode.ROOT:
        assert context.root_path is not None
        directories = list_sibling_directories(context.root_path)
    else:
        directories = list_repo_directories(cwd)

    if not directories:
        raise ValueError("No repositories found to update maps for.")

    if only_repos is not None and len(only_repos) > 0:
        available_dirs = set(directories)
        requested_dirs = set(only_repos)
        unknown_dirs = requested_dirs - available_dirs

        if unknown_dirs:
            unknown_list = ", ".join(sorted(unknown_dirs))
            available_list = ", ".join(sorted(directories))
            raise ValueError(
                f"Unknown repositories: {unknown_list}. Available: {available_list}"
            )

        directories = [d for d in directories if d in requested_dirs]

    # Phase 5: Validate map directories exist for all targeted repos
    missing_dirs = [d for d in directories if not (maps_dir / d).is_dir()]
    if missing_dirs:
        missing_list = ", ".join(sorted(missing_dirs))
        raise ValueError(
            f"Map directories missing for: {missing_list}. "
            "Run 'bench map init' for these repositories first."
        )

    # Phase 6: Load config, resolve model
    if context.base_config is not None:
        base_config = context.base_config
    else:
        assert context.root_path is not None
        config_path = context.root_path / BENCH_DIR_NAME_DEFAULT / BASE_CONFIG_FILENAME
        raw_config = load_yaml_file(config_path)
        base_config = BaseConfig(**raw_config)

    resolved_model = model if model is not None else base_config.models.map

    # Phase 7: Load and substitute prompt template
    prompt_path = prompts_dir / MAP_UPDATE_PROMPT_FILENAME
    raw_prompt = read_prompt_file(prompt_path)

    repos_block = render_repositories_block(directories)
    prompt = raw_prompt.replace(MAPS_LOCATION_PLACEHOLDER, maps_location)
    prompt = prompt.replace(REPOSITORIES_PLACEHOLDER, repos_block)

    # Phase 8: Execute headlessly via run_command()
    exit_code = run_command(prompt, resolved_model, opencode_cwd)
    if exit_code != 0:
        raise RuntimeError(f"opencode exited with code {exit_code} during map update")
