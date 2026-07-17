import pytest
from pydantic import ValidationError

from core.config import CeleryConfig, DatabaseConfig, JWTConfig, Settings, StorageConfig


def make_settings(**overrides) -> Settings:
    values = {
        "DEBUG": False,
        "db": DatabaseConfig(
            host="localhost",
            username="app",
            password="database-password",
            database="app",
        ),
        "jwt": JWTConfig(ACCESS_SECRET_KEY="a-secure-random-secret-with-32-chars"),
        "celery": CeleryConfig(
            broker_url="redis://localhost:6379/0",
            result_backend="redis://localhost:6379/1",
        ),
        "storage": StorageConfig(backend="local"),
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("jwt", JWTConfig(ACCESS_SECRET_KEY="replace-with-at-least-32-random-characters")),
        (
            "db",
            DatabaseConfig(
                host="localhost",
                username="app",
                password="replace-with-database-password",
                database="app",
            ),
        ),
        (
            "storage",
            StorageConfig(
                backend="minio",
                access_key="replace-with-minio-access-key",
                secret_key="replace-with-minio-secret-key",
            ),
        ),
    ],
)
def test_production_settings_reject_documented_placeholders(field, value) -> None:
    with pytest.raises(ValidationError):
        make_settings(**{field: value})
