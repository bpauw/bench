import shutil
from pathlib import Path
from typing import Any

import yaml

# The canonical and fallback bench directory names
BENCH_DIR_NAMES: list[str] = [".bench", "bench"]

BASE_CONFIG_FILENAME: str = "base-config.yaml"
WORKBENCH_CONFIG_FILENAME: str = "workbench-config.yaml"

# Default bench directory name used when creating new structures
BENCH_DIR_NAME_DEFAULT: str = ".bench"

# Subdirectory and file names for bench scaffolding
WORKBENCH_DIR_NAME: str = "workbench"
FILES_DIR_NAME: str = "files"
SCRIPTS_DIR_NAME: str = "scripts"
PROMPTS_DIR_NAME: str = "prompts"
AGENTS_MD_FILENAME: str = "AGENTS.md"
GITKEEP_FILENAME: str = ".gitkeep"

# Subdirectory and file names for workbench creation
HISTORY_MD_FILENAME: str = "history.md"
DISCUSSIONS_DIR_NAME: str = "discussions"
TASKS_DIR_NAME: str = "tasks"
BENCH_SUBDIR_NAME: str = "bench"
REPO_DIR_NAME: str = "repo"

# Task scaffold file names
TASK_YAML_FILENAME: str = "task.yaml"
SPEC_MD_FILENAME: str = "spec.md"
FILES_MD_FILENAME: str = "files.md"
IMPL_MD_FILENAME: str = "impl.md"
NOTES_MD_FILENAME: str = "notes.md"
TASK_PLACEHOLDER: str = "{{TASK}}"
REPOSITORIES_PLACEHOLDER: str = "{{REPOSITORIES}}"

SPEC_TEMPLATE: str = """\
# Spec

## Introduction

## Goals

## Specification
"""

AGENTS_MD_TEMPLATE: str = """\
# Project Instructions

## Sources

<!-- Define your source repository-to-branch mappings here -->

## Workbench Guidelines

<!-- Guidelines for working within workbenches -->

## Conventions

<!-- Project-specific coding conventions and standards -->
"""

# Discuss prompt seed
DISCUSS_PROMPT_FILENAME: str = "discuss.md"

# Prompt seed file names
TASK_CREATE_SPEC_FILENAME: str = "task-create-spec.md"
TASK_REFINE_SPEC_FILENAME: str = "task-refine-spec.md"
TASK_WRITE_IMPL_DOCS_FILENAME: str = "task-write-impl-docs.md"
TASK_DO_IMPL_FILENAME: str = "task-do-impl.md"
TASK_UPDATE_CHANGE_DOCS_FILENAME: str = "task-update-change-docs.md"

# Prompt seed templates
TASK_CREATE_SPEC_TEMPLATE: str = """\
agents.md: ./AGENTS.md
task-dir: ./bench/tasks/{{TASK}}
task-spec: {task-dir}/spec.md

{{REPOSITORIES}}

<spec-template>

# Spec

## Introduction

## Goals

## Specification

</spec-template>

Tasks:

- Read AGENTS.md
- Start a back and forth with the user to define a specification document
  - Ensure that task-spec is specific enough
    - Spend a lot of effort on this and try very hard to make sure the spec has everything it needs
  - Keep asking the user questions until you have enough information
    - Once you have all the required information, update task-spec with the clarified spec details
- Once all interactions are complete, let the user know they can exit opencode
"""

TASK_REFINE_SPEC_TEMPLATE: str = """\
agents.md: ./AGENTS.md
task-dir: ./bench/tasks/{{TASK}}
task-spec: {task-dir}/spec.md

{{REPOSITORIES}}

Tasks:

- Read AGENTS.md
- Read task-spec
  - Ensure that task-spec is specific enough
    - Spend a lot of effort on this and try very hard to make sure the spec has everything it needs
  - If it is not specific enough, ask the user questions until you have enough information
    - Once you have all the required information, update task-spec with the clarified spec details
"""

TASK_WRITE_IMPL_DOCS_TEMPLATE: str = """\
agents.md: ./AGENTS.md
task-dir: ./bench/tasks/{{TASK}}
task-spec: {task-dir}/spec.md
task-implementation-plan: {task-dir}/impl.md
task-notes: {task-dir}/notes.md
files-list: {task-dir}/files.md

{{REPOSITORIES}}

Tasks:

- Read AGENTS.md
- Read task-spec
- Create an implementation plan that describes in accurate detail how this spec will be implemented
  - Write out the plan comprehensively in task-implementation-plan
- Put any miscellaneous notes in task-notes
- Create a list of files that will be effected and place them in files-list
  - Organize the markdown file so that it is easy to understand how to find the files in question
"""

TASK_DO_IMPL_TEMPLATE: str = """\
agents.md: ./AGENTS.md
task-dir: ./bench/tasks/{{TASK}}
task-spec: {task-dir}/spec.md
task-implementation-plan: {task-dir}/impl.md
task-notes: {task-dir}/notes.md
files-list: {task-dir}/files.md

{{REPOSITORIES}}

Tasks:

- Read AGENTS.md
- Read task-spec, task-implementation-plan, task-notes, files-list
- Implement the feature as described by task-implementation-plan
"""

TASK_UPDATE_CHANGE_DOCS_TEMPLATE: str = """\
agents.md: ./AGENTS.md
task-dir: ./bench/tasks/{{TASK}}
task-spec: {task-dir}/spec.md
task-implementation-plan: {task-dir}/impl.md
task-notes: {task-dir}/notes.md

{{REPOSITORIES}}

Tasks:

- Within each repo:
    - Use git diff OR git diff HEAD~1 to discover changes
    - If CHANGELOG.md exists:
        - Update CHANGELOG.md with a summary of all changes that have been made
        - Keep the summary high level and not too granular
    - If README.md exists:
        - Comprehensively update README.md so that it incorporates all of the changes that have been made
        - Focus on adding a lot of detail to user interactions with the program

Notes:

- Only read the top 200 lines of CHANGELOG.md
"""

DISCUSS_PROMPT_TEMPLATE: str = """\
discussions-dir: ./bench/discussions

{{REPOSITORIES}}

You are having a free-form discussion with the user. Talk with the user about whatever they want to discuss. Be helpful, thorough, and engage in back-and-forth conversation.

When the user indicates the conversation is complete (e.g., says "done", "that's all", "thanks", "exit", etc.):

1. Generate a short, descriptive title for this discussion (3-7 words, lowercase with hyphens, no special characters)
2. Write a detailed summary of the entire conversation to a markdown file at: ./bench/discussions/YYYYMMDD - <title>.md
   - YYYYMMDD should be today's date
   - The summary should capture:
     - The main topics discussed
     - Key decisions or conclusions reached
     - Any action items or follow-ups identified
     - Important context or reasoning discussed
3. Let the user know the summary has been saved and they can exit opencode
"""

# Default implementation flow template (written into base-config.yaml at init)
DEFAULT_IMPLEMENTATION_FLOW_TEMPLATE: list[dict[str, str | list[str]]] = [
    {
        "name": "Writing implementation docs",
        "prompt": TASK_WRITE_IMPL_DOCS_FILENAME,
        "required-files": [SPEC_MD_FILENAME],
        "output-files": [IMPL_MD_FILENAME],
    },
    {
        "name": "Implementing",
        "prompt": TASK_DO_IMPL_FILENAME,
        "required-files": [SPEC_MD_FILENAME, IMPL_MD_FILENAME],
        "output-files": [],
    },
    {
        "name": "Updating change docs",
        "prompt": TASK_UPDATE_CHANGE_DOCS_FILENAME,
        "required-files": [SPEC_MD_FILENAME, IMPL_MD_FILENAME],
        "output-files": [],
    },
]

# Consolidated mapping of prompt seed filenames to their template content
PROMPT_SEED_FILES: dict[str, str] = {
    TASK_CREATE_SPEC_FILENAME: TASK_CREATE_SPEC_TEMPLATE,
    TASK_REFINE_SPEC_FILENAME: TASK_REFINE_SPEC_TEMPLATE,
    TASK_WRITE_IMPL_DOCS_FILENAME: TASK_WRITE_IMPL_DOCS_TEMPLATE,
    TASK_DO_IMPL_FILENAME: TASK_DO_IMPL_TEMPLATE,
    TASK_UPDATE_CHANGE_DOCS_FILENAME: TASK_UPDATE_CHANGE_DOCS_TEMPLATE,
    DISCUSS_PROMPT_FILENAME: DISCUSS_PROMPT_TEMPLATE,
}


def find_bench_root(start: Path) -> tuple[Path, str] | None:
    """Walk upward from `start` to the filesystem root looking for a bench project root.

    At each directory, checks for `.bench/base-config.yaml` first (canonical),
    then `bench/base-config.yaml` (fallback).

    Returns:
        A tuple of (root_path, bench_dir_name) if found, or None.
    """
    current = start.resolve()

    while True:
        for dir_name in BENCH_DIR_NAMES:
            config_path = current / dir_name / BASE_CONFIG_FILENAME
            if config_path.is_file():
                return (current, dir_name)

        parent = current.parent
        if parent == current:
            # Reached filesystem root
            break
        current = parent

    return None


def find_workbench_marker(directory: Path) -> tuple[Path, str] | None:
    """Check if the given directory contains a workbench config marker.

    Checks for `.bench/workbench-config.yaml` first (canonical),
    then `bench/workbench-config.yaml` (fallback).

    Returns:
        A tuple of (config_path, bench_dir_name) if found, or None.
    """
    resolved = directory.resolve()

    for dir_name in BENCH_DIR_NAMES:
        config_path = resolved / dir_name / WORKBENCH_CONFIG_FILENAME
        if config_path.is_file():
            return (config_path, dir_name)

    return None


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Read and parse a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
        ValueError: If the YAML file is empty or does not contain a mapping.
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"YAML file is empty: {path}")

    if not isinstance(data, dict):
        raise ValueError(f"YAML file does not contain a mapping: {path}")

    return data


def save_yaml_file(path: Path, data: dict[str, Any]) -> None:
    """Write a dictionary to a YAML file.

    Args:
        path: Path to the YAML file.
        data: Dictionary to serialize as YAML.

    Raises:
        OSError: If the file cannot be written.
    """
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def remove_workbench_workspace(workspace_path: Path) -> None:
    """Remove the workbench workspace directory tree.

    Deletes <project-root>/workbench/<name> entirely.

    Args:
        workspace_path: Path to the workbench workspace directory.

    Raises:
        FileNotFoundError: If the directory does not exist.
        OSError: If the directory cannot be removed.
    """
    if not workspace_path.is_dir():
        raise FileNotFoundError(f"Directory does not exist: {workspace_path}")
    shutil.rmtree(workspace_path)


def create_bench_scaffold(root_path: Path) -> list[str]:
    """Create the .bench directory structure for a new bench project.

    Creates:
        - .bench/
        - .bench/base-config.yaml (with empty sources)
        - .bench/files/ (with .gitkeep)
        - .bench/prompts/ (with .gitkeep)
        - .bench/scripts/ (with .gitkeep)
        - .bench/workbench/ (with .gitkeep)
        - .bench/AGENTS.md (with template content)

    Args:
        root_path: The project root directory.

    Returns:
        A list of relative paths (strings) of created items, for display purposes.

    Raises:
        OSError: If directory/file creation fails.
    """
    bench_dir = root_path / BENCH_DIR_NAME_DEFAULT
    created: list[str] = []

    # Create .bench/ directory
    bench_dir.mkdir()
    created.append(f"{BENCH_DIR_NAME_DEFAULT}/")

    # Write base-config.yaml
    config_path = bench_dir / BASE_CONFIG_FILENAME
    # Note: the "task" default is duplicated in model/config.py (Models.task).
    # The architecture forbids repository from importing model, so the value
    # appears in both places intentionally.
    save_yaml_file(
        config_path,
        {
            "sources": [],
            "models": {
                "task": "anthropic/claude-opus-4-6",
                "discuss": "anthropic/claude-opus-4-6",
            },
            "implementation-flow-template": DEFAULT_IMPLEMENTATION_FLOW_TEMPLATE,
        },
    )
    created.append(f"{BENCH_DIR_NAME_DEFAULT}/{BASE_CONFIG_FILENAME}")

    # Create subdirectories with .gitkeep files
    for subdir_name in [
        FILES_DIR_NAME,
        PROMPTS_DIR_NAME,
        SCRIPTS_DIR_NAME,
        WORKBENCH_DIR_NAME,
    ]:
        subdir = bench_dir / subdir_name
        subdir.mkdir()
        created.append(f"{BENCH_DIR_NAME_DEFAULT}/{subdir_name}/")

        gitkeep = subdir / GITKEEP_FILENAME
        gitkeep.touch()
        created.append(f"{BENCH_DIR_NAME_DEFAULT}/{subdir_name}/{GITKEEP_FILENAME}")

    # Write prompt seed files into .bench/prompts/
    prompts_dir = bench_dir / PROMPTS_DIR_NAME
    for filename, content in PROMPT_SEED_FILES.items():
        prompt_path = prompts_dir / filename
        prompt_path.write_text(content)
        created.append(f"{BENCH_DIR_NAME_DEFAULT}/{PROMPTS_DIR_NAME}/{filename}")

    # Write AGENTS.md
    agents_path = bench_dir / AGENTS_MD_FILENAME
    agents_path.write_text(AGENTS_MD_TEMPLATE)
    created.append(f"{BENCH_DIR_NAME_DEFAULT}/{AGENTS_MD_FILENAME}")

    return created


def create_workbench_scaffold(
    root_path: Path,
    bench_dir_name: str,
    workbench_name: str,
    workbench_config_data: dict[str, Any],
) -> list[str]:
    """Create the .bench/workbench/<name>/ directory structure.

    Creates:
        - <bench_dir>/workbench/<name>/
        - <bench_dir>/workbench/<name>/AGENTS.md (copied from <bench_dir>/AGENTS.md)
        - <bench_dir>/workbench/<name>/bench/
        - <bench_dir>/workbench/<name>/bench/workbench-config.yaml
        - <bench_dir>/workbench/<name>/bench/history.md
        - <bench_dir>/workbench/<name>/bench/discussions/ (with .gitkeep)
        - <bench_dir>/workbench/<name>/bench/tasks/ (with .gitkeep)
        - <bench_dir>/workbench/<name>/bench/files/ (copied from <bench_dir>/files/)
        - <bench_dir>/workbench/<name>/bench/prompts/ (copied from <bench_dir>/prompts/)
        - <bench_dir>/workbench/<name>/bench/scripts/ (copied from <bench_dir>/scripts/)

    Args:
        root_path: The project root directory.
        bench_dir_name: The bench directory name (".bench" or "bench").
        workbench_name: The name of the workbench.
        workbench_config_data: Dict to serialize as workbench-config.yaml.

    Returns:
        A list of relative paths (strings) of created items.

    Raises:
        OSError: If directory/file creation fails.
        FileNotFoundError: If source AGENTS.md doesn't exist.
    """
    bench_dir = root_path / bench_dir_name
    wb_dir = bench_dir / WORKBENCH_DIR_NAME / workbench_name
    wb_bench_dir = wb_dir / BENCH_SUBDIR_NAME
    rel_prefix = f"{bench_dir_name}/{WORKBENCH_DIR_NAME}/{workbench_name}"
    created: list[str] = []

    # 1. Create workbench directory
    wb_dir.mkdir(parents=True)
    created.append(f"{rel_prefix}/")

    # 2. Copy AGENTS.md from bench dir
    src_agents = bench_dir / AGENTS_MD_FILENAME
    shutil.copy2(src_agents, wb_dir / AGENTS_MD_FILENAME)
    created.append(f"{rel_prefix}/{AGENTS_MD_FILENAME}")

    # 3. Create bench subdirectory
    wb_bench_dir.mkdir()
    created.append(f"{rel_prefix}/{BENCH_SUBDIR_NAME}/")

    # 4. Write workbench-config.yaml
    save_yaml_file(wb_bench_dir / WORKBENCH_CONFIG_FILENAME, workbench_config_data)
    created.append(f"{rel_prefix}/{BENCH_SUBDIR_NAME}/{WORKBENCH_CONFIG_FILENAME}")

    # 5. Create empty history.md
    (wb_bench_dir / HISTORY_MD_FILENAME).write_text("")
    created.append(f"{rel_prefix}/{BENCH_SUBDIR_NAME}/{HISTORY_MD_FILENAME}")

    # 6. Create discussions/ with .gitkeep
    discussions_dir = wb_bench_dir / DISCUSSIONS_DIR_NAME
    discussions_dir.mkdir()
    (discussions_dir / GITKEEP_FILENAME).touch()
    created.append(f"{rel_prefix}/{BENCH_SUBDIR_NAME}/{DISCUSSIONS_DIR_NAME}/")

    # 7. Create tasks/ with .gitkeep
    tasks_dir = wb_bench_dir / TASKS_DIR_NAME
    tasks_dir.mkdir()
    (tasks_dir / GITKEEP_FILENAME).touch()
    created.append(f"{rel_prefix}/{BENCH_SUBDIR_NAME}/{TASKS_DIR_NAME}/")

    # 8-10. Copy files/, prompts/, scripts/ from bench dir
    for subdir_name in [FILES_DIR_NAME, PROMPTS_DIR_NAME, SCRIPTS_DIR_NAME]:
        src_dir = bench_dir / subdir_name
        dst_dir = wb_bench_dir / subdir_name
        shutil.copytree(src_dir, dst_dir)
        created.append(f"{rel_prefix}/{BENCH_SUBDIR_NAME}/{subdir_name}/")

    return created


def create_workbench_workspace(
    root_path: Path,
    bench_dir_name: str,
    workbench_name: str,
) -> list[str]:
    """Create the workbench/<name>/ workspace directory with symlinks.

    Creates:
        - workbench/<name>/
        - workbench/<name>/AGENTS.md  -> symlink to <bench_dir>/workbench/<name>/AGENTS.md
        - workbench/<name>/bench      -> symlink to <bench_dir>/workbench/<name>/bench
        - workbench/<name>/repo/

    Symlinks use relative paths for portability.

    Args:
        root_path: The project root directory.
        bench_dir_name: The bench directory name (".bench" or "bench").
        workbench_name: The name of the workbench.

    Returns:
        A list of relative paths (strings) of created items.

    Raises:
        OSError: If directory/symlink creation fails.
    """
    ws_dir = root_path / WORKBENCH_DIR_NAME / workbench_name
    rel_prefix = f"{WORKBENCH_DIR_NAME}/{workbench_name}"
    created: list[str] = []

    # 1. Create workspace directory (and parent workbench/ if needed)
    ws_dir.mkdir(parents=True)
    created.append(f"{rel_prefix}/")

    # 2. Symlink for AGENTS.md
    # From workbench/<name>/AGENTS.md -> ../../<bench_dir>/workbench/<name>/AGENTS.md
    agents_target = Path(
        f"../../{bench_dir_name}/{WORKBENCH_DIR_NAME}/{workbench_name}/{AGENTS_MD_FILENAME}"
    )
    (ws_dir / AGENTS_MD_FILENAME).symlink_to(agents_target)
    created.append(f"{rel_prefix}/{AGENTS_MD_FILENAME}")

    # 3. Symlink for bench/
    # From workbench/<name>/bench -> ../../<bench_dir>/workbench/<name>/bench
    bench_target = Path(
        f"../../{bench_dir_name}/{WORKBENCH_DIR_NAME}/{workbench_name}/{BENCH_SUBDIR_NAME}"
    )
    (ws_dir / BENCH_SUBDIR_NAME).symlink_to(bench_target)
    created.append(f"{rel_prefix}/{BENCH_SUBDIR_NAME}")

    # 4. Create repo/ directory
    (ws_dir / REPO_DIR_NAME).mkdir()
    created.append(f"{rel_prefix}/{REPO_DIR_NAME}/")

    return created


def create_task_scaffold(
    tasks_dir: Path,
    task_folder_name: str,
    task_name: str,
) -> list[str]:
    """Create a task folder with metadata and template files.

    Creates:
        - <tasks_dir>/<task_folder_name>/
        - <tasks_dir>/<task_folder_name>/task.yaml
        - <tasks_dir>/<task_folder_name>/spec.md
        - <tasks_dir>/<task_folder_name>/files.md
        - <tasks_dir>/<task_folder_name>/impl.md
        - <tasks_dir>/<task_folder_name>/notes.md

    Args:
        tasks_dir: The absolute path to the workbench's bench/tasks/ directory.
        task_folder_name: The full folder name (e.g., "20260208 - add-auth").
        task_name: The task name (e.g., "add-auth").

    Returns:
        A list of relative paths (strings) of created items, for display purposes.

    Raises:
        OSError: If directory/file creation fails.
    """
    task_dir = tasks_dir / task_folder_name
    created: list[str] = []

    # Create the task folder
    task_dir.mkdir(parents=True)
    created.append(f"{task_folder_name}/")

    # Write task.yaml
    save_yaml_file(
        task_dir / TASK_YAML_FILENAME,
        {"name": task_name, "completed": None},
    )
    created.append(f"{task_folder_name}/{TASK_YAML_FILENAME}")

    # Write spec.md with template
    (task_dir / SPEC_MD_FILENAME).write_text(SPEC_TEMPLATE)
    created.append(f"{task_folder_name}/{SPEC_MD_FILENAME}")

    # Create empty files
    for filename in [FILES_MD_FILENAME, IMPL_MD_FILENAME, NOTES_MD_FILENAME]:
        (task_dir / filename).write_text("")
        created.append(f"{task_folder_name}/{filename}")

    return created


def list_task_names(tasks_dir: Path) -> list[str]:
    """List existing task names from a tasks directory.

    Scans subdirectories matching the 'YYYYMMDD - <name>' pattern and extracts
    the task name portion.

    Args:
        tasks_dir: The absolute path to the workbench's bench/tasks/ directory.

    Returns:
        A list of task name strings (the portion after 'YYYYMMDD - ').
    """
    if not tasks_dir.is_dir():
        return []

    names: list[str] = []
    for entry in tasks_dir.iterdir():
        if not entry.is_dir():
            continue
        parts = entry.name.split(" - ", maxsplit=1)
        if len(parts) == 2 and len(parts[0]) == 8 and parts[0].isdigit():
            names.append(parts[1])
    return names


def list_task_entries(tasks_dir: Path) -> list[dict[str, Any]]:
    """Scan the tasks directory and return raw task entry data.

    For each subdirectory matching the 'YYYYMMDD - <name>' pattern:
    - Loads and parses task.yaml (skips the entry if missing/malformed)
    - Checks existence and non-emptiness of spec.md, impl.md, files.md
    - Extracts the creation date from the folder name prefix

    Args:
        tasks_dir: The absolute path to the workbench's bench/tasks/ directory.

    Returns:
        A list of dicts, each containing:
        - "name": str (task name from task.yaml)
        - "folder_name": str (full folder name)
        - "created_date": str (YYYYMMDD from folder prefix)
        - "completed": str | None (from task.yaml)
        - "has_spec": bool
        - "has_impl": bool
        - "has_files": bool

        Entries are returned in no guaranteed order; sorting is the service layer's responsibility.
    """
    if not tasks_dir.is_dir():
        return []

    entries: list[dict[str, Any]] = []
    for entry in tasks_dir.iterdir():
        if not entry.is_dir():
            continue
        parts = entry.name.split(" - ", maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 8 or not parts[0].isdigit():
            continue

        # Try to load task.yaml; skip on any error
        try:
            raw_data = load_yaml_file(entry / TASK_YAML_FILENAME)
        except FileNotFoundError, ValueError, yaml.YAMLError:
            continue

        task_name = raw_data.get("name", parts[1])

        entries.append(
            {
                "name": task_name,
                "folder_name": entry.name,
                "created_date": parts[0],
                "completed": raw_data.get("completed"),
                "has_spec": task_file_exists_and_nonempty(entry, SPEC_MD_FILENAME),
                "has_impl": task_file_exists_and_nonempty(entry, IMPL_MD_FILENAME),
                "has_files": task_file_exists_and_nonempty(entry, FILES_MD_FILENAME),
            }
        )

    return entries


def find_task_folder(tasks_dir: Path, task_name: str) -> tuple[Path, str]:
    """Resolve a task name to its folder path within the tasks directory.

    Scans subdirectories matching the 'YYYYMMDD - <name>' pattern where
    the <name> portion matches the given task_name.

    Args:
        tasks_dir: The absolute path to the workbench's bench/tasks/ directory.
        task_name: The task name to search for (e.g., "add-auth").

    Returns:
        A tuple of (task_folder_path, task_folder_name).

    Raises:
        ValueError: If no matching task is found.
        ValueError: If multiple tasks match (includes folder names for disambiguation).
    """
    matches: list[tuple[Path, str]] = []

    if tasks_dir.is_dir():
        for entry in tasks_dir.iterdir():
            if not entry.is_dir():
                continue
            parts = entry.name.split(" - ", maxsplit=1)
            if len(parts) == 2 and len(parts[0]) == 8 and parts[0].isdigit():
                if parts[1] == task_name:
                    matches.append((entry, entry.name))

    if len(matches) == 0:
        raise ValueError(f'Task "{task_name}" not found in this workbench.')

    if len(matches) > 1:
        names = ", ".join(m[1] for m in matches)
        raise ValueError(
            f'Multiple tasks match "{task_name}": {names}. '
            f"Please specify the full folder name."
        )

    return matches[0]


def task_spec_exists(task_folder: Path) -> bool:
    """Check whether a task folder contains a spec.md file.

    Args:
        task_folder: Absolute path to the task folder.

    Returns:
        True if spec.md exists, False otherwise.
    """
    return (task_folder / SPEC_MD_FILENAME).is_file()


def task_file_exists_and_nonempty(task_folder: Path, filename: str) -> bool:
    """Check whether a file in a task folder exists and is non-empty.

    Args:
        task_folder: Absolute path to the task folder.
        filename: The filename to check (e.g., "spec.md", "impl.md").

    Returns:
        True if the file exists and has non-zero length, False otherwise.
    """
    filepath = task_folder / filename
    return filepath.is_file() and filepath.stat().st_size > 0


def load_task_yaml(task_folder: Path) -> dict[str, Any]:
    """Load and return the task.yaml file from a task folder as a dict.

    Args:
        task_folder: Absolute path to the task folder.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If task.yaml does not exist in the folder.
        ValueError: If task.yaml is empty or does not contain a mapping.
        yaml.YAMLError: If task.yaml contains invalid YAML.
    """
    yaml_path = task_folder / TASK_YAML_FILENAME
    if not yaml_path.is_file():
        raise FileNotFoundError(f"task.yaml not found in {task_folder}")
    return load_yaml_file(yaml_path)


def save_task_yaml(task_folder: Path, data: dict[str, Any]) -> None:
    """Write task data to the task.yaml file in a task folder.

    Args:
        task_folder: Absolute path to the task folder.
        data: Dictionary to serialize as YAML.

    Raises:
        OSError: If the file cannot be written.
    """
    save_yaml_file(task_folder / TASK_YAML_FILENAME, data)


def read_prompt_file(prompt_path: Path) -> str:
    """Read a prompt template file and return its contents.

    Args:
        prompt_path: Absolute path to the prompt file.

    Returns:
        The prompt file contents as a string.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    return prompt_path.read_text()


def list_discussion_files(discussions_dir: Path) -> list[dict[str, str]]:
    """Scan the discussions directory for .md files and return parsed metadata.

    For each .md file matching the 'YYYYMMDD - <title>.md' pattern:
    - Extracts the date prefix (YYYYMMDD)
    - Extracts the title portion

    Args:
        discussions_dir: Absolute path to the discussions directory.

    Returns:
        A list of dicts with keys "filename", "name", "created_date".
        Entries are returned in no guaranteed order.
    """
    if not discussions_dir.is_dir():
        return []

    entries: list[dict[str, str]] = []
    for entry in discussions_dir.iterdir():
        if not entry.is_file() or entry.suffix != ".md":
            continue
        stem = entry.stem
        parts = stem.split(" - ", maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 8 or not parts[0].isdigit():
            continue
        entries.append(
            {
                "filename": entry.name,
                "name": parts[1],
                "created_date": parts[0],
            }
        )

    return entries


def render_repositories_block(repo_dirs: list[str]) -> str:
    """Render a <repositories> block from a list of repo directory names.

    Args:
        repo_dirs: List of repository directory names (e.g., ["service-repo", "client-repo"]).

    Returns:
        A string containing the <repositories> block with ./repo/<dir> paths.
    """
    lines = [f"./repo/{d}" for d in repo_dirs]
    inner = "\n".join(lines)
    if inner:
        return f"<repositories>\n{inner}\n</repositories>"
    return "<repositories>\n</repositories>"
