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


def display_populate_prompts_start() -> None:
    """Display a message indicating prompts population is starting."""
    console.print()
    console.print("[bold]Populating prompt files...[/bold]")


def display_populate_prompts_results(result: dict[str, object]) -> None:
    """Display per-file statuses and summary for prompts population.

    Args:
        result: Dict returned by populate_prompts() containing "results" (list of
                per-file status dicts), "created", "updated", and "up_to_date" counts.
    """
    results = result["results"]  # list[dict[str, str]]

    for entry in results:  # type: ignore[union-attr]
        filename = entry["filename"]
        status = entry["status"]

        if status == "created":
            console.print(f"  [green]Created[/green]     {filename}")
        elif status == "updated":
            console.print(f"  [green]Updated[/green]     {filename}")
        else:
            console.print(f"  [dim]Up to date[/dim]  {filename}")

    # Summary line
    created = result["created"]
    updated = result["updated"]
    up_to_date = result["up_to_date"]
    console.print()
    console.print(
        f"[bold]{updated} updated, {created} created, {up_to_date} already up to date[/bold]"
    )


def display_populate_prompts_error(message: str) -> None:
    """Display an error message for failed prompts population.

    Args:
        message: The error message to display.
    """
    console.print(f"[bold red]Error:[/bold red] {message}")
