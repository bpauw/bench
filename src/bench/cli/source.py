from typing import Annotated

import typer

from rich.console import Console

from bench.service.source import add_source, list_sources, remove_source, update_source
from bench.view.source import (
    display_source_added,
    display_source_error,
    display_source_list,
    display_source_removed,
    display_source_updated,
)

console = Console()

source_app: typer.Typer = typer.Typer(help="Manage sources.")


def source_add(
    name: Annotated[str, typer.Argument(help="Name of the source to create")],
    add_repo: Annotated[
        list[str] | None,
        typer.Option(
            "--add-repo",
            help=(
                "Repository mapping in format 'directory-name:branch-name'. "
                "Can be passed multiple times."
            ),
        ),
    ] = None,
) -> None:
    """Add a new source to the bench project."""
    try:
        message = add_source(name, add_repo or [])
        display_source_added(message)
    except ValueError as e:
        display_source_error(str(e))
        raise typer.Exit(code=1)


source_app.command("add")(source_add)


def source_list() -> None:
    """List all sources in the bench project."""
    try:
        sources = list_sources()
        display_source_list(sources)
    except ValueError as e:
        display_source_error(str(e))
        raise typer.Exit(code=1)


source_app.command("list")(source_list)


def _complete_source_name(incomplete: str) -> list[str]:
    """Provide tab-completion for source names."""
    try:
        sources = list_sources()
        return [s.name for s in sources if s.name.startswith(incomplete)]
    except Exception:
        return []


def source_update(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the source to update",
            autocompletion=_complete_source_name,
        ),
    ],
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
            help=(
                "Repository mapping to remove in format 'directory-name:branch-name'. "
                "Can be passed multiple times."
            ),
        ),
    ] = None,
) -> None:
    """Update an existing source in the bench project."""
    try:
        message = update_source(name, add_repo or [], remove_repo or [])
        display_source_updated(message)
    except ValueError as e:
        display_source_error(str(e))
        raise typer.Exit(code=1)


source_app.command("update")(source_update)


def source_remove(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the source to remove",
            autocompletion=_complete_source_name,
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
    """Remove a source from the bench project."""
    try:
        # Build confirmation prompt with source details
        if not yes:
            sources = list_sources()
            source = next((s for s in sources if s.name == name), None)
            if source is not None:
                if source.repos:
                    repo_desc = ", ".join(
                        f"{r.dir} -> {r.source_branch}" for r in source.repos
                    )
                    prompt_msg = (
                        f'Source "{name}" has {len(source.repos)} repo(s): '
                        f"{repo_desc}. Remove?"
                    )
                else:
                    prompt_msg = f'Source "{name}" has no repositories. Remove?'
                typer.confirm(prompt_msg, abort=True)
            # If source is None, remove_source() will raise ValueError

        message = remove_source(name)
        display_source_removed(message)
    except typer.Abort:
        console.print("[dim]Removal cancelled.[/dim]")
        raise typer.Exit(code=0)
    except ValueError as e:
        display_source_error(str(e))
        raise typer.Exit(code=1)


source_app.command("remove")(source_remove)


def register(app: typer.Typer) -> None:
    """Register the source subcommand group on the given Typer app."""
    app.add_typer(source_app, name="source")
