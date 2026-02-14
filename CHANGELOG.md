# Changelog

## Version 0.7.0

### New

- Added `--only-repo` option to `bench task create` and `bench discuss start` that scopes AI prompts to specific repositories. For tasks, the repo filter is persisted in `task.yaml` and automatically applied to all subsequent operations (interview, refine, implement). For discussions, the filter is ephemeral and only affects the current session.
- Added `--add-discussion` option to `bench task create` and `bench task refine` that attaches existing discussion files to a task, giving the AI agent context from prior conversations when creating or refining specs
- Added discussion name uniqueness enforcement to `bench discuss start` -- the AI agent is now informed of existing discussion names and instructed to choose a different title
- Added `bench populate agents` command that (re)generates `AGENTS.md` by scanning repositories. Works from both project root and workbench directories. Supports `--model` and `--repo` options.
- Added `bench populate` command group for regenerating AI-produced files

### Updated

- `bench init` simplified to scaffold creation only -- AGENTS.md population is now a separate step via `bench populate agents`
- Task prompt templates now support `{{DISCUSSIONS}}` and `{{EXISTING_DISCUSSIONS}}` placeholders
- Discussion references are injected into `spec.md` between `# Spec` and `## Introduction`, making them available to all downstream implementation phases
- Task list output now includes a "Repos" column showing which repositories a task is scoped to

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
