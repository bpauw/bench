from pathlib import Path
from typing import Annotated

import typer

from bench.service.populate import populate_agents_md
from bench.view.populate import (
    display_populate_agents_error,
    display_populate_agents_start,
)

populate_app: typer.Typer = typer.Typer(help="Populate generated files.")


def agents(
    model: Annotated[
        str | None,
        typer.Option(
            "--model", help="Override the model used for AGENTS.md population."
        ),
    ] = None,
) -> None:
    """Populate AGENTS.md using an AI agent."""
    try:
        display_populate_agents_start()
        populate_agents_md(Path.cwd(), model)
    except (ValueError, RuntimeError) as e:
        display_populate_agents_error(str(e))
        raise typer.Exit(code=1)


populate_app.command("agents")(agents)


def register(app: typer.Typer) -> None:
    """Register the populate subcommand group on the given Typer app."""
    app.add_typer(populate_app, name="populate")
