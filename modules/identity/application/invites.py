from dataclasses import dataclass

from schemas.invite import (
    InviteCreateBatch,
    InviteCreateOne,
    InviteCreateResult,
    InviteListItem,
)
from services.invite_service import InviteService
from modules.identity.ports import AuditLogger


@dataclass(slots=True, frozen=True)
class IdentityInviteCreateOneResult:
    invite: InviteCreateResult


@dataclass(slots=True, frozen=True)
class IdentityInviteCreateBatchResult:
    invites: list[InviteCreateResult]


@dataclass(slots=True, frozen=True)
class IdentityInviteRevokeResult:
    invite: InviteListItem


@dataclass(slots=True, frozen=True)
class IdentityInviteDeleteResult:
    pass


class IdentityInviteUseCases:
    def __init__(self, invite_service: InviteService) -> None:
        self.invite_service = invite_service

    async def create_one(
        self,
        *,
        data: InviteCreateOne,
        created_by_user_id: int,
        audit: AuditLogger,
    ) -> IdentityInviteCreateOneResult:
        result = await self.invite_service.create_one(
            created_by_user_id=created_by_user_id,
            schema=data,
        )

        await audit.log(
            action="invite.create",
            entity_type="invite",
            entity_id=result.id,
            payload={
                "target_email": result.target_email,
                "target_role": self._role_name(result.target_role),
                "expires_at": result.expires_at.isoformat(),
            },
        )

        return IdentityInviteCreateOneResult(invite=result)

    async def create_batch(
        self,
        *,
        data: InviteCreateBatch,
        created_by_user_id: int,
        audit: AuditLogger,
    ) -> IdentityInviteCreateBatchResult:
        result = await self.invite_service.create_batch(
            created_by_user_id=created_by_user_id,
            schema=data,
        )

        await audit.log(
            action="invite.create_batch",
            entity_type="invite",
            payload={
                "created_count": len(result),
                "target_role": self._role_name(data.target_role),
                "targeted": bool(data.emails),
                "targeted_emails_count": len(data.emails or []),
                "expires_at": data.expires_at.isoformat(),
            },
        )

        return IdentityInviteCreateBatchResult(invites=result)

    async def list_invites(self) -> list[InviteListItem]:
        return await self.invite_service.list_all()

    async def revoke(
        self,
        *,
        invite_id: int,
        audit: AuditLogger,
    ) -> IdentityInviteRevokeResult:
        result = await self.invite_service.revoke(invite_id)

        await audit.log(
            action="invite.revoke",
            entity_type="invite",
            entity_id=invite_id,
            payload={
                "target_email": result.target_email,
                "target_role": self._role_name(result.target_role),
            },
        )

        return IdentityInviteRevokeResult(invite=result)

    async def delete(
        self,
        *,
        invite_id: int,
        audit: AuditLogger,
    ) -> IdentityInviteDeleteResult:
        await self.invite_service.delete(invite_id)

        await audit.log(
            action="invite.delete",
            entity_type="invite",
            entity_id=invite_id,
            payload={"invite_id": invite_id},
        )

        return IdentityInviteDeleteResult()

    @staticmethod
    def _role_name(role) -> str | None:
        return role.name if hasattr(role, "name") else role
