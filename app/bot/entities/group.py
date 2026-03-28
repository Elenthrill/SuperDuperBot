from __future__ import annotations
from typing import List, TYPE_CHECKING
from dataclasses import dataclass, field
from .task import Task
from typing import List
from datetime import timedelta

if TYPE_CHECKING:
    from .user import User


@dataclass
class Group:
    group_id: int
    members: List[User] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    title: str = None
    name: str = None
    is_alive: bool = True
    banned: bool = False

    def get_members_count(self) -> int:
        return len(self.members)

    def get_task_count(self) -> int:
        return len(self.tasks)

    def get_raiting(self) -> int:
        raiting: int = 0
        for task in self.tasks:
            raiting += task.reward
        return raiting

    def get_all_tasks_duration(self) -> timedelta:
        duration: timedelta = 0
        for task in self.tasks:
            duration += task.duration
        return duration
