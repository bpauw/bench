from rich.console import Console

from bench.model import Source

console = Console()


def display_source_list(sources: list[Source]) -> None:
    """Display all sources as a styled bullet list."""
    if not sources:
        console.print(
            "[dim]No sources defined. Use 'bench source add' to create one.[/dim]"
        )
        return

    console.print("[bold]Sources:[/bold]")
    for source in sources:
        console.print(f"  [dim]*[/dim] [bold cyan]{source.name}[/bold cyan]")
        if source.repos:
            for repo in source.repos:
                console.print(
                    f"      [dim]-[/dim] {repo.dir} [dim]->[/dim] "
                    f"[green]{repo.source_branch}[/green]"
                )
        else:
            console.print("      [dim](no repositories)[/dim]")


def display_source_added(message: str) -> None:
    """Display a success message after adding a source."""
    console.print(f"[green]{message}[/green]")


def display_source_updated(message: str) -> None:
    """Display a success message after updating a source."""
    console.print(f"[green]{message}[/green]")


def display_source_removed(message: str) -> None:
    """Display a success message after removing a source."""
    console.print(f"[green]{message}[/green]")


def display_source_error(message: str) -> None:
    """Display an error message for source operations."""
    console.print(f"[red]Error:[/red] {message}")
