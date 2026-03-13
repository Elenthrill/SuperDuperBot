import logging
import os
from dataclasses import dataclass

from environs import Env

logger = logging.getLogger(__name__)


@dataclass
class BotSettings:
    token: str
    admin_ids: list[int]
    pollice_group_id: int
    traffic_police_group_id: int
    fire_department_group_id: int


@dataclass
class DatabaseSettings:
    name: str
    host: str
    port: int
    user: str
    password: str


@dataclass
class RedisSettings:
    host: str
    port: int
    db: int
    password: str
    username: str


@dataclass
class LoggSettings:
    level: str
    format: str


@dataclass
class Config:
    bot: BotSettings
    db: DatabaseSettings
    redis: RedisSettings
    log: LoggSettings


def load_config(path: str | None = None) -> Config:
    env = Env()

    if path:
        if not os.path.exists(path):
            logger.warning(".env file not found at '%s', skipping...", path)
        else:
            logger.info("Loading .env from '%s'", path)
    env.read_env(path)

    token = env("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN must be not empty")

    raw_ids = env.list("ADMIN_IDS", default=[])

    try:
        admin_ids = [int(x) for x in raw_ids]
        pollice_group_id = env.int("POLLICE_ID")
        traffic_police_group_id = env.int("TRAFFIC_POLICE_ID")
        fire_department_group_id = env.int("FIRE_DEPARTMENT_ID")

    except ValueError as e:
        raise ValueError(f"ADMIN_IDS must be integers, got: {raw_ids}") from e

    db = DatabaseSettings(
        name=env("POSTGRES_DB"),
        host=env("POSTGRES_HOST"),
        port=env.int("POSTGRES_PORT"),
        user=env("POSTGRES_USER"),
        password=env("POSTGRES_PASSWORD"),
    )

    redis = RedisSettings(
        host=env("REDIS_HOST"),
        port=env.int("REDIS_PORT"),
        db=env.int("REDIS_DATABASE"),
        password=env("REDIS_PASSWORD", default=""),
        username=env("REDIS_USERNAME", default=""),
    )

    logg_settings = LoggSettings(level=env("LOG_LEVEL"), format=env("LOG_FORMAT"))

    logger.info("Configurations loaded successfully")

    return Config(
        bot=BotSettings(
            token=token,
            admin_ids=admin_ids,
            pollice_group_id=pollice_group_id,
            traffic_police_group_id=traffic_police_group_id,
            fire_department_group_id=fire_department_group_id,
        ),
        db=db,
        redis=redis,
        log=logg_settings,
    )
