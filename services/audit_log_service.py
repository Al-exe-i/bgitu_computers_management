from models.audit_log import AuditLog
from repositories.audit_log_repo import AuditLogRepository
from utils.audit import clean_sensitive


class AuditLogService:
    def __init__(self, repo: AuditLogRepository):
        self.repo = repo

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
    ) -> AuditLog:
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
        return await self.repo.add(entry)

    async def list(self, **kwargs):
        return await self.repo.list(**kwargs)