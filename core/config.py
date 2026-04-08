from pathlib import Path
from pydantic import BaseModel, computed_field, PostgresDsn, model_validator
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
    REFRESH_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class CeleryConfig(BaseModel):
    broker_url: str
    result_backend: str
    timezone: str = "UTC"


class Settings(BaseSettings):
    db: DatabaseConfig
    jwt: JWTConfig
    api: ApiPrefix = ApiPrefix()
    static: StaticFiles = StaticFiles()
    DEBUG: bool = False
    logger: LoggingConfig = LoggingConfig()
    celery: CeleryConfig
    frontend_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=(".env",),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="BGITU__",
    )


settings = Settings()