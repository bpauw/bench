from rich.console import Console

console = Console()


def display_map_error(message: str) -> None:
    """Display an error message for a failed map operation.

    Args:
        message: The error message to display.
    """
    console.print(f"[bold red]Error:[/bold red] {message}")


def display_map_status(message: str) -> None:
    """Display a status message during map operations.

    Args:
        message: The status message to display.
    """
    console.print(f"[bold]{message}[/bold]")
