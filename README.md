# bench

A CLI orchestration tool for agentic coding workflows.

Bench manages git worktrees organized into **workbenches** -- isolated development environments where multiple repository worktrees are grouped together for coordinated work on coding tasks. It integrates with an external AI coding agent ([opencode](https://opencode.ai)) to provide interactive spec-writing sessions, automated multi-phase task implementation, and free-form discussion sessions.

---

## Table of Contents

- [Key Concepts](#key-concepts)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Workflow Overview](#workflow-overview)
- [Commands](#commands)
  - [bench init](#bench-init)
  - [bench status](#bench-status)
  - [bench source](#bench-source)
    - [source add](#bench-source-add)
    - [source list](#bench-source-list)
    - [source update](#bench-source-update)
    - [source remove](#bench-source-remove)
  - [bench workbench](#bench-workbench)
    - [workbench create](#bench-workbench-create)
    - [workbench update](#bench-workbench-update)
    - [workbench retire](#bench-workbench-retire)
    - [workbench delete](#bench-workbench-delete)
    - [workbench activate](#bench-workbench-activate)
    - [workbench list](#bench-workbench-list)
  - [bench task](#bench-task)
    - [task create](#bench-task-create)
    - [task refine](#bench-task-refine)
    - [task implement](#bench-task-implement)
    - [task complete](#bench-task-complete)
    - [task list](#bench-task-list)
  - [bench discuss](#bench-discuss)
    - [discuss start](#bench-discuss-start)
    - [discuss list](#bench-discuss-list)
- [Configuration](#configuration)
  - [Project Configuration (base-config.yaml)](#project-configuration)
  - [Workbench Configuration (workbench-config.yaml)](#workbench-configuration)
  - [AI Model Configuration](#ai-model-configuration)
  - [Implementation Flow](#implementation-flow)
  - [Prompt Templates](#prompt-templates)
  - [AGENTS.md](#agentsmd)
- [Operating Modes](#operating-modes)
- [Architecture](#architecture)
  - [Layered Design](#layered-design)
  - [Project Structure](#project-structure)
  - [Dependencies](#dependencies)
- [Development](#development)
- [License](#license)

---

## Key Concepts

| Concept | Description |
|---|---|
| **Source** | A named collection of repository-to-branch mappings. Sources define which repos and branches are used when creating workbenches. |
| **Workbench** | An isolated development environment containing git worktrees for each repo in a source, plus orchestration metadata (`AGENTS.md`, tasks, prompts, history, discussions). |
| **Task** | A unit of work tracked within a workbench. Each task has a spec, implementation plan, file list, and notes. Tasks can be created, refined, implemented (via AI), and completed. |
| **Discussion** | A free-form AI conversation session. When finished, the agent writes a dated summary to `bench/discussions/`. |
| **Implementation Flow** | A configurable multi-phase pipeline that automates task implementation using headless AI agent sessions. Each phase has a prompt template, required inputs, and expected outputs. |

---

## Requirements

- **Python** ~=3.14.0
- **Git** >= 2.11 (for `--porcelain=v2` status format and worktree support)
- **[uv](https://docs.astral.sh/uv/)** for Python package management
- **[opencode](https://opencode.ai)** AI coding agent CLI (for `task create --interview`, `task refine`, `task implement`, and `discuss start`)

---

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd bench

# Install dependencies and the bench CLI tool
uv sync --all-groups
uv tool install .
```

Or use the Makefile:

```bash
make setup    # uv sync --all-groups
make install  # uv tool install --reinstall .
```

After installation, the `bench` command is available on your PATH.

To enable **tab completion** for shell commands, source names, workbench names, and task names:

```bash
bench --install-completion
```

---

## Quick Start

```bash
# 1. Navigate to your project root (containing your git repos)
cd ~/projects/my-project

# 2. Initialize bench (auto-populates AGENTS.md by scanning your repos)
bench init

# 3. Add a source defining which repos and branches to work with
bench source add my-source \
  --add-repo service-repo:main \
  --add-repo client-repo:develop

# 4. Create a workbench from that source
bench workbench create my-source my-workbench

# 5. Navigate into the workbench
cd workbench/my-workbench

# 6. Create a task (optionally with an interactive AI spec session)
bench task create add-auth --interview

# 7. Refine the spec if needed
bench task refine add-auth

# 8. Run the automated implementation pipeline
bench task implement add-auth

# 9. Mark the task as complete
bench task complete add-auth
```

---

## Workflow Overview

Bench follows a structured development workflow:

```
                    ┌─────────────┐
                    │  bench init │  Initialize project + populate AGENTS.md
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ source add  │  Define repo-to-branch mappings
                    └──────┬──────┘
                           │
                ┌──────────▼──────────┐
                │  workbench create   │  Create isolated dev environment
                └──────────┬──────────┘
                           │
             ┌─────────────▼─────────────┐
             │       task create         │  Create task + optional AI interview
             │    (--interview)          │
             └─────────────┬─────────────┘
                           │
                   ┌───────▼───────┐
                   │  task refine  │  Iterative AI spec refinement
                   └───────┬───────┘
                           │
               ┌───────────▼───────────┐
               │   task implement      │  Multi-phase AI implementation
               │  (plan → build → doc) │
               └───────────┬───────────┘
                           │
                  ┌────────▼────────┐
                  │  task complete  │  Mark done
                  └─────────────────┘
```

At any point during development, you can also start free-form **discussion** sessions with the AI agent using `bench discuss start`.

---

## Commands

Running `bench` with no subcommand defaults to `bench status`.

| Command | Mode | Description |
|---|---|---|
| `bench init` | UNINITIALIZED | Initialize a new bench project and populate AGENTS.md |
| `bench status` | Any | Display current mode, project root, workbench info, AI model |
| `bench source add` | ROOT | Add a named source with repo-to-branch mappings |
| `bench source list` | ROOT | List all sources |
| `bench source update` | ROOT | Add/remove repos from an existing source |
| `bench source remove` | ROOT | Remove a source (with confirmation) |
| `bench workbench create` | ROOT | Create a workbench from a source |
| `bench workbench update` | ROOT / WORKBENCH | Add/remove repos from a workbench |
| `bench workbench retire` | ROOT | Retire a workbench (preserves metadata) |
| `bench workbench delete` | ROOT | Permanently delete a workbench and all its data |
| `bench workbench activate` | ROOT | Reactivate a retired workbench |
| `bench workbench list` | ROOT / WORKBENCH / WITHIN_ROOT | List all workbenches with status |
| `bench task create` | WORKBENCH | Create a task with scaffold files |
| `bench task refine` | WORKBENCH | Interactive AI spec refinement |
| `bench task implement` | WORKBENCH | Multi-phase automated AI implementation |
| `bench task complete` | WORKBENCH | Mark a task as complete |
| `bench task list` | WORKBENCH | List tasks with progress indicators |
| `bench discuss start` | WORKBENCH | Start a free-form AI discussion |
| `bench discuss list` | WORKBENCH | List past discussions |

### bench init

Initializes a new bench project in the current directory by creating the `.bench/` directory structure and optionally populating `AGENTS.md` with AI-generated project-specific content.

```bash
bench init                          # full init with AGENTS.md population
bench init --skip-agents-md         # create scaffold only, skip AI population
bench init --model anthropic/claude-sonnet-4-20250514  # use a specific model for population
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--skip-agents-md` | flag | `False` | Skip the AGENTS.md population step entirely |
| `--model` | string | from config | Override the AI model used for AGENTS.md population (falls back to `models.task` in `base-config.yaml`) |

**What it creates:**

```
.bench/
  base-config.yaml           # Project config (sources, models, implementation flow template)
  AGENTS.md                  # Project instructions (populated by AI, or minimal placeholder)
  files/                     # Shared files copied into each new workbench
  prompts/                   # Shared prompt templates copied into each new workbench
    task-create-spec.md      # Interactive spec creation prompt
    task-refine-spec.md      # Spec refinement prompt
    task-write-impl-docs.md  # Implementation planning prompt
    task-do-impl.md          # Implementation execution prompt
    task-update-change-docs.md  # Change documentation prompt
    discuss.md               # Free-form discussion prompt
    populate-agents.md       # AGENTS.md population prompt (user-editable)
  scripts/                   # Setup scripts auto-run during workbench creation (chmod +x required)
  workbench/                 # Workbench metadata directory
```

**AGENTS.md population:**

After the scaffold is created, bench automatically detects sibling directories in the project root (any directory that is not `.bench/` or `bench/`). If directories are found, it runs an AI agent (via `opencode run`) that scans those directories and writes structured content into `.bench/AGENTS.md`. The generated content includes a "Repositories Overview" with sections for each repository covering key files, structures, features, patterns, and conventions.

The population step is designed to be resilient:
- If no sibling directories are found, population is silently skipped and the file retains a minimal placeholder.
- If `opencode` is not installed or the agent fails, a warning is displayed but `bench init` still succeeds. The `AGENTS.md` file will contain a minimal placeholder that you can edit manually.
- The prompt used for population is saved to `.bench/prompts/populate-agents.md` and can be freely edited before re-running manually.

**Validation errors:**

| Condition | Error |
|---|---|
| Already a project root | `This directory is already a bench project root.` |
| Inside a workbench | `Cannot initialize inside a workbench directory.` |
| Inside a project | `Cannot initialize inside an existing bench project. Project root is at: /path` |

---

### bench status

Displays the current bench operating mode, project root path, workbench info (if applicable), and the configured AI model.

```bash
bench status
bench              # same (default command)
```

---

### bench source

Manage named source definitions. Sources are collections of repository-to-branch mappings stored in `base-config.yaml`.

#### bench source add

```bash
# Add a source with repos
bench source add my-source --add-repo service-repo:main --add-repo client-repo:develop

# Add an empty source (repos can be added later with source update)
bench source add my-source
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | yes | Source name (must be unique) |
| `--add-repo` | option | no | Repo mapping as `directory:branch`. Repeatable. |

Each `--add-repo` value must reference an existing directory in the project root that is a git repository with a valid local branch.

**Validation errors:**

| Condition | Error |
|---|---|
| Invalid format | `Invalid --add-repo format "value". Expected format: directory-name:branch-name` |
| Directory missing | `Repository directory "name" does not exist in project root: /path` |
| Not a git repo | `Directory "name" is not a git repository` |
| Branch missing | `Branch "name" does not exist in repository "repo". Available local branches: ...` |
| Duplicate name | `Source "name" already exists. Source names must be unique.` |

#### bench source list

```bash
bench source list
```

Lists all sources with their repo-to-branch mappings. Source names are displayed in bold cyan, branches in green.

#### bench source update

```bash
# Add a repo
bench source update my-source --add-repo client-repo:develop

# Remove a repo (requires exact dir:branch match)
bench source update my-source --remove-repo service-repo:main

# Replace a repo's branch in one command (removals happen before additions)
bench source update my-source --remove-repo service-repo:main --add-repo service-repo:feature/new
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | yes | Source name |
| `--add-repo` | option | no | Repo mapping to add (`directory:branch`). Repeatable. |
| `--remove-repo` | option | no | Repo mapping to remove (`directory:branch`, exact match). Repeatable. |

At least one `--add-repo` or `--remove-repo` is required. Removals are applied before additions (deterministic order). All changes are validated before anything is written (all-or-nothing).

#### bench source remove

```bash
bench source remove my-source          # with confirmation prompt
bench source remove my-source --yes    # skip confirmation
bench source remove my-source -y       # short form
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | yes | Source name |
| `--yes` / `-y` | flag | no | Skip confirmation prompt |

Tab completion is supported for source names.

---

### bench workbench

Manage workbenches -- isolated development environments with git worktrees, orchestration metadata, and AI-assisted tooling.

#### bench workbench create

Creates a new workbench from a source definition.

```bash
bench workbench create my-source my-workbench
bench workbench create my-source my-workbench --workbench-git-branch feature/custom-branch
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `source` | positional | yes | Source to use |
| `name` | positional | yes | Workbench name (must be unique) |
| `--workbench-git-branch` | option | no | Custom git branch name for worktrees (defaults to workbench name) |

**What it creates:**

The real files live under `.bench/workbench/<name>/`:

```
.bench/workbench/<name>/
  AGENTS.md                        # Copied from .bench/AGENTS.md
  bench/
    workbench-config.yaml          # Workbench config (name, source, branch, repos, flow)
    history.md                     # Empty history log
    discussions/                   # Discussion summaries
    tasks/                         # Task folders
    files/                         # Copied from .bench/files/
    prompts/                       # Copied from .bench/prompts/
    scripts/                       # Copied from .bench/scripts/ (auto-executed during creation)
```

The workspace directory uses symlinks for portability:

```
workbench/<name>/
  AGENTS.md                        # Symlink -> .bench/workbench/<name>/AGENTS.md
  bench/                           # Symlink -> .bench/workbench/<name>/bench/
  repo/
    <repo-1>/                      # Git worktree
    <repo-2>/                      # Git worktree
    ...
```

For each repo in the source, a git worktree is created. If the branch already exists locally, it is checked out; otherwise a new branch is created from the source branch.

**Setup script execution:**

As the final step of workbench creation (Phase 11), bench automatically discovers and runs executable scripts from the workbench's `bench/scripts/` directory. These scripts are copied from `.bench/scripts/` during scaffold creation, so any scripts you place in `.bench/scripts/` will be available in every new workbench.

Script discovery rules:
- Only top-level files are scanned (subdirectories are ignored)
- Hidden files (names starting with `.`) and `.gitkeep` files are excluded
- Only files with the executable bit set (`chmod +x`) are executed
- Non-executable files trigger a warning (you likely forgot `chmod +x`)
- Scripts run in alphabetical order by filename for deterministic execution

Each script runs with the **workbench workspace root** (`workbench/<name>/`) as its working directory, so scripts can access `repo/`, `bench/`, and `AGENTS.md` via the symlinked structure. The following environment variables are available to scripts (in addition to the inherited environment):

| Variable | Value |
|---|---|
| `BENCH_WORKBENCH_NAME` | The workbench name |
| `BENCH_SOURCE_NAME` | The source name used to create the workbench |
| `BENCH_GIT_BRANCH` | The git branch name for the workbench |
| `BENCH_PROJECT_ROOT` | Absolute path to the project root directory |
| `BENCH_WORKBENCH_DIR` | Absolute path to the workbench workspace directory (`workbench/<name>/`) |
| `BENCH_SCAFFOLD_DIR` | Absolute path to the workbench scaffold directory (`.bench/workbench/<name>/`) |

Script output (stdout and stderr) streams directly to the terminal in real-time. If a script fails (non-zero exit code), a warning is displayed but the remaining scripts continue and the workbench is still considered successfully created. If no executable scripts are found, this phase completes silently.

**Example:** To automatically install dependencies in every new workbench, create `.bench/scripts/01-install-deps.sh`:

```bash
#!/bin/bash
# Runs after workbench creation
for repo_dir in repo/*/; do
    if [ -f "$repo_dir/package.json" ]; then
        echo "Installing dependencies in $repo_dir..."
        (cd "$repo_dir" && npm install)
    fi
done
```

Then make it executable: `chmod +x .bench/scripts/01-install-deps.sh`. The next `bench workbench create` will run it automatically.

**Validation errors:**

| Condition | Error |
|---|---|
| Source not found | `Source "name" not found. Available sources: ...` |
| Source has no repos | `Source "name" has no repositories defined. Add repos first.` |
| Name already used (config) | `Workbench "name" already exists in configuration.` |
| Name already used (filesystem) | `Workbench directory already exists: /path` |

#### bench workbench update

Add or remove repos from an existing active workbench.

```bash
# From project root (name required)
bench workbench update my-workbench --add-repo new-repo:main
bench workbench update my-workbench --remove-repo old-repo

# From inside a workbench directory (name inferred)
bench workbench update --add-repo new-repo:main
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | ROOT mode: yes, WORKBENCH mode: omit | Workbench name |
| `--add-repo` | option | no | Repo mapping to add (`directory:branch`). Repeatable. |
| `--remove-repo` | option | no | Repo directory to remove (just the directory name, not `dir:branch`). Repeatable. |

At least one `--add-repo` or `--remove-repo` is required. Removals happen before additions. Removal uses `git worktree remove` without `--force` -- it will fail if the worktree has uncommitted changes.

Tab completion only suggests active workbench names. Only active workbenches can be updated -- attempting to update an inactive (retired) workbench produces an error directing you to activate it first with `bench workbench activate`.

**Validation errors:**

| Condition | Error |
|---|---|
| Workbench is inactive | `Workbench "name" is inactive. Activate it first with 'bench workbench activate'.` |

#### bench workbench retire

Retires a workbench by removing the workspace directory, pruning git worktree references, and marking it as `inactive`. The `.bench/workbench/<name>/` metadata directory is preserved (history, tasks, prompts, discussions, etc.).

```bash
bench workbench retire my-workbench          # with confirmation
bench workbench retire my-workbench --yes    # skip confirmation
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | yes | Workbench name (must be active) |
| `--yes` / `-y` | flag | no | Skip confirmation prompt |

Tab completion only suggests active workbench names. Already-retired workbenches are excluded since retiring them again would fail.

**What is deleted vs. preserved:**

| Deleted | Preserved |
|---|---|
| `workbench/<name>/` (workspace, symlinks, worktrees) | `.bench/workbench/<name>/` (all metadata, history, tasks) |

#### bench workbench delete

Permanently deletes a workbench -- removing the workspace directory (if active), scaffold data (`.bench/workbench/<name>/`), git branches from all source repos, and the config entry from `base-config.yaml`. This is the destructive counterpart to `retire` (which is a soft delete that preserves metadata). Works on both active and inactive workbenches.

```bash
bench workbench delete my-workbench          # with confirmation
bench workbench delete my-workbench --yes    # skip confirmation
bench workbench delete my-workbench -y       # short form
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | yes | Workbench name (active or inactive) |
| `--yes` / `-y` | flag | no | Skip confirmation prompt |

Tab completion suggests all workbench names (both active and inactive).

**Confirmation prompt:** When `--yes` is not set, the command displays a confirmation warning that explicitly lists what will be permanently deleted: the workspace directory, the `.bench/workbench/<name>/` data, and the associated git branches. Answering "no" cancels the operation cleanly.

**What happens during deletion:**

1. If the workbench is **active**, the workspace directory (`workbench/<name>/`) is removed and git worktrees are pruned -- the same cleanup that `retire` performs.
2. Git branches created for the workbench are deleted from each source repository (using safe delete `git branch -d`). If a branch has already been deleted or doesn't exist, it is silently skipped.
3. The scaffold directory (`.bench/workbench/<name>/`) is permanently removed, including all metadata, history, tasks, prompts, and discussions.
4. The workbench entry is removed from `base-config.yaml`.

**Retire vs. Delete:**

| | Retire | Delete |
|---|---|---|
| Workspace removed | Yes | Yes (if active) |
| Git branches deleted | No | Yes |
| Scaffold (`.bench/workbench/<name>/`) removed | No | Yes |
| Config entry removed | No (status set to `inactive`) | Yes (entry deleted) |
| Reversible | Yes (via `activate`) | No |
| Works on inactive workbenches | No | Yes |

**Output after deletion:**

The command displays a summary showing the workbench name, whether the workspace was removed (if it was active), the scaffold directory that was removed, and which repos had their branches deleted.

**Validation errors:**

| Condition | Error |
|---|---|
| Workbench not found | `Workbench "name" not found. Available workbenches: ...` |
| Not at project root | `The 'workbench delete' command can only be run from the project root directory.` |
| Uninitialized directory | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |

#### bench workbench activate

Reactivates a retired workbench by recreating the workspace directory, symlinks, and git worktrees. This is the inverse of `retire`.

```bash
bench workbench activate my-workbench
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | yes | Workbench name (must be inactive) |

No confirmation needed -- activation is non-destructive. Tab completion only suggests inactive workbench names.

| Retire does | Activate undoes |
|---|---|
| Removes `workbench/<name>/` | Recreates `workbench/<name>/` with symlinks |
| Runs `git worktree prune` on each repo | Creates git worktrees for each repo |
| Sets status to `inactive` | Sets status to `active` |
| Preserves `.bench/workbench/<name>/` | Reads from `.bench/workbench/<name>/` |

#### bench workbench list

Lists all workbenches in the current bench project, displayed as a Rich table.

```bash
bench workbench list
```

This command takes no arguments or flags. It always shows all workbenches, grouped by status.

**Table columns:**

| Column | Description |
|---|---|
| Name | Workbench name |
| Source | Source definition used to create the workbench |
| Git Branch | The git branch used for worktrees |
| Status | `active` (green) or `inactive` (dimmed) |

**Ordering:** Active workbenches are listed first (sorted alphabetically by name), followed by inactive workbenches (also sorted alphabetically by name).

**Example output:**

```
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Name          ┃ Source    ┃ Git Branch    ┃ Status   ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ add-auth      │ my-source │ add-auth      │ active   │
│ fix-api       │ my-source │ fix-api       │ active   │
│ old-feature   │ my-source │ old-feature   │ inactive │
└───────────────┴───────────┴───────────────┴──────────┘
```

**Empty state:** When no workbenches have been created yet, the command displays:

```
No workbenches defined. Use 'bench workbench create' to create one.
```

**Mode support:** Unlike most workbench commands (which require ROOT mode), `bench workbench list` works from any bench-aware directory -- ROOT, WORKBENCH, or WITHIN_ROOT. This makes it convenient to check the full list of workbenches regardless of where you are in the project tree. Running it from an uninitialized directory produces an error directing you to run `bench init` first.

---

### bench task

Manage tasks within a workbench. All task commands require WORKBENCH mode (run from inside a workbench directory).

#### bench task create

Creates a new task with a dated folder and scaffold files.

```bash
bench task create add-auth                  # create task scaffold
bench task create add-auth --interview      # create + launch interactive AI spec session
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | yes | Task name (must be unique within the workbench) |
| `--interview` | flag | no | Launch an interactive AI session to build the spec |

**What it creates:**

```
bench/tasks/YYYYMMDD - <name>/
  task.yaml     # Metadata: name + completed date (null until completed)
  spec.md       # Specification template (Introduction, Goals, Specification)
  files.md      # Files relevant to the task (initially empty)
  impl.md       # Implementation plan (initially empty)
  notes.md      # Miscellaneous notes (initially empty)
```

**task.yaml format:**

```yaml
name: add-auth
completed: null
```

**`--interview` flag:** After creating the scaffold, reads the `task-create-spec.md` prompt template, substitutes `{{TASK}}` with the full task folder name (e.g., `20260208 - add-auth`), and launches opencode interactively. The AI agent engages in a back-and-forth conversation to build a complete specification document in `spec.md`.

#### bench task refine

Refines an existing task's specification through an interactive AI session.

```bash
bench task refine add-auth
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | yes | Task name |

Reads `task-refine-spec.md`, substitutes `{{TASK}}` and `{{REPOSITORIES}}`, and launches opencode interactively. The AI reviews the existing spec for completeness and asks clarifying questions to improve it.

Requires `spec.md` to exist in the task folder.

#### bench task implement

Runs the configurable multi-phase implementation pipeline using headless AI agent sessions.

```bash
bench task implement add-auth
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | yes | Task name |

**Default implementation flow (3 phases):**

| Phase | Name | Prompt | Required Inputs | Expected Outputs |
|---|---|---|---|---|
| 1 | Writing implementation docs | `task-write-impl-docs.md` | `spec.md` | `impl.md` |
| 2 | Implementing | `task-do-impl.md` | `spec.md`, `impl.md` | -- |
| 3 | Updating change docs | `task-update-change-docs.md` | `spec.md`, `impl.md` | -- |

Each phase:
1. Validates all `required-files` exist and are non-empty
2. Reads and renders the prompt template (substituting `{{TASK}}` and `{{REPOSITORIES}}`)
3. Runs opencode in **headless mode** (`opencode run`) -- the agent processes the prompt to completion and exits automatically
4. Validates all `output-files` were created and are non-empty

If any phase fails, execution stops immediately.

**Output during execution:**

```
Implementing task "add-auth"
  Folder: 20260208 - add-auth
  Phases: Writing implementation docs, Implementing, Updating change docs (3 total)

Phase 1/3: Writing implementation docs...
[opencode run -- headless agent session]
Phase 1/3 complete: Writing implementation docs

Phase 2/3: Implementing...
[opencode run -- headless agent session]
Phase 2/3 complete: Implementing

Phase 3/3: Updating change docs...
[opencode run -- headless agent session]
Phase 3/3 complete: Updating change docs

Task "add-auth" implementation complete (3 phases executed)
```

See [Implementation Flow](#implementation-flow) for customization details.

#### bench task complete

Marks a task as complete by setting `completed` in `task.yaml` to today's date.

```bash
bench task complete add-auth
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | positional | yes | Task name |

**task.yaml after completion:**

```yaml
name: add-auth
completed: '2026-02-09'
```

#### bench task list

Lists tasks in the current workbench with metadata in a Rich table.

```bash
bench task list                # open tasks only (default)
bench task list --all          # all tasks (open + completed)
bench task list --completed    # completed tasks only
```

| Option | Description |
|---|---|
| `--all` | Show all tasks |
| `--completed` | Show only completed tasks |

`--all` and `--completed` are mutually exclusive.

**Table columns:**

| Column | Description |
|---|---|
| Name | Task name |
| Created | Date from folder prefix (YYYY-MM-DD) |
| Completed | Completion date, or empty |
| Spec | Green "yes" if `spec.md` exists and is non-empty |
| Impl | Green "yes" if `impl.md` exists and is non-empty |
| Files | Green "yes" if `files.md` exists and is non-empty |

Tasks are sorted by creation date ascending. Tasks with missing or malformed `task.yaml` are silently skipped.

---

### bench discuss

Start and manage free-form AI discussion sessions.

#### bench discuss start

Launches an interactive opencode discussion session.

```bash
bench discuss start
```

The AI agent engages in a free-form conversation. When the conversation ends, the agent writes a dated summary markdown file to `bench/discussions/YYYYMMDD - <title>.md` capturing the main topics, decisions, action items, and reasoning discussed.

#### bench discuss list

Lists past discussions as a Rich table.

```bash
bench discuss list
```

Scans `bench/discussions/` for `.md` files matching the `YYYYMMDD - <title>.md` pattern. Displays name and creation date, sorted by date ascending.

---

## Configuration

### Project Configuration

**File:** `.bench/base-config.yaml`

The central configuration file for a bench project.

```yaml
sources:
  - name: my-source
    repos:
      - dir: service-repo
        source-branch: main
      - dir: client-repo
        source-branch: develop

workbenches:
  - name: my-workbench
    source: my-source
    git-branch: my-workbench
    status: active

models:
  task: anthropic/claude-opus-4-6
  discuss: anthropic/claude-opus-4-6

implementation-flow-template:
  - name: Writing implementation docs
    prompt: task-write-impl-docs.md
    required-files:
      - spec.md
    output-files:
      - impl.md
  - name: Implementing
    prompt: task-do-impl.md
    required-files:
      - spec.md
      - impl.md
    output-files: []
  - name: Updating change docs
    prompt: task-update-change-docs.md
    required-files:
      - spec.md
      - impl.md
    output-files: []
```

| Section | Description |
|---|---|
| `sources` | Named source definitions with repo-to-branch mappings |
| `workbenches` | Registry of workbenches with name, source, git branch, and active/inactive status |
| `models` | AI model identifiers for different operations |
| `implementation-flow-template` | Template for new workbenches' implementation pipeline |

### Workbench Configuration

**File:** `.bench/workbench/<name>/bench/workbench-config.yaml`

Per-workbench configuration, created when a workbench is created and independent of the project template afterward.

```yaml
name: my-workbench
source: my-source
git-branch: my-workbench
repos:
  - dir: service-repo
    source-branch: main
implementation-flow:
  - name: Writing implementation docs
    prompt: task-write-impl-docs.md
    required-files:
      - spec.md
    output-files:
      - impl.md
  - name: Implementing
    prompt: task-do-impl.md
    required-files:
      - spec.md
      - impl.md
    output-files: []
  - name: Updating change docs
    prompt: task-update-change-docs.md
    required-files:
      - spec.md
      - impl.md
    output-files: []
```

### AI Model Configuration

The `models` section in `base-config.yaml` configures which AI models the coding agent uses.

| Field | Default | Description |
|---|---|---|
| `models.task` | `anthropic/claude-opus-4-6` | Model for task operations (create --interview, refine, implement) |
| `models.discuss` | `anthropic/claude-opus-4-6` | Model for discussion sessions |

The `Models` configuration is designed to be extensible -- additional fields (e.g., `planning`, `code_review`) can be added as needed.

### Implementation Flow

The implementation pipeline is fully customizable per-project and per-workbench.

**Two locations:**

| Location | Scope | Used when |
|---|---|---|
| `base-config.yaml` -> `implementation-flow-template` | Project-wide template | Copied into new workbenches at creation time |
| `workbench-config.yaml` -> `implementation-flow` | Per-workbench | Used by `bench task implement`; can diverge from the template |

**Step schema:**

```yaml
- name: My Custom Step             # Display name for progress output
  prompt: my-custom-prompt.md      # Prompt template filename (in bench/prompts/)
  required-files:                  # Must exist and be non-empty before this step
    - spec.md
  output-files:                    # Must exist and be non-empty after this step
    - impl.md
```

You can add, remove, or reorder steps. Each step runs opencode in headless mode (`opencode run`).

### Prompt Templates

Prompt templates are markdown files in `bench/prompts/` within each workbench. They contain two placeholders substituted at runtime:

| Placeholder | Replaced with |
|---|---|
| `{{TASK}}` | Full task folder name (e.g., `20260208 - add-auth`) |
| `{{REPOSITORIES}}` | A `<repositories>` block listing all repo directories from the workbench config |

**Rendered `{{REPOSITORIES}}` example:**

```xml
<repositories>
./repo/service-repo
./repo/client-repo
</repositories>
```

**Seed prompt templates created by `bench init`:**

| File | Used by | Purpose |
|---|---|---|
| `task-create-spec.md` | `task create --interview` | Interactive back-and-forth to build `spec.md` |
| `task-refine-spec.md` | `task refine` | Review spec for completeness, ask clarifying questions |
| `task-write-impl-docs.md` | `task implement` (phase 1) | Read spec, write `impl.md`, `notes.md`, `files.md` |
| `task-do-impl.md` | `task implement` (phase 2) | Read spec + impl docs, implement the feature |
| `task-update-change-docs.md` | `task implement` (phase 3) | Use `git diff` to update `CHANGELOG.md` and `README.md` |
| `populate-agents.md` | `bench init` | AI prompt for scanning repos and populating `AGENTS.md` |
| `discuss.md` | `discuss start` | Free-form conversation with summary generation |

All prompt templates are freely editable. Paths within prompts are relative to the workbench directory.

### AGENTS.md

Each workbench has an `AGENTS.md` file (copied from `.bench/AGENTS.md` at creation) that provides project-wide instructions to the AI agent. This file is referenced by all prompt templates and is read by the agent at the start of every session.

During `bench init`, the `AGENTS.md` file is automatically populated by an AI agent that scans all sibling directories in the project root. The agent produces a structured "Repositories Overview" document with sections for each repository covering key commands, key files, structures, features, patterns, and conventions. This gives the AI agent immediate context about the entire project when working on tasks.

If the auto-population step is skipped (via `--skip-agents-md`) or fails, the file contains a minimal placeholder that can be manually edited. The prompt used for population is stored at `.bench/prompts/populate-agents.md` and can be customized before re-running.

---

## Operating Modes

Bench detects its operating mode by walking up the directory tree from the current working directory:

| Mode | Condition | Available commands |
|---|---|---|
| **ROOT** | CWD is the project root (contains `.bench/base-config.yaml`) | `source *`, `workbench *`, `status` |
| **WORKBENCH** | CWD is a workbench workspace (has `bench/workbench-config.yaml`) | `task *`, `discuss *`, `status` |
| **WITHIN_ROOT** | Inside a project but not at root or in a workbench | `status` |
| **UNINITIALIZED** | No bench project found (walked to filesystem root) | `init` |

Both `.bench/` (canonical) and `bench/` (fallback) directory names are supported for project detection.

---

## Architecture

### Layered Design

The codebase follows a strict 5-layer architecture with unidirectional dependency flow:

```
                     +-----------+
                     |    cli    |   Command definitions (Typer)
                     +-----+-----+
                      /          \
                     v            v
              +-----------+  +-----------+
              |  service  |  |   view    |   Business logic / Presentation
              +-----+-----+  +-----------+
                    |              |
                    v              |
              +-----------+        |
              | repository|   Filesystem & Git I/O
              +-----------+        |
                    \             /
                     v           v
                    +-----------+
                    |   model   |   Shared data structures (Pydantic)
                    +-----------+
```

**Dependency rules:**

- **cli** -- Thin command handlers (5-10 lines each). Calls a service function, passes the result to a view function, handles exceptions. Depends on service and view.
- **service** -- Business logic, validation, orchestration. Depends on repository and model.
- **repository** -- Raw I/O: filesystem operations, git subprocess calls, opencode subprocess calls. Depends on model.
- **view** -- Rich terminal output (tables, colored text). Depends on model only.
- **model** -- Pydantic data models and enums. No dependencies on other layers.

### Project Structure

```
src/bench/
  __init__.py
  cli/
    __init__.py            # Typer app, command registration, default callback
    init.py                # bench init
    status.py              # bench status
    source.py              # bench source {add,list,update,remove}
    workbench.py           # bench workbench {create,update,retire,delete,activate,list}
    task.py                # bench task {create,refine,implement,complete,list}
    discuss.py             # bench discuss {start,list}
  model/
    __init__.py            # Re-exports all model classes
    mode.py                # BenchMode enum
    config.py              # BaseConfig, WorkbenchConfig, Models, ImplementationStep
    context.py             # BenchContext (runtime state)
    git.py                 # FileStatus, GitFileChange, GitStatus
    opencode.py            # OpenCodeResult
    source.py              # Source, SourceRepo
    task.py                # TaskConfig, TaskEntry, TaskFilter
    workbench.py           # WorkbenchEntry, WorkbenchStatus
    discuss.py             # DiscussionEntry
  service/
    __init__.py            # Re-exports public service functions
    mode_detection.py      # detect_mode()
    init.py                # initialize_project(), populate_agents_md()
    git.py                 # get_git_status(), create_git_branch(), push_git_branch()
    opencode.py            # run_opencode_prompt()
    source.py              # add/list/update/remove_source()
    workbench.py           # create/update/retire/delete/activate/list workbench functions
    task.py                # create/complete/list/refine/implement task functions
    discuss.py             # start_discussion(), list_discussions()
    _validation.py         # parse_repo_arg(), validate_repo() (private helpers)
  repository/
    __init__.py            # Re-exports public repository functions
    filesystem.py          # YAML I/O, scaffold creation, task/prompt helpers, constants
    git.py                 # Raw git CLI operations via subprocess
    opencode.py            # Raw opencode CLI operations via subprocess
  view/
    __init__.py            # Re-exports public view functions
    init.py                # Init display
    status.py              # Status display
    source.py              # Source display
    workbench.py           # Workbench display
    task.py                # Task display
    discuss.py             # Discussion display
```

### Dependencies

**Runtime:**

| Package | Purpose |
|---|---|
| [typer](https://typer.tiangolo.com/) | CLI framework (commands, arguments, options, tab completion) |
| [rich](https://rich.readthedocs.io/) | Terminal output (tables, colored text, formatting) |
| [pyyaml](https://pyyaml.org/) | YAML parsing for config and data files |
| [pydantic](https://docs.pydantic.dev/) | Data validation and model definitions |

**Dev:**

| Package | Version | Purpose |
|---|---|---|
| [ruff](https://docs.astral.sh/ruff/) | 0.15.0 | Linting and code formatting |
| [ty](https://docs.astral.sh/ty/) | 0.0.15 | Type checking |

**External tools (must be on PATH):**

| Tool | Purpose |
|---|---|
| `git` (>= 2.11) | Git operations (worktrees, branching, status parsing) |
| `opencode` | AI coding agent (interactive TUI and headless `run` mode) |

---

## Development

### Setup

```bash
make setup    # uv sync --all-groups
```

### Quality Checks

```bash
make check
```

This runs sequentially:
1. `ruff check --show-fixes --fix src/` -- linting with auto-fix
2. `ruff format src/` -- code formatting
3. `ty check src/` -- type checking

### Install (after changes)

```bash
make install  # uv tool install --reinstall .
```

### Entry Point

The CLI entry point is defined in `pyproject.toml`:

```toml
[project.scripts]
bench = 'bench.cli:app'
```

This points to the Typer application instance in `src/bench/cli/__init__.py`.

---

## License

MIT License. Copyright (c) 2026 Berthold Pauw.
