from dataclasses import dataclass
from datetime import datetime, timezone

from core.exceptions import (
    InviteAlreadyUsedError,
    InviteBatchInputError,
    InviteInvalidError,
    InviteNotFoundError,
)
from loguru import logger
from models.invite_link import InviteLink
from models.user import UserRole
from repositories.invite_repo import InviteRepository
from schemas.invite import (
    InviteCreateBatch,
    InviteCreateOne,
    InviteCreateResult,
    InviteListItem,
    InvitePreviewResponse,
)
from utils.invite_utils import hash_invite_token, new_invite_token


@dataclass(slots=True, frozen=True)
class InviteRegistrationData:
    id: int
    target_email: str | None
    target_role: UserRole


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
            raise InviteBatchInputError("Either count or emails must be provided")

        if schema.count and schema.emails:
            raise InviteBatchInputError("Use either count or emails, not both")

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
        return [self._to_list_item(invite) for invite in invites]

    async def revoke(self, invite_id: int) -> InviteListItem:
        invite = await self.repo.get_by_id(invite_id)
        if not invite:
            raise InviteNotFoundError()

        if invite.used_at is not None:
            raise InviteAlreadyUsedError()

        if invite.revoked_at is None:
            invite = await self.repo.revoke(invite)

        return self._to_list_item(invite)

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

    async def get_active_for_registration(self, token: str) -> InviteRegistrationData:
        token_hash = hash_invite_token(token)
        invite = await self.repo.get_active_by_token_hash_for_update(token_hash)
        if not invite:
            logger.warning("Register by invite failed: invite is invalid or inactive")
            raise InviteInvalidError()

        return InviteRegistrationData(
            id=invite.id,
            target_email=invite.target_email,
            target_role=invite.target_role,
        )

    async def mark_used(self, invite_id: int, *, used_by_user_id: int) -> None:
        invite = await self.repo.get_by_id(invite_id)
        if not invite:
            raise InviteNotFoundError()

        if invite.used_at is not None:
            raise InviteAlreadyUsedError()

        if invite.revoked_at is not None or invite.expires_at <= datetime.now(timezone.utc):
            raise InviteInvalidError()

        await self.repo.mark_used(invite, used_by_user_id=used_by_user_id)
        logger.info(
            "Invite consumed: invite_id={} user_id={} email={}",
            invite.id,
            used_by_user_id,
            invite.target_email,
        )

    async def delete(self, invite_id: int) -> None:
        invite = await self.repo.get_by_id(invite_id)
        if not invite:
            logger.warning("Invite delete failed: invite_id={} not found", invite_id)
            raise InviteNotFoundError()

        await self.repo.delete(invite)
        logger.info("Invite deleted: invite_id={}", invite_id)

    @staticmethod
    def _to_list_item(invite: InviteLink) -> InviteListItem:
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
