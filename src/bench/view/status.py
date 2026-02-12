from rich.console import Console
from rich.table import Table

from bench.model.context import BenchContext
from bench.model.mode import BenchMode

console = Console()

MODE_COLORS: dict[BenchMode, str] = {
    BenchMode.ROOT: "green",
    BenchMode.WORKBENCH: "cyan",
    BenchMode.WITHIN_ROOT: "yellow",
    BenchMode.UNINITIALIZED: "red",
}


def display_status(context: BenchContext) -> None:
    """Display the current bench mode and context using Rich formatting."""
    color = MODE_COLORS[context.mode]

    table = Table(title="Bench Status", show_header=False, title_style="bold")
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Mode", f"[{color}]{context.mode.value}[/{color}]")

    if context.mode == BenchMode.ROOT:
        if context.root_path:
            table.add_row("Root", str(context.root_path))

    elif context.mode == BenchMode.WORKBENCH:
        if context.workbench_config:
            table.add_row("Workbench", context.workbench_config.name)
        if context.root_path:
            table.add_row("Root", str(context.root_path))
        table.add_row("CWD", str(context.cwd))

    elif context.mode == BenchMode.WITHIN_ROOT:
        if context.root_path:
            table.add_row("Root", str(context.root_path))
            try:
                relative = context.cwd.relative_to(context.root_path)
                table.add_row("Position", str(relative))
            except ValueError:
                table.add_row("CWD", str(context.cwd))

    elif context.mode == BenchMode.UNINITIALIZED:
        table.add_row("Info", "No bench project found")
        table.add_row("CWD", str(context.cwd))

    # Display model configuration when available
    if context.base_config:
        table.add_row("Task Model", context.base_config.models.task)

    console.print(table)
