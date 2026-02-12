# bench

A CLI tool for managing development workbenches and worktrees.

## Overview

Bench is a CLI orchestration system for agentic coding workflows. It manages git worktrees organized into "workbenches" — isolated development environments where multiple repository worktrees are grouped together for coordinated work on coding tasks.

### Key Concepts

- **Source** — A named collection of repository-to-branch mappings stored in `base-config.yaml`. Sources define which repositories and branches are used when creating workbenches.
- **Workbench** — A directory containing a set of git worktrees created from a source, along with orchestration metadata (an `AGENTS.md` file and a `bench` folder)

## Requirements

- Python ~=3.14.0
- Git >= 2.11 (for porcelain v2 status format)
- [uv](https://docs.astral.sh/uv/) for package management

## Installation

```bash
# Clone the repository and install
uv sync --all-groups
uv tool install .
```

Or use the Makefile:

```bash
make setup    # uv sync --all-groups
make install  # uv tool install --reinstall .
```

After installation, the `bench` command is available on your PATH.

## Usage

```bash
bench --help
bench init
bench status
bench source add my-source --add-repo service-repo:main
bench source list
bench source update my-source --add-repo client-repo:develop
bench source update my-source --remove-repo service-repo:main --add-repo service-repo:feature/new
bench source remove my-source
bench source remove my-source --yes
bench workbench create my-source my-workbench
bench workbench create my-source my-workbench --workbench-git-branch custom-branch
bench workbench update my-workbench --add-repo new-repo:main
bench workbench update my-workbench --remove-repo old-repo
bench workbench update --add-repo new-repo:main   # from workbench directory
bench workbench retire my-workbench                # retire a workbench (with confirmation)
bench workbench retire my-workbench --yes          # retire without confirmation
bench workbench activate my-workbench              # activate a retired workbench
bench task create add-auth                         # from workbench directory
bench task create add-auth --interview             # create task + interactive spec session
bench task refine add-auth                         # from workbench directory — refine existing task spec
bench task implement add-auth                      # from workbench directory — run all configured implementation phases
bench task complete add-auth                       # from workbench directory — mark task as complete
bench task list                                    # from workbench directory — list open tasks
bench task list --all                              # list all tasks (including completed)
bench task list --completed                        # list only completed tasks
```

### Commands

| Command            | Description                                                      |
|--------------------|------------------------------------------------------------------|
| `init`             | Initialize a new bench project in the current directory          |
| `status`           | Display the current bench mode, project root, workbench info, and configured AI model |
| `source add`       | Add a named source to the bench project configuration            |
| `source list`      | List all sources and their repository-branch mappings            |
| `source update`    | Update an existing source by adding or removing repository mappings |
| `source remove`    | Remove a named source from the bench project configuration       |
| `workbench create` | Create a new workbench from a source definition                  |
| `workbench update` | Update an existing workbench by adding or removing repositories  |
| `workbench retire` | Retire a workbench by removing its workspace and pruning worktrees |
| `workbench activate` | Activate a retired workbench by recreating its workspace and worktrees |
| `task create`      | Create a new task in the current workbench with scaffold files   |
| `task refine`      | Refine an existing task's specification via an interactive AI session |
| `task implement`   | Implement a task through sequential AI-assisted phases from the configured implementation flow |
| `task complete`    | Mark a task as complete by setting its completed date in task.yaml             |
| `task list`        | List tasks in the current workbench with progress indicators                   |

Running `bench` with no subcommand defaults to `bench status`.

### `bench init`

Initializes a new bench project in the current directory by creating the `.bench/` directory structure with all necessary scaffolding files.

```bash
# Initialize a new bench project
bench init
```

**No arguments or options.**

**What it creates:**

| Path                        | Description                                  |
|-----------------------------|----------------------------------------------|
| `.bench/`                   | Bench configuration directory                |
| `.bench/base-config.yaml`  | Project config with `sources: []`, default `models` section, and default `implementation-flow-template` |
| `.bench/files/`             | Shared files directory (with `.gitkeep`)     |
| `.bench/prompts/`           | Shared prompts directory (with `.gitkeep` and seed prompt files) |
| `.bench/prompts/task-create-spec.md` | Seed prompt: interactive spec creation workflow |
| `.bench/prompts/task-refine-spec.md` | Seed prompt: spec refinement workflow |
| `.bench/prompts/task-write-impl-docs.md` | Seed prompt: implementation planning workflow |
| `.bench/prompts/task-do-impl.md` | Seed prompt: implementation execution workflow |
| `.bench/prompts/task-update-change-docs.md` | Seed prompt: change documentation workflow |
| `.bench/scripts/`           | Shared scripts directory (with `.gitkeep`)   |
| `.bench/workbench/`         | Workbench metadata directory (with `.gitkeep`) |
| `.bench/AGENTS.md`          | Agent instructions template                  |

**Output on success:**

```
Initialized bench project

  created .bench/
  created .bench/base-config.yaml
  created .bench/files/
  created .bench/files/.gitkeep
  created .bench/prompts/
  created .bench/prompts/.gitkeep
  created .bench/scripts/
  created .bench/scripts/.gitkeep
  created .bench/workbench/
  created .bench/workbench/.gitkeep
  created .bench/prompts/task-create-spec.md
  created .bench/prompts/task-refine-spec.md
  created .bench/prompts/task-write-impl-docs.md
  created .bench/prompts/task-do-impl.md
  created .bench/prompts/task-update-change-docs.md
  created .bench/AGENTS.md
```

**Validation errors:**

| Condition              | Error message                                                                                       |
|------------------------|-----------------------------------------------------------------------------------------------------|
| Already a project root | `This directory is already a bench project root.`                                                   |
| Inside a workbench     | `Cannot initialize inside a workbench directory.`                                                   |
| Inside a project       | `Cannot initialize inside an existing bench project. Project root is at: /path`                     |

### `bench source add`

Creates a named source entry in `base-config.yaml`. Sources define repository-to-branch mappings used when creating workbenches.

```bash
# Add a source with no repos
bench source add my-source

# Add a source with one repo
bench source add my-source --add-repo service-repo:main

# Add a source with multiple repos
bench source add my-source --add-repo service-repo:main --add-repo client-repo:develop
```

**Arguments:**

| Argument | Type       | Required | Description                           |
|----------|------------|----------|---------------------------------------|
| `name`   | positional | yes      | Name of the source to create          |

**Options:**

| Option       | Type   | Required | Description                                                                 |
|--------------|--------|----------|-----------------------------------------------------------------------------|
| `--add-repo` | string | no       | Repository mapping in `directory-name:branch-name` format. Can be repeated. |

**Behavior:**

- Only runs in ROOT mode (from the project root directory containing `.bench/base-config.yaml`)
- Source names must be unique — duplicates are rejected
- All `--add-repo` values are validated before any changes are written (all-or-nothing)
- Each `--add-repo` value must reference an existing directory in the project root that is a git repository, with a valid local branch name

**Validation errors:**

| Condition                  | Error message                                                                     |
|----------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder       | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in project root        | `The 'source add' command can only be run from the project root directory.`        |
| Invalid `--add-repo` format | `Invalid --add-repo format "value". Expected format: directory-name:branch-name`  |
| Directory doesn't exist    | `Repository directory "name" does not exist in project root: /path`               |
| Not a git repository       | `Directory "name" is not a git repository`                                        |
| Branch doesn't exist       | `Branch "name" does not exist in repository "repo". Available local branches: ...`|
| Duplicate source name      | `Source "name" already exists. Source names must be unique.`                       |

**Config example:**

After running `bench source add my-source --add-repo service-repo:main --add-repo client-repo:develop`:

```yaml
sources:
  - name: my-source
    repos:
      - dir: service-repo
        source-branch: main
      - dir: client-repo
        source-branch: develop
models:
  task: anthropic/claude-opus-4-6
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

### `bench source list`

Lists all sources defined in `base-config.yaml`, showing each source's name and its repository-to-branch mappings.

```bash
bench source list
```

**Output format:**

```
Sources:
  * my-source
      - service-repo -> main
      - client-repo -> develop
  * another-source
      - api-repo -> feature/auth
```

- Source names displayed in **bold cyan**
- Branch names in **green**
- Structural characters (`*`, `-`, `->`, heading) are **dimmed**

**Empty state:** If no sources are defined, prints: `No sources defined. Use 'bench source add' to create one.`

**Validation errors:**

| Condition            | Error message                                                                     |
|----------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in project root  | `The 'source list' command can only be run from the project root directory.`       |

### `bench source update`

Updates an existing source by removing and/or adding repository mappings. Removals are applied before additions, which allows replacing a repo's branch in a single invocation.

```bash
# Add a repo to an existing source
bench source update my-source --add-repo client-repo:develop

# Remove a repo from an existing source
bench source update my-source --remove-repo service-repo:main

# Replace a repo's branch (remove then add in one command)
bench source update my-source --remove-repo service-repo:main --add-repo service-repo:feature/new

# Multiple operations at once
bench source update my-source --remove-repo old-repo:main --add-repo new-repo:main --add-repo another-repo:develop
```

**Arguments:**

| Argument | Type       | Required | Description                           |
|----------|------------|----------|---------------------------------------|
| `name`   | positional | yes      | Name of the source to update          |

**Options:**

| Option         | Type   | Required | Description                                                                                        |
|----------------|--------|----------|----------------------------------------------------------------------------------------------------|
| `--add-repo`   | string | no       | Repository mapping to add in `directory-name:branch-name` format. Can be repeated.                 |
| `--remove-repo`| string | no       | Repository mapping to remove in `directory-name:branch-name` format. Must be an exact match. Can be repeated. |

At least one `--add-repo` or `--remove-repo` option is required.

**Behavior:**

- Only runs in ROOT mode (from the project root directory containing `.bench/base-config.yaml`)
- Removals are applied before additions (operation order is deterministic)
- All-or-nothing validation: all removals and additions are validated before any changes are written
- `--remove-repo` requires an exact `dir:branch` match against the source's current repos
- `--add-repo` checks for duplicate directory names (after removals are applied) — a source cannot have two entries for the same directory
- `--add-repo` values undergo full validation: directory must exist in the project root, must be a git repository, and the branch must exist locally
- Duplicates within the `--add-repo` list itself are also detected

**Validation errors:**

| Condition                    | Error message                                                                              |
|------------------------------|--------------------------------------------------------------------------------------------|
| Uninitialized folder         | `This folder is uninitialized. Run 'bench init' to create a bench project first.`          |
| Not in project root          | `The 'source update' command can only be run from the project root directory.`              |
| No options provided          | `At least one --add-repo or --remove-repo option is required.`                              |
| Source not found             | `Source "name" not found. Available sources: ...`                                           |
| Remove target not found      | `Repo "dir:branch" not found in source "name". Available repos: ...`                        |
| Duplicate directory on add   | `Repository directory "name" already exists in source "name". Remove it first or use a different directory.` |
| Invalid `--add-repo` format  | `Invalid --add-repo format "value". Expected format: directory-name:branch-name`            |
| Directory doesn't exist      | `Repository directory "name" does not exist in project root: /path`                         |
| Not a git repository         | `Directory "name" is not a git repository`                                                  |
| Branch doesn't exist         | `Branch "name" does not exist in repository "repo". Available local branches: ...`          |

### `bench source remove`

Removes a named source from `base-config.yaml`. Displays a confirmation prompt with the source's repository mappings before removal.

```bash
# Remove a source (with confirmation prompt)
bench source remove my-source

# Remove a source without confirmation (for scripting)
bench source remove my-source --yes
bench source remove my-source -y
```

**Arguments:**

| Argument | Type       | Required | Description                           |
|----------|------------|----------|---------------------------------------|
| `name`   | positional | yes      | Name of the source to remove          |

**Options:**

| Option       | Type | Required | Description                    |
|--------------|------|----------|--------------------------------|
| `--yes`/`-y` | flag | no       | Skip the confirmation prompt   |

**Behavior:**

- Only runs in ROOT mode (from the project root directory containing `.bench/base-config.yaml`)
- Shows a detailed confirmation prompt before removal:
  - With repos: `Source "my-source" has 2 repo(s): service-repo -> main, client-repo -> develop. Remove?`
  - Without repos: `Source "my-source" has no repositories. Remove?`
- The `--yes` / `-y` flag bypasses the confirmation prompt
- If the user declines, prints `Removal cancelled.` and exits with code 0
- On success, prints green message: `Source "my-source" removed successfully`
- Tab autocompletion is supported for source names (requires shell completion installed via `bench --install-completion`)

**Validation errors:**

| Condition                  | Error message                                                                     |
|----------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder       | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in project root        | `The 'source remove' command can only be run from the project root directory.`     |
| Source not found           | `Source "name" not found. Available sources: ...`                                  |

### `bench workbench create`

Creates a new workbench from a source definition. A workbench is an isolated development environment containing git worktrees for each repository in the source, along with orchestration metadata (AGENTS.md, config, history, prompts, files, scripts).

```bash
# Create a workbench using the default branch name (same as workbench name)
bench workbench create my-source my-workbench

# Create a workbench with a custom git branch name for worktrees
bench workbench create my-source my-workbench --workbench-git-branch feature/custom-branch
```

**Arguments:**

| Argument | Type       | Required | Description                                |
|----------|------------|----------|--------------------------------------------|
| `source` | positional | yes      | Name of the source to use                  |
| `name`   | positional | yes      | Name of the workbench to create            |

**Options:**

| Option                    | Type   | Required | Description                                                                  |
|---------------------------|--------|----------|------------------------------------------------------------------------------|
| `--workbench-git-branch`  | string | no       | Custom git branch name for worktrees (defaults to workbench name)            |

**Behavior:**

- Only runs in ROOT mode (from the project root directory containing `.bench/base-config.yaml`)
- The specified source must exist and have at least one repository defined
- Workbench names must be unique (checked in both config and filesystem)
- For each repo in the source, a git worktree is created:
  - If the branch already exists locally in the repo, it is checked out
  - If the branch does not exist, a new branch is created from the source-branch
- Symlinks use relative paths for portability (project can be moved without breaking links)

**What it creates:**

In `.bench/workbench/<name>/` (real files):

| Path                                   | Description                                      |
|----------------------------------------|--------------------------------------------------|
| `AGENTS.md`                            | Copied from `.bench/AGENTS.md`                   |
| `bench/workbench-config.yaml`          | Workbench config (name, source, git-branch, repos)|
| `bench/history.md`                     | Empty history file                               |
| `bench/discussions/`                   | Empty directory (with `.gitkeep`)                |
| `bench/tasks/`                         | Empty directory (with `.gitkeep`)                |
| `bench/files/`                         | Copied from `.bench/files/`                      |
| `bench/prompts/`                       | Copied from `.bench/prompts/`                    |
| `bench/scripts/`                       | Copied from `.bench/scripts/`                    |

In `workbench/<name>/` (workspace with symlinks):

| Path                                   | Description                                      |
|----------------------------------------|--------------------------------------------------|
| `AGENTS.md`                            | Symlink to `.bench/workbench/<name>/AGENTS.md`   |
| `bench/`                               | Symlink to `.bench/workbench/<name>/bench/`      |
| `repo/<repo-dir>/`                     | Git worktree for each repo in the source         |

**Config updates:**

After running `bench workbench create my-source my-workbench`, `base-config.yaml` is updated:

```yaml
sources:
  - name: my-source
    repos:
      - dir: service-repo
        source-branch: main
workbenches:
  - name: my-workbench
    source: my-source
    git-branch: my-workbench
    status: active
models:
  task: anthropic/claude-opus-4-6
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

And `workbench-config.yaml` is created:

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

**Output on success:**

```
Workbench "my-workbench" created successfully
  Source: my-source
  Git branch: my-workbench
  Repositories:
    service-repo -> workbench/my-workbench/repo/service-repo
```

**Validation errors:**

| Condition                    | Error message                                                                     |
|------------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder         | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in project root          | `The 'workbench create' command can only be run from the project root directory.`  |
| Source not found             | `Source "name" not found. Available sources: ...`                                  |
| Source has no repos          | `Source "name" has no repositories defined. Add repos first.`                      |
| Workbench already exists (config) | `Workbench "name" already exists in configuration.`                           |
| Workbench already exists (fs)     | `Workbench directory already exists: /path`                                   |
| Git worktree failure         | Runtime error from git with stderr output                                         |

### `bench workbench update`

Updates an existing workbench by adding or removing repositories. This command modifies the workbench's repository set and manages git worktrees accordingly. Removals are applied before additions, which allows replacing a repo in a single invocation.

```bash
# From project root — add a repo to a workbench
bench workbench update my-workbench --add-repo new-repo:main

# From project root — remove a repo from a workbench
bench workbench update my-workbench --remove-repo old-repo

# From project root — add and remove in one command
bench workbench update my-workbench --remove-repo old-repo --add-repo new-repo:main

# From project root — replace a repo's branch
bench workbench update my-workbench --remove-repo service-repo --add-repo service-repo:feature-branch

# From a workbench directory — name is inferred
bench workbench update --add-repo new-repo:main
bench workbench update --remove-repo old-repo
```

**Arguments:**

| Argument | Type       | Required                             | Description                                |
|----------|------------|--------------------------------------|--------------------------------------------|
| `name`   | positional | yes (ROOT mode) / omit (WORKBENCH)   | Name of the workbench to update            |

**Options:**

| Option         | Type   | Required | Description                                                                 |
|----------------|--------|----------|-----------------------------------------------------------------------------|
| `--add-repo`   | string | no       | Repository mapping to add in `directory-name:branch-name` format. Can be repeated. |
| `--remove-repo`| string | no       | Repository directory name to remove. Can be repeated.                       |

At least one `--add-repo` or `--remove-repo` option is required.

**Behavior:**

- Runs in ROOT mode (workbench name as positional argument) or WORKBENCH mode (name inferred from current directory)
- In WORKBENCH mode, providing a positional name argument is an error
- In ROOT mode, the positional name argument is required
- Removals are applied before additions (operation order is deterministic)
- All-or-nothing validation: all removals and additions are validated before any changes are made
- `--remove-repo` takes just the directory name (not `dir:branch` like source update)
- `--remove-repo` uses `git worktree remove` without `--force` — will fail if the worktree has uncommitted changes
- `--add-repo` checks for duplicate directory names (after removals are applied)
- For each added repo, if the workbench's `git-branch` already exists in that repo, it is checked out; otherwise a new branch is created from the source-branch

**Config updates:**

After running `bench workbench update my-workbench --add-repo new-repo:main`, the `workbench-config.yaml` is updated:

```yaml
name: my-workbench
source: my-source
git-branch: my-workbench
repos:
  - dir: service-repo
    source-branch: main
  - dir: new-repo
    source-branch: main
```

A new git worktree is created at `workbench/my-workbench/repo/new-repo/`.

**Output on success:**

```
Workbench "my-workbench" updated: added 1 repo(s)
```

```
Workbench "my-workbench" updated: removed 1 repo(s), added 2 repo(s)
```

**Validation errors:**

| Condition                    | Error message                                                                     |
|------------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder         | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in ROOT or WORKBENCH mode | `The 'workbench update' command can only be run from the project root or a workbench directory.` |
| No options provided          | `At least one --add-repo or --remove-repo option is required.`                    |
| Workbench not found          | `Workbench "name" not found. Available workbenches: ...`                          |
| Name arg in WORKBENCH mode   | `Do not provide a workbench name when running from a workbench directory.`        |
| No name arg in ROOT mode     | `A workbench name is required when running from the project root.`                |
| Repo not found for removal   | `Repo "dir" not found in workbench "name". Available repos: ...`                  |
| Duplicate dir on add         | `Repository directory "dir" already exists in workbench "name".`                  |
| Invalid `--add-repo` format  | `Invalid --add-repo format "value". Expected format: directory-name:branch-name`  |
| Directory doesn't exist      | `Repository directory "name" does not exist in project root: /path`               |
| Not a git repository         | `Directory "name" is not a git repository`                                        |
| Branch doesn't exist         | `Branch "name" does not exist in repository "repo". Available local branches: ...`|
| Dirty worktree on removal    | Git error from `git worktree remove` (no `--force`)                               |

### `bench workbench retire`

Retires a workbench by removing its workspace directory, pruning git worktree references, and marking it as inactive in `base-config.yaml`. The `.bench/workbench/<name>/` directory (containing history, tasks, prompts, etc.) is preserved.

```bash
# Retire a workbench (with confirmation prompt)
bench workbench retire my-workbench

# Retire without confirmation (for scripting)
bench workbench retire my-workbench --yes
bench workbench retire my-workbench -y
```

**Arguments:**

| Argument | Type       | Required | Description                           |
|----------|------------|----------|---------------------------------------|
| `name`   | positional | yes      | Name of the workbench to retire       |

**Options:**

| Option       | Type | Required | Description                    |
|--------------|------|----------|--------------------------------|
| `--yes`/`-y` | flag | no       | Skip the confirmation prompt   |

**Behavior:**

- Only runs in ROOT mode (from the project root directory containing `.bench/base-config.yaml`)
- Validates that the workbench exists in `base-config.yaml` and is currently active
- Validates that the workspace directory (`<project-root>/workbench/<name>`) exists
- Shows a confirmation prompt before proceeding (unless `--yes` is passed):
  `Retire workbench "my-workbench"? This will remove the workspace directory and prune associated worktrees.`
- The `--yes` / `-y` flag bypasses the confirmation prompt
- If the user declines, prints `Retirement cancelled.` and exits with code 0
- Deletes the workspace directory `<project-root>/workbench/<name>` entirely via `shutil.rmtree`
- Runs `git worktree prune` on each repository listed in the workbench's `workbench-config.yaml` to clean up stale worktree administrative references
- Sets the workbench entry's `status` field to `"inactive"` in `base-config.yaml` (the entry is NOT removed)
- Preserves `.bench/workbench/<name>/` completely (all history, tasks, prompts, discussions, files, scripts)
- Tab autocompletion is supported for workbench names (requires shell completion installed via `bench --install-completion`)

**What is deleted:**

| Path | Description |
|------|-------------|
| `workbench/<name>/` | Entire workspace directory (symlinks, repo worktrees) |

**What is preserved:**

| Path | Description |
|------|-------------|
| `.bench/workbench/<name>/` | All workbench metadata, history, tasks, prompts, etc. |

**Config updates:**

After running `bench workbench retire my-workbench`, the workbench entry in `base-config.yaml` is updated:

```yaml
workbenches:
  - name: my-workbench
    source: my-source
    git-branch: my-workbench
    status: inactive
```

**Output on success:**

```
Workbench "my-workbench" retired successfully
  Repos pruned: 2
  Preserved: /path/to/project/.bench/workbench/my-workbench
```

**Validation errors:**

| Condition                    | Error message                                                                     |
|------------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder         | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in project root          | `The 'workbench retire' command can only be run from the project root directory.`  |
| Workbench not in config      | `Workbench "X" not found. Available workbenches: a, b`                            |
| Workbench already inactive   | `Workbench "X" is already inactive.`                                              |
| Workspace dir missing        | `Workbench "X" workspace directory does not exist: <path>. The workbench may already be retired.` |

### `bench workbench activate`

Activates a retired (inactive) workbench by recreating its workspace directory with symlinks, recreating git worktrees for each repository, and setting the workbench status back to `"active"` in `base-config.yaml`. This is the inverse of `bench workbench retire`.

```bash
# Activate a retired workbench
bench workbench activate my-workbench
```

**Arguments:**

| Argument | Type       | Required | Description                           |
|----------|------------|----------|---------------------------------------|
| `name`   | positional | yes      | Name of the workbench to activate     |

**No options.** Activation is a non-destructive operation (only creates directories, symlinks, and worktrees), so no confirmation prompt is needed.

**Behavior:**

- Only runs in ROOT mode (from the project root directory containing `.bench/base-config.yaml`)
- Validates that the workbench exists in `base-config.yaml` and is currently inactive
- Validates that the `.bench/workbench/<name>/` directory exists (this is preserved during retirement and contains `workbench-config.yaml`, history, tasks, etc.)
- Validates that the workspace directory `<project-root>/workbench/<name>` does NOT already exist — if it does, the command errors out (the user must clean up first)
- Loads `workbench-config.yaml` from the preserved bench workbench directory to get the repo list, git branch, and source name
- Recreates the workspace directory with symlinks (identical to what `bench workbench create` produces):
  - `workbench/<name>/AGENTS.md` -> symlink to `.bench/workbench/<name>/AGENTS.md`
  - `workbench/<name>/bench/` -> symlink to `.bench/workbench/<name>/bench/`
  - `workbench/<name>/repo/`
- Recreates git worktrees for each repository in `workbench-config.yaml`:
  - If the git branch already exists locally in the repo, the worktree is created using the existing branch
  - If the git branch does NOT exist (e.g., it was deleted after retirement), a new branch is recreated from the `source-branch` stored in `workbench-config.yaml`
- Sets the workbench entry's `status` field from `"inactive"` back to `"active"` in `base-config.yaml`
- Tab autocompletion only suggests **inactive** workbench names (requires shell completion installed via `bench --install-completion`)

**Relationship to retire:**

| Retire does | Activate undoes |
|---|---|
| Removes `workbench/<name>/` | Recreates `workbench/<name>/` with symlinks |
| Runs `git worktree prune` on each repo | Creates git worktrees for each repo |
| Sets status to `"inactive"` | Sets status to `"active"` |
| Preserves `.bench/workbench/<name>/` | Reads from `.bench/workbench/<name>/` |

**Config updates:**

After running `bench workbench activate my-workbench`, the workbench entry in `base-config.yaml` is updated:

```yaml
workbenches:
  - name: my-workbench
    source: my-source
    git-branch: my-workbench
    status: active
```

**Output on success:**

```
Workbench "my-workbench" activated successfully
  Source: my-source
  Git branch: my-workbench
  Repositories:
    service-repo -> workbench/my-workbench/repo/service-repo
```

**Validation errors:**

| Condition                    | Error message                                                                     |
|------------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder         | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in project root          | `The 'workbench activate' command can only be run from the project root directory.`|
| Workbench not in config      | `Workbench "X" not found. Available workbenches: a, b`                            |
| Workbench already active     | `Workbench "X" is already active.`                                                |
| Bench workbench dir missing  | `Workbench "X" bench directory does not exist: <path>. The workbench data may have been deleted.` |
| Workspace dir already exists | `Workbench "X" workspace directory already exists: <path>. Remove it first before activating.` |

### `bench task create`

Creates a new task within the current workbench. A task is a folder containing metadata and template files for tracking a unit of work (feature, bug fix, refactoring, etc.).

```bash
# Create a task (from a workbench directory)
bench task create add-auth

# Create a task and launch an interactive spec session
bench task create add-auth --interview
```

**Arguments:**

| Argument | Type       | Required | Description                           |
|----------|------------|----------|---------------------------------------|
| `name`   | positional | yes      | Name of the task to create            |

**Options:**

| Option        | Type | Required | Description                                                      |
|---------------|------|----------|------------------------------------------------------------------|
| `--interview` | flag | no       | Launch an interactive opencode session to populate the spec       |

**Behavior:**

- Only runs in WORKBENCH mode (from a workbench workspace directory)
- Task names must be unique within the workbench — uniqueness is checked by matching only the task name portion (after the `YYYYMMDD - ` date prefix) against existing task folders in `bench/tasks/`
- Creates a folder named `YYYYMMDD - <name>` (where YYYYMMDD is today's date) in `<workbench>/bench/tasks/`

**What it creates:**

| Path                                        | Description                                                     |
|---------------------------------------------|-----------------------------------------------------------------|
| `bench/tasks/YYYYMMDD - <name>/`            | Task folder                                                     |
| `bench/tasks/YYYYMMDD - <name>/task.yaml`   | Task metadata: `name` and `completed` (null until completed)    |
| `bench/tasks/YYYYMMDD - <name>/spec.md`     | Spec template with Introduction, Goals, and Specification sections |
| `bench/tasks/YYYYMMDD - <name>/files.md`    | Empty file for listing files relevant to the task               |
| `bench/tasks/YYYYMMDD - <name>/impl.md`     | Empty file for the implementation plan                          |
| `bench/tasks/YYYYMMDD - <name>/notes.md`    | Empty file for miscellaneous notes                              |

**`task.yaml` format:**

```yaml
name: add-auth
completed: null
```

**Output on success:**

```
Task "add-auth" created successfully
  Folder: 20260208 - add-auth

  created 20260208 - add-auth/
  created 20260208 - add-auth/task.yaml
  created 20260208 - add-auth/spec.md
  created 20260208 - add-auth/files.md
  created 20260208 - add-auth/impl.md
  created 20260208 - add-auth/notes.md
```

**`--interview` flag:**

When `--interview` is provided:

1. The task folder and all files are created first
2. The creation summary is displayed
3. The `task-create-spec.md` prompt template is read from `<workbench>/bench/prompts/`
4. The `{{TASK}}` placeholder in the template is substituted with the full task folder name (e.g., `20260208 - add-auth`)
5. opencode is launched **interactively** with the substituted prompt and the `models.task` model from `base-config.yaml`
6. stdin/stdout/stderr are connected directly to the terminal, allowing a back-and-forth conversation with the AI agent

**Validation errors:**

| Condition                  | Error message                                                                     |
|----------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder       | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in workbench directory | `The 'task create' command can only be run from a workbench directory.`            |
| Task name already exists   | `Task "<name>" already exists in this workbench.`                                 |

### `bench task refine`

Refines an existing task's specification through an interactive AI session. Takes a task name, resolves it to the matching `YYYYMMDD - <name>` folder, reads the `task-refine-spec.md` prompt template, and launches opencode interactively.

```bash
# Refine a task's spec (from a workbench directory)
bench task refine add-auth
```

**Arguments:**

| Argument | Type       | Required | Description                           |
|----------|------------|----------|---------------------------------------|
| `name`   | positional | yes      | Name of the task to refine            |

**Behavior:**

- Only runs in WORKBENCH mode (from a workbench workspace directory)
- Resolves the task name to a matching `YYYYMMDD - <name>` folder in `bench/tasks/`
- Validates that `spec.md` exists within the resolved task folder
- Reads the `task-refine-spec.md` prompt template from `<workbench>/bench/prompts/`
- Substitutes the `{{TASK}}` placeholder with the full task folder name (e.g., `20260208 - add-auth`)
- Launches opencode **interactively** with the substituted prompt and the `models.task` model from `base-config.yaml`
- stdin/stdout/stderr are connected directly to the terminal for interactive conversation with the AI agent

**Output before launch:**

```
Refining task "add-auth"
  Folder: 20260208 - add-auth
```

**After the session completes**, if the opencode process exits with a non-zero code, an error message is displayed and bench exits with that code.

**Validation errors:**

| Condition                       | Error message                                                                     |
|---------------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder            | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in workbench directory      | `The 'task refine' command can only be run from a workbench directory.`            |
| Task name not found             | `Task "<name>" not found in this workbench.`                                      |
| Multiple tasks with same name   | `Multiple tasks match "<name>": <folder1>, <folder2>. Please specify the full folder name.` |
| spec.md missing from task folder | `Task "<name>" is missing spec.md.`                                              |
| Prompt template missing         | FileNotFoundError propagates naturally (fail-fast)                                |

### `bench task implement`

Implements a task through sequential AI-assisted phases defined by the workbench's configurable implementation flow. Takes a task name, resolves it to the matching `YYYYMMDD - <name>` folder, and orchestrates headless opencode sessions for each step in the `implementation-flow` from the workbench's `workbench-config.yaml`. Each phase uses `opencode run` (non-interactive, headless agent execution) rather than the interactive TUI, so the agent processes each phase to completion and exits automatically.

The default flow (written by `bench init` and copied into workbenches at creation) consists of 3 steps: plan (write implementation docs), implement (carry out the implementation), and docs (update change documentation). Users can customize this flow by editing `implementation-flow-template` in `base-config.yaml` (for new workbenches) or `implementation-flow` in an individual workbench's `workbench-config.yaml`.

```bash
# Run all configured phases (from a workbench directory)
bench task implement add-auth
```

**Arguments:**

| Argument | Type       | Required | Description                              |
|----------|------------|----------|------------------------------------------|
| `name`   | positional | yes      | Name of the task to implement            |

**No options.** All steps in the configured implementation flow always run sequentially.

**Default implementation flow steps:**

| Step | Name | Prompt Template | Required Inputs | Expected Outputs | Description |
|------|------|-----------------|-----------------|------------------|-------------|
| 1 | Writing implementation docs | `task-write-impl-docs.md` | `spec.md` | `impl.md` | Reads spec and writes implementation documentation |
| 2 | Implementing | `task-do-impl.md` | `spec.md`, `impl.md` | — | Reads spec + impl docs and implements the feature |
| 3 | Updating change docs | `task-update-change-docs.md` | `spec.md`, `impl.md` | — | Uses git diff to update CHANGELOG.md and README.md |

**Behavior:**

- Only runs in WORKBENCH mode (from a workbench workspace directory)
- Resolves the task name to a matching `YYYYMMDD - <name>` folder in `bench/tasks/`
- Reads the `implementation-flow` from the workbench's `workbench-config.yaml`
- Validates that at least one step is configured (errors if empty)
- For each step in the flow:
  1. Pre-flight validation: checks that all `required-files` exist and are non-empty in the task folder
  2. Displays a progress message (e.g., "Phase 1/3: Writing implementation docs...")
  3. Reads the step's `prompt` template from `<workbench>/bench/prompts/`
  4. Substitutes the `{{TASK}}` and `{{REPOSITORIES}}` placeholders
  5. Launches opencode in **headless mode** via `opencode run` with the substituted prompt and the `models.task` model from `base-config.yaml` — the agent processes the message to completion and exits (no interactive TUI)
  6. On completion, displays phase completion status
  7. Inter-phase output validation: checks that all `output-files` were created and are non-empty
- If any phase's opencode session exits non-zero, execution stops immediately with an error reporting which phase failed

**Customizing the implementation flow:**

The flow is stored in two locations:

- **`base-config.yaml` → `implementation-flow-template`**: The project-wide template. New workbenches created with `bench workbench create` receive a copy of this template.
- **`workbench-config.yaml` → `implementation-flow`**: The per-workbench flow. After creation, the workbench's flow is independent and can diverge from the template.

Each step has 4 fields:

```yaml
implementation-flow:
  - name: My Custom Step         # Display name (used in progress output and error messages)
    prompt: my-custom-prompt.md  # Prompt template filename (in bench/prompts/)
    required-files:              # Files that must exist and be non-empty before this step runs
      - spec.md
    output-files:                # Files that must exist and be non-empty after this step completes
      - impl.md
```

**Output during execution:**

```
Implementing task "add-auth"
  Folder: 20260208 - add-auth
  Phases: Writing implementation docs, Implementing, Updating change docs (3 total)

Phase 1/3: Writing implementation docs...

[opencode run — headless agent session]

Phase 1/3 complete: Writing implementation docs

Phase 2/3: Implementing...

[opencode run — headless agent session]

Phase 2/3 complete: Implementing

Phase 3/3: Updating change docs...

[opencode run — headless agent session]

Phase 3/3 complete: Updating change docs

Task "add-auth" implementation complete (3 phases executed)
```

**Validation errors:**

| Condition                              | Error message                                                                     |
|----------------------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder                   | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in workbench directory             | `The 'task implement' command can only be run from a workbench directory.`         |
| No implementation flow configured      | `No implementation flow steps configured for this workbench.`                     |
| Task name not found                    | `Task "<name>" not found in this workbench.`                                      |
| Multiple tasks with same name          | `Multiple tasks match "<name>": <folder1>, <folder2>. Please specify the full folder name.` |
| Required file missing or empty         | `Task "<name>" requires <filename> to be present and non-empty.`                  |
| Output file not created after step     | `Phase '<step name>' completed but <filename> was not created or is empty.`       |
| Prompt template missing                | FileNotFoundError propagates naturally (fail-fast)                                |
| opencode exits non-zero                | `Phase '<step name>' failed: opencode exited with code <code>.`                   |

### `bench task complete`

Marks a task as complete by setting the `completed` field in its `task.yaml` file to the current date. The task's `task.yaml` is loaded and validated via the `TaskConfig` Pydantic model before updating.

```bash
# Mark a task as complete (from a workbench directory)
bench task complete add-auth
```

**Arguments:**

| Argument | Type       | Required | Description                              |
|----------|------------|----------|------------------------------------------|
| `name`   | positional | yes      | Name of the task to mark as complete     |

**Behavior:**

- Only runs in WORKBENCH mode (from a workbench workspace directory)
- Resolves the task name to a matching `YYYYMMDD - <name>` folder in `bench/tasks/`
- Loads `task.yaml` from the task folder and validates it via the `TaskConfig` Pydantic model
- If the task's `completed` field is already set (not null), errors with a message indicating the task is already complete
- Sets the `completed` field to today's date in `YYYY-MM-DD` (ISO 8601) format
- Saves the updated `task.yaml` back to disk

**`task.yaml` after completion:**

```yaml
name: add-auth
completed: '2026-02-09'
```

**Output on success:**

```
Task "add-auth" marked as complete
  Folder: 20260208 - add-auth
  Completed: 2026-02-09
```

**Validation errors:**

| Condition                       | Error message                                                                     |
|---------------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder            | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in workbench directory      | `The 'task complete' command can only be run from a workbench directory.`          |
| Task name not found             | `Task "<name>" not found in this workbench.`                                      |
| Multiple tasks with same name   | `Multiple tasks match "<name>": <folder1>, <folder2>. Please specify the full folder name.` |
| task.yaml missing               | `task.yaml not found in <task_folder_path>`                                       |
| task.yaml malformed             | Pydantic `ValidationError` propagates naturally                                   |
| Task already completed          | `Task "<name>" is already marked as complete (completed: <date>).`                |

### `bench task list`

Lists tasks in the current workbench, displaying useful per-task metadata in a Rich Table. By default, only open (incomplete) tasks are shown.

```bash
# List open tasks (from a workbench directory)
bench task list

# List all tasks (including completed)
bench task list --all

# List only completed tasks
bench task list --completed
```

**Options:**

| Option        | Type | Required | Description                                          |
|---------------|------|----------|------------------------------------------------------|
| `--all`       | flag | no       | Show all tasks (both incomplete and completed)       |
| `--completed` | flag | no       | Show only completed tasks                            |

The `--all` and `--completed` flags are mutually exclusive.

**Behavior:**

- Only runs in WORKBENCH mode (from a workbench workspace directory)
- Scans all subdirectories in `bench/tasks/` matching the `YYYYMMDD - <name>` pattern
- For each matching directory, loads `task.yaml` and checks for `spec.md`, `impl.md`, and `files.md`
- Tasks with missing or malformed `task.yaml` are silently skipped (do not crash the list)
- Tasks are sorted by creation date ascending (oldest first)

**Display columns:**

| Column      | Description                                                        |
|-------------|--------------------------------------------------------------------|
| Name        | Task name (from `task.yaml` or folder name)                        |
| Created     | Date from folder name prefix, formatted as YYYY-MM-DD              |
| Completed   | Completed date from `task.yaml`, or empty if not completed         |
| Spec        | Green "yes" if `spec.md` exists and is non-empty, dim "-" otherwise |
| Impl        | Green "yes" if `impl.md` exists and is non-empty, dim "-" otherwise |
| Files       | Green "yes" if `files.md` exists and is non-empty, dim "-" otherwise |

**Output example:**

```
┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━┓
┃ Name     ┃ Created    ┃ Completed  ┃ Spec ┃ Impl ┃ Files ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━┩
│ add-auth │ 2026-02-08 │            │ yes  │ yes  │ -     │
│ add-api  │ 2026-02-09 │            │ yes  │ -    │ -     │
└──────────┴────────────┴────────────┴──────┴──────┴───────┘
```

**Empty-state messages:**

| Filter        | Message                                  |
|---------------|------------------------------------------|
| (no flags)    | `No open tasks in this workbench.`       |
| `--all`       | `No tasks in this workbench.`            |
| `--completed` | `No completed tasks in this workbench.`  |

**Validation errors:**

| Condition                       | Error message                                                                     |
|---------------------------------|-----------------------------------------------------------------------------------|
| Uninitialized folder            | `This folder is uninitialized. Run 'bench init' to create a bench project first.` |
| Not in workbench directory      | `The 'task list' command can only be run from a workbench directory.`              |
| `--all` and `--completed` both  | `--all and --completed are mutually exclusive.`                                   |

### Seed Prompt Templates

When `bench init` creates the `.bench/` directory, it includes 5 seed prompt templates in `.bench/prompts/`. These are markdown files designed for coding agents working within workbenches. When a workbench is created (`bench workbench create`), these prompts are automatically copied into the workbench's `bench/prompts/` directory.

Prompt templates contain two placeholders that are substituted by task commands (`bench task create --interview`, `bench task refine`, `bench task implement`) before being passed to opencode:

- **`{{TASK}}`** — replaced with the full task folder name (e.g., `20260208 - add-auth`)
- **`{{REPOSITORIES}}`** — replaced with a `<repositories>` block listing all repo directories from the workbench's `workbench-config.yaml`, using `./repo/<dir>` paths (one per line)

| Prompt File | Purpose |
|---|---|
| `task-create-spec.md` | Interactive spec creation — agent asks the user questions to build a specification document in `spec.md` |
| `task-refine-spec.md` | Spec refinement — agent reviews an existing spec for completeness and asks clarifying questions |
| `task-write-impl-docs.md` | Implementation planning — agent reads the spec and produces `impl.md` (implementation plan), `notes.md`, and `files.md` (affected files list) |
| `task-do-impl.md` | Implementation execution — agent reads spec + implementation docs and implements the feature |
| `task-update-change-docs.md` | Change documentation — agent discovers changes via `git diff` and updates `CHANGELOG.md` and `README.md` |

All prompt paths are relative to the workbench directory (e.g., `./bench/tasks/{{TASK}}/spec.md`).

**Rendered `{{REPOSITORIES}}` example** (for a workbench with `service-repo` and `client-repo`):

```
<repositories>
./repo/service-repo
./repo/client-repo
</repositories>
```

If the workbench has no repos, the block renders as an empty tag: `<repositories>\n</repositories>`.

### AI Model Configuration

The `base-config.yaml` file includes a `models` section that configures which AI models coding agents should use for various tasks within workbenches. This section is written explicitly when `bench init` creates a new project.

```yaml
sources: []
models:
  task: anthropic/claude-opus-4-6
```

| Field | Type | Default | Description |
|---|---|---|---|
| `models.task` | `str` | `anthropic/claude-opus-4-6` | AI model identifier for task execution |

**Behavior:**

- `bench init` writes the `models` section with default values into `base-config.yaml`
- `bench status` displays the configured task model as a "Task Model" row when `base_config` is available (ROOT, WORKBENCH, and WITHIN_ROOT modes)
- Existing `base-config.yaml` files without a `models` key load correctly — Pydantic applies the default `Models()` with `task="anthropic/claude-opus-4-6"`
- The `Models` sub-model lives only in `BaseConfig` (project root config); workbenches inherit it from their project root and do not override it
- The `Models` model is designed to be extensible — future keys (e.g., `planning`, `code_review`, `chat`) can be added as new fields with defaults

## Internal APIs

### OpenCode Interface

Bench includes an internal opencode interface for invoking the `opencode` coding agent CLI. It provides three modes of execution:

| Service Function                        | Description                                              |
|-----------------------------------------|----------------------------------------------------------|
| `run_opencode_prompt(prompt, model, cwd)` | Execute opencode with captured output, returning an `OpenCodeResult` with stdout, stderr, and return_code |
| `run_task_interview(task_folder_name)` | Read prompt template, substitute `{{TASK}}` and `{{REPOSITORIES}}`, and launch opencode interactively (used by `bench task create --interview`) |
| `resolve_task(task_name)` | Resolve a task name to its folder, validate spec.md exists, return metadata dict (used by `bench task refine`) |
| `refine_task(task_folder_name)` | Read `task-refine-spec.md` prompt template, substitute `{{TASK}}` and `{{REPOSITORIES}}`, and launch opencode interactively (used by `bench task refine`) |
| `complete_task(task_name)` | Load task.yaml, validate via TaskConfig, set completed date to today, save back to disk (used by `bench task complete`) |
| `list_tasks(task_filter)` | Enforce WORKBENCH mode, scan task entries from repository, convert to TaskEntry models, filter by open/completed/all, sort by created_date ascending (used by `bench task list`) |
| `resolve_task_for_implement(task_name)` | Resolve a task name to its folder without per-file validation, return metadata dict with task_folder_path (used by `bench task implement`) |
| `select_implement_phases(run_plan, run_implement, run_docs)` | Select which implementation phases to execute based on flags; returns all phases if no flags set |
| `validate_task_phase(task_folder_path, phase, task_name)` | Validate that all required input files exist and are non-empty for a phase |
| `run_task_phase(task_folder_name, phase)` | Read a phase's prompt template, substitute `{{TASK}}` and `{{REPOSITORIES}}`, and launch opencode in headless mode via `opencode run` (used by `bench task implement`) |
| `validate_task_phase_outputs(task_folder_path, phase)` | Validate that expected output files were created after a phase completes |

| Repository Function                          | Description                                              |
|----------------------------------------------|----------------------------------------------------------|
| `run_prompt(prompt, model, cwd)`             | Captured-output execution — returns `OpenCodeResult`     |
| `run_prompt_interactive(prompt, model, cwd)` | Terminal pass-through execution — stdin/stdout/stderr connected to terminal for interactive AI agent conversation; returns exit code |
| `run_command(message, model, cwd)`           | Headless execution via `opencode run` — non-interactive agent that processes the message to completion and exits; stdout/stderr passed through to terminal for real-time progress; returns exit code |
| `task_file_exists_and_nonempty(task_folder, filename)` | Check whether a file in a task folder exists and has non-zero length |
| `load_task_yaml(task_folder)` | Load and return `task.yaml` from a task folder as a dict |
| `save_task_yaml(task_folder, data)` | Write task data dict to `task.yaml` in a task folder |
| `list_task_entries(tasks_dir)` | Scan the tasks directory and return raw task entry data (name, folder, created date, completed, file existence flags); skips entries with missing/malformed task.yaml |
| `render_repositories_block(repo_dirs)` | Render a `<repositories>` block from a list of repo directory names with `./repo/<dir>` paths |
| `remove_workbench_workspace(workspace_path)` | Remove a workbench workspace directory tree via `shutil.rmtree`; raises `FileNotFoundError` if directory doesn't exist |

The caller is responsible for:
- Reading prompt files from `bench/prompts/`
- Rendering prompt templates (substituting variables like `{{TASK}}` and `{{REPOSITORIES}}`)
- Providing the model identifier string (e.g., `anthropic/claude-opus-4-6`)
- Providing the working directory path

**Execution details:**
- All three modes use `subprocess.run` with `timeout=None` (coding agent runs can take minutes or hours)
- Prompt/message text is passed as a list argument (no `shell=True`) — no shell injection risk
- Catches `FileNotFoundError` and raises `RuntimeError` with "opencode is not installed" message
- Captured mode (`run_prompt`): non-zero return codes raise `RuntimeError` with command, return code, and stderr details
- Interactive mode (`run_prompt_interactive`): does NOT raise on non-zero exit (the user may ctrl-C the interview); returns the exit code directly
- Headless mode (`run_command`): invokes `opencode run --model <model> <message>` — the agent runs to completion without a TUI; does NOT raise on non-zero exit; returns the exit code directly; used by `bench task implement` phases

#### OpenCode Data Model

- **`OpenCodeResult`** — Result of an opencode CLI execution with `stdout` (str), `stderr` (str), and `return_code` (int)
- **`TaskConfig`** — Schema for a task's `task.yaml` metadata file with `name` (str) and `completed` (str | None, default None)
- **`TaskFilter`** — String enum with `OPEN`, `COMPLETED`, and `ALL` values for filtering task listings
- **`TaskEntry`** — Enriched task entry for list display with `name` (str), `folder_name` (str), `created_date` (datetime.date), `completed` (str | None), `has_spec` (bool), `has_impl` (bool), `has_files` (bool)

### Git Interface

Bench includes an internal git interface used by other features (not exposed as CLI commands). It provides three operations via the service layer:

| Service Function       | Description                                              |
|------------------------|----------------------------------------------------------|
| `get_git_status(path)` | Parse `git status --porcelain=v2 --branch` into a structured `GitStatus` model containing branch name, file changes (staged/unstaged), and untracked files |
| `create_git_branch(name, path)` | Create a new branch without checking it out     |
| `push_git_branch(name, path)`   | Push a branch to origin with smart upstream tracking (`-u` on first push) |

All git operations use the `git` CLI via `subprocess.run` (no Python git libraries). Errors are wrapped in `RuntimeError` with descriptive messages including git stderr output.

#### Git Data Models

- **`FileStatus`** — String enum: `MODIFIED`, `ADDED`, `DELETED`, `RENAMED`, `COPIED`, `UNTRACKED`, `TYPE_CHANGED`, `UNMERGED`
- **`GitFileChange`** — A single file change entry with `path`, `status`, and `staged` flag
- **`GitStatus`** — Parsed git status with `branch` (None if detached HEAD), `files` (list of `GitFileChange`), and `untracked` (list of paths)

#### Git Repository Utilities

| Repository Function              | Description                                                    |
|----------------------------------|----------------------------------------------------------------|
| `is_git_repository(path)`        | Check if a directory is a git repo or worktree                 |
| `list_local_branches(repo_path)` | List all local branch names in a repository                    |
| `branch_exists(branch_name, repo_path)` | Check if a local branch exists in a repository           |
| `add_worktree(repo_path, worktree_path, branch_name, ...)` | Add a git worktree with optional branch creation |
| `remove_worktree(repo_path, worktree_path)` | Remove a git worktree (no `--force`; fails on dirty worktrees) |
| `prune_worktrees(repo_path)` | Prune stale worktree references (`git worktree prune`) for worktrees whose directories have been removed |

These utility functions are used by the `source add`, `workbench create`, `workbench update`, and `workbench retire` logic but are available for general use.

## Development

### Project Structure

```
src/bench/
  __init__.py              # Package root
  cli/
    __init__.py            # Typer app entry point, command registration
    init.py                # "init" command (thin handler: service -> view)
    status.py              # "status" command (thin handler: service -> view)
    source.py              # "source" subcommand group (source add, source list, source update, source remove)
    task.py                # "task" subcommand group (task create, task complete, task list, task refine, task implement)
    workbench.py           # "workbench" subcommand group (workbench create, workbench update, workbench retire)
  model/
    __init__.py            # Re-exports all public model classes
    mode.py                # BenchMode enum (ROOT, WORKBENCH, WITHIN_ROOT, UNINITIALIZED)
    config.py              # Pydantic schemas: BaseConfig (with sources, workbenches, models), Models, WorkbenchConfig (with source, git-branch, repos)
    context.py             # BenchContext runtime state model
    git.py                 # Git data models: FileStatus, GitFileChange, GitStatus
    opencode.py            # OpenCode data models: OpenCodeResult
    source.py              # Source data models: Source, SourceRepo
    task.py                # Task data models: TaskConfig, TaskEntry, TaskFilter
    workbench.py           # Workbench data models: WorkbenchEntry, WorkbenchStatus
  service/
    __init__.py            # Re-exports public service functions
    init.py                # Init business logic (initialize_project)
    mode_detection.py      # Mode detection logic (detect_mode)
    git.py                 # Git service facades (get_git_status, create_git_branch, push_git_branch)
    opencode.py            # OpenCode service facade (run_opencode_prompt)
    source.py              # Source business logic (add_source, list_sources, update_source, remove_source)
    task.py                # Task business logic (create_task, complete_task, list_tasks, run_task_interview, resolve_task, refine_task, resolve_task_for_implement, select_implement_phases, validate_task_phase, run_task_phase, validate_task_phase_outputs, _substitute_prompt_placeholders)
    _validation.py         # Shared validation helpers (parse_repo_arg, validate_repo) — private to service package
    workbench.py           # Workbench business logic (create_workbench, update_workbench, retire_workbench)
  repository/
    __init__.py            # Re-exports public repository functions
    filesystem.py          # Filesystem I/O (find_bench_root, find_workbench_marker, load_yaml_file, save_yaml_file, create_bench_scaffold, create_workbench_scaffold, create_workbench_workspace, remove_workbench_workspace, create_task_scaffold, list_task_names, list_task_entries, read_prompt_file, find_task_folder, task_spec_exists, task_file_exists_and_nonempty, load_task_yaml, save_task_yaml, render_repositories_block)
    git.py                 # Raw git subprocess operations (git_status, create_branch, push_branch, is_git_repository, list_local_branches, branch_exists, add_worktree, remove_worktree, prune_worktrees)
    opencode.py            # Raw opencode subprocess operations (run_prompt, run_prompt_interactive, run_command, OPENCODE_EXECUTABLE)
  view/
    __init__.py            # Re-exports public view functions
    init.py                # Rich terminal output for init display (display_init_success, display_init_error)
    status.py              # Rich terminal output for status display
    source.py              # Rich terminal output for source operations (display_source_added, display_source_error, display_source_list, display_source_removed, display_source_updated)
    task.py                # Rich terminal output for task operations (display_task_created, display_task_completed, display_task_list, display_task_error, display_task_refine_start, display_task_implement_start, display_task_implement_phase_start, display_task_implement_phase_complete, display_task_implement_complete)
    workbench.py           # Rich terminal output for workbench operations (display_workbench_created, display_workbench_error, display_workbench_retired, display_workbench_updated)
```

### Architecture

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
                    |   model   |   Shared data structures
                    +-----------+
```

- **cli** depends on service and view (never the reverse)
- **service** depends on repository (never the reverse)
- **repository** performs raw I/O (filesystem, git subprocess)
- **view** depends only on model
- **model** is depended on by all layers; depends on nothing

### Dependencies

**Runtime:**

| Package  | Purpose                              |
|----------|--------------------------------------|
| typer    | CLI framework                        |
| rich     | Rich terminal output for view layer  |
| pyyaml   | YAML parsing for config/data files   |
| pydantic | Data validation and model definitions|

**Dev:**

| Package      | Version | Purpose            |
|--------------|---------|--------------------|
| ruff         | 0.15.0  | Linting/formatting |
| ty           | 0.0.15  | Type checking      |

### Quality Checks

```bash
make check
```

This runs:
1. `ruff check --show-fixes --fix src/` — linting
2. `ruff format src/` — formatting
3. `ty check src/` — type checking

### Entry Point

The CLI entry point is defined in `pyproject.toml` as `bench = 'bench.cli:app'`, pointing to the Typer application instance in `src/bench/cli/__init__.py`.

## License

Not yet specified.
