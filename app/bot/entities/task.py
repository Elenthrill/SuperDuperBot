from dataclasses import dataclass
from datetime import datetime, timedelta
from app.bot.enums.roles import TaskStatus
from typing import Optional


@dataclass
class Task:
    id: int
    description: str
    start_time: datetime
    duration: timedelta
    deadline: datetime
    reward: int
    user_id: int
    group_id: int
    status: TaskStatus = TaskStatus.PENDING
    end_time: Optional[datetime] = None

    def is_overdue(self) -> bool:
        return datetime.now() > self.deadline

    def update_status(self, new_status: TaskStatus):
        self.status = new_status
