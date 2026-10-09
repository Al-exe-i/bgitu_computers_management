from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    PostgresDsn,
    SecretStr,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingConfig(BaseSettings):
    level: str = "INFO"
    format: str = (
        "%(asctime)s | %(levelname)-8s | %(name)-12s | %(lineno)4d | %(message)s"
    )


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class StaticFiles(BaseModel):
    root: Path = Path("static")

    @computed_field
    @property
    def upload_dir(self) -> Path:
        return self.root / "uploads"

    @computed_field
    @property
    def avatars_dir(self) -> Path:
        return self.root / "avatars"


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    username: str
    password: str
    database: str

    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @computed_field
    @property
    def url(self) -> PostgresDsn:
        db = self.database.lstrip("/")
        dsn = (
            f"postgresql+asyncpg://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{db}"
        )
        return PostgresDsn(dsn)


class JWTConfig(BaseModel):
    ACCESS_SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=10, gt=0, le=60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0, le=30)


class TaskiqConfig(BaseModel):
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    result_ttl_seconds: int = Field(default=86400, gt=0)


class CacheConfig(BaseModel):
    redis_url: str = "redis://localhost:6379/3"
    user_ttl_seconds: int = 600
    office_short_ttl_seconds: int = 300
    analytics_filter_options_ttl_seconds: int = 300


class StorageConfig(BaseModel):
    backend: Literal["local", "minio"] = "local"
    endpoint: str = "localhost:9005"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    bucket: str = "bgitu-files"
    secure: bool = False


class WebSocketConfig(BaseModel):
    enabled: bool = True
    transport: Literal["inmemory", "redis"] = "inmemory"
    redis_url: str = "redis://localhost:6379/2"
    pubsub_channel: str = "ws:broadcast"
    instance_ttl_seconds: int = 30
    connection_ttl_seconds: int = 30
    heartbeat_interval_seconds: int = 10
    cleanup_interval_seconds: int = 30
    instance_id: str | None = None


class BootstrapOfficeConfig(BaseModel):
    id: int = Field(gt=0)
    address: str = Field(min_length=1, max_length=100)


class BootstrapConfig(BaseModel):
    offices: list[BootstrapOfficeConfig] = Field(
        default_factory=lambda: [
            BootstrapOfficeConfig(id=1, address="Корпус №1"),
            BootstrapOfficeConfig(id=2, address="Корпус №2"),
        ]
    )
    require_superuser: bool = True
    superuser_email: str | None = Field(default=None, max_length=50)
    superuser_password: SecretStr | None = None
    superuser_name: str | None = Field(default=None, max_length=64)
    superuser_surname: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def validate_initial_superuser_credentials(self) -> "BootstrapConfig":
        has_email = bool(self.superuser_email and self.superuser_email.strip())
        has_password = bool(
            self.superuser_password and self.superuser_password.get_secret_value()
        )
        if has_email != has_password:
            raise ValueError(
                "Bootstrap superuser email and password must be configured together"
            )

        office_ids = [office.id for office in self.offices]
        if len(office_ids) != len(set(office_ids)):
            raise ValueError("Bootstrap office IDs must be unique")

        return self


class Settings(BaseSettings):
    db: DatabaseConfig
    jwt: JWTConfig
    api: ApiPrefix = ApiPrefix()
    static: StaticFiles = StaticFiles()
    DEBUG: bool = False
    logger: LoggingConfig = LoggingConfig()
    taskiq: TaskiqConfig = TaskiqConfig()
    cache: CacheConfig = CacheConfig()
    storage: StorageConfig = StorageConfig()
    websocket: WebSocketConfig = WebSocketConfig()
    bootstrap: BootstrapConfig = BootstrapConfig()
    frontend_url: str = "http://localhost:5173"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ]
    )
    PROJECT_NAME: str = "BGITU Computers Management"
    trusted_proxy_ips: list[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=(".env",),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="BGITU__",
        extra="ignore",
    )

    @model_validator(mode="after")
    def reject_insecure_production_defaults(self) -> "Settings":
        if self.DEBUG:
            return self

        if self.jwt.ACCESS_SECRET_KEY.startswith("replace-with-"):
            raise ValueError(
                "Placeholder JWT secret is forbidden when DEBUG is disabled"
            )

        if self.db.password.startswith("replace-with-"):
            raise ValueError(
                "Placeholder database password is forbidden when DEBUG is disabled"
            )

        if self.storage.backend == "minio" and any(
            value == "minioadmin" or value.startswith("replace-with-")
            for value in (self.storage.access_key, self.storage.secret_key)
        ):
            raise ValueError(
                "Default MinIO credentials are forbidden when DEBUG is disabled"
            )

        if (
            self.bootstrap.superuser_password is not None
            and self.bootstrap.superuser_password.get_secret_value().startswith(
                "replace-with-"
            )
        ):
            raise ValueError(
                "Placeholder bootstrap superuser password is forbidden when DEBUG is disabled"
            )

        return self


settings = Settings()
