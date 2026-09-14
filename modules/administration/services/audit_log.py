from modules.administration.models.audit_log import AuditLog
from modules.administration.repositories.audit_log import AuditLogRepository
from modules.administration.schemas import AuditLogActor, AuditLogItem
from modules.identity.public import UserSummaryDirectory
from utils.audit import clean_sensitive


class AuditLogService:
    def __init__(self, repo: AuditLogRepository, users: UserSummaryDirectory):
        self.repo = repo
        self.users = users

    async def log(
        self,
        *,
        user_id: int | None,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        payload: dict | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
        path: str | None = None,
        method: str | None = None,
    ) -> None:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=clean_sensitive(payload),
            ip=ip,
            user_agent=user_agent,
            path=path,
            method=method,
        )
        await self.repo.add(entry)

    async def list(self, **kwargs) -> tuple[list[AuditLogItem], int]:
        entries, total = await self.repo.list(**kwargs)
        user_ids = {entry.user_id for entry in entries if entry.user_id is not None}
        users = await self.users.get_summaries(user_ids) if user_ids else {}
        items = []
        for entry in entries:
            item = AuditLogItem.model_validate(entry)
            user = users.get(entry.user_id)
            item.user = AuditLogActor.model_validate(user) if user is not None else None
            items.append(item)
        return items, total
