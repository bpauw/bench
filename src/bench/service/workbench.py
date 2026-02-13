from pathlib import Path

from bench.model import BenchMode, WorkbenchEntry
from bench.model.source import SourceRepo
from bench.repository import (
    BASE_CONFIG_FILENAME,
    add_worktree,
    branch_exists,
    create_workbench_scaffold,
    create_workbench_workspace,
    delete_branch,
    load_yaml_file,
    prune_worktrees,
    remove_workbench_scaffold,
    remove_workbench_workspace,
    remove_worktree,
    save_yaml_file,
)
from bench.service._validation import parse_repo_arg, validate_repo
from bench.service.mode_detection import detect_mode


def create_workbench(
    source_name: str,
    workbench_name: str,
    workbench_git_branch: str | None = None,
) -> dict[str, object]:
    """Create a new workbench from a source definition.

    Args:
        source_name: Name of the source to use.
        workbench_name: Name of the new workbench.
        workbench_git_branch: Optional custom git branch name (defaults to workbench_name).

    Returns:
        A dict with summary info for the view layer:
        {
            "name": str,
            "source": str,
            "git_branch": str,
            "repos": list[dict[str, str]],  # each: {"dir": ..., "worktree_path": ...}
        }

    Raises:
        ValueError: If mode is not ROOT, source not found, workbench already exists, etc.
        RuntimeError: If git worktree creation fails.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())
    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. "
            "Run 'bench init' to create a bench project first."
        )
    if context.mode != BenchMode.ROOT:
        raise ValueError(
            "The 'workbench create' command can only be run from the "
            "project root directory."
        )
    assert context.root_path is not None
    assert context.bench_dir_name is not None
    assert context.base_config is not None

    # Phase 2: Resolve git branch
    git_branch = workbench_git_branch or workbench_name

    # Phase 3: Load config & find source
    config_path = context.root_path / context.bench_dir_name / BASE_CONFIG_FILENAME
    data = load_yaml_file(config_path)

    source = None
    for s in context.base_config.sources:
        if s.name == source_name:
            source = s
            break

    if source is None:
        available = ", ".join(s.name for s in context.base_config.sources) or "(none)"
        raise ValueError(
            f'Source "{source_name}" not found. Available sources: {available}'
        )

    if not source.repos:
        raise ValueError(
            f'Source "{source_name}" has no repositories defined. Add repos first.'
        )

    # Phase 4: Validate workbench name uniqueness
    existing_wb_names = [
        w.get("name") for w in data.get("workbenches", []) if isinstance(w, dict)
    ]
    if workbench_name in existing_wb_names:
        raise ValueError(
            f'Workbench "{workbench_name}" already exists in configuration.'
        )

    wb_dir = context.root_path / "workbench" / workbench_name
    if wb_dir.exists():
        raise ValueError(f"Workbench directory already exists: {wb_dir}")

    bench_wb_dir = (
        context.root_path / context.bench_dir_name / "workbench" / workbench_name
    )
    if bench_wb_dir.exists():
        raise ValueError(f"Workbench directory already exists: {bench_wb_dir}")

    # Phase 5: Validate git branches
    repo_branch_info: list[tuple[SourceRepo, bool]] = []
    for repo in source.repos:
        repo_path = context.root_path / repo.dir
        exists = branch_exists(git_branch, repo_path)
        repo_branch_info.append((repo, not exists))

    # Phase 6: Build workbench-config.yaml data
    workbench_config_data: dict[str, object] = {
        "name": workbench_name,
        "source": source_name,
        "git-branch": git_branch,
        "repos": [
            {"dir": repo.dir, "source-branch": repo.source_branch}
            for repo in source.repos
        ],
        "implementation-flow": [
            {
                "name": step.name,
                "prompt": step.prompt,
                "required-files": step.required_files,
                "output-files": step.output_files,
            }
            for step in context.base_config.implementation_flow_template
        ],
    }

    # Phase 7: Create scaffold in .bench/
    create_workbench_scaffold(
        context.root_path,
        context.bench_dir_name,
        workbench_name,
        workbench_config_data,
    )

    # Phase 8: Create workspace with symlinks
    create_workbench_workspace(
        context.root_path,
        context.bench_dir_name,
        workbench_name,
    )

    # Phase 9: Create worktrees
    repo_summaries: list[dict[str, str]] = []
    for repo, needs_creation in repo_branch_info:
        repo_path = context.root_path / repo.dir
        worktree_path = (
            context.root_path / "workbench" / workbench_name / "repo" / repo.dir
        )

        if needs_creation:
            add_worktree(
                repo_path=repo_path,
                worktree_path=worktree_path,
                branch_name=git_branch,
                start_point=repo.source_branch,
                create_branch=True,
            )
        else:
            add_worktree(
                repo_path=repo_path,
                worktree_path=worktree_path,
                branch_name=git_branch,
            )

        repo_summaries.append(
            {
                "dir": repo.dir,
                "worktree_path": str(worktree_path.relative_to(context.root_path)),
            }
        )

    # Phase 10: Update base-config.yaml
    if "workbenches" not in data:
        data["workbenches"] = []

    data["workbenches"].append(
        {
            "name": workbench_name,
            "source": source_name,
            "git-branch": git_branch,
            "status": "active",
        }
    )

    save_yaml_file(config_path, data)

    return {
        "name": workbench_name,
        "source": source_name,
        "git_branch": git_branch,
        "repos": repo_summaries,
    }


def update_workbench(
    workbench_name: str,
    add_repo_args: list[str],
    remove_repo_args: list[str],
) -> str:
    """Update an existing workbench by adding or removing repositories.

    Removals are applied before additions, allowing a repo to be removed
    and re-added with a different branch in a single invocation.

    Args:
        workbench_name: Name of the workbench to update.
        add_repo_args: List of raw --add-repo values in 'dir:branch' format.
        remove_repo_args: List of directory names to remove.

    Returns:
        A success message string summarising the changes.

    Raises:
        ValueError: If mode is invalid, workbench not found, validation fails,
            or no operations are specified.
        RuntimeError: If git worktree operations fail.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())
    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. "
            "Run 'bench init' to create a bench project first."
        )
    if context.mode not in (BenchMode.ROOT, BenchMode.WORKBENCH):
        raise ValueError(
            "The 'workbench update' command can only be run from the "
            "project root or a workbench directory."
        )

    # Phase 2: Require at least one operation
    if not add_repo_args and not remove_repo_args:
        raise ValueError("At least one --add-repo or --remove-repo option is required.")

    assert context.root_path is not None
    assert context.bench_dir_name is not None

    # Phase 3: Parse --add-repo arguments
    parsed_adds: list[tuple[str, str]] = []
    for arg in add_repo_args:
        dir_name, branch_name = parse_repo_arg(arg)
        parsed_adds.append((dir_name, branch_name))

    # Phase 4: Verify workbench exists in base-config.yaml
    config_path = context.root_path / context.bench_dir_name / BASE_CONFIG_FILENAME
    data = load_yaml_file(config_path)

    workbench_entry: dict[str, object] | None = None
    for w in data.get("workbenches", []):
        if isinstance(w, dict) and w.get("name") == workbench_name:
            workbench_entry = w
            break

    if workbench_entry is None:
        existing_names = [
            w["name"]
            for w in data.get("workbenches", [])
            if isinstance(w, dict) and "name" in w
        ]
        available = ", ".join(existing_names) if existing_names else "(none)"
        raise ValueError(
            f'Workbench "{workbench_name}" not found. '
            f"Available workbenches: {available}"
        )

    # Phase 5: Check status — must be active
    if workbench_entry.get("status") == "inactive":
        raise ValueError(
            f'Workbench "{workbench_name}" is inactive. '
            f"Activate it first with `bench workbench activate`."
        )

    # Phase 6: Load workbench-config.yaml
    wb_config_path = (
        context.root_path
        / context.bench_dir_name
        / "workbench"
        / workbench_name
        / "bench"
        / "workbench-config.yaml"
    )
    wb_data = load_yaml_file(wb_config_path)

    git_branch: str = wb_data.get("git-branch", workbench_name)
    repos_list: list[dict[str, str]] = wb_data.get("repos", [])

    # Phase 7: Validate removals (all-or-nothing)
    existing_repo_dirs = {r.get("dir") for r in repos_list}
    for dir_name in remove_repo_args:
        if dir_name not in existing_repo_dirs:
            available = (
                ", ".join(sorted(existing_repo_dirs))
                if existing_repo_dirs
                else "(none)"
            )
            raise ValueError(
                f'Repo "{dir_name}" not found in workbench "{workbench_name}". '
                f"Available repos: {available}"
            )

    # Phase 8: Apply removals to in-memory repos list
    remove_set = set(remove_repo_args)
    remaining_repos = [r for r in repos_list if r.get("dir") not in remove_set]

    # Phase 9: Validate additions (against remaining repos)
    remaining_dirs = {r.get("dir") for r in remaining_repos}
    for dir_name, branch_name in parsed_adds:
        if dir_name in remaining_dirs:
            raise ValueError(
                f'Repository directory "{dir_name}" already exists '
                f'in workbench "{workbench_name}".'
            )
        validate_repo(dir_name, branch_name, context.root_path)
        remaining_dirs.add(dir_name)  # prevent duplicates within the add list

    # Phase 10: Check git branch existence for additions
    add_info: list[tuple[str, str, bool]] = []  # (dir, source_branch, needs_creation)
    for dir_name, source_branch in parsed_adds:
        repo_path = context.root_path / dir_name
        exists = branch_exists(git_branch, repo_path)
        add_info.append((dir_name, source_branch, not exists))

    # Phase 11: Execute removals — remove git worktrees
    for dir_name in remove_repo_args:
        worktree_path = (
            context.root_path / "workbench" / workbench_name / "repo" / dir_name
        )
        repo_path = context.root_path / dir_name
        remove_worktree(repo_path, worktree_path)

    # Phase 12: Execute additions — create git worktrees
    for dir_name, source_branch, needs_creation in add_info:
        repo_path = context.root_path / dir_name
        worktree_path = (
            context.root_path / "workbench" / workbench_name / "repo" / dir_name
        )
        if needs_creation:
            add_worktree(
                repo_path=repo_path,
                worktree_path=worktree_path,
                branch_name=git_branch,
                start_point=source_branch,
                create_branch=True,
            )
        else:
            add_worktree(
                repo_path=repo_path,
                worktree_path=worktree_path,
                branch_name=git_branch,
            )

    # Phase 13: Update workbench-config.yaml
    # Apply removals
    updated_repos = [r for r in repos_list if r.get("dir") not in remove_set]
    # Apply additions
    for dir_name, source_branch, _ in add_info:
        updated_repos.append({"dir": dir_name, "source-branch": source_branch})

    wb_data["repos"] = updated_repos
    save_yaml_file(wb_config_path, wb_data)

    # Phase 14: Return summary message
    removed_count = len(remove_repo_args)
    added_count = len(parsed_adds)
    parts: list[str] = []
    if removed_count:
        parts.append(f"removed {removed_count} repo(s)")
    if added_count:
        parts.append(f"added {added_count} repo(s)")

    return f'Workbench "{workbench_name}" updated: {", ".join(parts)}'


def retire_workbench(workbench_name: str) -> dict[str, object]:
    """Retire a workbench by removing its workspace and pruning worktrees.

    Removes the workspace directory (<project-root>/workbench/<name>),
    prunes git worktree references for each repo, and marks the workbench
    entry as inactive in base-config.yaml. The .bench/workbench/<name>/
    directory is preserved.

    Args:
        workbench_name: Name of the workbench to retire.

    Returns:
        A dict with summary info for the view layer:
        {
            "name": str,
            "repos_pruned": int,
            "bench_dir_preserved": str,  # path to .bench/workbench/<name>/
        }

    Raises:
        ValueError: If mode is not ROOT, workbench not found, already inactive,
            or workspace directory missing.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())
    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. "
            "Run 'bench init' to create a bench project first."
        )
    if context.mode != BenchMode.ROOT:
        raise ValueError(
            "The 'workbench retire' command can only be run from the "
            "project root directory."
        )

    # Phase 2: Assert context fields
    assert context.root_path is not None
    assert context.bench_dir_name is not None
    assert context.base_config is not None

    # Phase 3: Load base-config.yaml (raw dict for mutation)
    config_path = context.root_path / context.bench_dir_name / BASE_CONFIG_FILENAME
    data = load_yaml_file(config_path)

    # Phase 4: Find workbench entry
    workbench_entry: dict[str, object] | None = None
    for w in data.get("workbenches", []):
        if isinstance(w, dict) and w.get("name") == workbench_name:
            workbench_entry = w
            break

    if workbench_entry is None:
        existing_names = [
            w["name"]
            for w in data.get("workbenches", [])
            if isinstance(w, dict) and "name" in w
        ]
        available = ", ".join(existing_names) if existing_names else "(none)"
        raise ValueError(
            f'Workbench "{workbench_name}" not found. '
            f"Available workbenches: {available}"
        )

    # Phase 5: Check status
    if workbench_entry.get("status") == "inactive":
        raise ValueError(f'Workbench "{workbench_name}" is already inactive.')

    # Phase 6: Validate workspace directory exists
    workspace_path = context.root_path / "workbench" / workbench_name
    if not workspace_path.is_dir():
        raise ValueError(
            f'Workbench "{workbench_name}" workspace directory does not exist: '
            f"{workspace_path}. The workbench may already be retired."
        )

    # Phase 7: Load workbench-config.yaml for repo list
    wb_config_path = (
        context.root_path
        / context.bench_dir_name
        / "workbench"
        / workbench_name
        / "bench"
        / "workbench-config.yaml"
    )
    wb_data = load_yaml_file(wb_config_path)
    repos_list: list[dict[str, str]] = wb_data.get("repos", [])

    # Phase 8: Remove workspace directory
    remove_workbench_workspace(workspace_path)

    # Phase 9: Prune worktrees for each repo
    repos_pruned = 0
    for repo in repos_list:
        repo_dir = repo.get("dir")
        if repo_dir:
            repo_path = context.root_path / repo_dir
            if repo_path.is_dir():
                prune_worktrees(repo_path)
                repos_pruned += 1

    # Phase 10: Update base-config.yaml — set status to inactive
    workbench_entry["status"] = "inactive"
    save_yaml_file(config_path, data)

    # Phase 11: Return summary
    bench_dir_preserved = str(
        context.root_path / context.bench_dir_name / "workbench" / workbench_name
    )
    return {
        "name": workbench_name,
        "repos_pruned": repos_pruned,
        "bench_dir_preserved": bench_dir_preserved,
    }


def delete_workbench(workbench_name: str) -> dict[str, object]:
    """Permanently delete a workbench and all its data.

    Removes the workspace directory (if active), scaffold data, git branches,
    and the config entry from base-config.yaml. Works on both active and
    inactive workbenches.

    Args:
        workbench_name: Name of the workbench to delete.

    Returns:
        A dict with summary info for the view layer:
        {
            "name": str,
            "was_active": bool,
            "workspace_removed": str | None,
            "scaffold_removed": str,
            "branches_deleted": list[str],
        }

    Raises:
        RuntimeError: If mode is not ROOT or context fields missing.
        ValueError: If workbench not found in config.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())
    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. "
            "Run 'bench init' to create a bench project first."
        )
    if context.mode != BenchMode.ROOT:
        raise RuntimeError(
            "The 'workbench delete' command can only be run from the "
            "project root directory."
        )

    # Phase 2: Assert context fields
    assert context.root_path is not None
    assert context.bench_dir_name is not None
    assert context.base_config is not None

    # Phase 3: Load base-config.yaml (raw dict for mutation)
    config_path = context.root_path / context.bench_dir_name / BASE_CONFIG_FILENAME
    data = load_yaml_file(config_path)

    # Phase 4: Find workbench entry
    workbench_index: int | None = None
    workbench_entry: dict[str, object] | None = None
    for i, w in enumerate(data.get("workbenches", [])):
        if isinstance(w, dict) and w.get("name") == workbench_name:
            workbench_index = i
            workbench_entry = w
            break

    if workbench_entry is None or workbench_index is None:
        existing_names = [
            w["name"]
            for w in data.get("workbenches", [])
            if isinstance(w, dict) and "name" in w
        ]
        available = ", ".join(existing_names) if existing_names else "(none)"
        raise ValueError(
            f'Workbench "{workbench_name}" not found. '
            f"Available workbenches: {available}"
        )

    was_active = workbench_entry.get("status") == "active"

    # Phase 5: Load workbench-config.yaml
    wb_config_path = (
        context.root_path
        / context.bench_dir_name
        / "workbench"
        / workbench_name
        / "bench"
        / "workbench-config.yaml"
    )
    wb_data = load_yaml_file(wb_config_path)
    git_branch: str = wb_data.get("git-branch", workbench_name)
    repos_list: list[dict[str, str]] = wb_data.get("repos", [])

    # Phase 6: If ACTIVE, perform retire steps (remove workspace + prune worktrees)
    workspace_removed: str | None = None
    if was_active:
        workspace_path = context.root_path / "workbench" / workbench_name
        if workspace_path.is_dir():
            remove_workbench_workspace(workspace_path)
            workspace_removed = str(workspace_path)
        for repo in repos_list:
            repo_dir = repo.get("dir")
            if repo_dir:
                repo_path = context.root_path / repo_dir
                if repo_path.is_dir():
                    prune_worktrees(repo_path)

    # Phase 7: Delete git branches
    branches_deleted: list[str] = []
    for repo in repos_list:
        repo_dir = repo.get("dir")
        if not repo_dir:
            continue
        repo_path = context.root_path / repo_dir
        if not repo_path.is_dir():
            continue
        if branch_exists(git_branch, repo_path):
            delete_branch(git_branch, repo_path)
            branches_deleted.append(repo_dir)

    # Phase 8: Remove scaffold directory
    scaffold_path = (
        context.root_path / context.bench_dir_name / "workbench" / workbench_name
    )
    remove_workbench_scaffold(scaffold_path)

    # Phase 9: Remove entry from base-config.yaml
    del data["workbenches"][workbench_index]
    save_yaml_file(config_path, data)

    # Phase 10: Return summary
    return {
        "name": workbench_name,
        "was_active": was_active,
        "workspace_removed": workspace_removed,
        "scaffold_removed": str(scaffold_path),
        "branches_deleted": branches_deleted,
    }


def activate_workbench(workbench_name: str) -> dict[str, object]:
    """Activate a retired workbench by recreating its workspace and worktrees.

    Recreates the workspace directory (<project-root>/workbench/<name>) with
    symlinks, creates git worktrees for each repo, and marks the workbench
    entry as active in base-config.yaml.

    Args:
        workbench_name: Name of the workbench to activate.

    Returns:
        A dict with summary info for the view layer:
        {
            "name": str,
            "source": str,
            "git_branch": str,
            "repos": list[dict[str, str]],  # each: {"dir": ..., "worktree_path": ...}
        }

    Raises:
        ValueError: If mode is not ROOT, workbench not found, already active,
            bench dir missing, or workspace already exists.
        RuntimeError: If git worktree creation fails.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())
    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. "
            "Run 'bench init' to create a bench project first."
        )
    if context.mode != BenchMode.ROOT:
        raise ValueError(
            "The 'workbench activate' command can only be run from the "
            "project root directory."
        )

    # Phase 2: Assert context fields
    assert context.root_path is not None
    assert context.bench_dir_name is not None
    assert context.base_config is not None

    # Phase 3: Load base-config.yaml (raw dict for mutation)
    config_path = context.root_path / context.bench_dir_name / BASE_CONFIG_FILENAME
    data = load_yaml_file(config_path)

    # Phase 4: Find workbench entry
    workbench_entry: dict[str, object] | None = None
    for w in data.get("workbenches", []):
        if isinstance(w, dict) and w.get("name") == workbench_name:
            workbench_entry = w
            break

    if workbench_entry is None:
        existing_names = [
            w["name"]
            for w in data.get("workbenches", [])
            if isinstance(w, dict) and "name" in w
        ]
        available = ", ".join(existing_names) if existing_names else "(none)"
        raise ValueError(
            f'Workbench "{workbench_name}" not found. '
            f"Available workbenches: {available}"
        )

    # Phase 5: Check status — must be inactive
    if workbench_entry.get("status") != "inactive":
        raise ValueError(f'Workbench "{workbench_name}" is already active.')

    # Phase 6: Validate bench workbench dir exists
    bench_wb_dir = (
        context.root_path / context.bench_dir_name / "workbench" / workbench_name
    )
    if not bench_wb_dir.is_dir():
        raise ValueError(
            f'Workbench "{workbench_name}" bench directory does not exist: '
            f"{bench_wb_dir}. The workbench data may have been deleted."
        )

    # Phase 7: Validate workspace directory does NOT exist
    workspace_path = context.root_path / "workbench" / workbench_name
    if workspace_path.exists():
        raise ValueError(
            f'Workbench "{workbench_name}" workspace directory already exists: '
            f"{workspace_path}. Remove it first before activating."
        )

    # Phase 8: Load workbench-config.yaml
    wb_config_path = (
        context.root_path
        / context.bench_dir_name
        / "workbench"
        / workbench_name
        / "bench"
        / "workbench-config.yaml"
    )
    wb_data = load_yaml_file(wb_config_path)
    git_branch: str = wb_data.get("git-branch", workbench_name)
    source_name: str = wb_data.get("source", "")
    repos_list: list[dict[str, str]] = wb_data.get("repos", [])

    # Phase 9: Recreate workspace directory with symlinks
    create_workbench_workspace(
        context.root_path,
        context.bench_dir_name,
        workbench_name,
    )

    # Phase 10: Recreate worktrees
    repo_summaries: list[dict[str, str]] = []
    for repo in repos_list:
        repo_dir = repo.get("dir")
        source_branch = repo.get("source-branch")
        if not repo_dir:
            continue

        repo_path = context.root_path / repo_dir
        worktree_path = (
            context.root_path / "workbench" / workbench_name / "repo" / repo_dir
        )

        if branch_exists(git_branch, repo_path):
            add_worktree(
                repo_path=repo_path,
                worktree_path=worktree_path,
                branch_name=git_branch,
            )
        else:
            add_worktree(
                repo_path=repo_path,
                worktree_path=worktree_path,
                branch_name=git_branch,
                start_point=source_branch,
                create_branch=True,
            )

        repo_summaries.append(
            {
                "dir": repo_dir,
                "worktree_path": str(worktree_path.relative_to(context.root_path)),
            }
        )

    # Phase 11: Update base-config.yaml — set status to active
    workbench_entry["status"] = "active"
    save_yaml_file(config_path, data)

    # Phase 12: Return summary
    return {
        "name": workbench_name,
        "source": source_name,
        "git_branch": git_branch,
        "repos": repo_summaries,
    }


def list_workbenches() -> list[WorkbenchEntry]:
    """List all workbenches from the base config.

    Returns:
        A list of WorkbenchEntry models from the base config.

    Raises:
        ValueError: If mode is UNINITIALIZED.
    """
    # Phase 1: Mode enforcement
    context = detect_mode(Path.cwd())

    if context.mode == BenchMode.UNINITIALIZED:
        raise ValueError(
            "This folder is uninitialized. "
            "Run 'bench init' to create a bench project first."
        )

    # Phase 2: Return workbenches from base config
    assert context.base_config is not None
    return context.base_config.workbenches
