from pathlib import Path

import typer

from bench.service.mode_detection import detect_mode
from bench.view.status import display_status

status_app: typer.Typer = typer.Typer(
    help="Display the current bench mode and context.",
    invoke_without_command=True,
)


@status_app.callback()
def status() -> None:
    """Display the current bench mode and context."""
    context = detect_mode(Path.cwd())
    display_status(context)


def register(app: typer.Typer) -> None:
    """Register the status command on the given Typer app."""
    app.add_typer(status_app, name="status")
