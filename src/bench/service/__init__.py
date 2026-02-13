from bench.service.discuss import list_discussions, start_discussion
from bench.service.git import create_git_branch, get_git_status, push_git_branch
from bench.service.init import initialize_project, populate_agents_md
from bench.service.mode_detection import detect_mode
from bench.service.opencode import run_opencode_prompt
from bench.service.source import add_source, list_sources, remove_source, update_source
from bench.service.task import (
    complete_task,
    create_task,
    list_tasks,
    refine_task,
    resolve_task,
    resolve_task_for_implement,
    run_task_interview,
    run_task_phase,
    validate_task_phase,
    validate_task_phase_outputs,
)
from bench.service.workbench import (
    activate_workbench,
    create_workbench,
    delete_workbench,
    list_workbenches,
    retire_workbench,
    update_workbench,
)

__all__ = [
    "activate_workbench",
    "add_source",
    "create_git_branch",
    "complete_task",
    "create_task",
    "create_workbench",
    "delete_workbench",
    "detect_mode",
    "get_git_status",
    "initialize_project",
    "list_discussions",
    "list_sources",
    "list_tasks",
    "list_workbenches",
    "populate_agents_md",
    "push_git_branch",
    "refine_task",
    "remove_source",
    "resolve_task",
    "retire_workbench",
    "resolve_task_for_implement",
    "run_opencode_prompt",
    "run_task_interview",
    "run_task_phase",
    "start_discussion",
    "update_source",
    "update_workbench",
    "validate_task_phase",
    "validate_task_phase_outputs",
]
