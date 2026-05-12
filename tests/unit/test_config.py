import pytest

from config.config import load_config


def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123:test")
    monkeypatch.setenv("POSTGRES_DB", "postgres")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DATABASE", "0")
    monkeypatch.setenv("REDIS_PASSWORD", "")
    monkeypatch.setenv("REDIS_USERNAME", "")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_FORMAT", "%(levelname)s:%(message)s")

    config = load_config()

    assert config.bot.token == "123:test"
    assert config.db.name == "postgres"
    assert config.db.host == "localhost"
    assert config.db.port == 5432
    assert config.db.user == "postgres"
    assert config.db.password == "secret"
    assert config.redis.host == "localhost"
    assert config.redis.port == 6379
    assert config.redis.db == 0
    assert config.log.level == "DEBUG"


def test_load_config_raises_error_when_bot_token_is_empty(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "")

    with pytest.raises(ValueError, match="BOT_TOKEN must be not empty"):
        load_config()

def test_load_config_reads_optional_redis_credentials(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123:test")
    monkeypatch.setenv("POSTGRES_DB", "postgres")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DATABASE", "0")
    monkeypatch.setenv("REDIS_PASSWORD", "redis_secret")
    monkeypatch.setenv("REDIS_USERNAME", "redis_user")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_FORMAT", "%(message)s")

    config = load_config()

    assert config.redis.password == "redis_secret"
    assert config.redis.username == "redis_user"