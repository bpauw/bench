import datetime
from pathlib import Path

from bench.model.config import ImplementationStep, WorkbenchConfig
from bench.model.mode import BenchMode
from bench.model.task import TaskConfig, TaskEntry, TaskFilter
from bench.repository.filesystem import (
    BENCH_SUBDIR_NAME,
    DISCUSSIONS_DIR_NAME,
    DISCUSSIONS_PLACEHOLDER,
    PROMPTS_DIR_NAME,
    REPOSITORIES_PLACEHOLDER,
    SPEC_MD_FILENAME,
    TASK_CREATE_SPEC_FILENAME,
    TASK_PLACEHOLDER,
    TASK_REFINE_SPEC_FILENAME,
    TASKS_DIR_NAME,
    build_discussion_block,
    create_task_scaffold,
    find_task_folder,
    inject_discussions_into_spec,
    list_task_entries,
    list_task_names,
    load_task_yaml,
    read_prompt_file,
    render_repositories_block,
    resolve_discussion_paths,
    save_task_yaml,
    task_file_exists_and_nonempty,
    task_spec_exists,
)
from bench.repository.opencode import run_command, run_prompt_interactive
from bench.service.mode_detection import detect_mode


def _substitute_prompt_placeholders(
    raw_prompt: str,
    task_folder_name: str,
    workbench_config: WorkbenchConfig,
    discussion_block: str = "",
) -> str:
    """Replace all template placeholders in a prompt string.

    Args:
        raw_prompt: The raw prompt template text.
        task_folder_name: Value for the {{TASK}} placeholder.
        workbench_config: Workbench config providing repos for {{REPOSITORIES}}.
        discussion_block: Value for the {{DISCUSSIONS}} placeholder.

    Returns:
        The prompt text with all placeholders resolved.
    """
    text = raw_prompt.replace(TASK_PLACEHOLDER, task_folder_name)
    repo_dirs = [r.dir for r in workbench_config.repos]
    repos_block = render_repositories_block(repo_dirs)
    text = text.replace(REPOSITORIES_PLACEHOLDER, repos_block)
    text = text.replace(DISCUSSIONS_PLACEHOLDER, discussion_block)
    return text


def create_task(
    task_name: str,
    discussion_names: list[str] | None = None,
) -> dict[str, object]:
    """Create a new task in the current workbench.

    Args:
        task_name: The name of the task to create.
        discussion_names: Optional list of discussion names to attach to the task.

    Returns:
        A dict with summary info for the view layer:
        {
            "name": str,               # task name
            "folder_name": str,         # full folder name (YYYYMMDD - name)
            "created_paths": list[str], # relative paths of created files
        }

    Raises:
        ValueError: If mode is not WORKBENCH, or task name already exists.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. Run 'bench init' to create a bench project first."
        )

    if context.mode != BenchMode.WORKBENCH:
        raise ValueError(
            "The 'task create' command can only be run from a workbench directory."
        )

    assert context.root_path is not None
    assert context.bench_dir_name is not None
    assert context.base_config is not None

    # Phase 2: Resolve the tasks directory path
    tasks_dir = context.cwd / BENCH_SUBDIR_NAME / TASKS_DIR_NAME

    # Phase 3: Check task name uniqueness
    existing_names = list_task_names(tasks_dir)
    if task_name in existing_names:
        raise ValueError(f'Task "{task_name}" already exists in this workbench.')

    # Phase 4: Build the folder name
    date_str = datetime.date.today().strftime("%Y%m%d")
    task_folder_name = f"{date_str} - {task_name}"

    # Phase 5: Create the task scaffold
    created_paths = create_task_scaffold(tasks_dir, task_folder_name, task_name)

    # Phase 5b: Inject discussion references into spec.md if provided
    if discussion_names:
        discussions_dir = context.cwd / BENCH_SUBDIR_NAME / DISCUSSIONS_DIR_NAME
        discussion_paths = resolve_discussion_paths(discussions_dir, discussion_names)
        spec_path = tasks_dir / task_folder_name / SPEC_MD_FILENAME
        inject_discussions_into_spec(spec_path, discussion_paths)

    # Phase 6: Return summary
    return {
        "name": task_name,
        "folder_name": task_folder_name,
        "created_paths": created_paths,
    }


def complete_task(task_name: str) -> dict[str, object]:
    """Mark a task as complete by setting its completed date to today.

    Loads the task's task.yaml, validates it via the TaskConfig model,
    checks that it is not already completed, sets the completed date
    to today in YYYY-MM-DD format, and saves back to disk.

    Args:
        task_name: The name of the task to complete.

    Returns:
        A dict with summary info for the view layer:
        {
            "name": str,            # task name
            "folder_name": str,     # full folder name (YYYYMMDD - name)
            "completed_date": str,  # the date set (YYYY-MM-DD)
        }

    Raises:
        ValueError: If mode is not WORKBENCH, task not found, task.yaml
                    missing/malformed, or task already completed.
        FileNotFoundError: If task.yaml does not exist.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. Run 'bench init' to create a bench project first."
        )

    if context.mode != BenchMode.WORKBENCH:
        raise ValueError(
            "The 'task complete' command can only be run from a workbench directory."
        )

    # Phase 2: Resolve the tasks directory path
    tasks_dir = context.cwd / BENCH_SUBDIR_NAME / TASKS_DIR_NAME

    # Phase 3: Find the task folder
    task_folder_path, folder_name = find_task_folder(tasks_dir, task_name)

    # Phase 4: Load task.yaml and validate via TaskConfig model
    raw_data = load_task_yaml(task_folder_path)
    task_config = TaskConfig(**raw_data)

    # Phase 5: Check if already completed
    if task_config.completed is not None:
        raise ValueError(
            f'Task "{task_name}" is already marked as complete '
            f"(completed: {task_config.completed})."
        )

    # Phase 6: Set the completed date (YYYY-MM-DD ISO 8601)
    completed_date = datetime.date.today().isoformat()
    task_config_dict = task_config.model_dump()
    task_config_dict["completed"] = completed_date

    # Phase 7: Save back to disk
    save_task_yaml(task_folder_path, task_config_dict)

    # Phase 8: Return summary for the view layer
    return {
        "name": task_name,
        "folder_name": folder_name,
        "completed_date": completed_date,
    }


def run_task_interview(
    task_folder_name: str,
    discussion_names: list[str] | None = None,
) -> int:
    """Launch an interactive opencode interview for a task's spec.

    Reads the task-create-spec.md prompt template, substitutes the
    {{TASK}}, {{REPOSITORIES}}, and {{DISCUSSIONS}} placeholders, and runs
    opencode interactively.

    Args:
        task_folder_name: The full task folder name (e.g., "20260208 - add-auth").
        discussion_names: Optional list of discussion names for prompt context.

    Returns:
        The exit code from the opencode process.

    Raises:
        ValueError: If mode is not WORKBENCH.
        RuntimeError: If opencode is not installed.
        FileNotFoundError: If the prompt template is missing.
    """
    # Mode enforcement
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. Run 'bench init' to create a bench project first."
        )

    if context.mode != BenchMode.WORKBENCH:
        raise ValueError(
            "The 'task create' command can only be run from a workbench directory."
        )

    assert context.base_config is not None
    assert context.workbench_config is not None

    # Build discussion block for prompt substitution
    discussion_block = ""
    if discussion_names:
        discussions_dir = context.cwd / BENCH_SUBDIR_NAME / DISCUSSIONS_DIR_NAME
        discussion_paths = resolve_discussion_paths(discussions_dir, discussion_names)
        discussion_block = build_discussion_block(discussion_paths)

    # Build the prompt file path
    prompt_path = (
        context.cwd / BENCH_SUBDIR_NAME / PROMPTS_DIR_NAME / TASK_CREATE_SPEC_FILENAME
    )

    # Read and substitute the prompt template
    raw_prompt = read_prompt_file(prompt_path)
    prompt_text = _substitute_prompt_placeholders(
        raw_prompt, task_folder_name, context.workbench_config, discussion_block
    )

    # Get the model
    model = context.base_config.models.task

    # Launch interactive opencode
    return run_prompt_interactive(prompt_text, model, context.cwd)


def resolve_task(task_name: str) -> dict[str, str]:
    """Resolve a task name to its folder metadata and validate it.

    Performs mode enforcement, task folder resolution, and spec.md validation.

    Args:
        task_name: The task name (e.g., "add-auth").

    Returns:
        A dict with "name" and "folder_name" keys.

    Raises:
        ValueError: If mode is not WORKBENCH, task not found, ambiguous, or spec.md missing.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. Run 'bench init' to create a bench project first."
        )

    if context.mode != BenchMode.WORKBENCH:
        raise ValueError(
            "The 'task refine' command can only be run from a workbench directory."
        )

    # Phase 2: Resolve the tasks directory path
    tasks_dir = context.cwd / BENCH_SUBDIR_NAME / TASKS_DIR_NAME

    # Phase 3: Find the task folder
    task_folder_path, folder_name = find_task_folder(tasks_dir, task_name)

    # Phase 4: Validate spec.md exists
    if not task_spec_exists(task_folder_path):
        raise ValueError(f'Task "{task_name}" is missing spec.md.')

    # Phase 5: Return metadata
    return {"name": task_name, "folder_name": folder_name}


def refine_task(
    task_folder_name: str,
    discussion_names: list[str] | None = None,
) -> int:
    """Launch an interactive opencode session to refine a task's spec.

    Reads the task-refine-spec.md prompt template, substitutes the
    {{TASK}}, {{REPOSITORIES}}, and {{DISCUSSIONS}} placeholders, and runs
    opencode interactively.

    Args:
        task_folder_name: The full task folder name (e.g., "20260208 - add-auth").
        discussion_names: Optional list of discussion names to attach and inject.

    Returns:
        The exit code from the opencode process.

    Raises:
        ValueError: If mode is not WORKBENCH.
        RuntimeError: If opencode is not installed.
        FileNotFoundError: If the prompt template is missing.
    """
    # Mode enforcement
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. Run 'bench init' to create a bench project first."
        )

    if context.mode != BenchMode.WORKBENCH:
        raise ValueError(
            "The 'task refine' command can only be run from a workbench directory."
        )

    assert context.base_config is not None
    assert context.workbench_config is not None

    # Validate and inject discussion references if provided
    discussion_block = ""
    if discussion_names:
        discussions_dir = context.cwd / BENCH_SUBDIR_NAME / DISCUSSIONS_DIR_NAME
        discussion_paths = resolve_discussion_paths(discussions_dir, discussion_names)
        # Inject into spec.md (append to existing block or create new one)
        tasks_dir = context.cwd / BENCH_SUBDIR_NAME / TASKS_DIR_NAME
        spec_path = tasks_dir / task_folder_name / SPEC_MD_FILENAME
        inject_discussions_into_spec(spec_path, discussion_paths)
        # Build discussion block for prompt substitution
        discussion_block = build_discussion_block(discussion_paths)

    # Build the prompt file path
    prompt_path = (
        context.cwd / BENCH_SUBDIR_NAME / PROMPTS_DIR_NAME / TASK_REFINE_SPEC_FILENAME
    )

    # Read and substitute the prompt template
    raw_prompt = read_prompt_file(prompt_path)
    prompt_text = _substitute_prompt_placeholders(
        raw_prompt, task_folder_name, context.workbench_config, discussion_block
    )

    # Get the model
    model = context.base_config.models.task

    # Launch interactive opencode
    return run_prompt_interactive(prompt_text, model, context.cwd)


def list_tasks(task_filter: TaskFilter) -> list[TaskEntry]:
    """List tasks in the current workbench, filtered and sorted.

    Args:
        task_filter: Which tasks to include (OPEN, COMPLETED, or ALL).

    Returns:
        A list of TaskEntry models sorted by created_date ascending.

    Raises:
        ValueError: If mode is not WORKBENCH.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. Run 'bench init' to create a bench project first."
        )

    if context.mode != BenchMode.WORKBENCH:
        raise ValueError(
            "The 'task list' command can only be run from a workbench directory."
        )

    # Phase 2: Resolve the tasks directory
    tasks_dir = context.cwd / BENCH_SUBDIR_NAME / TASKS_DIR_NAME

    # Phase 3: Fetch raw task entry data from repository
    raw_entries = list_task_entries(tasks_dir)

    # Phase 4: Convert raw dicts to TaskEntry models
    entries: list[TaskEntry] = []
    for raw in raw_entries:
        created_date = datetime.datetime.strptime(raw["created_date"], "%Y%m%d").date()
        entries.append(
            TaskEntry(
                name=raw["name"],
                folder_name=raw["folder_name"],
                created_date=created_date,
                completed=raw["completed"],
                has_spec=raw["has_spec"],
                has_impl=raw["has_impl"],
                has_files=raw["has_files"],
            )
        )

    # Phase 5: Filter
    if task_filter == TaskFilter.OPEN:
        entries = [e for e in entries if e.completed is None]
    elif task_filter == TaskFilter.COMPLETED:
        entries = [e for e in entries if e.completed is not None]
    # ALL: keep all entries

    # Phase 6: Sort by created_date ascending
    entries.sort(key=lambda e: e.created_date)

    return entries


def resolve_task_for_implement(task_name: str) -> dict[str, object]:
    """Resolve a task name and return metadata needed for implementation.

    Unlike resolve_task (which validates only spec.md), this resolves the
    task folder without per-file validation. Per-phase validation is
    handled separately by validate_task_phase.

    Args:
        task_name: The task name (e.g., "add-auth").

    Returns:
        A dict with "name" (str), "folder_name" (str),
        "task_folder_path" (Path), and "implementation_flow"
        (list[ImplementationStep]) keys.

    Raises:
        ValueError: If mode is not WORKBENCH or task not found/ambiguous.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. Run 'bench init' to create a bench project first."
        )

    if context.mode != BenchMode.WORKBENCH:
        raise ValueError(
            "The 'task implement' command can only be run from a workbench directory."
        )

    assert context.workbench_config is not None

    # Phase 2: Resolve the tasks directory path
    tasks_dir = context.cwd / BENCH_SUBDIR_NAME / TASKS_DIR_NAME

    # Phase 3: Find the task folder
    task_folder_path, folder_name = find_task_folder(tasks_dir, task_name)

    # Phase 4: Return metadata including implementation flow
    return {
        "name": task_name,
        "folder_name": folder_name,
        "task_folder_path": task_folder_path,
        "implementation_flow": context.workbench_config.implementation_flow,
    }


def validate_task_phase(
    task_folder_path: Path, phase: ImplementationStep, task_name: str
) -> None:
    """Validate that all required input files exist and are non-empty for a phase.

    Args:
        task_folder_path: Absolute path to the task folder.
        phase: The implementation step to validate.
        task_name: The task name (for error messages).

    Raises:
        ValueError: If any required file is missing or empty.
    """
    for filename in phase.required_files:
        if not task_file_exists_and_nonempty(task_folder_path, filename):
            raise ValueError(
                f'Task "{task_name}" requires {filename} to be present and non-empty.'
            )


def run_task_phase(task_folder_name: str, phase: ImplementationStep) -> int:
    """Execute a single implementation phase by launching opencode.

    Reads the phase's prompt template, substitutes {{TASK}} and {{REPOSITORIES}}
    placeholders, and launches opencode with terminal pass-through.

    Args:
        task_folder_name: The full task folder name (e.g., "20260208 - add-auth").
        phase: The implementation step to execute.

    Returns:
        The exit code from the opencode process.

    Raises:
        ValueError: If mode is not WORKBENCH.
        RuntimeError: If opencode is not installed.
        FileNotFoundError: If the prompt template is missing.
    """
    # Mode enforcement
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. Run 'bench init' to create a bench project first."
        )

    if context.mode != BenchMode.WORKBENCH:
        raise ValueError(
            "The 'task implement' command can only be run from a workbench directory."
        )

    assert context.base_config is not None
    assert context.workbench_config is not None

    # Build the prompt file path
    prompt_path = context.cwd / BENCH_SUBDIR_NAME / PROMPTS_DIR_NAME / phase.prompt

    # Read and substitute the prompt template
    raw_prompt = read_prompt_file(prompt_path)
    prompt_text = _substitute_prompt_placeholders(
        raw_prompt, task_folder_name, context.workbench_config
    )

    # Get the model
    model = context.base_config.models.task

    # Launch opencode run (headless agent execution)
    return run_command(prompt_text, model, context.cwd)


def validate_task_phase_outputs(
    task_folder_path: Path, phase: ImplementationStep
) -> None:
    """Validate that expected output files were created after a phase completes.

    Called after a phase finishes successfully to ensure its expected outputs
    exist before proceeding to the next phase.

    Args:
        task_folder_path: Absolute path to the task folder.
        phase: The implementation step whose outputs to validate.

    Raises:
        ValueError: If any expected output file is missing or empty.
    """
    for filename in phase.output_files:
        if not task_file_exists_and_nonempty(task_folder_path, filename):
            raise ValueError(
                f"Phase '{phase.name}' completed but {filename} was not created or is empty."
            )
