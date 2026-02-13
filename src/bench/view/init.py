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


def display_agents_populating() -> None:
    """Display a message indicating AGENTS.md population is in progress."""
    console.print()
    console.print("[bold]Populating AGENTS.md...[/bold]")


def display_agents_population_warning(message: str) -> None:
    """Display a warning when AGENTS.md population fails.

    Args:
        message: The error message describing what went wrong.
    """
    console.print(
        f"[bold yellow]Warning:[/bold yellow] AGENTS.md population failed: {message}. "
        "You can populate it later by editing .bench/AGENTS.md or re-running the prompt."
    )
