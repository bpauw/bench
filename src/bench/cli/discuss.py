import typer

from bench.service.discuss import list_discussions, start_discussion
from bench.view.discuss import (
    display_discuss_error,
    display_discuss_list,
    display_discuss_start,
)

discuss_app: typer.Typer = typer.Typer(help="Start and manage discussions.")


def discuss_start() -> None:
    """Start an interactive discussion via opencode."""
    try:
        display_discuss_start()
        exit_code = start_discussion()
        if exit_code != 0:
            display_discuss_error(f"opencode exited with code {exit_code}")
            raise typer.Exit(code=exit_code)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        display_discuss_error(str(e))
        raise typer.Exit(code=1)


discuss_app.command("start")(discuss_start)


def discuss_list_cmd() -> None:
    """List past discussions in the current workbench."""
    try:
        discussions = list_discussions()
        display_discuss_list(discussions)
    except (ValueError, RuntimeError) as e:
        display_discuss_error(str(e))
        raise typer.Exit(code=1)


discuss_app.command("list")(discuss_list_cmd)


def register(app: typer.Typer) -> None:
    """Register the discuss subcommand group on the given Typer app."""
    app.add_typer(discuss_app, name="discuss")
