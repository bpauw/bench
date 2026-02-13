from rich.console import Console

console = Console()


def display_populate_agents_start() -> None:
    """Display a message indicating AGENTS.md population is starting."""
    console.print()
    console.print("[bold]Populating AGENTS.md...[/bold]")


def display_populate_agents_error(message: str) -> None:
    """Display an error message for failed AGENTS.md population.

    Args:
        message: The error message to display.
    """
    console.print(f"[bold red]Error:[/bold red] {message}")


def display_populate_agents_warning(message: str) -> None:
    """Display a warning when AGENTS.md population fails non-fatally.

    Args:
        message: The error message describing what went wrong.
    """
    console.print(
        f"[bold yellow]Warning:[/bold yellow] AGENTS.md population failed: {message}. "
        "You can populate it later with 'bench populate agents'."
    )
