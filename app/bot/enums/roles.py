from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SERVICE_WORKER = "service_worker"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
