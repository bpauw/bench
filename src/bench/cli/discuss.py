from pathlib import Path
from typing import Annotated

import typer

from bench.service.discuss import list_discussions, start_discussion
from bench.view.discuss import (
    display_discuss_error,
    display_discuss_list,
    display_discuss_start,
)

discuss_app: typer.Typer = typer.Typer(help="Start and manage discussions.")


def _complete_repo_name(incomplete: str) -> list[str]:
    """Provide tab-completion for --only-repo with available repo directory names."""
    try:
        from bench.service.mode_detection import detect_mode

        context = detect_mode(Path.cwd())
        if context.workbench_config is None:
            return []
        return [
            r.dir
            for r in context.workbench_config.repos
            if r.dir.startswith(incomplete)
        ]
    except Exception:
        return []


def discuss_start_cmd(
    only_repo: Annotated[
        list[str] | None,
        typer.Option(
            "--only-repo",
            help="Scope this discussion to specific repositories (repeatable)",
            autocompletion=_complete_repo_name,
        ),
    ] = None,
) -> None:
    """Start an interactive discussion via opencode."""
    try:
        display_discuss_start()
        exit_code = start_discussion(only_repos=only_repo)
        if exit_code != 0:
            display_discuss_error(f"opencode exited with code {exit_code}")
            raise typer.Exit(code=exit_code)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        display_discuss_error(str(e))
        raise typer.Exit(code=1)


discuss_app.command("start")(discuss_start_cmd)


def discuss_list_cmd() -> None:
    """List past discussions in the current workbench."""
    try:
        discussions = list_discussions()
        display_discuss_list(discussions)
    except (ValueError, RuntimeError) as e:
        display_discuss_error(str(e))
        raise typer.Exit(code=1)


discuss_app.command("list")(discuss_list_cmd)


def register(app: typer.Typer) -> None:
    """Register the discuss subcommand group on the given Typer app."""
    app.add_typer(discuss_app, name="discuss")
