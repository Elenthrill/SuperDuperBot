from __future__ import annotations

from typing import List, Dict
from enum import IntEnum
from datetime import timedelta
from dataclasses import dataclass, field
from app.bot.entities.task import Task
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.bot.entities.group import Group  # только для проверки типов


@dataclass
class User:
    user_id: int
    user_name: str
    lang: str
    role: str
    tasks: List[Task] = field(default_factory=list)
    groups: List[Group] = field(default_factory=list)
    is_alive: bool = True
    banned: bool = False
    free_time_at_week: timedelta | None = None
    raiting: int = 0
