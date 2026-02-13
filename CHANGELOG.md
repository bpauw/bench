# Changelog

## Version 0.5.0

### New

- Added `bench workbench list` command that displays all workbenches in a Rich table with name, source, git branch, and status columns. Active workbenches are shown first (in green), followed by inactive ones (dimmed). Works from any bench-aware directory.
- Added `bench workbench delete` command that permanently removes a workbench -- its workspace directory, scaffold data (`.bench/workbench/<name>/`), git branches, and config entry. Works on both active and inactive workbenches. Includes a confirmation prompt with `--yes`/`-y` to skip.

### Updated

- Tab completion for `bench workbench retire` and `bench workbench update` now only suggests active workbenches, preventing users from selecting already-retired workbenches that would fail
- `bench workbench update` now rejects inactive workbenches with a clear error message suggesting `bench workbench activate` first, instead of failing with a confusing git worktree error
- AGENTS.md template now includes a "Key Commands" section for each repository

### Removed

- Removed the unfiltered `_complete_workbench_name` autocompletion callback (replaced by status-aware variants), then re-added it for the new `workbench delete` command which needs to suggest all workbenches regardless of status

## Version 0.2.0

### New

- Added automatic AGENTS.md population during `bench init` -- after creating the project scaffold, bench now runs an AI agent that scans sibling directories and writes structured, project-specific content into `.bench/AGENTS.md`
- Added `--skip-agents-md` flag to `bench init` to skip the population step entirely
- Added `--model` option to `bench init` to override the AI model used for AGENTS.md population
- Added `populate-agents.md` prompt seed file, written to `.bench/prompts/` during init and user-editable for customization
- Added changelog template to the `task-update-change-docs.md` prompt seed

### Updated

- Simplified the default `AGENTS.md` template to a minimal placeholder, since content is now generated automatically by the AI agent
- Updated the `task-update-change-docs.md` prompt to include guidance on keeping technical details high level in README updates
