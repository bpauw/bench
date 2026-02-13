# Changelog

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
