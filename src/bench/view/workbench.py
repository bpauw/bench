from rich.console import Console
from rich.table import Table

from bench.model import WorkbenchEntry, WorkbenchStatus

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


def display_workbench_deleted(summary: dict[str, object]) -> None:
    """Display a success message after workbench deletion.

    Args:
        summary: Dict with keys: name, was_active, workspace_removed,
                 scaffold_removed, branches_deleted.
    """
    name = summary["name"]
    was_active = summary["was_active"]
    workspace_removed = summary["workspace_removed"]
    scaffold_removed = summary["scaffold_removed"]
    branches_deleted: list[str] = summary.get("branches_deleted", [])  # type: ignore[assignment]

    console.print(f'[bold green]Workbench "{name}" deleted successfully[/bold green]')
    if was_active:
        console.print(f"  Workspace removed: [dim]{workspace_removed}[/dim]")
    console.print(f"  Scaffold removed: [dim]{scaffold_removed}[/dim]")
    if branches_deleted:
        console.print(f"  Branches deleted: [cyan]{', '.join(branches_deleted)}[/cyan]")
    else:
        console.print("  Branches deleted: [dim]none[/dim]")


def display_workbench_list(workbenches: list[WorkbenchEntry]) -> None:
    """Display a table of workbenches or an empty-state message.

    Active workbenches are listed first (sorted by name), then inactive
    workbenches (sorted by name).

    Args:
        workbenches: The list of WorkbenchEntry models to display.
    """
    if not workbenches:
        console.print(
            "[dim]No workbenches defined. Use 'bench workbench create' to create one.[/dim]"
        )
        return

    table = Table()
    table.add_column("Name")
    table.add_column("Source")
    table.add_column("Git Branch")
    table.add_column("Status")

    # Sort: active first (sorted by name), then inactive (sorted by name)
    active = sorted(
        [w for w in workbenches if w.status == WorkbenchStatus.ACTIVE],
        key=lambda w: w.name,
    )
    inactive = sorted(
        [w for w in workbenches if w.status == WorkbenchStatus.INACTIVE],
        key=lambda w: w.name,
    )
    ordered = active + inactive

    for entry in ordered:
        if entry.status == WorkbenchStatus.ACTIVE:
            status_str = "[green]active[/green]"
        else:
            status_str = "[dim]inactive[/dim]"

        table.add_row(
            entry.name,
            entry.source,
            entry.git_branch,
            status_str,
        )

    console.print(table)


def display_script_running(script_name: str) -> None:
    """Display a message before running a script."""
    console.print(f"  Running script [cyan]{script_name}[/cyan]...")


def display_script_completed(script_name: str) -> None:
    """Display a message after a script completes successfully."""
    console.print(f"  Script [cyan]{script_name}[/cyan] completed")


def display_script_failed(script_name: str, exit_code: int) -> None:
    """Display a warning when a script fails."""
    console.print(
        f"  [bold yellow]Warning:[/bold yellow] Script [cyan]{script_name}[/cyan] "
        f"failed (exit code {exit_code})"
    )


def display_script_not_executable(script_name: str) -> None:
    """Display a warning when a script is not executable."""
    console.print(
        f"  [bold yellow]Warning:[/bold yellow] [cyan]{script_name}[/cyan] "
        f"is not executable (skipping)"
    )


def display_workbench_error(message: str) -> None:
    """Display an error message for workbench operations.

    Args:
        message: The error message to display.
    """
    console.print(f"[bold red]Error:[/bold red] {message}")
