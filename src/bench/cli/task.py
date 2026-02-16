from pathlib import Path
from typing import Annotated

import typer

from bench.model.task import TaskFilter
from bench.model.config import ImplementationStep
from bench.service.task import (
    complete_task,
    create_task,
    list_tasks,
    refine_task,
    resolve_task,
    resolve_task_for_followup,
    resolve_task_for_implement,
    run_task_followup,
    run_task_interview,
    run_task_phase,
    validate_task_phase,
    validate_task_phase_outputs,
)
from bench.view.task import (
    display_task_completed,
    display_task_created,
    display_task_error,
    display_task_followup_complete,
    display_task_followup_start,
    display_task_implement_complete,
    display_task_implement_phase_complete,
    display_task_implement_phase_start,
    display_task_implement_start,
    display_task_list,
    display_task_refine_complete,
    display_task_refine_start,
)

task_app: typer.Typer = typer.Typer(help="Manage tasks.")


def _complete_task_name(incomplete: str) -> list[str]:
    """Provide tab-completion for task names (open tasks only)."""
    try:
        entries = list_tasks(TaskFilter.OPEN)
        return [e.name for e in entries if e.name.startswith(incomplete)]
    except Exception:
        return []


def _complete_discussion_name(incomplete: str) -> list[str]:
    """Provide tab-completion for discussion names."""
    try:
        from bench.service.discuss import list_discussions

        entries = list_discussions()
        return [e.name for e in entries if e.name.startswith(incomplete)]
    except Exception:
        return []


def _complete_repo_name(incomplete: str) -> list[str]:
    """Provide tab-completion for --only-repo with available repo directory names."""
    try:
        from bench.service.mode_detection import detect_mode

        context = detect_mode(Path.cwd())
        if context.workbench_config is None:
            return []
        return [
            r.dir
            for r in context.workbench_config.repos
            if r.dir.startswith(incomplete)
        ]
    except Exception:
        return []


def task_create(
    name: Annotated[str, typer.Argument(help="Name of the task to create")],
    interview: Annotated[
        bool,
        typer.Option(
            "--interview",
            help="Launch an interactive opencode session to populate the spec",
        ),
    ] = False,
    add_discussion: Annotated[
        list[str] | None,
        typer.Option(
            "--add-discussion",
            help="Name of an existing discussion to attach to the task",
            autocompletion=_complete_discussion_name,
        ),
    ] = None,
    only_repo: Annotated[
        list[str] | None,
        typer.Option(
            "--only-repo",
            help="Scope this task to specific repositories (repeatable)",
            autocompletion=_complete_repo_name,
        ),
    ] = None,
) -> None:
    """Create a new task in the current workbench."""
    try:
        summary = create_task(
            name, discussion_names=add_discussion, only_repos=only_repo
        )
        display_task_created(summary)
        if interview:
            folder_name = str(summary["folder_name"])
            run_task_interview(folder_name, discussion_names=add_discussion)
    except (ValueError, RuntimeError) as e:
        display_task_error(str(e))
        raise typer.Exit(code=1)


task_app.command("create")(task_create)


def task_refine(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the task to refine",
            autocompletion=_complete_task_name,
        ),
    ],
    add_discussion: Annotated[
        list[str] | None,
        typer.Option(
            "--add-discussion",
            help="Name of an existing discussion to attach to the task",
            autocompletion=_complete_discussion_name,
        ),
    ] = None,
) -> None:
    """Refine an existing task's specification via an interactive AI session."""
    try:
        summary = resolve_task(name)
        display_task_refine_start(name, str(summary["folder_name"]))
        exit_code = refine_task(
            str(summary["folder_name"]), discussion_names=add_discussion
        )
        if exit_code != 0:
            display_task_error(f"opencode exited with code {exit_code}")
            raise typer.Exit(code=exit_code)
        display_task_refine_complete(name)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        display_task_error(str(e))
        raise typer.Exit(code=1)


task_app.command("refine")(task_refine)


def task_followup(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the task to follow up on",
            autocompletion=_complete_task_name,
        ),
    ],
    add_discussion: Annotated[
        list[str] | None,
        typer.Option(
            "--add-discussion",
            help="Name of an existing discussion to include as context",
            autocompletion=_complete_discussion_name,
        ),
    ] = None,
) -> None:
    """Perform followup work on an implemented task via an interactive AI session."""
    try:
        summary = resolve_task_for_followup(name)
        display_task_followup_start(name, str(summary["folder_name"]))
        exit_code = run_task_followup(
            str(summary["folder_name"]), discussion_names=add_discussion
        )
        if exit_code != 0:
            display_task_error(f"opencode exited with code {exit_code}")
            raise typer.Exit(code=exit_code)
        display_task_followup_complete(name)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        display_task_error(str(e))
        raise typer.Exit(code=1)


task_app.command("followup")(task_followup)


def task_implement(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the task to implement",
            autocompletion=_complete_task_name,
        ),
    ],
) -> None:
    """Implement a task through sequential AI-assisted phases."""
    try:
        # Resolve task
        summary = resolve_task_for_implement(name)
        folder_name = str(summary["folder_name"])
        task_folder_path_raw = summary["task_folder_path"]
        assert isinstance(task_folder_path_raw, Path)
        task_folder_path: Path = task_folder_path_raw

        # Get implementation flow from workbench config
        implementation_flow_raw = summary["implementation_flow"]
        assert isinstance(implementation_flow_raw, list)
        implementation_flow = [
            step
            for step in implementation_flow_raw
            if isinstance(step, ImplementationStep)
        ]

        # Derive phase info for display
        phase_names = [step.name for step in implementation_flow]
        total_phases = len(implementation_flow)

        # Validate that there are phases to run
        if total_phases == 0:
            display_task_error(
                "No implementation flow steps configured for this workbench."
            )
            raise typer.Exit(code=1)

        # Display start
        display_task_implement_start(name, folder_name, phase_names, total_phases)

        # Execute phases
        for i, step in enumerate(implementation_flow, 1):
            # Pre-flight validation
            validate_task_phase(task_folder_path, step, name)

            # Display phase start
            display_task_implement_phase_start(i, total_phases, step.name)

            # Run phase
            exit_code = run_task_phase(folder_name, step)

            if exit_code != 0:
                display_task_error(
                    f"Phase '{step.name}' failed: opencode exited with code {exit_code}"
                )
                raise typer.Exit(code=exit_code)

            # Display phase complete
            display_task_implement_phase_complete(i, total_phases, step.name)

            # Inter-phase output validation
            validate_task_phase_outputs(task_folder_path, step)

        # Display overall completion
        display_task_implement_complete(name, total_phases)

    except (ValueError, RuntimeError, FileNotFoundError) as e:
        display_task_error(str(e))
        raise typer.Exit(code=1)


task_app.command("implement")(task_implement)


def task_complete_cmd(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the task to mark as complete",
            autocompletion=_complete_task_name,
        ),
    ],
) -> None:
    """Mark a task as complete in the current workbench."""
    try:
        summary = complete_task(name)
        display_task_completed(summary)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        display_task_error(str(e))
        raise typer.Exit(code=1)


task_app.command("complete")(task_complete_cmd)


def task_list(
    all_tasks: Annotated[
        bool,
        typer.Option("--all", help="Show all tasks (including completed)"),
    ] = False,
    completed: Annotated[
        bool,
        typer.Option("--completed", help="Show only completed tasks"),
    ] = False,
) -> None:
    """List tasks in the current workbench."""
    try:
        if all_tasks and completed:
            display_task_error("--all and --completed are mutually exclusive.")
            raise typer.Exit(code=1)

        if all_tasks:
            task_filter = TaskFilter.ALL
        elif completed:
            task_filter = TaskFilter.COMPLETED
        else:
            task_filter = TaskFilter.OPEN

        tasks = list_tasks(task_filter)
        display_task_list(tasks, task_filter)
    except (ValueError, RuntimeError) as e:
        display_task_error(str(e))
        raise typer.Exit(code=1)


task_app.command("list")(task_list)


def register(app: typer.Typer) -> None:
    """Register the task subcommand group on the given Typer app."""
    app.add_typer(task_app, name="task")
