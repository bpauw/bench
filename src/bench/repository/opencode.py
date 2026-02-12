import subprocess
from pathlib import Path

from bench.model.opencode import OpenCodeResult


OPENCODE_EXECUTABLE: str = "opencode"


def _run_opencode(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Execute an opencode command in the given directory.

    Args:
        args: Command arguments (e.g., ["--prompt", "...", "--model", "...", "."]).
        cwd: Working directory to run opencode from.

    Returns:
        The completed subprocess result with captured stdout and stderr.

    Raises:
        RuntimeError: If opencode is not installed, cwd is not a directory,
                      or the command exits with a non-zero status.
    """
    if not cwd.is_dir():
        raise RuntimeError(f"Not a directory: {cwd}")

    try:
        result = subprocess.run(
            [OPENCODE_EXECUTABLE, *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=None,
        )
    except FileNotFoundError:
        raise RuntimeError(
            f"opencode is not installed or not found on PATH (tried: {OPENCODE_EXECUTABLE})"
        )

    if result.returncode != 0:
        cmd_str = " ".join([OPENCODE_EXECUTABLE, *args])
        raise RuntimeError(
            f"opencode command failed: {cmd_str}\n"
            f"Return code: {result.returncode}\n"
            f"stderr: {result.stderr.strip()}"
        )

    return result


def run_prompt(prompt: str, model: str, cwd: Path) -> OpenCodeResult:
    """Run opencode with a prompt and model in the given directory.

    Executes: opencode --prompt '<prompt>' --model <model> .

    Args:
        prompt: The raw prompt text to send to opencode.
        model: The model identifier (e.g., "anthropic/claude-opus-4-6").
        cwd: Working directory to run opencode from.

    Returns:
        An OpenCodeResult with stdout, stderr, and return_code.

    Raises:
        RuntimeError: If opencode is not installed or the command fails.
    """
    result = _run_opencode(
        ["--prompt", prompt, "--model", model, "."],
        cwd,
    )
    return OpenCodeResult(
        stdout=result.stdout,
        stderr=result.stderr,
        return_code=result.returncode,
    )


def run_prompt_interactive(prompt: str, model: str, cwd: Path) -> int:
    """Run opencode interactively with terminal pass-through.

    Unlike run_prompt(), this does not capture output — stdin, stdout, and
    stderr are connected directly to the terminal so the user can interact
    with the AI agent.

    Executes: opencode --prompt '<prompt>' --model <model> .

    Args:
        prompt: The raw prompt text to send to opencode.
        model: The model identifier (e.g., "anthropic/claude-opus-4-6").
        cwd: Working directory to run opencode from.

    Returns:
        The exit code from the opencode process.

    Raises:
        RuntimeError: If opencode is not installed or cwd is not a directory.
    """
    if not cwd.is_dir():
        raise RuntimeError(f"Not a directory: {cwd}")

    try:
        result = subprocess.run(
            [OPENCODE_EXECUTABLE, "--prompt", prompt, "--model", model, "."],
            cwd=cwd,
            check=False,
            timeout=None,
        )
    except FileNotFoundError:
        raise RuntimeError(
            f"opencode is not installed or not found on PATH (tried: {OPENCODE_EXECUTABLE})"
        )

    return result.returncode


def run_command(message: str, model: str, cwd: Path) -> int:
    """Run opencode in headless mode via the `run` subcommand.

    Executes: opencode run --model <model> <message>

    Unlike run_prompt_interactive(), this does not open an interactive TUI.
    The agent processes the message to completion and exits. stdout and stderr
    are passed through to the terminal so the user can observe progress.

    Args:
        message: The fully-substituted prompt/message text.
        model: The model identifier (e.g., "anthropic/claude-opus-4-6").
        cwd: Working directory to run opencode from.

    Returns:
        The exit code from the opencode process.

    Raises:
        RuntimeError: If opencode is not installed or cwd is not a directory.
    """
    if not cwd.is_dir():
        raise RuntimeError(f"Not a directory: {cwd}")

    try:
        result = subprocess.run(
            [OPENCODE_EXECUTABLE, "run", "--model", model, message],
            cwd=cwd,
            check=False,
            timeout=None,
        )
    except FileNotFoundError:
        raise RuntimeError(
            f"opencode is not installed or not found on PATH (tried: {OPENCODE_EXECUTABLE})"
        )

    return result.returncode
