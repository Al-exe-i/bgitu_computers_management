from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from loguru import logger
from redis.asyncio import Redis
from redis.exceptions import RedisError

from models.user import UserRole


@dataclass(slots=True, frozen=True)
class CachedUser:
    id: int
    name: str | None
    surname: str | None
    email: str
    reg_date: datetime
    is_superuser: bool
    photo: str | None
    access_token_version: int
    role: UserRole


class UserCache:
    key_prefix = "identity:user"

    def __init__(
        self,
        redis: Redis,
        *,
        ttl_seconds: int,
    ) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    async def get(self, user_id: int) -> CachedUser | None:
        try:
            raw = await self.redis.get(self._key(user_id))
        except RedisError as exc:
            logger.debug("User cache read failed for user_id={}: {}", user_id, exc)
            return None

        if not raw:
            return None

        try:
            cached = self._deserialize(raw)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.debug(
                "User cache payload is invalid for user_id={}: {}", user_id, exc
            )
            await self.invalidate(user_id)
            return None

        return cached

    async def set(self, user: Any) -> None:
        user_id = getattr(user, "id", None)
        if user_id is None:
            return

        try:
            await self.redis.set(
                self._key(int(user_id)),
                self._serialize(user),
                ex=self.ttl_seconds,
            )
        except RedisError as exc:
            logger.debug("User cache write failed for user_id={}: {}", user_id, exc)

    async def invalidate(self, user_id: int) -> None:
        try:
            await self.redis.delete(self._key(user_id))
        except RedisError as exc:
            logger.debug(
                "User cache invalidation failed for user_id={}: {}", user_id, exc
            )

    def _key(self, user_id: int) -> str:
        return f"{self.key_prefix}:{user_id}:v2"

    def _serialize(self, user: Any) -> str:
        payload = {
            "id": user.id,
            "name": user.name,
            "surname": user.surname,
            "email": user.email,
            "reg_date": self._datetime_to_str(user.reg_date),
            "is_superuser": user.is_superuser,
            "photo": user.photo,
            "access_token_version": int(getattr(user, "access_token_version", 0) or 0),
            "role": self._role_to_name(user.role),
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _deserialize(raw: str | bytes) -> CachedUser:
        if isinstance(raw, bytes):
            raw = raw.decode()

        data = json.loads(raw)
        return CachedUser(
            id=int(data["id"]),
            name=data.get("name"),
            surname=data.get("surname"),
            email=data["email"],
            reg_date=datetime.fromisoformat(data["reg_date"]),
            is_superuser=bool(data.get("is_superuser", False)),
            photo=data.get("photo"),
            access_token_version=int(data.get("access_token_version", 0) or 0),
            role=UserRole[data["role"]],
        )

    @staticmethod
    def _datetime_to_str(value: datetime) -> str:
        return value.isoformat()

    @staticmethod
    def _role_to_name(role: UserRole | str) -> str:
        if isinstance(role, UserRole):
            return role.name
        return str(role)
