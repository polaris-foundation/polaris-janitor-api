from enum import Enum
from typing import Dict, List

from flask_batteries_included.helpers.error_handler import DuplicateResourceException


class TaskStatus(Enum):
    RUNNING = 0
    COMPLETE = 1
    ERROR = 2


known_tasks: Dict[str, TaskStatus] = {}


def check_no_ongoing_tasks() -> None:
    ongoing_tasks: List[str] = [
        k for k, v in known_tasks.items() if v == TaskStatus.RUNNING
    ]
    if ongoing_tasks:
        raise DuplicateResourceException(
            "Task already in progress: %s", ", ".join(ongoing_tasks)
        )
