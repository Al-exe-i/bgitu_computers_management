import os


ENV_DEFAULTS = {
    "BGITU__DB__USERNAME": "test_user",
    "BGITU__DB__PASSWORD": "test_password",
    "BGITU__DB__DATABASE": "test_db",
    "BGITU__JWT__ACCESS_SECRET_KEY": "test-secret-key-with-at-least-32-bytes",
    "BGITU__CELERY__BROKER_URL": "redis://localhost:6379/0",
    "BGITU__CELERY__RESULT_BACKEND": "redis://localhost:6379/1",
    "BGITU__CACHE__REDIS_URL": "redis://localhost:6379/3",
}


for key, value in ENV_DEFAULTS.items():
    os.environ.setdefault(key, value)

os.environ["BGITU__WEBSOCKET__ENABLED"] = "1"
os.environ["BGITU__WEBSOCKET__TRANSPORT"] = "inmemory"
