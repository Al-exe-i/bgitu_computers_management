from dataclasses import dataclass

from loguru import logger

from core.exceptions import (
    IdentityError,
    InvalidCurrentPasswordError,
    InvalidUserPhotoError,
    SamePasswordError,
    SelfDeleteForbiddenError,
    SuperuserDeleteForbiddenError,
    UserNotFoundError,
    UserPermissionDeniedError,
)
from core.security import verify_password
from models.user import UserRole
from schemas.user import ChangePasswordSchema, UserCreate, UserOut, UserUpdate
from modules.identity.events import AuthSecurityNotificationEvent, IdentityEvent
from modules.identity.ports import (
    AuditLogger,
    IdentityActor,
    StoredAvatarFile,
    UploadedAvatarFile,
    UserServicePort,
)
from utils.audit import changed_fields


PASSWORD_CHANGED_EVENT_NAME = "Изменён пароль аккаунта"


@dataclass(slots=True, frozen=True)
class IdentityUserResult:
    user: UserOut
    events: list[IdentityEvent]


@dataclass(slots=True, frozen=True)
class IdentityUserCommandResult:
    events: list[IdentityEvent]


class IdentityUserUseCases:
    def __init__(self, user_service: UserServicePort) -> None:
        self.user_service = user_service

    async def list_users(self) -> list[UserOut]:
        users = await self.user_service.get_all()
        return [UserOut.model_validate(user, from_attributes=True) for user in users]

    async def create_user(
        self,
        *,
        data: UserCreate,
        audit: AuditLogger,
    ) -> IdentityUserResult:
        user = await self.user_service.create(data)
        if user is None:
            raise IdentityError("User was not created")

        logger.info("User created: user_id={} email={}", user.id, user.email)
        await audit.log(
            action="user.create",
            entity_type="user",
            entity_id=user.id,
            payload={
                "target_user_id": user.id,
                "email": user.email,
                "role": self._role_name(user.role),
            },
        )

        return IdentityUserResult(user=user, events=[])

    async def read_user(
        self,
        *,
        user_id: int,
        actor: IdentityActor,
    ) -> UserOut:
        if actor.id != user_id and actor.role != UserRole.admin:
            logger.warning(
                "User read rejected: actor_id={} target_user_id={}",
                actor.id,
                user_id,
            )
            raise UserPermissionDeniedError()

        user = await self.user_service.get(user_id)
        if not user:
            logger.warning("User read failed: target_user_id={} not found", user_id)
            raise UserNotFoundError()

        return user

    def get_current_photo(self, *, actor: IdentityActor) -> StoredAvatarFile | None:
        return self.user_service.get_photo(actor)

    async def change_password(
        self,
        *,
        data: ChangePasswordSchema,
        actor: IdentityActor,
        audit: AuditLogger,
        ip: str | None,
        user_agent: str | None,
    ) -> IdentityUserCommandResult:
        if not verify_password(data.current_password, actor.password):
            logger.warning(
                "Password change rejected: invalid current password for user_id={}",
                actor.id,
            )
            raise InvalidCurrentPasswordError()

        if data.current_password == data.new_password:
            logger.warning("Password change rejected: new password equals old for user_id={}", actor.id)
            raise SamePasswordError()

        await self.user_service.update(actor.id, UserUpdate(password=data.new_password))
        logger.info("Password changed for user_id={}", actor.id)

        await audit.log(
            action="user.password_change",
            entity_type="user",
            entity_id=actor.id,
            payload={"target_user_id": actor.id},
        )

        return IdentityUserCommandResult(
            events=[
                AuthSecurityNotificationEvent(
                    user_id=actor.id,
                    event_name=PASSWORD_CHANGED_EVENT_NAME,
                    ip=ip,
                    user_agent=user_agent,
                )
            ],
        )

    async def delete_user(
        self,
        *,
        user_id: int,
        actor: IdentityActor,
        audit: AuditLogger,
    ) -> IdentityUserCommandResult:
        user = await self.user_service.get(user_id)
        if not user:
            logger.warning("User deletion failed: target_user_id={} not found", user_id)
            raise UserNotFoundError()

        if actor.id == user_id:
            logger.warning("User deletion rejected: self-delete attempt user_id={}", user_id)
            raise SelfDeleteForbiddenError()

        if user.is_superuser:
            logger.warning(
                "User deletion rejected: target_user_id={} is superuser actor_id={}",
                user_id,
                actor.id,
            )
            raise SuperuserDeleteForbiddenError()

        await self.user_service.delete(user_id)
        logger.info("User deleted: actor_id={} target_user_id={}", actor.id, user_id)

        await audit.log(
            action="user.delete",
            entity_type="user",
            entity_id=user_id,
            payload={
                "target_user_id": user_id,
                "email": user.email,
                "role": self._role_name(user.role),
            },
        )

        return IdentityUserCommandResult(events=[])

    async def update_user(
        self,
        *,
        user_id: int,
        data: UserUpdate,
        actor: IdentityActor,
        audit: AuditLogger,
    ) -> IdentityUserResult:
        if not self._can_manage_user(actor, user_id):
            logger.warning(
                "User update rejected: actor_id={} target_user_id={}",
                actor.id,
                user_id,
            )
            raise UserPermissionDeniedError()

        user = await self.user_service.get(user_id)
        if not user:
            logger.warning("User update failed: target_user_id={} not found", user_id)
            raise UserNotFoundError()

        self._ensure_can_change_superuser(actor, user)

        if actor.id == user_id and actor.role != UserRole.admin and not actor.is_superuser:
            data = UserUpdate(**data.model_dump(exclude={"role"}, exclude_unset=True))

        updated_user = await self.user_service.update(user_id, data)
        if updated_user is None:
            raise UserNotFoundError()

        fields = changed_fields(data)
        logger.info(
            "User updated: actor_id={} target_user_id={} changed_fields={}",
            actor.id,
            user_id,
            fields,
        )
        await audit.log(
            action="user.update",
            entity_type="user",
            entity_id=user_id,
            payload={
                "target_user_id": user_id,
                "changed_fields": fields,
            },
        )

        return IdentityUserResult(user=updated_user, events=[])

    async def upload_user_photo(
        self,
        *,
        user_id: int,
        file: UploadedAvatarFile,
        actor: IdentityActor,
        audit: AuditLogger,
    ) -> IdentityUserResult:
        if not self._can_manage_user(actor, user_id):
            logger.warning(
                "User photo upload rejected: actor_id={} target_user_id={}",
                actor.id,
                user_id,
            )
            raise UserPermissionDeniedError()

        user = await self.user_service.get(user_id)
        if not user:
            logger.warning("User photo upload failed: target_user_id={} not found", user_id)
            raise UserNotFoundError()

        self._ensure_can_change_superuser(actor, user)

        if not (file.content_type or "").startswith("image/"):
            logger.warning(
                "User photo upload rejected: invalid content type user_id={} filename={} content_type={}",
                user_id,
                file.filename,
                file.content_type,
            )
            raise InvalidUserPhotoError()

        result = await self.user_service.upload_photo(user_id, file)
        if result is None:
            logger.warning("User photo upload failed: target_user_id={} not found", user_id)
            raise UserNotFoundError()

        await audit.log(
            action="user.photo_upload",
            entity_type="user",
            entity_id=user_id,
            payload={
                "target_user_id": user_id,
                "replaced_existing": result.had_photo,
            },
        )
        logger.info(
            "User photo uploaded: actor_id={} target_user_id={} replaced_existing={}",
            actor.id,
            user_id,
            result.had_photo,
        )

        return IdentityUserResult(user=result.user, events=[])

    async def delete_user_photo(
        self,
        *,
        user_id: int,
        actor: IdentityActor,
        audit: AuditLogger,
    ) -> IdentityUserResult:
        if not self._can_manage_user(actor, user_id):
            logger.warning(
                "User photo delete rejected: actor_id={} target_user_id={}",
                actor.id,
                user_id,
            )
            raise UserPermissionDeniedError()

        user = await self.user_service.get(user_id)
        if not user:
            logger.warning("User photo delete failed: target_user_id={} not found", user_id)
            raise UserNotFoundError()

        self._ensure_can_change_superuser(actor, user)

        result = await self.user_service.delete_photo(user_id)
        if result is None:
            logger.warning("User photo delete failed: target_user_id={} not found", user_id)
            raise UserNotFoundError()

        await audit.log(
            action="user.photo_delete",
            entity_type="user",
            entity_id=user_id,
            payload={
                "target_user_id": user_id,
                "had_photo": result.had_photo,
            },
        )
        logger.info(
            "User photo deleted: actor_id={} target_user_id={} had_photo={}",
            actor.id,
            user_id,
            result.had_photo,
        )

        return IdentityUserResult(user=result.user, events=[])

    @staticmethod
    def _can_manage_user(actor: IdentityActor, target_user_id: int) -> bool:
        return actor.id == target_user_id or actor.role == UserRole.admin or actor.is_superuser

    @staticmethod
    def _ensure_can_change_superuser(actor: IdentityActor, target_user: UserOut) -> None:
        if target_user.is_superuser and actor.id != target_user.id:
            logger.warning(
                "User operation rejected by superuser protection: actor_id={} target_user_id={}",
                actor.id,
                target_user.id,
            )
            raise UserPermissionDeniedError("Can't change another superuser")

    @staticmethod
    def _role_name(role) -> str | None:
        return role.name if hasattr(role, "name") else role
