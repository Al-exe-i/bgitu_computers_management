from collections.abc import Awaitable, Callable
from functools import partial

from core.exceptions.management import BootstrapError, ManagementUserError
from core.security import get_password_hash
from modules.identity.adapters.user_cache import UserCache
from modules.identity.management_contracts import InitialSuperuser, ManagedUserResult
from modules.identity.management_validation import (
    normalize_email,
    validate_new_user_email,
    validate_password,
)
from modules.identity.models.user import User
from modules.identity.repositories.sessions import UserSessionRepository
from modules.identity.repositories.users import UserRepository
from modules.identity.roles import UserRole


def to_result(user: User) -> ManagedUserResult:
    return ManagedUserResult(user.id, user.email, user.role, user.is_superuser)


class ManagedUserService:
    def __init__(
        self,
        users: UserRepository,
        sessions: UserSessionRepository,
        cache: UserCache,
        *,
        on_commit: Callable[[Callable[[], Awaitable[None]]], None],
    ):
        self.users = users
        self.sessions = sessions
        self.cache = cache
        self.on_commit = on_commit

    async def create_admin_user(
        self,
        *,
        email: str,
        password: str,
        is_superuser: bool,
        name: str | None = None,
        surname: str | None = None,
    ) -> ManagedUserResult:
        email = validate_new_user_email(email)
        password = validate_password(password)
        for value in (name, surname):
            if value is not None and len(value) > 64:
                raise ManagementUserError(
                    "Name and surname must contain at most 64 characters"
                )
        if await self.users.get_by_email(email) is not None:
            raise ManagementUserError(f"User already exists: {email}")
        user = User(
            email=email,
            password=get_password_hash(password),
            role=UserRole.admin,
            is_superuser=is_superuser,
            name=name,
            surname=surname,
        )
        await self.users.create_managed(user)
        return to_result(user)

    async def reset_user_password(
        self, *, email: str, password: str
    ) -> ManagedUserResult:
        email = normalize_email(email)
        password_hash = get_password_hash(validate_password(password))
        user = await self.users.reset_managed_password(email, password_hash)
        if user is None:
            raise ManagementUserError(f"User not found: {email}")
        await self.sessions.revoke_all_for_user(user.id)
        self.on_commit(partial(self.cache.invalidate, user.id))
        return to_result(user)

    async def ensure_initial_superuser(
        self, config: InitialSuperuser
    ) -> tuple[ManagedUserResult | None, bool]:
        existing = await self.users.get_first_superuser()
        if existing is not None:
            return to_result(existing), False
        if config.email is None or config.password is None:
            if config.required:
                raise BootstrapError(
                    "No superuser exists. Set BGITU__BOOTSTRAP__SUPERUSER_EMAIL and "
                    "BGITU__BOOTSTRAP__SUPERUSER_PASSWORD, then run bootstrap again."
                )
            return None, False
        if await self.users.get_by_email(normalize_email(config.email)) is not None:
            raise BootstrapError(
                "Bootstrap superuser email belongs to a regular user. "
                "Refusing to elevate the account automatically."
            )
        try:
            result = await self.create_admin_user(
                email=config.email,
                password=config.password,
                is_superuser=True,
                name=config.name,
                surname=config.surname,
            )
        except ManagementUserError as exc:
            raise BootstrapError(str(exc)) from exc
        return result, True
