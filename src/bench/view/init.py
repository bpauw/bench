from rich.console import Console

console = Console()


def display_init_success(created_paths: list[str]) -> None:
    """Display the result of a successful bench init.

    Args:
        created_paths: List of relative paths that were created.
    """
    console.print("[bold green]Initialized bench project[/bold green]")
    console.print()
    for path in created_paths:
        console.print(f"  [dim]created[/dim] {path}")


def display_init_error(message: str) -> None:
    """Display an error message for failed init.

    Args:
        message: The error message to display.
    """
    console.print(f"[bold red]Error:[/bold red] {message}")
