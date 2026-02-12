from rich.console import Console

console = Console()


def display_workbench_created(summary: dict[str, object]) -> None:
    """Display a success message after workbench creation.

    Args:
        summary: Dict with keys: name, source, git_branch, repos.
    """
    name = summary["name"]
    source = summary["source"]
    git_branch = summary["git_branch"]
    repos: list[dict[str, str]] = summary.get("repos", [])  # type: ignore[assignment]

    console.print(f'[bold green]Workbench "{name}" created successfully[/bold green]')
    console.print(f"  Source: [cyan]{source}[/cyan]")
    console.print(f"  Git branch: [cyan]{git_branch}[/cyan]")

    if repos:
        console.print("  Repositories:")
        for repo in repos:
            console.print(
                f"    [bold]{repo['dir']}[/bold] -> [dim]{repo['worktree_path']}[/dim]"
            )


def display_workbench_activated(summary: dict[str, object]) -> None:
    """Display a success message after workbench activation.

    Args:
        summary: Dict with keys: name, source, git_branch, repos.
    """
    name = summary["name"]
    source = summary["source"]
    git_branch = summary["git_branch"]
    repos: list[dict[str, str]] = summary.get("repos", [])  # type: ignore[assignment]

    console.print(f'[bold green]Workbench "{name}" activated successfully[/bold green]')
    console.print(f"  Source: [cyan]{source}[/cyan]")
    console.print(f"  Git branch: [cyan]{git_branch}[/cyan]")

    if repos:
        console.print("  Repositories:")
        for repo in repos:
            console.print(
                f"    [bold]{repo['dir']}[/bold] -> [dim]{repo['worktree_path']}[/dim]"
            )


def display_workbench_updated(message: str) -> None:
    """Display a success message after workbench update.

    Args:
        message: The success message to display.
    """
    console.print(f"[bold green]{message}[/bold green]")


def display_workbench_retired(summary: dict[str, object]) -> None:
    """Display a success message after workbench retirement.

    Args:
        summary: Dict with keys: name, repos_pruned, bench_dir_preserved.
    """
    name = summary["name"]
    repos_pruned = summary["repos_pruned"]
    bench_dir = summary["bench_dir_preserved"]

    console.print(f'[bold green]Workbench "{name}" retired successfully[/bold green]')
    console.print(f"  Repos pruned: [cyan]{repos_pruned}[/cyan]")
    console.print(f"  Preserved: [dim]{bench_dir}[/dim]")


def display_workbench_error(message: str) -> None:
    """Display an error message for workbench operations.

    Args:
        message: The error message to display.
    """
    console.print(f"[bold red]Error:[/bold red] {message}")
