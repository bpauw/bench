from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from bench.service.populate import (
    populate_agents_md,
    populate_prompts,
    preview_populate_prompts,
)
from bench.view.populate import (
    display_populate_agents_error,
    display_populate_agents_start,
    display_populate_prompts_complete,
    display_populate_prompts_error,
    display_populate_prompts_preview,
    display_populate_prompts_start,
    display_populate_prompts_up_to_date,
)

console = Console()

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
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip confirmation prompt",
        ),
    ] = False,
) -> None:
    """Populate AGENTS.md using an AI agent."""
    try:
        if not yes:
            typer.confirm(
                "This will overwrite AGENTS.md with AI-generated content. Proceed?",
                abort=True,
            )

        display_populate_agents_start()
        populate_agents_md(Path.cwd(), model, repo)
    except typer.Abort:
        console.print("[dim]Population cancelled.[/dim]")
        raise typer.Exit(code=0)
    except (ValueError, RuntimeError) as e:
        display_populate_agents_error(str(e))
        raise typer.Exit(code=1)


populate_app.command("agents")(agents)


def prompts(
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip confirmation prompt",
        ),
    ] = False,
) -> None:
    """Synchronize prompt template files with the latest built-in templates."""
    try:
        display_populate_prompts_start()

        # Preview what will change
        preview = preview_populate_prompts(Path.cwd())

        # If nothing to do, show message and return
        if preview["created"] == 0 and preview["updated"] == 0:
            display_populate_prompts_up_to_date()
            return

        # Show preview of changes
        display_populate_prompts_preview(preview)

        # Confirm with user (unless --yes)
        if not yes:
            typer.confirm("Proceed?", abort=True)

        # Execute the changes
        result = populate_prompts(Path.cwd())
        display_populate_prompts_complete(result)
    except typer.Abort:
        console.print("[dim]Population cancelled.[/dim]")
        raise typer.Exit(code=0)
    except (ValueError, RuntimeError) as e:
        display_populate_prompts_error(str(e))
        raise typer.Exit(code=1)


populate_app.command("prompts")(prompts)


def register(app: typer.Typer) -> None:
    """Register the populate subcommand group on the given Typer app."""
    app.add_typer(populate_app, name="populate")
