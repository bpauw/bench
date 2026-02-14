# Changelog

## Verion 0.7.0

### New

- Added `--add-discussion` option to `bench task create` and `bench task refine` that attaches existing discussion files to a task, giving the AI agent context from prior conversations when creating or refining specs
- Added discussion name uniqueness enforcement to `bench discuss start` -- the AI agent is now informed of existing discussion names and instructed to choose a different title

## Version 0.6.0

### New

- Added `bench populate agents` command that (re)generates the `AGENTS.md` file for the current context. Works from both project root (scans sibling directories) and workbench directories (scans `repo/` subdirectories). Supports `--model` option to override the AI model and `--repo` option to filter which repositories are included.
- Added `bench populate` command group, designed for future extensibility (e.g., `bench populate prompts`, `bench populate config`)

### Updated

- `bench init` simplified to scaffold creation only -- AGENTS.md population is now handled exclusively by `bench populate agents`
- Task prompt templates (`task-create-spec.md`, `task-refine-spec.md`) now support a `{{DISCUSSIONS}}` placeholder for injecting discussion context
- Discussion references are injected into `spec.md` between `# Spec` and `## Introduction`, making them available to all downstream implementation phases without template changes
- Refactored `populate_agents_md()` from `service/init.py` into a standalone `service/populate.py` module, generalized to support both ROOT and WORKBENCH modes
- `bench init` now imports the population logic from the new `service/populate.py` module (behavior unchanged)
- `bench populate agents` now accepts `--repo` option (repeatable) to selectively scan specific repositories instead of all discovered directories
- Added `list_repo_directories()` repository function for scanning workbench `repo/` contents in WORKBENCH mode

### Removed

- Removed `--skip-agents-md` and `--model` options from `bench init` (use `bench populate agents` instead)

## Version 0.5.0

### New

- Added `bench workbench list` command that displays all workbenches in a Rich table with name, source, git branch, and status columns. Active workbenches are shown first (in green), followed by inactive ones (dimmed). Works from any bench-aware directory.
- Added `bench workbench delete` command that permanently removes a workbench -- its workspace directory, scaffold data (`.bench/workbench/<name>/`), git branches, and config entry. Works on both active and inactive workbenches. Includes a confirmation prompt with `--yes`/`-y` to skip.
- Added automatic setup script execution as the final phase of `bench workbench create`. Executable scripts in the workbench's `bench/scripts/` directory (copied from `.bench/scripts/`) are discovered and run alphabetically after workspace provisioning. Scripts receive environment variables (`BENCH_WORKBENCH_NAME`, `BENCH_SOURCE_NAME`, `BENCH_GIT_BRANCH`, `BENCH_PROJECT_ROOT`, `BENCH_WORKBENCH_DIR`, `BENCH_SCAFFOLD_DIR`) and their output streams directly to the terminal. Non-executable scripts are warned about; failed scripts warn but do not block workbench creation.

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
