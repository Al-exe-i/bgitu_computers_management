from datetime import datetime, timezone
from typing import Callable

from core.exceptions import HTTP400, HTTP404, HTTP409
from loguru import logger
from models.invite_link import InviteLink
from repositories.invite_repo import InviteRepository
from schemas.invite import (
    InviteCreateOne,
    InviteCreateBatch,
    InviteCreateResult,
    InviteListItem,
    InvitePreviewResponse,
    RegisterByInviteRequest,
    RegisterByInviteResponse,
)
from schemas.user import UserCreate

from utils.invite_utils import new_invite_token, hash_invite_token


class InviteService:
    def __init__(
        self,
        repo: InviteRepository,
        frontend_base_url: str,
    ):
        self.repo = repo
        self.frontend_base_url = frontend_base_url.rstrip("/")

    def _build_invite_url(self, raw_token: str) -> str:
        return f"{self.frontend_base_url}/register?invite={raw_token}"

    async def create_one(self, created_by_user_id: int, schema: InviteCreateOne) -> InviteCreateResult:
        raw_token = new_invite_token()
        token_hash = hash_invite_token(raw_token)

        invite = InviteLink(
            token_hash=token_hash,
            target_email=schema.target_email,
            target_role=schema.target_role,
            note=schema.note,
            created_by_user_id=created_by_user_id,
            expires_at=schema.expires_at,
        )

        created = await self.repo.create(invite)

        return InviteCreateResult(
            id=created.id,
            invite_url=self._build_invite_url(raw_token),
            target_email=created.target_email,
            target_role=created.target_role,
            expires_at=created.expires_at,
            note=created.note,
        )

    async def create_batch(self, created_by_user_id: int, schema: InviteCreateBatch) -> list[InviteCreateResult]:
        if not schema.count and not schema.emails:
            raise HTTP400("Either count or emails must be provided")

        if schema.count and schema.emails:
            raise HTTP400("Use either count or emails, not both")

        result: list[InviteCreateResult] = []

        if schema.emails:
            for email in schema.emails:
                item = InviteCreateOne(
                    target_email=email,
                    target_role=schema.target_role,
                    expires_at=schema.expires_at,
                    note=schema.note,
                )
                result.append(await self.create_one(created_by_user_id, item))
            return result

        for _ in range(schema.count or 0):
            item = InviteCreateOne(
                target_email=None,
                target_role=schema.target_role,
                expires_at=schema.expires_at,
                note=schema.note,
            )
            result.append(await self.create_one(created_by_user_id, item))

        return result

    async def list_all(self) -> list[InviteListItem]:
        invites = await self.repo.list_all()
        return [
            InviteListItem(
                id=i.id,
                target_email=i.target_email,
                target_role=i.target_role,
                note=i.note,
                created_by_user_id=i.created_by_user_id,
                created_at=i.created_at,
                expires_at=i.expires_at,
                used_at=i.used_at,
                revoked_at=i.revoked_at,
                used_by_user_id=i.used_by_user_id,
            )
            for i in invites
        ]

    async def revoke(self, invite_id: int) -> InviteListItem:
        invite = await self.repo.get_by_id(invite_id)
        if not invite:
            raise HTTP404("Invite not found")

        if invite.used_at is not None:
            raise HTTP400("Invite already used")

        if invite.revoked_at is None:
            invite = await self.repo.revoke(invite)

        return InviteListItem(
            id=invite.id,
            target_email=invite.target_email,
            target_role=invite.target_role,
            note=invite.note,
            created_by_user_id=invite.created_by_user_id,
            created_at=invite.created_at,
            expires_at=invite.expires_at,
            used_at=invite.used_at,
            revoked_at=invite.revoked_at,
            used_by_user_id=invite.used_by_user_id,
        )

    async def preview(self, token: str) -> InvitePreviewResponse:
        token_hash = hash_invite_token(token)
        invite = await self.repo.get_by_token_hash(token_hash)

        if not invite:
            logger.warning("Invite preview failed: invite not found")
            return InvitePreviewResponse(valid=False, reason="Invite not found")

        now = datetime.now(timezone.utc)

        if invite.revoked_at is not None:
            logger.warning("Invite preview failed: invite_id={} revoked", invite.id)
            return InvitePreviewResponse(valid=False, reason="Invite revoked")

        if invite.used_at is not None:
            logger.warning("Invite preview failed: invite_id={} already used", invite.id)
            return InvitePreviewResponse(valid=False, reason="Invite already used")

        if invite.expires_at <= now:
            logger.warning("Invite preview failed: invite_id={} expired", invite.id)
            return InvitePreviewResponse(valid=False, reason="Invite expired")

        return InvitePreviewResponse(
            valid=True,
            target_email=invite.target_email,
            target_role=invite.target_role,
            expires_at=invite.expires_at,
        )

    async def register_by_invite(
        self,
        schema: RegisterByInviteRequest,
        *,
        get_user_by_email: Callable,
        create_user: Callable,
    ) -> RegisterByInviteResponse:
        """
        Пробросить Callable из auth роутера
        """
        token_hash = hash_invite_token(schema.token)

        invite = await self.repo.get_active_by_token_hash_for_update(token_hash)
        if not invite:
            logger.warning("Register by invite failed: invite is invalid or inactive for email={}", schema.email)
            raise HTTP400("Invite is invalid, expired, revoked or already used")

        if invite.target_email and invite.target_email.lower() != schema.email.lower():
            logger.warning(
                "Register by invite failed: invite_id={} assigned to another email target_email={} requested_email={}",
                invite.id,
                invite.target_email,
                schema.email,
            )
            raise HTTP400("This invite is assigned to another email")

        existing_user = await get_user_by_email(schema.email)
        if existing_user is not None:
            logger.warning(
                "Register by invite failed: email already exists invite_id={} email={}",
                invite.id,
                schema.email,
            )
            raise HTTP409("User with this email already exists")

        new_user_schema: UserCreate = UserCreate(
            name=schema.name,
            surname=schema.surname,
            email=schema.email,
            password=schema.password,
            role=invite.target_role,
        )

        created_user = await create_user(
            new_user_schema
        )

        await self.repo.mark_used(invite, used_by_user_id=created_user.id)
        logger.info(
            "Invite consumed: invite_id={} user_id={} email={}",
            invite.id,
            created_user.id,
            created_user.email,
        )

        return RegisterByInviteResponse(
            user_id=created_user.id,
            email=created_user.email,
            role=str(created_user.role.value if hasattr(created_user.role, "value") else created_user.role),
        )

    async def delete(self, invite_id: int) -> None:
        invite = await self.repo.get_by_id(invite_id)
        if not invite:
            logger.warning("Invite delete failed: invite_id={} not found", invite_id)
            raise HTTP404("Invite not found")

        await self.repo.delete(invite)
        logger.info("Invite deleted: invite_id={}", invite_id)
