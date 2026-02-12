from pathlib import Path

from bench.model import BenchMode
from bench.repository import (
    BASE_CONFIG_FILENAME,
    load_yaml_file,
    save_yaml_file,
)
from bench.model import Source
from bench.service._validation import parse_repo_arg, validate_repo
from bench.service.mode_detection import detect_mode


def list_sources() -> list[Source]:
    """List all sources from the base config.

    Returns:
        A list of Source model objects from the base config.

    Raises:
        ValueError: If mode is not ROOT.
    """
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. "
            "Run 'bench init' to create a bench project first."
        )
    if context.mode != BenchMode.ROOT:
        raise ValueError(
            "The 'source list' command can only be run from the project root directory."
        )

    assert context.base_config is not None
    return context.base_config.sources


def add_source(name: str, repo_args: list[str]) -> str:
    """Add a new source to the base config.

    Args:
        name: The name of the source to create.
        repo_args: List of raw --add-repo values in 'dir:branch' format.

    Returns:
        A success message string.

    Raises:
        ValueError: If mode is not ROOT, validation fails, or name is duplicate.
    """
    context = detect_mode(Path.cwd())

    # Enforce ROOT mode only
    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. "
            "Run 'bench init' to create a bench project first."
        )
    if context.mode != BenchMode.ROOT:
        raise ValueError(
            "The 'source add' command can only be run from the project root directory."
        )

    # At this point we're in ROOT mode — root_path and bench_dir_name are set
    assert context.root_path is not None
    assert context.bench_dir_name is not None

    # Phase 1: Parse all --add-repo arguments
    parsed_repos: list[tuple[str, str]] = []
    for repo_arg in repo_args:
        dir_name, branch_name = parse_repo_arg(repo_arg)
        parsed_repos.append((dir_name, branch_name))

    # Phase 2: Validate all repos (all-or-nothing — fail before writing anything)
    for dir_name, branch_name in parsed_repos:
        validate_repo(dir_name, branch_name, context.root_path)

    # Phase 3: Load existing config
    config_path = context.root_path / context.bench_dir_name / BASE_CONFIG_FILENAME
    data = load_yaml_file(config_path)

    # Ensure sources list exists
    if "sources" not in data:
        data["sources"] = []

    # Phase 4: Check for duplicate source name
    existing_names: list[str] = [
        s["name"] for s in data["sources"] if isinstance(s, dict) and "name" in s
    ]
    if name in existing_names:
        raise ValueError(
            f'Source "{name}" already exists. Source names must be unique.'
        )

    # Phase 5: Build and append the new source entry
    source_entry: dict[str, object] = {"name": name, "repos": []}
    if parsed_repos:
        source_entry["repos"] = [
            {"dir": dir_name, "source-branch": branch_name}
            for dir_name, branch_name in parsed_repos
        ]

    data["sources"].append(source_entry)

    # Phase 6: Write back
    save_yaml_file(config_path, data)

    return f'Source "{name}" added successfully'


def update_source(
    name: str, add_repo_args: list[str], remove_repo_args: list[str]
) -> str:
    """Update an existing source by removing and/or adding repository mappings.

    Removals are applied before additions, allowing a repo to be removed and
    re-added with a different branch in a single invocation.

    Args:
        name: The name of the source to update.
        add_repo_args: List of raw --add-repo values in 'dir:branch' format.
        remove_repo_args: List of raw --remove-repo values in 'dir:branch' format.

    Returns:
        A success message string summarising the changes.

    Raises:
        ValueError: If mode is not ROOT, source not found, validation fails,
            or no operations are specified.
    """
    context = detect_mode(Path.cwd())

    # Enforce ROOT mode only
    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. "
            "Run 'bench init' to create a bench project first."
        )
    if context.mode != BenchMode.ROOT:
        raise ValueError(
            "The 'source update' command can only be run from the project root directory."
        )

    # Require at least one operation
    if not add_repo_args and not remove_repo_args:
        raise ValueError("At least one --add-repo or --remove-repo option is required.")

    assert context.root_path is not None
    assert context.bench_dir_name is not None

    # Parse all arguments
    parsed_adds: list[tuple[str, str]] = []
    for arg in add_repo_args:
        dir_name, branch_name = parse_repo_arg(arg)
        parsed_adds.append((dir_name, branch_name))

    parsed_removes: list[tuple[str, str]] = []
    for arg in remove_repo_args:
        dir_name, branch_name = parse_repo_arg(arg)
        parsed_removes.append((dir_name, branch_name))

    # Load existing config
    config_path = context.root_path / context.bench_dir_name / BASE_CONFIG_FILENAME
    data = load_yaml_file(config_path)

    # Find the source by name
    source_entry: dict[str, object] | None = None
    for s in data.get("sources", []):
        if isinstance(s, dict) and s.get("name") == name:
            source_entry = s
            break

    if source_entry is None:
        existing_names = [
            s["name"]
            for s in data.get("sources", [])
            if isinstance(s, dict) and "name" in s
        ]
        available = ", ".join(existing_names) if existing_names else "(none)"
        raise ValueError(f'Source "{name}" not found. Available sources: {available}')

    repos_list: list[dict[str, str]] = source_entry.get("repos", [])

    # Phase: Validate removals (all-or-nothing)
    for dir_name, branch_name in parsed_removes:
        found = any(
            r.get("dir") == dir_name and r.get("source-branch") == branch_name
            for r in repos_list
        )
        if not found:
            available = ", ".join(
                f"{r['dir']}:{r['source-branch']}" for r in repos_list
            )
            raise ValueError(
                f'Repo "{dir_name}:{branch_name}" not found in source "{name}". '
                f"Available repos: {available or '(none)'}"
            )

    # Phase: Apply removals (create filtered list)
    remove_set = {(d, b) for d, b in parsed_removes}
    remaining_repos = [
        r
        for r in repos_list
        if (r.get("dir"), r.get("source-branch")) not in remove_set
    ]

    # Phase: Validate additions (against remaining repos after removal)
    existing_dirs = {r.get("dir") for r in remaining_repos}

    for dir_name, branch_name in parsed_adds:
        if dir_name in existing_dirs:
            raise ValueError(
                f'Repository directory "{dir_name}" already exists in source "{name}". '
                f"Remove it first or use a different directory."
            )
        validate_repo(dir_name, branch_name, context.root_path)
        existing_dirs.add(dir_name)  # prevent duplicates within the add list itself

    # Phase: Apply additions
    for dir_name, branch_name in parsed_adds:
        remaining_repos.append({"dir": dir_name, "source-branch": branch_name})

    source_entry["repos"] = remaining_repos

    # Save
    save_yaml_file(config_path, data)

    removed_count = len(parsed_removes)
    added_count = len(parsed_adds)
    parts: list[str] = []
    if removed_count:
        parts.append(f"removed {removed_count} repo(s)")
    if added_count:
        parts.append(f"added {added_count} repo(s)")

    return f'Source "{name}" updated: {", ".join(parts)}'


def remove_source(name: str) -> str:
    """Remove a source from the base config.

    Args:
        name: The name of the source to remove.

    Returns:
        A success message string.

    Raises:
        ValueError: If mode is not ROOT or source name is not found.
    """
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. "
            "Run 'bench init' to create a bench project first."
        )
    if context.mode != BenchMode.ROOT:
        raise ValueError(
            "The 'source remove' command can only be run from the project root directory."
        )

    assert context.root_path is not None
    assert context.bench_dir_name is not None

    config_path = context.root_path / context.bench_dir_name / BASE_CONFIG_FILENAME
    data = load_yaml_file(config_path)

    sources_list = data.get("sources", [])
    source_index: int | None = None
    for i, s in enumerate(sources_list):
        if isinstance(s, dict) and s.get("name") == name:
            source_index = i
            break

    if source_index is None:
        existing_names = [
            s["name"] for s in sources_list if isinstance(s, dict) and "name" in s
        ]
        available = ", ".join(existing_names) if existing_names else "(none)"
        raise ValueError(f'Source "{name}" not found. Available sources: {available}')

    del data["sources"][source_index]
    save_yaml_file(config_path, data)

    return f'Source "{name}" removed successfully'
