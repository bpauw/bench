from pathlib import Path

import typer

from bench.cli import discuss as discuss_module
from bench.cli import init as init_module
from bench.cli import source as source_module
from bench.cli import status as status_module
from bench.cli import task as task_module
from bench.cli import workbench as workbench_module
from bench.service.mode_detection import detect_mode
from bench.view.status import display_status

app: typer.Typer = typer.Typer()

# Register subcommands
init_module.register(app)
source_module.register(app)
workbench_module.register(app)
discuss_module.register(app)
task_module.register(app)
status_module.register(app)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Orchestration layer for agent coding."""
    if ctx.invoked_subcommand is None:
        context = detect_mode(Path.cwd())
        display_status(context)
