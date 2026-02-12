from pathlib import Path

from bench.model.opencode import OpenCodeResult
from bench.repository.opencode import run_prompt


def run_opencode_prompt(prompt: str, model: str, cwd: Path) -> OpenCodeResult:
    """Run opencode with a prompt and model in the given directory.

    This is the primary entry point for other service-layer code to invoke
    opencode. The caller is responsible for reading prompt files and rendering
    any templates before passing the prompt text.

    Args:
        prompt: The raw prompt text to send to opencode.
        model: The model identifier (e.g., "anthropic/claude-opus-4-6").
        cwd: Working directory to run opencode from.

    Returns:
        An OpenCodeResult with stdout, stderr, and return_code.

    Raises:
        RuntimeError: If opencode is not installed or the command fails.
    """
    return run_prompt(prompt, model, cwd)
