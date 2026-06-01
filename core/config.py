from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, computed_field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingConfig(BaseSettings):
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)-12s | %(lineno)4d | %(message)s"


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
    ACCESS_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class CeleryConfig(BaseModel):
    broker_url: str
    result_backend: str
    timezone: str = "UTC"


class OutboxConfig(BaseModel):
    batch_size: int = 50
    max_attempts: int = 5
    retry_delay_seconds: int = 60
    stale_after_seconds: int = 300
    poll_interval_seconds: int = 10


class CacheConfig(BaseModel):
    redis_url: str = "redis://localhost:6379/3"
    user_ttl_seconds: int = 600
    office_short_ttl_seconds: int = 300
    analytics_filter_options_ttl_seconds: int = 300


class StorageConfig(BaseModel):
    backend: Literal["local", "minio"] = "local"
    endpoint: str = "localhost:9000"
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


class TelegramConfig(BaseModel):
    enabled: bool = False
    bot_token: str | None = None
    bot_username: str | None = None
    link_token_ttl_minutes: int = 15
    request_timeout_seconds: float = 15.0
    startup_retry_attempts: int = 3
    startup_retry_delay_seconds: float = 2.0


class Settings(BaseSettings):
    db: DatabaseConfig
    jwt: JWTConfig
    api: ApiPrefix = ApiPrefix()
    static: StaticFiles = StaticFiles()
    DEBUG: bool = False
    logger: LoggingConfig = LoggingConfig()
    celery: CeleryConfig
    outbox: OutboxConfig = OutboxConfig()
    cache: CacheConfig = CacheConfig()
    storage: StorageConfig = StorageConfig()
    websocket: WebSocketConfig = WebSocketConfig()
    telegram: TelegramConfig = TelegramConfig()
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


settings = Settings()
