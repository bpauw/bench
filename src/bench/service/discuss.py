import datetime
from pathlib import Path

from bench.model.discuss import DiscussionEntry
from bench.model.mode import BenchMode
from bench.repository.filesystem import (
    BENCH_SUBDIR_NAME,
    DISCUSS_PROMPT_FILENAME,
    DISCUSSIONS_DIR_NAME,
    PROMPTS_DIR_NAME,
    REPOSITORIES_PLACEHOLDER,
    list_discussion_files,
    read_prompt_file,
    render_repositories_block,
)
from bench.repository.opencode import run_prompt_interactive
from bench.service.mode_detection import detect_mode


def start_discussion() -> int:
    """Launch an interactive opencode discussion session.

    Reads the discuss.md prompt template, substitutes the
    {{REPOSITORIES}} placeholder, and runs opencode interactively.

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
            "The 'discuss start' command can only be run from a workbench directory."
        )

    assert context.base_config is not None
    assert context.workbench_config is not None

    # Build the prompt file path
    prompt_path = (
        context.cwd / BENCH_SUBDIR_NAME / PROMPTS_DIR_NAME / DISCUSS_PROMPT_FILENAME
    )

    # Read and substitute the prompt template
    raw_prompt = read_prompt_file(prompt_path)
    repo_dirs = [r.dir for r in context.workbench_config.repos]
    repos_block = render_repositories_block(repo_dirs)
    prompt_text = raw_prompt.replace(REPOSITORIES_PLACEHOLDER, repos_block)

    # Get the model
    model = context.base_config.models.discuss

    # Launch interactive opencode
    return run_prompt_interactive(prompt_text, model, context.cwd)


def list_discussions() -> list[DiscussionEntry]:
    """List discussions in the current workbench, sorted by date.

    Returns:
        A list of DiscussionEntry models sorted by created_date ascending.

    Raises:
        ValueError: If mode is not WORKBENCH.
    """
    # Mode enforcement
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. Run 'bench init' to create a bench project first."
        )

    if context.mode != BenchMode.WORKBENCH:
        raise ValueError(
            "The 'discuss list' command can only be run from a workbench directory."
        )

    # Resolve discussions directory
    discussions_dir = context.cwd / BENCH_SUBDIR_NAME / DISCUSSIONS_DIR_NAME

    # Fetch raw discussion file data from repository
    raw_entries = list_discussion_files(discussions_dir)

    # Convert raw dicts to DiscussionEntry models
    entries: list[DiscussionEntry] = []
    for raw in raw_entries:
        created_date = datetime.datetime.strptime(raw["created_date"], "%Y%m%d").date()
        entries.append(
            DiscussionEntry(
                name=raw["name"],
                filename=raw["filename"],
                created_date=created_date,
            )
        )

    # Sort by created_date ascending
    entries.sort(key=lambda e: e.created_date)

    return entries
