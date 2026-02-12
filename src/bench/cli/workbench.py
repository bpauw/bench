from pathlib import Path
from typing import Annotated

import typer

from bench.model import BenchMode, WorkbenchStatus
from bench.service.mode_detection import detect_mode
from bench.service.source import list_sources
from rich.console import Console

from bench.service.workbench import (
    activate_workbench,
    create_workbench,
    retire_workbench,
    update_workbench,
)
from bench.view.workbench import (
    display_workbench_activated,
    display_workbench_created,
    display_workbench_error,
    display_workbench_retired,
    display_workbench_updated,
)

workbench_app: typer.Typer = typer.Typer(help="Manage workbenches.")


def _complete_source_name(incomplete: str) -> list[str]:
    """Provide tab-completion for source names."""
    try:
        sources = list_sources()
        return [s.name for s in sources if s.name.startswith(incomplete)]
    except Exception:
        return []


def _complete_workbench_name(incomplete: str) -> list[str]:
    """Provide tab-completion for workbench names."""
    try:
        context = detect_mode(Path.cwd())
        if context.base_config is None:
            return []
        return [
            w.name
            for w in context.base_config.workbenches
            if w.name.startswith(incomplete)
        ]
    except Exception:
        return []


def _complete_inactive_workbench_name(incomplete: str) -> list[str]:
    """Provide tab-completion for inactive workbench names."""
    try:
        context = detect_mode(Path.cwd())
        if context.base_config is None:
            return []
        return [
            w.name
            for w in context.base_config.workbenches
            if w.name.startswith(incomplete) and w.status == WorkbenchStatus.INACTIVE
        ]
    except Exception:
        return []


def workbench_create(
    source: Annotated[
        str,
        typer.Argument(
            help="Name of the source to use",
            autocompletion=_complete_source_name,
        ),
    ],
    name: Annotated[str, typer.Argument(help="Name of the workbench to create")],
    workbench_git_branch: Annotated[
        str | None,
        typer.Option(
            "--workbench-git-branch",
            help="Custom git branch name for worktrees (defaults to workbench name)",
        ),
    ] = None,
) -> None:
    """Create a new workbench from a source."""
    try:
        summary = create_workbench(source, name, workbench_git_branch)
        display_workbench_created(summary)
    except (ValueError, RuntimeError) as e:
        display_workbench_error(str(e))
        raise typer.Exit(code=1)


workbench_app.command("create")(workbench_create)


def workbench_update(
    name: Annotated[
        str | None,
        typer.Argument(
            help="Name of the workbench to update (required from project root, omit from workbench directory)",
            autocompletion=_complete_workbench_name,
        ),
    ] = None,
    add_repo: Annotated[
        list[str] | None,
        typer.Option(
            "--add-repo",
            help=(
                "Repository mapping to add in format 'directory-name:branch-name'. "
                "Can be passed multiple times."
            ),
        ),
    ] = None,
    remove_repo: Annotated[
        list[str] | None,
        typer.Option(
            "--remove-repo",
            help=("Repository directory name to remove. Can be passed multiple times."),
        ),
    ] = None,
) -> None:
    """Update an existing workbench by adding or removing repositories."""
    try:
        # Determine workbench name based on mode
        context = detect_mode(Path.cwd())

        if context.mode == BenchMode.WORKBENCH:
            if name is not None:
                display_workbench_error(
                    "Do not provide a workbench name when running from a workbench directory."
                )
                raise typer.Exit(code=1)
            workbench_name = context.cwd.name
        elif context.mode == BenchMode.ROOT:
            if name is None:
                display_workbench_error(
                    "A workbench name is required when running from the project root."
                )
                raise typer.Exit(code=1)
            workbench_name = name
        else:
            # UNINITIALIZED or WITHIN_ROOT — let the service layer handle the error
            workbench_name = name or ""

        message = update_workbench(workbench_name, add_repo or [], remove_repo or [])
        display_workbench_updated(message)
    except (ValueError, RuntimeError) as e:
        display_workbench_error(str(e))
        raise typer.Exit(code=1)


workbench_app.command("update")(workbench_update)


def workbench_retire(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the workbench to retire",
            autocompletion=_complete_workbench_name,
        ),
    ],
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip confirmation prompt",
        ),
    ] = False,
) -> None:
    """Retire a workbench by removing its workspace directory."""
    try:
        if not yes:
            context = detect_mode(Path.cwd())
            if context.base_config is not None:
                wb = next(
                    (w for w in context.base_config.workbenches if w.name == name),
                    None,
                )
                if wb is not None:
                    typer.confirm(
                        f'Retire workbench "{name}"? This will remove the workspace directory '
                        f"and prune associated worktrees.",
                        abort=True,
                    )

        summary = retire_workbench(name)
        display_workbench_retired(summary)
    except typer.Abort:
        _console = Console()
        _console.print("[dim]Retirement cancelled.[/dim]")
        raise typer.Exit(code=0)
    except (ValueError, RuntimeError) as e:
        display_workbench_error(str(e))
        raise typer.Exit(code=1)


workbench_app.command("retire")(workbench_retire)


def workbench_activate(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the workbench to activate",
            autocompletion=_complete_inactive_workbench_name,
        ),
    ],
) -> None:
    """Activate a retired workbench by recreating its workspace and worktrees."""
    try:
        summary = activate_workbench(name)
        display_workbench_activated(summary)
    except (ValueError, RuntimeError) as e:
        display_workbench_error(str(e))
        raise typer.Exit(code=1)


workbench_app.command("activate")(workbench_activate)


def register(app: typer.Typer) -> None:
    """Register the workbench subcommand group on the given Typer app."""
    app.add_typer(workbench_app, name="workbench")
