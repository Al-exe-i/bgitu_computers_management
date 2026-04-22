import hashlib
import secrets


def new_telegram_link_token() -> str:
    return secrets.token_urlsafe(32)


def hash_telegram_link_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_telegram_deep_link(*, bot_username: str | None, token: str) -> str | None:
    if not bot_username:
        return None
    return f"https://t.me/{bot_username}?start=link_{token}"
