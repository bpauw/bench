from pathlib import Path
from typing import Annotated

import typer

from bench.service.init import initialize_project
from bench.service.populate import populate_agents_md
from bench.view.init import (
    display_agents_populating,
    display_agents_population_warning,
    display_init_error,
    display_init_success,
)


def init(
    skip_agents_md: Annotated[
        bool,
        typer.Option("--skip-agents-md", help="Skip the AGENTS.md population step."),
    ] = False,
    model: Annotated[
        str | None,
        typer.Option(
            "--model", help="Override the model used for AGENTS.md population."
        ),
    ] = None,
) -> None:
    """Initialize a new bench project in the current directory."""
    try:
        created_paths = initialize_project(Path.cwd())
        display_init_success(created_paths)
    except ValueError as e:
        display_init_error(str(e))
        raise typer.Exit(code=1)

    if not skip_agents_md:
        display_agents_populating()
        try:
            populate_agents_md(Path.cwd(), model)
        except RuntimeError as e:
            display_agents_population_warning(str(e))


def register(app: typer.Typer) -> None:
    """Register the init command with the Typer app."""
    app.command()(init)
