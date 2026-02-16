from rich.console import Console
from rich.table import Table

from bench.model.task import TaskEntry, TaskFilter

console = Console()

# Empty-state messages keyed by filter mode
_EMPTY_MESSAGES: dict[TaskFilter, str] = {
    TaskFilter.OPEN: "No open tasks in this workbench.",
    TaskFilter.ALL: "No tasks in this workbench.",
    TaskFilter.COMPLETED: "No completed tasks in this workbench.",
}


def display_task_created(summary: dict[str, object]) -> None:
    """Display a success message after task creation.

    Args:
        summary: Dict with keys: name, folder_name, created_paths.
    """
    name = summary["name"]
    folder_name = summary["folder_name"]
    created_paths = summary["created_paths"]

    console.print(f'[bold green]Task "{name}" created successfully[/bold green]')
    console.print(f"  [cyan]Folder:[/cyan] {folder_name}")
    console.print()

    if isinstance(created_paths, list):
        for path in created_paths:
            console.print(f"  [dim]created[/dim] {path}")


def display_task_completed(summary: dict[str, object]) -> None:
    """Display a success message after marking a task as complete.

    Args:
        summary: Dict with keys: name, folder_name, completed_date.
    """
    name = summary["name"]
    folder_name = summary["folder_name"]
    completed_date = summary["completed_date"]

    console.print(f'[bold green]Task "{name}" marked as complete[/bold green]')
    console.print(f"  [cyan]Folder:[/cyan] {folder_name}")
    console.print(f"  [cyan]Completed:[/cyan] {completed_date}")


def display_task_refine_start(task_name: str, folder_name: str) -> None:
    """Display a message before launching the refine session.

    Args:
        task_name: The task name.
        folder_name: The full task folder name.
    """
    console.print(f'[bold cyan]Refining task "{task_name}"[/bold cyan]')
    console.print(f"  [cyan]Folder:[/cyan] {folder_name}")
    console.print()


def display_task_refine_complete(task_name: str) -> None:
    """Display a completion message after the refine session.

    Args:
        task_name: The task name.
    """
    console.print(f"[green]Refine session complete for task: {task_name}[/green]")


def display_task_followup_start(task_name: str, folder_name: str) -> None:
    """Display a message before launching the followup session.

    Args:
        task_name: The task name.
        folder_name: The full task folder name.
    """
    console.print(
        f"[cyan]Starting followup session for task: {task_name} ({folder_name})[/cyan]"
    )
    console.print()


def display_task_followup_complete(task_name: str) -> None:
    """Display a completion message after the followup session.

    Args:
        task_name: The task name.
    """
    console.print(f"[green]Followup session complete for task: {task_name}[/green]")


def display_task_implement_start(
    task_name: str, folder_name: str, phase_names: list[str], total_phases: int
) -> None:
    """Display a message before starting the implement phases.

    Args:
        task_name: The task name.
        folder_name: The full task folder name.
        phase_names: List of phase key names that will be executed.
        total_phases: Total number of phases to execute.
    """
    console.print(f'[bold cyan]Implementing task "{task_name}"[/bold cyan]')
    console.print(f"  [cyan]Folder:[/cyan] {folder_name}")
    phases_str = ", ".join(phase_names)
    console.print(f"  [cyan]Phases:[/cyan] {phases_str} ({total_phases} total)")
    console.print()


def display_task_implement_phase_start(
    phase_number: int, total_phases: int, phase_label: str
) -> None:
    """Display a progress message before launching a phase.

    Args:
        phase_number: The 1-based index of the current phase.
        total_phases: Total number of phases to execute.
        phase_label: Human-readable description of the phase.
    """
    console.print(
        f"[bold yellow]Phase {phase_number}/{total_phases}:[/bold yellow] {phase_label}..."
    )
    console.print()


def display_task_implement_phase_complete(
    phase_number: int, total_phases: int, phase_label: str
) -> None:
    """Display a completion message after a phase finishes successfully.

    Args:
        phase_number: The 1-based index of the completed phase.
        total_phases: Total number of phases to execute.
        phase_label: Human-readable description of the phase.
    """
    console.print()
    console.print(
        f"[bold green]Phase {phase_number}/{total_phases} complete:[/bold green] {phase_label}"
    )
    console.print()


def display_task_implement_complete(task_name: str, phases_run: int) -> None:
    """Display a success message after all phases complete.

    Args:
        task_name: The task name.
        phases_run: Number of phases that were executed.
    """
    suffix = "s" if phases_run != 1 else ""
    console.print(
        f'[bold green]Task "{task_name}" implementation complete[/bold green] '
        f"({phases_run} phase{suffix} executed)"
    )


def display_task_list(tasks: list[TaskEntry], task_filter: TaskFilter) -> None:
    """Display a table of tasks or an appropriate empty-state message.

    Args:
        tasks: The list of TaskEntry models to display.
        task_filter: The active filter, used to select the empty-state message.
    """
    if not tasks:
        message = _EMPTY_MESSAGES[task_filter]
        console.print(f"[dim]{message}[/dim]")
        return

    table = Table()
    table.add_column("Name")
    table.add_column("Created")
    table.add_column("Completed")
    table.add_column("Repos")
    table.add_column("Spec")
    table.add_column("Impl")
    table.add_column("Files")
    table.add_column("Journal")

    for entry in tasks:
        completed_str = entry.completed if entry.completed is not None else ""
        repos_str = ", ".join(entry.repos) if entry.repos else "[dim]all[/dim]"
        spec_str = "[green]yes[/green]" if entry.has_spec else "[dim]-[/dim]"
        impl_str = "[green]yes[/green]" if entry.has_impl else "[dim]-[/dim]"
        files_str = "[green]yes[/green]" if entry.has_files else "[dim]-[/dim]"
        journal_str = "[green]yes[/green]" if entry.has_journal else "[dim]-[/dim]"

        table.add_row(
            entry.name,
            entry.created_date.isoformat(),
            completed_str,
            repos_str,
            spec_str,
            impl_str,
            files_str,
            journal_str,
        )

    console.print(table)


def display_task_error(message: str) -> None:
    """Display an error message for task operations.

    Args:
        message: The error message to display.
    """
    console.print(f"[bold red]Error:[/bold red] {message}")
