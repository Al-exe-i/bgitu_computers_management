from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


# class ApiV1Prefix(BaseModel):
#     prefix: str = "/v1"


class DatabaseConfig(BaseModel):
    url: str
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10


class JWTConfig(BaseModel):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class Settings(BaseSettings):
    db: DatabaseConfig
    jwt: JWTConfig
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=(".env",),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="BGITU__",
    )


settings = Settings()