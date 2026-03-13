from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SERVICE_WORKER = "service_worker"
