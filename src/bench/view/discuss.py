from rich.console import Console
from rich.table import Table

from bench.model.discuss import DiscussionEntry

console = Console()


def display_discuss_start() -> None:
    """Display a message before launching the discussion session."""
    console.print("[bold cyan]Starting discussion...[/bold cyan]")
    console.print()


def display_discuss_list(discussions: list[DiscussionEntry]) -> None:
    """Display a table of discussions or an empty-state message.

    Args:
        discussions: The list of DiscussionEntry models to display.
    """
    if not discussions:
        console.print("[dim]No discussions in this workbench.[/dim]")
        return

    table = Table()
    table.add_column("Name")
    table.add_column("Date")

    for entry in discussions:
        table.add_row(entry.name, entry.created_date.isoformat())

    console.print(table)


def display_discuss_error(message: str) -> None:
    """Display an error message for discuss operations.

    Args:
        message: The error message to display.
    """
    console.print(f"[bold red]Error:[/bold red] {message}")
