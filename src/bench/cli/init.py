from pathlib import Path

import typer

from bench.service.init import initialize_project
from bench.view.init import display_init_error, display_init_success


def init() -> None:
    """Initialize a new bench project in the current directory."""
    try:
        created_paths = initialize_project(Path.cwd())
        display_init_success(created_paths)
    except ValueError as e:
        display_init_error(str(e))
        raise typer.Exit(code=1)


def register(app: typer.Typer) -> None:
    """Register the init command with the Typer app."""
    app.command()(init)
