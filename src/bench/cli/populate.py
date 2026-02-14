from pathlib import Path
from typing import Annotated

import typer

from bench.service.populate import populate_agents_md, populate_prompts
from bench.view.populate import (
    display_populate_agents_error,
    display_populate_agents_start,
    display_populate_prompts_error,
    display_populate_prompts_results,
    display_populate_prompts_start,
)

populate_app: typer.Typer = typer.Typer(help="Populate generated files.")


def agents(
    model: Annotated[
        str | None,
        typer.Option(
            "--model", help="Override the model used for AGENTS.md population."
        ),
    ] = None,
    repo: Annotated[
        list[str] | None,
        typer.Option(
            "--repo",
            help="Specify repositories to include (can be used multiple times). If not specified, all repositories are included.",
        ),
    ] = None,
) -> None:
    """Populate AGENTS.md using an AI agent."""
    try:
        display_populate_agents_start()
        populate_agents_md(Path.cwd(), model, repo)
    except (ValueError, RuntimeError) as e:
        display_populate_agents_error(str(e))
        raise typer.Exit(code=1)


populate_app.command("agents")(agents)


def prompts() -> None:
    """Synchronize prompt template files with the latest built-in templates."""
    try:
        display_populate_prompts_start()
        result = populate_prompts(Path.cwd())
        display_populate_prompts_results(result)
    except (ValueError, RuntimeError) as e:
        display_populate_prompts_error(str(e))
        raise typer.Exit(code=1)


populate_app.command("prompts")(prompts)


def register(app: typer.Typer) -> None:
    """Register the populate subcommand group on the given Typer app."""
    app.add_typer(populate_app, name="populate")
