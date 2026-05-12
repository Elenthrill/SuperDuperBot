from datetime import datetime, timedelta
import pytest

from app.bot.entities.group import Group
from app.bot.entities.task import Task
from app.bot.entities.user import User
from app.bot.enums.roles import TaskStatus, UserRole



def make_task(
    task_id: int = 1,
    reward: int = 10,
    duration: timedelta = timedelta(hours=1),
    deadline: datetime | None = None,
    status: TaskStatus = TaskStatus.PENDING,
) -> Task:
    return Task(
        id=task_id,
        description="Test task",
        start_time=datetime.now(),
        duration=duration,
        deadline=deadline or datetime.now() + timedelta(days=1),
        reward=reward,
        user_id=100,
        group_id=200,
        status=status,
    )


def test_user_defaults():
    user = User(
        user_id=1,
        user_name="andrei",
        lang="ru",
        role=UserRole.USER.value,
    )

    assert user.tasks == []
    assert user.groups == []
    assert user.is_alive is True
    assert user.banned is False
    assert user.raiting == 0
    assert user.free_time_at_week is None


def test_group_members_count():
    user_1 = User(user_id=1, user_name="u1", lang="ru", role=UserRole.USER.value)
    user_2 = User(user_id=2, user_name="u2", lang="ru", role=UserRole.USER.value)

    group = Group(group_id=10, members=[user_1, user_2])

    assert group.get_members_count() == 2


def test_group_task_count():
    group = Group(
        group_id=10,
        tasks=[
            make_task(task_id=1),
            make_task(task_id=2),
        ],
    )

    assert group.get_task_count() == 2


def test_group_rating_is_sum_of_task_rewards():
    group = Group(
        group_id=10,
        tasks=[
            make_task(task_id=1, reward=10),
            make_task(task_id=2, reward=25),
            make_task(task_id=3, reward=5),
        ],
    )

    assert group.get_raiting() == 40

@pytest.mark.xfail(
    reason=(
        "BUG: Метод подсчёта общей длительности задач в группе падает, "
        "если в группе есть задачи. Причина: программа начинает считать сумму "
        "с числа 0, а потом пытается прибавить к нему значение типа timedelta."
    ),
    strict=True,
)
def test_group_all_tasks_duration_is_sum_of_durations():
    group = Group(
        group_id=10,
        tasks=[
            make_task(task_id=1, duration=timedelta(hours=1)),
            make_task(task_id=2, duration=timedelta(minutes=30)),
        ],
    )

    assert group.get_all_tasks_duration() == timedelta(hours=1, minutes=30)


def test_task_is_overdue_returns_true_for_past_deadline():
    task = make_task(deadline=datetime.now() - timedelta(days=1))

    assert task.is_overdue() is True


def test_task_is_overdue_returns_false_for_future_deadline():
    task = make_task(deadline=datetime.now() + timedelta(days=1))

    assert task.is_overdue() is False


def test_task_update_status():
    task = make_task(status=TaskStatus.PENDING)

    task.update_status(TaskStatus.IN_PROGRESS)

    assert task.status == TaskStatus.IN_PROGRESS

def test_empty_group_rating_is_zero():
    group = Group(group_id=10)

    assert group.get_raiting() == 0

@pytest.mark.xfail(
    reason=(
        "BUG: Для группы без задач метод общей длительности возвращает обычное "
        "число 0, хотя должен возвращать нулевую длительность timedelta(0). "
        "Из-за этого тип результата отличается от ожидаемого."
    ),
    strict=True,
)
def test_empty_group_all_tasks_duration_is_zero_timedelta():
    group = Group(group_id=10)

    assert group.get_all_tasks_duration() == timedelta()