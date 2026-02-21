from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from bench.service.map import init_maps, update_maps
from bench.view.map import display_map_error, display_map_status

console = Console()

map_app: typer.Typer = typer.Typer(help="Manage repository maps.")


def map_init(
    only_repo: Annotated[
        list[str] | None,
        typer.Option(
            "--only-repo",
            help="Limit mapping to specific repositories (repeatable)",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="Override the AI model for this run"),
    ] = None,
) -> None:
    """Generate initial maps for all (or selected) repositories."""
    try:
        display_map_status("Initializing repository maps...")
        init_maps(Path.cwd(), model, only_repo)
    except (ValueError, RuntimeError) as e:
        display_map_error(str(e))
        raise typer.Exit(code=1)


map_app.command("init")(map_init)


def map_update(
    only_repo: Annotated[
        list[str] | None,
        typer.Option(
            "--only-repo",
            help="Limit update to specific repositories (repeatable)",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="Override the AI model for this run"),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt"),
    ] = False,
) -> None:
    """Differentially update existing maps based on current repository state."""
    try:
        if not yes:
            typer.confirm(
                "Update repository maps?",
                abort=True,
            )

        display_map_status("Updating repository maps...")
        update_maps(Path.cwd(), model, only_repo)
    except typer.Abort:
        console.print("[dim]Map update cancelled.[/dim]")
        raise typer.Exit(code=0)
    except (ValueError, RuntimeError) as e:
        display_map_error(str(e))
        raise typer.Exit(code=1)


map_app.command("update")(map_update)


def register(app: typer.Typer) -> None:
    """Register the map subcommand group on the given Typer app."""
    app.add_typer(map_app, name="map")
