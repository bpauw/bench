from enum import Enum


class BenchMode(Enum):
    ROOT = "root"
    WORKBENCH = "workbench"
    WITHIN_ROOT = "within_root"
    UNINITIALIZED = "uninitialized"
