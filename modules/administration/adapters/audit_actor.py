from dataclasses import dataclass

from modules.administration.services.audit_log import AuditLogService
from modules.identity.public import UserOut
from utils.request_meta import RequestMeta


@dataclass(slots=True)
class AuditActor:
    service: AuditLogService
    meta: RequestMeta
    user: UserOut | None = None

    async def log(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        payload: dict | None = None,
        user_id: int | None = None,
    ) -> None:
        actor_id = (
            self.user.id if user_id is None and self.user is not None else user_id
        )
        return await self.service.log(
            user_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            **self.meta,
        )
